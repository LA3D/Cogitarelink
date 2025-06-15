"""Test cl_search integration with universal identifier discovery system.

Test-driven development for cl_search enhancement with universal cross-domain discovery,
replacing hard-coded assumptions with universal identifier patterns.
"""

import json
import subprocess
from pathlib import Path
from typing import Dict, Any
from unittest.mock import Mock, patch

import pytest

from cogitarelink.core.universal_identifier_discovery import (
    universal_identifier_discovery, IdentifierDomain
)
from cogitarelink.core.metadata_validation import metadata_validator


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


class TestUniversalDiscoveryIntegration:
    """Test integration with universal identifier discovery system."""
    
    def test_response_includes_universal_discovery_metadata(self):
        """Test that cl_search response includes universal discovery metadata."""
        result = run_cl_search_command(["insulin", "--limit", "2", "--format", "json"])
        data = parse_enhanced_response(result)
        
        # Should have enhanced metadata structure
        assert "metadata" in data
        metadata = data["metadata"]
        
        # Should include universal discovery analysis
        assert "universal_discovery" in metadata
        universal_discovery = metadata["universal_discovery"]
        
        # Universal discovery metadata structure
        assert "domains_detected" in universal_discovery
        assert "external_refs_by_domain" in universal_discovery
        assert "cross_domain_opportunities" in universal_discovery
        assert "validation_confidence" in universal_discovery
        
        # Domains detected should be valid domain names
        domains = universal_discovery["domains_detected"]
        assert isinstance(domains, list)
        valid_domains = [d.value for d in IdentifierDomain]
        for domain in domains:
            assert domain in valid_domains
    
    def test_cross_domain_composition_opportunities(self):
        """Test generation of cross-domain composition opportunities."""
        result = run_cl_search_command(["aspirin", "--limit", "2", "--format", "json"])
        data = parse_enhanced_response(result)
        
        comp_ops = data["composition_opportunities"]
        
        # Should include cross-domain pathways
        assert "cross_domain_pathways" in comp_ops
        cross_domain = comp_ops["cross_domain_pathways"]
        
        # Cross-domain pathways structure
        assert "primary_domain_workflow" in cross_domain
        assert "bridge_opportunities" in cross_domain
        assert "multi_domain_suggestions" in cross_domain
        
        # Bridge opportunities should suggest connections between domains
        bridges = cross_domain["bridge_opportunities"]
        assert isinstance(bridges, list)
        
        # Each bridge should have domain connections
        for bridge in bridges:
            assert "from_domain" in bridge
            assert "to_domain" in bridge
            assert "connection_type" in bridge
            assert "suggested_tools" in bridge
    
    def test_domain_specific_workflow_suggestions(self):
        """Test that domain-specific workflows are suggested based on discovered patterns."""
        result = run_cl_search_command(["spike protein", "--limit", "2", "--format", "json"])
        data = parse_enhanced_response(result)
        
        comp_ops = data["composition_opportunities"]
        
        # Should include domain-adaptive workflows
        assert "domain_adaptive_workflows" in comp_ops
        workflows = comp_ops["domain_adaptive_workflows"]
        
        # Should suggest appropriate workflows based on detected domains
        assert isinstance(workflows, dict)
        
        # For biological entities, should suggest biology workflow
        if "biology" in data["metadata"]["universal_discovery"]["domains_detected"]:
            assert "biology_workflow" in workflows
            bio_workflow = workflows["biology_workflow"]
            assert "suggested_tools" in bio_workflow
            assert "reasoning_pattern" in bio_workflow
            
            # Should suggest biological tools
            tools = bio_workflow["suggested_tools"]
            assert any("uniprot" in tool for tool in tools)
    
    def test_validation_aware_suggestions(self):
        """Test that suggestions are filtered by metadata validation system."""
        result = run_cl_search_command(["Mona Lisa", "--limit", "2", "--format", "json"])
        data = parse_enhanced_response(result)
        
        metadata = data["metadata"]
        
        # Should include validation results
        assert "validation_results" in metadata
        validation = metadata["validation_results"]
        
        # Validation structure
        assert "accessible_databases" in validation
        assert "confidence_scores" in validation
        assert "filtered_suggestions" in validation
        
        # Accessible databases should only include verified ones
        accessible = validation["accessible_databases"]
        assert isinstance(accessible, list)
        
        # Confidence scores should be realistic (0.0 to 1.0)
        confidence = validation["confidence_scores"]
        assert isinstance(confidence, dict)
        for db, score in confidence.items():
            assert 0.0 <= score <= 1.0
    
    def test_universal_external_identifier_discovery(self):
        """Test discovery of external identifiers across all domains."""
        result = run_cl_search_command(["Leonardo da Vinci", "--limit", "1", "--format", "json"])
        data = parse_enhanced_response(result)
        
        metadata = data["metadata"]
        universal_discovery = metadata["universal_discovery"]
        
        # Should discover external identifiers by domain
        external_refs = universal_discovery["external_refs_by_domain"]
        assert isinstance(external_refs, dict)
        
        # For Leonardo da Vinci, might expect cultural and bibliographic identifiers
        possible_domains = ["cultural", "bibliographic", "geographic"]
        
        # Should discover appropriate external reference patterns
        for domain, refs in external_refs.items():
            assert domain in [d.value for d in IdentifierDomain]
            assert isinstance(refs, list)
            
            # Refs should be valid property IDs
            for ref in refs:
                assert ref.startswith("P")
                assert ref[1:].isdigit()
    
    def test_format_validation_integration(self):
        """Test integration with identifier format validation."""
        result = run_cl_search_command(["insulin", "--limit", "1", "--format", "json"])
        data = parse_enhanced_response(result)
        
        comp_ops = data["composition_opportunities"]
        
        # Should include validated identifier suggestions
        assert "validated_identifiers" in comp_ops
        validated = comp_ops["validated_identifiers"]
        
        # Validated identifiers structure
        assert "valid_patterns" in validated
        assert "format_warnings" in validated
        assert "suggested_resolutions" in validated
        
        # Valid patterns should have format validation status
        valid_patterns = validated["valid_patterns"]
        assert isinstance(valid_patterns, dict)
        
        for prop_id, validation_info in valid_patterns.items():
            assert "format_valid" in validation_info
            assert "example_values" in validation_info
            assert "database_name" in validation_info
    
    def test_cross_reference_pathway_generation(self):
        """Test automatic generation of cross-reference pathways."""
        result = run_cl_search_command(["p53", "--limit", "1", "--format", "json"])  # Well-known protein
        data = parse_enhanced_response(result)
        
        comp_ops = data["composition_opportunities"]
        
        # Should include automatic pathway generation
        assert "automatic_pathways" in comp_ops
        pathways = comp_ops["automatic_pathways"]
        
        # Pathway structure
        assert "discovered_pathways" in pathways
        assert "confidence_scores" in pathways
        assert "validation_status" in pathways
        
        # Each pathway should have steps and confidence
        discovered = pathways["discovered_pathways"]
        assert isinstance(discovered, list)
        
        for pathway in discovered:
            assert "domain" in pathway
            assert "steps" in pathway
            assert "confidence" in pathway
            assert "databases_involved" in pathway
            
            # Steps should be actionable tool commands
            steps = pathway["steps"]
            assert isinstance(steps, list)
            for step in steps:
                assert any(tool in step for tool in ["cl_resolve", "cl_search", "cl_fetch"])
    
    def test_session_aware_domain_adaptation(self):
        """Test that domain detection adapts based on session context."""
        # Create temporary session file
        with patch('cogitarelink.cli.cl_search.get_session_context') as mock_session:
            mock_session.return_value = {
                "research_domain": "chemistry",
                "research_goal": "Drug discovery research",
                "entities_discovered_this_session": 5,
                "successful_patterns": ["search→fetch→resolve"]
            }
            
            result = run_cl_search_command(["aspirin", "--limit", "1", "--format", "json"])
            data = parse_enhanced_response(result)
            
            # Should adapt suggestions based on session domain
            comp_ops = data["composition_opportunities"]
            
            # Should prioritize chemistry-relevant suggestions
            domain_workflows = comp_ops.get("domain_adaptive_workflows", {})
            if "chemistry" in domain_workflows:
                chem_workflow = domain_workflows["chemistry"]
                suggested_tools = chem_workflow.get("suggested_tools", [])
                
                # Should suggest chemistry databases
                chemistry_dbs = ["cas", "pubchem", "chembl", "drugbank"]
                assert any(db in " ".join(suggested_tools) for db in chemistry_dbs)
    
    def test_unknown_pattern_discovery(self):
        """Test handling of unknown external identifier patterns."""
        # This tests the dynamic discovery capability
        result = run_cl_search_command(["test entity", "--limit", "1", "--format", "json"])
        data = parse_enhanced_response(result)
        
        metadata = data["metadata"]
        universal_discovery = metadata["universal_discovery"]
        
        # Should handle unknown patterns gracefully
        assert "unknown_patterns_discovered" in universal_discovery
        unknown = universal_discovery["unknown_patterns_discovered"]
        assert isinstance(unknown, list)
        
        # Each unknown pattern should have discovery metadata
        for pattern in unknown:
            assert "property_id" in pattern
            assert "discovered_dynamically" in pattern
            assert pattern["discovered_dynamically"] == True


