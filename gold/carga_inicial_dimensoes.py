from pyspark.sql import SparkSession

# 1. Iniciar a Sessao unica do Spark configurada para Delta Lake
spark = SparkSession.builder \
    .appName("Gold_Carga_Inicial_Dimensoes") \
    .config("spark.jars.packages", "io.delta:delta-spark_2.12:3.2.0") \
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
    .getOrCreate()

print("==================================================")
print("INICIANDO CARGA INICIAL (FULL LOAD) DA CAMADA GOLD")
print("==================================================")

dimensoes = [
    "gold/dim_clientes.py",
    "gold/dim_produtos.py",
    "gold/dim_lojas.py",
    "gold/dim_vendedores.py",
    "gold/dim_metodos_pagamento.py"
]

# 2. Executar o conteudo de cada script usando a mesma sessao ativa
for script in dimensoes:
    print(f"Executando carga de: {script}")
    try:
        with open(script, "r", encoding="utf-8") as f:
            codigo = f.read()
        
        # Executa o codigo do script aproveitando a variavel 'spark' ja configurada
        exec(codigo, {"spark": spark, "__name__": "__main__"})
        print(f"Script {script} carregado com sucesso.")
    except Exception as e:
        print(f"Erro ao executar o script {script}: {str(e)}")

print("\n==================================================")
print("INICIANDO VALIDACAO DE VOLUME")
print("==================================================")

tabelas_gold = {
    "Dimensao Clientes": "gold/dim_clientes",
    "Dimensao Produtos": "gold/dim_produtos",
    "Dimensao Lojas": "gold/dim_lojas",
    "Dimensao Vendedores": "gold/dim_vendedores",
    "Dimensao Metodos Pagamento": "gold/dim_metodos_pagamento"
}

linhas_evidencia = ["=== EVIDENCIA DE EXECUCAO: CARGA INICIAL GOLD ===\n\n"]

for nome, caminho in tabelas_gold.items():
    try:
        df = spark.read.format("delta").load(caminho)
        qtd_linhas = df.count()
        log = f"Tabela [{nome}]: {qtd_linhas} registros carregados com sucesso."
        print(log)
        linhas_evidencia.append(log + "\n")
    except Exception as e:
        erro_log = f"Erro ao ler a tabela {nome}: {str(e)}"
        print(erro_log)
        linhas_evidencia.append(erro_log + "\n")

caminho_evidencia = "gold/evidencia_carga_inicial.txt"
with open(caminho_evidencia, "w", encoding="utf-8") as f:
    f.writelines(linhas_evidencia)

print(f"\nArquivo de evidencia gerado em: {caminho_evidencia}")
print("==================================================")
