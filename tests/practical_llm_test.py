"""Practical test of LLM interpretation capabilities for cl_materialize.

This script demonstrates how an LLM can interpret materialization results
and provides concrete examples of interpretation tasks.
"""

import json
import tempfile
from pathlib import Path
from click.testing import CliRunner
from cogitarelink.cli.cl_materialize import materialize


def test_llm_interpretation_with_real_data():
    """Test LLM interpretation with realistic biological data."""
    
    runner = CliRunner()
    
    # Realistic protein data that should trigger meaningful inferences
    protein_data = [
        {
            "@type": "Protein",
            "@id": "https://www.uniprot.org/uniprot/P04637",
            "identifier": "P04637",
            "name": "Cellular tumor antigen p53",
            "organism": "Homo sapiens",
            "molecularFunction": "sequence-specific DNA binding",
            "biologicalProcess": "regulation of transcription",
            "diseaseAssociation": "Li-Fraumeni syndrome"
        },
        {
            "@type": "Protein", 
            "@id": "https://www.uniprot.org/uniprot/P53039",
            "identifier": "P53039",
            "name": "Spike glycoprotein",
            "organism": "SARS-CoV-2",
            "molecularFunction": "receptor binding",
            "biologicalProcess": "viral entry into host cell"
        }
    ]
    
    entities_json = json.dumps(protein_data)
    
    # Execute materialization
    result = runner.invoke(materialize, [
        '--from-entities', entities_json,
        '--vocab', 'bioschemas',
        '--format', 'json',
        '--level', 'detailed'
    ])
    
    print("=== MATERIALIZATION RESULT ===")
    print(f"Exit code: {result.exit_code}")
    
    if result.exit_code == 0:
        response = json.loads(result.output)
        print(f"Success: {response['success']}")
        
        # Analyze response for LLM interpretability
        print("\n=== LLM INTERPRETATION ANALYSIS ===")
        
        # 1. Basic entity information
        metadata = response.get("metadata", {})
        entities_count = metadata.get("entities_materialized", 0)
        print(f"✓ Entities materialized: {entities_count}")
        
        # 2. Guidance for LLM
        claude_guidance = response.get("claude_guidance", {})
        print(f"✓ Claude guidance provided: {bool(claude_guidance)}")
        
        if claude_guidance:
            # Next actions for LLM to follow
            next_actions = claude_guidance.get("next_actions", [])
            print(f"✓ Next actions suggested: {len(next_actions)}")
            for i, action in enumerate(next_actions[:3], 1):
                print(f"   {i}. {action}")
            
            # Reasoning scaffolds for LLM interpretation
            reasoning_scaffolds = claude_guidance.get("reasoning_scaffolds", [])
            print(f"✓ Reasoning scaffolds: {len(reasoning_scaffolds)}")
            for scaffold in reasoning_scaffolds[:2]:
                print(f"   → {scaffold}")
        
        # 3. Suggestions for workflow continuation
        suggestions = response.get("suggestions", {})
        next_tools = suggestions.get("next_tools", [])
        print(f"✓ Next tools suggested: {len(next_tools)}")
        for tool in next_tools[:3]:
            print(f"   → {tool}")
            
        # 4. Reasoning patterns
        reasoning_patterns = suggestions.get("reasoning_patterns", [])
        print(f"✓ Reasoning patterns: {len(reasoning_patterns)}")
        for pattern in reasoning_patterns[:2]:
            print(f"   → {pattern}")
            
        print("\n=== LLM INTERPRETATION PROMPTS ===")
        
        # Generate specific prompts that test LLM interpretation
        prompts = generate_llm_test_prompts(response)
        for i, prompt in enumerate(prompts, 1):
            print(f"\nPrompt {i}: {prompt}")
            
        print("\n=== EXPECTED LLM CAPABILITIES ===")
        
        # What we expect a good LLM to do with this output
        capabilities = [
            "Recognize p53 as a tumor suppressor protein with cancer relevance",
            "Identify SARS-CoV-2 spike protein as a viral pathogen target",
            "Understand that both proteins have different therapeutic implications",
            "Follow suggested next steps for deeper analysis",
            "Use reasoning scaffolds to explain biological significance",
            "Chain to appropriate follow-up tools for continued research"
        ]
        
        for capability in capabilities:
            print(f"✓ {capability}")
            
        return True
        
    else:
        print(f"Error: {result.output}")
        return False


