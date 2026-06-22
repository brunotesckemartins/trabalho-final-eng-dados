"""
kpis.py
-------
Cálculo dos 4 KPIs obrigatórios do dashboard.

KPI 1 — Receita Total     : soma do valor_total_item dos pedidos Concluídos
KPI 2 — Total de Pedidos  : contagem distinta de id_pedido (todos os status)
KPI 3 — Ticket Médio      : receita total / pedidos Concluídos
KPI 4 — Clientes Únicos   : contagem distinta de sk_cliente na fato_vendas
"""

import duckdb

from visualization.queries import (
    CLIENTES_UNICOS,
    RECEITA_TOTAL,
    TICKET_MEDIO,
    TOTAL_PEDIDOS,
)


def get_receita_total(conn: duckdb.DuckDBPyConnection) -> float:
    return float(conn.execute(RECEITA_TOTAL).fetchone()[0])


def get_total_pedidos(conn: duckdb.DuckDBPyConnection) -> int:
    return int(conn.execute(TOTAL_PEDIDOS).fetchone()[0])


def get_ticket_medio(conn: duckdb.DuckDBPyConnection) -> float:
    return float(conn.execute(TICKET_MEDIO).fetchone()[0])


def get_clientes_unicos(conn: duckdb.DuckDBPyConnection) -> int:
    return int(conn.execute(CLIENTES_UNICOS).fetchone()[0])
