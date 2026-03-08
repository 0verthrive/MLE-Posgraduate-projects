import json
import os
from statistics import mean

import boto3

s3 = boto3.client("s3")
cloudwatch = boto3.client("cloudwatch")

DATA_BUCKET = os.environ["DATA_BUCKET"]
NAMESPACE = os.getenv("NAMESPACE", "PassosMagicos/MLOps")


def _list_prediction_scores():
    response = s3.list_objects_v2(Bucket=DATA_BUCKET, Prefix="predictions/")
    scores = []
    for obj in response.get("Contents", []):
        data = s3.get_object(Bucket=DATA_BUCKET, Key=obj["Key"])
        payload = json.loads(data["Body"].read().decode("utf-8"))
        if "risk_score" in payload:
            scores.append(float(payload["risk_score"]))
    return scores


def _calculate_drift(scores):
    if not scores:
        return 0.0
    baseline = 0.5
    return abs(mean(scores) - baseline)


def handler(event, context):
    scores = _list_prediction_scores()
    drift = _calculate_drift(scores)

    cloudwatch.put_metric_data(
        Namespace=NAMESPACE,
        MetricData=[
            {"MetricName": "PredictionCount", "Value": float(len(scores)), "Unit": "Count"},
            {"MetricName": "DriftScore", "Value": float(drift), "Unit": "None"},
        ],
    )
    return {"prediction_count": len(scores), "drift_score": drift, "event": event}
