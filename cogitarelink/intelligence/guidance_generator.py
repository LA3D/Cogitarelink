"""Agent guidance generation based on wikidata-mcp reasoning scaffolds."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass
from enum import Enum

from ..core.debug import get_logger

log = get_logger("guidance")

class DomainType(str, Enum):
    """Domain types for specialized guidance."""
    BIOLOGICAL = "biological"
    LIFE_SCIENCES = "life_sciences"
    CHEMISTRY = "chemistry"
    SEMANTIC_WEB = "semantic_web"
    KNOWLEDGE_GRAPH = "knowledge_graph"
    GEOSPATIAL = "geospatial" 
    GENERAL = "general"

@dataclass
class GuidanceContext:
    """Context for generating domain-specific guidance."""
    entity_type: str
    domain_type: DomainType
    properties: List[str]
    confidence_score: float
    previous_actions: List[str]
    available_tools: List[str]

class GuidanceGenerator:
    """
    Generate reasoning scaffolds and next-action suggestions for AI agents.
    
    Based on wikidata-mcp's biological-aware guidance patterns.
    """
    
    def __init__(self):
        # Domain-specific reasoning patterns
        self.biological_patterns = {
            "Protein": [
                "Structure → Function analysis pathway",
                "Sequence → Domains → Interactions workflow",
                "Protein → Pathway → Disease association",
                "Target identification → Drug discovery pipeline"
            ],
            "Gene": [
                "Gene → Expression → Phenotype pathway",
                "Sequence → Regulatory elements → Function",
                "Gene → Pathway → Disease mechanism",
                "Comparative genomics → Evolution → Function"
            ],
            "Compound": [
                "Structure → Activity relationship (SAR)",
                "Compound → Target → Pathway analysis",
                "Chemical space → Drug-likeness evaluation",
                "Compound → Bioactivity → Mechanism"
            ],
            "Disease": [
                "Symptoms → Mechanisms → Targets",
                "Disease → Genes → Pathways → Drugs",
                "Epidemiology → Risk factors → Prevention",
                "Disease progression → Biomarkers → Diagnosis"
            ]
        }
        
        self.semantic_web_patterns = {
            "Entity": [
                "Schema discovery → Property exploration → Relationship mapping",
                "Cross-reference resolution → Data integration",
                "Ontology alignment → Semantic reasoning",
                "Entity linking → Knowledge graph construction"
            ],
            "Property": [
                "Domain/Range analysis → Usage patterns",
                "Property hierarchy → Subsumption reasoning",
                "Cardinality constraints → Data validation",
                "Property alignment → Semantic matching"
            ],
            "Vocabulary": [
                "Namespace resolution → Context composition",
                "Version tracking → Compatibility analysis",
                "Collision detection → Resolution strategies",
                "Quality assessment → Metadata validation"
            ]
        }
        
        # Tool recommendation patterns
        self.tool_sequences = {
            "biological_discovery": [
                "cl_discover → cl_sparql → cl_materialize",
                "cl_discover → cl_resolve → cl_explain",
                "cl_sparql → cl_validate → cl_query_memory"
            ],
            "semantic_exploration": [
                "cl_discover → cl_validate → cl_explain",
                "cl_resolve → cl_sparql → cl_materialize",
                "cl_query_memory → cl_explain → cl_orchestrate"
            ],
            "research_workflow": [
                "cl_discover → cl_orchestrate → cl_explain",
                "cl_materialize → cl_validate → cl_query_memory"
            ]
        }
    
    def generate_guidance(
        self, 
        context: GuidanceContext,
        include_reasoning_patterns: bool = True,
        include_next_tools: bool = True,
        include_workflow_guidance: bool = True
    ) -> Dict[str, Any]:
        """Generate comprehensive agent guidance."""
        
        guidance = {
            "domain_context": self._detect_domain_context(context),
            "entity_analysis": self._analyze_entity(context),
        }
        
        if include_reasoning_patterns:
            guidance["reasoning_patterns"] = self._generate_reasoning_patterns(context)
        
        if include_next_tools:
            guidance["next_tools"] = self._recommend_next_tools(context)
        
        if include_workflow_guidance:
            guidance["workflow_guidance"] = self._generate_workflow_guidance(context)
        
        # Add cross-domain opportunities
        guidance["cross_domain_opportunities"] = self._identify_cross_domain_links(context)
        
        # Add confidence-based suggestions
        guidance["confidence_guidance"] = self._generate_confidence_guidance(context)
        
        return guidance
    
    def _detect_domain_context(self, context: GuidanceContext) -> Dict[str, Any]:
        """Detect and provide domain-specific context."""
        domain_info = {
            "primary_domain": context.domain_type.value,
            "entity_type": context.entity_type,
            "domain_confidence": context.confidence_score
        }
        
        # Add domain-specific metadata
        if context.domain_type == DomainType.BIOLOGICAL:
            domain_info.update({
                "biological_context": True,
                "expected_databases": ["UniProt", "ChEBI", "Ensembl", "KEGG"],
                "common_properties": ["hasSequence", "molecularFunction", "biologicalProcess"]
            })
        elif context.domain_type == DomainType.SEMANTIC_WEB:
            domain_info.update({
                "semantic_context": True,
                "expected_vocabularies": ["schema.org", "bioschemas", "FOAF", "Dublin Core"],
                "common_properties": ["@type", "@id", "name", "identifier"]
            })
        
        return domain_info
    
    def _analyze_entity(self, context: GuidanceContext) -> Dict[str, Any]:
        """Analyze entity characteristics for guidance."""
        analysis = {
            "entity_type": context.entity_type,
            "property_count": len(context.properties),
            "key_properties": context.properties[:5],  # First 5 properties
            "analysis_depth": "rich" if len(context.properties) > 5 else "basic"
        }
        
        # Add type-specific analysis
        if context.entity_type in ["Protein", "Gene", "Compound", "Disease"]:
            analysis["biological_entity"] = True
            analysis["research_potential"] = "high"
        
        return analysis
    
    def _generate_reasoning_patterns(self, context: GuidanceContext) -> List[str]:
        """Generate domain-specific reasoning patterns."""
        patterns = []
        
        # Get domain-specific patterns
        if context.domain_type == DomainType.BIOLOGICAL:
            entity_patterns = self.biological_patterns.get(context.entity_type, [])
            patterns.extend(entity_patterns)
            
            # Add general biological patterns
            patterns.extend([
                "Consider biological pathways and interactions",
                "Look for cross-references to other biological databases",
                "Examine temporal aspects of biological processes"
            ])
            
        elif context.domain_type == DomainType.SEMANTIC_WEB:
            entity_patterns = self.semantic_web_patterns.get(context.entity_type, 
                                                           self.semantic_web_patterns["Entity"])
            patterns.extend(entity_patterns)
        
        # Add confidence-based patterns
        if context.confidence_score < 0.5:
            patterns.append("Low confidence - validate findings with multiple sources")
        elif context.confidence_score > 0.8:
            patterns.append("High confidence - suitable for automated reasoning")
        
        return patterns[:6]  # Limit to most relevant patterns
    
    def _recommend_next_tools(self, context: GuidanceContext) -> List[str]:
        """Recommend next tools based on context and entity type."""
        recommendations = []
        
        # Base recommendations based on entity type and domain
        if context.domain_type == DomainType.BIOLOGICAL:
            if context.entity_type == "Protein":
                recommendations.extend([
                    "cl_sparql --query 'SELECT ?pathway WHERE { <entity> wdt:P2781 ?pathway }'",
                    "cl_resolve --identifier <uniprot_id>",
                    "cl_materialize --entity <entity> --depth 2"
                ])
            elif context.entity_type == "Gene":
                recommendations.extend([
                    "cl_sparql --query 'SELECT ?disease WHERE { ?disease wdt:P2293 <entity> }'",
                    "cl_discover --enhance <entity> --domains biology"
                ])
        
        # Add workflow-based recommendations
        if "discovery" not in context.previous_actions:
            recommendations.insert(0, "cl_discover --entity <entity>")
        
        if "validation" not in context.previous_actions and len(context.properties) > 3:
            recommendations.append("cl_validate --entity <entity>")
        
        # Add explanation if complex entity
        if len(context.properties) > 10:
            recommendations.append("cl_explain --entity <entity> --include-provenance")
        
        return recommendations[:5]  # Limit to top 5 recommendations
    
    def _generate_workflow_guidance(self, context: GuidanceContext) -> Dict[str, Any]:
        """Generate step-by-step workflow guidance."""
        
        workflow = {
            "suggested_sequence": [],
            "research_methodology": [],
            "validation_steps": []
        }
        
        if context.domain_type == DomainType.BIOLOGICAL:
            if context.entity_type == "Protein":
                workflow["suggested_sequence"] = [
                    "1. Discover protein metadata and cross-references",
                    "2. Query for protein-pathway associations", 
                    "3. Explore protein-protein interactions",
                    "4. Investigate disease associations",
                    "5. Validate findings with multiple databases"
                ]
                
                workflow["research_methodology"] = [
                    "Structure-based analysis: sequence → domains → 3D structure",
                    "Function-based analysis: biochemical → cellular → organismal",
                    "Evolution-based analysis: homology → phylogeny → conservation"
                ]
            
            elif context.entity_type == "Disease":
                workflow["suggested_sequence"] = [
                    "1. Discover disease-gene associations",
                    "2. Query for affected biological pathways",
                    "3. Explore disease mechanisms and symptoms",
                    "4. Investigate therapeutic targets",
                    "5. Cross-reference with drug databases"
                ]
        
        # Add validation steps
        workflow["validation_steps"] = [
            "Cross-reference findings with authoritative databases",
            "Verify temporal consistency of data",
            "Check for conflicting information",
            "Validate reasoning chain with provenance tracking"
        ]
        
        return workflow
    
    def _identify_cross_domain_links(self, context: GuidanceContext) -> List[str]:
        """Identify opportunities for cross-domain exploration."""
        opportunities = []
        
        if context.domain_type == DomainType.BIOLOGICAL:
            opportunities.extend([
                "Link to spatial databases for geographic distribution",
                "Connect to literature databases for research context",
                "Explore chemical databases for compound interactions"
            ])
        
        elif context.domain_type == DomainType.SEMANTIC_WEB:
            opportunities.extend([
                "Bridge to domain-specific vocabularies",
                "Connect to geographic or temporal ontologies",
                "Link to bibliographic metadata"
            ])
        
        # Add entity-specific opportunities
        if "identifier" in context.properties:
            opportunities.append("Use identifiers for cross-database linking")
        
        if any(p in context.properties for p in ["location", "coordinate", "place"]):
            opportunities.append("Explore geospatial relationships")
        
        return opportunities
    
    def _generate_confidence_guidance(self, context: GuidanceContext) -> Dict[str, Any]:
        """Generate guidance based on confidence levels."""
        
        guidance = {
            "confidence_level": context.confidence_score,
            "reliability_assessment": "high" if context.confidence_score > 0.8 else 
                                    "medium" if context.confidence_score > 0.5 else "low"
        }
        
        if context.confidence_score < 0.5:
            guidance["improvement_suggestions"] = [
                "Seek additional data sources for validation",
                "Use enhanced discovery methods",
                "Cross-reference with authoritative databases"
            ]
        elif context.confidence_score > 0.8:
            guidance["automation_opportunities"] = [
                "Suitable for automated reasoning workflows",
                "High confidence for downstream processing",
                "Reliable for knowledge graph construction"
            ]
        
        return guidance

# Global guidance generator instance
guidance_generator = GuidanceGenerator()