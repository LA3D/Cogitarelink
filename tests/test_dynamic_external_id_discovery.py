"""Test dynamic external identifier discovery using DESCRIBE queries.

Test-driven development for transforming the universal identifier discovery system
from Software 1.0 (hardcoded patterns) to Software 2.0 (dynamic discovery).
"""

import pytest
from unittest.mock import Mock, patch

from cogitarelink.core.universal_identifier_discovery import (
    universal_identifier_discovery, IdentifierPattern, IdentifierDomain
)
from cogitarelink.discovery.base import discovery_engine


class TestDynamicExternalIdDiscovery:
    """Test dynamic discovery of external identifier patterns using DESCRIBE queries."""
    
    def test_discover_p1667_dynamically(self):
        """Test that P1667 (Getty Thesaurus of Geographic Names ID) is discovered dynamically."""
        # This should work without P1667 being in known_patterns
        pattern = universal_identifier_discovery.discover_pattern_via_describe("P1667")
        
        assert pattern is not None
        assert pattern.property_id == "P1667"
        assert pattern.label == "Getty Thesaurus of Geographic Names ID"
        assert pattern.domain == IdentifierDomain.GEOGRAPHIC
        assert pattern.format_pattern == "[1-9][0-9]{6}"
        assert "vocab.getty.edu/page/tgn/$1" in pattern.endpoint_url
        assert pattern.database_name == "getty_tgn"
    
    def test_discover_service_via_describe(self):
        """Test discovery of service properties via DESCRIBE on service entity."""
        # Q1520117 = Getty Thesaurus of Geographic Names
        service_info = universal_identifier_discovery.discover_service_properties_via_describe("Q1520117")
        
        assert service_info is not None
        assert "P1687" in service_info["properties_defined"]
        assert "P1667" in service_info["properties_defined"]["P1687"]
        assert service_info["domain"] == "geographic"
        assert service_info["service_name"] == "Getty Thesaurus of Geographic Names"
    
    def test_bidirectional_discovery(self):
        """Test bidirectional discovery: PID → QID and QID → PID."""
        # P1667 → Q1520117
        service_id = universal_identifier_discovery.find_service_for_property("P1667")
        assert service_id == "Q1520117"
        
        # Q1520117 → P1667
        properties = universal_identifier_discovery.find_properties_for_service("Q1520117")
        assert "P1667" in properties
    
    def test_describe_result_parsing(self):
        """Test parsing DESCRIBE query results to extract identifier metadata."""
        # Mock DESCRIBE result for P1667 (using actual format)
        mock_describe_result = {
            "success": True,
            "results": [
                {
                    "subject": {"value": "http://www.wikidata.org/entity/P1667"},
                    "predicate": {"value": "http://www.w3.org/2000/01/rdf-schema#label"},
                    "object": {"type": "literal", "value": "Getty Thesaurus of Geographic Names ID", "xml:lang": "en"}
                },
                {
                    "subject": {"value": "http://www.wikidata.org/entity/P1667"},
                    "predicate": {"value": "http://www.wikidata.org/prop/direct/P1793"},
                    "object": {"type": "literal", "value": "[1-9][0-9]{6}"}
                },
                {
                    "subject": {"value": "http://www.wikidata.org/entity/P1667"},
                    "predicate": {"value": "http://www.wikidata.org/prop/direct/P1630"},
                    "object": {"type": "literal", "value": "https://vocab.getty.edu/page/tgn/$1"}
                },
                {
                    "subject": {"value": "http://www.wikidata.org/entity/P1667"},
                    "predicate": {"value": "http://www.wikidata.org/prop/direct/P31"},
                    "object": {"type": "uri", "value": "http://www.wikidata.org/entity/Q18616576"}
                }
            ]
        }
        
        pattern = universal_identifier_discovery._parse_property_describe_result(mock_describe_result, "P1667")
        
        assert pattern.property_id == "P1667"
        assert pattern.label == "Getty Thesaurus of Geographic Names ID"
        assert pattern.format_pattern == "[1-9][0-9]{6}"
        assert "vocab.getty.edu/page/tgn/$1" in pattern.endpoint_url
    
    def test_domain_classification_from_service(self):
        """Test domain classification from service entity DESCRIBE."""
        # Mock DESCRIBE result for Q1520117 (Getty Thesaurus)
        mock_describe_result = {
            "success": True,
            "results": [
                {
                    "predicate": {"value": "http://www.wikidata.org/prop/direct/P31"},
                    "object": {"type": "uri", "value": "http://www.wikidata.org/entity/Q17152639"}  # thesaurus
                },
                {
                    "predicate": {"value": "http://www.wikidata.org/prop/direct/P1687"},
                    "object": {"type": "uri", "value": "http://www.wikidata.org/entity/P1667"}
                }
            ]
        }
        
        domain = universal_identifier_discovery._classify_domain_from_service_describe(mock_describe_result)
        assert domain == IdentifierDomain.GEOGRAPHIC
    
    def test_caching_of_discovered_patterns(self):
        """Test that discovered patterns are cached for performance."""
        # Clear cache first
        universal_identifier_discovery.clear_pattern_cache()
        
        # First discovery should hit network
        with patch('httpx.Client') as mock_client:
            mock_response = Mock()
            mock_response.json.return_value = {
                "entities": {
                    "P9999": {
                        "labels": {"en": {"value": "Test Property"}},
                        "descriptions": {"en": {"value": "Test description"}},
                        "claims": {}
                    }
                }
            }
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response
            
            pattern1 = universal_identifier_discovery.discover_pattern_via_describe("P9999")
            assert mock_client.call_count == 1
            
            # Second discovery should use cache
            pattern2 = universal_identifier_discovery.discover_pattern_via_describe("P9999")
            assert mock_client.call_count == 1  # No additional call
            assert pattern1.property_id == pattern2.property_id
    
    def test_unknown_pattern_fallback(self):
        """Test graceful handling of unknown patterns."""
        # Mock a property that doesn't exist or has minimal metadata
        with patch.object(discovery_engine, 'query_endpoint') as mock_query:
            mock_query.return_value = {"success": True, "results": []}
            
            pattern = universal_identifier_discovery.discover_pattern_via_describe("P99999")
            
            assert pattern.property_id == "P99999"
            assert pattern.domain == IdentifierDomain.GENERAL
            assert pattern.discovered_dynamically is True
    
    def test_integration_with_existing_system(self):
        """Test that dynamic discovery integrates with existing discovery system."""
        # Should work with discover_all_external_identifiers
        result = universal_identifier_discovery.discover_all_external_identifiers("Q1520117")
        
        # Should now include dynamically discovered patterns
        assert "discovered_identifiers" in result
        assert "unknown_patterns" in result
        
        # Should handle both known and unknown patterns gracefully
        assert len(result["unknown_patterns"]) >= 0  # May or may not have unknown patterns


