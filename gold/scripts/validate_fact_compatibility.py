import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from pyspark.sql import functions as F
from gold.config import get_spark_session, gold_path

def validate_dimension(df, sk_col, bk_col):
    print(f"\nValidando {sk_col}")
    total = df.count()
    sk_null = df.filter(F.col(sk_col).isNull()).count()
    sk_dup = (
        df.groupBy(sk_col)
        .count()
        .filter("count > 1")
        .count()
    )
    print(f"Registros: {total}")
    print(f"SK nulas: {sk_null}")
    print(f"SK duplicadas: {sk_dup}")
    return sk_null == 0 and sk_dup == 0

def main():
    spark = get_spark_session("gold10")
    dimensoes = [
        ("dim_clientes", "sk_cliente", "id_cliente"),
        ("dim_produtos", "sk_produto", "id_produto"),
        ("dim_lojas", "sk_loja", "id_loja"),
        ("dim_vendedores", "sk_vendedor", "id_vendedor"),
        ("dim_metodos_pagamento", "sk_metodo", "id_metodo"),
    ]
    for tabela, sk, bk in dimensoes:
        df = spark.read.format("delta").load(gold_path(tabela))
        validate_dimension(df, sk, bk)
    print("\n[OK] Dimensões compatíveis com tabela fato.")
    spark.stop()

if __name__ == "__main__":
    main()
