# GOLD-13 - Documentacao e Entrega

## Objetivo
Documentar a solucao completa da camada Gold.

## Fluxo Silver to Gold
Silver (Delta Lake) -> Extracao PySpark -> SCD Tipo 2 (gold/utils/scd2.py) -> Persistencia Delta -> Camada Gold (MinIO)

## Estrategia SCD Tipo 2
- Etapa 1: Registros alterados recebem registro_ativo=False e data_fim_vigencia=agora
- Etapa 2: Nova versao inserida com registro_ativo=True

## Dimensoes entregues
- dim_clientes (sk_cliente / id_cliente)
- dim_produtos (sk_produto / id_produto)
- dim_lojas (sk_loja / id_loja)
- dim_vendedores (sk_vendedor / id_vendedor)
- dim_metodos_pagamento (sk_metodo / id_metodo)

## Evidencias GOLD-10
dim_clientes: 500 registros, 0 SK nulas, 0 duplicatas
dim_produtos: 100 registros, 0 SK nulas, 0 duplicatas
dim_lojas: 5 registros, 0 SK nulas, 0 duplicatas
dim_vendedores: 20 registros, 0 SK nulas, 0 duplicatas
dim_metodos_pagamento: 4 registros, 0 SK nulas, 0 duplicatas

## Evidencias GOLD-11
OK - Registros carregados corretamente
OK - Estrutura SCD2 presente
OK - Consistencia ativo/inativo validada
OK - SKs sem nulos nem duplicatas

## Evidencias GOLD-12
OK - Carga inicial
OK - Novo registro inserido
OK - Registro alterado versionado
OK - 1 ativo por chave
OK - Historico com data_fim_vigencia

## Artefatos
gold/utils/scd2.py
gold/scripts/persist_dimensions.py
gold/scripts/validate_fact_compatibility.py
gold/scripts/test_carga_inicial.py
gold/scripts/test_scd2_incremental.py
