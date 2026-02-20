"""
AWS CDK Stack - Word-to-JATS Conversion Platform

Define: VPC, ECS Fargate (GROBID), S3, Step Functions, Lambdas.
"""
from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_ecs_patterns as ecs_patterns,
    aws_s3 as s3,
    aws_lambda as lambda_,
    aws_stepfunctions as sfn,
    aws_stepfunctions_tasks as sfn_tasks,
    aws_iam as iam,
)
from constructs import Construct
import os


class WordToJatsStack(Stack):
    """Stack principal para la plataforma Word-to-JATS."""

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # --- VPC ---
        self.vpc = ec2.Vpc(
            self,
            "WordToJatsVpc",
            max_azs=2,
            nat_gateways=1,
        )

        # --- S3 Buckets ---
        self.input_bucket = s3.Bucket(
            self,
            "InputBucket",
            removal_policy=RemovalPolicy.RETAIN,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
        )
        self.output_bucket = s3.Bucket(
            self,
            "OutputBucket",
            removal_policy=RemovalPolicy.RETAIN,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
        )

        # --- ECS Cluster for GROBID ---
        self.cluster = ecs.Cluster(
            self,
            "WordToJatsCluster",
            vpc=self.vpc,
            container_insights=True,
        )

        # GROBID task definition - imagen oficial de GROBID
        grobid_task_def = ecs.FargateTaskDefinition(
            self,
            "GrobidTaskDef",
            memory_limit_mib=4096,
            cpu=2048,
            runtime_platform=ecs.RuntimePlatform(
                cpu_architecture=ecs.CpuArchitecture.X86_64,
                operating_system_family=ecs.OperatingSystemFamily.LINUX,
            ),
        )
        grobid_task_def.add_container(
            "grobid",
            image=ecs.ContainerImage.from_registry("lfoppiano/grobid:0.8.0"),
            port_mappings=[ecs.PortMapping(container_port=8070)],
            logging=ecs.LogDrivers.aws_logs(stream_prefix="grobid"),
            environment={"JAVA_OPTS": "-Xmx2g"},
        )

        # Fargate service con ALB
        self.grobid_service = ecs_patterns.ApplicationLoadBalancedFargateService(
            self,
            "GrobidService",
            cluster=self.cluster,
            task_definition=grobid_task_def,
            desired_count=1,
            public_load_balancer=True,
            listener_port=8070,
        )
        # Ajustar target group para puerto 8070
        self.grobid_service.target_group.configure_health_check(path="/api/isalive")

        # Obtener URL del ALB para GROBID (una vez desplegado)
        self.grobid_url = (
            f"http://{self.grobid_service.load_balancer.load_balancer_dns_name}:8070"
        )

        # --- Lambdas ---
        lambda_runtime = lambda_.Runtime.PYTHON_3_12
        lambda_common = {
            "runtime": lambda_runtime,
            "timeout": Duration.minutes(5),
            "memory_size": 512,
        }

        # Pre-processor Lambda
        self.preprocessor_lambda = lambda_.Function(
            self,
            "PreprocessorLambda",
            code=lambda_.Code.from_asset("src/handlers"),
            handler="preprocessor_handler.handler",
            function_name="word-to-jats-preprocessor",
            environment={
                "INPUT_BUCKET": self.input_bucket.bucket_name,
                "OUTPUT_BUCKET": self.output_bucket.bucket_name,
            },
            **lambda_common,
        )
        self.input_bucket.grant_read(self.preprocessor_lambda)
        self.output_bucket.grant_read_write(self.preprocessor_lambda)

        # Merger Lambda
        self.merger_lambda = lambda_.Function(
            self,
            "MergerLambda",
            code=lambda_.Code.from_asset("src"),
            handler="handlers.merger_handler.handler",
            function_name="word-to-jats-merger",
            environment={
                "OUTPUT_BUCKET": self.output_bucket.bucket_name,
            },
            **lambda_common,
        )
        self.output_bucket.grant_read_write(self.merger_lambda)

        # Validator Lambda
        self.validator_lambda = lambda_.Function(
            self,
            "ValidatorLambda",
            code=lambda_.Code.from_asset("src"),
            handler="handlers.validator_handler.handler",
            function_name="word-to-jats-validator",
            environment={
                "OUTPUT_BUCKET": self.output_bucket.bucket_name,
            },
            **lambda_common,
        )
        self.output_bucket.grant_read_write(self.validator_lambda)

        # Permisos Bedrock para las Lambdas que lo usen
        bedrock_policy = iam.ManagedPolicy.from_aws_managed_policy_name(
            "AmazonBedrockFullAccess"
        )
        self.merger_lambda.role.add_managed_policy(bedrock_policy)

        # --- Step Functions State Machine ---
        # Preprocessor
        preprocessor_task = sfn_tasks.LambdaInvoke(
            self, "PreprocessorTask", lambda_function=self.preprocessor_lambda
        )
        # Parallel: Grobid, Pandoc, Bedrock (usaremos merger para coordinar; las vías se invocan desde merger por simplicidad inicial)
        merger_task = sfn_tasks.LambdaInvoke(
            self, "MergerTask", lambda_function=self.merger_lambda
        )
        validator_task = sfn_tasks.LambdaInvoke(
            self, "ValidatorTask", lambda_function=self.validator_lambda
        )

        definition = preprocessor_task.next(merger_task).next(validator_task)

        sfn.StateMachine(
            self,
            "WordToJatsStateMachine",
            definition_body=sfn.DefinitionBody.from_chainable(definition),
            state_machine_name="word-to-jats-workflow",
        )
