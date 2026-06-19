"""
version_inserter.py
-------------------
Processo de inserção de novas versões para registros alterados.

Responsabilidades:
  - Inserir nova versão ativa após alteração.
  - Preservar histórico completo de versões anteriores.
  - Garantir que o registro ativo reflete o estado atual.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.functions import col, current_timestamp, lit
from delta.tables import DeltaTable


def insert_new_version(
    spark: SparkSession,
    df_novos: DataFrame,
    dst_path: str,
) -> int:
    """
    Insere novas versões ativas na tabela Gold.

    Cada linha em df_novos é inserida com:
      - registro_ativo = True
      - data_inicio_vigencia = agora
      - data_fim_vigencia = None
    """

    count = df_novos.count()
    if count == 0:
        print("[VERSION INSERTER] Nenhuma nova versão para inserir.")
        return 0

    now = current_timestamp()

    df_para_inserir = (
        df_novos
        .withColumn("registro_ativo", lit(True))
        .withColumn("data_inicio_vigencia", now)
        .withColumn("data_fim_vigencia", lit(None).cast("timestamp"))
        .withColumn("_gold_processed_at", now)
    )

    if not DeltaTable.isDeltaTable(spark, dst_path):
        df_para_inserir.write.format("delta").mode("overwrite").save(dst_path)
        print(f"[VERSION INSERTER] Tabela criada com {count} registro(s): {dst_path}")
        return count

    tgt = DeltaTable.forPath(spark, dst_path)
    tgt.alias("t").merge(
        df_para_inserir.alias("s"),
        "1=0"  # nunca faz match — força insert de todos
    ).whenNotMatchedInsertAll().execute()

    print(f"[VERSION INSERTER] {count} nova(s) versão(ões) inserida(s): {dst_path}")
    return count


def get_history(
    spark: SparkSession,
    dst_path: str,
    primary_key: str,
    key_value,
) -> DataFrame:
    """
    Retorna todo o histórico de versões de uma chave de negócio.
    Útil para auditoria e evidência de histórico.
    """

    df = spark.read.format("delta").load(dst_path)
    return (
        df.filter(col(primary_key) == key_value)
        .orderBy("data_inicio_vigencia")
    )
