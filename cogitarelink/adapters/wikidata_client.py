"""
Wikidata API Client - Foundation Layer for CogitareLink

Provides the basic Wikidata API client that integrates with CogitareLink's
entity system and semantic memory architecture.
"""

from __future__ import annotations

import asyncio
import httpx
from typing import Dict, List, Optional, Any, Union

from ..core.debug import get_logger
from ..core.entity import Entity

log = get_logger("wikidata_client")


class WikidataClient:
    """
    Wikidata API client integrated with CogitareLink architecture.
    
    Provides basic Wikidata operations with Entity integration and
    semantic memory compatibility.
    """
    
    def __init__(self, timeout: int = 30):
        self.base_url = "https://www.wikidata.org/w/api.php"
        self.sparql_url = "https://query.wikidata.org/sparql"
        self.timeout = timeout
        
    async def search_entities(
        self, 
        query: str, 
        language: str = "en", 
        limit: int = 10,
        entity_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Search for Wikidata entities.
        
        Returns raw Wikidata API response for processing into Entities.
        """
        params = {
            'action': 'wbsearchentities',
            'search': query,
            'language': language,
            'limit': limit,
            'format': 'json'
        }
        
        if entity_type:
            params['type'] = entity_type
            
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(self.base_url, params=params)
                response.raise_for_status()
                result = response.json()
                log.debug(f"Search for '{query}' returned {len(result.get('search', []))} results")
                return result
        except Exception as e:
            log.error(f"Wikidata search failed for '{query}': {e}")
            raise
    
    async def get_entities(
        self,
        entity_ids: Union[str, List[str]],
        language: str = "en",
        props: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get entity data by IDs.
        
        Returns raw Wikidata API response for Entity processing.
        """
        # Convert single ID to list for consistent interface
        if isinstance(entity_ids, str):
            entity_ids = [entity_ids]
            
        params = {
            'action': 'wbgetentities',
            'ids': '|'.join(entity_ids),
            'languages': language,
            'format': 'json'
        }
        
        if props:
            params['props'] = '|'.join(props)
        else:
            params['props'] = 'labels|descriptions|claims|sitelinks'
            
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(self.base_url, params=params)
                response.raise_for_status()
                result = response.json()
                log.debug(f"Retrieved {len(result.get('entities', {}))} entities")
                return result
        except Exception as e:
            log.error(f"Wikidata entity retrieval failed for {entity_ids}: {e}")
            raise
    
    async def sparql_query(self, query: str) -> Dict[str, Any]:
        """
        Execute SPARQL query against Wikidata.
        
        Automatically adds common prefixes if not present.
        """
        # Add common prefixes if not present
        prefixes = """
        PREFIX wd: <http://www.wikidata.org/entity/>
        PREFIX wdt: <http://www.wikidata.org/prop/direct/>
        PREFIX wikibase: <http://wikiba.se/ontology#>
        PREFIX bd: <http://www.bigdata.com/rdf#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX schema: <https://schema.org/>
        """
        
        # Check if prefixes are needed
        if not any(prefix.split(':')[1].strip() in query for prefix in prefixes.strip().split('\n')):
            query = prefixes + "\n" + query
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                headers = {
                    'Accept': 'application/sparql-results+json',
                    'User-Agent': 'CogitareLink/1.0'
                }
                
                response = await client.post(
                    self.sparql_url,
                    data={'query': query},
                    headers=headers
                )
                response.raise_for_status()
                result = response.json()
                
                bindings_count = len(result.get('results', {}).get('bindings', []))
                log.debug(f"SPARQL query returned {bindings_count} results")
                return result
                
        except Exception as e:
            log.error(f"Wikidata SPARQL query failed: {e}")
            raise
    
    async def convert_search_to_entities(
        self, 
        search_results: Dict[str, Any], 
        vocab: List[str] = None
    ) -> List[Entity]:
        """
        Convert Wikidata search results to CogitareLink Entities.
        """
        if vocab is None:
            vocab = ["wikidata", "schema.org"]
            
        entities = []
        
        for item in search_results.get('search', []):
            content = {
                "@type": "WikidataEntity",
                "@id": item.get('concepturi', f"http://www.wikidata.org/entity/{item.get('id')}"),
                "identifier": item.get('id'),
                "name": item.get('label', 'No label'),
                "description": item.get('description', 'No description'),
                "wikidataUrl": item.get('url', ''),
                "matchScore": item.get('match', {}).get('text', '')
            }
            
            try:
                entity = Entity(vocab=vocab, content=content)
                entities.append(entity)
                log.debug(f"Created entity for {item.get('id')}: {item.get('label')}")
            except Exception as e:
                log.warning(f"Failed to create entity for {item.get('id')}: {e}")
                
        return entities
    
    async def convert_entity_data_to_entity(
        self, 
        entity_data: Dict[str, Any], 
        entity_id: str,
        vocab: List[str] = None
    ) -> Optional[Entity]:
        """
        Convert Wikidata entity data to CogitareLink Entity.
        """
        if vocab is None:
            vocab = ["wikidata", "schema.org"]
            
        try:
            content = {
                "@type": "WikidataEntity",
                "@id": f"http://www.wikidata.org/entity/{entity_id}",
                "identifier": entity_id,
                "name": entity_data.get('labels', {}).get('en', {}).get('value', 'No label'),
                "description": entity_data.get('descriptions', {}).get('en', {}).get('value', 'No description')
            }
            
            # Add Wikipedia link if available
            sitelinks = entity_data.get('sitelinks', {})
            if 'enwiki' in sitelinks:
                wiki_data = sitelinks['enwiki']
                if 'url' in wiki_data:
                    content['wikipediaUrl'] = wiki_data['url']
                elif 'title' in wiki_data:
                    title = wiki_data['title'].replace(' ', '_')
                    content['wikipediaUrl'] = f"https://en.wikipedia.org/wiki/{title}"
            
            # Process claims into structured properties
            if 'claims' in entity_data:
                content['claims'] = {}
                for prop_id, claim_list in entity_data['claims'].items():
                    values = []
                    for claim in claim_list:
                        value = self._extract_claim_value(claim)
                        if value:
                            values.append({
                                'value': value,
                                'rank': claim.get('rank', 'normal')
                            })
                    if values:
                        content['claims'][prop_id] = values
            
            entity = Entity(vocab=vocab, content=content)
            log.debug(f"Created entity for {entity_id}: {content['name']}")
            return entity
            
        except Exception as e:
            log.error(f"Failed to create entity for {entity_id}: {e}")
            return None
    
    def _extract_claim_value(self, claim: Dict[str, Any]) -> Optional[str]:
        """Extract human-readable value from a Wikidata claim."""
        if 'mainsnak' not in claim or 'datavalue' not in claim['mainsnak']:
            return None
        
        value = claim['mainsnak']['datavalue']['value']
        datatype = claim['mainsnak'].get('datatype', '')
        
        if datatype == 'wikibase-entityid':
            return value.get('id')  # Return Q-number for now
        elif datatype == 'time':
            return value.get('time', '').replace('+', '')  # Clean up time format
        elif datatype == 'string':
            return str(value)
        else:
            return str(value)


# Quick test function
async def test_wikidata_client():
    """Test the Wikidata client with CogitareLink integration."""
    client = WikidataClient()
    
    print("🔍 Testing Wikidata client...")
    
    # Test search
    search_result = await client.search_entities("Douglas Adams", limit=3)
    print(f"Search found {len(search_result.get('search', []))} results")
    
    # Convert to entities
    entities = await client.convert_search_to_entities(search_result)
    print(f"Created {len(entities)} CogitareLink entities")
    
    if entities:
        entity = entities[0]
        print(f"First entity: {entity.content.get('name')} ({entity.content.get('identifier')})")
        print(f"Entity SHA-256: {entity.sha256[:12]}...")
    
    # Test entity retrieval
    if search_result.get('search'):
        entity_id = search_result['search'][0]['id']
        entity_data = await client.get_entities([entity_id])
        
        if entity_id in entity_data.get('entities', {}):
            entity = await client.convert_entity_data_to_entity(
                entity_data['entities'][entity_id], 
                entity_id
            )
            if entity:
                print(f"Retrieved detailed entity: {entity.content.get('name')}")
                print(f"Claims count: {len(entity.content.get('claims', {}))}")
    
    print("✅ Wikidata client test completed!")


if __name__ == "__main__":
    asyncio.run(test_wikidata_client())