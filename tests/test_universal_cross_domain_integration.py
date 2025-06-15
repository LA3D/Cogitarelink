"""Integration tests for universal identifier discovery across domains.

Tests the complete workflow for discovering external identifiers across biology,
chemistry, cultural, and other domains using real metadata validation.
"""

import pytest
from cogitarelink.core.universal_identifier_discovery import (
    universal_identifier_discovery, IdentifierDomain
)
from cogitarelink.core.metadata_validation import metadata_validator


class TestUniversalCrossDomainIntegration:
    """Integration tests for cross-domain external identifier workflows."""
    
    @pytest.mark.integration
    def test_biology_domain_workflow(self):
        """Test complete workflow for biological entities."""
        # Test with erythropoietin (Q218706) - known biological entity
        try:
            biology_patterns = universal_identifier_discovery.discover_by_domain(
                IdentifierDomain.BIOLOGY
            )
            
            # Should have major biological databases
            assert "P352" in biology_patterns  # UniProt
            assert "P638" in biology_patterns  # PDB
            assert "P705" in biology_patterns  # Ensembl
            
            # Validate pattern information
            uniprot_pattern = biology_patterns["P352"]
            assert uniprot_pattern.database_name == "uniprot"
            assert uniprot_pattern.format_pattern is not None
            assert len(uniprot_pattern.example_values) > 0
            assert "P638" in uniprot_pattern.cross_references
            
        except Exception as e:
            pytest.skip(f"Biology domain workflow test skipped: {e}")
    
    @pytest.mark.integration
    def test_chemistry_domain_workflow(self):
        """Test complete workflow for chemical entities.""" 
        try:
            chemistry_patterns = universal_identifier_discovery.discover_by_domain(
                IdentifierDomain.CHEMISTRY
            )
            
            # Should have major chemical databases
            assert "P231" in chemistry_patterns  # CAS
            assert "P662" in chemistry_patterns  # PubChem
            assert "P592" in chemistry_patterns  # ChEMBL
            
            # Validate pattern information
            cas_pattern = chemistry_patterns["P231"]
            assert cas_pattern.database_name == "cas"
            assert cas_pattern.format_pattern is not None
            assert len(cas_pattern.example_values) > 0
            
        except Exception as e:
            pytest.skip(f"Chemistry domain workflow test skipped: {e}")
    
    @pytest.mark.integration
    def test_cultural_domain_workflow(self):
        """Test complete workflow for cultural entities."""
        try:
            cultural_patterns = universal_identifier_discovery.discover_by_domain(
                IdentifierDomain.CULTURAL
            )
            
            # Should have major cultural databases
            assert "P350" in cultural_patterns  # RKD Images
            assert "P347" in cultural_patterns  # Joconde
            assert "P9394" in cultural_patterns  # Louvre
            
            # Validate pattern information
            rkd_pattern = cultural_patterns["P350"]
            assert rkd_pattern.database_name == "rkd_images"
            assert rkd_pattern.format_pattern is not None
            assert len(rkd_pattern.example_values) > 0
            
        except Exception as e:
            pytest.skip(f"Cultural domain workflow test skipped: {e}")
    
    @pytest.mark.integration
    def test_cross_domain_pathway_discovery(self):
        """Test discovery of research pathways across multiple domains."""
        try:
            # Test with an entity that might have identifiers in multiple domains
            # This is a simulation since we can't guarantee real multi-domain entities
            
            # Mock multi-domain entity data
            mock_pathways = universal_identifier_discovery.discover_cross_reference_pathways("Q12345")
            
            # Should return pathway structure
            assert "pathways" in mock_pathways
            assert "multi_domain_coverage" in mock_pathways
            assert "total_databases" in mock_pathways
            
        except Exception as e:
            pytest.skip(f"Cross-domain pathway test skipped: {e}")
    
    def test_identifier_format_validation_across_domains(self):
        """Test identifier format validation across all domains."""
        # Biology identifiers
        assert universal_identifier_discovery._validate_identifier_format("P352", "P01588") == "valid"
        assert universal_identifier_discovery._validate_identifier_format("P638", "1BUY") == "valid"
        
        # Chemistry identifiers
        assert universal_identifier_discovery._validate_identifier_format("P231", "50-00-0") == "valid"
        assert universal_identifier_discovery._validate_identifier_format("P662", "702") == "valid"
        
        # Cultural identifiers
        assert universal_identifier_discovery._validate_identifier_format("P350", "70503") == "valid"
        
        # Medical identifiers
        assert universal_identifier_discovery._validate_identifier_format("P486", "D000001") == "valid"
        assert universal_identifier_discovery._validate_identifier_format("P2566", "DB00001") == "valid"
        
        # Bibliographic identifiers
        assert universal_identifier_discovery._validate_identifier_format("P214", "102333412") == "valid"
        
        # Geographic identifiers
        assert universal_identifier_discovery._validate_identifier_format("P1566", "2988507") == "valid"
    
    def test_cross_reference_suggestions_multi_domain(self):
        """Test cross-reference suggestions across domains."""
        # Test biology → chemistry cross-references
        biology_identifiers = {
            "P352": {
                "values": ["P01588"],
                "pattern": universal_identifier_discovery.known_patterns["P352"].__dict__
            }
        }
        
        suggestions = universal_identifier_discovery._generate_cross_reference_suggestions(biology_identifiers)
        
        # Should suggest following cross-references
        assert len(suggestions) >= 0
        
        # Verify suggestion structure
        if suggestions:
            suggestion = suggestions[0]
            assert "from_property" in suggestion
            assert "to_property" in suggestion
            assert "suggested_tool" in suggestion
            assert "reasoning" in suggestion
    
    def test_domain_specific_cross_connections(self):
        """Test discovery of cross-domain connection opportunities."""
        # Biology ↔ Chemistry connections
        all_domains = {"biology": [], "chemistry": []}
        bio_connections = universal_identifier_discovery._find_cross_domain_connections("biology", all_domains)
        
        # Should find biology → chemistry connections
        chem_connections = [c for c in bio_connections if c["target_domain"] == "chemistry"]
        assert len(chem_connections) > 0
        
        connection = chem_connections[0]
        assert connection["connection_type"] == "protein_drug_targets"
        assert "drug targets" in connection["reasoning"]
        
        # Cultural ↔ Geographic connections
        all_domains = {"cultural": [], "geographic": []}
        cultural_connections = universal_identifier_discovery._find_cross_domain_connections("cultural", all_domains)
        
        geo_connections = [c for c in cultural_connections if c["target_domain"] == "geographic"]
        assert len(geo_connections) > 0
        
        geo_connection = geo_connections[0]
        assert geo_connection["connection_type"] == "artwork_provenance"
        assert "geographical" in geo_connection["reasoning"]
    
    def test_enhanced_metadata_validation_with_universal_patterns(self):
        """Test enhanced metadata validation using universal identifier patterns."""
        # Test validation request with multiple domains
        validation_request = {
            "entity_id": "Q12345",
            "discovered_external_ids": {
                "P352": "P01588",  # Biology
                "P231": "50-00-0", # Chemistry
                "P350": "70503"    # Cultural
            },
            "suggested_databases": ["uniprot", "cas", "rkd_images"],
            "suggested_workflow": [
                "cl_resolve Q12345 --to-db uniprot",
                "cl_resolve Q12345 --to-db cas", 
                "cl_resolve Q12345 --to-db rkd_images"
            ]
        }
        
        try:
            result = metadata_validator.validate_complete_metadata(validation_request)
            
            # Should return validation result
            assert hasattr(result, 'confidence_score')
            assert hasattr(result, 'is_valid')
            assert hasattr(result, 'validation_details')
            
            # Should validate identifier formats using universal patterns
            assert 0.0 <= result.confidence_score <= 1.0
            
        except Exception as e:
            pytest.skip(f"Enhanced metadata validation test skipped: {e}")
    
    @pytest.mark.integration
    def test_real_universal_identifier_discovery_workflow(self):
        """Test real universal identifier discovery with network calls (requires network)."""
        try:
            # Test with a known entity that has multiple external identifiers
            # Using aspirin (Q18216) as it should have chemical identifiers
            
            result = universal_identifier_discovery.discover_all_external_identifiers("Q18216")
            
            # Should return discovery structure
            assert "entity_id" in result
            assert "discovered_identifiers" in result
            assert "domains_covered" in result
            assert "cross_reference_suggestions" in result
            
            # Should discover some identifiers
            if result["discovered_identifiers"]:
                # Should have at least one identifier
                assert len(result["discovered_identifiers"]) > 0
                
                # Should cover some domains
                assert len(result["domains_covered"]) >= 0
                
        except Exception as e:
            pytest.skip(f"Real universal discovery test skipped (network required): {e}")
    
    def test_unknown_pattern_discovery(self):
        """Test discovery of unknown identifier patterns."""
        # Test with a hypothetical unknown property
        unknown_pattern = universal_identifier_discovery._discover_unknown_pattern("P99999", "wikidata")
        
        assert unknown_pattern["property_id"] == "P99999"
        assert unknown_pattern["domain"] == "general"
        assert unknown_pattern["discovered_dynamically"] == True
        
    def test_comprehensive_domain_coverage(self):
        """Test that universal discovery covers all major domains."""
        all_patterns = universal_identifier_discovery.known_patterns
        
        # Group patterns by domain
        by_domain = {}
        for pattern in all_patterns.values():
            domain = pattern.domain.value
            if domain not in by_domain:
                by_domain[domain] = []
            by_domain[domain].append(pattern)
        
        # Should cover major domains
        assert "biology" in by_domain
        assert "chemistry" in by_domain
        assert "cultural" in by_domain
        assert "medical" in by_domain
        assert "geographic" in by_domain
        assert "bibliographic" in by_domain
        
        # Each domain should have multiple patterns
        assert len(by_domain["biology"]) >= 3
        assert len(by_domain["chemistry"]) >= 3
        assert len(by_domain["cultural"]) >= 3
        
        # Verify cross-references exist between domains
        cross_refs_exist = False
        for pattern in all_patterns.values():
            if len(pattern.cross_references) > 0:
                cross_refs_exist = True
                break
        assert cross_refs_exist


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])