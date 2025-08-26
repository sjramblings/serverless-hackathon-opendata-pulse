"""
Infrastructure Overview Documentation Generator.

This module generates comprehensive architecture overview documentation
with Mermaid diagrams showing all CDK stacks and their relationships.
"""

import json
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

from .infrastructure_analyzer import InfrastructureAnalyzer


class OverviewGenerator:
    """Generator for infrastructure overview documentation."""
    
    def __init__(self, analyzer: InfrastructureAnalyzer = None):
        """Initialize with infrastructure analyzer."""
        self.analyzer = analyzer or InfrastructureAnalyzer()
        self.analysis_data = None
    
    def generate_overview_documentation(self, output_path: str = "docs/architecture/overview.md") -> None:
        """Generate comprehensive infrastructure overview documentation."""
        # Get analysis data
        self.analysis_data = self.analyzer.analyze_infrastructure()
        
        # Generate documentation content
        content = self._generate_overview_content()
        
        # Write to file
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"Infrastructure overview documentation generated: {output_file}")
    
    def _generate_overview_content(self) -> str:
        """Generate the complete overview documentation content."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        content = f"""# Architecture Overview

*This document provides a comprehensive overview of the OpenData Pulse system architecture.*

**Last Updated:** {timestamp}  
**Generated from:** CDK stack definitions and infrastructure analysis

## System Overview

{self._generate_system_overview()}

## Architecture Diagram

{self._generate_architecture_diagram()}

## Stack Architecture

{self._generate_stack_architecture()}

## Service Architecture

{self._generate_service_architecture()}

## Deployment Architecture

{self._generate_deployment_architecture()}

## Data Flow Architecture

{self._generate_data_flow_overview()}

## Security Architecture

{self._generate_security_overview()}

## Technology Stack

{self._generate_technology_stack()}

## Resource Summary

{self._generate_resource_summary()}

---

*This documentation is automatically generated from CDK stack definitions. For detailed component information, see the individual stack documentation.*
"""
        return content
    
    def _generate_system_overview(self) -> str:
        """Generate high-level system overview."""
        overview = self.analysis_data['overview']
        
        return f"""OpenData Pulse is a {overview['architecture_pattern'].lower()} application built on AWS that makes NSW government open datasets accessible through real-time dashboards, Gen-AI natural language queries, and MCP (Model Context Protocol) integration.

### Key Characteristics
- **Architecture Pattern:** {overview['architecture_pattern']}
- **Deployment Model:** {overview['deployment_model']}
- **Primary Region:** {overview['primary_region']} (Sydney)
- **Total Infrastructure:** {overview['total_stacks']} stacks, {overview['total_services']} AWS services, {overview['total_resources']} resources

