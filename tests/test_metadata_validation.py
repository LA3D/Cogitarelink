"""Test metadata validation and hallucination guards.

Test-driven development for cross-reference validation and multi-source verification.
"""

import pytest
from unittest.mock import Mock, patch
from typing import Dict, List, Any

from cogitarelink.core.metadata_validation import (
    MetadataValidator, ValidationResult, CrossReferenceValidator,
    ConfidenceScorer, HallucinationGuard
)


class TestMetadataValidator:
    """Test core metadata validation functionality."""
    
    def test_validation_result_dataclass(self):
        """Test ValidationResult structure."""
        result = ValidationResult(
            is_valid=True,
            confidence_score=0.95,
            validation_details={"source": "multi_db_agreement"},
            warnings=["minor_timestamp_mismatch"],
            errors=[]
        )
        
        assert result.is_valid == True
        assert result.confidence_score == 0.95
        assert "multi_db_agreement" in result.validation_details["source"]
        assert len(result.warnings) == 1
        assert len(result.errors) == 0
    
    def test_validator_initialization(self):
        """Test MetadataValidator initialization."""
        validator = MetadataValidator()
        
        assert hasattr(validator, 'cross_ref_validator')
        assert hasattr(validator, 'confidence_scorer')
        assert hasattr(validator, 'hallucination_guard')
    
    @patch('cogitarelink.core.metadata_validation.endpoint_verification')
    @patch('cogitarelink.core.metadata_validation.property_discovery')
    @patch('cogitarelink.core.metadata_validation.entity_type_discovery')
    def test_validate_external_identifier_chain(self, mock_entity_discovery, mock_prop_discovery, mock_endpoint_verification):
        """Test validation of external identifier chains."""
        validator = MetadataValidator()
        
        # Mock discovery results
        mock_prop_discovery.discover_properties.return_value = {
            "P352": Mock(property_id="P352", label="UniProt protein ID", is_external_ref=True),
            "P638": Mock(property_id="P638", label="PDB structure ID", is_external_ref=True)
        }
        
        # Mock database accessibility
        mock_endpoint_verification.verify_database_accessible.return_value = True
        
        # Test external ID chain
        chain = {
            "entity_id": "Q218706",
            "external_ids": {"P352": "P01588", "P638": ["1BUY", "1CN4"]},
            "target_databases": ["uniprot", "pdb"]
        }
        
        result = validator.validate_external_identifier_chain(chain)
        
        assert isinstance(result, ValidationResult)
        assert hasattr(result, 'is_valid')
        assert hasattr(result, 'confidence_score')
    
    def test_validate_research_pathway_suggestions(self):
        """Test validation of suggested research pathways."""
        validator = MetadataValidator()
        
        pathway = {
            "entity_id": "Q218706",
            "suggested_steps": [
                "cl_resolve Q218706 --to-db uniprot",
                "cl_resolve Q218706 --to-db pdb",
                "cl_resolve Q218706 --to-db chembl"
            ],
            "databases": ["uniprot", "pdb", "chembl"]
        }
        
        result = validator.validate_research_pathway(pathway)
        
        assert isinstance(result, ValidationResult)
        # Should check database accessibility before suggesting


