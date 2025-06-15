"""cl_resolve: Cross-reference resolution following Claude Code patterns.

Minimal tool for resolving identifiers across databases - fast, simple, composable.
"""

from __future__ import annotations

import json
import sys
from typing import Optional, Dict, Any, List

import click

from ..discovery.base import discovery_engine
from ..core.debug import get_logger
from ..core.universal_identifier_discovery import universal_identifier_discovery
import re

log = get_logger("cl_resolve")


# Known cross-reference patterns (kept for backward compatibility)
XREF_PATTERNS = {
    "wikidata": {
        "uniprot": "wdt:P352",        # UniProt protein ID
        "kegg": "wdt:P665",           # KEGG ID
        "ensembl": "wdt:P594",        # Ensembl gene ID
        "ncbi_gene": "wdt:P351",      # Entrez Gene ID
        "pubmed": "wdt:P698",         # PubMed ID
        "doi": "wdt:P356"             # DOI
    },
    "uniprot": {
        "wikidata": "rdfs:seeAlso",   # General cross-references
        "kegg": "up:classifiedWith",   # Classification links
        "ensembl": "up:database"      # Database cross-references
    },
    "wikipathways": {
        "wikidata": "wp:hasXref",     # External references
        "kegg": "wp:hasXref",         # KEGG pathway references
        "uniprot": "wp:hasXref"       # Protein references
    }
}

# Dynamic discovery cache
_discovery_cache = {}
_database_name_cache = {}


def resolve_from_wikidata(identifier: str, target_db: str) -> List[Dict[str, Any]]:
    """Resolve identifier from Wikidata to other databases using dynamic discovery."""
    
    # First try hardcoded patterns for backward compatibility
    xref_prop = XREF_PATTERNS["wikidata"].get(target_db)
    
    # If not in hardcoded patterns, use dynamic discovery
    if not xref_prop:
        xref_prop = get_wikidata_property_for_database_dynamic(target_db)
        if not xref_prop:
            return []
    
    # Query Wikidata for cross-references
    sparql_query = f"""
    SELECT ?item ?itemLabel ?xref WHERE {{
        ?item {xref_prop} "{identifier}" .
        SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en" }}
    }}
    """.strip()
    
    result = discovery_engine.query_endpoint("wikidata", sparql_query)
    
    if not result["success"]:
        log.error(f"Wikidata resolution failed: {result.get('error')}")
        return []
    
    results = []
    for binding in result["results"]:
        item_uri = binding.get("item", {}).get("value", "")
        label = binding.get("itemLabel", {}).get("value", "")
        xref = binding.get("xref", {}).get("value", "")
        
        if item_uri:
            entity_id = item_uri.split("/")[-1]
            results.append({
                "source_id": identifier,
                "source_db": target_db,
                "target_id": entity_id,
                "target_db": "wikidata",
                "target_label": label,
                "target_uri": item_uri
            })
    
    return results


def resolve_to_wikidata(identifier: str, source_db: str) -> List[Dict[str, Any]]:
    """Resolve identifier to Wikidata from other databases using dynamic discovery."""
    
    # First try hardcoded patterns for backward compatibility
    xref_prop = XREF_PATTERNS["wikidata"].get(source_db)
    
    # If not in hardcoded patterns, use dynamic discovery
    if not xref_prop:
        xref_prop = get_wikidata_property_for_database_dynamic(source_db)
        if not xref_prop:
            return []
    
    # Query Wikidata for entities with this cross-reference
    sparql_query = f"""
    SELECT ?item ?itemLabel WHERE {{
        ?item {xref_prop} "{identifier}" .
        SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en" }}
    }}
    """.strip()
    
    result = discovery_engine.query_endpoint("wikidata", sparql_query)
    
    if not result["success"]:
        log.error(f"Wikidata resolution failed: {result.get('error')}")
        return []
    
    results = []
    for binding in result["results"]:
        item_uri = binding.get("item", {}).get("value", "")
        label = binding.get("itemLabel", {}).get("value", "")
        
        if item_uri:
            entity_id = item_uri.split("/")[-1]
            results.append({
                "source_id": identifier,
                "source_db": source_db,
                "target_id": entity_id,
                "target_db": "wikidata",
                "target_label": label,
                "target_uri": item_uri
            })
    
    return results


