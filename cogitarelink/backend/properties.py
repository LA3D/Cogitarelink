"""Discovery Infrastructure: Self-configuring property and entity type discovery.

Foundation module that eliminates hard-coded assumptions by dynamically discovering
what properties and entity types actually mean from SPARQL endpoints.
"""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Any, Set

from .sparql import sparql_engine
from .cache import cache_manager
from ..utils.logging import get_logger

log = get_logger("discovery_infrastructure")


@dataclass
class PropertyInfo:
    """Information about a discovered property."""
    property_id: str
    label: str
    description: str
    datatype: Optional[str] = None
    domain: Optional[str] = None
    range: Optional[str] = None
    is_external_ref: bool = False
    
    
@dataclass
class EntityTypeInfo:
    """Information about a discovered entity type."""
    type_id: str
    label: str
    description: str
    subclass_of: List[str]
    instance_count: Optional[int] = None
    domain_category: Optional[str] = None  # biology, chemistry, general, etc.


class PropertyDiscovery:
    """Dynamically discover what properties mean from SPARQL endpoints."""
    
    def __init__(self):
        self.cache_prefix = "property_discovery"
        
    def discover_properties(self, property_ids: List[str], endpoint: str = "wikidata") -> Dict[str, PropertyInfo]:
        """Discover information about properties from the endpoint."""
        if not property_ids:
            return {}
            
        # Check cache first
        cache_key = f"{self.cache_prefix}:{endpoint}:{':'.join(sorted(property_ids))}"
        cached = cache_manager.get(cache_key)
        if cached:
            return {pid: PropertyInfo(**info) for pid, info in cached.items()}
        
        discovered = {}
        
        if endpoint == "wikidata":
            discovered = self._discover_wikidata_properties(property_ids)
        else:
            discovered = self._discover_sparql_properties(property_ids, endpoint)
            
        # Cache results
        cache_data = {pid: info.__dict__ for pid, info in discovered.items()}
        cache_manager.set(cache_key, cache_data, ttl=86400)  # 24 hours
        
        return discovered
    
    def _discover_wikidata_properties(self, property_ids: List[str]) -> Dict[str, PropertyInfo]:
        """Discover Wikidata properties using SPARQL."""
        # Build SPARQL query for property information
        property_values = " ".join([f"wd:{pid}" for pid in property_ids])
        
        sparql_query = f"""
        SELECT ?prop ?propLabel ?propDescription ?datatype ?domain ?range WHERE {{
            VALUES ?prop {{ {property_values} }}
            OPTIONAL {{ ?prop wdt:P31 ?datatype }}
            OPTIONAL {{ ?prop wdt:P1629 ?domain }}
            OPTIONAL {{ ?prop wdt:P1629 ?range }}
            SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en" }}
        }}
        """
        
        try:
            result = discovery_engine.query_endpoint("wikidata", sparql_query)
            properties = {}
            
            if result.get("success"):
                for binding in result.get("results", []):
                    prop_uri = binding.get("prop", {}).get("value", "")
                    prop_id = prop_uri.split("/")[-1] if prop_uri else ""
                    
                    if prop_id in property_ids:
                        label = binding.get("propLabel", {}).get("value", prop_id)
                        description = binding.get("propDescription", {}).get("value", "")
                        datatype = binding.get("datatype", {}).get("value", "")
                        domain = binding.get("domain", {}).get("value", "")
                        range_val = binding.get("range", {}).get("value", "")
                        
                        # Determine if this is an external reference property
                        is_external_ref = self._is_external_reference_property(prop_id, label, description)
                        
                        properties[prop_id] = PropertyInfo(
                            property_id=prop_id,
                            label=label,
                            description=description,
                            datatype=datatype.split("/")[-1] if datatype else None,
                            domain=domain.split("/")[-1] if domain else None,
                            range=range_val.split("/")[-1] if range_val else None,
                            is_external_ref=is_external_ref
                        )
            
            # Add any missing properties with basic info
            for prop_id in property_ids:
                if prop_id not in properties:
                    properties[prop_id] = PropertyInfo(
                        property_id=prop_id,
                        label=prop_id,
                        description="Property information not found",
                        is_external_ref=self._is_external_reference_property(prop_id, "", "")
                    )
            
            return properties
            
        except Exception as e:
            log.error(f"Property discovery failed for {property_ids}: {e}")
            # Return basic fallback information
            return {
                pid: PropertyInfo(
                    property_id=pid,
                    label=pid,
                    description="Discovery failed",
                    is_external_ref=self._is_external_reference_property(pid, "", "")
                ) for pid in property_ids
            }
    
    def _discover_sparql_properties(self, property_ids: List[str], endpoint: str) -> Dict[str, PropertyInfo]:
        """Discover properties from general SPARQL endpoints."""
        # For non-Wikidata endpoints, use basic RDFS discovery
        discovered = {}
        
        for prop_id in property_ids:
            # Try to discover using RDFS patterns
            sparql_query = f"""
            SELECT ?label ?comment WHERE {{
                <{prop_id}> rdfs:label ?label .
                OPTIONAL {{ <{prop_id}> rdfs:comment ?comment }}
                FILTER(LANG(?label) = "en" || LANG(?label) = "")
            }} LIMIT 1
            """
            
            try:
                result = discovery_engine.query_endpoint(endpoint, sparql_query)
                
                if result.get("success") and result.get("results"):
                    binding = result["results"][0]
                    label = binding.get("label", {}).get("value", prop_id)
                    description = binding.get("comment", {}).get("value", "")
                else:
                    label = prop_id
                    description = "Property from " + endpoint
                
                discovered[prop_id] = PropertyInfo(
                    property_id=prop_id,
                    label=label,
                    description=description,
                    is_external_ref=False  # Conservative for unknown endpoints
                )
                
            except Exception as e:
                log.debug(f"Failed to discover property {prop_id} on {endpoint}: {e}")
                discovered[prop_id] = PropertyInfo(
                    property_id=prop_id,
                    label=prop_id,
                    description="Discovery failed",
                    is_external_ref=False
                )
        
        return discovered
    
    def _is_external_reference_property(self, prop_id: str, label: str, description: str) -> bool:
        """Determine if a property represents an external reference."""
        # Use heuristics to identify external reference properties
        external_indicators = [
            "id", "identifier", "registry", "database", "accession",
            "uniprot", "ensembl", "pdb", "pubchem", "chembl", "mesh", "cas"
        ]
        
        text_to_check = f"{prop_id} {label} {description}".lower()
        return any(indicator in text_to_check for indicator in external_indicators)


