#!/bin/bash

# OpenData Pulse - ApiStack Deployment Script
# This script deploys the GraphQL API and Cognito authentication infrastructure

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if AWS CLI is configured
check_aws_config() {
    print_status "Checking AWS configuration..."
    
    if ! aws sts get-caller-identity > /dev/null 2>&1; then
        print_error "AWS credentials not configured. Please run 'aws configure' first."
        exit 1
    fi
    
    ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    REGION=$(aws configure get region)
    
    print_success "AWS configured for account: $ACCOUNT_ID in region: $REGION"
}

# Function to check dependencies
check_dependencies() {
    print_status "Checking stack dependencies..."
    
    # Check if DataStack is deployed
    if ! aws cloudformation describe-stacks --stack-name OpenDataPulseDataStack > /dev/null 2>&1; then
        print_error "DataStack not found. Please deploy DataStack first: ./scripts/deploy-data-stack.sh"
        exit 1
    fi
    
    # Check if ComputeStack is deployed
    if ! aws cloudformation describe-stacks --stack-name OpenDataPulseComputeStack > /dev/null 2>&1; then
        print_error "ComputeStack not found. Please deploy ComputeStack first: ./scripts/deploy-compute-stack.sh"
        exit 1
    fi
    
    print_success "All dependencies satisfied"
}

# Function to check if CDK is bootstrapped
check_cdk_bootstrap() {
    print_status "Checking CDK bootstrap status..."
    
    if ! cdk list > /dev/null 2>&1; then
        print_warning "CDK not bootstrapped. Bootstrapping now..."
        cdk bootstrap
        print_success "CDK bootstrap completed"
    else
        print_success "CDK already bootstrapped"
    fi
}

# Function to validate stack before deployment
validate_stack() {
    print_status "Validating ApiStack..."
    
    if cdk synth OpenDataPulseApiStack > /dev/null 2>&1; then
        print_success "ApiStack validation passed"
    else
        print_error "ApiStack validation failed"
        exit 1
    fi
}

# Function to deploy the stack
deploy_stack() {
    print_status "Deploying OpenDataPulseApiStack..."
    
    # Deploy with progress monitoring
    cdk deploy OpenDataPulseApiStack --require-approval never
    
    if [ $? -eq 0 ]; then
        print_success "ApiStack deployment completed successfully!"
    else
        print_error "ApiStack deployment failed"
        exit 1
    fi
}

# Function to display stack outputs
show_outputs() {
    print_status "Retrieving stack outputs..."
    
    echo ""
    echo "=== ApiStack Outputs ==="
    aws cloudformation describe-stacks \
        --stack-name OpenDataPulseApiStack \
        --query 'Stacks[0].Outputs[*].[OutputKey,OutputValue,Description]' \
        --output table
}

# Function to test GraphQL API
test_graphql_api() {
    print_status "Testing GraphQL API..."
    
    # Get GraphQL endpoint
    GRAPHQL_ENDPOINT=$(aws cloudformation describe-stacks \
        --stack-name OpenDataPulseApiStack \
        --query 'Stacks[0].Outputs[?OutputKey==`GraphQLEndpoint`].OutputValue' \
        --output text)
    
    if [ ! -z "$GRAPHQL_ENDPOINT" ]; then
        print_success "GraphQL endpoint: $GRAPHQL_ENDPOINT"
        
        # Test introspection query (should work without authentication)
        INTROSPECTION_QUERY='{"query":"query IntrospectionQuery { __schema { queryType { name } } }"}'
        
        RESPONSE=$(curl -s -X POST \
            -H "Content-Type: application/json" \
            -d "$INTROSPECTION_QUERY" \
            "$GRAPHQL_ENDPOINT")
        
        if echo "$RESPONSE" | grep -q "queryType"; then
            print_success "GraphQL API is responding correctly"
        else
            print_warning "GraphQL API test failed or requires authentication"
            echo "Response: $RESPONSE"
        fi
    else
        print_warning "Could not retrieve GraphQL endpoint"
    fi
}

# Function to test Cognito User Pool
test_cognito_user_pool() {
    print_status "Testing Cognito User Pool..."
    
    # Get User Pool ID
    USER_POOL_ID=$(aws cloudformation describe-stacks \
        --stack-name OpenDataPulseApiStack \
        --query 'Stacks[0].Outputs[?OutputKey==`UserPoolId`].OutputValue' \
        --output text)
    
    # Get User Pool Client ID
    USER_POOL_CLIENT_ID=$(aws cloudformation describe-stacks \
        --stack-name OpenDataPulseApiStack \
        --query 'Stacks[0].Outputs[?OutputKey==`UserPoolClientId`].OutputValue' \
        --output text)
    
    if [ ! -z "$USER_POOL_ID" ]; then
        print_success "User Pool ID: $USER_POOL_ID"
        print_success "User Pool Client ID: $USER_POOL_CLIENT_ID"
        
        # Get User Pool details
        aws cognito-idp describe-user-pool \
            --user-pool-id "$USER_POOL_ID" \
            --query 'UserPool.{Name:Name,Status:Status,MfaConfiguration:MfaConfiguration}' \
            --output table
        
        # List User Pool clients
        aws cognito-idp list-user-pool-clients \
            --user-pool-id "$USER_POOL_ID" \
            --query 'UserPoolClients[*].[ClientName,ClientId]' \
            --output table
    else
        print_warning "Could not retrieve User Pool information"
    fi
}

