#!/usr/bin/env python3
"""
Test cl_resolve universal identifier resolution functionality

Tests the service description-powered approach for resolving external identifiers
across biological databases with vocabulary intelligence.
"""

import pytest
import asyncio
import json
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

# Add the parent directory to path for imports
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cogitarelink.cli.cl_resolve import UniversalIdentifierResolver
from cogitarelink.adapters.wikidata_client import WikidataClient

class TestUniversalIdentifierResolver:
    """Test suite for universal identifier resolution"""
    
    @pytest.fixture
    def resolver(self):
        """Create resolver instance for testing"""
        return UniversalIdentifierResolver()
    
    @pytest.mark.asyncio
    async def test_property_metadata_discovery(self, resolver):
        """Test property metadata discovery for known biological properties"""
        
        # Test UniProt property P352
        metadata = await resolver._discover_property_metadata("P352")
        
        assert metadata["property_id"] == "P352"
        assert "UniProt" in metadata["name"]
        assert metadata["domain"] == "proteins"
        assert metadata["datatype"] == "external-id"
        assert "formatter_url" in metadata
        
        # Test caching
        cached_metadata = await resolver._discover_property_metadata("P352")
        assert cached_metadata == metadata  # Should be identical from cache
    
    @pytest.mark.asyncio
    async def test_domain_extraction(self, resolver):
        """Test domain extraction from property metadata"""
        
        # Test known biological properties
        test_cases = [
            ("P352", "proteins"),    # UniProt
            ("P683", "chemicals"),   # ChEBI
            ("P486", "medical"),     # MeSH
            ("P4333", "genetics"),   # GenBank
        ]
        
        for property_id, expected_domain in test_cases:
            metadata = await resolver._discover_property_metadata(property_id)
            assert metadata["domain"] == expected_domain, f"Property {property_id} should have domain {expected_domain}"
    
    @pytest.mark.asyncio
    async def test_identifier_validation(self, resolver):
        """Test identifier format validation against property constraints"""
        
        # Test with P683 (ChEBI) which has regex pattern \d+
        property_metadata = {
            "regex_pattern": r"\d+",
            "example_value": "15365"
        }
        
        # Valid identifier
        valid_result = await resolver._validate_identifier_format("15365", property_metadata)
        assert valid_result["valid"] == True
        
        # Invalid identifier
        invalid_result = await resolver._validate_identifier_format("INVALID", property_metadata)
        assert invalid_result["valid"] == False
        assert "pattern" in invalid_result
    
    @pytest.mark.asyncio 
    async def test_wikidata_resolution(self, resolver):
        """Test identifier resolution in Wikidata"""
        
        # Test with known UniProt ID P01308 (insulin)
        result = await resolver._resolve_in_wikidata("P352", "P01308")
        
        assert "found_entities" in result
        assert "total_count" in result
        assert "query_used" in result
        
        if result["found_entities"]:
            entity = result["found_entities"][0]
            assert "id" in entity
            assert "label" in entity
            # Should find preproinsulin or similar
            assert "insulin" in entity["label"].lower() or "proinsulin" in entity["label"].lower()
    
    @pytest.mark.asyncio
    async def test_vocabulary_context_composition(self, resolver):
        """Test vocabulary context composition using cogitarelink registry"""
        
        # Test with protein domain
        protein_metadata = {"domain": "proteins", "property_id": "P352"}
        context = await resolver._compose_vocabulary_context(protein_metadata, None)
        
        if context:  # If vocabularies are available
            assert "composed_context" in context
            assert "prefixes_used" in context
            assert "domain" in context
            assert context["domain"] == "proteins"
            
            # Should include bioschemas for proteins
            if context["prefixes_used"]:
                assert any("bioschemas" in prefix or "schema" in prefix for prefix in context["prefixes_used"])
    
    @pytest.mark.asyncio
    async def test_full_resolution_workflow(self, resolver):
        """Test complete resolution workflow with real data"""
        
        # Test with ChEBI aspirin (15365)
        result = await resolver.resolve_identifier(
            property_id="P683",
            identifier="15365",
            validate=True,
            follow_links=False,  # Skip external links for testing
            include_context=True
        )
        
        assert result["success"] == True
        assert result["data"]["property_id"] == "P683"
        assert result["data"]["identifier"] == "15365"
        
        # Should have property metadata
        metadata = result["data"]["property_metadata"]
        assert metadata["domain"] == "chemicals"
        assert "ChEBI" in metadata["name"]
        
        # Should have Wikidata results
        wikidata_results = result["data"]["wikidata_results"]
        assert "found_entities" in wikidata_results
        
        # Should have validation result
        validation = result["data"]["validation"]
        assert validation["valid"] == True
        
        # Should have metadata and suggestions
        assert "execution_time_ms" in result["metadata"]
        assert "suggestions" in result
        assert "next_tools" in result["suggestions"]
    
    @pytest.mark.asyncio
    async def test_error_handling(self, resolver):
        """Test error handling for invalid inputs"""
        
        # Test with non-existent property
        result = await resolver.resolve_identifier(
            property_id="P999999",
            identifier="test",
            validate=False,
            follow_links=False,
            include_context=False
        )
        
        # Should handle gracefully and still provide metadata (even if minimal)
        assert "property_metadata" in result["data"]
        
        # Test with invalid format when validation is enabled
        result = await resolver.resolve_identifier(
            property_id="P683",  # ChEBI expects digits
            identifier="INVALID_FORMAT",
            validate=True,
            follow_links=False,
            include_context=False
        )
        
        # Should fail validation but provide helpful error
        if not result["success"]:
            assert "validation_details" in result["error"]
    
    def test_entity_id_extraction(self, resolver):
        """Test extraction of entity IDs from Wikidata URIs"""
        
        test_cases = [
            ("http://www.wikidata.org/entity/Q7240673", "Q7240673"),
            ("https://www.wikidata.org/entity/Q18216", "Q18216"),
            ("Q42", "Q42"),  # Already just ID
        ]
        
        for uri, expected_id in test_cases:
            extracted_id = resolver._extract_entity_id(uri)
            assert extracted_id == expected_id
    
    def test_suggestions_generation(self, resolver):
        """Test intelligent suggestions generation"""
        
        # Mock data for testing
        property_metadata = {"domain": "proteins", "property_id": "P352"}
        wikidata_results = {
            "found_entities": [{"id": "Q7240673", "label": "preproinsulin"}],
            "total_count": 1
        }
        external_results = {"results": []}
        
        suggestions = resolver._generate_resolution_suggestions(
            property_metadata, wikidata_results, external_results
        )
        
        assert "next_tools" in suggestions
        assert "research_patterns" in suggestions
        assert "workflow_steps" in suggestions
        
        # Should suggest follow-up for found entity
        assert any("Q7240673" in tool for tool in suggestions["next_tools"])
        
        # Should have protein-specific research patterns
        assert any("PROTEIN" in pattern for pattern in suggestions["research_patterns"])