class TestCrossDomainWorkflows:
    """Test cross-domain workflow generation and validation."""
    
    def test_biology_chemistry_bridge(self):
        """Test biology → chemistry bridge workflow generation."""
        result = run_cl_search_command(["hemoglobin", "--limit", "1", "--format", "json"])
        data = parse_enhanced_response(result)
        
        comp_ops = data["composition_opportunities"]
        cross_domain = comp_ops.get("cross_domain_pathways", {})
        
        # Should suggest biology → chemistry bridges
        bridges = cross_domain.get("bridge_opportunities", [])
        
        bio_to_chem = [b for b in bridges if b.get("from_domain") == "biology" and b.get("to_domain") == "chemistry"]
        
        if bio_to_chem:
            bridge = bio_to_chem[0]
            assert "connection_type" in bridge
            assert "protein" in bridge["connection_type"] or "drug" in bridge["connection_type"]
            
            # Should suggest relevant tools
            tools = bridge["suggested_tools"]
            assert any("inhibitor" in tool for tool in tools) or any("compound" in tool for tool in tools)
    
    def test_cultural_geographic_bridge(self):
        """Test cultural → geographic bridge workflow generation."""
        result = run_cl_search_command(["Starry Night", "--limit", "1", "--format", "json"])
        data = parse_enhanced_response(result)
        
        comp_ops = data["composition_opportunities"]
        cross_domain = comp_ops.get("cross_domain_pathways", {})
        
        # Should suggest cultural → geographic bridges
        bridges = cross_domain.get("bridge_opportunities", [])
        
        cultural_to_geo = [b for b in bridges if b.get("from_domain") == "cultural" and b.get("to_domain") == "geographic"]
        
        if cultural_to_geo:
            bridge = cultural_to_geo[0]
            assert "provenance" in bridge["connection_type"] or "location" in bridge["connection_type"]
    
    def test_universal_bibliographic_bridge(self):
        """Test universal → bibliographic bridge workflow generation."""
        result = run_cl_search_command(["Einstein", "--limit", "1", "--format", "json"])
        data = parse_enhanced_response(result)
        
        comp_ops = data["composition_opportunities"]
        cross_domain = comp_ops.get("cross_domain_pathways", {})
        
        # Should always suggest bibliographic connections
        bridges = cross_domain.get("bridge_opportunities", [])
        
        to_bibliographic = [b for b in bridges if b.get("to_domain") == "bibliographic"]
        
        # Should have at least one bridge to bibliographic domain
        assert len(to_bibliographic) > 0
        
        bib_bridge = to_bibliographic[0]
        assert "literature" in bib_bridge["connection_type"] or "research" in bib_bridge["connection_type"]


