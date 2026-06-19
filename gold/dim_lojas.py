from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import IntegerType, StringType

spark = SparkSession.builder.appName("Gold_Dim_Lojas").getOrCreate()

# Leitura da Silver
df_silver = spark.read.format("delta").load("silver/lojas")

# Seleção corrigida usando 'nome_loja' da Silver
df_final = df_silver.select(
    F.col("id_loja").cast(IntegerType()),
    F.col("nome_loja").cast(StringType())
).distinct() \
 .withColumn("sk_loja", F.md5(F.col("id_loja").cast("string")).cast(StringType())) \
 .withColumn("dt_alteracao", F.current_timestamp())

# Seleção final garantindo a ordem das colunas
df_final_ordenado = df_final.select(
    "sk_loja",
    "id_loja",
    "nome_loja",
    "dt_alteracao"
)

df_final_ordenado.write.format("delta").mode("overwrite").save("gold/dim_lojas")
print("Dimensao de Lojas processada com sucesso!")
