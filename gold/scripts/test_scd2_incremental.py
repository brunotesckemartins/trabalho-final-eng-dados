"""
test_scd2_incremental.py
-------------------------
GOLD-12: Testes de atualização incremental e histórico SCD Tipo 2.
Valida inserção de novos registros, versionamento de alterações,
preservação do histórico e unicidade do registro ativo por chave.
"""
import sys
import os
import shutil
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from pyspark.sql import Row
from pyspark.sql.functions import col, lit, current_timestamp
from gold.config import get_spark_session
from gold.utils.scd2 import apply_scd2

PK = "id_cliente"
BIZ_COLS = ["nome_cliente", "cidade"]

def make_df(spark, rows):
    return spark.createDataFrame([Row(**r) for r in rows])

def run_tests():
    spark = get_spark_session("gold12-testes-scd2")
    tmp_dir = tempfile.mkdtemp(prefix="gold12_test_")
    dst = os.path.join(tmp_dir, "dim_teste")
    falhas = []

    try:
        print("\n=== GOLD-12: Testes Incrementais e Histórico SCD Tipo 2 ===\n")

        # --- TESTE 1: Carga inicial ---
        print("--- TESTE 1: Carga inicial ---")
        df1 = make_df(spark, [
            {"id_cliente": 1, "nome_cliente": "Ana",   "cidade": "SP"},
            {"id_cliente": 2, "nome_cliente": "Bruno", "cidade": "RJ"},
        ])
        apply_scd2(spark, df1, dst, PK, BIZ_COLS)
        df = spark.read.format("delta").load(dst)
        total = df.count()
        assert total == 2, f"Esperado 2, encontrado {total}"
        assert df.filter("registro_ativo = true").count() == 2
        print(f"[OK] {total} registros carregados na carga inicial")

        # --- TESTE 2: Novo registro inserido ---
        print("\n--- TESTE 2: Novo registro inserido ---")
        df2 = make_df(spark, [
            {"id_cliente": 1, "nome_cliente": "Ana",    "cidade": "SP"},
            {"id_cliente": 2, "nome_cliente": "Bruno",  "cidade": "RJ"},
            {"id_cliente": 3, "nome_cliente": "Carlos", "cidade": "MG"},
        ])
        apply_scd2(spark, df2, dst, PK, BIZ_COLS)
        df = spark.read.format("delta").load(dst)
        ativos = df.filter("registro_ativo = true").count()
        assert ativos == 3, f"Esperado 3 ativos, encontrado {ativos}"
        print(f"[OK] Novo registro inserido — {ativos} ativos")

        # --- TESTE 3: Registro alterado gera nova versão ---
        print("\n--- TESTE 3: Registro alterado versionado ---")
        df3 = make_df(spark, [
            {"id_cliente": 1, "nome_cliente": "Ana Silva", "cidade": "SP"},  # alterado
            {"id_cliente": 2, "nome_cliente": "Bruno",     "cidade": "RJ"},
            {"id_cliente": 3, "nome_cliente": "Carlos",    "cidade": "MG"},
        ])
        apply_scd2(spark, df3, dst, PK, BIZ_COLS)
        df = spark.read.format("delta").load(dst)

        historico_ana = df.filter("id_cliente = 1")
        total_ana = historico_ana.count()
        ativo_ana = historico_ana.filter("registro_ativo = true").count()
        inativo_ana = historico_ana.filter("registro_ativo = false").count()

        assert total_ana == 2,    f"Esperado 2 versões de Ana, encontrado {total_ana}"
        assert ativo_ana == 1,    f"Esperado 1 ativo de Ana, encontrado {ativo_ana}"
        assert inativo_ana == 1,  f"Esperado 1 histórico de Ana, encontrado {inativo_ana}"
        print(f"[OK] Ana versionada — {inativo_ana} histórico, {ativo_ana} ativo")

        # --- TESTE 4: Apenas 1 ativo por chave ---
        print("\n--- TESTE 4: Unicidade do registro ativo por chave ---")
        df_ativos = spark.read.format("delta").load(dst).filter("registro_ativo = true")
        dups = df_ativos.groupBy(PK).count().filter("count > 1").count()
        assert dups == 0, f"[FALHA] {dups} chaves com mais de 1 registro ativo"
        print(f"[OK] Nenhuma chave com mais de 1 registro ativo")

        # --- TESTE 5: Histórico preservado com data_fim_vigencia ---
        print("\n--- TESTE 5: Histórico com data_fim_vigencia preenchida ---")
        df_inativo = spark.read.format("delta").load(dst).filter("registro_ativo = false")
        sem_fim = df_inativo.filter(col("data_fim_vigencia").isNull()).count()
        assert sem_fim == 0, f"[FALHA] {sem_fim} registros inativos sem data_fim_vigencia"
        print(f"[OK] Todos os registros históricos possuem data_fim_vigencia")

        print("\n=== RESULTADO ===")
        print("[OK] Todos os testes da GOLD-12 passaram!")

    except AssertionError as e:
        falhas.append(str(e))
        print(f"\n[FALHA] {e}")
        sys.exit(1)
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
        spark.stop()

if __name__ == "__main__":
    run_tests()