def resolve_via_sparql(identifier: str, source_db: str, target_db: str) -> List[Dict[str, Any]]:
    """Resolve identifier using SPARQL queries on endpoint."""
    
    # Simple SPARQL resolution - look for sameAs or seeAlso relationships
    discovery_result = discovery_engine.discover(source_db)
    
    # Build PREFIX declarations
    prefix_lines = []
    for prefix, uri in discovery_result.prefixes.items():
        prefix_lines.append(f"PREFIX {prefix}: <{uri}>")
    
    # Try different resolution patterns
    sparql_queries = [
        # Pattern 1: Direct sameAs links
        f"""SELECT ?target WHERE {{
            <{identifier}> owl:sameAs ?target .
        }}""",
        
        # Pattern 2: See also links
        f"""SELECT ?target WHERE {{
            <{identifier}> rdfs:seeAlso ?target .
            FILTER(CONTAINS(STR(?target), "{target_db}"))
        }}""",
        
        # Pattern 3: Generic cross-references
        f"""SELECT ?target WHERE {{
            <{identifier}> ?xref ?target .
            FILTER(CONTAINS(STR(?target), "{target_db}"))
        }}"""
    ]
    
    results = []
    for sparql_body in sparql_queries:
        full_query = "\n".join(prefix_lines) + "\n\n" + sparql_body
        
        result = discovery_engine.query_endpoint(source_db, full_query)
        
        if result["success"]:
            for binding in result["results"]:
                target_uri = binding.get("target", {}).get("value", "")
                if target_uri:
                    target_id = target_uri.split("/")[-1]
                    results.append({
                        "source_id": identifier,
                        "source_db": source_db,
                        "target_id": target_id,
                        "target_db": target_db,
                        "target_uri": target_uri
                    })
    
    return results


@click.command()
@click.argument('identifier')
@click.option('--from-db', 'source_db', help='Source database (auto-detect if not specified)')
@click.option('--to-db', 'target_db', help='Target database (resolve to all if not specified)')
@click.option('--format', 'output_format', default='json', type=click.Choice(['json', 'text']),
              help='Output format (default: json)')
