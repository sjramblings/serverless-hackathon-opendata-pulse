"""
Mermaid Diagram Generator for infrastructure documentation.

This module provides utilities to generate different types of Mermaid diagrams
from infrastructure components and their relationships.
"""

from enum import Enum
from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass
from .cdk_parser import InfrastructureComponent


class DiagramType(Enum):
    """Supported Mermaid diagram types."""
    ARCHITECTURE = "graph"
    SEQUENCE = "sequenceDiagram"
    FLOWCHART = "flowchart"
    NETWORK = "graph"
    DEPENDENCY = "graph"


@dataclass
class DiagramNode:
    """Represents a node in a Mermaid diagram."""
    id: str
    label: str
    shape: str = "rect"  # rect, circle, diamond, etc.
    style_class: str = ""


@dataclass
class DiagramEdge:
    """Represents an edge/connection in a Mermaid diagram."""
    from_node: str
    to_node: str
    label: str = ""
    style: str = "-->"  # -->, -.-> , ==>, etc.


class MermaidDiagramGenerator:
    """Generator for various types of Mermaid diagrams."""
    
    def __init__(self):
        """Initialize the diagram generator."""
        self.aws_service_colors = {
            'S3': '#FF9900',
            'DynamoDB': '#FF9900', 
            'Lambda': '#FF9900',
            'AppSync': '#FF9900',
            'Cognito': '#FF9900',
            'EventBridge': '#FF9900',
            'SQS': '#FF9900',
            'SNS': '#FF9900',
            'Glue': '#FF9900',
            'Athena': '#FF9900',
            'Amplify': '#FF9900',
            'CloudFront': '#FF9900',
            'Location Service': '#FF9900',
            'API Gateway': '#FF9900'
        }
    
    def generate_architecture_diagram(self, components: List[InfrastructureComponent],
                                    stack_dependencies: Dict[str, List[str]]) -> str:
        """Generate high-level architecture diagram showing all stacks and services."""
        
        diagram_lines = ["graph TB"]
        
        # Group components by stack
        stacks = {}
        for component in components:
            if component.type == "stack":
                stacks[component.stack_name] = []
        
        for component in components:
            if component.type == "resource" and component.stack_name in stacks:
                stacks[component.stack_name].append(component)
        
        # Generate subgraphs for each stack
        for stack_name, stack_components in stacks.items():
            if stack_components:  # Only create subgraph if it has components
                diagram_lines.append(f'    subgraph "{stack_name}"')
                
                for component in stack_components:
                    node_id = self._sanitize_id(component.id)
                    label = f"{component.name}[{component.aws_service}]"
                    diagram_lines.append(f'        {node_id}["{label}"]')
                
                diagram_lines.append("    end")
        
        # Add external systems
        diagram_lines.extend([
            '    subgraph "External Systems"',
            '        NSW["NSW Government APIs"]',
            '        Users["End Users"]',
            '        Devs["Developers/MCP Clients"]',
            '    end'
        ])
        
        # Add connections based on common data flow patterns
        diagram_lines.extend(self._generate_data_flow_connections(components))
        
        # Add stack dependencies
        for stack, deps in stack_dependencies.items():
            for dep in deps:
                if stack in stacks and dep in stacks:
                    diagram_lines.append(f'    {dep} -.-> {stack}')
        
        return '\n'.join(diagram_lines)
    
    def generate_sequence_diagram(self, process_name: str, 
                                components: List[InfrastructureComponent]) -> str:
        """Generate sequence diagram for a specific process flow."""
        
        if process_name.lower() == "data_ingestion":
            return self._generate_ingestion_sequence()
        elif process_name.lower() == "etl_processing":
            return self._generate_etl_sequence()
        elif process_name.lower() == "query_processing":
            return self._generate_query_sequence()
        else:
            return self._generate_generic_sequence(components)
    
    def _generate_ingestion_sequence(self) -> str:
        """Generate sequence diagram for data ingestion process."""
        return """sequenceDiagram
    participant EB as EventBridge
    participant IL as Ingestion Lambda
    participant NSW as NSW API
    participant S3 as S3 Raw Bucket
    participant SNS as SNS Alerts
    participant DLQ as Dead Letter Queue
    
    EB->>IL: Hourly trigger
    activate IL
    IL->>NSW: HTTP GET request
    NSW-->>IL: JSON response
    
    alt Success
        IL->>IL: Validate data
        IL->>S3: Store raw data (partitioned)
        IL->>SNS: Success notification
    else API Error
        IL->>DLQ: Send to dead letter queue
        IL->>SNS: Error notification
    end
    
    deactivate IL
    
    Note over S3: Data partitioned by YYYY/MM/DD/HH
    Note over IL: Includes retry logic and error handling"""
    
    def _generate_etl_sequence(self) -> str:
        """Generate sequence diagram for ETL processing."""
        return """sequenceDiagram
    participant S3Raw as S3 Raw Data
    participant ETL as ETL Lambda
    participant DDB as DynamoDB
    participant S3Cur as S3 Curated
    participant SNS as SNS Alerts
    
    S3Raw->>ETL: S3 object created event
    activate ETL
    
    ETL->>S3Raw: Read raw data
    ETL->>ETL: Validate schema
    ETL->>ETL: Clean & transform
    ETL->>ETL: Calculate aggregates
    
    par Store Hot Aggregates
        ETL->>DDB: Write aggregated data
    and Store Curated Data
        ETL->>S3Cur: Write parquet files
    end
    
    ETL->>SNS: Processing complete
    deactivate ETL
    
    Note over DDB: Hot aggregates for fast queries
    Note over S3Cur: Partitioned parquet for analytics"""
    
    def _generate_query_sequence(self) -> str:
        """Generate sequence diagram for query processing."""
        return """sequenceDiagram
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
    Note over Athena: Complex analytics on historical data"""
    
    def generate_flowchart_diagram(self, process_name: str,
                                 components: List[InfrastructureComponent]) -> str:
        """Generate flowchart diagram for decision flows and processes."""
        
        if process_name.lower() == "deployment":
            return self._generate_deployment_flowchart()
        elif process_name.lower() == "error_handling":
            return self._generate_error_handling_flowchart()
        else:
            return self._generate_generic_flowchart(components)
    
    def _generate_deployment_flowchart(self) -> str:
        """Generate deployment process flowchart."""
        return """flowchart TD
    Start([Start Deployment]) --> CheckEnv{Environment?}
    
    CheckEnv -->|Development| DevDeploy[Deploy to Dev]
    CheckEnv -->|Staging| StageDeploy[Deploy to Staging]
    CheckEnv -->|Production| ProdChecks{Pre-deployment Checks}
    
    ProdChecks -->|Pass| ProdDeploy[Deploy to Production]
    ProdChecks -->|Fail| FixIssues[Fix Issues]
    FixIssues --> ProdChecks
    
    DevDeploy --> DataStack[Deploy DataStack]
    StageDeploy --> DataStack
    ProdDeploy --> DataStack
    
    DataStack --> ComputeStack[Deploy ComputeStack]
    ComputeStack --> APIStack[Deploy APIStack]
    APIStack --> FrontendStack[Deploy FrontendStack]
    FrontendStack --> LocationStack[Deploy LocationStack]
    
    LocationStack --> Validate{Validation Tests}
    Validate -->|Pass| Success([Deployment Complete])
    Validate -->|Fail| Rollback[Rollback Changes]
    Rollback --> Investigate[Investigate Issues]
    
    style Success fill:#90EE90
    style Rollback fill:#FFB6C1
    style FixIssues fill:#FFB6C1"""
    
    def _generate_error_handling_flowchart(self) -> str:
        """Generate error handling flowchart."""
        return """flowchart TD
    Error([Error Detected]) --> Classify{Error Type?}
    
    Classify -->|API Error| APIError[NSW API Unavailable]
    Classify -->|Data Error| DataError[Invalid Data Format]
    Classify -->|System Error| SysError[AWS Service Error]
    
    APIError --> Retry{Retry Count < 3?}
    Retry -->|Yes| Wait[Wait with Backoff]
    Wait --> APICall[Retry API Call]
    APICall --> Success{Success?}
    Success -->|Yes| Continue([Continue Processing])
    Success -->|No| Retry
    Retry -->|No| DLQ[Send to Dead Letter Queue]
    
    DataError --> Validate[Log Validation Error]
    Validate --> Skip[Skip Invalid Records]
    Skip --> Continue
    
    SysError --> Alert[Send SNS Alert]
    Alert --> Manual[Manual Investigation]
    
    DLQ --> Alert
    Manual --> Resolve[Resolve Issue]
    Resolve --> Continue
    
    style Continue fill:#90EE90
    style DLQ fill:#FFB6C1
    style Alert fill:#FFA500"""
    
    def generate_network_diagram(self, components: List[InfrastructureComponent]) -> str:
        """Generate network security and connectivity diagram."""
        return """graph TB
    subgraph "Internet"
        Users[End Users]
        APIs[NSW Government APIs]
        Devs[MCP Clients]
    end
    
    subgraph "AWS Cloud"
        subgraph "Edge Services"
            CF[CloudFront CDN]
            WAF[AWS WAF]
        end
        
        subgraph "API Layer"
            AppSync[AppSync GraphQL]
            Cognito[Cognito User Pool]
        end
        
        subgraph "Compute Layer"
            Lambda1[Ingestion Lambda]
            Lambda2[ETL Lambda]
            Lambda3[Health Check Lambda]
        end
        
        subgraph "Data Layer"
            S3[S3 Buckets]
            DDB[DynamoDB Tables]
            Athena[Athena Workgroup]
        end
        
        subgraph "Messaging"
            EventBridge[EventBridge]
            SQS[SQS Queues]
            SNS[SNS Topics]
        end
    end
    
    Users --> CF
    CF --> WAF
    WAF --> AppSync
    AppSync --> Cognito
    AppSync --> DDB
    AppSync --> Athena
    
    APIs --> Lambda1
    Lambda1 --> S3
    S3 --> Lambda2
    Lambda2 --> DDB
    Lambda2 --> S3
    
    EventBridge --> Lambda1
    EventBridge --> Lambda2
    Lambda1 --> SNS
    Lambda2 --> SNS
    
    Devs --> AppSync
    
    style CF fill:#FF9900
    style AppSync fill:#FF9900
    style Lambda1 fill:#FF9900
    style S3 fill:#FF9900
    style DDB fill:#FF9900"""
    
    def _generate_data_flow_connections(self, components: List[InfrastructureComponent]) -> List[str]:
        """Generate data flow connections between components."""
        connections = []
        
        # Find key components
        ingestion_lambda = None
        etl_lambda = None
        s3_raw = None
        s3_curated = None
        dynamodb = None
        appsync = None
        
        for comp in components:
            comp_name_lower = comp.name.lower()
            if 'ingest' in comp_name_lower and comp.aws_service == 'Lambda':
                ingestion_lambda = comp.id
            elif 'etl' in comp_name_lower and comp.aws_service == 'Lambda':
                etl_lambda = comp.id
            elif 'raw' in comp_name_lower and comp.aws_service == 'S3':
                s3_raw = comp.id
            elif 'curated' in comp_name_lower and comp.aws_service == 'S3':
                s3_curated = comp.id
            elif comp.aws_service == 'DynamoDB':
                dynamodb = comp.id
            elif comp.aws_service == 'AppSync':
                appsync = comp.id
        
        # Add data flow connections
        if ingestion_lambda and s3_raw:
            connections.append(f'    NSW --> {self._sanitize_id(ingestion_lambda)}')
            connections.append(f'    {self._sanitize_id(ingestion_lambda)} --> {self._sanitize_id(s3_raw)}')
        
        if s3_raw and etl_lambda:
            connections.append(f'    {self._sanitize_id(s3_raw)} --> {self._sanitize_id(etl_lambda)}')
        
        if etl_lambda and s3_curated:
            connections.append(f'    {self._sanitize_id(etl_lambda)} --> {self._sanitize_id(s3_curated)}')
        
        if etl_lambda and dynamodb:
            connections.append(f'    {self._sanitize_id(etl_lambda)} --> {self._sanitize_id(dynamodb)}')
        
        if appsync and dynamodb:
            connections.append(f'    {self._sanitize_id(appsync)} --> {self._sanitize_id(dynamodb)}')
        
        if appsync and s3_curated:
            connections.append(f'    {self._sanitize_id(appsync)} --> {self._sanitize_id(s3_curated)}')
        
        connections.extend([
            '    Users --> CloudFront',
            '    Devs --> MCPServer'
        ])
        
        return connections
    
    def _generate_generic_sequence(self, components: List[InfrastructureComponent]) -> str:
        """Generate a generic sequence diagram from components."""
        return """sequenceDiagram
    participant User as User/Client
    participant API as API Layer
    participant Compute as Compute Layer
    participant Data as Data Layer
    
    User->>API: Request
    API->>Compute: Process
    Compute->>Data: Store/Retrieve
    Data-->>Compute: Response
    Compute-->>API: Result
    API-->>User: Response"""
    
    def _generate_generic_flowchart(self, components: List[InfrastructureComponent]) -> str:
        """Generate a generic flowchart from components."""
        return """flowchart TD
    Start([Start]) --> Process[Process Data]
    Process --> Decision{Success?}
    Decision -->|Yes| Success([Complete])
    Decision -->|No| Error[Handle Error]
    Error --> Process
    
    style Success fill:#90EE90
    style Error fill:#FFB6C1"""
    
    def _sanitize_id(self, node_id: str) -> str:
        """Sanitize node ID for Mermaid syntax."""
        # Replace invalid characters with underscores
        sanitized = node_id.replace('-', '_').replace(' ', '_').replace('.', '_')
        # Ensure it starts with a letter
        if not sanitized[0].isalpha():
            sanitized = 'node_' + sanitized
        return sanitized
    
    def generate_dependency_graph(self, stack_dependencies: Dict[str, List[str]]) -> str:
        """Generate stack dependency graph."""
        lines = ["graph LR"]
        
        for stack, deps in stack_dependencies.items():
            for dep in deps:
                lines.append(f'    {dep} --> {stack}')
        
        # Add styling
        lines.extend([
            '    classDef dataStack fill:#e1f5fe',
            '    classDef computeStack fill:#f3e5f5', 
            '    classDef apiStack fill:#e8f5e8',
            '    classDef frontendStack fill:#fff3e0',
            '    classDef locationStack fill:#fce4ec',
            '    class DataStack dataStack',
            '    class ComputeStack computeStack',
            '    class APIStack apiStack', 
            '    class FrontendStack frontendStack',
            '    class LocationStack locationStack'
        ])
        
        return '\n'.join(lines)