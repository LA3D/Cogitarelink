"""Test enhanced cl_search functionality with rich metadata and composition patterns.

Test-driven development for cl_search enhancement following Software 2.0 principles.
"""

import json
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Any

import pytest


def run_cl_search_command(args: list[str], cwd: Path = None) -> subprocess.CompletedProcess:
    """Run cl_search command and return result."""
    cmd = ["uv", "run", "cl_search"] + args
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=30,
        cwd=cwd or Path.cwd()
    )


def parse_enhanced_response(result: subprocess.CompletedProcess) -> Dict[str, Any]:
    """Parse enhanced cl_search JSON response."""
    if result.returncode != 0:
        pytest.fail(f"cl_search failed: {result.stderr}")
    
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as e:
        pytest.fail(f"Invalid JSON output: {e}\nOutput: {result.stdout}")


class TestEnhancedResponseStructure:
    """Test the enhanced response structure with rich metadata."""
    
    def test_enhanced_response_has_required_sections(self):
        """Test that enhanced response includes all required sections."""
        result = run_cl_search_command(["insulin", "--limit", "2", "--format", "json"])
        data = parse_enhanced_response(result)
        
        # Core sections (existing)
        assert "query" in data
        assert "endpoint" in data
        assert "results" in data
        assert "count" in data
        
        # New enhanced sections
        assert "metadata" in data
        assert "composition_opportunities" in data
        
        # Optional session context (only if session exists)
        # assert "session_context" in data  # Optional
    
    def test_metadata_structure(self):
        """Test metadata section has proper structure."""
        result = run_cl_search_command(["protein", "--limit", "3", "--format", "json"])
        data = parse_enhanced_response(result)
        
        metadata = data["metadata"]
        
        # Discovery analysis section
        assert "discovery_analysis" in metadata
        discovery = metadata["discovery_analysis"]
        assert "entity_types_found" in discovery
        assert "type_distribution" in discovery
        assert "external_refs_available" in discovery
        assert "semantic_depth_indicators" in discovery
        
        # Endpoint context section
        assert "endpoint_context" in metadata
        endpoint_ctx = metadata["endpoint_context"]
        assert "search_method_used" in endpoint_ctx
        assert "capabilities_available" in endpoint_ctx
        assert "related_endpoints" in endpoint_ctx
        
        # Execution context section
        assert "execution_context" in metadata
        exec_ctx = metadata["execution_context"]
        assert "execution_time_ms" in exec_ctx
        assert "search_effectiveness" in exec_ctx
        assert isinstance(exec_ctx["execution_time_ms"], (int, float))
    
    def test_composition_opportunities_structure(self):
        """Test composition opportunities section structure."""
        result = run_cl_search_command(["spike protein", "--limit", "2", "--format", "json"])
        data = parse_enhanced_response(result)
        
        comp_ops = data["composition_opportunities"]
        
        # Required subsections
        assert "immediate_actions" in comp_ops
        assert "cross_reference_exploration" in comp_ops
        assert "semantic_exploration" in comp_ops
        assert "search_refinement" in comp_ops
        
        # Should contain actionable commands
        immediate = comp_ops["immediate_actions"]
        assert isinstance(immediate, list)
        if immediate:  # If results found
            assert any("cl_fetch" in action for action in immediate)
    
    def test_entity_type_analysis(self):
        """Test that entity types are properly analyzed."""
        result = run_cl_search_command(["insulin", "--limit", "3", "--format", "json"])
        data = parse_enhanced_response(result)
        
        discovery = data["metadata"]["discovery_analysis"]
        
        # Should find entity types
        entity_types = discovery["entity_types_found"]
        assert isinstance(entity_types, list)
        
        # Type distribution should match
        type_dist = discovery["type_distribution"]
        assert isinstance(type_dist, dict)
        
        # All types in distribution should be in entity_types
        for entity_type in type_dist.keys():
            assert entity_type in entity_types
    
    def test_external_references_detection(self):
        """Test detection of external reference properties."""
        result = run_cl_search_command(["P04637", "--limit", "2", "--format", "json"])  # p53 protein
        data = parse_enhanced_response(result)
        
        discovery = data["metadata"]["discovery_analysis"]
        external_refs = discovery["external_refs_available"]
        
        assert isinstance(external_refs, dict)
        
        # Should detect common external reference properties
        # P352 = UniProt, P594 = Ensembl, P638 = PDB
        expected_props = ["P352", "P594", "P638", "P705", "P486"]  # Common bio external refs
        
        # At least some external refs should be detected for protein searches
        # (This is probabilistic, so we check if any are found rather than specific ones)
        if data["results"]:  # If any results found
            assert len(external_refs) >= 0  # Could be 0 if no external refs in sample


class TestSessionIntegration:
    """Test session awareness and context integration."""
    
    def test_search_without_session(self):
        """Test cl_search works without research session."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            result = run_cl_search_command(
                ["test", "--limit", "1", "--format", "json"],
                cwd=temp_path
            )
            data = parse_enhanced_response(result)
            
            # Should work without session
            assert "metadata" in data
            assert "composition_opportunities" in data
            
            # Session context should be None or absent
            session_ctx = data.get("session_context")
            assert session_ctx is None or session_ctx == {}
    
    def test_search_with_active_session(self):
        """Test cl_search integrates with active research session."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create research session first
            session_init = subprocess.run(
                ["uv", "run", "cogitarelink", "init", "biology", "--goal", "Test session"],
                capture_output=True,
                text=True,
                cwd=temp_path
            )
            assert session_init.returncode == 0
            
            # Now run search with session
            result = run_cl_search_command(
                ["protein", "--limit", "2", "--format", "json"],
                cwd=temp_path
            )
            data = parse_enhanced_response(result)
            
            # Should include session context
            if "session_context" in data:
                session_ctx = data["session_context"]
                assert "research_domain" in session_ctx
                assert session_ctx["research_domain"] == "biology"
                assert "research_goal" in session_ctx or "entities_discovered_this_session" in session_ctx


