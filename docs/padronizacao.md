# 📚 Padronização de Código e Nomenclaturas

Este projeto segue diretrizes de boas práticas e convenções estabelecidas pela engenharia de dados moderna, permitindo a escalabilidade e o onboarding ágil de novos membros no time.

---

## 🗂️ Estrutura de Diretórios e Objetos MinIO

1.  **Buckets (Containers MinIO):** Escritos em caixa baixa e sem pontuação.
    `landing`, `bronze`, `silver`, `gold`.
2.  **Tabelas/Path de Objetos:** Em snake_case.
    `fato_vendas`, `dim_clientes`, `itens_pedido`.

---

## 🐍 Python (Estilo de Código PySpark)

*   O projeto foi construído respeitando as regras do padrão PEP-8 da linguagem Python.
*   Bibliotecas utilizadas, como o `uv` e `pytest` seguem essa filosofia nativamente.

### Nomes de Dataframes (Sufixos e Prefixos)
Padrão claro para saber em qual ambiente ou transformação o DataFrame está num dado momento:

```python
df_bronze       # Representa os dados carregados ou apontados na camada Bronze.
df_silver       # Representa os dados carregados ou apontados na camada Silver.
df_gold         # Representa a junção/cálculos aplicados na Gold.
df_atualizado   # Reflete um DF transitório sofrendo modificação ou merge.
```

---

## 📅 Variáveis de Ambiente e Conexões

Credenciais sensíveis nunca estão em Hardcode no projeto.
Todas as configurações estão isoladas no arquivo global `.env` com a seguinte padronização de nomenclatura:
`{TECNOLOGIA}_USER`, `{TECNOLOGIA}_PASSWORD`, `{TECNOLOGIA}_HOST`.

**Exemplo:**
```bash
POSTGRES_USER=postgres
MINIO_ROOT_USER=admin
AIRFLOW_USER=admin
```
