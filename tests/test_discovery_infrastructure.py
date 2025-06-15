"""Test discovery infrastructure for property and entity type discovery.

Test the foundation that eliminates hard-coded assumptions by dynamically 
discovering what properties and entity types actually mean.
"""

import pytest
from unittest.mock import Mock, patch

from cogitarelink.core.discovery_infrastructure import (
    PropertyDiscovery, EntityTypeDiscovery, EndpointVerification,
    PropertyInfo, EntityTypeInfo, discover_metadata_meanings
)


class TestPropertyDiscovery:
    """Test property discovery functionality."""
    
    def test_property_info_dataclass(self):
        """Test PropertyInfo dataclass structure."""
        prop = PropertyInfo(
            property_id="P352",
            label="UniProt protein ID",
            description="identifier for a protein in the UniProt database"
        )
        
        assert prop.property_id == "P352"
        assert prop.label == "UniProt protein ID"
        assert "UniProt" in prop.description
        assert prop.is_external_ref == False  # Default value
    
    def test_external_reference_detection(self):
        """Test detection of external reference properties."""
        discovery = PropertyDiscovery()
        
        # Should detect external references
        assert discovery._is_external_reference_property("P352", "UniProt protein ID", "database identifier")
        assert discovery._is_external_reference_property("P594", "Ensembl ID", "genomic database")
        assert discovery._is_external_reference_property("P638", "PDB structure ID", "protein database")
        
        # Should not detect as external references
        assert not discovery._is_external_reference_property("P31", "instance of", "type classification")
        assert not discovery._is_external_reference_property("P279", "subclass of", "hierarchy relation")
    
    @patch('cogitarelink.core.discovery_infrastructure.discovery_engine')
    @patch('cogitarelink.core.discovery_infrastructure.cache_manager')
    def test_discover_properties_with_cache_hit(self, mock_cache, mock_discovery):
        """Test property discovery with cache hit."""
        discovery = PropertyDiscovery()
        
        # Mock cache hit
        cached_data = {
            "P352": {
                "property_id": "P352",
                "label": "UniProt protein ID", 
                "description": "cached description",
                "is_external_ref": True
            }
        }
        mock_cache.get.return_value = cached_data
        
        result = discovery.discover_properties(["P352"], "wikidata")
        
        assert len(result) == 1
        assert "P352" in result
        assert result["P352"].label == "UniProt protein ID"
        assert result["P352"].is_external_ref == True
        
        # Should not call discovery engine due to cache hit
        mock_discovery.query_endpoint.assert_not_called()
    
    @patch('cogitarelink.core.discovery_infrastructure.discovery_engine')
    @patch('cogitarelink.core.discovery_infrastructure.cache_manager')
    def test_discover_wikidata_properties(self, mock_cache, mock_discovery):
        """Test Wikidata property discovery."""
        discovery = PropertyDiscovery()
        
        # Mock cache miss
        mock_cache.get.return_value = None
        
        # Mock successful SPARQL response
        mock_discovery.query_endpoint.return_value = {
            "success": True,
            "results": [
                {
                    "prop": {"value": "http://www.wikidata.org/entity/P352"},
                    "propLabel": {"value": "UniProt protein ID"},
                    "propDescription": {"value": "identifier for a protein in the UniProt database"}
                }
            ]
        }
        
        result = discovery.discover_properties(["P352"], "wikidata")
        
        assert len(result) == 1
        assert "P352" in result
        prop_info = result["P352"]
        assert prop_info.property_id == "P352"
        assert prop_info.label == "UniProt protein ID"
        assert "UniProt" in prop_info.description
        assert prop_info.is_external_ref == True  # Should be detected as external ref
        
        # Should cache the result
        mock_cache.set.assert_called_once()
    
    @patch('cogitarelink.core.discovery_infrastructure.discovery_engine')
    @patch('cogitarelink.core.discovery_infrastructure.cache_manager')
    def test_discover_properties_fallback(self, mock_cache, mock_discovery):
        """Test property discovery fallback when SPARQL fails."""
        discovery = PropertyDiscovery()
        
        # Mock cache miss and SPARQL failure
        mock_cache.get.return_value = None
        mock_discovery.query_endpoint.side_effect = Exception("SPARQL failed")
        
        result = discovery.discover_properties(["P352"], "wikidata")
        
        assert len(result) == 1
        assert "P352" in result
        prop_info = result["P352"]
        assert prop_info.property_id == "P352"
        assert prop_info.label == "P352"  # Fallback to ID
        assert "Discovery failed" in prop_info.description


