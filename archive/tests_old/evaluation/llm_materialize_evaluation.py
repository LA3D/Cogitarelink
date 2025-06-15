"""LLM Materialization Interpretation Evaluation Framework.

This module provides tools to evaluate how well LLMs can interpret and reason
about materialized knowledge from cl_materialize outputs.
"""

from __future__ import annotations

import json
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import tempfile

from click.testing import CliRunner
from cogitarelink.cli.cl_materialize import materialize


@dataclass
class LLMEvaluationResult:
    """Results of LLM interpretation evaluation."""
    test_name: str
    input_description: str
    materialization_response: Dict[str, Any]
    interpretation_quality: float  # 0.0 to 1.0
    semantic_understanding: float  # 0.0 to 1.0
    reasoning_chain_clarity: float  # 0.0 to 1.0
    domain_appropriateness: float  # 0.0 to 1.0
    actionability: float  # 0.0 to 1.0
    interpretation_prompts: List[str]
    expected_llm_outputs: List[str]
    evaluation_notes: str


class LLMMaterializationEvaluator:
    """Evaluates LLM interpretation capabilities for materialization results."""
    
    def __init__(self):
        """Initialize the evaluator."""
        self.runner = CliRunner()
        self.evaluation_results: List[LLMEvaluationResult] = []
    
    def create_biological_test_scenario(self) -> Tuple[str, Dict[str, Any]]:
        """Create a biological test scenario for LLM interpretation."""
        
        # Complex biological entities that should trigger meaningful inferences
        entities = [
            {
                "@type": "Protein",
                "@id": "https://www.uniprot.org/uniprot/P04637",
                "identifier": "P04637", 
                "name": "Cellular tumor antigen p53",
                "alternativeName": "Tumor suppressor p53",
                "organism": "Homo sapiens",
                "molecularFunction": "sequence-specific DNA binding",
                "biologicalProcess": ["cell cycle checkpoint", "apoptotic process"],
                "cellularComponent": "nucleus",
                "diseaseAssociation": ["Li-Fraumeni syndrome", "various cancers"],
                "proteinFamily": "p53 family",
                "functionalDomain": ["DNA-binding domain", "transactivation domain"]
            },
            {
                "@type": "Protein",
                "@id": "https://www.uniprot.org/uniprot/P53039", 
                "identifier": "P53039",
                "name": "Spike glycoprotein",
                "organism": "SARS-CoV-2",
                "molecularFunction": "receptor binding",
                "biologicalProcess": "viral entry into host cell",
                "cellularComponent": "viral envelope",
                "pathogenicity": "high",
                "targetReceptor": "ACE2"
            },
            {
                "@type": "Protein",
                "@id": "https://www.uniprot.org/uniprot/P69905",
                "identifier": "P69905",
                "name": "Hemoglobin subunit alpha",
                "organism": "Homo sapiens", 
                "molecularFunction": "oxygen binding",
                "biologicalProcess": "oxygen transport",
                "cellularComponent": "hemoglobin complex",
                "quaternaryStructure": "alpha2-beta2 tetramer"
            }
        ]
        
        # SHACL rules for biological inference
        rules = """
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix bio: <https://bioschemas.org/> .
@prefix ex: <http://example.org/> .

# Rule 1: Classify viral proteins
ex:ViralClassification a sh:SPARQLRule ;
    rdfs:comment "Classify proteins from viral organisms" ;
    sh:construct '''
        CONSTRUCT {
            ?protein a bio:ViralProtein .
            ?protein bio:pathogenicity ?pathogenicity .
            ?protein bio:hostInteraction "required" .
            ?protein bio:therapeuticTarget "true" .
        } WHERE {
            ?protein a bio:Protein .
            ?protein bio:organism ?organism .
            OPTIONAL { ?protein bio:pathogenicity ?pathogenicity }
            FILTER(CONTAINS(LCASE(STR(?organism)), "virus") || 
                   CONTAINS(LCASE(STR(?organism)), "sars") ||
                   CONTAINS(LCASE(STR(?organism)), "covid"))
        }
    ''' .

# Rule 2: Tumor suppressor classification
ex:TumorSuppressorClassification a sh:SPARQLRule ;
    rdfs:comment "Classify tumor suppressor proteins" ;
    sh:construct '''
        CONSTRUCT {
            ?protein a bio:TumorSuppressor .
            ?protein bio:oncologyRelevance "high" .
            ?protein bio:therapeuticImplication "cancer treatment" .
            ?protein bio:regulatoryRole "cell cycle control" .
        } WHERE {
            ?protein a bio:Protein .
            ?protein bio:name ?name .
            FILTER(CONTAINS(LCASE(STR(?name)), "tumor") && 
                   CONTAINS(LCASE(STR(?name)), "suppressor"))
        }
    ''' .

# Rule 3: Oxygen transport proteins
ex:OxygenTransportClassification a sh:SPARQLRule ;
    rdfs:comment "Classify oxygen transport proteins" ;
    sh:construct '''
        CONSTRUCT {
            ?protein a bio:OxygenCarrier .
            ?protein bio:physiologicalRole "respiratory function" .
            ?protein bio:clinicalRelevance "anemia, oxygen disorders" .
            ?protein bio:structuralImportance "quaternary structure critical" .
        } WHERE {
            ?protein a bio:Protein .
            ?protein bio:molecularFunction ?function .
            FILTER(CONTAINS(LCASE(STR(?function)), "oxygen"))
        }
    ''' .

# Rule 4: Cross-protein functional analysis
ex:FunctionalClustering a sh:SPARQLRule ;
    rdfs:comment "Group proteins by functional similarity" ;
    sh:construct '''
        CONSTRUCT {
            ?protein1 bio:functionallyRelatedTo ?protein2 .
            ?protein1 bio:functionalCluster ?cluster .
        } WHERE {
            ?protein1 a bio:Protein .
            ?protein2 a bio:Protein .
            ?protein1 bio:organism ?org1 .
            ?protein2 bio:organism ?org2 .
            FILTER(?protein1 != ?protein2)
            FILTER(STR(?org1) = STR(?org2))  # Same organism
        }
    ''' .
        """
        
        return json.dumps(entities), {"rules": rules, "description": "Multi-protein biological analysis"}
    
    def evaluate_materialization_response_for_llm(
        self, 
        response: Dict[str, Any], 
        test_context: Dict[str, Any]
    ) -> LLMEvaluationResult:
        """Evaluate how well a materialization response supports LLM interpretation."""
        
        # Analyze response structure for LLM-friendliness
        interpretation_quality = self._assess_interpretation_quality(response)
        semantic_understanding = self._assess_semantic_clarity(response)
        reasoning_chain_clarity = self._assess_reasoning_chains(response)
        domain_appropriateness = self._assess_domain_intelligence(response)
        actionability = self._assess_actionable_guidance(response)
        
        # Generate interpretation prompts that an LLM could use
        interpretation_prompts = self._generate_interpretation_prompts(response)
        
        # Define expected LLM outputs
        expected_outputs = self._define_expected_llm_outputs(response, test_context)
        
        return LLMEvaluationResult(
            test_name="biological_protein_analysis",
            input_description=test_context.get("description", ""),
            materialization_response=response,
            interpretation_quality=interpretation_quality,
            semantic_understanding=semantic_understanding, 
            reasoning_chain_clarity=reasoning_chain_clarity,
            domain_appropriateness=domain_appropriateness,
            actionability=actionability,
            interpretation_prompts=interpretation_prompts,
            expected_llm_outputs=expected_outputs,
            evaluation_notes=self._generate_evaluation_notes(response)
        )
    
    def _assess_interpretation_quality(self, response: Dict[str, Any]) -> float:
        """Assess overall interpretation quality for LLMs."""
        score = 0.0
        
        # Check for structured guidance
        if "claude_guidance" in response:
            score += 0.3
            
        # Check for reasoning scaffolds
        claude_guidance = response.get("claude_guidance", {})
        if "reasoning_scaffolds" in claude_guidance:
            scaffolds = claude_guidance["reasoning_scaffolds"]
            if len(scaffolds) >= 3:
                score += 0.2
                
        # Check for next actions
        if "next_actions" in claude_guidance:
            actions = claude_guidance["next_actions"]
            if len(actions) >= 2:
                score += 0.2
                
        # Check for suggestions
        if "suggestions" in response:
            suggestions = response["suggestions"]
            if "reasoning_patterns" in suggestions:
                score += 0.15
            if "next_tools" in suggestions:
                score += 0.15
                
        return min(score, 1.0)
    
    def _assess_semantic_clarity(self, response: Dict[str, Any]) -> float:
        """Assess semantic clarity for LLM understanding."""
        score = 0.0
        
        # Check metadata clarity
        metadata = response.get("metadata", {})
        if "entities_materialized" in metadata:
            score += 0.2
        if "new_triples_count" in metadata:
            score += 0.2
            
        # Check data structure clarity
        data = response.get("data", {})
        if "entity_count" in data:
            score += 0.2
            
        # Check for confidence information
        if "confidence_score" in metadata:
            score += 0.2
            
        # Check for provenance indicators
        claude_guidance = response.get("claude_guidance", {})
        memory_intelligence = claude_guidance.get("memory_intelligence", {})
        if "knowledge_depth" in memory_intelligence:
            score += 0.2
            
        return min(score, 1.0)
    
    def _assess_reasoning_chains(self, response: Dict[str, Any]) -> float:
        """Assess clarity of reasoning chains."""
        score = 0.0
        
        # Check for reasoning patterns
        suggestions = response.get("suggestions", {})
        reasoning_patterns = suggestions.get("reasoning_patterns", [])
        
        if reasoning_patterns:
            score += 0.4
            
            # Check for biological reasoning indicators
            pattern_text = " ".join(reasoning_patterns).lower()
            biological_indicators = ["protein", "function", "organism", "biological", "molecular"]
            if any(indicator in pattern_text for indicator in biological_indicators):
                score += 0.3
                
        # Check for workflow guidance
        workflow_guidance = suggestions.get("workflow_guidance", {})
        if workflow_guidance:
            score += 0.3
            
        return min(score, 1.0)
    
    def _assess_domain_intelligence(self, response: Dict[str, Any]) -> float:
        """Assess domain-specific intelligence."""
        score = 0.0
        
        claude_guidance = response.get("claude_guidance", {})
        
        # Check for domain-specific memory intelligence
        memory_intelligence = claude_guidance.get("memory_intelligence", {})
        query_suggestions = memory_intelligence.get("query_suggestions", [])
        
        if query_suggestions:
            score += 0.4
            
            # Check for biological domain awareness
            suggestions_text = " ".join(query_suggestions).lower()
            domain_terms = ["protein", "biological", "molecular", "cellular", "functional"]
            if any(term in suggestions_text for term in domain_terms):
                score += 0.3
                
        # Check for domain-appropriate next actions
        next_actions = claude_guidance.get("next_actions", [])
        if next_actions:
            actions_text = " ".join(next_actions).lower()
            if any(term in actions_text for term in ["validate", "explore", "analyze"]):
                score += 0.3
                
        return min(score, 1.0)
    
    def _assess_actionable_guidance(self, response: Dict[str, Any]) -> float:
        """Assess actionability of guidance for LLMs."""
        score = 0.0
        
        # Check for specific next tools
        suggestions = response.get("suggestions", {})
        next_tools = suggestions.get("next_tools", [])
        
        if next_tools and len(next_tools) >= 2:
            score += 0.4
            
        # Check for context chaining
        if "chaining_context" in suggestions:
            score += 0.3
            
        # Check for specific workflow recommendations
        workflow_guidance = suggestions.get("workflow_guidance", {})
        if "validation_steps" in workflow_guidance:
            score += 0.3
            
        return min(score, 1.0)
    
    def _generate_interpretation_prompts(self, response: Dict[str, Any]) -> List[str]:
        """Generate prompts that test LLM interpretation capabilities."""
        
        prompts = []
        
        # Basic interpretation prompt
        entity_count = response.get("metadata", {}).get("entities_materialized", 0)
        prompts.append(
            f"Given that {entity_count} entities were materialized, explain what new "
            "biological knowledge was discovered and its potential significance."
        )
        
        # Reasoning chain prompt
        reasoning_scaffolds = response.get("claude_guidance", {}).get("reasoning_scaffolds", [])
        if reasoning_scaffolds:
            prompts.append(
                "Based on the reasoning scaffolds provided, trace the logical steps "
                "that led to the materialized conclusions about these proteins."
            )
            
        # Domain expertise prompt
        memory_intelligence = response.get("claude_guidance", {}).get("memory_intelligence", {})
        if memory_intelligence:
            prompts.append(
                "Using your biological expertise, evaluate the clinical and research "
                "implications of the materialized protein relationships."
            )
            
        # Workflow planning prompt
        next_tools = response.get("suggestions", {}).get("next_tools", [])
        if next_tools:
            prompts.append(
                f"Plan the next 3 research steps using the suggested tools: {', '.join(next_tools)}. "
                "Explain your reasoning for each step."
            )
            
        return prompts
    
    def _define_expected_llm_outputs(
        self, 
        response: Dict[str, Any], 
        test_context: Dict[str, Any]
    ) -> List[str]:
        """Define what outputs we expect from a well-functioning LLM."""
        
        expected = []
        
        # Should recognize protein types and functions
        expected.append(
            "Identify that p53 is a tumor suppressor with cancer relevance"
        )
        expected.append(
            "Recognize spike protein as viral with therapeutic target potential"
        )
        expected.append(
            "Understand hemoglobin's role in oxygen transport"
        )
        
        # Should understand inference chains
        expected.append(
            "Explain how functional annotations lead to therapeutic classifications"
        )
        
        # Should suggest appropriate follow-ups
        expected.append(
            "Recommend validation of materialized relationships"
        )
        expected.append(
            "Suggest querying for related proteins or pathways"
        )
        
        # Should demonstrate domain knowledge
        expected.append(
            "Connect protein functions to broader biological processes"
        )
        expected.append(
            "Recognize clinical or research implications"
        )
        
        return expected
    
    def _generate_evaluation_notes(self, response: Dict[str, Any]) -> str:
        """Generate evaluation notes about LLM interpretability."""
        
        notes = []
        
        # Analyze guidance quality
        claude_guidance = response.get("claude_guidance", {})
        if claude_guidance:
            notes.append("✓ Provides structured Claude guidance")
        else:
            notes.append("⚠ Missing Claude-specific guidance")
            
        # Analyze reasoning support
        reasoning_scaffolds = claude_guidance.get("reasoning_scaffolds", [])
        if len(reasoning_scaffolds) >= 3:
            notes.append("✓ Rich reasoning scaffolds provided")
        else:
            notes.append("⚠ Limited reasoning scaffolds")
            
        # Analyze actionability
        next_tools = response.get("suggestions", {}).get("next_tools", [])
        if len(next_tools) >= 2:
            notes.append("✓ Clear next steps provided")
        else:
            notes.append("⚠ Limited actionable guidance")
            
        # Analyze domain intelligence
        memory_intelligence = claude_guidance.get("memory_intelligence", {})
        if memory_intelligence:
            notes.append("✓ Domain-specific intelligence included")
        else:
            notes.append("⚠ Generic responses, lacks domain specificity")
            
        return " | ".join(notes)
    
    async def run_comprehensive_evaluation(self) -> Dict[str, Any]:
        """Run comprehensive LLM interpretation evaluation."""
        
        print("Running LLM Materialization Interpretation Evaluation...")
        
        # Test 1: Biological protein analysis
        entities_json, test_context = self.create_biological_test_scenario()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ttl', delete=False) as f:
            f.write(test_context["rules"])
            shapes_file = f.name
        
        try:
            result = self.runner.invoke(materialize, [
                '--from-entities', entities_json,
                '--shapes-file', shapes_file,
                '--include-provenance',
                '--format', 'json',
                '--level', 'detailed'
            ])
            
            if result.exit_code == 0:
                response = json.loads(result.output)
                evaluation = self.evaluate_materialization_response_for_llm(response, test_context)
                self.evaluation_results.append(evaluation)
                
        finally:
            Path(shapes_file).unlink()
        
        # Generate summary report
        return self._generate_evaluation_report()
    
    def _generate_evaluation_report(self) -> Dict[str, Any]:
        """Generate comprehensive evaluation report."""
        
        if not self.evaluation_results:
            return {"error": "No evaluation results available"}
        
        # Calculate average scores
        avg_interpretation = sum(r.interpretation_quality for r in self.evaluation_results) / len(self.evaluation_results)
        avg_semantic = sum(r.semantic_understanding for r in self.evaluation_results) / len(self.evaluation_results)
        avg_reasoning = sum(r.reasoning_chain_clarity for r in self.evaluation_results) / len(self.evaluation_results)
        avg_domain = sum(r.domain_appropriateness for r in self.evaluation_results) / len(self.evaluation_results)
        avg_actionability = sum(r.actionability for r in self.evaluation_results) / len(self.evaluation_results)
        
        overall_score = (avg_interpretation + avg_semantic + avg_reasoning + avg_domain + avg_actionability) / 5
        
        return {
            "evaluation_summary": {
                "total_tests": len(self.evaluation_results),
                "overall_llm_interpretability_score": round(overall_score, 3),
                "component_scores": {
                    "interpretation_quality": round(avg_interpretation, 3),
                    "semantic_understanding": round(avg_semantic, 3), 
                    "reasoning_chain_clarity": round(avg_reasoning, 3),
                    "domain_appropriateness": round(avg_domain, 3),
                    "actionability": round(avg_actionability, 3)
                }
            },
            "llm_readiness_assessment": {
                "ready_for_production": overall_score >= 0.7,
                "strengths": self._identify_strengths(),
                "improvement_areas": self._identify_improvements(),
                "recommended_llm_prompting_strategies": self._recommend_prompting_strategies()
            },
            "test_results": [
                {
                    "test_name": r.test_name,
                    "scores": {
                        "interpretation_quality": r.interpretation_quality,
                        "semantic_understanding": r.semantic_understanding,
                        "reasoning_chain_clarity": r.reasoning_chain_clarity,
                        "domain_appropriateness": r.domain_appropriateness,
                        "actionability": r.actionability
                    },
                    "interpretation_prompts": r.interpretation_prompts[:2],  # First 2 prompts
                    "evaluation_notes": r.evaluation_notes
                }
                for r in self.evaluation_results
            ]
        }
    
    def _identify_strengths(self) -> List[str]:
        """Identify strengths in LLM interpretability."""
        strengths = []
        
        avg_scores = {
            "interpretation": sum(r.interpretation_quality for r in self.evaluation_results) / len(self.evaluation_results),
            "semantic": sum(r.semantic_understanding for r in self.evaluation_results) / len(self.evaluation_results),
            "reasoning": sum(r.reasoning_chain_clarity for r in self.evaluation_results) / len(self.evaluation_results),
            "domain": sum(r.domain_appropriateness for r in self.evaluation_results) / len(self.evaluation_results),
            "actionability": sum(r.actionability for r in self.evaluation_results) / len(self.evaluation_results)
        }
        
        for category, score in avg_scores.items():
            if score >= 0.8:
                strengths.append(f"Excellent {category} support for LLM interpretation")
            elif score >= 0.7:
                strengths.append(f"Good {category} support for LLM interpretation")
                
        return strengths
    
    def _identify_improvements(self) -> List[str]:
        """Identify areas for improvement."""
        improvements = []
        
        avg_scores = {
            "interpretation": sum(r.interpretation_quality for r in self.evaluation_results) / len(self.evaluation_results),
            "semantic": sum(r.semantic_understanding for r in self.evaluation_results) / len(self.evaluation_results), 
            "reasoning": sum(r.reasoning_chain_clarity for r in self.evaluation_results) / len(self.evaluation_results),
            "domain": sum(r.domain_appropriateness for r in self.evaluation_results) / len(self.evaluation_results),
            "actionability": sum(r.actionability for r in self.evaluation_results) / len(self.evaluation_results)
        }
        
        for category, score in avg_scores.items():
            if score < 0.6:
                improvements.append(f"Enhance {category} guidance for better LLM interpretation")
                
        return improvements
    
    def _recommend_prompting_strategies(self) -> List[str]:
        """Recommend LLM prompting strategies based on evaluation."""
        strategies = []
        
        # Always recommend these core strategies
        strategies.extend([
            "Use Chain-of-Thought prompting to leverage reasoning scaffolds",
            "Prime with domain context using provided memory intelligence",
            "Reference confidence scores when making claims", 
            "Follow suggested workflow sequences for systematic analysis"
        ])
        
        # Add specific recommendations based on scores
        avg_reasoning = sum(r.reasoning_chain_clarity for r in self.evaluation_results) / len(self.evaluation_results)
        if avg_reasoning >= 0.8:
            strategies.append("Leverage rich reasoning chains for complex multi-step inference")
            
        avg_domain = sum(r.domain_appropriateness for r in self.evaluation_results) / len(self.evaluation_results)
        if avg_domain >= 0.7:
            strategies.append("Use domain-specific query suggestions for targeted follow-up")
            
        return strategies


# Example usage and testing
if __name__ == "__main__":
    async def main():
        evaluator = LLMMaterializationEvaluator()
        report = await evaluator.run_comprehensive_evaluation()
        
        print("=== LLM Materialization Interpretation Evaluation Report ===")
        print(json.dumps(report, indent=2))
        
        # Practical recommendations
        print("\n=== Practical LLM Integration Recommendations ===")
        
        overall_score = report["evaluation_summary"]["overall_llm_interpretability_score"]
        if overall_score >= 0.8:
            print("🟢 EXCELLENT: Materialization outputs are highly LLM-interpretable")
        elif overall_score >= 0.7:
            print("🟡 GOOD: Materialization outputs support LLM interpretation well")
        elif overall_score >= 0.6:
            print("🟠 FAIR: Materialization outputs need improvement for LLM use")
        else:
            print("🔴 POOR: Significant improvements needed for LLM interpretability")
            
        print(f"Overall LLM Interpretability Score: {overall_score:.3f}")
    
    asyncio.run(main())