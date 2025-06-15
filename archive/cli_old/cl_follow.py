"""
cl_follow: Cross-reference following with biological intelligence

Provides automatic cross-reference resolution and navigation between 
biological databases with agent-friendly guidance.
"""

from __future__ import annotations

import asyncio
import json
import sys
import time
from typing import Optional, List, Dict, Any

import click

from ..adapters.wikidata_client import WikidataClient
from ..adapters.multi_sparql_client import MultiSparqlClient
from ..core.entity import Entity
from ..core.debug import get_logger
from ..intelligence.guidance_generator import guidance_generator, GuidanceContext, DomainType
from ..intelligence.response_manager import response_manager, ResponseLevel

log = get_logger("cl_follow")


@click.command()
@click.argument('entity_id', required=True)
@click.option('--databases', multiple=True, 
              help='Target databases to follow: uniprot, chebi, pubchem, ensembl, mesh')
@click.option('--auto-discover', is_flag=True, default=True,
              help='Automatically discover available cross-references')
@click.option('--include-metadata', is_flag=True, default=True,
              help='Include metadata about cross-reference properties')
@click.option('--resolve-urls', is_flag=True, default=False,
              help='Resolve cross-reference URLs (slower but richer data)')
@click.option('--level', type=click.Choice(['summary', 'detailed', 'full']), 
              default='detailed', help='Response detail level')
@click.option('--format', 'output_format', type=click.Choice(['json', 'human']), 
              default='json', help='Output format')
def follow(
    entity_id: str,
    databases: List[str],
    auto_discover: bool,
    include_metadata: bool,
    resolve_urls: bool,
    level: str,
    output_format: str
):
    """
    Follow cross-references from a Wikidata entity to external databases.
    
    Examples:
        cl_follow Q42 --databases uniprot,chebi
        cl_follow Q8054 --auto-discover --resolve-urls
        cl_follow P01308 --databases uniprot --format human
        cl_follow Q7240673 --level full --include-metadata
    """
    asyncio.run(_follow_async(
        entity_id, list(databases), auto_discover, include_metadata, 
        resolve_urls, level, output_format
    ))


async def _follow_async(
    entity_id: str,
    databases: List[str],
    auto_discover: bool,
    include_metadata: bool,
    resolve_urls: bool,
    level: str,
    output_format: str
):
    """Async cross-reference following with biological intelligence."""
    
    start_time = time.time()
    
    try:
        log.info(f"Following cross-references for entity: {entity_id}")
        
        # Validate entity ID format
        if not ((entity_id.startswith('Q') or entity_id.startswith('P')) and entity_id[1:].isdigit()):
            _output_error(
                f"Entity ID must be in format Q123456 or P123456, got: {entity_id}",
                output_format
            )
            return
        
        # Initialize clients
        wikidata_client = WikidataClient(timeout=30)
        sparql_client = MultiSparqlClient(timeout=30)
        
        # Get entity data with claims
        log.info(f"Retrieving entity data for {entity_id}")
        entity_data = await wikidata_client.get_entities([entity_id])
        
        if entity_id not in entity_data.get('entities', {}):
            _output_error(f"Entity {entity_id} not found in Wikidata", output_format)
            return
        
        entity_info = entity_data['entities'][entity_id]
        
        # Extract cross-references
        cross_references = await _extract_cross_references(
            entity_info, databases, auto_discover, include_metadata
        )
        
        # Resolve URLs if requested
        resolved_data = {}
        if resolve_urls:
            resolved_data = await _resolve_cross_reference_urls(
                cross_references, sparql_client
            )
        
        # Generate biological intelligence
        guidance = await _generate_cross_reference_guidance(
            entity_id, entity_info, cross_references, resolved_data
        )
        
        # Build comprehensive response
        response = await _build_follow_response(
            entity_id, entity_info, cross_references, resolved_data, 
            guidance, start_time, level
        )
        
        # Apply response management
        response_level = ResponseLevel(level)
        if response_level != ResponseLevel.FULL:
            final_response, _ = response_manager.truncate_response(
                response, response_level, preserve_structure=True
            )
        else:
            final_response = response_manager.enhance_for_agent_chain(response)
            
        _output_response(final_response, output_format)
        
    except Exception as e:
        log.error(f"Cross-reference following failed: {e}")
        _output_error(f"Cross-reference following failed: {str(e)}", output_format)
        sys.exit(1)


async def _extract_cross_references(
    entity_info: Dict[str, Any],
    target_databases: List[str],
    auto_discover: bool,
    include_metadata: bool
) -> Dict[str, Any]:
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
    }
    
    claims = entity_info.get('claims', {})
    cross_references = {}
    metadata = {}
    
    # Process each relevant property
    for prop_id, db_name in database_properties.items():
        if prop_id in claims:
            # Check if this database was requested
            if target_databases and db_name not in target_databases and not auto_discover:
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
                
                if include_metadata:
                    metadata[db_name] = {
                        'property_id': prop_id,
                        'count': len(values),
                        'wikidata_property_url': f"https://www.wikidata.org/wiki/Property:{prop_id}"
                    }
    
    return {
        'cross_references': cross_references,
        'metadata': metadata,
        'total_databases': len(cross_references),
        'total_identifiers': sum(len(refs) for refs in cross_references.values())
    }


