"""
incremental_loader.py
---------------------
Processo de carga incremental para as dimensões Gold.

Combina o change_detector (GOLD-05) com o scd2 (GOLD-04):
  1. Detecta o que mudou (novos e alterados).
  2. Aplica SCD2 apenas nesses registros.
  3. Registros sem alteração são ignorados — sem escrita desnecessária.
"""

import sys
sys.path.insert(0, '/home/elison/trabalho-final-eng-dados')

from pyspark.sql import DataFrame, SparkSession
from gold.utils.change_detector import detect_changes
from gold.utils.scd2 import apply_scd2


def incremental_load(
    spark: SparkSession,
    df_new: DataFrame,
    dst_path: str,
    primary_key: str,
    business_columns: list,
    table_name: str = "",
) -> dict:
    """
    Executa carga incremental com SCD Tipo 2.

    Fluxo:
      1. Detecta novos, alterados e sem alteração.
      2. Se não há nada para processar, encerra sem escrita.
      3. Aplica SCD2 apenas nos registros que mudaram.

    Retorna resumo com contagens de cada categoria.
    """

    print(f"\n[INCREMENTAL] Iniciando carga incremental: '{table_name}'")

    changes = detect_changes(
        spark=spark,
        df_new=df_new,
        dst_path=dst_path,
        primary_key=primary_key,
        business_columns=business_columns,
    )

    novos = changes["novos"]
    alterados = changes["alterados"]
    sem_alteracao = changes["sem_alteracao"]

    count_novos = novos.count()
    count_alterados = alterados.count()
    count_sem_alteracao = sem_alteracao.count()

    if count_novos == 0 and count_alterados == 0:
        print(f"[INCREMENTAL] '{table_name}': nenhuma alteração detectada — carga ignorada.")
        return {
            "novos": 0,
            "alterados": 0,
            "sem_alteracao": count_sem_alteracao,
        }

    # Une novos e alterados para aplicar SCD2
    df_para_processar = novos.union(alterados)

    apply_scd2(
        spark=spark,
        df_new=df_para_processar,
        dst_path=dst_path,
        primary_key=primary_key,
        business_columns=business_columns,
    )

    print(f"[INCREMENTAL] '{table_name}' concluído — "
          f"Novos: {count_novos} | Alterados: {count_alterados} | "
          f"Ignorados: {count_sem_alteracao}")

    return {
        "novos": count_novos,
        "alterados": count_alterados,
        "sem_alteracao": count_sem_alteracao,
    }
