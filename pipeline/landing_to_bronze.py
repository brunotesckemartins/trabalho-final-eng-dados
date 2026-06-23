"""
landing_to_bronze.py
---------------------
Job Spark: Landing (CSV bruto) -> Bronze (Delta Lake)

Responsabilidade desta camada (e só esta):
  - Ler o CSV exatamente como ele chega da origem (sem casting de tipo,
    sem regra de negócio, sem deduplicação).
  - Adicionar colunas de auditoria (quando/de onde o dado entrou no Lake).
  - Gravar em Delta, em modo APPEND -> a Bronze acumula histórico de toda
    extração feita pelo Gabriel, nunca sobrescreve.

A deduplicação e a tipagem ficam por conta da camada Silver
(bronze_to_silver.py), que escolhe a versão mais recente de cada registro.

Uso (um job por tabela, pensado para virar uma task do orquestrador):

    spark-submit landing_to_bronze.py --table pedidos
    spark-submit landing_to_bronze.py --table clientes
    ...
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.functions import current_timestamp, input_file_name, lit

from config import bronze_path, get_spark_session, landing_path
from schemas import TABLE_SCHEMAS, string_schema


def _read_landing_csv(spark: SparkSession, table_name: str) -> DataFrame:
    schema = string_schema(table_name)
    src_path = landing_path(table_name)
    print(f"[BRONZE] Lendo CSV de origem: {src_path}")
    return (
        spark.read.option("header", "true")
        .option("sep", ",")
        .option("enforceSchema", "false")
        .schema(schema)
        .csv(src_path)
    )

def run(table_name: str, spark: SparkSession = None) -> None:
    if table_name not in TABLE_SCHEMAS:
        raise ValueError(
            f"Tabela '{table_name}' não está mapeada em schemas.py "
            f"(opções válidas: {sorted(TABLE_SCHEMAS.keys())})"
        )

    owns_session = spark is None
    if spark is None:
        spark = get_spark_session(f"bronze_{table_name}")

    df_raw = _read_landing_csv(spark, table_name)

    df_bronze = (
        df_raw.withColumn("_ingestion_timestamp", current_timestamp())
        .withColumn("_source_file", input_file_name())
        .withColumn("_source_table", lit(table_name))
    )

    dst_path = bronze_path(table_name)
    print(f"[BRONZE] Gravando em Delta (append): {dst_path}")
    df_bronze.write.format("delta").mode("append").save(dst_path)

    total = df_bronze.count()
    print(f"[BRONZE] OK -> '{table_name}': {total} linha(s) gravada(s).")

    if owns_session:
        spark.stop()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Landing -> Bronze (Delta Lake)")
    parser.add_argument(
        "--table", required=True, help="Nome da tabela a processar (ex: pedidos)"
    )
    args = parser.parse_args()
    run(args.table)
