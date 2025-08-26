"""
Service Dependency Documentation Generator.

This module generates comprehensive service dependency documentation
with Mermaid diagrams showing cross-stack relationships and service interactions.
"""

from typing import Dict, List, Any, Set, Tuple
from datetime import datetime
from pathlib import Path
import re

from .infrastructure_analyzer import InfrastructureAnalyzer


class DependencyGenerator:
    """Generator for service dependency documentation."""
    
    def __init__(self, analyzer: InfrastructureAnalyzer = None):
        """Initialize with infrastructure analyzer."""
        self.analyzer = analyzer or InfrastructureAnalyzer()
        self.analysis_data = None
    
    def generate_dependency_documentation(self, output_path: str = "docs/architecture/service-dependencies.md") -> None:
        """Generate comprehensive service dependency documentation."""
        # Get analysis data
        self.analysis_data = self.analyzer.analyze_infrastructure()
        
        # Generate documentation content
        content = self._generate_dependency_content()
        
        # Write to file
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"Service dependency documentation generated: {output_file}")
    
    def _generate_dependency_content(self) -> str:
        """Generate the complete dependency documentation content."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        content = f"""# Service Dependencies

*Comprehensive mapping of service interactions, dependencies, and resource relationships within the OpenData Pulse system.*

**Last Updated:** {timestamp}  
**Generated from:** CDK stack definitions and infrastructure analysis

## Overview

{self._generate_dependency_overview()}

## Cross-Stack Dependencies

{self._generate_cross_stack_dependencies()}

## Service Interaction Map

{self._generate_service_interaction_map()}

## Resource Dependencies

{self._generate_resource_dependencies()}

## Data Flow Dependencies

{self._generate_data_flow_dependencies()}

## Naming Conventions

{self._generate_naming_conventions()}

## Dependency Matrix

{self._generate_dependency_matrix()}

## Impact Analysis

{self._generate_impact_analysis()}

---

*This documentation is automatically generated from CDK stack definitions and updated with infrastructure changes.*
"""
        return content
    
    def _generate_dependency_overview(self) -> str:
        """Generate dependency overview with statistics."""
        dependencies = self.analysis_data['dependencies']
        relationships = self.analysis_data['relationships']
        
        return f"""The OpenData Pulse system consists of {len(self.analysis_data['stacks'])} interconnected CDK stacks with {dependencies['dependency_count']} explicit dependencies and {len(relationships)} service relationships.

### Dependency Statistics
- **Stack Dependencies:** {dependencies['dependency_count']} explicit cross-stack dependencies
- **Service Relationships:** {len(relationships)} inter-service relationships
- **Deployment Phases:** {len(set(self._get_deployment_phase(stack) for stack in dependencies['deployment_order']))} deployment phases
- **Critical Path:** {' → '.join(dependencies['deployment_order'])}

### Architecture Characteristics
- **Layered Architecture:** Clear separation between data, compute, API, and presentation layers
- **Loose Coupling:** Services communicate through well-defined interfaces
- **High Cohesion:** Related functionality grouped within appropriate stacks
- **Dependency Direction:** Dependencies flow upward through architectural layers"""
    
    def _get_deployment_phase(self, stack_name: str) -> int:
        """Get deployment phase number for a stack."""
        phase_map = {
            'DataStack': 1,
            'ComputeStack': 2,
            'LocationStack': 2,
            'APIStack': 3,
            'ApiStack': 3,
            'FrontendStack': 4
        }
        return phase_map.get(stack_name, 0)
    
    def _generate_cross_stack_dependencies(self) -> str:
        """Generate detailed cross-stack dependency documentation."""
        stacks = self.analysis_data['stacks']
        dependencies = self.analysis_data['dependencies']['dependency_map']
        
        content = """### Stack Dependency Diagram

