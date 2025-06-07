"""Tool-specific discovery patterns for semantic web exploration.

Provides practical guidance for follow-your-nose patterns, external identifier
prioritization, and Wikidata navigation strategies based on actual tool usage.
"""

from __future__ import annotations

from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass

# External identifier priorities and follow patterns
EXTERNAL_ID_PATTERNS = {
    # Biological/Life Sciences
    "P352": {  # UniProt protein ID
        "name": "UniProt",
        "domain": "proteins",
        "priority": "high",
        "follow_pattern": "sequence → structure → pathways → diseases",
        "next_tools": ["cl_resolve P352 {id}", "cl_sparql for protein interactions"],
        "discovery_hint": "🧬 UniProt → Follow for protein sequences, domains, and functional annotations"
    },
    "P638": {  # PDB structure ID
        "name": "PDB",
        "domain": "structures", 
        "priority": "high",
        "follow_pattern": "structure → binding sites → drug targets",
        "next_tools": ["cl_resolve P638 {id}", "structural analysis"],
        "discovery_hint": "🔬 PDB → Follow for 3D structures, binding sites, and conformational data"
    },
    "P486": {  # MeSH ID
        "name": "MeSH",
        "domain": "medical",
        "priority": "medium",
        "follow_pattern": "medical concepts → clinical trials → treatments",
        "next_tools": ["cl_resolve P486 {id}", "medical literature search"],
        "discovery_hint": "🏥 MeSH → Follow for medical terminology and clinical classifications"
    },
    "P699": {  # Disease Ontology ID
        "name": "Disease Ontology",
        "domain": "diseases",
        "priority": "medium", 
        "follow_pattern": "disease → symptoms → biomarkers → treatments",
        "next_tools": ["cl_resolve P699 {id}", "disease mechanism queries"],
        "discovery_hint": "🦠 Disease Ontology → Follow for disease classifications and relationships"
    },
    "P686": {  # Gene Ontology ID
        "name": "Gene Ontology",
        "domain": "functions",
        "priority": "high",
        "follow_pattern": "function → processes → cellular components",
        "next_tools": ["cl_resolve P686 {id}", "functional annotation queries"],
        "discovery_hint": "📊 Gene Ontology → Follow for biological processes and molecular functions"
    },
    "P683": {  # ChEBI ID  
        "name": "ChEBI",
        "domain": "chemistry",
        "priority": "medium",
        "follow_pattern": "chemical → reactions → pathways → targets",
        "next_tools": ["cl_resolve P683 {id}", "chemical interaction queries"],
        "discovery_hint": "⚗️ ChEBI → Follow for chemical entities and biochemical reactions"
    },
    "P2888": {  # OBO/ontology URI
        "name": "OBO/Ontology",
        "domain": "ontologies",
        "priority": "medium",
        "follow_pattern": "concept → hierarchy → related terms",
        "next_tools": ["ontology browsing", "concept hierarchy exploration"],
        "discovery_hint": "🌳 OBO → Follow for ontological relationships and concept hierarchies"
    }
}