async def _resolve_cross_reference_urls(
    cross_ref_data: Dict[str, Any], 
    sparql_client: MultiSparqlClient
) -> Dict[str, Any]:
    """Resolve cross-reference URLs and fetch additional data."""
    
    cross_references = cross_ref_data.get('cross_references', {})
    resolved_data = {}
    
    # URL templates for different databases
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
        'pubchem_sid': 'https://pubchem.ncbi.nlm.nih.gov/substance/{id}'
    }
    
    for db_name, identifiers in cross_references.items():
        if db_name in url_templates:
            template = url_templates[db_name]
            resolved_data[db_name] = {
                'identifiers': identifiers,
                'urls': [template.format(id=id_val) for id_val in identifiers],
                'database_info': _get_database_info(db_name)
            }
            
            # Try to query the corresponding SPARQL endpoint if available
            if db_name == 'uniprot':
                try:
                    # Query UniProt for basic protein info
                    for uniprot_id in identifiers[:3]:  # Limit to avoid timeout
                        query = f"""
                        SELECT ?protein ?name ?organism WHERE {{
                            ?protein up:mnemonic "{uniprot_id}" .
                            OPTIONAL {{ ?protein up:recommendedName/up:fullName ?name }}
                            OPTIONAL {{ ?protein up:organism ?organism }}
                        }}
                        LIMIT 1
                        """
                        
                        result = await sparql_client.sparql_query(query, endpoint="uniprot")
                        bindings = result.get('results', {}).get('bindings', [])
                        
                        if bindings:
                            binding = bindings[0]
                            resolved_data[db_name][f'{uniprot_id}_details'] = {
                                'protein_uri': binding.get('protein', {}).get('value', ''),
                                'name': binding.get('name', {}).get('value', ''),
                                'organism': binding.get('organism', {}).get('value', '')
                            }
                except Exception as e:
                    log.warning(f"Failed to resolve UniProt data: {e}")
    
    return resolved_data


def _get_database_info(db_name: str) -> Dict[str, str]:
    """Get database description and type information."""
    
    database_info = {
        'uniprot': {
            'full_name': 'Universal Protein Resource',
            'type': 'protein_database',
            'description': 'Comprehensive protein sequence and functional information',
            'sparql_endpoint': 'https://sparql.uniprot.org/sparql'
        },
        'chebi': {
            'full_name': 'Chemical Entities of Biological Interest',
            'type': 'chemical_database',
            'description': 'Chemical entities and their relationships',
            'sparql_endpoint': None
        },
        'cas': {
            'full_name': 'Chemical Abstracts Service Registry',
            'type': 'chemical_registry',
            'description': 'Unique chemical substance identifiers',
            'sparql_endpoint': None
        },
        'chembl': {
            'full_name': 'ChEMBL Database',
            'type': 'chemical_database',
            'description': 'Bioactive molecules with drug-like properties',
            'sparql_endpoint': None
        },
        'drugbank': {
            'full_name': 'DrugBank Database',
            'type': 'drug_database',
            'description': 'Comprehensive drug and drug target information',
            'sparql_endpoint': None
        },
        'mesh': {
            'full_name': 'Medical Subject Headings',
            'type': 'medical_vocabulary',
            'description': 'Controlled vocabulary for biomedical literature',
            'sparql_endpoint': None
        },
        'ncbi_gene': {
            'full_name': 'NCBI Gene',
            'type': 'gene_database',
            'description': 'Gene-specific information from NCBI',
            'sparql_endpoint': None
        },
        'ensembl_gene': {
            'full_name': 'Ensembl Genome Browser',
            'type': 'genome_database',
            'description': 'Genome annotation and comparative genomics',
            'sparql_endpoint': None
        }
    }
    
    return database_info.get(db_name, {
        'full_name': db_name.title(),
        'type': 'unknown',
        'description': f'{db_name} database',
        'sparql_endpoint': None
    })