### Core Value Proposition
- Real-time data ingestion from NSW Air Quality API with hourly updates
- Gen-AI natural language interface for data exploration
- Interactive maps using Amazon Location Service for geographic visualization
- MCP tools for developer integration and programmatic access
- Serverless architecture ensuring scalability and cost-effectiveness"""
    
    def _generate_architecture_diagram(self) -> str:
        """Generate Mermaid architecture diagram showing all stacks and relationships."""
        stacks = self.analysis_data['stacks']
        dependencies = self.analysis_data['dependencies']['dependency_map']
        
        # Create Mermaid diagram
        diagram = """```mermaid
graph TB
    subgraph "OpenData Pulse Architecture"
        subgraph "Data Layer"
            DS[DataStack<br/>S3, DynamoDB, Glue, Athena]
        end
        
        subgraph "Compute Layer"
            CS[ComputeStack<br/>Lambda, EventBridge, SQS, SNS]
        end
        
        subgraph "API Layer"
            AS[APIStack<br/>AppSync, Cognito, WAF]
        end
        
        subgraph "Frontend Layer"
            FS[FrontendStack<br/>Amplify, CloudFront]
        end
        
        subgraph "Location Layer"
            LS[LocationStack<br/>Location Service, Maps]
        end
        
        %% Dependencies
"""
        
        # Add dependency arrows
        for source_stack, deps in dependencies.items():
            for dep_info in deps:
                target_stack = dep_info['depends_on']
                # Map stack names to diagram nodes
                source_node = self._get_stack_node_id(source_stack)
                target_node = self._get_stack_node_id(target_stack)
                diagram += f"        {target_node} --> {source_node}\n"
        
        # Add external connections
        diagram += """
        %% External Connections
        NSW[NSW Government APIs] --> CS
        CS --> DS
        DS --> AS
        AS --> FS
        DS --> LS
        
        %% User Interactions
        Users[Citizens & Developers] --> FS
        Users --> AS
        MCP[MCP Clients] --> AS
    end
```"""
        
        return diagram
    
    def _get_stack_node_id(self, stack_name: str) -> str:
        """Get diagram node ID for stack name."""
        node_map = {
            'DataStack': 'DS',
            'ComputeStack': 'CS',
            'APIStack': 'AS',
            'ApiStack': 'AS',  # Handle both naming conventions
            'FrontendStack': 'FS',
            'LocationStack': 'LS'
        }
        return node_map.get(stack_name, stack_name[:2].upper())
    
    def _generate_stack_architecture(self) -> str:
        """Generate detailed stack architecture documentation."""
        stacks = self.analysis_data['stacks']
        
        content = "### Infrastructure Stacks\n\n"
        
        for stack_name, stack_info in stacks.items():
            content += f"#### {stack_name}\n"
            content += f"**Purpose:** {stack_info['purpose']}\n\n"
            content += f"**Resources:** {stack_info['resource_count']} resources across {len(stack_info['services_used'])} AWS services\n\n"
            
            # List services used
            content += "**AWS Services:**\n"
            for service in sorted(stack_info['services_used']):
                service_resources = [r for r in stack_info['resources'] if r['service'] == service]
                content += f"- **{service}:** {len(service_resources)} resources\n"
            
            # List key resources
            content += "\n**Key Resources:**\n"
            for resource in stack_info['resources'][:5]:  # Show top 5 resources
                content += f"- `{resource['name']}` ({resource['service']} {resource['construct']}) - {resource['purpose']}\n"
            
            if len(stack_info['resources']) > 5:
                content += f"- ... and {len(stack_info['resources']) - 5} more resources\n"
            
            # Show outputs if any
            if stack_info['outputs']:
                content += "\n**Stack Outputs:**\n"
                for output in stack_info['outputs']:
                    content += f"- `{output['name']}`: {output['description']}\n"
            
            content += "\n"
        
        return content
    
    def _generate_service_architecture(self) -> str:
        """Generate service architecture overview."""
        services = self.analysis_data['services']
        
        content = "### AWS Services Usage\n\n"
        
        # Sort services by resource count
        sorted_services = sorted(services.items(), key=lambda x: x[1]['resource_count'], reverse=True)
        
        for service_name, service_info in sorted_services:
            if service_name == 'Unknown':
                continue
                
            content += f"#### {service_name}\n"
            content += f"**Usage:** {service_info['resource_count']} resources across {len(service_info['stacks_used_in'])} stacks\n\n"
            content += f"**Purpose:** {service_info['primary_purpose']}\n\n"
            
            # Show which stacks use this service
            content += f"**Used in Stacks:** {', '.join(service_info['stacks_used_in'])}\n\n"
            
            # Show key resources
            content += "**Key Resources:**\n"
            for resource in service_info['resources'][:3]:  # Show top 3 resources
                content += f"- `{resource['name']}` in {resource['stack']} - {resource['purpose']}\n"
            
            if len(service_info['resources']) > 3:
                content += f"- ... and {len(service_info['resources']) - 3} more\n"
            
            content += "\n"
        
        return content
    
    def _generate_deployment_architecture(self) -> str:
        """Generate deployment architecture documentation."""
        dependencies = self.analysis_data['dependencies']
        
        content = f"""### Deployment Architecture

**Stack Dependencies:** {dependencies['dependency_count']} explicit dependencies

**Deployment Order:**
```
{' → '.join(dependencies['deployment_order'])}
```

#### Dependency Details

"""
        
        for stack, deps in dependencies['dependency_map'].items():
            content += f"**{stack}** depends on:\n"
            for dep in deps:
                content += f"- {dep['depends_on']} ({dep['type']}): {dep['description']}\n"
            content += "\n"
        
        content += """#### Deployment Strategy

1. **Foundation Layer** - Deploy DataStack first to establish storage infrastructure
2. **Processing Layer** - Deploy ComputeStack with Lambda functions and event processing
3. **API Layer** - Deploy APIStack with GraphQL API and authentication
4. **Presentation Layer** - Deploy FrontendStack for web interface
5. **Enhancement Layer** - Deploy LocationStack for geographic features

Each stack can be deployed independently once its dependencies are satisfied, enabling incremental deployments and rollbacks.
"""
        
        return content
    
    def _generate_data_flow_overview(self) -> str:
        """Generate data flow architecture overview."""
        data_flow = self.analysis_data['data_flow']
        
        content = """### Data Flow Architecture

```mermaid
flowchart LR
    subgraph "Data Sources"
        NSW[NSW Government APIs]
    end
    
    subgraph "Ingestion"
        ING[Ingest Lambda]
    end
    
    subgraph "Storage"
        S3R[S3 Raw Data]
        S3C[S3 Curated Data]
        DDB[DynamoDB Hot Aggregates]
    end
    
    subgraph "Processing"
        ETL[ETL Lambda]
        GLUE[Glue Catalog]
    end
    
    subgraph "Query & Analytics"
        ATHENA[Athena]
        APPSYNC[AppSync GraphQL]
    end
    
    subgraph "Presentation"
        WEB[React Frontend]
        MCP[MCP Tools]
    end
    
    NSW --> ING
    ING --> S3R
    S3R --> ETL
    ETL --> S3C
    ETL --> DDB
    S3C --> GLUE
    GLUE --> ATHENA
    DDB --> APPSYNC
    ATHENA --> APPSYNC
    APPSYNC --> WEB
    APPSYNC --> MCP
```

