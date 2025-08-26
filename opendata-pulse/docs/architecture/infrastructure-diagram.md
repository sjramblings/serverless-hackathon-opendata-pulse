# Infrastructure Diagrams

*Visual representation of the OpenData Pulse infrastructure, service relationships, and data flow patterns.*

**Last Updated:** 2025-08-26 23:13:03  
**Generated from:** CDK stack definitions and infrastructure analysis

## High-Level Architecture

```mermaid
graph TB
    subgraph "External Systems"
        NSW[NSW Government APIs<br/>Air Quality Data]
        Users[Citizens & Analysts<br/>Web Interface]
        Devs[Developers<br/>MCP Clients]
        AI[AI Applications<br/>Bedrock Integration]
    end
    
    subgraph "AWS Cloud - ap-southeast-2"
        subgraph "Data Layer"
            S3Raw[S3 Raw Data Bucket<br/>Partitioned by Date/Hour]
            S3Curated[S3 Curated Data Bucket<br/>Parquet Format]
            S3Exports[S3 Exports Bucket<br/>7-day TTL]
            DDB[DynamoDB Table<br/>Hot Aggregates & GSI]
            Glue[Glue Data Catalog<br/>Schema Registry]
            Athena[Athena Workgroup<br/>SQL Analytics]
        end
        
        subgraph "Compute Layer"
            EventBridge[EventBridge Rules<br/>Hourly Scheduling]
            IngestLambda[Ingest Lambda<br/>NSW API Client]
            ETLLambda[ETL Lambda<br/>Data Transformation]
            HealthLambda[Health Check Lambda<br/>System Monitoring]
            SQS[SQS Dead Letter Queue<br/>Error Handling]
            SNS[SNS Notifications<br/>Alerts & Status]
        end
        
        subgraph "API Layer"
            WAF[AWS WAF<br/>API Protection]
            AppSync[AppSync GraphQL API<br/>Unified Data Access]
            Cognito[Cognito User Pool<br/>Authentication & MFA]
            CognitoIdentity[Cognito Identity Pool<br/>AWS Resource Access]
        end
        
        subgraph "Frontend Layer"
            Amplify[Amplify Hosting<br/>React Application]
            LocationService[Location Service<br/>Maps & Geocoding]
            LocationMap[Interactive Maps<br/>Air Quality Visualization]
            LocationIndex[Place Index<br/>NSW Geocoding]
        end
    end
    
    %% Data Flow
    NSW -->|Hourly Fetch| IngestLambda
    EventBridge -->|Trigger| IngestLambda
    EventBridge -->|Monitor| HealthLambda
    
    IngestLambda -->|Store Raw| S3Raw
    S3Raw -->|Process| ETLLambda
    ETLLambda -->|Store Curated| S3Curated
    ETLLambda -->|Hot Aggregates| DDB
    ETLLambda -->|Notifications| SNS
    
    S3Curated -->|Catalog| Glue
    Glue -->|Query| Athena
    
    %% API Access
    WAF -->|Protect| AppSync
    Cognito -->|Authenticate| AppSync
    CognitoIdentity -->|Authorize| AppSync
    
    AppSync -->|Read| DDB
    AppSync -->|Query| Athena
    AppSync -->|Export| S3Exports
    
    %% User Interfaces
    Users -->|Access| Amplify
    Amplify -->|API Calls| AppSync
    Amplify -->|Maps| LocationService
    LocationService -->|Render| LocationMap
    LocationService -->|Geocode| LocationIndex
    
    Devs -->|MCP Tools| AppSync
    AI -->|Bedrock NLP| AppSync
    
    %% Error Handling
    IngestLambda -.->|Failures| SQS
    ETLLambda -.->|Failures| SQS
    SNS -.->|Alerts| Users
```

## Stack Architecture

