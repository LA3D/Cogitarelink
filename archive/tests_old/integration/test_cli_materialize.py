"""Integration tests for cl_materialize CLI tool."""

from __future__ import annotations

import json
import pytest
from pathlib import Path
from click.testing import CliRunner

from cogitarelink.cli.cl_materialize import materialize


class TestClMaterializeIntegration:
    """Integration tests for cl_materialize with realistic scenarios."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
    
    def test_materialize_sparql_results_from_file(self):
        """Test materializing SPARQL results from an existing file."""
        
        # Use the existing test file from previous cl_sparql execution
        sparql_results_file = "/tmp/sparql_results.json"
        
        if not Path(sparql_results_file).exists():
            pytest.skip("SPARQL results file not available for integration test")
        
        result = self.runner.invoke(materialize, [
            '--from-sparql-results', sparql_results_file,
            '--vocab', 'bioschemas',
            '--format', 'json'
        ])
        
        assert result.exit_code == 0
        response = json.loads(result.output)
        assert response["success"] is True
        
        # Basic response structure checks
        assert "data" in response
        assert "metadata" in response
        assert "suggestions" in response
        assert "claude_guidance" in response
        
        # Should have processed entities
        assert response["metadata"]["entities_materialized"] >= 0
    
    def test_materialize_empty_entities_list(self):
        """Test materialization with empty entities list."""
        
        empty_entities = "[]"
        
        result = self.runner.invoke(materialize, [
            '--from-entities', empty_entities,
            '--format', 'json'
        ])
        
        assert result.exit_code == 0
        response = json.loads(result.output)
        assert response["success"] is True
        assert response["metadata"]["entities_materialized"] == 0
    
    def test_materialize_invalid_json_input(self):
        """Test error handling with invalid JSON input."""
        
        invalid_json = '{"incomplete": json'
        
        result = self.runner.invoke(materialize, [
            '--from-entities', invalid_json,
            '--format', 'json'
        ])
        
        assert result.exit_code == 0  # CLI returns error response, doesn't exit
        response = json.loads(result.output)
        assert response["success"] is False
        assert "INPUT_ERROR" in response["error"]["code"]
    
    def test_materialize_no_dependencies_graceful_degradation(self):
        """Test that materialization works even with missing optional dependencies."""
        
        simple_entities = json.dumps([
            {"@type": "Thing", "name": "Test Entity"}
        ])
        
        result = self.runner.invoke(materialize, [
            '--from-entities', simple_entities,
            '--format', 'json'
        ])
        
        assert result.exit_code == 0
        response = json.loads(result.output)
        assert response["success"] is True
        
        # Should still create entities even without advanced features
        assert response["metadata"]["entities_materialized"] >= 1