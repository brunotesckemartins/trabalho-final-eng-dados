"""
schemas.py
----------
Schemas explícitos das 10 tabelas da origem (espelhando init_schema.sql do
Tiago) e a chave primária de cada uma, usada para deduplicação na Silver
e para o MERGE (upsert) na escrita Delta.

Por que schema explícito e não inferSchema=True?
Com 10.000+ linhas geradas por Faker, deixar o Spark inferir tipo a partir
do CSV é arriscado (ex: uma data nula no início do arquivo pode fazer a
coluna inteira ser inferida como string). Definir o schema manualmente
garante resultado determinístico e documenta o contrato de dados da
origem.
"""

from pyspark.sql.types import (
    DateType,
    DecimalType,
    IntegerType,
    StringType,
    StructField,
    StructType,
    TimestampType,
)

# ---------------------------------------------------------------------------
# Schema "tipado" de cada tabela -> usado pela camada SILVER (tipagem final)
# ---------------------------------------------------------------------------
TABLE_SCHEMAS = {
    "categorias": StructType(
        [
            StructField("id_categoria", IntegerType(), False),
            StructField("nome_categoria", StringType(), False),
        ]
    ),
    "produtos": StructType(
        [
            StructField("id_produto", IntegerType(), False),
            StructField("id_categoria", IntegerType(), True),
            StructField("nome_produto", StringType(), False),
            StructField("preco_base", DecimalType(10, 2), False),
        ]
    ),
    "clientes": StructType(
        [
            StructField("id_cliente", IntegerType(), False),
            StructField("nome_completo", StringType(), False),
            StructField("cpf", StringType(), False),
            StructField("email", StringType(), False),
            StructField("data_cadastro", DateType(), False),
        ]
    ),
    "enderecos": StructType(
        [
            StructField("id_endereco", IntegerType(), False),
            StructField("id_cliente", IntegerType(), True),
            StructField("estado", StringType(), False),
            StructField("cidade", StringType(), False),
        ]
    ),
    "lojas": StructType(
        [
            StructField("id_loja", IntegerType(), False),
            StructField("nome_loja", StringType(), False),
            StructField("estado_loja", StringType(), False),
        ]
    ),
    "vendedores": StructType(
        [
            StructField("id_vendedor", IntegerType(), False),
            StructField("id_loja", IntegerType(), True),
            StructField("nome_vendedor", StringType(), False),
        ]
    ),
    "metodos_pagamento": StructType(
        [
            StructField("id_metodo", IntegerType(), False),
            StructField("tipo_pagamento", StringType(), False),
        ]
    ),
    "pedidos": StructType(
        [
            StructField("id_pedido", IntegerType(), False),
            StructField("id_cliente", IntegerType(), True),
            StructField("id_loja", IntegerType(), True),
            StructField("id_vendedor", IntegerType(), True),
            StructField("data_pedido", TimestampType(), False),
            StructField("status_pedido", StringType(), False),
        ]
    ),
    "itens_pedido": StructType(
        [
            StructField("id_item", IntegerType(), False),
            StructField("id_pedido", IntegerType(), True),
            StructField("id_produto", IntegerType(), True),
            StructField("quantidade", IntegerType(), False),
            StructField("preco_unitario", DecimalType(10, 2), False),
        ]
    ),
    "pagamentos_pedido": StructType(
        [
            StructField("id_pagamento", IntegerType(), False),
            StructField("id_pedido", IntegerType(), True),
            StructField("id_metodo", IntegerType(), True),
            StructField("valor_pago", DecimalType(10, 2), False),
            StructField("data_pagamento", TimestampType(), False),
        ]
    ),
}

# ---------------------------------------------------------------------------
# Chave primária de cada tabela (usada para dedup + MERGE na Silver)
# ---------------------------------------------------------------------------
PRIMARY_KEYS = {
    "categorias": "id_categoria",
    "produtos": "id_produto",
    "clientes": "id_cliente",
    "enderecos": "id_endereco",
    "lojas": "id_loja",
    "vendedores": "id_vendedor",
    "metodos_pagamento": "id_metodo",
    "pedidos": "id_pedido",
    "itens_pedido": "id_item",
    "pagamentos_pedido": "id_pagamento",
}

# Ordem sugerida de processamento: dimensões antes dos fatos.
# Não é estritamente necessário no Bronze/Silver (não há checagem de FK
# bloqueante aqui), mas deixa o pipeline mais legível e já adianta a ordem
# que o Elison/Ian provavelmente vão querer na Gold.
TABLE_ORDER = [
    "categorias",
    "lojas",
    "metodos_pagamento",
    "clientes",
    "produtos",
    "enderecos",
    "vendedores",
    "pedidos",
    "itens_pedido",
    "pagamentos_pedido",
]


def string_schema(table_name: str) -> StructType:
    """
    Gera a versão "bruta" do schema de uma tabela: mesmos nomes de coluna,
    porém todos os tipos como StringType.

    Usada pela camada BRONZE, que deve preservar a fidelidade do dado
    original (princípio de medalhão: Bronze = raw, Silver = tipado/limpo).
    Casting de tipo (int, decimal, timestamp...) só acontece na Silver.
    """
    typed_schema = TABLE_SCHEMAS[table_name]
    return StructType(
        [StructField(f.name, StringType(), True) for f in typed_schema.fields]
    )
