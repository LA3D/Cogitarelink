#!/usr/bin/env python3
"""
Comprehensive integration test suite for ontology dereferencing use cases

Tests different ontology patterns, formats, and challenges including:
- Standard RDF ontologies (FOAF, Dublin Core)
- JSON-LD with content negotiation (Schema.org)
- Different content types and patterns
- Error handling and fallback strategies
- Domain-specific strategy requirements

This test suite validates the HTTP-based ontology dereferencing functionality
implemented in cl_ontfetch with RDFLib integration and Claude-friendly output.
"""

import pytest

from cogitarelink.cli.cl_ontfetch import AgenticOntologyFetcher


class OntologyTestCase:
    """Test case for a specific ontology"""
    
    def __init__(self, uri: str, name: str, expected_format: str, expected_features: dict, 
                 special_strategies: list = None, should_succeed: bool = True):
        self.uri = uri
        self.name = name
        self.expected_format = expected_format
        self.expected_features = expected_features
        self.special_strategies = special_strategies or []
        self.should_succeed = should_succeed


# Define test cases for different ontology patterns
TEST_CASES = [
    OntologyTestCase(
        uri="http://xmlns.com/foaf/0.1/",
        name="FOAF (Friend of a Friend)",
        expected_format="application/ld+json",
        expected_features={
            "properties": {"min": 50, "object_props": True, "data_props": True},
            "classes": {"min": 10},
            "vocabularies": {"min": 5}
        },
        should_succeed=True
    ),
    
    OntologyTestCase(
        uri="http://purl.org/dc/elements/1.1/",
        name="Dublin Core Elements",
        expected_format="text/turtle",
        expected_features={
            "properties": {"min": 10, "metadata": True},
            "classes": {"min": 0},  # DC Elements may not have classes
            "vocabularies": {"min": 5}
        },
        should_succeed=True
    ),
    
    OntologyTestCase(
        uri="https://schema.org/",
        name="Schema.org",
        expected_format="application/ld+json",
        expected_features={
            "properties": {"min": 100, "structured_data": True},
            "classes": {"min": 50},
            "vocabularies": {"min": 1}
        },
        special_strategies=[
            "schema_org_jsonld_context",
            "schema_org_all_layers", 
            "schema_org_specific_versions"
        ],
        should_succeed=True  # Should work with special handling
    ),
    
    OntologyTestCase(
        uri="http://www.w3.org/2004/02/skos/core#",
        name="SKOS Core",
        expected_format="application/rdf+xml",
        expected_features={
            "properties": {"min": 20, "concept_relations": True},
            "classes": {"min": 5},
            "vocabularies": {"min": 3}
        },
        should_succeed=True
    ),
    
    OntologyTestCase(
        uri="http://purl.org/ontology/bibo/",
        name="Bibliographic Ontology (BIBO)",
        expected_format="application/rdf+xml",
        expected_features={
            "properties": {"min": 30, "bibliographic": True},
            "classes": {"min": 20},
            "vocabularies": {"min": 5}
        },
        should_succeed=True
    ),
    
    OntologyTestCase(
        uri="http://example.com/nonexistent/ontology/",
        name="Non-existent Ontology",
        expected_format="none",
        expected_features={},
        should_succeed=False
    )
]


async def test_ontology_case(fetcher: AgenticOntologyFetcher, test_case: OntologyTestCase) -> dict:
    """Test a specific ontology case"""
    
    print(f"\n📍 Testing: {test_case.name}")
    print(f"🌐 URI: {test_case.uri}")
    print(f"📋 Expected: {test_case.expected_format} format")
    print("-" * 60)
    
    result_summary = {
        "name": test_case.name,
        "uri": test_case.uri,
        "success": False,
        "method_used": None,
        "issues": [],
        "recommendations": []
    }
    
    try:
        # Test the HTTP dereferencing
        result = await fetcher.discover_ontology(
            target=test_case.uri,
            ontology_type="discover",
            domain=None,
            force_refresh=True
        )
        
        if result.get("success"):
            print("✅ SUCCESS: HTTP dereferencing worked!")
            result_summary["success"] = True
            
            metadata = result.get("metadata", {})
            ontology_type = result.get("ontology_type", "unknown")
            result_summary["method_used"] = ontology_type
            
            if ontology_type == "http_dereferenced":
                # Analyze dereferencing quality
                await _analyze_dereferencing_quality(result, test_case, result_summary)
            else:
                print(f"ℹ️  Used fallback method: {ontology_type}")
                result_summary["method_used"] = f"fallback_{ontology_type}"
                
        else:
            error = result.get("error", {})
            error_code = error.get("code", "UNKNOWN")
            error_message = error.get("message", "Unknown error")
            
            print(f"❌ FAILED: {error_code}")
            print(f"   {error_message}")
            
            result_summary["issues"].append(f"{error_code}: {error_message}")
            
            # Analyze failure and suggest improvements
            await _analyze_failure(result, test_case, result_summary)
            
            if not test_case.should_succeed:
                print("✅ Expected failure - test case working correctly")
                result_summary["success"] = True  # Expected failure
    
    except Exception as e:
        print(f"❌ Exception occurred: {e}")
        result_summary["issues"].append(f"Exception: {str(e)}")
        import traceback
        traceback.print_exc()
    
    return result_summary


