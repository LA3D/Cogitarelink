"""Tests for cl_materialize CLI tool with dual SHACL modes."""

from __future__ import annotations

import json
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, mock_open, AsyncMock
from click.testing import CliRunner

from cogitarelink.cli.cl_materialize import materialize, _extract_construct_queries_from_shacl
from cogitarelink.core.entity import Entity


class TestClMaterialize:
    """Test suite for cl_materialize CLI tool."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        
        # Sample SPARQL results JSON
        self.sample_sparql_results = {
            "results": [
                {"item": "http://www.wikidata.org/entity/Q24190"},
                {"item": "http://www.wikidata.org/entity/Q30530"}
            ]
        }
        
        # Sample entities JSON
        self.sample_entities = [
            {
                "@type": "Protein",
                "identifier": "P04637",
                "name": "Tumor protein p53"
            },
            {
                "@type": "Protein", 
                "identifier": "P53039",
                "name": "Spike protein"
            }
        ]
        
        # Sample SHACL rules with CONSTRUCT queries
        self.sample_shacl_rules = """
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix ex: <http://example.org/> .

ex:SubclassTransitivityRule a sh:SPARQLRule ;
    rdfs:comment "RDFS subclass transitivity" ;
    sh:construct '''
        CONSTRUCT {
            ?subclass rdfs:subClassOf ?superclass .
        } WHERE {
            ?subclass rdfs:subClassOf ?intermediate .
            ?intermediate rdfs:subClassOf ?superclass .
            FILTER (?subclass != ?superclass)
        }
    ''' .