```mermaid
graph TD
    subgraph "Dependency Layers"
        subgraph "Layer 1: Foundation"
            DS[DataStack<br/>Storage & Analytics Foundation]
        end
        
        subgraph "Layer 2: Processing & Location"
            CS[ComputeStack<br/>Lambda Functions & Events]
            LS[LocationStack<br/>Geographic Services]
        end
        
        subgraph "Layer 3: API & Authentication"
            AS[APIStack<br/>GraphQL API & Cognito]
        end
        
        subgraph "Layer 4: Presentation"
            FS[FrontendStack<br/>Web Interface & CDN]
        end
    end
    
    %% Dependencies with descriptions
    DS -->|Provides Storage| CS
    DS -->|Provides Data Access| AS
    DS -->|Provides Geographic Data| LS
    CS -->|Provides Health Checks| AS
    AS -->|Provides API & Auth| FS
    
    %% External dependencies
    NSW[NSW Government APIs] -.->|Data Source| CS
    Users[End Users] -.->|Access| FS
    MCP[MCP Clients] -.->|API Access| AS
```

### Detailed Stack Dependencies

"""
        
        # Generate detailed dependency information for each stack
        for stack_name, stack_info in stacks.items():
            content += f"#### {stack_name}\n\n"
            content += f"**Purpose:** {stack_info['purpose']}\n\n"
            
            # Dependencies (what this stack depends on)
            stack_deps = dependencies.get(stack_name, [])
            if stack_deps:
                content += "**Dependencies:**\n"
                for dep in stack_deps:
                    content += f"- **{dep['depends_on']}** ({dep['type']}): {dep['description']}\n"
            else:
                content += "**Dependencies:** None (foundation layer)\n"
            
            # Dependents (what depends on this stack)
            dependents = []
            for other_stack, other_deps in dependencies.items():
                for dep in other_deps:
                    if dep['depends_on'] == stack_name:
                        dependents.append(other_stack)
            
            if dependents:
                content += f"\n**Consumed by:** {', '.join(dependents)}\n"
            else:
                content += "\n**Consumed by:** None (top layer)\n"
            
            # Resources provided
            content += f"\n**Provides:**\n"
            services_provided = {}
            for resource in stack_info['resources']:
                service = resource['service']
                if service not in services_provided:
                    services_provided[service] = []
                services_provided[service].append(resource['name'])
            
            for service, resources in services_provided.items():
                content += f"- **{service}:** {', '.join(resources[:3])}"
                if len(resources) > 3:
                    content += f" (and {len(resources) - 3} more)"
                content += "\n"
            
            content += "\n"
        
        return content
    
    def _generate_service_interaction_map(self) -> str:
        """Generate service interaction mapping."""
        relationships = self.analysis_data['relationships']
        services = self.analysis_data['services']
        
        content = """### Service Interaction Diagram

```mermaid
graph LR
    subgraph "Data Services"
        S3[Amazon S3<br/>Raw & Curated Storage]
        DDB[DynamoDB<br/>Hot Aggregates]
        Glue[AWS Glue<br/>Data Catalog]
        Athena[Amazon Athena<br/>SQL Analytics]
    end
    
    subgraph "Compute Services"
        Lambda[AWS Lambda<br/>Serverless Functions]
        EventBridge[Amazon EventBridge<br/>Event Scheduling]
        SQS[Amazon SQS<br/>Message Queuing]
        SNS[Amazon SNS<br/>Notifications]
    end
    
    subgraph "API Services"
        AppSync[AWS AppSync<br/>GraphQL API]
        Cognito[Amazon Cognito<br/>Authentication]
        WAF[AWS WAF<br/>Web Protection]
        IAM[AWS IAM<br/>Access Control]
    end
    
    subgraph "Frontend Services"
        Amplify[AWS Amplify<br/>Web Hosting]
        LocationService[Amazon Location Service<br/>Maps & Geocoding]
    end
    
    %% Service Interactions
    EventBridge -->|triggers| Lambda
    Lambda -->|stores_in| S3
    Lambda -->|stores_in| DDB
    Lambda -->|sends| SNS
    Lambda -.->|failures| SQS
    
    S3 -->|catalogs| Glue
    Glue -->|enables| Athena
    
    AppSync -->|reads_from| DDB
    AppSync -->|queries| Athena
    Cognito -->|authenticates| AppSync
    WAF -->|protects| AppSync
    IAM -->|authorizes| AppSync
    
    Amplify -->|calls| AppSync
    Amplify -->|uses| LocationService
```

