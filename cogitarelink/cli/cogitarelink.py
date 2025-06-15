"""cogitarelink: Research agent entry point for Claude Code integration.

Transforms Claude Code into a semantic research assistant through instruction enhancement 
and parallel session management.
"""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any

import click

from ..core.debug import get_logger

log = get_logger("cogitarelink")


class ResearchSession:
    """Manages research session state in .cogitarelink/session.json"""
    
    def __init__(self, session_dir: Optional[Path] = None):
        self.session_dir = session_dir or Path.cwd() / ".cogitarelink"
        self.session_file = self.session_dir / "session.json"
        self.instructions_dir = Path(__file__).parent.parent / "instructions"
        
    def ensure_session_dir(self) -> None:
        """Create .cogitarelink directory if it doesn't exist."""
        self.session_dir.mkdir(parents=True, exist_ok=True)
        
    def get_claude_session_id(self) -> Optional[str]:
        """Try to get Claude Code's current session ID from .claude/session.json"""
        claude_session_file = Path.cwd() / ".claude" / "session.json"
        if claude_session_file.exists():
            try:
                with open(claude_session_file) as f:
                    claude_session = json.load(f)
                    return claude_session.get("sessionId")
            except Exception as e:
                log.debug(f"Could not read Claude session: {e}")
        return None
        
    def create_session(self, domain: str, goal: Optional[str] = None) -> Dict[str, Any]:
        """Create new research session."""
        self.ensure_session_dir()
        
        session_id = f"cl_research_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"
        claude_session_id = self.get_claude_session_id()
        
        session_data = {
            "sessionId": session_id,
            "claudeSessionId": claude_session_id,
            "originalCwd": str(Path.cwd()),
            "cwd": str(Path.cwd()),
            "researchDomain": domain,
            "researchGoal": goal or f"{domain.title()} research session",
            "createdAt": datetime.now(timezone.utc).isoformat(),
            "lastInteractionTime": datetime.now(timezone.utc).timestamp(),
            "sessionCounter": 1,
            "toolUsage": {
                "cl_discover": 0,
                "cl_search": 0,
                "cl_fetch": 0,
                "cl_query": 0,
                "cl_resolve": 0
            },
            "discoveredEndpoints": [],
            "activeInstructions": [
                "discovery_first",
                "cache_aware_workflow",
                f"{domain}_workflow" if domain in ["biology", "chemistry", "cultural", "medical", "geographic", "bibliographic"] else "cross_domain_workflow"
            ],
            "researchProgress": {
                "entitiesDiscovered": 0,
                "relationshipsFound": 0,
                "workflowsCompleted": 0
            }
        }
        
        # Save session
        with open(self.session_file, 'w') as f:
            json.dump(session_data, f, indent=2)
            
        return session_data
        
    def load_session(self) -> Optional[Dict[str, Any]]:
        """Load current research session."""
        if not self.session_file.exists():
            return None
            
        try:
            with open(self.session_file) as f:
                return json.load(f)
        except Exception as e:
            log.error(f"Failed to load session: {e}")
            return None
            
    def update_session(self, updates: Dict[str, Any]) -> None:
        """Update session with new data."""
        session = self.load_session()
        if session:
            session.update(updates)
            session["lastInteractionTime"] = datetime.now(timezone.utc).timestamp()
            session["sessionCounter"] += 1
            
            with open(self.session_file, 'w') as f:
                json.dump(session, f, indent=2)


