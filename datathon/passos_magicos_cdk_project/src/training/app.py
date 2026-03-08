import io
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import boto3
import pandas as pd

from src_shared.modeling import train_model

s3 = boto3.client("s3")
dynamodb = boto3.resource("dynamodb")

DATA_BUCKET = os.environ["DATA_BUCKET"]
MODEL_PREFIX = os.getenv("MODEL_PREFIX", "artifacts/models")
METADATA_TABLE = os.environ["METADATA_TABLE"]
RUN_ID = os.getenv("RUN_ID", "manual-run")


def main():
    obj = s3.get_object(Bucket=DATA_BUCKET, Key="gold/training/training_dataset.parquet")
    df = pd.read_parquet(io.BytesIO(obj["Body"].read()))

    workdir = Path("/tmp/model")
    workdir.mkdir(parents=True, exist_ok=True)
    model_path = str(workdir / "model.joblib")

    result = train_model(df, model_path)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    model_key = f"{MODEL_PREFIX}/model-{timestamp}.joblib"
    report_key = f"{MODEL_PREFIX}/metrics-{timestamp}.json"

    s3.upload_file(model_path, DATA_BUCKET, model_key)
    s3.put_object(
        Bucket=DATA_BUCKET,
        Key=report_key,
        Body=json.dumps(
            {"weighted_f1": result.weighted_f1, "report": result.report},
            default=str,
        ).encode("utf-8"),
        ContentType="application/json",
    )

    dynamodb.Table(METADATA_TABLE).put_item(
        Item={
            "pk": "MODEL",
            "sk": timestamp,
            "run_id": RUN_ID,
            "model_key": model_key,
            "metrics_key": report_key,
            "weighted_f1": str(result.weighted_f1),
            "status": "TRAINED",
        }
    )

    print(json.dumps({"model_key": model_key, "weighted_f1": result.weighted_f1}))


if __name__ == "__main__":
    main()