class EntityTypeDiscovery:
    """Dynamically discover what entity types mean from SPARQL endpoints."""
    
    def __init__(self):
        self.cache_prefix = "entity_type_discovery"
        
    def discover_entity_types(self, type_ids: List[str], endpoint: str = "wikidata") -> Dict[str, EntityTypeInfo]:
        """Discover information about entity types from the endpoint."""
        if not type_ids:
            return {}
            
        # Check cache first
        cache_key = f"{self.cache_prefix}:{endpoint}:{':'.join(sorted(type_ids))}"
        cached = cache_manager.get(cache_key)
        if cached:
            return {tid: EntityTypeInfo(**info) for tid, info in cached.items()}
        
        discovered = {}
        
        if endpoint == "wikidata":
            discovered = self._discover_wikidata_entity_types(type_ids)
        else:
            discovered = self._discover_sparql_entity_types(type_ids, endpoint)
        
        # Cache results
        cache_data = {tid: info.__dict__ for tid, info in discovered.items()}
        cache_manager.set(cache_key, cache_data, ttl=86400)  # 24 hours
        
        return discovered
    
    def _discover_wikidata_entity_types(self, type_ids: List[str]) -> Dict[str, EntityTypeInfo]:
        """Discover Wikidata entity types using SPARQL."""
        type_values = " ".join([f"wd:{tid}" for tid in type_ids])
        
        sparql_query = f"""
        SELECT ?type ?typeLabel ?typeDescription ?superclass WHERE {{
            VALUES ?type {{ {type_values} }}
            OPTIONAL {{ ?type wdt:P279 ?superclass }}
            SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en" }}
        }}
        """
        
        try:
            result = discovery_engine.query_endpoint("wikidata", sparql_query)
            types = defaultdict(lambda: {"superclasses": set()})
            
            if result.get("success"):
                for binding in result.get("results", []):
                    type_uri = binding.get("type", {}).get("value", "")
                    type_id = type_uri.split("/")[-1] if type_uri else ""
                    
                    if type_id in type_ids:
                        label = binding.get("typeLabel", {}).get("value", type_id)
                        description = binding.get("typeDescription", {}).get("value", "")
                        superclass_uri = binding.get("superclass", {}).get("value", "")
                        superclass_id = superclass_uri.split("/")[-1] if superclass_uri else ""
                        
                        types[type_id]["label"] = label
                        types[type_id]["description"] = description
                        if superclass_id:
                            types[type_id]["superclasses"].add(superclass_id)
            
            # Convert to EntityTypeInfo objects
            discovered = {}
            for type_id in type_ids:
                type_data = types.get(type_id, {})
                label = type_data.get("label", type_id)
                description = type_data.get("description", "")
                superclasses = list(type_data.get("superclasses", set()))
                
                discovered[type_id] = EntityTypeInfo(
                    type_id=type_id,
                    label=label,
                    description=description,
                    subclass_of=superclasses,
                    domain_category=self._infer_domain_category(label, description, superclasses)
                )
            
            return discovered
            
        except Exception as e:
            log.error(f"Entity type discovery failed for {type_ids}: {e}")
            # Return basic fallback information
            return {
                tid: EntityTypeInfo(
                    type_id=tid,
                    label=tid,
                    description="Discovery failed",
                    subclass_of=[],
                    domain_category="general"
                ) for tid in type_ids
            }
    
    def _discover_sparql_entity_types(self, type_ids: List[str], endpoint: str) -> Dict[str, EntityTypeInfo]:
        """Discover entity types from general SPARQL endpoints."""
        discovered = {}
        
        for type_id in type_ids:
            # Try RDFS/OWL discovery patterns
            sparql_query = f"""
            SELECT ?label ?comment ?superclass WHERE {{
                <{type_id}> rdfs:label ?label .
                OPTIONAL {{ <{type_id}> rdfs:comment ?comment }}
                OPTIONAL {{ <{type_id}> rdfs:subClassOf ?superclass }}
                FILTER(LANG(?label) = "en" || LANG(?label) = "")
            }} LIMIT 10
            """
            
            try:
                result = discovery_engine.query_endpoint(endpoint, sparql_query)
                
                superclasses = []
                label = type_id
                description = ""
                
                if result.get("success") and result.get("results"):
                    for binding in result["results"]:
                        if "label" in binding:
                            label = binding["label"]["value"]
                        if "comment" in binding:
                            description = binding["comment"]["value"]
                        if "superclass" in binding:
                            superclass = binding["superclass"]["value"]
                            if superclass not in superclasses:
                                superclasses.append(superclass)
                
                discovered[type_id] = EntityTypeInfo(
                    type_id=type_id,
                    label=label,
                    description=description,
                    subclass_of=superclasses,
                    domain_category=self._infer_domain_category(label, description, superclasses)
                )
                
            except Exception as e:
                log.debug(f"Failed to discover entity type {type_id} on {endpoint}: {e}")
                discovered[type_id] = EntityTypeInfo(
                    type_id=type_id,
                    label=type_id,
                    description="Discovery failed",
                    subclass_of=[],
                    domain_category="general"
                )
        
        return discovered
    
    def _infer_domain_category(self, label: str, description: str, superclasses: List[str]) -> str:
        """Infer domain category by discovering from knowledge base (Software 2.0 approach)."""
        # TODO: Use discovery infrastructure to determine domain from superclass hierarchy
        # This should query the knowledge base to understand domain relationships
        # For now, return general to avoid hard-coded assumptions
        return "general"


