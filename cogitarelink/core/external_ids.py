#!/usr/bin/env python3
"""
Dynamic External Identifier Discovery

Replaces hardcoded property mappings with dynamic discovery from Wikidata.
Discovers all external identifier properties with their metadata, formatter URLs, and descriptions.
"""

from __future__ import annotations

import asyncio
import json
from typing import Dict, List, Any, Optional
from ..adapters.wikidata_client import WikidataClient
from ..core.debug import get_logger

log = get_logger("external_ids")

class ExternalIdentifierDiscovery:
    """Dynamic discovery of external identifier properties from Wikidata"""
    
    def __init__(self, cache_duration: int = 3600):
        self.wikidata_client = WikidataClient()
        self.property_cache = {}
        self.cache_duration = cache_duration
        
    async def discover_all_external_id_properties(self) -> Dict[str, Any]:
        """
        Discover all external identifier properties from Wikidata using SPARQL.
        
        Returns mapping from property ID to database metadata.
        This replaces hardcoded mappings in cl_describe and cl_follow.
        """
        
        if "all_external_properties" in self.property_cache:
            return self.property_cache["all_external_properties"]
        
        try:
            # SPARQL query to find all external identifier properties
            query = """
            SELECT DISTINCT ?property ?propertyLabel ?propertyDescription 
                   ?formatterURL ?exampleValue ?regex ?sparqlEndpoint
                   ?officialWebsite ?subjectItem ?subjectItemLabel WHERE {
              ?property wikibase:propertyType wikibase:ExternalId .
              
              # Get formatter URL if available
              OPTIONAL { ?property wdt:P1630 ?formatterURL }
              
              # Get example value if available  
              OPTIONAL { ?property wdt:P1855 ?exampleValue }
              
              # Get regular expression pattern if available
              OPTIONAL { ?property wdt:P1793 ?regex }
              
              # Get SPARQL endpoint if available
              OPTIONAL { ?property wdt:P1696 ?sparqlEndpoint }
              
              # Get official website of the subject item
              OPTIONAL { 
                ?property wdt:P1629 ?subjectItem .
                ?subjectItem wdt:P856 ?officialWebsite .
              }
              
              SERVICE wikibase:label { bd:serviceParam wikibase:language "en" }
            }
            ORDER BY ?property
            """
            
            result = await self.wikidata_client.sparql_query(query)
            bindings = result.get("results", {}).get("bindings", [])
            
            properties = {}
            
            for binding in bindings:
                property_id = self._extract_property_id(binding.get("property", {}).get("value", ""))
                
                if not property_id:
                    continue
                
                # Extract metadata
                property_data = {
                    "property_id": property_id,
                    "name": binding.get("propertyLabel", {}).get("value", f"Property {property_id}"),
                    "description": binding.get("propertyDescription", {}).get("value", ""),
                    "formatter_url": binding.get("formatterURL", {}).get("value"),
                    "example_value": binding.get("exampleValue", {}).get("value"),
                    "regex_pattern": binding.get("regex", {}).get("value"),
                    "sparql_endpoint": binding.get("sparqlEndpoint", {}).get("value"),
                    "official_website": binding.get("officialWebsite", {}).get("value"),
                    "subject_item": self._extract_entity_id(binding.get("subjectItem", {}).get("value", "")),
                    "subject_item_label": binding.get("subjectItemLabel", {}).get("value", ""),
                    "database_name": self._generate_database_name(binding),
                    "domain": self._classify_domain(binding)
                }
                
                properties[property_id] = property_data
                
            log.info(f"Discovered {len(properties)} external identifier properties")
            
            # Cache the results
            self.property_cache["all_external_properties"] = properties
            
            return properties
            
        except Exception as e:
            log.error(f"Failed to discover external identifier properties: {e}")
            return {}
    
    async def get_external_ids_for_entity(self, entity_id: str) -> Dict[str, Any]:
        """
        Get all external identifiers for a specific Wikidata entity.
        
        This dynamically discovers what external IDs an entity has,
        replacing the need for hardcoded property mappings.
        """
        
        try:
            # Get all properties for this entity
            entity_data = await self.wikidata_client.get_entities([entity_id])
            
            if entity_id not in entity_data.get('entities', {}):
                return {}
            
            entity_info = entity_data['entities'][entity_id]
            claims = entity_info.get('claims', {})
            
            # Get property metadata for all external ID properties
            all_properties = await self.discover_all_external_id_properties()
            
            # Extract external identifiers that exist for this entity
            external_ids = {}
            
            for prop_id, prop_metadata in all_properties.items():
                if prop_id in claims:
                    values = []
                    for claim in claims[prop_id][:5]:  # Limit to first 5 per database
                        if 'mainsnak' in claim and 'datavalue' in claim['mainsnak']:
                            value = claim['mainsnak']['datavalue']['value']
                            if isinstance(value, str):
                                values.append(value)
                            elif isinstance(value, dict):
                                if 'text' in value:
                                    values.append(value['text'])
                                elif 'id' in value:  # Entity reference
                                    values.append(value['id'])
                    
                    if values:
                        db_name = prop_metadata['database_name']
                        external_ids[db_name] = {
                            "values": values,
                            "property_id": prop_id,
                            "property_name": prop_metadata['name'],
                            "formatter_url": prop_metadata['formatter_url'],
                            "official_website": prop_metadata['official_website'],
                            "domain": prop_metadata['domain'],
                            "description": prop_metadata['description']
                        }
            
            return external_ids
            
        except Exception as e:
            log.error(f"Failed to get external IDs for {entity_id}: {e}")
            return {}
    
    def _extract_property_id(self, property_uri: str) -> Optional[str]:
        """Extract property ID from Wikidata URI"""
        if "/entity/" in property_uri:
            prop_id = property_uri.split("/entity/")[-1]
            if prop_id.startswith("P") and prop_id[1:].isdigit():
                return prop_id
        return None
    
    def _extract_entity_id(self, entity_uri: str) -> Optional[str]:
        """Extract entity ID from Wikidata URI"""
        if "/entity/" in entity_uri:
            entity_id = entity_uri.split("/entity/")[-1]
            if (entity_id.startswith("Q") or entity_id.startswith("P")) and entity_id[1:].isdigit():
                return entity_id
        return None
    
    def _generate_database_name(self, binding: Dict[str, Any]) -> str:
        """Generate a clean database name from property metadata"""
        
        property_label = binding.get("propertyLabel", {}).get("value", "")
        subject_item_label = binding.get("subjectItemLabel", {}).get("value", "")
        
        # Clean up common patterns
        if property_label:
            # Remove "ID" suffixes and common phrases
            name = property_label.lower()
            name = name.replace(" id", "").replace(" identifier", "")
            name = name.replace("registry number", "registry")
            name = name.replace("database", "").strip()
            
            # Convert to snake_case
            name = name.replace(" ", "_").replace("-", "_")
            
            # Special cases for well-known databases
            if "uniprot" in name:
                return "uniprot"
            elif "chebi" in name:
                return "chebi"
            elif "pubchem" in name:
                if "cid" in name:
                    return "pubchem_cid"
                elif "sid" in name:
                    return "pubchem_sid"
                else:
                    return "pubchem"
            elif "mesh" in name:
                return "mesh"
            elif "wikipathways" in name:
                return "wikipathways"
            elif "drugbank" in name:
                return "drugbank"
            elif "cas" in name:
                return "cas"
            elif "chembl" in name:
                return "chembl"
            elif "pdb" in name:
                return "pdb"
            elif "ensembl" in name:
                return "ensembl"
            elif "ncbi" in name:
                if "gene" in name:
                    return "ncbi_gene"
                else:
                    return "ncbi"
            elif "refseq" in name:
                return "refseq"
            elif "kegg" in name:
                return "kegg"
            else:
                return name
        
        # Fallback to subject item label
        if subject_item_label:
            return subject_item_label.lower().replace(" ", "_")
        
        # Ultimate fallback
        property_id = self._extract_property_id(binding.get("property", {}).get("value", ""))
        return f"property_{property_id.lower()}" if property_id else "unknown"
    
    def _classify_domain(self, binding: Dict[str, Any]) -> str:
        """Classify the domain of an external identifier property"""
        
        property_label = binding.get("propertyLabel", {}).get("value", "").lower()
        description = binding.get("propertyDescription", {}).get("value", "").lower()
        subject_label = binding.get("subjectItemLabel", {}).get("value", "").lower()
        
        combined_text = f"{property_label} {description} {subject_label}"
        
        # Domain classification
        if any(term in combined_text for term in ["protein", "uniprot", "pdb", "enzyme", "amino", "peptide"]):
            return "proteins"
        elif any(term in combined_text for term in ["chemical", "compound", "chebi", "pubchem", "cas", "chembl", "drug", "molecule"]):
            return "chemicals"
        elif any(term in combined_text for term in ["gene", "dna", "rna", "genome", "genbank", "ensembl", "ncbi", "genetic"]):
            return "genetics"
        elif any(term in combined_text for term in ["disease", "medical", "mesh", "icd", "snomed", "umls", "health"]):
            return "medical"
        elif any(term in combined_text for term in ["pathway", "biological process", "go", "reactome", "kegg", "wikipathways"]):
            return "pathways"
        elif any(term in combined_text for term in ["taxonomy", "species", "organism", "taxon"]):
            return "taxonomy"
        elif any(term in combined_text for term in ["publication", "pmid", "doi", "literature"]):
            return "publications"
        elif any(term in combined_text for term in ["geographic", "location", "place", "geonames"]):
            return "geography"
        else:
            return "general"

