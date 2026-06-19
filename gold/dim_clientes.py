import sys
import os

# Adiciona a raiz do projeto ao path do Python para encontrar a pasta 'utils'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import sys
import os
import shutil
from pyspark.sql import SparkSession, functions as F

# Inicialização da Sessão Spark com extensões para Delta
spark = SparkSession.builder \
    .appName("Gold_Dim_Clientes") \
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
    .getOrCreate()

# Caminho de destino
tabela = "clientes"
caminho_gold = f"gold/dim_{tabela}"

# Limpeza preventiva: remove a pasta existente para garantir que o Delta não se perca no log
if os.path.exists(caminho_gold):
    shutil.rmtree(caminho_gold)

# Leitura da camada Silver
df = spark.read.format("parquet").load(f"silver/{tabela}")

# Transformações (MD5 e coluna de controle)
df_final = df.distinct() \
    .withColumn("sk_cliente", F.md5(F.col("id_cliente").cast("string"))) \
    .withColumn("dt_alteracao", F.current_timestamp())

# Aplicação da estrutura SCD (importado do seu utilitário)
sys.path.append(os.path.abspath(".."))
from utils.scd_utils import aplicar_estrutura_scd
df_final = aplicar_estrutura_scd(df_final)

# Escrita em formato Delta
df_final.write.format("delta").mode("overwrite").save(caminho_gold)

print(f"Processamento de {tabela} concluído com sucesso.")
