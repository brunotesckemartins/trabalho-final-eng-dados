"""
change_detector.py
------------------
Mecanismo de detecção de alterações para SCD Tipo 2.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.functions import col
from delta.tables import DeltaTable


def detect_changes(
    spark: SparkSession,
    df_new: DataFrame,
    dst_path: str,
    primary_key: str,
    business_columns: list,
) -> dict:

    if not DeltaTable.isDeltaTable(spark, dst_path):
        print("[CHANGE DETECTOR] Tabela Gold não existe — todos os registros são novos.")
        return {
            "novos": df_new,
            "alterados": spark.createDataFrame([], df_new.schema),
            "sem_alteracao": spark.createDataFrame([], df_new.schema),
        }

    df_gold = (
        spark.read.format("delta").load(dst_path)
        .filter(col("registro_ativo") == True)
        .select([primary_key] + business_columns)
    )

    df_novos = df_new.join(df_gold, on=primary_key, how="left_anti")

    df_joined = df_new.alias("new").join(
        df_gold.alias("gold"), on=primary_key, how="inner"
    )

    change_expr = None
    for c in business_columns:
        cond = col(f"new.{c}") != col(f"gold.{c}")
        change_expr = cond if change_expr is None else change_expr | cond

    df_alterados = df_joined.filter(change_expr).select(
        [col(f"new.{c}") for c in df_new.columns]
    )
    df_sem_alteracao = df_joined.filter(~change_expr).select(
        [col(f"new.{c}") for c in df_new.columns]
    )

    print(f"[CHANGE DETECTOR] Novos: {df_novos.count()} | "
          f"Alterados: {df_alterados.count()} | "
          f"Sem alteração: {df_sem_alteracao.count()}")

    return {
        "novos": df_novos,
        "alterados": df_alterados,
        "sem_alteracao": df_sem_alteracao,
    }
