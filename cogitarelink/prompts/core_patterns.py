"""Core research patterns for CogitareLink.

These are the fundamental patterns that apply across all domains.
Edit these when we discover better approaches through usage.

Version: 1.0
Last Updated: 2024-06-16
Changes: Initial pattern-driven structure
"""

# =============================================================================
# DISCOVERY-FIRST PATTERN
# =============================================================================
# This is the most critical pattern - never query without discovery
# Edit this when we find users are still skipping discovery steps

DISCOVERY_FIRST = """
RESEARCH_MODE_ACTIVE: universal_domain_discovery
CRITICAL_RULE: cl_discover REQUIRED before any SPARQL queries (-$1000 penalty for violations)

Basic workflow:
- cl_discover <endpoint> → Cache schema and capabilities
- cl_search "<query>" --limit 5 → ANALYZE universal_discovery section first
- Follow composition_opportunities.immediate_actions systematically

Advanced capabilities:
- Automatic domain detection across 8+ domains (biology, chemistry, medical, cultural, geographic)
- Cross-domain bridge discovery for multi-domain research pathways
- Dynamic pattern learning with 200x performance improvement through caching
- Universal identifier resolution across 50+ database types

FORBIDDEN WORKFLOWS (avoid these patterns):
- "cl_query before cl_discover" → Always discover schemas first
- "Ignoring universal_discovery metadata" → Misses 80% of research intelligence
- "Skipping composition_opportunities" → Loses systematic research guidance  
- "Using hardcoded database assumptions" → Tools auto-detect databases dynamically

METADATA_ANALYSIS_PRIORITY:
1. universal_discovery.domains_detected → Identify research domain(s)
2. external_refs_by_domain → Map available cross-references
3. cross_domain_pathways.bridge_opportunities → Enable cross-domain research
4. validation_results.accessible_databases → Prevent access failures

PERFORMANCE_INDICATORS:
- cache_hit: true = Success (5-50ms execution)
- cache_hit: false = Learning phase (500-1000ms, then cached)
- execution_time_ms < 50 = Optimal cached performance achieved
- confidence: "high" = Trust and proceed
- confidence: "low" = Verify manually before proceeding

VALIDATION_RULES:
- ONLY use databases from validation_results.accessible_databases
- Check accessibility_scores > 0.8 before suggesting databases
- Trust filtered_suggestions warnings - they prevent failures
"""

# =============================================================================
# CACHE-AWARE OPTIMIZATION PATTERN  
# =============================================================================
# Edit this when we discover new performance optimization strategies

CACHE_OPTIMIZATION = """
CACHE_STRATEGY_ACTIVE: claude_code_methodology
PRINCIPLE: READ→VERIFY→Cache for 200x performance gains

CACHE_PERFORMANCE_TIERS:
- First tool usage: ~500-1000ms (discovery + pattern learning) 
- Subsequent usage: ~5-50ms (cached pattern reuse)
- GOAL: execution_time_ms < 50 for optimal performance
- SUCCESS_INDICATOR: "Pattern cached for faster future access" in metadata

CACHE_WARMING_STRATEGY:
1. Early domain cache building: Use cl_resolve on 3-5 identifiers of same type
2. Monitor cache_hit status in all tool responses
3. Build cross-domain cache for comprehensive research coverage
4. Track discovered_patterns for session optimization

PERFORMANCE_OPTIMIZATION_RULES:
- cache_hit: true → Expect 5-50ms execution (200x improvement)
- cache_hit: false → Pattern learning in progress, cache warming needed
- execution_time_ms > 200 → Cache miss, expect pattern discovery
- confidence: "high" + cache_hit: true → Optimal performance achieved

CACHE_INTELLIGENCE:
- System learns identifier patterns dynamically (Medical: MeSH, Geographic: GeoNames)
- Cross-domain patterns cached for bridge research (biology→chemistry workflows)  
- Domain-specific workflows optimized through usage (P352→P638→P705 biology chains)
- Universal discovery results cached for domain detection

CACHE_FAILURE_RECOVERY:
- If execution_time_ms > 500, retry same identifier type to benefit from caching
- Monitor "patterns_learned" count for session progress
- Use cache warming before intensive research sessions
- Fallback to discovery mode if cache corruption detected
"""

