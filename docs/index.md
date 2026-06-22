# Pipeline de Engenharia de Dados — E-commerce

Documentação técnica do projeto final de Engenharia de Dados. O pipeline implementa a **arquitetura medalhão** completa — Landing → Bronze → Silver → Gold — sobre um e-commerce sintético, com um dashboard analítico em Streamlit.

## Fluxo de Dados

```
PostgreSQL (origem)
      │  Airflow: extração diária
      ▼
  Landing Zone  — MinIO / bucket landing  (CSV raw)
      │  Spark: landing_to_bronze.py
      ▼
    Bronze      — MinIO / bucket bronze   (Delta Lake, append)
      │  Spark: bronze_to_silver.py
      ▼
    Silver      — MinIO / bucket silver   (Delta Lake, upsert)
      │  Spark: gold/run_dimensions.py + gold/facts/fato_vendas.py
      ▼
     Gold       — MinIO / bucket gold     (Delta Lake, SCD Tipo 2)
      │  DuckDB lê via extensão delta + httpfs
      ▼
  Dashboard     — Streamlit (4 KPIs + 2 métricas)
```

## Módulos Principais

- **[Origem dos Dados](origem_dados.md):** Banco PostgreSQL sintético com 10 tabelas e ~50k linhas.
- **[Ingestão / Landing Zone](ingestao_landing.md):** Extração via Airflow, upload CSV para MinIO.
- **[Bronze](bronze.md):** CSV → Delta Lake (append-only, schema bruto).
- **[Silver](silver.md):** Bronze → Delta Lake (upsert, tipado, deduplicado, regras de qualidade).
- **[Dimensões SCD2](dimensoes.md):** Silver → Gold, 5 dimensões com Slowly Changing Dimension Tipo 2.
- **[Fato Vendas](fato_vendas.md):** Silver + dimensões Gold → tabela fato no grão de item.
- **[Checkpoints](checkpoints.md):** Watermark Delta Lake para cargas incrementais idempotentes.
- **[Visualização](visualizacao.md):** DuckDB + views + dashboard Streamlit.

## Serviços Docker

| Serviço | Porta | Descrição |
|---|---|---|
| MinIO Console | 9001 | Interface do Data Lake |
| Airflow | 8080 | Orquestração do pipeline |
| MkDocs | 8000 | Esta documentação |
| PostgreSQL (origem) | 5432 | Banco relacional de origem |
