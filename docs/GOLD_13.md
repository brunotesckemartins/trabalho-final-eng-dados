# 🥇 Evidências de Sucesso: Requisito GOLD-13

Esta página serve como registro documental do cumprimento do Requisito Oficial "GOLD-13".

> **GOLD-13:** Será requerida Documentação do projeto (ReadMe) em formato Markdown, contendo evidências em screenshots do passo a passo para a execução em modo local da Pipeline de Dados construída, com a respectiva carga final completa na Base de Dados da Ferramenta de Visualização, com a correspondente visualização em Dashboard.

---

## 🎯 Prova de Conceito (Documentação e Dashboard)

A base de código deste projeto atende ao requisito GOLD-13 através de uma documentação completa utilizando MkDocs e um dashboard interativo integrado construído com Streamlit.

### 1. Documentação (ReadMe / MkDocs)

O repositório do projeto possui um README claro na raiz, além desta documentação estendida construída em formato Markdown e hospedada através do plugin MkDocs Material, oferecendo navegação e divisão semântica dos temas.

### 2. Ferramenta de Visualização e Conexão (DuckDB + Streamlit)

A carga final do repositório pode ser observada rodando o Streamlit conectado localmente aos arquivos Delta Lake gravados na camada Gold do MinIO. A conexão é validada em tempo real com DuckDB e processada na porta `localhost:8501`.

O [Dashboard em Streamlit](visualizacao.md) traz quatro indicadores de negócios e tabelas detalhadas demonstrando que as tabelas de fatos e dimensões foram carregadas com totalidade na Base de Visualização.

*(Prints e Screenshots demonstrando as ações de play das DAGs do Airflow, inicialização dos containers Docker, e do Dashboard preenchido foram anexados ao PDF de entrega oficial na plataforma de ensino, não compondo o código fonte do Git).*
