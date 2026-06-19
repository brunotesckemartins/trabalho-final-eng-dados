from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import IntegerType, StringType

spark = SparkSession.builder.appName("Gold_Dim_Metodos_Pagamento").getOrCreate()
df_silver = spark.read.format("delta").load("silver/metodos_pagamento")

df_final = df_silver.select(
    F.col("id_metodo").cast(IntegerType()).alias("id_metodo_pagamento"),
    F.col("tipo_pagamento").cast(StringType()).alias("descricao_pagamento")
).distinct() \
 .withColumn("sk_metodo_pagamento", F.md5(F.col("id_metodo_pagamento").cast("string")).cast(StringType())) \
 .withColumn("dt_alteracao", F.current_timestamp())

df_final_ordenado = df_final.select(
    "sk_metodo_pagamento", 
    "id_metodo_pagamento", 
    "descricao_pagamento", 
    "dt_alteracao"
)

df_final_ordenado.write.format("delta").mode("overwrite").save("gold/dim_metodos_pagamento")
print("Dimensao de Metodos de Pagamento processada com sucesso!")