async def _analyze_dereferencing_quality(result: dict, test_case: OntologyTestCase, summary: dict):
    """Analyze the quality of successful dereferencing"""
    
    metadata = result.get("metadata", {})
    properties = result.get("properties", [])
    classes = result.get("classes", [])
    vocabularies = result.get("vocabularies", [])
    
    # Show basic metrics
    content_type = metadata.get("content_type", "unknown")
    triples_count = metadata.get("triples_count", 0)
    successful_uri = metadata.get("successful_uri", test_case.uri)
    
    print(f"🌐 Content Type: {content_type}")
    print(f"📊 RDF Triples: {triples_count}")
    print(f"✅ Successful URI: {successful_uri}")
    
    print(f"\n📚 Discovered Content:")
    print(f"   Properties: {len(properties)}")
    print(f"   Classes: {len(classes)}")
    print(f"   Vocabularies: {len(vocabularies)}")
    
    # Validate against expected features
    expected = test_case.expected_features
    issues = []
    
    if "properties" in expected:
        prop_expected = expected["properties"]
        if len(properties) < prop_expected.get("min", 0):
            issues.append(f"Properties: expected min {prop_expected['min']}, got {len(properties)}")
        
        # Check for specific property types
        if prop_expected.get("object_props"):
            object_props = [p for p in properties if 'ObjectProperty' in p.get('property_type', '')]
            if not object_props:
                issues.append("Expected ObjectProperties but none found")
            else:
                print(f"   🌐 Object Properties: {len(object_props)}")
        
        if prop_expected.get("data_props"):
            data_props = [p for p in properties if 'DatatypeProperty' in p.get('property_type', '')]
            if not data_props:
                issues.append("Expected DatatypeProperties but none found")
            else:
                print(f"   📊 Data Properties: {len(data_props)}")
    
    if "classes" in expected:
        class_expected = expected["classes"]
        if len(classes) < class_expected.get("min", 0):
            issues.append(f"Classes: expected min {class_expected['min']}, got {len(classes)}")
    
    # Show Claude guidance quality
    claude_guidance = metadata.get("claude_guidance", [])
    if claude_guidance:
        print(f"\n💡 Claude Guidance Quality: {len(claude_guidance)} guidance items")
        for guidance in claude_guidance[:3]:
            print(f"   • {guidance}")
    
    # Show example properties
    if properties:
        print(f"\n🔍 Example Properties (first 3):")
        for i, prop in enumerate(properties[:3]):
            uri = prop.get('uri', 'Unknown')
            label = prop.get('label', 'Unknown')
            prop_type = prop.get('property_type', 'Unknown')
            print(f"   {i+1}. {label} ({uri})")
            print(f"      Type: {prop_type}")
    
    if issues:
        print(f"\n⚠️  Quality Issues:")
        for issue in issues:
            print(f"   • {issue}")
        summary["issues"].extend(issues)


async def _analyze_failure(result: dict, test_case: OntologyTestCase, summary: dict):
    """Analyze failure and suggest specific improvements"""
    
    error = result.get("error", {})
    attempted_uris = error.get("attempted_uris", [])
    
    if attempted_uris:
        print(f"\n🔍 Attempted URIs ({len(attempted_uris)}):")
        for uri in attempted_uris[:5]:  # Show first 5
            print(f"   • {uri}")
    
    # Generate specific recommendations based on the test case
    recommendations = []
    
    if test_case.name == "Schema.org":
        recommendations.extend([
            "Implement Schema.org specific strategies:",
            "  • Try https://schema.org/version/latest/schemaorg-current-https.jsonld",
            "  • Use Schema.org API: https://schema.org/docs/developers.html",
            "  • Parse HTML with RDFa/Microdata extraction",
            "  • Use schemaorg-lite versions for specific domains"
        ])
    
    elif "purl.org" in test_case.uri:
        recommendations.extend([
            "PURL.org specific strategies:",
            "  • Try HTTP redirects with different Accept headers",
            "  • Check for .rdf, .ttl, .n3 file variants",
            "  • Use content negotiation with q-values"
        ])
    
    elif test_case.uri.startswith("http://www.w3.org/"):
        recommendations.extend([
            "W3C ontology strategies:",
            "  • Check W3C TR specifications for RDF downloads",
            "  • Try versioned URLs (e.g., /2004/02/ vs current)",
            "  • Look for separate RDF files in spec directories"
        ])
    
    if recommendations:
        print(f"\n💡 Specific Recommendations:")
        for rec in recommendations:
            print(f"   {rec}")
        summary["recommendations"].extend(recommendations)


