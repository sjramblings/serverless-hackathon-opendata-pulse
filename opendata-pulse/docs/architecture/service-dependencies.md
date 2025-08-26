# Service Dependencies

*Detailed mapping of service interactions and dependencies within the OpenData Pulse system.*

## Cross-Stack Dependencies

### DataStack Dependencies
- **Provides**: S3 buckets, DynamoDB tables, Glue catalog, Athena workgroup
- **Consumed by**: ComputeStack (Lambda functions), APIStack (GraphQL resolvers)

### ComputeStack Dependencies
- **Depends on**: DataStack (storage resources)
- **Provides**: Lambda functions, EventBridge rules, SQS queues
- **Consumed by**: APIStack (health checks), External systems (scheduled execution)

### APIStack Dependencies
- **Depends on**: DataStack (data access), ComputeStack (health functions)
- **Provides**: GraphQL API, Cognito user pools, IAM roles
- **Consumed by**: FrontendStack (authentication), MCP Server (API access)

### FrontendStack Dependencies
- **Depends on**: APIStack (GraphQL endpoint, authentication)
- **Provides**: Amplify hosting, CloudFront distribution
- **Consumed by**: End users (web interface)

### LocationStack Dependencies
- **Depends on**: DataStack (geographic data)
- **Provides**: Location Service resources, map styles
- **Consumed by**: FrontendStack (map visualization)

## Resource Naming Conventions

All resources follow the pattern: `opendata-pulse-{resource-type}-{account-id}`

### Examples
- S3 Buckets: `opendata-pulse-raw-data-123456789012`
- DynamoDB Tables: `opendata-pulse-aggregates`
- Lambda Functions: `opendata-pulse-data-ingest`
- API Gateway: `opendata-pulse-graphql-api`

*Generated from CDK stack definitions and resource configurations*