"""
API Stack - AppSync GraphQL API and Cognito authentication
"""

import aws_cdk as cdk
from aws_cdk import (
    aws_appsync as appsync,
    aws_cognito as cognito,
    aws_iam as iam
)
from constructs import Construct

class ApiStack(cdk.Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # Cognito User Pool
        self.user_pool = cognito.UserPool(
            self, "OpenDataPulseUserPool",
            user_pool_name="opendata-pulse-users",
            self_sign_up_enabled=True,
            sign_in_aliases=cognito.SignInAliases(email=True),
            standard_attributes=cognito.StandardAttributes(
                email=cognito.StandardAttribute(required=True, mutable=True)
            ),
            password_policy=cognito.PasswordPolicy(
                min_length=8,
                require_lowercase=True,
                require_uppercase=True,
                require_digits=True,
                require_symbols=True
            )
        )
        
        # App Client
        self.app_client = self.user_pool.add_client(
            "OpenDataPulseAppClient",
            generate_secret=True,
            user_pool_client_name="opendata-pulse-client"
        )
        
        # AppSync API
        self.api = appsync.GraphqlApi(
            self, "OpenDataPulseAPI",
            name="opendata-pulse-api",
            schema=appsync.SchemaFile.from_asset("infrastructure/schema.graphql"),
            authorization_config=appsync.AuthorizationConfig(
                default_authorization=appsync.AuthorizationMode(
                    authorization_type=appsync.AuthorizationType.USER_POOL,
                    user_pool_config=appsync.UserPoolConfig(
                        user_pool=self.user_pool
                    )
                )
            )
        ) 