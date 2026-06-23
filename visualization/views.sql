-- views.sql
-- Views SQL de virtualização da camada de consumo analítico.
-- Nomenclatura: vw_<propósito>
--
-- Dependências: load_gold_tables() deve ser executado antes (registra as
-- tabelas Gold como views no DuckDB antes destas views serem criadas).

-- View principal: une fato_vendas com todas as dimensões ativas.
-- Expõe os campos necessários para KPIs e métricas do dashboard.
CREATE OR REPLACE VIEW vw_vendas_detalhadas AS
SELECT
    f.id_pedido,
    f.id_item,
    f.data_pedido,
    f.status_pedido,
    f.quantidade,
    f.preco_unitario,
    f.valor_total_item,
    f.valor_total_pago_pedido,
    c.nome_cliente,
    c.cidade          AS cidade_cliente,
    c.estado          AS estado_cliente,
    p.nome_produto,
    p.preco_base,
    p.nome_categoria,
    l.nome_loja,
    l.estado_loja,
    v.nome_vendedor,
    m.tipo_pagamento
FROM fato_vendas f
LEFT JOIN dim_clientes          c ON f.sk_cliente  = c.sk_cliente
LEFT JOIN dim_produtos          p ON f.sk_produto  = p.sk_produto
LEFT JOIN dim_lojas             l ON f.sk_loja     = l.sk_loja
LEFT JOIN dim_vendedores        v ON f.sk_vendedor = v.sk_vendedor
LEFT JOIN dim_metodos_pagamento m ON f.sk_metodo   = m.sk_metodo
;
