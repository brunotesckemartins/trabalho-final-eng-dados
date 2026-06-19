# Regras de Implementação SCD Tipo 2 (Delta Lake)

1. **Campos Adicionados:** `data_inicio_vigencia`, `data_fim_vigencia`, `registro_ativo`.
2. **Formato:** Todas as tabelas são armazenadas em **Delta Lake** para permitir operações transacionais.
3. **Regra de Vigência:** O valor '9999-12-31' no campo `data_fim_vigencia` identifica o registro ativo atual.
