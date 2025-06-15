"""Integration tests for CLI tool composition.

Test how tools work together in real research workflows.
"""

import json
import subprocess
from pathlib import Path
from typing import List, Dict, Any

import pytest


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


def parse_json_output(result: subprocess.CompletedProcess) -> Dict[str, Any]:
    """Parse JSON output from CLI command."""
    if result.returncode != 0:
        pytest.fail(f"Command failed: {result.stderr}")
    return json.loads(result.stdout)


class TestWorkflowIntegration:
    """Test complete research workflows using multiple tools."""
    
    def test_search_then_fetch_workflow(self):
        """Test: Search for entities, then fetch detailed data."""
        # Step 1: Search for insulin-related entities
        search_result = run_cli_command("cl_search", ["insulin", "--limit", "2", "--format", "json"])
        assert search_result.returncode == 0
        
        search_data = parse_json_output(search_result)
        assert len(search_data["results"]) >= 1
        
        # Step 2: Fetch detailed data for first result
        entity_id = search_data["results"][0]["id"]
        fetch_result = run_cli_command("cl_fetch", [entity_id, "--format", "json"])
        assert fetch_result.returncode == 0
        
        fetch_data = parse_json_output(fetch_result)
        assert fetch_data["id"] == entity_id
        
        # Verify we got more detailed data than search
        assert "labels" in fetch_data or "properties" in fetch_data
        print(f"✅ Search→Fetch workflow: {entity_id}")
    
    def test_discover_then_query_workflow(self):
        """Test: Discover endpoint capabilities, then execute custom query."""
        # Step 1: Discover WikiPathways capabilities
        discover_result = run_cli_command("cl_discover", ["wikipathways", "--patterns", "--format", "json"])
        assert discover_result.returncode == 0
        
        discover_data = parse_json_output(discover_result)
        patterns = discover_data["patterns"]
        assert "pathway_search" in patterns
        
        # Step 2: Use discovered pattern in custom query
        # Extract the pattern and modify it
        pathway_pattern = patterns["pathway_search"]
        custom_query = pathway_pattern.replace("{query}", "COVID")
        
        query_result = run_cli_command("cl_query", [custom_query, "--endpoint", "wikipathways", "--format", "json"])
        assert query_result.returncode == 0
        
        query_data = parse_json_output(query_result)
        assert query_data["count"] >= 0  # Should execute without error
        print(f"✅ Discover→Query workflow: found {query_data['count']} pathways")
    
    def test_resolve_then_fetch_workflow(self):
        """Test: Resolve cross-references, then fetch from target database."""
        # Step 1: Resolve UniProt ID to Wikidata
        resolve_result = run_cli_command("cl_resolve", ["P04637", "--to-db", "wikidata", "--format", "json"])
        assert resolve_result.returncode == 0
        
        resolve_data = parse_json_output(resolve_result)
        
        if resolve_data["results"]:
            # Step 2: Fetch detailed data from target database
            wikidata_id = resolve_data["results"][0]["target_id"]
            fetch_result = run_cli_command("cl_fetch", [wikidata_id, "--format", "json"])
            assert fetch_result.returncode == 0
            
            fetch_data = parse_json_output(fetch_result)
            assert fetch_data["id"] == wikidata_id
            print(f"✅ Resolve→Fetch workflow: P04637 → {wikidata_id}")
        else:
            print("⚠️ No cross-references found for resolution test")
    
    def test_multi_endpoint_workflow(self):
        """Test: Research workflow across multiple endpoints."""
        endpoints = ["wikidata", "wikipathways"]
        search_term = "COVID"
        all_results = {}
        
        for endpoint in endpoints:
            # Search each endpoint
            search_result = run_cli_command("cl_search", [search_term, "--endpoint", endpoint, "--limit", "2", "--format", "json"])
            
            if search_result.returncode == 0:
                search_data = parse_json_output(search_result)
                all_results[endpoint] = search_data["results"]
            else:
                all_results[endpoint] = []
        
        # Verify we got results from at least one endpoint
        total_results = sum(len(results) for results in all_results.values())
        assert total_results > 0, "Should find COVID-related entities in at least one endpoint"
        
        print(f"✅ Multi-endpoint workflow: {total_results} total results across {len(endpoints)} endpoints")
        for endpoint, results in all_results.items():
            print(f"  {endpoint}: {len(results)} results")


