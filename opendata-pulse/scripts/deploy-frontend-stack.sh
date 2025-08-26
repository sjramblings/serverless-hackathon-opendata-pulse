#!/bin/bash

# OpenData Pulse - FrontendStack Deployment Script
# This script deploys the React frontend with Amplify hosting and CloudFront

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
    
    # Check if ApiStack is deployed
    if ! aws cloudformation describe-stacks --stack-name OpenDataPulseApiStack > /dev/null 2>&1; then
        print_error "ApiStack not found. Please deploy ApiStack first: ./scripts/deploy-api-stack.sh"
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
    print_status "Validating FrontendStack..."
    
    if cdk synth OpenDataPulseFrontendStack > /dev/null 2>&1; then
        print_success "FrontendStack validation passed"
    else
        print_error "FrontendStack validation failed"
        exit 1
    fi
}

# Function to deploy the stack
deploy_stack() {
    print_status "Deploying OpenDataPulseFrontendStack..."
    
    # Deploy with progress monitoring
    cdk deploy OpenDataPulseFrontendStack --require-approval never
    
    if [ $? -eq 0 ]; then
        print_success "FrontendStack deployment completed successfully!"
    else
        print_error "FrontendStack deployment failed"
        exit 1
    fi
}

# Function to display stack outputs
show_outputs() {
    print_status "Retrieving stack outputs..."
    
    echo ""
    echo "=== FrontendStack Outputs ==="
    aws cloudformation describe-stacks \
        --stack-name OpenDataPulseFrontendStack \
        --query 'Stacks[0].Outputs[*].[OutputKey,OutputValue,Description]' \
        --output table
}

# Function to test frontend deployment
test_frontend_deployment() {
    print_status "Testing frontend deployment..."
    
    # Get CloudFront URL
    CLOUDFRONT_URL=$(aws cloudformation describe-stacks \
        --stack-name OpenDataPulseFrontendStack \
        --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontURL`].OutputValue' \
        --output text)
    
    # Get Amplify App URL
    AMPLIFY_URL=$(aws cloudformation describe-stacks \
        --stack-name OpenDataPulseFrontendStack \
        --query 'Stacks[0].Outputs[?OutputKey==`AmplifyAppURL`].OutputValue' \
        --output text)
    
    if [ ! -z "$CLOUDFRONT_URL" ]; then
        print_success "CloudFront URL: $CLOUDFRONT_URL"
        
        # Test if the site is accessible
        HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$CLOUDFRONT_URL" || echo "000")
        
        if [ "$HTTP_STATUS" = "200" ]; then
            print_success "Frontend is accessible via CloudFront"
        else
            print_warning "Frontend may still be deploying (HTTP $HTTP_STATUS)"
        fi
    fi
    
    if [ ! -z "$AMPLIFY_URL" ]; then
        print_success "Amplify App URL: $AMPLIFY_URL"
    fi
}

# Function to check Amplify app status
check_amplify_status() {
    print_status "Checking Amplify app status..."
    
    # Get Amplify App ID
    AMPLIFY_APP_ID=$(aws cloudformation describe-stacks \
        --stack-name OpenDataPulseFrontendStack \
        --query 'Stacks[0].Outputs[?OutputKey==`AmplifyAppId`].OutputValue' \
        --output text)
    
    if [ ! -z "$AMPLIFY_APP_ID" ]; then
        print_success "Amplify App ID: $AMPLIFY_APP_ID"
        
        # Get app details
        aws amplify get-app \
            --app-id "$AMPLIFY_APP_ID" \
            --query 'app.{Name:name,Status:status,DefaultDomain:defaultDomain}' \
            --output table
        
        # List branches
        aws amplify list-branches \
            --app-id "$AMPLIFY_APP_ID" \
            --query 'branches[*].[branchName,stage,displayName]' \
            --output table
    else
        print_warning "Could not retrieve Amplify App ID"
    fi
}

# Function to check CloudFront distribution
check_cloudfront_distribution() {
    print_status "Checking CloudFront distribution..."
    
    # Get CloudFront Distribution ID
    DISTRIBUTION_ID=$(aws cloudformation describe-stacks \
        --stack-name OpenDataPulseFrontendStack \
        --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontDistributionId`].OutputValue' \
        --output text)
    
    if [ ! -z "$DISTRIBUTION_ID" ]; then
        print_success "CloudFront Distribution ID: $DISTRIBUTION_ID"
        
        # Get distribution status
        aws cloudfront get-distribution \
            --id "$DISTRIBUTION_ID" \
            --query 'Distribution.{Status:Status,DomainName:DomainName,Enabled:DistributionConfig.Enabled}' \
            --output table
        
        # Check if distribution is deployed
        STATUS=$(aws cloudfront get-distribution \
            --id "$DISTRIBUTION_ID" \
            --query 'Distribution.Status' \
            --output text)
        
        if [ "$STATUS" = "Deployed" ]; then
            print_success "CloudFront distribution is fully deployed"
        else
            print_warning "CloudFront distribution is still deploying (Status: $STATUS)"
            print_status "This may take 10-15 minutes to complete"
        fi
    else
        print_warning "Could not retrieve CloudFront Distribution ID"
    fi
}