class EndpointVerification:
    """Verify that suggested databases and endpoints are actually accessible."""
    
    def __init__(self):
        self.cache_prefix = "endpoint_verification"
        
    def verify_database_accessible(self, database: str) -> bool:
        """Check if a database/endpoint is accessible."""
        # Check cache first
        cache_key = f"{self.cache_prefix}:{database}"
        cached = cache_manager.get(cache_key)
        if cached is not None:
            return cached
        
        accessible = False
        
        try:
            # Try to discover the database to see if it's accessible
            discovery_result = discovery_engine.discover(database)
            accessible = discovery_result is not None and hasattr(discovery_result, 'url')
            
        except Exception as e:
            log.debug(f"Database verification failed for {database}: {e}")
            accessible = False
        
        # Cache result (shorter TTL for accessibility checks)
        cache_manager.set(cache_key, accessible, ttl=3600)  # 1 hour
        
        return accessible
    
    def get_accessible_databases(self, suggested_databases: List[str]) -> List[str]:
        """Filter list of databases to only include accessible ones."""
        accessible = []
        
        for db in suggested_databases:
            if self.verify_database_accessible(db):
                accessible.append(db)
        
        return accessible


# Global instances for use across tools
property_discovery = PropertyDiscovery()
entity_type_discovery = EntityTypeDiscovery()
endpoint_verification = EndpointVerification()


def discover_metadata_meanings(
    entity_types: List[str],
    properties: List[str], 
    endpoint: str = "wikidata"
) -> Dict[str, Any]:
    """
    Comprehensive metadata discovery for entity types and properties.
    
    This replaces hard-coded assumptions with dynamic discovery.
    """
    result = {
        "entity_types": {},
        "properties": {},
        "endpoint": endpoint
    }
    
    if entity_types:
        result["entity_types"] = entity_type_discovery.discover_entity_types(entity_types, endpoint)
    
    if properties:
        result["properties"] = property_discovery.discover_properties(properties, endpoint)
    
    return result