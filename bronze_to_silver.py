"""
bronze_to_silver.py
--------------------
Job Spark: Bronze (Delta, raw/string) -> Silver (Delta, tipado e limpo).

Responsabilidade desta camada:
  1. Ler a Bronze (que é append-only e pode ter o mesmo registro repetido
     em várias cargas) e ficar só com a versão mais recente de cada
     chave primária (_ingestion_timestamp mais alto).
  2. Converter cada coluna do texto bruto para o tipo definido em
     schemas.py (int, decimal, date, timestamp), com checagem de quantos
     valores "se perderam" no cast (sinal de formato inesperado vindo da
     origem).
  3. Aplicar regras de qualidade específicas por tabela (TABLE_RULES).
  4. Gravar na Silver via MERGE (upsert) pela chave primária — assim a
     Silver sempre reflete o estado atual e correto de cada entidade,
     sem duplicar histórico (histórico fica só na Bronze).

Uso (um job por tabela, pensado para virar uma task do orquestrador):

    spark-submit bronze_to_silver.py --table pedidos
    spark-submit bronze_to_silver.py --table clientes
    ...
"""

import argparse

from delta.tables import DeltaTable
from pyspark.sql import Column, DataFrame, SparkSession, Window
from pyspark.sql.functions import col, current_timestamp, desc, row_number, trim, upper

from config import bronze_path, get_spark_session, silver_path
from schemas import PRIMARY_KEYS, TABLE_SCHEMAS

# ---------------------------------------------------------------------------
# Regras de qualidade / negócio específicas por tabela.
# Cada função recebe o DataFrame já tipado e devolve o DataFrame filtrado
# /ajustado. Tabelas sem regra especial simplesmente não entram no dict.
# ---------------------------------------------------------------------------


def _rules_clientes(df: DataFrame) -> DataFrame:
    # CPF e e-mail são a base de identificação do cliente: sem eles,
    # o registro não é confiável para a Gold.
    return df.filter(col("cpf").isNotNull() & col("email").isNotNull())


def _rules_pedidos(df: DataFrame) -> DataFrame:
    status_validos = ["Concluído", "Pendente", "Cancelado"]
    return df.filter(col("status_pedido").isin(status_validos))


def _rules_itens_pedido(df: DataFrame) -> DataFrame:
    return df.filter((col("quantidade") > 0) & (col("preco_unitario") > 0))


def _rules_pagamentos_pedido(df: DataFrame) -> DataFrame:
    return df.filter(col("valor_pago") > 0)


def _rules_lojas(df: DataFrame) -> DataFrame:
    return df.withColumn("estado_loja", upper(trim(col("estado_loja"))))


def _rules_enderecos(df: DataFrame) -> DataFrame:
    return df.withColumn("estado", upper(trim(col("estado"))))


TABLE_RULES = {
    "clientes": _rules_clientes,
    "pedidos": _rules_pedidos,
    "itens_pedido": _rules_itens_pedido,
    "pagamentos_pedido": _rules_pagamentos_pedido,
    "lojas": _rules_lojas,
    "enderecos": _rules_enderecos,
}


def _latest_per_key(df: DataFrame, primary_key: str) -> DataFrame:
    """Mantém apenas a linha mais recente de cada chave primária."""
    window = Window.partitionBy(primary_key).orderBy(desc("_ingestion_timestamp"))
    return (
        df.withColumn("_rn", row_number().over(window))
        .filter(col("_rn") == 1)
        .drop("_rn")
    )


def _is_blank(c: Column) -> Column:
    return c.isNull() | (trim(c) == "")


def _cast_and_validate(df: DataFrame, schema) -> DataFrame:
    """
    Faz o cast de cada coluna para o tipo definido no schema e avisa
    (via log) se algum valor não-nulo na origem virou nulo após o cast
    -- isso normalmente indica formato de data/número inesperado vindo
    da extração do Gabriel, e precisa ser investigado, não ignorado.
    """
    for field in schema.fields:
        name = field.name
        antes = df.filter(~_is_blank(col(name))).count()

        df = df.withColumn(name, col(name).cast(field.dataType))

        if field.dataType.typeName() == "string":
            df = df.withColumn(name, trim(col(name)))
        else:
            depois = df.filter(col(name).isNotNull()).count()
            perdidos = antes - depois
            if perdidos > 0:
                print(
                    f"[SILVER] Aviso: {perdidos} valor(es) em '{name}' "
                    f"não foram convertidos para {field.dataType.simpleString()} "
                    f"(possível formato inesperado vindo da Landing/Bronze)."
                )
    return df


def _upsert_silver(spark: SparkSession, df_silver: DataFrame, dst_path: str, primary_key: str) -> None:
    if DeltaTable.isDeltaTable(spark, dst_path):
        tgt = DeltaTable.forPath(spark, dst_path)
        (
            tgt.alias("t")
            .merge(df_silver.alias("s"), f"t.{primary_key} = s.{primary_key}")
            .whenMatchedUpdateAll()
            .whenNotMatchedInsertAll()
            .execute()
        )
    else:
        # Primeira carga: a tabela Delta ainda não existe na Silver.
        df_silver.write.format("delta").mode("overwrite").save(dst_path)


def run(table_name: str, spark: SparkSession = None) -> None:
    if table_name not in TABLE_SCHEMAS:
        raise ValueError(
            f"Tabela '{table_name}' não está mapeada em schemas.py "
            f"(opções válidas: {sorted(TABLE_SCHEMAS.keys())})"
        )

    owns_session = spark is None
    if spark is None:
        spark = get_spark_session(f"silver_{table_name}")

    schema = TABLE_SCHEMAS[table_name]
    primary_key = PRIMARY_KEYS[table_name]
    src_path = bronze_path(table_name)
    dst_path = silver_path(table_name)

    print(f"[SILVER] Lendo Bronze: {src_path}")
    df_bronze = spark.read.format("delta").load(src_path)

    df_dedup = _latest_per_key(df_bronze, primary_key)

    print(f"[SILVER] Tipando e limpando '{table_name}'")
    df_typed = _cast_and_validate(df_dedup, schema)

    total_antes = df_typed.count()
    df_typed = df_typed.filter(col(primary_key).isNotNull())

    if table_name in TABLE_RULES:
        df_typed = TABLE_RULES[table_name](df_typed)

    total_depois = df_typed.count()
    descartadas = total_antes - total_depois
    if descartadas > 0:
        print(
            f"[SILVER] Aviso: {descartadas} linha(s) descartada(s) por regra "
            f"de qualidade em '{table_name}'."
        )

    df_final = df_typed.withColumn("_silver_processed_at", current_timestamp())

    print(f"[SILVER] Gravando (merge/upsert) em: {dst_path}")
    _upsert_silver(spark, df_final, dst_path, primary_key)

    print(f"[SILVER] OK -> '{table_name}': {total_depois} linha(s) válida(s) processada(s).")

    if owns_session:
        spark.stop()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Bronze -> Silver (Delta Lake)")
    parser.add_argument(
        "--table", required=True, help="Nome da tabela a processar (ex: pedidos)"
    )
    args = parser.parse_args()
    run(args.table)
