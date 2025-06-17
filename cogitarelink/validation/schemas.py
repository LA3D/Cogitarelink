"""Pydantic schemas for RDF tool input validation.

Following Claude Code's Zod schema patterns for comprehensive input validation
with clear error messages optimized for LLM consumption.
"""

from typing import Optional, List, Literal, Union
from pydantic import BaseModel, Field, validator, AnyUrl
import re


class RdfGetInput(BaseModel):
    """Input schema for rdf_get tool."""
    
    url: AnyUrl = Field(
        description="URL to fetch RDF content from (must be valid URL)"
    )
    format_pref: Optional[Literal['json-ld', 'turtle', 'rdf-xml', 'n3', 'n-triples']] = Field(
        None,
        description="Preferred RDF format for content negotiation"
    )
    cache_as: Optional[str] = Field(
        None,
        description="Cache name for reuse (alphanumeric and underscores only)"
    )
    discover: bool = Field(
        False,
        description="Show available formats when content negotiation fails"
    )
    
    @validator('cache_as')
    def validate_cache_name(cls, v):
        if v is not None:
            if not re.match(r'^[a-zA-Z0-9_]+$', v):
                raise ValueError('Cache name must contain only alphanumeric characters and underscores')
            if len(v) > 50:
                raise ValueError('Cache name must be 50 characters or less')
        return v


class RdfCacheInput(BaseModel):
    """Input schema for rdf_cache tool."""
    
    query: str = Field(
        default="",
        description="Search term or cache name to query"
    )
    result_type: Optional[Literal['class', 'property', 'namespace', 'context']] = Field(
        None,
        description="Filter results by semantic type"
    )
    list_cache: bool = Field(
        False,
        description="List all cached vocabularies and service descriptions"
    )
    get_graph: bool = Field(
        False,
        description="Get complete named graph (requires graph name in query)"
    )
    force: bool = Field(
        False,
        description="Force load large graphs (override size warnings)"
    )
    subclasses: Optional[str] = Field(
        None,
        description="Find subclasses of given class URI via rdfs:subClassOf"
    )
    properties: Optional[str] = Field(
        None,
        description="Find properties related to given class URI via rdfs:domain/range"
    )
    related: Optional[str] = Field(
        None,
        description="Find related terms via skos:broader/narrower, owl:sameAs"
    )
    clear_cache: bool = Field(
        False,
        description="Clear all cached RDF data"
    )
    clear_item: Optional[str] = Field(
        None,
        description="Clear specific cached item by name"
    )
    update_metadata: Optional[str] = Field(
        None,
        description="Update semantic metadata for cached item (valid JSON string)"
    )
    
    @validator('update_metadata')
    def validate_metadata_json(cls, v):
        if v is not None:
            try:
                import json
                json.loads(v)
            except json.JSONDecodeError as e:
                raise ValueError(f'Invalid JSON in update_metadata: {e}')
        return v
    
    @validator('query')
    def validate_query_with_graph(cls, v, values):
        if values.get('get_graph') and not v.strip():
            raise ValueError('Graph name required when using --graph option')
        return v


class ClSearchInput(BaseModel):
    """Input schema for cl_search tool."""
    
    query: str = Field(
        min_length=1,
        description="Search query (cannot be empty)"
    )
    limit: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Maximum number of results (1-100)"
    )
    offset: int = Field(
        default=0,
        ge=0,
        description="Starting offset for pagination"
    )
    endpoint: Optional[str] = Field(
        None,
        description="SPARQL endpoint URL or alias (e.g., 'uniprot', 'wikidata')"
    )
    format: Literal['json', 'text', 'csv'] = Field(
        default='json',
        description="Output format"
    )


