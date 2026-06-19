# trabalho-final-eng-dados

## 🚰 Camada de Ingestão e Landing Zone

A ingestão de dados da origem relacional (PostgreSQL) para o Data Lake (MinIO) é 100% orquestrada pelo **Apache Airflow**, sem o uso de agendadores de sistema operacional.

**Tecnologias Utilizadas:**
* **Apache Airflow:** Orquestração dinâmica diária (`@daily`) do pipeline.
* **SQLAlchemy & Pandas:** Conexão robusta e extração massiva em buffers de memória (RAM).
* **Boto3:** Cliente S3 para upload direto no bucket do object storage.

**Regras de Negócio Implementadas:**
1. **Formato Bruto Original:** Atendendo aos requisitos da arquitetura, os dados extraídos do ambiente relacional SQL são salvos na camada `landing` no formato `.csv`.
2. **Otimização de I/O:** Os arquivos não são gravados no disco local (`io.BytesIO`). O fluxo vai direto do banco para a memória, e da memória para o Data Lake.
3. **Data Quality Check:** A pipeline verifica a propriedade `.empty` das tabelas extraídas. Se o banco relacional retornar zero registros para uma dimensão ou fato, a task falha de forma controlada (`ValueError`), evitando o envio de lixo digital ou arquivos vazios para o storage.
