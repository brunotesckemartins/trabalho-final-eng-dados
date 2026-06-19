from pyspark.sql import SparkSession
import os
import subprocess

# Inicialização otimizada para Delta Lake
spark = SparkSession.builder \
    .appName("Gold_Carga_Inicial_Dimensoes") \
    .config("spark.jars.packages", "io.delta:delta-spark_3.2.1:3.2.0") \
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
    .getOrCreate()

print("\n--- INICIANDO ORQUESTRAÇÃO GOLD ---")

dimensoes = [
    "gold/dim_clientes.py",
    "gold/dim_produtos.py",
    "gold/dim_lojas.py",
    "gold/dim_vendedores.py",
    "gold/dim_metodos_pagamento.py"
]

for script in dimensoes:
    if os.path.exists(script):
        print(f"Executando: {script}...")
        # Executa o script isolado
        result = subprocess.run(["python3", script], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"Sucesso: {script}")
        else:
            print(f"ERRO em {script}: {result.stderr}")
    else:
        print(f"Arquivo não encontrado: {script}")

print("--- ORQUESTRAÇÃO FINALIZADA ---")
