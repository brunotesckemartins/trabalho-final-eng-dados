"""
fato_vendas.py
--------------
Pipeline principal de processamento da Tabela Fato de Vendas para a camada Gold.
"""

import sys
import os
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql import functions as F

# Adiciona o diretório raiz ao PYTHONPATH
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, root_dir)

from config import get_spark_session
from gold.config import gold_path
from gold.read_silver import read_silver
from gold.utils.checkpoint_manager import get_last_checkpoint, save_checkpoint


def read_incremental_silver(spark: SparkSession, table_name: str, watermark: str) -> DataFrame:
    """
    [Issue #59] Lê a camada Silver e aplica filtro incremental.
    """
    df = read_silver(table_name, spark)
    return df.filter(F.col("_silver_processed_at") > watermark)


def join_scd2(df_fact: DataFrame, df_dim: DataFrame, fk_col: str, sk_col: str) -> DataFrame:
    """
    [Issue #60] Realiza o JOIN temporal (SCD2) entre a Fato e a Dimensão.
    Garante que a métrica se conecte à versão exata da dimensão na data do evento.
    """
    # Renomeando as colunas da dimensão para evitar colisão, mantendo o SK limpo
    dim_cols = [c for c in df_dim.columns if c not in [fk_col, "data_inicio_vigencia", "data_fim_vigencia", "registro_ativo", "_gold_processed_at"]]
    
    cond = [
        df_fact[fk_col] == df_dim[fk_col],
        df_fact["data_pedido"] >= df_dim["data_inicio_vigencia"],
        df_dim["data_fim_vigencia"].isNull() | (df_fact["data_pedido"] <= df_dim["data_fim_vigencia"])
    ]
    
    df_joined = df_fact.join(df_dim, cond, how="left")
    
    # Descarta colunas técnicas do SCD2 e a FK original vinda da dimensão
    cols_to_drop = ["data_inicio_vigencia", "data_fim_vigencia", "registro_ativo", "_gold_processed_at"]
    df_joined = df_joined.drop(*cols_to_drop)
    
    # O Spark mantém a FK da df_fact e da df_dim se os nomes forem iguais, 
    # para não haver ambiguidade, selecionamos os SKs da dimensão e mantemos os dados da fato
    return df_joined


def run() -> None:
    # 1. Setup do PySpark
    spark = get_spark_session("fato_vendas")
    checkpoint_file = gold_path("checkpoints/fato_vendas")
    
    # 2. Resgata o Checkpoint
    last_watermark = get_last_checkpoint(spark, checkpoint_file)
    print(f"[FATO VENDAS] Iniciando extração. Último checkpoint: {last_watermark}")
    
    # 3. Extração Incremental da Silver (Issue #59)
    df_pedidos = read_incremental_silver(spark, "pedidos", last_watermark)
    df_itens = read_incremental_silver(spark, "itens_pedido", last_watermark)
    df_pagamentos = read_incremental_silver(spark, "pagamentos_pedido", last_watermark)
    
    count_pedidos = df_pedidos.count()
    if count_pedidos == 0:
        print("[FATO VENDAS] Nenhuma alteração nova detectada em 'pedidos'. Encerrando carga.")
        spark.stop()
        return
        
    # Extrair a data máxima processada neste lote para atualizar o Checkpoint no fim
    new_watermark_row = df_pedidos.agg(F.max("_silver_processed_at").alias("max_ts")).collect()[0]
    new_watermark = str(new_watermark_row["max_ts"])
    print(f"[FATO VENDAS] Novos registros detectados. Próximo checkpoint será: {new_watermark}")

    # 4. Estruturação do Schema Fato e Agregações (Issue #61)
    print("[FATO VENDAS] Consolidando Fatos e realizando agregações (Issue #61)...")
    
    # Um pedido pode ter pagamentos, vamos agregar para o caso de múltiplos pagamentos
    # (Embora no dataset gerado seja 1:1, a modelagem fica resiliente)
    df_pag_agg = df_pagamentos.groupBy("id_pedido").agg(
        F.sum("valor_pago").alias("valor_total_pago_pedido"),
        F.first("id_metodo").alias("id_metodo")
    )
    
    # Fato no grão de Item (Fato Vendas Itens)
    df_fato_bruta = df_itens.join(
        df_pedidos, on="id_pedido", how="inner"
    ).join(
        df_pag_agg, on="id_pedido", how="left"
    )
    
    # Adicionando métricas calculadas
    df_fato_calc = df_fato_bruta.withColumn(
        "valor_total_item", F.col("quantidade") * F.col("preco_unitario")
    ).withColumn(
        "data_pedido", F.to_timestamp("data_pedido")
    )
    
    # 5. Mapeamento de Chaves Estrangeiras (Issue #60)
    print("[FATO VENDAS] Carregando dimensões e mapeando chaves substitutas (Issue #60)...")
    df_dim_clientes = spark.read.format("delta").load(gold_path("dim_clientes"))
    df_dim_lojas = spark.read.format("delta").load(gold_path("dim_lojas"))
    df_dim_vendedores = spark.read.format("delta").load(gold_path("dim_vendedores"))
    df_dim_produtos = spark.read.format("delta").load(gold_path("dim_produtos"))
    df_dim_metodos = spark.read.format("delta").load(gold_path("dim_metodos_pagamento"))
    
    df_fato_mapped = join_scd2(df_fato_calc, df_dim_clientes, "id_cliente", "sk_cliente")
    df_fato_mapped = join_scd2(df_fato_mapped, df_dim_lojas, "id_loja", "sk_loja")
    df_fato_mapped = join_scd2(df_fato_mapped, df_dim_vendedores, "id_vendedor", "sk_vendedor")
    df_fato_mapped = join_scd2(df_fato_mapped, df_dim_produtos, "id_produto", "sk_produto")
    df_fato_mapped = join_scd2(df_fato_mapped, df_dim_metodos, "id_metodo", "sk_metodo")
    
    # Seleção do Schema Final limpo, trocando FKs pelas SKs (quando disponíveis na modelagem)
    # A dimensão pode usar o ID original para consulta
    df_fato_final = df_fato_mapped.select(
        "id_pedido",
        "id_item",
        "sk_cliente",
        "sk_loja",
        "sk_vendedor",
        "sk_produto",
        "sk_metodo",
        "data_pedido",
        "status_pedido",
        "quantidade",
        "preco_unitario",
        "valor_total_item",
        "valor_total_pago_pedido",
        F.current_timestamp().alias("_gold_processed_at")
    )

    # 6. Escrita da Tabela Fato na camada Gold (Issue #62)
    dst_path = gold_path("fato_vendas")
    print(f"[FATO VENDAS] Gravando dados no formato Delta em {dst_path} (Issue #62)...")
    df_fato_final.write.format("delta").mode("append").save(dst_path)
    
    # 7. Atualização do Checkpoint (Issue #63)
    print("[FATO VENDAS] Atualizando Checkpoint no MinIO (Issue #63)...")
    save_checkpoint(spark, checkpoint_file, new_watermark)
    
    print("[FATO VENDAS] Carga da Fato concluída com sucesso!")
    spark.stop()


if __name__ == "__main__":
    run()
