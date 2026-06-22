"""
Módulo responsável pela comunicação e carga de dados no Object Storage (MinIO/S3).
"""

import boto3
from io import BytesIO

# Importa as configurações do nosso próprio pacote
from dags.utils.config import (
    MINIO_ENDPOINT, 
    MINIO_ACCESS_KEY, 
    MINIO_SECRET_KEY, 
    MINIO_BUCKET_LANDING
)

def get_s3_client():
    """
    Instancia e retorna um cliente boto3 configurado para o MinIO local.
    """
    return boto3.client(
        's3',
        endpoint_url=MINIO_ENDPOINT,
        aws_access_key_id=MINIO_ACCESS_KEY,
        aws_secret_access_key=MINIO_SECRET_KEY
    )

def upload_buffer_to_landing(csv_buffer: BytesIO, table_name: str) -> str:
    """
    Recebe um buffer de memória (CSV) e faz o upload para o bucket da Landing Zone.
    Retorna o caminho do arquivo (Object Key) salvo no storage.
    """
    s3_client = get_s3_client()
    
    # Define a estrutura de pastas no bucket: nome_da_tabela/arquivo.csv
    object_key = f"{table_name}/{table_name}_raw.csv"
    
    print(f"☁️ Iniciando upload para o Data Lake (Bucket: {MINIO_BUCKET_LANDING} | Path: {object_key})...")
    
    try:
        # Faz o upload usando o upload_fileobj, ideal para streams em memória
        s3_client.upload_fileobj(
            Fileobj=csv_buffer,
            Bucket=MINIO_BUCKET_LANDING,
            Key=object_key
        )
        print(f"✅ Upload concluído com sucesso: {object_key}")
        return object_key
        
    except Exception as e:
        print(f"❌ Erro ao enviar os dados da tabela {table_name} para o MinIO: {e}")
        raise e
