import json
import os
from datetime import datetime, timezone
import boto3

s3 = boto3.client("s3")
dynamodb = boto3.resource("dynamodb")

DATA_BUCKET = os.environ["DATA_BUCKET"]
METADATA_TABLE = os.environ["METADATA_TABLE"]
RAW_PREFIX = os.getenv("RAW_PREFIX", "bronze/")


def handler(event, context):
    table = dynamodb.Table(METADATA_TABLE)
    records = event.get("Records", [])

    for record in records:
        body = json.loads(record["body"])
        payload = body.get("payload", body)
        now = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        key = f"{RAW_PREFIX}students/{now}.json"

        s3.put_object(
            Bucket=DATA_BUCKET,
            Key=key,
            Body=json.dumps(payload).encode("utf-8"),
            ContentType="application/json",
        )

        table.put_item(
            Item={
                "pk": "INGESTION",
                "sk": now,
                "bucket": DATA_BUCKET,
                "key": key,
                "status": "INGESTED",
            }
        )

    return {"statusCode": 200, "processed": len(records)}
