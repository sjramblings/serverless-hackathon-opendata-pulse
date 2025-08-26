"""
CDK Stack Parser for extracting infrastructure component information.

This module provides utilities to parse CDK stack definitions and extract
AWS service configurations, dependencies, and resource information.
"""

import ast
import os
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Any, Tuple
from pathlib import Path


@dataclass
class InfrastructureComponent:
    """Represents an AWS infrastructure component from CDK stacks."""
    
    id: str
    name: str
    type: str  # 'stack', 'service', 'resource'
    aws_service: str
    cdk_construct: str
    purpose: str
    dependencies: List[str] = field(default_factory=list)
    configuration: Dict[str, Any] = field(default_factory=dict)
    stack_name: str = ""
    file_path: str = ""
    line_number: int = 0
    outputs: List[str] = field(default_factory=list)
    environment_variables: Dict[str, str] = field(default_factory=dict)
    permissions: List[str] = field(default_factory=list)


@dataclass
class StackDependency:
    """Represents a dependency relationship between stacks."""
    
    source_stack: str
    target_stack: str
    dependency_type: str  # 'explicit', 'resource_reference', 'output_import'
    description: str = ""


@dataclass
class ServiceRelationship:
    """Represents a relationship between AWS services."""
    
    source_service: str
    target_service: str
    relationship_type: str  # 'triggers', 'stores_in', 'reads_from', 'authenticates_with'
    source_component: str = ""
    target_component: str = ""
    description: str = ""


