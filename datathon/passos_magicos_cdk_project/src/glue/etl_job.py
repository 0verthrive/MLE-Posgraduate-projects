import io
import sys
import unicodedata
from datetime import datetime, timezone

import boto3
import numpy as np
import pandas as pd
from awsglue.utils import getResolvedOptions

args = getResolvedOptions(sys.argv, ["JOB_NAME", "DATA_BUCKET", "RAW_PARQUET_PREFIX", "GOLD_PREFIX"])
bucket = args["DATA_BUCKET"]
raw_parquet_prefix = args["RAW_PARQUET_PREFIX"]
gold_prefix = args["GOLD_PREFIX"].rstrip("/") + "/"
s3 = boto3.client("s3")


RENAME_MAP = {
    "ra": "student_id",
    "fase": "fase",
    "turma": "turma",
    "nome": "nome",
    "ano_nasc": "ano_nasc",
    "idade_22": "idade",
    "genero": "genero",
    "ano_ingresso": "ano_ingresso",
    "instituicao_de_ensino": "instituicao_ensino",
    "matem": "nota_matematica",
    "portug": "nota_portugues",
    "ingles": "nota_ciencias",
    "n_av": "faltas",
    "n_av.": "faltas",
    "n_av_": "faltas",
    "n_avaliacoes": "faltas",
    "ips": "participacao",
    "inde_22": "inde",
    "defas": "defasagem",
}


def list_objects(prefix: str):
    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            if obj["Key"].endswith(".parquet"):
                yield obj["Key"]


def normalize_text(value: str) -> str:
    value = unicodedata.normalize("NFKD", str(value))
    value = value.encode("ascii", "ignore").decode("ascii")
    value = value.lower().strip()
    value = value.replace(" ", "_")
    value = value.replace("-", "_")
    value = value.replace("/", "_")
    return value


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    cols = []
    for col in df.columns:
        normalized = normalize_text(col)
        normalized = RENAME_MAP.get(normalized, normalized)
        cols.append(normalized)
    df.columns = cols
    return df


def parse_numeric_series(series: pd.Series) -> pd.Series:
    return pd.to_numeric(
        series.astype(str).str.replace(".", "", regex=False).str.replace(",", ".", regex=False),
        errors="coerce",
    )


def create_target(df: pd.DataFrame) -> pd.DataFrame:
    numeric_defaults = {
        "nota_portugues": 0.0,
        "nota_matematica": 0.0,
        "nota_ciencias": 0.0,
        "faltas": 0.0,
        "idade": 0.0,
        "participacao": 0.0,
        "inde": 0.0,
        "defasagem": 0.0,
    }

    text_defaults = {
        "student_id": "",
        "turma": "Sem turma",
        "fase": "Sem fase",
        "nome": "",
        "genero": "Nao informado",
        "instituicao_ensino": "Nao informada",
        "ano_ingresso": "Nao informado",
    }

    for col, default in text_defaults.items():
        if col not in df.columns:
            df[col] = default

    for col, default in numeric_defaults.items():
        if col not in df.columns:
            df[col] = default

    for col in numeric_defaults:
        df[col] = parse_numeric_series(df[col]).fillna(0)

    df["media_notas"] = (
        df["nota_portugues"] + df["nota_matematica"] + df["nota_ciencias"]
    ) / 3

    df["indice_presenca"] = 1 - (df["faltas"] / (df["faltas"] + 10).clip(lower=1))
    df["engajamento_total"] = (df["participacao"] + df["indice_presenca"]) / 2

    conditions = [
        (df["media_notas"] >= 8) & (df["faltas"] <= 3),
        (df["media_notas"] >= 6) & (df["faltas"] <= 6),
        ((df["media_notas"] >= 4) & (df["media_notas"] < 6)) | ((df["faltas"] > 6) & (df["faltas"] <= 10)),
        (df["media_notas"] < 4) | (df["faltas"] > 10),
    ]
    choices = ["Excelente", "Saudavel", "Suporte", "Perigo"]

    df["risk_category"] = np.select(conditions, choices, default="Suporte")
    df["target"] = df["risk_category"].isin(["Suporte", "Perigo"]).astype(int)

    return df


def enrich_dashboard_columns(df: pd.DataFrame) -> pd.DataFrame:
    df["idade"] = parse_numeric_series(df["idade"]).fillna(0)

    df["faixa_etaria"] = pd.cut(
        df["idade"],
        bins=[0, 10, 13, 15, 18, 100],
        labels=["Até 10", "11-13", "14-15", "16-18", "18+"],
        include_lowest=True,
    ).astype(str)

    return df


def main():
    frames = []
    for key in list_objects(raw_parquet_prefix):
        obj = s3.get_object(Bucket=bucket, Key=key)
        frames.append(pd.read_parquet(io.BytesIO(obj["Body"].read())))

    if not frames:
        print(f"Nenhum parquet encontrado em s3://{bucket}/{raw_parquet_prefix}")
        return

    df = pd.concat(frames, ignore_index=True)
    df = normalize_columns(df)
    df["processed_at"] = datetime.now(timezone.utc).isoformat()
    df = create_target(df)
    df = enrich_dashboard_columns(df)

    silver_key = "silver/students/students.parquet"
    gold_features_key = f"{gold_prefix}features/students_features.parquet"
    gold_training_key = f"{gold_prefix}training/training_dataset.parquet"
    gold_dashboard_key = f"{gold_prefix}dashboard/students_dashboard.parquet"

    silver_buffer = io.BytesIO()
    df.to_parquet(silver_buffer, index=False)
    s3.put_object(
        Bucket=bucket,
        Key=silver_key,
        Body=silver_buffer.getvalue(),
        ContentType="application/octet-stream",
    )

    gold_buffer = io.BytesIO()
    df.to_parquet(gold_buffer, index=False)
    s3.put_object(
        Bucket=bucket,
        Key=gold_features_key,
        Body=gold_buffer.getvalue(),
        ContentType="application/octet-stream",
    )

    train_columns = [
        "student_id",
        "nota_portugues",
        "nota_matematica",
        "nota_ciencias",
        "faltas",
        "idade",
        "participacao",
        "media_notas",
        "target",
    ]
    for col in train_columns:
        if col not in df.columns:
            df[col] = "" if col == "student_id" else 0

    train_df = df[train_columns].copy()

    training_buffer = io.BytesIO()
    train_df.to_parquet(training_buffer, index=False)
    s3.put_object(
        Bucket=bucket,
        Key=gold_training_key,
        Body=training_buffer.getvalue(),
        ContentType="application/octet-stream",
    )

    dashboard_columns = [
        "student_id",
        "nome",
        "turma",
        "fase",
        "idade",
        "faixa_etaria",
        "genero",
        "instituicao_ensino",
        "ano_ingresso",
        "nota_portugues",
        "nota_matematica",
        "nota_ciencias",
        "faltas",
        "media_notas",
        "participacao",
        "risk_category",
        "target",
        "processed_at",
    ]
    for col in dashboard_columns:
        if col not in df.columns:
            df[col] = ""

    dashboard_df = df[dashboard_columns].copy()

    dashboard_buffer = io.BytesIO()
    dashboard_df.to_parquet(dashboard_buffer, index=False)
    s3.put_object(
        Bucket=bucket,
        Key=gold_dashboard_key,
        Body=dashboard_buffer.getvalue(),
        ContentType="application/octet-stream",
    )

    print(
        f"Arquivos salvos: {silver_key}, {gold_features_key}, {gold_training_key}, {gold_dashboard_key}"
    )


if __name__ == "__main__":
    main()