class TestBackwardCompatibility:
    """Test that enhanced cl_search maintains backward compatibility."""
    
    def test_text_format_unchanged(self):
        """Test that text format output remains unchanged."""
        result = run_cl_search_command(["insulin", "--format", "text"])
        
        # Should still work and return text format
        assert result.returncode == 0
        assert "insulin" in result.stdout.lower()
        
        # Should not be JSON
        with pytest.raises(json.JSONDecodeError):
            json.loads(result.stdout)
    
    def test_basic_json_structure_preserved(self):
        """Test that basic JSON structure is preserved."""
        result = run_cl_search_command(["insulin", "--format", "json"])
        data = parse_enhanced_response(result)
        
        # Original fields should still exist
        assert "query" in data
        assert "endpoint" in data  
        assert "results" in data
        assert "count" in data
        
        # Results should have original structure
        if data["results"]:
            result_item = data["results"][0]
            assert "id" in result_item
            assert "label" in result_item
            assert "description" in result_item
    
    def test_error_handling_preserved(self):
        """Test that error handling behavior is preserved."""
        # Test empty query
        result = run_cl_search_command(["", "--format", "json"])
        assert result.returncode != 0
        
        # Should return JSON error
        try:
            error_data = json.loads(result.stderr)
            assert "error" in error_data
        except json.JSONDecodeError:
            # Fallback - should at least mention error
            assert "error" in result.stderr.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])