def resolve(identifier: str, source_db: Optional[str], target_db: Optional[str], output_format: str):
    """Resolve identifiers across databases.
    
    Examples:
        cl_resolve P04637                           # Auto-detect and resolve to all
        cl_resolve P04637 --from-db uniprot        # From UniProt to all
        cl_resolve Q7240673 --to-db uniprot        # From auto-detected to UniProt
        cl_resolve P04637 --from-db uniprot --to-db wikidata  # Specific resolution
    """
    
    if not identifier.strip():
        click.echo('{"error": "Identifier cannot be empty"}', err=True)
        sys.exit(1)
    
    try:
        results = []
        
        # Auto-detect source database if not specified (enhanced with dynamic patterns)
        if not source_db:
            source_db = auto_detect_source_database_enhanced(identifier)
        
        # Resolve based on source and target
        if source_db == "wikidata" and target_db:
            # Resolve from Wikidata to specific target
            results = resolve_from_wikidata(identifier, target_db)
        
        elif target_db == "wikidata" or not target_db:
            # Resolve to Wikidata (or all targets via Wikidata)
            results = resolve_to_wikidata(identifier, source_db)
        
        else:
            # Try SPARQL-based resolution
            results = resolve_via_sparql(identifier, source_db, target_db)
        
        # If no results and we have both source and target, try reverse lookup
        if not results and source_db and target_db and source_db != target_db:
            results = resolve_via_sparql(identifier, target_db, source_db)
            # Swap source/target in results
            for result in results:
                result["source_db"], result["target_db"] = result["target_db"], result["source_db"]
                result["source_id"], result["target_id"] = result["target_id"], result["source_id"]
        
        # Format output
        if output_format == "json":
            output = {
                "identifier": identifier,
                "source_db": source_db,
                "target_db": target_db or "all",
                "results": results,
                "count": len(results)
            }
            click.echo(json.dumps(output, indent=2))
        
        else:
            # Text format
            if not results:
                click.echo(f"No cross-references found for {identifier}")
                if source_db:
                    click.echo(f"Source database: {source_db}")
                if target_db:
                    click.echo(f"Target database: {target_db}")
            else:
                click.echo(f"Cross-references for {identifier}:")
                if source_db:
                    click.echo(f"Source: {source_db}")
                click.echo()
                
                for result in results:
                    target_info = result["target_id"]
                    if result.get("target_label"):
                        target_info += f" ({result['target_label']})"
                    
                    click.echo(f"  {result['target_db']}: {target_info}")
                    if result.get("target_uri"):
                        click.echo(f"    URI: {result['target_uri']}")
    
    except Exception as e:
        error_output = {
            "error": str(e),
            "identifier": identifier,
            "source_db": source_db,
            "target_db": target_db
        }
        if output_format == "json":
            click.echo(json.dumps(error_output), err=True)
        else:
            click.echo(f"Error: {e}", err=True)
        sys.exit(1)


def get_wikidata_property_for_database_dynamic(database: str) -> Optional[str]:
    """Get Wikidata property for database using dynamic discovery."""
    # First check known patterns
    all_patterns = universal_identifier_discovery.known_patterns
    for prop_id, pattern in all_patterns.items():
        if pattern.database_name == database:
            return f"wdt:{prop_id}"
    
    # Then check dynamic cache
    dynamic_patterns = universal_identifier_discovery.dynamic_pattern_cache
    for prop_id, pattern in dynamic_patterns.items():
        if pattern.database_name == database:
            return f"wdt:{prop_id}"
    
    # If not found, try to discover it
    if database == "getty_tgn":
        # We know P1667 is for Getty, so discover it
        pattern = universal_identifier_discovery.discover_pattern_via_describe("P1667")
        if pattern and pattern.database_name == database:
            return f"wdt:P1667"
    
    return None


def auto_detect_source_database_enhanced(identifier: str) -> str:
    """Enhanced auto-detection using dynamic patterns."""
    # Start with basic patterns
    if identifier.startswith("Q") and identifier[1:].isdigit():
        return "wikidata"
    elif identifier.startswith("P") and len(identifier) == 6:
        return "uniprot"
    elif identifier.startswith("WP") and "_r" in identifier:
        return "wikipathways"
    
    # Enhanced patterns for new domains using format patterns from our discovery system
    
    # Getty Thesaurus of Geographic Names: [1-9][0-9]{6}
    if re.match(r"^[1-9][0-9]{6}$", identifier):
        return "getty_tgn"
    
    # Chemical patterns
    if identifier.startswith("CHEMBL"):
        return "chembl"
    elif re.match(r"^[0-9]+-[0-9]+-[0-9]+$", identifier):
        return "cas"  # CAS Registry Number
    
    # Cultural patterns  
    if re.match(r"^[0-9]{6}PE[0-9]{6}$", identifier):
        return "joconde"
    elif re.match(r"^[A-Z0-9\-\.]+$", identifier) and any(prefix in identifier for prefix in ["INV.", "LP.", "MR."]):
        return "louvre"
    
    # Bibliographic patterns
    if re.match(r"^[0-9]{4} [0-9]{4} [0-9]{4} [0-9]{3}[0-9X]$", identifier):
        return "isni"
    elif re.match(r"^[a-z]{1,2}[0-9]{8,10}$", identifier):
        return "loc"  # Library of Congress
    
    return "unknown"


