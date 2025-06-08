#!/usr/bin/env python3
"""
Test cross-reference discovery REALITY - what actually works vs what should work.

This test validates the CURRENT implementation to establish baseline, then identifies gaps:
1. What hardcoded mappings exist vs what properties are available in Wikidata
2. Which cross-references are successfully extracted vs missed  
3. Coverage gaps (like WikiPathways P2410 missing)
4. Integration points that need to be built
"""

import asyncio
import json
import sys
import os
from typing import Dict, Set

# Add project root to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# Test entities with known external identifiers
REALITY_TEST_ENTITIES = [
    {
        "id": "Q44054606", 
        "name": "Glycogen Metabolism (mouse)",
        "description": "Entity we know has WikiPathways P2410='WP317'",
        "expected_properties": {
            "P2410": "WP317"  # WikiPathways ID - now WORKING with tools
        },
        "expected_in_current_tools": True,  # Should work with current hardcoded mappings
    },
    {
        "id": "Q7240673",
        "name": "preproinsulin", 
        "description": "Entity with known biological cross-references",
        "expected_properties": {
            "P352": "P01308",  # UniProt ID - should be found (hardcoded)
        },
        "expected_in_current_tools": True,  # Should work with current hardcoded system
    }
]

async def test_current_reality():
    """Test what the current cl_describe/cl_follow tools actually return."""
    
    print("🔍 Testing CURRENT Cross-Reference Extraction Reality")
    print("=" * 70)
    
    results = {"hardcoded_working": [], "hardcoded_missing": [], "gaps_found": []}
    
    for test_case in REALITY_TEST_ENTITIES:
        print(f"\n📋 Testing: {test_case['name']} ({test_case['id']})")
        print(f"   Description: {test_case['description']}")
        
        # Test what cl_describe actually returns
        await test_cl_describe_reality(test_case, results)
        
        # Test what raw Wikidata has vs what tools extract
        await test_wikidata_vs_tools(test_case, results)
    
    print_reality_summary(results)
    return results

async def test_cl_describe_reality(test_case: Dict, results: Dict):
    """Test what cl_describe actually extracts."""
    
    try:
        from cogitarelink.cli.cl_describe import _extract_cross_references, _build_entity_description
        from cogitarelink.adapters.wikidata_client import WikidataClient
        
        # Get entity data
        client = WikidataClient(timeout=30)
        entity_data = await client.get_entities([test_case['id']])
        
        if test_case['id'] not in entity_data.get('entities', {}):
            print(f"   ❌ Entity {test_case['id']} not found in Wikidata")
            return
            
        entity_info = entity_data['entities'][test_case['id']]
        
        # Test current cl_describe extraction
        cross_refs = await _extract_cross_references(entity_info)
        
        print(f"   📊 cl_describe extracted: {len(cross_refs)} cross-references")
        for db_name, db_ids in cross_refs.items():
            print(f"      {db_name}: {db_ids}")
        
        # Check expected properties
        for prop_id, expected_value in test_case['expected_properties'].items():
            found_in_tools = any(expected_value in str(ids) for ids in cross_refs.values())
            
            if found_in_tools:
                print(f"   ✅ Found expected {prop_id}={expected_value} in tools output")
                results["hardcoded_working"].append({
                    "entity": test_case['id'],
                    "property": prop_id,
                    "value": expected_value
                })
            else:
                print(f"   ❌ Missing expected {prop_id}={expected_value} from tools output")
                results["hardcoded_missing"].append({
                    "entity": test_case['id'], 
                    "property": prop_id,
                    "value": expected_value,
                    "expected_in_tools": test_case.get('expected_in_current_tools', True)
                })
                
    except Exception as e:
        print(f"   ❌ Error testing cl_describe: {e}")