class TestCrossReferenceValidator:
    """Test cross-reference validation across databases."""
    
    def test_cross_reference_validator_init(self):
        """Test CrossReferenceValidator initialization."""
        validator = CrossReferenceValidator()
        
        assert hasattr(validator, 'cache_manager')
        assert hasattr(validator, 'discovery_engine')
    
    @patch('cogitarelink.core.metadata_validation.cache_manager')
    def test_validate_uniprot_pdb_consistency(self, mock_cache):
        """Test UniProt-PDB cross-reference consistency."""
        validator = CrossReferenceValidator()
        
        # Mock cache miss
        mock_cache.get.return_value = None
        
        # Mock the internal method directly
        validator._query_uniprot_pdb_cross_refs = Mock(return_value=["1BUY", "1CN4"])
        
        result = validator.validate_cross_reference_consistency(
            source_db="uniprot",
            source_id="P01588", 
            target_db="pdb",
            expected_ids=["1BUY", "1CN4"]
        )
        
        assert result.is_valid == True
        assert result.confidence_score > 0.8
    
    @patch('cogitarelink.core.metadata_validation.discovery_engine')
    def test_validate_inconsistent_cross_references(self, mock_discovery):
        """Test detection of inconsistent cross-references."""
        validator = CrossReferenceValidator()
        
        # Mock response with missing expected cross-reference
        mock_discovery.query_endpoint.return_value = {
            "success": True,
            "results": [
                {"pdb_id": {"value": "1BUY"}}
                # Missing 1CN4
            ]
        }
        
        result = validator.validate_cross_reference_consistency(
            source_db="uniprot",
            source_id="P01588",
            target_db="pdb", 
            expected_ids=["1BUY", "1CN4"]
        )
        
        assert result.confidence_score < 1.0
        assert len(result.warnings) > 0
    
    def test_multi_source_validation(self):
        """Test validation across multiple source databases."""
        validator = CrossReferenceValidator()
        
        external_ids = {
            "uniprot": "P01588",
            "pdb": ["1BUY", "1CN4"], 
            "ensembl": "ENSP00000252723"
        }
        
        result = validator.validate_multi_source_consistency(external_ids)
        
        assert isinstance(result, ValidationResult)
        assert hasattr(result, 'validation_details')


class TestConfidenceScorer:
    """Test confidence scoring for validation results."""
    
    def test_confidence_scorer_init(self):
        """Test ConfidenceScorer initialization."""
        scorer = ConfidenceScorer()
        
        assert hasattr(scorer, 'scoring_weights')
        assert hasattr(scorer, 'validation_history')
    
    def test_calculate_cross_reference_confidence(self):
        """Test confidence calculation for cross-references."""
        scorer = ConfidenceScorer()
        
        validation_data = {
            "sources_agreeing": 3,
            "total_sources": 3,
            "timestamp_consistency": True,
            "identifier_format_valid": True,
            "database_accessibility": True
        }
        
        confidence = scorer.calculate_cross_reference_confidence(validation_data)
        
        assert 0.0 <= confidence <= 1.0
        assert confidence > 0.9  # Should be high confidence for perfect agreement
    
    def test_calculate_pathway_confidence(self):
        """Test confidence calculation for research pathways."""
        scorer = ConfidenceScorer()
        
        pathway_data = {
            "databases_accessible": 3,
            "databases_suggested": 3,
            "cross_references_valid": True,
            "historical_success_rate": 0.85
        }
        
        confidence = scorer.calculate_pathway_confidence(pathway_data)
        
        assert 0.0 <= confidence <= 1.0
        assert confidence > 0.8  # Should be high for accessible, validated pathway
    
    def test_confidence_degradation_with_issues(self):
        """Test that confidence decreases with validation issues."""
        scorer = ConfidenceScorer()
        
        # Perfect validation
        perfect_data = {
            "sources_agreeing": 3,
            "total_sources": 3,
            "timestamp_consistency": True,
            "identifier_format_valid": True,
            "database_accessibility": True
        }
        
        # Validation with issues
        problematic_data = {
            "sources_agreeing": 2,
            "total_sources": 3, 
            "timestamp_consistency": False,
            "identifier_format_valid": True,
            "database_accessibility": True
        }
        
        perfect_confidence = scorer.calculate_cross_reference_confidence(perfect_data)
        problematic_confidence = scorer.calculate_cross_reference_confidence(problematic_data)
        
        assert perfect_confidence > problematic_confidence


