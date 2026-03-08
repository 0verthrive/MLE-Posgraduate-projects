import io
import sys

import boto3
import pandas as pd
from awsglue.utils import getResolvedOptions

args = getResolvedOptions(sys.argv, ["JOB_NAME", "DATA_BUCKET", "TRAINING_DATASET_KEY"])
bucket = args["DATA_BUCKET"]
training_key = args["TRAINING_DATASET_KEY"]

s3 = boto3.client("s3")


def main():
    obj = s3.get_object(Bucket=bucket, Key=training_key)
    df = pd.read_parquet(io.BytesIO(obj["Body"].read()))

    if df.empty:
        raise ValueError("Training dataset vazio")

    required_columns = [
        "nota_portugues",
        "nota_matematica",
        "nota_ciencias",
        "faltas",
        "media_notas",
        "target",
    ]

    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        raise ValueError(f"Colunas obrigatórias ausentes: {missing}")

    null_counts = df[required_columns].isnull().sum().to_dict()
    print(f"Null counts: {null_counts}")

    if any(v > 0 for v in null_counts.values()):
        raise ValueError(f"Há valores nulos em colunas obrigatórias: {null_counts}")

    print("Data Quality finalizado com sucesso")


if __name__ == "__main__":
    main()