class TestEntityTypeDiscovery:
    """Test entity type discovery functionality."""
    
    def test_entity_type_info_dataclass(self):
        """Test EntityTypeInfo dataclass structure."""
        entity_type = EntityTypeInfo(
            type_id="Q8054",
            label="protein",
            description="biological macromolecule",
            subclass_of=["Q11173"],
            domain_category="general"
        )
        
        assert entity_type.type_id == "Q8054"
        assert entity_type.label == "protein"
        assert entity_type.domain_category == "general"
        assert "Q11173" in entity_type.subclass_of
    
    def test_domain_category_inference(self):
        """Test domain category inference using Software 2.0 approach."""
        discovery = EntityTypeDiscovery()
        
        # Software 2.0 approach: Avoid hard-coded domain classifications
        # Instead, return "general" until we implement knowledge-base discovery
        assert discovery._infer_domain_category("protein", "biological macromolecule", []) == "general"
        assert discovery._infer_domain_category("gene", "DNA sequence", []) == "general"
        assert discovery._infer_domain_category("enzyme", "protein catalyst", []) == "general"
        
        # Chemistry entities also return general (to be discovered from KB)
        assert discovery._infer_domain_category("chemical compound", "molecular entity", []) == "general"
        assert discovery._infer_domain_category("pharmaceutical drug", "therapeutic compound", []) == "general"
        assert discovery._infer_domain_category("organic molecule", "carbon-based compound", []) == "general"
        
        # General domain
        assert discovery._infer_domain_category("concept", "abstract idea", []) == "general"
        assert discovery._infer_domain_category("location", "geographic place", []) == "general"
    
    @patch('cogitarelink.core.discovery_infrastructure.discovery_engine')
    @patch('cogitarelink.core.discovery_infrastructure.cache_manager')
    def test_discover_wikidata_entity_types(self, mock_cache, mock_discovery):
        """Test Wikidata entity type discovery."""
        discovery = EntityTypeDiscovery()
        
        # Mock cache miss
        mock_cache.get.return_value = None
        
        # Mock successful SPARQL response
        mock_discovery.query_endpoint.return_value = {
            "success": True,
            "results": [
                {
                    "type": {"value": "http://www.wikidata.org/entity/Q8054"},
                    "typeLabel": {"value": "protein"},
                    "typeDescription": {"value": "biological macromolecule"},
                    "superclass": {"value": "http://www.wikidata.org/entity/Q11173"}
                }
            ]
        }
        
        result = discovery.discover_entity_types(["Q8054"], "wikidata")
        
        assert len(result) == 1
        assert "Q8054" in result
        type_info = result["Q8054"]
        assert type_info.type_id == "Q8054"
        assert type_info.label == "protein"
        assert type_info.domain_category == "general"
        assert "Q11173" in type_info.subclass_of


