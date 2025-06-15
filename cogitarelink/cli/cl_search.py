"""cl_search: Simple entity search following Claude Code patterns.

Minimal tool for entity discovery - fast, simple, composable.
"""

from __future__ import annotations

import json
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Optional, List, Dict, Any

import click

from ..discovery.base import discovery_engine
from ..core.debug import get_logger
from ..core.universal_identifier_discovery import universal_identifier_discovery
from ..core.metadata_validation import metadata_validator

log = get_logger("cl_search")


def sample_entity_properties(entity_id: str, endpoint: str = "wikidata") -> Dict[str, Any]:
    """Sample key properties from an entity for metadata analysis."""
    if endpoint != "wikidata":
        return {"external_refs": [], "types": []}
        
    try:
        import httpx
        
        # Quick SPARQL query to get P31 (instance of) and external identifiers
        sparql_query = f"""
        SELECT ?prop ?value WHERE {{
            wd:{entity_id} ?prop ?value .
            FILTER(?prop IN (wdt:P31, wdt:P352, wdt:P594, wdt:P638, wdt:P705, wdt:P486))
        }} LIMIT 20
        """
        
        result = discovery_engine.query_endpoint("wikidata", sparql_query)
        
        external_refs = []
        types = []
        
        if result.get("success"):
            for binding in result.get("results", []):
                prop_uri = binding.get("prop", {}).get("value", "")
                value = binding.get("value", {}).get("value", "")
                
                prop_id = prop_uri.split("/")[-1] if prop_uri else ""
                
                if prop_id == "P31":  # instance of
                    type_id = value.split("/")[-1] if value else ""
                    if type_id:
                        types.append(type_id)
                elif prop_id in ["P352", "P594", "P638", "P705", "P486"]:  # external refs
                    external_refs.append(prop_id)
        
        return {"external_refs": external_refs, "types": types}
        
    except Exception as e:
        log.debug(f"Property sampling failed for {entity_id}: {e}")
        return {"external_refs": [], "types": []}


def generate_universal_discovery_metadata(results: List[Dict[str, Any]], endpoint: str = "wikidata") -> Dict[str, Any]:
    """Generate universal discovery metadata using the comprehensive identifier discovery system."""
    if not results or endpoint != "wikidata":
        return {
            "domains_detected": [],
            "external_refs_by_domain": {},
            "cross_domain_opportunities": [],
            "validation_confidence": 0.0,
            "unknown_patterns_discovered": []
        }
    
    # Analyze top results with universal discovery
    all_domains = set()
    external_refs_by_domain = {}
    cross_domain_opportunities = []
    validation_confidences = []
    
    # Sample first few results to avoid too many API calls
    sample_size = min(2, len(results))
    for result in results[:sample_size]:
        entity_id = result.get("id", "")
        if not entity_id:
            continue
            
        try:
            # Use universal identifier discovery
            discovery_result = universal_identifier_discovery.discover_all_external_identifiers(entity_id, endpoint)
            
            # Collect domains
            domains_covered = discovery_result.get("domains_covered", [])
            all_domains.update(domains_covered)
            
            # Organize external refs by domain
            discovered_identifiers = discovery_result.get("discovered_identifiers", {})
            for prop_id, identifier_info in discovered_identifiers.items():
                pattern = identifier_info.get("pattern", {})
                domain = pattern.get("domain", "general")
                
                if domain not in external_refs_by_domain:
                    external_refs_by_domain[domain] = []
                external_refs_by_domain[domain].append(prop_id)
            
            # Generate cross-domain opportunities
            pathway_result = universal_identifier_discovery.discover_cross_reference_pathways(entity_id)
            if pathway_result.get("multi_domain_coverage"):
                pathways = pathway_result.get("pathways", {})
                for pathway_name, pathway_info in pathways.items():
                    cross_domain_opportunities.extend(
                        pathway_info.get("cross_reference_opportunities", [])
                    )
            
            # Basic validation confidence (simplified for now)
            validation_confidences.append(0.8)  # Default confidence
            
        except Exception as e:
            log.debug(f"Universal discovery failed for {entity_id}: {e}")
            continue
    
    # Calculate overall confidence
    overall_confidence = sum(validation_confidences) / len(validation_confidences) if validation_confidences else 0.0
    
    return {
        "domains_detected": list(all_domains),
        "external_refs_by_domain": external_refs_by_domain,
        "cross_domain_opportunities": cross_domain_opportunities[:5],  # Limit to top 5
        "validation_confidence": overall_confidence,
        "unknown_patterns_discovered": []  # Placeholder for dynamic discovery
    }