class TestHallucinationGuard:
    """Test hallucination prevention mechanisms."""
    
    def test_hallucination_guard_init(self):
        """Test HallucinationGuard initialization."""
        guard = HallucinationGuard()
        
        assert hasattr(guard, 'endpoint_verification')
        assert hasattr(guard, 'cross_ref_validator')
    
    @patch('cogitarelink.core.metadata_validation.endpoint_verification')
    def test_prevent_database_hallucination(self, mock_verification):
        """Test prevention of suggesting non-existent databases."""
        guard = HallucinationGuard()
        
        # Mock database accessibility  
        mock_verification.verify_database_accessible.side_effect = lambda db: db in ["uniprot", "pdb"]
        
        suggested_databases = ["uniprot", "pdb", "nonexistent_db", "fake_database"]
        
        result = guard.filter_accessible_databases(suggested_databases)
        
        assert result.validated_databases == ["uniprot", "pdb"]
        assert result.rejected_databases == ["nonexistent_db", "fake_database"]
        assert len(result.warnings) == 2  # Should warn about rejected databases
    
    def test_prevent_identifier_hallucination(self):
        """Test prevention of suggesting invalid external identifiers."""
        guard = HallucinationGuard()
        
        identifier_suggestions = {
            "P352": "P01588",  # Valid UniProt format
            "P638": "1BUY",    # Valid PDB format  
            "P352": "INVALID_FORMAT_123456789",  # Invalid format
            "P999": "Q12345"   # Non-existent property
        }
        
        result = guard.validate_identifier_suggestions(identifier_suggestions)
        
        assert len(result.valid_identifiers) >= 2
        assert len(result.invalid_identifiers) >= 1
    
    @patch('cogitarelink.core.metadata_validation.endpoint_verification')
    def test_prevent_pathway_hallucination(self, mock_endpoint_verification):
        """Test prevention of suggesting impossible research pathways.""" 
        guard = HallucinationGuard()
        
        # Mock database accessibility - only uniprot and pdb are accessible
        mock_endpoint_verification.verify_database_accessible.side_effect = lambda db: db in ["uniprot", "pdb"]
        
        pathway = {
            "entity_id": "Q218706",
            "steps": [
                "cl_resolve Q218706 --to-db uniprot",
                "cl_resolve Q218706 --to-db nonexistent_db",  # Should be flagged
                "cl_resolve Q218706 --to-db pdb"
            ]
        }
        
        result = guard.validate_research_pathway(pathway)
        
        assert not result.is_fully_valid  # Should flag the invalid step
        assert len(result.validation_details["invalid_steps"]) >= 1


class TestIntegrationValidation:
    """Integration tests for complete validation workflow."""
    
    @patch('cogitarelink.core.metadata_validation.endpoint_verification')
    @patch('cogitarelink.core.metadata_validation.property_discovery')
    @patch('cogitarelink.core.metadata_validation.discovery_engine')
    def test_end_to_end_validation_workflow(self, mock_discovery, mock_prop_discovery, mock_endpoint_verification):
        """Test complete validation workflow for external identifier discovery."""
        validator = MetadataValidator()
        
        # Mock property discovery
        mock_prop_discovery.discover_properties.return_value = {
            "P352": Mock(property_id="P352", label="UniProt protein ID", is_external_ref=True),
            "P638": Mock(property_id="P638", label="PDB structure ID", is_external_ref=True)
        }
        
        # Mock database accessibility
        mock_endpoint_verification.verify_database_accessible.side_effect = lambda db: db in ["uniprot", "pdb"]
        
        # Mock realistic discovery results
        mock_discovery.query_endpoint.return_value = {
            "success": True,
            "results": [
                {
                    "entity": {"value": "http://www.wikidata.org/entity/Q218706"},
                    "uniprot_id": {"value": "P01588"},
                    "pdb_id": {"value": "1BUY"}
                }
            ]
        }
        
        # Test entity with known external identifiers
        validation_request = {
            "entity_id": "Q218706",
            "discovered_external_ids": {"P352": "P01588", "P638": "1BUY"},
            "suggested_databases": ["uniprot", "pdb", "chembl"],
            "suggested_workflow": [
                "cl_resolve Q218706 --to-db uniprot",
                "cl_resolve Q218706 --to-db pdb"
            ]
        }
        
        result = validator.validate_complete_metadata(validation_request)
        
        assert isinstance(result, ValidationResult)
        assert result.confidence_score > 0.0
        assert len(result.validation_details) > 0
    
    def test_validation_with_missing_data(self):
        """Test validation behavior when data is missing or incomplete.""" 
        validator = MetadataValidator()
        
        incomplete_request = {
            "entity_id": "Q999999",  # Non-existent entity
            "discovered_external_ids": {},
            "suggested_databases": [],
            "suggested_workflow": []
        }
        
        result = validator.validate_complete_metadata(incomplete_request)
        
        assert result.confidence_score == 0.0
        assert len(result.errors) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])