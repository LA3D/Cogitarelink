#!/usr/bin/env python3
"""
Experiment 01: Baseline Profiling of Current CLI Tools

Goal: Understand current tool behavior and JSON structure to identify
      improvements for jq navigability and composition.

Test Entities:
- insulin (Q7240673) - Well-studied protein
- caffeine (Q60235) - Simple chemical compound  
- BRCA1 (Q227339) - Cancer-related gene/protein
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from test_harness import CLIExperiment, explore_entity, compare_formats
import json
from pprint import pprint


def profile_discovery_tools(exp: CLIExperiment):
    """Profile all discovery-related tools"""
    print("\n" + "="*80)
    print("🔍 PROFILING DISCOVERY TOOLS")
    print("="*80)
    
    # Test cl_discover with different entities
    entities = [
        ("insulin", "protein"),
        ("Q7240673", "wikidata_id"),
        ("caffeine", "chemical"),
        ("BRCA1", "gene")
    ]
    
    for entity, entity_type in entities:
        print(f"\n{'='*60}")
        print(f"Testing: {entity} ({entity_type})")
        print(f"{'='*60}")
        
        # Basic discovery
        result = exp.run_cli(f"cl_discover {entity}")
        
        if result["success"] and "output" in result:
            output = result["output"]
            
            # Analyze structure
            print("\n📊 Output Analysis:")
            print(f"  - Top-level keys: {list(output.keys())}")
            print(f"  - Success: {output.get('success', 'N/A')}")
            print(f"  - Has 'data' key: {'data' in output}")
            
            if "data" in output:
                print(f"  - Data type: {type(output['data'])}")
                print(f"  - Data length: {len(output['data']) if isinstance(output['data'], list) else 'N/A'}")
                
                if isinstance(output['data'], dict):
                    print(f"  - Data keys: {list(output['data'].keys())[:10]}")
                elif isinstance(output['data'], list) and len(output['data']) > 0:
                    print(f"  - First item type: {type(output['data'][0])}")
                    if isinstance(output['data'][0], dict):
                        print(f"  - First item keys: {list(output['data'][0].keys())[:10]}")
            
            # Test common jq patterns
            print("\n🧪 Testing jq patterns:")
            patterns = {
                "Get success": ".success",
                "Get data": ".data",
                "Count results": ".data | length",
                "Get first item": ".data[0]",
                "Extract suggestions": ".suggestions[]"
            }
            
            for pattern_name, pattern in patterns.items():
                try:
                    result = exp.run_jq(output, pattern)
                    print(f"  ✓ {pattern_name}: works")
                except:
                    print(f"  ✗ {pattern_name}: failed")


def profile_sparql_tool(exp: CLIExperiment):
    """Profile cl_sparql tool"""
    print("\n" + "="*80)
    print("⚡ PROFILING SPARQL TOOL")
    print("="*80)
    
    queries = [
        {
            "name": "Simple protein query",
            "query": 'SELECT ?protein WHERE { ?protein wdt:P31 wd:Q8054 } LIMIT 5'
        },
        {
            "name": "Entity with cross-references",
            "query": 'SELECT ?item ?uniprot WHERE { ?item wdt:P352 ?uniprot } LIMIT 5'
        }
    ]
    
    for q in queries:
        print(f"\n📝 Query: {q['name']}")
        
        result = exp.run_cli(f'cl_sparql "{q["query"]}"')
        
        if result["success"] and "output" in result:
            output = result["output"]
            
            print("\n📊 SPARQL Output Analysis:")
            print(f"  - Top-level keys: {list(output.keys())}")
            
            # Check for standard SPARQL result format
            if "results" in output:
                results = output["results"]
                print(f"  - Has 'results': True")
                print(f"  - Results keys: {list(results.keys()) if isinstance(results, dict) else 'N/A'}")
                
                if isinstance(results, dict) and "bindings" in results:
                    bindings = results["bindings"]
                    print(f"  - Bindings count: {len(bindings)}")
                    if len(bindings) > 0:
                        print(f"  - First binding keys: {list(bindings[0].keys())}")
                        # Check value structure
                        for key, val in bindings[0].items():
                            if isinstance(val, dict):
                                print(f"    - {key} structure: {list(val.keys())}")


def profile_resolve_tool(exp: CLIExperiment):
    """Profile cl_resolve tool"""
    print("\n" + "="*80)
    print("🔗 PROFILING RESOLVE TOOL")
    print("="*80)
    
    # Test resolving UniProt IDs
    test_cases = [
        ("P352", "P01308", "UniProt ID for insulin"),
        ("P683", "CHEBI:15365", "ChEBI ID for caffeine")
    ]
    
    for prop_id, identifier, description in test_cases:
        print(f"\n🧪 Testing: {description}")
        
        result = exp.run_cli(f"cl_resolve {prop_id} {identifier}")
        
        if result["success"] and "output" in result:
            output = result["output"]
            
            print("\n📊 Resolve Output Analysis:")
            print(f"  - Top-level keys: {list(output.keys())}")
            print(f"  - Success: {output.get('success', 'N/A')}")
            
            if "data" in output:
                data = output["data"]
                print(f"  - Data keys: {list(data.keys()) if isinstance(data, dict) else 'N/A'}")
                
                # Check for nested structures
                for key in ["wikidata_results", "cross_references", "external_results"]:
                    if key in data:
                        print(f"  - {key}: {type(data[key])}")


def test_tool_composition(exp: CLIExperiment):
    """Test how well tools compose together"""
    print("\n" + "="*80)
    print("🔧 TESTING TOOL COMPOSITION")
    print("="*80)
    
    # Pipeline 1: Discover → Extract ID → Resolve
    print("\n📋 Pipeline 1: Entity Discovery → ID Extraction → Resolution")
    
    # Step 1: Discover
    discover = exp.run_cli("cl_discover insulin")
    
    if discover["success"]:
        # Try to extract data in different ways
        print("\n🔍 Attempting ID extraction patterns:")
        
        patterns = [
            ('.data.resource_identifier', "Direct resource_identifier"),
            ('.data[0]["@id"]', "JSON-LD @id"),
            ('.data[0].id', "Simple id"),
            ('.data[0].resource_identifier', "Nested resource_identifier"),
            ('.resource_identifier', "Top-level resource_identifier")
        ]
        
        extracted_id = None
        for pattern, description in patterns:
            result = exp.run_jq(discover["output"], pattern)
            if result and result != "null":
                print(f"  ✓ {description}: {result}")
                extracted_id = result
                break
            else:
                print(f"  ✗ {description}: failed")
        
        # Step 2: Try to get cross-references
        if extracted_id:
            print(f"\n🔗 Attempting to resolve: {extracted_id}")
            # This might fail if the tool expects different input format
            resolve = exp.run_cli(f"cl_resolve P352 {extracted_id}")


def analyze_improvement_opportunities(exp: CLIExperiment):
    """Analyze results and identify improvement opportunities"""
    print("\n" + "="*80)
    print("💡 IMPROVEMENT OPPORTUNITIES")
    print("="*80)
    
    print("""
