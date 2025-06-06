"""Tests for LLM interpretation of materialization results.

This module tests whether an LLM can correctly interpret and reason about
materialized knowledge, including understanding inferred facts, reasoning chains,
and semantic relationships.
"""

from __future__ import annotations

import json
import tempfile
import pytest
from pathlib import Path
from click.testing import CliRunner

from cogitarelink.cli.cl_materialize import materialize


class TestLLMMaterializationInterpretation:
    """Test LLM's ability to interpret materialization results."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        
        # Sample biological entities for testing semantic interpretation
        self.protein_entities = [
            {
                "@type": "Protein",
                "@id": "https://www.uniprot.org/uniprot/P04637",
                "identifier": "P04637",
                "name": "Cellular tumor antigen p53",
                "organism": "Homo sapiens",
                "hasFunction": "tumor suppressor"
            },
            {
                "@type": "Protein", 
                "@id": "https://www.uniprot.org/uniprot/P53039",
                "identifier": "P53039",
                "name": "Spike glycoprotein",
                "organism": "SARS-CoV-2",
                "hasFunction": "viral attachment"
            }
        ]
        
        # SHACL rules that create interpretable inferences
        self.interpretable_shacl_rules = """
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix bio: <https://bioschemas.org/> .
@prefix ex: <http://example.org/> .

# Rule 1: Proteins from viruses are classified as viral proteins
ex:ViralProteinRule a sh:SPARQLRule ;
    rdfs:comment "Classify proteins from viral organisms as viral proteins" ;
    sh:construct '''
        CONSTRUCT {
            ?protein a bio:ViralProtein .
            ?protein bio:hasClassification "viral" .
            ?protein bio:inferredFrom "organism classification" .
        } WHERE {
            ?protein a bio:Protein .
            ?protein bio:organism ?organism .
            FILTER(CONTAINS(LCASE(STR(?organism)), "virus") || 
                   CONTAINS(LCASE(STR(?organism)), "sars") ||
                   CONTAINS(LCASE(STR(?organism)), "covid"))
        }
    ''' .

# Rule 2: Tumor suppressor proteins are cancer-related
ex:CancerProteinRule a sh:SPARQLRule ;
    rdfs:comment "Classify tumor suppressor proteins as cancer-related" ;
    sh:construct '''
        CONSTRUCT {
            ?protein a bio:CancerRelatedProtein .
            ?protein bio:hasRole "tumor suppression" .
            ?protein bio:clinicalRelevance "oncology" .
            ?protein bio:inferredFrom "functional classification" .
        } WHERE {
            ?protein a bio:Protein .
            ?protein bio:hasFunction ?function .
            FILTER(CONTAINS(LCASE(STR(?function)), "tumor") || 
                   CONTAINS(LCASE(STR(?function)), "suppressor"))
        }
    ''' .

