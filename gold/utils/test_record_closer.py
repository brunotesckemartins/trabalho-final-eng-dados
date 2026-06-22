"""
test_record_closer.py
---------------------
Testes de encerramento de registros antigos SCD Tipo 2.

Valida:
  - Registro anterior marcado como inativo.
  - data_fim_vigencia preenchida corretamente.
  - Apenas uma versão ativa por chave de negócio.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pyspark.sql import Row
from pyspark.sql.functions import col
from config import get_spark_session
from gold.utils.record_closer import close_old_records, validate_single_active
from gold.utils.incremental_loader import incremental_load

DST_PATH = "s3a://gold/test_record_closer_dim"
PRIMARY_KEY = "id_cliente"
BUSINESS_COLUMNS = ["nome_cliente", "cidade", "estado"]


def test_encerramento(spark):
    print("\n--- TESTE 1: Encerramento de registro antigo ---")

    # Primeira carga
    df_inicial = spark.createDataFrame([
        Row(id_cliente=1, nome_cliente="Ana Silva", cidade="SP", estado="SP"),
        Row(id_cliente=2, nome_cliente="João Costa", cidade="RJ", estado="RJ"),
    ])
    incremental_load(spark, df_inicial, DST_PATH, PRIMARY_KEY, BUSINESS_COLUMNS, "test_closer")

    # Segunda carga com alteração
    df_alterado = spark.createDataFrame([
        Row(id_cliente=1, nome_cliente="Ana Silva", cidade="Campinas", estado="SP"),
        Row(id_cliente=2, nome_cliente="João Costa", cidade="RJ", estado="RJ"),
    ])
    incremental_load(spark, df_alterado, DST_PATH, PRIMARY_KEY, BUSINESS_COLUMNS, "test_closer")

    df_gold = spark.read.format("delta").load(DST_PATH)

    # Verifica registros inativos
    inativos = df_gold.filter(col("registro_ativo") == False)
    count_inativos = inativos.count()
    assert count_inativos >= 1, f"FALHA: esperado >= 1 inativo, got {count_inativos}"
    print(f"[OK] {count_inativos} registro(s) encerrado(s) corretamente.")

    # Verifica data_fim_vigencia preenchida nos inativos
    sem_fim = inativos.filter(col("data_fim_vigencia").isNull()).count()
    assert sem_fim == 0, f"FALHA: {sem_fim} registro(s) inativo(s) sem data_fim_vigencia."
    print("[OK] data_fim_vigencia preenchida em todos os registros inativos.")


def test_unica_versao_ativa(spark):
    print("\n--- TESTE 2: Apenas uma versão ativa por chave ---")
    valido = validate_single_active(spark, DST_PATH, PRIMARY_KEY)
    assert valido, "FALHA: encontradas múltiplas versões ativas para a mesma chave."
    print("[OK] Apenas uma versão ativa por chave de negócio.")


def main():
    spark = get_spark_session("test_record_closer")
    try:
        test_encerramento(spark)
        test_unica_versao_ativa(spark)
        print("\n[OK] Todos os testes de encerramento passaram!")
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
