"""
dim_lojas.py
------------
Job Spark: Silver -> Gold (dimensão loja com SCD Tipo 2).
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pyspark.sql import functions as F
from config import get_spark_session, silver_path
from gold.config import gold_path
from gold.utils.scd2 import apply_scd2

BUSINESS_COLUMNS = ["nome_loja", "estado_loja"]


def run(spark=None):
    owns_session = spark is None
    if spark is None:
        spark = get_spark_session("gold_dim_lojas")

    df = spark.read.format("delta").load(silver_path("lojas"))

    df_dim = df.select(
        F.md5(F.col("id_loja").cast("string")).alias("sk_loja"),
        F.col("id_loja"),
        F.col("nome_loja"),
        F.col("estado_loja"),
    ).distinct()

    apply_scd2(
        spark=spark,
        df_new=df_dim,
        dst_path=gold_path("dim_lojas"),
        primary_key="id_loja",
        business_columns=BUSINESS_COLUMNS,
    )

    print("[GOLD] dim_lojas processada com SCD2.")

    if owns_session:
        spark.stop()


if __name__ == "__main__":
    run()
