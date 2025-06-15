"""Universal External Identifier Discovery System.

Implements comprehensive discovery patterns for external identifiers across all domains,
extending beyond biology to cultural, chemical, geographic, and bibliographic domains.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Set, Tuple
from enum import Enum

from .discovery_infrastructure import property_discovery
from ..discovery.cache_manager import cache_manager
from ..core.debug import get_logger

log = get_logger("universal_identifier_discovery")


class IdentifierDomain(Enum):
    """Domains for external identifiers discovered from knowledge bases."""
    BIOLOGY = "biology"
    CHEMISTRY = "chemistry"
    CULTURAL = "cultural"
    BIBLIOGRAPHIC = "bibliographic"
    GEOGRAPHIC = "geographic"
    MEDICAL = "medical"
    TECHNICAL = "technical"
    GENERAL = "general"


@dataclass
class IdentifierPattern:
    """Pattern information for external identifier validation and discovery."""
    property_id: str
    domain: IdentifierDomain
    label: str
    description: str
    format_pattern: Optional[str] = None
    database_name: str = ""
    endpoint_url: str = ""
    example_values: List[str] = None
    cross_references: List[str] = None  # Related identifier properties
    discovered_dynamically: bool = False  # True if discovered via DESCRIBE query
    
    def __post_init__(self):
        if self.example_values is None:
            self.example_values = []
        if self.cross_references is None:
            self.cross_references = []


class UniversalIdentifierDiscovery:
    """Discovers external identifier patterns across all domains using Wikidata's crosswalk capabilities."""
    
    def __init__(self):
        self.cache_prefix = "universal_identifier_discovery"
        # Core biological identifier patterns (from earlier work)
        self.known_patterns = self._initialize_known_patterns()
        # Dynamic discovery cache
        self.dynamic_pattern_cache = {}
        
    def _initialize_known_patterns(self) -> Dict[str, IdentifierPattern]:
        """Initialize known identifier patterns across all domains."""
        patterns = {}
        
        # Biology Domain
        patterns["P352"] = IdentifierPattern(
            property_id="P352",
            domain=IdentifierDomain.BIOLOGY,
            label="UniProt protein ID",
            description="identifier for a protein in the UniProt database",
            format_pattern=r"^[A-Z0-9]{6,10}$",
            database_name="uniprot", 
            endpoint_url="https://rest.uniprot.org/uniprotkb/",
            example_values=["P01588", "Q9UHC7", "P04637"],
            cross_references=["P638"]  # Often linked to PDB
        )
        
        patterns["P638"] = IdentifierPattern(
            property_id="P638",
            domain=IdentifierDomain.BIOLOGY,
            label="PDB structure ID",
            description="identifier for a 3D protein structure in the Protein Data Bank",
            format_pattern=r"^[0-9][A-Z0-9]{3}$",
            database_name="pdb",
            endpoint_url="https://data.rcsb.org/rest/v1/core/entry/",
            example_values=["1BUY", "1CN4", "6LU7"],
            cross_references=["P352"]  # Often linked from UniProt
        )
        
        patterns["P705"] = IdentifierPattern(
            property_id="P705",
            domain=IdentifierDomain.BIOLOGY,
            label="Ensembl protein ID",
            description="identifier for a protein in the Ensembl database",
            format_pattern=r"^ENSP[0-9]{11}$",
            database_name="ensembl",
            endpoint_url="https://rest.ensembl.org/",
            example_values=["ENSP00000252723", "ENSP00000379387"],
            cross_references=["P352", "P594"]
        )
        
        # Chemistry Domain
        patterns["P231"] = IdentifierPattern(
            property_id="P231",
            domain=IdentifierDomain.CHEMISTRY,
            label="CAS Registry Number",
            description="identifier for chemical substances in the Chemical Abstracts Service registry",
            format_pattern=r"^[0-9]+-[0-9]+-[0-9]+$",
            database_name="cas",
            endpoint_url="https://commonchemistry.cas.org/detail?cas_rn=",
            example_values=["50-00-0", "64-17-5", "7732-18-5"],
            cross_references=["P662", "P592"]
        )
        
        patterns["P662"] = IdentifierPattern(
            property_id="P662",
            domain=IdentifierDomain.CHEMISTRY,
            label="PubChem CID",
            description="identifier for a chemical compound in the PubChem database",
            format_pattern=r"^[0-9]+$",
            database_name="pubchem",
            endpoint_url="https://pubchem.ncbi.nlm.nih.gov/rest/pug/",
            example_values=["702", "5950", "962"],
            cross_references=["P231", "P592"]
        )
        
        patterns["P592"] = IdentifierPattern(
            property_id="P592",
            domain=IdentifierDomain.CHEMISTRY,
            label="ChEMBL ID",
            description="identifier for a chemical compound in the ChEMBL database",
            format_pattern=r"^CHEMBL[0-9]+$",
            database_name="chembl",
            endpoint_url="https://chembl.ebi.ac.uk/chembl/api/data/",
            example_values=["CHEMBL25", "CHEMBL1096", "CHEMBL112"],
            cross_references=["P231", "P662"]
        )
        
        # Cultural/Art Domain  
        patterns["P350"] = IdentifierPattern(
            property_id="P350",
            domain=IdentifierDomain.CULTURAL,
            label="RKD Images ID",
            description="identifier for an artwork image in the RKD Images database",
            format_pattern=r"^[0-9]+$",
            database_name="rkd_images",
            endpoint_url="https://rkd.nl/images/",
            example_values=["70503", "12345", "89012"],
            cross_references=["P347", "P9394"]
        )
        
        patterns["P347"] = IdentifierPattern(
            property_id="P347",
            domain=IdentifierDomain.CULTURAL,
            label="Joconde ID",
            description="identifier for an artwork in the Joconde database",
            format_pattern=r"^[A-Z0-9]+$",
            database_name="joconde",
            endpoint_url="https://www.pop.culture.gouv.fr/notice/joconde/",
            example_values=["000PE003563", "000PE025604"],
            cross_references=["P350", "P9394"]
        )
        
        patterns["P9394"] = IdentifierPattern(
            property_id="P9394",
            domain=IdentifierDomain.CULTURAL,
            label="Louvre Museum ID",
            description="identifier for an artwork in the Louvre Museum collection",
            format_pattern=r"^[A-Z0-9\-\.]+$",
            database_name="louvre",
            endpoint_url="https://collections.louvre.fr/ark:/53355/",
            example_values=["INV.779", "LP.2449", "MR.1953"],
            cross_references=["P350", "P347"]
        )
        
        # Medical Domain
        patterns["P486"] = IdentifierPattern(
            property_id="P486",
            domain=IdentifierDomain.MEDICAL,
            label="MeSH descriptor ID",
            description="identifier for a medical subject in the MeSH thesaurus",
            format_pattern=r"^D[0-9]{6}$",
            database_name="mesh",
            endpoint_url="https://meshb.nlm.nih.gov/record/ui?ui=",
            example_values=["D000001", "D000970", "D001943"],
            cross_references=["P2566"]
        )
        
        patterns["P2566"] = IdentifierPattern(
            property_id="P2566",
            domain=IdentifierDomain.MEDICAL,
            label="DrugBank ID",
            description="identifier for a drug in the DrugBank database",
            format_pattern=r"^DB[0-9]{5}$",
            database_name="drugbank",
            endpoint_url="https://go.drugbank.com/drugs/",
            example_values=["DB00001", "DB00945", "DB01050"],
            cross_references=["P486", "P592"]
        )
        
        # Geographic Domain
        patterns["P1566"] = IdentifierPattern(
            property_id="P1566",
            domain=IdentifierDomain.GEOGRAPHIC,
            label="GeoNames ID",
            description="identifier for a geographical location in the GeoNames database",
            format_pattern=r"^[0-9]+$",
            database_name="geonames",
            endpoint_url="https://www.geonames.org/",
            example_values=["2988507", "6545158", "3017382"],
            cross_references=["P1082"]
        )
        
        # Bibliographic Domain
        patterns["P214"] = IdentifierPattern(
            property_id="P214",
            domain=IdentifierDomain.BIBLIOGRAPHIC,
            label="VIAF ID",
            description="identifier for a person or organization in the VIAF authority file",
            format_pattern=r"^[0-9]+$",
            database_name="viaf",
            endpoint_url="https://viaf.org/viaf/",
            example_values=["102333412", "24604287", "73859244"],
            cross_references=["P213", "P244"]
        )
        
        patterns["P213"] = IdentifierPattern(
            property_id="P213",
            domain=IdentifierDomain.BIBLIOGRAPHIC,
            label="ISNI",
            description="International Standard Name Identifier for a person or organization",
            format_pattern=r"^[0-9]{4} [0-9]{4} [0-9]{4} [0-9]{3}[0-9X]$",
            database_name="isni",
            endpoint_url="https://isni.org/isni/",
            example_values=["0000 0001 2096 0218", "0000 0001 2135 6334"],
            cross_references=["P214", "P244"]
        )
        
        patterns["P244"] = IdentifierPattern(
            property_id="P244",
            domain=IdentifierDomain.BIBLIOGRAPHIC,
            label="Library of Congress authority ID",
            description="identifier for a name or subject in the Library of Congress authority files",
            format_pattern=r"^[a-z]{1,2}[0-9]{8,10}$",
            database_name="loc",
            endpoint_url="https://id.loc.gov/authorities/",
            example_values=["n79021164", "sh85026371", "no2008183293"],
            cross_references=["P214", "P213"]
        )
        
        return patterns
    
    def discover_all_external_identifiers(self, entity_id: str, endpoint: str = "wikidata") -> Dict[str, Any]:
        """Discover all external identifiers for an entity across all domains."""
        cache_key = f"{self.cache_prefix}:all_identifiers:{entity_id}:{endpoint}"
        cached = cache_manager.get(cache_key)
        if cached:
            return cached
        
        # Query for all external identifier properties on the entity
        discovered_identifiers = self._query_all_external_identifiers(entity_id, endpoint)
        
        # Enrich with pattern information
        enriched_identifiers = {}
        unknown_patterns = []
        
        for prop_id, values in discovered_identifiers.items():
            if prop_id in self.known_patterns:
                pattern = self.known_patterns[prop_id]
                enriched_identifiers[prop_id] = {
                    "values": values if isinstance(values, list) else [values],
                    "pattern": pattern.__dict__,
                    "validation_status": self._validate_identifier_format(prop_id, values),
                    "cross_reference_potential": pattern.cross_references
                }
            else:
                # Discover unknown pattern dynamically
                pattern_info = self._discover_unknown_pattern(prop_id, endpoint)
                enriched_identifiers[prop_id] = {
                    "values": values if isinstance(values, list) else [values],
                    "pattern": pattern_info,
                    "validation_status": "unknown_pattern",
                    "cross_reference_potential": []
                }
                unknown_patterns.append(prop_id)
        
        result = {
            "entity_id": entity_id,
            "discovered_identifiers": enriched_identifiers,
            "domains_covered": list(set(
                self.known_patterns[pid].domain.value 
                for pid in enriched_identifiers.keys() 
                if pid in self.known_patterns
            )),
            "unknown_patterns": unknown_patterns,
            "cross_reference_suggestions": self._generate_cross_reference_suggestions(enriched_identifiers)
        }
        
        # Cache result
        cache_manager.set(cache_key, result, ttl=3600)
        return result
    
    def discover_by_domain(self, domain: IdentifierDomain, entity_id: Optional[str] = None) -> Dict[str, IdentifierPattern]:
        """Discover all identifier patterns for a specific domain."""
        domain_patterns = {
            pid: pattern for pid, pattern in self.known_patterns.items()
            if pattern.domain == domain
        }
        
        if entity_id:
            # Filter to only patterns present on this entity
            entity_identifiers = self.discover_all_external_identifiers(entity_id)
            domain_patterns = {
                pid: pattern for pid, pattern in domain_patterns.items()
                if pid in entity_identifiers.get("discovered_identifiers", {})
            }
        
        return domain_patterns
    
    def discover_cross_reference_pathways(self, entity_id: str) -> Dict[str, Any]:
        """Discover research pathways using cross-reference relationships."""
        all_identifiers = self.discover_all_external_identifiers(entity_id)
        
        pathways = {}
        discovered = all_identifiers.get("discovered_identifiers", {})
        
        # Group by domain for domain-specific workflows
        by_domain = {}
        for prop_id, info in discovered.items():
            if prop_id in self.known_patterns:
                domain = self.known_patterns[prop_id].domain.value
                if domain not in by_domain:
                    by_domain[domain] = []
                by_domain[domain].append({
                    "property": prop_id,
                    "values": info["values"],
                    "database": self.known_patterns[prop_id].database_name
                })
        
        # Generate cross-domain pathways
        for domain, identifiers in by_domain.items():
            pathways[f"{domain}_workflow"] = {
                "domain": domain,
                "identifiers": identifiers,
                "suggested_tools": [
                    f"cl_resolve {entity_id} --to-db {ident['database']}" 
                    for ident in identifiers
                ],
                "cross_reference_opportunities": self._find_cross_domain_connections(domain, by_domain)
            }
        
        return {
            "entity_id": entity_id,
            "pathways": pathways,
            "multi_domain_coverage": len(by_domain) > 1,
            "total_databases": sum(len(idents) for idents in by_domain.values())
        }
    
    def _query_all_external_identifiers(self, entity_id: str, endpoint: str) -> Dict[str, Any]:
        """Query endpoint for all external identifier properties on an entity."""
        if endpoint != "wikidata":
            return {}  # Only Wikidata supported for now
        
        # Query for all properties that are external identifiers
        sparql_query = f"""
        SELECT ?prop ?value WHERE {{
            wd:{entity_id} ?prop ?value .
            {{
                ?prop wdt:P31 wd:Q18616576 .  # external identifier property
            }} UNION {{
                ?prop wdt:P31 wd:Q19829908 .  # authority control for places
            }} UNION {{
                ?prop wdt:P31 wd:Q89560413 .  # property related to thesaurus
            }}
        }}
        """
        
        try:
            from ..discovery.base import discovery_engine
            result = discovery_engine.query_endpoint(endpoint, sparql_query)
            
            identifiers = {}
            if result.get("success"):
                for binding in result.get("results", []):
                    prop_uri = binding.get("prop", {}).get("value", "")
                    prop_id = prop_uri.split("/")[-1] if prop_uri else ""
                    value = binding.get("value", {}).get("value", "")
                    
                    if prop_id and value:
                        if prop_id in identifiers:
                            if not isinstance(identifiers[prop_id], list):
                                identifiers[prop_id] = [identifiers[prop_id]]
                            identifiers[prop_id].append(value)
                        else:
                            identifiers[prop_id] = value
            
            return identifiers
            
        except Exception as e:
            log.error(f"Failed to query external identifiers for {entity_id}: {e}")
            return {}
    
    def _discover_unknown_pattern(self, prop_id: str, endpoint: str) -> Dict[str, Any]:
        """Discover information about an unknown identifier pattern."""
        # Use existing property discovery infrastructure
        prop_info = property_discovery.discover_properties([prop_id], endpoint)
        
        if prop_id in prop_info:
            info = prop_info[prop_id]
            return {
                "property_id": prop_id,
                "domain": "general",  # Default for unknown patterns
                "label": info.label,
                "description": info.description,
                "discovered_dynamically": True
            }
        else:
            return {
                "property_id": prop_id,
                "domain": "general",
                "label": prop_id,
                "description": "Unknown external identifier pattern",
                "discovered_dynamically": True
            }
    
    def _validate_identifier_format(self, prop_id: str, values: Any) -> str:
        """Validate identifier format against known patterns."""
        if prop_id not in self.known_patterns:
            return "unknown_pattern"
        
        pattern = self.known_patterns[prop_id]
        if not pattern.format_pattern:
            return "no_validation_pattern"
        
        values_list = values if isinstance(values, list) else [values]
        
        all_valid = True
        for value in values_list:
            if not re.match(pattern.format_pattern, str(value)):
                all_valid = False
                break
        
        return "valid" if all_valid else "invalid_format"
    
    def _generate_cross_reference_suggestions(self, identifiers: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate suggestions for following cross-references between databases."""
        suggestions = []
        
        for prop_id, info in identifiers.items():
            if prop_id in self.known_patterns:
                pattern = self.known_patterns[prop_id]
                for cross_ref_prop in pattern.cross_references:
                    if cross_ref_prop not in identifiers:
                        # Suggest discovering this cross-reference
                        if cross_ref_prop in self.known_patterns:
                            cross_ref_pattern = self.known_patterns[cross_ref_prop]
                            suggestions.append({
                                "from_property": prop_id,
                                "from_database": pattern.database_name,
                                "to_property": cross_ref_prop,
                                "to_database": cross_ref_pattern.database_name,
                                "suggested_tool": f"cl_resolve --from-db {pattern.database_name} --to-db {cross_ref_pattern.database_name}",
                                "reasoning": f"Entities in {pattern.database_name} often have cross-references to {cross_ref_pattern.database_name}"
                            })
        
        return suggestions
    
    def _find_cross_domain_connections(self, current_domain: str, all_domains: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find opportunities to connect across domains."""
        connections = []
        
        # Biology ↔ Chemistry connections
        if current_domain == "biology" and "chemistry" in all_domains:
            connections.append({
                "target_domain": "chemistry",
                "connection_type": "protein_drug_targets",
                "reasoning": "Proteins often serve as drug targets - explore chemical compounds that interact"
            })
        
        if current_domain == "chemistry" and "biology" in all_domains:
            connections.append({
                "target_domain": "biology", 
                "connection_type": "compound_targets",
                "reasoning": "Chemical compounds often target specific proteins - explore biological targets"
            })
        
        # Cultural ↔ Geographic connections
        if current_domain == "cultural" and "geographic" in all_domains:
            connections.append({
                "target_domain": "geographic",
                "connection_type": "artwork_provenance",
                "reasoning": "Artworks have geographical origins and current locations"
            })
        
        # Bibliographic connections to all domains
        if "bibliographic" in all_domains and current_domain != "bibliographic":
            connections.append({
                "target_domain": "bibliographic",
                "connection_type": "literature_references",
                "reasoning": f"Find scholarly literature about this {current_domain} entity"
            })
        
        return connections
    
    def discover_pattern_via_describe(self, prop_id: str) -> IdentifierPattern:
        """Discover identifier pattern using DESCRIBE query on property.
        
        This is the core Software 2.0 method that replaces hardcoded patterns.
        """
        # Check dynamic cache first
        if prop_id in self.dynamic_pattern_cache:
            return self.dynamic_pattern_cache[prop_id]
        
        # Check hardcoded patterns for backward compatibility
        if prop_id in self.known_patterns:
            return self.known_patterns[prop_id]
        
        try:
            # Use Wikidata API to get property metadata (more reliable than DESCRIBE)
            import httpx
            
            with httpx.Client(timeout=10.0) as client:
                response = client.get(
                    "https://www.wikidata.org/w/api.php",
                    params={
                        "action": "wbgetentities",
                        "ids": prop_id,
                        "format": "json",
                        "languages": "en"
                    }
                )
                response.raise_for_status()
                data = response.json()
                
                if "entities" in data and prop_id in data["entities"]:
                    entity_data = data["entities"][prop_id]
                    pattern = self._parse_property_api_result(entity_data, prop_id)
                    # Cache the discovered pattern
                    self.dynamic_pattern_cache[prop_id] = pattern
                    return pattern
                else:
                    log.warning(f"Property {prop_id} not found in Wikidata API")
                
        except Exception as e:
            log.error(f"Dynamic discovery failed for {prop_id}: {e}")
        
        # Fallback to minimal pattern
        fallback_pattern = IdentifierPattern(
            property_id=prop_id,
            domain=IdentifierDomain.GENERAL,
            label=prop_id,
            description="Dynamically discovered external identifier",
            discovered_dynamically=True
        )
        self.dynamic_pattern_cache[prop_id] = fallback_pattern
        return fallback_pattern
    
    def discover_service_properties_via_describe(self, service_id: str) -> Dict[str, Any]:
        """Discover all properties associated with a service using DESCRIBE query."""
        try:
            from ..discovery.base import discovery_engine
            result = discovery_engine.query_endpoint("wikidata", f"DESCRIBE wd:{service_id}")
            
            if result["success"]:
                return self._parse_service_describe_result(result, service_id)
            else:
                log.warning(f"DESCRIBE query failed for {service_id}: {result.get('error')}")
                
        except Exception as e:
            log.error(f"Service discovery failed for {service_id}: {e}")
        
        return {
            "service_id": service_id,
            "service_name": service_id,
            "domain": "general",
            "properties_defined": {}
        }
    
    def find_service_for_property(self, prop_id: str) -> Optional[str]:
        """Find the service/database entity that defines a property."""
        try:
            from ..discovery.base import discovery_engine
            # Query for entities that have P1687 (Wikidata property) pointing to this property
            sparql_query = f"""
            SELECT ?service WHERE {{
                ?service wdt:P1687 wd:{prop_id} .
            }} LIMIT 1
            """
            
            result = discovery_engine.query_endpoint("wikidata", sparql_query)
            
            if result["success"] and result["results"]:
                service_uri = result["results"][0].get("service", {}).get("value", "")
                if service_uri:
                    return service_uri.split("/")[-1]  # Extract Q-ID
                    
        except Exception as e:
            log.error(f"Service lookup failed for {prop_id}: {e}")
        
        return None
    
    def find_properties_for_service(self, service_id: str) -> List[str]:
        """Find all properties defined by a service."""
        try:
            from ..discovery.base import discovery_engine
            # Query for properties that this service defines via P1687
            sparql_query = f"""
            SELECT ?prop WHERE {{
                wd:{service_id} wdt:P1687 ?prop .
            }}
            """
            
            result = discovery_engine.query_endpoint("wikidata", sparql_query)
            
            if result["success"]:
                properties = []
                for binding in result["results"]:
                    prop_uri = binding.get("prop", {}).get("value", "")
                    if prop_uri:
                        properties.append(prop_uri.split("/")[-1])  # Extract P-ID
                return properties
                        
        except Exception as e:
            log.error(f"Property lookup failed for {service_id}: {e}")
        
        return []
    
    def _parse_property_api_result(self, entity_data: Dict[str, Any], prop_id: str) -> IdentifierPattern:
        """Parse Wikidata API result to extract identifier pattern information."""
        # Extract basic info
        label = prop_id
        description = "External identifier property"
        format_pattern = None
        endpoint_url = ""
        
        # Extract label
        labels = entity_data.get("labels", {})
        if "en" in labels:
            label = labels["en"]["value"]
        
        # Extract description
        descriptions = entity_data.get("descriptions", {})
        if "en" in descriptions:
            description = descriptions["en"]["value"]
        
        # Extract claims for metadata
        claims = entity_data.get("claims", {})
        
        # Extract format pattern (P1793)
        if "P1793" in claims:
            for claim in claims["P1793"]:
                if "mainsnak" in claim and "datavalue" in claim["mainsnak"]:
                    format_pattern = claim["mainsnak"]["datavalue"]["value"]
                    break
        
        # Extract formatter URL (P1630)
        if "P1630" in claims:
            for claim in claims["P1630"]:
                if "mainsnak" in claim and "datavalue" in claim["mainsnak"]:
                    endpoint_url = claim["mainsnak"]["datavalue"]["value"]
                    break
        
        # Determine domain from label and patterns
        domain = self._classify_domain_from_label(label, endpoint_url)
        
        # Generate database name from label
        database_name = self._generate_database_name(label)
        
        return IdentifierPattern(
            property_id=prop_id,
            domain=domain,
            label=label,
            description=description,
            format_pattern=format_pattern,
            database_name=database_name,
            endpoint_url=endpoint_url,
            discovered_dynamically=True
        )
    
    def _parse_property_describe_result(self, describe_result: Dict[str, Any], prop_id: str) -> IdentifierPattern:
        """Parse DESCRIBE result to extract identifier pattern information."""
        label = prop_id
        description = "External identifier property"
        format_pattern = None
        endpoint_url = ""
        database_name = prop_id.lower()
        domain = IdentifierDomain.GENERAL
        
        # Parse the RDF triples from DESCRIBE result
        for binding in describe_result.get("results", []):
            subject = binding.get("subject", {}).get("value", "")
            predicate = binding.get("predicate", {}).get("value", "")
            obj = binding.get("object", {})
            
            # Only process triples where the subject is our property
            if not subject.endswith(f"/{prop_id}"):
                continue
            
            # Extract label
            if predicate.endswith("rdf-schema#label") and obj.get("xml:lang") == "en":
                label = obj.get("value", label)
            
            # Extract description  
            elif predicate.endswith("schema#description") and obj.get("xml:lang") == "en":
                description = obj.get("value", description)
            
            # Extract format pattern (P1793)
            elif predicate.endswith("/P1793"):
                format_pattern = obj.get("value")
            
            # Extract formatter URL (P1630)
            elif predicate.endswith("/P1630"):
                endpoint_url = obj.get("value", "")
        
        # Determine domain from label and patterns
        domain = self._classify_domain_from_label(label, endpoint_url)
        
        # Generate database name from label
        database_name = self._generate_database_name(label)
        
        return IdentifierPattern(
            property_id=prop_id,
            domain=domain,
            label=label,
            description=description,
            format_pattern=format_pattern,
            database_name=database_name,
            endpoint_url=endpoint_url,
            discovered_dynamically=True
        )
    
    def _parse_service_describe_result(self, describe_result: Dict[str, Any], service_id: str) -> Dict[str, Any]:
        """Parse DESCRIBE result for service entity."""
        service_name = service_id
        domain = "general"
        properties_defined = {"P1687": []}
        
        # Parse the RDF triples
        for binding in describe_result.get("results", []):
            predicate = binding.get("predicate", {}).get("value", "")
            obj = binding.get("object", {})
            
            # Extract service name
            if predicate.endswith("rdf-schema#label") and obj.get("xml:lang") == "en":
                service_name = obj.get("value", service_name)
            
            # Extract properties defined (P1687)
            elif predicate.endswith("/P1687"):
                prop_uri = obj.get("value", "")
                if prop_uri:
                    prop_id = prop_uri.split("/")[-1]
                    properties_defined["P1687"].append(prop_id)
        
        # Classify domain from service name
        domain = self._classify_domain_from_service_name(service_name)
        
        return {
            "service_id": service_id,
            "service_name": service_name,
            "domain": domain,
            "properties_defined": properties_defined
        }
    
    def _classify_domain_from_service_describe(self, describe_result: Dict[str, Any]) -> IdentifierDomain:
        """Classify domain from service DESCRIBE result."""
        # Look for P31 (instance of) classifications
        for binding in describe_result.get("results", []):
            predicate = binding.get("predicate", {}).get("value", "")
            obj = binding.get("object", {})
            
            if predicate.endswith("/P31"):
                class_uri = obj.get("value", "")
                if "Q17152639" in class_uri:  # thesaurus
                    return IdentifierDomain.GEOGRAPHIC  # Geographic thesaurus
                elif "Q7094076" in class_uri:  # online database
                    return IdentifierDomain.GENERAL
        
        return IdentifierDomain.GENERAL
    
    def _classify_domain_from_label(self, label: str, endpoint_url: str) -> IdentifierDomain:
        """Classify domain from property label and URL."""
        label_lower = label.lower()
        url_lower = endpoint_url.lower()
        
        # Geographic indicators
        if any(term in label_lower for term in ["geographic", "getty", "thesaurus", "location", "place"]):
            return IdentifierDomain.GEOGRAPHIC
        if any(term in url_lower for term in ["getty", "geonames", "place"]):
            return IdentifierDomain.GEOGRAPHIC
            
        # Biology indicators
        if any(term in label_lower for term in ["protein", "uniprot", "ensembl", "gene"]):
            return IdentifierDomain.BIOLOGY
        if any(term in url_lower for term in ["uniprot", "ensembl", "protein", "rcsb"]):
            return IdentifierDomain.BIOLOGY
            
        # Chemistry indicators
        if any(term in label_lower for term in ["chemical", "pubchem", "chembl", "cas"]):
            return IdentifierDomain.CHEMISTRY
        if any(term in url_lower for term in ["pubchem", "chembl", "cas"]):
            return IdentifierDomain.CHEMISTRY
            
        # Cultural indicators
        if any(term in label_lower for term in ["museum", "artwork", "cultural", "joconde", "louvre"]):
            return IdentifierDomain.CULTURAL
        if any(term in url_lower for term in ["museum", "louvre", "rkd"]):
            return IdentifierDomain.CULTURAL
            
        return IdentifierDomain.GENERAL
    
    def _classify_domain_from_service_name(self, service_name: str) -> str:
        """Classify domain from service name."""
        name_lower = service_name.lower()
        
        if any(term in name_lower for term in ["geographic", "thesaurus", "location"]):
            return "geographic"
        elif any(term in name_lower for term in ["protein", "gene", "biological"]):
            return "biology"
        elif any(term in name_lower for term in ["chemical", "compound"]):
            return "chemistry"
        elif any(term in name_lower for term in ["museum", "cultural", "art"]):
            return "cultural"
        
        return "general"
    
    def _generate_database_name(self, label: str) -> str:
        """Generate database name from property label."""
        # Extract key terms and convert to database name
        label_lower = label.lower()
        
        if "getty" in label_lower and "geographic" in label_lower:
            return "getty_tgn"
        elif "uniprot" in label_lower:
            return "uniprot"
        elif "pubchem" in label_lower:
            return "pubchem"
        elif "chembl" in label_lower:
            return "chembl"
        elif "ensembl" in label_lower:
            return "ensembl"
        elif "mesh" in label_lower:
            return "mesh"
        elif "cas" in label_lower:
            return "cas"
        elif "geonames" in label_lower:
            return "geonames"
        elif "viaf" in label_lower:
            return "viaf"
        
        # Fallback: use first word
        words = label_lower.split()
        if words:
            return words[0].replace(" ", "_")
        
        return "unknown"
    
    def discover_patterns_bulk(self, property_ids: List[str]) -> Dict[str, IdentifierPattern]:
        """Discover multiple patterns efficiently."""
        patterns = {}
        for prop_id in property_ids:
            patterns[prop_id] = self.discover_pattern_via_describe(prop_id)
        return patterns
    
    def clear_pattern_cache(self):
        """Clear the dynamic pattern cache."""
        self.dynamic_pattern_cache.clear()
    
    def get_pattern(self, prop_id: str) -> Optional[IdentifierPattern]:
        """Get pattern (backward compatibility method)."""
        if prop_id in self.known_patterns:
            return self.known_patterns[prop_id]
        elif prop_id in self.dynamic_pattern_cache:
            return self.dynamic_pattern_cache[prop_id]
        else:
            # Discover dynamically
            return self.discover_pattern_via_describe(prop_id)


# Global instance for use across tools
universal_identifier_discovery = UniversalIdentifierDiscovery()