"""
extract_to_landing.py
----------------------
Extrai as tabelas do PostgreSQL e salva como CSV na Landing Zone do MinIO.
"""

import pandas as pd
from sqlalchemy import create_engine
import boto3
from io import StringIO

DB_USER = "postgres"
DB_PASS = "admin123"
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "ecommerce_db"

MINIO_ENDPOINT = "http://localhost:9000"
MINIO_ACCESS_KEY = "admin"
MINIO_SECRET_KEY = "adminpassword"
BUCKET_LANDING = "landing"

TABELAS = [
    "categorias", "lojas", "metodos_pagamento", "clientes",
    "enderecos", "produtos", "vendedores", "pedidos",
    "itens_pedido", "pagamentos_pedido"
]

engine = create_engine(f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}")

s3 = boto3.client(
    "s3",
    endpoint_url=MINIO_ENDPOINT,
    aws_access_key_id=MINIO_ACCESS_KEY,
    aws_secret_access_key=MINIO_SECRET_KEY,
)

print(" Iniciando extração Postgres -> Landing Zone (MinIO)...\n")

for tabela in TABELAS:
    print(f"⏳ Extraindo '{tabela}'...")
    df = pd.read_sql(f"SELECT * FROM {tabela}", engine)
    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=False)
    s3.put_object(
        Bucket=BUCKET_LANDING,
        Key=f"{tabela}/{tabela}.csv",
        Body=csv_buffer.getvalue()
    )
    print(f"✅ '{tabela}': {len(df)} linhas -> s3://landing/{tabela}/{tabela}.csv")

print("\n✅ Extração concluída!")
