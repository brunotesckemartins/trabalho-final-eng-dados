from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import pandas as pd
import sqlite3 

# MOCKS (Aguardando Issues 1 e 2)

DB_CONNECTION_STRING = "mock_database.db" 

TABELAS_ORIGEM = [
    "clientes", "produtos", "vendas", "vendedores", "lojas", 
    "estoque", "fornecedores", "categorias", "pagamentos", "entregas"
]

LANDING_ZONE_PATH = "/tmp/data_lake/landing/"

# Função de extração (Formato bruto original)

def extract_and_load_to_landing(tabela_nome, **kwargs):
    """
    Conecta no banco SQL, extrai a tabela e salva como CSV na landing zone.
    Atende ao requisito de manter o formato bruto original para SQL (CSV).
    """
    print(f"Iniciando extração da tabela: {tabela_nome}")
    
    conn = sqlite3.connect(DB_CONNECTION_STRING) 
    
    try:
        query = f"SELECT * FROM {tabela_nome};"
        df = pd.read_sql_query(query, conn)
        
        # Salva o arquivo no formato CSV exigido pelo projeto

        file_path = f"{LANDING_ZONE_PATH}{tabela_nome}_raw.csv"
        df.to_csv(file_path, index=False)
        print(f"Sucesso. Dados de '{tabela_nome}' gravados em: {file_path}")
        
    except Exception as e:
        print(f"Erro ao extrair a tabela {tabela_nome}: {e}")
        raise e
    finally:
        conn.close()

# Definição da DAG da orquestração

default_args = {
    'owner': 'seu_nome',
    'depends_on_past': False,
    'start_date': datetime(2026, 6, 9),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# O agendamento é gerenciado 100% pelo Airflow, sem cron ou task scheduler do SO

with DAG(
    dag_id='ingestao_sql_to_landing_csv',
    default_args=default_args,
    description='Pipeline de ingestão de dados SQL para a Landing Zone em CSV',
    schedule_interval='@daily', 
    catchup=False,
) as dag:

    # Geração dinâmica de tasks

    for tabela in TABELAS_ORIGEM:
        task_extract = PythonOperator(
            task_id=f'extract_{tabela}_to_landing',
            python_callable=extract_and_load_to_landing,
            op_kwargs={'tabela_nome': tabela},
        )