def analyze_search_results(results: List[Dict[str, Any]], endpoint: str = "wikidata") -> Dict[str, Any]:
    """Analyze search results to extract rich metadata."""
    if not results:
        return {
            "entity_types_found": [],
            "type_distribution": {},
            "external_refs_available": {},
            "semantic_depth_indicators": {
                "has_type_hierarchy": False,
                "max_hierarchy_depth": 0,
                "relationship_density": 0.0
            }
        }
    
    # Sample properties from top results for analysis
    all_types = []
    all_external_refs = []
    
    # Sample first few results to avoid too many API calls
    sample_size = min(3, len(results))
    for result in results[:sample_size]:
        entity_id = result.get("id", "")
        if entity_id and endpoint == "wikidata":
            props = sample_entity_properties(entity_id, endpoint)
            all_types.extend(props["types"])
            all_external_refs.extend(props["external_refs"])
    
    # Analyze types
    type_counter = Counter(all_types)
    unique_types = list(type_counter.keys())
    
    # Analyze external references
    ref_counter = Counter(all_external_refs)
    
    # Calculate semantic depth indicators
    has_hierarchy = len(unique_types) > 1
    max_depth = len(unique_types)  # Simplified depth measure
    relationship_density = len(all_external_refs) / max(len(results), 1)
    
    return {
        "entity_types_found": unique_types,
        "type_distribution": dict(type_counter),
        "external_refs_available": dict(ref_counter),
        "semantic_depth_indicators": {
            "has_type_hierarchy": has_hierarchy,
            "max_hierarchy_depth": max_depth,
            "relationship_density": relationship_density
        }
    }


def get_endpoint_context(endpoint: str) -> Dict[str, Any]:
    """Get endpoint capabilities and context."""
    try:
        discovery_result = discovery_engine.discover(endpoint)
        
        # Map to related endpoints based on endpoint type
        related_endpoints = []
        if endpoint == "wikidata":
            related_endpoints = ["uniprot", "ensembl", "pdb", "wikipathways"]
        elif endpoint == "uniprot":
            related_endpoints = ["wikidata", "pdb", "ensembl"]
        elif endpoint == "wikipathways":
            related_endpoints = ["wikidata", "uniprot"]
        
        return {
            "search_method_used": "wikidata_api" if endpoint == "wikidata" else "sparql_patterns",
            "capabilities_available": ["describe", "sparql", "cross_refs"],
            "related_endpoints": related_endpoints,
            "endpoint_url": discovery_result.url if discovery_result else "unknown"
        }
        
    except Exception as e:
        log.debug(f"Endpoint context failed for {endpoint}: {e}")
        return {
            "search_method_used": "unknown",
            "capabilities_available": [],
            "related_endpoints": [],
            "endpoint_url": "unknown"
        }


