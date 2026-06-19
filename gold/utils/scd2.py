"""
scd2.py
-------
Utilitário de SCD Tipo 2 para a camada Gold.

Regras:
  - registro_ativo = True  -> registro vigente atual
  - registro_ativo = False -> registro histórico
  - data_fim_vigencia = None -> registro ainda ativo
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from delta.tables import DeltaTable
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.functions import col, current_timestamp, lit


def apply_scd2(
    spark: SparkSession,
    df_new: DataFrame,
    dst_path: str,
    primary_key: str,
    business_columns: list,
) -> None:
    """
    Aplica SCD Tipo 2 na tabela Gold.

    - Registros novos: inseridos com registro_ativo=True e data_inicio_vigencia=agora.
    - Registros alterados: o antigo é fechado (registro_ativo=False, data_fim_vigencia=agora)
      e uma nova versão é inserida como ativa.
    - Registros sem alteração: não são tocados.
    """
    now = current_timestamp()
    is_initial = not DeltaTable.isDeltaTable(spark, dst_path)
    start_date = lit("1900-01-01 00:00:00").cast("timestamp") if is_initial else now

    df_new = (
        df_new
        .withColumn("data_inicio_vigencia", start_date)
        .withColumn("data_fim_vigencia", lit(None).cast("timestamp"))
        .withColumn("registro_ativo", lit(True))
        .withColumn("_gold_processed_at", now)
    )

    if not DeltaTable.isDeltaTable(spark, dst_path):
        df_new.write.format("delta").mode("overwrite").save(dst_path)
        print(f"[GOLD SCD2] Tabela criada (primeira carga): {dst_path}")
        return

    tgt = DeltaTable.forPath(spark, dst_path)

    # Condição de mudança: qualquer coluna de negócio diferente
    change_condition = " OR ".join(
        [f"t.{c} <> s.{c}" for c in business_columns]
    )

    # Fecha registros antigos que mudaram
    tgt.alias("t").merge(
        df_new.alias("s"),
        f"t.{primary_key} = s.{primary_key} AND t.registro_ativo = true AND ({change_condition})"
    ).whenMatchedUpdate(set={
        "registro_ativo": lit(False),
        "data_fim_vigencia": now,
    }).execute()

    # Insere novos registros (novos ou atualizados)
    tgt.alias("t").merge(
        df_new.alias("s"),
        f"t.{primary_key} = s.{primary_key} AND t.registro_ativo = true"
    ).whenNotMatchedInsertAll().execute()

    print(f"[GOLD SCD2] Merge SCD2 concluído: {dst_path}")
