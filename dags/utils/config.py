"""
Módulo de centralização de configurações e credenciais.
Evita hardcode no script principal da DAG.
"""

# ==========================================
# CREDENCIAIS DO BANCO DE ORIGEM (POSTGRESQL)
# ==========================================
# Aponta para o container 'postgres-origem' na rede do Docker
DB_HOST = "postgres-origem" 
DB_USER = "postgres"
DB_PASS = "admin123"
DB_PORT = "5432"
DB_NAME = "ecommerce_db"

# ==========================================
# CREDENCIAIS DO DATA LAKE (MINIO / S3)
# ==========================================
# Aponta para o container 'minio' na rede do Docker
MINIO_ENDPOINT = "http://minio:9000"
MINIO_ACCESS_KEY = "admin"
MINIO_SECRET_KEY = "adminpassword"
MINIO_BUCKET_LANDING = "landing"

# ==========================================
# METADADOS DE INGESTÃO
# ==========================================
# Lista exata das 10 tabelas criadas no banco sintético
TABELAS_ORIGEM = [
    "categorias", 
    "produtos", 
    "clientes", 
    "enderecos", 
    "lojas", 
    "vendedores", 
    "metodos_pagamento", 
    "pedidos", 
    "itens_pedido", 
    "pagamentos_pedido"
]
