#!/usr/bin/env python3
"""
cl_describe: Entity description tool

Get entity descriptions with cross-references.
Simplified for Claude Code patterns - clean data output only.
"""

from __future__ import annotations

import asyncio
import json
import sys
from typing import Optional, List, Dict, Any

import click

from ..adapters.wikidata_client import WikidataClient
from ..core.debug import get_logger

log = get_logger("cl_describe")


@click.command()
@click.argument('entity_identifier', required=True)
@click.option('--include-cross-refs', is_flag=True, default=True,
              help='Include cross-references to external databases')
def describe(entity_identifier: str, include_cross_refs: bool):
    """
    Get detailed entity description with cross-references.
    
    Examples:
        cl_describe Q7240673
        cl_describe P352 --include-cross-refs
    """
    asyncio.run(_describe_async(entity_identifier, include_cross_refs))


async def _describe_async(entity_identifier: str, include_cross_refs: bool):
    """Async entity description with clean output."""
    
    try:
        # Validate entity ID format
        if not _is_valid_entity_id(entity_identifier):
            error_result = {
                "entity_id": entity_identifier,
                "error": f"Invalid entity ID format: {entity_identifier}. Expected Q123456 or P123456"
            }
            click.echo(json.dumps(error_result, indent=2))
            sys.exit(1)
        
        # Initialize client
        client = WikidataClient(timeout=30)
        
        log.info(f"Describing entity: {entity_identifier}")
        
        # Get entity data
        entity_data = await client.get_entities([entity_identifier])
        
        if entity_identifier not in entity_data.get('entities', {}):
            error_result = {
                "entity_id": entity_identifier,
                "error": f"Entity {entity_identifier} not found in Wikidata"
            }
            click.echo(json.dumps(error_result, indent=2))
            sys.exit(1)
        
        entity_info = entity_data['entities'][entity_identifier]
        
        # Build entity description
        description = _build_entity_description(entity_info, entity_identifier)
        
        # Add cross-references if requested
        if include_cross_refs:
            cross_refs = await _extract_cross_references(entity_info)
            description['cross_references'] = cross_refs
        
        # Clean output - just the data Claude needs
        click.echo(json.dumps(description, indent=2))
        
    except Exception as e:
        log.error(f"Entity description failed: {e}")
        error_result = {
            "entity_id": entity_identifier,
            "error": str(e)
        }
        click.echo(json.dumps(error_result, indent=2))
        sys.exit(1)


def _build_entity_description(entity_info: Dict[str, Any], entity_id: str) -> Dict[str, Any]:
    """Build clean entity description."""
    
    # Extract basic information
    labels = entity_info.get('labels', {})
    descriptions = entity_info.get('descriptions', {})
    aliases = entity_info.get('aliases', {})
    claims = entity_info.get('claims', {})
    
    # Get English label and description
    name = labels.get('en', {}).get('value', '')
    description = descriptions.get('en', {}).get('value', '')
    
    # Extract entity types (P31 - instance of)
    entity_types = []
    if 'P31' in claims:
        for claim in claims['P31'][:3]:  # Limit to first 3
            if 'mainsnak' in claim and 'datavalue' in claim['mainsnak']:
                type_id = claim['mainsnak']['datavalue']['value']['id']
                entity_types.append(type_id)
    
    # Count total claims
    claims_count = sum(len(prop_claims) for prop_claims in claims.values())
    
    return {
        "entity": {
            "identifier": entity_id,
            "name": name,
            "description": description,
            "wikidata_url": f"https://www.wikidata.org/wiki/{entity_id}",
            "entity_types": entity_types,
            "claims_count": claims_count
        }
    }


async def _extract_cross_references(entity_info: Dict[str, Any]) -> Dict[str, Any]:
    """Extract cross-references using dynamic external identifier discovery."""
    
    try:
        # Use dynamic external identifier discovery
        from ..core.external_ids import get_external_ids_for_entity
        
        entity_id = entity_info.get('id', '')
        if not entity_id:
            # Try to extract from the URI
            entity_uri = entity_info.get('uri', '')
            if entity_uri and '/entity/' in entity_uri:
                entity_id = entity_uri.split('/entity/')[-1]
            else:
                return {}
        
        # Get all external identifiers dynamically
        external_ids = await get_external_ids_for_entity(entity_id)
        
        # Convert to the format expected by cl_describe
        cross_refs = {}
        for db_name, db_data in external_ids.items():
            cross_refs[db_name] = db_data['values']
        
        return cross_refs
        
    except Exception as e:
        log.warning(f"Dynamic external ID discovery failed, falling back to hardcoded: {e}")
        
        # Fallback to hardcoded mappings if dynamic discovery fails
        claims = entity_info.get('claims', {})
        cross_refs = {}
        
        # Database property mappings (fallback only)
        database_properties = {
            'P352': 'uniprot',          # UniProt protein ID
            'P683': 'chebi',            # ChEBI ID
            'P231': 'cas',              # CAS Registry Number
            'P592': 'chembl',           # ChEMBL ID
            'P715': 'drugbank',         # DrugBank ID
            'P486': 'mesh',             # MeSH descriptor ID
            'P685': 'ncbi_gene',        # NCBI Gene ID
            'P594': 'ensembl_gene',     # Ensembl gene ID
            'P637': 'refseq',           # RefSeq protein ID
            'P699': 'disease_ontology', # Disease Ontology ID
            'P665': 'kegg',             # KEGG ID
            'P232': 'ec_number',        # EC number
            'P662': 'pubchem_cid',      # PubChem CID
            'P2017': 'isomeric_smiles', # isomeric SMILES
            'P1579': 'pubchem_sid',     # PubChem SID
            'P638': 'pdb',              # Protein Data Bank ID
            'P2892': 'umls',            # UMLS CUI
            'P233': 'smiles',           # SMILES string
            'P274': 'molecular_formula', # molecular formula
            'P2798': 'hgnc',            # HGNC gene symbol
            'P351': 'entrez_gene',      # Entrez Gene ID
            'P2410': 'wikipathways',    # WikiPathways ID
        }
        
        # Extract clean cross-references
        for prop_id, db_name in database_properties.items():
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
                    cross_refs[db_name] = values
    
    # Special handling for coordinates (P625) - useful for geographic entities
    if 'P625' in claims:
        coord_claims = claims['P625']
        if coord_claims and 'mainsnak' in coord_claims[0] and 'datavalue' in coord_claims[0]['mainsnak']:
            coord_value = coord_claims[0]['mainsnak']['datavalue']['value']
            cross_refs['coordinates'] = {
                "latitude": coord_value.get('latitude'),
                "longitude": coord_value.get('longitude'),
                "precision": coord_value.get('precision')
            }
    
    return cross_refs




def _is_valid_entity_id(entity_id: str) -> bool:
    """Check if entity ID is valid format."""
    return ((entity_id.startswith('Q') or entity_id.startswith('P')) and 
            entity_id[1:].isdigit())


if __name__ == "__main__":
    describe()