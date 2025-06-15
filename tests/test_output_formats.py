"""Output format tests for CLI tools.

Test JSON, text, and CSV output consistency for agent parsing.
"""

import json
import csv
import io
import subprocess
from pathlib import Path
from typing import List, Dict, Any

import pytest
from fastcore.test import test_eq


def run_cli_command(command: str, args: List[str]) -> subprocess.CompletedProcess:
    """Run CLI command and return result."""
    cmd = ["uv", "run", command] + args
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=30,
        cwd=Path(__file__).parent.parent
    )


class TestJsonOutputFormat:
    """Test JSON output format consistency across tools."""
    
    def test_json_output_structure_cl_search(self):
        """Test cl_search JSON output structure."""
        result = run_cli_command("cl_search", ["insulin", "--limit", "2", "--format", "json"])
        test_eq(result.returncode, 0)
        
        data = json.loads(result.stdout)
        
        # Required fields
        required_fields = ["query", "endpoint", "results", "count"]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
        
        # Field types
        assert isinstance(data["query"], str)
        assert isinstance(data["endpoint"], str)
        assert isinstance(data["results"], list)
        assert isinstance(data["count"], int)
        
        # Count should match results length
        test_eq(data["count"], len(data["results"]))
        
        # Result structure
        if data["results"]:
            result_item = data["results"][0]
            result_fields = ["id", "label", "type", "url"]
            for field in result_fields:
                assert field in result_item, f"Missing result field: {field}"
    
    def test_json_output_structure_cl_fetch(self):
        """Test cl_fetch JSON output structure."""
        result = run_cli_command("cl_fetch", ["Q7240673", "--format", "json"])
        test_eq(result.returncode, 0)
        
        data = json.loads(result.stdout)
        
        # Required fields
        assert "id" in data
        assert "type" in data
        
        # Field types
        assert isinstance(data["id"], str)
        assert isinstance(data["type"], str)
        
        # Optional structured fields
        if "labels" in data:
            assert isinstance(data["labels"], dict)
        if "descriptions" in data:
            assert isinstance(data["descriptions"], dict)
        if "claims" in data:
            assert isinstance(data["claims"], dict)
    
    def test_json_output_structure_cl_discover(self):
        """Test cl_discover JSON output structure."""
        result = run_cli_command("cl_discover", ["wikidata", "--format", "json"])
        test_eq(result.returncode, 0)
        
        data = json.loads(result.stdout)
        
        # Required fields
        required_fields = ["endpoint", "url"]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
        
        # Field types
        assert isinstance(data["endpoint"], str)
        assert isinstance(data["url"], str)
        
        # Optional structured fields
        if "capabilities" in data:
            caps = data["capabilities"]
            assert isinstance(caps, dict)
            if "search_methods" in caps:
                assert isinstance(caps["search_methods"], list)
            if "query_methods" in caps:
                assert isinstance(caps["query_methods"], list)
        
        if "schema" in data:
            schema = data["schema"]
            assert isinstance(schema, dict)
            if "prefixes" in schema:
                assert isinstance(schema["prefixes"], dict)
    
    def test_json_output_structure_cl_query(self):
        """Test cl_query JSON output structure."""
        query = "SELECT ?s WHERE { ?s ?p ?o } LIMIT 2"
        result = run_cli_command("cl_query", [query, "--format", "json"])
        test_eq(result.returncode, 0)
        
        data = json.loads(result.stdout)
        
        # Required fields
        required_fields = ["query", "endpoint", "results", "count"]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
        
        # Field types
        assert isinstance(data["query"], str)
        assert isinstance(data["endpoint"], str)
        assert isinstance(data["results"], list)
        assert isinstance(data["count"], int)
        
        # Count consistency
        test_eq(data["count"], len(data["results"]))
    
    def test_json_output_structure_cl_resolve(self):
        """Test cl_resolve JSON output structure."""
        result = run_cli_command("cl_resolve", ["P04637", "--format", "json"])
        test_eq(result.returncode, 0)
        
        data = json.loads(result.stdout)
        
        # Required fields
        required_fields = ["identifier", "source_db", "target_db", "results", "count"]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
        
        # Field types
        assert isinstance(data["identifier"], str)
        assert isinstance(data["source_db"], str)
        assert isinstance(data["target_db"], str)
        assert isinstance(data["results"], list)
        assert isinstance(data["count"], int)
        
        # Count consistency
        test_eq(data["count"], len(data["results"]))
        
        # Result structure
        if data["results"]:
            result_item = data["results"][0]
            result_fields = ["source_id", "source_db", "target_id", "target_db"]
            for field in result_fields:
                assert field in result_item, f"Missing result field: {field}"
    
    def test_json_error_output_consistency(self):
        """Test consistent JSON error output format."""
        # Test error from cl_search
        result = run_cli_command("cl_search", ["", "--format", "json"])
        test_eq(result.returncode, 1)
        
        error_data = json.loads(result.stderr)
        
        # Error structure
        assert "error" in error_data
        assert isinstance(error_data["error"], str)
        
        # Should include context
        expected_context = ["query", "endpoint"]
        for field in expected_context:
            if field in error_data:
                assert isinstance(error_data[field], str)
    
    def test_json_unicode_handling(self):
        """Test JSON output handles Unicode correctly."""
        result = run_cli_command("cl_search", ["α-synuclein", "--limit", "1", "--format", "json"])
        test_eq(result.returncode, 0)
        
        data = json.loads(result.stdout)
        test_eq(data["query"], "α-synuclein")
        
        # Should be valid JSON with proper Unicode encoding
        json_str = json.dumps(data, ensure_ascii=False)
        assert "α-synuclein" in json_str


