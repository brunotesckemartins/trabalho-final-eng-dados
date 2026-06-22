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

## Views de Virtualização

| View | Propósito |
|---|---|
| `vw_vendas_detalhadas` | Join entre `fato_vendas` e todas as dimensões ativas (versão vigente SCD2) |

## Indicadores do Dashboard

### KPIs

| # | Indicador | Lógica | Fonte |
|---|---|---|---|
| 1 | Receita Total | `SUM(valor_total_item)` — pedidos `Concluído` | `vw_vendas_detalhadas` |
| 2 | Total de Pedidos | `COUNT(DISTINCT id_pedido)` — todos os status | `vw_vendas_detalhadas` |
| 3 | Ticket Médio | Receita Total / Pedidos `Concluído` | `vw_vendas_detalhadas` |
| 4 | Clientes Únicos | `COUNT(DISTINCT sk_cliente)` | `fato_vendas` |

### Métricas

| # | Indicador | Lógica | Visualização |
|---|---|---|---|
| 1 | Receita por Categoria | `SUM(valor_total_item)` agrupado por `nome_categoria` | Gráfico de barras |
| 2 | Evolução Mensal | `SUM(valor_total_item)` agrupado por mês | Gráfico de linha |

## Como Executar

```bash
streamlit run visualization/dashboard.py
```
