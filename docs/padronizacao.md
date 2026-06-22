# Camada Gold — Padrões de Implementação

## Nomenclatura de Tabelas

| Tipo | Prefixo | Exemplo |
|---|---|---|
| Dimensão | `dim_` | `dim_clientes` |
| Fato | `fato_` | `fato_vendas` |

Convenção adotada: nomes no **plural**, alinhados com os nomes das tabelas Silver de origem.

## Paths no Data Lake (MinIO)

```
s3a://gold/dim_clientes/
s3a://gold/dim_lojas/
s3a://gold/dim_produtos/
s3a://gold/dim_vendedores/
s3a://gold/dim_metodos_pagamento/
s3a://gold/fato_vendas/
s3a://gold/checkpoints/fato_vendas/
```

## Tabelas Implementadas

### Dimensões (SCD Tipo 2)

| Tabela Gold | Chave Substituta | Fonte Silver |
|---|---|---|
| `dim_clientes` | `sk_cliente` | `clientes` + `enderecos` |
| `dim_lojas` | `sk_loja` | `lojas` |
| `dim_produtos` | `sk_produto` | `produtos` + `categorias` |
| `dim_vendedores` | `sk_vendedor` | `vendedores` + `lojas` |
| `dim_metodos_pagamento` | `sk_metodo` | `metodos_pagamento` |

### Fatos

| Tabela Gold | Grão | Fonte Silver |
|---|---|---|
| `fato_vendas` | Item de pedido (`id_item`) | `pedidos` + `itens_pedido` + `pagamentos_pedido` |

## Ordem de Carga

Dimensões são sempre processadas antes dos fatos (`gold/run_dimensions.py` precede `gold/facts/fato_vendas.py`).

## Colunas de Auditoria

Todas as tabelas Gold recebem automaticamente:

| Coluna | Tipo | Descrição |
|---|---|---|
| `_gold_processed_at` | Timestamp | Quando a linha entrou na Gold |

Dimensões SCD Tipo 2 recebem adicionalmente:

| Coluna | Tipo | Descrição |
|---|---|---|
| `data_inicio_vigencia` | Timestamp | Início da validade do registro |
| `data_fim_vigencia` | Timestamp | Fim da validade (nulo = registro atual) |
| `registro_ativo` | Boolean | `true` = versão vigente |
