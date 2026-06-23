# 🔄 Orquestração — Apache Airflow

## Visão Geral

O **Apache Airflow** é o orquestrador central do pipeline. Todas as etapas — desde a extração do PostgreSQL até a carga na camada Gold — são executadas automaticamente pela DAG principal.

!!! success "Sem cron jobs"
    Nenhuma tarefa utiliza cron do Linux ou Agendador de Tarefas do Windows. Toda a orquestração é feita pelo Airflow.

---

## DAG Principal

**Nome:** `orquestracao_medalhao_end_to_end`  
**Agendamento:** `@daily`  
**Arquivo:** `dags/ingestao_landing_zone.py`

### Fluxo de Execução

```mermaid
flowchart TD
    START(["▶ Início"]) --> EXT

    subgraph EXT ["📥 Extração"]
        direction LR
        T1["categorias"]
        T2["produtos"]
        T3["clientes"]
        T4["enderecos"]
        T5["lojas"]
        T6["vendedores"]
        T7["metodos_pagamento"]
        T8["pedidos"]
        T9["itens_pedido"]
        T10["pagamentos_pedido"]
    end

    EXT --> BRONZE["🥉 Landing → Bronze\nspark-submit landing_to_bronze.py"]
    BRONZE --> SILVER["🥈 Bronze → Silver\nspark-submit bronze_to_silver.py"]
    SILVER --> DIMS["⭐ Silver → Gold: Dimensões\nspark-submit run_dimensions.py"]
    DIMS --> FATO["⭐ Silver → Gold: Fato Vendas\nspark-submit fato_vendas.py"]
    FATO --> FIM(["✅ Fim"])

    style START fill:#4caf50,stroke:#fff,color:#fff
    style FIM fill:#4caf50,stroke:#fff,color:#fff
    style EXT fill:#ff9800,stroke:#333
    style BRONZE fill:#cd7f32,stroke:#fff,color:#fff
    style SILVER fill:#c0c0c0,stroke:#333
    style DIMS fill:#ffd700,stroke:#333
    style FATO fill:#ffd700,stroke:#333
```

---

## Etapas da DAG

### 1. Extração (PostgreSQL → Landing)

!!! note "10 tasks paralelas"
    Uma task `PythonOperator` é gerada dinamicamente para cada tabela. Se uma falhar, as demais continuam.

- **Método:** `pandas` + `SQLAlchemy` para leitura, `boto3` para upload ao MinIO
- **Formato de saída:** CSV bruto
- **Destino:** `s3a://landing/<tabela>/<tabela>_raw.csv`
- **Validação:** Tabelas vazias lançam `ValueError`, abortando a task

### 2. Landing → Bronze

- **Job:** `spark-submit pipeline/landing_to_bronze.py`
- **Lógica:** Lê CSV, adiciona colunas de auditoria, grava em Delta Lake (append)
- **Schema:** Todas as colunas como `StringType`

### 3. Bronze → Silver

- **Job:** `spark-submit pipeline/bronze_to_silver.py`
- **Lógica:** Deduplica, tipa, aplica regras de qualidade, grava via MERGE (upsert)
- **Schema:** Tipos corretos conforme `schemas.py`

### 4. Silver → Gold: Dimensões

- **Job:** `spark-submit gold/run_dimensions.py`
- **Lógica:** Aplica SCD Tipo 2 em 5 dimensões

### 5. Silver → Gold: Fato Vendas

- **Job:** `spark-submit gold/facts/fato_vendas.py`
- **Lógica:** Carga incremental via checkpoints, join temporal com dimensões

---

## Acesso ao Airflow

| Propriedade | Valor |
|---|---|
| **URL** | [http://localhost:8080](http://localhost:8080) |
| **Usuário** | `admin` |
| **Senha** | `admin` |
| **Executor** | `LocalExecutor` |

---

## Como Executar a DAG

1. Acesse **http://localhost:8080** e faça login
2. Localize a DAG `orquestracao_medalhao_end_to_end`
3. Ative clicando no **toggle** (deve ficar azul)
4. Clique em **Trigger DAG** (ícone ▶)
5. Acompanhe em **Graph View**

!!! warning "Tempo de execução"
    A execução completa leva entre **5 e 15 minutos** dependendo do hardware.

---

## Módulos Auxiliares

```
dags/
├── ingestao_landing_zone.py   # DAG principal
└── utils/
    ├── config.py              # Credenciais PostgreSQL + MinIO
    ├── db_extractor.py        # Extração PostgreSQL → buffer
    └── storage_loader.py      # Upload buffer → MinIO
```

| Módulo | Responsabilidade |
|---|---|
| `config.py` | Centraliza credenciais dos containers Docker |
| `db_extractor.py` | Lê tabela do PostgreSQL via pandas, valida dados e retorna buffer CSV |
| `storage_loader.py` | Recebe buffer e faz upload via boto3 para o MinIO |
