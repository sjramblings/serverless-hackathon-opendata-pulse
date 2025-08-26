"""
Infrastructure Analyzer for OpenData Pulse CDK stacks.

This module provides comprehensive analysis of the CDK infrastructure,
including component relationships, dependencies, and service interactions.
"""

import json
from typing import Dict, List, Any, Tuple
from pathlib import Path
from dataclasses import asdict

from .cdk_parser import CDKStackParser, InfrastructureComponent, StackDependency, ServiceRelationship


class InfrastructureAnalyzer:
    """Comprehensive analyzer for CDK infrastructure components and relationships."""
    
    def __init__(self, infrastructure_path: str = "infrastructure", app_file: str = "app.py"):
        """Initialize analyzer with CDK project paths."""
        self.parser = CDKStackParser(infrastructure_path, app_file)
        self.components = []
        self.stack_dependencies = []
        self.service_relationships = []
        
    def analyze_infrastructure(self) -> Dict[str, Any]:
        """Perform comprehensive infrastructure analysis."""
        # Parse all stacks and relationships
        self.components, self.stack_dependencies, self.service_relationships = self.parser.parse_all_stacks()
        
        # Generate comprehensive analysis
        analysis = {
            'overview': self._generate_overview(),
            'stacks': self._analyze_stacks(),
            'services': self._analyze_services(),
            'dependencies': self._analyze_dependencies(),
            'relationships': self._analyze_relationships(),
            'security': self._analyze_security(),
            'data_flow': self._analyze_data_flow(),
            'naming_conventions': self._analyze_naming_conventions()
        }
        
        return analysis
    
    def _generate_overview(self) -> Dict[str, Any]:
        """Generate high-level infrastructure overview."""
        stack_count = len(set(comp.stack_name for comp in self.components if comp.type == 'stack'))
        service_count = len(set(comp.aws_service for comp in self.components if comp.type == 'resource'))
        resource_count = len([comp for comp in self.components if comp.type == 'resource'])
        
        return {
            'total_stacks': stack_count,
            'total_services': service_count,
            'total_resources': resource_count,
            'architecture_pattern': 'Serverless Multi-Stack',
            'primary_region': 'ap-southeast-2',
            'deployment_model': 'AWS CDK v2'
        }
    
    def _analyze_stacks(self) -> Dict[str, Any]:
        """Analyze individual stacks and their purposes."""
        stacks = {}
        
        for component in self.components:
            if component.type == 'stack':
                stack_resources = [comp for comp in self.components 
                                 if comp.stack_name == component.name and comp.type == 'resource']
                
                services_used = list(set(comp.aws_service for comp in stack_resources))
                
                stacks[component.name] = {
                    'purpose': component.purpose,
                    'file_path': component.file_path,
                    'resource_count': len(stack_resources),
                    'services_used': services_used,
                    'resources': [
                        {
                            'name': comp.name,
                            'service': comp.aws_service,
                            'construct': comp.cdk_construct,
                            'purpose': comp.purpose
                        }
                        for comp in stack_resources
                    ],
                    'outputs': self.parser.stack_outputs.get(component.name, [])
                }
        
        return stacks
    
    def _analyze_services(self) -> Dict[str, Any]:
        """Analyze AWS services usage across stacks."""
        services = {}
        
        for component in self.components:
            if component.type == 'resource':
                service = component.aws_service
                
                if service not in services:
                    services[service] = {
                        'resource_count': 0,
                        'stacks_used_in': set(),
                        'resources': [],
                        'primary_purpose': '',
                        'configurations': []
                    }
                
                services[service]['resource_count'] += 1
                services[service]['stacks_used_in'].add(component.stack_name)
                services[service]['resources'].append({
                    'name': component.name,
                    'stack': component.stack_name,
                    'construct': component.cdk_construct,
                    'purpose': component.purpose
                })
                
                # Extract key configurations
                if component.configuration:
                    services[service]['configurations'].append({
                        'resource': component.name,
                        'config': component.configuration
                    })
        
        # Convert sets to lists for JSON serialization
        for service_data in services.values():
            service_data['stacks_used_in'] = list(service_data['stacks_used_in'])
            service_data['primary_purpose'] = self._infer_service_purpose(service_data['resources'])
        
        return services
    
    def _analyze_dependencies(self) -> Dict[str, Any]:
        """Analyze stack dependencies and deployment order."""
        dependency_map = {}
        deployment_order = []
        
        # Build dependency map
        for dep in self.stack_dependencies:
            if dep.source_stack not in dependency_map:
                dependency_map[dep.source_stack] = []
            dependency_map[dep.source_stack].append({
                'depends_on': dep.target_stack,
                'type': dep.dependency_type,
                'description': dep.description
            })
        
        # Calculate deployment order using topological sort
        deployment_order = self._calculate_deployment_order(dependency_map)
        
        return {
            'dependency_map': dependency_map,
            'deployment_order': deployment_order,
            'dependency_count': len(self.stack_dependencies)
        }
    
    def _analyze_relationships(self) -> Dict[str, Any]:
        """Analyze service-to-service relationships."""
        relationships = {}
        
        for rel in self.service_relationships:
            key = f"{rel.source_service}_to_{rel.target_service}"
            
            if key not in relationships:
                relationships[key] = {
                    'source_service': rel.source_service,
                    'target_service': rel.target_service,
                    'relationship_types': set(),
                    'interactions': []
                }
            
            relationships[key]['relationship_types'].add(rel.relationship_type)
            relationships[key]['interactions'].append({
                'type': rel.relationship_type,
                'source_component': rel.source_component,
                'target_component': rel.target_component,
                'description': rel.description
            })
        
        # Convert sets to lists for JSON serialization
        for rel_data in relationships.values():
            rel_data['relationship_types'] = list(rel_data['relationship_types'])
        
        return relationships
    
    def _analyze_security(self) -> Dict[str, Any]:
        """Analyze security configurations and IAM permissions."""
        security_analysis = {
            'iam_roles': [],
            'encryption_enabled': [],
            'access_controls': [],
            'authentication_methods': []
        }
        
        for component in self.components:
            if component.aws_service == 'IAM':
                security_analysis['iam_roles'].append({
                    'name': component.name,
                    'stack': component.stack_name,
                    'purpose': component.purpose
                })
            
            # Check for encryption configurations
            if 'encryption' in str(component.configuration).lower():
                security_analysis['encryption_enabled'].append({
                    'resource': component.name,
                    'service': component.aws_service,
                    'stack': component.stack_name
                })
            
            # Check for Cognito authentication
            if component.aws_service == 'Cognito':
                security_analysis['authentication_methods'].append({
                    'resource': component.name,
                    'type': component.cdk_construct,
                    'stack': component.stack_name
                })
            
            # Collect permission grants
            if component.permissions:
                security_analysis['access_controls'].append({
                    'resource': component.name,
                    'service': component.aws_service,
                    'permissions': component.permissions,
                    'stack': component.stack_name
                })
        
        return security_analysis
    
    def _analyze_data_flow(self) -> Dict[str, Any]:
        """Analyze data flow patterns through the infrastructure."""
        data_flow = {
            'ingestion_sources': [],
            'storage_layers': [],
            'processing_components': [],
            'api_endpoints': [],
            'data_transformations': []
        }
        
        for component in self.components:
            # Identify data ingestion sources
            if 'ingest' in component.name.lower() or 'api' in component.purpose.lower():
                data_flow['ingestion_sources'].append({
                    'name': component.name,
                    'service': component.aws_service,
                    'purpose': component.purpose,
                    'stack': component.stack_name
                })
            
            # Identify storage layers
            elif component.aws_service in ['S3', 'DynamoDB']:
                data_flow['storage_layers'].append({
                    'name': component.name,
                    'service': component.aws_service,
                    'purpose': component.purpose,
                    'stack': component.stack_name
                })
            
            # Identify processing components
            elif component.aws_service in ['Lambda', 'Glue']:
                data_flow['processing_components'].append({
                    'name': component.name,
                    'service': component.aws_service,
                    'purpose': component.purpose,
                    'stack': component.stack_name
                })
            
            # Identify API endpoints
            elif component.aws_service in ['AppSync', 'API Gateway']:
                data_flow['api_endpoints'].append({
                    'name': component.name,
                    'service': component.aws_service,
                    'purpose': component.purpose,
                    'stack': component.stack_name
                })
        
        return data_flow
    
    def _analyze_naming_conventions(self) -> Dict[str, Any]:
        """Analyze resource naming conventions and patterns."""
        naming_analysis = {
            'patterns': {},
            'prefixes': set(),
            'suffixes': set(),
            'conventions': []
        }
        
        for component in self.components:
            if component.type == 'resource':
                name = component.name.lower()
                
                # Extract prefixes and suffixes
                parts = name.split('_')
                if len(parts) > 1:
                    naming_analysis['prefixes'].add(parts[0])
                    naming_analysis['suffixes'].add(parts[-1])
                
                # Analyze service-specific patterns
                service = component.aws_service
                if service not in naming_analysis['patterns']:
                    naming_analysis['patterns'][service] = []
                
                naming_analysis['patterns'][service].append({
                    'name': component.name,
                    'construct': component.cdk_construct,
                    'stack': component.stack_name
                })
        
        # Convert sets to lists
        naming_analysis['prefixes'] = list(naming_analysis['prefixes'])
        naming_analysis['suffixes'] = list(naming_analysis['suffixes'])
        
        # Generate naming conventions
        naming_analysis['conventions'] = [
            "Resources use descriptive names indicating their purpose",
            "Stack names follow OpenDataPulse{Purpose}Stack pattern",
            "S3 buckets include account ID for global uniqueness",
            "Lambda functions use {Purpose}Function naming pattern",
            "DynamoDB tables use kebab-case naming"
        ]
        
        return naming_analysis
    
    def _infer_service_purpose(self, resources: List[Dict[str, str]]) -> str:
        """Infer the primary purpose of a service based on its resources."""
        purposes = [res['purpose'] for res in resources]
        
        if any('storage' in purpose.lower() for purpose in purposes):
            return "Data storage and management"
        elif any('compute' in purpose.lower() or 'function' in purpose.lower() for purpose in purposes):
            return "Serverless compute and processing"
        elif any('api' in purpose.lower() or 'auth' in purpose.lower() for purpose in purposes):
            return "API and authentication services"
        elif any('map' in purpose.lower() or 'location' in purpose.lower() for purpose in purposes):
            return "Geographic and location services"
        else:
            return "Infrastructure services"
    
    def _calculate_deployment_order(self, dependency_map: Dict[str, List[Dict[str, str]]]) -> List[str]:
        """Calculate optimal deployment order using topological sort."""
        # Simple topological sort implementation
        all_stacks = set()
        dependencies = {}
        
        # Collect all stacks and their dependencies
        for stack, deps in dependency_map.items():
            all_stacks.add(stack)
            dependencies[stack] = [dep['depends_on'] for dep in deps]
            for dep in deps:
                all_stacks.add(dep['depends_on'])
        
        # Add stacks with no dependencies
        for stack in all_stacks:
            if stack not in dependencies:
                dependencies[stack] = []
        
        # Topological sort
        result = []
        visited = set()
        temp_visited = set()
        
        def visit(stack):
            if stack in temp_visited:
                return  # Circular dependency detected
            if stack in visited:
                return
            
            temp_visited.add(stack)
            for dep in dependencies.get(stack, []):
                visit(dep)
            temp_visited.remove(stack)
            visited.add(stack)
            result.append(stack)
        
        for stack in all_stacks:
            if stack not in visited:
                visit(stack)
        
        return result
    
    def export_analysis(self, output_path: str = "docs/infrastructure_analysis.json") -> None:
        """Export analysis results to JSON file."""
        analysis = self.analyze_infrastructure()
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2, default=str)
        
        print(f"Infrastructure analysis exported to {output_file}")
    
    def get_component_relationships(self, component_name: str) -> Dict[str, List[str]]:
        """Get all relationships for a specific component."""
        relationships = {
            'depends_on': [],
            'depended_by': [],
            'interacts_with': []
        }
        
        # Find component
        component = None
        for comp in self.components:
            if comp.name == component_name:
                component = comp
                break
        
        if not component:
            return relationships
        
        # Find stack dependencies
        for dep in self.stack_dependencies:
            if dep.source_stack == component.stack_name:
                relationships['depends_on'].append(dep.target_stack)
            elif dep.target_stack == component.stack_name:
                relationships['depended_by'].append(dep.source_stack)
        
        # Find service relationships
        for rel in self.service_relationships:
            if rel.source_component == component_name:
                relationships['interacts_with'].append(f"{rel.target_component} ({rel.relationship_type})")
            elif rel.target_component == component_name:
                relationships['interacts_with'].append(f"{rel.source_component} ({rel.relationship_type})")
        
        return relationships