# Wikidata property navigation patterns
WIKIDATA_PROPERTY_PATTERNS = {
    "P31": {  # instance of
        "name": "instance of", 
        "navigation_hint": "📋 Instance of → Explore entity classification and type hierarchy",
        "sparql_pattern": "SELECT ?type WHERE { wd:{entity} wdt:P31 ?type }",
        "discovery_strategy": "Follow classification chain to understand entity context"
    },
    "P279": {  # subclass of
        "name": "subclass of",
        "navigation_hint": "🌳 Subclass of → Navigate concept taxonomy and parent classes", 
        "sparql_pattern": "SELECT ?parent WHERE { wd:{entity} wdt:P279 ?parent }",
        "discovery_strategy": "Follow upward in taxonomy to find broader concepts"
    },
    "P361": {  # part of
        "name": "part of",
        "navigation_hint": "🧩 Part of → Explore containing systems, structures, or processes",
        "sparql_pattern": "SELECT ?container WHERE { wd:{entity} wdt:P361 ?container }",
        "discovery_strategy": "Follow containment relationships to understand context"
    },
    "P527": {  # has part
        "name": "has part", 
        "navigation_hint": "🔧 Has part → Explore components, subunits, or constituents",
        "sparql_pattern": "SELECT ?part WHERE { wd:{entity} wdt:P527 ?part }",
        "discovery_strategy": "Follow downward to understand internal structure"
    },
    "P2781": {  # has pathway
        "name": "has pathway",
        "navigation_hint": "🛤️ Has pathway → Explore biological pathways and processes",
        "sparql_pattern": "SELECT ?pathway WHERE { wd:{entity} wdt:P2781 ?pathway }",
        "discovery_strategy": "Follow to understand biological mechanisms"
    }
}

# Search result interpretation patterns
SEARCH_RESULT_PATTERNS = {
    "no_results": {
        "hints": [
            "🔍 Try broader terms (spike protein → protein)",
            "📝 Check spelling or try alternative names/synonyms", 
            "🌳 Search for parent concepts first, then narrow down",
            "🔄 Use scientific names vs common names",
            "🏷️ Try different languages or transliterations"
        ],
        "strategies": [
            "Start with general concepts and navigate downward",
            "Use Wikipedia to find Wikidata entity IDs",
            "Try related terms from the same domain"
        ]
    },
    "too_many_results": {
        "hints": [
            "🎯 Add specific qualifiers (SARS-CoV-2 spike protein)",
            "🧬 Include species, organism, or taxonomic names",
            "📊 Filter by instance type (P31) in follow-up queries",
            "🏷️ Use more specific terminology",
            "⏰ Add temporal qualifiers if relevant"
        ],
        "strategies": [
            "Use SPARQL filters to narrow results",
            "Sort by relevance indicators",
            "Focus on most recent or authoritative entities"
        ]
    },
    "mixed_quality": {
        "hints": [
            "✅ Prioritize entities with rich property sets",
            "🔗 Look for entities with multiple external identifiers",
            "📊 Check for instance type classifications",
            "🌐 Prefer entities with multiple language versions"
        ],
        "strategies": [
            "Compare entity completeness before deep exploration",
            "Cross-validate findings across multiple entities"
        ]
    }
}

# SPARQL query strategy patterns
SPARQL_STRATEGY_PATTERNS = {
    "empty_results": {
        "debugging_hints": [
            "🔍 Try broader property searches: ?item ?property ?value",
            "🏷️ Add language tags for labels: rdfs:label 'term'@en",
            "🔗 Use wdt: for direct properties, not full property paths",
            "📊 Check if entity exists: ASK { wd:{entity} ?p ?o }",
            "🌐 Try alternative property patterns"
        ],
        "recovery_strategies": [
            "Start with DESCRIBE queries to see available properties",
            "Use entity exploration before complex queries",
            "Verify entity IDs are correct"
        ]
    },
    "complex_queries": {
        "optimization_hints": [
            "📊 Start simple, add complexity incrementally",
            "⚡ Use LIMIT to prevent timeouts and test patterns",
            "🎯 Filter by instance types (P31) early to reduce scope",
            "🔧 Use OPTIONAL for non-essential properties",
            "📈 Profile query performance with different patterns"
        ],
        "development_strategy": [
            "Build queries step by step",
            "Test each clause independently", 
            "Use subqueries for complex logic"
        ]
    },
    "performance_issues": {
        "optimization_hints": [
            "⚡ Add LIMIT clauses to large result sets",
            "🎯 Use specific property paths instead of ?p ?o patterns", 
            "📊 Filter early in the query, not at the end",
            "🔧 Avoid OPTIONAL on large datasets",
            "⏱️ Use timeouts and pagination for large queries"
        ]
    }
}