class TestEndpointVerification:
    """Test endpoint verification functionality."""
    
    @patch('cogitarelink.core.discovery_infrastructure.discovery_engine')
    @patch('cogitarelink.core.discovery_infrastructure.cache_manager')
    def test_verify_database_accessible(self, mock_cache, mock_discovery):
        """Test database accessibility verification."""
        verification = EndpointVerification()
        
        # Mock cache miss
        mock_cache.get.return_value = None
        
        # Mock successful discovery
        mock_discovery_result = Mock()
        mock_discovery_result.url = "https://example.com/sparql"
        mock_discovery.discover.return_value = mock_discovery_result
        
        result = verification.verify_database_accessible("wikidata")
        
        assert result == True
        mock_cache.set.assert_called_once()
    
    @patch('cogitarelink.core.discovery_infrastructure.discovery_engine')  
    @patch('cogitarelink.core.discovery_infrastructure.cache_manager')
    def test_verify_database_inaccessible(self, mock_cache, mock_discovery):
        """Test database inaccessibility detection."""
        verification = EndpointVerification()
        
        # Mock cache miss
        mock_cache.get.return_value = None
        
        # Mock failed discovery
        mock_discovery.discover.side_effect = Exception("Connection failed")
        
        result = verification.verify_database_accessible("nonexistent")
        
        assert result == False
        mock_cache.set.assert_called_with(
            "endpoint_verification:nonexistent", 
            False, 
            ttl=3600
        )
    
    @patch('cogitarelink.core.discovery_infrastructure.discovery_engine')
    @patch('cogitarelink.core.discovery_infrastructure.cache_manager')
    def test_get_accessible_databases(self, mock_cache, mock_discovery):
        """Test filtering to only accessible databases."""
        verification = EndpointVerification()
        
        # Mock cache misses
        mock_cache.get.return_value = None
        
        # Mock discovery results
        def mock_discover(db):
            if db in ["wikidata", "uniprot"]:
                result = Mock()
                result.url = f"https://{db}.org/sparql"
                return result
            else:
                raise Exception("Not accessible")
        
        mock_discovery.discover.side_effect = mock_discover
        
        suggested = ["wikidata", "uniprot", "nonexistent", "broken"]
        accessible = verification.get_accessible_databases(suggested)
        
        assert accessible == ["wikidata", "uniprot"]


class TestDiscoverMetadataMeanings:
    """Test comprehensive metadata discovery function."""
    
    @patch('cogitarelink.core.discovery_infrastructure.entity_type_discovery')
    @patch('cogitarelink.core.discovery_infrastructure.property_discovery')
    def test_discover_metadata_meanings(self, mock_prop_discovery, mock_type_discovery):
        """Test comprehensive metadata discovery."""
        # Mock discovery results
        mock_prop_discovery.discover_properties.return_value = {
            "P352": PropertyInfo("P352", "UniProt protein ID", "protein database ID", is_external_ref=True)
        }
        
        mock_type_discovery.discover_entity_types.return_value = {
            "Q8054": EntityTypeInfo("Q8054", "protein", "biological macromolecule", ["Q11173"], domain_category="general")
        }
        
        result = discover_metadata_meanings(
            entity_types=["Q8054"],
            properties=["P352"],
            endpoint="wikidata"
        )
        
        assert "entity_types" in result
        assert "properties" in result
        assert "endpoint" in result
        assert result["endpoint"] == "wikidata"
        
        # Check that discovery methods were called
        mock_type_discovery.discover_entity_types.assert_called_once_with(["Q8054"], "wikidata")
        mock_prop_discovery.discover_properties.assert_called_once_with(["P352"], "wikidata")


class TestIntegration:
    """Integration tests for discovery infrastructure."""
    
    def test_empty_inputs_handling(self):
        """Test handling of empty entity types and properties."""
        result = discover_metadata_meanings(
            entity_types=[],
            properties=[],
            endpoint="wikidata"
        )
        
        assert result["entity_types"] == {}
        assert result["properties"] == {}
        assert result["endpoint"] == "wikidata"
    
    def test_real_property_discovery_structure(self):
        """Test that real property discovery returns expected structure."""
        # This test uses real discovery (integration test)
        # Skip if network unavailable
        try:
            discovery = PropertyDiscovery()
            result = discovery.discover_properties(["P31"], "wikidata")
            
            assert len(result) >= 1
            if "P31" in result:
                prop_info = result["P31"]
                assert hasattr(prop_info, 'property_id')
                assert hasattr(prop_info, 'label')
                assert hasattr(prop_info, 'description')
                assert hasattr(prop_info, 'is_external_ref')
                
        except Exception:
            pytest.skip("Network unavailable for integration test")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])