class InstructionIndex:
    """Manages research instruction templates."""
    
    def __init__(self, instructions_dir: Path):
        self.instructions_dir = instructions_dir
        
    def get_instruction(self, pattern: str) -> Optional[str]:
        """Get instruction content by pattern name."""
        instruction_file = self.instructions_dir / f"{pattern}.md"
        
        if instruction_file.exists():
            return instruction_file.read_text()
        
        # Return built-in instructions if file doesn't exist
        return self._get_builtin_instruction(pattern)
        
    def _get_builtin_instruction(self, pattern: str) -> Optional[str]:
        """Built-in instruction templates."""
        instructions = {
            "discovery_first": """
🔍 **UNIVERSAL DISCOVERY-FIRST RESEARCH PATTERN**

Claude Code Enhanced Instructions:
- ALWAYS use `cl_discover <endpoint>` before querying any SPARQL endpoint
- Cache endpoint schemas to avoid repeated discovery calls  
- Use discovery results to understand available prefixes and patterns
- Apply discovery-first guardrails: "Never query without schema understanding"

🚀 **NEW: CACHE-AWARE DYNAMIC DISCOVERY**
CogitareLink now implements Claude Code's READ→VERIFY→Cache methodology for external identifiers:

**Cache-First External Identifier Resolution:**
```bash
# These commands now use cache-aware dynamic discovery
cl_resolve P04637 --from-db uniprot --to-db wikidata  # 10x faster with caching
cl_resolve 7001393 --from-db getty_tgn              # Auto-detects Getty TGN format
cl_resolve Q283350 --to-db uniprot                  # Discovers UniProt patterns dynamically
```

**🧠 Claude Code Pattern Integration:**
1. **READ**: Uses `DESCRIBE wd:P1667` to get ALL properties (not hardcoded)
2. **VERIFY**: Semantic analysis extracts meaningful properties dynamically
3. **CACHE**: Stores discovered patterns with confidence metadata

**⚡ Performance Characteristics:**
- **Cache Hit**: <10ms response time, "10x faster due to caching"
- **Cache Miss**: ~1000ms for discovery, then cached for 24 hours
- **Auto-Detection**: 15+ external identifier formats recognized automatically

**🌐 SERVICE-FIRST SPARQL ENDPOINT DISCOVERY:**
The system now discovers ALL services with SPARQL endpoints automatically (Software 2.0):

```python
# Discover all 72+ services with SPARQL endpoints dynamically
from cogitarelink.cli.cl_resolve import discover_all_services_with_endpoints
services = discover_all_services_with_endpoints()

# Services automatically categorized by domain:
# - Cultural: performing-arts.ch, Europeana, RKDimages
# - Bibliographic: BnF authorities, Web NDL, VIAF, ISNI
# - Geographic: Getty TGN, GeoNames
# - Scientific: MeSH, ChEMBL, SIMBAD
# - Technical: UNESCO Thesaurus, AGROVOC
```

**Zero Hardcoding**: No predefined lists of "special identifiers" - the system discovers:
- **Getty TGN**: `http://vocab.getty.edu/sparql` (geographic domain)
- **UniProt**: `https://sparql.uniprot.org/sparql` (biology domain)
- **MeSH**: `http://id.nlm.nih.gov/mesh/sparql` (medical domain)
- **BnF**: `https://data.bnf.fr/sparql/` (bibliographic domain)
- **And 68+ more automatically...**

**📊 Structured Responses with Claude Guidance:**
All discovery functions return Claude Code style responses:
```json
{
  "success": true,
  "data": { "results": [...] },
  "metadata": {
    "cache_hit": true,
    "execution_time_ms": 5,
    "discovery_method": "cached_pattern"
  },
  "suggestions": {
    "next_tools": ["cl_resolve <id> --to-db pdb"],
    "workflow_patterns": ["biology: Dynamic discovery enabled"]
  },
  "claude_guidance": {
    "domain_intelligence": ["Biology domain: Focus on protein interactions"],
    "performance_note": "10x faster due to caching"
  }
}
```

**NEW: Universal Cross-Domain Intelligence**
CogitareLink now supports 15+ domains with universal external identifier discovery:

📊 **Universal External Identifier Patterns:**
**Biology Domain:**
   - P352 (UniProt) → Protein sequences, structures, functions
   - P638 (PDB) → 3D protein structures, crystallography data
   - P705 (Ensembl) → Genomic locations, expression data

**Chemistry Domain:**
   - P231 (CAS) → Chemical identity, registry numbers
   - P662 (PubChem) → Chemical structures, properties
   - P592 (ChEMBL) → Bioactivity, drug-target data

**Cultural/Art Domain:**
   - P350 (RKD Images) → Art image database references
   - P347 (Joconde) → French cultural heritage objects
   - P9394 (Louvre) → Louvre Museum collection items

**Medical Domain:**
   - P486 (MeSH) → Medical subject headings
   - P2566 (DrugBank) → Pharmaceutical drug data

**Geographic Domain:**
   - P1566 (GeoNames) → Geographic location data

**Bibliographic Domain:**
   - P214 (VIAF) → Authority files for persons/organizations
   - P213 (ISNI) → International name identifiers
   - P244 (Library of Congress) → Authority control

🌐 **Cross-Domain Research Strategies:**

1. **Multi-Domain Entity Analysis**: 
   ```bash
   cl_search "Leonardo da Vinci" --limit 5
   ```
   **Expect cross-domain identifiers:**
   - P214 (VIAF) → Biographical/bibliographic data
   - P350 (RKD) → Artwork references  
   - P1566 (GeoNames) → Associated locations

2. **Domain-Specific Workflow Selection**:
   - **Biology research** → Focus on P352, P638, P705 cross-references
   - **Chemistry research** → Focus on P231, P662, P592 cross-references
   - **Cultural research** → Focus on P350, P347, P9394 cross-references
   - **Medical research** → Focus on P486, P2566 cross-references

3. **Cross-Domain Connection Discovery**:
   - **Biology ↔ Chemistry**: Protein targets → Drug compounds
   - **Cultural ↔ Geographic**: Artwork provenance → Location history
   - **Any Domain ↔ Bibliographic**: Find scholarly literature

Example Universal Workflow:
1. `cl_search "<entity>" --limit 5` → Analyze all external identifiers
2. Identify domain(s) from external identifier patterns
3. Use domain-appropriate `cl_resolve` strategies
4. Follow cross-domain connections for comprehensive research

This enables truly universal, cross-domain research workflows.
""",
            
            "biology_workflow": """
🧬 **ENHANCED BIOLOGY RESEARCH WORKFLOW PATTERNS**

**Metadata-Driven Protein Research Chain-of-Thought:**

1. **Smart Entity Discovery**: 
   ```bash
   cl_search "spike protein" --limit 5
   ```
   **Analyze the metadata response:**
   - Check `entity_types_found` for Q8054 (protein), Q7187 (gene), Q898273 (protein domain)
   - Examine `external_refs_available` for cross-database opportunities:
     * P352 (UniProt) → Protein sequence, structure, function
     * P594 (Ensembl) → Genomic location, expression data
     * P638 (PDB) → 3D structure data
     * P637 (RefSeq) → Reference sequences

2. **Cache-Aware Cross-Database Navigation**:
   **Based on discovered external references (now with cache-aware performance):**
   - If P352 found → `cl_resolve Q22329850 --to-db uniprot` (protein details, cached patterns)
   - If P594 found → `cl_resolve Q22329850 --to-db ensembl` (genomic context, 10x faster)  
   - If P638 found → `cl_resolve Q22329850 --to-db pdb` (structural data, auto-detection)
   
   **🚀 NEW: Dynamic External Identifier Discovery**
   ```bash
   # System now auto-detects and caches ANY external identifier format
   cl_resolve P04637                    # Auto-detects UniProt format
   cl_resolve ENSG00000141510          # Auto-detects Ensembl format  
   cl_resolve 1A0O                     # Auto-detects PDB format
   ```
   
   **Cache Intelligence**: Each resolution includes performance metadata:
   - Cache hits: ~5ms response time
   - Discovery metadata shows confidence levels
   - SPARQL endpoints discovered and cached automatically

3. **Composition-Guided Research Flow**:
   **Follow composition_opportunities from cl_search:**
   - Execute `immediate_actions` for detailed entity data
   - Use `cross_reference_exploration` for multi-database research
   - Apply `semantic_exploration` for relationship discovery

4. **Domain-Specific Entity Type Interpretation**:
   - **Q8054 (Protein)** → Focus on:
     * Protein-protein interactions
     * Enzymatic functions and pathways  
     * Structural domains and binding sites
     * Disease associations
   
   - **Q7187 (Gene)** → Focus on:
     * Expression patterns and regulation
     * Genetic variants and mutations
     * Chromosomal location and context
     * Phenotypic associations

   - **Q37748 (Chromosome)** → Focus on:
     * Genomic organization
     * Gene density and distribution
     * Chromosomal abnormalities

**Enhanced Biological Reasoning Patterns:**
- **Metadata-Driven**: Use entity_types_found to guide research strategy
- **Cross-Reference Optimized**: Leverage external_refs_available for comprehensive data
- **Composition-Aware**: Follow suggested workflows from composition_opportunities
- **Session-Contextual**: Adapt strategy based on research_domain and research_goal

**Example Intelligent Workflow:**
```bash
# Step 1: Enhanced discovery
cl_search "SARS-CoV-2 spike protein" --limit 3

# Step 2: Analyze metadata and follow suggestions
# If metadata shows Q8054 + P352 + P638:
cl_fetch Q22329850  # From immediate_actions
cl_resolve Q22329850 --to-db uniprot  # From cross_reference_exploration  
cl_search "ACE2 receptor" --endpoint uniprot  # From cross_reference_exploration

# Step 3: Pathway and interaction analysis
cl_search "spike protein binding" --endpoint wikipathways
cl_query "SELECT ?pathway WHERE { ?protein wdt:P2806 ?pathway }"  # From semantic_exploration
```

This leverages enhanced cl_search intelligence for efficient, comprehensive biological research.
""",
            
            "cross_domain_workflow": """
🌐 **UNIVERSAL CROSS-DOMAIN RESEARCH PATTERNS**

**Multi-Domain Entity Research Strategy:**

1. **Universal Entity Discovery**:
   ```bash
   cl_search "<entity_name>" --limit 5
   ```
   **Analyze cross-domain metadata:**
   - Identify all external identifier patterns (P352, P231, P350, P214, etc.)
   - Determine primary research domain(s) from identifier coverage
   - Plan cross-domain exploration pathways

2. **Domain-Adaptive Research Flows**:

   **🧬 Biology-Centric Entities** (P352, P638, P705 present):
   ```bash
   # Protein/gene research pathway
   cl_resolve <entity> --to-db uniprot    # Sequence/function data
   cl_resolve <entity> --to-db pdb        # Structural data
   cl_resolve <entity> --to-db ensembl    # Genomic context
   
   # Cross to chemistry domain
   cl_search "<protein> inhibitors" --limit 3  # Find drug compounds
   ```

   **⚗️ Chemistry-Centric Entities** (P231, P662, P592 present):
   ```bash
   # Chemical compound research pathway  
   cl_resolve <entity> --to-db cas        # Chemical identity
   cl_resolve <entity> --to-db pubchem    # Structure/properties
   cl_resolve <entity> --to-db chembl     # Bioactivity data
   
   # Cross to biology domain
   cl_search "<compound> targets" --limit 3    # Find protein targets
   ```

   **🎨 Cultural-Centric Entities** (P350, P347, P9394 present):
   ```bash
   # Artwork/cultural object research pathway
   cl_resolve <entity> --to-db rkd_images # Image database
   cl_resolve <entity> --to-db joconde    # Cultural heritage
   cl_resolve <entity> --to-db louvre     # Museum collection
   
   # Cross to geographic domain
   cl_search "<artwork> provenance" --limit 3  # Find locations
   ```

   **🏥 Medical-Centric Entities** (P486, P2566 present):
   ```bash
   # Medical/pharmaceutical research pathway
   cl_resolve <entity> --to-db mesh       # Medical classifications
   cl_resolve <entity> --to-db drugbank   # Drug information
   
   # Cross to biology domain
   cl_search "<drug> mechanism" --limit 3      # Find biological targets
   ```

3. **Cross-Domain Connection Strategies**:

   **Biology → Chemistry Bridge**:
   - Protein entities → Search for "inhibitors", "agonists", "compounds"
   - Gene entities → Search for "modulators", "drugs targeting"
   
   **Chemistry → Biology Bridge**:
   - Chemical compounds → Search for "targets", "binding proteins"
   - Drugs → Search for "mechanism of action", "pathways"

   **Cultural → Geographic Bridge**:
   - Artworks → Search for "created in", "exhibited at", "provenance"
   - Artists → Search for "born in", "worked in", "schools"

   **Any Domain → Bibliographic Bridge**:
   - Add "research", "studies", "literature" to searches
   - Use P214 (VIAF), P213 (ISNI) for authority control

4. **Multi-Domain Validation Strategy**:
   ```bash
   # Always validate cross-references before following them
   # The system automatically checks database accessibility
   # Only suggests accessible pathways with confidence scoring
   ```

5. **Domain-Agnostic Research Patterns**:
   - **Chronological research**: Search by time periods, historical context
   - **Geographic research**: Search by locations, regions, spatial relationships  
   - **Bibliographic research**: Find scholarly literature across all domains
   - **Institutional research**: Museums, universities, organizations

**Example Multi-Domain Research Session**:
```bash
# Starting with Leonardo da Vinci (cultural + biographical)
cl_search "Leonardo da Vinci" --limit 3

# Follow cultural identifiers
cl_resolve Q762 --to-db rkd_images     # Artwork database
cl_resolve Q762 --to-db louvre         # Museum collections

# Follow geographic connections  
cl_search "Leonardo Florence Italy" --limit 3

# Follow bibliographic connections
cl_search "Leonardo da Vinci research studies" --limit 5

# Cross-domain exploration
cl_search "Renaissance art Florence" --limit 5  # Broader cultural context
```

This enables seamless research across any combination of domains with intelligent pathway discovery.
""",
            
            "chemistry_workflow": """
⚗️ **ENHANCED CHEMISTRY RESEARCH WORKFLOW PATTERNS**

**Metadata-Driven Chemical Compound Analysis:**

1. **Smart Compound Discovery**:
   ```bash
   cl_search "aspirin" --limit 5
   ```
   **Analyze the metadata response:**
   - Check `entity_types_found` for Q11173 (chemical compound), Q12136 (disease), Q2166630 (pharmaceutical drug)
   - Examine `external_refs_available` for chemical databases:
     * P231 (CAS Registry Number) → Chemical identity and properties
     * P486 (MeSH) → Medical/pharmacological classifications  
     * P592 (ChEMBL) → Bioactivity and target data
     * P2017 (PubChem CID) → Chemical structure and properties
     * P2566 (DrugBank) → Drug information and interactions

2. **Cache-Aware Chemical Database Navigation Strategy**:
   **Based on discovered external references (now with dynamic discovery):**
   - If P231 (CAS) found → `cl_resolve Q12484 --to-db cas` (chemical properties, cached)
   - If P592 (ChEMBL) found → `cl_resolve Q12484 --to-db chembl` (bioactivity, SPARQL endpoint cached)
   - If P2017 (PubChem) found → `cl_resolve Q12484 --to-db pubchem` (structure data, auto-format detection)
   - If P2566 (DrugBank) found → `cl_resolve Q12484 --to-db drugbank` (drug interactions, 10x faster)
   
   **🚀 NEW: Chemical Identifier Auto-Detection**
   ```bash
   # System recognizes chemical formats automatically
   cl_resolve 50-78-2               # Auto-detects CAS Registry Number
   cl_resolve CHEMBL25             # Auto-detects ChEMBL ID
   cl_resolve DB00945              # Auto-detects DrugBank ID
   ```
   
   **Chemical SPARQL Endpoints Discovered:**
   - **ChEMBL**: Bioactivity data endpoint auto-discovered
   - **PubChem**: Chemical structure endpoint cached
   - **DrugBank**: Drug interaction endpoint available

3. **Chemical Entity Type Interpretation**:
   - **Q11173 (Chemical Compound)** → Focus on:
     * Molecular structure and properties
     * Chemical synthesis pathways
     * Reactivity and stability
     * Environmental fate
   
   - **Q2166630 (Pharmaceutical Drug)** → Focus on:
     * Mechanism of action
     * Pharmacokinetics (ADME)
     * Drug targets and pathways
     * Side effects and contraindications
     * Drug-drug interactions
   
   - **Q12136 (Disease)** → Focus on:
     * Disease mechanisms
     * Therapeutic targets
     * Biomarkers
     * Treatment pathways

4. **Composition-Guided Chemical Research**:
   **Follow composition_opportunities from cl_search:**
   - Use `immediate_actions` for detailed molecular data
   - Apply `cross_reference_exploration` for multi-database chemical profiling
   - Leverage `semantic_exploration` for structure-activity relationships

**Enhanced Chemical Reasoning Patterns:**
- **Structure-Property-Activity**: Use entity types to guide SAR analysis
- **Multi-Database Integration**: Leverage external_refs for comprehensive profiling
- **Target-Pathway Mapping**: Follow composition suggestions for mechanism discovery
- **Safety-Efficacy Analysis**: Use metadata to identify toxicity and efficacy data sources

**Example Intelligent Chemical Workflow:**
```bash
# Step 1: Enhanced compound discovery
cl_search "ibuprofen" --limit 3

# Step 2: Analyze metadata and follow suggestions  
# If metadata shows Q2166630 + P231 + P592 + P2566:
cl_fetch Q192156  # From immediate_actions (detailed compound data)
cl_resolve Q192156 --to-db chembl  # From cross_reference_exploration (bioactivity)
cl_resolve Q192156 --to-db drugbank  # From cross_reference_exploration (drug data)

# Step 3: Target and pathway analysis
cl_search "COX-2 inhibitor" --endpoint wikidata  # From search_refinement
cl_query "SELECT ?target WHERE { ?compound wdt:P129 ?target }"  # From semantic_exploration

# Step 4: Safety and interaction analysis
cl_search "ibuprofen interactions" --endpoint drugbank
cl_query "SELECT ?effect WHERE { ?drug wdt:P1050 ?effect }"  # Adverse effects
```

**Chemical Database Strategy by External Reference:**
- **P231 (CAS)**: Authoritative chemical identity, properties, safety data
- **P592 (ChEMBL)**: Bioactivity, target interactions, dose-response data  
- **P2017 (PubChem)**: Structure, physicochemical properties, biological assays
- **P2566 (DrugBank)**: Drug mechanism, pharmacology, interactions, clinical data
- **P486 (MeSH)**: Medical classifications, therapeutic uses, pharmacological actions

This enables comprehensive, metadata-driven chemical and drug research workflows.
""",
            
            "cache_aware_workflow": """
🚀 **CACHE-AWARE DYNAMIC DISCOVERY WORKFLOW**

**Claude Code's READ→VERIFY→Cache Methodology Applied to Scientific Research**

**🧠 Core Cache-Aware Patterns:**

1. **Smart Cache-First Resolution**:
   ```bash
   # Let the system auto-detect formats and use cached patterns
   cl_resolve P04637                    # ✅ Auto-detects UniProt, ~5ms (cached)
   cl_resolve 7001393                   # ✅ Auto-detects Getty TGN, ~5ms (cached)
   cl_resolve CHEMBL25                  # ✅ Auto-detects ChEMBL, ~1000ms (discovery)
   cl_resolve CHEMBL25                  # ✅ Now cached, ~5ms (10x faster!)
   ```

2. **Confidence-Driven Discovery**:
   **System provides confidence metadata for all discoveries:**
   ```json
   "semantic_analysis": {
     "discovery_method": "universal_identifier_system",
     "confidence": "high",
     "semantic_properties_found": true,
     "describe_based": true
   }
   ```
   
   **Use confidence to guide research strategy:**
   - **High confidence**: Trust the discovery, proceed with workflow
   - **Low confidence**: Verify results, consider alternative approaches

3. **Service-First SPARQL Endpoint Intelligence**:
   ```python
   # SOFTWARE 2.0: Discover all services with endpoints automatically
   from cogitarelink.cli.cl_resolve import discover_all_services_with_endpoints
   services = discover_all_services_with_endpoints()
   
   # Returns 72+ services categorized by domain:
   # services["services_by_domain"]["cultural"]     # performing-arts.ch, Europeana
   # services["services_by_domain"]["bibliographic"] # BnF, VIAF, ISNI
   # services["services_by_domain"]["geographic"]   # Getty TGN, GeoNames
   ```
   
   ```bash
   # Individual identifier resolution still works with discovered patterns
   cl_resolve P1667 --format json       # Uses discovered Getty TGN endpoint
   cl_resolve P352 --format json        # Uses discovered UniProt endpoint
   cl_resolve P268 --format json        # Uses discovered BnF endpoint
   ```
   
   **No Hardcoding**: System discovers services, domains, properties, and endpoints automatically

4. **Performance-Aware Research Planning**:
   **Cache hit patterns optimize research workflows:**
   ```bash
   # Fast path: Use cached patterns (5-10ms)
   cl_resolve <known_identifier>
   
   # Discovery path: Learn new patterns (1000ms), then cache for session
   cl_resolve <unknown_identifier>
   
   # Subsequent uses: 10x faster due to caching
   cl_resolve <previously_unknown_identifier>
   ```

5. **Domain Intelligence Guidance**:
   **System provides domain-specific next steps:**
   ```json
   "claude_guidance": {
     "domain_intelligence": ["Biology domain: Focus on protein interactions"],
     "learned_patterns": ["Cached UniProt patterns for faster future access"],
     "performance_note": "10x faster due to caching"
   }
   ```

**🎯 Cache-Aware Research Strategies:**

**Pattern 1: Multi-Identifier Discovery Session**
```bash
# Discovery session: Learn patterns for entire research domain
cl_resolve P04637                    # Learn UniProt patterns
cl_resolve ENSG00000141510          # Learn Ensembl patterns  
cl_resolve 1A0O                     # Learn PDB patterns

# Subsequent research: All cached, ultra-fast resolution
cl_resolve P12345                   # ~5ms (UniProt cached)
cl_resolve ENSG00000123456         # ~5ms (Ensembl cached)
cl_resolve 2ABC                    # ~5ms (PDB cached)
```

**Pattern 2: Cross-Domain Cache Building**
```bash
# Build cache across domains in single session
cl_resolve 50-78-2                 # Chemistry: CAS (learn)
cl_resolve 7001393                 # Geography: Getty TGN (learn)
cl_resolve P214-123456789          # Bibliography: VIAF (learn)

# Now all domains cached for fast cross-domain research
```

**Pattern 3: Service-First Domain Research**
```python
# SOFTWARE 2.0: Discover all services in a domain automatically
services = discover_all_services_with_endpoints()

# Research cultural domain
cultural_services = services["services_by_domain"]["cultural"]
for service in cultural_services:
    print(f"Service: {service['name']}")
    print(f"Endpoint: {service['sparql_endpoint']}")
    print(f"Properties: {service['properties']}")
    
# Research bibliographic domain  
biblio_services = services["services_by_domain"]["bibliographic"]
# Each service includes discovered properties and endpoints
```

**Pattern 4: Cache-Informed Research Planning**
```bash
# Check cache status to plan research efficiency
cl_resolve <identifier> --format json | jq '.metadata.cache_hit'

# If cache_hit: false → First time discovery
# If cache_hit: true → Optimized path available
```

**🔧 Cache Management Best Practices:**

1. **Session Warmup**: Discover patterns for your research domain early
2. **Cache Awareness**: Use structured responses to understand performance
3. **Confidence Checking**: Verify high-confidence vs. low-confidence discoveries
4. **Endpoint Intelligence**: Leverage discovered SPARQL endpoints for direct queries
5. **Domain Building**: Build comprehensive domain caches for ongoing research

**⚡ Performance Characteristics You'll See:**
- **First discovery**: ~1000ms, "discovery_method": "claude_semantic_analysis"
- **Cached access**: ~5ms, "cache_hit": true, "10x faster due to caching"
- **Confidence tracking**: "confidence": "high" for reliable patterns
- **Endpoint discovery**: SPARQL endpoints cached automatically

This transforms external identifier resolution from hardcoded Software 1.0 to intelligent, cache-aware Software 2.0 following Claude Code's proven methodology.
""",
            
            "cultural_workflow": """
🎨 **CULTURAL/ART RESEARCH WORKFLOW PATTERNS**

**Metadata-Driven Cultural Entity Analysis:**

1. **Cultural Entity Discovery**:
   ```bash
   cl_search "Mona Lisa" --limit 5
   ```
   **Analyze cultural metadata:**
   - Check `entity_types_found` for Q3305213 (painting), Q838948 (artwork), Q5 (person)
   - Examine `external_refs_available` for cultural databases:
     * P350 (RKD Images) → Art image database references
     * P347 (Joconde) → French cultural heritage objects  
     * P9394 (Louvre) → Louvre Museum collection items
     * P214 (VIAF) → Authority files for artists/persons
     * P1566 (GeoNames) → Geographic locations

2. **Cultural Database Navigation**:
   ```bash
   # Follow cultural identifiers systematically
   cl_resolve Q12418 --to-db rkd_images  # Art image database
   cl_resolve Q12418 --to-db joconde     # Cultural heritage
   cl_resolve Q12418 --to-db louvre      # Museum collection
   ```

3. **Cross-Domain Cultural Research**:
   ```bash
   # Cultural → Geographic connections
   cl_search "Mona Lisa provenance history" --limit 3
   cl_search "Leonardo Florence workshop" --limit 3
   
   # Cultural → Bibliographic connections  
   cl_search "Mona Lisa art history research" --limit 5
   cl_resolve Q762 --to-db viaf  # Artist authority data
   ```

Cultural research enables provenance tracking, art historical analysis, and cultural heritage exploration.
""",
            
            "medical_workflow": """
🏥 **MEDICAL/PHARMACEUTICAL RESEARCH PATTERNS**

**Medical Entity Research Strategy:**

1. **Medical Entity Discovery**:
   ```bash
   cl_search "aspirin" --limit 5
   ```
   **Analyze medical metadata:**
   - Check for Q2166630 (pharmaceutical drug), Q12136 (disease), Q8054 (protein)
   - Examine external references:
     * P486 (MeSH) → Medical subject headings
     * P2566 (DrugBank) → Pharmaceutical drug data
     * P592 (ChEMBL) → Bioactivity data
     * P231 (CAS) → Chemical identity

2. **Medical Database Navigation**:
   ```bash
   # Follow medical/pharmaceutical pathways
   cl_resolve Q12484 --to-db mesh      # Medical classifications
   cl_resolve Q12484 --to-db drugbank  # Drug information
   cl_resolve Q12484 --to-db chembl    # Bioactivity data
   ```

3. **Cross-Domain Medical Research**:
   ```bash
   # Medical → Biology connections
   cl_search "aspirin mechanism action" --limit 3
   cl_search "COX enzyme inhibition" --limit 3
   
   # Medical → Chemistry connections
   cl_search "salicylic acid derivatives" --limit 3
   ```

Medical research enables drug discovery, mechanism analysis, and therapeutic exploration.
""",
            
            "geographic_workflow": """
🌍 **GEOGRAPHIC RESEARCH WORKFLOW PATTERNS**

**Location-Based Entity Research:**

1. **Geographic Entity Discovery**:
   ```bash
   cl_search "Florence Italy" --limit 5
   ```
   **Analyze geographic metadata:**
   - Check for geographic entity types and administrative divisions
   - Examine external references:
     * P1566 (GeoNames) → Geographic location data
     * P214 (VIAF) → Authority files for places
     * Cultural connections through P350, P347, P9394

2. **Geographic Database Navigation**:
   ```bash
   # Follow geographic identifiers
   cl_resolve Q2044 --to-db geonames  # Geographic data
   
   # Cross-domain geographic research
   cl_search "Florence Renaissance art" --limit 3
   cl_search "Florence scientific history" --limit 3
   ```

Geographic research enables spatial analysis, cultural geography, and location-based discovery.
""",
            
            "bibliographic_workflow": """
📚 **BIBLIOGRAPHIC/AUTHORITY RESEARCH PATTERNS**

**Authority Control and Literature Discovery:**

1. **Bibliographic Entity Discovery**:
   ```bash
   cl_search "Marie Curie" --limit 5
   ```
   **Analyze bibliographic metadata:**
   - Check for Q5 (person), Q36180 (writer), Q901 (scientist)
   - Examine authority control references:
     * P214 (VIAF) → Virtual International Authority File
     * P213 (ISNI) → International Standard Name Identifier
     * P244 (Library of Congress) → Authority control

2. **Authority Database Navigation**:
   ```bash
   # Follow authority control identifiers
   cl_resolve Q7186 --to-db viaf  # Authority data
   cl_resolve Q7186 --to-db loc   # Library of Congress
   
   # Literature and publication research
   cl_search "Marie Curie publications" --limit 5
   cl_search "Nobel Prize physics 1903" --limit 3
   ```

3. **Cross-Domain Bibliographic Research**:
   ```bash
   # Person → Science connections
   cl_search "radioactivity discovery" --limit 3
   cl_search "radium polonium elements" --limit 3
   
   # Person → Geographic connections
   cl_search "Marie Curie Paris laboratory" --limit 3
   ```

Bibliographic research enables scholarly discovery, authority verification, and literature exploration.
""",

            "metadata_interpretation": """
📊 **ENHANCED cl_search METADATA INTERPRETATION GUIDE**

**Understanding Rich Metadata from cl_search Responses:**

## 🔍 Core Metadata Structure Analysis

**1. Discovery Analysis (`metadata.discovery_analysis`)**
```json
{
  "entity_types_found": ["Q8054", "Q11173", "Q37748"],
  "type_distribution": {"Q8054": 3, "Q11173": 1},
  "external_refs_available": {"P352": 4, "P594": 2, "P638": 1},
  "semantic_depth_indicators": {
    "has_type_hierarchy": true,
    "max_hierarchy_depth": 3,
    "relationship_density": 0.7
  }
}
```

**2. Endpoint Context (`metadata.endpoint_context`)**
```json
{
  "search_method_used": "wikidata_api",
  "capabilities_available": ["describe", "sparql", "cross_refs"],
  "related_endpoints": ["uniprot", "ensembl", "pdb"],
  "endpoint_url": "https://query.wikidata.org/sparql"
}
```

**3. Execution Context (`metadata.execution_context`)**
```json
{
  "cache_hit": false,
  "execution_time_ms": 245.3,
  "search_effectiveness": 0.8
}
```

## 🧬 Domain-Specific Entity Type Interpretation

**Biological Entity Types:**
- **Q8054 (Protein)**: Focus on structure, function, interactions, pathways
- **Q7187 (Gene)**: Focus on expression, regulation, variants, phenotypes  
- **Q37748 (Chromosome)**: Focus on genomic organization, gene density
- **Q898273 (Protein domain)**: Focus on structural motifs, binding sites
- **Q7239 (Organism)**: Focus on taxonomy, ecology, genomics

**Chemical Entity Types:**
- **Q11173 (Chemical compound)**: Focus on structure, properties, reactions
- **Q2166630 (Pharmaceutical drug)**: Focus on mechanism, pharmacology, interactions
- **Q12136 (Disease)**: Focus on pathophysiology, biomarkers, treatments
- **Q79529 (Chemical element)**: Focus on properties, compounds, applications

## 🔗 External Reference Strategy Matrix

**Protein Research (P352 UniProt + P638 PDB + P594 Ensembl):**
```bash
# Comprehensive protein analysis
cl_resolve Q22329850 --to-db uniprot    # Sequence, function, domains
cl_resolve Q22329850 --to-db pdb        # 3D structure, binding sites  
cl_resolve Q22329850 --to-db ensembl    # Genomic context, expression
```

**Chemical Research (P231 CAS + P592 ChEMBL + P2017 PubChem):**
```bash
# Comprehensive compound analysis
cl_resolve Q192156 --to-db cas       # Chemical identity, safety
cl_resolve Q192156 --to-db chembl    # Bioactivity, targets
cl_resolve Q192156 --to-db pubchem   # Structure, properties
```

**Medical Research (P486 MeSH + P2566 DrugBank + P493 ICD):**
```bash
# Comprehensive medical analysis
cl_resolve Q12484 --to-db mesh      # Medical classifications
cl_resolve Q12484 --to-db drugbank  # Drug interactions, pharmacology
cl_resolve Q12484 --to-db icd       # Disease classifications
```

## 🎯 Composition Opportunities Decision Matrix

**immediate_actions (Always execute first):**
- High priority: Fetch detailed data for top results
- Use when: You need comprehensive entity information
- Example: `cl_fetch Q22329850  # Get detailed properties`

**cross_reference_exploration (Use when external_refs_available > 0):**
- High priority: When P352, P594, P638, P231, P592 found
- Use when: Multi-database research needed
- Example: `cl_resolve Q22329850 --to-db uniprot`

**semantic_exploration (Use when has_type_hierarchy = true):**
- Medium priority: When relationship_density > 0.5
- Use when: Need to understand entity relationships
- Example: `cl_query "SELECT ?super WHERE { wd:Q8054 wdt:P279* ?super }"`

**search_refinement (Use when search_effectiveness < 0.7):**
- High priority: When initial search was not effective
- Use when: Need better or more specific results
- Example: `cl_search "SARS-CoV-2 spike protein"  # More specific`

## 📈 Session Context Integration

**research_domain Adaptation:**
- **biology**: Prioritize protein interactions, pathways, genomics
- **chemistry**: Prioritize structure-activity, synthesis, properties
- **general**: Use balanced approach across all domains

**Research Progress Awareness:**
- Track `entities_discovered_this_session` to avoid redundancy
- Use `successful_patterns` to guide workflow decisions
- Adapt strategy based on `research_goal` alignment

## 🚀 Advanced Metadata-Driven Workflows

**High-Throughput Discovery (relationship_density > 0.8):**
```bash
# Rich semantic space detected - go deep
cl_query "SELECT ?related WHERE { ?entity wdt:P31/wdt:P279* ?type }"
cl_discover related_endpoints --patterns
```

**Cross-Database Integration (external_refs_available.count > 3):**
```bash
# Multiple databases available - comprehensive profiling
for ref in external_refs_available:
    cl_resolve entity --to-db ref_database
```

**Focused Domain Research (single entity_type dominance):**
```bash
# Specialized domain detected - apply domain expertise
if Q8054 dominates: use biology_workflow
if Q11173 dominates: use chemistry_workflow
```

This metadata interpretation enables intelligent, adaptive research workflows that leverage the full power of enhanced cl_search capabilities.
"""
        }
        
        return instructions.get(pattern)
        
    def list_available_patterns(self) -> list[str]:
        """List all available instruction patterns."""
        patterns = [
            "discovery_first", "biology_workflow", "chemistry_workflow", "cross_domain_workflow",
            "cultural_workflow", "medical_workflow", "geographic_workflow", "bibliographic_workflow", 
            "metadata_interpretation"
        ]
        
        # Add file-based patterns
        if self.instructions_dir.exists():
            for file in self.instructions_dir.glob("*.md"):
                pattern_name = file.stem
                if pattern_name not in patterns:
                    patterns.append(pattern_name)
                    
        return sorted(patterns)


