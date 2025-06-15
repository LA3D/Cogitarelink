"""
Schema Discovery Engine for SPARQL Endpoints

Provides comprehensive schema discovery and analysis for biological databases
with agent-friendly guidance generation.
"""

from __future__ import annotations

import asyncio
import httpx
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass

from ..core.debug import get_logger
from ..adapters.multi_sparql_client import MultiSparqlClient

log = get_logger("schema_discovery")


@dataclass
class SchemaInfo:
    """Schema information for a SPARQL endpoint."""
    endpoint: str
    classes: List[Dict[str, Any]]
    properties: List[Dict[str, Any]]
    prefixes: Dict[str, str]
    examples: List[str]
    statistics: Dict[str, Any]
    discovery_method: str
    confidence_score: float


class SchemaDiscoveryEngine:
    """
    Comprehensive schema discovery for biological SPARQL endpoints.
    
    Uses multiple discovery methods with biological domain expertise
    to generate agent-friendly guidance.
    """
    
    def __init__(self, timeout: int = 60):
        self.timeout = timeout
        self.sparql_client = MultiSparqlClient(timeout=timeout)
        
        # Discovery queries for different endpoint types
        self.discovery_queries = {
            "classes": """
            SELECT DISTINCT ?class ?classLabel (COUNT(?instance) as ?instanceCount) WHERE {
                ?instance a ?class .
                OPTIONAL { ?class rdfs:label ?classLabel . FILTER(LANG(?classLabel) = "en") }
            }
            GROUP BY ?class ?classLabel
            ORDER BY DESC(?instanceCount)
            LIMIT 20
            """,
            
            "properties": """
            SELECT DISTINCT ?property ?propertyLabel (COUNT(?usage) as ?usageCount) WHERE {
                ?subject ?property ?object .
                OPTIONAL { ?property rdfs:label ?propertyLabel . FILTER(LANG(?propertyLabel) = "en") }
            }
            GROUP BY ?property ?propertyLabel
            ORDER BY DESC(?usageCount)
            LIMIT 50
            """,
            
            "void_statistics": """
            SELECT ?stat ?value WHERE {
                ?dataset a void:Dataset .
                ?dataset ?stat ?value .
                FILTER(?stat IN (void:triples, void:entities, void:classes, void:properties))
            }
            """,
            
            "prefixes": """
            SELECT DISTINCT ?prefix WHERE {
                {
                    SELECT (SUBSTR(STR(?p), 1, STRDT(STR(?idx), xsd:integer)) as ?prefix) WHERE {
                        ?s ?p ?o .
                        BIND(STRLEN(STR(?p)) - STRLEN(STRAFTER(STR(?p), "#")) - 1 as ?idx)
                        FILTER(?idx > 10)
                    }
                }
                UNION
                {
                    SELECT (SUBSTR(STR(?p), 1, STRDT(STR(?lastSlash), xsd:integer)) as ?prefix) WHERE {
                        ?s ?p ?o .
                        BIND(STRLEN(STR(?p)) - STRLEN(STRAFTER(REVERSE(STR(?p)), "/")) as ?lastSlash)
                        FILTER(?lastSlash > 10)
                    }
                }
            }
            LIMIT 20
            """
        }
        
        # Biological domain-specific discovery queries
        self.biological_queries = {
            "proteins": """
            SELECT ?protein ?name WHERE {
                ?protein a ?proteinClass .
                OPTIONAL { ?protein rdfs:label ?name }
                VALUES ?proteinClass { up:Protein wp:Protein }
            }
            LIMIT 10
            """,
            
            "pathways": """
            SELECT ?pathway ?title WHERE {
                ?pathway a wp:Pathway .
                OPTIONAL { ?pathway dc:title ?title }
            }
            LIMIT 10
            """,
            
            "compounds": """
            SELECT ?compound ?name WHERE {
                ?compound rdfs:label ?name .
                FILTER(CONTAINS(LCASE(?name), "insulin") || CONTAINS(LCASE(?name), "glucose"))
            }
            LIMIT 10
            """
        }
    
    async def discover_schema(
        self, 
        endpoint: str, 
        method: str = "auto",
        include_examples: bool = True
    ) -> SchemaInfo:
        """
        Discover schema for a SPARQL endpoint.
        
        Args:
            endpoint: Endpoint name or URL
            method: Discovery method (auto, introspection, void, documentation)
            include_examples: Whether to generate example queries
            
        Returns:
            Comprehensive schema information
        """
        
        log.info(f"Discovering schema for endpoint: {endpoint} using method: {method}")
        
        if method == "auto":
            # Try multiple discovery methods
            schema = await self._auto_discover_schema(endpoint, include_examples)
        elif method == "introspection":
            schema = await self._introspection_discovery(endpoint, include_examples)
        elif method == "void":
            schema = await self._void_discovery(endpoint, include_examples)
        elif method == "documentation":
            schema = await self._documentation_discovery(endpoint, include_examples)
        else:
            raise ValueError(f"Unknown discovery method: {method}")
        
        log.info(f"Schema discovery completed for {endpoint} with confidence {schema.confidence_score:.2f}")
        return schema
    
    async def _auto_discover_schema(self, endpoint: str, include_examples: bool) -> SchemaInfo:
        """Automatic schema discovery using multiple methods."""
        
        # Try introspection first (most reliable)
        try:
            return await self._introspection_discovery(endpoint, include_examples)
        except Exception as e:
            log.warning(f"Introspection discovery failed for {endpoint}: {e}")
        
        # Fall back to VoID discovery
        try:
            return await self._void_discovery(endpoint, include_examples)
        except Exception as e:
            log.warning(f"VoID discovery failed for {endpoint}: {e}")
        
        # Fall back to documentation discovery
        try:
            return await self._documentation_discovery(endpoint, include_examples)
        except Exception as e:
            log.warning(f"Documentation discovery failed for {endpoint}: {e}")
        
        # Return minimal schema if all methods fail
        return await self._minimal_schema(endpoint, include_examples)
    
    async def _introspection_discovery(self, endpoint: str, include_examples: bool) -> SchemaInfo:
        """Schema discovery via SPARQL introspection queries."""
        
        classes = []
        properties = []
        statistics = {}
        prefixes = {}
        examples = []
        
        try:
            # Discover classes
            log.debug(f"Discovering classes for {endpoint}")
            classes_result = await self.sparql_client.sparql_query(
                self.discovery_queries["classes"], 
                endpoint=endpoint,
                add_prefixes=True
            )
            
            classes = self._process_classes_result(classes_result)
            
        except Exception as e:
            log.warning(f"Class discovery failed for {endpoint}: {e}")
        
        try:
            # Discover properties
            log.debug(f"Discovering properties for {endpoint}")
            properties_result = await self.sparql_client.sparql_query(
                self.discovery_queries["properties"],
                endpoint=endpoint,
                add_prefixes=True
            )
            
            properties = self._process_properties_result(properties_result)
            
        except Exception as e:
            log.warning(f"Property discovery failed for {endpoint}: {e}")
        
        # Try biological domain-specific discovery
        try:
            biological_data = await self._discover_biological_patterns(endpoint)
            statistics.update(biological_data)
        except Exception as e:
            log.debug(f"Biological pattern discovery failed for {endpoint}: {e}")
        
        # Generate examples
        if include_examples:
            examples = self._generate_examples(endpoint, classes, properties)
        
        # Get endpoint configuration if available
        endpoint_config = self.sparql_client.get_endpoint_info(endpoint)
        if endpoint_config:
            prefixes = self._parse_prefixes(endpoint_config.default_prefixes)
            examples.extend(endpoint_config.examples or [])
        
        return SchemaInfo(
            endpoint=endpoint,
            classes=classes,
            properties=properties,
            prefixes=prefixes,
            examples=examples,
            statistics=statistics,
            discovery_method="introspection",
            confidence_score=0.8 if classes or properties else 0.3
        )
    
    async def _void_discovery(self, endpoint: str, include_examples: bool) -> SchemaInfo:
        """Schema discovery via VoID (Vocabulary of Interlinked Datasets) metadata."""
        
        statistics = {}
        
        try:
            void_result = await self.sparql_client.sparql_query(
                self.discovery_queries["void_statistics"],
                endpoint=endpoint,
                add_prefixes=True
            )
            
            for binding in void_result.get('results', {}).get('bindings', []):
                stat = binding.get('stat', {}).get('value', '')
                value = binding.get('value', {}).get('value', '')
                if stat and value:
                    statistics[stat.split('/')[-1]] = value
        
        except Exception as e:
            log.warning(f"VoID discovery failed for {endpoint}: {e}")
        
        return SchemaInfo(
            endpoint=endpoint,
            classes=[],
            properties=[],
            prefixes={},
            examples=[],
            statistics=statistics,
            discovery_method="void",
            confidence_score=0.5 if statistics else 0.2
        )
    
    async def _documentation_discovery(self, endpoint: str, include_examples: bool) -> SchemaInfo:
        """Schema discovery via endpoint documentation."""
        
        # Get endpoint configuration
        endpoint_config = self.sparql_client.get_endpoint_info(endpoint)
        
        if endpoint_config:
            prefixes = self._parse_prefixes(endpoint_config.default_prefixes)
            examples = endpoint_config.examples or []
            
            return SchemaInfo(
                endpoint=endpoint,
                classes=[],
                properties=[],
                prefixes=prefixes,
                examples=examples,
                statistics={"description": endpoint_config.description},
                discovery_method="documentation",
                confidence_score=0.6
            )
        
        return await self._minimal_schema(endpoint, include_examples)
    
    async def _minimal_schema(self, endpoint: str, include_examples: bool) -> SchemaInfo:
        """Create minimal schema when discovery fails."""
        
        return SchemaInfo(
            endpoint=endpoint,
            classes=[],
            properties=[],
            prefixes={},
            examples=[],
            statistics={},
            discovery_method="minimal",
            confidence_score=0.1
        )
    
    async def _discover_biological_patterns(self, endpoint: str) -> Dict[str, Any]:
        """Discover biological patterns specific to the endpoint."""
        
        biological_data = {}
        
        # Try biological queries based on endpoint type
        if "uniprot" in endpoint.lower():
            try:
                result = await self.sparql_client.sparql_query(
                    self.biological_queries["proteins"],
                    endpoint=endpoint
                )
                protein_count = len(result.get('results', {}).get('bindings', []))
                biological_data["proteins_sampled"] = protein_count
            except:
                pass
        
        elif "wikipathways" in endpoint.lower():
            try:
                result = await self.sparql_client.sparql_query(
                    self.biological_queries["pathways"],
                    endpoint=endpoint
                )
                pathway_count = len(result.get('results', {}).get('bindings', []))
                biological_data["pathways_sampled"] = pathway_count
            except:
                pass
        
        elif "idsm" in endpoint.lower():
            try:
                result = await self.sparql_client.sparql_query(
                    self.biological_queries["compounds"],
                    endpoint=endpoint
                )
                compound_count = len(result.get('results', {}).get('bindings', []))
                biological_data["compounds_sampled"] = compound_count
            except:
                pass
        
        return biological_data
    
    def _process_classes_result(self, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process SPARQL result for classes."""
        
        classes = []
        bindings = result.get('results', {}).get('bindings', [])
        
        for binding in bindings:
            class_uri = binding.get('class', {}).get('value', '')
            class_label = binding.get('classLabel', {}).get('value', class_uri.split('/')[-1])
            instance_count = binding.get('instanceCount', {}).get('value', '0')
            
            if class_uri:
                classes.append({
                    "uri": class_uri,
                    "label": class_label,
                    "instance_count": int(instance_count) if instance_count.isdigit() else 0,
                    "prefix": self._extract_prefix(class_uri)
                })
        
        return classes
    
    def _process_properties_result(self, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process SPARQL result for properties."""
        
        properties = []
        bindings = result.get('results', {}).get('bindings', [])
        
        for binding in bindings:
            prop_uri = binding.get('property', {}).get('value', '')
            prop_label = binding.get('propertyLabel', {}).get('value', prop_uri.split('/')[-1])
            usage_count = binding.get('usageCount', {}).get('value', '0')
            
            if prop_uri:
                properties.append({
                    "uri": prop_uri,
                    "label": prop_label,
                    "usage_count": int(usage_count) if usage_count.isdigit() else 0,
                    "prefix": self._extract_prefix(prop_uri)
                })
        
        return properties
    
    def _extract_prefix(self, uri: str) -> str:
        """Extract namespace prefix from URI."""
        
        if '#' in uri:
            return uri.split('#')[0] + '#'
        elif '/' in uri:
            parts = uri.split('/')
            return '/'.join(parts[:-1]) + '/'
        return uri
    
    def _parse_prefixes(self, prefix_string: str) -> Dict[str, str]:
        """Parse PREFIX declarations into dictionary."""
        
        prefixes = {}
        
        for line in prefix_string.strip().split('\n'):
            line = line.strip()
            if line.startswith('PREFIX'):
                parts = line.split()
                if len(parts) >= 3:
                    prefix_name = parts[1].rstrip(':')
                    prefix_uri = parts[2].strip('<>')
                    prefixes[prefix_name] = prefix_uri
        
        return prefixes
    
    def _generate_examples(
        self, 
        endpoint: str, 
        classes: List[Dict[str, Any]], 
        properties: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate example queries based on discovered schema."""
        
        examples = []
        
        # Generate class-based examples
        if classes:
            top_class = classes[0]
            class_uri = top_class['uri']
            class_prefix = self._get_prefix_name(class_uri, endpoint)
            
            if class_prefix:
                examples.append(f"SELECT ?item WHERE {{ ?item a {class_prefix} }} LIMIT 10")
        
        # Generate property-based examples  
        if properties:
            top_prop = properties[0]
            prop_uri = top_prop['uri']
            prop_prefix = self._get_prefix_name(prop_uri, endpoint)
            
            if prop_prefix:
                examples.append(f"SELECT ?subject ?object WHERE {{ ?subject {prop_prefix} ?object }} LIMIT 10")
        
        return examples
    
    def _get_prefix_name(self, uri: str, endpoint: str) -> Optional[str]:
        """Get prefix name for URI based on endpoint configuration."""
        
        endpoint_config = self.sparql_client.get_endpoint_info(endpoint)
        if not endpoint_config:
            return None
        
        prefixes = self._parse_prefixes(endpoint_config.default_prefixes)
        
        for prefix_name, prefix_uri in prefixes.items():
            if uri.startswith(prefix_uri):
                local_part = uri[len(prefix_uri):]
                return f"{prefix_name}:{local_part}"
        
        return None
    
    def generate_agent_guidance(self, schema: SchemaInfo) -> Dict[str, Any]:
        """Generate agent-friendly guidance from schema information."""
        
        guidance = {
            "schema_summary": {
                "endpoint": schema.endpoint,
                "discovery_method": schema.discovery_method,
                "confidence": schema.confidence_score,
                "classes_discovered": len(schema.classes),
                "properties_discovered": len(schema.properties),
                "prefixes_available": len(schema.prefixes)
            },
            "query_patterns": [],
            "biological_intelligence": [],
            "next_steps": []
        }
        
        # Add class-based patterns
        if schema.classes:
            guidance["query_patterns"].append({
                "pattern": "Class-based entity discovery",
                "template": "SELECT ?entity WHERE { ?entity a <CLASS> } LIMIT N",
                "top_classes": [c["label"] for c in schema.classes[:5]]
            })
        
        # Add property-based patterns
        if schema.properties:
            guidance["query_patterns"].append({
                "pattern": "Property-based relationship exploration", 
                "template": "SELECT ?subject ?object WHERE { ?subject <PROPERTY> ?object } LIMIT N",
                "top_properties": [p["label"] for p in schema.properties[:5]]
            })
        
        # Add biological intelligence based on endpoint
        if "uniprot" in schema.endpoint.lower():
            guidance["biological_intelligence"] = [
                "UniProt specializes in protein sequence and function data",
                "Use up:Protein class for protein entities",
                "Key properties: up:mnemonic (protein name), up:organism, up:sequence",
                "Cross-reference with Wikidata via P352 (UniProt ID)"
            ]
        elif "wikipathways" in schema.endpoint.lower():
            guidance["biological_intelligence"] = [
                "WikiPathways contains biological pathway data",
                "Use wp:Pathway class for pathway entities",
                "Key properties: dc:title, dcterms:description, wp:organism",
                "Connect gene products with dcterms:isPartOf relationships"
            ]
        elif "wikidata" in schema.endpoint.lower():
            guidance["biological_intelligence"] = [
                "Wikidata is a general knowledge graph with biological entities",
                "Use wdt:P31 (instance of) to find entity types",
                "Key biological classes: Q8054 (protein), Q7187 (gene)",
                "Rich cross-references to specialized databases via P352, P683, etc."
            ]
        
        # Add next steps
        guidance["next_steps"] = [
            f"Try example queries to explore {schema.endpoint} data",
            "Use discovered classes and properties in custom queries",
            "Cross-reference with other biological databases",
            "Materialize interesting results for semantic analysis"
        ]
        
        if schema.examples:
            guidance["example_queries"] = schema.examples
        
        return guidance


# Global schema discovery engine instance
schema_discovery_engine = SchemaDiscoveryEngine()


# Test function
async def test_schema_discovery():
    """Test schema discovery functionality."""
    
    print("🔍 Testing Schema Discovery Engine...")
    
    # Test Wikidata schema discovery
    try:
        print("\n📊 Discovering Wikidata schema...")
        schema = await schema_discovery_engine.discover_schema("wikidata", method="documentation")
        print(f"Wikidata schema confidence: {schema.confidence_score:.2f}")
        print(f"Prefixes found: {len(schema.prefixes)}")
        print(f"Examples: {len(schema.examples)}")
        
        # Generate guidance
        guidance = schema_discovery_engine.generate_agent_guidance(schema)
        print(f"Query patterns: {len(guidance['query_patterns'])}")
        print(f"Biological intelligence items: {len(guidance['biological_intelligence'])}")
        
    except Exception as e:
        print(f"Wikidata schema discovery failed: {e}")
    
    print("✅ Schema discovery test completed!")


if __name__ == "__main__":
    asyncio.run(test_schema_discovery())