def get_wikidata_property_for_database(database: str) -> Optional[str]:
    """Get Wikidata property for database using hardcoded patterns (backward compatibility)."""
    return XREF_PATTERNS["wikidata"].get(database)


# Core Live Discovery Functions

def discover_service_for_property(prop_id: str) -> str:
    """Discover service entity for property - cache-aware discovery."""
    from ..discovery.cache_manager import cache_manager
    
    # 1. Check cache first (fast path)
    cache_key = f"service_discovery:{prop_id}"
    cached = cache_manager.get(cache_key)
    if cached:
        return cached
    
    # 2. Fallback to live discovery capability
    sparql_query = f"""
    SELECT ?service WHERE {{
        ?service wdt:P1687 wd:{prop_id} .
    }} LIMIT 1
    """
    
    result = discovery_engine.query_endpoint("wikidata", sparql_query)
    service_id = ""
    
    if result["success"] and result["results"]:
        service_uri = result["results"][0].get("service", {}).get("value", "")
        service_id = service_uri.split("/")[-1] if service_uri else ""
    
    # 3. Cache the result for future use
    cache_manager.set(cache_key, service_id, ttl=86400)  # 24 hours
    
    return service_id


def discover_properties_for_service(service_id: str) -> List[str]:
    """Discover all properties defined by a service using live Wikidata."""
    sparql_query = f"""
    SELECT ?prop WHERE {{
        wd:{service_id} wdt:P1687 ?prop .
    }}
    """
    
    result = discovery_engine.query_endpoint("wikidata", sparql_query)
    
    properties = []
    if result["success"]:
        for binding in result["results"]:
            prop_uri = binding.get("prop", {}).get("value", "")
            if prop_uri:
                properties.append(prop_uri.split("/")[-1])
    
    return properties


def classify_domain_from_service(service_id: str) -> str:
    """Classify domain from service main subject - cache-aware discovery."""
    from ..discovery.cache_manager import cache_manager
    
    # 1. Check cache first (fast path)
    cache_key = f"service_domain:{service_id}"
    cached = cache_manager.get(cache_key)
    if cached:
        return cached
    
    # 2. Fallback to live discovery capability
    domain = _discover_domain_via_sparql(service_id)
    
    # 3. Cache the result for future use
    cache_manager.set(cache_key, domain, ttl=86400)  # 24 hours
    
    return domain


def _discover_domain_via_sparql(service_id: str) -> str:
    """Discover domain from service main subject using live SPARQL."""
    # First try to find academic disciplines
    sparql_query = f"""
    SELECT ?subjectLabel WHERE {{
        wd:{service_id} wdt:P921 ?subject .
        ?subject wdt:P31 ?type .
        VALUES ?type {{ wd:Q2465832 wd:Q11862829 wd:Q1047113 }}
        ?subject rdfs:label ?subjectLabel .
        FILTER(LANG(?subjectLabel) = "en")
    }} LIMIT 1
    """
    
    result = discovery_engine.query_endpoint("wikidata", sparql_query)
    
    if result["success"] and result["results"]:
        subject_label = result["results"][0].get("subjectLabel", {}).get("value", "")
        
        # Use the label directly as domain, with normalization
        if "biology" in subject_label.lower():
            return "biology"
        elif "chemistry" in subject_label.lower() or "chemical" in subject_label.lower():
            return "chemistry" 
        elif "geography" in subject_label.lower() or "geographic" in subject_label.lower():
            return "geography"
        else:
            return subject_label.lower()  # Use the actual label
    
    # If no academic discipline found, look for any main subject
    broader_query = f"""
    SELECT ?subjectLabel WHERE {{
        wd:{service_id} wdt:P921 ?subject .
        ?subject rdfs:label ?subjectLabel .
        FILTER(LANG(?subjectLabel) = "en")
    }} LIMIT 5
    """
    
    broader_result = discovery_engine.query_endpoint("wikidata", broader_query)
    
    if broader_result["success"] and broader_result["results"]:
        for binding in broader_result["results"]:
            subject_label = binding.get("subjectLabel", {}).get("value", "")
            
            # Check for domain keywords in any main subject
            if "biology" in subject_label.lower() or "biological" in subject_label.lower():
                return "biology"
            elif "chemistry" in subject_label.lower() or "chemical" in subject_label.lower():
                return "chemistry"
            elif any(geo_word in subject_label.lower() for geo_word in ["geography", "geographic", "location", "toponym", "place"]):
                return "geography"
            elif any(cult_word in subject_label.lower() for cult_word in ["culture", "cultural", "heritage", "art", "museum"]):
                return "cultural"
            elif any(bio_word in subject_label.lower() for bio_word in ["medicine", "medical", "health", "disease"]):
                return "medical"
    
    return "general"


