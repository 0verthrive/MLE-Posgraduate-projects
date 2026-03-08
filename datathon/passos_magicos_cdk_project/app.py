#!/usr/bin/env python3
import os
import aws_cdk as cdk

from infra.stacks.storage_stack import StorageStack
from infra.stacks.processing_stack import ProcessingStack
from infra.stacks.frontend_stack import FrontendStack
from infra.stacks.mlops_stack import MlOpsStack
from infra.stacks.api_stack import ApiStack

app = cdk.App()
project_name = app.node.try_get_context("project_name") or "passos-magicos"
stage = app.node.try_get_context("stage") or "dev"
env = cdk.Environment(
    account=os.getenv("CDK_DEFAULT_ACCOUNT"),
    region=os.getenv("CDK_DEFAULT_REGION") or app.node.try_get_context("region") or "us-east-1",
)

storage = StorageStack(
    app,
    f"{project_name}-{stage}-storage",
    project_name=project_name,
    stage=stage,
    env=env,
)

processing = ProcessingStack(
    app,
    f"{project_name}-{stage}-processing",
    project_name=project_name,
    stage=stage,
    data_bucket=storage.data_bucket,
    metadata_table=storage.metadata_table,
    env=env,
)

mlops = MlOpsStack(
    app,
    f"{project_name}-{stage}-mlops",
    project_name=project_name,
    stage=stage,
    data_bucket=storage.data_bucket,
    metadata_table=storage.metadata_table,
    glue_jobs=processing.glue_jobs,
    env=env,
)

api = ApiStack(
    app,
    f"{project_name}-{stage}-api",
    project_name=project_name,
    stage=stage,
    data_bucket=storage.data_bucket,
    metadata_table=storage.metadata_table,
    state_machine=mlops.state_machine,
    env=env,
)

frontend = FrontendStack(
    app,
    f"{project_name}-{stage}-frontend",
    project_name=project_name,
    stage=stage,
    upload_api_url=processing.upload_api.url,
    predict_api_url=mlops.api_url,
    env=env,
)


api.add_dependency(mlops)
mlops.add_dependency(processing)
processing.add_dependency(storage)

app.synth()