ex:DomainInferenceRule a sh:SPARQLRule ;
    rdfs:comment "Property domain inference" ;
    sh:construct '''
        CONSTRUCT {
            ?instance a ?domain .
        } WHERE {
            ?property rdfs:domain ?domain .
            ?instance ?property ?value .
        }
    ''' .
        """

    def test_materialize_from_sparql_results_json_string(self):
        """Test materialization from SPARQL results as JSON string."""
        
        results_json = json.dumps(self.sample_sparql_results)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ttl', delete=False) as f:
            f.write(self.sample_shacl_rules)
            shapes_file = f.name
        
        try:
            result = self.runner.invoke(materialize, [
                '--from-sparql-results', results_json,
                '--shapes-file', shapes_file,
                '--format', 'json'
            ])
            
            assert result.exit_code == 0
            response = json.loads(result.output)
            assert response["success"] is True
            assert "entity_count" in response["data"]
            assert response["metadata"]["entities_materialized"] >= 2
            
        finally:
            Path(shapes_file).unlink()

    def test_materialize_from_entities_json(self):
        """Test materialization from entities JSON."""
        
        entities_json = json.dumps(self.sample_entities)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ttl', delete=False) as f:
            f.write(self.sample_shacl_rules)
            shapes_file = f.name
        
        try:
            result = self.runner.invoke(materialize, [
                '--from-entities', entities_json,
                '--shapes-file', shapes_file,
                '--format', 'json'
            ])
            
            assert result.exit_code == 0
            response = json.loads(result.output)
            assert response["success"] is True
            assert "entity_count" in response["data"]
            
        finally:
            Path(shapes_file).unlink()

    @patch('cogitarelink.cli.cl_materialize._HAS_SPARQLWRAPPER', True)
    @patch('cogitarelink.cli.cl_materialize._HAS_RDFLIB', True)
    @patch('cogitarelink.cli.cl_materialize.SPARQLWrapper')
    def test_materialize_from_sparql_endpoint(self, mock_sparql_wrapper):
        """Test SPARQL CONSTRUCT materialization from endpoint."""
        
        # Mock SPARQLWrapper response
        from unittest.mock import MagicMock
        mock_query_result = MagicMock()
        mock_graph = MagicMock()
        mock_graph.serialize.return_value = """
        @prefix ex: <http://example.org/> .
        ex:protein1 a ex:Protein ;
            ex:name "Test Protein" .
        """
        mock_query_result.convert.return_value = mock_graph
        
        mock_sparql_instance = MagicMock()
        mock_sparql_instance.query.return_value = mock_query_result
        mock_sparql_wrapper.return_value = mock_sparql_instance
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ttl', delete=False) as f:
            f.write(self.sample_shacl_rules)
            rules_file = f.name
        
        try:
            result = self.runner.invoke(materialize, [
                '--from-sparql-endpoint', 'wikidata',
                '--rules-file', rules_file,
                '--format', 'json'
            ])
            
            assert result.exit_code == 0
            response = json.loads(result.output)
            assert response["success"] is True
            assert "materialization_method" in response["data"]["materialization_summary"]
            assert response["data"]["materialization_summary"].get("materialization_method") == "sparql_construct"
            
        finally:
            Path(rules_file).unlink()

    @patch('cogitarelink.cli.cl_materialize._HAS_REASONING', True)
    @patch('cogitarelink.cli.cl_materialize.reason_over')
    def test_shacl_materialization_with_pyshacl(self, mock_reason_over):
        """Test local SHACL materialization using pyshacl."""
        
        # Mock reason_over response
        mock_reason_over.return_value = (
            '',  # Empty patch when no new facts derived
            "SHACL run; conforms:True; added 0 triples"
        )
        
        entities_json = json.dumps(self.sample_entities)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ttl', delete=False) as f:
            f.write(self.sample_shacl_rules)
            shapes_file = f.name
        
        try:
            result = self.runner.invoke(materialize, [
                '--from-entities', entities_json,
                '--shapes-file', shapes_file,
                '--format', 'json'
            ])
            
            assert result.exit_code == 0
            response = json.loads(result.output)
            assert response["success"] is True
            
            # Verify reason_over was called for materialization
            assert mock_reason_over.called
            
        finally:
            Path(shapes_file).unlink()

    def test_extract_construct_queries_from_shacl(self):
        """Test extraction of CONSTRUCT queries from SHACL rules."""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ttl', delete=False) as f:
            f.write(self.sample_shacl_rules)
            rules_file = f.name
        
        try:
            # This is an async function, so we need to run it properly
            import asyncio
            construct_queries = asyncio.run(_extract_construct_queries_from_shacl(rules_file))
            
            assert len(construct_queries) == 2
            
            # Check first rule
            rule_name_1, query_1 = construct_queries[0]
            assert "SubclassTransitivityRule" in rule_name_1
            assert "CONSTRUCT" in query_1
            assert "rdfs:subClassOf" in query_1
            
            # Check second rule
            rule_name_2, query_2 = construct_queries[1]
            assert "DomainInferenceRule" in rule_name_2
            assert "CONSTRUCT" in query_2
            assert "rdfs:domain" in query_2
            
        finally:
            Path(rules_file).unlink()

    def test_materialize_no_input_error(self):
        """Test error handling when no input is provided."""
        
        result = self.runner.invoke(materialize, [
            '--format', 'json'
        ])
        
        assert result.exit_code == 0  # CLI doesn't exit with error, returns error response
        response = json.loads(result.output)
        assert response["success"] is False
        assert "INPUT_ERROR" in response["error"]["code"]

    def test_materialize_human_output_format(self):
        """Test human-readable output format."""
        
        entities_json = json.dumps(self.sample_entities)
        
        result = self.runner.invoke(materialize, [
            '--from-entities', entities_json,
            '--format', 'human'
        ])
        
        assert result.exit_code == 0
        assert "Knowledge Materialization Complete" in result.output
        assert "Entities:" in result.output

    def test_materialize_entities_output_format(self):
        """Test entities output format."""
        
        entities_json = json.dumps(self.sample_entities)
        
        result = self.runner.invoke(materialize, [
            '--from-entities', entities_json,
            '--format', 'entities'
        ])
        
        assert result.exit_code == 0
        assert "# Materialized Entities" in result.output
        assert "Count:" in result.output

    def test_materialize_with_context_chaining(self):
        """Test materialization with context chaining."""
        
        entities_json = json.dumps(self.sample_entities)
        context_id = "ctx_test_123"
        
        result = self.runner.invoke(materialize, [
            '--from-entities', entities_json,
            '--context-id', context_id,
            '--format', 'json'
        ])
        
        assert result.exit_code == 0
        response = json.loads(result.output)
        assert response["success"] is True
        assert response.get("context_id") == context_id
        assert "chaining_context" in response["suggestions"]

    def test_materialize_detailed_response_level(self):
        """Test materialization with detailed response level."""
        
        entities_json = json.dumps(self.sample_entities)
        
        result = self.runner.invoke(materialize, [
            '--from-entities', entities_json,
            '--level', 'detailed',
            '--format', 'json'
        ])
        
        assert result.exit_code == 0
        response = json.loads(result.output)
        assert response["success"] is True
        assert "claude_guidance" in response
        assert "suggestions" in response

    @patch('cogitarelink.cli.cl_materialize._HAS_RDFLIB', False)
    def test_materialize_missing_rdflib_dependency(self):
        """Test error handling when RDFLib is not available for SPARQL endpoint mode."""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ttl', delete=False) as f:
            f.write(self.sample_shacl_rules)
            rules_file = f.name
        
        try:
            result = self.runner.invoke(materialize, [
                '--from-sparql-endpoint', 'wikidata',
                '--rules-file', rules_file,
                '--format', 'json'
            ])
            
            assert result.exit_code == 0
            response = json.loads(result.output)
            assert response["success"] is True  # Should still complete with empty results
            assert response["data"]["materialization_summary"]["rules_applied"] == 0
            
        finally:
            Path(rules_file).unlink()

    @patch('cogitarelink.cli.cl_materialize._HAS_REASONING', False)
    def test_materialize_missing_reasoning_dependency(self):
        """Test behavior when SHACL reasoning is not available."""
        
        entities_json = json.dumps(self.sample_entities)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ttl', delete=False) as f:
            f.write(self.sample_shacl_rules)
            shapes_file = f.name
        
        try:
            result = self.runner.invoke(materialize, [
                '--from-entities', entities_json,
                '--shapes-file', shapes_file,
                '--format', 'json'
            ])
            
            assert result.exit_code == 0
            response = json.loads(result.output)
            assert response["success"] is True
            # Should still work but without SHACL materialization
            assert response["data"]["materialization_summary"]["rules_applied"] == 0
            
        finally:
            Path(shapes_file).unlink()

    def test_sparql_endpoint_url_mapping(self):
        """Test SPARQL endpoint URL mapping for common endpoints."""
        
        from cogitarelink.cli.cl_materialize import _determine_sparql_endpoint_url
        
        # Test known endpoints
        assert _determine_sparql_endpoint_url("wikidata") == "https://query.wikidata.org/sparql"
        assert _determine_sparql_endpoint_url("uniprot") == "https://sparql.uniprot.org/sparql"
        assert _determine_sparql_endpoint_url("dbpedia") == "https://dbpedia.org/sparql"
        
        # Test direct URL passthrough
        custom_url = "https://example.org/sparql"
        assert _determine_sparql_endpoint_url(custom_url) == custom_url

    def test_entity_creation_from_sparql_results(self):
        """Test entity creation from SPARQL results with different formats."""
        
        # SPARQL JSON format with bindings
        sparql_json_bindings = {
            "results": {
                "bindings": [
                    {
                        "protein": {"value": "http://example.org/P53", "type": "uri"},
                        "name": {"value": "Tumor protein p53", "type": "literal"}
                    }
                ]
            }
        }
        
        results_json = json.dumps(sparql_json_bindings)
        
        result = self.runner.invoke(materialize, [
            '--from-sparql-results', results_json,
            '--format', 'json'
        ])
        
        assert result.exit_code == 0
        response = json.loads(result.output)
        assert response["success"] is True
        assert response["metadata"]["entities_materialized"] >= 1

    def test_comprehensive_agent_guidance(self):
        """Test that materialization provides comprehensive agent guidance."""
        
        entities_json = json.dumps(self.sample_entities)
        
        result = self.runner.invoke(materialize, [
            '--from-entities', entities_json,
            '--format', 'json'
        ])
        
        assert result.exit_code == 0
        response = json.loads(result.output)
        
        # Check comprehensive guidance structure
        assert "suggestions" in response
        assert "claude_guidance" in response
        
        # Should have basic entity information
        assert response["metadata"]["entities_materialized"] >= 2


class TestMaterializeIntegration:
    """Integration tests for cl_materialize with real data."""
    
    def test_materialize_with_real_sparql_results(self):
        """Test materialization with realistic SPARQL results."""
        
        runner = CliRunner()
        
        # Use the existing test file
        sparql_results_file = "/tmp/sparql_results.json"
        
        result = runner.invoke(materialize, [
            '--from-sparql-results', sparql_results_file,
            '--vocab', 'bioschemas',
            '--format', 'json'
        ])
        
        assert result.exit_code == 0
        response = json.loads(result.output)
        assert response["success"] is True
        assert response["metadata"]["entities_materialized"] == 2
        
        # Check entity count
        assert response["data"]["entity_count"] == 2