@click.group()
@click.pass_context
def main(ctx):
    """CogitareLink: Transform Claude Code into a semantic research assistant.
    
    Provides research-specific instructions and session management for
    enhanced scientific discovery workflows.
    """
    ctx.ensure_object(dict)
    ctx.obj['session_manager'] = ResearchSession()
    ctx.obj['instruction_index'] = InstructionIndex(
        Path(__file__).parent.parent / "instructions"
    )


@main.command()
@click.argument('domain', type=click.Choice(['biology', 'chemistry', 'general']))
@click.option('--goal', help='Research goal description')
@click.pass_context
def init(ctx, domain: str, goal: Optional[str]):
    """Initialize research session for specified domain.
    
    Examples:
        cogitarelink init biology --goal "COVID spike protein analysis"
        cogitarelink init chemistry --goal "Drug discovery workflow"
        cogitarelink init general --goal "Scientific literature review"
    """
    session_manager = ctx.obj['session_manager']
    instruction_index = ctx.obj['instruction_index']
    
    # Create new session
    session_data = session_manager.create_session(domain, goal)
    
    click.echo(f"🧬 Research session initialized!")
    click.echo(f"📋 Session ID: {session_data['sessionId']}")
    click.echo(f"🎯 Domain: {domain}")
    click.echo(f"📝 Goal: {session_data['researchGoal']}")
    
    if session_data['claudeSessionId']:
        click.echo(f"🔗 Linked to Claude session: {session_data['claudeSessionId'][:8]}...")
    
    click.echo()
    click.echo("🔍 **CLAUDE CODE RESEARCH MODE ACTIVATED**")
    click.echo()
    
    # Print relevant instructions
    for instruction_pattern in session_data['activeInstructions']:
        instruction_content = instruction_index.get_instruction(instruction_pattern)
        if instruction_content:
            click.echo(instruction_content)
            click.echo()
            
    click.echo("✅ Research context loaded. Use other CogitareLink tools with enhanced capabilities.")
    click.echo("💡 Tip: Use 'cogitarelink remind <pattern>' to see specific research patterns.")


