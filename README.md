# Pipeline de Engenharia de Dados — E-commerce

Projeto final de Engenharia de Dados. Implementa uma arquitetura **medalhão** completa (Landing → Bronze → Silver → Gold) para um e-commerce sintético, com dashboard analítico em Streamlit.

## Arquitetura

```
PostgreSQL (origem)
      │  extração via Airflow (pandas + boto3)
      ▼
  Landing Zone  ─── MinIO / bucket landing  (CSV raw, _raw.csv)
      │  spark-submit landing_to_bronze.py
      ▼
    Bronze      ─── MinIO / bucket bronze   (Delta Lake, append)
      │  spark-submit bronze_to_silver.py
      ▼
    Silver      ─── MinIO / bucket silver   (Delta Lake, upsert tipado)
      │  spark-submit gold/run_dimensions.py
      │  spark-submit gold/facts/fato_vendas.py
      ▼
     Gold       ─── MinIO / bucket gold     (Delta Lake, SCD Tipo 2)
      │  DuckDB lê as tabelas Delta via extensão delta + httpfs
      ▼
  Dashboard     ─── Streamlit               (4 KPIs + 2 métricas)
```

Toda a orquestração é feita pelo **Apache Airflow** com uma DAG diária (`@daily`).

## Stack

| Camada | Tecnologia |
|---|---|
| Origem | PostgreSQL 15 |
| Object Storage | MinIO (S3-compatible) |
| Processamento | PySpark 3.5.1 + Delta Lake 3.2.0 |
| Orquestração | Apache Airflow 2.9.1 |
| Virtualização | DuckDB 1.1.3 |
| Dashboard | Streamlit 1.35.0 + Plotly |
| Infra local | Docker Compose |

## Estrutura do Projeto

```
trabalho-final-eng-dados/
├── config.py              # Configuração Spark + MinIO (compartilhada)
├── schemas.py             # Schemas e chaves primárias das 10 tabelas
│
├── pipeline/              # Jobs Spark: Bronze e Silver
│   ├── landing_to_bronze.py   # Landing (CSV) → Bronze (Delta, append)
│   ├── bronze_to_silver.py    # Bronze → Silver (Delta, upsert tipado)
│   └── run_all_tables.py      # Utilitário local: roda todas as tabelas
│
├── dags/                  # Orquestração Airflow
│   ├── ingestao_landing_zone.py   # DAG principal end-to-end
│   └── utils/
│       ├── config.py          # Credenciais PostgreSQL + MinIO (containers)
│       ├── db_extractor.py    # Extração PostgreSQL → buffer em memória
│       └── storage_loader.py  # Upload buffer → MinIO/landing
│
├── gold/                  # Camada Gold (Star Schema + SCD Tipo 2)
│   ├── config.py
│   ├── run_dimensions.py      # Orquestra todas as dimensões
│   ├── read_silver.py         # Utilitários de leitura da Silver
│   ├── validate_setup.py      # Validação de estrutura Gold
│   ├── dimensions/            # 5 dimensões SCD Tipo 2
│   │   ├── dim_clientes.py
│   │   ├── dim_lojas.py
│   │   ├── dim_metodos_pagamento.py
│   │   ├── dim_produtos.py
│   │   └── dim_vendedores.py
│   ├── facts/
│   │   └── fato_vendas.py     # Fato no grão de item (incremental)
│   ├── utils/                 # Utilitários SCD2, checkpoint, validação
│   │   ├── scd2.py
│   │   ├── checkpoint_manager.py
│   │   ├── change_detector.py
│   │   ├── incremental_loader.py
│   │   ├── record_closer.py
│   │   ├── version_inserter.py
│   │   └── delta_validator.py
│   ├── scripts/               # Scripts operacionais (otimização, QA)
│   │   ├── persist_dimensions.py
│   │   └── validate_fact_compatibility.py
│   └── tests/                 # Testes da camada Gold
│
├── visualization/         # Camada de consumo analítico
│   ├── config.py              # DuckDB + conexão MinIO
│   ├── setup_db.py            # Provisiona o DuckDB
│   ├── gold_reader.py         # Registra tabelas Gold como views DuckDB
│   ├── views.sql              # View vw_vendas_detalhadas
│   ├── create_views.py        # Cria as views no DuckDB
│   ├── queries.py             # Queries SQL dos indicadores
│   ├── kpis.py                # 4 KPIs obrigatórios
│   ├── metrics.py             # 2 métricas obrigatórias
│   ├── dashboard.py           # Dashboard Streamlit (One Page View)
│   └── tests/
│       └── test_validacao.py  # Validação dashboard vs. Gold
│
├── scripts/               # Utilitários de desenvolvimento
│   ├── faker_generator.py     # Geração de dados sintéticos no PostgreSQL
│   └── extract_to_landing.py  # Extração manual (alternativa à DAG)
│
├── docs/                  # Documentação MkDocs
├── init_schema.sql        # Schema do PostgreSQL de origem
├── docker-compose.yml     # Todos os serviços
├── Dockerfile.airflow     # Imagem Airflow com PySpark + Java
├── requirements.txt       # Dependências Python (ambiente local)
└── .env.example           # Modelo de variáveis de ambiente
```

