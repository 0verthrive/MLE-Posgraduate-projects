from pathlib import Path
from aws_cdk import (
    Stack,
    RemovalPolicy,
    CfnOutput,
    Tags,
    Duration,
    aws_s3 as s3,
    aws_dynamodb as dynamodb,
    aws_athena as athena,
    aws_lambda as lambda_,
    aws_s3_notifications as s3n,
)
from constructs import Construct

from .common import ProjectTags


class StorageStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        project_name: str,
        stage: str,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        tags = ProjectTags(project_name, stage)
        base_dir = Path(__file__).resolve().parents[2]

        self.data_bucket = s3.Bucket(
            self,
            "DataLakeBucket",
            versioned=True,
            enforce_ssl=True,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            encryption=s3.BucketEncryption.S3_MANAGED,
            lifecycle_rules=[
                s3.LifecycleRule(
                    enabled=True,
                    expiration=Duration.days(365),
                )
            ],
            auto_delete_objects=True,
            removal_policy=RemovalPolicy.DESTROY if stage != "prod" else RemovalPolicy.RETAIN,
        )

        self.metadata_table = dynamodb.Table(
            self,
            "MetadataTable",
            partition_key=dynamodb.Attribute(name="pk", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="sk", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            point_in_time_recovery_specification=dynamodb.PointInTimeRecoverySpecification(
                point_in_time_recovery_enabled=True
            ),
            removal_policy=RemovalPolicy.DESTROY if stage != "prod" else RemovalPolicy.RETAIN,
        )

        athena_results_bucket = s3.Bucket(
            self,
            "AthenaResultsBucket",
            versioned=False,
            enforce_ssl=True,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            encryption=s3.BucketEncryption.S3_MANAGED,
            auto_delete_objects=True,
            removal_policy=RemovalPolicy.DESTROY if stage != "prod" else RemovalPolicy.RETAIN,
        )

        self.workgroup = athena.CfnWorkGroup(
            self,
            "AthenaWorkgroup",
            name=f"{project_name}-{stage}-wg",
            recursive_delete_option=True,
            state="ENABLED",
            work_group_configuration=athena.CfnWorkGroup.WorkGroupConfigurationProperty(
                result_configuration=athena.CfnWorkGroup.ResultConfigurationProperty(
                    output_location=f"s3://{athena_results_bucket.bucket_name}/results/"
                )
            ),
        )

        self.xlsx_to_parquet_function = lambda_.DockerImageFunction(
            self,
            "XlsxToParquetFunction",
            code=lambda_.DockerImageCode.from_image_asset(
                str(base_dir / "src" / "lambda_xlsx_to_parquet")
            ),
            memory_size=2048,
            timeout=Duration.minutes(5),
            environment={
                "DATA_BUCKET": self.data_bucket.bucket_name,
                "INPUT_PREFIX": "raw/xlsx/",
                "OUTPUT_PREFIX": "raw/parquet/",
                "METADATA_TABLE": self.metadata_table.table_name,
            },
        )

        self.data_bucket.grant_read_write(self.xlsx_to_parquet_function)
        self.metadata_table.grant_read_write_data(self.xlsx_to_parquet_function)

        self.data_bucket.add_event_notification(
            s3.EventType.OBJECT_CREATED_PUT,
            s3n.LambdaDestination(self.xlsx_to_parquet_function),
            s3.NotificationKeyFilter(prefix="raw/xlsx/", suffix=".xlsx"),
        )

        for k, v in tags.as_dict().items():
            Tags.of(self).add(k, v)

        CfnOutput(self, "DataBucketName", value=self.data_bucket.bucket_name)
        CfnOutput(self, "MetadataTableName", value=self.metadata_table.table_name)