Based on profiling, key issues for jq navigation:

1. INCONSISTENT OUTPUT STRUCTURE
   - Some tools return nested 'data', others don't
   - Success indicators vary
   - Array vs object for single results

2. DEEP NESTING
   - Multiple levels to reach actual data
   - Inconsistent paths to common fields

3. MISSING STANDARD FIELDS
   - No consistent way to extract entity IDs
   - No standard 'count' field
   - Suggestions mixed with data

4. COMPOSITION BARRIERS
   - Output of one tool doesn't match input of next
   - Need complex jq to extract and transform

RECOMMENDATIONS:
- Standardize on {status, data[], count, meta} structure  
- Always use arrays for data (even single items)
- Flatten common fields (id, name, type) to top of each item
- Add 'next' field with ready-to-run commands
- Move complex JSON-LD to separate 'context' field
""")


if __name__ == "__main__":
    exp = CLIExperiment(verbose=True)
    
    print("🚀 CogitareLink CLI Baseline Profiling")
    print("="*80)
    
    # Run all profiling
    profile_discovery_tools(exp)
    profile_sparql_tool(exp)
    profile_resolve_tool(exp)
    test_tool_composition(exp)
    
    # Summarize findings
    exp.summarize_results()
    analyze_improvement_opportunities(exp)
    
    # Save detailed results
    with open("baseline_results.json", "w") as f:
        json.dump(exp.results, f, indent=2)
    
    print("\n✅ Baseline profiling complete. Results saved to baseline_results.json")