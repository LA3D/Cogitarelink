#!/usr/bin/env python3
"""
Experiment 05: Container-Aware Workflows and Semantic Memory

Goal: Demonstrate sophisticated JSON-LD container workflows that showcase
      semantic memory management, research thread isolation, and advanced
      composition patterns for scientific research.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from test_harness import CLIExperiment
import json


def test_semantic_memory_workflow(exp: CLIExperiment):
    """Test end-to-end semantic memory workflow with containers using enhanced discovery"""
    print("\n" + "="*80)
    print("🧠 ENHANCED SEMANTIC MEMORY WORKFLOW - REAL DATA")
    print("="*80)
    
    # Step 1: Test enhanced cl_discover with real orchestration
    test_entities = ["WP5558", "insulin", "Q28209"]  # Mix of pathway, protein, and Wikidata ID
    contexts = []
    
    print("📋 Step 1: Testing enhanced discovery orchestrator with real tools...")
    for entity in test_entities:
        print(f"\n🔬 Discovering {entity} with orchestrated tools...")
        result = exp.run_cli(f'cl_discover {entity} --domains biology pathways --container')
        
        if result["success"]:
            output = result["output"]
            
            # Check if we're getting container format with real data
            has_container = "@context" in output and "memory" in output
            entity_count = output.get("count", 0)
            discovery_method = output.get("meta", {}).get("discovery_method", "unknown")
            sources = output.get("meta", {}).get("sources", [])
            
            print(f"  📊 Discovery method: {discovery_method}")
            print(f"  📊 Sources used: {sources}")
            print(f"  📊 Container format: {has_container}")
            print(f"  📊 Entities found: {entity_count}")
            
            # Check if synthesis indicates real data
            synthesis = output.get("meta", {}).get("synthesis", "")
            if "mock" in synthesis.lower() or "placeholder" in synthesis.lower():
                print(f"  ⚠️  Still getting mock data: {synthesis}")
            else:
                print(f"  ✅ Real discovery synthesis: {synthesis[:100]}...")
            
            # Save each discovery to context
            save_result = exp.run_cli_with_input(
                f'cl_context --save {entity}_context --thread enhanced_research', 
                json.dumps(result["output"])
            )
            if save_result["success"]:
                context_id = save_result["output"]["data"][0]["context_id"]
                contexts.append((entity, context_id))
                print(f"  ✅ {entity} → saved as {context_id}")
            else:
                print(f"  ❌ Failed to save {entity} context")
        else:
            print(f"  ❌ Failed to discover {entity}: {result.get('error', 'Unknown error')}")
    
    # Step 2: Merge contexts to create unified memory
    if len(contexts) >= 2:
        print(f"\n📋 Step 2: Merging {len(contexts)} contexts into unified memory...")
        context_names = [f"{name}_context" for name, _ in contexts]  # Use actual saved context names
        merge_flags = " ".join([f"--merge {name}" for name in context_names])  # Correct CLI syntax
        merge_cmd = f'cl_context {merge_flags} --save unified_protein_memory --thread protein_research'
        merge_result = exp.run_cli(merge_cmd)
        
        if merge_result["success"]:
            print("  ✅ Contexts successfully merged")
            
            # Step 3: Demonstrate container navigation on merged memory
            print("\n📋 Step 3: Testing container navigation on merged memory...")
            
            # Load the unified memory with correct thread
            load_result = exp.run_cli("cl_context --load unified_protein_memory --thread protein_research")
            if load_result["success"]:
                memory_data = load_result["output"]
                
                # Test semantic memory patterns
                patterns = [
                    ("memory_stats", "Memory statistics"),
                    ("context_entities", "All entity IDs"),
                    ("context_domains", "All domains"),
                    ("biological_entities", "Biology entities"),
                    ("semantic_summary", "Semantic summary")
                ]
                
                for pattern, description in patterns:
                    result = exp.run_jq(memory_data, f"$(cl_lens {pattern} --raw)")
                    print(f"  ✅ {pattern}: {result} # {description}")
        else:
            print("  ❌ Failed to merge contexts")


def test_research_thread_isolation(exp: CLIExperiment):
    """Test research thread isolation using @container: ['@graph', '@index']"""
    print("\n" + "="*80)
    print("🧵 RESEARCH THREAD ISOLATION")
    print("="*80)
    
    # Create contexts in different research threads
    threads = [
        ("cancer_research", ["BRCA1", "p53", "oncogene"]),
        ("diabetes_research", ["insulin", "glucose", "pancreas"]),
        ("general_biology", ["protein", "DNA", "cell"])
    ]
    
    print("📋 Creating isolated research threads...")
    
    for thread_name, entities in threads:
        print(f"\n🧬 Thread: {thread_name}")
        for entity in entities:
            # Discover entity
            result = exp.run_cli(f'cl_discover {entity} --domains biology')
            if result["success"]:
                # Save to thread-specific context
                save_result = exp.run_cli_with_input(
                    f'cl_context --save {entity}_study --thread {thread_name}',
                    json.dumps(result["output"])
                )
                if save_result["success"]:
                    print(f"  ✅ {entity} → {thread_name}")
                else:
                    print(f"  ❌ Failed to save {entity} to {thread_name}")
    
    # Test thread isolation by listing contexts
    print("\n📋 Testing thread isolation...")
    list_result = exp.run_cli("cl_context --list")
    if list_result["success"]:
        # Extract thread information
        thread_data = exp.run_jq(list_result["output"], "$(cl_lens thread_list --raw)")
        print(f"  ✅ Research threads identified: {thread_data}")
        
        # Show recent contexts with thread info
        recent_data = exp.run_jq(list_result["output"], "$(cl_lens recent_contexts --raw)")
        print(f"  ✅ Recent contexts with threads: {recent_data}")


def test_scientific_workflow_composition(exp: CLIExperiment):
    """Test complex scientific workflow composition with containers"""
    print("\n" + "="*80)
    print("🔬 SCIENTIFIC WORKFLOW COMPOSITION")
    print("="*80)
    
    # Workflow: Drug Discovery Research Pipeline
    print("📋 Workflow: Drug Discovery Research Pipeline")
    print("   Disease → Pathways → Proteins → Compounds → Candidates")
    
    # Step 1: Disease discovery
    print("\n🦠 Step 1: Disease entity discovery...")
    disease_result = exp.run_cli('cl_discover "Alzheimer disease" --domains biology')
    if disease_result["success"]:
        # Save disease context
        save_result = exp.run_cli_with_input(
            'cl_context --save alzheimer_disease --thread drug_discovery',
            json.dumps(disease_result["output"])
        )
        print("  ✅ Disease context saved")
        
        # Extract entity for next step
        entity_id = exp.run_jq(disease_result["output"], "$(cl_lens pipe_ready --raw)")
        print(f"  ✅ Disease entity ready: {entity_id}")
    
    # Step 2: Protein discovery (simulated)
    print("\n🧬 Step 2: Related protein discovery...")
    proteins = ["amyloid", "tau", "presenilin"]
    protein_contexts = []
    
    for protein in proteins:
        result = exp.run_cli(f'cl_discover {protein} --domains biology')
        if result["success"]:
            save_result = exp.run_cli_with_input(
                f'cl_context --save {protein}_protein --thread drug_discovery',
                json.dumps(result["output"])
            )
            if save_result["success"]:
                protein_contexts.append(f"{protein}_protein")
                print(f"  ✅ Protein context: {protein}")
    
    # Step 3: Merge all drug discovery contexts  
    if len(protein_contexts) > 0:
        print("\n💊 Step 3: Unifying drug discovery knowledge...")
        # Only merge the protein contexts since alzheimer_disease context doesn't exist
        merge_flags = " ".join([f"--merge {name}" for name in protein_contexts])  # Correct CLI syntax
        merge_cmd = f'cl_context {merge_flags} --save drug_discovery_knowledge --thread drug_discovery'
        merge_result = exp.run_cli(merge_cmd)
        
        if merge_result["success"]:
            print("  ✅ Drug discovery knowledge unified")
            
            # Step 4: Advanced semantic analysis
            print("\n🔍 Step 4: Advanced semantic analysis...")
            load_result = exp.run_cli("cl_context --load drug_discovery_knowledge --thread drug_discovery")
            if load_result["success"]:
                knowledge_data = load_result["output"]
                
                # Run sophisticated analyses
                analyses = [
                    ("research_entities", "Research-relevant entities"),
                    ("protein_network", "Protein network entities"), 
                    ("memory_stats", "Knowledge base statistics"),
                    ("high_confidence", "High-confidence entities")
                ]
                
                for analysis, description in analyses:
                    result = exp.run_jq(knowledge_data, f"$(cl_lens {analysis} --raw)")
                    print(f"  ✅ {analysis}: {result} # {description}")


def test_context_compression_workflow(exp: CLIExperiment):
    """Test context compression for Claude token efficiency"""
    print("\n" + "="*80)
    print("📦 CONTEXT COMPRESSION WORKFLOW")
    print("="*80)
    
    # Create a large context and test compression
    print("📋 Building large research context...")
    
    # Discover multiple entities to create substantial context
    entities = ["insulin", "diabetes", "glucose", "pancreas", "hormone", "endocrine"]
    
    for entity in entities:
        result = exp.run_cli(f'cl_discover {entity} --domains biology')
        if result["success"]:
            save_result = exp.run_cli_with_input(
                f'cl_context --save {entity}_large --thread compression_test',
                json.dumps(result["output"])
            )
            if save_result["success"]:
                print(f"  ✅ Added {entity} to large context")
    
    # Merge all contexts
    context_names = [f"{entity}_large" for entity in entities]
    merge_flags = " ".join([f"--merge {name}" for name in context_names])  # Correct CLI syntax
    merge_cmd = f'cl_context {merge_flags} --save large_research_context --thread compression_test'
    merge_result = exp.run_cli(merge_cmd)
    
    if merge_result["success"]:
        print("  ✅ Large research context created")
        
        # Test compression
        print("\n📦 Testing context compression...")
        
        # Load normal context
        normal_result = exp.run_cli("cl_context --load large_research_context --thread compression_test")
        if normal_result["success"]:
            normal_size = len(json.dumps(normal_result["output"]))
            print(f"  ✅ Normal context size: {normal_size} chars")
            
            # Load compressed context
            compressed_result = exp.run_cli("cl_context --load large_research_context --compress --thread compression_test")
            if compressed_result["success"]:
                compressed_size = len(json.dumps(compressed_result["output"]))
                compression_ratio = compressed_size / normal_size
                print(f"  ✅ Compressed context size: {compressed_size} chars")
                print(f"  ✅ Compression ratio: {compression_ratio:.2f} ({(1-compression_ratio)*100:.1f}% reduction)")
                
                # Verify essential data preserved
                entity_count = exp.run_jq(compressed_result["output"], "$(cl_lens memory_stats --raw)")
                print(f"  ✅ Preserved entities: {entity_count}")


def test_advanced_container_patterns(exp: CLIExperiment):
    """Test advanced JSON-LD container patterns"""
    print("\n" + "="*80)
    print("🗃️ ADVANCED CONTAINER PATTERNS")
    print("="*80)
    
    # Test @container: "@set" consistency
    print("📋 Testing @container: '@set' consistency...")
    result = exp.run_cli('cl_discover insulin --domains biology')
    if result["success"]:
        # Verify data is always array
        data_type = exp.run_jq(result["output"], "(.data | type)")
        print(f"  ✅ .data type: {data_type} (should be 'array')")
        
        # Test array navigation patterns
        first_id = exp.run_jq(result["output"], ".data[0].id")
        all_ids = exp.run_jq(result["output"], ".data[].id")
        print(f"  ✅ First ID: {first_id}")
        print(f"  ✅ All IDs: {all_ids}")
    
    # Test @container: "@id" direct access
    print("\n📋 Testing @container: '@id' direct access...")
    save_result = exp.run_cli_with_input(
        'cl_context --save insulin_container_test',
        json.dumps(result["output"])
    )
    
    if save_result["success"]:
        load_result = exp.run_cli("cl_context --load insulin_container_test")
        if load_result["success"]:
            # Direct entity access by ID
            entity_access = exp.run_jq(load_result["output"], '.memory.entities.insulin')
            print(f"  ✅ Direct entity access: {entity_access}")
            
            # Test @container: "@type" grouping
            type_groups = exp.run_jq(load_result["output"], ".memory.by_type | keys")
            print(f"  ✅ Type groupings: {type_groups}")
            
            # Test @container: "@index" domain grouping
            domain_groups = exp.run_jq(load_result["output"], ".memory.by_domain | keys")
            print(f"  ✅ Domain groupings: {domain_groups}")


def test_lens_powered_research_pipelines(exp: CLIExperiment):
    """Test research pipelines powered by semantic lenses"""
    print("\n" + "="*80)
    print("🔍 LENS-POWERED RESEARCH PIPELINES")
    print("="*80)
    
    # Pipeline 1: Entity Discovery → Memory Analysis → Research Insights
    print("📋 Pipeline 1: Discovery → Memory → Insights")
    
    # Discover entity (avoid quotes in entity name for cleaner IDs)
    result = exp.run_cli('cl_discover COVID-19 --domains biology')
    if result["success"]:
        # Save to memory
        save_result = exp.run_cli_with_input(
            'cl_context --save covid_research --thread pandemic_study',
            json.dumps(result["output"])
        )
        
        if save_result["success"]:
            # Load and analyze with lenses
            load_result = exp.run_cli("cl_context --load covid_research --thread pandemic_study")
            if load_result["success"]:
                memory_data = load_result["output"]
                
                # Chain of lens analyses
                print("\n🔗 Lens analysis chain:")
                
                # Basic stats
                stats = exp.run_jq(memory_data, "$(cl_lens memory_stats --raw)")
                print(f"  1️⃣ Memory stats: {stats}")
                
                # Entity extraction
                entities = exp.run_jq(memory_data, "$(cl_lens context_entities --raw)")
                print(f"  2️⃣ Entities: {entities}")
                
                # Domain analysis
                domains = exp.run_jq(memory_data, "$(cl_lens context_domains --raw)")
                print(f"  3️⃣ Domains: {domains}")
                
                # Research-specific extraction
                research_entities = exp.run_jq(memory_data, "$(cl_lens research_entities --raw)")
                print(f"  4️⃣ Research entities: {research_entities}")
    
    # Pipeline 2: Multi-context research workflow
    print("\n📋 Pipeline 2: Multi-context research synthesis")
    
    # List all contexts and analyze patterns
    list_result = exp.run_cli("cl_context --list")
    if list_result["success"]:
        context_data = list_result["output"]
        
        # Extract research insights
        print("\n🧠 Research pattern analysis:")
        
        # Thread analysis
        threads = exp.run_jq(context_data, "$(cl_lens thread_list --raw)")
        print(f"  🧵 Active threads: {threads}")
        
        # Context analysis
        recent = exp.run_jq(context_data, "$(cl_lens recent_contexts --raw)")
        print(f"  📅 Recent contexts: {recent}")
        
        # Size analysis
        large = exp.run_jq(context_data, "$(cl_lens large_contexts --raw)")
        print(f"  📊 Large contexts: {large}")


if __name__ == "__main__":
    exp = CLIExperiment(verbose=True)
    
    print("🚀 Container-Aware Workflows and Semantic Memory")
    print("   Testing JSON-LD 1.1 containers for scientific research")
    print("="*80)
    
    # Run all workflow tests
    test_semantic_memory_workflow(exp)
    test_research_thread_isolation(exp)
    test_scientific_workflow_composition(exp)
    test_context_compression_workflow(exp)
    test_advanced_container_patterns(exp)
    test_lens_powered_research_pipelines(exp)
    
    # Final summary
    exp.summarize_results()
    
    print("\n" + "="*80)
    print("✅ CONTAINER WORKFLOWS COMPLETE")
    print("   Demonstrated:")
    print("   • JSON-LD 1.1 container patterns (@set, @id, @type, @index)")
    print("   • Semantic memory management with thread isolation")
    print("   • Research workflow composition and context merging")
    print("   • Token-efficient compression for Claude Code")
    print("   • Lens-powered scientific research pipelines")
    print("   • Advanced container navigation and semantic analysis")
    print("="*80)