# ⭐️ Camada Gold: Dimensões (SCD2)

A camada **Gold** implementa o modelo dimensional (Star Schema), otimizado para o consumo no Dashboard de Visualização. Esta seção descreve a construção das **Dimensões**.

!!! success "SCD Tipo 2 Implementado"
    Todas as dimensões Gold implementam Slowly Changing Dimension Tipo 2.
    Histórico completo das alterações cadastrais é mantido.

---

## 🎯 Visão Geral

As dimensões são derivadas do cruzamento e limpeza das tabelas da Silver, consolidando chaves substitutas (Surrogate Keys) numéricas ou strings que unificam o histórico.

No nosso projeto final, geramos 5 tabelas de dimensão baseadas no esquema Silver:

1.  `dim_clientes` (cruza Clientes + Endereços)
2.  `dim_produtos` (cruza Produtos + Categorias)
3.  `dim_lojas` (Lojas puras)
4.  `dim_vendedores` (cruza Vendedores + Lojas)
5.  `dim_metodos_pagamento` (Métodos de Pagamento puros)

---

## 🧬 Colunas de Controle SCD2

As dimensões geradas via PySpark (`gold/run_dimensions.py`) introduzem colunas padronizadas de controle SCD2.

| Coluna | Função |
|---|---|
| `sk_*` | Surrogate Key — Um Hash MD5 dos atributos de negócio com a data, garantindo unicidade temporal |
| `data_inicio_vigencia` | Data de entrada desta versão do registro |
| `data_fim_vigencia` | Data em que o registro sofreu alteração. Null para os ativos |
| `registro_ativo` | Boleano (True/False) indicando qual a versão vigente no sistema |
| `_gold_processed_at` | Auditoria — Timestamp do processamento Gold |

### Entendendo na Prática:

Se o produto "Tênis Nike" sofrer uma mudança de preço (`preco_base`), não atualizamos o preço (SCD Tipo 1).
Criamos uma nova linha fechando a vigência anterior, e ativando a nova versão:

| sk_produto | id_produto | nome_produto | preco_base | registro_ativo | data_inicio_vigencia | data_fim_vigencia |
|---|---|---|---|---|---|---|
| `d8b5c...` | 42 | Tênis Nike | 150.00 | **False** | 2021-05-10 | **2023-11-20** |
| `a92f1...` | 42 | Tênis Nike | 190.00 | **True**  | **2023-11-20** | Null |

---

## 🔄 Lógica de Implementação no Spark

Para construir o SCD2 no Spark, utilizamos lógica relacional (Left Anti Join, Unions) somada à API do Delta Lake.

1.  **Join Silver:** Criar um DataFrame "Atual" cruzando as tabelas necessárias da Silver.
2.  **Identificação de Novos/Alterados:** Usando hash MD5 (hash de atributos + data). Se os atributos mudaram desde a última carga Gold, fechamos a linha antiga (update) e criamos uma nova (insert).
3.  **Merge Condition:** O script executa a função DeltaTable `MERGE INTO`, finalizando a operação.

> *Mais detalhes sobre os joins exatos no script `gold/run_dimensions.py` e `scd2_regras.md`.*

---

## ⚙️ Como Executar

O processamento ocorre de uma só vez para as 5 dimensões:

```bash
spark-submit gold/run_dimensions.py
```

---

## 💾 Armazenamento

Os dados são salvos em:

```
s3a://gold/<nome_da_dimensao>/
```
