#!/usr/bin/env python3
"""
Test script for documentation generation utilities.
"""

import sys
from pathlib import Path

# Add utils to path
sys.path.insert(0, str(Path(__file__).parent / "utils"))

from doc_generator import DocumentationGenerator


def test_documentation_generation():
    """Test the documentation generation process."""
    print("Testing OpenData Pulse Documentation Generation")
    print("=" * 50)
    
    # Initialize generator
    project_root = Path(__file__).parent.parent  # opendata-pulse/
    docs_output = Path(__file__).parent / "test_output"  # Don't overwrite existing docs
    
    generator = DocumentationGenerator(
        project_root=str(project_root),
        docs_output=str(docs_output)
    )
    
    try:
        # Test parsing
        print("1. Testing CDK parsing...")
        generator._parse_infrastructure()
        
        summary = generator.get_component_summary()
        print(f"   ✓ Found {summary['total_components']} components")
        print(f"   ✓ Found {summary['stacks']} stacks")
        print(f"   ✓ Found {summary['resources']} resources")
        print(f"   ✓ Found {summary['aws_services']} AWS services")
        
        # Test diagram generation
        print("\n2. Testing diagram generation...")
        arch_diagram = generator.diagram_generator.generate_architecture_diagram(
            generator.components, generator.stack_dependencies
        )
        print(f"   ✓ Generated architecture diagram ({len(arch_diagram)} characters)")
        
        sequence_diagram = generator.diagram_generator.generate_sequence_diagram(
            "data_ingestion", generator.components
        )
        print(f"   ✓ Generated sequence diagram ({len(sequence_diagram)} characters)")
        
        # Test content generation
        print("\n3. Testing content generation...")
        overview_content = generator._generate_architecture_overview()
        print(f"   ✓ Generated architecture overview ({len(overview_content)} characters)")
        
        print("\n4. All tests passed! ✓")
        print("\nSample Architecture Diagram:")
        print("-" * 30)
        print(arch_diagram[:500] + "..." if len(arch_diagram) > 500 else arch_diagram)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_documentation_generation()
    sys.exit(0 if success else 1)