def main():
    """Main function to run infrastructure analysis."""
    analyzer = InfrastructureAnalyzer()
    
    try:
        # Perform analysis
        analysis = analyzer.analyze_infrastructure()
        
        # Export results
        analyzer.export_analysis()
        
        # Print summary
        print("\n=== Infrastructure Analysis Summary ===")
        print(f"Total Stacks: {analysis['overview']['total_stacks']}")
        print(f"Total Services: {analysis['overview']['total_services']}")
        print(f"Total Resources: {analysis['overview']['total_resources']}")
        print(f"Architecture Pattern: {analysis['overview']['architecture_pattern']}")
        
        print("\n=== Stack Overview ===")
        for stack_name, stack_info in analysis['stacks'].items():
            print(f"- {stack_name}: {stack_info['resource_count']} resources, {len(stack_info['services_used'])} services")
        
        print("\n=== Service Usage ===")
        for service_name, service_info in analysis['services'].items():
            print(f"- {service_name}: {service_info['resource_count']} resources across {len(service_info['stacks_used_in'])} stacks")
        
        print(f"\nDeployment Order: {' -> '.join(analysis['dependencies']['deployment_order'])}")
        
    except Exception as e:
        print(f"Error during analysis: {e}")
        raise


if __name__ == "__main__":
    main()