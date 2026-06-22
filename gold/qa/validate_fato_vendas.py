"""
validate_fato_vendas.py
-----------------------
[Issue #64] Validação de QA da Tabela Fato na camada Gold.
Garante a integridade, idempotência e corretude das agregações, servindo como "Data Contract".
"""
import sys
import os
from pyspark.sql import functions as F

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config import get_spark_session
from gold.config import gold_path

def run():
    spark = get_spark_session("qa_fato_vendas")
    
    print("\n[QA FATO VENDAS] Iniciando bateria de testes...")
    df_fato = spark.read.format("delta").load(gold_path("fato_vendas"))
    
    total_linhas = df_fato.count()
    print(f"[QA] Total de linhas processadas: {total_linhas}")
    assert total_linhas > 0, "❌ ERRO: A tabela Fato Vendas está vazia!"

    # 1. Ausência de Duplicidades (Idempotência no nível de Item)
    # Como os registros vêm da tabela Itens, o `id_item` deve ser rigorosamente único.
    print("[QA] Verificando unicidade do 'id_item'...")
    duplicados = df_fato.groupBy("id_item").count().filter("count > 1").count()
    assert duplicados == 0, f"❌ ERRO DE IDEMPOTÊNCIA: Encontrados {duplicados} 'id_item' duplicados na Fato!"
    
    # 2. Corretude das Agregações Financeiras
    print("[QA] Verificando integridade das métricas financeiras...")
    invalidos = df_fato.filter(F.col("valor_total_item") <= 0).count()
    assert invalidos == 0, f"❌ ERRO: {invalidos} registros com valor_total_item <= 0. (O Faker pode gerar? Se sim, ignorar)."
    
    # 3. Integridade do JOIN SCD2 (SKs não podem ser nulas se o mapeamento ocorreu com sucesso)
    # Ignoramos `sk_metodo` porque pode não existir pagamento (LEFT JOIN de pagamentos)
    print("[QA] Verificando integridade dos cruzamentos de chaves (SCD2)...")
    nulos_cliente = df_fato.filter(F.col("sk_cliente").isNull()).count()
    nulos_produto = df_fato.filter(F.col("sk_produto").isNull()).count()
    assert nulos_cliente == 0, f"❌ ERRO: Faltou mapeamento SCD2! Encontradas {nulos_cliente} SKs de Clientes nulas."
    assert nulos_produto == 0, f"❌ ERRO: Faltou mapeamento SCD2! Encontradas {nulos_produto} SKs de Produtos nulas."
    
    print("\n[QA FATO VENDAS] ✅ TODAS AS VALIDAÇÕES PASSARAM! Tabela idônea e validada.")
    spark.stop()

if __name__ == "__main__":
    run()
