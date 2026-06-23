# 🚀 Guia de Instalação e Execução

## Pré-requisitos

!!! warning "Instale antes de continuar"
    Todas as ferramentas abaixo são obrigatórias.

### Docker

Necessário para subir toda a infraestrutura.

=== "Linux"
    Siga o [guia oficial do Docker Engine](https://docs.docker.com/engine/install/)

=== "Windows"
    Baixe e instale o [Docker Desktop](https://www.docker.com/products/docker-desktop/)

=== "macOS"
    Baixe e instale o [Docker Desktop](https://www.docker.com/products/docker-desktop/)

Verifique a instalação:
```bash
docker --version
docker compose version
```

### Python 3.11+

=== "Linux / macOS"
    Use [pyenv](https://github.com/pyenv/pyenv) ou o gerenciador de pacotes do sistema.

=== "Windows"
    Baixe em [python.org](https://www.python.org/downloads/).

```bash
python --version
```

### UV (Gerenciador de Pacotes)

=== "Linux / macOS"
    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```

=== "Windows (PowerShell)"
    ```powershell
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    ```

!!! tip "Reinicie o terminal após instalar o UV"

```bash
uv --version
```

---

## Passo a Passo

### 1️⃣ Clonar o Repositório

```bash
git clone https://github.com/brunotesckemartins/trabalho-final-eng-dados.git
cd trabalho-final-eng-dados
```

### 2️⃣ Configurar Variáveis de Ambiente

```bash
cp .env.example .env
```

!!! note "Os valores padrão já funcionam para o ambiente local"
    Não é necessário alterar o `.env` para rodar localmente.

### 3️⃣ Instalar Dependências Python

```bash
uv sync
```

Ative o ambiente virtual:

=== "Linux / macOS"
    ```bash
    source .venv/bin/activate
    ```

=== "Windows (PowerShell)"
    ```powershell
    .venv\Scripts\Activate.ps1
    ```

### 4️⃣ Subir a Infraestrutura

```bash
docker compose up -d
```

!!! warning "Primeira execução"
    A imagem do Airflow (com Java + PySpark) será construída, o que pode levar **5 a 10 minutos**.

Verifique o status dos containers:

```bash
docker compose ps
```

!!! success "Status esperado"
    Todos os serviços devem estar com status `running`.
    O `airflow-init` ficará `exited (0)` — **isso é normal**.

### 5️⃣ Popular o Banco de Dados

```bash
python scripts/faker_generator.py
```

Gera dados sintéticos: ~500 clientes, ~200 produtos, ~10.000 pedidos com itens aleatórios.

### 6️⃣ Executar o Pipeline via Airflow

1. Acesse [http://localhost:8080](http://localhost:8080)
2. Login: `admin` / `admin`
3. Localize a DAG **`orquestracao_medalhao_end_to_end`**
4. Ative a DAG (toggle → azul)
5. Clique em **Trigger DAG** (▶)
6. Acompanhe em **Graph View**

!!! info "Tempo de execução: 5 a 15 minutos"

### 7️⃣ Iniciar o Dashboard

Após a DAG concluir com sucesso:

```bash
uv run streamlit run visualization/dashboard.py
```

Acesse em [http://localhost:8501](http://localhost:8501).

### 8️⃣ (Opcional) Validar o Dashboard

```bash
python visualization/tests/test_validacao.py
```

---

## Troubleshooting

??? question "Docker Compose não sobe?"
    - Verifique se o Docker Desktop está rodando
    - Verifique se as portas 5432, 8080, 9000, 9001 não estão em uso
    - Tente: `docker compose down -v && docker compose up -d`

??? question "Airflow mostra erro na DAG?"
    - Verifique os logs: `docker compose logs airflow-webserver`
    - Reinicie: `docker compose restart airflow-webserver airflow-scheduler`

??? question "Dashboard não conecta ao MinIO?"
    - Confirme que as variáveis no `.env` estão corretas
    - Verifique se a DAG do Airflow finalizou com sucesso

??? question "Erro de memória no Spark?"
    - Aumente a memória do Docker Desktop (Settings → Resources → Memory)
    - Recomendado: mínimo 4GB para Docker
