from pyspark.sql import SparkSession

spark = (
    SparkSession.builder
    .appName("teste")
    .master("local[*]")
    .getOrCreate()
)

print("Spark OK!")
print(spark.version)

spark.stop()
