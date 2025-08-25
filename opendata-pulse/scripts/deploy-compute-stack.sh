#!/bin/bash

# OpenData Pulse - ComputeStack Deployment Script
# This script deploys the Lambda functions and EventBridge infrastructure

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
    print_status "Validating ComputeStack..."
    
    if cdk synth OpenDataPulseComputeStack > /dev/null 2>&1; then
        print_success "ComputeStack validation passed"
    else
        print_error "ComputeStack validation failed"
        exit 1
    fi
}

# Function to deploy the stack
deploy_stack() {
    print_status "Deploying OpenDataPulseComputeStack..."
    
    # Deploy with progress monitoring
    cdk deploy OpenDataPulseComputeStack --require-approval never
    
    if [ $? -eq 0 ]; then
        print_success "ComputeStack deployment completed successfully!"
    else
        print_error "ComputeStack deployment failed"
        exit 1
    fi
}

# Function to display stack outputs
show_outputs() {
    print_status "Retrieving stack outputs..."
    
    echo ""
    echo "=== ComputeStack Outputs ==="
    aws cloudformation describe-stacks \
        --stack-name OpenDataPulseComputeStack \
        --query 'Stacks[0].Outputs[*].[OutputKey,OutputValue,Description]' \
        --output table
}

# Function to test Lambda functions
test_lambda_functions() {
    print_status "Testing Lambda functions..."
    
    # Get function names from stack outputs
    INGEST_FUNCTION=$(aws cloudformation describe-stacks \
        --stack-name OpenDataPulseComputeStack \
        --query 'Stacks[0].Outputs[?OutputKey==`IngestFunctionName`].OutputValue' \
        --output text)
    
    ETL_FUNCTION=$(aws cloudformation describe-stacks \
        --stack-name OpenDataPulseComputeStack \
        --query 'Stacks[0].Outputs[?OutputKey==`ETLFunctionName`].OutputValue' \
        --output text)
    
    HEALTH_CHECK_FUNCTION=$(aws cloudformation describe-stacks \
        --stack-name OpenDataPulseComputeStack \
        --query 'Stacks[0].Outputs[?OutputKey==`HealthCheckFunctionName`].OutputValue' \
        --output text)
    
    if [ ! -z "$INGEST_FUNCTION" ]; then
        print_success "Ingest function created: $INGEST_FUNCTION"
        
        # Test ingest function
        aws lambda invoke \
            --function-name "$INGEST_FUNCTION" \
            --payload '{}' \
            /tmp/ingest_response.json
        
        if [ $? -eq 0 ]; then
            print_success "Ingest function test successful"
            cat /tmp/ingest_response.json
        else
            print_warning "Ingest function test failed"
        fi
    fi
    
    if [ ! -z "$ETL_FUNCTION" ]; then
        print_success "ETL function created: $ETL_FUNCTION"
    fi
    
    if [ ! -z "$HEALTH_CHECK_FUNCTION" ]; then
        print_success "Health check function created: $HEALTH_CHECK_FUNCTION"
        
        # Test health check function
        aws lambda invoke \
            --function-name "$HEALTH_CHECK_FUNCTION" \
            --payload '{}' \
            /tmp/health_check_response.json
        
        if [ $? -eq 0 ]; then
            print_success "Health check function test successful"
            cat /tmp/health_check_response.json
        else
            print_warning "Health check function test failed"
        fi
    fi
}

# Function to check EventBridge rules
check_eventbridge_rules() {
    print_status "Checking EventBridge rules..."
    
    # List rules
    aws events list-rules \
        --name-prefix "OpenDataPulse" \
        --query 'Rules[*].[Name,ScheduleExpression,State]' \
        --output table
}

# Function to check SNS topic
check_sns_topic() {
    print_status "Checking SNS notification topic..."
    
    TOPIC_ARN=$(aws cloudformation describe-stacks \
        --stack-name OpenDataPulseComputeStack \
        --query 'Stacks[0].Outputs[?OutputKey==`NotificationTopicArn`].OutputValue' \
        --output text)
    
    if [ ! -z "$TOPIC_ARN" ]; then
        print_success "SNS topic created: $TOPIC_ARN"
        
        # List subscriptions
        aws sns list-subscriptions-by-topic \
            --topic-arn "$TOPIC_ARN" \
            --query 'Subscriptions[*].[Protocol,Endpoint]' \
            --output table
    fi
}

# Function to check SQS DLQ
check_sqs_dlq() {
    print_status "Checking SQS Dead Letter Queue..."
    
    DLQ_URL=$(aws cloudformation describe-stacks \
        --stack-name OpenDataPulseComputeStack \
        --query 'Stacks[0].Outputs[?OutputKey==`DLQUrl`].OutputValue' \
        --output text)
    
    if [ ! -z "$DLQ_URL" ]; then
        print_success "SQS DLQ created: $DLQ_URL"
        
        # Get queue attributes
        aws sqs get-queue-attributes \
            --queue-url "$DLQ_URL" \
            --attribute-names All \
            --query 'Attributes.{ApproximateNumberOfMessages:ApproximateNumberOfMessages,ApproximateNumberOfMessagesNotVisible:ApproximateNumberOfMessagesNotVisible}' \
            --output table
    fi
}

# Function to create test subscription (optional)
create_test_subscription() {
    print_status "Creating test SNS subscription (optional)..."
    
    read -p "Would you like to create a test email subscription for notifications? (y/n): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        TOPIC_ARN=$(aws cloudformation describe-stacks \
            --stack-name OpenDataPulseComputeStack \
            --query 'Stacks[0].Outputs[?OutputKey==`NotificationTopicArn`].OutputValue' \
            --output text)
        
        if [ ! -z "$TOPIC_ARN" ]; then
            read -p "Enter email address for notifications: " EMAIL_ADDRESS
            
            aws sns subscribe \
                --topic-arn "$TOPIC_ARN" \
                --protocol email \
                --notification-endpoint "$EMAIL_ADDRESS"
            
            if [ $? -eq 0 ]; then
                print_success "Test subscription created for: $EMAIL_ADDRESS"
                print_warning "Check your email and confirm the subscription"
            else
                print_error "Failed to create test subscription"
            fi
        else
            print_warning "Could not retrieve SNS topic ARN"
        fi
    fi
}

# Main execution
main() {
    echo "=========================================="
    echo "OpenData Pulse - ComputeStack Deployment"
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
    test_lambda_functions
    check_eventbridge_rules
    check_sns_topic
    check_sqs_dlq
    create_test_subscription
    
    echo ""
    print_success "ComputeStack deployment and setup completed!"
    echo ""
    echo "Next steps:"
    echo "1. Deploy FrontendStack: ./scripts/deploy-frontend-stack.sh"
    echo "2. Configure NSW Air Quality API integration"
    echo "3. Test data ingestion pipeline"
    echo "4. Monitor Lambda function logs and metrics"
    echo ""
}

# Run main function
main "$@" 