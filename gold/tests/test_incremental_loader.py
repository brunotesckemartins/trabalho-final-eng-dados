"""
test_incremental_loader.py
--------------------------
Testes de validação da carga incremental.

Valida:
  - Primeira carga: todos os registros inseridos.
  - Segunda carga sem mudanças: nenhuma escrita.
  - Terceira carga com alterações: apenas alterados processados.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pyspark.sql import Row
from pyspark.sql.functions import col
from config import get_spark_session
from gold.utils.incremental_loader import incremental_load

DST_PATH = "s3a://gold/test_incremental_dim"
PRIMARY_KEY = "id_cliente"
BUSINESS_COLUMNS = ["nome_cliente", "cidade", "estado"]


def test_primeira_carga(spark):
    print("\n--- TESTE 1: Primeira carga ---")
    df = spark.createDataFrame([
        Row(id_cliente=1, nome_cliente="Ana Silva", cidade="SP", estado="SP"),
        Row(id_cliente=2, nome_cliente="João Costa", cidade="RJ", estado="RJ"),
    ])
    resultado = incremental_load(spark, df, DST_PATH, PRIMARY_KEY, BUSINESS_COLUMNS, "test_dim")
    assert resultado["novos"] == 2, f"FALHA: esperado 2 novos, got {resultado['novos']}"
    print("[OK] Primeira carga: 2 registros inseridos.")


def test_segunda_carga_sem_mudanca(spark):
    print("\n--- TESTE 2: Segunda carga sem mudanças ---")
    df = spark.createDataFrame([
        Row(id_cliente=1, nome_cliente="Ana Silva", cidade="SP", estado="SP"),
        Row(id_cliente=2, nome_cliente="João Costa", cidade="RJ", estado="RJ"),
    ])
    resultado = incremental_load(spark, df, DST_PATH, PRIMARY_KEY, BUSINESS_COLUMNS, "test_dim")
    assert resultado["novos"] == 0, f"FALHA: esperado 0 novos, got {resultado['novos']}"
    assert resultado["alterados"] == 0, f"FALHA: esperado 0 alterados, got {resultado['alterados']}"
    print("[OK] Segunda carga: nenhuma escrita desnecessária.")


def test_terceira_carga_com_alteracao(spark):
    print("\n--- TESTE 3: Terceira carga com alteração ---")
    df = spark.createDataFrame([
        Row(id_cliente=1, nome_cliente="Ana Silva", cidade="Campinas", estado="SP"),  # cidade mudou
        Row(id_cliente=2, nome_cliente="João Costa", cidade="RJ", estado="RJ"),       # sem mudança
        Row(id_cliente=3, nome_cliente="Maria Lima", cidade="BH", estado="MG"),       # novo
    ])
    resultado = incremental_load(spark, df, DST_PATH, PRIMARY_KEY, BUSINESS_COLUMNS, "test_dim")
    assert resultado["novos"] == 1, f"FALHA: esperado 1 novo, got {resultado['novos']}"
    assert resultado["alterados"] == 1, f"FALHA: esperado 1 alterado, got {resultado['alterados']}"
    assert resultado["sem_alteracao"] == 1, f"FALHA: esperado 1 ignorado, got {resultado['sem_alteracao']}"
    print("[OK] Terceira carga: apenas novos e alterados processados.")


def main():
    spark = get_spark_session("test_incremental_loader")
    try:
        test_primeira_carga(spark)
        test_segunda_carga_sem_mudanca(spark)
        test_terceira_carga_com_alteracao(spark)
        print("\n[OK] Todos os testes de carga incremental passaram!")
    finally:
        spark.stop()


if __name__ == "__main__": main()
