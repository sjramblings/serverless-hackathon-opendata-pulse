#!/usr/bin/env python3
"""
OpenData Pulse - Gen-AI + MCP Edition
Main CDK application entry point
"""

import aws_cdk as cdk
from infrastructure.data_stack import DataStack
from infrastructure.compute_stack import ComputeStack
from infrastructure.api_stack import ApiStack
from infrastructure.frontend_stack import FrontendStack
from infrastructure.location_stack import LocationStack

app = cdk.App()

# Environment configuration
env = cdk.Environment(
    account=app.node.try_get_context('account'),
    region=app.node.try_get_context('region') or 'ap-southeast-2'  # Sydney region
)

# Stack definitions
data_stack = DataStack(app, "OpenDataPulseDataStack", env=env)
compute_stack = ComputeStack(app, "OpenDataPulseComputeStack", env=env)
api_stack = ApiStack(app, "OpenDataPulseApiStack", env=env)
frontend_stack = FrontendStack(app, "OpenDataPulseFrontendStack", env=env)
location_stack = LocationStack(app, "OpenDataPulseLocationStack", env=env)

# Add dependencies between stacks
compute_stack.add_dependency(data_stack)
api_stack.add_dependency(data_stack)
api_stack.add_dependency(compute_stack)
frontend_stack.add_dependency(api_stack)
location_stack.add_dependency(data_stack)

# Add tags to all stacks
for stack in [data_stack, compute_stack, api_stack, frontend_stack, location_stack]:
    cdk.Tags.of(stack).add("Project", "OpenDataPulse")
    cdk.Tags.of(stack).add("Environment", "Development")
    cdk.Tags.of(stack).add("ManagedBy", "CDK")

app.synth() 