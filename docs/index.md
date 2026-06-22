# Bem-vindo ao Datalake Ecommerce

Documentação técnica do projeto de Engenharia de Dados, cobrindo a arquitetura em medalhão (Bronze, Silver, Gold), modelagem dimensional e os mecanismos de resiliência e qualidade de dados implementados.

## Módulos Principais

- **[Fato Vendas](fato_vendas.md):** A principal tabela de fatos do negócio, consolidando os pedidos, itens e informações de pagamentos, além das métricas agregadas.
- **[Dimensões (SCD2)](dimensoes.md):** O modelo dimensional que armazena dados de contexto (Lojas, Clientes, Produtos, etc.) guardando o histórico temporal através de Slowly Changing Dimensions do Tipo 2.
- **[Checkpoints e Idempotência](checkpoints.md):** Como a aplicação garante que cargas parciais não quebrem o pipeline e que dados não sejam processados em duplicidade.
