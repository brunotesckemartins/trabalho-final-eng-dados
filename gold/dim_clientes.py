from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, TimestampType

# 1. Iniciar a Sessão do Spark
spark = SparkSession.builder \
    .appName("Gold_Dim_Clientes") \
    .getOrCreate()

# CRITÉRIO DE ACEITE: Esquema definido explicitamente
schema_dim_clientes = StructType([
    StructField("sk_cliente", StringType(), False),      # Chave Substituta (Surrogate Key)
    StructField("id_cliente", IntegerType(), False),     # Chave de Negócio (Business Key)
    StructField("nome_cliente", StringType(), True),
    StructField("cidade", StringType(), True),
    StructField("estado", StringType(), True),
    StructField("dt_alteracao", TimestampType(), False)
])

# DEPENDÊNCIA: Carregar dados da Camada Silver
# (Nota: Ajuste os caminhos abaixo se a pasta silver de vocês estiver em outro local)
df_clientes_silver = spark.read.format("delta").load("silver/clientes")
df_enderecos_silver = spark.read.format("delta").load("silver/enderecos")

# Fazer o Join para enriquecer o cliente com o endereço dele
df_join = df_clientes_silver.join(
    df_enderecos_silver, 
    df_clientes_silver.id_endereco == df_enderecos_silver.id_endereco, 
    "left"
)

# CRITÉRIO DE ACEITE: Identificar chave de negócio e estruturar dados
df_transformado = df_join.select(
    F.col("id_cliente").alias("id_cliente"), 
    F.col("nome").alias("nome_cliente"),
    F.col("cidade"),
    F.col("estado")
).distinct()

# CRITÉRIO DE ACEITE: Chave Substituta gerada via Hash MD5
df_resultado = df_transformado \
    .withColumn("sk_cliente", F.md5(F.col("id_cliente").cast("string"))) \
    .withColumn("dt_alteracao", F.current_timestamp())

# Aplicar o esquema definido rigidamente
df_dim_clientes_final = spark.createDataFrame(df_resultado.rdd, schema=schema_dim_clientes)

# CRITÉRIO DE ACEITE: Dados carregados corretamente no Delta Lake
df_dim_clientes_final.write \
    .format("delta") \
    .mode("overwrite") \
    .save("gold/dim_clientes")

print("Dimensão de Clientes processada com sucesso!")
