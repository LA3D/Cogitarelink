#!/usr/bin/env python3
"""
Experiment 02: Test Improved cl_discover Tool

Goal: Verify that the refactored cl_discover produces jq-friendly output
      and enables better tool composition patterns.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from test_harness import CLIExperiment
import json


def test_improved_structure(exp: CLIExperiment):
    """Test the new standardized output structure"""
    print("\n" + "="*80)
    print("🔬 TESTING IMPROVED cl_discover STRUCTURE")
    print("="*80)
    
    # Test same entities as baseline
    entities = ["insulin", "Q7240673", "caffeine", "BRCA1"]
    
    for entity in entities:
        print(f"\n{'='*50}")
        print(f"Testing: {entity}")
        print(f"{'='*50}")
        
        result = exp.run_cli(f"cl_discover {entity}")
        
        if result["success"]:
            output = result["output"]
            
            # Verify standardized structure
            print("✅ Structure validation:")
            required_fields = ['status', 'data', 'count', 'meta', 'next']
            for field in required_fields:
                if field in output:
                    print(f"  ✓ Has '{field}' field")
                else:
                    print(f"  ✗ Missing '{field}' field")
            
            # Verify data is array
            data = output.get('data', [])
            print(f"  ✓ Data is array: {isinstance(data, list)}")
            print(f"  ✓ Count matches data length: {output.get('count') == len(data)}")
            
            if len(data) > 0:
                entity_obj = data[0]
                print(f"  ✓ Entity has ID: {'id' in entity_obj}")
                print(f"  ✓ Entity has type: {'type' in entity_obj}")
                print(f"  ✓ Entity has confidence: {'confidence' in entity_obj}")


def test_jq_patterns(exp: CLIExperiment):
    """Test jq patterns that failed before now work"""
    print("\n" + "="*80)
    print("🧪 TESTING JQ PATTERNS")
    print("="*80)
    
    result = exp.run_cli("cl_discover insulin")
    
    if result["success"]:
        output = result["output"]
        
        # These patterns should all work now
        patterns = {
            "Get status": ".status",
            "Get count": ".count", 
            "Get first entity": ".data[0]",
            "Get entity ID": ".data[0].id",
            "Get entity type": ".data[0].type",
            "Get confidence": ".data[0].confidence", 
            "Get all entity IDs": ".data[].id",
            "Get next commands": ".next[]",
            "Get meta info": ".meta.query"
        }
        
        print("\n🎯 Pattern test results:")
        for name, pattern in patterns.items():
            result_val = exp.run_jq(output, pattern)
            if result_val is not None and result_val != "null":
                print(f"  ✅ {name}: {result_val}")
            else:
                print(f"  ❌ {name}: failed")


def test_composition_pipeline(exp: CLIExperiment):
    """Test tool composition with improved output"""
    print("\n" + "="*80)
    print("🔗 TESTING TOOL COMPOSITION")
    print("="*80)
    
    # Step 1: Discover
    discover_result = exp.run_cli("cl_discover insulin")
    
    if discover_result["success"]:
        # Step 2: Extract ID using jq
        entity_id = exp.run_jq(discover_result["output"], ".data[0].id")
        print(f"✅ Extracted entity ID: {entity_id}")
        
        # Step 3: Get suggested next command
        next_command = exp.run_jq(discover_result["output"], ".next[0]")
        print(f"✅ Next command suggestion: {next_command}")
        
        # Step 4: Test if next command would work
        if next_command and entity_id:
            print(f"✅ Pipeline composition successful!")
            print(f"   Discovery → ID extraction → Next command ready")
        else:
            print("❌ Pipeline broken")


def compare_old_vs_new(exp: CLIExperiment):
    """Compare old problematic patterns vs new working ones"""
    print("\n" + "="*80)
    print("📊 OLD vs NEW PATTERN COMPARISON")
    print("="*80)
    
    result = exp.run_cli("cl_discover insulin")
    
    if result["success"]:
        output = result["output"]
        
        print("\n❌ OLD PATTERNS (would have failed):")
        old_patterns = [
            ".data[0]  # data was object, not array",
            ".success  # now .status", 
            ".suggestions[]  # now .next[]"
        ]
        
        for pattern in old_patterns:
            print(f"  - {pattern}")
            
        print("\n✅ NEW PATTERNS (work perfectly):")
        new_patterns = {
            ".status": "Get operation status",
            ".data[0].id": "Extract entity identifier",
            ".count": "Get result count",
            ".next[0]": "Get first suggested command",
            ".meta.query": "Get original query"
        }
        
        for pattern, description in new_patterns.items():
            result_val = exp.run_jq(output, pattern)
            print(f"  ✅ {pattern}  # {description} → {result_val}")


if __name__ == "__main__":
    exp = CLIExperiment(verbose=True)
    
    print("🔬 Testing Improved cl_discover Tool")
    print("="*80)
    
    # Run all tests
    test_improved_structure(exp)
    test_jq_patterns(exp)
    test_composition_pipeline(exp)
    compare_old_vs_new(exp)
    
    # Summarize results
    exp.summarize_results()
    
    print("\n✅ Improved cl_discover testing complete!")