async def test_wikidata_vs_tools(test_case: Dict, results: Dict):
    """Compare raw Wikidata properties vs what tools extract."""
    
    try:
        from cogitarelink.adapters.wikidata_client import WikidataClient
        
        # Get raw Wikidata entity
        client = WikidataClient(timeout=30)  
        entity_data = await client.get_entities([test_case['id']])
        entity_info = entity_data['entities'][test_case['id']]
        
        # Extract all claims
        claims = entity_info.get('claims', {})
        external_id_claims = {}
        
        for prop_id, claim_list in claims.items():
            for claim in claim_list:
                if claim.get('mainsnak', {}).get('datatype') == 'external-id':
                    value = claim.get('mainsnak', {}).get('datavalue', {}).get('value')
                    if value:
                        external_id_claims[prop_id] = value
        
        print(f"   🗃️  Raw Wikidata external IDs: {len(external_id_claims)}")
        for prop_id, value in external_id_claims.items():
            print(f"      {prop_id}: {value}")
        
        # Check for gaps - properties in Wikidata but missing from hardcoded mappings
        # Note: database_properties is defined inside _extract_cross_references function
        # so we'll hardcode the current mappings here for testing
        database_properties = {
            'P352': 'uniprot', 'P683': 'chebi', 'P231': 'cas', 'P592': 'chembl',
            'P715': 'drugbank', 'P486': 'mesh', 'P685': 'ncbi_gene', 'P594': 'ensembl_gene',
            'P637': 'refseq', 'P699': 'disease_ontology', 'P665': 'kegg', 'P232': 'ec_number',
            'P662': 'pubchem_cid', 'P2017': 'isomeric_smiles', 'P1579': 'pubchem_sid',
            'P638': 'pdb', 'P2892': 'umls', 'P233': 'smiles', 'P274': 'molecular_formula',
            'P2798': 'hgnc', 'P351': 'entrez_gene', 'P2410': 'wikipathways'
        }
        
        hardcoded_props = set(database_properties.keys())
        wikidata_props = set(external_id_claims.keys())
        
        missing_from_tools = wikidata_props - hardcoded_props
        
        if missing_from_tools:
            print(f"   ⚠️  Properties in Wikidata but missing from tools: {missing_from_tools}")
            for prop_id in missing_from_tools:
                results["gaps_found"].append({
                    "entity": test_case['id'],
                    "missing_property": prop_id,
                    "value": external_id_claims[prop_id],
                    "reason": "not_in_hardcoded_mappings"
                })
        
    except Exception as e:
        print(f"   ❌ Error comparing Wikidata vs tools: {e}")

def print_reality_summary(results: Dict):
    """Print summary of what's working vs broken."""
    
    print("\n" + "=" * 70)
    print("📋 CROSS-REFERENCE EXTRACTION REALITY CHECK")
    print("=" * 70)
    
    print(f"\n✅ WORKING (Hardcoded mappings working): {len(results['hardcoded_working'])}")
    for item in results['hardcoded_working']:
        print(f"   • {item['entity']}: {item['property']} → {item['value']}")
    
    print(f"\n❌ BROKEN (Expected but missing): {len(results['hardcoded_missing'])}")
    for item in results['hardcoded_missing']:
        expected = "Expected" if item['expected_in_tools'] else "Not expected in current tools"
        print(f"   • {item['entity']}: {item['property']} → {item['value']} ({expected})")
    
    print(f"\n🕳️  GAPS (Properties in Wikidata but missing from tools): {len(results['gaps_found'])}")
    for item in results['gaps_found']:
        print(f"   • {item['entity']}: {item['missing_property']} → {item['value']}")
        print(f"     Reason: {item['reason']}")
    
    # Recommend fixes
    print(f"\n🔧 RECOMMENDED FIXES:")
    
    if results['gaps_found']:
        missing_props = set(item['missing_property'] for item in results['gaps_found'])
        print(f"   1. Add missing properties to hardcoded mappings: {missing_props}")
    
    if any(not item['expected_in_tools'] for item in results['hardcoded_missing']):
        print(f"   2. Build dynamic property discovery to replace hardcoded mappings")
    
    print(f"   3. Integration test should verify specific property extraction")

