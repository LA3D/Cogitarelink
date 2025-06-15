"""Integration test for Wikidata workflow: search → entity → materialize → sparql.

Tests the complete agentic workflow similar to wikidata-mcp/docs/agentic_test.txt
"""

from __future__ import annotations

import json
import pytest
import tempfile
from pathlib import Path
from click.testing import CliRunner

from cogitarelink.cli.cl_wikidata import wikidata
from cogitarelink.cli.cl_materialize import materialize


class TestWikidataAgenticWorkflow:
    """Test complete agentic workflow patterns."""
    
    def setup_method(self):
        """Set up test environment."""
        self.runner = CliRunner()
    
    def test_protein_research_workflow(self):
        """Test protein research workflow like agentic_test.txt."""
        
        print("\n=== Testing Protein Research Workflow ===")
        
        # Step 1: Search for protein entities
        print("1. Searching for 'protein' entities...")
        result = self.runner.invoke(wikidata, [
            'search', 'protein', '--limit', '3', '--format', 'json', '--level', 'full'
        ])
        
        assert result.exit_code == 0
        search_response = json.loads(result.output)
        assert search_response["success"] is True
        
        entities = search_response["data"]["entities"]
        assert len(entities) >= 1
        
        # Should find Q8054 (protein)
        protein_entity = None
        for entity in entities:
            if entity["id"] == "Q8054":
                protein_entity = entity
                break
        
        if not protein_entity:
            protein_entity = entities[0]  # Use first result
        
        print(f"   Found protein entity: {protein_entity['id']} - {protein_entity['name']}")
        
        # Step 2: Get detailed entity information
        print(f"2. Getting detailed info for {protein_entity['id']}...")
        result = self.runner.invoke(wikidata, [
            'entity', protein_entity['id'], '--format', 'json', '--level', 'full'
        ])
        
        assert result.exit_code == 0
        entity_response = json.loads(result.output)
        assert entity_response["success"] is True
        
        entity_data = entity_response["data"]["entity"]
        claims_count = entity_response["data"]["claims_count"]
        print(f"   Retrieved entity with {claims_count} claims")
        
        # Step 3: Create entities for materialization 
        print("3. Creating entities for materialization...")
        test_entities = [
            {
                "@type": "Protein",
                "@id": entity_data["wikidataUrl"],
                "identifier": entity_data["id"],
                "name": entity_data["name"],
                "description": entity_data["description"]
            }
        ]
        
        entities_json = json.dumps(test_entities)
        
        # Step 4: Materialize entities
        print("4. Materializing protein entities...")
        result = self.runner.invoke(materialize, [
            '--from-entities', entities_json,
            '--vocab', 'bioschemas',
            '--format', 'json',
            '--level', 'full'
        ])
        
        assert result.exit_code == 0
        materialize_response = json.loads(result.output)
        assert materialize_response["success"] is True
        
        materialized_count = materialize_response["metadata"]["entities_materialized"]
        print(f"   Materialized {materialized_count} entities")
        
        # Step 5: Follow up with SPARQL query for related proteins
        print("5. Querying for related proteins...")
        sparql_query = f"""
        SELECT ?protein ?proteinLabel WHERE {{
          ?protein wdt:P31 wd:{protein_entity['id']} .
          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en" }}
        }}
        """
        
        result = self.runner.invoke(wikidata, [
            'sparql', sparql_query, '--limit', '5', '--format', 'json', '--level', 'full'
        ])
        
        assert result.exit_code == 0
        sparql_response = json.loads(result.output)
        assert sparql_response["success"] is True
        
        sparql_results = sparql_response["data"]["sparql_results"]
        print(f"   Found {len(sparql_results)} related proteins")
        
        print("✅ Complete protein research workflow successful!")
        
        return {
            "search_results": len(entities),
            "entity_claims": claims_count,
            "materialized_entities": materialized_count,
            "sparql_results": len(sparql_results)
        }
    
    def test_cross_reference_discovery_workflow(self):
        """Test cross-reference discovery like preproinsulin example."""
        
        print("\n=== Testing Cross-Reference Discovery Workflow ===")
        
        # Step 1: Search for preproinsulin 
        print("1. Searching for 'preproinsulin'...")
        result = self.runner.invoke(wikidata, [
            'search', 'preproinsulin', '--limit', '3', '--format', 'json', '--level', 'full'
        ])
        
        assert result.exit_code == 0
        search_response = json.loads(result.output)
        assert search_response["success"] is True
        
        entities = search_response["data"]["entities"]
        if not entities:
            pytest.skip("Preproinsulin not found in search results")
        
        target_entity = entities[0]
        print(f"   Found: {target_entity['id']} - {target_entity['name']}")
        
        # Step 2: Get entity with cross-references
        print(f"2. Getting cross-references for {target_entity['id']}...")
        result = self.runner.invoke(wikidata, [
            'entity', target_entity['id'], '--format', 'json', '--level', 'full'
        ])
        
        assert result.exit_code == 0
        entity_response = json.loads(result.output)
        assert entity_response["success"] is True
        
        cross_refs = entity_response["data"]["cross_references"]
        print(f"   Found cross-references: {list(cross_refs.keys())}")
        
        # Step 3: Create entity for materialization with cross-references
        print("3. Materializing entity with cross-references...")
        entity_data = entity_response["data"]["entity"]
        
        materialization_entity = {
            "@type": "Protein",
            "@id": entity_data["wikidataUrl"],
            "identifier": entity_data["id"],
            "name": entity_data["name"],
            "description": entity_data["description"],
            "crossReferences": cross_refs
        }
        
        entities_json = json.dumps([materialization_entity])
        
        result = self.runner.invoke(materialize, [
            '--from-entities', entities_json,
            '--vocab', 'bioschemas',
            '--include-provenance',
            '--format', 'json',
            '--level', 'full'
        ])
        
        assert result.exit_code == 0
        materialize_response = json.loads(result.output)
        assert materialize_response["success"] is True
        
        print("✅ Cross-reference discovery workflow successful!")
        
        return {
            "entity_found": target_entity['id'],
            "cross_reference_databases": len(cross_refs),
            "materialization_success": materialize_response["success"]
        }
    
    def test_sparql_to_materialization_pipeline(self):
        """Test SPARQL → materialization pipeline."""
        
        print("\n=== Testing SPARQL → Materialization Pipeline ===")
        
        # Step 1: Execute SPARQL query for proteins
        print("1. Executing SPARQL query for proteins...")
        sparql_query = """
        SELECT ?item ?itemLabel WHERE {
          ?item wdt:P31 wd:Q8054 .
          SERVICE wikibase:label { bd:serviceParam wikibase:language "en" }
        }
        """
        
        result = self.runner.invoke(wikidata, [
            'sparql', sparql_query, '--limit', '5', '--format', 'json', '--level', 'full'
        ])
        
        assert result.exit_code == 0
        sparql_response = json.loads(result.output)
        assert sparql_response["success"] is True
        
        sparql_results = sparql_response["data"]["sparql_results"]
        print(f"   SPARQL returned {len(sparql_results)} protein results")
        
        # Step 2: Convert SPARQL results to entities format
        print("2. Converting SPARQL results to entities...")
        entities = []
        for result_item in sparql_results:
            if "item" in result_item and "itemLabel" in result_item:
                entity_uri = result_item["item"]["value"]
                entity_label = result_item["itemLabel"]["value"]
                entity_id = entity_uri.split("/")[-1]
                
                entity = {
                    "@type": "Protein",
                    "@id": entity_uri,
                    "identifier": entity_id,
                    "name": entity_label,
                    "source": "wikidata_sparql"
                }
                entities.append(entity)
        
        print(f"   Created {len(entities)} entities from SPARQL results")
        
        # Step 3: Materialize the SPARQL-derived entities
        print("3. Materializing SPARQL-derived entities...")
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"results": sparql_results}, f)
            sparql_file = f.name
        
        try:
            result = self.runner.invoke(materialize, [
                '--from-sparql-results', sparql_file,
                '--vocab', 'bioschemas',
                '--format', 'json',
                '--level', 'full'
            ])
            
            assert result.exit_code == 0
            materialize_response = json.loads(result.output)
            assert materialize_response["success"] is True
            
            materialized_count = materialize_response["metadata"]["entities_materialized"]
            print(f"   Materialized {materialized_count} entities from SPARQL results")
            
        finally:
            Path(sparql_file).unlink()
        
        print("✅ SPARQL → Materialization pipeline successful!")
        
        return {
            "sparql_results": len(sparql_results),
            "entities_created": len(entities),
            "materialized_count": materialized_count
        }


def test_complete_agentic_workflow():
    """Run complete agentic workflow test."""
    
    test_runner = TestWikidataAgenticWorkflow()
    test_runner.setup_method()
    
    print("🧪 Running Complete Agentic Workflow Tests")
    
    # Test 1: Protein research workflow
    protein_results = test_runner.test_protein_research_workflow()
    
    # Test 2: Cross-reference discovery 
    cross_ref_results = test_runner.test_cross_reference_discovery_workflow()
    
    # Test 3: SPARQL to materialization pipeline
    pipeline_results = test_runner.test_sparql_to_materialization_pipeline()
    
    print(f"\n🎉 All Agentic Workflow Tests Completed!")
    print(f"   Protein Research: {protein_results}")
    print(f"   Cross-Reference Discovery: {cross_ref_results}")
    print(f"   SPARQL Pipeline: {pipeline_results}")
    
    return {
        "protein_workflow": protein_results,
        "cross_reference_workflow": cross_ref_results,
        "sparql_pipeline": pipeline_results
    }


if __name__ == "__main__":
    # Run the complete workflow test
    results = test_complete_agentic_workflow()
    
    print(f"\n📊 Final Test Results:")
    print(json.dumps(results, indent=2))