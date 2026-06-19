"""
gold_config.py
--------------
Configuração central da camada Gold.

Padrão de nomenclatura:
  - Dimensões: dim_<entidade>   ex: dim_cliente, dim_produto
  - Fatos:     fato_<processo>  ex: fato_vendas, fato_pagamentos
"""

import sys
sys.path.insert(0, '/home/elison/trabalho-final-eng-dados')

from config import get_spark_session

BUCKET_GOLD = "gold"

GOLD_DIMENSIONS = [
    "dim_cliente",
    "dim_produto",
    "dim_categoria",
    "dim_loja",
    "dim_vendedor",
    "dim_metodo_pagamento",
]

GOLD_FACTS = [
    "fato_vendas",
    "fato_pagamentos",
]

GOLD_TABLE_ORDER = GOLD_DIMENSIONS + GOLD_FACTS


def gold_path(table_name: str) -> str:
    return f"s3a://{BUCKET_GOLD}/{table_name}"