```mermaid
graph TB
    subgraph "OpenData Pulse CDK Stacks"
        
        subgraph "LocationStack"
            Location_Purpose["Geographic and location services"]
            Location_LocationService[Location Service<br/>2 resources]
        
        subgraph "ComputeStack"
            Compute_Purpose["Compute and processing services"]
            Compute_Lambda[Lambda<br/>5 resources]
            Compute_SQS[SQS<br/>1 resources]
            Compute_SNS[SNS<br/>1 resources]
            Compute_IAM[IAM<br/>1 resources]
            Compute_EventBridge[EventBridge<br/>2 resources]
        
        subgraph "DataStack"
            Data_Purpose["Data storage and management services"]
            Data_S3[S3<br/>3 resources]
            Data_DynamoDB[DynamoDB<br/>1 resources]
            Data_Glue[Glue<br/>1 resources]
            Data_Athena[Athena<br/>1 resources]
            Data_IAM[IAM<br/>1 resources]
        
        subgraph "ApiStack"
            Api_Purpose["API and authentication services"]
            Api_Cognito[Cognito<br/>2 resources]
            Api_WAF[WAF<br/>1 resources]
            Api_AppSync[AppSync<br/>1 resources]
            Api_IAM[IAM<br/>2 resources]
        
        subgraph "FrontendStack"
            Frontend_Purpose["Frontend hosting and distribution"]
            Frontend_Amplify[Amplify<br/>2 resources]
        end
    end
    
    %% Stack Dependencies
    Data_Purpose --> Compute_Purpose
    Data_Purpose --> Api_Purpose
    Compute_Purpose --> Api_Purpose
    Api_Purpose --> Frontend_Purpose
    Data_Purpose --> Location_Purpose
```

## Service Relationships

```mermaid
graph LR
    subgraph "AWS Services Interaction Map"
        LocationService[Location Service<br/>2 resources]
        Lambda[Lambda<br/>5 resources]
        SQS[SQS<br/>1 resources]
        SNS[SNS<br/>1 resources]
        IAM[IAM<br/>4 resources]
        EventBridge[EventBridge<br/>2 resources]
        S3[S3<br/>3 resources]
        DynamoDB[DynamoDB<br/>1 resources]
        Glue[Glue<br/>1 resources]
        Athena[Athena<br/>1 resources]
        Cognito[Cognito<br/>2 resources]
        WAF[WAF<br/>1 resources]
        AppSync[AppSync<br/>1 resources]
        Amplify[Amplify<br/>2 resources]
    end

    %% Service Relationships
    Lambda -->|stores_in| S3
    Lambda -->|stores_in| DynamoDB
    EventBridge -->|triggers| Lambda
    AppSync -->|authenticates_with| Cognito
    S3 -->|processed_by| Glue
    S3 -->|queried_by| Athena
```

## Data Flow Architecture

```mermaid
flowchart TD
    subgraph "Data Sources"
        NSWAPI[NSW Air Quality API<br/>data.airquality.nsw.gov.au]
    end
    
    subgraph "Ingestion Layer"
        Schedule[EventBridge Rule<br/>Hourly Trigger]
        IngestFunc[Ingest Lambda Function<br/>NSW API Client]
        DLQ[SQS Dead Letter Queue<br/>Failed Processing]
    end
    
    subgraph "Raw Storage"
        S3Raw[S3 Raw Data Bucket<br/>JSON Format<br/>Partitioned: YYYY/MM/DD/HH]
    end
    
    subgraph "Processing Layer"
        ETLFunc[ETL Lambda Function<br/>Data Transformation]
        Powertools[Lambda Powertools<br/>Logging & Metrics]
    end
    
    subgraph "Curated Storage"
        S3Curated[S3 Curated Data Bucket<br/>Parquet Format<br/>Optimized for Analytics]
        DynamoDB[DynamoDB Table<br/>Hot Aggregates<br/>PK: Location, SK: Timestamp]
        GSI[Global Secondary Index<br/>SUBURB + TIMESTAMP<br/>Geographic Queries]
    end
    
    subgraph "Data Catalog"
        GlueDB[Glue Database<br/>opendata_pulse_db<br/>Schema Registry]
        AthenaTables[Athena Tables<br/>SQL Query Interface]
    end
    
    subgraph "Query Layer"
        AppSyncAPI[AppSync GraphQL API<br/>Unified Data Access]
        Resolvers[GraphQL Resolvers<br/>DynamoDB & Athena]
    end
    
    subgraph "Analytics & Export"
        AthenaWorkgroup[Athena Workgroup<br/>Ad-hoc SQL Queries]
        S3Exports[S3 Exports Bucket<br/>Query Results<br/>7-day TTL]
    end
    
    subgraph "Presentation Layer"
        ReactApp[React Frontend<br/>Apollo GraphQL Client]
        LocationMaps[Amazon Location Service<br/>Interactive Maps]
        MCPTools[MCP Server Tools<br/>Programmatic Access]
    end
    
    %% Data Flow
    NSWAPI -->|HTTP GET| IngestFunc
    Schedule -->|Trigger| IngestFunc
    IngestFunc -->|Store JSON| S3Raw
    IngestFunc -.->|Failures| DLQ
    
    S3Raw -->|Trigger| ETLFunc
    ETLFunc -->|Transform & Store| S3Curated
    ETLFunc -->|Hot Aggregates| DynamoDB
    ETLFunc -->|Metrics| Powertools
    DynamoDB -->|Index| GSI
    
    S3Curated -->|Register Schema| GlueDB
    GlueDB -->|Create Tables| AthenaTables
    
    AppSyncAPI -->|Real-time Queries| DynamoDB
    AppSyncAPI -->|Historical Queries| AthenaTables
    AppSyncAPI -->|Complex Analytics| AthenaWorkgroup
    AthenaWorkgroup -->|Results| S3Exports
    
    ReactApp -->|GraphQL Queries| AppSyncAPI
    ReactApp -->|Map Visualization| LocationMaps
    MCPTools -->|API Access| AppSyncAPI
    
    %% Error Handling
    ETLFunc -.->|Processing Errors| DLQ
    DLQ -.->|Alerts| SNSNotifications[SNS Notifications]
```

