from aws_cdk import (
    aws_s3 as s3,
    aws_s3_deployment as s3_deploy,
    Stack
)
from constructs import Construct

class S3Stack(Stack):
    def __init__(self, scope: Construct, construct_id: str, configs_s3: dict, **kwargs):
        self.bucket_name = kwargs.pop("bucket_name")
        self.versioned = configs_s3['versioned']
        
        super().__init__(scope, construct_id, **kwargs)

        self.bucket = s3.Bucket(
            self,
            "b3DataBucket",
            bucket_name=self.bucket_name,
            versioned=self.versioned
        )


    def deployment(self, describe, destination, path_source, prefix):
        s3_deploy.BucketDeployment(
            self, describe,
            destination_bucket=destination,
            sources=[s3_deploy.Source.asset(path_source)],
            destination_key_prefix=prefix
        )
        return True

    def get_bucket(self):
        return self.bucket