def generate_enhanced_composition_opportunities(results: List[Dict[str, Any]], endpoint: str, query: str, universal_discovery_data: Dict[str, Any]) -> Dict[str, Any]:
    """Generate enhanced composition opportunities using universal discovery and validation."""
    opportunities = {
        "immediate_actions": [],
        "cross_reference_exploration": [],
        "semantic_exploration": [],
        "search_refinement": [],
        # New universal discovery sections
        "cross_domain_pathways": {
            "primary_domain_workflow": {},
            "bridge_opportunities": [],
            "multi_domain_suggestions": []
        },
        "domain_adaptive_workflows": {},
        "validated_identifiers": {
            "valid_patterns": {},
            "format_warnings": [],
            "suggested_resolutions": []
        },
        "automatic_pathways": {
            "discovered_pathways": [],
            "confidence_scores": {},
            "validation_status": "pending"
        }
    }
    
    if not results:
        return opportunities
    
    # Immediate actions - fetch details for top results
    top_results = results[:3]
    for result in top_results:
        entity_id = result.get("id", "")
        if entity_id:
            opportunities["immediate_actions"].append(f"cl_fetch {entity_id}  # Get detailed properties")
    
    # Generate cross-domain pathways based on universal discovery
    domains_detected = universal_discovery_data.get("domains_detected", [])
    external_refs_by_domain = universal_discovery_data.get("external_refs_by_domain", {})
    
    # Primary domain workflow
    if domains_detected:
        primary_domain = domains_detected[0]  # Most prominent domain
        opportunities["cross_domain_pathways"]["primary_domain_workflow"] = {
            "domain": primary_domain,
            "suggested_tools": generate_domain_specific_tools(primary_domain, external_refs_by_domain.get(primary_domain, []))
        }
    
    # Bridge opportunities between domains
    for i, from_domain in enumerate(domains_detected):
        for to_domain in domains_detected[i+1:]:
            bridge = generate_domain_bridge(from_domain, to_domain, query)
            if bridge:
                opportunities["cross_domain_pathways"]["bridge_opportunities"].append(bridge)
    
    # Always suggest bibliographic bridge if no other bridges exist or if we have results
    if not opportunities["cross_domain_pathways"]["bridge_opportunities"] and results:
        # Create universal bibliographic bridge
        primary_domain = domains_detected[0] if domains_detected else "general"
        bibliographic_bridge = generate_domain_bridge(primary_domain, "bibliographic", query)
        if bibliographic_bridge:
            opportunities["cross_domain_pathways"]["bridge_opportunities"].append(bibliographic_bridge)
    
    # Domain-adaptive workflows
    for domain in domains_detected:
        opportunities["domain_adaptive_workflows"][f"{domain}_workflow"] = {
            "suggested_tools": generate_domain_specific_tools(domain, external_refs_by_domain.get(domain, [])),
            "reasoning_pattern": get_domain_reasoning_pattern(domain)
        }
    
    # Automatic pathway generation for first result
    if results:
        entity_id = results[0].get("id", "")
        if entity_id:
            try:
                pathways = universal_identifier_discovery.discover_cross_reference_pathways(entity_id)
                
                # Convert pathways to tool suggestions
                discovered_pathways = []
                for pathway_name, pathway_info in pathways.get("pathways", {}).items():
                    discovered_pathways.append({
                        "domain": pathway_info.get("domain", "general"),
                        "steps": pathway_info.get("suggested_tools", []),
                        "confidence": 0.8,  # Default confidence
                        "databases_involved": [id_info.get("database", "unknown") for id_info in pathway_info.get("identifiers", [])]
                    })
                
                opportunities["automatic_pathways"]["discovered_pathways"] = discovered_pathways
                opportunities["automatic_pathways"]["validation_status"] = "validated" if pathways.get("multi_domain_coverage") else "single_domain"
                
            except Exception as e:
                log.debug(f"Automatic pathway generation failed: {e}")
    
    # Legacy composition opportunities (backward compatibility)
    legacy_opportunities = generate_composition_opportunities(results, endpoint, query)
    opportunities["cross_reference_exploration"] = legacy_opportunities["cross_reference_exploration"]
    opportunities["semantic_exploration"] = legacy_opportunities["semantic_exploration"]
    opportunities["search_refinement"] = legacy_opportunities["search_refinement"]
    
    return opportunities


def generate_domain_specific_tools(domain: str, external_refs: List[str]) -> List[str]:
    """Generate domain-specific tool suggestions based on external references."""
    tools = []
    
    # Map external refs to databases using universal discovery
    for prop_id in external_refs:
        try:
            if prop_id in universal_identifier_discovery.known_patterns:
                pattern = universal_identifier_discovery.known_patterns[prop_id]
                database = pattern.database_name
                tools.append(f"cl_resolve <entity> --to-db {database}  # {pattern.label}")
        except Exception:
            continue
    
    # Add domain-specific search suggestions
    domain_searches = {
        "biology": ["protein interactions", "pathways", "gene expression"],
        "chemistry": ["compounds", "reactions", "targets"],
        "cultural": ["artworks", "exhibitions", "provenance"],
        "medical": ["treatments", "mechanisms", "interactions"],
        "geographic": ["locations", "regions", "demographics"],
        "bibliographic": ["publications", "citations", "authors"]
    }
    
    if domain in domain_searches:
        for search_term in domain_searches[domain][:2]:  # Limit to 2
            tools.append(f"cl_search '<entity> {search_term}' --limit 3")
    
    return tools


