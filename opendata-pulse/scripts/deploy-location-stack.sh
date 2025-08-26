#!/bin/bash

# OpenData Pulse - LocationStack Deployment Script
# This script deploys Amazon Location Service resources for geographic visualization

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
    print_status "Validating LocationStack..."
    
    if cdk synth OpenDataPulseLocationStack > /dev/null 2>&1; then
        print_success "LocationStack validation passed"
    else
        print_error "LocationStack validation failed"
        exit 1
    fi
}

# Function to deploy the stack
deploy_stack() {
    print_status "Deploying OpenDataPulseLocationStack..."
    
    # Deploy with progress monitoring
    cdk deploy OpenDataPulseLocationStack --require-approval never
    
    if [ $? -eq 0 ]; then
        print_success "LocationStack deployment completed successfully!"
    else
        print_error "LocationStack deployment failed"
        exit 1
    fi
}

# Function to display stack outputs
show_outputs() {
    print_status "Retrieving stack outputs..."
    
    echo ""
    echo "=== LocationStack Outputs ==="
    aws cloudformation describe-stacks \
        --stack-name OpenDataPulseLocationStack \
        --query 'Stacks[0].Outputs[*].[OutputKey,OutputValue,Description]' \
        --output table
}

# Function to test Location Service resources
test_location_services() {
    print_status "Testing Location Service resources..."
    
    # Get Map resource name
    MAP_NAME=$(aws cloudformation describe-stacks \
        --stack-name OpenDataPulseLocationStack \
        --query 'Stacks[0].Outputs[?OutputKey==`MapName`].OutputValue' \
        --output text)
    
    # Get Place Index name
    PLACE_INDEX_NAME=$(aws cloudformation describe-stacks \
        --stack-name OpenDataPulseLocationStack \
        --query 'Stacks[0].Outputs[?OutputKey==`PlaceIndexName`].OutputValue' \
        --output text)
    
    if [ ! -z "$MAP_NAME" ]; then
        print_success "Map resource created: $MAP_NAME"
        
        # Get map details
        aws location describe-map \
            --map-name "$MAP_NAME" \
            --query 'MapName,DataSource,Configuration' \
            --output table
    else
        print_warning "Could not retrieve Map resource name"
    fi
    
    if [ ! -z "$PLACE_INDEX_NAME" ]; then
        print_success "Place Index created: $PLACE_INDEX_NAME"
        
        # Get place index details
        aws location describe-place-index \
            --index-name "$PLACE_INDEX_NAME" \
            --query 'IndexName,DataSource,DataSourceConfiguration' \
            --output table
    else
        print_warning "Could not retrieve Place Index name"
    fi
}

# Function to test geocoding functionality
test_geocoding() {
    print_status "Testing geocoding functionality..."
    
    PLACE_INDEX_NAME=$(aws cloudformation describe-stacks \
        --stack-name OpenDataPulseLocationStack \
        --query 'Stacks[0].Outputs[?OutputKey==`PlaceIndexName`].OutputValue' \
        --output text)
    
    if [ ! -z "$PLACE_INDEX_NAME" ]; then
        print_status "Testing geocoding with Sydney, NSW..."
        
        # Test geocoding for Sydney
        GEOCODE_RESULT=$(aws location search-place-index-for-text \
            --index-name "$PLACE_INDEX_NAME" \
            --text "Sydney, NSW, Australia" \
            --max-results 1 \
            --query 'Results[0].Place.{Label:Label,Geometry:Geometry}' \
            --output json)
        
        if [ ! -z "$GEOCODE_RESULT" ] && [ "$GEOCODE_RESULT" != "null" ]; then
            print_success "Geocoding test successful:"
            echo "$GEOCODE_RESULT" | jq '.'
        else
            print_warning "Geocoding test failed or returned no results"
        fi
        
        # Test reverse geocoding for Sydney coordinates
        print_status "Testing reverse geocoding for Sydney coordinates..."
        
        REVERSE_GEOCODE_RESULT=$(aws location search-place-index-for-position \
            --index-name "$PLACE_INDEX_NAME" \
            --position 151.2093 -33.8688 \
            --max-results 1 \
            --query 'Results[0].Place.{Label:Label,AddressNumber:AddressNumber,Street:Street,Municipality:Municipality}' \
            --output json)
        
        if [ ! -z "$REVERSE_GEOCODE_RESULT" ] && [ "$REVERSE_GEOCODE_RESULT" != "null" ]; then
            print_success "Reverse geocoding test successful:"
            echo "$REVERSE_GEOCODE_RESULT" | jq '.'
        else
            print_warning "Reverse geocoding test failed or returned no results"
        fi
    else
        print_warning "Could not test geocoding - Place Index name not found"
    fi
}

