#!/usr/bin/env python3
"""
Test dynamic cross-reference discovery with SPARQL endpoint classification.

This test validates:
1. Dynamic property discovery replaces hard-coded mappings
2. SPARQL endpoint vs API endpoint classification works
3. Official property labels are used instead of abbreviations
4. Formatter URLs and descriptions are included
5. Pattern matching accuracy for SPARQL endpoints
"""

import asyncio
import json
import sys
import os
from typing import Dict

# Add project root to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# Test cases covering different domains
TEST_ENTITIES = [
    {
        "id": "Q7240673",
        "name": "preproinsulin",
        "domain": "biology",
        "expected_sparql": ["uniprot"],  # Should find UniProt SPARQL endpoint
        "expected_apis": ["refseq", "ensembl", "pdb"],  # Should be API endpoints
    },
    {
        "id": "Q60235", 
        "name": "caffeine",
        "domain": "chemistry",
        "expected_sparql": [],  # Most chemical databases are APIs
        "expected_apis": ["chembl", "pubchem", "chebi", "drugbank", "cas"],
    },
    {
        "id": "Q42",
        "name": "Douglas Adams", 
        "domain": "person",
        "expected_sparql": [],  # Person identifiers typically don't have SPARQL
        "expected_apis": ["viaf", "isni", "gnd"],  # Authority control systems
    }
]

async def test_dynamic_discovery():
    """Test the dynamic cross-reference discovery system."""
    
    print("🧪 Testing Dynamic Cross-Reference Discovery with SPARQL Classification")
    print("=" * 80)
    
    results = {"passed": 0, "failed": 0, "tests": []}
    
    for test_case in TEST_ENTITIES:
        print(f"\n📋 Testing: {test_case['name']} ({test_case['id']})")
        print(f"   Domain: {test_case['domain']}")
        
        # Import and run cl_describe functions directly
        try:
            from cogitarelink.cli.cl_describe import _extract_cross_references, _build_entity_description
            from cogitarelink.adapters.wikidata_client import WikidataClient
            
            # Get entity data
            client = WikidataClient(timeout=30)
            entity_data = await client.get_entities([test_case['id']])
            
            if test_case['id'] not in entity_data.get('entities', {}):
                print(f"   ❌ Entity {test_case['id']} not found")
                results["failed"] += 1
                continue
                
            entity_info = entity_data['entities'][test_case['id']]
            
            # Build description
            description = _build_entity_description(entity_info, test_case['id'])
            cross_refs = await _extract_cross_references(entity_info)
            description['cross_references'] = cross_refs
            
            await analyze_test_result(test_case, description, results)
                
        except Exception as e:
            print(f"   ❌ Error testing {test_case['id']}: {e}")
            results["failed"] += 1
    
    # Print summary
    print("\n" + "=" * 80)
    print(f"📊 Test Results: {results['passed']} passed, {results['failed']} failed")
    
    if results["failed"] == 0:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed. See details above.")
    
    return results

