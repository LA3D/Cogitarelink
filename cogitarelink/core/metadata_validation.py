"""Metadata validation and hallucination guards using cross-reference validation.

Prevents hallucinations by validating suggestions against multiple authoritative sources.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Set
from datetime import datetime

from .discovery_infrastructure import (
    property_discovery, entity_type_discovery, endpoint_verification
)
from .universal_identifier_discovery import universal_identifier_discovery
from ..discovery.base import discovery_engine
from ..discovery.cache_manager import cache_manager
from ..core.debug import get_logger

log = get_logger("metadata_validation")


@dataclass
class ValidationResult:
    """Result of metadata validation with confidence scoring."""
    is_valid: bool
    confidence_score: float  # 0.0 to 1.0
    validation_details: Dict[str, Any]
    warnings: List[str]
    errors: List[str]
    
    @property
    def is_fully_valid(self) -> bool:
        """Check if validation passed without any errors or warnings."""
        return self.is_valid and len(self.errors) == 0 and len(self.warnings) == 0


@dataclass 
class DatabaseValidationResult:
    """Result of database accessibility validation."""
    validated_databases: List[str]
    rejected_databases: List[str]
    accessibility_scores: Dict[str, float]
    warnings: List[str]


@dataclass
class IdentifierValidationResult:
    """Result of external identifier validation."""
    valid_identifiers: Dict[str, str]
    invalid_identifiers: Dict[str, str]
    format_issues: List[str]
    consistency_scores: Dict[str, float]


class CrossReferenceValidator:
    """Validates external identifier consistency across databases."""
    
    def __init__(self):
        self.cache_manager = cache_manager
        self.discovery_engine = discovery_engine
        
    def validate_cross_reference_consistency(
        self, 
        source_db: str, 
        source_id: str,
        target_db: str, 
        expected_ids: List[str]
    ) -> ValidationResult:
        """Validate that source database contains expected cross-references."""
        
        cache_key = f"cross_ref_validation:{source_db}:{source_id}:{target_db}"
        cached = self.cache_manager.get(cache_key)
        if cached:
            return ValidationResult(**cached)
        
        validation_details = {
            "source_db": source_db,
            "source_id": source_id,
            "target_db": target_db,
            "expected_ids": expected_ids
        }
        
        warnings = []
        errors = []
        
        try:
            # Query source database for cross-references to target database
            if source_db == "uniprot" and target_db == "pdb":
                cross_refs = self._query_uniprot_pdb_cross_refs(source_id)
            elif source_db == "wikidata":
                cross_refs = self._query_wikidata_cross_refs(source_id, target_db)
            else:
                log.warning(f"Cross-reference validation not implemented for {source_db} → {target_db}")
                cross_refs = []
            
            # Check consistency
            found_ids = set(cross_refs)
            expected_set = set(expected_ids)
            
            missing_ids = expected_set - found_ids
            extra_ids = found_ids - expected_set
            
            if missing_ids:
                warnings.append(f"Missing cross-references in {source_db}: {list(missing_ids)}")
            
            if extra_ids:
                validation_details["extra_cross_refs"] = list(extra_ids)
            
            # Calculate confidence based on agreement
            if expected_set:
                agreement_ratio = len(found_ids & expected_set) / len(expected_set)
            else:
                agreement_ratio = 1.0 if not found_ids else 0.5
                
            confidence_score = agreement_ratio * 0.9  # Slightly conservative
            is_valid = agreement_ratio >= 0.5  # At least half should match
            
            validation_details.update({
                "found_cross_refs": list(found_ids),
                "agreement_ratio": agreement_ratio,
                "validation_timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            log.error(f"Cross-reference validation failed: {e}")
            errors.append(f"Validation error: {str(e)}")
            confidence_score = 0.0
            is_valid = False
        
        result = ValidationResult(
            is_valid=is_valid,
            confidence_score=confidence_score,
            validation_details=validation_details,
            warnings=warnings,
            errors=errors
        )
        
        # Cache result
        self.cache_manager.set(cache_key, result.__dict__, ttl=3600)
        
        return result
    
    def validate_multi_source_consistency(self, external_ids: Dict[str, Any]) -> ValidationResult:
        """Validate consistency across multiple external identifier sources."""
        
        validation_details = {"external_ids": external_ids}
        warnings = []
        errors = []
        confidence_scores = []
        
        # Validate each pair of cross-references
        db_pairs = [
            ("wikidata", "uniprot"),
            ("uniprot", "pdb"),
            ("wikidata", "pdb")
        ]
        
        for source_db, target_db in db_pairs:
            if source_db in external_ids and target_db in external_ids:
                source_id = external_ids[source_db]
                target_ids = external_ids[target_db]
                
                if isinstance(target_ids, str):
                    target_ids = [target_ids]
                
                cross_ref_result = self.validate_cross_reference_consistency(
                    source_db, source_id, target_db, target_ids
                )
                
                confidence_scores.append(cross_ref_result.confidence_score)
                warnings.extend(cross_ref_result.warnings)
                errors.extend(cross_ref_result.errors)
                
                validation_details[f"{source_db}_{target_db}_validation"] = cross_ref_result.validation_details
        
        # Overall confidence is average of individual validations
        overall_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
        is_valid = overall_confidence >= 0.7 and len(errors) == 0
        
        return ValidationResult(
            is_valid=is_valid,
            confidence_score=overall_confidence,
            validation_details=validation_details,
            warnings=warnings,
            errors=errors
        )
    
    def _query_uniprot_pdb_cross_refs(self, uniprot_id: str) -> List[str]:
        """Query UniProt API for PDB cross-references."""
        try:
            import httpx
            
            log.debug(f"Querying UniProt {uniprot_id} for PDB cross-references")
            
            # Query UniProt REST API for cross-references
            url = f"https://rest.uniprot.org/uniprotkb/{uniprot_id}.json"
            
            with httpx.Client(timeout=10.0) as client:
                response = client.get(url)
                response.raise_for_status()
                data = response.json()
                
                # Extract PDB cross-references from UniProt data
                pdb_ids = []
                
                # Look for PDB references in dbReferences
                for ref in data.get("dbReferences", []):
                    if ref.get("type") == "PDB":
                        pdb_id = ref.get("id")
                        if pdb_id:
                            pdb_ids.append(pdb_id)
                
                log.debug(f"Found {len(pdb_ids)} PDB cross-references for {uniprot_id}")
                return pdb_ids
                
        except Exception as e:
            log.debug(f"UniProt cross-reference query failed: {e}")
            return []
    
    def _query_wikidata_cross_refs(self, entity_id: str, target_db: str) -> List[str]:
        """Query Wikidata for cross-references to target database."""
        
        # Use universal identifier discovery to get property mapping
        db_property_map = {}
        for prop_id, pattern in universal_identifier_discovery.known_patterns.items():
            if pattern.database_name.lower() == target_db.lower():
                db_property_map[target_db.lower()] = prop_id
                break
        
        # Fallback to hardcoded mapping for compatibility
        if target_db.lower() not in db_property_map:
            fallback_map = {
                "uniprot": "P352",
                "pdb": "P638", 
                "ensembl": "P705",
                "chembl": "P592",
                "pubchem": "P662",
                "mesh": "P486",
                "drugbank": "P2566",
                "rkd_images": "P350",
                "joconde": "P347",
                "louvre": "P9394",
                "cas": "P231",
                "viaf": "P214",
                "isni": "P213",
                "loc": "P244",
                "geonames": "P1566"
            }
            db_property_map.update(fallback_map)
        
        property_id = db_property_map.get(target_db.lower())
        if not property_id:
            log.debug(f"No property mapping for database: {target_db}")
            return []
        
        # Query Wikidata SPARQL endpoint directly
        sparql_query = f"""
        SELECT ?value WHERE {{
            wd:{entity_id} wdt:{property_id} ?value .
        }}
        """
        
        try:
            import httpx
            
            # Query Wikidata SPARQL endpoint directly
            sparql_endpoint = "https://query.wikidata.org/sparql"
            
            headers = {
                "Accept": "application/sparql-results+json",
                "User-Agent": "CogitareLink/1.0 (https://github.com/example/cogitarelink)"
            }
            
            with httpx.Client(timeout=10.0) as client:
                response = client.get(
                    sparql_endpoint,
                    params={"query": sparql_query},
                    headers=headers
                )
                response.raise_for_status()
                data = response.json()
                
                # Extract values from SPARQL results
                values = []
                for binding in data.get("results", {}).get("bindings", []):
                    if "value" in binding:
                        values.append(binding["value"]["value"])
                
                log.debug(f"Found {len(values)} {target_db} cross-references for {entity_id}")
                return values
                
        except Exception as e:
            log.debug(f"Wikidata cross-reference query failed: {e}")
            return []


class ConfidenceScorer:
    """Calculates confidence scores for validation results."""
    
    def __init__(self):
        self.scoring_weights = {
            "source_agreement": 0.4,
            "timestamp_consistency": 0.2,
            "format_validity": 0.2,
            "database_accessibility": 0.2
        }
        self.validation_history = {}
    
    def calculate_cross_reference_confidence(self, validation_data: Dict[str, Any]) -> float:
        """Calculate confidence score for cross-reference validation."""
        
        scores = {}
        
        # Source agreement score
        sources_agreeing = validation_data.get("sources_agreeing", 0)
        total_sources = validation_data.get("total_sources", 1)
        scores["source_agreement"] = sources_agreeing / total_sources
        
        # Timestamp consistency score
        scores["timestamp_consistency"] = 1.0 if validation_data.get("timestamp_consistency", True) else 0.5
        
        # Format validity score  
        scores["format_validity"] = 1.0 if validation_data.get("identifier_format_valid", True) else 0.0
        
        # Database accessibility score
        scores["database_accessibility"] = 1.0 if validation_data.get("database_accessibility", True) else 0.0
        
        # Weighted average
        confidence = sum(
            scores[factor] * self.scoring_weights[factor] 
            for factor in scores
        )
        
        return min(max(confidence, 0.0), 1.0)  # Clamp to [0, 1]
    
    def calculate_pathway_confidence(self, pathway_data: Dict[str, Any]) -> float:
        """Calculate confidence score for research pathway suggestions."""
        
        databases_accessible = pathway_data.get("databases_accessible", 0)
        databases_suggested = pathway_data.get("databases_suggested", 1)
        accessibility_ratio = databases_accessible / databases_suggested
        
        cross_references_valid = pathway_data.get("cross_references_valid", False)
        cross_ref_score = 1.0 if cross_references_valid else 0.5
        
        historical_success = pathway_data.get("historical_success_rate", 0.5)
        
        # Weighted combination
        confidence = (
            accessibility_ratio * 0.4 +
            cross_ref_score * 0.4 +
            historical_success * 0.2
        )
        
        return min(max(confidence, 0.0), 1.0)


class HallucinationGuard:
    """Prevents hallucinations by validating suggestions before presenting them."""
    
    def __init__(self):
        self.endpoint_verification = endpoint_verification
        self.cross_ref_validator = CrossReferenceValidator()
        
    def filter_accessible_databases(self, suggested_databases: List[str]) -> DatabaseValidationResult:
        """Filter database suggestions to only include accessible ones."""
        
        validated_databases = []
        rejected_databases = []
        accessibility_scores = {}
        warnings = []
        
        # Use universal identifier discovery to build endpoint mapping
        database_endpoints = {}
        for pattern in universal_identifier_discovery.known_patterns.values():
            if pattern.endpoint_url:
                database_endpoints[pattern.database_name] = pattern.endpoint_url
        
        # Add special endpoints not covered by patterns
        database_endpoints.update({
            "wikidata": "https://query.wikidata.org/sparql"
        })
        
        for database in suggested_databases:
            try:
                # Try to verify database accessibility
                is_accessible = self._test_database_accessibility(database, database_endpoints)
                accessibility_scores[database] = 1.0 if is_accessible else 0.0
                
                if is_accessible:
                    validated_databases.append(database)
                else:
                    rejected_databases.append(database)
                    warnings.append(f"Database '{database}' is not accessible - removed from suggestions")
                    
            except Exception as e:
                log.warning(f"Failed to verify database {database}: {e}")
                rejected_databases.append(database)
                accessibility_scores[database] = 0.0
                warnings.append(f"Could not verify database '{database}' - removed from suggestions")
        
        return DatabaseValidationResult(
            validated_databases=validated_databases,
            rejected_databases=rejected_databases,
            accessibility_scores=accessibility_scores,
            warnings=warnings
        )
    
    def _test_database_accessibility(self, database: str, endpoints: Dict[str, str]) -> bool:
        """Test if a database endpoint is actually accessible."""
        endpoint = endpoints.get(database.lower())
        if not endpoint:
            log.debug(f"No endpoint configured for database: {database}")
            return False
        
        try:
            import httpx
            
            # Test endpoint accessibility with a simple HEAD/GET request
            with httpx.Client(timeout=5.0) as client:
                if database.lower() == "wikidata":
                    # Test SPARQL endpoint with a simple query
                    response = client.get(
                        endpoint,
                        params={"query": "SELECT ?s WHERE { ?s ?p ?o } LIMIT 1"},
                        headers={"Accept": "application/sparql-results+json"}
                    )
                else:
                    # Test REST endpoint accessibility
                    response = client.head(endpoint)
                
                # Consider 2xx, 3xx, and some 4xx responses as "accessible"
                # (4xx might just mean the specific resource doesn't exist, but API is working)
                is_accessible = response.status_code < 500
                
                log.debug(f"Database {database} accessibility test: {response.status_code} -> {'accessible' if is_accessible else 'not accessible'}")
                return is_accessible
                
        except Exception as e:
            log.debug(f"Database {database} accessibility test failed: {e}")
            return False
    
    def validate_identifier_suggestions(self, identifier_suggestions: Dict[str, Any]) -> IdentifierValidationResult:
        """Validate that suggested external identifiers have valid formats."""
        
        valid_identifiers = {}
        invalid_identifiers = {}
        format_issues = []
        consistency_scores = {}
        
        # Use universal identifier discovery to get format patterns
        format_patterns = {}
        for prop_id, pattern in universal_identifier_discovery.known_patterns.items():
            if pattern.format_pattern:
                format_patterns[prop_id] = pattern.format_pattern
        
        for property_id, identifier_value in identifier_suggestions.items():
            
            # Handle both single values and lists
            if isinstance(identifier_value, list):
                identifier_values = identifier_value
            else:
                identifier_values = [identifier_value]
            
            # Check if property exists
            try:
                prop_info = property_discovery.discover_properties([property_id])
                if property_id not in prop_info:
                    invalid_identifiers[property_id] = identifier_value
                    format_issues.append(f"Property {property_id} does not exist")
                    continue
                    
                # Check if it's actually an external reference
                if not prop_info[property_id].is_external_ref:
                    invalid_identifiers[property_id] = identifier_value
                    format_issues.append(f"Property {property_id} is not an external reference")
                    continue
                    
            except Exception as e:
                log.warning(f"Could not validate property {property_id}: {e}")
                invalid_identifiers[property_id] = identifier_value
                continue
            
            # Check identifier format for each value
            pattern = format_patterns.get(property_id)
            all_valid = True
            
            for id_val in identifier_values:
                if pattern and not re.match(pattern, str(id_val)):
                    all_valid = False
                    format_issues.append(f"Identifier '{id_val}' does not match expected format for {property_id}")
            
            if all_valid:
                valid_identifiers[property_id] = identifier_value
                consistency_scores[property_id] = 1.0
            else:
                invalid_identifiers[property_id] = identifier_value
                consistency_scores[property_id] = 0.0
        
        return IdentifierValidationResult(
            valid_identifiers=valid_identifiers,
            invalid_identifiers=invalid_identifiers,
            format_issues=format_issues,
            consistency_scores=consistency_scores
        )
    
    def validate_research_pathway(self, pathway: Dict[str, Any]) -> ValidationResult:
        """Validate that suggested research pathway is feasible."""
        
        entity_id = pathway.get("entity_id")
        steps = pathway.get("steps", [])
        
        validation_details = {"entity_id": entity_id, "total_steps": len(steps)}
        warnings = []
        errors = []
        invalid_steps = []
        
        # Extract databases from pathway steps
        suggested_databases = []
        for step in steps:
            if "--to-db" in step:
                db_name = step.split("--to-db")[-1].strip()
                suggested_databases.append(db_name)
        
        # Validate database accessibility
        db_validation = self.filter_accessible_databases(suggested_databases)
        
        # Check for invalid steps
        for i, step in enumerate(steps):
            if "--to-db" in step:
                db_name = step.split("--to-db")[-1].strip()
                if db_name in db_validation.rejected_databases:
                    invalid_steps.append(i)
                    errors.append(f"Step {i+1} suggests inaccessible database: {db_name}")
        
        warnings.extend(db_validation.warnings)
        
        # Calculate confidence
        valid_steps = len(steps) - len(invalid_steps)
        confidence_score = valid_steps / len(steps) if steps else 0.0
        
        is_valid = len(invalid_steps) == 0
        
        validation_details.update({
            "valid_steps": valid_steps,
            "invalid_steps": invalid_steps,
            "database_validation": db_validation.__dict__
        })
        
        return ValidationResult(
            is_valid=is_valid,
            confidence_score=confidence_score,
            validation_details=validation_details,
            warnings=warnings,
            errors=errors
        )


class MetadataValidator:
    """Main validator that orchestrates all validation components."""
    
    def __init__(self):
        self.cross_ref_validator = CrossReferenceValidator()
        self.confidence_scorer = ConfidenceScorer()
        self.hallucination_guard = HallucinationGuard()
    
    def validate_external_identifier_chain(self, chain: Dict[str, Any]) -> ValidationResult:
        """Validate a complete external identifier chain."""
        
        entity_id = chain.get("entity_id")
        external_ids = chain.get("external_ids", {})
        target_databases = chain.get("target_databases", [])
        
        validation_details = {
            "entity_id": entity_id,
            "external_ids": external_ids,
            "target_databases": target_databases
        }
        
        warnings = []
        errors = []
        
        # Validate external identifier formats
        identifier_validation = self.hallucination_guard.validate_identifier_suggestions(external_ids)
        
        if identifier_validation.invalid_identifiers:
            errors.extend(identifier_validation.format_issues)
        
        warnings.extend([f"Format issue: {issue}" for issue in identifier_validation.format_issues])
        
        # Validate cross-reference consistency
        if len(external_ids) > 1:
            cross_ref_result = self.cross_ref_validator.validate_multi_source_consistency(external_ids)
            validation_details["cross_reference_validation"] = cross_ref_result.validation_details
            warnings.extend(cross_ref_result.warnings)
            errors.extend(cross_ref_result.errors)
            confidence_score = cross_ref_result.confidence_score
        else:
            confidence_score = 0.8  # Single source has decent confidence
        
        # Validate database accessibility
        db_validation = self.hallucination_guard.filter_accessible_databases(target_databases)
        validation_details["database_validation"] = db_validation.__dict__
        warnings.extend(db_validation.warnings)
        
        # Adjust confidence based on database accessibility
        accessible_ratio = len(db_validation.validated_databases) / len(target_databases) if target_databases else 1.0
        confidence_score *= accessible_ratio
        
        is_valid = len(errors) == 0 and confidence_score >= 0.5
        
        return ValidationResult(
            is_valid=is_valid,
            confidence_score=confidence_score,
            validation_details=validation_details,
            warnings=warnings,
            errors=errors
        )
    
    def validate_research_pathway(self, pathway: Dict[str, Any]) -> ValidationResult:
        """Validate a suggested research pathway."""
        return self.hallucination_guard.validate_research_pathway(pathway)
    
    def validate_complete_metadata(self, validation_request: Dict[str, Any]) -> ValidationResult:
        """Validate complete metadata including external IDs, databases, and workflows."""
        
        entity_id = validation_request.get("entity_id")
        external_ids = validation_request.get("discovered_external_ids", {})
        suggested_databases = validation_request.get("suggested_databases", [])
        suggested_workflow = validation_request.get("suggested_workflow", [])
        
        # If no data to validate, return low confidence
        if not external_ids and not suggested_databases and not suggested_workflow:
            return ValidationResult(
                is_valid=False,
                confidence_score=0.0,
                validation_details={"entity_id": entity_id},
                warnings=["No metadata to validate"],
                errors=["Entity has no discoverable external identifiers or pathways"]
            )
        
        # Validate external identifier chain
        chain_validation = self.validate_external_identifier_chain({
            "entity_id": entity_id,
            "external_ids": external_ids,
            "target_databases": suggested_databases
        })
        
        # Validate suggested workflow
        pathway_validation = self.validate_research_pathway({
            "entity_id": entity_id,
            "steps": suggested_workflow
        })
        
        # Combine results
        overall_confidence = (chain_validation.confidence_score + pathway_validation.confidence_score) / 2
        overall_valid = chain_validation.is_valid and pathway_validation.is_valid
        
        combined_warnings = chain_validation.warnings + pathway_validation.warnings
        combined_errors = chain_validation.errors + pathway_validation.errors
        
        validation_details = {
            "entity_id": entity_id,
            "chain_validation": chain_validation.validation_details,
            "pathway_validation": pathway_validation.validation_details,
            "overall_confidence": overall_confidence
        }
        
        return ValidationResult(
            is_valid=overall_valid,
            confidence_score=overall_confidence,
            validation_details=validation_details,
            warnings=combined_warnings,
            errors=combined_errors
        )


# Global instance for use across tools
metadata_validator = MetadataValidator()