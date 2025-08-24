"""
Frontend Stack - Amplify hosting for React application
"""

import aws_cdk as cdk
from aws_cdk import (
    aws_amplify as amplify,
    aws_iam as iam
)
from constructs import Construct

class FrontendStack(cdk.Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # Amplify App
        self.amplify_app = amplify.CfnApp(
            self, "OpenDataPulseApp",
            name="opendata-pulse-frontend",
            description="OpenData Pulse React frontend application"
        )
        
        # Amplify Branch (main)
        self.main_branch = amplify.CfnBranch(
            self, "MainBranch",
            app_id=self.amplify_app.attr_app_id,
            branch_name="main",
            description="Main branch for OpenData Pulse frontend"
        ) 