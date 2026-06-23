# 📊 Visualização de Dados (Dashboard)

A última camada da nossa arquitetura representa a área de consumo de negócios, onde os dados da Camada Gold são virtualizados e transformados em painéis gerenciais.

No lugar de instanciar pesados conectores diretos no Apache Spark ou conectar ferramentas tradicionais complexas, optamos por uma solução moderna, ágil (In-Memory) e *Open Source* para nosso *One Page View*.

---

## 🛠️ Stack Tecnológica de Consumo

*   **DuckDB:** Funciona como nosso motor SQL In-Memory e ferramenta de Virtualização. Ele consome diretamente os metadados e os aquivos parquet dentro da estrutura Delta Lake do MinIO.
*   **Streamlit:** Biblioteca em Python que cria a aplicação Web (Front-End) baseada em Python puro para plotagem de gráficos dinâmicos com **Plotly**.

---

## 📈 Dashboard One Page View

Nosso painel concentra 4 KPIs macro para acompanhamento diário das lideranças e 2 Métricas profundas (Múltiplas variáveis).

### KPIs Principais

1.  **Faturamento Bruto Consolidado:** Soma da `fato_vendas` ao longo do tempo.
2.  **Quantidade Total de Vendas Realizadas:** Volume de transações no E-commerce.
3.  **Ticket Médio Global:** Faturamento total / Volume total de pedidos.
4.  **Média de Produtos por Pedido:** Itens transacionados divididos pelo montante de checkouts.

### Métricas Analíticas

1.  **Curva ABC de Vendas por Categoria de Produto:** Gráfico de Pareto demonstrando as categorias que trazem maior concentração de receita para o negócio.
2.  **Evolução de Pedidos vs Meio de Pagamento:** Análise temporal e proporcional avaliando a preferência dos usuários na hora de finalizar o carrinho.

---

## ⚙️ Como Iniciar a Visualização

Garantindo que todos os contêineres Docker estejam ativos e a Pipeline do Airflow já tenha rodado ao menos 1 vez popularizando o `s3a://gold/fato_vendas/`, siga os passos:

### Opção 1: Via Container Metabase (Se Configurado)
Acesse via navegador o serviço subido pelo Docker Compose.
URL: `http://localhost:3000`

### Opção 2: Via Streamlit (Aplicação Python Local)
No terminal, ative seu ambiente virtual do UV, e chame o arquivo principal do Dashboard.

```bash
uv run streamlit run visualization/dashboard.py
```
Acesse o seu navegador no endereço: `http://localhost:8501`

*(Nota: Na inicialização, o Streamlit pode levar 2-5 segundos lendo os dados em memória do MinIO na primeira conexão).*
