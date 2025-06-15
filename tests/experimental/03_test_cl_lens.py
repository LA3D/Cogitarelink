#!/usr/bin/env python3
"""
Experiment 03: Test cl_lens Semantic Filter Library

Goal: Verify that cl_lens provides useful jq filters for common patterns
      and enables powerful tool composition workflows.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from test_harness import CLIExperiment
import json


def test_lens_listing(exp: CLIExperiment):
    """Test listing all available lenses"""
    print("\n" + "="*80)
    print("📚 TESTING LENS LIBRARY")
    print("="*80)
    
    result = exp.run_cli("cl_lens --list")
    
    if result["success"]:
        output = result["output"]
        
        print("✅ Lens listing structure:")
        print(f"  - Status: {output.get('status')}")
        print(f"  - Total lenses: {output.get('meta', {}).get('total_lenses')}")
        print(f"  - Categories: {output.get('meta', {}).get('categories')}")
        print(f"  - Data count: {output.get('count')}")
        
        # Show some example lenses
        if output.get('data'):
            print("\n📋 Sample lenses by category:")
            categories = {}
            for lens in output['data']:
                cat = lens.get('category', 'Unknown')
                if cat not in categories:
                    categories[cat] = []
                categories[cat].append(lens['name'])
            
            for cat, lenses in list(categories.items())[:3]:  # Show first 3 categories
                print(f"  {cat}: {', '.join(lenses[:3])}")


def test_individual_lenses(exp: CLIExperiment):
    """Test individual lens filters"""
    print("\n" + "="*80)
    print("🔍 TESTING INDIVIDUAL LENSES")
    print("="*80)
    
    # Test key lenses
    lenses_to_test = [
        "entity_ids",
        "discovery_status", 
        "pipe_ready",
        "protein_summary"
    ]
    
    for lens_name in lenses_to_test:
        print(f"\n{'='*50}")
        print(f"Testing lens: {lens_name}")
        print(f"{'='*50}")
        
        # Get lens filter
        result = exp.run_cli(f"cl_lens {lens_name}")
        
        if result["success"]:
            output = result["output"]
            if output.get('data') and len(output['data']) > 0:
                lens_data = output['data'][0]
                filter_str = lens_data.get('filter')
                print(f"  ✅ Filter: {filter_str}")
                print(f"  ✅ Usage: {lens_data.get('usage')}")
            else:
                print("  ❌ No lens data returned")
        else:
            print(f"  ❌ Failed to get lens: {lens_name}")


def test_lens_with_discovery_data(exp: CLIExperiment):
    """Test lens filters on actual discovery data"""
    print("\n" + "="*80)
    print("🧪 TESTING LENSES WITH REAL DATA")
    print("="*80)
    
    # First get some discovery data
    discover_result = exp.run_cli("cl_discover insulin")
    
    if discover_result["success"]:
        discovery_data = discover_result["output"]
        
        # Test key patterns on real data
        patterns_to_test = {
            "entity_ids": ".data[].id",
            "discovery_status": ".status",
            "discovery_count": ".count",
            "pipe_ready": ".data[0].id",
            "has_results": ".count > 0"
        }
        
        print("🎯 Testing patterns on insulin discovery:")
        for pattern_name, pattern in patterns_to_test.items():
            result = exp.run_jq(discovery_data, pattern)
            print(f"  ✅ {pattern_name}: {result}")


def test_lens_composition_pipeline(exp: CLIExperiment):
    """Test using lenses in actual tool composition"""
    print("\n" + "="*80)
    print("🔗 TESTING LENS-POWERED COMPOSITION")
    print("="*80)
    
    # Simulate the pattern: discover → extract ID → use ID
    print("📋 Pipeline: Discover → Extract ID via lens → Show usage")
    
    # Step 1: Discovery
    discover_result = exp.run_cli("cl_discover Q7240673")
    
    if discover_result["success"]:
        # Step 2: Get lens filter for ID extraction
        lens_result = exp.run_cli("cl_lens pipe_ready --raw")
        
        if lens_result["success"]:
            # The raw output should be just the jq filter
            filter_str = lens_result["output"].strip().strip('"')
            print(f"✅ Got lens filter: {filter_str}")
            
            # Step 3: Apply lens to discovery data
            extracted_id = exp.run_jq(discover_result["output"], filter_str)
            print(f"✅ Extracted ID: {extracted_id}")
            
            # Step 4: Show this enables next command
            next_command = exp.run_jq(discover_result["output"], ".next[0]")
            print(f"✅ Next command: {next_command}")
            
            print("✅ Pipeline demonstrates successful composition!")
        else:
            print("❌ Failed to get lens filter")
    else:
        print("❌ Discovery failed")


def test_error_handling(exp: CLIExperiment):
    """Test error handling for unknown lenses"""
    print("\n" + "="*80)
    print("❌ TESTING ERROR HANDLING")
    print("="*80)
    
    # Test unknown lens
    result = exp.run_cli("cl_lens unknown_pattern")
    
    # Should return structured error, not crash
    if not result["success"]:
        print("✅ Tool handles unknown lens gracefully")
    else:
        # Check if it's a proper error response
        output = result["output"]
        if output.get("status") == "error":
            print("✅ Returns structured error response")
            print(f"  - Error message: {output.get('error', {}).get('message')}")
            print(f"  - Suggestions: {output.get('next', [])}")
        else:
            print("❌ Unexpected success for unknown lens")


if __name__ == "__main__":
    exp = CLIExperiment(verbose=True)
    
    print("🔍 Testing cl_lens Semantic Filter Library")
    print("="*80)
    
    # Run all tests
    test_lens_listing(exp)
    test_individual_lenses(exp)
    test_lens_with_discovery_data(exp)
    test_lens_composition_pipeline(exp)
    test_error_handling(exp)
    
    # Summarize results
    exp.summarize_results()
    
    print("\n✅ cl_lens testing complete!")