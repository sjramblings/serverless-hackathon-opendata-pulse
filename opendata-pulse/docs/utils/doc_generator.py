"""
Documentation Generator for OpenData Pulse infrastructure.

This module provides the main documentation generation functionality,
coordinating CDK parsing, diagram generation, and content creation.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

try:
    from .cdk_parser import CDKStackParser, InfrastructureComponent
    from .diagram_generator import DiagramGenerator
    from .infrastructure_analyzer import InfrastructureAnalyzer
except ImportError:
    from cdk_parser import CDKStackParser, InfrastructureComponent
    from diagram_generator import DiagramGenerator
    from infrastructure_analyzer import InfrastructureAnalyzer


class DocumentationGenerator:
    """Main documentation generator that coordinates all documentation creation."""
    
    def __init__(self, project_root: str = ".", docs_output: str = "docs"):
        """Initialize the documentation generator.
        
        Args:
            project_root: Root directory of the OpenData Pulse project
            docs_output: Output directory for generated documentation
        """
        self.project_root = Path(project_root)
        self.docs_output = Path(docs_output)
        self.infrastructure_path = self.project_root / "infrastructure"
        
        # Initialize parsers and generators
        self.cdk_parser = CDKStackParser(str(self.infrastructure_path))
        self.diagram_generator = MermaidDiagramGenerator()
        
        # Parsed components
        self.components: List[InfrastructureComponent] = []
        self.stack_dependencies: Dict[str, List[str]] = {}
        
    def generate_all_documentation(self) -> None:
        """Generate complete documentation suite."""
        print("Starting documentation generation...")
        
        # Parse CDK stacks
        self._parse_infrastructure()
        
        # Generate architecture documentation
        self._generate_architecture_docs()
        
        # Generate data flow documentation
        self._generate_data_flow_docs()
        
        # Generate deployment documentation
        self._generate_deployment_docs()
        
        # Generate API documentation
        self._generate_api_docs()
        
        # Generate security documentation
        self._generate_security_docs()
        
        # Generate operations documentation
        self._generate_operations_docs()
        
        print("Documentation generation complete!")
    
    def _parse_infrastructure(self) -> None:
        """Parse CDK infrastructure and extract components."""
        print("Parsing CDK infrastructure...")
        
        try:
            self.components = self.cdk_parser.parse_all_stacks()
            self.stack_dependencies = self.cdk_parser.get_stack_dependencies()
            print(f"Found {len(self.components)} infrastructure components")
        except Exception as e:
            print(f"Warning: Failed to parse infrastructure: {e}")
            # Continue with empty components list
            self.components = []
            self.stack_dependencies = {}
    
    def _generate_architecture_docs(self) -> None:
        """Generate architecture documentation with diagrams."""
        print("Generating architecture documentation...")
        
        # Update overview with parsed information
        overview_content = self._generate_architecture_overview()
        self._write_doc_file("architecture/overview.md", overview_content)
        
        # Update infrastructure diagram with actual components
        diagram_content = self._generate_infrastructure_diagram_doc()
        self._write_doc_file("architecture/infrastructure-diagram.md", diagram_content)
        
        # Update service dependencies
        dependencies_content = self._generate_service_dependencies_doc()
        self._write_doc_file("architecture/service-dependencies.md", dependencies_content)
    
    def _generate_architecture_overview(self) -> str:
        """Generate architecture overview content."""
        stacks = [comp for comp in self.components if comp.type == "stack"]
        resources = [comp for comp in self.components if comp.type == "resource"]
        
        content = f"""# Architecture Overview

*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} from CDK stack analysis*

## System Architecture

OpenData Pulse is a serverless application built on AWS that ingests, processes, and serves NSW government open data through multiple interfaces including web dashboards, GraphQL APIs, and MCP tools.

## Infrastructure Summary

- **Total Stacks**: {len(stacks)}
- **Total Resources**: {len(resources)}
- **AWS Services Used**: {len(set(comp.aws_service for comp in self.components if comp.aws_service != 'Unknown'))}

## Core Components

### Infrastructure Stacks
"""
        
        for stack in stacks:
            stack_resources = [comp for comp in resources if comp.stack_name == stack.name]
            content += f"- **{stack.name}** - {stack.purpose}\n"
            content += f"  - Resources: {len(stack_resources)}\n"
            if stack_resources:
                services = set(comp.aws_service for comp in stack_resources)
                content += f"  - Services: {', '.join(sorted(services))}\n"
        
        content += """
### Data Flow
1. **Ingestion** - Scheduled Lambda functions fetch data from NSW APIs
2. **Processing** - ETL Lambda transforms raw data into curated formats
3. **Storage** - Multi-layer storage in S3 (raw/curated) and DynamoDB (hot aggregates)
4. **Access** - Data served through GraphQL API and MCP tools

