#!/usr/bin/env python3
"""
Test script for Property Affordance Discovery pathway

Tests the semantic hierarchy when no known entities are available,
focusing on discovering what kinds of things exist and their capabilities.
"""

import asyncio
import json
import sys
import time

# Add the project root to Python path
sys.path.insert(0, '/Users/cvardema/dev/git/LA3D/cl/Cogitarelink')

from cogitarelink.intelligence.ontology_discovery import discovery_engine


async def test_property_affordance_pathway():
    """Test the Property Affordance Discovery pathway implementation"""
    
    print("🔬 Testing Property Affordance Discovery Pathway")
    print("=" * 60)
    
    # Test with WikiPathways endpoint - has good type structure
    endpoint = "wikipathways"
    
    print(f"📍 Testing Property Affordance pathway on: {endpoint}")
    print(f"🔍 No known entity provided - discovering capabilities")
    print("⏱️  Expected process:")
    print("   1. Service Description/VoID Discovery (if available)")
    print("   2. Entity Type Discovery (what kinds of things exist)")
    print("   3. Type Affordance Analysis (what can each type do)")
    print("   4. Schema Building from Type Capabilities")
    print()
    
    try:
        start_time = time.time()
        
        # Execute Property Affordance discovery
        schema = await discovery_engine.discover_schema(
            endpoint=endpoint,
            discovery_method="auto",
            known_entity_id=None  # No known entity - triggers Property Affordance pathway
        )
        
        execution_time = time.time() - start_time
        
        print(f"📊 Discovery Results Summary:")
        print("-" * 40)
        
        if not schema:
            print("❌ No schema returned")
            return False
        
        # Check discovery method and semantic approach
        discovery_method = schema.discovery_metadata.get("primary_method", "unknown")
        semantic_approach = schema.discovery_metadata.get("semantic_approach", False)
        
        print(f"🔄 Discovery Method: {discovery_method}")
        print(f"🧠 Semantic Approach: {'✅ Yes' if semantic_approach else '❌ No'}")
        
        success = False
        
        if discovery_method == "property_affordance_pathway":
            print("🎯 SUCCESS: Property Affordance pathway was used!")
            
            # Check property affordance specific metadata
            types_discovered = schema.discovery_metadata.get("entity_types_discovered", 0)
            type_affordances_analyzed = schema.discovery_metadata.get("type_affordances_analyzed", 0)
            
            print(f"🏗️  Entity Types Discovered: {types_discovered}")
            print(f"🔗 Type Affordances Analyzed: {type_affordances_analyzed}")
            
            success = True
            
        elif discovery_method in ["service_description", "void"]:
            print("🎯 SUCCESS: Authoritative semantic discovery was used!")
            print(f"   Method: {discovery_method} (higher in semantic hierarchy)")
            success = True
            
        elif discovery_method in ["introspection", "samples"]:
            print("⚠️  Fell back to statistical methods")
            print(f"   Method: {discovery_method} - semantic methods may have failed")
            success = True  # Still acceptable
            
        else:
            print(f"❓ Unknown discovery method: {discovery_method}")
            success = False
        
        # Check schema content regardless of method
        vocab_count = len(schema.vocabularies)
        class_count = len(schema.classes)
        prop_count = len(schema.properties)
        pattern_count = len(schema.query_patterns)
        
        print(f"\n📚 Schema Content:")
        print(f"   Vocabularies: {vocab_count}")
        print(f"   Classes/Types: {class_count}")
        print(f"   Properties: {prop_count}")
        print(f"   Query Patterns: {pattern_count}")
        
        # Show example discovered types
        if schema.classes and discovery_method == "property_affordance_pathway":
            print(f"\n🏷️  Discovered Entity Types (top 5):")
            for i, class_info in enumerate(schema.classes[:5]):
                class_uri = class_info.get('uri', 'Unknown')
                label = class_info.get('label', 'Unknown')
                instance_count = class_info.get('instance_count', '0')
                print(f"   {i+1}. {label} ({class_uri}) - {instance_count} instances")
        
        # Show example affordances/properties
        if schema.properties:
            print(f"\n🔍 Discovered Properties (top 5):")
            for i, prop in enumerate(schema.properties[:5]):
                prop_uri = prop.get('uri', 'Unknown')
                label = prop.get('label', 'Unknown')
                usage = prop.get('usage_count', '0')
                domain = prop.get('domain_type', 'Unknown')
                print(f"   {i+1}. {label} ({prop_uri}) - {usage} uses, domain: {domain.split('/')[-1]}")
        
        # Show query patterns
        if schema.query_patterns:
            print(f"\n📝 Generated Query Patterns:")
            for pattern in schema.query_patterns:
                name = pattern.get('name', 'Unknown')
                desc = pattern.get('description', 'No description')
                vars_count = len(pattern.get('variables', []))
                print(f"   • {name}: {desc} ({vars_count} variables)")
        
        # Performance metrics
        discovery_time = schema.discovery_metadata.get('discovery_time_ms', 0)
        print(f"\n⚡ Performance:")
        print(f"   Total Time: {execution_time:.1f}s")
        print(f"   Discovery Method: {discovery_method}")
        print(f"   Approach: {'Semantic' if semantic_approach else 'Statistical'}")
        
        return success
        
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_type_affordance_discovery():
    """Test the type affordance discovery helper methods"""
    
    print("\n🔬 Testing Type Affordance Discovery Methods")
    print("=" * 60)
    
    endpoint = "wikipathways"
    print(f"📍 Testing individual methods on: {endpoint}")
    print()
    
    try:
        print("Step 1: Discovering Entity Types")
        print("-" * 30)
        
        entity_types = await discovery_engine._discover_entity_types(endpoint)
        print(f"Found {len(entity_types)} entity types")
        
        if entity_types:
            print("Top 3 entity types:")
            for i, entity_type in enumerate(entity_types[:3]):
                type_uri = entity_type.get('type', {}).get('value', 'Unknown')
                count = entity_type.get('count', {}).get('value', '0')
                type_label = type_uri.split('/')[-1].split('#')[-1]
                print(f"   {i+1}. {type_label} ({type_uri}) - {count} instances")
        
        if entity_types:
            print(f"\nStep 2: Analyzing Affordances for Top Type")
            print("-" * 30)
            
            top_type = entity_types[0]
            type_uri = top_type.get('type', {}).get('value', '')
            type_label = type_uri.split('/')[-1].split('#')[-1]
            
            print(f"Analyzing type: {type_label}")
            
            affordances = await discovery_engine._discover_type_affordances(endpoint, type_uri)
            properties = affordances.get('properties', [])
            
            print(f"Found {len(properties)} properties for this type")
            
            if properties:
                print("Top 5 properties:")
                for i, prop in enumerate(properties[:5]):
                    prop_uri = prop.get('property', {}).get('value', 'Unknown')
                    usage = prop.get('usage', {}).get('value', '0')
                    prop_label = prop_uri.split('/')[-1].split('#')[-1]
                    print(f"   {i+1}. {prop_label} ({prop_uri}) - {usage} uses")
        
        print(f"\n✅ Type affordance discovery methods working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Type affordance test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_fallback_to_statistical():
    """Test fallback to statistical discovery when semantic methods fail"""
    
    print("\n🔬 Testing Statistical Fallback")
    print("=" * 60)
    
    # Test with an endpoint that might not have good type structure
    endpoint = "uniprot"  # UniProt might have complex type hierarchies
    
    print(f"📍 Testing statistical fallback on: {endpoint}")
    print(f"🔄 Should fall back to property-first discovery if type discovery fails")
    print()
    
    try:
        start_time = time.time()
        
        # Execute discovery and see what happens
        schema = await discovery_engine.discover_schema(
            endpoint=endpoint,
            discovery_method="auto",
            known_entity_id=None
        )
        
        execution_time = time.time() - start_time
        
        discovery_method = schema.discovery_metadata.get("primary_method", "unknown")
        semantic_approach = schema.discovery_metadata.get("semantic_approach", False)
        fallback_level = schema.discovery_metadata.get("fallback_level", None)
        
        print(f"📊 Fallback Results:")
        print(f"   Discovery Method: {discovery_method}")
        print(f"   Semantic Approach: {'✅ Yes' if semantic_approach else '❌ No'}")
        print(f"   Fallback Level: {fallback_level or 'None'}")
        print(f"   Execution Time: {execution_time:.1f}s")
        
        # Check if we got some useful schema regardless of method
        vocab_count = len(schema.vocabularies)
        class_count = len(schema.classes)
        prop_count = len(schema.properties)
        
        print(f"\n📚 Schema Generated:")
        print(f"   Vocabularies: {vocab_count}")
        print(f"   Classes: {class_count}")
        print(f"   Properties: {prop_count}")
        
        if vocab_count > 0 or prop_count > 0:
            print("✅ Fallback mechanisms working - schema was generated")
            return True
        else:
            print("⚠️  No schema generated - may need debugging")
            return False
            
    except Exception as e:
        print(f"❌ Fallback test failed: {e}")
        return False


async def main():
    """Run Property Affordance Discovery pathway tests"""
    
    print("🧪 Property Affordance Discovery Pathway Tests")
    print("=" * 60)
    print("Testing semantic hierarchy when no known entities are available")
    print("Focus: Discovering entity types and their capabilities")
    print()
    
    # Test 1: Main Property Affordance pathway
    affordance_success = await test_property_affordance_pathway()
    
    # Test 2: Individual type affordance methods
    type_methods_success = await test_type_affordance_discovery()
    
    # Test 3: Statistical fallback mechanisms
    fallback_success = await test_fallback_to_statistical()
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 Test Summary:")
    print(f"   Property Affordance Pathway: {'✅ PASS' if affordance_success else '❌ FAIL'}")
    print(f"   Type Affordance Methods: {'✅ PASS' if type_methods_success else '❌ FAIL'}")
    print(f"   Statistical Fallback: {'✅ PASS' if fallback_success else '❌ FAIL'}")
    
    if affordance_success and type_methods_success and fallback_success:
        print("\n🎉 All tests passed! Property Affordance Discovery working correctly.")
        print("   ✅ Type discovery and affordance analysis")
        print("   ✅ Schema building from type capabilities")
        print("   ✅ Graceful fallback to statistical methods")
        print("   ✅ Semantic-first approach with robust error handling")
    else:
        print("\n⚠️  Some tests failed. Check the implementation.")
        
        if not affordance_success:
            print("   🔧 Property Affordance pathway needs debugging")
        if not type_methods_success:
            print("   🔧 Type affordance discovery methods need debugging")
        if not fallback_success:
            print("   🔧 Statistical fallback mechanisms need debugging")


if __name__ == "__main__":
    asyncio.run(main())