"""
create_views.py
---------------
Cria as views SQL de virtualização no banco DuckDB.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import duckdb

from visualization.config import get_connection
from visualization.gold_reader import load_gold_tables

_VIEWS_SQL = os.path.join(os.path.dirname(__file__), "views.sql")


def create_views(conn: duckdb.DuckDBPyConnection = None) -> None:
    """
    Cria as views de virtualização no DuckDB.
    Quando conn é None, abre uma conexão própria e a fecha ao final.
    """
    owns_conn = conn is None
    if owns_conn:
        conn = get_connection()
        load_gold_tables(conn)

    with open(_VIEWS_SQL) as f:
        sql = f.read()

    for stmt in sql.split(";"):
        stmt = stmt.strip()
        if stmt and not stmt.startswith("--"):
            conn.execute(stmt)

    print("[VIEWS] Views criadas com sucesso.")

    if owns_conn:
        conn.close()


if __name__ == "__main__":
    create_views()