# Rule 3: Cross-species functional similarity
ex:FunctionalSimilarityRule a sh:SPARQLRule ;
    rdfs:comment "Identify proteins with similar functions across species" ;
    sh:construct '''
        CONSTRUCT {
            ?protein1 bio:functionallyRelatedTo ?protein2 .
            ?protein1 bio:crossSpeciesRelation "functional similarity" .
            ?protein1 bio:inferredFrom "function comparison" .
        } WHERE {
            ?protein1 a bio:Protein .
            ?protein2 a bio:Protein .
            ?protein1 bio:hasFunction ?func1 .
            ?protein2 bio:hasFunction ?func2 .
            FILTER(?protein1 != ?protein2)
            FILTER(CONTAINS(LCASE(STR(?func1)), "suppressor") && 
                   CONTAINS(LCASE(STR(?func2)), "suppressor"))
        }
    ''' .
        """

    def test_llm_semantic_understanding_prompt_generation(self):
        """Test generation of LLM-interpretable materialization summaries."""
        
        entities_json = json.dumps(self.protein_entities)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ttl', delete=False) as f:
            f.write(self.interpretable_shacl_rules)
            shapes_file = f.name
        
        try:
            result = self.runner.invoke(materialize, [
                '--from-entities', entities_json,
                '--shapes-file', shapes_file,
                '--format', 'json',
                '--level', 'detailed'
            ])
            
            assert result.exit_code == 0
            response = json.loads(result.output)
            assert response["success"] is True
            
            # Check for LLM-interpretable guidance
            claude_guidance = response.get("claude_guidance", {})
            
            # Should provide semantic interpretation hints
            assert "materialization_summary" in claude_guidance
            assert "reasoning_scaffolds" in claude_guidance
            
            # Should explain what was inferred
            reasoning_scaffolds = claude_guidance["reasoning_scaffolds"]
            assert any("inferred" in scaffold.lower() for scaffold in reasoning_scaffolds)
            
            # Should provide next action guidance
            assert "next_actions" in claude_guidance
            next_actions = claude_guidance["next_actions"]
            assert len(next_actions) > 0
            
        finally:
            Path(shapes_file).unlink()

    def test_llm_reasoning_chain_interpretation(self):
        """Test LLM's ability to understand reasoning chains in materialization."""
        
        # Create test data that will trigger multiple inference rules
        test_entities = [
            {
                "@type": "Protein",
                "@id": "https://example.org/p53",
                "name": "p53 tumor suppressor",
                "organism": "Homo sapiens",
                "hasFunction": "tumor suppressor activity"
            },
            {
                "@type": "Protein",
                "@id": "https://example.org/spike",
                "name": "spike protein",
                "organism": "SARS-CoV-2 virus", 
                "hasFunction": "viral attachment"
            }
        ]
        
        entities_json = json.dumps(test_entities)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ttl', delete=False) as f:
            f.write(self.interpretable_shacl_rules)
            shapes_file = f.name
        
        try:
            result = self.runner.invoke(materialize, [
                '--from-entities', entities_json,
                '--shapes-file', shapes_file,
                '--include-provenance',
                '--format', 'json'
            ])
            
            assert result.exit_code == 0
            response = json.loads(result.output)
            
            # Verify reasoning patterns are provided for LLM interpretation
            suggestions = response.get("suggestions", {})
            reasoning_patterns = suggestions.get("reasoning_patterns", [])
            
            # Should contain biological reasoning patterns
            pattern_text = " ".join(reasoning_patterns).lower()
            biological_terms = ["protein", "function", "organism", "classification"]
            assert any(term in pattern_text for term in biological_terms)
            
            # Should provide workflow guidance
            workflow_guidance = suggestions.get("workflow_guidance", {})
            assert isinstance(workflow_guidance, dict)
            
        finally:
            Path(shapes_file).unlink()

    def test_llm_confidence_and_provenance_interpretation(self):
        """Test LLM's ability to interpret confidence levels and provenance."""
        
        entities_json = json.dumps(self.protein_entities)
        
        result = self.runner.invoke(materialize, [
            '--from-entities', entities_json,
            '--include-provenance',
            '--format', 'json'
        ])
        
        assert result.exit_code == 0
        response = json.loads(result.output)
        
        # Check metadata includes confidence information
        metadata = response.get("metadata", {})
        assert "confidence_score" in metadata
        
        # Should provide guidance on interpreting confidence
        claude_guidance = response.get("claude_guidance", {})
        assert "knowledge_quality" in claude_guidance
        
        # Should explain provenance tracking
        reasoning_scaffolds = claude_guidance.get("reasoning_scaffolds", [])
        provenance_mentions = [s for s in reasoning_scaffolds if "provenance" in s.lower()]
        assert len(provenance_mentions) > 0

    def test_llm_error_interpretation_and_recovery(self):
        """Test LLM's ability to interpret errors and suggest recovery."""
        
        # Test with invalid JSON to trigger error interpretation
        invalid_json = '{"invalid": json'
        
        result = self.runner.invoke(materialize, [
            '--from-entities', invalid_json,
            '--format', 'json'
        ])
        
        assert result.exit_code == 0  # Returns error response, doesn't exit
        response = json.loads(result.output)
        assert response["success"] is False
        
        # Check error includes LLM-interpretable recovery guidance
        error = response.get("error", {})
        assert "recovery_plan" in error
        
        recovery_plan = error["recovery_plan"]
        assert "next_tool" in recovery_plan
        assert "reasoning" in recovery_plan
        
        # Should provide actionable suggestions
        suggestions = error.get("suggestions", [])
        assert len(suggestions) > 0
        assert any("JSON" in suggestion for suggestion in suggestions)

    def test_llm_biological_domain_interpretation(self):
        """Test LLM's interpretation of biological domain-specific materialization."""
        
        # Biological entities with rich semantic context
        biological_entities = [
            {
                "@type": ["Protein", "BiologicalEntity"],
                "@id": "https://www.uniprot.org/uniprot/P04637",
                "identifier": "P04637",
                "name": "Tumor protein p53",
                "alternativeName": "Cellular tumor antigen p53",
                "organism": {
                    "@type": "Organism",
                    "name": "Homo sapiens",
                    "taxonomicId": "9606"
                },
                "molecularFunction": "DNA binding",
                "biologicalProcess": "cell cycle regulation",
                "cellularComponent": "nucleus",
                "diseaseAssociation": ["Li-Fraumeni syndrome", "cancer"]
            }
        ]
        
        entities_json = json.dumps(biological_entities)
        
        result = self.runner.invoke(materialize, [
            '--from-entities', entities_json,
            '--vocab', 'bioschemas', 'schema.org',
            '--format', 'json'
        ])
        
        assert result.exit_code == 0
        response = json.loads(result.output)
        
        # Check for biological domain intelligence
        claude_guidance = response.get("claude_guidance", {})
        memory_intelligence = claude_guidance.get("memory_intelligence", {})
        
        # Should provide biological query suggestions
        query_suggestions = memory_intelligence.get("query_suggestions", [])
        assert len(query_suggestions) > 0
        
        # Should recognize biological context
        reasoning_scaffolds = claude_guidance.get("reasoning_scaffolds", [])
        biological_context = any("biological" in scaffold.lower() or 
                                "protein" in scaffold.lower() or
                                "semantic" in scaffold.lower() 
                                for scaffold in reasoning_scaffolds)
        assert biological_context

    def test_llm_workflow_chaining_interpretation(self):
        """Test LLM's ability to interpret workflow chaining context."""
        
        entities_json = json.dumps(self.protein_entities)
        context_id = "test_workflow_ctx_123"
        
        result = self.runner.invoke(materialize, [
            '--from-entities', entities_json,
            '--context-id', context_id,
            '--format', 'json'
        ])
        
        assert result.exit_code == 0
        response = json.loads(result.output)
        
        # Should preserve context for workflow chaining
        assert response.get("context_id") == context_id
        
        # Should provide workflow guidance
        suggestions = response.get("suggestions", {})
        chaining_context = suggestions.get("chaining_context", {})
        
        assert "previous_context" in chaining_context
        assert "recommended_workflows" in chaining_context or "recommended_tool_sequence" in chaining_context
        
        # Should suggest logical next steps
        next_tools = suggestions.get("next_tools", [])
        tool_names = " ".join(next_tools).lower()
        expected_tools = ["validate", "explain", "query"]
        assert any(tool in tool_names for tool in expected_tools)


