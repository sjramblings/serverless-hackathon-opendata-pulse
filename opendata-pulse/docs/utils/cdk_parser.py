"""
CDK Stack Parser for extracting infrastructure component information.

This module provides utilities to parse CDK stack definitions and extract
AWS service configurations, dependencies, and resource information.
"""

import ast
import os
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Any
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


class CDKStackParser:
    """Parser for CDK stack files to extract infrastructure components."""
    
    def __init__(self, infrastructure_path: str = "infrastructure"):
        """Initialize parser with path to CDK infrastructure directory."""
        self.infrastructure_path = Path(infrastructure_path)
        self.components: List[InfrastructureComponent] = []
        self.stack_dependencies: Dict[str, List[str]] = {}
        
    def parse_all_stacks(self) -> List[InfrastructureComponent]:
        """Parse all CDK stack files and return infrastructure components."""
        if not self.infrastructure_path.exists():
            raise FileNotFoundError(f"Infrastructure directory not found: {self.infrastructure_path}")
            
        stack_files = list(self.infrastructure_path.glob("*_stack.py"))
        
        for stack_file in stack_files:
            try:
                self._parse_stack_file(stack_file)
            except Exception as e:
                print(f"Warning: Failed to parse {stack_file}: {e}")
                
        return self.components
    
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
            'aws_iam': 'IAM'
        }
        
        for cdk_module, service in service_mapping.items():
            if cdk_module in module_name:
                return service
                
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
        elif isinstance(call_node.func, ast.Name):
            construct_name = call_node.func.id
            aws_service = imports.get(construct_name, "Unknown")
        
        # Extract configuration from constructor arguments
        configuration = self._extract_call_arguments(call_node)
        
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
            stack_name=stack_name,
            file_path=str(file_path),
            line_number=line_number
        )
    
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