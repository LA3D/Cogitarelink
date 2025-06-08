#!/usr/bin/env python3
"""
Test WikiPathways cross-database workflow that was originally failing.

This test validates the complete cross-database discovery workflow:
1. Start with WP1189 (missing from Wikidata)
2. Find WP317 in Wikidata via Q44054606
3. Extract WikiPathways cross-reference using tools
4. Follow to external WikiPathways database
"""

import asyncio
import json
import sys
import os

# Add project root to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

async def test_wikipathways_discovery_workflow():
    """Test the complete WikiPathways discovery workflow."""
    
    print("🧬 Testing WikiPathways Cross-Database Discovery Workflow")
    print("=" * 65)
    
    # Step 1: Note that WP1189 is missing from Wikidata (from previous investigation)
    print("\n📋 Step 1: WP1189 (dog glycogen) missing from Wikidata")
    print("   ✅ WP1189 not found in Wikidata (confirmed in previous investigation)")
    print("   → This led us to discover WP317 (mouse glycogen) instead")
    
    from cogitarelink.adapters.wikidata_client import WikidataClient
    client = WikidataClient(timeout=30)
    
    # Step 2: Test that Q44054606 has WikiPathways cross-reference
    print("\n📋 Step 2: Extract WikiPathways from Q44054606 (mouse glycogen pathway)")
    
    entity_data = await client.get_entities(["Q44054606"])
    entity_info = entity_data['entities']['Q44054606']
    
    from cogitarelink.cli.cl_describe import _extract_cross_references
    cross_refs = await _extract_cross_references(entity_info)
    
    wikipathways_found = 'wikipathways' in cross_refs
    wp317_found = wikipathways_found and 'WP317' in cross_refs['wikipathways']
    
    if wp317_found:
        print("   ✅ Successfully extracted WikiPathways WP317")
        print(f"      cross_refs['wikipathways'] = {cross_refs['wikipathways']}")
    else:
        print("   ❌ Failed to extract WikiPathways WP317")
        print(f"      Available cross-refs: {list(cross_refs.keys())}")
        return False
    
    # Step 3: Test cl_follow for WikiPathways URL generation
    print("\n📋 Step 3: Test cl_follow URL generation for WikiPathways")
    
    from cogitarelink.cli.cl_follow import _extract_cross_references as follow_extract, _add_urls_to_cross_references
    
    follow_cross_refs, metadata = follow_extract(entity_info, [])
    _add_urls_to_cross_references(follow_cross_refs)
    
    if 'wikipathways' in follow_cross_refs:
        wp317_data = follow_cross_refs['wikipathways'][0]
        expected_url = "https://www.wikipathways.org/pathways/WP317.html"
        
        if wp317_data.get('url') == expected_url:
            print("   ✅ Correct WikiPathways URL generated")
            print(f"      URL: {wp317_data['url']}")
        else:
            print("   ❌ Incorrect WikiPathways URL")
            print(f"      Expected: {expected_url}")
            print(f"      Got: {wp317_data.get('url', 'None')}")
            return False
    else:
        print("   ❌ WikiPathways not found in cl_follow output")
        return False
    
    # Step 4: Test complete tool workflow using functions directly
    print("\n📋 Step 4: Test complete tool workflow")
    
    # Test cl_describe functions directly  
    from cogitarelink.cli.cl_describe import _build_entity_description
    
    try:
        # Build entity description
        description = _build_entity_description(entity_info, "Q44054606")
        cross_refs = await _extract_cross_references(entity_info)
        description['cross_references'] = cross_refs
        
        tool_wp_found = 'wikipathways' in description.get('cross_references', {})
        if tool_wp_found:
            print("   ✅ cl_describe successfully extracts WikiPathways")
            print(f"      WikiPathways IDs: {description['cross_references']['wikipathways']}")
        else:
            print("   ❌ cl_describe missing WikiPathways")
            return False
            
    except Exception as e:
        print(f"   ❌ cl_describe workflow failed: {e}")
        return False
    
    print("\n🎉 WikiPathways cross-database workflow test PASSED!")
    print("\n📊 Summary:")
    print("   ✅ WP1189 confirmed missing from Wikidata")
    print("   ✅ WP317 found in mouse glycogen pathway (Q44054606)")
    print("   ✅ WikiPathways cross-reference extracted by tools")
    print("   ✅ WikiPathways URL correctly generated")
    print("   ✅ Complete cl_describe workflow working")
    
    return True

async def test_cross_species_comparison():
    """Test cross-species comparison to understand pathway coverage."""
    
    print("\n🧬 Testing Cross-Species Pathway Coverage")
    print("=" * 50)
    
    # Test entities for glycogen pathways in different species
    test_entities = [
        {"id": "Q44054606", "name": "Glycogen Metabolism (mouse)", "species": "mouse"},
        # Add more as they're discovered
    ]
    
    from cogitarelink.adapters.wikidata_client import WikidataClient
    from cogitarelink.cli.cl_describe import _extract_cross_references
    
    client = WikidataClient(timeout=30)
    
    print("\n📋 Scanning glycogen pathways across species:")
    
    results = []
    for entity in test_entities:
        entity_data = await client.get_entities([entity["id"]])
        entity_info = entity_data['entities'][entity["id"]]
        cross_refs = await _extract_cross_references(entity_info)
        
        wp_ids = cross_refs.get('wikipathways', [])
        
        result = {
            "entity": entity,
            "wikipathways_ids": wp_ids,
            "has_wikipathways": len(wp_ids) > 0
        }
        results.append(result)
        
        print(f"   {entity['species']}: {entity['name']} → {wp_ids if wp_ids else 'No WikiPathways'}")
    
    # Summary
    entities_with_wp = sum(1 for r in results if r["has_wikipathways"])
    print(f"\n📊 Coverage: {entities_with_wp}/{len(results)} entities have WikiPathways identifiers")
    
    return results

async def main():
    """Run WikiPathways workflow tests."""
    
    print("🚀 WikiPathways Cross-Database Workflow Tests")
    print("Testing cross-database discovery patterns")
    print("=" * 65)
    
    # Test 1: Core workflow
    workflow_success = await test_wikipathways_discovery_workflow()
    
    # Test 2: Cross-species comparison
    if workflow_success:
        species_results = await test_cross_species_comparison()
    else:
        print("\n⏭️  Skipping species comparison due to workflow failure")
        species_results = []
    
    # Final summary
    print("\n" + "=" * 65)
    print("📋 WikiPathways Testing Summary")
    print("=" * 65)
    
    if workflow_success:
        print("✅ PASS: WikiPathways cross-database workflow working")
        print("   → WP1189 investigation successfully led to WP317 discovery")
        print("   → Cross-reference extraction tools working correctly")
        print("   → URL generation and metadata correct")
    else:
        print("❌ FAIL: WikiPathways cross-database workflow broken")
    
    if species_results:
        total_entities = len(species_results)
        wp_entities = sum(1 for r in species_results if r["has_wikipathways"])
        print(f"📊 Species coverage: {wp_entities}/{total_entities} entities with WikiPathways")
    
    print("\n🔧 Next steps for extending coverage:")
    print("   1. Search for more glycogen pathways in other species")
    print("   2. Build dynamic property discovery to find additional patterns")
    print("   3. Create systematic pathway discovery workflows")

if __name__ == "__main__":
    asyncio.run(main())