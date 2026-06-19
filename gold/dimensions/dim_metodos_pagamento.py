"""
dim_metodos_pagamento.py
------------------------
Job Spark: Silver -> Gold (dimensão método de pagamento com SCD Tipo 2).
"""

import sys
sys.path.insert(0, '/home/elison/trabalho-final-eng-dados')

from pyspark.sql import functions as F
from config import get_spark_session, silver_path
from gold.config import gold_path
from gold.utils.scd2 import apply_scd2

BUSINESS_COLUMNS = ["tipo_pagamento"]


def run(spark=None):
    owns_session = spark is None
    if spark is None:
        spark = get_spark_session("gold_dim_metodos_pagamento")

    df = spark.read.format("delta").load(silver_path("metodos_pagamento"))

    df_dim = df.select(
        F.md5(F.col("id_metodo").cast("string")).alias("sk_metodo"),
        F.col("id_metodo"),
        F.col("tipo_pagamento"),
    ).distinct()

    apply_scd2(
        spark=spark,
        df_new=df_dim,
        dst_path=gold_path("dim_metodos_pagamento"),
        primary_key="id_metodo",
        business_columns=BUSINESS_COLUMNS,
    )

    print("[GOLD] dim_metodos_pagamento processada com SCD2.")

    if owns_session:
        spark.stop()


if __name__ == "__main__":
    run()