def generate_domain_bridge(from_domain: str, to_domain: str, query: str) -> Optional[Dict[str, Any]]:
    """Generate bridge between two domains."""
    # Define known domain bridges
    bridges = {
        ("biology", "chemistry"): {
            "connection_type": "protein_drug_targets",
            "suggested_tools": [
                f"cl_search '{query} inhibitors' --limit 3",
                f"cl_search '{query} compounds' --limit 3"
            ]
        },
        ("chemistry", "biology"): {
            "connection_type": "compound_targets", 
            "suggested_tools": [
                f"cl_search '{query} targets' --limit 3",
                f"cl_search '{query} mechanism' --limit 3"
            ]
        },
        ("cultural", "geographic"): {
            "connection_type": "artwork_provenance",
            "suggested_tools": [
                f"cl_search '{query} provenance' --limit 3",
                f"cl_search '{query} location' --limit 3"
            ]
        }
    }
    
    bridge_key = (from_domain, to_domain)
    if bridge_key in bridges:
        bridge_info = bridges[bridge_key].copy()
        bridge_info["from_domain"] = from_domain
        bridge_info["to_domain"] = to_domain
        return bridge_info
    
    # Universal bibliographic bridge - always available
    if to_domain == "bibliographic" or to_domain == "general":
        return {
            "from_domain": from_domain,
            "to_domain": "bibliographic",
            "connection_type": "literature_references",
            "suggested_tools": [
                f"cl_search '{query} research' --limit 3",
                f"cl_search '{query} studies' --limit 3"
            ]
        }
    
    return None


def get_domain_reasoning_pattern(domain: str) -> str:
    """Get reasoning pattern for domain."""
    patterns = {
        "biology": "Structure → Function → Interactions → Pathways",
        "chemistry": "Structure → Properties → Reactions → Applications", 
        "cultural": "Object → Context → Provenance → Significance",
        "medical": "Condition → Mechanism → Treatment → Outcomes",
        "geographic": "Location → Context → Demographics → Relationships",
        "bibliographic": "Work → Author → Citations → Impact"
    }
    return patterns.get(domain, "Entity → Properties → Relationships → Context")


def generate_composition_opportunities(results: List[Dict[str, Any]], endpoint: str, query: str) -> Dict[str, Any]:
    """Generate composition opportunities based on search results."""
    opportunities = {
        "immediate_actions": [],
        "cross_reference_exploration": [],
        "semantic_exploration": [],
        "search_refinement": []
    }
    
    if not results:
        return opportunities
    
    # Immediate actions - fetch details for top results
    top_results = results[:3]  # Top 3 results
    for result in top_results:
        entity_id = result.get("id", "")
        if entity_id:
            opportunities["immediate_actions"].append(f"cl_fetch {entity_id}  # Get detailed properties")
    
    # Cross-reference exploration
    if endpoint == "wikidata":
        opportunities["cross_reference_exploration"].extend([
            f"cl_search '{query}' --endpoint uniprot  # Search protein database",
            f"cl_discover wikipathways --patterns  # Explore pathway database"
        ])
        
        # Add specific cross-reference resolution if we have external refs
        sample_result = results[0] if results else {}
        entity_id = sample_result.get("id", "")
        if entity_id:
            opportunities["cross_reference_exploration"].append(
                f"cl_resolve {entity_id} --to-db uniprot  # Follow cross-references"
            )
    
    # Semantic exploration
    opportunities["semantic_exploration"].extend([
        f"cl_query 'SELECT ?item ?itemLabel WHERE {{ ?item wdt:P31 ?type . ?item rdfs:label ?itemLabel . FILTER(CONTAINS(?itemLabel, \"{query}\")) }}' --endpoint {endpoint}  # Explore by type",
        f"cl_discover {endpoint} --schema  # Understand endpoint structure"
    ])
    
    # Search refinement
    query_words = query.split()
    if len(query_words) > 1:
        # Suggest broader search
        broader_query = query_words[0]
        opportunities["search_refinement"].append(f"cl_search '{broader_query}'  # Broader search")
        
        # Suggest more specific search
        specific_query = f"{query} protein" if "protein" not in query.lower() else f"{query} human"
        opportunities["search_refinement"].append(f"cl_search '{specific_query}'  # More specific")
    else:
        # Single word query - suggest related terms
        related_terms = {
            "insulin": "diabetes hormone",
            "protein": "enzyme biomolecule", 
            "COVID": "coronavirus SARS-CoV-2",
            "spike": "SARS-CoV-2 protein"
        }
        
        base_query = query.lower()
        if base_query in related_terms:
            opportunities["search_refinement"].append(f"cl_search '{related_terms[base_query]}'  # Related terms")
    
    return opportunities


