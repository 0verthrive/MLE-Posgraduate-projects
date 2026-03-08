import io
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import boto3
import pandas as pd

s3 = boto3.client("s3")
dynamodb = boto3.resource("dynamodb")

DATA_BUCKET = os.environ["DATA_BUCKET"]
INPUT_PREFIX = os.getenv("INPUT_PREFIX", "raw/xlsx/")
OUTPUT_PREFIX = os.getenv("OUTPUT_PREFIX", "raw/parquet/")
METADATA_TABLE = os.getenv("METADATA_TABLE")


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    normalized = []
    for col in df.columns:
        name = str(col).strip().lower()
        name = "_".join(name.split())
        normalized.append(name)
    df.columns = normalized
    return df


def _write_metadata(status: str, source_key: str, target_key: str | None = None, details: str | None = None) -> None:
    if not METADATA_TABLE:
        return
    table = dynamodb.Table(METADATA_TABLE)
    now = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    item = {
        "pk": "CONVERSION",
        "sk": f"{now}#{Path(source_key).name}",
        "bucket": DATA_BUCKET,
        "source_key": source_key,
        "status": status,
    }
    if target_key:
        item["target_key"] = target_key
    if details:
        item["details"] = details
    table.put_item(Item=item)


def handler(event, context):
    results = []
    for record in event.get("Records", []):
        bucket = record["s3"]["bucket"]["name"]
        source_key = record["s3"]["object"]["key"]
        if bucket != DATA_BUCKET or not source_key.startswith(INPUT_PREFIX) or not source_key.lower().endswith(".xlsx"):
            continue

        try:
            obj = s3.get_object(Bucket=bucket, Key=source_key)
            content = obj["Body"].read()
            df = pd.read_excel(io.BytesIO(content), engine="openpyxl")
            df = _normalize_columns(df)
            df["source_file"] = Path(source_key).name
            df["ingested_at"] = datetime.now(timezone.utc).isoformat()

            target_key = f"{OUTPUT_PREFIX}{Path(source_key).stem}.parquet"
            buffer = io.BytesIO()
            df.to_parquet(buffer, index=False)
            s3.put_object(Bucket=bucket, Key=target_key, Body=buffer.getvalue(), ContentType="application/octet-stream")
            _write_metadata("CONVERTED", source_key, target_key)
            results.append({"source_key": source_key, "target_key": target_key, "rows": int(len(df))})
        except Exception as exc:  # pragma: no cover
            _write_metadata("ERROR", source_key, details=str(exc))
            raise

    return {"statusCode": 200, "body": json.dumps(results)}
