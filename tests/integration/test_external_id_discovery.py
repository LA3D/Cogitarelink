#!/usr/bin/env python3
"""
Test script for external identifier pattern discovery

Tests the discovery state machine we implemented based on the experimental workflow.
"""

import asyncio
import json
import sys
import os

# Add the project root to Python path
sys.path.insert(0, '/Users/cvardema/dev/git/LA3D/cl/Cogitarelink')

from cogitarelink.intelligence.ontology_discovery import discovery_engine


async def test_external_id_discovery():
    """Test the external identifier pattern discovery with P01308 → UniProt"""
    
    print("🔬 Testing External Identifier Pattern Discovery")
    print("=" * 60)
    
    # Test the exact pattern we discovered manually: P01308 in UniProt
    external_id = "P01308"
    endpoint = "uniprot"
    id_type = "uniprot"
    
    print(f"📍 Testing: {external_id} → {endpoint} ({id_type})")
    print()
    
    try:
        # Execute discovery
        results = await discovery_engine.discover_external_identifier_patterns(
            endpoint=endpoint,
            external_id=external_id,
            id_property=id_type,
            progress_format="human"
        )
        
        print("\n📊 Discovery Results:")
        print("-" * 30)
        
        if "error" in results:
            print(f"❌ Discovery failed: {results['error']}")
            return False
        
        # Check URI patterns
        uri_patterns = results.get("uri_patterns", [])
        print(f"🔗 URI Patterns Found: {len(uri_patterns)}")
        for i, pattern in enumerate(uri_patterns):
            print(f"   {i+1}. {pattern.get('example_uri', 'N/A')}")
            print(f"      Pattern: {pattern.get('pattern', 'N/A')}")
            print(f"      Method: {pattern.get('search_method', 'N/A')}")
            print(f"      Confidence: {pattern.get('confidence', 0):.2f}")
        
        # Check validated patterns
        validated = results.get("validated_patterns", [])
        print(f"\n✅ Validated Patterns: {len(validated)}")
        for i, pattern in enumerate(validated):
            print(f"   {i+1}. {pattern.get('example_uri', 'N/A')}")
            print(f"      Properties: {pattern.get('property_count', 0)}")
            print(f"      Status: {pattern.get('validation_status', 'N/A')}")
        
        # Check discovered properties
        properties = results.get("properties", [])
        print(f"\n🏷️  Properties Discovered: {len(properties)}")
        for i, prop in enumerate(properties[:5]):  # Show top 5
            print(f"   {i+1}. {prop.get('prefixed_form', 'N/A')} (used {prop.get('usage_count', 0)} times)")
        
        # Check query templates
        templates = results.get("query_templates", {})
        print(f"\n📝 Query Templates: {len(templates)}")
        for name, template in templates.items():
            print(f"   • {name}: {template.get('description', 'N/A')}")
        
        # Validate the expected pattern
        expected_uri = "http://purl.uniprot.org/uniprot/P01308"
        found_expected = any(expected_uri in pattern.get("example_uri", "") for pattern in validated)
        
        if found_expected:
            print(f"\n🎯 SUCCESS: Found expected URI pattern {expected_uri}")
            return True
        else:
            print(f"\n⚠️  Expected URI pattern {expected_uri} not found")
            print("   Available URIs:")
            for pattern in validated:
                print(f"   - {pattern.get('example_uri', 'N/A')}")
            return False
            
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_simple_discovery():
    """Test basic discovery functionality"""
    
    print("\n🔬 Testing Basic Discovery Functionality")
    print("=" * 60)
    
    try:
        # Test basic schema discovery first
        schema = await discovery_engine.discover_schema("uniprot", "auto")
        
        print(f"📊 Basic Schema Discovery Results:")
        print(f"   Vocabularies: {len(schema.vocabularies)}")
        print(f"   Classes: {len(schema.classes)}")
        print(f"   Properties: {len(schema.properties)}")
        print(f"   Method: {schema.discovery_metadata.get('method', 'N/A')}")
        
        # Check if we have the expected UniProt vocabularies
        expected_vocabs = ['up', 'rdfs', 'taxon']
        found_vocabs = [v for v in expected_vocabs if v in schema.vocabularies]
        
        print(f"   Expected vocabularies found: {found_vocabs}")
        
        if len(found_vocabs) >= 2:
            print("✅ Basic discovery working")
            return True
        else:
            print("⚠️  Basic discovery has limited results")
            return False
            
    except Exception as e:
        print(f"❌ Basic discovery failed: {e}")
        return False


async def main():
    """Run all discovery tests"""
    
    print("🧪 External Identifier Pattern Discovery Tests")
    print("=" * 60)
    
    # Test 1: Basic discovery
    basic_success = await test_simple_discovery()
    
    # Test 2: External ID pattern discovery
    if basic_success:
        pattern_success = await test_external_id_discovery()
    else:
        print("\n⏭️  Skipping pattern discovery test due to basic discovery failure")
        pattern_success = False
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 Test Summary:")
    print(f"   Basic Discovery: {'✅ PASS' if basic_success else '❌ FAIL'}")
    print(f"   Pattern Discovery: {'✅ PASS' if pattern_success else '❌ FAIL'}")
    
    if basic_success and pattern_success:
        print("\n🎉 All tests passed! External identifier pattern discovery is working.")
    else:
        print("\n⚠️  Some tests failed. Check the implementation.")


if __name__ == "__main__":
    asyncio.run(main())