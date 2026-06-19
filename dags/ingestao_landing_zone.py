from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

# Importa os módulos que construímos nas issues 2, 3 e 4
from dags.utils.config import TABELAS_ORIGEM
from dags.utils.db_extractor import extract_table_to_csv_buffer
from dags.utils.storage_loader import upload_buffer_to_landing

# ==========================================
# FUNÇÃO PONTE (Executada pelas Tasks)
# ==========================================
def process_table_ingestion(tabela_nome, **kwargs):
    """
    Função wrapper que orquestra as etapas de extração e carga para uma tabela específica.
    """
    print(f"🚀 Iniciando pipeline para a tabela: {tabela_nome}")
    
    # Etapa 1: Extrai do PostgreSQL em formato bruto (CSV em memória)
    csv_buffer = extract_table_to_csv_buffer(tabela_nome)
    
    # Etapa 2: Carrega no MinIO (Bucket Landing)
    caminho_salvo = upload_buffer_to_landing(csv_buffer, tabela_nome)
    
    print(f"🏁 Task finalizada. Caminho no Data Lake: {caminho_salvo}")

# ==========================================
# CONFIGURAÇÕES E DEFINIÇÃO DA DAG
# ==========================================
default_args = {
    'owner': 'engenharia_dados',
    'depends_on_past': False,
    'start_date': datetime(2026, 6, 17), # Data de início
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2, # Tenta 2 vezes caso o banco de dados oscile
    'retry_delay': timedelta(minutes=2),
}

with DAG(
    dag_id='ingestao_postgres_to_minio_landing',
    default_args=default_args,
    description='Pipeline de ingestão das 10 tabelas do E-commerce para a Landing Zone',
    schedule_interval='@daily', 
    catchup=False,
    tags=['ingestao', 'landing', 'postgresql', 'minio']
) as dag:

    # ==========================================
    # GERAÇÃO DINÂMICA DE TASKS
    # ==========================================
    # Para cada tabela mapeada na issue 2, o Airflow criará uma tarefa isolada
    for tabela in TABELAS_ORIGEM:
        PythonOperator(
            task_id=f'ingestao_tabela_{tabela}',
            python_callable=process_table_ingestion,
            op_kwargs={'tabela_nome': tabela},
        )
