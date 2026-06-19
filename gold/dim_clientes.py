from pyspark.sql import SparkSession, functions as F

# Inicialização da sessão Spark
spark = SparkSession.builder \
    .appName("Gold_Dim_Clientes") \
    .getOrCreate()

# Leitura da camada Silver
df = spark.read.format("parquet").load("silver/clientes")

# Transformação: Selecionando a coluna correta 'nome_completo' e renomeando para 'nome_cliente'
df_final = df.select(
    F.col("id_cliente").cast("int"),
    F.col("nome_completo").alias("nome_cliente").cast("string")
).distinct() \
 .withColumn("sk_cliente", F.md5(F.col("id_cliente").cast("string"))) \
 .withColumn("dt_alteracao", F.current_timestamp())

# Escrita na camada Gold
df_final.write.format("parquet").mode("overwrite").save("gold/dim_clientes")

print("Dimensao de Clientes processada com sucesso!")
