#!/bin/bash

# OpenData Pulse - DataStack Deployment Script
# This script deploys the core infrastructure stack for OpenData Pulse

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
    print_status "Validating DataStack..."
    
    if cdk synth OpenDataPulseDataStack > /dev/null 2>&1; then
        print_success "DataStack validation passed"
    else
        print_error "DataStack validation failed"
        exit 1
    fi
}

# Function to deploy the stack
deploy_stack() {
    print_status "Deploying OpenDataPulseDataStack..."
    
    # Deploy with progress monitoring
    cdk deploy OpenDataPulseDataStack --require-approval never
    
    if [ $? -eq 0 ]; then
        print_success "DataStack deployment completed successfully!"
    else
        print_error "DataStack deployment failed"
        exit 1
    fi
}

# Function to display stack outputs
show_outputs() {
    print_status "Retrieving stack outputs..."
    
    echo ""
    echo "=== DataStack Outputs ==="
    aws cloudformation describe-stacks \
        --stack-name OpenDataPulseDataStack \
        --query 'Stacks[0].Outputs[*].[OutputKey,OutputValue,Description]' \
        --output table
}

# Function to create S3 folder structure
create_s3_structure() {
    print_status "Creating S3 folder structure for NSW air quality data..."
    
    RAW_BUCKET=$(aws cloudformation describe-stacks \
        --stack-name OpenDataPulseDataStack \
        --query 'Stacks[0].Outputs[?OutputKey==`RawBucketName`].OutputValue' \
        --output text)
    
    if [ ! -z "$RAW_BUCKET" ]; then
        aws s3api put-object --bucket "$RAW_BUCKET" --key "nsw-air-quality/raw/"
        aws s3api put-object --bucket "$RAW_BUCKET" --key "nsw-air-quality/processed/"
        aws s3api put-object --bucket "$RAW_BUCKET" --key "nsw-air-quality/metadata/"
        print_success "S3 folder structure created in $RAW_BUCKET"
    else
        print_warning "Could not retrieve bucket name from stack outputs"
    fi
}

# Main execution
main() {
    echo "=========================================="
    echo "OpenData Pulse - DataStack Deployment"
    echo "=========================================="
    echo ""
    
    # Check prerequisites
    check_aws_config
    check_cdk_bootstrap
    
    # Validate and deploy
    validate_stack
    deploy_stack
    
    # Post-deployment tasks
    show_outputs
    create_s3_structure
    
    echo ""
    print_success "DataStack deployment and setup completed!"
    echo ""
    echo "Next steps:"
    echo "1. Deploy ComputeStack: ./scripts/deploy-compute-stack.sh"
    echo "2. Deploy ApiStack: ./scripts/deploy-api-stack.sh"
    echo "3. Configure NSW Air Quality API integration"
    echo ""
}

# Run main function
main "$@" 