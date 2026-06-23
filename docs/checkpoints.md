# ⏱️ Checkpoints na Tabela Fato

Ao trabalhar com grandes volumes de dados (a tabela fato de um e-commerce é a que mais cresce), processar 100% da base todos os dias torna o pipeline ineficiente, caro e muito demorado (Full Load).

A solução é usar processamento Incremental (Delta Load). Para habilitá-lo de forma simplificada em batch usando PySpark comum, construímos uma **camada de controle lógico por Checkpoint**.

---

## 🛠️ O que é um Checkpoint?

É um arquivo JSON leve salvo no MinIO contendo a última `data_pedido` extraída e processada com sucesso pela tabela fato na camada Gold. Funciona como uma "marca d'água" (Watermark).

**Estrutura do arquivo `checkpoint.json`:**
```json
{
  "max_date": "2023-10-15 14:30:22.000",
  "updated_at": "2023-10-15T18:00:00Z"
}
```

---

## 🔄 Funcionamento da Carga Incremental

### Fase 1: Leitura do Checkpoint
O script PySpark (`fato_vendas.py`) inicia buscando este arquivo JSON.
*   Se o arquivo **não existe**, o script assume o valor padrão (`1970-01-01`), forçando um processamento inicial inteiro (Carga Histórica/Full Load).
*   Se o arquivo **existe**, a variável `max_data_processada` recebe a data do arquivo.

### Fase 2: Filtro na Camada Silver
Ao ler os dados da Silver para montar a fato, o PySpark injeta um filtro direto na leitura (Pushdown):

```python
df_pedidos_silver = spark.read.format("delta").load("s3a://silver/pedidos") \
    .filter(col("data_pedido") > max_data_processada)
```

**Benefício:** Se apenas 50 novos pedidos ocorreram ontem, o Spark processa e cruza com a dimensões apenas esses 50 pedidos (e não os 10.000 do passado).

### Fase 3: Gravação Append e Atualização de Checkpoint
Os 50 novos registros fato são inseridos (APPEND) na Tabela Gold.
Se a operação for concluída com sucesso, o script extrai a maior data dentre os 50 registros, e atualiza o arquivo `checkpoint.json` no MinIO.

Se o job falhar, o JSON não é sobrescrito, garantindo consistência na próxima execução.
