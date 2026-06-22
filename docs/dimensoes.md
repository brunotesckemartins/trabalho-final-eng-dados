# Dimensões e SCD Tipo 2

As dimensões formam o contexto do negócio (O "Quem", "Onde" e "O Que" da Fato). 

## Slow Changing Dimensions (SCD2)

Na modelagem dimensional, os dados muitas vezes sofrem atualizações (ex: O cliente mudou de cidade). Se nós atualizássemos a linha do cliente diretamente, as Fatos antigas do passado passariam a apontar para a nova cidade, ferindo a veracidade histórica da venda.

O **SCD2** previne isso. Ao invés de `UPDATE` na linha, ocorre a seguinte transação:
1. Identifica-se a mudança em colunas críticas (ex: estado, cidade).
2. O registro antigo é "fechado":
   - `registro_ativo = false`
   - `data_fim_vigencia = agora`
3. O registro novo é "aberto":
   - `registro_ativo = true`
   - `data_inicio_vigencia = agora`
   - `data_fim_vigencia = nulo`
   - Nova Chave Substituta (`sk`) é gerada via MD5.

### Data Inicial na Primeira Carga
Para que o sistema consiga lidar com registros históricos que ocorreram *antes* do datalake começar a operar (ex: Vendas de 2024 carregadas no sistema em 2026), a **primeira versão** da dimensão é populada com `data_inicio_vigencia = "1900-01-01"`. Isso faz com que todo o histórico passado feche o relacionamento corretamente.