### Service Relationship Details

"""
        
        # Group relationships by type
        relationship_types = {}
        for rel_key, rel_info in relationships.items():
            for interaction in rel_info['interactions']:
                rel_type = interaction['type']
                if rel_type not in relationship_types:
                    relationship_types[rel_type] = []
                relationship_types[rel_type].append({
                    'source': rel_info['source_service'],
                    'target': rel_info['target_service'],
                    'source_component': interaction['source_component'],
                    'target_component': interaction['target_component'],
                    'description': interaction['description']
                })
        
        for rel_type, interactions in relationship_types.items():
            content += f"#### {rel_type.replace('_', ' ').title()} Relationships\n\n"
            for interaction in interactions:
                content += f"- **{interaction['source']}** {rel_type} **{interaction['target']}**\n"
                content += f"  - Source: `{interaction['source_component']}`\n"
                content += f"  - Target: `{interaction['target_component']}`\n"
                content += f"  - Description: {interaction['description']}\n\n"
        
        return content
    
    def _generate_resource_dependencies(self) -> str:
        """Generate resource-level dependency documentation."""
        stacks = self.analysis_data['stacks']
        
        content = """### Resource Dependencies

#### Critical Resource Dependencies

"""
        
        # Identify critical resources and their dependencies
        critical_resources = self._identify_critical_resources()
        
        for resource_info in critical_resources:
            content += f"##### {resource_info['name']} ({resource_info['service']})\n\n"
            content += f"**Stack:** {resource_info['stack']}\n"
            content += f"**Purpose:** {resource_info['purpose']}\n"
            
            if resource_info['dependencies']:
                content += f"**Dependencies:** {', '.join(resource_info['dependencies'])}\n"
            
            if resource_info['dependents']:
                content += f"**Used by:** {', '.join(resource_info['dependents'])}\n"
            
            content += "\n"
        
        return content
    
    def _identify_critical_resources(self) -> List[Dict[str, Any]]:
        """Identify critical resources that have multiple dependencies."""
        stacks = self.analysis_data['stacks']
        critical_resources = []
        
        # Define critical resource patterns
        critical_patterns = ['bucket', 'table', 'api', 'function', 'pool']
        
        for stack_name, stack_info in stacks.items():
            for resource in stack_info['resources']:
                resource_name_lower = resource['name'].lower()
                
                if any(pattern in resource_name_lower for pattern in critical_patterns):
                    critical_resources.append({
                        'name': resource['name'],
                        'service': resource['service'],
                        'stack': stack_name,
                        'purpose': resource['purpose'],
                        'dependencies': self._get_resource_dependencies(resource),
                        'dependents': self._get_resource_dependents(resource)
                    })
        
        return critical_resources[:10]  # Return top 10 critical resources
    
    def _get_resource_dependencies(self, resource: Dict[str, str]) -> List[str]:
        """Get dependencies for a specific resource."""
        # This would analyze the resource configuration to find dependencies
        # For now, return empty list as placeholder
        return []
    
    def _get_resource_dependents(self, resource: Dict[str, str]) -> List[str]:
        """Get what depends on a specific resource."""
        # This would analyze cross-references to find dependents
        # For now, return empty list as placeholder
        return []
    
    def _generate_data_flow_dependencies(self) -> str:
        """Generate data flow dependency documentation."""
        data_flow = self.analysis_data['data_flow']
        
        content = """### Data Flow Dependencies

