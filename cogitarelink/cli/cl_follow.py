#!/usr/bin/env python3
"""
cl_follow: Simple cross-reference following tool

Follow cross-references from Wikidata entities to external databases.
Simplified version without complex response management.
"""

from __future__ import annotations

import asyncio
import json
import sys
import time
from typing import Optional, List, Dict, Any

import click

from ..adapters.wikidata_client import WikidataClient
from ..core.debug import get_logger

log = get_logger("cl_follow")


@click.command()
@click.argument('entity_id', required=True)
@click.option('--databases', multiple=True, 
              help='Target databases: uniprot, chebi, pubchem, ensembl, mesh')
@click.option('--resolve-urls', is_flag=True, default=False,
              help='Include URLs for cross-references')
@click.option('--format', 'output_format', type=click.Choice(['json', 'human']), 
              default='json', help='Output format')
def follow(entity_id: str, databases: List[str], resolve_urls: bool, output_format: str):
    """
    Follow cross-references from a Wikidata entity to external databases.
    
    Examples:
        cl_follow Q7240673 --databases uniprot
        cl_follow Q7240673 --resolve-urls
        cl_follow P01308 --format human
    """
    asyncio.run(_follow_async(entity_id, list(databases), resolve_urls, output_format))


async def _follow_async(entity_id: str, databases: List[str], resolve_urls: bool, output_format: str):
    """Async cross-reference following."""
    
    start_time = time.time()
    
    try:
        # Validate entity ID format
        if not ((entity_id.startswith('Q') or entity_id.startswith('P')) and entity_id[1:].isdigit()):
            _output_error(f"Entity ID must be in format Q123456 or P123456, got: {entity_id}", output_format)
            return
        
        # Initialize client
        wikidata_client = WikidataClient(timeout=30)
        
        # Get entity data
        log.info(f"Retrieving entity data for {entity_id}")
        entity_data = await wikidata_client.get_entities([entity_id])
        
        if entity_id not in entity_data.get('entities', {}):
            _output_error(f"Entity {entity_id} not found in Wikidata", output_format)
            return
        
        entity_info = entity_data['entities'][entity_id]
        
        # Extract cross-references
        cross_references, metadata = _extract_cross_references(entity_info, databases)
        
        # Add URLs if requested
        if resolve_urls:
            _add_urls_to_cross_references(cross_references)
        
        # Build response
        execution_time = int((time.time() - start_time) * 1000)
        
        entity_name = entity_info.get('labels', {}).get('en', {}).get('value', 'Unknown')
        entity_description = entity_info.get('descriptions', {}).get('en', {}).get('value', '')
        
        response = {
            'success': True,
            'data': {
                'entity': {
                    'id': entity_id,
                    'name': entity_name,
                    'description': entity_description,
                    'wikidata_url': f"https://www.wikidata.org/wiki/{entity_id}"
                },
                'cross_references': cross_references,
                'metadata': metadata,
                'statistics': {
                    'databases_found': len(cross_references),
                    'total_identifiers': sum(len(ids) for ids in cross_references.values())
                }
            },
            'suggestions': _generate_suggestions(cross_references, entity_name),
            'execution_time_ms': execution_time
        }
        
        # Output response
        if output_format == 'human':
            _print_human_readable(response)
        else:
            click.echo(json.dumps(response, indent=2))
            
    except Exception as e:
        log.error(f"Cross-reference following failed: {e}")
        _output_error(f"Cross-reference following failed: {str(e)}", output_format)
        sys.exit(1)


def _extract_cross_references(entity_info: Dict[str, Any], target_databases: List[str]) -> tuple[Dict[str, List[str]], Dict[str, Dict[str, Any]]]:
    """Extract cross-references from Wikidata entity."""
    
    # Database property mappings (Wikidata property ID -> database name)
    database_properties = {
        'P352': 'uniprot',      # UniProt protein ID
        'P683': 'chebi',        # ChEBI ID
        'P231': 'cas',          # CAS Registry Number
        'P592': 'chembl',       # ChEMBL ID
        'P715': 'drugbank',     # DrugBank ID
        'P486': 'mesh',         # MeSH descriptor ID
        'P685': 'ncbi_gene',    # NCBI Gene ID
        'P594': 'ensembl_gene', # Ensembl gene ID
        'P637': 'refseq',       # RefSeq protein ID
        'P699': 'disease_ontology', # Disease Ontology ID
        'P665': 'kegg',         # KEGG ID
        'P232': 'ec_number',    # EC number
        'P662': 'pubchem_cid',  # PubChem CID
        'P2017': 'isomeric_smiles', # isomeric SMILES
        'P1579': 'pubchem_sid', # PubChem SID
        'P638': 'pdb',          # Protein Data Bank ID
    }
    
    claims = entity_info.get('claims', {})
    cross_references = {}
    metadata = {}
    
    # Process each relevant property
    for prop_id, db_name in database_properties.items():
        if prop_id in claims:
            # Check if this database was requested (if specified)
            if target_databases and db_name not in target_databases:
                continue
                
            values = []
            for claim in claims[prop_id]:
                if 'mainsnak' in claim and 'datavalue' in claim['mainsnak']:
                    value = claim['mainsnak']['datavalue']['value']
                    if isinstance(value, str):
                        values.append(value)
                    elif isinstance(value, dict) and 'text' in value:
                        values.append(value['text'])
            
            if values:
                cross_references[db_name] = values
                metadata[db_name] = {
                    'property_id': prop_id,
                    'count': len(values),
                    'wikidata_property_url': f"https://www.wikidata.org/wiki/Property:{prop_id}"
                }
    
    return cross_references, metadata


