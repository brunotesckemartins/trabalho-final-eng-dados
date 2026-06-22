"""
gold_reader.py
--------------
Leitura das tabelas Delta Lake da camada Gold via DuckDB.

Tabelas mapeadas:
  Dimensões (filtradas por registro_ativo=true):
    - dim_clientes      (sk_cliente, id_cliente, nome_cliente, cidade, estado)
    - dim_produtos      (sk_produto, id_produto, nome_produto, preco_base, nome_categoria)
    - dim_lojas         (sk_loja, id_loja, nome_loja, estado_loja)
    - dim_vendedores    (sk_vendedor, id_vendedor, nome_vendedor, nome_loja)
    - dim_metodos_pagamento (sk_metodo, id_metodo, tipo_pagamento)

  Fatos:
    - fato_vendas       (id_pedido, id_item, sk_*, data_pedido, status_pedido,
                         quantidade, preco_unitario, valor_total_item,
                         valor_total_pago_pedido)
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import duckdb

from visualization.config import get_connection, gold_path

GOLD_DIMENSIONS = [
    "dim_clientes",
    "dim_produtos",
    "dim_lojas",
    "dim_vendedores",
    "dim_metodos_pagamento",
]

GOLD_FACTS = ["fato_vendas"]

GOLD_TABLES = GOLD_DIMENSIONS + GOLD_FACTS


def _register_dimension(conn: duckdb.DuckDBPyConnection, table: str) -> None:
    path = gold_path(table)
    conn.execute(
        f"CREATE OR REPLACE VIEW {table} AS "
        f"SELECT * FROM delta_scan('{path}') WHERE registro_ativo = true"
    )


def _register_fact(conn: duckdb.DuckDBPyConnection, table: str) -> None:
    path = gold_path(table)
    conn.execute(
        f"CREATE OR REPLACE VIEW {table} AS SELECT * FROM delta_scan('{path}')"
    )


def load_gold_tables(conn: duckdb.DuckDBPyConnection) -> None:
    """Registra todas as tabelas Gold como views no DuckDB."""
    for table in GOLD_DIMENSIONS:
        _register_dimension(conn, table)
    for table in GOLD_FACTS:
        _register_fact(conn, table)


def validate_gold_connection() -> None:
    """Valida leitura de todas as tabelas Gold e imprime contagem de registros."""
    conn = get_connection()
    load_gold_tables(conn)
    print("Tabelas Gold carregadas via DuckDB:")
    for table in GOLD_TABLES:
        count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"  {table}: {count} registros")
    conn.close()


if __name__ == "__main__":
    validate_gold_connection()
