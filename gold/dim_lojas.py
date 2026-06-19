from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, TimestampType

spark = SparkSession.builder.appName("Gold_Dim_Lojas").getOrCreate()

schema_dim_lojas = StructType([
    StructField("sk_loja", StringType(), False),
    StructField("id_loja", IntegerType(), False),
    StructField("nome_loja", StringType(), True),
    StructField("dt_alteracao", TimestampType(), False)
])

df_silver = spark.read.format("delta").load("silver/lojas")

df_transformado = df_silver.select(
    F.col("id_loja"),
    F.col("nome").alias("nome_loja")
).distinct()

df_resultado = df_transformado \
    .withColumn("sk_loja", F.md5(F.col("id_loja").cast("string"))) \
    .withColumn("dt_alteracao", F.current_timestamp())

df_final = spark.createDataFrame(df_resultado.rdd, schema=schema_dim_lojas)
df_final.write.format("delta").mode("overwrite").save("gold/dim_lojas")

print("Dimensão de Lojas processada com sucesso!")
