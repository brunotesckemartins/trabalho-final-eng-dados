"""
test_version_inserter.py
------------------------
Testes de inserção de novas versões e preservação de histórico.

Valida:
  - Nova versão criada após alteração.
  - Registro ativo atualizado corretamente.
  - Histórico completo preservado.
"""

import sys
sys.path.insert(0, '/home/elison/trabalho-final-eng-dados')

from pyspark.sql import Row
from pyspark.sql.functions import col
from config import get_spark_session
from gold.utils.incremental_loader import incremental_load
from gold.utils.version_inserter import get_history

DST_PATH = "s3a://gold/test_version_inserter_dim"
PRIMARY_KEY = "id_cliente"
BUSINESS_COLUMNS = ["nome_cliente", "cidade", "estado"]


def test_nova_versao_apos_alteracao(spark):
    print("\n--- TESTE 1: Nova versão criada após alteração ---")

    df_v1 = spark.createDataFrame([
        Row(id_cliente=1, nome_cliente="Ana Silva", cidade="SP", estado="SP"),
    ])
    incremental_load(spark, df_v1, DST_PATH, PRIMARY_KEY, BUSINESS_COLUMNS, "test_version")

    df_v2 = spark.createDataFrame([
        Row(id_cliente=1, nome_cliente="Ana Silva", cidade="Campinas", estado="SP"),
    ])
    incremental_load(spark, df_v2, DST_PATH, PRIMARY_KEY, BUSINESS_COLUMNS, "test_version")

    df_gold = spark.read.format("delta").load(DST_PATH)
    total_versoes = df_gold.filter(col(PRIMARY_KEY) == 1).count()

    assert total_versoes >= 2, f"FALHA: esperado >= 2 versões, got {total_versoes}"
    print(f"[OK] {total_versoes} versões encontradas para id_cliente=1.")


def test_registro_ativo_atualizado(spark):
    print("\n--- TESTE 2: Apenas uma versão ativa ---")

    df_gold = spark.read.format("delta").load(DST_PATH)
    ativos = df_gold.filter(
        (col(PRIMARY_KEY) == 1) & (col("registro_ativo") == True)
    ).count()

    assert ativos == 1, f"FALHA: esperado 1 ativo, got {ativos}"

    versao_ativa = df_gold.filter(
        (col(PRIMARY_KEY) == 1) & (col("registro_ativo") == True)
    ).select("cidade").collect()[0]["cidade"]

    assert versao_ativa == "Campinas", f"FALHA: esperado 'Campinas', got '{versao_ativa}'"
    print(f"[OK] Versão ativa correta: cidade='{versao_ativa}'.")


def test_historico_preservado(spark):
    print("\n--- TESTE 3: Histórico completo preservado ---")

    df_historico = get_history(spark, DST_PATH, PRIMARY_KEY, 1)
    df_historico.select(
        PRIMARY_KEY, "cidade", "registro_ativo",
        "data_inicio_vigencia", "data_fim_vigencia"
    ).show(truncate=False)

    inativos = df_historico.filter(col("registro_ativo") == False).count()
    assert inativos >= 1, f"FALHA: esperado >= 1 versão inativa no histórico."
    print(f"[OK] Histórico preservado com {inativos} versão(ões) inativa(s).")


def main():
    spark = get_spark_session("test_version_inserter")
    try:
        test_nova_versao_apos_alteracao(spark)
        test_registro_ativo_atualizado(spark)
        test_historico_preservado(spark)
        print("\n[OK] Todos os testes de versionamento passaram!")
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
