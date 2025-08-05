from aws_cdk import Stack
from constructs import Construct
from cdk.s3_stack import S3Stack
from cdk.glue_stacks import GlueStack
from cdk.lambda_stack import LambdaStack

class CdkStack(Stack):
    def __init__(self, scope: Construct, id: str, configs: dict, **kwargs):
        self.bucket_name = kwargs.pop("bucket_name", None)
        self.bucket_url = kwargs.pop("bucket_url", None)
        self.bucket_arn = kwargs.pop("bucket_arn", None)
        self.account_id = kwargs.pop("account_id", None)

        super().__init__(scope, id, **kwargs)

        s3_stack = S3Stack(scope=self, construct_id='S3Stack', configs_s3=configs["S3"], bucket_name=self.bucket_name)
        bucket = s3_stack.get_bucket()

        s3_stack.deployment("scriptGlueDeploy", bucket, configs["Glue"]["assets"], configs["Glue"]["script"])

        glue_stack = GlueStack(self, "GlueStack", configs["Glue"], bucket_url=self.bucket_url, account_id=self.account_id)
        glue_stack.get_job()

        lambda_stack = LambdaStack(self, "LambdaStack", configs["Lambda"], bucket, bucket_arn=self.bucket_arn, account_id=self.account_id)
        lambda_stack.get_lambda()
        
        s3_stack.deployment("rawFilesDeploy", bucket, configs["S3"]["assets"], configs["S3"]["prefix"])
