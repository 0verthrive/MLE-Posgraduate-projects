from pathlib import Path
from aws_cdk import (
    Stack,
    CfnOutput,
    Duration,
    Tags,
    aws_apigateway as apigateway,
    aws_glue as glue,
    aws_iam as iam,
    aws_lambda as lambda_,
    aws_s3_deployment as s3deploy,
    aws_sqs as sqs,
)

from constructs import Construct

from .common import ProjectTags


class ProcessingStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        project_name: str,
        stage: str,
        data_bucket,
        metadata_table,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        tags = ProjectTags(project_name, stage)
        base_dir = Path(__file__).resolve().parents[2]

        self.ingestion_queue = sqs.Queue(
            self,
            "IngestionQueue",
            visibility_timeout=Duration.minutes(5),
            retention_period=Duration.days(4),
        )

        upload_fn = lambda_.Function(
            self,
            "UploadRawXlsxFunction",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="app.handler",
            code=lambda_.Code.from_asset(str(base_dir / "src" / "lambda_upload")),
            memory_size=512,
            timeout=Duration.minutes(1),
            environment={
                "DATA_BUCKET": data_bucket.bucket_name,
                "UPLOAD_PREFIX": "raw/xlsx/",
                "METADATA_TABLE": metadata_table.table_name,
            },
        )
        data_bucket.grant_put(upload_fn)
        metadata_table.grant_read_write_data(upload_fn)

        self.upload_api = apigateway.RestApi(
            self,
            "RawUploadApi",
            rest_api_name=f"{project_name}-{stage}-raw-upload-api",
            description="API para upload de arquivos XLSX para a camada raw.",
            binary_media_types=[
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "application/octet-stream",
                "multipart/form-data",
            ],
            deploy_options=apigateway.StageOptions(stage_name=stage),
        )

        upload_integration = apigateway.LambdaIntegration(upload_fn, proxy=True)
        files_resource = self.upload_api.root.add_resource("files")
        files_resource.add_method("POST", upload_integration)
        named_file_resource = files_resource.add_resource("{filename}")
        named_file_resource.add_method("POST", upload_integration)
        named_file_resource.add_method("PUT", upload_integration)

        glue_role = iam.Role(
            self,
            "GlueRole",
            assumed_by=iam.ServicePrincipal("glue.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSGlueServiceRole"
                )
            ],
        )
        data_bucket.grant_read_write(glue_role)
        metadata_table.grant_read_write_data(glue_role)

        s3deploy.BucketDeployment(
            self,
            "DeployGlueScripts",
            destination_bucket=data_bucket,
            destination_key_prefix="artifacts/glue",
            sources=[s3deploy.Source.asset(str(base_dir / "src" / "glue"))],
        )

        self.glue_database = glue.CfnDatabase(
            self,
            "GlueDatabase",
            catalog_id=self.account,
            database_input=glue.CfnDatabase.DatabaseInputProperty(
                name=f"{project_name}_{stage}_db".replace("-", "_")
            ),
        )

        etl_script = glue.CfnJob(
            self,
            "EtlJob",
            name=f"{project_name}-{stage}-etl",
            role=glue_role.role_arn,
            glue_version="4.0",
            command=glue.CfnJob.JobCommandProperty(
                name="glueetl",
                script_location=f"s3://{data_bucket.bucket_name}/artifacts/glue/etl_job.py",
                python_version="3",
            ),
            default_arguments={
                "--job-language": "python",
                "--enable-metrics": "true",
                "--enable-continuous-cloudwatch-log": "true",
                "--DATA_BUCKET": data_bucket.bucket_name,
                "--RAW_PARQUET_PREFIX": "raw/parquet/",
                "--GOLD_PREFIX": "gold/",
            },
            execution_property=glue.CfnJob.ExecutionPropertyProperty(
                max_concurrent_runs=1
            ),
            worker_type="G.1X",
            number_of_workers=2,
            timeout=30,
        )

        dq_script = glue.CfnJob(
            self,
            "DataQualityJob",
            name=f"{project_name}-{stage}-dq",
            role=glue_role.role_arn,
            glue_version="4.0",
            command=glue.CfnJob.JobCommandProperty(
                name="glueetl",
                script_location=f"s3://{data_bucket.bucket_name}/artifacts/glue/data_quality_job.py",
                python_version="3",
            ),
            default_arguments={
                "--job-language": "python",
                "--enable-metrics": "true",
                "--enable-continuous-cloudwatch-log": "true",
                "--DATA_BUCKET": data_bucket.bucket_name,
                "--TRAINING_DATASET_KEY": "gold/training/training_dataset.parquet",
            },
            execution_property=glue.CfnJob.ExecutionPropertyProperty(
                max_concurrent_runs=1
            ),
            worker_type="G.1X",
            number_of_workers=2,
            timeout=30,
        )

        self.glue_jobs = {
            "etl": etl_script.name,
            "dq": dq_script.name,
        }

        for k, v in tags.as_dict().items():
            Tags.of(self).add(k, v)

        CfnOutput(self, "QueueUrl", value=self.ingestion_queue.queue_url)
        CfnOutput(self, "EtlJobName", value=etl_script.name)
        CfnOutput(self, "DqJobName", value=dq_script.name)
        CfnOutput(self, "UploadApiUrl", value=self.upload_api.url)