async def _generate_cross_reference_guidance(
    entity_id: str,
    entity_info: Dict[str, Any],
    cross_ref_data: Dict[str, Any],
    resolved_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Generate biological intelligence for cross-reference navigation."""
    
    # Determine entity type based on cross-references
    cross_references = cross_ref_data.get('cross_references', {})
    
    if 'uniprot' in cross_references:
        entity_type = "Protein"
        domain_type = DomainType.LIFE_SCIENCES
    elif any(db in cross_references for db in ['chebi', 'cas', 'chembl', 'drugbank']):
        entity_type = "Chemical"
        domain_type = DomainType.CHEMISTRY
    elif any(db in cross_references for db in ['ncbi_gene', 'ensembl_gene']):
        entity_type = "Gene"
        domain_type = DomainType.LIFE_SCIENCES
    else:
        entity_type = "BiologicalEntity"
        domain_type = DomainType.KNOWLEDGE_GRAPH
    
    # Generate guidance context
    guidance_context = GuidanceContext(
        entity_type=entity_type,
        domain_type=domain_type,
        properties=list(cross_references.keys()),
        confidence_score=0.9,  # High confidence for cross-reference data
        previous_actions=["cross_reference_following"],
        available_tools=["cl_wikidata sparql", "cl_validate", "cl_discover"]
    )
    
    return guidance_generator.generate_guidance(guidance_context)


async def _build_follow_response(
    entity_id: str,
    entity_info: Dict[str, Any],
    cross_ref_data: Dict[str, Any],
    resolved_data: Dict[str, Any],
    guidance: Dict[str, Any],
    start_time: float,
    level: str
) -> Dict[str, Any]:
    """Build comprehensive cross-reference following response."""
    
    execution_time = int((time.time() - start_time) * 1000)
    
    # Extract entity basic info
    entity_name = entity_info.get('labels', {}).get('en', {}).get('value', 'Unknown')
    entity_description = entity_info.get('descriptions', {}).get('en', {}).get('value', '')
    
    cross_references = cross_ref_data.get('cross_references', {})
    
    return {
        "success": True,
        "data": {
            "entity": {
                "id": entity_id,
                "name": entity_name,
                "description": entity_description,
                "wikidata_url": f"https://www.wikidata.org/wiki/{entity_id}"
            },
            "cross_references": cross_references,
            "cross_reference_metadata": cross_ref_data.get('metadata', {}),
            "resolved_data": resolved_data,
            "statistics": {
                "databases_found": cross_ref_data.get('total_databases', 0),
                "total_identifiers": cross_ref_data.get('total_identifiers', 0),
                "resolved_databases": len(resolved_data)
            }
        },
        "metadata": {
            "execution_time_ms": execution_time,
            "entity_id": entity_id,
            "cross_reference_count": cross_ref_data.get('total_identifiers', 0),
            "confidence_score": 0.95
        },
        "suggestions": {
            "next_tools": [
                "Query external databases using discovered identifiers",
                "cl_wikidata sparql with cross-reference filters",
                "cl_validate entity data for semantic analysis"
            ],
            "database_exploration": [
                f"Explore {db}: {ids[0] if ids else 'N/A'}" 
                for db, ids in cross_references.items()
            ][:5],
            "reasoning_patterns": guidance.get("reasoning_patterns", [])
        },
        "claude_guidance": {
            "cross_reference_summary": f"Found {cross_ref_data.get('total_identifiers', 0)} cross-references across {cross_ref_data.get('total_databases', 0)} databases for {entity_name}",
            "database_intelligence": [
                f"{db.title()}: {len(ids)} identifier(s)" 
                for db, ids in cross_references.items()
            ],
            "workflow_recommendations": [
                "Use cross-references to query specialized biological databases",
                "Follow protein identifiers to UniProt for detailed structural data",
                "Cross-reference chemical compounds with ChEBI and PubChem",
                "Integrate findings with semantic materialization workflows"
            ],
            "biological_context": guidance.get("reasoning_patterns", [])[:3]
        }
    }


def _output_error(message: str, output_format: str):
    """Output error in requested format."""
    error_response = {
        "success": False,
        "error": {
            "code": "CROSS_REFERENCE_ERROR",
            "message": message,
            "suggestions": [
                "Check entity ID format (Q123456 or P123456)",
                "Verify entity exists in Wikidata",
                "Try with different target databases"
            ]
        }
    }
    _output_response(error_response, output_format)


def _output_response(response: Dict[str, Any], output_format: str):
    """Output response in requested format."""
    
    if output_format == 'json':
        click.echo(json.dumps(response, indent=2))
    elif output_format == 'human':
        _print_human_readable(response)


def _print_human_readable(response: Dict[str, Any]):
    """Print human-readable cross-reference summary."""
    
    if response.get("success", False):
        data = response.get("data", {})
        entity = data.get("entity", {})
        cross_refs = data.get("cross_references", {})
        stats = data.get("statistics", {})
        
        print(f"🔗 Cross-References for {entity.get('name', 'Unknown')} ({entity.get('id', '')})")
        print(f"   Description: {entity.get('description', 'No description')}")
        print(f"   Databases: {stats.get('databases_found', 0)}")
        print(f"   Total Identifiers: {stats.get('total_identifiers', 0)}")
        
        if cross_refs:
            print(f"\n📊 Database Cross-References:")
            for db, identifiers in cross_refs.items():
                print(f"   {db.title()}: {', '.join(identifiers[:3])}")
                if len(identifiers) > 3:
                    print(f"      ... and {len(identifiers) - 3} more")
        
        suggestions = response.get("suggestions", {})
        next_tools = suggestions.get("next_tools", [])
        if next_tools:
            print(f"\n💡 Next Steps:")
            for tool in next_tools[:3]:
                print(f"   → {tool}")
                
    else:
        error = response.get("error", {})
        print(f"❌ Error: {error.get('message', 'Unknown error')}")


if __name__ == "__main__":
    follow()