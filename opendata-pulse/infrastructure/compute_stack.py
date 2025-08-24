"""
Compute Stack - Lambda functions and EventBridge resources
"""

import aws_cdk as cdk
from aws_cdk import (
    aws_lambda as _lambda,
    aws_events as events,
    aws_events_targets as targets,
    aws_iam as iam,
    Duration
)
from constructs import Construct

class ComputeStack(cdk.Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # Lambda Layer for common dependencies
        self.common_layer = _lambda.LayerVersion(
            self, "CommonLayer",
            code=_lambda.Code.from_asset("lambda-functions/layers/common"),
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_9],
            description="Common dependencies for OpenData Pulse Lambda functions"
        )
        
        # Basic Lambda functions (placeholders)
        self.ingest_function = _lambda.Function(
            self, "DataIngestFunction",
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset("lambda-functions/ingest"),
            handler="index.handler",
            timeout=Duration.minutes(5),
            memory_size=512,
            layers=[self.common_layer]
        )
        
        self.etl_function = _lambda.Function(
            self, "ETLFunction",
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset("lambda-functions/etl"),
            handler="index.handler",
            timeout=Duration.minutes(10),
            memory_size=1024,
            layers=[self.common_layer]
        )
        
        # EventBridge Rule for scheduled ingestion
        self.ingestion_rule = events.Rule(
            self, "DataIngestionRule",
            schedule=events.Schedule.rate(Duration.hours(1)),
            description="Trigger data ingestion every hour"
        )
        
        self.ingestion_rule.add_target(
            targets.LambdaFunction(self.ingest_function)
        ) 