class CDKStackParser:
    """Parser for CDK stack files to extract infrastructure components."""
    
    def __init__(self, infrastructure_path: str = "infrastructure", app_file: str = "app.py"):
        """Initialize parser with path to CDK infrastructure directory."""
        self.infrastructure_path = Path(infrastructure_path)
        self.app_file = Path(app_file)
        self.components: List[InfrastructureComponent] = []
        self.stack_dependencies: List[StackDependency] = []
        self.service_relationships: List[ServiceRelationship] = []
        self.stack_outputs: Dict[str, List[str]] = {}
        
    def parse_all_stacks(self) -> Tuple[List[InfrastructureComponent], List[StackDependency], List[ServiceRelationship]]:
        """Parse all CDK stack files and return infrastructure components, dependencies, and relationships."""
        if not self.infrastructure_path.exists():
            raise FileNotFoundError(f"Infrastructure directory not found: {self.infrastructure_path}")
            
        # Parse the main app.py file first to understand stack dependencies
        if self.app_file.exists():
            self._parse_app_file()
            
        stack_files = list(self.infrastructure_path.glob("*_stack.py"))
        
        for stack_file in stack_files:
            try:
                self._parse_stack_file(stack_file)
            except Exception as e:
                print(f"Warning: Failed to parse {stack_file}: {e}")
        
        # Analyze service relationships after parsing all stacks
        self._analyze_service_relationships()
                
        return self.components, self.stack_dependencies, self.service_relationships
    
    def _parse_stack_file(self, file_path: Path) -> None:
        """Parse a single CDK stack file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        try:
            tree = ast.parse(content)
            stack_name = self._extract_stack_name(file_path.name)
            
            # Extract imports to understand CDK constructs
            imports = self._extract_imports(tree)
            
            # Find stack class definition
            stack_class = self._find_stack_class(tree)
            if stack_class:
                self._parse_stack_class(stack_class, stack_name, file_path, imports)
                
        except SyntaxError as e:
            print(f"Syntax error in {file_path}: {e}")
    
    def _extract_stack_name(self, filename: str) -> str:
        """Extract stack name from filename."""
        # Convert data_stack.py -> DataStack
        base_name = filename.replace('.py', '').replace('_', ' ').title().replace(' ', '')
        return base_name
    
    def _extract_imports(self, tree: ast.AST) -> Dict[str, str]:
        """Extract import statements to map construct names to AWS services."""
        imports = {}
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module and 'aws_cdk' in node.module:
                    for alias in node.names:
                        construct_name = alias.asname or alias.name
                        # Map CDK module to AWS service
                        aws_service = self._map_cdk_module_to_service(node.module)
                        imports[construct_name] = aws_service
                        
        return imports
    
    def _map_cdk_module_to_service(self, module_name: str) -> str:
        """Map CDK module names to AWS service names."""
        service_mapping = {
            'aws_s3': 'S3',
            'aws_dynamodb': 'DynamoDB', 
            'aws_lambda': 'Lambda',
            '_lambda': 'Lambda',  # Handle underscore prefix
            'aws_apigateway': 'API Gateway',
            'aws_appsync': 'AppSync',
            'aws_cognito': 'Cognito',
            'aws_events': 'EventBridge',
            'aws_sqs': 'SQS',
            'aws_sns': 'SNS',
            'aws_glue': 'Glue',
            'aws_athena': 'Athena',
            'aws_amplify': 'Amplify',
            'aws_cloudfront': 'CloudFront',
            'aws_location': 'Location Service',
            'aws_iam': 'IAM',
            'aws_wafv2': 'WAF',
            'aws_ec2': 'EC2',
            'aws_logs': 'CloudWatch Logs'
        }
        
        for cdk_module, service in service_mapping.items():
            if cdk_module in module_name:
                return service
        
        # Try to infer from construct names if module mapping fails
        if 's3' in module_name.lower():
            return 'S3'
        elif 'lambda' in module_name.lower():
            return 'Lambda'
        elif 'dynamo' in module_name.lower():
            return 'DynamoDB'
        elif 'cognito' in module_name.lower():
            return 'Cognito'
        elif 'appsync' in module_name.lower():
            return 'AppSync'
        elif 'location' in module_name.lower():
            return 'Location Service'
        elif 'amplify' in module_name.lower():
            return 'Amplify'
                
        return 'Unknown'
    
    def _find_stack_class(self, tree: ast.AST) -> Optional[ast.ClassDef]:
        """Find the main stack class definition."""
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Look for classes that inherit from Stack
                for base in node.bases:
                    if isinstance(base, ast.Name) and base.id == 'Stack':
                        return node
                    elif isinstance(base, ast.Attribute) and base.attr == 'Stack':
                        return node
        return None
    
    def _parse_stack_class(self, stack_class: ast.ClassDef, stack_name: str, 
                          file_path: Path, imports: Dict[str, str]) -> None:
        """Parse stack class to extract components."""
        
        # Create stack component
        stack_component = InfrastructureComponent(
            id=f"stack_{stack_name.lower()}",
            name=stack_name,
            type="stack",
            aws_service="CloudFormation",
            cdk_construct="Stack",
            purpose=self._extract_stack_purpose(stack_class),
            stack_name=stack_name,
            file_path=str(file_path),
            line_number=stack_class.lineno
        )
        self.components.append(stack_component)
        
        # Parse constructor to find resource definitions
        init_method = self._find_init_method(stack_class)
        if init_method:
            self._parse_init_method(init_method, stack_name, file_path, imports)
    
    def _extract_stack_purpose(self, stack_class: ast.ClassDef) -> str:
        """Extract stack purpose from docstring or class name."""
        if ast.get_docstring(stack_class):
            return ast.get_docstring(stack_class).split('\n')[0]
        
        # Infer purpose from class name
        name_lower = stack_class.name.lower()
        if 'data' in name_lower:
            return "Data storage and management services"
        elif 'compute' in name_lower:
            return "Compute and processing services"
        elif 'api' in name_lower:
            return "API and authentication services"
        elif 'frontend' in name_lower:
            return "Frontend hosting and distribution"
        elif 'location' in name_lower:
            return "Geographic and location services"
        else:
            return "AWS infrastructure stack"
    
    def _find_init_method(self, stack_class: ast.ClassDef) -> Optional[ast.FunctionDef]:
        """Find the __init__ method of the stack class."""
        for node in stack_class.body:
            if isinstance(node, ast.FunctionDef) and node.name == '__init__':
                return node
        return None
    
    def _parse_init_method(self, init_method: ast.FunctionDef, stack_name: str,
                          file_path: Path, imports: Dict[str, str]) -> None:
        """Parse __init__ method to extract resource definitions."""
        
        for node in ast.walk(init_method):
            if isinstance(node, ast.Assign):
                # Look for resource assignments like self.bucket = s3.Bucket(...)
                if (len(node.targets) == 1 and 
                    isinstance(node.targets[0], ast.Attribute) and
                    isinstance(node.targets[0].value, ast.Name) and
                    node.targets[0].value.id == 'self'):
                    
                    resource_name = node.targets[0].attr
                    
                    if isinstance(node.value, ast.Call):
                        component = self._parse_resource_call(
                            node.value, resource_name, stack_name, 
                            file_path, imports, node.lineno
                        )
                        if component:
                            self.components.append(component)
            
            # Look for CloudFormation outputs
            elif isinstance(node, ast.Call):
                if (isinstance(node.func, ast.Attribute) and 
                    node.func.attr == 'CfnOutput'):
                    self._parse_cfn_output(node, stack_name)
                
                # Look for grant permissions
                elif (isinstance(node.func, ast.Attribute) and 
                      'grant' in node.func.attr):
                    self._parse_grant_permission(node, stack_name)
    
    def _parse_resource_call(self, call_node: ast.Call, resource_name: str,
                           stack_name: str, file_path: Path, imports: Dict[str, str],
                           line_number: int) -> Optional[InfrastructureComponent]:
        """Parse a resource constructor call."""
        
        # Extract construct type and AWS service
        construct_name = ""
        aws_service = "Unknown"
        
        if isinstance(call_node.func, ast.Attribute):
            construct_name = call_node.func.attr
            if isinstance(call_node.func.value, ast.Name):
                module_alias = call_node.func.value.id
                aws_service = imports.get(module_alias, "Unknown")
                
                # If import mapping failed, try to infer from construct name
                if aws_service == "Unknown":
                    aws_service = self._infer_service_from_construct(construct_name)
        elif isinstance(call_node.func, ast.Name):
            construct_name = call_node.func.id
            aws_service = imports.get(construct_name, "Unknown")
            
            # If import mapping failed, try to infer from construct name
            if aws_service == "Unknown":
                aws_service = self._infer_service_from_construct(construct_name)
        
        # Extract configuration from constructor arguments
        configuration = self._extract_call_arguments(call_node)
        
        # Extract environment variables for Lambda functions
        environment_vars = {}
        if aws_service == "Lambda" and "environment" in configuration:
            environment_vars = configuration.get("environment", {})
        
        # Determine resource purpose
        purpose = self._infer_resource_purpose(resource_name, construct_name, aws_service)
        
        return InfrastructureComponent(
            id=f"{stack_name.lower()}_{resource_name}",
            name=resource_name,
            type="resource",
            aws_service=aws_service,
            cdk_construct=construct_name,
            purpose=purpose,
            configuration=configuration,
            environment_variables=environment_vars,
            stack_name=stack_name,
            file_path=str(file_path),
            line_number=line_number
        )
    
    def _parse_cfn_output(self, call_node: ast.Call, stack_name: str) -> None:
        """Parse CloudFormation output definitions."""
        output_name = ""
        output_description = ""
        
        # Extract output name from first argument
        if call_node.args and isinstance(call_node.args[1], ast.Constant):
            output_name = call_node.args[1].value
        
        # Extract description from keyword arguments
        for keyword in call_node.keywords:
            if keyword.arg == "description" and isinstance(keyword.value, ast.Constant):
                output_description = keyword.value.value
        
        if output_name:
            if stack_name not in self.stack_outputs:
                self.stack_outputs[stack_name] = []
            self.stack_outputs[stack_name].append({
                'name': output_name,
                'description': output_description
            })
    
    def _parse_grant_permission(self, call_node: ast.Call, stack_name: str) -> None:
        """Parse grant permission calls to understand resource relationships."""
        if isinstance(call_node.func, ast.Attribute):
            permission_type = call_node.func.attr
            
            # Find the component this permission is being granted to
            if (isinstance(call_node.func.value, ast.Attribute) and
                isinstance(call_node.func.value.value, ast.Name) and
                call_node.func.value.value.id == 'self'):
                
                resource_name = call_node.func.value.attr
                
                # Find the component and add permission info
                for component in self.components:
                    if component.name == resource_name and component.stack_name == stack_name:
                        component.permissions.append(permission_type)
                        break
    
    def _extract_call_arguments(self, call_node: ast.Call) -> Dict[str, Any]:
        """Extract configuration from constructor call arguments."""
        config = {}
        
        # Extract keyword arguments
        for keyword in call_node.keywords:
            if keyword.arg:
                config[keyword.arg] = self._extract_value(keyword.value)
        
        return config
    
    def _extract_value(self, node: ast.AST) -> Any:
        """Extract value from AST node."""
        if isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.Str):  # Python < 3.8 compatibility
            return node.s
        elif isinstance(node, ast.Num):  # Python < 3.8 compatibility
            return node.n
        elif isinstance(node, ast.Name):
            return f"${node.id}"  # Variable reference
        elif isinstance(node, ast.Attribute):
            return f"${ast.unparse(node) if hasattr(ast, 'unparse') else 'attribute'}"
        else:
            return "complex_value"
    
    def _infer_resource_purpose(self, resource_name: str, construct_name: str, 
                              aws_service: str) -> str:
        """Infer the purpose of a resource from its name and type."""
        name_lower = resource_name.lower()
        construct_lower = construct_name.lower()
        
        purpose_patterns = {
            'bucket': 'Data storage',
            'table': 'Data storage and retrieval',
            'function': 'Serverless compute',
            'api': 'API endpoint',
            'pool': 'User authentication',
            'queue': 'Message queuing',
            'topic': 'Event notifications',
            'rule': 'Event scheduling',
            'role': 'Access control',
            'policy': 'Permission management'
        }
        
        for pattern, purpose in purpose_patterns.items():
            if pattern in name_lower or pattern in construct_lower:
                return purpose
        
        return f"{aws_service} resource"
    
    def get_stack_dependencies(self) -> Dict[str, List[str]]:
        """Analyze and return stack dependencies."""
        # This would analyze cross-stack references
        # For now, return a basic dependency map based on common patterns
        return {
            'DataStack': [],
            'ComputeStack': ['DataStack'],
            'APIStack': ['DataStack', 'ComputeStack'],
            'FrontendStack': ['APIStack'],
            'LocationStack': ['DataStack']
        }
    
    def get_components_by_stack(self, stack_name: str) -> List[InfrastructureComponent]:
        """Get all components for a specific stack."""
        return [comp for comp in self.components if comp.stack_name == stack_name]
    
    def get_components_by_service(self, aws_service: str) -> List[InfrastructureComponent]:
        """Get all components for a specific AWS service."""
        return [comp for comp in self.components if comp.aws_service == aws_service]
    
    def _parse_app_file(self) -> None:
        """Parse the main app.py file to extract stack dependencies."""
        try:
            with open(self.app_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            # Find stack instantiations and dependencies
            stack_instances = {}
            
            for node in ast.walk(tree):
                # Find stack instantiations
                if isinstance(node, ast.Assign):
                    if (len(node.targets) == 1 and 
                        isinstance(node.targets[0], ast.Name) and
                        isinstance(node.value, ast.Call)):
                        
                        var_name = node.targets[0].id
                        if 'stack' in var_name.lower():
                            stack_instances[var_name] = self._extract_stack_class_name(node.value)
                
                # Find add_dependency calls
                elif isinstance(node, ast.Call):
                    if (isinstance(node.func, ast.Attribute) and 
                        node.func.attr == 'add_dependency' and
                        len(node.args) == 1):
                        
                        source_stack = self._get_stack_name_from_var(node.func.value, stack_instances)
                        target_stack = self._get_stack_name_from_var(node.args[0], stack_instances)
                        
                        if source_stack and target_stack:
                            self.stack_dependencies.append(StackDependency(
                                source_stack=source_stack,
                                target_stack=target_stack,
                                dependency_type="explicit",
                                description=f"{source_stack} depends on {target_stack}"
                            ))
                            
        except Exception as e:
            print(f"Warning: Failed to parse app.py: {e}")
    
    def _extract_stack_class_name(self, call_node: ast.Call) -> str:
        """Extract stack class name from constructor call."""
        if isinstance(call_node.func, ast.Name):
            return call_node.func.id
        return "Unknown"
    
    def _get_stack_name_from_var(self, node: ast.AST, stack_instances: Dict[str, str]) -> Optional[str]:
        """Get stack name from variable reference."""
        if isinstance(node, ast.Name):
            return stack_instances.get(node.id)
        return None
    
    def _analyze_service_relationships(self) -> None:
        """Analyze relationships between AWS services based on component configurations."""
        
        # Define common service relationship patterns
        relationship_patterns = [
            # Lambda triggers and data access
            {
                'source_service': 'Lambda',
                'target_service': 'S3',
                'relationship_type': 'stores_in',
                'pattern': lambda comp: 'bucket' in str(comp.configuration).lower()
            },
            {
                'source_service': 'Lambda', 
                'target_service': 'DynamoDB',
                'relationship_type': 'stores_in',
                'pattern': lambda comp: 'table' in str(comp.configuration).lower()
            },
            {
                'source_service': 'EventBridge',
                'target_service': 'Lambda',
                'relationship_type': 'triggers',
                'pattern': lambda comp: comp.cdk_construct == 'Rule'
            },
            # API and authentication
            {
                'source_service': 'AppSync',
                'target_service': 'Cognito',
                'relationship_type': 'authenticates_with',
                'pattern': lambda comp: 'user_pool' in str(comp.configuration).lower()
            },
            # Data flow relationships
            {
                'source_service': 'S3',
                'target_service': 'Glue',
                'relationship_type': 'processed_by',
                'pattern': lambda comp: comp.aws_service == 'Glue'
            },
            {
                'source_service': 'S3',
                'target_service': 'Athena',
                'relationship_type': 'queried_by',
                'pattern': lambda comp: comp.aws_service == 'Athena'
            }
        ]
        
        # Find components that match relationship patterns
        for pattern in relationship_patterns:
            source_components = self.get_components_by_service(pattern['source_service'])
            target_components = self.get_components_by_service(pattern['target_service'])
            
            for source_comp in source_components:
                for target_comp in target_components:
                    if pattern['pattern'](source_comp) or pattern['pattern'](target_comp):
                        self.service_relationships.append(ServiceRelationship(
                            source_service=pattern['source_service'],
                            target_service=pattern['target_service'],
                            relationship_type=pattern['relationship_type'],
                            source_component=source_comp.name,
                            target_component=target_comp.name,
                            description=f"{source_comp.name} {pattern['relationship_type']} {target_comp.name}"
                        ))
    
    def get_stack_dependency_map(self) -> Dict[str, List[str]]:
        """Get stack dependencies as a simple dictionary map."""
        dependency_map = {}
        
        for dep in self.stack_dependencies:
            if dep.source_stack not in dependency_map:
                dependency_map[dep.source_stack] = []
            dependency_map[dep.source_stack].append(dep.target_stack)
            
        return dependency_map
    
    def get_service_interaction_map(self) -> Dict[str, List[Dict[str, str]]]:
        """Get service interactions organized by source service."""
        interaction_map = {}
        
        for rel in self.service_relationships:
            if rel.source_service not in interaction_map:
                interaction_map[rel.source_service] = []
            
            interaction_map[rel.source_service].append({
                'target_service': rel.target_service,
                'relationship_type': rel.relationship_type,
                'description': rel.description
            })
            
        return interaction_map
    
    def _infer_service_from_construct(self, construct_name: str) -> str:
        """Infer AWS service from CDK construct name."""
        construct_lower = construct_name.lower()
        
        construct_service_map = {
            'bucket': 'S3',
            'table': 'DynamoDB',
            'function': 'Lambda',
            'layerversion': 'Lambda',
            'rule': 'EventBridge',
            'queue': 'SQS',
            'topic': 'SNS',
            'userpool': 'Cognito',
            'identitypool': 'Cognito',
            'graphqlapi': 'AppSync',
            'cfnapp': 'Amplify',
            'cfnbranch': 'Amplify',
            'cfnmap': 'Location Service',
            'cfnplaceindex': 'Location Service',
            'cfndatabase': 'Glue',
            'cfnworkgroup': 'Athena',
            'role': 'IAM',
            'cfnwebacl': 'WAF'
        }
        
        for construct_pattern, service in construct_service_map.items():
            if construct_pattern in construct_lower:
                return service
        
        return 'Unknown'