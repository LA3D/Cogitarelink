#!/usr/bin/env python3
"""
cl_resolve - Universal Identifier Resolution Tool

Leverages service description-powered vocabulary discovery to automatically resolve
external identifiers across biological databases with contextual integration.

Usage:
    cl_resolve P352 P01308                # Resolve UniProt ID 
    cl_resolve P683 CHEBI:15365          # Resolve ChEBI compound ID
    cl_resolve --discover P352           # Discover metadata for property
    cl_resolve --validate P352 INVALID   # Validate identifier format
"""

import asyncio
import click
import json
import time
from typing import Optional, Dict, List, Any
from pathlib import Path

# Import Cogitarelink's own implementations
from ..adapters.wikidata_client import WikidataClient
from ..intelligence.ontology_discovery import OntologyDiscovery
WIKIDATA_CLIENT_AVAILABLE = True
ONTOLOGY_DISCOVERY_AVAILABLE = True

from ..core.debug import get_logger
from ..vocab.registry import registry
from ..vocab.composer import composer
from .cl_ontfetch import AgenticOntologyFetcher

log = get_logger("cl_resolve")

class UniversalIdentifierResolver:
    """Universal identifier resolution using service description-powered approach"""
    
    def __init__(self):
        self.wikidata_client = WikidataClient()
        self.discovery_engine = OntologyDiscovery(progress_format="silent") if ONTOLOGY_DISCOVERY_AVAILABLE else None
        self.property_cache = {}
        self.endpoint_schemas = {}
        
    async def resolve_identifier(
        self, 
        property_id: str, 
        identifier: str,
        validate: bool = True,
        follow_links: bool = True,
        include_context: bool = True
    ) -> Dict[str, Any]:
        """
        Resolve external identifier using Wikidata crosswalk + ontology discovery
        
        This implements the intelligent crosswalk pattern:
        1. Use Wikidata's external identifier metadata as authoritative source
        2. Discover endpoints and vocabulary context using OntFetch when needed
        3. Follow nose to external databases with rich ontology context
        
        Args:
            property_id: Wikidata property ID (e.g., P352 for UniProt)
            identifier: External identifier value
            validate: Validate identifier format against property constraints
            follow_links: Follow links to external databases using discovered ontologies
            include_context: Include vocabulary context from OntFetch
        """
        start_time = time.time()
        
        try:
            # Step 1: Discover property metadata from Wikidata (authoritative crosswalk)
            property_metadata = await self._discover_property_metadata(property_id)
            
            # Step 2: Validate identifier format if requested
            validation_result = None
            if validate:
                validation_result = await self._validate_identifier_format(
                    identifier, property_metadata
                )
                if not validation_result["valid"]:
                    return {
                        "success": False,
                        "error": {
                            "code": "INVALID_IDENTIFIER_FORMAT",
                            "message": f"Identifier '{identifier}' invalid for property {property_id}",
                            "validation_details": validation_result,
                            "suggestions": [
                                f"Check {property_metadata.get('name', property_id)} format requirements",
                                f"Example valid format: {property_metadata.get('example_value', 'N/A')}",
                                "Use --no-validate to skip format checking"
                            ]
                        }
                    }
            
            # Step 3: Resolve identifier in Wikidata (find Wikidata entities)
            wikidata_results = await self._resolve_in_wikidata(property_id, identifier)
            
            # Step 4: Prepare cross-reference suggestions (agentic workflow)
            cross_references = {}
            if wikidata_results.get("found_entities"):
                cross_references = self._prepare_crosswalk_suggestions(
                    wikidata_results["found_entities"], property_metadata
                )
            
            # Step 5: Use OntFetch for external database ontology discovery
            external_ontology = {}
            if follow_links and property_metadata.get("sparql_endpoint"):
                external_ontology = await self._discover_external_ontology(property_metadata)
            
            # Step 6: Follow links to external databases with ontology context
            external_results = {}
            if follow_links and external_ontology.get("success"):
                external_results = await self._resolve_in_external_database(
                    identifier, property_metadata, external_ontology
                )
            
            execution_time = int((time.time() - start_time) * 1000)
            
            # Generate intelligent suggestions based on crosswalk analysis
            suggestions = self._generate_crosswalk_suggestions(
                property_metadata, wikidata_results, cross_references, external_ontology
            )
            
            return {
                "success": True,
                "data": {
                    "property_id": property_id,
                    "identifier": identifier,
                    "property_metadata": property_metadata,
                    "wikidata_results": wikidata_results,
                    "cross_references": cross_references,
                    "external_ontology": external_ontology,
                    "external_results": external_results,
                    "validation": validation_result
                },
                "metadata": {
                    "execution_time_ms": execution_time,
                    "crosswalk_strategy": "wikidata_external_identifiers",
                    "ontology_discovery": bool(external_ontology.get("success")),
                    "cross_references_found": len(cross_references.get("related_identifiers", [])),
                    "external_resolution": bool(external_results)
                },
                "suggestions": suggestions
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": {
                    "code": "RESOLUTION_FAILED",
                    "message": f"Failed to resolve {property_id}:{identifier}: {str(e)}",
                    "suggestions": [
                        "Check property ID format (e.g., P352, P683)",
                        "Verify identifier value exists",
                        "Try with --no-validate if format validation fails",
                        "Use cl_property to inspect property metadata"
                    ]
                }
            }
    
    async def _discover_property_metadata(self, property_id: str) -> Dict[str, Any]:
        """Discover property metadata from Wikidata with caching"""
        
        if property_id in self.property_cache:
            return self.property_cache[property_id]
        
        try:
            # Get property entity from Wikidata
            raw_result = await self.wikidata_client.get_entities([property_id], "en")
            
            if property_id not in raw_result.get("entities", {}):
                raise ValueError(f"Property {property_id} not found")
            
            property_data = raw_result["entities"][property_id]
            
            # Extract essential metadata
            metadata = {
                "property_id": property_id,
                "name": property_data.get("labels", {}).get("en", {}).get("value", "Unknown"),
                "description": property_data.get("descriptions", {}).get("en", {}).get("value", ""),
                "datatype": property_data.get("datatype", "unknown"),
                "example_value": None,
                "formatter_url": None,
                "regex_pattern": None,
                "sparql_endpoint": None,
                "domain": self._extract_domain(property_id, property_data)
            }
            
            # Extract constraints and formatting info from claims
            if "claims" in property_data:
                claims = property_data["claims"]
                
                # P1630: Formatter URL
                if "P1630" in claims:
                    for claim in claims["P1630"]:
                        if claim.get("mainsnak", {}).get("datavalue"):
                            metadata["formatter_url"] = claim["mainsnak"]["datavalue"]["value"]
                            break
                
                # P1793: Regular expression
                if "P1793" in claims:
                    for claim in claims["P1793"]:
                        if claim.get("mainsnak", {}).get("datavalue"):
                            metadata["regex_pattern"] = claim["mainsnak"]["datavalue"]["value"]
                            break
                
                # P1855: Example value
                if "P1855" in claims:
                    for claim in claims["P1855"]:
                        if claim.get("mainsnak", {}).get("datavalue"):
                            metadata["example_value"] = claim["mainsnak"]["datavalue"]["value"]
                            break
                
                # P1696: SPARQL endpoint
                if "P1696" in claims:
                    for claim in claims["P1696"]:
                        if claim.get("mainsnak", {}).get("datavalue"):
                            metadata["sparql_endpoint"] = claim["mainsnak"]["datavalue"]["value"]
                            break
            
            self.property_cache[property_id] = metadata
            return metadata
            
        except Exception as e:
            log.error(f"Failed to discover property metadata for {property_id}: {e}")
            # Return minimal metadata for graceful degradation
            return {
                "property_id": property_id,
                "name": f"Property {property_id}",
                "description": "Metadata discovery failed",
                "domain": "unknown"
            }
    
    def _extract_domain(self, property_id: str, property_data: Dict) -> str:
        """Extract domain information from property data"""
        
        # Known biological property patterns
        biological_properties = {
            "P352": "proteins",      # UniProt protein ID
            "P683": "chemicals",     # ChEBI ID
            "P486": "medical",       # MeSH ID
            "P662": "chemicals",     # PubChem ID
            "P4333": "genetics",     # GenBank ID
            "P699": "diseases",      # Disease Ontology ID
        }
        
        if property_id in biological_properties:
            return biological_properties[property_id]
        
        # Extract from property name/description
        name = property_data.get("labels", {}).get("en", {}).get("value", "").lower()
        description = property_data.get("descriptions", {}).get("en", {}).get("value", "").lower()
        
        if any(term in name or term in description for term in ["protein", "uniprot"]):
            return "proteins"
        elif any(term in name or term in description for term in ["chemical", "compound", "chebi", "pubchem"]):
            return "chemicals"
        elif any(term in name or term in description for term in ["gene", "dna", "rna", "genbank"]):
            return "genetics"
        elif any(term in name or term in description for term in ["disease", "medical", "mesh"]):
            return "medical"
        
        return "general"
    
    async def _validate_identifier_format(
        self, 
        identifier: str, 
        property_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate identifier format against property constraints"""
        
        regex_pattern = property_metadata.get("regex_pattern")
        if not regex_pattern:
            return {
                "valid": True,
                "note": "No format validation available for this property"
            }
        
        try:
            import re
            if re.match(regex_pattern, identifier):
                return {
                    "valid": True,
                    "pattern": regex_pattern,
                    "note": "Identifier matches expected format"
                }
            else:
                return {
                    "valid": False,
                    "pattern": regex_pattern,
                    "example": property_metadata.get("example_value"),
                    "note": f"Identifier does not match pattern: {regex_pattern}"
                }
        except Exception as e:
            return {
                "valid": True,
                "note": f"Validation error: {e}"
            }
    
    async def _discover_endpoint_schema(self, endpoint_url: str) -> Optional[Dict]:
        """Discover endpoint schema using service description infrastructure"""
        
        if not self.discovery_engine:
            return None
        
        if endpoint_url in self.endpoint_schemas:
            return self.endpoint_schemas[endpoint_url]
        
        try:
            # Use service description discovery from wikidata-mcp
            schema = await self.discovery_engine.discover_schema(
                endpoint_url, 
                discovery_method="service_description"
            )
            
            # Convert to dictionary format for caching
            schema_dict = {
                "endpoint": schema.endpoint,
                "vocabularies": schema.vocabularies,
                "classes": {k: v for k, v in schema.classes.items()},
                "properties": {k: v for k, v in schema.properties.items()},
                "performance_hints": schema.performance_hints,
                "agent_guidance": schema.agent_guidance,
                "discovery_metadata": schema.discovery_metadata
            }
            
            self.endpoint_schemas[endpoint_url] = schema_dict
            return schema_dict
            
        except Exception as e:
            log.warning(f"Failed to discover schema for {endpoint_url}: {e}")
            return None
    
    async def _resolve_in_wikidata(
        self, 
        property_id: str, 
        identifier: str
    ) -> Dict[str, Any]:
        """Resolve identifier in Wikidata"""
        
        try:
            # SPARQL query to find entities with this external identifier
            query = f"""
            SELECT ?entity ?entityLabel ?instanceOf ?instanceOfLabel WHERE {{
                ?entity wdt:{property_id} "{identifier}" .
                OPTIONAL {{ ?entity wdt:P31 ?instanceOf }}
                SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en" }}
            }}
            LIMIT 50
            """
            
            result = await self.wikidata_client.sparql_query(query)
            bindings = result.get("results", {}).get("bindings", [])
            
            entities = []
            for binding in bindings:
                entity_info = {
                    "id": self._extract_entity_id(binding.get("entity", {}).get("value", "")),
                    "label": binding.get("entityLabel", {}).get("value", ""),
                    "instance_of": binding.get("instanceOf", {}).get("value", ""),
                    "instance_of_label": binding.get("instanceOfLabel", {}).get("value", "")
                }
                entities.append(entity_info)
            
            return {
                "found_entities": entities,
                "total_count": len(entities),
                "query_used": query
            }
            
        except Exception as e:
            log.error(f"Failed to resolve in Wikidata: {e}")
            return {
                "found_entities": [],
                "total_count": 0,
                "error": str(e)
            }
    
    def _extract_entity_id(self, entity_uri: str) -> str:
        """Extract Wikidata entity ID from URI"""
        if "/entity/" in entity_uri:
            return entity_uri.split("/entity/")[-1]
        return entity_uri
    
    def _prepare_crosswalk_suggestions(
        self,
        wikidata_entities: List[Dict[str, Any]],
        property_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Prepare agentic crosswalk suggestions without doing complex queries"""
        
        if not wikidata_entities:
            return {"agentic_suggestions": []}
        
        entity = wikidata_entities[0]  # Focus on first entity
        entity_id = entity.get("id")
        entity_label = entity.get("label", "")
        
        # Prepare agentic workflow suggestions
        suggestions = {
            "agentic_workflow": [
                f"Use cl_wikidata entity {entity_id} to see all external identifiers",
                f"Use cl_describe wd:{entity_id} to get complete entity details",
                f"Look for P638 (PDB), P683 (ChEBI), P486 (MeSH) and other external IDs",
                f"Use cl_resolve with those property IDs to follow the crosswalk chain"
            ],
            "crosswalk_pattern": f"Found {entity_label} ({entity_id}) - now explore its external identifiers",
            "expected_databases": self._get_expected_databases(property_metadata.get("domain", "general")),
            "workflow_example": [
                f"1. cl_wikidata entity {entity_id}  # See all properties",
                f"2. cl_resolve P638 <pdb_id>       # Follow PDB structure links", 
                f"3. cl_resolve P683 <chebi_id>     # Follow chemical compound links",
                f"4. Continue crosswalk chain across databases"
            ]
        }
        
        return suggestions
    
    def _get_expected_databases(self, domain: str) -> List[str]:
        """Get expected external databases for a domain"""
        
        database_map = {
            "proteins": [
                "P638 (PDB) - Protein structures",
                "P683 (ChEBI) - Chemical compounds", 
                "P486 (MeSH) - Medical terms",
                "P4333 (GenBank) - Genetic sequences",
                "P699 (Disease Ontology) - Disease classifications"
            ],
            "chemicals": [
                "P662 (PubChem) - Chemical properties",
                "P683 (ChEBI) - Chemical ontology",
                "P486 (MeSH) - Medical subject headings",
                "P2275 (InChI) - Chemical identifiers"
            ],
            "genetics": [
                "P4333 (GenBank) - Sequence database",
                "P352 (UniProt) - Protein sequences",
                "P699 (Disease Ontology) - Genetic diseases"
            ],
            "medical": [
                "P486 (MeSH) - Medical terminology", 
                "P699 (Disease Ontology) - Disease classifications",
                "P2892 (UMLS) - Medical concepts"
            ]
        }
        
        return database_map.get(domain, [
            "P352 (UniProt) - Proteins",
            "P683 (ChEBI) - Chemicals", 
            "P638 (PDB) - Structures",
            "P486 (MeSH) - Medical terms"
        ])
    
    async def _discover_external_ontology(self, property_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Use OntFetch for external database ontology discovery"""
        
        sparql_endpoint = property_metadata.get("sparql_endpoint")
        if not sparql_endpoint:
            return {"success": False, "note": "No SPARQL endpoint available"}
        
        try:
            # Use OntFetch to discover endpoint ontology
            fetcher = AgenticOntologyFetcher()
            ontology_result = await fetcher.discover_ontology(
                target=sparql_endpoint,
                ontology_type="sparql",
                domain=property_metadata.get("domain"),
                force_refresh=False
            )
            
            return ontology_result
            
        except Exception as e:
            log.warning(f"Failed to discover external ontology: {e}")
            return {
                "success": False,
                "error": str(e),
                "note": "OntFetch discovery failed"
            }
    
    async def _resolve_in_external_database(
        self,
        identifier: str,
        property_metadata: Dict[str, Any],
        external_ontology: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Resolve identifier in external database using discovered ontology"""
        
        sparql_endpoint = property_metadata.get("sparql_endpoint")
        if not sparql_endpoint or not external_ontology.get("success"):
            return {}
        
        try:
            # Generate SPARQL query based on discovered ontology
            query = self._generate_external_query(identifier, property_metadata, external_ontology)
            
            if not query:
                return {"note": "Could not generate appropriate query for external endpoint"}
            
            # Execute query against external endpoint
            result = await self.wikidata_client.sparql_query(query)
            
            bindings = result.get("results", {}).get("bindings", [])
            
            return {
                "external_endpoint": sparql_endpoint,
                "results": bindings[:10],  # Limit results for context management
                "total_found": len(bindings),
                "query_used": query,
                "ontology_guided": True
            }
            
        except Exception as e:
            log.warning(f"Failed to resolve in external database: {e}")
            return {
                "external_endpoint": sparql_endpoint,
                "error": str(e),
                "note": "External database resolution failed"
            }
    
    def _generate_external_query(
        self,
        identifier: str,
        property_metadata: Dict[str, Any],
        external_ontology: Dict[str, Any]
    ) -> Optional[str]:
        """Generate SPARQL query for external endpoint based on discovered ontology"""
        
        domain = property_metadata.get("domain", "general")
        vocabularies = external_ontology.get("vocabularies", {})
        
        # Domain-specific query generation
        if domain == "proteins" and "up" in vocabularies:
            # UniProt query pattern
            return f"""
            PREFIX up: <{vocabularies.get("up", "http://purl.uniprot.org/core/")}>
            SELECT ?protein ?name ?organism ?function WHERE {{
                ?protein up:mnemonic "{identifier}" .
                OPTIONAL {{ ?protein up:recommendedName/up:fullName ?name }}
                OPTIONAL {{ ?protein up:organism/up:scientificName ?organism }}
                OPTIONAL {{ ?protein up:annotation/up:comment ?function }}
            }}
            LIMIT 10
            """
        
        elif domain == "chemicals" and any(prefix in vocabularies for prefix in ["chebi", "pubchem"]):
            # Chemical database query pattern
            chebi_ns = vocabularies.get("chebi", "http://purl.obolibrary.org/obo/")
            return f"""
            PREFIX chebi: <{chebi_ns}>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            SELECT ?compound ?name ?formula ?inchi WHERE {{
                ?compound rdfs:label ?name .
                FILTER(CONTAINS(STR(?compound), "{identifier}"))
                OPTIONAL {{ ?compound chebi:formula ?formula }}
                OPTIONAL {{ ?compound chebi:inchi ?inchi }}
            }}
            LIMIT 10
            """
        
        # Generic query pattern using discovered vocabularies
        if vocabularies:
            return f"""
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            SELECT ?resource ?label ?type WHERE {{
                ?resource rdfs:label ?label .
                OPTIONAL {{ ?resource a ?type }}
                FILTER(CONTAINS(STR(?resource), "{identifier}") || CONTAINS(?label, "{identifier}"))
            }}
            LIMIT 10
            """
        
        return None
    
    async def _compose_vocabulary_context(
        self,
        property_metadata: Dict[str, Any],
        endpoint_schema: Optional[Dict]
    ) -> Dict[str, Any]:
        """Compose vocabulary context using cogitarelink registry"""
        
        try:
            context_prefixes = []
            
            # Add domain-specific vocabularies from registry
            domain = property_metadata.get("domain", "general")
            if domain == "proteins":
                # Add bioschemas context for proteins
                try:
                    bioschemas_entry = registry.resolve("bioschemas")
                    context_prefixes.append("bioschemas")
                except KeyError:
                    pass
            
            # Add schema.org for general structured data
            try:
                schema_entry = registry.resolve("schema")
                context_prefixes.append("schema")
            except KeyError:
                pass
            
            # Compose final context if we have vocabularies
            if context_prefixes:
                composed_context = composer.compose(context_prefixes)
                
                # Add discovered endpoint vocabularies
                if endpoint_schema and endpoint_schema.get("vocabularies"):
                    endpoint_vocabs = endpoint_schema["vocabularies"]
                    
                    # Merge with composed context
                    if "@context" in composed_context:
                        if isinstance(composed_context["@context"], dict):
                            composed_context["@context"].update(endpoint_vocabs)
                        elif isinstance(composed_context["@context"], list):
                            composed_context["@context"].append(endpoint_vocabs)
                
                return {
                    "composed_context": composed_context,
                    "prefixes_used": context_prefixes,
                    "endpoint_vocabularies": endpoint_schema.get("vocabularies", {}) if endpoint_schema else {},
                    "domain": domain
                }
        
        except Exception as e:
            log.warning(f"Failed to compose vocabulary context: {e}")
        
        return {}
    
    def _get_queried_endpoints(self, target_endpoint: Optional[str]) -> List[str]:
        """Get list of endpoints that were queried"""
        endpoints = ["https://query.wikidata.org/sparql"]  # Always query Wikidata
        if target_endpoint:
            endpoints.append(target_endpoint)
        return endpoints
    
    def _generate_crosswalk_suggestions(
        self,
        property_metadata: Dict[str, Any],
        wikidata_results: Dict[str, Any],
        cross_references: Dict[str, Any],
        external_ontology: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate intelligent suggestions based on crosswalk analysis"""
        
        suggestions = {
            "next_tools": [],
            "research_patterns": [],
            "crosswalk_opportunities": [],
            "workflow_steps": []
        }
        
        # Suggest follow-up based on results
        found_entities = wikidata_results.get("found_entities", [])
        if found_entities:
            entity_id = found_entities[0].get("id")
            entity_label = found_entities[0].get("label", "")
            if entity_id:
                suggestions["next_tools"].extend([
                    f"cl_wikidata entity {entity_id}",
                    f"cl_describe wd:{entity_id}"
                ])
                
                # Add the agentic workflow suggestions from cross_references
                if cross_references.get("agentic_workflow"):
                    suggestions["workflow_steps"] = cross_references["agentic_workflow"]
                
                # Add expected databases for this domain
                if cross_references.get("expected_databases"):
                    suggestions["crosswalk_opportunities"] = [
                        f"🔗 Expected external IDs to look for in {entity_label}:"
                    ] + cross_references["expected_databases"]
        
        # Domain-specific research patterns
        domain = property_metadata.get("domain", "general")
        if domain == "proteins":
            suggestions["research_patterns"].extend([
                "🧬 PROTEIN CROSSWALK: Wikidata → UniProt → PDB → Reactome → PathBank",
                "🔗 AGENTIC WORKFLOW: Use cl_wikidata to see all external IDs, then cl_resolve each",
                "📊 INTEGRATION: Combine sequence, structure, pathway, and disease data"
            ])
        
        elif domain == "chemicals":
            suggestions["research_patterns"].extend([
                "⚗️ CHEMICAL CROSSWALK: Wikidata → ChEBI → PubChem → ChEMBL → DrugBank",
                "🔗 AGENTIC WORKFLOW: Use cl_wikidata to discover external IDs, then resolve them",
                "📊 SAFETY PIPELINE: Structure → Properties → Bioactivity → Toxicity"
            ])
        
        # Add crosswalk pattern explanation
        if cross_references.get("crosswalk_pattern"):
            suggestions["crosswalk_opportunities"].insert(0, 
                f"✅ {cross_references['crosswalk_pattern']}"
            )
        
        # Add general suggestions if none found
        if not suggestions["next_tools"]:
            suggestions["next_tools"].extend([
                f"cl_property {property_metadata['property_id']}",
                "cl_discover --endpoint to explore related databases"
            ])
        
        return suggestions


# CLI interface
@click.command()
@click.argument('property_id')
@click.argument('identifier', required=False)
@click.option('--discover', is_flag=True, help='Discover property metadata only')
@click.option('--validate/--no-validate', default=True, help='Validate identifier format')
@click.option('--follow/--no-follow', default=True, help='Follow links to external databases')
@click.option('--context/--no-context', default=True, help='Include vocabulary context')
@click.option('--timeout', default=30, help='Query timeout in seconds')
def resolve(property_id: str, identifier: Optional[str], discover: bool, validate: bool, 
           follow: bool, context: bool, timeout: int):
    """
    Universal identifier resolution with vocabulary intelligence
    
    Automatically discovers vocabulary context and resolves identifiers across
    biological databases using service description-powered schema discovery.
    
    Examples:
        cl_resolve P352 P01308                # Resolve UniProt protein ID
        cl_resolve P683 CHEBI:15365          # Resolve ChEBI compound ID  
        cl_resolve --discover P352           # Discover property metadata
        cl_resolve --no-validate P352 CUSTOM # Skip format validation
    
    Biological Research Patterns:
        🧬 PROTEIN WORKFLOW: P352 (UniProt) → sequence → structure → function
        ⚗️ CHEMICAL WORKFLOW: P683 (ChEBI) → structure → properties → bioactivity
        🧬 GENETIC WORKFLOW: P4333 (GenBank) → sequence → annotation → pathways
        🏥 MEDICAL WORKFLOW: P486 (MeSH) → disease → pathways → drug targets
    """
    
    async def run_resolution():
        try:
            resolver = UniversalIdentifierResolver()
            
            if discover:
                # Discovery-only mode
                property_metadata = await resolver._discover_property_metadata(property_id)
                
                response = {
                    "success": True,
                    "data": {
                        "property_metadata": property_metadata,
                        "discovery_only": True
                    },
                    "suggestions": {
                        "next_tools": [
                            f"cl_resolve {property_id} <identifier>",
                            f"cl_property {property_id}",
                            "Use discovered metadata to resolve actual identifiers"
                        ],
                        "example_usage": [
                            f"cl_resolve {property_id} {property_metadata.get('example_value', '<identifier>')}"
                        ] if property_metadata.get('example_value') else []
                    }
                }
            else:
                # Full resolution - require identifier
                if not identifier:
                    response = {
                        "success": False,
                        "error": {
                            "code": "MISSING_IDENTIFIER",
                            "message": "Identifier required for resolution (use --discover for metadata only)",
                            "suggestions": [
                                f"cl_resolve {property_id} <identifier>",
                                f"cl_resolve --discover {property_id}",
                                "Provide both property_id and identifier for resolution"
                            ]
                        }
                    }
                else:
                    response = await resolver.resolve_identifier(
                        property_id=property_id,
                        identifier=identifier,
                        validate=validate,
                        follow_links=follow,
                        include_context=context
                    )
            
            click.echo(json.dumps(response, indent=2))
            
        except Exception as e:
            error_response = {
                "success": False,
                "error": {
                    "code": "RESOLUTION_ERROR",
                    "message": f"Resolution failed: {str(e)}",
                    "suggestions": [
                        "Check property ID format (e.g., P352, P683)",
                        "Verify identifier value exists",
                        "Try with --no-validate for format issues",
                        "Use --discover to inspect property metadata"
                    ]
                }
            }
            click.echo(json.dumps(error_response, indent=2))
    
    # Run async function
    asyncio.run(run_resolution())

if __name__ == "__main__":
    resolve()