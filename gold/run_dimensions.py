"""
run_dimensions.py
-----------------
Roda todas as dimensões Gold em sequência.
"""

import sys
sys.path.insert(0, '/home/elison/trabalho-final-eng-dados')

from config import get_spark_session
from gold.dimensions import dim_clientes, dim_lojas, dim_produtos, dim_vendedores, dim_metodos_pagamento

DIMENSIONS = [
    ("dim_clientes", dim_clientes),
    ("dim_lojas", dim_lojas),
    ("dim_produtos", dim_produtos),
    ("dim_vendedores", dim_vendedores),
    ("dim_metodos_pagamento", dim_metodos_pagamento),
]


def main():
    spark = get_spark_session("gold_run_dimensions")
    falhas = []

    for nome, modulo in DIMENSIONS:
        print(f"\n===== Processando '{nome}' =====")
        try:
            modulo.run(spark=spark)
        except Exception as e:
            print(f"[ERRO] '{nome}': {e}")
            falhas.append(nome)

    spark.stop()

    print("\n===== RESUMO =====")
    if falhas:
        print(f"Dimensões com falha: {falhas}")
        sys.exit(1)
    else:
        print("Todas as dimensões processadas com sucesso!")


if __name__ == "__main__":
    main()
