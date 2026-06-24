"""
run_all_tables.py
-----------------
Script de conveniência para desenvolvimento/teste local: roda a camada
Bronze OU Silver para as 10 tabelas em sequência, reutilizando a mesma
SparkSession (mais rápido que abrir uma sessão nova por tabela).

NÃO é pensado para ser a forma definitiva de orquestração -- a
recomendação para o Gabriel/Bruno é criar uma task por tabela no
orquestrador (cada uma chamando landing_to_bronze.py / bronze_to_silver.py
com --table), o que permite retry e monitoramento individual por tabela.
Este script aqui serve para você validar o pipeline inteiro de uma vez,
sem depender do orquestrador já estar pronto.

Uso:
    python run_all_tables.py bronze
    python run_all_tables.py silver
"""

import os
import sys

_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_pipeline = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _root)
sys.path.insert(0, _pipeline)

import bronze_to_silver
import landing_to_bronze
from config import get_spark_session
from schemas import TABLE_ORDER


def main(stage: str) -> None:
    if stage not in ("bronze", "silver"):
        raise ValueError("Uso: python run_all_tables.py [bronze|silver]")

    spark = get_spark_session(f"run_all_{stage}")
    falhas = []

    for table in TABLE_ORDER:
        print(f"\n===== [{stage.upper()}] Processando '{table}' =====")
        try:
            if stage == "bronze":
                landing_to_bronze.run(table, spark=spark)
            else:
                bronze_to_silver.run(table, spark=spark)
        except Exception as exc:  # noqa: BLE001 - queremos seguir para as outras tabelas
            print(f"[ERRO] Falha ao processar '{table}': {exc}")
            falhas.append(table)

    spark.stop()

    print("\n===== RESUMO =====")
    if falhas:
        print(f"Tabelas com falha: {falhas}")
        sys.exit(1)
    else:
        print(f"Todas as {len(TABLE_ORDER)} tabelas processadas com sucesso na camada {stage}.")


if __name__ == "__main__":
    stage_arg = sys.argv[1] if len(sys.argv) > 1 else "bronze"
    main(stage_arg)
