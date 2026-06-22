"""
metrics.py
----------
Cálculo das 2 métricas complementares obrigatórias do dashboard.

Métrica 1 — Receita por Categoria : receita agrupada por nome_categoria (bar chart)
Métrica 2 — Evolução Mensal       : receita agrupada por mês (line chart)
"""

import duckdb
import pandas as pd

from visualization.queries import EVOLUCAO_MENSAL, RECEITA_POR_CATEGORIA


def get_receita_por_categoria(conn: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    """Retorna DataFrame com colunas: nome_categoria, receita."""
    return conn.execute(RECEITA_POR_CATEGORIA).df()


def get_evolucao_mensal(conn: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    """Retorna DataFrame com colunas: mes (datetime), receita."""
    return conn.execute(EVOLUCAO_MENSAL).df()
