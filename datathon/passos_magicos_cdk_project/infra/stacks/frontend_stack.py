from pathlib import Path
from aws_cdk import (
    Stack,
    CfnOutput,
    Duration,
    Tags,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_ecs_patterns as ecs_patterns,
)
from constructs import Construct

from .common import ProjectTags


class FrontendStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        project_name: str,
        stage: str,
        upload_api_url: str,
        predict_api_url: str,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        tags = ProjectTags(project_name, stage)
        base_dir = Path(__file__).resolve().parents[2]

        vpc = ec2.Vpc(
            self,
            "FrontendVpc",
            max_azs=2,
            nat_gateways=1 if stage == "prod" else 0,
        )

        cluster = ecs.Cluster(
            self,
            "FrontendCluster",
            vpc=vpc,
            cluster_name=f"{project_name}-{stage}-frontend-cluster",
        )

        service = ecs_patterns.ApplicationLoadBalancedFargateService(
            self,
            "FrontendService",
            cluster=cluster,
            cpu=256,
            memory_limit_mib=512,
            desired_count=1,
            public_load_balancer=True,
            assign_public_ip=True,
            health_check_grace_period=Duration.seconds(180),
            task_image_options=ecs_patterns.ApplicationLoadBalancedTaskImageOptions(
                image=ecs.ContainerImage.from_asset(str(base_dir / "src" / "frontend")),
                container_port=8501,
                environment={
                    "UPLOAD_API_URL": upload_api_url,
                    "PREDICT_API_URL": predict_api_url,
                },
            ),
        )

        service.service.connections.allow_from(
            service.load_balancer,
            ec2.Port.tcp(8501),
            "Allow ALB to reach Streamlit on port 8501",
        )

        service.target_group.configure_health_check(
            path="/",
            port="8501",
            healthy_http_codes="200",
            interval=Duration.seconds(30),
            timeout=Duration.seconds(10),
            healthy_threshold_count=2,
            unhealthy_threshold_count=5,
        )

        for k, v in tags.as_dict().items():
            Tags.of(self).add(k, v)

        CfnOutput(self, "FrontendUrl", value=f"http://{service.load_balancer.load_balancer_dns_name}")