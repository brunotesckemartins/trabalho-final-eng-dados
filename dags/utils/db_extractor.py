"""
Módulo responsável pela extração de dados da origem relacional
e validação primária de qualidade (Data Quality).
"""

import pandas as pd
from sqlalchemy import create_engine
from io import BytesIO

from dags.utils.config import DB_USER, DB_PASS, DB_HOST, DB_PORT, DB_NAME

def extract_table_to_csv_buffer(table_name: str) -> BytesIO:
    """
    Conecta no banco PostgreSQL, extrai a tabela e valida o volume de registros.
    Retorna os dados em buffer de memória (CSV) ou interrompe em caso de anomalia.
    """
    print(f"🔌 [Extrator] Conectando ao PostgreSQL para extrair a tabela: {table_name}")
    
    engine_url = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    engine = create_engine(engine_url)
    
    try:
        query = f"SELECT * FROM {table_name};"
        df = pd.read_sql_query(query, engine)
        
        # ==========================================
        # DATA QUALITY CHECK (Validação de Volume)
        # ==========================================
        if df.empty:
            error_msg = f"A tabela '{table_name}' está vazia no banco de origem. Abortando ingestão para evitar arquivos inúteis."
            print(f"⚠️ [Extrator] Falha de Qualidade: {error_msg}")
            raise ValueError(error_msg)
            
        print(f"📊 [Extrator] Validação concluída. Linhas processadas: {len(df)}")
        
        csv_buffer = BytesIO()
        df.to_csv(csv_buffer, index=False)
        csv_buffer.seek(0)
        
        return csv_buffer
        
    except Exception as e:
        print(f"❌ [Extrator] Erro durante a operação na tabela {table_name}: {str(e)}")
        raise e
    finally:
        engine.dispose()
        print(f"🔒 [Extrator] Conexão com o banco encerrada.")
