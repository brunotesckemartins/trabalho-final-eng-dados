from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, TimestampType

spark = SparkSession.builder.appName("Gold_Dim_Vendedores").getOrCreate()

schema_dim_vendedores = StructType([
    StructField("sk_vendedor", StringType(), False),
    StructField("id_vendedor", IntegerType(), False),
    StructField("nome_vendedor", StringType(), True),
    StructField("dt_alteracao", TimestampType(), False)
])

df_silver = spark.read.format("delta").load("silver/vendedores")

df_transformado = df_silver.select(
    F.col("id_vendedor"),
    F.col("nome").alias("nome_vendedor")
).distinct()

df_resultado = df_transformado \
    .withColumn("sk_vendedor", F.md5(F.col("id_vendedor").cast("string"))) \
    .withColumn("dt_alteracao", F.current_timestamp())

df_final = spark.createDataFrame(df_resultado.rdd, schema=schema_dim_vendedores)
df_final.write.format("delta").mode("overwrite").save("gold/dim_vendedores")

print("Dimensão de Vendedores processada com sucesso!")
