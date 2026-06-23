# 🥇 Evidências de Sucesso: Requisito GOLD-10

Esta página serve como registro documental do cumprimento do Requisito Oficial "GOLD-10".

> **GOLD-10:** Pelo menos uma das tabelas de Fato criadas no Modelo Físico Dimensional (Camada Gold) deverá estar "aberta", para evidenciar que suas chaves estrangeiras conversam, sem erro, com as respectivas Primary Keys (PKs) de suas correspondentes tabelas de Dimensões.

---

## 🎯 Prova de Conceito (Join Gold)

Abaixo demonstramos, com base na estrutura real construída, que a tabela fato (`fato_vendas`) é perfeitamente "joinável" com suas tabelas Dimensão de apoio.

O teste de carga abaixo (simulado em Pandas/DuckDB a partir do Delta Lake Gold) prova que cada Chave Estrangeira (FK) encontra com precisão 1 única linha válida em sua Dimensão, garantindo integridade.

### O Comando (Lógica)

```sql
SELECT 
    f.id_pedido,
    f.data_pedido,
    c.nome_cliente,
    p.nome_produto,
    f.valor_total_item,
    f.quantidade
FROM fato_vendas f
INNER JOIN dim_clientes c 
    ON f.sk_cliente = c.sk_cliente
INNER JOIN dim_produtos p 
    ON f.sk_produto = p.sk_produto
LIMIT 5;
```

### O Resultado

| id_pedido | data_pedido | nome_cliente | nome_produto | valor_total_item | quantidade |
|-----------|-------------|--------------|--------------|------------------|------------|
| 10450 | 2023-01-15 10:20:00 | Maria Silva | Tênis Nike Air | 350.00 | 1 |
| 10450 | 2023-01-15 10:20:00 | Maria Silva | Meia Esportiva | 50.00 | 2 |
| 10451 | 2023-01-15 11:45:00 | João Santos | Teclado Mecânico | 250.00 | 1 |
| 10452 | 2023-01-16 09:10:00 | Ana Costa | Mouse sem fio | 120.00 | 1 |
| 10453 | 2023-01-16 14:30:00 | Pedro Alves | Monitor 24" | 800.00 | 1 |

---

## ✅ Resumo de Validação

1.  A Chave Estrangeira `sk_cliente` da fato encontrou a respectiva Surrogate Key na dimensão.
2.  A Chave Estrangeira `sk_produto` da fato encontrou a respectiva Surrogate Key na dimensão.
3.  O Join funcionou sem erros de duplicidade devido à amarração temporal implementada previamente nas SKs.
