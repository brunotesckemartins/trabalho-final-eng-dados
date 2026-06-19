"""
fato_vendas.py
--------------
Pipeline principal de processamento da Tabela Fato de Vendas e Pagamentos para a camada Gold.
"""

import sys
import os
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import col

# Adiciona o diretório raiz ao PYTHONPATH para acessar as configurações base
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import get_spark_session
from gold.config import gold_path
from gold.read_silver import read_silver
from gold.utils.checkpoint_manager import get_last_checkpoint, save_checkpoint


def read_incremental_silver(spark: SparkSession, table_name: str, watermark: str) -> DataFrame:
    """
    [Issue #59] Lê a camada Silver e aplica o filtro incremental baseado no checkpoint.
    Garante que só traremos registros processados após a última execução desta fato.
    """
    df = read_silver(table_name, spark)
    
    # O campo _silver_processed_at foi gerado no script bronze_to_silver.py
    df_incremental = df.filter(col("_silver_processed_at") > watermark)
    return df_incremental


def run() -> None:
    # 1. Setup do PySpark (reaproveitando config.py)
    spark = get_spark_session("fato_vendas")
    
    # Caminho do checkpoint desta fato no MinIO
    checkpoint_file = gold_path("checkpoints/fato_vendas")
    
    # 2. Resgata a data do último processamento bem-sucedido
    last_watermark = get_last_checkpoint(spark, checkpoint_file)
    print(f"[FATO VENDAS] Iniciando extração. Último checkpoint (watermark): {last_watermark}")
    
    # 3. Extração Incremental da Silver (Issue #59)
    df_pedidos = read_incremental_silver(spark, "pedidos", last_watermark)
    df_itens = read_incremental_silver(spark, "itens_pedido", last_watermark)
    df_pagamentos = read_incremental_silver(spark, "pagamentos_pedido", last_watermark)
    
    count_pedidos = df_pedidos.count()
    if count_pedidos == 0:
        print("[FATO VENDAS] Nenhuma alteração nova detectada em 'pedidos'. Encerrando carga incremental cedo.")
        spark.stop()
        return
        
    print(f"[FATO VENDAS] Extração incremental concluída. Pedidos processados na Silver pós-checkpoint: {count_pedidos}")


if __name__ == "__main__":
    run()
