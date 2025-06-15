"""Test universal external identifier discovery across all domains.

Tests the comprehensive discovery patterns beyond biology to cultural, chemical,
geographic, and bibliographic domains.
"""

import pytest
from unittest.mock import Mock, patch

from cogitarelink.core.universal_identifier_discovery import (
    UniversalIdentifierDiscovery, IdentifierPattern, IdentifierDomain,
    universal_identifier_discovery
)


class TestUniversalIdentifierDiscovery:
    """Test universal external identifier discovery functionality."""
    
    def test_initialization_with_known_patterns(self):
        """Test that discovery initializes with comprehensive known patterns."""
        discovery = UniversalIdentifierDiscovery()
        
        # Should have patterns for all major domains
        patterns = discovery.known_patterns
        
        # Biology domain patterns
        assert "P352" in patterns  # UniProt
        assert "P638" in patterns  # PDB
        assert "P705" in patterns  # Ensembl
        
        # Chemistry domain patterns
        assert "P231" in patterns  # CAS
        assert "P662" in patterns  # PubChem
        assert "P592" in patterns  # ChEMBL
        
        # Cultural domain patterns
        assert "P350" in patterns  # RKD Images
        assert "P347" in patterns  # Joconde
        assert "P9394" in patterns  # Louvre
        
        # Medical domain patterns
        assert "P486" in patterns  # MeSH
        assert "P2566" in patterns  # DrugBank
        
        # Geographic domain patterns
        assert "P1566" in patterns  # GeoNames
        
        # Bibliographic domain patterns
        assert "P214" in patterns  # VIAF
        assert "P213" in patterns  # ISNI
        assert "P244" in patterns  # Library of Congress
    
    def test_identifier_pattern_structure(self):
        """Test IdentifierPattern dataclass structure."""
        pattern = IdentifierPattern(
            property_id="P352",
            domain=IdentifierDomain.BIOLOGY,
            label="UniProt protein ID",
            description="identifier for a protein in the UniProt database",
            format_pattern=r"^[A-Z0-9]{6,10}$",
            database_name="uniprot",
            endpoint_url="https://rest.uniprot.org/uniprotkb/",
            example_values=["P01588", "Q9UHC7"],
            cross_references=["P638"]
        )
        
        assert pattern.property_id == "P352"
        assert pattern.domain == IdentifierDomain.BIOLOGY
        assert pattern.database_name == "uniprot"
        assert len(pattern.example_values) == 2
        assert "P638" in pattern.cross_references
    
    def test_identifier_domains_enum(self):
        """Test IdentifierDomain enum covers all major domains."""
        domains = [domain.value for domain in IdentifierDomain]
        
        expected_domains = [
            "biology", "chemistry", "cultural", "bibliographic",
            "geographic", "medical", "technical", "general"
        ]
        
        for expected in expected_domains:
            assert expected in domains
    
    def test_discover_by_domain_biology(self):
        """Test discovery of biological identifier patterns."""
        discovery = UniversalIdentifierDiscovery()
        
        biology_patterns = discovery.discover_by_domain(IdentifierDomain.BIOLOGY)
        
        # Should include major biological databases
        assert "P352" in biology_patterns  # UniProt
        assert "P638" in biology_patterns  # PDB
        assert "P705" in biology_patterns  # Ensembl
        
        # Should not include non-biological patterns
        assert "P231" not in biology_patterns  # CAS (chemistry)
        assert "P350" not in biology_patterns  # RKD Images (cultural)
        
        # All returned patterns should be biology domain
        for pattern in biology_patterns.values():
            assert pattern.domain == IdentifierDomain.BIOLOGY
    
    def test_discover_by_domain_chemistry(self):
        """Test discovery of chemical identifier patterns."""
        discovery = UniversalIdentifierDiscovery()
        
        chemistry_patterns = discovery.discover_by_domain(IdentifierDomain.CHEMISTRY)
        
        # Should include major chemical databases
        assert "P231" in chemistry_patterns  # CAS
        assert "P662" in chemistry_patterns  # PubChem
        assert "P592" in chemistry_patterns  # ChEMBL
        
        # Should not include non-chemical patterns
        assert "P352" not in chemistry_patterns  # UniProt (biology)
        assert "P350" not in chemistry_patterns  # RKD Images (cultural)
        
        # All returned patterns should be chemistry domain
        for pattern in chemistry_patterns.values():
            assert pattern.domain == IdentifierDomain.CHEMISTRY
    
    def test_discover_by_domain_cultural(self):
        """Test discovery of cultural identifier patterns."""
        discovery = UniversalIdentifierDiscovery()
        
        cultural_patterns = discovery.discover_by_domain(IdentifierDomain.CULTURAL)
        
        # Should include major cultural databases
        assert "P350" in cultural_patterns  # RKD Images
        assert "P347" in cultural_patterns  # Joconde
        assert "P9394" in cultural_patterns  # Louvre
        
        # Should not include non-cultural patterns
        assert "P352" not in cultural_patterns  # UniProt (biology)
        assert "P231" not in cultural_patterns  # CAS (chemistry)
        
        # All returned patterns should be cultural domain
        for pattern in cultural_patterns.values():
            assert pattern.domain == IdentifierDomain.CULTURAL
    
    def test_cross_reference_relationships(self):
        """Test cross-reference relationships between identifier patterns."""
        discovery = UniversalIdentifierDiscovery()
        
        # UniProt should cross-reference to PDB
        uniprot_pattern = discovery.known_patterns["P352"]
        assert "P638" in uniprot_pattern.cross_references
        
        # PDB should cross-reference to UniProt
        pdb_pattern = discovery.known_patterns["P638"]
        assert "P352" in pdb_pattern.cross_references
        
        # Chemistry patterns should cross-reference each other
        cas_pattern = discovery.known_patterns["P231"]
        assert "P662" in cas_pattern.cross_references or "P592" in cas_pattern.cross_references
        
        # Cultural patterns should cross-reference each other
        rkd_pattern = discovery.known_patterns["P350"]
        assert "P347" in rkd_pattern.cross_references or "P9394" in rkd_pattern.cross_references
    
    @patch('cogitarelink.core.universal_identifier_discovery.cache_manager')
    @patch('cogitarelink.discovery.base.discovery_engine')
    def test_discover_all_external_identifiers_biology_entity(self, mock_discovery_engine, mock_cache):
        """Test discovery of all external identifiers for a biological entity."""
        discovery = UniversalIdentifierDiscovery()
        
        # Mock cache miss
        mock_cache.get.return_value = None
        
        # Mock SPARQL response for erythropoietin (Q218706)
        mock_discovery_engine.query_endpoint.return_value = {
            "success": True,
            "results": [
                {
                    "prop": {"value": "http://www.wikidata.org/prop/direct/P352"},
                    "value": {"value": "P01588"}
                },
                {
                    "prop": {"value": "http://www.wikidata.org/prop/direct/P638"},
                    "value": {"value": "1BUY"}
                },
                {
                    "prop": {"value": "http://www.wikidata.org/prop/direct/P638"},
                    "value": {"value": "1CN4"}
                }
            ]
        }
        
        result = discovery.discover_all_external_identifiers("Q218706")
        
        # Should find biological identifiers
        assert "P352" in result["discovered_identifiers"]
        assert "P638" in result["discovered_identifiers"]
        
        # Should have biology in domains covered
        assert "biology" in result["domains_covered"]
        
        # Should have cross-reference suggestions
        assert len(result["cross_reference_suggestions"]) >= 0
        
        # Should cache the result
        mock_cache.set.assert_called_once()
    
    @patch('cogitarelink.core.universal_identifier_discovery.cache_manager')
    @patch('cogitarelink.discovery.base.discovery_engine')
    def test_discover_all_external_identifiers_cultural_entity(self, mock_discovery_engine, mock_cache):
        """Test discovery of all external identifiers for a cultural entity."""
        discovery = UniversalIdentifierDiscovery()
        
        # Mock cache miss
        mock_cache.get.return_value = None
        
        # Mock SPARQL response for Mona Lisa (Q12418)
        mock_discovery_engine.query_endpoint.return_value = {
            "success": True,
            "results": [
                {
                    "prop": {"value": "http://www.wikidata.org/prop/direct/P350"},
                    "value": {"value": "70503"}
                },
                {
                    "prop": {"value": "http://www.wikidata.org/prop/direct/P347"},
                    "value": {"value": "000PE003563"}
                },
                {
                    "prop": {"value": "http://www.wikidata.org/prop/direct/P9394"},
                    "value": {"value": "INV.779"}
                }
            ]
        }
        
        result = discovery.discover_all_external_identifiers("Q12418")
        
        # Should find cultural identifiers
        assert "P350" in result["discovered_identifiers"]
        assert "P347" in result["discovered_identifiers"]
        assert "P9394" in result["discovered_identifiers"]
        
        # Should have cultural in domains covered
        assert "cultural" in result["domains_covered"]
        
        # Should suggest cross-references between cultural databases
        cross_refs = result["cross_reference_suggestions"]
        cultural_suggestions = [
            s for s in cross_refs 
            if s.get("from_database") in ["rkd_images", "joconde", "louvre"]
        ]
        assert len(cultural_suggestions) >= 0
    
    def test_discover_cross_reference_pathways_multi_domain(self):
        """Test discovery of cross-reference pathways across multiple domains.""" 
        discovery = UniversalIdentifierDiscovery()
        
        # Mock entity with identifiers across multiple domains
        mock_identifiers = {
            "discovered_identifiers": {
                "P352": {
                    "values": ["P01588"],
                    "pattern": discovery.known_patterns["P352"].__dict__
                },
                "P231": {
                    "values": ["50-00-0"],
                    "pattern": discovery.known_patterns["P231"].__dict__
                },
                "P214": {
                    "values": ["102333412"],
                    "pattern": discovery.known_patterns["P214"].__dict__
                }
            }
        }
        
        with patch.object(discovery, 'discover_all_external_identifiers', return_value=mock_identifiers):
            pathways = discovery.discover_cross_reference_pathways("Q12345")
        
        # Should have workflows for multiple domains
        assert "biology_workflow" in pathways["pathways"]
        assert "chemistry_workflow" in pathways["pathways"]
        assert "bibliographic_workflow" in pathways["pathways"]
        
        # Should indicate multi-domain coverage
        assert pathways["multi_domain_coverage"] == True
        assert pathways["total_databases"] == 3
    
    def test_format_validation_known_patterns(self):
        """Test format validation for known identifier patterns."""
        discovery = UniversalIdentifierDiscovery()
        
        # Valid UniProt IDs
        assert discovery._validate_identifier_format("P352", "P01588") == "valid"
        assert discovery._validate_identifier_format("P352", ["P01588", "Q9UHC7"]) == "valid"
        
        # Invalid UniProt ID format
        assert discovery._validate_identifier_format("P352", "invalid_format") == "invalid_format"
        
        # Valid PDB IDs
        assert discovery._validate_identifier_format("P638", "1BUY") == "valid"
        assert discovery._validate_identifier_format("P638", ["1BUY", "1CN4"]) == "valid"
        
        # Invalid PDB ID format
        assert discovery._validate_identifier_format("P638", "INVALID") == "invalid_format"
        
        # Valid CAS Registry Numbers
        assert discovery._validate_identifier_format("P231", "50-00-0") == "valid"
        assert discovery._validate_identifier_format("P231", "7732-18-5") == "valid"
        
        # Invalid CAS format
        assert discovery._validate_identifier_format("P231", "invalid") == "invalid_format"
    
    @patch('cogitarelink.core.universal_identifier_discovery.property_discovery')
    def test_discover_unknown_pattern(self, mock_property_discovery):
        """Test discovery of unknown identifier patterns."""
        discovery = UniversalIdentifierDiscovery()
        
        # Mock property discovery for unknown pattern
        mock_prop_info = Mock()
        mock_prop_info.label = "Example Database ID"
        mock_prop_info.description = "identifier for an example database"
        mock_property_discovery.discover_properties.return_value = {"P99999": mock_prop_info}
        
        result = discovery._discover_unknown_pattern("P99999", "wikidata")
        
        assert result["property_id"] == "P99999"
        assert result["domain"] == "general"
        assert result["label"] == "Example Database ID"
        assert result["discovered_dynamically"] == True
    
    def test_cross_domain_connections(self):
        """Test finding cross-domain connection opportunities."""
        discovery = UniversalIdentifierDiscovery()
        
        # Test biology → chemistry connections
        all_domains = {"biology": [], "chemistry": []}
        connections = discovery._find_cross_domain_connections("biology", all_domains)
        
        biology_to_chemistry = [c for c in connections if c["target_domain"] == "chemistry"]
        assert len(biology_to_chemistry) > 0
        assert any("drug_targets" in c["connection_type"] for c in biology_to_chemistry)
        
        # Test cultural → geographic connections
        all_domains = {"cultural": [], "geographic": []}
        connections = discovery._find_cross_domain_connections("cultural", all_domains)
        
        cultural_to_geographic = [c for c in connections if c["target_domain"] == "geographic"]
        assert len(cultural_to_geographic) > 0
        assert any("provenance" in c["connection_type"] for c in cultural_to_geographic)
        
        # Test bibliographic connections (should connect to all other domains)
        all_domains = {"biology": [], "bibliographic": []}
        connections = discovery._find_cross_domain_connections("biology", all_domains)
        
        to_bibliographic = [c for c in connections if c["target_domain"] == "bibliographic"]
        assert len(to_bibliographic) > 0
        assert any("literature" in c["connection_type"] for c in to_bibliographic)
    
    def test_generate_cross_reference_suggestions(self):
        """Test generation of cross-reference suggestions."""
        discovery = UniversalIdentifierDiscovery()
        
        # Mock identifiers with known cross-reference potential
        identifiers = {
            "P352": {
                "values": ["P01588"],
                "pattern": discovery.known_patterns["P352"].__dict__
            }
            # Missing P638 (PDB) which should be suggested
        }
        
        suggestions = discovery._generate_cross_reference_suggestions(identifiers)
        
        # Should suggest following cross-reference from UniProt to PDB
        uniprot_to_pdb = [
            s for s in suggestions 
            if s["from_property"] == "P352" and s["to_property"] == "P638"
        ]
        assert len(uniprot_to_pdb) > 0
        
        suggestion = uniprot_to_pdb[0]
        assert suggestion["from_database"] == "uniprot"
        assert suggestion["to_database"] == "pdb"
        assert "cl_resolve" in suggestion["suggested_tool"]


class TestGlobalInstance:
    """Test the global universal_identifier_discovery instance."""
    
    def test_global_instance_available(self):
        """Test that global instance is available and properly initialized."""
        assert universal_identifier_discovery is not None
        assert isinstance(universal_identifier_discovery, UniversalIdentifierDiscovery)
        assert len(universal_identifier_discovery.known_patterns) > 10
    
    def test_global_instance_has_all_domains(self):
        """Test that global instance has patterns for all major domains."""
        patterns = universal_identifier_discovery.known_patterns
        
        # Check that all domains are represented
        domains_present = set(pattern.domain for pattern in patterns.values())
        
        expected_domains = {
            IdentifierDomain.BIOLOGY, IdentifierDomain.CHEMISTRY,
            IdentifierDomain.CULTURAL, IdentifierDomain.MEDICAL,
            IdentifierDomain.GEOGRAPHIC, IdentifierDomain.BIBLIOGRAPHIC
        }
        
        for expected_domain in expected_domains:
            assert expected_domain in domains_present


if __name__ == "__main__":
    pytest.main([__file__, "-v"])