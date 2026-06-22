"""
queries.py
----------
Consultas SQL de agregação para os indicadores do dashboard.

Mapeamento: indicador → query → campos de saída
─────────────────────────────────────────────────────────────────────────────
KPI 1  | RECEITA_TOTAL        | receita_total (float)
KPI 2  | TOTAL_PEDIDOS        | total_pedidos (int)
KPI 3  | TICKET_MEDIO         | ticket_medio (float)
KPI 4  | CLIENTES_UNICOS      | clientes_unicos (int)
─────────────────────────────────────────────────────────────────────────────
MET 1  | RECEITA_POR_CATEGORIA | nome_categoria, receita
MET 2  | EVOLUCAO_MENSAL       | mes, receita
─────────────────────────────────────────────────────────────────────────────

Fonte: view vw_vendas_detalhadas (issue #21).
Pedidos com status 'Concluído' são a base de cálculo de receita.
"""

# ── KPIs ──────────────────────────────────────────────────────────────────

RECEITA_TOTAL = """
SELECT COALESCE(SUM(valor_total_item), 0) AS receita_total
FROM vw_vendas_detalhadas
WHERE status_pedido = 'Concluído'
"""

TOTAL_PEDIDOS = """
SELECT COUNT(DISTINCT id_pedido) AS total_pedidos
FROM vw_vendas_detalhadas
"""

TICKET_MEDIO = """
SELECT COALESCE(
    SUM(valor_total_item) / NULLIF(COUNT(DISTINCT id_pedido), 0),
    0
) AS ticket_medio
FROM vw_vendas_detalhadas
WHERE status_pedido = 'Concluído'
"""

CLIENTES_UNICOS = """
SELECT COUNT(DISTINCT sk_cliente) AS clientes_unicos
FROM fato_vendas
"""

# ── Métricas ──────────────────────────────────────────────────────────────

RECEITA_POR_CATEGORIA = """
SELECT
    nome_categoria,
    COALESCE(SUM(valor_total_item), 0) AS receita
FROM vw_vendas_detalhadas
WHERE status_pedido = 'Concluído'
GROUP BY nome_categoria
ORDER BY receita DESC
"""

EVOLUCAO_MENSAL = """
SELECT
    DATE_TRUNC('month', data_pedido) AS mes,
    COALESCE(SUM(valor_total_item), 0) AS receita
FROM vw_vendas_detalhadas
WHERE status_pedido = 'Concluído'
GROUP BY mes
ORDER BY mes
"""
