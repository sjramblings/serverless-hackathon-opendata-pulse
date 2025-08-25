"""
API Stack - AppSync GraphQL API and Cognito authentication
"""

import aws_cdk as cdk
from aws_cdk import (
    aws_appsync as appsync,
    aws_cognito as cognito,
    aws_iam as iam,
    aws_wafv2 as wafv2,
    aws_ec2 as ec2,
    Duration,
    RemovalPolicy
)
from constructs import Construct

class ApiStack(cdk.Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # Cognito User Pool with enhanced security
        self.user_pool = cognito.UserPool(
            self, "OpenDataPulseUserPool",
            user_pool_name="opendata-pulse-users",
            self_sign_up_enabled=True,
            sign_in_aliases=cognito.SignInAliases(email=True),
            standard_attributes=cognito.StandardAttributes(
                email=cognito.StandardAttribute(required=True, mutable=True),
                given_name=cognito.StandardAttribute(required=False, mutable=True),
                family_name=cognito.StandardAttribute(required=False, mutable=True),
                phone_number=cognito.StandardAttribute(required=False, mutable=True)
            ),
            custom_attributes={
                "region_preference": cognito.StringAttribute(mutable=True),
                "subscription_level": cognito.StringAttribute(mutable=True)
            },
            password_policy=cognito.PasswordPolicy(
                min_length=8,
                require_lowercase=True,
                require_uppercase=True,
                require_digits=True,
                require_symbols=True
            ),
            account_recovery=cognito.AccountRecovery.EMAIL_ONLY,
            user_verification=cognito.UserVerificationConfig(
                email_subject="Verify your email for OpenData Pulse",
                email_body="Thanks for signing up! Your verification code is {####}",
                email_style=cognito.VerificationEmailStyle.CODE
            ),
            mfa=cognito.Mfa.OPTIONAL,
            mfa_second_factor=cognito.MfaSecondFactor(
                sms=True,
                otp=True
            ),
            device_tracking=cognito.DeviceTracking(
                challenge_required_on_new_device=True,
                device_only_remembered_on_user_prompt=True
            ),
            removal_policy=RemovalPolicy.RETAIN
        )
        
        # App Client for web application
        self.app_client = self.user_pool.add_client(
            "OpenDataPulseAppClient",
            user_pool_client_name="opendata-pulse-web-client",
            generate_secret=False,  # No secret for public clients
            supported_identity_providers=[cognito.UserPoolClientIdentityProvider.COGNITO]
        )
        
        # Identity Pool for AWS resource access
        self.identity_pool = cognito.CfnIdentityPool(
            self, "OpenDataPulseIdentityPool",
            identity_pool_name="opendata-pulse-identity-pool",
            allow_unauthenticated_identities=False,
            cognito_identity_providers=[
                cognito.CfnIdentityPool.CognitoIdentityProviderProperty(
                    client_id=self.app_client.user_pool_client_id,
                    provider_name=self.user_pool.user_pool_provider_name
                )
            ]
        )
        
        # WAF Web ACL for API protection (simplified)
        self.web_acl = wafv2.CfnWebACL(
            self, "OpenDataPulseWebACL",
            default_action=wafv2.CfnWebACL.DefaultActionProperty(
                allow=wafv2.CfnWebACL.AllowActionProperty()
            ),
            scope="REGIONAL",
            visibility_config=wafv2.CfnWebACL.VisibilityConfigProperty(
                cloud_watch_metrics_enabled=True,
                metric_name="OpenDataPulseWebACLMetric",
                sampled_requests_enabled=True
            )
        )
        
        # AppSync API with WAF protection
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
            ),
            xray_enabled=True
        )
        
        # Associate WAF with AppSync API
        wafv2.CfnWebACLAssociation(
            self, "AppSyncWebACLAssociation",
            resource_arn=self.api.arn,
            web_acl_arn=self.web_acl.attr_arn
        )
        
        # IAM Role for authenticated users
        self.authenticated_role = iam.Role(
            self, "AuthenticatedUserRole",
            assumed_by=iam.FederatedPrincipal(
                "cognito-identity.amazonaws.com",
                conditions={
                    "StringEquals": {
                        "cognito-identity.amazonaws.com:aud": self.identity_pool.ref
                    },
                    "ForAnyValue:StringLike": {
                        "cognito-identity.amazonaws.com:amr": "authenticated"
                    }
                },
                assume_role_action="sts:AssumeRoleWithWebIdentity"
            ),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSAppSyncPushToCloudWatchLogs")
            ]
        )
        
        # IAM Role for unauthenticated users (if needed later)
        self.unauthenticated_role = iam.Role(
            self, "UnauthenticatedUserRole",
            assumed_by=iam.FederatedPrincipal(
                "cognito-identity.amazonaws.com",
                conditions={
                    "StringEquals": {
                        "cognito-identity.amazonaws.com:aud": self.identity_pool.ref
                    },
                    "ForAnyValue:StringLike": {
                        "cognito-identity.amazonaws.com:amr": "unauthenticated"
                    }
                },
                assume_role_action="sts:AssumeRoleWithWebIdentity"
            )
        )
        
        # Attach roles to identity pool
        cognito.CfnIdentityPoolRoleAttachment(
            self, "IdentityPoolRoleAttachment",
            identity_pool_id=self.identity_pool.ref,
            roles={
                "authenticated": self.authenticated_role.role_arn,
                "unauthenticated": self.unauthenticated_role.role_arn
            }
        )
        
        # CloudFormation outputs
        cdk.CfnOutput(
            self, "UserPoolId",
            value=self.user_pool.user_pool_id,
            description="Cognito User Pool ID"
        )
        
        cdk.CfnOutput(
            self, "UserPoolClientId",
            value=self.app_client.user_pool_client_id,
            description="Cognito User Pool Client ID"
        )
        
        cdk.CfnOutput(
            self, "IdentityPoolId",
            value=self.identity_pool.ref,
            description="Cognito Identity Pool ID"
        )
        
        cdk.CfnOutput(
            self, "GraphQLApiUrl",
            value=self.api.graphql_url,
            description="AppSync GraphQL API URL"
        )
        
        cdk.CfnOutput(
            self, "GraphQLApiId",
            value=self.api.api_id,
            description="AppSync GraphQL API ID"
        )
        
        cdk.CfnOutput(
            self, "WebACLId",
            value=self.web_acl.ref,
            description="WAF Web ACL ID"
        ) 