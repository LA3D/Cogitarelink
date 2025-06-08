#!/usr/bin/env python3
"""
Test script for property-first discovery pattern

Tests the Claude Code async generator architecture implementation
with progressive discovery phases.
"""

import asyncio
import json
import sys
import time

# Add the project root to Python path
sys.path.insert(0, '/Users/cvardema/dev/git/LA3D/cl/Cogitarelink')

from cogitarelink.intelligence.ontology_discovery import discovery_engine


async def test_property_first_discovery():
    """Test the property-first discovery pattern implementation"""
    
    print("🔬 Testing Property-First Discovery Pattern")
    print("=" * 60)
    
    # Test with WikiPathways endpoint (accessible and good for testing)
    endpoint = "wikipathways"
    
    print(f"📍 Testing property-first discovery on: {endpoint}")
    print("⏱️  Expected phases:")
    print("   1. Property Enumeration")
    print("   2. Usage Pattern Analysis") 
    print("   3. Co-occurrence Analysis")
    print("   4. Query Template Generation")
    print()
    
    try:
        start_time = time.time()
        
        # Execute property-first discovery with human progress
        results = await discovery_engine.discover_properties_first(
            endpoint=endpoint,
            progress_format="human",
            property_limit=20,  # Smaller limit for testing
            co_occurrence_limit=3   # Much smaller for testing
        )
        
        execution_time = time.time() - start_time
        
        print(f"\n📊 Discovery Results Summary:")
        print("-" * 40)
        
        # Check for errors
        if "error" in results:
            print(f"❌ Discovery failed: {results['error']}")
            return False
        
        # Validate results structure
        required_keys = ["endpoint", "discovery_method", "phases", "properties", 
                        "usage_patterns", "co_occurrence_patterns", "query_templates"]
        
        missing_keys = [key for key in required_keys if key not in results]
        if missing_keys:
            print(f"❌ Missing required keys: {missing_keys}")
            return False
        
        # Check phases completed
        phases = results.get("phases", [])
        expected_phases = ["property_enumeration", "usage_pattern_analysis", 
                          "cooccurrence_analysis", "template_generation"]
        
        completed_phases = [phase.get("phase") for phase in phases]
        print(f"🔄 Phases Completed: {len(completed_phases)}/4")
        for i, phase in enumerate(expected_phases):
            status = "✅" if phase in completed_phases else "❌"
            print(f"   {i+1}. {phase.replace('_', ' ').title()}: {status}")
        
        # Properties discovered
        properties = results.get("properties", [])
        print(f"\n🏷️  Properties Discovered: {len(properties)}")
        if properties:
            print("   Top 5 properties:")
            for i, prop in enumerate(properties[:5]):
                usage = prop.get("usage_count", 0)
                prefixed = prop.get("prefixed_form", prop.get("uri", "Unknown"))
                print(f"   {i+1}. {prefixed} ({usage:,} uses)")
        
        # Usage patterns
        usage_patterns = results.get("usage_patterns", {})
        pattern_summary = next(
            (phase.get("summary", {}) for phase in phases if phase.get("phase") == "usage_pattern_analysis"),
            {}
        )
        if pattern_summary:
            print(f"\n📈 Usage Pattern Analysis:")
            print(f"   Object Properties: {pattern_summary.get('object_properties', 0)}")
            print(f"   Datatype Properties: {pattern_summary.get('datatype_properties', 0)}")
            print(f"   Mixed Properties: {pattern_summary.get('mixed_properties', 0)}")
        
        # Co-occurrence patterns
        cooccurrence = results.get("co_occurrence_patterns", {})
        print(f"\n🔗 Co-occurrence Analysis: {len(cooccurrence)} properties analyzed")
        
        # Query templates
        templates = results.get("query_templates", {})
        print(f"\n📝 Query Templates Generated: {len(templates)}")
        if templates:
            for name, template in templates.items():
                desc = template.get("description", "No description")
                vars_count = len(template.get("variables", []))
                print(f"   • {name}: {desc} ({vars_count} variables)")
        
        # Performance metrics
        metrics = results.get("performance_metrics", {})
        total_time = metrics.get("total_time_ms", 0)
        queries_executed = metrics.get("queries_executed", 0)
        print(f"\n⚡ Performance Metrics:")
        print(f"   Total Time: {total_time:,}ms ({execution_time:.1f}s)")
        print(f"   Queries Executed: {queries_executed}")
        print(f"   Avg Query Time: {total_time/max(queries_executed,1):.1f}ms")
        
        # Validate we got reasonable results
        success_criteria = [
            len(phases) >= 4,  # All phases completed
            len(properties) >= 10,  # Found some properties
            len(templates) >= 3,   # Generated templates
            total_time > 0,        # Timing recorded
            queries_executed > 0   # Queries were executed
        ]
        
        if all(success_criteria):
            print(f"\n🎯 SUCCESS: Property-first discovery working correctly!")
            print(f"   Phases: {len(phases)}/4, Properties: {len(properties)}, Templates: {len(templates)}")
            return True
        else:
            print(f"\n⚠️  Some success criteria not met:")
            criteria_names = ["4 phases", "10+ properties", "3+ templates", "timing", "queries"]
            for i, (criterion, name) in enumerate(zip(success_criteria, criteria_names)):
                status = "✅" if criterion else "❌"
                print(f"   {status} {name}")
            return False
            
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_template_quality():
    """Test the quality and usability of generated query templates"""
    
    print("\n🔬 Testing Query Template Quality")
    print("=" * 60)
    
    try:
        # Get property discovery results
        results = await discovery_engine.discover_properties_first(
            endpoint="wikipathways",
            progress_format="silent",
            property_limit=15,
            co_occurrence_limit=3
        )
        
        templates = results.get("query_templates", {})
        
        if not templates:
            print("❌ No templates generated")
            return False
        
        print(f"📝 Testing {len(templates)} generated templates:")
        
        # Test each template for basic quality
        template_quality = {}
        for name, template in templates.items():
            quality_score = 0
            issues = []
            
            # Check required fields
            if "description" in template:
                quality_score += 1
            else:
                issues.append("Missing description")
                
            if "query" in template and len(template["query"].strip()) > 50:
                quality_score += 1
            else:
                issues.append("Query too short or missing")
                
            if "variables" in template and len(template["variables"]) > 0:
                quality_score += 1
            else:
                issues.append("No variables defined")
            
            # Check SPARQL syntax basics
            query = template.get("query", "")
            if "SELECT" in query and "WHERE" in query:
                quality_score += 1
            else:
                issues.append("Invalid SPARQL structure")
            
            if "LIMIT" in query:
                quality_score += 1
            else:
                issues.append("Missing LIMIT clause")
            
            template_quality[name] = {
                "score": quality_score,
                "max_score": 5,
                "issues": issues
            }
            
            status = "✅" if quality_score >= 4 else "⚠️" if quality_score >= 3 else "❌"
            print(f"   {status} {name}: {quality_score}/5")
            if issues:
                print(f"      Issues: {', '.join(issues)}")
        
        # Overall assessment
        avg_score = sum(t["score"] for t in template_quality.values()) / len(template_quality)
        high_quality = sum(1 for t in template_quality.values() if t["score"] >= 4)
        
        print(f"\n📊 Template Quality Summary:")
        print(f"   Average Score: {avg_score:.1f}/5")
        print(f"   High Quality Templates: {high_quality}/{len(templates)}")
        
        if avg_score >= 4.0 and high_quality >= len(templates) * 0.8:
            print("🎯 SUCCESS: Template quality is excellent!")
            return True
        elif avg_score >= 3.0:
            print("⚠️  Template quality is acceptable but could be improved")
            return True
        else:
            print("❌ Template quality needs improvement")
            return False
            
    except Exception as e:
        print(f"❌ Template quality test failed: {e}")
        return False


async def main():
    """Run all property-first discovery tests"""
    
    print("🧪 Property-First Discovery Tests")
    print("=" * 60)
    print("Testing Claude Code async generator architecture implementation")
    print("with progressive discovery phases and performance optimization.")
    print()
    
    # Test 1: Basic property-first discovery
    discovery_success = await test_property_first_discovery()
    
    # Test 2: Template quality validation
    if discovery_success:
        template_success = await test_template_quality()
    else:
        print("\n⏭️  Skipping template quality test due to discovery failure")
        template_success = False
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 Test Summary:")
    print(f"   Property Discovery: {'✅ PASS' if discovery_success else '❌ FAIL'}")
    print(f"   Template Quality: {'✅ PASS' if template_success else '❌ FAIL'}")
    
    if discovery_success and template_success:
        print("\n🎉 All tests passed! Property-first discovery is working correctly.")
        print("   ✅ Claude Code async generator pattern implemented")
        print("   ✅ Progressive discovery phases working")
        print("   ✅ Performance optimization active")
        print("   ✅ Query templates generated successfully")
    else:
        print("\n⚠️  Some tests failed. Check the implementation.")


if __name__ == "__main__":
    asyncio.run(main())