@main.command()
@click.pass_context
def status(ctx):
    """Show current research session status."""
    session_manager = ctx.obj['session_manager']
    
    session = session_manager.load_session()
    if not session:
        click.echo("❌ No active research session found.")
        click.echo("💡 Use 'cogitarelink init <domain>' to start a research session.")
        return
        
    click.echo(f"📋 **Research Session Status**")
    click.echo(f"Session ID: {session['sessionId']}")
    click.echo(f"Domain: {session['researchDomain']}")
    click.echo(f"Goal: {session['researchGoal']}")
    click.echo(f"Created: {session['createdAt']}")
    click.echo(f"Interactions: {session['sessionCounter']}")
    click.echo()
    
    # Tool usage stats
    click.echo("🔧 **Tool Usage:**")
    for tool, count in session['toolUsage'].items():
        click.echo(f"  {tool}: {count}")
    click.echo()
    
    # Research progress
    progress = session['researchProgress']
    click.echo("📊 **Research Progress:**")
    click.echo(f"  Entities discovered: {progress['entitiesDiscovered']}")
    click.echo(f"  Relationships found: {progress['relationshipsFound']}")
    click.echo(f"  Workflows completed: {progress['workflowsCompleted']}")
    click.echo()
    
    # Active instructions
    click.echo("📚 **Active Instructions:**")
    for pattern in session['activeInstructions']:
        click.echo(f"  - {pattern}")
    click.echo()
    
    # Discovered endpoints
    if session['discoveredEndpoints']:
        click.echo("🌐 **Discovered Endpoints:**")
        for endpoint in session['discoveredEndpoints']:
            click.echo(f"  - {endpoint['name']}: {endpoint['url']}")
    else:
        click.echo("🌐 **Discovered Endpoints:** None yet")
        click.echo("💡 Use 'cl_discover <endpoint>' to discover endpoint capabilities")


