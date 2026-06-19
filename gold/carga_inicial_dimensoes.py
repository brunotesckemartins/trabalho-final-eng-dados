from pyspark.sql import SparkSession
from pyspark.sql import functions as F

# 1. Iniciar a sessao Spark configurada para Delta Lake e Postgres (JDBC)
spark = SparkSession.builder \
    .appName("Gold_Carga_Inicial_Dimensoes") \
    .config("spark.jars.packages", "io.delta:delta-spark_2.12:3.2.0,org.postgresql:postgresql:42.7.3") \
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
    .getOrCreate()

print("==================================================")
print("PREPARANDO AMBIENTE LOCAL: EXTRAINDO DA ORIGEM PARA A SILVER")
print("==================================================")

db_properties = {
    "user": "postgres",
    "password": "admin123",
    "driver": "org.postgresql.Driver"
}
db_url = "jdbc:postgresql://localhost:5432/ecommerce_db"

# Tabelas simples (Origem Postgres -> Caminho Silver)
tabelas_diretas = {
    "clientes": "silver/clientes",
    "enderecos": "silver/enderecos",
    "produtos": "silver/produtos",
    "categorias": "silver/categorias"
}

for tabela_origem, caminho_silver in tabelas_diretas.items():
    try:
        df = spark.read.jdbc(url=db_url, table=tabela_origem, properties=db_properties)
        df.write.format("delta").mode("overwrite").save(caminho_silver)
        print(f"Pasta temporaria [{caminho_silver}] gerada com sucesso.")
    except Exception as e:
        print(f"Erro ao gerar {caminho_silver}: {str(e)}")

# Tabelas com ajuste de nome de coluna para bater com o que a Gold espera ler
try:
    # Ajuste Lojas (nome_loja -> nome)
    df_lojas = spark.read.jdbc(url=db_url, table="lojas", properties=db_properties)
    df_lojas.withColumnRenamed("nome_loja", "nome").write.format("delta").mode("overwrite").save("silver/lojas")
    print("Pasta temporaria [silver/lojas] ajustada e gerada.")

    # Ajuste Vendedores (nome_vendedor -> nome)
    df_vendedores = spark.read.jdbc(url=db_url, table="vendedores", properties=db_properties)
    df_vendedores.withColumnRenamed("nome_vendedor", "nome").write.format("delta").mode("overwrite").save("silver/vendedores")
    print("Pasta temporaria [silver/vendedores] ajustada e gerada.")

    # Ajuste Metodos Pagamento (id_metodo -> id_metodo_pagamento, tipo_pagamento -> descricao)
    df_metodos = spark.read.jdbc(url=db_url, table="metodos_pagamento", properties=db_properties)
    df_metodos.withColumnRenamed("id_metodo", "id_metodo_pagamento") \
              .withColumnRenamed("tipo_pagamento", "descricao") \
              .write.format("delta").mode("overwrite").save("silver/metodos_pagamento")
    print("Pasta temporaria [silver/metodos_pagamento] ajustada e gerada.")

except Exception as e:
    print(f"Erro critico no ajuste de colunas da Silver: {str(e)}")


print("\n==================================================")
print("INICIANDO CARGA INICIAL (FULL LOAD) DA CAMADA GOLD")
print("==================================================")

dimensoes = [
    "gold/dim_clientes.py",
    "gold/dim_produtos.py",
    "gold/dim_lojas.py",
    "gold/dim_vendedores.py",
    "gold/dim_metodos_pagamento.py"
]

# Executar o conteudo de cada script usando a mesma sessao ativa
for script in dimensoes:
    print(f"Executando carga de: {script}")
    try:
        with open(script, "r", encoding="utf-8") as f:
            codigo = f.read()
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
