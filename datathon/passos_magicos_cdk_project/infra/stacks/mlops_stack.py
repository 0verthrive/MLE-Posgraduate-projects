from pathlib import Path
from aws_cdk import (
    Stack,
    CfnOutput,
    Duration,
    Tags,
    aws_iam as iam,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_logs as logs,
    aws_events as events,
    aws_events_targets as targets,
    aws_lambda as lambda_,
    aws_stepfunctions as sfn,
    aws_stepfunctions_tasks as tasks,
    aws_cloudwatch as cloudwatch,
)
from constructs import Construct

from .common import ProjectTags


class MlOpsStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        project_name: str,
        stage: str,
        data_bucket,
        metadata_table,
        glue_jobs: dict,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        tags = ProjectTags(project_name, stage)
        base_dir = Path(__file__).resolve().parents[2]

        self.vpc = ec2.Vpc(self, "MlVpc", max_azs=2, nat_gateways=1)
        self.cluster = ecs.Cluster(self, "MlCluster", vpc=self.vpc)

        train_task_definition = ecs.FargateTaskDefinition(
            self,
            "TrainingTaskDefinition",
            cpu=1024,
            memory_limit_mib=2048,
        )
        
        train_container = train_task_definition.add_container(
            "Trainer",
            image=ecs.ContainerImage.from_asset(str(base_dir / "src" / "training")),
            logging=ecs.LogDrivers.aws_logs(stream_prefix="trainer"),
            environment={
                "DATA_BUCKET": data_bucket.bucket_name,
                "MODEL_PREFIX": "artifacts/models",
                "METADATA_TABLE": metadata_table.table_name,
            },
        )
        train_container.add_port_mappings(ecs.PortMapping(container_port=8080))
        data_bucket.grant_read_write(train_task_definition.task_role)
        metadata_table.grant_read_write_data(train_task_definition.task_role)

        monitoring_fn = lambda_.DockerImageFunction(
            self,
            "MonitoringFunction",
            code=lambda_.DockerImageCode.from_image_asset(str(base_dir / "src" / "monitoring")),
            memory_size=512,
            timeout=Duration.minutes(5),
            environment={
                "DATA_BUCKET": data_bucket.bucket_name,
                "METADATA_TABLE": metadata_table.table_name,
                "NAMESPACE": f"{project_name}/{stage}/mlops",
            },
        )
        data_bucket.grant_read_write(monitoring_fn)
        metadata_table.grant_read_write_data(monitoring_fn)
        
        monitoring_fn.add_to_role_policy(
            iam.PolicyStatement(
                actions=["cloudwatch:PutMetricData"],
                resources=["*"],
            )
        )

        etl_step = tasks.GlueStartJobRun(
            self,
            "RunEtlJob",
            glue_job_name=glue_jobs["etl"],
            integration_pattern=sfn.IntegrationPattern.RUN_JOB,
            arguments=sfn.TaskInput.from_object({
                "--DATA_BUCKET": data_bucket.bucket_name,
            }),
        )

        dq_step = tasks.GlueStartJobRun(
            self,
            "RunDataQualityJob",
            glue_job_name=glue_jobs["dq"],
            integration_pattern=sfn.IntegrationPattern.RUN_JOB,
            arguments=sfn.TaskInput.from_object({
                "--DATA_BUCKET": data_bucket.bucket_name,
            }),
        )

        train_step = tasks.EcsRunTask(
            self,
            "RunTrainingTask",
            integration_pattern=sfn.IntegrationPattern.RUN_JOB,
            cluster=self.cluster,
            task_definition=train_task_definition,
            launch_target=tasks.EcsFargateLaunchTarget(
                platform_version=ecs.FargatePlatformVersion.LATEST
            ),
            assign_public_ip=True,
            container_overrides=[
                tasks.ContainerOverride(
                    container_definition=train_container,
                    environment=[
                        tasks.TaskEnvironmentVariable(name="RUN_ID", value=sfn.JsonPath.string_at("$$.Execution.Id")),
                    ],
                )
            ],
        )

        monitoring_step = tasks.LambdaInvoke(
            self,
            "RunMonitoring",
            lambda_function=monitoring_fn,
            payload=sfn.TaskInput.from_object({
                "mode": "stepfunction",
                "execution_id": sfn.JsonPath.string_at("$$.Execution.Id"),
            }),
            result_path=sfn.JsonPath.DISCARD,
        )

        success = sfn.Succeed(self, "TrainingPipelineFinished")
        chain = etl_step.next(dq_step).next(train_step).next(monitoring_step).next(success)

        log_group = logs.LogGroup(self, "StateMachineLogs")
        self.state_machine = sfn.StateMachine(
            self,
            "TrainingStateMachine",
            definition_body=sfn.DefinitionBody.from_chainable(chain),
            timeout=Duration.hours(2),
            logs=sfn.LogOptions(destination=log_group, level=sfn.LogLevel.ALL),
        )

        events.Rule(
            self,
            "DailyMonitoringSchedule",
            schedule=events.Schedule.rate(Duration.days(1)),
            targets=[targets.LambdaFunction(monitoring_fn, event=events.RuleTargetInput.from_object({"mode": "scheduled"}))],
        )

        dashboard = cloudwatch.Dashboard(
            self,
            "MlOpsDashboard",
            dashboard_name=f"{project_name}-{stage}-mlops",
        )
        dashboard.add_widgets(
            cloudwatch.GraphWidget(
                title="Prediction Count",
                left=[cloudwatch.Metric(namespace=f"{project_name}/{stage}/mlops", metric_name="PredictionCount")],
            ),
            cloudwatch.GraphWidget(
                title="Drift Score",
                left=[cloudwatch.Metric(namespace=f"{project_name}/{stage}/mlops", metric_name="DriftScore")],
            ),
        )

        api_fn = lambda_.DockerImageFunction(
            self,
            "PredictApiFunction",
            code=lambda_.DockerImageCode.from_image_asset(str(base_dir / "src" / "api")),
            memory_size=1024,
            timeout=Duration.minutes(1),
            environment={
                "DATA_BUCKET": data_bucket.bucket_name,
                "MODEL_PREFIX": "artifacts/models",
                "PREDICTIONS_PREFIX": "predictions",
                "METADATA_TABLE": metadata_table.table_name,
                "STATE_MACHINE_ARN": self.state_machine.state_machine_arn,
            },
        )

        data_bucket.grant_read_write(api_fn)
        metadata_table.grant_read_write_data(api_fn)
        self.state_machine.grant_start_execution(api_fn)

        api_fn_url = api_fn.add_function_url(
            auth_type=lambda_.FunctionUrlAuthType.NONE
        )

        self.api_url = api_fn_url.url

        for k, v in tags.as_dict().items():
            Tags.of(self).add(k, v)

        CfnOutput(self, "StateMachineArn", value=self.state_machine.state_machine_arn)
        CfnOutput(self, "DashboardName", value=dashboard.dashboard_name)
        CfnOutput(self, "ApiUrl", value=self.api_url)
