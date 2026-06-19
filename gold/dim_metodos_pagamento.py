from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, TimestampType

spark = SparkSession.builder.appName("Gold_Dim_Metodos_Pagamento").getOrCreate()

schema_dim_pagamento = StructType([
    StructField("sk_metodo_pagamento", StringType(), False),
    StructField("id_metodo_pagamento", IntegerType(), False),
    StructField("descricao_pagamento", StringType(), True),
    StructField("dt_alteracao", TimestampType(), False)
])

df_silver = spark.read.format("delta").load("silver/metodos_pagamento")

df_transformado = df_silver.select(
    F.col("id_metodo_pagamento"),
    F.col("descricao").alias("descricao_pagamento")
).distinct()

df_resultado = df_transformado \
    .withColumn("sk_metodo_pagamento", F.md5(F.col("id_metodo_pagamento").cast("string"))) \
    .withColumn("dt_alteracao", F.current_timestamp())

df_final = spark.createDataFrame(df_resultado.rdd, schema=schema_dim_pagamento)
df_final.write.format("delta").mode("overwrite").save("gold/dim_metodos_pagamento")

print("Dimensão de Métodos de Pagamento processada com sucesso!")