class TestLLMSemanticReasoningCapabilities:
    """Test LLM's semantic reasoning capabilities with materialized knowledge."""
    
    def test_llm_ontology_understanding_prompts(self):
        """Test generation of prompts that help LLMs understand ontological relationships."""
        
        runner = CliRunner()
        
        # Entities with clear ontological relationships
        ontological_entities = [
            {
                "@type": "Protein",
                "@id": "https://example.org/enzyme1",
                "name": "DNA polymerase",
                "molecularFunction": "DNA replication",
                "enzymeClass": "EC 2.7.7.7"
            },
            {
                "@type": "Protein",
                "@id": "https://example.org/enzyme2", 
                "name": "RNA polymerase",
                "molecularFunction": "RNA synthesis",
                "enzymeClass": "EC 2.7.7.6"
            }
        ]
        
        entities_json = json.dumps(ontological_entities)
        
        result = runner.invoke(materialize, [
            '--from-entities', entities_json,
            '--vocab', 'bioschemas',
            '--format', 'json',
            '--level', 'full'
        ])
        
        assert result.exit_code == 0
        response = json.loads(result.output)
        
        # Should provide ontological reasoning guidance
        claude_guidance = response.get("claude_guidance", {})
        reasoning_scaffolds = claude_guidance.get("reasoning_scaffolds", [])
        
        # Should mention semantic relationships
        semantic_terms = ["semantic", "ontology", "relationship", "classification"]
        scaffold_text = " ".join(reasoning_scaffolds).lower()
        assert any(term in scaffold_text for term in semantic_terms)

    def test_llm_cross_domain_reasoning_prompts(self):
        """Test prompts that enable cross-domain reasoning."""
        
        runner = CliRunner()
        
        # Cross-domain entities (biology + chemistry)
        cross_domain_entities = [
            {
                "@type": ["Protein", "ChemicalEntity"],
                "@id": "https://example.org/insulin",
                "name": "insulin",
                "biologicalRole": "hormone",
                "chemicalFormula": "C257H383N65O77S6",
                "therapeuticUse": "diabetes treatment"
            }
        ]
        
        entities_json = json.dumps(cross_domain_entities)
        
        result = runner.invoke(materialize, [
            '--from-entities', entities_json,
            '--vocab', 'bioschemas', 'schema.org',
            '--format', 'json'
        ])
        
        assert result.exit_code == 0
        response = json.loads(result.output)
        
        # Should recognize cross-domain nature
        claude_guidance = response.get("claude_guidance", {})
        next_actions = claude_guidance.get("next_actions", [])
        
        # Should suggest cross-domain analysis
        action_text = " ".join(next_actions).lower()
        cross_domain_indicators = ["relationship", "integration", "cross", "domain"]
        assert any(indicator in action_text for indicator in cross_domain_indicators)


