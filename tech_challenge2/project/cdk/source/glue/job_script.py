import sys
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.utils import getResolvedOptions
from awsglue.job import Job
from pyspark.sql.functions import (
    regexp_replace,
    col,
    input_file_name,
    regexp_extract,
    concat_ws,
    to_date,
    monotonically_increasing_id
)

# Argumentos recebidos pelo Glue
args = getResolvedOptions(sys.argv, ["JOB_NAME", "SOURCE_BUCKET", "SOURCE_KEY", "TARGET_PATH"])

# Inicializa contexto
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args["JOB_NAME"], args={})

# Caminhos
bucket = args['SOURCE_BUCKET']
key = args['SOURCE_KEY']
input_path = f"s3://{bucket}/{key}"
output_path = args["TARGET_PATH"]

# Lê o Parquet de entrada
df = spark.read.format("parquet").load(input_path)

# Verifica colunas (debug)
print("Colunas originais:", df.columns)

# Renomeia colunas
df = df.withColumnRenamed("Tipo", "qtde_teorica_temp") \
       .withColumnRenamed("Ação", "tipo") \
       .withColumnRenamed("Código", "codigo") \
       .withColumnRenamed("Qtde. Teórica", "part_percentual") \
       .drop("Part. (%)")

# Corrige a coluna qtde_teorica
df = df.withColumnRenamed("qtde_teorica_temp", "qtde_teorica")
df = df.drop("part_percentual")
# Limpa e converte valores numéricos
df = df.withColumn(
    "qtde_teorica",
    regexp_replace("qtde_teorica", r"\.", "").cast("double")
)

print("Conteúdo:")
df.show(truncate=False)
# Adiciona o nome do arquivo como coluna auxiliar
df = df.withColumn("file_name", input_file_name())

# Extrai ano, mês e dia a partir do caminho
df = df.withColumn("ano", regexp_extract("file_name", r"/(\d{2})/\d{2}/\d{2}/", 1)) \
       .withColumn("mes", regexp_extract("file_name", r"/\d{2}/(\d{2})/\d{2}/", 1)) \
       .withColumn("dia", regexp_extract("file_name", r"/\d{2}/\d{2}/(\d{2})/", 1))

# Cria coluna data real
df = df.withColumn("data", to_date(concat_ws("-", "ano", "mes", "dia"), "yy-MM-dd"))

# Adiciona ID único
df = df.withColumn("id", monotonically_increasing_id())

# Remove colunas auxiliares
df = df.drop("file_name", "ano", "mes", "dia")

# Grava o resultado no S3
df.write \
  .mode("append") \
  .partitionBy("data") \
  .parquet(output_path)

job.commit()
