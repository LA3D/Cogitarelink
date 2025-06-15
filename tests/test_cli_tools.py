"""Test CLI tools following Jeremy Howard's test-as-you-go approach.

Critical tests for agent reliability - ensure all 5 CLI tools work correctly.
"""

import json
import subprocess
import tempfile
from pathlib import Path
from typing import List, Dict, Any

import pytest


def run_cli_command(command: str, args: List[str], timeout: int = 30) -> subprocess.CompletedProcess:
    """Run CLI command and return result."""
    cmd = ["uv", "run", command] + args
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=Path(__file__).parent.parent
        )
        return result
    except subprocess.TimeoutExpired:
        pytest.fail(f"Command timed out: {' '.join(cmd)}")


def parse_json_output(result: subprocess.CompletedProcess) -> Dict[str, Any]:
    """Parse JSON output from CLI command."""
    if result.returncode != 0:
        pytest.fail(f"Command failed: {result.stderr}")
    
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as e:
        pytest.fail(f"Invalid JSON output: {e}\nOutput: {result.stdout}")


class TestClSearch:
    """Test cl_search tool functionality."""
    
    def test_cl_search_wikidata_api_basic(self):
        """Test basic Wikidata search using API."""
        result = run_cli_command("cl_search", ["insulin", "--limit", "2", "--format", "json"])
        
        assert result.returncode == 0
        data = parse_json_output(result)
        
        # Check structure
        assert data["query"] == "insulin"
        assert data["endpoint"] == "wikidata"
        assert data["count"] == 2
        assert len(data["results"]) == 2
        
        # Check result format
        first_result = data["results"][0]
        assert "id" in first_result
        assert "label" in first_result
        assert "type" in first_result
        assert "url" in first_result
    
    def test_cl_search_text_format(self):
        """Test text output format."""
        result = run_cli_command("cl_search", ["insulin", "--limit", "1", "--format", "text"])
        
        assert result.returncode == 0
        assert "Found 1 results for 'insulin':" in result.stdout
        assert "Q" in result.stdout  # Should contain Wikidata ID
    
    def test_cl_search_error_handling(self):
        """Test search error handling."""
        # Empty query should fail
        result = run_cli_command("cl_search", ["", "--format", "json"])
        assert result.returncode == 1
        
        error_data = json.loads(result.stderr)
        assert "error" in error_data
        assert "empty" in error_data["error"].lower()


class TestClFetch:
    """Test cl_fetch tool functionality."""
    
    def test_cl_fetch_wikidata_basic(self):
        """Test basic Wikidata entity fetch."""
        result = run_cli_command("cl_fetch", ["Q7240673", "--format", "json"])  # preproinsulin
        
        assert result.returncode == 0
        data = parse_json_output(result)
        
        assert data["id"] == "Q7240673"
        assert data["type"] == "entity"
        assert "labels" in data
        assert "descriptions" in data
        
        # Check English label exists
        if "en" in data["labels"]:
            assert "value" in data["labels"]["en"]
    
    def test_cl_fetch_text_format(self):
        """Test text output format."""
        result = run_cli_command("cl_fetch", ["Q7240673", "--format", "text"])
        
        assert result.returncode == 0
        assert "Entity: Q7240673" in result.stdout
        assert "Label:" in result.stdout or "Properties:" in result.stdout


class TestClDiscover:
    """Test cl_discover tool functionality."""
    
    def test_cl_discover_wikidata_capabilities(self):
        """Test discovering Wikidata capabilities."""
        result = run_cli_command("cl_discover", ["wikidata", "--capabilities"])
        
        assert result.returncode == 0
        data = parse_json_output(result)
        
        assert data["endpoint"] == "wikidata"
        assert data["url"] == "https://query.wikidata.org/sparql"
        
        caps = data["capabilities"]
        assert len(caps["search_methods"]) >= 1
        assert "sparql" in caps["query_methods"]
        assert caps["supports_describe"] is True
        assert caps["supports_introspection"] is True


class TestClQuery:
    """Test cl_query tool functionality."""
    
    def test_cl_query_basic_sparql(self):
        """Test basic SPARQL query execution."""
        query = "SELECT ?s ?p ?o WHERE { ?s ?p ?o } LIMIT 2"
        result = run_cli_command("cl_query", [query, "--endpoint", "wikidata"])
        
        assert result.returncode == 0
        data = parse_json_output(result)
        
        assert data["query"] == query
        assert data["endpoint"] == "wikidata"
        assert len(data["results"]) <= 2
        assert data["count"] == len(data["results"])
    
    def test_cl_query_text_format(self):
        """Test text table output format."""
        query = "SELECT ?item WHERE { ?item wdt:P31 wd:Q8054 } LIMIT 2"
        result = run_cli_command("cl_query", [query, "--format", "text"])
        
        assert result.returncode == 0
        assert "Query results" in result.stdout
        # Text format uses table structure with dashes
        assert ("item" in result.stdout and "-" in result.stdout) or "No results" in result.stdout
    
    def test_cl_query_empty_query(self):
        """Test empty query handling."""
        result = run_cli_command("cl_query", ["", "--format", "json"])
        
        assert result.returncode == 1
        error_data = json.loads(result.stderr)
        assert "error" in error_data


class TestClResolve:
    """Test cl_resolve tool functionality."""
    
    def test_cl_resolve_uniprot_to_wikidata(self):
        """Test resolving UniProt ID to Wikidata."""
        result = run_cli_command("cl_resolve", ["P04637", "--from-db", "uniprot", "--to-db", "wikidata"])
        
        assert result.returncode == 0
        data = parse_json_output(result)
        
        assert data["identifier"] == "P04637"
        assert data["source_db"] == "uniprot"
        assert data["target_db"] == "wikidata"
        
        # Should find p53 protein
        if data["results"]:
            first_result = data["results"][0]
            assert "Q" in first_result["target_id"]  # Wikidata ID format


class TestCliErrorHandling:
    """Test error handling across all CLI tools."""
    
    def test_all_tools_handle_empty_args(self):
        """Test all tools handle missing required arguments."""
        tools_and_args = [
            ("cl_search", []),
            ("cl_fetch", []),
            ("cl_discover", []),
            ("cl_query", []),
            ("cl_resolve", [])
        ]
        
        for tool, args in tools_and_args:
            result = run_cli_command(tool, args)
            # Should fail with non-zero exit code
            assert result.returncode != 0, f"{tool} should fail with empty args"
    
    def test_all_tools_support_help(self):
        """Test all tools support --help flag."""
        tools = ["cl_search", "cl_fetch", "cl_discover", "cl_query", "cl_resolve"]
        
        for tool in tools:
            result = run_cli_command(tool, ["--help"])
            assert result.returncode == 0
            assert "Usage:" in result.stdout or "Examples:" in result.stdout


if __name__ == "__main__":
    # Run tests directly with pytest
    pytest.main([__file__, "-v"])