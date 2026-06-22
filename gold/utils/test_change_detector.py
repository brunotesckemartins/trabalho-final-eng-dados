"""
test_change_detector.py
-----------------------
Testes de validação do mecanismo de detecção de alterações.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pyspark.sql import Row
from config import get_spark_session
from gold.utils.change_detector import detect_changes
from gold.config import gold_path


def test_deteccao(spark):
    print("\n===== TESTE: Detecção de Alterações =====")

    # Simula dados atuais na Gold (registro ativo)
    df_gold_atual = spark.createDataFrame([
        Row(id_cliente=1, nome_cliente="Ana Silva", cidade="SP", estado="SP",
            registro_ativo=True),
        Row(id_cliente=2, nome_cliente="João Costa", cidade="RJ", estado="RJ",
            registro_ativo=True),
        Row(id_cliente=3, nome_cliente="Maria Lima", cidade="BH", estado="MG",
            registro_ativo=True),
    ])

    # Simula novos dados vindos da Silver
    df_silver_novo = spark.createDataFrame([
        Row(id_cliente=1, nome_cliente="Ana Silva", cidade="SP", estado="SP"),      # sem alteração
        Row(id_cliente=2, nome_cliente="João Costa", cidade="Niterói", estado="RJ"), # alterado (cidade)
        Row(id_cliente=4, nome_cliente="Pedro Souza", cidade="POA", estado="RS"),   # novo
    ])

    business_columns = ["nome_cliente", "cidade", "estado"]

    # Filtra só ativos da Gold para comparação
    df_gold_filtrado = df_gold_atual.filter(
        df_gold_atual.registro_ativo == True
    ).select("id_cliente", *business_columns)

    # Novos
    df_novos = df_silver_novo.join(df_gold_filtrado, on="id_cliente", how="left_anti")
    count_novos = df_novos.count()

    # Joined para detectar alterados e sem alteração
    df_joined = df_silver_novo.alias("new").join(
        df_gold_filtrado.alias("gold"), on="id_cliente", how="inner"
    )

    from pyspark.sql.functions import col
    change_expr = None
    for c in business_columns:
        cond = col(f"new.{c}") != col(f"gold.{c}")
        change_expr = cond if change_expr is None else change_expr | cond

    count_alterados = df_joined.filter(change_expr).count()
    count_sem_alteracao = df_joined.filter(~change_expr).count()

    print(f"  Novos encontrados: {count_novos} (esperado: 1)")
    print(f"  Alterados encontrados: {count_alterados} (esperado: 1)")
    print(f"  Sem alteração: {count_sem_alteracao} (esperado: 1)")

    assert count_novos == 1, f"FALHA: esperado 1 novo, got {count_novos}"
    assert count_alterados == 1, f"FALHA: esperado 1 alterado, got {count_alterados}"
    assert count_sem_alteracao == 1, f"FALHA: esperado 1 sem alteração, got {count_sem_alteracao}"

    print("\n[OK] Todos os testes passaram!")


def main():
    spark = get_spark_session("test_change_detector")
    try:
        test_deteccao(spark)
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
