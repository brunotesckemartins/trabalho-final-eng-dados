"""
read_silver.py
--------------
Utilitário base para leitura da camada Silver na Gold.
"""

import sys
sys.path.insert(0, '/home/elison/trabalho-final-eng-dados')

from pyspark.sql import DataFrame, SparkSession
from config import silver_path


def read_silver(table_name: str, spark: SparkSession) -> DataFrame:
    src = silver_path(table_name)
    print(f"[GOLD] Lendo Silver '{table_name}': {src}")
    return spark.read.format("delta").load(src)


def validate_not_empty(df: DataFrame, table_name: str) -> None:
    count = df.count()
    if count == 0:
        raise ValueError(
            f"[GOLD] Tabela Silver '{table_name}' está vazia. "
            f"Verifique se a Silver foi processada corretamente."
        )
    print(f"[GOLD] '{table_name}': {count} linha(s) disponível(eis) na Silver.")


def read_silver_validated(table_name: str, spark: SparkSession) -> DataFrame:
    df = read_silver(table_name, spark)
    validate_not_empty(df, table_name)
    return df
