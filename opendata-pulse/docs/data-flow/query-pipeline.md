# Query Pipeline

*Documentation for data access flow from storage through GraphQL API to frontend.*

## Overview

The query pipeline serves data from storage through GraphQL API to frontend applications and MCP clients with optimized performance for different access patterns.

## Query Flow Components

### GraphQL API (AppSync)
- **Service**: AWS AppSync
- **Authentication**: Cognito JWT tokens
- **Resolvers**: Direct DynamoDB and Athena integration
- **Caching**: Built-in response caching

### Data Sources
- **Hot Data**: DynamoDB for recent aggregates (sub-second response)
- **Historical Data**: Athena queries on S3 parquet files
- **Raw Data**: Direct S3 access for exports

## Query Flow Diagram

```mermaid
sequenceDiagram
    participant Client as Client App
    participant CF as CloudFront
    participant AppSync as AppSync API
    participant Auth as Cognito
    participant DDB as DynamoDB
    participant S3 as S3 Curated
    participant Athena as Athena
    
    Client->>CF: GraphQL request
    CF->>AppSync: Forward request
    AppSync->>Auth: Validate JWT token
    Auth-->>AppSync: Token valid
    
    alt Hot Data Query
        AppSync->>DDB: Query aggregates
        DDB-->>AppSync: Return results
    else Historical Data Query
        AppSync->>Athena: Execute query
        Athena->>S3: Scan parquet files
        S3-->>Athena: Return data
        Athena-->>AppSync: Query results
    end
    
    AppSync-->>CF: GraphQL response
    CF-->>Client: Cached response
    
    Note over DDB: Sub-second response for recent data
    Note over Athena: Complex analytics on historical data
```

*Content will be generated from GraphQL schema and resolver analysis*