## Como Executar

### 1. Pré-requisitos

- Docker e Docker Compose instalados
- Python 3.11+ (para execução local fora do Docker)

### 2. Subir a infraestrutura

```bash
docker compose up -d
```

Serviços disponíveis:
- **MinIO Console**: http://localhost:9001 (admin / adminpassword)
- **Airflow**: http://localhost:8080 (admin / admin)
- **MkDocs**: http://localhost:8000
- **Metabase**: http://localhost:3000

### 3. Popular o banco de dados

```bash
python scripts/faker_generator.py
```

### 4. Executar o pipeline via Airflow

Acesse http://localhost:8080, habilite a DAG `orquestracao_medalhao_end_to_end` e dispare manualmente.

### 5. Rodar o dashboard

```bash
# Copie e configure as variáveis de ambiente
cp .env.example .env

# Instale as dependências de visualização
pip install duckdb streamlit plotly

# Inicie o dashboard
streamlit run visualization/dashboard.py
```

### 6. Executar os testes

```bash
# Validação do dashboard contra a camada Gold
python visualization/tests/test_validacao.py
```

## Modelo de Dados (Gold)

### Dimensões (SCD Tipo 2)

| Tabela | Chave Substituta | Fonte Silver |
|---|---|---|
| `dim_clientes` | `sk_cliente` | `clientes` + `enderecos` |
| `dim_produtos` | `sk_produto` | `produtos` + `categorias` |
| `dim_lojas` | `sk_loja` | `lojas` |
| `dim_vendedores` | `sk_vendedor` | `vendedores` + `lojas` |
| `dim_metodos_pagamento` | `sk_metodo` | `metodos_pagamento` |

### Fato

| Tabela | Grão | Fonte Silver |
|---|---|---|
| `fato_vendas` | Item de pedido | `pedidos` + `itens_pedido` + `pagamentos_pedido` |

### Colunas de controle SCD Tipo 2

| Coluna | Descrição |
|---|---|
| `data_inicio_vigencia` | Quando o registro passou a ser válido |
| `data_fim_vigencia` | Quando deixou de ser válido (nulo = ativo) |
| `registro_ativo` | `true` = versão atual, `false` = histórico |

## Dashboard

4 KPIs e 2 métricas na página principal:

| Tipo | Indicador |
|---|---|
| KPI | Receita Total (pedidos Concluído) |
| KPI | Total de Pedidos (todos os status) |
| KPI | Ticket Médio |
| KPI | Clientes Únicos |
| Métrica | Receita por Categoria (gráfico de barras) |
| Métrica | Evolução Mensal de Receita (gráfico de linha) |

## Documentação

Disponível em http://localhost:8000 (MkDocs Material) ou em `docs/`.