@main.command()
@click.argument('pattern', required=False)
@click.pass_context
def remind(ctx, pattern: Optional[str]):
    """Print specific research instruction patterns.
    
    Examples:
        cogitarelink remind discovery  
        cogitarelink remind biology-workflow
        cogitarelink remind                  # List all patterns
    """
    instruction_index = ctx.obj['instruction_index']
    
    if not pattern:
        # List available patterns
        patterns = instruction_index.list_available_patterns()
        click.echo("📚 **Available Instruction Patterns:**")
        for p in patterns:
            click.echo(f"  - {p}")
        click.echo()
        click.echo("💡 Use 'cogitarelink remind <pattern>' to see specific instructions.")
        return
        
    # Try pattern with underscores (discovery_first)
    instruction = instruction_index.get_instruction(pattern)
    
    # Try pattern with hyphens converted to underscores
    if not instruction and '-' in pattern:
        instruction = instruction_index.get_instruction(pattern.replace('-', '_'))
        
    # Try partial matches
    if not instruction:
        available_patterns = instruction_index.list_available_patterns()
        matches = [p for p in available_patterns if pattern.lower() in p.lower()]
        
        if len(matches) == 1:
            instruction = instruction_index.get_instruction(matches[0])
        elif len(matches) > 1:
            click.echo(f"❓ Multiple patterns match '{pattern}':")
            for match in matches:
                click.echo(f"  - {match}")
            click.echo()
            click.echo("💡 Use exact pattern name: 'cogitarelink remind <pattern>'")
            return
            
    if instruction:
        click.echo(instruction)
    else:
        click.echo(f"❌ Pattern '{pattern}' not found.")
        click.echo("💡 Use 'cogitarelink remind' to see available patterns.")


