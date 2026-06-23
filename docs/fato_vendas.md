# ⭐ Camada Gold: Fato Vendas

O centro do nosso Star Schema na camada Gold é a **Fato Vendas**. Ela consolida todas as métricas financeiras de um item de pedido cruzado com as chaves históricas (`Surrogate Keys`) geradas pelas Dimensões (SCD2).

---

## 🎯 Grão (Granularidade)

O grão da tabela fato é **1 Item de Pedido**.

Cada registro representa o produto X, comprado dentro do pedido Y, na data Z.
Se um pedido tiver 3 itens, ele gerará 3 linhas na tabela `fato_vendas`.

---

## 🧩 Cruzamento de Tabelas Silver

A construção da Fato une 3 tabelas transacionais da camada Silver:

*   `pedidos`: Informações cabecalho (id do pedido, cliente, data, status).
*   `itens_pedido`: Grão da fato (id item, produto, quantidade, preco).
*   `pagamentos_pedido`: Forma de pagamento.

A Fato também realiza **Join com as Dimensões Gold** para resgatar as **Surrogate Keys (SK)** vigentes na data em que a compra ocorreu.

---

## 🔗 Resgate de Surrogate Key no Tempo (SCD2 Point-in-Time Join)

Ao construir a `fato_vendas`, não cruzamos diretamente com `id_cliente`. Em vez disso, cruzamos o ID do cliente com a `dim_clientes` verificando se a **data do pedido ocorreu dentro da vigência daquela versão de cliente**.

**Exemplo da condição de Join:**
```python
condicao_cliente = (
    (df_fato_temp.id_cliente == dim_clientes.id_cliente) &
    (df_fato_temp.data_pedido >= dim_clientes.data_inicio_vigencia) &
    (
        (dim_clientes.data_fim_vigencia.isNull()) |
        (df_fato_temp.data_pedido < dim_clientes.data_fim_vigencia)
    )
)
```
Isso garante precisão histórica: se um vendedor mudou de loja em 2022, as vendas de 2021 serão creditadas à loja antiga.

---

## 📊 Métricas Calculadas

*   `valor_total_item` = (quantidade * preco_unitario)
*   `valor_total_pago_pedido` = valor contido na tabela pagamentos_pedido.

---

## 🛡️ Carga Incremental com Checkpoints

!!! info "Checkpointing"
    Para evitar recalcular a base inteira a cada execução, a tabela Fato utiliza checkpoints.

1.  O script verifica no MinIO qual foi o `max(data_pedido)` da última carga efetuada na Gold.
2.  Carrega da Silver apenas dados onde `data_pedido > max(data_pedido)`.
3.  Calcula a Fato e dá append na Gold.
4.  Grava o novo Checkpoint no MinIO em formato JSON.

> *Consulte a seção `checkpoints.md` para entender como criamos essa solução em PySpark sem depender de Structured Streaming.*

---

## ⚙️ Como Executar

O processamento da Fato depende estritamente das dimensões atualizadas. (No Airflow, ele roda após o step de dimensões).

```bash
spark-submit gold/facts/fato_vendas.py
```

---

## 💾 Armazenamento

Os dados da Fato e os arquivos de Checkpoint ficam no path:

```
s3a://gold/fato_vendas/
s3a://gold/checkpoints/fato_vendas/
```
