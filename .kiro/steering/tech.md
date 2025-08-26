# Technology Stack & Build System

## Core Technologies

### Infrastructure
- **AWS CDK v2+** with Python for Infrastructure as Code
- **Python 3.9+** for Lambda functions and CDK stacks
- **Node.js 18+** for frontend and MCP server
- **AWS Services**: S3, DynamoDB, Lambda, AppSync, Cognito, EventBridge, Athena, Glue

### Development Stack
- **Backend**: Python with AWS Lambda Powertools for observability
- **Frontend**: React with Apollo Client for GraphQL
- **API**: AppSync GraphQL with Cognito authentication
- **AI/ML**: Amazon Bedrock for natural language processing
- **Maps**: Amazon Location Service for geographic visualization

### Key Dependencies
- `aws-cdk-lib>=2.100.0` - CDK framework
- `boto3>=1.34.0` - AWS SDK for Python
- `aws-lambda-powertools` - Observability and best practices
- `requests>=2.31.0` - HTTP client for API calls
- `pandas>=2.0.0` - Data processing
- `pyarrow>=14.0.0` - Parquet file handling

## Build & Development Commands

### Environment Setup
```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
```

### CDK Operations
```bash
# Bootstrap CDK (first time only)
cdk bootstrap

# Synthesize CloudFormation templates
cdk synth

# Deploy all stacks
cdk deploy --all

# Deploy specific stack
cdk deploy OpenDataPulseDataStack

# View differences before deployment
cdk diff

# Watch for changes during development
cdk watch

# Destroy stacks (use with caution)
cdk destroy --all
```

### Testing & Quality
```bash
# Run unit tests
pytest

# Run with coverage
pytest --cov=infrastructure

# Code formatting
black infrastructure/
black lambda-functions/

# Linting
flake8 infrastructure/
flake8 lambda-functions/

# Type checking
mypy infrastructure/
```

### Deployment Scripts
- `scripts/deploy-data-stack.sh` - Deploy data infrastructure
- `scripts/deploy-compute-stack.sh` - Deploy Lambda functions
- `scripts/deploy-api-stack.sh` - Deploy API and authentication

### AWS Configuration
- Default region: `ap-southeast-2` (Sydney) for NSW data
- Account ID configured via CDK context
- IAM least privilege principles enforced
- All resources tagged with Project, Environment, ManagedBy

## Development Patterns

### Lambda Functions
- Use AWS Lambda Powertools for logging, tracing, and metrics
- Environment variables for configuration
- Dead letter queues for error handling
- CloudWatch log retention policies

### CDK Stacks
- Modular stack design (Data, Compute, API, Frontend, Location)
- Cross-stack dependencies properly defined
- Removal policies for data retention
- CloudFormation outputs for resource references

### Error Handling
- SNS notifications for operational alerts
- SQS dead letter queues for failed processing
- Comprehensive logging with structured data
- Health check functions for monitoring