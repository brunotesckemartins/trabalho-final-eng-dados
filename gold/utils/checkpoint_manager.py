"""
checkpoint_manager.py
---------------------
Gerenciador de Watermark para cargas incrementais na camada Gold (Tabelas Fato).
Salva a data/hora máxima processada na última execução usando uma tabela Delta
de uma linha, garantindo suporte ACID e compatibilidade com o MinIO.
"""

from pyspark.sql import SparkSession, Row


def get_last_checkpoint(spark: SparkSession, checkpoint_path: str) -> str:
    """
    Retorna o timestamp do último processamento com base no arquivo de Checkpoint.
    Se não existir, retorna a data de início da época (para processar todo o histórico).
    """
    try:
        # Tenta ler a tabela Delta do checkpoint
        df = spark.read.format("delta").load(checkpoint_path)
        # Extrai a string de data/hora (ou objeto datetime convertido)
        last_watermark = df.collect()[0]["last_watermark"]
        return str(last_watermark)
    except Exception:
        # Se a tabela não existir, ocorreu erro de leitura ou a tabela de controle
        # está vazia, o fallback é 1970-01-01 (full load)
        print(f"[CHECKPOINT] Tabela de controle não encontrada ou vazia em {checkpoint_path}. Retornando fallback inicial.")
        return "1970-01-01 00:00:00.000"


def save_checkpoint(spark: SparkSession, checkpoint_path: str, watermark: str) -> None:
    """
    Cria ou sobrescreve a tabela Delta de Checkpoint com a nova marca d'água de tempo.
    """
    df = spark.createDataFrame([Row(last_watermark=watermark)])
    df.write.format("delta").mode("overwrite").save(checkpoint_path)
    print(f"[CHECKPOINT] Atualizado com sucesso para '{watermark}' em {checkpoint_path}.")