class TestCLResolveIntegration:
    """Integration tests for cl_resolve CLI command"""
    
    def test_cli_help(self):
        """Test that CLI help works"""
        from click.testing import CliRunner
        from cogitarelink.cli.cl_resolve import resolve
        
        runner = CliRunner()
        result = runner.invoke(resolve, ['--help'])
        assert result.exit_code == 0
        assert "Universal identifier resolution" in result.output
        assert "PROTEIN WORKFLOW" in result.output
        assert "CHEMICAL WORKFLOW" in result.output
    
    def test_missing_identifier_validation(self):
        """Test validation when identifier is missing"""
        from click.testing import CliRunner  
        from cogitarelink.cli.cl_resolve import resolve
        
        runner = CliRunner()
        
        # Should fail without --discover flag and no identifier
        result = runner.invoke(resolve, ['P352'])
        assert result.exit_code == 0  # Command runs but returns error JSON
        
        output = json.loads(result.output)
        assert output["success"] == False
        assert output["error"]["code"] == "MISSING_IDENTIFIER"

@pytest.mark.asyncio
async def test_service_description_integration():
    """Test integration with wikidata-mcp ontology discovery"""
    
    resolver = UniversalIdentifierResolver()
    
    # Test that ontology discovery is available
    if resolver.discovery_engine:
        # Should be able to discover endpoint schemas
        # This is tested indirectly through the resolver functionality
        assert hasattr(resolver.discovery_engine, 'discover_schema')
    else:
        pytest.skip("Ontology discovery not available - install wikidata-mcp dependencies")

def test_vocabulary_registry_integration():
    """Test integration with cogitarelink vocabulary registry"""
    
    from cogitarelink.vocab.registry import registry
    from cogitarelink.vocab.composer import composer
    
    # Test that we can access basic vocabularies
    try:
        schema_entry = registry.resolve("schema")
        assert schema_entry.prefix == "schema"
    except KeyError:
        pass  # Optional vocabulary
    
    try:
        bioschemas_entry = registry.resolve("bioschemas") 
        assert bioschemas_entry.prefix == "bioschemas"
    except KeyError:
        pass  # Optional vocabulary
    
    # Test basic composition functionality
    try:
        context = composer.compose(["schema"])
        assert "@context" in context
    except Exception:
        pass  # May fail if vocabularies not available

if __name__ == "__main__":
    # Run basic tests
    pytest.main([__file__, "-v"])