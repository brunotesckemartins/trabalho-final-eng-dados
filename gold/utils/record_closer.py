"""
record_closer.py
----------------
Lógica de encerramento de registros antigos para SCD Tipo 2.

Responsabilidades:
  - Marcar registro anterior como inativo (registro_ativo=False).
  - Preencher data_fim_vigencia corretamente.
  - Garantir apenas uma versão ativa por chave de negócio.
"""

import sys
sys.path.insert(0, '/home/elison/trabalho-final-eng-dados')

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.functions import col, current_timestamp, lit
from delta.tables import DeltaTable


def close_old_records(
    spark: SparkSession,
    df_alterados: DataFrame,
    dst_path: str,
    primary_key: str,
) -> int:
    """
    Encerra registros antigos na Gold para os registros alterados.

    Para cada chave primária em df_alterados:
      - Busca o registro ativo na Gold.
      - Marca registro_ativo=False.
      - Preenche data_fim_vigencia com o timestamp atual.

    Retorna o número de registros encerrados.
    """

    if not DeltaTable.isDeltaTable(spark, dst_path):
        print("[RECORD CLOSER] Tabela Gold não existe ainda — nada a encerrar.")
        return 0

    count = df_alterados.count()
    if count == 0:
        print("[RECORD CLOSER] Nenhum registro alterado — nada a encerrar.")
        return 0

    tgt = DeltaTable.forPath(spark, dst_path)
    now = current_timestamp()

    tgt.alias("t").merge(
        df_alterados.alias("s"),
        f"t.{primary_key} = s.{primary_key} AND t.registro_ativo = true"
    ).whenMatchedUpdate(set={
        "registro_ativo": lit(False),
        "data_fim_vigencia": now,
    }).execute()

    print(f"[RECORD CLOSER] {count} registro(s) encerrado(s) em: {dst_path}")
    return count


def validate_single_active(
    spark: SparkSession,
    dst_path: str,
    primary_key: str,
) -> bool:
    """
    Valida que existe apenas uma versão ativa por chave de negócio.
    Retorna True se válido, False se houver duplicidade.
    """

    if not DeltaTable.isDeltaTable(spark, dst_path):
        print("[RECORD CLOSER] Tabela não existe — validação ignorada.")
        return True

    df = spark.read.format("delta").load(dst_path)

    duplicados = (
        df.filter(col("registro_ativo") == True)
        .groupBy(primary_key)
        .count()
        .filter(col("count") > 1)
    )

    count_dup = duplicados.count()
    if count_dup > 0:
        print(f"[RECORD CLOSER] ALERTA: {count_dup} chave(s) com mais de uma versão ativa!")
        duplicados.show()
        return False

    print(f"[RECORD CLOSER] Validação OK — apenas uma versão ativa por chave.")
    return True
