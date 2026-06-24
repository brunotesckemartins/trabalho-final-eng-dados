# Pipeline de Engenharia de Dados — E-commerce:

Projeto final de Engenharia de Dados. Simula o pipeline de dados de um e-commerce sintético, implementando a **arquitetura medalhão** completa (Landing → Bronze → Silver → Gold) sobre um Data Lake local, com orquestração via Apache Airflow e dashboard analítico em Streamlit.

Os dados são gerados com Faker, armazenados no PostgreSQL (origem), extraídos e processados pelo Spark em camadas Delta Lake no MinIO (Data Lake), e consumidos via DuckDB no dashboard final.

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

## Tecnologias

| Camada                        | Tecnologia            | Versão          |
| ----------------------------- | --------------------- | --------------- |
| Origem                        | PostgreSQL            | 15              |
| Object Storage                | MinIO (S3-compatible) | latest          |
| Processamento                 | PySpark + Delta Lake  | 3.5.1 + 3.2.0   |
| Orquestração                  | Apache Airflow        | 2.9.1           |
| Virtualização                 | DuckDB                | 1.1.3           |
| Dashboard                     | Streamlit + Plotly    | 1.35.0 + 5.22.0 |
| Gerenciador de pacotes Python | UV                    | latest          |
| Infra local                   | Docker Compose        | —               |

## Pré-requisitos

Instale as ferramentas abaixo antes de continuar:

### Docker

Necessário para subir toda a infraestrutura (PostgreSQL, MinIO, Airflow, MkDocs).

