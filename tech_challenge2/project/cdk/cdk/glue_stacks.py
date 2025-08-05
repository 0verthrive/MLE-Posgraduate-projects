from aws_cdk import (
    aws_glue as glue,
    aws_iam as iam,
    Stack,
)
from constructs import Construct

class GlueStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, params:dict, **kwargs):
        self.bucket_url = kwargs.pop("bucket_url")
        self.account_id = kwargs.pop("account_id")
        self.database_name = params["database_name"]
        self.table_name = params["table_name"]

        super().__init__(scope, construct_id, **kwargs)
        
        self.database = glue.CfnDatabase(self, "GlueDatabase",
            catalog_id=self.account_id,
            database_input=glue.CfnDatabase.DatabaseInputProperty(
                name=self.database_name
            )
        )

        self.table = glue.CfnTable(self, "RefinedParquetTable",
            catalog_id=self.account_id,
            database_name=self.database_name,
            table_input=glue.CfnTable.TableInputProperty(
                name=self.table_name,
                table_type="EXTERNAL_TABLE",
                parameters={"classification": "parquet"},
                storage_descriptor=glue.CfnTable.StorageDescriptorProperty(
                    columns=[
                        {"name": "id", "type": "bigint"},
                        {"name": "codigo", "type": "string"},
                        {"name": "tipo", "type": "string"},
                        {"name": "qtde_teorica", "type": "double"}
                    ],
                    location=f"{self.bucket_url}/refined/",
                    input_format="org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat",
                    output_format="org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat",
                    serde_info=glue.CfnTable.SerdeInfoProperty(
                        serialization_library="org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe",
                        parameters={"serialization.format": "1"}
                    )
                ),
                partition_keys=[
                    glue.CfnTable.ColumnProperty(name="data", type="date")
                ]
            )
        )

        self.table.add_dependency(self.database)

        self.glue_job = glue.CfnJob(self, 'JobRefinamentoB3',
            name=params['job_name'],
            role=f'arn:aws:iam::{self.account_id}:{params["role"]}',
            command=glue.CfnJob.JobCommandProperty(
                name='glueetl',
                python_version='3',
                script_location=f'{self.bucket_url}/{params["script"]}job_script.py'
            ),
            default_arguments={
                "--job-language": "python",
                "--TARGET_PATH": f'{self.bucket_url}/refined/',
                "--TempDir": f'{self.bucket_url}/{params["temp"]}'
            },
            glue_version="4.0",
            number_of_workers=2,
            worker_type="G.1X",
            timeout= 1200
        )

    def get_job(self):
        return self.glue_job
