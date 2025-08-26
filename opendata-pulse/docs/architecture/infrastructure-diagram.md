# Infrastructure Diagram

*Visual representation of the OpenData Pulse infrastructure and service relationships.*

## High-Level Architecture

```mermaid
graph TB
    subgraph "External"
        NSW[NSW Government APIs]
        Users[End Users]
        Devs[Developers/MCP Clients]
    end
    
    subgraph "AWS Infrastructure"
        subgraph "Data Layer"
            S3Raw[S3 Raw Data]
            S3Curated[S3 Curated Data]
            DDB[DynamoDB Hot Aggregates]
            Athena[Athena Query Engine]
        end
        
        subgraph "Compute Layer"
            IngestLambda[Data Ingestion Lambda]
            ETLLambda[ETL Processing Lambda]
            HealthLambda[Health Check Lambda]
        end
        
        subgraph "API Layer"
            AppSync[AppSync GraphQL API]
            Cognito[Cognito Authentication]
            MCPServer[MCP Server]
        end
        
        subgraph "Frontend Layer"
            Amplify[Amplify Hosting]
            CloudFront[CloudFront CDN]
            LocationService[Amazon Location Service]
        end
    end
    
    NSW --> IngestLambda
    IngestLambda --> S3Raw
    S3Raw --> ETLLambda
    ETLLambda --> S3Curated
    ETLLambda --> DDB
    
    AppSync --> DDB
    AppSync --> S3Curated
    AppSync --> Athena
    
    Users --> CloudFront
    CloudFront --> Amplify
    Amplify --> AppSync
    Amplify --> LocationService
    
    Devs --> MCPServer
    MCPServer --> AppSync
    
    Cognito --> AppSync
```

## Stack Dependencies

```mermaid
graph LR
    DataStack --> ComputeStack
    DataStack --> APIStack
    APIStack --> FrontendStack
    DataStack --> LocationStack
    ComputeStack --> APIStack
```

*Diagrams generated automatically from CDK stack analysis*