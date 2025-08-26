#!/usr/bin/env python3
"""
Documentation generation script for OpenData Pulse.

This script uses the documentation utilities to parse CDK stacks and generate
comprehensive infrastructure documentation with diagrams and cross-references.
"""

import sys
import os
from pathlib import Path

# Add utils to path
sys.path.insert(0, str(Path(__file__).parent / "utils"))

from doc_generator import DocumentationGenerator


def main():
    """Main documentation generation function."""
    print("OpenData Pulse Documentation Generator")
    print("=" * 40)
    
    # Initialize generator with project paths
    project_root = Path(__file__).parent.parent  # opendata-pulse/
    docs_output = Path(__file__).parent  # opendata-pulse/docs/
    
    generator = DocumentationGenerator(
        project_root=str(project_root),
        docs_output=str(docs_output)
    )
    
    try:
        # Generate all documentation
        generator.generate_all_documentation()
        
        # Print summary
        summary = generator.get_component_summary()
        print("\nDocumentation Generation Summary:")
        print(f"- Total Components: {summary['total_components']}")
        print(f"- CDK Stacks: {summary['stacks']}")
        print(f"- AWS Resources: {summary['resources']}")
        print(f"- AWS Services: {summary['aws_services']}")
        
        print("\nDocumentation generated successfully!")
        print(f"Output directory: {docs_output}")
        
    except Exception as e:
        print(f"Error generating documentation: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()