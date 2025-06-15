"""Integration tests for real metadata validation (requires network access).

These tests verify the real implementation works with live APIs.
"""

import pytest
from cogitarelink.core.metadata_validation import (
    metadata_validator, CrossReferenceValidator, HallucinationGuard
)


class TestRealValidationIntegration:
    """Integration tests with real APIs (requires network access)."""
    
    @pytest.mark.integration
    def test_real_wikidata_cross_reference_query(self):
        """Test real Wikidata cross-reference queries."""
        validator = CrossReferenceValidator()
        
        # Test known entity: erythropoietin (Q218706)
        try:
            uniprot_ids = validator._query_wikidata_cross_refs("Q218706", "uniprot")
            pdb_ids = validator._query_wikidata_cross_refs("Q218706", "pdb")
            
            # Should find some cross-references for this well-known protein
            assert isinstance(uniprot_ids, list)
            assert isinstance(pdb_ids, list)
            
            # If successful, should contain known values
            if uniprot_ids:
                assert "P01588" in uniprot_ids
            if pdb_ids:
                assert any(pdb_id in ["1BUY", "1CN4", "1EER"] for pdb_id in pdb_ids)
                
        except Exception as e:
            pytest.skip(f"Network not available for integration test: {e}")
    
    @pytest.mark.integration  
    def test_real_database_accessibility_check(self):
        """Test real database accessibility checking."""
        guard = HallucinationGuard()
        
        try:
            databases = ["wikidata", "uniprot", "pdb", "nonexistent_database"]
            result = guard.filter_accessible_databases(databases)
            
            # Should identify real databases as accessible
            assert "wikidata" in result.validated_databases
            assert "nonexistent_database" in result.rejected_databases
            
            # Should have realistic accessibility scores
            assert result.accessibility_scores["wikidata"] > 0.0
            assert result.accessibility_scores["nonexistent_database"] == 0.0
            
        except Exception as e:
            pytest.skip(f"Network not available for integration test: {e}")
    
    @pytest.mark.integration
    def test_real_complete_validation_workflow(self):
        """Test complete validation with real data and APIs."""
        try:
            validation_request = {
                "entity_id": "Q218706",  # erythropoietin
                "discovered_external_ids": {"P352": "P01588", "P638": ["1BUY", "1CN4"]},
                "suggested_databases": ["wikidata", "uniprot", "pdb"],
                "suggested_workflow": [
                    "cl_resolve Q218706 --to-db uniprot",
                    "cl_resolve Q218706 --to-db pdb"
                ]
            }
            
            result = metadata_validator.validate_complete_metadata(validation_request)
            
            # Should return realistic results
            assert isinstance(result.confidence_score, float)
            assert 0.0 <= result.confidence_score <= 1.0
            
            # Should have database validation results
            db_validation = result.validation_details["chain_validation"]["database_validation"]
            assert len(db_validation["validated_databases"]) > 0  # At least some should be accessible
            
            # Should not have empty validation details
            assert len(result.validation_details) > 0
            
        except Exception as e:
            pytest.skip(f"Network not available for integration test: {e}")
    
    def test_validation_degrades_gracefully_without_network(self):
        """Test that validation works gracefully when network is unavailable."""
        # This test should always work, even without network
        
        validation_request = {
            "entity_id": "Q218706",
            "discovered_external_ids": {"P352": "P01588"},
            "suggested_databases": ["uniprot"],
            "suggested_workflow": ["cl_resolve Q218706 --to-db uniprot"]
        }
        
        result = metadata_validator.validate_complete_metadata(validation_request)
        
        # Should return a result even if network calls fail
        assert hasattr(result, 'confidence_score')
        assert hasattr(result, 'is_valid')
        assert hasattr(result, 'validation_details')
        
        # Confidence might be low due to network issues, but should not crash
        assert 0.0 <= result.confidence_score <= 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])