async def test_special_schema_org_strategies(fetcher: AgenticOntologyFetcher):
    """Test specific strategies for Schema.org"""
    
    print(f"\n" + "=" * 60)
    print("🌐 SPECIAL TEST: Schema.org Strategies")
    print("=" * 60)
    
    # Known Schema.org URLs that should work
    schema_urls = [
        "https://schema.org/version/latest/schemaorg-current-https.jsonld",
        "https://schema.org/version/latest/schemaorg-current-http.jsonld", 
        "https://schema.org/docs/jsonldcontext.jsonld",
        "https://raw.githubusercontent.com/schemaorg/schemaorg/main/data/releases/13.0/schemaorg-current-https.jsonld"
    ]
    
    for url in schema_urls:
        print(f"\n📍 Testing Schema.org URL: {url}")
        print("-" * 40)
        
        try:
            result = await fetcher.discover_ontology(
                target=url,
                ontology_type="discover",
                domain="general",
                force_refresh=True
            )
            
            if result.get("success"):
                properties = result.get("properties", [])
                classes = result.get("classes", [])
                print(f"✅ SUCCESS: Found {len(properties)} properties, {len(classes)} classes")
                
                # Show some Schema.org specific properties
                schema_props = [p for p in properties if 'schema.org' in p.get('uri', '')]
                if schema_props:
                    print(f"🎯 Schema.org properties: {len(schema_props)}")
                    for prop in schema_props[:3]:
                        print(f"   • {prop.get('label', 'Unknown')}: {prop.get('uri', 'Unknown')}")
                
                break  # Success with this URL
            else:
                error = result.get("error", {})
                print(f"❌ Failed: {error.get('code', 'UNKNOWN')}")
                
        except Exception as e:
            print(f"❌ Exception: {e}")


@pytest.mark.asyncio
async def test_foaf_ontology_dereferencing():
    """Test FOAF ontology dereferencing"""
    fetcher = AgenticOntologyFetcher()
    
    result = await fetcher.discover_ontology(
        target="http://xmlns.com/foaf/0.1/",
        ontology_type="discover",
        domain=None,
        force_refresh=True
    )
    
    assert result.get("success"), f"FOAF dereferencing failed: {result.get('error', {})}"
    assert result.get("ontology_type") == "http_dereferenced"
    
    # Validate content quality
    properties = result.get("properties", [])
    classes = result.get("classes", [])
    
    assert len(properties) >= 50, f"Expected at least 50 properties, got {len(properties)}"
    assert len(classes) >= 10, f"Expected at least 10 classes, got {len(classes)}"
    
    # Check for OWL property types
    object_props = [p for p in properties if 'ObjectProperty' in p.get('property_type', '')]
    data_props = [p for p in properties if 'DatatypeProperty' in p.get('property_type', '')]
    
    assert len(object_props) > 0, "Expected ObjectProperties in FOAF ontology"
    assert len(data_props) > 0, "Expected DatatypeProperties in FOAF ontology"


@pytest.mark.asyncio
async def test_dublin_core_ontology_dereferencing():
    """Test Dublin Core Elements ontology dereferencing"""
    fetcher = AgenticOntologyFetcher()
    
    result = await fetcher.discover_ontology(
        target="http://purl.org/dc/elements/1.1/",
        ontology_type="discover",
        domain=None,
        force_refresh=True
    )
    
    assert result.get("success"), f"Dublin Core dereferencing failed: {result.get('error', {})}"
    assert result.get("ontology_type") == "http_dereferenced"
    
    properties = result.get("properties", [])
    assert len(properties) >= 10, f"Expected at least 10 properties, got {len(properties)}"
    
    # Dublin Core should have metadata-focused properties
    dc_props = [p for p in properties if 'purl.org/dc' in p.get('uri', '')]
    assert len(dc_props) > 0, "Expected Dublin Core properties"


