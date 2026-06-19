from pyspark.sql import SparkSession, functions as F

spark = SparkSession.builder.appName("Gold_Dim_Produtos").getOrCreate()

# Leitura e Transformação
df = spark.read.format("parquet").load("silver/produtos")

df_final = df.select(
    F.col("id_produto").cast("int"),
    F.col("nome_produto").cast("string")
).distinct() \
 .withColumn("sk_produto", F.md5(F.col("id_produto").cast("string"))) \
 .withColumn("dt_alteracao", F.current_timestamp())

# Escrita
df_final.write.format("parquet").mode("overwrite").save("gold/dim_produtos")

print("Dimensao de Produtos processada com sucesso!")