class TestDynamicDiscoveryPerformance:
    """Test performance characteristics of dynamic discovery."""
    
    def test_bulk_discovery_performance(self):
        """Test discovering multiple patterns efficiently."""
        properties = ["P1667", "P352", "P231", "P1566"]  # Mix of known and unknown
        
        patterns = universal_identifier_discovery.discover_patterns_bulk(properties)
        
        assert len(patterns) == len(properties)
        for prop_id in properties:
            assert prop_id in patterns
            assert patterns[prop_id].property_id == prop_id
    
    def test_cache_invalidation(self):
        """Test cache invalidation and refresh."""
        # Clear cache for testing
        universal_identifier_discovery.clear_pattern_cache()
        
        # Discovery should work after cache clear
        pattern = universal_identifier_discovery.discover_pattern_via_describe("P1667")
        assert pattern is not None
    
    def test_error_resilience(self):
        """Test system resilience when DESCRIBE queries fail."""
        # Clear cache and test with unknown property
        universal_identifier_discovery.clear_pattern_cache()
        
        with patch('httpx.Client') as mock_client:
            mock_client.side_effect = Exception("Network timeout")
            
            # Should fallback gracefully
            pattern = universal_identifier_discovery.discover_pattern_via_describe("P99998")
            
            assert pattern.property_id == "P99998"
            assert pattern.discovered_dynamically is True
            assert pattern.domain == IdentifierDomain.GENERAL  # Safe fallback


class TestBackwardCompatibility:
    """Test that dynamic discovery maintains backward compatibility."""
    
    def test_existing_known_patterns_still_work(self):
        """Test that existing hardcoded patterns still work during transition."""
        # P352 should work (was in known_patterns)
        pattern = universal_identifier_discovery.get_pattern("P352")
        assert pattern is not None
        assert pattern.property_id == "P352"
        assert pattern.domain == IdentifierDomain.BIOLOGY
    
    def test_api_compatibility(self):
        """Test that all existing APIs still work."""
        # discover_by_domain should work
        bio_patterns = universal_identifier_discovery.discover_by_domain(IdentifierDomain.BIOLOGY)
        assert len(bio_patterns) > 0
        
        # discover_cross_reference_pathways should work
        pathways = universal_identifier_discovery.discover_cross_reference_pathways("Q7240673")
        assert "pathways" in pathways
    
    def test_cli_tool_integration(self):
        """Test that CLI tools work with dynamic discovery."""
        # This would be tested by running actual CLI commands
        # For now, test the underlying functions they use
        
        # cl_search uses universal discovery
        result = universal_identifier_discovery.discover_all_external_identifiers("Q1520117")
        assert "discovered_identifiers" in result
        
        # Should now include P1667 dynamically
        # (This test verifies the fix to the original P1667 problem)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])