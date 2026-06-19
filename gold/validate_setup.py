"""
validate_setup.py
-----------------
Valida a estrutura base da camada Gold.
"""

import sys
sys.path.insert(0, '/home/elison/trabalho-final-eng-dados')

from config import get_spark_session
from gold.config import GOLD_TABLE_ORDER, gold_path, BUCKET_GOLD
from gold.read_silver import read_silver_validated

SILVER_TABLES = [
    "clientes", "produtos", "categorias", "lojas",
    "vendedores", "metodos_pagamento", "pedidos",
    "itens_pedido", "pagamentos_pedido"
]

def main():
    erros = []

    print("=== [1] Verificando imports ===")
    print("[OK] Imports da camada Gold OK.")

    print("\n=== [2] Verificando paths e nomenclatura ===")
    for table in GOLD_TABLE_ORDER:
        path = gold_path(table)
        nome_ok = table.startswith("dim_") or table.startswith("fato_")
        path_ok = path.startswith(f"s3a://{BUCKET_GOLD}/")
        status = "[OK]" if (nome_ok and path_ok) else "[ERRO]"
        print(f"  {status} {table} -> {path}")
        if not (nome_ok and path_ok):
            erros.append(table)

    print("\n=== [3] Verificando acesso à Silver ===")
    spark = get_spark_session("validate_gold_setup")
    for table in SILVER_TABLES:
        try:
            df = read_silver_validated(table, spark)
            print(f"  [OK] Silver '{table}' acessível.")
        except Exception as e:
            print(f"  [ERRO] Silver '{table}': {e}")
            erros.append(table)
    spark.stop()

    print("\n===== RESULTADO =====")
    if erros:
        print(f"[FALHA] {len(erros)} problema(s): {erros}")
    else:
        print("[OK] Estrutura da camada Gold validada com sucesso!")

if __name__ == "__main__":
    main()
