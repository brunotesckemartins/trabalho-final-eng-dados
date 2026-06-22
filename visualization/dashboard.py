"""
dashboard.py
------------
Dashboard One Page View — camada de visualização analítica.

Execução:
    streamlit run visualization/dashboard.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import plotly.express as px
import streamlit as st

from visualization.config import get_connection
from visualization.create_views import create_views
from visualization.gold_reader import load_gold_tables
from visualization.kpis import (
    get_clientes_unicos,
    get_receita_total,
    get_ticket_medio,
    get_total_pedidos,
)
from visualization.metrics import get_evolucao_mensal, get_receita_por_categoria


@st.cache_resource
def _init_connection():
    conn = get_connection()
    load_gold_tables(conn)
    create_views(conn)
    return conn


def main() -> None:
    st.set_page_config(page_title="Dashboard de Vendas", layout="wide")
    st.title("Dashboard de Vendas — E-commerce")
    st.markdown("---")

    conn = _init_connection()

    # ── KPIs ──────────────────────────────────────────────────────────────
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Receita Total", f"R$ {get_receita_total(conn):,.2f}")
    col2.metric("Total de Pedidos", f"{get_total_pedidos(conn):,}")
    col3.metric("Ticket Médio", f"R$ {get_ticket_medio(conn):,.2f}")
    col4.metric("Clientes Únicos", f"{get_clientes_unicos(conn):,}")

    st.markdown("---")

    # ── Métricas ──────────────────────────────────────────────────────────
    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("Receita por Categoria de Produto")
        df_cat = get_receita_por_categoria(conn)
        fig = px.bar(
            df_cat,
            x="nome_categoria",
            y="receita",
            labels={"nome_categoria": "Categoria", "receita": "Receita (R$)"},
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        st.subheader("Evolução Mensal de Receita")
        df_mes = get_evolucao_mensal(conn)
        df_mes["mes"] = df_mes["mes"].astype(str).str[:7]
        fig = px.line(
            df_mes,
            x="mes",
            y="receita",
            markers=True,
            labels={"mes": "Mês", "receita": "Receita (R$)"},
        )
        st.plotly_chart(fig, use_container_width=True)


if __name__ == "__main__":
    main()