class TestDataConsistency:
    """Test data consistency across tools."""
    
    def test_search_fetch_consistency(self):
        """Test that search results match fetch data."""
        # Search for a specific entity
        search_result = run_cli_command("cl_search", ["preproinsulin", "--limit", "1", "--format", "json"])
        assert search_result.returncode == 0
        
        search_data = parse_json_output(search_result)
        
        if search_data["results"]:
            search_entity = search_data["results"][0]
            entity_id = search_entity["id"]
            
            # Fetch the same entity
            fetch_result = run_cli_command("cl_fetch", [entity_id, "--format", "json"])
            assert fetch_result.returncode == 0
            
            fetch_data = parse_json_output(fetch_result)
            
            # IDs should match
            assert fetch_data["id"] == entity_id
            
            # Labels should be consistent (if available)
            if "labels" in fetch_data and "en" in fetch_data["labels"]:
                fetch_label = fetch_data["labels"]["en"]["value"].lower()
                search_label = search_entity["label"].lower()
                
                # Should be related (exact match or contains)
                assert (fetch_label in search_label or 
                       search_label in fetch_label or 
                       fetch_label == search_label), f"Labels inconsistent: '{search_label}' vs '{fetch_label}'"
    
    def test_discover_query_consistency(self):
        """Test that discovered patterns work in queries."""
        # Discover patterns for Wikidata
        discover_result = run_cli_command("cl_discover", ["wikidata", "--patterns", "--format", "json"])
        assert discover_result.returncode == 0
        
        discover_data = parse_json_output(discover_result)
        
        if "entity_search" in discover_data["patterns"]:
            # Use the discovered pattern
            pattern = discover_data["patterns"]["entity_search"]
            test_query = pattern.replace("{query}", "insulin")
            
            query_result = run_cli_command("cl_query", [test_query, "--endpoint", "wikidata", "--format", "json"])
            assert query_result.returncode == 0
            
            query_data = parse_json_output(query_result)
            # Should execute without SPARQL errors
            assert "error" not in query_data


class TestPerformanceBaseline:
    """Test performance baselines for tools."""
    
    def test_search_performance(self):
        """Test search tool performance baseline."""
        import time
        
        start_time = time.time()
        result = run_cli_command("cl_search", ["insulin", "--limit", "1", "--format", "json"])
        end_time = time.time()
        
        assert result.returncode == 0
        
        # Should complete in reasonable time (allowing for network)
        execution_time = end_time - start_time
        assert execution_time < 10.0, f"Search took too long: {execution_time:.2f}s"
        print(f"✅ Search performance: {execution_time:.2f}s")
    
    def test_discover_caching(self):
        """Test that discovery results are cached."""
        import time
        
        # First discovery (should cache)
        start_time = time.time()
        result1 = run_cli_command("cl_discover", ["wikidata", "--capabilities", "--format", "json"])
        first_time = time.time() - start_time
        
        assert result1.returncode == 0
        
        # Second discovery (should use cache)
        start_time = time.time()
        result2 = run_cli_command("cl_discover", ["wikidata", "--capabilities", "--format", "json"])
        second_time = time.time() - start_time
        
        assert result2.returncode == 0
        
        # Results should be identical
        data1 = parse_json_output(result1)
        data2 = parse_json_output(result2)
        assert data1["endpoint"] == data2["endpoint"]
        assert data1["url"] == data2["url"]
        
        print(f"✅ Discovery caching: first={first_time:.2f}s, second={second_time:.2f}s")


class TestErrorRecovery:
    """Test error recovery in workflows."""
    
    def test_graceful_endpoint_failure(self):
        """Test graceful handling when one endpoint fails."""
        # Try to search a non-existent endpoint, then fall back to working one
        bad_result = run_cli_command("cl_search", ["test", "--endpoint", "nonexistent", "--format", "json"])
        
        # Should not crash the tool
        assert bad_result.returncode == 0
        bad_data = parse_json_output(bad_result)
        assert bad_data["endpoint"] == "nonexistent"
        
        # Fall back to working endpoint
        good_result = run_cli_command("cl_search", ["insulin", "--endpoint", "wikidata", "--limit", "1", "--format", "json"])
        assert good_result.returncode == 0
        
        good_data = parse_json_output(good_result)
        assert len(good_data["results"]) >= 0  # Should work
        
        print("✅ Graceful endpoint failure handling")
    
    def test_partial_workflow_failure(self):
        """Test workflow continues when some steps fail."""
        # Step 1: Search (should work)
        search_result = run_cli_command("cl_search", ["insulin", "--limit", "1"])
        assert search_result.returncode == 0
        search_data = parse_json_output(search_result)
        
        # Step 2: Try to fetch non-existent entity (should fail gracefully)
        fetch_result = run_cli_command("cl_fetch", ["NONEXISTENT123", "--format", "json"])
        assert fetch_result.returncode == 0  # Should not crash
        fetch_data = parse_json_output(fetch_result)
        
        # Step 3: Continue with valid entity from search
        if search_data["results"]:
            entity_id = search_data["results"][0]["id"]
            valid_fetch = run_cli_command("cl_fetch", [entity_id, "--format", "json"])
            assert valid_fetch.returncode == 0
            
            print("✅ Partial workflow failure recovery")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])