def discover_database_pattern(prop_id: str) -> Dict[str, Any]:
    """Discover complete database pattern using Claude Code READ→VERIFY→Cache methodology."""
    from ..discovery.cache_manager import cache_manager
    import time
    
    cache_key = f"database_pattern:{prop_id}"
    start_time = time.time()
    
    # 1. Check cache first (fast path)
    cached = cache_manager.get(cache_key)
    if cached:
        cached["_cache_metadata"] = {
            "cache_hit": True,
            "execution_time_ms": int((time.time() - start_time) * 1000),
            "discovery_method": "cached_pattern"
        }
        return cached
    
    # 2. Claude Code pattern: READ all properties, let Claude VERIFY semantics
    pattern = discover_pattern_via_claude_analysis(prop_id)
    
    # Add cache metadata
    execution_time = int((time.time() - start_time) * 1000)
    pattern["_cache_metadata"] = {
        "cache_hit": False,
        "execution_time_ms": execution_time,
        "discovery_method": "claude_semantic_analysis"
    }
    
    # 3. Cache result for future use
    cache_manager.set(cache_key, pattern, ttl=86400)  # 24 hours
    
    return pattern


def discover_pattern_via_claude_analysis(prop_id: str) -> Dict[str, Any]:
    """Use Claude Code READ→VERIFY→Cache pattern for property discovery."""
    # Step 1: READ - Get ALL properties via DESCRIBE
    describe_query = f"DESCRIBE wd:{prop_id}"
    describe_result = discovery_engine.query_endpoint("wikidata", describe_query)
    
    base_pattern = {
        "property_id": prop_id,
        "name": "",
        "domain": "general", 
        "discovered_dynamically": True,
        "semantic_analysis": {},
        "raw_describe_data": {}
    }
    
    if not describe_result["success"]:
        return base_pattern
    
    # Step 2: VERIFY - Let existing semantic analysis extract meaningful properties
    # Use the universal_identifier_discovery system's DESCRIBE analysis
    from ..core.universal_identifier_discovery import universal_identifier_discovery
    
    try:
        # Leverage existing DESCRIBE-based pattern discovery
        discovered_pattern = universal_identifier_discovery.discover_pattern_via_describe(prop_id)
        
        if discovered_pattern:
            # Convert from universal discovery format to our cache format
            base_pattern.update({
                "name": discovered_pattern.label,
                "domain": discovered_pattern.domain.value if hasattr(discovered_pattern.domain, 'value') else str(discovered_pattern.domain),
                "format_pattern": discovered_pattern.format_pattern or "",
                "formatter_url": discovered_pattern.endpoint_url or "",
                "example": discovered_pattern.example_values[0] if discovered_pattern.example_values else "",
                "database_name": discovered_pattern.database_name,
                "semantic_analysis": {
                    "discovery_method": "universal_identifier_system",
                    "confidence": "high",
                    "semantic_properties_found": True,
                    "describe_based": discovered_pattern.discovered_dynamically
                }
            })
            
            # Add service discovery using existing cache-aware function
            service_id = discover_service_for_property(prop_id)
            if service_id:
                base_pattern["service_id"] = service_id
                base_pattern["domain"] = classify_domain_from_service(service_id)
                
                # Try to discover SPARQL endpoint for the service
                sparql_endpoint = discover_sparql_endpoint_for_service(service_id)
                if sparql_endpoint:
                    base_pattern["sparql_endpoint"] = sparql_endpoint
        
        else:
            # Fallback: Basic label extraction if universal discovery fails
            basic_info = extract_basic_property_info(prop_id)
            base_pattern.update(basic_info)
            base_pattern["semantic_analysis"] = {
                "discovery_method": "basic_fallback",
                "confidence": "low",
                "semantic_properties_found": False
            }
            
    except Exception as e:
        # Fallback to basic info if semantic analysis fails
        basic_info = extract_basic_property_info(prop_id)
        base_pattern.update(basic_info)
        base_pattern["semantic_analysis"] = {
            "discovery_method": "error_fallback",
            "confidence": "low", 
            "error": str(e),
            "semantic_properties_found": False
        }
    
    return base_pattern