@pytest.mark.asyncio
async def test_schema_org_specialized_url():
    """Test Schema.org using specialized URL strategy"""
    fetcher = AgenticOntologyFetcher()
    
    # Test the specialized Schema.org URL that should work
    result = await fetcher.discover_ontology(
        target="https://schema.org/version/latest/schemaorg-current-https.jsonld",
        ontology_type="discover",
        domain="general",
        force_refresh=True
    )
    
    assert result.get("success"), f"Schema.org specialized URL failed: {result.get('error', {})}"
    
    properties = result.get("properties", [])
    classes = result.get("classes", [])
    
    # Schema.org should have extensive vocabulary
    assert len(properties) >= 1000, f"Expected at least 1000 properties, got {len(properties)}"
    assert len(classes) >= 500, f"Expected at least 500 classes, got {len(classes)}"
    
    # Check for Schema.org specific properties
    schema_props = [p for p in properties if 'schema.org' in p.get('uri', '')]
    assert len(schema_props) > 0, "Expected Schema.org properties"


@pytest.mark.asyncio
async def test_skos_core_ontology_dereferencing():
    """Test SKOS Core ontology dereferencing"""
    fetcher = AgenticOntologyFetcher()
    
    result = await fetcher.discover_ontology(
        target="http://www.w3.org/2004/02/skos/core#",
        ontology_type="discover",
        domain=None,
        force_refresh=True
    )
    
    assert result.get("success"), f"SKOS Core dereferencing failed: {result.get('error', {})}"
    assert result.get("ontology_type") == "http_dereferenced"
    
    properties = result.get("properties", [])
    classes = result.get("classes", [])
    
    assert len(properties) >= 20, f"Expected at least 20 properties, got {len(properties)}"
    assert len(classes) >= 3, f"Expected at least 3 classes, got {len(classes)}"


@pytest.mark.asyncio
async def test_nonexistent_ontology_handling():
    """Test handling of non-existent ontology URIs"""
    fetcher = AgenticOntologyFetcher()
    
    result = await fetcher.discover_ontology(
        target="http://example.com/nonexistent/ontology/",
        ontology_type="discover",
        domain=None,
        force_refresh=True
    )
    
    # Should fail gracefully
    assert not result.get("success"), "Expected failure for non-existent ontology"
    assert result.get("error", {}).get("code") == "DEREFERENCING_FAILED"
    
    # Should provide helpful suggestions
    suggestions = result.get("error", {}).get("suggestions", [])
    assert len(suggestions) > 0, "Expected suggestions for failed dereferencing"


@pytest.mark.asyncio 
async def test_claude_guidance_generation():
    """Test that Claude-specific guidance is generated properly"""
    fetcher = AgenticOntologyFetcher()
    
    result = await fetcher.discover_ontology(
        target="http://xmlns.com/foaf/0.1/",
        ontology_type="discover",
        domain=None,
        force_refresh=True
    )
    
    assert result.get("success"), "FOAF dereferencing should succeed"
    
    metadata = result.get("metadata", {})
    claude_guidance = metadata.get("claude_guidance", [])
    
    assert len(claude_guidance) > 0, "Expected Claude guidance to be generated"
    
    # Check for specific guidance patterns
    guidance_text = " ".join(claude_guidance)
    assert "ONTOLOGY PROPERTIES" in guidance_text, "Expected property guidance"
    assert "USAGE" in guidance_text, "Expected usage guidance"


@pytest.mark.asyncio
async def test_content_negotiation_and_format_detection():
    """Test content negotiation and RDF format detection"""
    fetcher = AgenticOntologyFetcher()
    
    # Test different content types
    test_cases = [
        ("http://xmlns.com/foaf/0.1/", "application/ld+json"),
        ("http://purl.org/dc/elements/1.1/", "text/turtle"),
        ("http://www.w3.org/2004/02/skos/core#", "application/rdf+xml"),
    ]
    
    for uri, _expected_content_pattern in test_cases:
        result = await fetcher.discover_ontology(
            target=uri,
            ontology_type="discover",
            domain=None,
            force_refresh=True
        )
        
        assert result.get("success"), f"Dereferencing failed for {uri}"
        
        metadata = result.get("metadata", {})
        content_type = metadata.get("content_type", "")
        
        # Content negotiation should work
        assert content_type, f"Expected content type for {uri}"
        
        # Should have parsed RDF triples
        triples_count = metadata.get("triples_count", 0)
        assert triples_count > 0, f"Expected RDF triples for {uri}, got {triples_count}"


def test_ontology_test_case_structure():
    """Test the OntologyTestCase class structure"""
    test_case = OntologyTestCase(
        uri="http://example.org/test",
        name="Test Ontology",
        expected_format="text/turtle",
        expected_features={"properties": {"min": 10}},
        should_succeed=True
    )
    
    assert test_case.uri == "http://example.org/test"
    assert test_case.name == "Test Ontology"
    assert test_case.should_succeed is True
    assert test_case.special_strategies == []


if __name__ == "__main__":
    # Allow running as script for development
    pytest.main([__file__, "-v"])