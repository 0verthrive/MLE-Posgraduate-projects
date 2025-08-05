from aws_cdk import (
    aws_lambda as _lambda,
    aws_iam as iam,
    aws_s3 as s3,
    aws_s3_notifications as s3n,
    Stack,
    Duration
)
from constructs import Construct

class LambdaStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, configs_lambda: dict, s3_bucket: s3.Bucket, **kwargs):
        self.account_id = kwargs.pop("account_id")
        self.bucket_arn = kwargs.pop("bucket_arn")

        super().__init__(scope, construct_id, **kwargs)
        
        lambda_role = iam.Role.from_role_arn(
            self,
            "LambdaExecutionRole",
            role_arn=f'arn:aws:iam::{self.account_id}:{configs_lambda["role"]}',
            mutable=False
        )

        self.lambda_function = _lambda.Function(
            self, "TriggerGlueJobFunction",
            function_name=configs_lambda["function_name"],
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="lambda_function.handler",
            code=_lambda.Code.from_asset(configs_lambda["assets"]),
            role=lambda_role,
            environment={
                "GLUE_JOB_NAME": configs_lambda["glue_job_name"]
            },
            timeout=Duration.seconds(300)
        )

        s3_bucket.grant_read(self.lambda_function)
        self.lambda_function.add_permission(
            "AllowS3Invoke",
            principal=iam.ServicePrincipal("s3.amazonaws.com"),
            action="lambda:InvokeFunction",
            source_arn=self.bucket_arn
        )

        notification = s3n.LambdaDestination(self.lambda_function)
        s3_bucket.add_event_notification(
            s3.EventType.OBJECT_CREATED,
            notification,
            s3.NotificationKeyFilter(prefix="raw/", suffix=".parquet")
        )

    def get_lambda(self):
        return self.lambda_function