"""
ingestao_landing_zone.py
------------------------
DAG principal do pipeline medalhão end-to-end.

Fluxo por tabela (execução paralela entre tabelas):
  1. ingestao_landing_<tabela>  — extrai do PostgreSQL e sobe CSV para MinIO/landing
  2. processa_bronze_<tabela>   — Spark: Landing (CSV) → Bronze (Delta, append)
  3. processa_silver_<tabela>   — Spark: Bronze → Silver (Delta, upsert tipado)

Após todas as Silvers:
  4. processa_gold_dimensoes — Spark: Silver → Gold dimensões (SCD Tipo 2)
  5. processa_gold_fatos     — Spark: Silver + Gold dims → fato_vendas

Agendamento: @daily (sem catchup).
Retentativas: 2x com intervalo de 2 minutos.
"""

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

from dags.utils.config import TABELAS_ORIGEM
from dags.utils.db_extractor import extract_table_to_csv_buffer
from dags.utils.storage_loader import upload_buffer_to_landing

if not TABELAS_ORIGEM:
    raise ValueError(
        "TABELAS_ORIGEM está vazia em dags/utils/config.py. "
        "Verifique a configuração antes de carregar a DAG."
    )


def process_table_ingestion(tabela_nome, **kwargs):
    print(f"Iniciando ingestão para a tabela: {tabela_nome}")
    csv_buffer = extract_table_to_csv_buffer(tabela_nome)
    caminho_salvo = upload_buffer_to_landing(csv_buffer, tabela_nome)
    print(f"Ingestão finalizada. Data Lake: {caminho_salvo}")


default_args = {
    'owner': 'engenharia_dados',
    'depends_on_past': False,
    'start_date': datetime(2026, 6, 17),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=2),
}

with DAG(
    dag_id='orquestracao_medalhao_end_to_end',
    default_args=default_args,
    description='Pipeline completo: Origem SQL -> Landing -> Bronze -> Silver -> Gold',
    schedule_interval='@daily', 
    catchup=False,
    tags=['ingestao', 'landing', 'bronze', 'silver', 'gold']
) as dag:

    # Lista para guardarmos as referências das tasks da camada Silver
    silver_tasks = []

    for tabela in TABELAS_ORIGEM:
        # 1. Task de Ingestão (Landing)
        task_landing = PythonOperator(
            task_id=f'ingestao_landing_{tabela}',
            python_callable=process_table_ingestion,
            op_kwargs={'tabela_nome': tabela},
        )

        # 2. Task da Camada Bronze (Spark)
        task_bronze = BashOperator(
            task_id=f'processa_bronze_{tabela}',
            # O BashOperator invoca o job Spark via terminal, passando a tabela como argumento
            bash_command=f'spark-submit /opt/airflow/pipeline/landing_to_bronze.py --table {tabela}'
        )

        # 3. Task da Camada Silver (Spark)
        task_silver = BashOperator(
            task_id=f'processa_silver_{tabela}',
            bash_command=f'spark-submit /opt/airflow/pipeline/bronze_to_silver.py --table {tabela}'
        )

        # Define a ordem de execução para esta tabela específica
        task_landing >> task_bronze >> task_silver
        
        # Adiciona a task silver na lista para as dependências da Gold
        silver_tasks.append(task_silver)

    # ==========================================
    # CAMADA GOLD (Executada apenas quando TODAS as Silvers terminarem)
    # ==========================================
    task_gold_dimensoes = BashOperator(
        task_id='processa_gold_dimensoes',
        bash_command='spark-submit /opt/airflow/gold/run_dimensions.py'
    )

    task_gold_fatos = BashOperator(
        task_id='processa_gold_fatos',
        bash_command='spark-submit /opt/airflow/gold/facts/fato_vendas.py'
    )

    # Faz com que a processa_gold_dimensoes aguarde a conclusão de todas as tabelas na Silver
    for task in silver_tasks:
        task >> task_gold_dimensoes

    # As fatos só podem ser processadas APÓS o carregamento (SCD2) das dimensões
    task_gold_dimensoes >> task_gold_fatos
    