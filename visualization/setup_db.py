"""
setup_db.py
-----------
Provisiona e valida o banco DuckDB da camada de consumo analítico.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from visualization.config import DUCKDB_PATH, MINIO_ENDPOINT, get_connection


def setup() -> None:
    print(f"Provisionando DuckDB em: {DUCKDB_PATH}")
    print(f"MinIO endpoint: {MINIO_ENDPOINT}")

    conn = get_connection()

    result = conn.execute("SELECT 42 AS teste").fetchone()
    assert result[0] == 42, "Falha na validação básica do DuckDB"

    version = conn.execute("SELECT version()").fetchone()[0]
    print(f"DuckDB versão: {version}")
    print("Extensões httpfs e delta instaladas.")
    print("Banco acessível e configurado com sucesso.")

    conn.close()


if __name__ == "__main__":
    setup()