def generate_validation_metadata(results: List[Dict[str, Any]], universal_discovery_data: Dict[str, Any]) -> Dict[str, Any]:
    """Generate validation metadata using the metadata validation system."""
    if not results:
        return {
            "accessible_databases": [],
            "confidence_scores": {},
            "filtered_suggestions": []
        }
    
    try:
        # Collect suggested databases from universal discovery
        external_refs_by_domain = universal_discovery_data.get("external_refs_by_domain", {})
        suggested_databases = []
        
        for domain, refs in external_refs_by_domain.items():
            for prop_id in refs:
                if prop_id in universal_identifier_discovery.known_patterns:
                    pattern = universal_identifier_discovery.known_patterns[prop_id]
                    suggested_databases.append(pattern.database_name)
        
        # Use metadata validation to filter accessible databases
        if suggested_databases:
            validation_result = metadata_validator.hallucination_guard.filter_accessible_databases(suggested_databases)
            
            return {
                "accessible_databases": validation_result.validated_databases,
                "confidence_scores": validation_result.accessibility_scores,
                "filtered_suggestions": validation_result.warnings
            }
        else:
            return {
                "accessible_databases": [],
                "confidence_scores": {},
                "filtered_suggestions": ["No external databases detected"]
            }
            
    except Exception as e:
        log.debug(f"Validation metadata generation failed: {e}")
        return {
            "accessible_databases": [],
            "confidence_scores": {},
            "filtered_suggestions": [f"Validation failed: {str(e)}"]
        }


def get_session_context() -> Optional[Dict[str, Any]]:
    """Get research session context if available."""
    try:
        session_file = Path.cwd() / ".cogitarelink" / "session.json"
        if not session_file.exists():
            return None
            
        with open(session_file) as f:
            session_data = json.load(f)
            
        return {
            "research_domain": session_data.get("researchDomain"),
            "research_goal": session_data.get("researchGoal"), 
            "entities_discovered_this_session": session_data.get("researchProgress", {}).get("entitiesDiscovered", 0),
            "successful_patterns": ["search→fetch→resolve"]  # Could be extracted from session history
        }
        
    except Exception as e:
        log.debug(f"Session context failed: {e}")
        return None