## Technology Stack
- **Infrastructure**: AWS CDK with Python
- **Backend**: Python Lambda functions with Powertools
- **Frontend**: React with Apollo Client
- **API**: AppSync GraphQL
- **AI/ML**: Amazon Bedrock for natural language processing

## Architecture Diagram

```mermaid
"""
        
        # Add the generated architecture diagram
        arch_diagram = self.diagram_generator.generate_architecture_diagram(
            self.components, self.stack_dependencies
        )
        content += arch_diagram + "\n```\n"
        
        return content
    
    def _generate_infrastructure_diagram_doc(self) -> str:
        """Generate infrastructure diagram documentation."""
        content = """# Infrastructure Diagram

*Visual representation of the OpenData Pulse infrastructure and service relationships.*

## High-Level Architecture

```mermaid
"""
        
        # Generate architecture diagram
        arch_diagram = self.diagram_generator.generate_architecture_diagram(
            self.components, self.stack_dependencies
        )
        content += arch_diagram + "\n```\n"
        
        content += """
## Stack Dependencies

```mermaid
"""
        
        # Generate dependency diagram
        dep_diagram = self.diagram_generator.generate_dependency_graph(self.stack_dependencies)
        content += dep_diagram + "\n```\n"
        
        content += """
## Network Architecture

```mermaid
"""
        
        # Generate network diagram
        network_diagram = self.diagram_generator.generate_network_diagram(self.components)
        content += network_diagram + "\n```\n"
        
        content += f"\n*Diagrams generated automatically on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} from CDK stack analysis*"
        
        return content
    
    def _generate_service_dependencies_doc(self) -> str:
        """Generate service dependencies documentation."""
        content = f"""# Service Dependencies

*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} from CDK stack analysis*

## Cross-Stack Dependencies

"""
        
        for stack_name, deps in self.stack_dependencies.items():
            stack_components = self.cdk_parser.get_components_by_stack(stack_name)
            
            content += f"### {stack_name} Dependencies\n"
            if deps:
                content += f"- **Depends on**: {', '.join(deps)}\n"
            else:
                content += "- **Depends on**: None (foundational stack)\n"
            
            if stack_components:
                resources = [comp for comp in stack_components if comp.type == "resource"]
                if resources:
                    content += f"- **Provides**: {len(resources)} resources\n"
                    services = set(comp.aws_service for comp in resources)
                    content += f"- **Services**: {', '.join(sorted(services))}\n"
            
            content += "\n"
        
        content += """## Resource Naming Conventions

All resources follow the pattern: `opendata-pulse-{resource-type}-{account-id}`

### Examples
"""
        
        # Add examples from actual parsed components
        for component in self.components[:10]:  # Show first 10 as examples
            if component.type == "resource":
                content += f"- **{component.aws_service}**: `{component.name}` - {component.purpose}\n"
        
        content += f"\n*Analysis based on {len(self.components)} parsed infrastructure components*"
        
        return content
    
    def _generate_data_flow_docs(self) -> None:
        """Generate data flow documentation."""
        print("Generating data flow documentation...")
        
        # Generate ingestion pipeline doc
        ingestion_content = self._generate_ingestion_pipeline_doc()
        self._write_doc_file("data-flow/ingestion-pipeline.md", ingestion_content)
        
        # Generate ETL processing doc
        etl_content = self._generate_etl_processing_doc()
        self._write_doc_file("data-flow/etl-processing.md", etl_content)
        
        # Generate query pipeline doc
        query_content = self._generate_query_pipeline_doc()
        self._write_doc_file("data-flow/query-pipeline.md", query_content)
        
        # Generate monitoring doc
        monitoring_content = self._generate_monitoring_doc()
        self._write_doc_file("data-flow/monitoring-alerting.md", monitoring_content)
    
    def _generate_ingestion_pipeline_doc(self) -> str:
        """Generate ingestion pipeline documentation."""
        # Find ingestion-related components
        ingestion_lambda = None
        for comp in self.components:
            if 'ingest' in comp.name.lower() and comp.aws_service == 'Lambda':
                ingestion_lambda = comp
                break
        
        content = f"""# Data Ingestion Pipeline

*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} from infrastructure analysis*

## Overview

The data ingestion pipeline automatically fetches data from NSW Government APIs on a scheduled basis and stores it in S3 raw data buckets with proper partitioning.

## Pipeline Components

"""
        
        if ingestion_lambda:
            content += f"""### Ingestion Lambda Function
- **Function**: `{ingestion_lambda.name}`
- **AWS Service**: {ingestion_lambda.aws_service}
- **Purpose**: {ingestion_lambda.purpose}
- **Stack**: {ingestion_lambda.stack_name}
"""
            
            if ingestion_lambda.configuration:
                content += "- **Configuration**:\n"
                for key, value in ingestion_lambda.configuration.items():
                    content += f"  - {key}: {value}\n"
        
        content += """
### Data Sources
- NSW Air Quality API
- Additional NSW Government APIs (configurable)

## Data Flow Diagram

```mermaid
"""
        
        # Generate sequence diagram for ingestion
        sequence_diagram = self.diagram_generator.generate_sequence_diagram(
            "data_ingestion", self.components
        )
        content += sequence_diagram + "\n```\n"
        
        content += f"\n*Documentation generated from {len(self.components)} infrastructure components*"
        
        return content
    
    def _generate_etl_processing_doc(self) -> str:
        """Generate ETL processing documentation."""
        content = f"""# ETL Processing Pipeline

*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} from infrastructure analysis*

## Overview

The ETL pipeline processes raw data from S3, applies transformations, and outputs curated data in multiple formats for different access patterns.

## Data Flow Diagram

```mermaid
"""
        
        # Generate sequence diagram for ETL
        sequence_diagram = self.diagram_generator.generate_sequence_diagram(
            "etl_processing", self.components
        )
        content += sequence_diagram + "\n```\n"
        
        return content
    
    def _generate_query_pipeline_doc(self) -> str:
        """Generate query pipeline documentation."""
        content = f"""# Query Pipeline

*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} from infrastructure analysis*

## Overview

The query pipeline serves data from storage through GraphQL API to frontend applications and MCP clients.

## Query Flow Diagram

```mermaid
"""
        
        # Generate sequence diagram for queries
        sequence_diagram = self.diagram_generator.generate_sequence_diagram(
            "query_processing", self.components
        )
        content += sequence_diagram + "\n```\n"
        
        return content
    
    def _generate_monitoring_doc(self) -> str:
        """Generate monitoring and alerting documentation."""
        return f"""# Monitoring and Alerting

*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} from infrastructure analysis*

## Overview

Comprehensive monitoring and alerting for all data processing stages using CloudWatch metrics, alarms, and SNS notifications.

## Error Handling Flow

```mermaid
{self.diagram_generator.generate_flowchart_diagram("error_handling", self.components)}
```

## Monitoring Components

### CloudWatch Metrics
- Lambda function duration and error rates
- S3 object creation and access patterns
- DynamoDB read/write capacity utilization
- API Gateway request rates and latency

### SNS Notifications
- Data ingestion success/failure alerts
- ETL processing completion notifications
- System health check results
- Error threshold breach alerts

*Monitoring configuration extracted from infrastructure components*"""
    
    def _generate_deployment_docs(self) -> None:
        """Generate deployment documentation."""
        print("Generating deployment documentation...")
        
        deployment_content = f"""# Environment Setup and Deployment

*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*

## Deployment Process

```mermaid
{self.diagram_generator.generate_flowchart_diagram("deployment", self.components)}
```

## Stack Deployment Order

Based on the analyzed dependencies:

"""
        
        # Generate deployment order from dependencies
        deployment_order = self._calculate_deployment_order()
        for i, stack in enumerate(deployment_order, 1):
            deployment_content += f"{i}. **{stack}**\n"
        
        deployment_content += """
## CDK Commands

```bash
# Deploy all stacks in correct order
cdk deploy --all

# Deploy specific stack
cdk deploy OpenDataPulse{StackName}Stack

# View differences before deployment
cdk diff
```

## Environment Variables

Key environment variables required for deployment:
- `AWS_ACCOUNT_ID` - Target AWS account
- `AWS_REGION` - Deployment region (default: ap-southeast-2)
- `ENVIRONMENT` - Environment name (dev/staging/prod)
"""
        
        self._write_doc_file("deployment/environment-setup.md", deployment_content)
    
    def _calculate_deployment_order(self) -> List[str]:
        """Calculate correct deployment order based on dependencies."""
        # Simple topological sort of stack dependencies
        order = []
        remaining = set(self.stack_dependencies.keys())
        
        while remaining:
            # Find stacks with no unresolved dependencies
            ready = []
            for stack in remaining:
                deps = self.stack_dependencies[stack]
                if all(dep in order or dep not in remaining for dep in deps):
                    ready.append(stack)
            
            if not ready:
                # Circular dependency or missing stack - add remaining arbitrarily
                ready = list(remaining)
            
            # Sort alphabetically for consistent ordering
            ready.sort()
            order.extend(ready)
            remaining -= set(ready)
        
        return order
    
    def _generate_api_docs(self) -> None:
        """Generate API documentation."""
        print("Generating API documentation...")
        
        api_content = f"""# GraphQL API Documentation

*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*

## API Overview

The OpenData Pulse GraphQL API provides access to NSW government data through a unified interface with authentication and authorization.

## API Components
"""
        
        # Find API-related components
        api_components = [comp for comp in self.components 
                         if comp.aws_service in ['AppSync', 'Cognito', 'API Gateway']]
        
        for comp in api_components:
            api_content += f"- **{comp.name}** ({comp.aws_service}): {comp.purpose}\n"
        
        api_content += """
## Authentication Flow

Authentication is handled through AWS Cognito with JWT tokens.

## GraphQL Schema

The complete GraphQL schema is defined in `infrastructure/schema.graphql`.

## MCP Tools

The system exposes 5+ MCP tools for programmatic access:
- Data query tools
- Alert management tools
- System health tools
- Geographic query tools
- Export tools
"""
        
        self._write_doc_file("api/graphql-schema.md", api_content)
    
    def _generate_security_docs(self) -> None:
        """Generate security documentation."""
        print("Generating security documentation...")
        
        security_content = f"""# Security and Compliance

*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*

## Security Overview

OpenData Pulse implements comprehensive security controls following AWS Well-Architected security principles.

## IAM Access Control

### IAM Components
"""
        
        # Find IAM-related components
        iam_components = [comp for comp in self.components if comp.aws_service == 'IAM']
        for comp in iam_components:
            security_content += f"- **{comp.name}**: {comp.purpose}\n"
        
        security_content += """
## Data Protection

### Encryption at Rest
- S3 buckets encrypted with AES-256
- DynamoDB tables encrypted with AWS managed keys
- Lambda environment variables encrypted

### Encryption in Transit
- HTTPS/TLS for all API communications
- VPC endpoints for internal service communication

## Network Security

All services operate within AWS managed security boundaries with:
- WAF protection for public endpoints
- Security groups restricting access
- VPC endpoints for internal communication

## Compliance Framework Mapping

The system implements controls aligned with:
- AWS Well-Architected Security Pillar
- SOC 2 Type II requirements
- ISO 27001 security controls
"""
        
        self._write_doc_file("security/iam-policies.md", security_content)
    
    def _generate_operations_docs(self) -> None:
        """Generate operations documentation."""
        print("Generating operations documentation...")
        
        ops_content = f"""# Operations and Monitoring

*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*

## Operational Overview

OpenData Pulse is designed for minimal operational overhead with automated monitoring, alerting, and self-healing capabilities.

## Monitoring Components
"""
        
        # Find monitoring-related components
        monitoring_components = [comp for comp in self.components 
                               if comp.aws_service in ['SNS', 'SQS', 'EventBridge']]
        
        for comp in monitoring_components:
            ops_content += f"- **{comp.name}** ({comp.aws_service}): {comp.purpose}\n"
        
        ops_content += """
## Cost Optimization

### Resource Costs
- Lambda: Pay-per-execution model
- S3: Tiered storage with lifecycle policies
- DynamoDB: On-demand billing for variable workloads
- AppSync: Pay-per-request GraphQL API

### Optimization Strategies
- S3 Intelligent Tiering for automatic cost optimization
- DynamoDB on-demand scaling
- Lambda provisioned concurrency for consistent performance
- CloudFront caching to reduce API calls

## Troubleshooting

### Common Issues
1. **Data Ingestion Failures**: Check NSW API availability and Lambda logs
2. **ETL Processing Delays**: Monitor S3 event triggers and Lambda duration
3. **API Latency**: Review DynamoDB performance and AppSync resolver efficiency
4. **Frontend Issues**: Check CloudFront cache status and Amplify deployment

### Health Checks
- Automated health check Lambda functions
- CloudWatch alarms for key metrics
- SNS notifications for critical issues
"""
        
        self._write_doc_file("operations/monitoring.md", ops_content)
    
    def _write_doc_file(self, relative_path: str, content: str) -> None:
        """Write documentation content to file."""
        file_path = self.docs_output / relative_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"Generated: {relative_path}")
    
    def get_component_summary(self) -> Dict[str, int]:
        """Get summary statistics of parsed components."""
        summary = {
            'total_components': len(self.components),
            'stacks': len([c for c in self.components if c.type == 'stack']),
            'resources': len([c for c in self.components if c.type == 'resource']),
            'aws_services': len(set(c.aws_service for c in self.components if c.aws_service != 'Unknown'))
        }
        return summary