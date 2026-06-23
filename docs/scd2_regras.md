# 🧠 Lógica SCD Tipo 2 (Slowly Changing Dimensions)

O Slowly Changing Dimension Tipo 2 é um padrão clássico de Data Warehousing. Seu principal objetivo é **preservar o histórico completo das informações**, de forma que dados do passado fiquem associados à versão do cadastro válida na época.

---

## 🏗️ Fluxo Lógico PySpark

A construção deste algoritmo no PySpark segue o seguinte passo a passo para cada uma das dimensões:

### 1. Hash e Identificação
A Silver envia a tabela consolidada mais recente. O Spark calcula o hash MD5 (Surrogate Key) para a linha recebida usando seus atributos e data.

### 2. Cruzamento com a Tabela Delta Gold
O Dataframe recém calculado sofre um Left Join com o estado atual da tabela Delta (onde `registro_ativo = True`).

### 3. Cenários de Ação
Baseado no cruzamento do passo 2, temos 3 cenários matemáticos possíveis:

#### Cenário A: Inserção Inédita (Novo Cliente)
A chave primária não existia na Gold.
*   **Ação:** O registro é inserido como novo (`registro_ativo=True`, `data_fim_vigencia=Null`).

#### Cenário B: Sem Mudanças (Cliente igual)
O registro existe, mas o hash das colunas de rastreamento é idêntico.
*   **Ação:** Nenhuma alteração é feita.

#### Cenário C: Atualização Cadastral (Mudou de cidade)
O registro existe, mas houve mudança nos atributos rastreados.
*   **Ação:**
    *   **Passo 1 (Update):** Encerra o registro existente na Gold (`registro_ativo=False`, `data_fim_vigencia=hoje`).
    *   **Passo 2 (Insert):** Insere o novo registro (`registro_ativo=True`, `data_fim_vigencia=Null`, com nova `sk_cliente`).

### 4. O `MERGE INTO` Final
A operação de update e insert descrita no Cenário C é efetuada atomica e eficientemente pelo Delta Lake usando um único comando de Merge.

```python
delta_table.alias("gold").merge(
    df_novo.alias("silver"),
    "gold.id_tabela = silver.id_tabela AND gold.sk_tabela = silver.sk_tabela"
) \
.whenMatchedUpdate(
    condition="gold.registro_ativo = True AND silver.mudou_algo = True",
    set={"registro_ativo": lit(False), "data_fim_vigencia": col("silver.data")}
) \
.whenNotMatchedInsertAll() \
.execute()
```