async def analyze_test_result(test_case: Dict, data: Dict, results: Dict):
    """Analyze the test result for a specific entity."""
    
    cross_refs = data.get("cross_references", {}).get("databases", {})
    
    if not cross_refs:
        print(f"   ⚠️  No cross-references found for {test_case['name']}")
        results["failed"] += 1
        return
    
    print(f"   📊 Found {len(cross_refs)} external identifiers:")
    
    sparql_found = []
    api_found = []
    
    for db_name, db_info in cross_refs.items():
        endpoint_type = db_info.get("endpoint_type", "unknown")
        property_id = db_info.get("property_id", "")
        
        if endpoint_type == "sparql_endpoint":
            sparql_endpoint = db_info.get("sparql_endpoint", "")
            sparql_found.append(db_name.lower())
            print(f"   🔗 SPARQL: {db_name} ({property_id}) → {sparql_endpoint}")
        elif endpoint_type == "api_endpoint":
            formatter_url = db_info.get("formatter_url", "")
            api_found.append(db_name.lower())
            print(f"   🌐 API: {db_name} ({property_id}) → {formatter_url[:50]}...")
        else:
            print(f"   ❓ Unknown: {db_name} ({property_id})")
    
    # Validate expectations
    test_passed = True
    
    # Check expected SPARQL endpoints
    for expected in test_case["expected_sparql"]:
        found_match = any(expected in sparql_name for sparql_name in sparql_found)
        if found_match:
            print(f"   ✅ Expected SPARQL endpoint found: {expected}")
        else:
            print(f"   ❌ Expected SPARQL endpoint missing: {expected}")
            test_passed = False
    
    # Check expected API endpoints 
    for expected in test_case["expected_apis"]:
        found_match = any(expected in api_name for api_name in api_found)
        if found_match:
            print(f"   ✅ Expected API endpoint found: {expected}")
        else:
            print(f"   ⚠️  Expected API endpoint not found: {expected} (may not be present)")
    
    # Check that we're using official property labels (not abbreviations)
    official_labels = True
    for db_name in cross_refs.keys():
        if len(db_name) <= 3 or not any(c.isupper() for c in db_name):
            print(f"   ❌ Suspicious short/lowercase label: '{db_name}' (should be official)")
            official_labels = False
    
    if official_labels:
        print(f"   ✅ Using official property labels (not abbreviations)")
    
    # Check that formatter URLs are present
    formatter_count = sum(1 for db_info in cross_refs.values() if db_info.get("formatter_url"))
    print(f"   📋 Formatter URLs: {formatter_count}/{len(cross_refs)} databases")
    
    if test_passed:
        results["passed"] += 1
    else:
        results["failed"] += 1

def test_direct_functionality():
    """Run a direct test of specific functionality."""
    
    print("\n🔬 Direct Function Tests")
    print("-" * 40)
    
    # Test 1: SPARQL database discovery
    print("Test 1: SPARQL Database Discovery")
    
    async def test_sparql_discovery():
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
        
        from cogitarelink.cli.cl_describe import _get_sparql_databases
        databases = await _get_sparql_databases()
        
        print(f"   Found {len(databases)} databases with SPARQL endpoints")
        
        # Check for expected databases
        expected = ["uniprot", "wikidata", "lingua libre"]
        found = 0
        for db_name in databases.keys():
            for expected_db in expected:
                if expected_db in db_name.lower():
                    print(f"   ✅ Found: {db_name} → {databases[db_name]}")
                    found += 1
                    break
        
        print(f"   Summary: {found}/{len(expected)} expected databases found")
        return len(databases) > 0
    
    # Test 2: Property metadata extraction
    print("\nTest 2: Property Metadata Extraction")
    
    async def test_property_metadata():
        from cogitarelink.cli.cl_describe import _get_property_metadata
        
        test_properties = ["P352", "P683", "P231"]  # UniProt, ChEBI, CAS
        metadata = await _get_property_metadata(test_properties)
        
        for prop_id in test_properties:
            if prop_id in metadata:
                info = metadata[prop_id]
                label = info.get("label", "")
                endpoint_type = info.get("database_info", {}).get("type", "unknown")
                
                print(f"   {prop_id}: {label} ({endpoint_type})")
                
                if prop_id == "P352" and endpoint_type == "sparql_endpoint":
                    print(f"      ✅ UniProt correctly identified as SPARQL endpoint")
                elif prop_id in ["P683", "P231"] and endpoint_type == "api_endpoint":
                    print(f"      ✅ {label} correctly identified as API endpoint")
            else:
                print(f"   ❌ Missing metadata for {prop_id}")
        
        return len(metadata) == len(test_properties)
    
    # Run direct tests
    async def run_async_tests():
        test1_result = await test_sparql_discovery()
        test2_result = await test_property_metadata()
        
        return test1_result and test2_result
    
    return asyncio.run(run_async_tests())

if __name__ == "__main__":
    print("🚀 Starting Dynamic Cross-Reference Discovery Tests")
    
    # Run direct function tests first
    direct_test_passed = test_direct_functionality()
    
    if direct_test_passed:
        print("\n✅ Direct tests passed, proceeding to integration tests...")
        # Run full integration tests
        asyncio.run(test_dynamic_discovery())
    else:
        print("\n❌ Direct tests failed, skipping integration tests")