def generate_llm_interpretation_test_suite() -> dict:
    """Generate a comprehensive test suite for LLM materialization interpretation.
    
    Returns a structured test suite that can be used to evaluate:
    1. Semantic understanding of materialized facts
    2. Reasoning chain interpretation 
    3. Confidence and provenance understanding
    4. Domain-specific knowledge interpretation
    5. Error interpretation and recovery
    """
    
    return {
        "test_suite_name": "LLM Materialization Interpretation",
        "version": "1.0",
        "description": "Evaluates LLM ability to interpret and reason about materialized knowledge",
        
        "test_categories": {
            "semantic_understanding": {
                "description": "Tests LLM's understanding of semantic relationships and inferences",
                "test_cases": [
                    {
                        "name": "protein_classification_inference",
                        "input_entities": "proteins with functional annotations",
                        "expected_interpretations": [
                            "recognize functional categories",
                            "understand protein classification",
                            "infer biological relevance"
                        ]
                    },
                    {
                        "name": "cross_species_relationships", 
                        "input_entities": "proteins from different organisms",
                        "expected_interpretations": [
                            "identify orthologous relationships",
                            "understand evolutionary connections",
                            "recognize functional conservation"
                        ]
                    }
                ]
            },
            
            "reasoning_chain_interpretation": {
                "description": "Tests LLM's ability to follow and explain reasoning chains",
                "test_cases": [
                    {
                        "name": "multi_step_inference",
                        "reasoning_steps": [
                            "protein has tumor suppressor function",
                            "tumor suppressors are cancer-related",
                            "therefore protein is cancer-related"
                        ],
                        "expected_understanding": "complete inference chain explanation"
                    }
                ]
            },
            
            "provenance_understanding": {
                "description": "Tests LLM's interpretation of evidence and confidence",
                "test_cases": [
                    {
                        "name": "confidence_assessment",
                        "materialized_facts": "facts with confidence scores",
                        "expected_behavior": "appropriately weight confidence in reasoning"
                    },
                    {
                        "name": "source_citation",
                        "materialized_facts": "facts with provenance trails",
                        "expected_behavior": "cite sources in explanations"
                    }
                ]
            },
            
            "domain_expertise": {
                "description": "Tests domain-specific interpretation capabilities",
                "domains": ["biology", "chemistry", "medicine", "informatics"],
                "test_cases": [
                    {
                        "name": "biological_pathway_reasoning",
                        "domain": "biology",
                        "expected_capabilities": [
                            "understand pathway relationships",
                            "recognize biological significance",
                            "suggest relevant follow-up queries"
                        ]
                    }
                ]
            },
            
            "error_interpretation": {
                "description": "Tests LLM's ability to understand and recover from errors",
                "test_cases": [
                    {
                        "name": "materialization_failure_recovery",
                        "error_scenarios": ["missing dependencies", "invalid input", "rule conflicts"],
                        "expected_recovery": "actionable suggestions for resolution"
                    }
                ]
            }
        },
        
        "evaluation_metrics": {
            "semantic_accuracy": "correctness of semantic interpretations", 
            "reasoning_completeness": "coverage of inference chains",
            "confidence_calibration": "appropriate confidence assessment",
            "domain_appropriateness": "domain-specific reasoning quality",
            "recovery_effectiveness": "quality of error recovery suggestions"
        },
        
        "llm_prompting_strategies": {
            "chain_of_thought": "step-by-step reasoning explanation",
            "semantic_scaffolding": "provide ontological context",
            "domain_priming": "activate domain-specific knowledge", 
            "confidence_calibration": "explicit uncertainty quantification",
            "error_analysis": "systematic error interpretation"
        }
    }


# Export the test suite for use by other modules
LLM_INTERPRETATION_TEST_SUITE = generate_llm_interpretation_test_suite()