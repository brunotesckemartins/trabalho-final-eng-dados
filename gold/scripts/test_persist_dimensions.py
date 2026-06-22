"""
test_persist_dimensions.py
----------------------------
Testes de integração para a GOLD-09: otimização Delta e validação
de integridade pós-merge.

Roda contra um path Delta temporário (não usa o MinIO real), simulando
o resultado de um apply_scd2 para validar a lógica de forma isolada.
"""
import sys
import os
import shutil
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from pyspark.sql import Row
from pyspark.sql.functions import lit, current_timestamp

from config import get_spark_session
from gold.utils.delta_validator import validate_delta_table, IntegrityError
from gold.scripts.persist_dimensions import persist_and_validate, DimensionConfig


def run_tests():
    spark = get_spark_session("test-gold-09")
    tmp_dir = tempfile.mkdtemp(prefix="gold09_test_")
    dst_path = os.path.join(tmp_dir, "dim_teste")

    try:
        print("\n--- TESTE 1: Tabela íntegra passa na validação ---")
        df_ativos = spark.createDataFrame([
            Row(id_cliente=1, nome_cliente="Ana", cidade="SP"),
            Row(id_cliente=2, nome_cliente="Bruno", cidade="RJ"),
        ]).withColumn("registro_ativo", lit(True)) \
          .withColumn("data_inicio_vigencia", current_timestamp()) \
          .withColumn("data_fim_vigencia", lit(None).cast("timestamp"))

        df_ativos.write.format("delta").mode("overwrite").save(dst_path)

        config = DimensionConfig(nome="dim_teste", dst_path=dst_path, primary_key="id_cliente")
        ok = persist_and_validate(spark, config, run_optimize=True)
        assert ok, "Tabela íntegra deveria passar na validação"
        print("[OK] OPTIMIZE + validação concluídos sem erros.")

        print("\n--- TESTE 2: Dados preservados após OPTIMIZE ---")
        df_pos_optimize = spark.read.format("delta").load(dst_path)
        total = df_pos_optimize.count()
        assert total == 2, f"Esperado 2 registros após OPTIMIZE, encontrado {total}"
        print(f"[OK] {total} registros preservados após otimização.")

        print("\n--- TESTE 3: Validação detecta integridade quebrada ---")
        df_duplicado = df_pos_optimize.filter("id_cliente = 1")
        df_duplicado.write.format("delta").mode("append").save(dst_path)

        df_check = spark.read.format("delta").load(dst_path)
        print(f"[DEBUG] Total de linhas: {df_check.count()}")
        df_check.filter("id_cliente = 1").show(truncate=False)

        falhou_como_esperado = False
        try:
            validate_delta_table(
                spark=spark,
                table_path=dst_path,
                primary_key="id_cliente",
                raise_on_failure=True,
            )
        except IntegrityError:
            falhou_como_esperado = True

        assert falhou_como_esperado, "Validação deveria ter detectado duplicidade de registro ativo"
        print("[OK] Validação corretamente identificou quebra de integridade (>1 registro ativo).")

        print("\n--- TESTE 4: Validação detecta path inválido ---")
        path_invalido = os.path.join(tmp_dir, "nao_existe")
        falhou_como_esperado = False
        try:
            validate_delta_table(
                spark=spark,
                table_path=path_invalido,
                primary_key="id_cliente",
                raise_on_failure=True,
            )
        except IntegrityError:
            falhou_como_esperado = True

        assert falhou_como_esperado, "Validação deveria falhar para path que não é Delta"
        print("[OK] Validação corretamente rejeitou path inválido.")

        print("\n[OK] Todos os testes da GOLD-09 passaram!")

    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
        spark.stop()


if __name__ == "__main__":
    run_tests()
