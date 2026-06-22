# Camada de Visualização

## Banco de Virtualização

**Banco escolhido:** DuckDB  
**Justificativa:** banco embarcado orientado a análise, sem necessidade de serviço externo adicional. Lê tabelas Delta Lake diretamente do MinIO via extensões `httpfs` (acesso S3) e `delta` (formato Delta Lake).

**Configuração:** credenciais via variáveis de ambiente (sem exposição no repositório).

| Variável | Padrão | Descrição |
|---|---|---|
| `DUCKDB_PATH` | `visualization/analytics.duckdb` | Caminho do arquivo DuckDB |
| `MINIO_ENDPOINT` | `http://localhost:9000` | Endpoint do MinIO |
| `MINIO_ACCESS_KEY` | `admin` | Chave de acesso |
| `MINIO_SECRET_KEY` | `adminpassword` | Chave secreta |

## Estrutura de Artefatos

```
visualization/
├── config.py          # Configuração do DuckDB e credenciais MinIO
├── setup_db.py        # Provisionamento e validação do banco
├── gold_reader.py     # Leitura das tabelas Delta Lake da camada Gold
├── views.sql          # Scripts SQL das views de virtualização
├── create_views.py    # Criação das views no DuckDB
├── queries.py         # Consultas de agregação para KPIs e métricas
├── kpis.py            # Cálculo dos 4 KPIs obrigatórios
├── metrics.py         # Cálculo das 2 métricas obrigatórias
├── dashboard.py       # Dashboard One Page View (Streamlit)
└── tests/
    └── test_validacao.py  # Validação dos dados do dashboard vs. Gold
```

## Tabelas Gold Consumidas

Antes de criar as views, `gold_reader.py` registra as tabelas Gold como views no DuckDB. Dimensões são filtradas por `registro_ativo = true` (versão vigente SCD2).

| Tabela Gold | Tipo | Campos principais |
|---|---|---|
| `fato_vendas` | Fato | `id_pedido`, `id_item`, `sk_cliente`, `sk_produto`, `sk_loja`, `sk_vendedor`, `sk_metodo`, `data_pedido`, `status_pedido`, `quantidade`, `preco_unitario`, `valor_total_item`, `valor_total_pago_pedido` |
| `dim_clientes` | Dimensão (SCD2) | `sk_cliente`, `id_cliente`, `nome_cliente`, `cidade`, `estado` |
| `dim_produtos` | Dimensão (SCD2) | `sk_produto`, `id_produto`, `nome_produto`, `preco_base`, `nome_categoria` |
| `dim_lojas` | Dimensão (SCD2) | `sk_loja`, `id_loja`, `nome_loja`, `estado_loja` |
| `dim_vendedores` | Dimensão (SCD2) | `sk_vendedor`, `id_vendedor`, `nome_vendedor`, `nome_loja` |
| `dim_metodos_pagamento` | Dimensão (SCD2) | `sk_metodo`, `id_metodo`, `tipo_pagamento` |

## Views de Virtualização

### `vw_vendas_detalhadas`

**Propósito:** une `fato_vendas` com todas as dimensões ativas (versão vigente SCD2), expondo os campos necessários para KPIs e métricas do dashboard em uma única superfície de consulta.

**Tabelas de origem:** `fato_vendas`, `dim_clientes`, `dim_produtos`, `dim_lojas`, `dim_vendedores`, `dim_metodos_pagamento`.

**Campos expostos:**

| Campo | Origem | Descrição |
|---|---|---|
| `id_pedido` | `fato_vendas` | Identificador do pedido |
| `id_item` | `fato_vendas` | Identificador do item no pedido |
| `data_pedido` | `fato_vendas` | Data de realização do pedido |
| `status_pedido` | `fato_vendas` | Status atual (`Concluído`, `Pendente`, `Cancelado`) |
| `quantidade` | `fato_vendas` | Quantidade de unidades do item |
| `preco_unitario` | `fato_vendas` | Preço unitário do produto no momento da venda |
| `valor_total_item` | `fato_vendas` | Receita do item (`quantidade × preco_unitario`) |
| `valor_total_pago_pedido` | `fato_vendas` | Valor total pago no pedido (soma dos itens) |
| `nome_cliente` | `dim_clientes` | Nome do cliente |
| `cidade_cliente` | `dim_clientes` | Cidade de origem do cliente |
| `estado_cliente` | `dim_clientes` | Estado de origem do cliente |
| `nome_produto` | `dim_produtos` | Nome do produto |
| `preco_base` | `dim_produtos` | Preço base cadastrado no catálogo |
| `nome_categoria` | `dim_produtos` | Categoria do produto |
| `nome_loja` | `dim_lojas` | Nome da loja |
| `estado_loja` | `dim_lojas` | Estado onde a loja está localizada |
| `nome_vendedor` | `dim_vendedores` | Nome do vendedor responsável |
| `tipo_pagamento` | `dim_metodos_pagamento` | Método de pagamento utilizado |

