"""
dim_vendedores.py
-----------------
Job Spark: Silver -> Gold (dimensão vendedor com SCD Tipo 2).
"""

import sys
sys.path.insert(0, '/home/elison/trabalho-final-eng-dados')

from pyspark.sql import functions as F
from config import get_spark_session, silver_path
from gold.config import gold_path
from gold.utils.scd2 import apply_scd2

BUSINESS_COLUMNS = ["nome_vendedor", "nome_loja"]


def run(spark=None):
    owns_session = spark is None
    if spark is None:
        spark = get_spark_session("gold_dim_vendedores")

    df_vendedores = spark.read.format("delta").load(silver_path("vendedores"))
    df_lojas = spark.read.format("delta").load(silver_path("lojas"))

    df_join = df_vendedores.join(
        df_lojas,
        df_vendedores.id_loja == df_lojas.id_loja,
        "left"
    )

    df_dim = df_join.select(
        F.md5(df_vendedores.id_vendedor.cast("string")).alias("sk_vendedor"),
        df_vendedores.id_vendedor,
        F.col("nome_vendedor"),
        df_lojas.nome_loja,
    ).distinct()

    apply_scd2(
        spark=spark,
        df_new=df_dim,
        dst_path=gold_path("dim_vendedores"),
        primary_key="id_vendedor",
        business_columns=BUSINESS_COLUMNS,
    )

    print("[GOLD] dim_vendedores processada com SCD2.")

    if owns_session:
        spark.stop()


if __name__ == "__main__":
    run()