class ClSelectInput(BaseModel):
    """Input schema for cl_select tool."""
    
    query: str = Field(
        min_length=1,
        description="SPARQL SELECT query"
    )
    limit: int = Field(
        default=10,
        ge=1,
        le=1000,
        description="Maximum number of results (1-1000)"
    )
    offset: int = Field(
        default=0,
        ge=0,
        description="Starting offset for pagination"
    )
    endpoint: Optional[str] = Field(
        None,
        description="SPARQL endpoint URL or alias"
    )
    format: Literal['json', 'text', 'csv'] = Field(
        default='json',
        description="Output format"
    )
    
    @validator('query')
    def validate_sparql_select(cls, v):
        query_upper = v.strip().upper()
        if not query_upper.startswith('SELECT'):
            raise ValueError('Query must be a SPARQL SELECT statement')
        if 'DELETE' in query_upper or 'INSERT' in query_upper or 'DROP' in query_upper:
            raise ValueError('Only SELECT queries are allowed (no modifications)')
        return v


class ClDescribeInput(BaseModel):
    """Input schema for cl_describe tool."""
    
    entity: str = Field(
        min_length=1,
        description="Entity URI or identifier to describe"
    )
    endpoint: Optional[str] = Field(
        None,
        description="SPARQL endpoint URL or alias"
    )
    format: Literal['json', 'text'] = Field(
        default='json',
        description="Output format"
    )


class ClAskInput(BaseModel):
    """Input schema for cl_ask tool."""
    
    query: str = Field(
        min_length=1,
        description="SPARQL ASK query (boolean fact verification)"
    )
    endpoint: Optional[str] = Field(
        None,
        description="SPARQL endpoint URL or alias"
    )
    format: Literal['json', 'text'] = Field(
        default='json',
        description="Output format"
    )
    
    @validator('query')
    def validate_sparql_ask(cls, v):
        query_upper = v.strip().upper()
        if not query_upper.startswith('ASK'):
            raise ValueError('Query must be a SPARQL ASK statement')
        if 'DELETE' in query_upper or 'INSERT' in query_upper or 'DROP' in query_upper:
            raise ValueError('Only ASK queries are allowed (no modifications)')
        return v


# Common validation patterns
class EndpointValidator:
    """Validates endpoint URLs and aliases."""
    
    KNOWN_ALIASES = {
        'wikidata': 'https://query.wikidata.org/sparql',
        'uniprot': 'https://sparql.uniprot.org/sparql',
        'wikipathways': 'https://sparql.wikipathways.org/sparql',
        'qlever-wikidata': 'https://qlever.cs.uni-freiburg.de/api/wikidata',
        'qlever-osm': 'https://qlever.cs.uni-freiburg.de/api/osm-planet'
    }
    
    @classmethod
    def validate_endpoint(cls, endpoint: Optional[str]) -> Optional[str]:
        """Validate and resolve endpoint URL or alias."""
        if endpoint is None:
            return None
            
        # Check if it's a known alias
        if endpoint.lower() in cls.KNOWN_ALIASES:
            return cls.KNOWN_ALIASES[endpoint.lower()]
            
        # Validate as URL
        if not (endpoint.startswith('http://') or endpoint.startswith('https://')):
            raise ValueError(f'Endpoint must be a valid URL or known alias. Known aliases: {list(cls.KNOWN_ALIASES.keys())}')
            
        return endpoint


# Metadata schemas for semantic annotation
class SemanticMetadataInput(BaseModel):
    """Schema for semantic metadata in rdf_cache --update-metadata."""
    
    semantic_type: Literal['vocabulary', 'ontology', 'context', 'service'] = Field(
        description="Type of semantic resource"
    )
    domains: List[str] = Field(
        default_factory=list,
        description="Research domains (e.g., biology, chemistry, social)"
    )
    purpose: str = Field(
        default="unknown",
        description="Purpose or use case of the resource"
    )
    dependencies: List[str] = Field(
        default_factory=list,
        description="Other vocabularies this resource depends on"
    )
    usage_patterns: List[str] = Field(
        default_factory=list,
        description="Common usage patterns discovered"
    )
    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Confidence in the analysis (0.0-1.0)"
    )
    notes: str = Field(
        default="",
        description="Additional analysis notes"
    )