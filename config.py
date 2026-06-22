"""
config.py
---------
Configuração central do módulo de transformação (Bronze/Silver).


"""

import os

from pyspark.sql import SparkSession

# ---------------------------------------------------------------------------
# Conexão com o MinIO (Object Storage / Data Lake)
# ---------------------------------------------------------------------------
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "admin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "adminpassword")

# Se os scripts rodarem DENTRO da mesma rede Docker do MinIO (ex: chamados
# pelo container do orquestrador), troque o endpoint para "http://minio:9000".

# ---------------------------------------------------------------------------
# Buckets da arquitetura medalhão (já criados pelo serviço minio-init)
# ---------------------------------------------------------------------------
BUCKET_LANDING = "landing"
BUCKET_BRONZE = "bronze"
BUCKET_SILVER = "silver"

# Versões dos pacotes Maven usados para Delta Lake + acesso S3A.
# Mantidas centralizadas aqui para facilitar upgrade futuro.
_DELTA_VERSION = "3.2.0"
_HADOOP_AWS_VERSION = "3.3.4"
_AWS_SDK_VERSION = "1.12.262"


def get_spark_session(app_name: str) -> SparkSession:
    """
    Cria (ou recupera) uma SparkSession configurada com:
      - Delta Lake habilitado (catálogo + extensões SQL).
      - Conector S3A apontando para o MinIO, em modo path-style
        (obrigatório para MinIO, que não resolve bucket como subdomínio).

    Observação: no primeiro uso, o Spark fará o download dos jars listados
    em spark.jars.packages via Maven Central — é necessário acesso à
    internet na primeira execução (os jars ficam em cache local depois,
    em ~/.ivy2 ou ~/.m2).
    """
    builder = (
        SparkSession.builder.appName(app_name)
        .config(
            "spark.jars.packages",
            f"io.delta:delta-spark_2.12:{_DELTA_VERSION},"
            f"org.apache.hadoop:hadoop-aws:{_HADOOP_AWS_VERSION},"
            f"com.amazonaws:aws-java-sdk-bundle:{_AWS_SDK_VERSION}",
        )
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
        .config(
            "spark.sql.catalog.spark_catalog",
            "org.apache.spark.sql.delta.catalog.DeltaCatalog",
        )
        .config("spark.hadoop.fs.s3a.endpoint", MINIO_ENDPOINT)
        .config("spark.hadoop.fs.s3a.access.key", MINIO_ACCESS_KEY)
        .config("spark.hadoop.fs.s3a.secret.key", MINIO_SECRET_KEY)
        .config("spark.hadoop.fs.s3a.path.style.access", "true")
        .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false")
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
        # Volume pequeno (~50k linhas no total) -> não precisa de muitos shuffles
        .config("spark.sql.shuffle.partitions", "4")
    )
    return builder.getOrCreate()


def landing_path(table_name: str) -> str:
    """Retorna o caminho S3A do CSV raw de uma tabela na Landing Zone.

    Convenção: s3a://landing/<tabela>/<tabela>_raw.csv
    Sufixo _raw.csv é o padrão adotado pelo storage_loader da DAG.
    """
    return f"s3a://{BUCKET_LANDING}/{table_name}/{table_name}_raw.csv"


def bronze_path(table_name: str) -> str:
    return f"s3a://{BUCKET_BRONZE}/{table_name}"


def silver_path(table_name: str) -> str:
    return f"s3a://{BUCKET_SILVER}/{table_name}"