def _add_urls_to_cross_references(cross_references: Dict[str, List[str]]):
    """Add URL templates to cross-references."""
    
    url_templates = {
        'uniprot': 'https://www.uniprot.org/uniprotkb/{id}',
        'chebi': 'https://www.ebi.ac.uk/chebi/searchId.do?chebiId=CHEBI:{id}',
        'cas': 'https://www.cas.org/cas-data/cas-registry/{id}',
        'chembl': 'https://www.ebi.ac.uk/chembl/compound_report_card/{id}',
        'drugbank': 'https://go.drugbank.com/drugs/{id}',
        'mesh': 'https://meshb.nlm.nih.gov/record/ui?ui={id}',
        'ncbi_gene': 'https://www.ncbi.nlm.nih.gov/gene/{id}',
        'ensembl_gene': 'https://www.ensembl.org/id/{id}',
        'refseq': 'https://www.ncbi.nlm.nih.gov/protein/{id}',
        'disease_ontology': 'https://disease-ontology.org/?id=DOID:{id}',
        'kegg': 'https://www.kegg.jp/entry/{id}',
        'pubchem_cid': 'https://pubchem.ncbi.nlm.nih.gov/compound/{id}',
        'pubchem_sid': 'https://pubchem.ncbi.nlm.nih.gov/substance/{id}',
        'pdb': 'https://www.rcsb.org/structure/{id}'
    }
    
    for db_name, identifiers in cross_references.items():
        if db_name in url_templates:
            template = url_templates[db_name]
            cross_references[db_name] = [
                {
                    'id': id_val,
                    'url': template.format(id=id_val)
                } for id_val in identifiers
            ]


def _generate_suggestions(cross_references: Dict[str, List[str]], entity_name: str) -> List[str]:
    """Generate next-step suggestions."""
    
    suggestions = []
    
    if not cross_references:
        suggestions.extend([
            f'Try: cl_describe {entity_name} for more details',
            'Check if entity has biological properties',
            'Use cl_sparql to query for cross-references'
        ])
    else:
        for db_name, identifiers in cross_references.items():
            if identifiers:
                first_id = identifiers[0] if isinstance(identifiers[0], str) else identifiers[0]['id']
                suggestions.append(f'cl_resolve P{_get_property_number(db_name)} {first_id}')
        
        # General suggestions
        suggestions.extend([
            'cl_sparql for biological relationships',
            'cl_describe for more entity details'
        ])
    
    return suggestions[:5]


def _get_property_number(db_name: str) -> str:
    """Get property number for database."""
    property_map = {
        'uniprot': '352',
        'chebi': '683',
        'refseq': '637',
        'pdb': '638',
        'mesh': '486',
        'chembl': '592'
    }
    return property_map.get(db_name, '352')


def _print_human_readable(response: Dict[str, Any]):
    """Print human-readable output."""
    
    if not response['success']:
        click.echo(f"❌ Error: {response['error']}")
        return
    
    data = response['data']
    entity = data['entity']
    cross_refs = data['cross_references']
    
    click.echo(f"🔗 Cross-references for {entity['name']} ({entity['id']})")
    click.echo(f"📄 Description: {entity.get('description', 'N/A')}")
    click.echo(f"🔗 Wikidata: {entity['wikidata_url']}")
    click.echo()
    
    if cross_refs:
        click.echo(f"📊 Found {data['statistics']['total_identifiers']} cross-references across {data['statistics']['databases_found']} databases:")
        click.echo()
        
        for db_name, identifiers in cross_refs.items():
            click.echo(f"🗄️  {db_name.title()}:")
            for identifier in identifiers[:3]:  # Show first 3
                if isinstance(identifier, dict):
                    click.echo(f"   • {identifier['id']} → {identifier['url']}")
                else:
                    click.echo(f"   • {identifier}")
            if len(identifiers) > 3:
                click.echo(f"   ... and {len(identifiers) - 3} more")
            click.echo()
    else:
        click.echo("❌ No cross-references found")
    
    if response['suggestions']:
        click.echo("💡 Next steps:")
        for suggestion in response['suggestions']:
            click.echo(f"   • {suggestion}")


def _output_error(message: str, output_format: str):
    """Output error in requested format."""
    
    error_response = {
        'success': False,
        'error': message,
        'suggestions': [
            'Check entity ID format (Q123456 or P123456)',
            'Verify entity exists in Wikidata',
            'Try with different target databases'
        ]
    }
    
    if output_format == 'human':
        click.echo(f"❌ Error: {message}")
    else:
        click.echo(json.dumps(error_response, indent=2))


if __name__ == "__main__":
    follow()