def add_search_guidance(response: Dict[str, Any], results_count: int, query: str) -> None:
    """Add search-specific discovery guidance based on result patterns."""
    
    guidance_hints = []
    
    if results_count == 0:
        guidance_hints.extend(SEARCH_RESULT_PATTERNS["no_results"]["hints"])
        response["discovery_strategy"] = "broad_to_narrow"
        response["next_approach"] = "Try broader concepts or alternative terminology"
        
    elif results_count > 50:
        guidance_hints.extend(SEARCH_RESULT_PATTERNS["too_many_results"]["hints"])
        response["discovery_strategy"] = "narrow_and_filter"
        response["next_approach"] = "Add specificity or use SPARQL filters"
        
    elif 1 <= results_count <= 5:
        guidance_hints.extend([
            "✅ Good result count - explore entities in detail",
            "🔍 Use cl_wikidata entity to examine promising candidates",
            "🔗 Check for external identifiers to follow"
        ])
        response["discovery_strategy"] = "deep_exploration"
        response["next_approach"] = "Examine entity details and follow cross-references"
    
    response["discovery_hints"] = guidance_hints[:4]  # Limit to most relevant

def add_entity_navigation_guidance(response: Dict[str, Any], properties: Dict[str, Any]) -> None:
    """Add entity-specific navigation guidance based on available properties."""
    
    # Extract external identifiers
    external_ids = extract_external_identifiers(properties)
    follow_hints = []
    
    for prop_id, values in external_ids.items():
        if prop_id in EXTERNAL_ID_PATTERNS:
            pattern = EXTERNAL_ID_PATTERNS[prop_id]
            follow_hints.append({
                "property": prop_id,
                "name": pattern["name"],
                "hint": pattern["discovery_hint"],
                "priority": pattern["priority"],
                "next_tools": [tool.format(id=values[0]) if values else tool for tool in pattern["next_tools"]]
            })
    
    # Sort by priority 
    follow_hints.sort(key=lambda x: {"high": 0, "medium": 1, "low": 2}[x["priority"]])
    response["follow_your_nose"] = follow_hints[:5]  # Top 5 priorities
    
    # Add semantic relationship navigation
    semantic_nav = []
    for prop_id in ["P31", "P279", "P361", "P527"]:
        if prop_id in properties:
            pattern = WIKIDATA_PROPERTY_PATTERNS[prop_id]
            semantic_nav.append({
                "property": prop_id,
                "hint": pattern["navigation_hint"],
                "sparql_pattern": pattern["sparql_pattern"],
                "strategy": pattern["discovery_strategy"]
            })
    
    response["semantic_navigation"] = semantic_nav

def add_sparql_strategy_guidance(response: Dict[str, Any], results_count: int, query_complexity: float) -> None:
    """Add SPARQL-specific strategy guidance based on query results and complexity."""
    
    strategy_hints = []
    
    if results_count == 0:
        strategy_hints.extend(SPARQL_STRATEGY_PATTERNS["empty_results"]["debugging_hints"])
        response["sparql_strategy"] = "debugging"
        response["recovery_approach"] = SPARQL_STRATEGY_PATTERNS["empty_results"]["recovery_strategies"]
        
    elif query_complexity > 0.5:  # Complex query
        strategy_hints.extend(SPARQL_STRATEGY_PATTERNS["complex_queries"]["optimization_hints"])
        response["sparql_strategy"] = "optimization"
        response["development_approach"] = SPARQL_STRATEGY_PATTERNS["complex_queries"]["development_strategy"]
        
    elif results_count > 1000:  # Performance issues
        strategy_hints.extend(SPARQL_STRATEGY_PATTERNS["performance_issues"]["optimization_hints"])
        response["sparql_strategy"] = "performance_optimization"
    
    response["sparql_hints"] = strategy_hints[:4]