# Function to test map tile access
test_map_tiles() {
    print_status "Testing map tile access..."
    
    MAP_NAME=$(aws cloudformation describe-stacks \
        --stack-name OpenDataPulseLocationStack \
        --query 'Stacks[0].Outputs[?OutputKey==`MapName`].OutputValue' \
        --output text)
    
    if [ ! -z "$MAP_NAME" ]; then
        print_status "Map tiles are available for: $MAP_NAME"
        print_status "Map tiles can be accessed via AWS SDK or REST API with proper authentication"
        
        # Get map configuration
        aws location describe-map \
            --map-name "$MAP_NAME" \
            --query 'Configuration.Style' \
            --output text
        
        print_success "Map configuration verified"
    else
        print_warning "Could not test map tiles - Map name not found"
    fi
}

# Function to create sample geographic data
create_sample_data() {
    print_status "Creating sample geographic data..."
    
    # Get DynamoDB table name from DataStack
    TABLE_NAME=$(aws cloudformation describe-stacks \
        --stack-name OpenDataPulseDataStack \
        --query 'Stacks[0].Outputs[?OutputKey==`HotAggregatesTableName`].OutputValue' \
        --output text)
    
    if [ ! -z "$TABLE_NAME" ]; then
        print_status "Adding sample NSW air quality stations with coordinates..."
        
        # Sample air quality monitoring stations in NSW
        declare -a stations=(
            "Sydney CBD:-33.8688:151.2093"
            "Parramatta:-33.8150:151.0000"
            "Newcastle:-32.9267:151.7789"
            "Wollongong:-34.4278:150.8931"
            "Albury:-36.0737:146.9135"
        )
        
        for station in "${stations[@]}"; do
            IFS=':' read -r name lat lon <<< "$station"
            
            aws dynamodb put-item \
                --table-name "$TABLE_NAME" \
                --item "{
                    \"PK\": {\"S\": \"STATION#${name// /_}\"},
                    \"SK\": {\"S\": \"METADATA\"},
                    \"station_name\": {\"S\": \"$name\"},
                    \"latitude\": {\"N\": \"$lat\"},
                    \"longitude\": {\"N\": \"$lon\"},
                    \"region\": {\"S\": \"NSW\"},
                    \"status\": {\"S\": \"active\"},
                    \"last_updated\": {\"S\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}
                }" > /dev/null
            
            if [ $? -eq 0 ]; then
                print_success "Added station: $name ($lat, $lon)"
            else
                print_warning "Failed to add station: $name"
            fi
        done
    else
        print_warning "Could not retrieve DynamoDB table name for sample data"
    fi
}

# Function to verify Location Service IAM permissions
verify_iam_permissions() {
    print_status "Verifying Location Service IAM permissions..."
    
    # Check if we can list maps
    if aws location list-maps > /dev/null 2>&1; then
        print_success "Location Service list permissions verified"
    else
        print_warning "Location Service list permissions may be insufficient"
    fi
    
    # Check if we can list place indexes
    if aws location list-place-indexes > /dev/null 2>&1; then
        print_success "Place Index list permissions verified"
    else
        print_warning "Place Index list permissions may be insufficient"
    fi
}

# Function to display usage examples
show_usage_examples() {
    print_status "Location Service usage examples..."
    
    MAP_NAME=$(aws cloudformation describe-stacks \
        --stack-name OpenDataPulseLocationStack \
        --query 'Stacks[0].Outputs[?OutputKey==`MapName`].OutputValue' \
        --output text)
    
    PLACE_INDEX_NAME=$(aws cloudformation describe-stacks \
        --stack-name OpenDataPulseLocationStack \
        --query 'Stacks[0].Outputs[?OutputKey==`PlaceIndexName`].OutputValue' \
        --output text)
    
    echo ""
    echo "=== Usage Examples ==="
    echo ""
    echo "1. Geocoding (Address to Coordinates):"
    echo "   aws location search-place-index-for-text \\"
    echo "     --index-name \"$PLACE_INDEX_NAME\" \\"
    echo "     --text \"George Street, Sydney, NSW\" \\"
    echo "     --max-results 5"
    echo ""
    echo "2. Reverse Geocoding (Coordinates to Address):"
    echo "   aws location search-place-index-for-position \\"
    echo "     --index-name \"$PLACE_INDEX_NAME\" \\"
    echo "     --position 151.2093 -33.8688 \\"
    echo "     --max-results 1"
    echo ""
    echo "3. Map Tiles (via SDK):"
    echo "   Use AWS SDK with map name: $MAP_NAME"
    echo "   Zoom levels: 0-19"
    echo "   Tile format: PNG"
    echo ""
    echo "4. Frontend Integration:"
    echo "   - Use AWS Amplify Geo for React components"
    echo "   - Configure with map name and place index"
    echo "   - Implement proper authentication"
}

# Main execution
main() {
    echo "=========================================="
    echo "OpenData Pulse - LocationStack Deployment"
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
    test_location_services
    test_geocoding
    test_map_tiles
    create_sample_data
    verify_iam_permissions
    show_usage_examples
    
    echo ""
    print_success "LocationStack deployment and setup completed!"
    echo ""
    echo "Next steps:"
    echo "1. Integrate Location Service with frontend application"
    echo "2. Configure map styling and customization"
    echo "3. Test geographic queries with real air quality data"
    echo "4. Set up monitoring for Location Service usage"
    echo "5. Implement location-based alerts and notifications"
    echo ""
}

# Run main function
main "$@"