#### Data Flow Components

"""
        
        # Add ingestion sources
        if data_flow['ingestion_sources']:
            content += "**Data Ingestion:**\n"
            for source in data_flow['ingestion_sources']:
                content += f"- `{source['name']}` ({source['service']}) - {source['purpose']}\n"
            content += "\n"
        
        # Add storage layers
        if data_flow['storage_layers']:
            content += "**Storage Layers:**\n"
            for storage in data_flow['storage_layers']:
                content += f"- `{storage['name']}` ({storage['service']}) - {storage['purpose']}\n"
            content += "\n"
        
        # Add processing components
        if data_flow['processing_components']:
            content += "**Processing Components:**\n"
            for processor in data_flow['processing_components']:
                content += f"- `{processor['name']}` ({processor['service']}) - {processor['purpose']}\n"
            content += "\n"
        
        # Add API endpoints
        if data_flow['api_endpoints']:
            content += "**API Endpoints:**\n"
            for api in data_flow['api_endpoints']:
                content += f"- `{api['name']}` ({api['service']}) - {api['purpose']}\n"
            content += "\n"
        
        return content
    
    def _generate_security_overview(self) -> str:
        """Generate security architecture overview."""
        security = self.analysis_data['security']
        
        content = """### Security Architecture

#### Authentication & Authorization
"""
        
        if security['authentication_methods']:
            for auth in security['authentication_methods']:
                content += f"- **{auth['type']}** (`{auth['resource']}`) in {auth['stack']}\n"
        
        content += "\n#### Access Control\n"
        
        if security['iam_roles']:
            content += f"**IAM Roles:** {len(security['iam_roles'])} roles for service access control\n"
            for role in security['iam_roles']:
                content += f"- `{role['name']}` in {role['stack']} - {role['purpose']}\n"
        
        content += "\n#### Data Protection\n"
        
        if security['encryption_enabled']:
            content += f"**Encryption:** {len(security['encryption_enabled'])} resources with encryption enabled\n"
            for encrypted in security['encryption_enabled']:
                content += f"- `{encrypted['resource']}` ({encrypted['service']}) in {encrypted['stack']}\n"
        
        content += "\n#### Permission Grants\n"
        
        if security['access_controls']:
            for control in security['access_controls']:
                permissions_str = ', '.join(control['permissions'])
                content += f"- `{control['resource']}` ({control['service']}): {permissions_str}\n"
        
        return content
    
    def _generate_technology_stack(self) -> str:
        """Generate technology stack documentation."""
        return """### Technology Stack

#### Infrastructure as Code
- **AWS CDK v2+** with Python for infrastructure definitions
- **CloudFormation** for resource provisioning and management

#### Backend Services
- **AWS Lambda** with Python 3.9+ runtime
- **AWS Lambda Powertools** for observability and best practices
- **EventBridge** for event-driven architecture
- **SQS/SNS** for message queuing and notifications

#### Data Services
- **Amazon S3** for raw and curated data storage
- **Amazon DynamoDB** for hot aggregates and fast queries
- **AWS Glue** for data cataloging and ETL jobs
- **Amazon Athena** for ad-hoc SQL queries

#### API & Authentication
- **AWS AppSync** for GraphQL API
- **Amazon Cognito** for user authentication and authorization
- **AWS WAF** for API protection

#### Frontend & Visualization
- **React** with Apollo Client for GraphQL integration
- **AWS Amplify** for hosting and CI/CD
- **Amazon Location Service** for geographic visualization

#### AI/ML & Integration
- **Amazon Bedrock** for natural language processing
- **Model Context Protocol (MCP)** for tool integration
- **GraphQL** for flexible data querying"""
    
    def _generate_resource_summary(self) -> str:
        """Generate resource summary table."""
        overview = self.analysis_data['overview']
        services = self.analysis_data['services']
        
        content = f"""### Resource Summary

| Metric | Count |
|--------|-------|
| Total Stacks | {overview['total_stacks']} |
| Total Services | {overview['total_services']} |
| Total Resources | {overview['total_resources']} |

#### Service Distribution

| AWS Service | Resources | Stacks |
|-------------|-----------|--------|
"""
        
        # Sort services by resource count
        sorted_services = sorted(services.items(), key=lambda x: x[1]['resource_count'], reverse=True)
        
        for service_name, service_info in sorted_services:
            if service_name == 'Unknown':
                continue
            content += f"| {service_name} | {service_info['resource_count']} | {len(service_info['stacks_used_in'])} |\n"
        
        return content


def main():
    """Main function to generate infrastructure overview documentation."""
    generator = OverviewGenerator()
    
    try:
        # Generate overview documentation
        generator.generate_overview_documentation()
        print("Infrastructure overview documentation generated successfully!")
        
    except Exception as e:
        print(f"Error generating overview documentation: {e}")
        raise


if __name__ == "__main__":
    main()