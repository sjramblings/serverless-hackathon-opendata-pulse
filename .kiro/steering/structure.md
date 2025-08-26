# Project Structure & Organization

## Root Directory Layout

```
opendata-pulse/
├── app.py                  # Main CDK application entry point
├── cdk.json               # CDK configuration and context
├── requirements.txt       # Python dependencies for CDK
├── infrastructure/        # CDK stack definitions
├── lambda-functions/      # Lambda function source code
├── frontend/             # React application
├── mcp-server/           # MCP server implementation
├── docs/                 # Project documentation
├── scripts/              # Deployment and utility scripts
└── venv/                 # Python virtual environment
```

## Infrastructure Directory (`infrastructure/`)

Contains modular CDK stack definitions following single responsibility principle:

- `__init__.py` - Package initialization
- `data_stack.py` - S3, DynamoDB, Glue, Athena resources
- `compute_stack.py` - Lambda functions, EventBridge, SQS, SNS
- `api_stack.py` - AppSync GraphQL API, Cognito authentication
- `frontend_stack.py` - Amplify hosting, CloudFront distribution
- `location_stack.py` - Amazon Location Service resources
- `schema.graphql` - GraphQL schema definition

## Lambda Functions (`lambda-functions/`)

Organized by function purpose with shared layers:

```
lambda-functions/
├── ingest/               # Data ingestion from NSW API
│   └── index.py         # Main handler with Powertools
├── etl/                 # ETL processing and transformation
│   └── index.py         # Data processing logic
├── health-check/        # System health monitoring
│   └── index.py         # Health check handler
└── layers/              # Shared dependencies
    ├── common/          # Common utilities and dependencies
    │   └── requirements.txt
    └── powertools/      # AWS Lambda Powertools layer
        ├── python/      # Layer structure
        └── requirements.txt
```

## Frontend Directory (`frontend/`)

React application with modern tooling:
- Component-based architecture
- Apollo Client for GraphQL integration
- Amazon Location Service SDK for maps
- Responsive design for mobile/desktop

## MCP Server (`mcp-server/`)

Model Context Protocol server implementation:
- Exposes 5+ tools for data access
- Handles authentication and authorization
- Provides programmatic API access

## Documentation (`docs/`)

Technical documentation and references:
- `APISTACK_REFERENCE.md` - API documentation
- `COMPUTESTACK_REFERENCE.md` - Lambda function details
- `DATASTACK_REFERENCE.md` - Data architecture guide

## Scripts Directory (`scripts/`)

Deployment and utility scripts:
- `deploy-data-stack.sh` - Data infrastructure deployment
- `deploy-compute-stack.sh` - Lambda function deployment
- `deploy-api-stack.sh` - API stack deployment

## Naming Conventions

### CDK Stacks
- Pattern: `OpenDataPulse{Purpose}Stack`
- Examples: `OpenDataPulseDataStack`, `OpenDataPulseComputeStack`

### AWS Resources
- Prefix: `opendata-pulse-`
- Include account ID for global uniqueness (S3 buckets)
- Use kebab-case for resource names

### Lambda Functions
- Descriptive names: `DataIngestFunction`, `ETLFunction`
- Environment variables in UPPER_CASE
- Service names for Powertools: `opendata-pulse-{service}`

### S3 Structure
```
raw/
├── nsw-air-quality/
│   └── raw/YYYY/MM/DD/HH/  # Partitioned by date/hour
curated/
├── nsw-air-quality/
│   └── parquet/YYYY/MM/DD/ # Processed parquet files
exports/
└── temp/                   # Temporary export files (7-day TTL)
```

### DynamoDB Schema
- Primary Key: `PK` (partition key), `SK` (sort key)
- GSI: Geographic queries with `SUBURB` and `TIMESTAMP`
- TTL attribute for automatic cleanup

## Development Workflow

1. **Infrastructure Changes**: Modify CDK stacks in `infrastructure/`
2. **Lambda Development**: Update function code in `lambda-functions/`
3. **Frontend Changes**: React components in `frontend/`
4. **Testing**: Use pytest for Python, Jest for JavaScript
5. **Deployment**: Use CDK commands or deployment scripts

## File Organization Principles

- **Separation of Concerns**: Each stack handles specific AWS services
- **Dependency Management**: Clear stack dependencies defined in `app.py`
- **Environment Isolation**: Use CDK context for environment-specific config
- **Resource Tagging**: Consistent tagging across all resources
- **Documentation**: Keep docs close to implementation code