async def test_specific_wikipathways_case():
    """Test the specific WikiPathways case that's failing."""
    
    print("\n🎯 SPECIFIC TEST: WikiPathways P2410 Extraction")
    print("=" * 50)
    
    # Test the exact case we know fails
    entity_id = "Q44054606"  # Mouse glycogen metabolism
    expected_wp_id = "WP317"
    
    # First verify P2410 exists in raw Wikidata
    from cogitarelink.adapters.wikidata_client import WikidataClient
    
    client = WikidataClient(timeout=30)
    entity_data = await client.get_entities([entity_id])
    entity_info = entity_data['entities'][entity_id]
    
    # Check if P2410 exists in claims
    claims = entity_info.get('claims', {})
    p2410_claims = claims.get('P2410', [])
    
    if p2410_claims:
        actual_value = p2410_claims[0].get('mainsnak', {}).get('datavalue', {}).get('value')
        print(f"✅ P2410 exists in Wikidata: {actual_value}")
        
        if actual_value == expected_wp_id:
            print(f"✅ Value matches expected: {expected_wp_id}")
        else:
            print(f"❌ Value mismatch. Expected: {expected_wp_id}, Got: {actual_value}")
    else:
        print(f"❌ P2410 not found in Wikidata claims")
        return False
    
    # Test if current tools extract it
    from cogitarelink.cli.cl_describe import _extract_cross_references
    
    cross_refs = await _extract_cross_references(entity_info)
    
    # Check hardcoded mappings (copied from cl_describe.py)
    database_properties = {
        'P352': 'uniprot', 'P683': 'chebi', 'P231': 'cas', 'P592': 'chembl',
        'P715': 'drugbank', 'P486': 'mesh', 'P685': 'ncbi_gene', 'P594': 'ensembl_gene',
        'P637': 'refseq', 'P699': 'disease_ontology', 'P665': 'kegg', 'P232': 'ec_number',
        'P662': 'pubchem_cid', 'P2017': 'isomeric_smiles', 'P1579': 'pubchem_sid',
        'P638': 'pdb', 'P2892': 'umls', 'P233': 'smiles', 'P274': 'molecular_formula',
        'P2798': 'hgnc', 'P351': 'entrez_gene', 'P2410': 'wikipathways'
    }
    
    print(f"🔧 Current hardcoded mappings include P2410: {'P2410' in database_properties}")
    print(f"🔍 Tools extracted WikiPathways: {'wikipathways' in cross_refs}")
    
    if 'wikipathways' in cross_refs and expected_wp_id in str(cross_refs['wikipathways']):
        print(f"✅ SUCCESS: Tools correctly extracted WikiPathways {expected_wp_id}")
        return True
    else:
        print(f"❌ FAILURE: Tools did not extract WikiPathways {expected_wp_id}")
        print(f"   Available cross-refs: {list(cross_refs.keys())}")
        return False

async def main():
    """Run reality-based cross-reference tests."""
    
    print("🚀 Cross-Reference Extraction REALITY Tests")
    print("Testing what actually works vs what should work")
    print("=" * 70)
    
    # Test 1: Current reality check
    reality_results = await test_current_reality()
    
    # Test 2: Specific WikiPathways case
    wp_success = await test_specific_wikipathways_case()
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 REALITY TEST SUMMARY")
    print("=" * 70)
    
    working_count = len(reality_results['hardcoded_working'])
    missing_count = len(reality_results['hardcoded_missing'])
    gaps_count = len(reality_results['gaps_found'])
    
    print(f"✅ Working cross-references: {working_count}")
    print(f"❌ Missing cross-references: {missing_count}")
    print(f"🕳️  Discovery gaps: {gaps_count}")
    print(f"🎯 WikiPathways test: {'✅ PASS' if wp_success else '❌ FAIL'}")
    
    if gaps_count > 0 or not wp_success:
        print(f"\n🔧 NEXT STEPS:")
        print(f"   1. Fix hardcoded mappings to include missing properties")
        print(f"   2. Build dynamic property discovery system")  
        print(f"   3. Update integration tests to verify specific extractions")
    else:
        print(f"\n🎉 All tests passed! Cross-reference extraction is working correctly.")

if __name__ == "__main__":
    asyncio.run(main())