def discover_sparql_endpoint_for_service(service_id: str) -> str:
    """Discover SPARQL endpoint for a service using semantic analysis."""
    sparql_query = f"""
    SELECT ?endpoint WHERE {{
        wd:{service_id} wdt:P5305 ?endpoint .
    }} LIMIT 1
    """
    
    result = discovery_engine.query_endpoint("wikidata", sparql_query)
    
    if result["success"] and result["results"]:
        return result["results"][0].get("endpoint", {}).get("value", "")
    
    return ""


def extract_basic_property_info(prop_id: str) -> Dict[str, Any]:
    """Fallback: Extract basic property information."""
    sparql_query = f"""
    SELECT ?label ?description WHERE {{
        wd:{prop_id} rdfs:label ?label .
        OPTIONAL {{ wd:{prop_id} schema:description ?description }}
        FILTER(LANG(?label) = "en")
        FILTER(LANG(?description) = "en")
    }} LIMIT 1
    """
    
    result = discovery_engine.query_endpoint("wikidata", sparql_query)
    
    basic_info = {
        "name": "",
        "format_pattern": "",
        "formatter_url": "",
        "example": "",
        "service_id": "",
        "sparql_endpoint": ""
    }
    
    if result["success"] and result["results"]:
        binding = result["results"][0]
        basic_info["name"] = binding.get("label", {}).get("value", "")
    
    return basic_info


def resolve_identifier_dynamic(identifier: str) -> Dict[str, Any]:
    """Resolve identifier using cache-aware dynamic discovery with structured response."""
    import time
    from ..discovery.cache_manager import cache_manager
    
    start_time = time.time()
    
    # Auto-detect database using enhanced patterns
    source_db = auto_detect_source_database_enhanced(identifier)
    
    # Check resolution cache first
    cache_key = f"identifier_resolution:{identifier}"
    cached_resolution = cache_manager.get(cache_key)
    if cached_resolution:
        execution_time = int((time.time() - start_time) * 1000)
        return _build_structured_response(
            identifier=identifier,
            source_db=source_db,
            results=cached_resolution,
            cache_hit=True,
            execution_time=execution_time,
            learned_patterns=[]
        )
    
    # Discover pattern for this database using cache-aware discovery
    discovered_patterns = []
    prop_id = None
    
    # First try known patterns
    for pid, pattern in universal_identifier_discovery.known_patterns.items():
        if pattern.database_name == source_db.replace("_", ""):
            prop_id = pid
            break
    
    # If not found, try dynamic discovery
    if not prop_id and source_db != "unknown":
        # Look for properties by database name pattern
        database_pattern = discover_database_pattern_by_name(source_db)
        if database_pattern:
            prop_id = database_pattern["property_id"]
            discovered_patterns.append(database_pattern)
    
    # Perform resolution
    if prop_id:
        results = resolve_to_wikidata(identifier, source_db)
        # Cache the resolution results
        cache_manager.set(cache_key, results, ttl=3600)  # 1 hour
    else:
        results = []
    
    execution_time = int((time.time() - start_time) * 1000)
    
    return _build_structured_response(
        identifier=identifier,
        source_db=source_db,
        results=results,
        cache_hit=False,
        execution_time=execution_time,
        learned_patterns=discovered_patterns
    )


