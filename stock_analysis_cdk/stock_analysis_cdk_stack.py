from constructs import Construct

from aws_cdk import (aws_ec2 as ec2, 
                     aws_ecs as ecs,
                     aws_ecr as ecr,
                     aws_ecs_patterns as ecs_patterns,
                     Stack, CfnOutput, Duration
                    )

import os, dotenv

dotenv.load_dotenv()

class StockAnalysisCdkStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # VPC
        vpc = ec2.Vpc(self, 
                      "StockAnalysisVpc", 
                      gateway_endpoints={
                            "S3": ec2.GatewayVpcEndpointOptions(
                                service=ec2.GatewayVpcEndpointAwsService.S3
                            )
                        },
                      max_azs=2)

        # VPC Interface Endpoints
        ec2.InterfaceVpcEndpoint(self, "VPC Endpoint Docker",
            vpc=vpc,
            service=ec2.InterfaceVpcEndpointService(f"com.amazonaws.{os.environ.get('AWS_REGION')}.ecr.dkr"),
        )

        ec2.InterfaceVpcEndpoint(self, "VPC Endpoint ECR API",
            vpc=vpc,
            service=ec2.InterfaceVpcEndpointService(f"com.amazonaws.{os.environ.get('AWS_REGION')}.ecr.api"),
        )

        # ECR Repo
        repository = ecr.Repository.from_repository_arn(
            self,
            construct_id,
            repository_arn=os.environ.get('ECR_REPO_ARN'))
        
        # ECS Cluster
        cluster = ecs.Cluster(self, "StockAnalysisCluster", vpc=vpc)

        # Fargate
        fargate_service = ecs_patterns.NetworkLoadBalancedFargateService(
            self, "FargateService",
            cluster=cluster,
            task_image_options=ecs_patterns.NetworkLoadBalancedTaskImageOptions(
                image=ecs.ContainerImage.from_ecr_repository(repository, tag="latest"),
            )
        )

        fargate_service.service.connections.security_groups[0].add_ingress_rule(
            peer = ec2.Peer.ipv4(vpc.vpc_cidr_block),
            connection = ec2.Port.tcp(80),
            description="Allow http inbound from VPC"
        )

        # AutoScaling policy
        scaling = fargate_service.service.auto_scale_task_count(
            max_capacity=2
        )
        scaling.scale_on_cpu_utilization(
            "CpuScaling",
            target_utilization_percent=50,
            scale_in_cooldown=Duration.seconds(60),
            scale_out_cooldown=Duration.seconds(60),
        )

        CfnOutput(
            self, "LoadBalancerDNS",
            value=fargate_service.load_balancer.load_balancer_dns_name
        )