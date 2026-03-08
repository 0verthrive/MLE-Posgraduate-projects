from __future__ import annotations
import io
import json
import os
from functools import lru_cache
from typing import Any

import boto3
import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException
from mangum import Mangum
from pydantic import BaseModel, Field
from src_shared.features import TRAIN_FEATURE_COLUMNS, build_features, label_from_risk_score


app = FastAPI(title="Passos Mágicos API", version="1.0.0")
s3 = boto3.client("s3")
dynamodb = boto3.resource("dynamodb")
stepfunctions = boto3.client("stepfunctions")

DATA_BUCKET = os.environ["DATA_BUCKET"]
MODEL_PREFIX = os.getenv("MODEL_PREFIX", "artifacts/models")
PREDICTIONS_PREFIX = os.getenv("PREDICTIONS_PREFIX", "predictions")
METADATA_TABLE = os.environ["METADATA_TABLE"]
STATE_MACHINE_ARN = os.getenv("STATE_MACHINE_ARN", "")


class StudentRequest(BaseModel):
    student_id: str = Field(..., min_length=1)
    nota_portugues: float
    nota_matematica: float
    nota_ciencias: float
    faltas: int
    idade: int = 0
    participacao: float = 0.0


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@lru_cache(maxsize=1)
def load_latest_model():
    response = s3.list_objects_v2(Bucket=DATA_BUCKET, Prefix=f"{MODEL_PREFIX}/")
    contents = sorted(response.get("Contents", []), key=lambda x: x["LastModified"], reverse=True)
    for item in contents:
        if item["Key"].endswith(".joblib"):
            obj = s3.get_object(Bucket=DATA_BUCKET, Key=item["Key"])
            return joblib.load(io.BytesIO(obj["Body"].read())), item["Key"]
    raise FileNotFoundError("Nenhum modelo encontrado no bucket")


@app.post("/predict")
def predict(payload: StudentRequest) -> dict[str, Any]:
    try:
        model, model_key = load_latest_model()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    try:
        frame = pd.DataFrame([payload.model_dump()])
        features = build_features(frame)
        X = features[TRAIN_FEATURE_COLUMNS]

        if hasattr(model, "predict_proba"):
            proba = model.predict_proba(X)

            if len(proba[0]) == 1:
                if hasattr(model, "classes_") and len(model.classes_) == 1:
                    only_class = model.classes_[0]
                    probability = 1.0 if int(only_class) == 1 else 0.0
                else:
                    probability = float(proba[0][0])
            else:
                class_index = (
                    list(model.classes_).index(1)
                    if hasattr(model, "classes_") and 1 in model.classes_
                    else 1
                )
                probability = float(proba[0][class_index])
        else:
            probability = float(model.predict(X)[0])

        if pd.isna(probability) or probability == float("inf") or probability == float("-inf"):
            raise ValueError(f"Probabilidade inválida gerada pelo modelo: {probability}")

        label = str(label_from_risk_score(float(probability)))

        result = {
            "student_id": str(payload.student_id),
            "risk_score": round(float(probability), 4),
            "risk_category": label,
            "model_key": str(model_key),
        }

        key = f"{PREDICTIONS_PREFIX}/{payload.student_id}.json"
        s3.put_object(
            Bucket=DATA_BUCKET,
            Key=key,
            Body=json.dumps(result).encode("utf-8"),
            ContentType="application/json",
        )

        dynamodb.Table(METADATA_TABLE).put_item(
            Item={
                "pk": "PREDICTION",
                "sk": str(payload.student_id),
                **{k: str(v) for k, v in result.items()},
            }
        )

        return result

    except Exception as exc:
        print(f"Erro no predict: {type(exc).__name__}: {exc}")
        raise HTTPException(status_code=500, detail=f"Erro ao gerar predição: {exc}") from exc

@lru_cache(maxsize=1)
def load_dashboard_data():
    key = "gold/dashboard/students_dashboard.parquet"
    obj = s3.get_object(Bucket=DATA_BUCKET, Key=key)
    return pd.read_parquet(io.BytesIO(obj["Body"].read()))

@app.get("/dashboard/students")
def dashboard_students() -> list[dict[str, Any]]:
    try:
        df = load_dashboard_data().copy()
    except Exception as exc:
        raise HTTPException(status_code=404, detail=f"Dataset de dashboard não encontrado: {exc}") from exc

    return df.fillna("").to_dict(orient="records")

@app.get("/dashboard/status")
def dashboard_status() -> dict[str, Any]:
    try:
        df = load_dashboard_data().copy()
        total_students = len(df)
        last_processed_at = df["processed_at"].max() if "processed_at" in df.columns else None
    except Exception:
        total_students = 0
        last_processed_at = None

    response = s3.list_objects_v2(Bucket=DATA_BUCKET, Prefix="raw/parquet/")
    raw_files = len(response.get("Contents", []))

    model_response = s3.list_objects_v2(Bucket=DATA_BUCKET, Prefix=f"{MODEL_PREFIX}/")
    model_files = [x["Key"] for x in model_response.get("Contents", []) if x["Key"].endswith(".joblib")]

    return {
        "raw_parquet_files": raw_files,
        "total_students": total_students,
        "last_processed_at": last_processed_at,
        "model_available": len(model_files) > 0,
        "latest_model_key": model_files[-1] if model_files else None,
    }


@app.post("/train")
def trigger_training() -> dict[str, str]:
    if not STATE_MACHINE_ARN:
        raise HTTPException(status_code=500, detail="STATE_MACHINE_ARN não configurado")
    stepfunctions.start_execution(stateMachineArn=STATE_MACHINE_ARN, input=json.dumps({"source": "api"}))
    return {"message": "Treinamento acionado"}


handler = Mangum(app)