- **Linux:** siga o [guia oficial do Docker Engine](https://docs.docker.com/engine/install/)
- **Windows / macOS:** instale o [Docker Desktop](https://www.docker.com/products/docker-desktop/)

Verifique a instalação:

```bash
docker --version
docker compose version
```

### Python 3.11+

- **Linux / macOS:** use seu gerenciador de pacotes ou [pyenv](https://github.com/pyenv/pyenv)
- **Windows:** baixe em [python.org](https://www.python.org/downloads/)

Verifique:

```bash
python --version
```

### UV

Gerenciador de pacotes Python moderno e rápido. Substitui `pip` + `venv`.

```bash
# Linux / macOS
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Verifique:

```bash
uv --version
```

> Após instalar o UV, reinicie o terminal para que o comando fique disponível.

---

## Execução — Passo a Passo

### 1. Clonar o repositório

```bash
git clone https://github.com/seu-usuario/trabalho-final-eng-dados.git
cd trabalho-final-eng-dados
```

### 2. Configurar variáveis de ambiente

```bash
cp .env.example .env
```

O arquivo `.env` já vem com os valores padrão para o ambiente local. Não é necessário alterá-los para rodar o projeto.

### 3. Instalar as dependências Python

```bash
uv sync
```

Isso cria o ambiente virtual `.venv/` na raiz do projeto e instala todas as dependências listadas no `pyproject.toml`.

Em seguida, ative o ambiente virtual:

```bash
# Linux / macOS
source .venv/bin/activate

# Windows (PowerShell)
.venv\Scripts\Activate.ps1
```

### 4. Subir a infraestrutura

```bash
docker compose up -d
```

Na primeira execução, a imagem do Airflow (com Java + PySpark) será construída, o que pode levar **5 a 10 minutos**. Nas execuções seguintes, será muito mais rápido.

Aguarde os containers subirem completamente antes de prosseguir. Verifique o status:

```bash
docker compose ps
```

Todos os serviços devem estar com status `running`. O `airflow-init` ficará `exited (0)` — isso é normal (ele só inicializa o banco do Airflow e encerra).

Serviços disponíveis após a subida:

| Serviço               | URL                   | Credenciais           |
| --------------------- | --------------------- | --------------------- |
| Airflow               | http://localhost:8080 | admin / admin         |
| MinIO Console         | http://localhost:9001 | admin / adminpassword |
| MkDocs (documentação) | http://localhost:8000 | —                     |
| Metabase              | http://localhost:3000 | —                     |

### 5. Popular o banco de dados

Gera dados sintéticos (clientes, produtos, pedidos, etc.) diretamente no PostgreSQL:

```bash
python scripts/faker_generator.py
```

O script insere aproximadamente 500 clientes, 200 produtos e 1.000 pedidos com itens aleatórios.

### 6. Executar o pipeline via Airflow

1. Acesse **http://localhost:8080** e faça login com `admin` / `admin`
2. Localize a DAG **`orquestracao_medalhao_end_to_end`**
3. Ative a DAG clicando no botão de toggle (deve ficar azul)
4. Clique em **Trigger DAG** (ícone de play ▶) para disparar manualmente
5. Acompanhe a execução clicando no nome da DAG → **Graph View**

A DAG executa as seguintes etapas em sequência:

- Extração do PostgreSQL → Landing Zone (MinIO)
- Landing → Bronze (Delta Lake, append)
- Bronze → Silver (Delta Lake, upsert tipado)
- Silver → Gold: dimensões (SCD Tipo 2) + fato vendas

A execução completa leva entre **5 e 15 minutos** dependendo do hardware.

### 7. Iniciar o dashboard

Após a DAG concluir com sucesso (todos os nós verdes no Airflow), inicie o dashboard:

```bash
streamlit run visualization/dashboard.py
```

Acesse em **http://localhost:8501**.

O dashboard se conecta automaticamente ao MinIO, lê as tabelas Delta Lake da camada Gold via DuckDB e exibe os 4 KPIs e 2 métricas na página principal.

### 8. (Opcional) Validar o dashboard

```bash
python visualization/tests/test_validacao.py
```

Verifica se os valores exibidos no dashboard batem com os dados da camada Gold.

---

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
│   └── utils/                 # Utilitários SCD2, checkpoint, validação
│
├── visualization/         # Camada de consumo analítico
│   ├── config.py              # DuckDB + conexão MinIO
│   ├── setup_db.py            # Valida o DuckDB
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
├── pyproject.toml         # Dependências Python (gerenciadas pelo UV)
├── requirements.txt       # Dependências Python (alternativa pip)
└── .env.example           # Modelo de variáveis de ambiente
```

## Modelo de Dados (Gold)

### Dimensões (SCD Tipo 2)

| Tabela                  | Chave Substituta | Fonte Silver              |
| ----------------------- | ---------------- | ------------------------- |
| `dim_clientes`          | `sk_cliente`     | `clientes` + `enderecos`  |
| `dim_produtos`          | `sk_produto`     | `produtos` + `categorias` |
| `dim_lojas`             | `sk_loja`        | `lojas`                   |
| `dim_vendedores`        | `sk_vendedor`    | `vendedores` + `lojas`    |
| `dim_metodos_pagamento` | `sk_metodo`      | `metodos_pagamento`       |

### Fato

| Tabela        | Grão           | Fonte Silver                                     |
| ------------- | -------------- | ------------------------------------------------ |
| `fato_vendas` | Item de pedido | `pedidos` + `itens_pedido` + `pagamentos_pedido` |

### Colunas de controle SCD Tipo 2

| Coluna                 | Descrição                                  |
| ---------------------- | ------------------------------------------ |
| `data_inicio_vigencia` | Quando o registro passou a ser válido      |
| `data_fim_vigencia`    | Quando deixou de ser válido (nulo = ativo) |
| `registro_ativo`       | `true` = versão atual, `false` = histórico |

## Dashboard

4 KPIs e 2 métricas na página principal:

| Tipo    | Indicador                                     |
| ------- | --------------------------------------------- |
| KPI     | Receita Total (pedidos Concluído)             |
| KPI     | Total de Pedidos (todos os status)            |
| KPI     | Ticket Médio                                  |
| KPI     | Clientes Únicos                               |
| Métrica | Receita por Categoria (gráfico de barras)     |
| Métrica | Evolução Mensal de Receita (gráfico de linha) |

## Documentação

Disponível em (https://brunotesckemartins.github.io/trabalho-final-eng-dados/) (MkDocs Material) ou na pasta `docs/`.