```mermaid
flowchart TD
    subgraph "Data Sources"
        NSW[NSW Government APIs]
    end
    
    subgraph "Ingestion Dependencies"
        Schedule[EventBridge Schedule] -->|triggers| IngestLambda[Ingest Lambda]
        IngestLambda -->|requires| S3Raw[S3 Raw Bucket]
        IngestLambda -.->|on failure| DLQ[SQS Dead Letter Queue]
    end
    
    subgraph "Processing Dependencies"
        S3Raw -->|triggers| ETLLambda[ETL Lambda]
        ETLLambda -->|requires| S3Curated[S3 Curated Bucket]
        ETLLambda -->|requires| DynamoDB[DynamoDB Table]
        ETLLambda -->|updates| GlueCatalog[Glue Catalog]
    end
    
    subgraph "Query Dependencies"
        DynamoDB -->|serves| AppSync[AppSync API]
        GlueCatalog -->|enables| Athena[Athena Queries]
        Athena -->|serves| AppSync
        S3Curated -->|stores results| S3Exports[S3 Exports]
    end
    
    subgraph "Presentation Dependencies"
        AppSync -->|serves| ReactApp[React Frontend]
        AppSync -->|serves| MCPTools[MCP Tools]
        LocationService[Location Service] -->|serves| ReactApp
    end
    
    NSW -->|data source| IngestLambda
```

#### Data Flow Stages

"""
        
        # Document each data flow stage
        stages = [
            {
                'name': 'Data Ingestion',
                'components': data_flow['ingestion_sources'],
                'dependencies': ['NSW Government APIs', 'EventBridge scheduling', 'S3 raw storage']
            },
            {
                'name': 'Data Processing',
                'components': data_flow['processing_components'],
                'dependencies': ['S3 raw data', 'Lambda execution environment', 'DynamoDB tables']
            },
            {
                'name': 'Data Storage',
                'components': data_flow['storage_layers'],
                'dependencies': ['Processed data', 'Glue catalog', 'Athena workgroup']
            },
            {
                'name': 'Data Access',
                'components': data_flow['api_endpoints'],
                'dependencies': ['Stored data', 'Authentication services', 'Authorization policies']
            }
        ]
        
        for stage in stages:
            content += f"##### {stage['name']}\n\n"
            content += f"**Dependencies:** {', '.join(stage['dependencies'])}\n\n"
            
            if stage['components']:
                content += "**Components:**\n"
                for component in stage['components']:
                    content += f"- `{component['name']}` ({component['service']}) - {component['purpose']}\n"
            
            content += "\n"
        
        return content
    
    def _generate_naming_conventions(self) -> str:
        """Generate naming convention documentation with examples."""
        naming = self.analysis_data['naming_conventions']
        stacks = self.analysis_data['stacks']
        
        content = """### Resource Naming Conventions

#### Naming Patterns

"""
        
        # Document naming conventions
        for convention in naming['conventions']:
            content += f"- {convention}\n"
        
        content += "\n#### Naming Examples by Service\n\n"
        
        # Show examples for each service
        for service, patterns in naming['patterns'].items():
            if service == 'Unknown':
                continue
                
            content += f"##### {service}\n\n"
            
            # Show up to 3 examples per service
            for pattern in patterns[:3]:
                content += f"- `{pattern['name']}` ({pattern['construct']}) in {pattern['stack']}\n"
            
            if len(patterns) > 3:
                content += f"- ... and {len(patterns) - 3} more resources\n"
            
            content += "\n"
        
        content += """#### Naming Convention Rules

1. **Prefix Pattern:** All resources use `opendata-pulse-` prefix
2. **Account ID Suffix:** S3 buckets include account ID for global uniqueness
3. **Descriptive Names:** Resource names clearly indicate their purpose
4. **Consistent Casing:** Use kebab-case for most resources, PascalCase for CDK constructs
5. **Stack Grouping:** Related resources grouped within appropriate stacks

#### Examples by Resource Type

| Resource Type | Pattern | Example |
|---------------|---------|---------|
| S3 Bucket | `opendata-pulse-{purpose}-{account-id}` | `opendata-pulse-raw-data-123456789012` |
| DynamoDB Table | `opendata-pulse-{purpose}` | `opendata-pulse-air-quality` |
| Lambda Function | `{Purpose}Function` | `DataIngestFunction` |
| IAM Role | `{Purpose}Role` | `LambdaExecutionRole` |
| EventBridge Rule | `{Purpose}Rule` | `DataIngestionRule` |
"""
        
        return content
    
    def _generate_dependency_matrix(self) -> str:
        """Generate dependency matrix table."""
        stacks = list(self.analysis_data['stacks'].keys())
        dependencies = self.analysis_data['dependencies']['dependency_map']
        
        content = """### Stack Dependency Matrix

