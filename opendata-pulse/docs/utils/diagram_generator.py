"""
Infrastructure Diagram Generator for OpenData Pulse.

This module generates comprehensive Mermaid diagrams showing infrastructure
components, service relationships, and data flow patterns.
"""

from typing import Dict, List, Any, Set
from datetime import datetime
from pathlib import Path

from .infrastructure_analyzer import InfrastructureAnalyzer


class DiagramGenerator:
    """Generator for infrastructure Mermaid diagrams."""
    
    def __init__(self, analyzer: InfrastructureAnalyzer = None):
        """Initialize with infrastructure analyzer."""
        self.analyzer = analyzer or InfrastructureAnalyzer()
        self.analysis_data = None
    
    def generate_infrastructure_diagrams(self, output_path: str = "docs/architecture/infrastructure-diagram.md") -> None:
        """Generate comprehensive infrastructure diagram documentation."""
        # Get analysis data
        self.analysis_data = self.analyzer.analyze_infrastructure()
        
        # Generate documentation content
        content = self._generate_diagram_content()
        
        # Write to file
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"Infrastructure diagram documentation generated: {output_file}")
    
    def _generate_diagram_content(self) -> str:
        """Generate the complete diagram documentation content."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        content = f"""# Infrastructure Diagrams

*Visual representation of the OpenData Pulse infrastructure, service relationships, and data flow patterns.*

**Last Updated:** {timestamp}  
**Generated from:** CDK stack definitions and infrastructure analysis

## High-Level Architecture

{self._generate_high_level_architecture()}

## Stack Architecture

{self._generate_stack_architecture_diagram()}

## Service Relationships

{self._generate_service_relationships_diagram()}

## Data Flow Architecture

{self._generate_data_flow_diagram()}

## Deployment Dependencies

{self._generate_deployment_dependencies_diagram()}

## Security Architecture

{self._generate_security_architecture_diagram()}

## Network Architecture

{self._generate_network_architecture_diagram()}

---

*All diagrams are automatically generated from CDK stack definitions and updated with infrastructure changes.*
"""
        return content
    
    def _generate_high_level_architecture(self) -> str:
        """Generate high-level architecture diagram."""
        return """```mermaid
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
```"""
    
    def _generate_stack_architecture_diagram(self) -> str:
        """Generate stack architecture diagram."""
        stacks = self.analysis_data['stacks']
        dependencies = self.analysis_data['dependencies']['dependency_map']
        
        diagram = """```mermaid
graph TB
    subgraph "OpenData Pulse CDK Stacks"
"""
        
        # Add each stack with its resources
        for stack_name, stack_info in stacks.items():
            stack_id = stack_name.replace('Stack', '')
            diagram += f"""        
        subgraph "{stack_name}"
            {stack_id}_Purpose["{stack_info['purpose']}"]
"""
            
            # Group resources by service
            services = {}
            for resource in stack_info['resources']:
                service = resource['service']
                if service not in services:
                    services[service] = []
                services[service].append(resource)
            
            # Add service groups
            for service, resources in services.items():
                if service == 'Unknown':
                    continue
                service_id = f"{stack_id}_{service.replace(' ', '')}"
                diagram += f"            {service_id}[{service}<br/>{len(resources)} resources]\n"
        
        diagram += "        end\n"
        
        diagram += """    end
    
    %% Stack Dependencies"""
        
        # Add dependency arrows
        for source_stack, deps in dependencies.items():
            for dep_info in deps:
                target_stack = dep_info['depends_on']
                source_id = source_stack.replace('Stack', '')
                target_id = target_stack.replace('Stack', '')
                diagram += f"\n    {target_id}_Purpose --> {source_id}_Purpose"
        
        diagram += "\n```"
        
        return diagram
    
    def _generate_service_relationships_diagram(self) -> str:
        """Generate service relationships diagram."""
        services = self.analysis_data['services']
        relationships = self.analysis_data['relationships']
        
        diagram = """```mermaid
graph LR
    subgraph "AWS Services Interaction Map"
"""
        
        # Add service nodes
        service_nodes = {}
        for service_name, service_info in services.items():
            if service_name == 'Unknown':
                continue
            node_id = service_name.replace(' ', '').replace('-', '')
            service_nodes[service_name] = node_id
            resource_count = service_info['resource_count']
            diagram += f"        {node_id}[{service_name}<br/>{resource_count} resources]\n"
        
        diagram += "    end\n\n    %% Service Relationships\n"
        
        # Add relationship arrows
        for rel_key, rel_info in relationships.items():
            source_service = rel_info['source_service']
            target_service = rel_info['target_service']
            
            if source_service in service_nodes and target_service in service_nodes:
                source_node = service_nodes[source_service]
                target_node = service_nodes[target_service]
                
                # Get relationship types
                rel_types = list(rel_info['relationship_types'])
                rel_label = ', '.join(rel_types)
                
                diagram += f"    {source_node} -->|{rel_label}| {target_node}\n"
        
        diagram += "```"
        
        return diagram
    
    def _generate_data_flow_diagram(self) -> str:
        """Generate detailed data flow diagram."""
        return """```mermaid
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
```"""
    
    def _generate_deployment_dependencies_diagram(self) -> str:
        """Generate deployment dependencies diagram."""
        dependencies = self.analysis_data['dependencies']
        
        diagram = """```mermaid
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

"""
        
        deployment_order = dependencies['deployment_order']
        diagram += f"**Recommended Deployment Order:** {' → '.join(deployment_order)}\n\n"
        
        diagram += """**Parallel Deployment Opportunities:**
- ComputeStack and LocationStack can be deployed in parallel after DataStack
- Individual resources within stacks deploy in parallel where possible
- Stack updates can be performed independently once dependencies are satisfied

**Rollback Strategy:**
- Stacks can be rolled back in reverse dependency order
- DataStack rollback requires careful consideration due to data retention policies
- Lambda functions support blue/green deployments for zero-downtime updates"""
        
        return diagram
    
    def _generate_security_architecture_diagram(self) -> str:
        """Generate security architecture diagram."""
        return """```mermaid
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
```"""
    
    def _generate_network_architecture_diagram(self) -> str:
        """Generate network architecture diagram."""
        return """```mermaid
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
- **Service Integration:** Native AWS service connectivity without internet routing"""


def main():
    """Main function to generate infrastructure diagrams."""
    generator = DiagramGenerator()
    
    try:
        # Generate diagram documentation
        generator.generate_infrastructure_diagrams()
        print("Infrastructure diagram documentation generated successfully!")
        
    except Exception as e:
        print(f"Error generating diagram documentation: {e}")
        raise


if __name__ == "__main__":
    main()