## Deployment Dependencies

```mermaid
graph TD
    subgraph "Deployment Order & Dependencies"
        subgraph "Phase 1: Foundation"
            DS[DataStack<br/>S3, DynamoDB, Glue, Athena<br/>🟢 No Dependencies]
        end
        
        subgraph "Phase 2: Processing"
            CS[ComputeStack<br/>Lambda, EventBridge, SQS, SNS<br/>🟡 Depends on DataStack]
            LS[LocationStack<br/>Location Service, Maps<br/>🟡 Depends on DataStack]
        end
        
        subgraph "Phase 3: API"
            AS[APIStack<br/>AppSync, Cognito, WAF<br/>🟠 Depends on Data + Compute]
        end
        
        subgraph "Phase 4: Frontend"
            FS[FrontendStack<br/>Amplify, CloudFront<br/>🔴 Depends on API]
        end
    end
    
    %% Dependencies
    DS --> CS
    DS --> LS
    DS --> AS
    CS --> AS
    AS --> FS
    
    %% Deployment Commands
    subgraph "CDK Deployment Commands"
        CMD1[cdk deploy OpenDataPulseDataStack]
        CMD2[cdk deploy OpenDataPulseComputeStack<br/>cdk deploy OpenDataPulseLocationStack]
        CMD3[cdk deploy OpenDataPulseApiStack]
        CMD4[cdk deploy OpenDataPulseFrontendStack]
    end
    
    CMD1 --> CMD2
    CMD2 --> CMD3
    CMD3 --> CMD4
```

### Deployment Strategy

**Recommended Deployment Order:** DataStack → LocationStack → ComputeStack → ApiStack → FrontendStack

**Parallel Deployment Opportunities:**
- ComputeStack and LocationStack can be deployed in parallel after DataStack
- Individual resources within stacks deploy in parallel where possible
- Stack updates can be performed independently once dependencies are satisfied

**Rollback Strategy:**
- Stacks can be rolled back in reverse dependency order
- DataStack rollback requires careful consideration due to data retention policies
- Lambda functions support blue/green deployments for zero-downtime updates

## Security Architecture

