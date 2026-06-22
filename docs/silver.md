# Camada Silver (Bronze → Silver)

A camada **Silver** é a camada de dados **limpos, tipados e confiáveis** do Data Lake. Ela consome a Bronze e aplica um conjunto de transformações que garantem a qualidade e integridade dos dados antes de serem consumidos pela camada Gold.

## Responsabilidades

A Silver executa 4 etapas em sequência para cada tabela:

### 1. Deduplicação
A Bronze é append-only e pode conter o mesmo registro repetido em várias cargas. A Silver aplica uma **janela (Window)** ordenada por `_ingestion_timestamp` (descendente), particionada pela chave primária, e mantém apenas a **versão mais recente** de cada registro.

### 2. Tipagem (Cast)
Cada coluna é convertida do `StringType` bruto da Bronze para o tipo correto definido em `schemas.py`:

| Tipo de Destino | Exemplo de Colunas |
|-----------------|--------------------|
| `IntegerType` | `id_pedido`, `id_cliente`, `quantidade` |
| `DecimalType(10,2)` | `preco_base`, `valor_pago`, `preco_unitario` |
| `DateType` | `data_cadastro` |
| `TimestampType` | `data_pedido`, `data_pagamento` |
| `StringType` (com trim) | `nome_completo`, `cpf`, `email` |

Se algum valor não-nulo na origem virar `null` após o cast, o pipeline emite um aviso no log indicando possível formato inesperado na extração.

### 3. Regras de Qualidade por Tabela
Cada tabela pode ter regras de negócio específicas aplicadas após a tipagem:

| Tabela | Regra |
|--------|-------|
| `clientes` | Remove registros com `cpf` ou `email` nulo |
| `pedidos` | Filtra apenas status válidos: Concluído, Pendente, Cancelado |
| `itens_pedido` | Exige `quantidade > 0` e `preco_unitario > 0` |
| `pagamentos_pedido` | Exige `valor_pago > 0` |
| `lojas` | Padroniza `estado_loja` para maiúsculo (UPPER + TRIM) |
| `enderecos` | Padroniza `estado` para maiúsculo (UPPER + TRIM) |

### 4. Escrita via MERGE (Upsert)
A Silver **não acumula histórico** como a Bronze. Ela sempre reflete o **estado atual e correto** de cada entidade. Para isso, a escrita é feita via **Delta MERGE**:

- Se o registro já existe (mesma chave primária) → **UPDATE**
- Se é um registro novo → **INSERT**

Na primeira carga (quando a tabela Delta ainda não existe), a escrita é feita em modo `overwrite`.

## Coluna de Auditoria

Cada registro processado na Silver recebe a coluna:

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `_silver_processed_at` | `timestamp` | Data/hora em que o registro foi processado pela Silver |

Essa coluna é utilizada pela camada Gold para **extração incremental** (filtro de watermark nos checkpoints).

## Como Executar

```bash
# Processar uma tabela específica
spark-submit pipeline/bronze_to_silver.py --table pedidos

# Processar todas as 10 tabelas de uma vez (conveniência para testes locais)
python pipeline/run_all_tables.py silver
```

## Armazenamento

Os dados são gravados no MinIO no path:
```
s3a://silver/<nome_da_tabela>/
```

Exemplo: `s3a://silver/pedidos/`, `s3a://silver/clientes/`, etc.
