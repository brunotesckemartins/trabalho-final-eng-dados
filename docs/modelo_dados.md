# 📐 Modelo de Dados

## Banco de Origem (PostgreSQL)

O banco `ecommerce_db` possui **10 tabelas** divididas entre tabelas dimensionais e tabelas fato.

### Diagrama Entidade-Relacionamento

```mermaid
erDiagram
    categorias ||--o{ produtos : "id_categoria"
    clientes ||--o{ enderecos : "id_cliente"
    clientes ||--o{ pedidos : "id_cliente"
    lojas ||--o{ vendedores : "id_loja"
    lojas ||--o{ pedidos : "id_loja"
    vendedores ||--o{ pedidos : "id_vendedor"
    pedidos ||--o{ itens_pedido : "id_pedido"
    pedidos ||--o{ pagamentos_pedido : "id_pedido"
    produtos ||--o{ itens_pedido : "id_produto"
    metodos_pagamento ||--o{ pagamentos_pedido : "id_metodo"

    categorias {
        int id_categoria PK
        varchar nome_categoria
    }
    produtos {
        int id_produto PK
        int id_categoria FK
        varchar nome_produto
        decimal preco_base
    }
    clientes {
        int id_cliente PK
        varchar nome_completo
        varchar cpf UK
        varchar email UK
        date data_cadastro
    }
    enderecos {
        int id_endereco PK
        int id_cliente FK
        varchar estado
        varchar cidade
    }
    lojas {
        int id_loja PK
        varchar nome_loja
        varchar estado_loja
    }
    vendedores {
        int id_vendedor PK
        int id_loja FK
        varchar nome_vendedor
    }
    metodos_pagamento {
        int id_metodo PK
        varchar tipo_pagamento
    }
    pedidos {
        int id_pedido PK
        int id_cliente FK
        int id_loja FK
        int id_vendedor FK
        timestamp data_pedido
        varchar status_pedido
    }
    itens_pedido {
        int id_item PK
        int id_pedido FK
        int id_produto FK
        int quantidade
        decimal preco_unitario
    }
    pagamentos_pedido {
        int id_pagamento PK
        int id_pedido FK
        int id_metodo FK
        decimal valor_pago
        timestamp data_pagamento
    }
```

---

## Star Schema (Camada Gold)

Na camada Gold, os dados são organizados em um modelo **Star Schema** otimizado para análise.

```mermaid
erDiagram
    fato_vendas }o--|| dim_clientes : "sk_cliente"
    fato_vendas }o--|| dim_produtos : "sk_produto"
    fato_vendas }o--|| dim_lojas : "sk_loja"
    fato_vendas }o--|| dim_vendedores : "sk_vendedor"
    fato_vendas }o--|| dim_metodos_pagamento : "sk_metodo"

    fato_vendas {
        int id_pedido
        int id_item
        string sk_cliente FK
        string sk_produto FK
        string sk_loja FK
        string sk_vendedor FK
        string sk_metodo FK
        timestamp data_pedido
        string status_pedido
        int quantidade
        decimal preco_unitario
        decimal valor_total_item
        decimal valor_total_pago_pedido
        timestamp _gold_processed_at
    }
    dim_clientes {
        string sk_cliente PK
        int id_cliente
        string nome_cliente
        string cidade
        string estado
        timestamp data_inicio_vigencia
        timestamp data_fim_vigencia
        boolean registro_ativo
    }
    dim_produtos {
        string sk_produto PK
        int id_produto
        string nome_produto
        decimal preco_base
        string nome_categoria
        timestamp data_inicio_vigencia
        timestamp data_fim_vigencia
        boolean registro_ativo
    }
    dim_lojas {
        string sk_loja PK
        int id_loja
        string nome_loja
        string estado_loja
        timestamp data_inicio_vigencia
        timestamp data_fim_vigencia
        boolean registro_ativo
    }
    dim_vendedores {
        string sk_vendedor PK
        int id_vendedor
        string nome_vendedor
        string nome_loja
        timestamp data_inicio_vigencia
        timestamp data_fim_vigencia
        boolean registro_ativo
    }
    dim_metodos_pagamento {
        string sk_metodo PK
        int id_metodo
        string tipo_pagamento
        timestamp data_inicio_vigencia
        timestamp data_fim_vigencia
        boolean registro_ativo
    }
```

---

## Tabelas Dimensão (SCD Tipo 2)

!!! info "Slowly Changing Dimension Tipo 2"
    Todas as dimensões implementam SCD2, mantendo histórico completo de alterações.

| Tabela | Chave Substituta | Fonte Silver | Colunas Rastreadas |
|---|---|---|---|
| `dim_clientes` | `sk_cliente` (MD5) | `clientes` + `enderecos` | `nome_completo`, `cidade`, `estado` |
| `dim_produtos` | `sk_produto` (MD5) | `produtos` + `categorias` | `nome_produto`, `preco_base`, `nome_categoria` |
| `dim_lojas` | `sk_loja` (MD5) | `lojas` | `nome_loja`, `estado_loja` |
| `dim_vendedores` | `sk_vendedor` (MD5) | `vendedores` + `lojas` | `nome_vendedor`, `nome_loja` |
| `dim_metodos_pagamento` | `sk_metodo` (MD5) | `metodos_pagamento` | `tipo_pagamento` |

---

## Tabela Fato

| Tabela | Grão | Fonte Silver | Métricas |
|---|---|---|---|
| `fato_vendas` | Item de pedido (`id_item`) | `pedidos` + `itens_pedido` + `pagamentos_pedido` | `valor_total_item`, `valor_total_pago_pedido` |

---

## Volume de Dados

| Tabela | Registros Aproximados |
|---|---|
| `categorias` | ~10 |
| `produtos` | ~200 |
| `clientes` | ~500 |
| `enderecos` | ~500 |
| `lojas` | ~5 |
| `vendedores` | ~20 |
| `metodos_pagamento` | ~4 |
| `pedidos` | ~10.000+ |
| `itens_pedido` | ~26.000+ |
| `pagamentos_pedido` | ~10.000+ |