# Function to check AppSync data sources
check_appsync_data_sources() {
    print_status "Checking AppSync data sources..."
    
    # Get GraphQL API ID
    API_ID=$(aws cloudformation describe-stacks \
        --stack-name OpenDataPulseApiStack \
        --query 'Stacks[0].Outputs[?OutputKey==`GraphQLApiId`].OutputValue' \
        --output text)
    
    if [ ! -z "$API_ID" ]; then
        print_success "GraphQL API ID: $API_ID"
        
        # List data sources
        aws appsync list-data-sources \
            --api-id "$API_ID" \
            --query 'dataSources[*].[name,type]' \
            --output table
        
        # List resolvers
        aws appsync list-types \
            --api-id "$API_ID" \
            --format SDL \
            --query 'types[?definition.kind==`OBJECT`].name' \
            --output table
    else
        print_warning "Could not retrieve GraphQL API ID"
    fi
}

# Function to check WAF configuration (if enabled)
check_waf_configuration() {
    print_status "Checking WAF configuration..."
    
    # Get WAF Web ACL ARN
    WAF_ARN=$(aws cloudformation describe-stacks \
        --stack-name OpenDataPulseApiStack \
        --query 'Stacks[0].Outputs[?OutputKey==`WAFWebACLArn`].OutputValue' \
        --output text 2>/dev/null)
    
    if [ ! -z "$WAF_ARN" ] && [ "$WAF_ARN" != "None" ]; then
        print_success "WAF Web ACL configured: $WAF_ARN"
        
        # Get WAF Web ACL details
        WAF_ID=$(echo "$WAF_ARN" | cut -d'/' -f3)
        aws wafv2 get-web-acl \
            --scope CLOUDFRONT \
            --id "$WAF_ID" \
            --name "OpenDataPulseWAF" \
            --query 'WebACL.{Name:Name,DefaultAction:DefaultAction.Allow}' \
            --output table 2>/dev/null || print_warning "WAF details not accessible"
    else
        print_status "WAF not configured (likely development environment)"
    fi
}

# Function to create test user (optional)
create_test_user() {
    print_status "Creating test user (optional)..."
    
    read -p "Would you like to create a test user account? (y/n): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        USER_POOL_ID=$(aws cloudformation describe-stacks \
            --stack-name OpenDataPulseApiStack \
            --query 'Stacks[0].Outputs[?OutputKey==`UserPoolId`].OutputValue' \
            --output text)
        
        if [ ! -z "$USER_POOL_ID" ]; then
            read -p "Enter email address for test user: " EMAIL_ADDRESS
            read -p "Enter username for test user: " USERNAME
            
            # Create user with temporary password
            TEMP_PASSWORD="TempPass123!"
            
            aws cognito-idp admin-create-user \
                --user-pool-id "$USER_POOL_ID" \
                --username "$USERNAME" \
                --user-attributes Name=email,Value="$EMAIL_ADDRESS" \
                --temporary-password "$TEMP_PASSWORD" \
                --message-action SUPPRESS
            
            if [ $? -eq 0 ]; then
                print_success "Test user created: $USERNAME"
                print_warning "Temporary password: $TEMP_PASSWORD"
                print_warning "User must change password on first login"
            else
                print_error "Failed to create test user"
            fi
        else
            print_warning "Could not retrieve User Pool ID"
        fi
    fi
}

# Function to test API authentication flow
test_authentication_flow() {
    print_status "Testing authentication flow..."
    
    USER_POOL_ID=$(aws cloudformation describe-stacks \
        --stack-name OpenDataPulseApiStack \
        --query 'Stacks[0].Outputs[?OutputKey==`UserPoolId`].OutputValue' \
        --output text)
    
    USER_POOL_CLIENT_ID=$(aws cloudformation describe-stacks \
        --stack-name OpenDataPulseApiStack \
        --query 'Stacks[0].Outputs[?OutputKey==`UserPoolClientId`].OutputValue' \
        --output text)
    
    if [ ! -z "$USER_POOL_ID" ] && [ ! -z "$USER_POOL_CLIENT_ID" ]; then
        print_success "Authentication configuration verified"
        echo ""
        echo "=== Authentication Details ==="
        echo "User Pool ID: $USER_POOL_ID"
        echo "User Pool Client ID: $USER_POOL_CLIENT_ID"
        echo ""
        echo "To test authentication:"
        echo "1. Use the Cognito Hosted UI or implement custom authentication"
        echo "2. Use the User Pool Client ID in your frontend application"
        echo "3. Include JWT tokens in GraphQL requests"
    else
        print_warning "Could not retrieve authentication configuration"
    fi
}

# Main execution
main() {
    echo "=========================================="
    echo "OpenData Pulse - ApiStack Deployment"
    echo "=========================================="
    echo ""
    
    # Check prerequisites
    check_aws_config
    check_dependencies
    check_cdk_bootstrap
    
    # Validate and deploy
    validate_stack
    deploy_stack
    
    # Post-deployment tasks
    show_outputs
    test_graphql_api
    test_cognito_user_pool
    check_appsync_data_sources
    check_waf_configuration
    create_test_user
    test_authentication_flow
    
    echo ""
    print_success "ApiStack deployment and setup completed!"
    echo ""
    echo "Next steps:"
    echo "1. Deploy FrontendStack: cdk deploy OpenDataPulseFrontendStack"
    echo "2. Deploy LocationStack: cdk deploy OpenDataPulseLocationStack"
    echo "3. Configure frontend with GraphQL endpoint and Cognito settings"
    echo "4. Test end-to-end authentication and API access"
    echo "5. Set up monitoring and alerting for API usage"
    echo ""
}

# Run main function
main "$@"