@main.command()
@click.argument('session_id', required=False)
@click.pass_context
def resume(ctx, session_id: Optional[str]):
    """Resume previous research session.
    
    If no session_id provided, resumes most recent session.
    """
    session_manager = ctx.obj['session_manager']
    instruction_index = ctx.obj['instruction_index']
    
    current_session = session_manager.load_session()
    if not current_session:
        click.echo("❌ No research session found to resume.")
        click.echo("💡 Use 'cogitarelink init <domain>' to start a new session.")
        return
        
    # For now, just reactivate current session (future: support multiple sessions)
    if session_id and session_id != current_session['sessionId']:
        click.echo(f"⚠️ Session '{session_id}' not found. Using current session.")
        
    click.echo(f"🔄 Resuming research session: {current_session['sessionId']}")
    click.echo(f"🎯 Domain: {current_session['researchDomain']}")
    click.echo(f"📝 Goal: {current_session['researchGoal']}")
    click.echo()
    
    # Reprint active instructions to restore research context
    click.echo("🔍 **RESEARCH CONTEXT RESTORED**")
    click.echo()
    
    for instruction_pattern in current_session['activeInstructions']:
        instruction_content = instruction_index.get_instruction(instruction_pattern)
        if instruction_content:
            click.echo(instruction_content)
            click.echo()
            
    # Update session interaction count
    session_manager.update_session({"resumed": True})
    
    click.echo("✅ Research context reactivated. Continue using CogitareLink tools.")


if __name__ == "__main__":
    main()