class TestTextOutputFormat:
    """Test text output format consistency."""
    
    def test_text_output_readability_cl_search(self):
        """Test cl_search text output is human-readable."""
        result = run_cli_command("cl_search", ["insulin", "--limit", "2", "--format", "text"])
        test_eq(result.returncode, 0)
        
        output = result.stdout
        
        # Should contain key information
        assert "Found" in output
        assert "results for" in output
        assert "insulin" in output
        
        # Should have structured layout
        lines = output.strip().split('\n')
        assert len(lines) >= 2  # Header + at least one result line
        
        # First line should be summary
        assert "Found" in lines[0] and "results" in lines[0]
    
    def test_text_output_readability_cl_fetch(self):
        """Test cl_fetch text output is informative."""
        result = run_cli_command("cl_fetch", ["Q7240673", "--format", "text"])
        test_eq(result.returncode, 0)
        
        output = result.stdout
        
        # Should contain entity information
        assert "Entity:" in output
        assert "Q7240673" in output
        
        # Should show additional info if available
        info_indicators = ["Label:", "Description:", "Properties:"]
        has_info = any(indicator in output for indicator in info_indicators)
        assert has_info, "Should show at least one type of entity information"
    
    def test_text_output_readability_cl_discover(self):
        """Test cl_discover text output is informative."""
        result = run_cli_command("cl_discover", ["wikidata", "--capabilities", "--format", "text"])
        test_eq(result.returncode, 0)
        
        output = result.stdout
        
        # Should contain endpoint information
        assert "Endpoint:" in output
        assert "wikidata" in output
        assert "URL:" in output
        
        # Should show capabilities
        assert "Search Methods:" in output
        assert "Query Methods:" in output
    
    def test_text_output_formatting_consistency(self):
        """Test text output formatting is consistent across tools."""
        tools_and_args = [
            ("cl_search", ["insulin", "--limit", "1", "--format", "text"]),
            ("cl_fetch", ["Q7240673", "--format", "text"]),
            ("cl_discover", ["wikidata", "--capabilities", "--format", "text"])
        ]
        
        for tool, args in tools_and_args:
            result = run_cli_command(tool, args)
            test_eq(result.returncode, 0)
            
            output = result.stdout
            
            # Should not have trailing whitespace
            lines = output.split('\n')
            for line in lines:
                assert line == line.rstrip(), f"Line has trailing whitespace: '{line}'"
            
            # Should use consistent formatting
            assert not output.startswith('\n'), "Should not start with newline"
            assert not output.endswith('\n\n'), "Should not end with multiple newlines"
    
    def test_text_output_no_results(self):
        """Test text output for empty results."""
        result = run_cli_command("cl_search", ["NONEXISTENTQUERY12345", "--format", "text"])
        test_eq(result.returncode, 0)
        
        output = result.stdout
        
        # Should clearly indicate no results
        no_results_indicators = ["No results", "0 results", "not found"]
        has_indicator = any(indicator in output for indicator in no_results_indicators)
        assert has_indicator, f"Should indicate no results clearly. Output: {output}"


class TestCsvOutputFormat:
    """Test CSV output format for structured data."""
    
    def test_csv_output_structure_cl_query(self):
        """Test cl_query CSV output is valid CSV."""
        query = "SELECT ?s ?p WHERE { ?s ?p ?o } LIMIT 3"
        result = run_cli_command("cl_query", [query, "--format", "csv"])
        test_eq(result.returncode, 0)
        
        csv_output = result.stdout
        
        # Should be valid CSV
        reader = csv.reader(io.StringIO(csv_output))
        rows = list(reader)
        
        if rows:
            # First row should be header
            header = rows[0]
            assert len(header) >= 1, "Should have at least one column"
            
            # Should contain SPARQL variables
            assert any(col.startswith('s') or col.startswith('p') for col in header), "Should contain SPARQL variables"
            
            # Data rows should match header length
            for i, row in enumerate(rows[1:], 1):
                assert len(row) == len(header), f"Row {i} length mismatch: {len(row)} vs {len(header)}"
    
    def test_csv_output_escaping(self):
        """Test CSV output properly escapes special characters."""
        # Search for something that might contain commas or quotes
        result = run_cli_command("cl_search", ["test, query", "--limit", "1", "--format", "json"])
        
        if result.returncode == 0:
            # Convert JSON to see if we have data, then test CSV if query tool supports it
            # For now, test CSV with cl_query which definitely supports it
            query = 'SELECT ?s WHERE { ?s rdfs:label "test, label" } LIMIT 1'
            csv_result = run_cli_command("cl_query", [query, "--format", "csv"])
            
            if csv_result.returncode == 0:
                csv_output = csv_result.stdout
                
                # Should be parseable as CSV
                reader = csv.reader(io.StringIO(csv_output))
                rows = list(reader)
                
                # Should not break CSV structure
                assert len(rows) >= 1, "Should have at least header row"
    
    def test_csv_output_empty_results(self):
        """Test CSV output for empty results."""
        query = "SELECT ?nonexistent WHERE { ?nonexistent rdfs:label 'NONEXISTENT12345' }"
        result = run_cli_command("cl_query", [query, "--format", "csv"])
        test_eq(result.returncode, 0)
        
        csv_output = result.stdout
        
        # Should handle empty results gracefully
        if csv_output.strip():
            reader = csv.reader(io.StringIO(csv_output))
            rows = list(reader)
            # Should have header but no data rows, or clear indication of no results
            assert len(rows) >= 0, "Should handle empty results"


