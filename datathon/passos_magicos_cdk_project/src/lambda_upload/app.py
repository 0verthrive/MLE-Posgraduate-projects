import base64
import json
import os
import re
from datetime import datetime, timezone
from urllib.parse import unquote_plus

import boto3

s3 = boto3.client("s3")
dynamodb = boto3.resource("dynamodb")

DATA_BUCKET = os.environ["DATA_BUCKET"]
UPLOAD_PREFIX = os.getenv("UPLOAD_PREFIX", "raw/xlsx/")
METADATA_TABLE = os.getenv("METADATA_TABLE")


SAFE_NAME = re.compile(r"[^A-Za-z0-9._-]+")


def _normalize_filename(raw_name: str | None) -> str:
    if not raw_name:
        raw_name = f"upload_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.xlsx"
    name = unquote_plus(raw_name).split("/")[-1].strip()
    name = SAFE_NAME.sub("_", name)
    if not name.lower().endswith(".xlsx"):
        name = f"{name}.xlsx"
    return name


def _get_filename(event: dict) -> str:
    path_params = event.get("pathParameters") or {}
    query_params = event.get("queryStringParameters") or {}
    headers = {k.lower(): v for k, v in (event.get("headers") or {}).items()}

    filename = path_params.get("filename") or query_params.get("filename")
    if filename:
        return _normalize_filename(filename)

    content_disposition = headers.get("content-disposition", "")
    if "filename=" in content_disposition:
        value = content_disposition.split("filename=", 1)[1].strip().strip('"')
        return _normalize_filename(value)

    return _normalize_filename(None)


def handler(event, context):
    method = event.get("httpMethod")
    if method not in {"POST", "PUT"}:
        return {"statusCode": 405, "body": json.dumps({"message": "Method not allowed"})}

    body = event.get("body")
    if not body:
        return {"statusCode": 400, "body": json.dumps({"message": "Empty body"})}

    if event.get("isBase64Encoded", False):
        payload = base64.b64decode(body)
    else:
        payload = body.encode("utf-8")

    filename = _get_filename(event)
    object_key = f"{UPLOAD_PREFIX}{filename}"

    s3.put_object(
        Bucket=DATA_BUCKET,
        Key=object_key,
        Body=payload,
        ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    if METADATA_TABLE:
        table = dynamodb.Table(METADATA_TABLE)
        now = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        table.put_item(
            Item={
                "pk": "UPLOAD",
                "sk": now,
                "bucket": DATA_BUCKET,
                "key": object_key,
                "status": "UPLOADED",
                "filename": filename,
            }
        )

    return {
        "statusCode": 201,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(
            {
                "message": "Arquivo enviado com sucesso.",
                "bucket": DATA_BUCKET,
                "key": object_key,
            }
        ),
    }
