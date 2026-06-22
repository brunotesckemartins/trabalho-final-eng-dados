# Regras SCD Tipo 2 — Camada Gold

## O que é SCD Tipo 2?
Slowly Changing Dimension Tipo 2 mantém o histórico completo de alterações
de cada registro, criando uma nova linha a cada mudança.

## Colunas de controle

| Coluna                | Tipo      | Descrição                                      |
|-----------------------|-----------|------------------------------------------------|
| `data_inicio_vigencia`| Timestamp | Quando o registro passou a ser válido          |
| `data_fim_vigencia`   | Timestamp | Quando deixou de ser válido (nulo = ativo)     |
| `registro_ativo`      | Boolean   | True = registro atual, False = histórico       |

## Regras de preenchimento

- **Novo registro**: `data_inicio_vigencia=agora`, `data_fim_vigencia=nulo`, `registro_ativo=True`
- **Registro alterado**: o antigo recebe `registro_ativo=False` e `data_fim_vigencia=agora`;
  uma nova linha é inserida com `registro_ativo=True`
- **Registro sem alteração**: não é tocado

## Dimensões com SCD Tipo 2
- `dim_clientes`
- `dim_lojas`
- `dim_produtos`
- `dim_vendedores`
- `dim_metodos_pagamento`
