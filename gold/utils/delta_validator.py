"""
delta_validator.py
-------------------
Validacoes de integridade aplicadas apos operacoes de persistencia
(merge/insert) em tabelas Delta da camada Gold.
"""
from dataclasses import dataclass, field

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from delta.tables import DeltaTable


class IntegrityError(Exception):
    """Levantada quando uma validacao de integridade falha."""


@dataclass
class ValidationReport:
    table_path: str
    total_registros: int = 0
    registros_ativos: int = 0
    checks_executados: list = field(default_factory=list)
    ok: bool = True

    def add(self, nome_check: str, passou: bool, detalhe: str = ""):
        self.checks_executados.append(
            {"check": nome_check, "passou": passou, "detalhe": detalhe}
        )
        if not passou:
            self.ok = False

    def print_summary(self):
        status = "OK" if self.ok else "FALHOU"
        print(f"\n[VALIDATOR] Relatorio de integridade - {self.table_path}")
        print(f"[VALIDATOR] Total de registros: {self.total_registros}")
        print(f"[VALIDATOR] Registros ativos:   {self.registros_ativos}")
        for c in self.checks_executados:
            marca = "OK" if c["passou"] else "FALHOU"
            linha = f"  [{marca}] {c['check']}"
            if c["detalhe"]:
                linha += f" - {c['detalhe']}"
            print(linha)
        print(f"[VALIDATOR] Status final: {status}\n")


def validate_delta_table(
    spark: SparkSession,
    table_path: str,
    primary_key: str,
    required_columns: list = None,
    raise_on_failure: bool = True,
) -> ValidationReport:
    """
    Executa a suite de validacoes de integridade sobre uma tabela Delta
    de dimensao (SCD Tipo 2).
    """
    report = ValidationReport(table_path=table_path)

    is_delta = DeltaTable.isDeltaTable(spark, table_path)
    report.add("tabela_e_delta", is_delta, "" if is_delta else "path nao e uma tabela Delta valida")
    if not is_delta:
        report.print_summary()
        if raise_on_failure:
            raise IntegrityError(f"'{table_path}' nao e uma tabela Delta valida.")
        return report

    df = spark.read.format("delta").load(table_path)
    report.total_registros = df.count()

    if report.total_registros == 0:
        report.add("tabela_nao_vazia", False, "tabela existe mas esta vazia")
        report.print_summary()
        if raise_on_failure:
            raise IntegrityError(f"'{table_path}' esta vazia apos a persistencia.")
        return report
    report.add("tabela_nao_vazia", True)

    colunas_scd2 = {"registro_ativo", "data_inicio_vigencia", "data_fim_vigencia"}
    colunas_existentes = set(df.columns)
    faltando = colunas_scd2 - colunas_existentes
    report.add(
        "colunas_scd2_presentes",
        len(faltando) == 0,
        "" if not faltando else f"faltando: {sorted(faltando)}",
    )

    if "registro_ativo" in colunas_existentes:
        ativo_flag = F.col("registro_ativo")

        ativos = df.filter(ativo_flag)
        report.registros_ativos = ativos.count()

        duplicados_ativos = (
            ativos.groupBy(primary_key)
            .count()
            .filter(F.col("count") > 1)
        )
        n_duplicados = duplicados_ativos.count()
        report.add(
            "unicidade_registro_ativo_por_chave",
            n_duplicados == 0,
            "" if n_duplicados == 0 else f"{n_duplicados} chave(s) com >1 registro ativo",
        )

        ativo_com_fim_preenchido = ativos.filter(
            F.col("data_fim_vigencia").isNotNull()
        ).count()
        report.add(
            "ativos_sem_data_fim",
            ativo_com_fim_preenchido == 0,
            "" if ativo_com_fim_preenchido == 0
            else f"{ativo_com_fim_preenchido} registro(s) ativo(s) com data_fim_vigencia preenchida",
        )

        inativos = df.filter(~ativo_flag)
        inativo_sem_fim = inativos.filter(F.col("data_fim_vigencia").isNull()).count()
        report.add(
            "inativos_com_data_fim",
            inativo_sem_fim == 0,
            "" if inativo_sem_fim == 0
            else f"{inativo_sem_fim} registro(s) inativo(s) sem data_fim_vigencia",
        )

    cols_obrigatorias = required_columns or [primary_key, "registro_ativo", "data_inicio_vigencia"]
    for c in cols_obrigatorias:
        if c not in colunas_existentes:
            continue
        n_nulos = df.filter(F.col(c).isNull()).count()
        report.add(
            f"sem_nulos_em_{c}",
            n_nulos == 0,
            "" if n_nulos == 0 else f"{n_nulos} valor(es) nulo(s)",
        )

    report.print_summary()

    if raise_on_failure and not report.ok:
        falhas = [c["check"] for c in report.checks_executados if not c["passou"]]
        raise IntegrityError(
            f"Validacao de integridade falhou para '{table_path}': {falhas}"
        )

    return report