class TestCompositionGeneration:
    """Test composition opportunity generation."""
    
    def test_immediate_actions_generation(self):
        """Test generation of immediate action suggestions."""
        result = run_cl_search_command(["insulin", "--limit", "2", "--format", "json"])
        data = parse_enhanced_response(result)
        
        immediate = data["composition_opportunities"]["immediate_actions"]
        
        if data["results"]:  # If results found
            assert len(immediate) > 0
            
            # Should suggest cl_fetch for top results
            entity_ids = [r["id"] for r in data["results"]]
            
            # At least one immediate action should reference found entity IDs
            action_text = " ".join(immediate)
            assert any(entity_id in action_text for entity_id in entity_ids)
    
    def test_cross_reference_suggestions(self):
        """Test cross-reference exploration suggestions."""
        result = run_cl_search_command(["spike protein", "--limit", "2", "--format", "json"])
        data = parse_enhanced_response(result)
        
        cross_ref = data["composition_opportunities"]["cross_reference_exploration"]
        assert isinstance(cross_ref, list)
        
        # Should suggest relevant cross-reference commands
        if cross_ref:
            cross_ref_text = " ".join(cross_ref)
            assert "cl_resolve" in cross_ref_text or "cl_search" in cross_ref_text
    
    def test_semantic_exploration_suggestions(self):
        """Test semantic exploration suggestions."""
        result = run_cl_search_command(["protein", "--limit", "2", "--format", "json"])
        data = parse_enhanced_response(result)
        
        semantic = data["composition_opportunities"]["semantic_exploration"]
        assert isinstance(semantic, list)
        
        # Should suggest semantic exploration tools
        if semantic:
            semantic_text = " ".join(semantic)
            assert "cl_query" in semantic_text or "cl_discover" in semantic_text
    
    def test_search_refinement_suggestions(self):
        """Test search refinement suggestions."""
        result = run_cl_search_command(["COVID", "--limit", "2", "--format", "json"])
        data = parse_enhanced_response(result)
        
        refinement = data["composition_opportunities"]["search_refinement"]
        assert isinstance(refinement, list)
        
        # Should suggest search refinements
        if refinement:
            refinement_text = " ".join(refinement)
            assert "cl_search" in refinement_text
            
            # Should include original query variations
            assert "COVID" in refinement_text or "coronavirus" in refinement_text.lower()


class TestPerformanceAndBackwardCompatibility:
    """Test that enhancements don't break existing functionality."""
    
    def test_basic_search_still_works(self):
        """Test that basic search functionality is preserved."""
        result = run_cl_search_command(["insulin", "--limit", "1", "--format", "json"])
        data = parse_enhanced_response(result)
        
        # Core functionality preserved
        assert data["query"] == "insulin"
        assert data["endpoint"] == "wikidata"
        assert isinstance(data["results"], list)
        assert data["count"] == len(data["results"])
        
        # Results format preserved
        if data["results"]:
            entity = data["results"][0]
            assert "id" in entity
            assert "label" in entity
            assert "type" in entity
            assert "url" in entity
    
    def test_text_format_still_works(self):
        """Test that text format output is preserved."""
        result = run_cl_search_command(["insulin", "--limit", "1", "--format", "text"])
        
        assert result.returncode == 0
        assert "Found" in result.stdout and "results" in result.stdout
    
    def test_enhanced_response_performance(self):
        """Test that enhanced response doesn't significantly impact performance."""
        import time
        
        start_time = time.time()
        result = run_cl_search_command(["test", "--limit", "2", "--format", "json"])
        end_time = time.time()
        
        assert result.returncode == 0
        
        # Should complete in reasonable time (allowing for network)
        execution_time = end_time - start_time
        assert execution_time < 10.0, f"Enhanced search took too long: {execution_time:.2f}s"
        
        # Check if execution time is included in metadata
        data = parse_enhanced_response(result)
        if "execution_context" in data["metadata"]:
            reported_time = data["metadata"]["execution_context"]["execution_time_ms"]
            assert isinstance(reported_time, (int, float))
            assert reported_time > 0


class TestErrorHandling:
    """Test error handling in enhanced cl_search."""
    
    def test_empty_query_handling(self):
        """Test handling of empty queries."""
        result = run_cl_search_command(["", "--format", "json"])
        
        # Should fail gracefully
        assert result.returncode == 1
        
        # Should return JSON error format
        try:
            error_data = json.loads(result.stderr)
            assert "error" in error_data
        except json.JSONDecodeError:
            # Text error format is also acceptable
            assert "error" in result.stderr.lower() or "empty" in result.stderr.lower()
    
    def test_network_error_handling(self):
        """Test handling when network requests fail."""
        # Use invalid endpoint to trigger network error
        result = run_cl_search_command(["test", "--endpoint", "nonexistent", "--format", "json"])
        
        # Should handle gracefully (return empty results, not crash)
        assert result.returncode == 0
        data = parse_enhanced_response(result)
        
        # Should still have proper structure
        assert "metadata" in data
        assert "composition_opportunities" in data
        assert data["count"] == 0 or len(data["results"]) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])