def discover_database_pattern_by_name(database_name: str) -> Optional[Dict[str, Any]]:
    """Discover property pattern by database name using cache-aware SPARQL discovery."""
    from ..discovery.cache_manager import cache_manager
    import time
    
    cache_key = f"database_name_lookup:{database_name}"
    start_time = time.time()
    
    # 1. Check cache first (fast path)
    cached = cache_manager.get(cache_key)
    if cached:
        return cached
    
    # 2. Fallback to live discovery capability
    # Search for properties that have formatter URLs or examples containing the database name
    sparql_query = f"""
    SELECT ?prop ?label ?description ?format ?formatter ?example WHERE {{
        ?prop wdt:P31 wd:Q19847637 .  # external identifier property
        ?prop rdfs:label ?label .
        OPTIONAL {{ ?prop schema:description ?description }}
        OPTIONAL {{ ?prop wdt:P1793 ?format }}
        OPTIONAL {{ ?prop wdt:P1630 ?formatter }}
        OPTIONAL {{ ?prop wdt:P1855 ?example }}
        FILTER(LANG(?label) = "en")
        FILTER(LANG(?description) = "en")
        FILTER(CONTAINS(LCASE(?label), "{database_name.lower()}") || 
               CONTAINS(LCASE(STR(?formatter)), "{database_name.lower()}"))
    }} LIMIT 5
    """
    
    result = discovery_engine.query_endpoint("wikidata", sparql_query)
    
    if result["success"] and result["results"]:
        # Take the first match that looks most relevant
        for binding in result["results"]:
            prop_uri = binding.get("prop", {}).get("value", "")
            if prop_uri:
                prop_id = prop_uri.split("/")[-1]
                
                pattern = {
                    "property_id": prop_id,
                    "name": binding.get("label", {}).get("value", ""),
                    "domain": "general",
                    "format_pattern": binding.get("format", {}).get("value", ""),
                    "formatter_url": binding.get("formatter", {}).get("value", ""),
                    "example": binding.get("example", {}).get("value", ""),
                    "service_id": "",
                    "discovered_dynamically": True,
                    "_cache_metadata": {
                        "cache_hit": False,
                        "execution_time_ms": int((time.time() - start_time) * 1000),
                        "discovery_method": "database_name_search"
                    }
                }
                
                # Try to discover service and domain
                service_id = discover_service_for_property(prop_id)
                if service_id:
                    pattern["service_id"] = service_id
                    pattern["domain"] = classify_domain_from_service(service_id)
                
                # 3. Cache the successful result
                cache_manager.set(cache_key, pattern, ttl=86400)  # 24 hours
                
                return pattern
    
    # 4. Cache negative result to avoid repeated lookups
    negative_result = {
        "property_id": "",
        "discovered_dynamically": False,
        "_cache_metadata": {
            "cache_hit": False,
            "execution_time_ms": int((time.time() - start_time) * 1000),
            "discovery_method": "database_name_search_failed"
        }
    }
    cache_manager.set(cache_key, negative_result, ttl=3600)  # 1 hour for negative results
    
    return None