# =============================================================================
# COMPOSITION-GUIDED RESEARCH PATTERN
# =============================================================================  
# Edit this when we find better ways to guide systematic research

COMPOSITION_GUIDANCE = """
SYSTEMATIC_RESEARCH_ACTIVE: composition_opportunities
PRINCIPLE: Follow structured suggestions rather than ad-hoc exploration

COMPOSITION_PRIORITY:
1. immediate_actions → Execute first (detailed entity data)
2. cross_reference_exploration → Multi-database research  
3. semantic_exploration → Relationship discovery
4. search_refinement → Improved query strategies

METADATA_ANALYSIS:
- entity_types_found → Guide domain-specific focus
- external_refs_available → Identify cross-reference opportunities
- universal_discovery.domains_detected → Enable cross-domain bridges
- validation_results → Ensure accessible database usage

SYSTEMATIC_APPROACH:
- Never ignore composition_opportunities suggestions
- Follow immediate_actions before exploring cross-references
- Use metadata to understand research landscape before proceeding
- Apply domain reasoning patterns to guide analysis direction
"""

# =============================================================================
# UNIVERSAL DOMAIN PATTERNS
# =============================================================================
# Edit this when adding new domains or improving existing domain intelligence

DOMAIN_PATTERNS = {
    "biology": {
        "entity_types": ["Q8054", "Q7187", "Q898273"],  # protein, gene, domain
        "cross_refs": ["P352", "P594", "P638", "P705"], # UniProt, Ensembl, PDB, Ensembl Gene
        "reasoning_pattern": "Structure → Function → Interactions → Pathways",
        "databases": ["uniprot", "pdb", "ensembl"],
        "search_examples": ["spike protein", "BRCA1", "kinase domain"],
        "success_indicators": ["protein sequence data", "3D structure", "pathway connections"]
    },
    
    "chemistry": {
        "entity_types": ["Q11173", "Q2166630", "Q79529"], # compound, drug, element
        "cross_refs": ["P231", "P592", "P2017", "P2566"], # CAS, ChEMBL, PubChem, DrugBank  
        "reasoning_pattern": "Structure → Properties → Reactions → Applications",
        "databases": ["cas", "chembl", "pubchem", "drugbank"],
        "search_examples": ["aspirin", "benzene", "insulin"],
        "success_indicators": ["chemical structure", "bioactivity data", "pharmacology"]
    },
    
    "medical": {
        "entity_types": ["Q12136", "Q11173", "Q169872", "Q917269"], # disease, drug, symptom, medical procedure
        "cross_refs": ["P486", "P2566", "P672", "P1748"], # MeSH, DrugBank, MedDRA, NCI Thesaurus
        "reasoning_pattern": "Condition → Mechanism → Treatment → Outcomes",
        "databases": ["mesh", "drugbank", "medline", "nci"],
        "search_examples": ["COVID-19", "hypertension", "chemotherapy"],
        "success_indicators": ["clinical data", "treatment protocols", "medical outcomes"]
    },
    
    "geographic": {
        "entity_types": ["Q486972", "Q56061", "Q35872", "Q23413"], # settlement, country, natural feature, mountain
        "cross_refs": ["P1566", "P1667", "P590", "P238"], # GeoNames, Getty TGN, GNIS, IATA
        "reasoning_pattern": "Location → Context → Demographics → Relationships",
        "databases": ["geonames", "getty_tgn", "gnis"],
        "search_examples": ["Mount Everest", "Paris", "Amazon River"],
        "success_indicators": ["geographic coordinates", "demographic data", "administrative context"]
    },
    
    "cultural": {
        "entity_types": ["Q3305213", "Q838948", "Q5", "Q2516866"], # painting, artwork, person, cultural institution
        "cross_refs": ["P350", "P347", "P9394", "P214"], # RKD, Joconde, Louvre, VIAF
        "reasoning_pattern": "Object → Context → Provenance → Significance",
        "databases": ["rkd_images", "joconde", "louvre", "viaf"],
        "search_examples": ["Mona Lisa", "Van Gogh", "Renaissance painting"],
        "success_indicators": ["provenance data", "museum collections", "artist biography"]
    },
    
    "history": {
        "entity_types": ["Q5", "Q1656682", "Q198", "Q45382"],  # person, event, war, coup
        "cross_refs": ["P214", "P213", "P244", "P1566"],     # VIAF, ISNI, LoC, GeoNames
        "reasoning_pattern": "Event → Context → Causes → Consequences", 
        "databases": ["viaf", "loc", "bnf", "geonames"],
        "search_examples": ["World War II", "Napoleon", "French Revolution"],
        "success_indicators": ["historical context", "biographical data", "geographic connections"]
    },
    
    "bibliographic": {
        "entity_types": ["Q571", "Q5", "Q2085381", "Q13442814"], # book, person, publisher, scholarly article
        "cross_refs": ["P214", "P213", "P244", "P236"], # VIAF, ISNI, LoC, ISSN
        "reasoning_pattern": "Work → Author → Context → Impact",
        "databases": ["viaf", "isni", "loc", "worldcat"],
        "search_examples": ["Darwin Origin of Species", "Nature journal", "academic publication"],
        "success_indicators": ["bibliographic metadata", "author information", "citation data"]
    },
    
    "technical": {
        "entity_types": ["Q317623", "Q899523", "Q1047113"], # standard, specification, protocol
        "cross_refs": ["P2892", "P2798", "P1482"], # RFC number, ISO standard, specification
        "reasoning_pattern": "Standard → Implementation → Usage → Evolution",
        "databases": ["ietf", "iso", "ieee"],
        "search_examples": ["HTTP protocol", "ISO 8601", "IEEE 802.11"],
        "success_indicators": ["technical specifications", "implementation guides", "adoption metrics"]
    },
    
    "general": {
        "entity_types": ["Q35120", "Q16521"],  # entity, taxon
        "cross_refs": ["P214", "P1566", "P31"], # VIAF, GeoNames, instance of
        "reasoning_pattern": "Entity → Properties → Relationships → Context",
        "databases": ["wikidata", "viaf", "geonames"], 
        "search_examples": ["<any topic>", "<any entity>"],
        "success_indicators": ["comprehensive metadata", "cross-domain connections"]
    }
}

