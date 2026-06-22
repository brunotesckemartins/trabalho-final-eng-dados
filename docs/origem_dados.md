# 🗄️ Origem de Dados: E-commerce Sintético

Para simular um ambiente transacional realista, a origem de dados deste projeto foi construída do zero, simulando o banco de dados relacional de um E-commerce.

A base foi instanciada em um banco de dados **PostgreSQL** e estruturada com 10 tabelas interligadas, divididas entre tabelas dimensionais (cadastros) e tabelas fato (eventos transacionais).

## 🛠️ Tecnologias Utilizadas
* **PostgreSQL (Docker):** Hospedagem do banco relacional.
* **Python (Pandas & SQLAlchemy):** Geração, manipulação e injeção massiva de dados.
* **Python (Pandas & SQLAlchemy):** Manipulação e injeção massiva de dados.
* **Faker (pt_BR):** Geração de dados fictícios em padrão brasileiro (Nomes, CPFs, Cidades, Datas).

## 📊 Estrutura do Banco (MER)
O banco `ecommerce_db` possui a seguinte estrutura de tabelas:

**Tabelas de Dimensão/Apoio:**
1. `categorias`
2. `produtos`
3. `clientes`
4. `enderecos`
5. `lojas`
6. `vendedores`
7. `metodos_pagamento`

**Tabelas Fato (Principais):**
8. `pedidos` (+10.000 registros)
9. `itens_pedido` (+26.000 registros)
10. `pagamentos_pedido`

## ⚙️ Premissas Cumpridas
* **Volume:** As tabelas principais ultrapassam a marca exigida de 10.000 linhas.
* **Distribuição Temporal:** A lógica de geração em Python distribuiu as datas de compra ao longo dos últimos 3 anos, garantindo variabilidade de dados para a futura construção do Dashboard.

## 🚀 Como reproduzir este ambiente
Caso precise recriar a origem de dados, siga os passos abaixo:
1. Garanta que o contêiner `postgres-origem` do Docker Compose está rodando.
2. Com a nova configuração do docker-compose, a estrutura vazia é criada automaticamente ao inicializar o banco através do script `init_schema.sql` montado em `/docker-entrypoint-initdb.d/`.
3. Crie um ambiente virtual Python e instale as dependências: `pip install faker pandas sqlalchemy psycopg2-binary`.
2. Execute o arquivo `init_schema.sql` diretamente no banco para criar a estrutura vazia.
3. Utilize o uv para instalar as dependências e criar o ambiente virtual de forma rápida: `uv sync`.
4. Execute o script `faker_generator.py` para gerar os dados em memória e injetá-los no banco de dados.