**SQL:**

```sql
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
```

## Indicadores do Dashboard

### KPIs

#### KPI 1 — Receita Total

**Definição:** soma de `valor_total_item` de todos os itens de pedidos com `status_pedido = 'Concluído'`.  
**Fonte:** `vw_vendas_detalhadas`

```sql
SELECT COALESCE(SUM(valor_total_item), 0) AS receita_total
FROM vw_vendas_detalhadas
WHERE status_pedido = 'Concluído'
```

---

#### KPI 2 — Total de Pedidos

**Definição:** contagem distinta de `id_pedido`, incluindo todos os status (Concluído, Pendente, Cancelado).  
**Fonte:** `vw_vendas_detalhadas`

```sql
SELECT COUNT(DISTINCT id_pedido) AS total_pedidos
FROM vw_vendas_detalhadas
```

---

#### KPI 3 — Ticket Médio

**Definição:** receita total dividida pelo número de pedidos concluídos. Retorna 0 se não houver pedidos.  
**Fonte:** `vw_vendas_detalhadas`

```sql
SELECT COALESCE(
    SUM(valor_total_item) / NULLIF(COUNT(DISTINCT id_pedido), 0),
    0
) AS ticket_medio
FROM vw_vendas_detalhadas
WHERE status_pedido = 'Concluído'
```

---

#### KPI 4 — Clientes Únicos

**Definição:** contagem distinta de `sk_cliente` na tabela fato, representando o total de clientes distintos que realizaram ao menos um pedido.  
**Fonte:** `fato_vendas`

```sql
SELECT COUNT(DISTINCT sk_cliente) AS clientes_unicos
FROM fato_vendas
```

### Métricas

#### Métrica 1 — Receita por Categoria de Produto

**Definição:** soma de `valor_total_item` agrupada por `nome_categoria`, considerando apenas pedidos concluídos. Ordenada de forma decrescente.  
**Visualização:** gráfico de barras  
**Fonte:** `vw_vendas_detalhadas`

```sql
SELECT
    nome_categoria,
    COALESCE(SUM(valor_total_item), 0) AS receita
FROM vw_vendas_detalhadas
WHERE status_pedido = 'Concluído'
GROUP BY nome_categoria
ORDER BY receita DESC
```

---

#### Métrica 2 — Evolução Mensal de Receita

**Definição:** soma de `valor_total_item` agrupada por mês (truncado via `DATE_TRUNC`), para pedidos concluídos. Exibe a tendência de receita ao longo do tempo.  
**Visualização:** gráfico de linha  
**Fonte:** `vw_vendas_detalhadas`

```sql
SELECT
    DATE_TRUNC('month', data_pedido) AS mes,
    COALESCE(SUM(valor_total_item), 0) AS receita
FROM vw_vendas_detalhadas
WHERE status_pedido = 'Concluído'
GROUP BY mes
ORDER BY mes
```

## Como Executar o Dashboard

### Pré-requisitos

- Infraestrutura em execução via Docker Compose (MinIO com as tabelas Gold carregadas).
- Python 3.11+ com [UV](https://github.com/astral-sh/uv) instalado.
- Dependências do projeto instaladas:

```bash
uv sync
```

### Variáveis de Ambiente

Configure as credenciais do MinIO caso os valores padrão não se apliquem:

```bash
export MINIO_ENDPOINT=http://localhost:9000
export MINIO_ACCESS_KEY=admin
export MINIO_SECRET_KEY=adminpassword
```

### Executar

```bash
uv run streamlit run visualization/dashboard.py
```

O dashboard abrirá automaticamente no navegador em `http://localhost:8501`.

### Fluxo de Inicialização

Ao iniciar, o dashboard executa automaticamente:

1. `get_connection()` — abre a conexão DuckDB com as extensões `httpfs` e `delta`.
2. `load_gold_tables()` — registra as tabelas Delta Lake do MinIO como views no DuckDB.
3. `create_views()` — cria `vw_vendas_detalhadas` a partir das tabelas Gold.

Os resultados são cacheados via `@st.cache_resource`, evitando re-execução a cada interação.