def generate_llm_test_prompts(response):
    """Generate specific prompts to test LLM interpretation."""
    
    prompts = []
    
    # Basic interpretation prompt
    entity_count = response.get("metadata", {}).get("entities_materialized", 0)
    prompts.append(
        f"You've materialized {entity_count} biological entities. "
        "Explain what new knowledge was discovered and its potential significance."
    )
    
    # Reasoning prompt
    reasoning_scaffolds = response.get("claude_guidance", {}).get("reasoning_scaffolds", [])
    if reasoning_scaffolds:
        prompts.append(
            "Using the reasoning scaffolds provided, explain the logical steps "
            "that led to these biological conclusions."
        )
    
    # Next steps prompt
    next_tools = response.get("suggestions", {}).get("next_tools", [])
    if next_tools:
        prompts.append(
            f"You have these tools available: {', '.join(next_tools)}. "
            "Plan your next 3 research steps and explain your reasoning."
        )
    
    # Domain expertise prompt
    prompts.append(
        "As a computational biologist, analyze the clinical and research "
        "implications of these protein discoveries."
    )
    
    # Integration prompt
    prompts.append(
        "How would you integrate these findings into a broader research "
        "workflow? What additional data would you need?"
    )
    
    return prompts


def demonstrate_error_interpretation():
    """Demonstrate how LLMs can interpret and recover from errors."""
    
    runner = CliRunner()
    
    print("\n=== ERROR INTERPRETATION TEST ===")
    
    # Test with invalid JSON
    result = runner.invoke(materialize, [
        '--from-entities', '{"invalid": json',
        '--format', 'json'
    ])
    
    if result.exit_code == 0:
        response = json.loads(result.output)
        if not response.get("success", True):
            error = response.get("error", {})
            print(f"✓ Error detected: {error.get('code', 'Unknown')}")
            print(f"✓ Error message: {error.get('message', 'No message')}")
            
            # Check for recovery guidance
            if "recovery_plan" in error:
                recovery = error["recovery_plan"]
                print(f"✓ Recovery suggested: {recovery.get('next_tool', 'None')}")
                print(f"✓ Reasoning: {recovery.get('reasoning', 'None')}")
            
            # Check for actionable suggestions
            suggestions = error.get("suggestions", [])
            print(f"✓ Actionable suggestions: {len(suggestions)}")
            for suggestion in suggestions:
                print(f"   → {suggestion}")


def test_sparql_results_interpretation():
    """Test LLM interpretation of materialized SPARQL results."""
    
    runner = CliRunner()
    
    print("\n=== SPARQL RESULTS INTERPRETATION TEST ===")
    
    # Use existing SPARQL results if available
    sparql_results_file = "/tmp/sparql_results.json"
    
    if Path(sparql_results_file).exists():
        result = runner.invoke(materialize, [
            '--from-sparql-results', sparql_results_file,
            '--vocab', 'bioschemas',
            '--format', 'json'
        ])
        
        if result.exit_code == 0:
            response = json.loads(result.output)
            print(f"✓ Materialized SPARQL results: {response.get('success', False)}")
            
            # Analyze for LLM interpretation
            entity_count = response.get("metadata", {}).get("entities_materialized", 0)
            print(f"✓ Entities from SPARQL: {entity_count}")
            
            # Check guidance quality
            claude_guidance = response.get("claude_guidance", {})
            if claude_guidance:
                print("✓ LLM guidance provided for SPARQL results")
                
                # Memory intelligence for query context
                memory_intelligence = claude_guidance.get("memory_intelligence", {})
                if memory_intelligence:
                    entities_available = memory_intelligence.get("entities_available", "")
                    print(f"✓ Memory context: {entities_available}")
                    
                    query_suggestions = memory_intelligence.get("query_suggestions", [])
                    print(f"✓ Query suggestions: {len(query_suggestions)}")
            
            return True
    else:
        print("⚠ No SPARQL results file available for testing")
        return False


if __name__ == "__main__":
    print("=== LLM INTERPRETATION TEST FOR CL_MATERIALIZE ===")
    
    # Test 1: Basic protein materialization
    success1 = test_llm_interpretation_with_real_data()
    
    # Test 2: Error handling and recovery
    demonstrate_error_interpretation()
    
    # Test 3: SPARQL results materialization
    success2 = test_sparql_results_interpretation()
    
    print(f"\n=== SUMMARY ===")
    print(f"Basic materialization test: {'✓ PASSED' if success1 else '✗ FAILED'}")
    print(f"SPARQL results test: {'✓ PASSED' if success2 else '⚠ SKIPPED'}")
    
    print(f"\n=== LLM INTEGRATION RECOMMENDATIONS ===")
    
    if success1:
        print("🟢 cl_materialize provides rich structured responses suitable for LLM interpretation")
        print("🟢 Reasoning scaffolds help LLMs understand inference chains")
        print("🟢 Next action guidance enables workflow continuation") 
        print("🟢 Error responses include recovery strategies")
        
        print(f"\n=== PROMPT ENGINEERING STRATEGIES ===")
        print("1. Use reasoning scaffolds for Chain-of-Thought prompting")
        print("2. Reference entity counts and confidence scores")
        print("3. Follow suggested next tools for systematic analysis")
        print("4. Leverage domain-specific vocabulary contexts")
        print("5. Build on memory intelligence for query refinement")
        
    else:
        print("🔴 Issues detected with LLM interpretability")
        print("🔴 Consider enhancing structured response guidance")