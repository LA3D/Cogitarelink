"""Test Enhanced Entity implementation."""

from __future__ import annotations

import pytest
from cogitarelink.core.entity import Entity
from tests.conftest import assert_eq


@pytest.mark.unit
def test_minimum_viable_entity():
    """Test that we can create and use basic entities."""
    # Create simple entity
    entity = Entity(
        vocab=["bioschemas"],
        content={"name": "insulin", "@type": "Protein"}
    )
    
    # Test basic properties
    assert_eq(entity.vocab, ["bioschemas"])
    assert_eq(entity.content["name"], "insulin")
    assert_eq(entity.content["@type"], "Protein")
    
    # Test JSON-LD conversion
    json_ld = entity.to_dict()
    assert "@context" in json_ld
    assert "name" in json_ld["@context"]  # Should have proper context now
    assert_eq(json_ld["name"], "insulin")
    assert_eq(json_ld["@type"], "Protein")
    assert "@id" in json_ld  # Should have auto-generated ID
    

@pytest.mark.unit  
def test_entity_immutability():
    """Test that entity fields are immutable."""
    entity = Entity(
        vocab=["schema.org"], 
        content={"name": "test"}
    )
    
    # Should not be able to reassign fields (dataclass frozen=True)
    with pytest.raises(Exception):
        entity.vocab = ["new"]  # type: ignore
        
    with pytest.raises(Exception):
        entity.content = {"name": "modified"}  # type: ignore


@pytest.mark.unit
def test_sha256_signatures():
    """Test cryptographic signatures work correctly with URDNA2015 normalization."""
    # Use same ID to test content-based signature consistency
    test_id = "urn:test:insulin"
    
    entity1 = Entity(
        id=test_id,
        vocab=["bioschemas"],
        content={"name": "insulin", "@type": "Protein"}
    )
    
    entity2 = Entity(
        id=test_id,  # Same ID and content, different order
        vocab=["bioschemas"],
        content={"@type": "Protein", "name": "insulin"}
    )
    
    entity3 = Entity(
        id=test_id,  # Same ID, different content
        vocab=["bioschemas"],
        content={"name": "glucagon", "@type": "Protein"}
    )
    
    # Same content should have same signature (deterministic via URDNA2015)
    assert_eq(entity1.sha256, entity2.sha256)
    
    # Different content should have different signature
    assert entity1.sha256 != entity3.sha256
    
    # Signatures should be consistent across multiple calls
    assert_eq(entity1.sha256, entity1.sha256)


@pytest.mark.unit
def test_urdna2015_normalization():
    """Test that we use proper URDNA2015 normalization when pyld is available."""
    entity = Entity(
        vocab=["bioschemas"],
        content={"name": "test", "@type": "Protein"}
    )
    
    # Should have normalized property
    normalized = entity.normalized
    assert len(normalized) > 0
    
    # Should be consistent
    assert_eq(entity.normalized, entity.normalized)
    
    # Should be deterministic (same entity = same normalization)
    entity2 = Entity(
        vocab=["bioschemas"],
        content={"name": "test", "@type": "Protein"}
    )
    
    # Note: Different entities will have different UUIDs, so normalization will differ
    # But the normalization process itself should be consistent
    assert len(entity2.normalized) > 0


@pytest.mark.unit
def test_signature_caching():
    """Test that signatures are cached for performance."""
    entity = Entity(
        vocab=["test"],
        content={"name": "test"}
    )
    
    # First call
    sig1 = entity.sha256
    
    # Second call should be cached (same object)
    sig2 = entity.sha256
    
    assert_eq(sig1, sig2)
    # Note: We can't easily test caching performance without more complex setup