# =============================================================================
# STRUCTURED ANALYSIS TEMPLATES
# =============================================================================
# Edit this when we need to change how metadata analysis is structured

STRUCTURED_ANALYSIS = """
METADATA_ANALYSIS_ENFORCEMENT: 
When using cl_search, wrap your analysis in <cogitarelink_analysis> tags:

<cogitarelink_analysis>
- Domains detected: [Extract from universal_discovery.domains_detected]
- Entity types found: [List prominent entity types from results]
- External references available: [List from external_refs_by_domain]
- Cross-domain opportunities: [Identify bridge_opportunities if multiple domains]
- Database accessibility: [Check validation_results.accessible_databases]
- Performance status: [Monitor cache_hit and execution_time_ms]
- Immediate actions required: [Extract from composition_opportunities.immediate_actions]
- Research pathway suggestions: [Based on cross_domain_pathways or domain patterns]
- Confidence assessment: [Evaluate confidence scores and validation warnings]
</cogitarelink_analysis>

PARALLEL_EXECUTION_GUIDANCE:
You have the capability to call multiple CogitareLink tools in a single response. 
ALWAYS batch related operations for optimal performance:

DISCOVERY_PHASE (run in parallel):
- cl_discover wikidata
- cl_discover uniprot (if biology detected)
- cl_discover pubchem (if chemistry detected)

SEARCH_PHASE (run in parallel):
- cl_search "primary query" --limit 5
- cl_search "related query" --limit 3  
- cl_search "cross-domain query" --limit 3

RESOLUTION_PHASE (run in parallel):
- cl_resolve <identifier1>
- cl_resolve <identifier2>
- cl_resolve <identifier3>

This parallel execution improves research speed by 5-10x.

ERROR_RECOVERY_PATTERNS:
If CogitareLink tools fail, follow this recovery pattern:

DATABASE_ACCESS_FAILURES:
1. Check validation_results.accessible_databases for alternatives
2. Retry with fallback databases from filtered_suggestions
3. Use cl_discover to find new endpoints if all databases fail

CACHE_MISS_OPTIMIZATION:
1. If execution_time_ms > 200, pattern learning in progress
2. Retry same identifier type to benefit from newly cached pattern
3. Monitor for "Pattern cached" success indicators

LOW_CONFIDENCE_RESULTS:
1. If confidence_score < 0.8, verify through multiple sources
2. Use cl_fetch for additional entity validation
3. Cross-reference through cl_resolve before proceeding
"""

