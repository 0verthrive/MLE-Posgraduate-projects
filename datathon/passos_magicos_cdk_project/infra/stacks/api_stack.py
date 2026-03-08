from pathlib import Path
from aws_cdk import (
    Stack,
    CfnOutput,
    Duration,
    Tags,
    aws_lambda as lambda_,
)
from constructs import Construct

from .common import ProjectTags


class ApiStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        project_name: str,
        stage: str,
        data_bucket,
        metadata_table,
        state_machine,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        tags = ProjectTags(project_name, stage)
        base_dir = Path(__file__).resolve().parents[2]

        api_fn = lambda_.DockerImageFunction(
            self,
            "FastApiFunction",
            code=lambda_.DockerImageCode.from_image_asset(str(base_dir / "src" / "api")),
            timeout=Duration.seconds(30),
            memory_size=1024,
            environment={
                "DATA_BUCKET": data_bucket.bucket_name,
                "MODEL_PREFIX": "artifacts/models",
                "PREDICTIONS_PREFIX": "predictions",
                "METADATA_TABLE": metadata_table.table_name,
                "STATE_MACHINE_ARN": state_machine.state_machine_arn,
            },
        )

        url = api_fn.add_function_url(auth_type=lambda_.FunctionUrlAuthType.NONE)
        data_bucket.grant_read_write(api_fn)
        metadata_table.grant_read_write_data(api_fn)
        state_machine.grant_start_execution(api_fn)

        for k, v in tags.as_dict().items():
            Tags.of(self).add(k, v)

        CfnOutput(self, "ApiUrl", value=url.url)
