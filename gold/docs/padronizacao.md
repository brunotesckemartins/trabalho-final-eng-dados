# Camada Gold — Documento de Padronização

## Padrão de Nomenclatura

| Tipo     | Prefixo  | Exemplo              |
|----------|----------|----------------------|
| Dimensão | `dim_`   | `dim_cliente`        |
| Fato     | `fato_`  | `fato_vendas`        |

## Paths no Data Lake# Camada Gold — Documento de Padronização

## Padrão de Nomenclatura

| Tipo     | Prefixo  | Exemplo              |
|----------|----------|----------------------|
| Dimensão | `dim_`   | `dim_cliente`        |
| Fato     | `fato_`  | `fato_vendas`        |

## Paths no Data Lake
s3a://gold/dim_cliente/

s3a://gold/dim_produto/

s3a://gold/fato_vendas/

s3a://gold/fato_pagamentos/

## Tabelas Previstas

### Dimensões
- `dim_cliente`        <- Silver: `clientes`
- `dim_produto`        <- Silver: `produtos`, `categorias`
- `dim_categoria`      <- Silver: `categorias`
- `dim_loja`           <- Silver: `lojas`
- `dim_vendedor`       <- Silver: `vendedores`
- `dim_metodo_pagamento` <- Silver: `metodos_pagamento`

### Fatos
- `fato_vendas`        <- Silver: `pedidos`, `itens_pedido`
- `fato_pagamentos`    <- Silver: `pagamentos_pedido`, `pedidos`

## Ordem de Carga
Dimensões sempre antes dos fatos.

## Colunas de Auditoria
Todas as tabelas Gold recebem automaticamente:

| Coluna               | Tipo      | Descrição                        |
|----------------------|-----------|----------------------------------|
| `_gold_processed_at` | Timestamp | Quando a linha entrou na Gold    |
