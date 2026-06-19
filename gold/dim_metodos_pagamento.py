import sys, os
from pyspark.sql import SparkSession, functions as F
sys.path.append(os.path.abspath(".."))
from utils.scd_utils import aplicar_estrutura_scd

spark = SparkSession.builder.appName("Gold_Dim_Metodos_Pagamento").config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension").config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog").getOrCreate()

df = spark.read.format("parquet").load("silver/metodos_pagamento")
df_final = df.distinct().withColumn("sk_metodo_pagamento", F.md5(F.col("id_metodo_pagamento").cast("string"))).withColumn("dt_alteracao", F.current_timestamp())
df_final = aplicar_estrutura_scd(df_final)
df_final.write.format("delta").mode("overwrite").save("gold/dim_metodos_pagamento")
