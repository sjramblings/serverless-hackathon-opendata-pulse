"""
Data Stack - S3, DynamoDB, Glue, and Athena resources
"""

import aws_cdk as cdk
from aws_cdk import (
    aws_s3 as s3,
    aws_dynamodb as dynamodb,
    aws_glue as glue,
    aws_athena as athena,
    aws_iam as iam,
    RemovalPolicy,
    Duration
)
from constructs import Construct

class DataStack(cdk.Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # S3 Buckets with NSW-specific naming
        bucket_prefix = "opendata-pulse"
        
        self.raw_bucket = s3.Bucket(
            self, "RawDataBucket",
            bucket_name=f"{bucket_prefix}-raw-data-{cdk.Aws.ACCOUNT_ID}",
            versioned=True,
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            lifecycle_rules=[
                s3.LifecycleRule(
                    id="RawDataLifecycle",
                    enabled=True,
                    transitions=[
                        s3.Transition(
                            storage_class=s3.StorageClass.INFREQUENT_ACCESS,
                            transition_after=Duration.days(30)
                        ),
                        s3.Transition(
                            storage_class=s3.StorageClass.GLACIER,
                            transition_after=Duration.days(90)
                        )
                    ],
                    expiration=Duration.days(365)
                )
            ],
            removal_policy=RemovalPolicy.RETAIN
        )
        
        self.curated_bucket = s3.Bucket(
            self, "CuratedDataBucket",
            bucket_name=f"{bucket_prefix}-curated-data-{cdk.Aws.ACCOUNT_ID}",
            versioned=True,
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.RETAIN
        )
        
        self.exports_bucket = s3.Bucket(
            self, "ExportsBucket",
            bucket_name=f"{bucket_prefix}-exports-{cdk.Aws.ACCOUNT_ID}",
            versioned=False,
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            lifecycle_rules=[
                s3.LifecycleRule(
                    id="ExportsLifecycle",
                    enabled=True,
                    expiration=Duration.days(7)
                )
            ],
            removal_policy=RemovalPolicy.DESTROY
        )
        
        # DynamoDB Table for hot aggregates
        self.air_quality_table = dynamodb.Table(
            self, "AirQualityTable",
            table_name="opendata-pulse-air-quality",
            partition_key=dynamodb.Attribute(
                name="PK",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="SK",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            time_to_live_attribute="TTL",
            removal_policy=RemovalPolicy.RETAIN
        )
        
        # Add GSI for geographic queries
        self.air_quality_table.add_global_secondary_index(
            index_name="SuburbIndex",
            partition_key=dynamodb.Attribute(
                name="SUBURB",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="TIMESTAMP",
                type=dynamodb.AttributeType.STRING
            )
        )
        
        # Glue Database
        self.glue_database = glue.CfnDatabase(
            self, "OpenDataPulseDatabase",
            catalog_id=cdk.Aws.ACCOUNT_ID,
            database_input=glue.CfnDatabase.DatabaseInputProperty(
                name="opendata_pulse_db",
                description="Database for OpenData Pulse datasets"
            )
        )
        
        # Athena Workgroup
        self.athena_workgroup = athena.CfnWorkGroup(
            self, "OpenDataPulseWorkGroup",
            name="opendata-pulse-workgroup",
            description="Workgroup for OpenData Pulse queries",
            work_group_configuration=athena.CfnWorkGroup.WorkGroupConfigurationProperty(
                result_configuration=athena.CfnWorkGroup.ResultConfigurationProperty(
                    output_location=f"s3://{self.curated_bucket.bucket_name}/athena-results/"
                ),
                enforce_work_group_configuration=True
            )
        )
        
        # IAM Role for Glue operations
        self.glue_role = iam.Role(
            self, "GlueServiceRole",
            assumed_by=iam.ServicePrincipal("glue.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSGlueServiceRole")
            ]
        )
        
        # Grant Glue role access to S3 buckets
        self.raw_bucket.grant_read_write(self.glue_role)
        self.curated_bucket.grant_read_write(self.glue_role)
        
        # Output the bucket names for reference
        cdk.CfnOutput(
            self, "RawBucketName",
            value=self.raw_bucket.bucket_name,
            description="S3 bucket for raw NSW air quality data"
        )
        
        cdk.CfnOutput(
            self, "CuratedBucketName", 
            value=self.curated_bucket.bucket_name,
            description="S3 bucket for curated/processed data"
        )
        
        cdk.CfnOutput(
            self, "ExportsBucketName",
            value=self.exports_bucket.bucket_name,
            description="S3 bucket for data exports"
        )
        
        cdk.CfnOutput(
            self, "DynamoDBTableName",
            value=self.air_quality_table.table_name,
            description="DynamoDB table for air quality hot aggregates"
        ) 