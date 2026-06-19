"""
persist_dimensions.py  (GOLD-09)
---------------------------------
Garante o armazenamento das dimensões Gold no formato Delta Lake.

Roda DEPOIS do run_dimensions.py (que já faz o merge SCD2 via apply_scd2).
Este script foca no que a GOLD-09 pede especificamente:

  1. Otimizar cada tabela Delta já persistida (OPTIMIZE + VACUUM).
  2. Validar a integridade dos dados após a escrita/merge.

Não duplica a lógica de merge (gold/utils/scd2.py já cobre isso, GOLD-05 a 08).

Uso:
    python3 gold/run_dimensions.py            # GOLD-05 a 08: detecção + merge SCD2
    python3 gold/scripts/persist_dimensions.py  # GOLD-09: otimização + validação
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from dataclasses import dataclass

from pyspark.sql import SparkSession

from config import get_spark_session
from gold.config import gold_path
from gold.utils.delta_validator import validate_delta_table, IntegrityError


@dataclass
class DimensionConfig:
    """Configuração de validação/otimização de uma dimensão Gold."""
    nome: str
    dst_path: str
    primary_key: str


# Dimensões reais do projeto (mesmos nomes/chaves de gold/run_dimensions.py
# e gold/dimensions/dim_*.py)
DIMENSOES = [
    DimensionConfig("dim_clientes", gold_path("dim_clientes"), "id_cliente"),
    DimensionConfig("dim_lojas", gold_path("dim_lojas"), "id_loja"),
    DimensionConfig("dim_produtos", gold_path("dim_produtos"), "id_produto"),
    DimensionConfig("dim_vendedores", gold_path("dim_vendedores"), "id_vendedor"),
    DimensionConfig("dim_metodos_pagamento", gold_path("dim_metodos_pagamento"), "id_metodo"),
]


def optimize_table(spark: SparkSession, table_path: str, vacuum_hours: int = 168) -> None:
    """
    Executa OPTIMIZE (compactação de arquivos pequenos) e VACUUM
    (limpeza de arquivos obsoletos) sobre a tabela Delta.

    vacuum_hours=168 (7 dias) é o padrão de retenção do Delta Lake;
    valores menores exigem desabilitar o retentionDurationCheck.
    """
    print(f"[OPTIMIZE] Compactando arquivos: {table_path}")
    spark.sql(f"OPTIMIZE delta.`{table_path}`")

    print(f"[VACUUM] Limpando arquivos obsoletos (retenção {vacuum_hours}h): {table_path}")
    spark.sql(f"VACUUM delta.`{table_path}` RETAIN {vacuum_hours} HOURS")


def persist_and_validate(spark: SparkSession, config: DimensionConfig, run_optimize: bool = True) -> bool:
    """
    Otimiza e valida a integridade de uma dimensão já persistida em Delta.

    Returns:
        True se a otimização e validação foram bem-sucedidas.
    """
    print(f"\n{'=' * 60}")
    print(f"[GOLD-09] Dimensão: {config.nome}")
    print(f"[GOLD-09] Path:      {config.dst_path}")
    print(f"{'=' * 60}")

    try:
        if run_optimize:
            optimize_table(spark, config.dst_path)

        validate_delta_table(
            spark=spark,
            table_path=config.dst_path,
            primary_key=config.primary_key,
            raise_on_failure=True,
        )

        print(f"[GOLD-09] '{config.nome}' otimizada e validada com sucesso.\n")
        return True

    except IntegrityError as e:
        print(f"[GOLD-09][ERRO] Falha de integridade em '{config.nome}': {e}")
        return False


def main():
    spark = get_spark_session("gold_persist_dimensions")

    resultados = {}
    for config in DIMENSOES:
        resultados[config.nome] = persist_and_validate(spark, config)

    spark.stop()

    print("\n" + "=" * 60)
    print("[RESUMO] GOLD-09 - Persistência em Delta Lake")
    for nome, ok in resultados.items():
        print(f"  {'✓' if ok else '✗'} {nome}")
    print("=" * 60)

    if not all(resultados.values()):
        sys.exit(1)


if __name__ == "__main__":
    main()