@pytest.mark.unit
def test_agent_response_structure():
    """Test structured responses for AI agents."""
    entity = Entity(
        vocab=["bioschemas", "schema.org"],
        content={"name": "insulin", "@type": "Protein", "identifier": "P01308"}
    )
    
    response = entity.to_agent_response()
    
    # Test response structure (wikidata-mcp pattern)
    assert response["success"] is True
    
    # Test data section
    assert "entity" in response["data"]
    assert "signature" in response["data"]
    assert "vocab" in response["data"]
    assert_eq(response["data"]["vocab"], ["bioschemas", "schema.org"])
    
    # Test metadata
    assert_eq(response["metadata"]["vocab_count"], 2)
    assert_eq(response["metadata"]["property_count"], 3)
    assert_eq(response["metadata"]["entity_type"], "Protein")
    assert response["metadata"]["has_signature"] is True
    
    # Test suggestions (enhanced with wikidata-mcp patterns)
    assert "next_tools" in response["suggestions"]
    assert "reasoning_patterns" in response["suggestions"]
    assert "workflow_guidance" in response["suggestions"]
    assert "cross_domain_opportunities" in response["suggestions"]
    
    # Test claude_guidance section (enhanced with intelligence patterns)
    assert "reasoning_hints" in response["claude_guidance"]
    assert "next_actions" in response["claude_guidance"]
    
    # Test that guidance is helpful  
    assert len(response["claude_guidance"]["reasoning_hints"]) > 0
    assert len(response["claude_guidance"]["next_actions"]) > 0


@pytest.mark.unit
def test_agent_response_guidance_quality():
    """Test that agent guidance is actually helpful."""
    entity = Entity(
        vocab=["bioschemas"],
        content={"name": "SARS-CoV-2", "@type": "Virus", "species": "Human"}
    )
    
    response = entity.to_agent_response()
    guidance = response["claude_guidance"]
    
    # Should mention entity type
    assert "Virus" in guidance["entity_summary"]
    
    # Should include key information in summary
    assert "Virus" in guidance["entity_summary"]
    assert len(guidance["reasoning_hints"]) > 0
    
    # Should give actionable next steps
    next_actions = guidance["next_actions"]
    assert len(next_actions) > 0
    assert any("discover" in action.lower() for action in next_actions)


@pytest.mark.unit
def test_reasoning_context_generation():
    """Test Chain-of-Thought reasoning scaffolds."""
    entity = Entity(
        vocab=["bioschemas"],
        content={"name": "insulin", "@type": "Protein", "identifier": "P01308"}
    )
    
    context = entity.generate_reasoning_context()
    
    # Test structure
    assert "reasoning_patterns" in context
    assert "workflow_suggestions" in context
    assert "biological_reasoning" in context
    assert "semantic_context" in context
    
    # Test content quality
    reasoning = context["reasoning_patterns"]
    assert any("Protein" in pattern for pattern in reasoning)
    assert len(reasoning) > 0
    
    # Test workflow suggestions
    workflow = context["workflow_suggestions"]
    assert len(workflow) > 0
    assert any("protein" in step.lower() for step in workflow)
    assert any("discover" in step.lower() for step in workflow)
    
    # Test biological reasoning (should be present for Protein)
    bio_reasoning = context["biological_reasoning"]
    assert len(bio_reasoning) > 0  # Should have biological reasoning for Protein
    assert any("biological" in reason for reason in bio_reasoning)
    
    # Test semantic context
    semantic = context["semantic_context"]
    assert semantic["vocabularies_used"] == ["bioschemas"]
    assert "name" in semantic["properties_available"]
    assert "entity_signature" in semantic
    assert semantic["reasoning_confidence"] in ["high", "medium", "low"]


@pytest.mark.unit
def test_biological_vs_non_biological_reasoning():
    """Test that biological entities get biological reasoning."""
    
    # Biological entity
    protein = Entity(
        vocab=["bioschemas"],
        content={"name": "insulin", "@type": "Protein"}
    )
    
    # Non-biological entity
    document = Entity(
        vocab=["schema.org"],
        content={"name": "research paper", "@type": "Document"}
    )
    
    protein_context = protein.generate_reasoning_context()
    document_context = document.generate_reasoning_context()
    
    # Protein should have biological reasoning
    assert len(protein_context["biological_reasoning"]) > 0
    
    # Document should not have biological reasoning
    assert len(document_context["biological_reasoning"]) == 0


if __name__ == "__main__":
    # Fast.ai style: run tests directly
    test_minimum_viable_entity()
    test_entity_immutability()
    test_sha256_signatures()
    test_signature_caching()
    test_agent_response_structure()
    test_agent_response_guidance_quality()
    test_reasoning_context_generation()
    test_biological_vs_non_biological_reasoning()
    print("✅ Iteration 4 tests passed!")