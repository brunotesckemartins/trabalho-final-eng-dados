"""
test_carga_inicial.py
----------------------
GOLD-11: Testes de validação da carga inicial das dimensões.
Valida registros carregados, estrutura SCD2 e integridade dos dados.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from pyspark.sql import functions as F
from gold.config import get_spark_session, gold_path

DIMENSOES = [
    ("dim_clientes",          "sk_cliente",  "id_cliente"),
    ("dim_produtos",          "sk_produto",  "id_produto"),
    ("dim_lojas",             "sk_loja",     "id_loja"),
    ("dim_vendedores",        "sk_vendedor", "id_vendedor"),
    ("dim_metodos_pagamento", "sk_metodo",   "id_metodo"),
]

def test_registros_carregados(spark, tabela, sk_col):
    df = spark.read.format("delta").load(gold_path(tabela))
    total = df.count()
    assert total > 0, f"[FALHA] {tabela}: nenhum registro encontrado"
    print(f"[OK] {tabela}: {total} registros carregados")
    return df

def test_estrutura_scd2(df, tabela):
    colunas_scd2 = ["registro_ativo", "data_inicio_vigencia", "data_fim_vigencia"]
    colunas_presentes = df.columns
    for col in colunas_scd2:
        assert col in colunas_presentes, f"[FALHA] {tabela}: coluna SCD2 ausente -> {col}"
    print(f"[OK] {tabela}: estrutura SCD2 presente {colunas_scd2}")

def test_registro_ativo_consistente(df, tabela):
    nulos = df.filter(F.col("registro_ativo").isNull()).count()
    assert nulos == 0, f"[FALHA] {tabela}: {nulos} registros com 'registro_ativo' nulo"

    ativos = df.filter(F.col("registro_ativo") == True)
    inativos = df.filter(F.col("registro_ativo") == False)

    fim_nulo_inativo = inativos.filter(F.col("data_fim_vigencia").isNull()).count()
    assert fim_nulo_inativo == 0, f"[FALHA] {tabela}: {fim_nulo_inativo} inativos sem data_fim_vigencia"

    fim_preenchido_ativo = ativos.filter(F.col("data_fim_vigencia").isNotNull()).count()
    assert fim_preenchido_ativo == 0, f"[FALHA] {tabela}: {fim_preenchido_ativo} ativos com data_fim_vigencia preenchida"

    print(f"[OK] {tabela}: SCD2 consistente — {ativos.count()} ativos, {inativos.count()} inativos")

def test_sk_valida(df, tabela, sk_col):
    nulas = df.filter(F.col(sk_col).isNull()).count()
    assert nulas == 0, f"[FALHA] {tabela}: {nulas} SKs nulas"

    dups = df.groupBy(sk_col).count().filter("count > 1").count()
    assert dups == 0, f"[FALHA] {tabela}: {dups} SKs duplicadas"

    print(f"[OK] {tabela}: SK '{sk_col}' válida — sem nulos nem duplicatas")

def run_tests():
    spark = get_spark_session("gold11-testes-carga-inicial")
    print("\n=== GOLD-11: Testes de Carga Inicial ===\n")
    falhas = []

    for tabela, sk_col, bk_col in DIMENSOES:
        print(f"--- {tabela} ---")
        try:
            df = test_registros_carregados(spark, tabela, sk_col)
            test_estrutura_scd2(df, tabela)
            test_registro_ativo_consistente(df, tabela)
            test_sk_valida(df, tabela, sk_col)
        except AssertionError as e:
            print(str(e))
            falhas.append(str(e))

    print("\n=== RESULTADO ===")
    if falhas:
        print(f"[FALHA] {len(falhas)} teste(s) falharam:")
        for f in falhas:
            print(f"  - {f}")
        sys.exit(1)
    else:
        print("[OK] Todos os testes da GOLD-11 passaram!")

    spark.stop()

if __name__ == "__main__":
    run_tests()
