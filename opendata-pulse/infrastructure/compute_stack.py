"""
Compute Stack - Lambda functions and EventBridge resources
"""

import aws_cdk as cdk
from aws_cdk import (
    aws_lambda as _lambda,
    aws_events as events,
    aws_events_targets as targets,
    aws_iam as iam,
    aws_logs as logs,
    aws_sqs as sqs,
    aws_sns as sns,
    Duration,
    RemovalPolicy
)
from constructs import Construct

class ComputeStack(cdk.Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # Lambda Layer for common dependencies (including Lambda Powertools)
        self.common_layer = _lambda.LayerVersion(
            self, "CommonLayer",
            code=_lambda.Code.from_asset("lambda-functions/layers/common"),
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_9],
            description="Common dependencies including Lambda Powertools for OpenData Pulse Lambda functions"
        )
        
        # Lambda Powertools Layer
        self.powertools_layer = _lambda.LayerVersion(
            self, "PowertoolsLayer",
            code=_lambda.Code.from_asset("lambda-functions/layers/powertools"),
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_9],
            description="AWS Lambda Powertools for observability and best practices"
        )
        
        # SQS Dead Letter Queue for failed processing
        self.dlq = sqs.Queue(
            self, "ProcessingDLQ",
            queue_name="opendata-pulse-processing-dlq",
            retention_period=Duration.days(14),
            removal_policy=RemovalPolicy.DESTROY
        )
        
        # SNS Topic for notifications
        self.notification_topic = sns.Topic(
            self, "NotificationTopic",
            topic_name="opendata-pulse-notifications",
            display_name="OpenData Pulse Notifications"
        )
        
        # IAM Role for Lambda functions
        self.lambda_role = iam.Role(
            self, "LambdaExecutionRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole"),
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaVPCAccessExecutionRole")
            ]
        )
        
        # Enhanced Lambda functions with Powertools
        self.ingest_function = _lambda.Function(
            self, "DataIngestFunction",
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset("lambda-functions/ingest"),
            handler="index.handler",
            timeout=Duration.minutes(5),
            memory_size=512,
            layers=[self.common_layer, self.powertools_layer],
            role=self.lambda_role,
            environment={
                "POWERTOOLS_SERVICE_NAME": "opendata-pulse-ingest",
                "POWERTOOLS_METRICS_NAMESPACE": "OpenDataPulse/Ingest",
                "LOG_LEVEL": "INFO",
                "NSW_API_BASE_URL": "https://data.airquality.nsw.gov.au",
                "NOTIFICATION_TOPIC_ARN": self.notification_topic.topic_arn
            },
            log_retention=logs.RetentionDays.ONE_MONTH,
            dead_letter_queue_enabled=True,
            dead_letter_queue=self.dlq
        )
        
        self.etl_function = _lambda.Function(
            self, "ETLFunction",
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset("lambda-functions/etl"),
            handler="index.handler",
            timeout=Duration.minutes(10),
            memory_size=1024,
            layers=[self.common_layer, self.powertools_layer],
            role=self.lambda_role,
            environment={
                "POWERTOOLS_SERVICE_NAME": "opendata-pulse-etl",
                "POWERTOOLS_METRICS_NAMESPACE": "OpenDataPulse/ETL",
                "LOG_LEVEL": "INFO",
                "NOTIFICATION_TOPIC_ARN": self.notification_topic.topic_arn
            },
            log_retention=logs.RetentionDays.ONE_MONTH,
            dead_letter_queue_enabled=True,
            dead_letter_queue=self.dlq
        )
        
        # Health check function
        self.health_check_function = _lambda.Function(
            self, "HealthCheckFunction",
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset("lambda-functions/health-check"),
            handler="index.handler",
            timeout=Duration.minutes(1),
            memory_size=128,
            layers=[self.common_layer, self.powertools_layer],
            role=self.lambda_role,
            environment={
                "POWERTOOLS_SERVICE_NAME": "opendata-pulse-health-check",
                "POWERTOOLS_METRICS_NAMESPACE": "OpenDataPulse/HealthCheck",
                "LOG_LEVEL": "INFO"
            },
            log_retention=logs.RetentionDays.ONE_WEEK
        )
        
        # EventBridge Rules for scheduling
        self.ingestion_rule = events.Rule(
            self, "DataIngestionRule",
            schedule=events.Schedule.rate(Duration.hours(1)),
            description="Trigger data ingestion every hour"
        )
        
        self.ingestion_rule.add_target(
            targets.LambdaFunction(self.ingest_function)
        )
        
        # Health check rule (every 5 minutes)
        self.health_check_rule = events.Rule(
            self, "HealthCheckRule",
            schedule=events.Schedule.rate(Duration.minutes(5)),
            description="Trigger health check every 5 minutes"
        )
        
        self.health_check_rule.add_target(
            targets.LambdaFunction(self.health_check_function)
        )
        
        # Grant permissions to Lambda functions
        self.notification_topic.grant_publish(self.lambda_role)
        self.dlq.grant_send_messages(self.lambda_role)
        self.dlq.grant_consume_messages(self.lambda_role)
        
        # CloudFormation outputs
        cdk.CfnOutput(
            self, "IngestFunctionName",
            value=self.ingest_function.function_name,
            description="Data ingestion Lambda function name"
        )
        
        cdk.CfnOutput(
            self, "ETLFunctionName",
            value=self.etl_function.function_name,
            description="ETL processing Lambda function name"
        )
        
        cdk.CfnOutput(
            self, "HealthCheckFunctionName",
            value=self.health_check_function.function_name,
            description="Health check Lambda function name"
        )
        
        cdk.CfnOutput(
            self, "NotificationTopicArn",
            value=self.notification_topic.topic_arn,
            description="SNS notification topic ARN"
        )
        
        cdk.CfnOutput(
            self, "DLQUrl",
            value=self.dlq.queue_url,
            description="Dead Letter Queue URL"
        ) 