from pyspark.sql import SparkSession, functions as F
from pyspark.sql.types import IntegerType, StringType

spark = SparkSession.builder.appName("Gold_Dim_Vendedores").getOrCreate()
df_silver = spark.read.format("delta").load("silver/vendedores")

df_final = df_silver.select(
    F.col("id_vendedor").cast(IntegerType()),
    F.col("nome_vendedor").cast(StringType())
).distinct() \
 .withColumn("sk_vendedor", F.md5(F.col("id_vendedor").cast("string")).cast(StringType())) \
 .withColumn("dt_alteracao", F.current_timestamp())

df_final.select("sk_vendedor", "id_vendedor", "nome_vendedor", "dt_alteracao").write.format("delta").mode("overwrite").save("gold/dim_vendedores")
print("Dimensao de Vendedores processada com sucesso!")
