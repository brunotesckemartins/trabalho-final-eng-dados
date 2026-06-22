"""
test_validacao.py
-----------------
Validação de consistência dos dados do dashboard contra a camada Gold.

Execução:
    python visualization/tests/test_validacao.py

Saída: resultado por indicador (APROVADO / REPROVADO) e resumo final.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from visualization.config import get_connection
from visualization.gold_reader import load_gold_tables
from visualization.create_views import create_views
from visualization.kpis import (
    get_receita_total,
    get_ticket_medio,
    get_total_pedidos,
    get_clientes_unicos,
)
from visualization.metrics import get_receita_por_categoria, get_evolucao_mensal

_TOLERANCE = 0.01  # tolerância de R$ 0,01 para comparações de float


def _check(nome: str, resultado: bool) -> bool:
    status = "APROVADO" if resultado else "REPROVADO"
    print(f"  [{status}] {nome}")
    return resultado


def _run_validacoes(conn) -> list[bool]:
    resultados = []

    # ── 1. Sem perda de registros na view principal ────────────────────────
    total_fato = conn.execute("SELECT COUNT(*) FROM fato_vendas").fetchone()[0]
    total_view = conn.execute("SELECT COUNT(*) FROM vw_vendas_detalhadas").fetchone()[0]
    resultados.append(_check(
        "Contagem de itens: vw_vendas_detalhadas == fato_vendas",
        total_fato == total_view,
    ))

    # ── 2. KPI: Receita Total == soma direta da fato ───────────────────────
    receita_kpi = get_receita_total(conn)
    receita_direta = conn.execute(
        "SELECT COALESCE(SUM(valor_total_item), 0) FROM fato_vendas f "
        "JOIN vw_vendas_detalhadas v ON f.id_item = v.id_item "
        "WHERE v.status_pedido = 'Concluído'"
    ).fetchone()[0]
    resultados.append(_check(
        "KPI Receita Total: view == fato direto",
        abs(float(receita_kpi) - float(receita_direta)) <= _TOLERANCE,
    ))

    # ── 3. KPI: Total de Pedidos == COUNT DISTINCT da fato ────────────────
    pedidos_kpi = get_total_pedidos(conn)
    pedidos_direto = conn.execute(
        "SELECT COUNT(DISTINCT id_pedido) FROM fato_vendas"
    ).fetchone()[0]
    resultados.append(_check(
        "KPI Total de Pedidos: view == fato direto",
        pedidos_kpi == pedidos_direto,
    ))

    # ── 4. KPI: Clientes Únicos == COUNT DISTINCT da fato ─────────────────
    clientes_kpi = get_clientes_unicos(conn)
    clientes_direto = conn.execute(
        "SELECT COUNT(DISTINCT sk_cliente) FROM fato_vendas"
    ).fetchone()[0]
    resultados.append(_check(
        "KPI Clientes Únicos: view == fato direto",
        clientes_kpi == clientes_direto,
    ))

    # ── 5. KPI: Ticket Médio == receita / pedidos calculado manualmente ───
    ticket_kpi = get_ticket_medio(conn)
    if pedidos_kpi > 0:
        ticket_esperado = receita_kpi / conn.execute(
            "SELECT COUNT(DISTINCT id_pedido) FROM vw_vendas_detalhadas "
            "WHERE status_pedido = 'Concluído'"
        ).fetchone()[0]
    else:
        ticket_esperado = 0.0
    resultados.append(_check(
        "KPI Ticket Médio: view == receita / pedidos",
        abs(float(ticket_kpi) - float(ticket_esperado)) <= _TOLERANCE,
    ))

    # ── 6. Métrica: soma de receita_por_categoria == receita_total ────────
    df_cat = get_receita_por_categoria(conn)
    soma_categorias = float(df_cat["receita"].sum())
    resultados.append(_check(
        "Métrica Receita por Categoria: soma das categorias == receita total",
        abs(soma_categorias - float(receita_kpi)) <= _TOLERANCE,
    ))

    # ── 7. Métrica: soma de evolucao_mensal == receita_total ──────────────
    df_mes = get_evolucao_mensal(conn)
    soma_mensal = float(df_mes["receita"].sum())
    resultados.append(_check(
        "Métrica Evolução Mensal: soma dos meses == receita total",
        abs(soma_mensal - float(receita_kpi)) <= _TOLERANCE,
    ))

    # ── 8. Sem duplicatas na view (id_item deve ser único) ────────────────
    total_items = conn.execute("SELECT COUNT(*) FROM vw_vendas_detalhadas").fetchone()[0]
    itens_distintos = conn.execute("SELECT COUNT(DISTINCT id_item) FROM vw_vendas_detalhadas").fetchone()[0]
    resultados.append(_check(
        "Sem duplicatas na view: COUNT(*) == COUNT(DISTINCT id_item)",
        total_items == itens_distintos,
    ))

    return resultados


def main() -> None:
    print("=" * 60)
    print("Validação: Dashboard vs. Camada Gold")
    print("=" * 60)

    conn = get_connection()
    load_gold_tables(conn)
    create_views(conn)

    resultados = _run_validacoes(conn)
    conn.close()

    aprovados = sum(resultados)
    total = len(resultados)

    print("=" * 60)
    print(f"Resultado: {aprovados}/{total} validações aprovadas")
    if aprovados == total:
        print("Status: APROVADO — dashboard consistente com a camada Gold.")
    else:
        print("Status: REPROVADO — inconsistências encontradas.")
    print("=" * 60)

    sys.exit(0 if aprovados == total else 1)


if __name__ == "__main__":
    main()
