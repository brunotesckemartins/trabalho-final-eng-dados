"""
config.py
---------
Configuração central da camada de consumo analítico (DuckDB).

Banco escolhido: DuckDB
Justificativa: banco embarcado orientado a análise, sem necessidade de serviço
externo adicional. Suporta leitura de tabelas Delta Lake via extensão `delta`
e acesso ao MinIO via extensão `httpfs`, integrando nativamente com a camada Gold.
"""

import os

import duckdb

DUCKDB_PATH = os.getenv("DUCKDB_PATH", "visualization/analytics.duckdb")

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "admin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "adminpassword")

BUCKET_GOLD = "gold"

GOLD_TABLES = [
    "dim_clientes",
    "dim_produtos",
    "dim_lojas",
    "dim_vendedores",
    "dim_metodos_pagamento",
    "fato_vendas",
]


def gold_path(table_name: str) -> str:
    return f"s3://{BUCKET_GOLD}/{table_name}"


def get_connection() -> duckdb.DuckDBPyConnection:
    conn = duckdb.connect(DUCKDB_PATH)
    _configure_s3(conn)
    return conn


def _configure_s3(conn: duckdb.DuckDBPyConnection) -> None:
    endpoint = MINIO_ENDPOINT.replace("http://", "").replace("https://", "")
    use_ssl = str(MINIO_ENDPOINT.startswith("https://")).lower()

    conn.execute("INSTALL httpfs; LOAD httpfs;")
    conn.execute("INSTALL delta; LOAD delta;")
    conn.execute(f"SET s3_endpoint='{endpoint}';")
    conn.execute(f"SET s3_access_key_id='{MINIO_ACCESS_KEY}';")
    conn.execute(f"SET s3_secret_access_key='{MINIO_SECRET_KEY}';")
    conn.execute(f"SET s3_use_ssl={use_ssl};")
    conn.execute("SET s3_url_style='path';")
