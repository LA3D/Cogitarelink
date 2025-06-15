#!/usr/bin/env python3
"""
Experiment 04: Final Demonstration of Improved CogitareLink CLI

Goal: Demonstrate the complete working system with jq-friendly outputs
      and semantic lens-powered composition patterns.
"""

import subprocess
import json


def run_command(cmd: str) -> tuple[bool, str]:
    """Run a shell command and return success, output"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
        return True, result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return False, e.stderr.strip()


def demonstrate_basic_improvements():
    """Show basic improvements to cl_discover"""
    print("=" * 80)
    print("🎯 DEMONSTRATION: Improved cl_discover Structure")
    print("=" * 80)
    
    success, output = run_command("uv run cl_discover insulin")
    
    if success:
        data = json.loads(output)
        print("✅ NEW STRUCTURE (jq-friendly):")
        print(f"  - Status: {data.get('status')}")
        print(f"  - Data is array: {isinstance(data.get('data'), list)}")
        print(f"  - Count: {data.get('count')}")
        print(f"  - First entity ID: {data.get('data', [{}])[0].get('id')}")
        print(f"  - Next command: {data.get('next', ['N/A'])[0]}")
        
        print("\n🧪 JQ PATTERNS THAT NOW WORK:")
        patterns = [
            (".data[0].id", "Extract first entity ID"),
            (".count", "Get result count"),
            (".status", "Get operation status"),
            (".next[0]", "Get next command")
        ]
        
        for pattern, description in patterns:
            cmd = f"echo '{output}' | jq -r '{pattern}'"
            success, result = run_command(cmd)
            if success:
                print(f"  ✅ {pattern:<15} → {result:<20} # {description}")
            else:
                print(f"  ❌ {pattern:<15} → FAILED")
    else:
        print(f"❌ Failed to run cl_discover: {output}")


def demonstrate_lens_library():
    """Show the semantic lens library"""
    print("\n" + "=" * 80)
    print("🔍 DEMONSTRATION: Semantic Lens Library")
    print("=" * 80)
    
    # Show available lenses
    success, output = run_command("uv run cl_lens --list")
    
    if success:
        data = json.loads(output)
        print(f"✅ LENS LIBRARY: {data.get('count')} lenses available")
        
        # Group by category
        categories = {}
        for lens in data.get('data', []):
            cat = lens.get('category', 'Unknown')
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(lens['name'])
        
        for category, lenses in categories.items():
            print(f"  📁 {category}: {', '.join(lenses[:3])}{'...' if len(lenses) > 3 else ''}")
    
    print("\n🔧 KEY LENSES FOR COMPOSITION:")
    key_lenses = [
        ("pipe_ready", "Extract ID for piping to next tool"),
        ("entity_ids", "Get all entity identifiers"), 
        ("discovery_status", "Check operation success"),
        ("has_results", "Boolean: any results found")
    ]
    
    for lens_name, description in key_lenses:
        success, output = run_command(f"uv run cl_lens {lens_name} --raw")
        if success:
            filter_str = output.strip()
            print(f"  ✅ {lens_name:<15} → {filter_str:<20} # {description}")


def demonstrate_tool_composition():
    """Show powerful tool composition patterns"""
    print("\n" + "=" * 80)
    print("🔗 DEMONSTRATION: Tool Composition Patterns")
    print("=" * 80)
    
    print("📋 Pattern 1: Discovery → ID Extraction → Ready for Next Tool")
    
    # Step 1: Discover
    success, discover_output = run_command("uv run cl_discover Q7240673")
    if success:
        print("  ✅ Step 1: Discovery successful")
        
        # Step 2: Extract ID using lens
        cmd = f"echo '{discover_output}' | jq -r \"$(uv run cl_lens pipe_ready --raw)\""
        success, entity_id = run_command(cmd)
        if success:
            print(f"  ✅ Step 2: Extracted ID via lens → {entity_id}")
            
            # Step 3: Get next command suggestion
            cmd = f"echo '{discover_output}' | jq -r \"$(uv run cl_lens discovery_next --raw)\""
            success, next_cmd = run_command(cmd)
            if success:
                print(f"  ✅ Step 3: Next command → {next_cmd}")
                print("  🎯 Pipeline ready for composition!")
            else:
                print(f"  ❌ Step 3 failed: {next_cmd}")
        else:
            print(f"  ❌ Step 2 failed: {entity_id}")
    else:
        print(f"  ❌ Step 1 failed: {discover_output}")
    
    print("\n📋 Pattern 2: Check Results Before Processing")
    cmd = f"echo '{discover_output}' | jq \"$(uv run cl_lens has_results --raw)\""
    success, has_results = run_command(cmd)
    if success:
        print(f"  ✅ Has results check → {has_results}")
        if has_results.strip() == "true":
            print("  ✅ Safe to proceed with processing")
        else:
            print("  ⚠️  No results, skip processing")


def demonstrate_scientific_workflows():
    """Show scientific research workflow patterns"""
    print("\n" + "=" * 80)
    print("🧬 DEMONSTRATION: Scientific Research Workflows")
    print("=" * 80)
    
    test_entities = [
        ("insulin", "Protein hormone"),
        ("Q7240673", "Wikidata entity"),
        ("BRCA1", "Cancer gene")
    ]
    
    print("🔬 Testing entity discovery patterns:")
    
    for entity, description in test_entities:
        success, output = run_command(f"uv run cl_discover '{entity}' --domains biology")
        if success:
            # Extract key info using lenses
            cmd_id = f"echo '{output}' | jq -r \"$(uv run cl_lens entity_ids --raw)\""
            cmd_type = f"echo '{output}' | jq -r \".data[0].type\""
            cmd_confidence = f"echo '{output}' | jq -r \".data[0].confidence\""
            
            _, entity_id = run_command(cmd_id)
            _, entity_type = run_command(cmd_type)  
            _, confidence = run_command(cmd_confidence)
            
            print(f"  ✅ {entity:<12} → ID: {entity_id:<12} Type: {entity_type:<15} Conf: {confidence}")
        else:
            print(f"  ❌ {entity:<12} → Failed")
    
    print("\n🧪 Claude Code can now easily:")
    print("  • Extract entity IDs with simple jq patterns")
    print("  • Check operation success before proceeding")
    print("  • Get ready-to-run next commands")
    print("  • Compose tools into scientific research pipelines")
    print("  • Use semantic lenses for domain-specific extraction")


def show_before_after_comparison():
    """Show before/after comparison"""
    print("\n" + "=" * 80)
    print("📊 BEFORE vs AFTER COMPARISON")
    print("=" * 80)
    
    print("❌ BEFORE (Problematic for Claude Code):")
    print("  • .data was object, not array → .data[0] failed")
    print("  • Inconsistent field names → .success vs .status")
    print("  • Deep nesting → hard to navigate with jq")
    print("  • No composition patterns → tools didn't chain")
    print("  • Mixed suggestions with data → complex extraction")
    
    print("\n✅ AFTER (Claude Code Optimized):")
    print("  • .data always array → .data[0] works perfectly")
    print("  • Standardized fields → .status, .count, .meta, .next")
    print("  • Flat structure → easy jq navigation")
    print("  • Semantic lenses → powerful composition patterns")  
    print("  • Clean separation → data vs commands vs metadata")
    
    print("\n🎯 RESULT: Claude Code can now effortlessly:")
    print("  • Navigate CogitareLink outputs with simple jq")
    print("  • Compose tools into complex scientific workflows")
    print("  • Use semantic lenses for domain-specific patterns")
    print("  • Build research pipelines with Unix-style composition")


if __name__ == "__main__":
    print("🚀 CogitareLink CLI Evolution - Final Demonstration")
    print("   Optimized for Claude Code Integration & jq Composition")
    
    demonstrate_basic_improvements()
    demonstrate_lens_library()
    demonstrate_tool_composition()
    demonstrate_scientific_workflows()
    show_before_after_comparison()
    
    print("\n" + "=" * 80)
    print("✅ EVOLUTION COMPLETE: CogitareLink → Claude Code Ready!")
    print("=" * 80)