"""
dim_clientes.py
---------------
Job Spark: Silver -> Gold (dimensão cliente com SCD Tipo 2).
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from config import get_spark_session, silver_path
from gold.config import gold_path
from gold.utils.scd2 import apply_scd2

BUSINESS_COLUMNS = ["nome_cliente", "cidade", "estado"]


def run(spark=None):
    owns_session = spark is None
    if spark is None:
        spark = get_spark_session("gold_dim_clientes")

    df_clientes = spark.read.format("delta").load(silver_path("clientes"))
    df_enderecos = spark.read.format("delta").load(silver_path("enderecos"))

    df_join = df_clientes.join(
        df_enderecos,
        df_clientes.id_cliente == df_enderecos.id_cliente,
        "left"
    )

    df_dim = df_join.select(
        F.md5(df_clientes.id_cliente.cast("string")).alias("sk_cliente"),
        df_clientes.id_cliente,
        F.col("nome_completo").alias("nome_cliente"),
        df_enderecos.cidade,
        df_enderecos.estado,
    ).distinct()

    apply_scd2(
        spark=spark,
        df_new=df_dim,
        dst_path=gold_path("dim_clientes"),
        primary_key="id_cliente",
        business_columns=BUSINESS_COLUMNS,
    )

    print("[GOLD] dim_clientes processada com SCD2.")

    if owns_session:
        spark.stop()


if __name__ == "__main__":
    run()