# Function to configure frontend environment
configure_frontend_environment() {
    print_status "Configuring frontend environment variables..."
    
    # Get API configuration from ApiStack
    GRAPHQL_ENDPOINT=$(aws cloudformation describe-stacks \
        --stack-name OpenDataPulseApiStack \
        --query 'Stacks[0].Outputs[?OutputKey==`GraphQLEndpoint`].OutputValue' \
        --output text)
    
    USER_POOL_ID=$(aws cloudformation describe-stacks \
        --stack-name OpenDataPulseApiStack \
        --query 'Stacks[0].Outputs[?OutputKey==`UserPoolId`].OutputValue' \
        --output text)
    
    USER_POOL_CLIENT_ID=$(aws cloudformation describe-stacks \
        --stack-name OpenDataPulseApiStack \
        --query 'Stacks[0].Outputs[?OutputKey==`UserPoolClientId`].OutputValue' \
        --output text)
    
    if [ ! -z "$GRAPHQL_ENDPOINT" ] && [ ! -z "$USER_POOL_ID" ] && [ ! -z "$USER_POOL_CLIENT_ID" ]; then
        print_success "Frontend configuration retrieved:"
        echo "GraphQL Endpoint: $GRAPHQL_ENDPOINT"
        echo "User Pool ID: $USER_POOL_ID"
        echo "User Pool Client ID: $USER_POOL_CLIENT_ID"
        
        # Create environment configuration file
        cat > frontend/.env.production << EOF
REACT_APP_GRAPHQL_ENDPOINT=$GRAPHQL_ENDPOINT
REACT_APP_USER_POOL_ID=$USER_POOL_ID
REACT_APP_USER_POOL_CLIENT_ID=$USER_POOL_CLIENT_ID
REACT_APP_AWS_REGION=ap-southeast-2
EOF
        
        print_success "Frontend environment configuration created"
    else
        print_warning "Could not retrieve complete API configuration"
    fi
}

# Function to trigger Amplify build
trigger_amplify_build() {
    print_status "Triggering Amplify build..."
    
    AMPLIFY_APP_ID=$(aws cloudformation describe-stacks \
        --stack-name OpenDataPulseFrontendStack \
        --query 'Stacks[0].Outputs[?OutputKey==`AmplifyAppId`].OutputValue' \
        --output text)
    
    if [ ! -z "$AMPLIFY_APP_ID" ]; then
        # Start a new build
        BUILD_ID=$(aws amplify start-job \
            --app-id "$AMPLIFY_APP_ID" \
            --branch-name "main" \
            --job-type RELEASE \
            --query 'jobSummary.jobId' \
            --output text)
        
        if [ ! -z "$BUILD_ID" ]; then
            print_success "Amplify build started: $BUILD_ID"
            print_status "Monitor build progress in AWS Console or wait for completion"
            
            # Wait for build completion (optional)
            read -p "Would you like to wait for build completion? (y/n): " -n 1 -r
            echo
            
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                print_status "Waiting for build completion..."
                
                while true; do
                    BUILD_STATUS=$(aws amplify get-job \
                        --app-id "$AMPLIFY_APP_ID" \
                        --branch-name "main" \
                        --job-id "$BUILD_ID" \
                        --query 'job.summary.status' \
                        --output text)
                    
                    if [ "$BUILD_STATUS" = "SUCCEED" ]; then
                        print_success "Amplify build completed successfully"
                        break
                    elif [ "$BUILD_STATUS" = "FAILED" ]; then
                        print_error "Amplify build failed"
                        break
                    else
                        print_status "Build status: $BUILD_STATUS"
                        sleep 30
                    fi
                done
            fi
        else
            print_warning "Could not start Amplify build"
        fi
    else
        print_warning "Could not retrieve Amplify App ID"
    fi
}

# Main execution
main() {
    echo "=========================================="
    echo "OpenData Pulse - FrontendStack Deployment"
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
    test_frontend_deployment
    check_amplify_status
    check_cloudfront_distribution
    configure_frontend_environment
    trigger_amplify_build
    
    echo ""
    print_success "FrontendStack deployment and setup completed!"
    echo ""
    echo "Next steps:"
    echo "1. Deploy LocationStack: cdk deploy OpenDataPulseLocationStack"
    echo "2. Test the complete application end-to-end"
    echo "3. Configure custom domain (optional)"
    echo "4. Set up monitoring for frontend performance"
    echo "5. Configure CI/CD pipeline for automatic deployments"
    echo ""
}

# Run main function
main "$@"