# Global instance for use across the codebase
external_id_discovery = ExternalIdentifierDiscovery()

async def get_dynamic_external_id_mapping() -> Dict[str, str]:
    """
    Get dynamic mapping from property ID to database name.
    
    This replaces the hardcoded database_properties mappings in cl_describe and cl_follow.
    
    Returns:
        Dict mapping property IDs (e.g., "P352") to database names (e.g., "uniprot")
    """
    
    all_properties = await external_id_discovery.discover_all_external_id_properties()
    
    mapping = {}
    for prop_id, prop_data in all_properties.items():
        mapping[prop_id] = prop_data['database_name']
    
    return mapping

async def get_external_ids_for_entity(entity_id: str) -> Dict[str, Any]:
    """
    Get all external identifiers for a Wikidata entity with full metadata.
    
    This replaces the _extract_cross_references functions in cl_describe and cl_follow.
    
    Args:
        entity_id: Wikidata entity ID (e.g., "Q44054606")
        
    Returns:
        Dict mapping database names to external ID data with metadata
    """
    
    return await external_id_discovery.get_external_ids_for_entity(entity_id)

if __name__ == "__main__":
    # Test the dynamic discovery
    async def test_discovery():
        print("🔍 Testing Dynamic External Identifier Discovery")
        print("=" * 60)
        
        # Test 1: Discover all properties
        print("\n📋 Discovering all external identifier properties...")
        all_props = await external_id_discovery.discover_all_external_id_properties()
        print(f"Found {len(all_props)} external identifier properties")
        
        # Show a few examples
        print("\n📊 Sample properties:")
        for i, (prop_id, prop_data) in enumerate(list(all_props.items())[:5]):
            print(f"   {prop_id}: {prop_data['name']} ({prop_data['database_name']}) - {prop_data['domain']}")
        
        # Test 2: Get external IDs for specific entity
        print("\n🧬 Testing with Q44054606 (mouse glycogen pathway)...")
        entity_external_ids = await external_id_discovery.get_external_ids_for_entity("Q44054606")
        
        print(f"Found {len(entity_external_ids)} external identifiers:")
        for db_name, db_data in entity_external_ids.items():
            print(f"   {db_name}: {db_data['values']} ({db_data['property_id']})")
        
        # Test 3: Check if WikiPathways is found
        if 'wikipathways' in entity_external_ids:
            wp_data = entity_external_ids['wikipathways']
            print(f"\n✅ WikiPathways found: {wp_data['values']}")
            print(f"   Property: {wp_data['property_id']} - {wp_data['property_name']}")
            print(f"   URL: {wp_data['formatter_url']}")
        else:
            print(f"\n❌ WikiPathways not found in dynamic discovery")
    
    asyncio.run(test_discovery())