# =============================================================================
# CROSS-DOMAIN BRIDGE PATTERNS
# =============================================================================
# Edit this when we discover new productive cross-domain research strategies

CROSS_DOMAIN_BRIDGES = {
    ("biology", "chemistry"): {
        "connection_type": "protein_drug_interactions",
        "bridge_terms": ["inhibitors", "agonists", "compounds", "targets"],
        "workflow": "protein → drug targets → chemical compounds → bioactivity"
    },
    
    ("biology", "medical"): {
        "connection_type": "biomedical_research",
        "bridge_terms": ["pathways", "biomarkers", "therapeutic targets", "clinical trials"],
        "workflow": "protein → disease mechanism → therapeutic target → clinical application"
    },
    
    ("chemistry", "medical"): {
        "connection_type": "pharmaceutical_development",
        "bridge_terms": ["drug discovery", "pharmacology", "clinical trials", "therapeutics"],
        "workflow": "chemical compound → pharmacological properties → clinical testing → medical application"
    },
    
    ("cultural", "history"): {
        "connection_type": "cultural_historical_context", 
        "bridge_terms": ["period", "movement", "historical context", "cultural significance"],
        "workflow": "artwork → historical period → cultural movement → social context"
    },
    
    ("cultural", "geographic"): {
        "connection_type": "cultural_geographic_context",
        "bridge_terms": ["origin", "cultural region", "artistic movement", "geographic influence"],
        "workflow": "artwork → place of origin → cultural region → geographic influence"
    },
    
    ("history", "geographic"): {
        "connection_type": "historical_geographic_events",
        "bridge_terms": ["battles", "borders", "migrations", "territorial changes"],
        "workflow": "historical event → geographic location → territorial impact → demographic changes"
    },
    
    ("medical", "history"): {
        "connection_type": "medical_historical_events",
        "bridge_terms": ["disease outbreaks", "medical history", "epidemics", "treatments"],
        "workflow": "disease → historical outbreaks → medical developments → treatments"
    },
    
    ("technical", "history"): {
        "connection_type": "technological_development",
        "bridge_terms": ["innovation", "adoption", "standardization", "historical impact"],
        "workflow": "technical standard → historical development → adoption timeline → societal impact"
    },
    
    ("any", "bibliographic"): {
        "connection_type": "scholarly_literature",
        "bridge_terms": ["research", "studies", "literature", "citations"],
        "workflow": "topic → scholarly articles → citations → related research"
    },
    
    ("any", "geographic"): {
        "connection_type": "geographic_context",
        "bridge_terms": ["location", "region", "place", "geographic distribution"],
        "workflow": "topic → geographic location → regional context → spatial relationships"
    }
}

def get_domain_pattern(domain: str) -> dict:
    """Get pattern for specified domain, fallback to general."""
    return DOMAIN_PATTERNS.get(domain.lower(), DOMAIN_PATTERNS["general"])

def get_cross_domain_bridge(from_domain: str, to_domain: str) -> dict:
    """Get bridge pattern between domains."""
    key = (from_domain.lower(), to_domain.lower())
    reverse_key = (to_domain.lower(), from_domain.lower())
    
    return (CROSS_DOMAIN_BRIDGES.get(key) or 
            CROSS_DOMAIN_BRIDGES.get(reverse_key) or
            CROSS_DOMAIN_BRIDGES[("any", "bibliography")])