```mermaid
graph TB
    subgraph "Security Architecture"
        subgraph "External Access"
            Internet[Internet Users]
            MCPClients[MCP Clients]
        end
        
        subgraph "Edge Security"
            WAF[AWS WAF<br/>Web Application Firewall<br/>Rate Limiting & Protection]
            CloudFront[CloudFront CDN<br/>DDoS Protection<br/>SSL/TLS Termination]
        end
        
        subgraph "Authentication Layer"
            CognitoUserPool[Cognito User Pool<br/>User Authentication<br/>MFA Support]
            CognitoIdentityPool[Cognito Identity Pool<br/>AWS Resource Access<br/>Temporary Credentials]
        end
        
        subgraph "Authorization Layer"
            AppSyncAuth[AppSync Authorization<br/>User Pool Integration<br/>Field-level Security]
            IAMRoles[IAM Roles<br/>Service-to-Service Access<br/>Least Privilege]
        end
        
        subgraph "Data Protection"
            S3Encryption[S3 Server-Side Encryption<br/>AES-256<br/>Bucket Policies]
            DDBEncryption[DynamoDB Encryption<br/>At Rest & In Transit<br/>AWS Managed Keys]
            LambdaEnvVars[Lambda Environment Variables<br/>Encrypted at Rest<br/>KMS Integration]
        end
        
        subgraph "Network Security"
            VPCEndpoints[VPC Endpoints<br/>Private Service Access<br/>No Internet Gateway]
            SecurityGroups[Security Groups<br/>Stateful Firewall<br/>Least Privilege Access]
        end
        
        subgraph "Monitoring & Compliance"
            CloudTrail[AWS CloudTrail<br/>API Audit Logging<br/>Compliance Tracking]
            CloudWatch[CloudWatch Logs<br/>Security Event Monitoring<br/>Alerting]
            XRay[AWS X-Ray<br/>Request Tracing<br/>Security Analysis]
        end
    end
    
    %% Access Flow
    Internet -->|HTTPS| CloudFront
    Internet -->|HTTPS| WAF
    MCPClients -->|HTTPS| WAF
    
    WAF -->|Filtered Requests| AppSyncAuth
    CloudFront -->|Static Content| AppSyncAuth
    
    AppSyncAuth -->|Authenticate| CognitoUserPool
    CognitoUserPool -->|Authorize| CognitoIdentityPool
    CognitoIdentityPool -->|Temporary Creds| IAMRoles
    
    IAMRoles -->|Access| S3Encryption
    IAMRoles -->|Access| DDBEncryption
    IAMRoles -->|Execute| LambdaEnvVars
    
    %% Security Monitoring
    AppSyncAuth -.->|Audit| CloudTrail
    IAMRoles -.->|Logs| CloudWatch
    LambdaEnvVars -.->|Traces| XRay
```

## Network Architecture

```mermaid
graph TB
    subgraph "Network Architecture"
        subgraph "Internet"
            Users[End Users<br/>Global Access]
            APIs[NSW Government APIs<br/>Public Endpoints]
        end
        
        subgraph "AWS Global Infrastructure"
            subgraph "CloudFront Edge Locations"
                Edge[Global Edge Network<br/>Low Latency Content Delivery]
            end
            
            subgraph "ap-southeast-2 (Sydney)"
                subgraph "Availability Zone A"
                    AZA[Lambda Functions<br/>Auto-scaling Compute]
                end
                
                subgraph "Availability Zone B"
                    AZB[Lambda Functions<br/>High Availability]
                end
                
                subgraph "Regional Services"
                    S3Regional[S3 Buckets<br/>Regional Replication]
                    DDBRegional[DynamoDB<br/>Multi-AZ Deployment]
                    AppSyncRegional[AppSync API<br/>Regional Endpoint]
                end
            end
        end
        
        subgraph "Service Connectivity"
            subgraph "AWS Service Network"
                ServiceMesh[AWS Service Mesh<br/>Internal Communication<br/>Private Networking]
            end
            
            subgraph "External Integrations"
                LocationService[Amazon Location Service<br/>Map Tile Servers<br/>Geocoding APIs]
                BedrockService[Amazon Bedrock<br/>AI/ML Models<br/>Natural Language Processing]
            end
        end
    end
    
    %% Network Flow
    Users -->|HTTPS/443| Edge
    Edge -->|Origin Requests| AppSyncRegional
    
    APIs -->|HTTPS/443| AZA
    APIs -->|HTTPS/443| AZB
    
    AZA -->|Internal| ServiceMesh
    AZB -->|Internal| ServiceMesh
    ServiceMesh -->|Private| S3Regional
    ServiceMesh -->|Private| DDBRegional
    
    AppSyncRegional -->|API Calls| LocationService
    AppSyncRegional -->|AI Queries| BedrockService
    
    %% High Availability
    AZA -.->|Failover| AZB
    S3Regional -.->|Cross-AZ Replication| S3Regional
    DDBRegional -.->|Multi-AZ| DDBRegional
```

### Network Characteristics

- **Global Distribution:** CloudFront edge locations for low-latency content delivery
- **Regional Deployment:** Primary deployment in ap-southeast-2 (Sydney) for NSW data locality
- **High Availability:** Multi-AZ deployment for Lambda functions and DynamoDB
- **Private Networking:** AWS service mesh for internal service communication
- **External Connectivity:** Secure HTTPS connections to NSW Government APIs
- **Service Integration:** Native AWS service connectivity without internet routing

---

*All diagrams are automatically generated from CDK stack definitions and updated with infrastructure changes.*