def add_crosswalk_prioritization(response: Dict[str, Any], external_ids: Dict[str, List[str]], domain: str = "biological") -> None:
    """Add cross-reference prioritization guidance based on domain and identifier types."""
    
    prioritized_crosswalks = []
    
    # Domain-specific prioritization
    if domain == "biological":
        priority_order = ["P352", "P638", "P686", "P699", "P486", "P683"]  # UniProt, PDB, GO, Disease Ontology, MeSH, ChEBI
    elif domain == "medical":
        priority_order = ["P486", "P699", "P352", "P2892"]  # MeSH, Disease Ontology, UniProt, UMLS
    else:
        priority_order = list(EXTERNAL_ID_PATTERNS.keys())
    
    for prop_id in priority_order:
        if prop_id in external_ids and prop_id in EXTERNAL_ID_PATTERNS:
            pattern = EXTERNAL_ID_PATTERNS[prop_id]
            prioritized_crosswalks.append({
                "property": prop_id,
                "identifiers": external_ids[prop_id][:3],  # Limit to first 3
                "priority": pattern["priority"],
                "follow_pattern": pattern["follow_pattern"],
                "discovery_hint": pattern["discovery_hint"]
            })
    
    response["crosswalk_prioritization"] = prioritized_crosswalks[:5]  # Top 5
    
    # Add domain-specific workflow guidance
    if domain == "biological":
        response["biological_workflow"] = [
            "1. 🧬 Start with UniProt (P352) for sequence and functional data",
            "2. 🔬 Follow PDB (P638) for structural information",
            "3. 📊 Explore Gene Ontology (P686) for functional classification",
            "4. 🛤️ Investigate biological pathways and interactions",
            "5. 🦠 Connect to disease associations if relevant"
        ]

def extract_external_identifiers(properties: Dict[str, Any]) -> Dict[str, List[str]]:
    """Extract external identifier properties and their values."""
    
    external_ids = {}
    
    for prop_id, values in properties.items():
        if prop_id in EXTERNAL_ID_PATTERNS:
            # Extract actual values from Wikidata claim structure
            if isinstance(values, list):
                external_ids[prop_id] = [
                    v.get("value", v) if isinstance(v, dict) else str(v) 
                    for v in values[:5]  # Limit to first 5 values
                ]
            else:
                external_ids[prop_id] = [str(values)]
    
    return external_ids

def generate_discovery_reflection(
    tool_sequence: List[str], 
    confidence_progression: List[float],
    final_entities_found: int
) -> Dict[str, Any]:
    """Generate reflection on discovery process effectiveness."""
    
    reflection = {
        "process_analysis": {
            "total_steps": len(tool_sequence),
            "confidence_improvement": confidence_progression[-1] - confidence_progression[0] if confidence_progression else 0,
            "entities_discovered": final_entities_found,
            "tool_diversity": len(set(tool_sequence))
        },
        "effectiveness_patterns": [],
        "improvement_suggestions": []
    }
    
    # Analyze tool effectiveness patterns
    if "cl_wikidata search" in tool_sequence and "cl_wikidata entity" in tool_sequence:
        reflection["effectiveness_patterns"].append("✅ Good search-to-detail exploration pattern")
    
    if "cl_resolve" in " ".join(tool_sequence):
        reflection["effectiveness_patterns"].append("✅ Effective cross-reference following")
    else:
        reflection["improvement_suggestions"].append("🔗 Consider using cl_resolve to follow external identifiers")
    
    if len(set(tool_sequence)) < 3:
        reflection["improvement_suggestions"].append("🔄 Try more diverse tool combinations for comprehensive coverage")
    
    # Confidence analysis
    if confidence_progression:
        if confidence_progression[-1] < 0.6:
            reflection["improvement_suggestions"].append("📊 Low final confidence - seek additional validation sources")
        elif max(confidence_progression) - min(confidence_progression) < 0.2:
            reflection["improvement_suggestions"].append("🎯 Flat confidence curve - try different discovery strategies")
    
    return reflection