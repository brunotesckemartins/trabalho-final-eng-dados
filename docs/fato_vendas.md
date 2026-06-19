# Fato de Vendas (fato_vendas)

A tabela **Fato de Vendas** fica na camada `Gold` e é o ponto central para análise do negócio de Ecommerce.

## Como os Dados Chegam

1. Os dados originais vêm da camada `Silver`, onde já foram limpos e deduplicados.
2. É feito um *Join* com as dimensões (`dim_clientes`, `dim_lojas`, `dim_produtos`, etc.) baseando-se na **Data do Pedido** para garantir a validade temporal do mapeamento.
3. Isso garante que se um cliente morava em São Paulo em 2024 e se mudou para o Rio em 2025, as vendas de 2024 serão sempre contabilizadas para a sua SK (Surrogate Key) em São Paulo (recurso SCD Tipo 2).

## Granularidade

A granularidade desta Fato é o **Item do Pedido** (`id_item`). Se um pedido possui 3 produtos, ele gera 3 linhas na fato.

## Métricas (Facts)

A tabela computa automaticamente:
- **`valor_venda`**: `quantidade * preco_unitario`
- **`custo_frete`**: `peso_kg * 5.0`
- **`tempo_entrega_dias`**: `(data_entrega - data_pedido)` em dias.

## Formato e Armazenamento

Os dados são armazenados como **Delta Table** no MinIO (`s3a://gold/fato_vendas`). A utilização do formato Delta permite que a tabela aceite *appends* com controle transacional ACID (não corrompendo em falhas e permitindo *Time Travel* e auditorias).
