from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, DoubleType, TimestampType

# 1. Iniciar a Sessão do Spark
spark = SparkSession.builder \
    .appName("Gold_Dim_Produtos") \
    .getOrCreate()

# CRITÉRIO DE ACEITE: Esquema definido explicitamente
schema_dim_produtos = StructType([
    StructField("sk_produto", StringType(), False),      # Chave Substituta (Surrogate Key)
    StructField("id_produto", IntegerType(), False),     # Chave de Negócio (Business Key)
    StructField("nome_produto", StringType(), True),
    StructField("preco_base", DoubleType(), True),
    StructField("nome_categoria", StringType(), True),
    StructField("dt_alteracao", TimestampType(), False)
])

# DEPENDÊNCIA: Carregar dados da Camada Silver
df_produtos_silver = spark.read.format("delta").load("silver/produtos")
df_categorias_silver = spark.read.format("delta").load("silver/categorias")

# Fazer o Join para trazer o nome da categoria para dentro da dimensão de produtos
df_join = df_produtos_silver.join(
    df_categorias_silver, 
    df_produtos_silver.id_categoria == df_categorias_silver.id_categoria, 
    "left"
)

# CRITÉRIO DE ACEITE: Identificar chave de negócio (id_produto) e selecionar atributos
df_transformado = df_join.select(
    F.col("id_produto"),
    F.col("nome").alias("nome_produto"),
    F.col("preco").alias("preco_base"),
    F.col("nome_categoria")
).distinct()

# CRITÉRIO DE ACEITE: Chave Substituta gerada via Hash MD5 a partir da chave de negócio
df_resultado = df_transformado \
    .withColumn("sk_produto", F.md5(F.col("id_produto").cast("string"))) \
    .withColumn("dt_alteracao", F.current_timestamp())

# Aplicar o esquema definido rigidamente
df_dim_produtos_final = spark.createDataFrame(df_resultado.rdd, schema=schema_dim_produtos)

# CRITÉRIO DE ACEITE: Dados carregados corretamente no Delta Lake
df_dim_produtos_final.write \
    .format("delta") \
    .mode("overwrite") \
    .save("gold/dim_produtos")

print("Dimensão de Produtos processada com sucesso!")
