# 🚀 Trabalho Final: Engenharia de Dados

Bem-vindo à documentação do projeto final de Engenharia de Dados! 

Este projeto simula um pipeline completo de dados, desde a geração na origem transacional até o armazenamento no Data Lake local (MinIO) estruturado em camadas.

## 🏗️ Arquitetura e Serviços do Docker Compose

O arquivo `docker-compose.yml` gerencia os seguintes contêineres:

1. **PostgreSQL (`postgres-origem`)**: Banco de dados relacional que atua como a origem transacional.
   - O schema (`init_schema.sql`) é inicializado automaticamente no primeiro boot.
2. **MinIO (`minio`)**: Object storage que atua como nosso Data Lake local.
   - **Porta 9000**: API para conexões de dados (Spark, Airflow).
   - **Porta 9001**: Console web para visualização dos arquivos.
3. **Setup MinIO (`minio-init`)**: Configuração inicial automática que cria os buckets da arquitetura medalhão:
   - `landing`
   - `bronze`
   - `silver`
   - `gold`
4. **MkDocs (`mkdocs`)**: Servidor de documentação (este site).
   - **Porta 8000**: Acesso à documentação interativa.

## 📁 Estrutura de Pastas do Projeto

- [docker-compose.yml](file:///home/mendax/trabalho-final-eng-dados/docker-compose.yml): Orquestração de contêineres.
- [init_schema.sql](file:///home/mendax/trabalho-final-eng-dados/init_schema.sql): Script SQL de criação das tabelas.
- [faker_generator.py](file:///home/mendax/trabalho-final-eng-dados/faker_generator.py): Script Python para alimentar o banco de dados.
- [origem_dados.md](file:///home/mendax/trabalho-final-eng-dados/origem_dados.md): Detalhes da geração e modelagem da origem.
# Bem-vindo ao Datalake Ecommerce

Documentação técnica do projeto de Engenharia de Dados, cobrindo a arquitetura em medalhão (Bronze, Silver, Gold), modelagem dimensional e os mecanismos de resiliência e qualidade de dados implementados.

## Módulos Principais

- **[Fato Vendas](fato_vendas.md):** A principal tabela de fatos do negócio, consolidando os pedidos, itens e informações de pagamentos, além das métricas agregadas.
- **[Dimensões (SCD2)](dimensoes.md):** O modelo dimensional que armazena dados de contexto (Lojas, Clientes, Produtos, etc.) guardando o histórico temporal através de Slowly Changing Dimensions do Tipo 2.
- **[Checkpoints e Idempotência](checkpoints.md):** Como a aplicação garante que cargas parciais não quebrem o pipeline e que dados não sejam processados em duplicidade.
