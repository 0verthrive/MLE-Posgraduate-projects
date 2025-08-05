#!/usr/bin/env python3
import os
import yaml
import aws_cdk as cdk
from cdk.cdk_stack import CdkStack

def get_yaml_file(path):
    with open(path, 'r') as file:
        return yaml.safe_load(file)


configs = get_yaml_file('config/config.yaml')
envs = get_yaml_file('config/enviroments.yaml')

account_id = envs["ACCOUNT_ID"]
region = envs["REGION"]
bucket_name = f"b3-bucket-mle-{account_id}"
bucket_url = f's3://{bucket_name}'
bucket_arn = f'arn:aws:s3:::{bucket_name}'

app = cdk.App()
CdkStack(
    app,
    "CdkStack",
    configs,
    bucket_name=bucket_name,
    bucket_url=bucket_url,
    bucket_arn=bucket_arn,
    account_id=account_id
)
app.synth()