def search_wikidata(query: str, entity_type: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
    """Search Wikidata entities using Wikidata API."""
    import httpx
    
    params = {
        "action": "wbsearchentities",
        "search": query,
        "language": "en",
        "limit": limit,
        "format": "json"
    }
    if entity_type:
        params["type"] = entity_type
    
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get("https://www.wikidata.org/w/api.php", params=params)
            response.raise_for_status()
            data = response.json()
            
            results = []
            for item in data.get("search", []):
                results.append({
                    "id": item.get("id", ""),
                    "label": item.get("label", ""),
                    "description": item.get("description", ""),
                    "type": entity_type or "entity",
                    "url": item.get("concepturi", "")
                })
            
            return results
            
    except Exception as e:
        log.error(f"Wikidata search failed: {e}")
        return []


def search_sparql_endpoint(endpoint: str, query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Search SPARQL endpoints using simple patterns."""
    discovery_result = discovery_engine.discover(endpoint)
    
    # Build PREFIX declarations
    prefix_lines = []
    for prefix, uri in discovery_result.prefixes.items():
        prefix_lines.append(f"PREFIX {prefix}: <{uri}>")
    
    # Get search pattern and format properly
    sparql_body = None
    if "pathway_search" in discovery_result.patterns:
        sparql_body = discovery_result.patterns["pathway_search"].format(query=query.lower())
    elif "protein_search" in discovery_result.patterns:
        sparql_body = discovery_result.patterns["protein_search"].format(query=query.lower())
    elif "entity_search" in discovery_result.patterns:
        sparql_body = discovery_result.patterns["entity_search"].format(query=query.lower())
    else:
        # Fallback to basic search with rdfs:label
        sparql_body = f"""SELECT ?item ?itemLabel WHERE {{{{
    ?item rdfs:label ?itemLabel .
    FILTER(CONTAINS(LCASE(?itemLabel), "{query.lower()}"))
}}}} LIMIT {limit}"""
    
    # Combine prefixes and query body
    full_query = "\n".join(prefix_lines) + "\n\n" + sparql_body
    
    log.debug(f"Executing SPARQL query on {endpoint}:\n{full_query}")
    
    result = discovery_engine.query_endpoint(endpoint, full_query)
    
    if not result["success"]:
        log.error(f"SPARQL search failed: {result.get('error', 'Unknown error')}")
        return []
    
    # Convert SPARQL results to simple format
    entities = []
    for binding in result["results"]:
        # Try different possible result variable names
        item_uri = (binding.get("item", {}).get("value", "") or 
                   binding.get("pathway", {}).get("value", "") or
                   binding.get("protein", {}).get("value", ""))
        
        label = (binding.get("itemLabel", {}).get("value", "") or 
                binding.get("title", {}).get("value", "") or
                binding.get("name", {}).get("value", "") or
                binding.get("label", {}).get("value", ""))
        
        # Extract ID from URI
        entity_id = item_uri.split("/")[-1] if item_uri else ""
        
        if item_uri and label:  # Only include results with both URI and label
            entities.append({
                "id": entity_id,
                "label": label,
                "description": "",
                "type": "entity",
                "url": item_uri
            })
    
    return entities


@click.command()
@click.argument('query')
@click.option('--type', 'entity_type', help='Entity type filter (for Wikidata)')
@click.option('--endpoint', default='wikidata', help='Search endpoint (default: wikidata)')
@click.option('--limit', default=10, help='Number of results (default: 10)')
@click.option('--format', 'output_format', default='json', type=click.Choice(['json', 'text']),
              help='Output format (default: json)')
def search(query: str, entity_type: Optional[str], endpoint: str, limit: int, output_format: str):
    """Enhanced entity search with rich metadata and composition opportunities.
    
    Examples:
        cl_search "insulin"
        cl_search "MFN2" --type item
        cl_search "COVID" --endpoint wikipathways
        cl_search "spike protein" --format text
    """
    
    if not query.strip():
        click.echo('{"error": "Query cannot be empty"}', err=True)
        sys.exit(1)
    
    try:
        start_time = time.time()
        
        # Search based on endpoint
        if endpoint == "wikidata":
            results = search_wikidata(query, entity_type, limit)
        else:
            results = search_sparql_endpoint(endpoint, query, limit)
        
        end_time = time.time()
        execution_time_ms = round((end_time - start_time) * 1000, 2)
        
        # Generate enhanced metadata and composition opportunities
        if output_format == "json":
            # Universal discovery analysis
            universal_discovery_data = generate_universal_discovery_metadata(results, endpoint)
            
            # Rich metadata analysis (legacy)
            discovery_analysis = analyze_search_results(results, endpoint)
            endpoint_context = get_endpoint_context(endpoint)
            
            # Validation metadata
            validation_results = generate_validation_metadata(results, universal_discovery_data)
            
            # Enhanced composition opportunities
            composition_opportunities = generate_enhanced_composition_opportunities(
                results, endpoint, query, universal_discovery_data
            )
            
            session_context = get_session_context()
            
            # Calculate search effectiveness
            search_effectiveness = min(len(results) / max(limit, 1), 1.0)
            
            # Enhanced output structure
            output = {
                "query": query,
                "endpoint": endpoint,
                "results": results,
                "count": len(results),
                
                # Enhanced metadata
                "metadata": {
                    "discovery_analysis": discovery_analysis,
                    "endpoint_context": endpoint_context,
                    "execution_context": {
                        "cache_hit": False,  # Could be enhanced with actual cache detection
                        "execution_time_ms": execution_time_ms,
                        "search_effectiveness": search_effectiveness
                    },
                    # NEW: Universal discovery metadata
                    "universal_discovery": universal_discovery_data,
                    # NEW: Validation results
                    "validation_results": validation_results
                },
                
                # Enhanced composition opportunities
                "composition_opportunities": composition_opportunities
            }
            
            # Add session context if available
            if session_context:
                output["session_context"] = session_context
            
            click.echo(json.dumps(output, indent=2))
        else:
            # Simple text format (unchanged for backward compatibility)
            if not results:
                click.echo(f"No results found for '{query}'")
            else:
                click.echo(f"Found {len(results)} results for '{query}':")
                for result in results:
                    click.echo(f"  {result['id']:<15} {result['label']}")
    
    except Exception as e:
        error_output = {
            "error": str(e),
            "query": query,
            "endpoint": endpoint
        }
        if output_format == "json":
            click.echo(json.dumps(error_output), err=True)
        else:
            click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    search()