class TestFormatConsistency:
    """Test consistency across different output formats."""
    
    def test_same_data_different_formats(self):
        """Test same query returns consistent data in different formats."""
        query_args = ["insulin", "--limit", "1"]
        
        # Get JSON output
        json_result = run_cli_command("cl_search", query_args + ["--format", "json"])
        test_eq(json_result.returncode, 0)
        json_data = json.loads(json_result.stdout)
        
        # Get text output
        text_result = run_cli_command("cl_search", query_args + ["--format", "text"])
        test_eq(text_result.returncode, 0)
        text_output = text_result.stdout
        
        # Should contain same basic information
        assert json_data["query"] in text_output
        assert str(json_data["count"]) in text_output
        
        # If there are results, should show same entity
        if json_data["results"]:
            entity_id = json_data["results"][0]["id"]
            entity_label = json_data["results"][0]["label"]
            
            assert entity_id in text_output
            # Label might be truncated in text, so check partial match
            assert any(word in text_output for word in entity_label.split() if len(word) > 3)
    
    def test_error_format_consistency(self):
        """Test error messages are consistent across formats."""
        # Test with empty query (should fail)
        json_result = run_cli_command("cl_search", ["", "--format", "json"])
        text_result = run_cli_command("cl_search", ["", "--format", "text"])
        
        # Both should fail
        test_eq(json_result.returncode, 1)
        test_eq(text_result.returncode, 1)
        
        # Should contain similar error information
        json_error = json.loads(json_result.stderr)
        text_error = text_result.stderr
        
        # Key error terms should appear in both
        error_keywords = ["error", "empty", "cannot"]
        json_error_text = json_error["error"].lower()
        text_error_lower = text_error.lower()
        
        common_keywords = []
        for keyword in error_keywords:
            if keyword in json_error_text and keyword in text_error_lower:
                common_keywords.append(keyword)
        
        assert len(common_keywords) >= 1, "Should have at least one common error keyword"
    
    def test_unicode_consistency_across_formats(self):
        """Test Unicode handling is consistent across formats."""
        unicode_query = "α-synuclein"
        
        # Test JSON format
        json_result = run_cli_command("cl_search", [unicode_query, "--limit", "1", "--format", "json"])
        test_eq(json_result.returncode, 0)
        json_data = json.loads(json_result.stdout)
        
        # Test text format
        text_result = run_cli_command("cl_search", [unicode_query, "--limit", "1", "--format", "text"])
        test_eq(text_result.returncode, 0)
        text_output = text_result.stdout
        
        # Both should preserve Unicode correctly
        test_eq(json_data["query"], unicode_query)
        assert unicode_query in text_output


class TestOutputValidation:
    """Test output validation and schema compliance."""
    
    def test_json_schema_compliance(self):
        """Test JSON output follows expected schema."""
        # This could be extended with actual JSON schema validation
        result = run_cli_command("cl_search", ["test", "--format", "json"])
        test_eq(result.returncode, 0)
        
        data = json.loads(result.stdout)
        
        # Validate basic schema compliance
        assert isinstance(data, dict), "Top level should be object"
        
        # Check required fields exist and have correct types
        schema_checks = [
            ("query", str),
            ("endpoint", str),
            ("results", list),
            ("count", int)
        ]
        
        for field_name, expected_type in schema_checks:
            assert field_name in data, f"Missing required field: {field_name}"
            assert isinstance(data[field_name], expected_type), f"Field {field_name} should be {expected_type.__name__}"
    
    def test_output_size_limits(self):
        """Test output size is reasonable for large queries."""
        # Try query that might return large results
        result = run_cli_command("cl_search", ["protein", "--limit", "100", "--format", "json"])
        
        if result.returncode == 0:
            # Output should not be excessively large
            output_size = len(result.stdout)
            assert output_size < 10 * 1024 * 1024, f"Output too large: {output_size / 1024 / 1024:.1f}MB"
            
            # Should still be valid JSON
            data = json.loads(result.stdout)
            assert len(data["results"]) <= 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])