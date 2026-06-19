"""
dim_produtos.py
---------------
Job Spark: Silver -> Gold (dimensão produto com SCD Tipo 2).
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pyspark.sql import functions as F
from config import get_spark_session, silver_path
from gold.config import gold_path
from gold.utils.scd2 import apply_scd2

BUSINESS_COLUMNS = ["nome_produto", "preco_base", "nome_categoria"]


def run(spark=None):
    owns_session = spark is None
    if spark is None:
        spark = get_spark_session("gold_dim_produtos")

    df_produtos = spark.read.format("delta").load(silver_path("produtos"))
    df_categorias = spark.read.format("delta").load(silver_path("categorias"))

    df_join = df_produtos.join(
        df_categorias,
        df_produtos.id_categoria == df_categorias.id_categoria,
        "left"
    )

    df_dim = df_join.select(
        F.md5(df_produtos.id_produto.cast("string")).alias("sk_produto"),
        df_produtos.id_produto,
        F.col("nome_produto"),
        F.col("preco_base"),
        F.col("nome_categoria"),
    ).distinct()

    apply_scd2(
        spark=spark,
        df_new=df_dim,
        dst_path=gold_path("dim_produtos"),
        primary_key="id_produto",
        business_columns=BUSINESS_COLUMNS,
    )

    print("[GOLD] dim_produtos processada com SCD2.")

    if owns_session:
        spark.stop()


if __name__ == "__main__":
    run()
