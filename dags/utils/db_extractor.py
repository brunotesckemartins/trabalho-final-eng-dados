"""
Módulo responsável pela extração de dados da origem relacional.
"""

import pandas as pd
from sqlalchemy import create_engine
from io import BytesIO

# Importa as configurações do nosso próprio pacote
from dags.utils.config import DB_USER, DB_PASS, DB_HOST, DB_PORT, DB_NAME

def extract_table_to_csv_buffer(table_name: str) -> BytesIO:
    """
    Conecta no banco PostgreSQL de origem, extrai a tabela solicitada 
    e retorna os dados em um buffer de memória no formato bruto original (CSV).
    """
    print(f"🔌 Conectando ao PostgreSQL para extrair: {table_name}...")
    
    # Monta a string de conexão baseada nas variáveis de ambiente
    engine_url = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    engine = create_engine(engine_url)
    
    try:
        # Extrai os dados utilizando Pandas
        query = f"SELECT * FROM {table_name};"
        df = pd.read_sql_query(query, engine)
        print(f"📊 Dados extraídos com sucesso. Linhas processadas: {len(df)}")
        
        # Converte o DataFrame para CSV em memória (Buffer) para não gravar em disco local
        csv_buffer = BytesIO()
        df.to_csv(csv_buffer, index=False)
        
        # Reseta o ponteiro do buffer para o início (essencial para a leitura posterior do S3)
        csv_buffer.seek(0)
        
        return csv_buffer
        
    except Exception as e:
        print(f"❌ Erro grave na extração da tabela {table_name}: {e}")
        raise e
    finally:
        # Garante que a conexão com o banco seja fechada mesmo se houver erro
        engine.dispose()