| Stack | DataStack | ComputeStack | APIStack | FrontendStack | LocationStack |
|-------|-----------|--------------|----------|---------------|---------------|
"""
        
        for stack in stacks:
            row = f"| {stack} |"
            
            for target_stack in stacks:
                if stack == target_stack:
                    row += " - |"
                elif target_stack in [dep['depends_on'] for dep in dependencies.get(stack, [])]:
                    row += " ✓ |"
                else:
                    row += " - |"
            
            content += row + "\n"
        
        content += """
**Legend:**
- ✓ = Direct dependency
- - = No dependency

**Reading the Matrix:**
- Rows represent dependent stacks
- Columns represent dependency targets
- ✓ indicates that the row stack depends on the column stack
"""
        
        return content
    
    def _generate_impact_analysis(self) -> str:
        """Generate impact analysis documentation."""
        dependencies = self.analysis_data['dependencies']
        stacks = self.analysis_data['stacks']
        
        content = """### Impact Analysis

#### Change Impact Assessment

Understanding the impact of changes to each stack:

"""
        
        # Analyze impact for each stack
        for stack_name, stack_info in stacks.items():
            content += f"##### {stack_name} Changes\n\n"
            
            # Find what depends on this stack
            dependents = []
            for other_stack, deps in dependencies['dependency_map'].items():
                for dep in deps:
                    if dep['depends_on'] == stack_name:
                        dependents.append(other_stack)
            
            if dependents:
                content += f"**Direct Impact:** {', '.join(dependents)}\n"
                
                # Calculate cascading impact
                cascading_impact = set()
                for dependent in dependents:
                    cascading_impact.update(self._get_cascading_dependents(dependent, dependencies['dependency_map']))
                
                if cascading_impact:
                    content += f"**Cascading Impact:** {', '.join(cascading_impact)}\n"
                
                content += f"**Risk Level:** {'High' if len(dependents) > 2 else 'Medium' if len(dependents) > 0 else 'Low'}\n"
            else:
                content += "**Direct Impact:** None (leaf stack)\n"
                content += "**Risk Level:** Low\n"
            
            content += "\n"
        
        content += """#### Deployment Risk Assessment

**High Risk Changes:**
- DataStack modifications (affects all other stacks)
- Breaking changes to GraphQL schema in APIStack
- Authentication changes in Cognito configuration

**Medium Risk Changes:**
- Lambda function updates in ComputeStack
- New API endpoints in APIStack
- Frontend deployment in FrontendStack

**Low Risk Changes:**
- LocationStack updates (isolated geographic features)
- Non-breaking schema additions
- Configuration parameter updates

#### Rollback Considerations

**Rollback Order:** Reverse of deployment order
1. FrontendStack (lowest risk)
2. APIStack (medium risk - may affect active users)
3. ComputeStack & LocationStack (medium risk - may affect data processing)
4. DataStack (highest risk - data retention policies apply)

**Data Considerations:**
- S3 buckets have retention policies preventing accidental deletion
- DynamoDB tables use point-in-time recovery
- Lambda functions support blue/green deployments
"""
        
        return content
    
    def _get_cascading_dependents(self, stack: str, dependency_map: Dict[str, List[Dict[str, str]]]) -> Set[str]:
        """Get all stacks that transitively depend on the given stack."""
        cascading = set()
        
        for other_stack, deps in dependency_map.items():
            for dep in deps:
                if dep['depends_on'] == stack:
                    cascading.add(other_stack)
                    cascading.update(self._get_cascading_dependents(other_stack, dependency_map))
        
        return cascading


def main():
    """Main function to generate service dependency documentation."""
    generator = DependencyGenerator()
    
    try:
        # Generate dependency documentation
        generator.generate_dependency_documentation()
        print("Service dependency documentation generated successfully!")
        
    except Exception as e:
        print(f"Error generating dependency documentation: {e}")
        raise


if __name__ == "__main__":
    main()