# Gerenciamento de Checkpoints (Idempotência)

Em Engenharia de Dados, pipelines quebram e falham na metade do caminho. É imperativo que eles sejam idempotentes, ou seja: **Rodar o pipeline duas vezes não pode gerar dados duplicados**.

## O Mecanismo

Para solucionar isso de maneira elegante com o Apache Spark, foi implementado um mecanismo central de _Checkpoints_.

### Extração Incremental
1. O processo `fato_vendas.py` inicia e tenta ler a data da última execução bem-sucedida a partir de uma **tabela Delta de controle** no MinIO (`s3a://gold/checkpoints/fato_vendas`).
2. Se a tabela existir, o timestamp contido ali é a variável `last_run`.
3. Se não existir (primeira carga), assume-se a data de início da Era Unix (`1970-01-01`).
4. O filtro é aplicado na leitura da Camada Silver: o script solicita apenas registros onde `_silver_processed_at > last_run`.
5. Dessa forma, varremos apenas os dados "delta", o que chamamos de extração incremental.

### Confirmação e ACID
1. Após cruzar as informações com as dimensões e agregar as métricas, os dados são gravados na tabela `fato_vendas` no formato **Delta**.
2. **Crucial:** O formato Delta não consolida transações até que toda a tarefa Spark termine no executor. Se o script falhar por memória (`OOM`), incompatibilidade de driver (`PYTHON_VERSION_MISMATCH`), ou qualquer outro erro da VM durante a etapa de *write*, os arquivos soltos em log são automaticamente ignorados e revertidos. 
3. **Somente após a gravação Delta ser concluída** com sucesso é que o nosso script atualiza a **tabela Delta de Checkpoint** para a nova data (o maior valor encontrado na leitura atual). A atualização é feita em modo `overwrite`, garantindo que sempre exista apenas uma linha com o watermark mais recente.
4. Essa barreira ACID, amarrada com a persistência atômica, garante que falhas ocorridas "no meio do caminho" manterão a data de Checkpoint antiga, e o pipeline recarregará exatamente do ponto em que falhou na próxima execução, sem criar duplicidades na destinação final.

## Scripts de QA
A resiliência e corretude desse processo é homologada via rotinas de Testes de Qualidade (`qa/validate_fato_vendas.py`), que inspecionam unicidade e idoneidade referencial (como nulidades indevidas da SKU).