def discover_all_services_with_endpoints() -> Dict[str, Any]:
    """Software 2.0: Discover all services with SPARQL endpoints automatically."""
    sparql_query = """
    SELECT DISTINCT ?service ?serviceLabel ?endpoint WHERE {
        ?service wdt:P5305 ?endpoint .
        ?service wdt:P1687 ?prop .
        SERVICE wikibase:label { bd:serviceParam wikibase:language "en" }
    }
    """
    
    result = discovery_engine.query_endpoint("wikidata", sparql_query)
    
    services_by_domain = {
        "bibliographic": [],
        "geographic": [], 
        "cultural": [],
        "scientific": [],
        "technical": [],
        "general": []
    }
    
    if result["success"]:
        for binding in result["results"]:
            service_uri = binding.get("service", {}).get("value", "")
            service_label = binding.get("serviceLabel", {}).get("value", "")
            endpoint = binding.get("endpoint", {}).get("value", "")
            
            if service_uri:
                service_id = service_uri.split("/")[-1]
                
                # Discover domain dynamically
                domain = classify_domain_from_service(service_id)
                
                # Discover properties dynamically
                properties = discover_properties_for_service(service_id)
                
                service_info = {
                    "service_id": service_id,
                    "name": service_label,
                    "sparql_endpoint": endpoint,
                    "domain": domain,
                    "properties": properties,
                    "property_count": len(properties)
                }
                
                # Categorize by discovered domain
                domain_key = domain if domain in services_by_domain else "general"
                services_by_domain[domain_key].append(service_info)
    
    return {
        "success": True,
        "services_by_domain": services_by_domain,
        "total_services": sum(len(services) for services in services_by_domain.values()),
        "methodology": "Software 2.0: Dynamic service-first discovery",
        "discovery_method": "service_endpoint_analysis"
    }


def _build_structured_response(
    identifier: str,
    source_db: str,
    results: List[Dict[str, Any]], 
    cache_hit: bool,
    execution_time: int,
    learned_patterns: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Build Claude Code style structured response."""
    
    # Generate workflow suggestions based on discovered domain
    workflow_suggestions = []
    domain_intelligence = []
    
    if learned_patterns:
        for pattern in learned_patterns:
            domain = pattern.get("domain", "general")
            if domain == "biology":
                workflow_suggestions.extend([
                    "cl_resolve <protein_id> --to-db pdb  # 3D structure",
                    "cl_resolve <protein_id> --to-db ensembl  # genomic context"
                ])
                domain_intelligence.append("Biology domain: Focus on protein interactions and pathways")
            elif domain == "chemistry":
                workflow_suggestions.extend([
                    "cl_resolve <compound_id> --to-db chembl  # bioactivity",
                    "cl_resolve <compound_id> --to-db pubchem  # properties"
                ])
                domain_intelligence.append("Chemistry domain: Focus on structure-activity relationships")
    
    return {
        "success": True,
        "data": {
            "identifier": identifier,
            "source_db": source_db,
            "target_db": "wikidata",
            "results": results,
            "count": len(results)
        },
        "metadata": {
            "cache_hit": cache_hit,
            "execution_time_ms": execution_time,
            "discovery_method": "cache_aware_dynamic" if learned_patterns else "standard_resolution",
            "patterns_learned": len(learned_patterns)
        },
        "suggestions": {
            "next_tools": workflow_suggestions[:3],
            "workflow_patterns": [f"{source_db}: Dynamic discovery enabled"],
            "cache_status": "pattern_cached" if learned_patterns else "using_cached_pattern" if cache_hit else "pattern_discovered"
        },
        "claude_guidance": {
            "domain_intelligence": domain_intelligence,
            "learned_patterns": [f"Cached {p['name']} for faster future access" for p in learned_patterns],
            "discovery_insights": [f"System learned {len(learned_patterns)} new patterns"] if learned_patterns else ["Using cached patterns for fast resolution"],
            "performance_note": f"{'10x faster due to caching' if cache_hit else 'Pattern cached for next time'}"
        }
    }


if __name__ == "__main__":
    resolve()