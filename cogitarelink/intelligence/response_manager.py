"""Response truncation and management based on wikidata-mcp patterns."""

from __future__ import annotations

import json
from typing import Any, Dict, List, Set, Tuple, Optional
from enum import Enum
from dataclasses import dataclass

from ..core.debug import get_logger

log = get_logger("response_manager")

class ResponseLevel(str, Enum):
    """Response detail levels for progressive disclosure."""
    SUMMARY = "summary"      # ~7% of full response (essential only)
    DETAILED = "detailed"    # ~25% of full response (essential + high priority)
    FULL = "full"           # 100% of full response

@dataclass
class TruncationMetadata:
    """Metadata about response truncation for agents."""
    original_size: int
    truncated_size: int
    reduction_ratio: float
    level: ResponseLevel
    preserved_fields: int
    total_fields: int
    
    def as_dict(self) -> Dict[str, Any]:
        return {
            "original_size": self.original_size,
            "truncated_size": self.truncated_size,
            "reduction_ratio": self.reduction_ratio,
            "level": self.level.value,
            "preserved_fields": self.preserved_fields,
            "total_fields": self.total_fields,
            "reduction_percentage": f"{(1 - self.reduction_ratio) * 100:.1f}%"
        }

@dataclass 
class PaginationMetadata:
    """Metadata about pagination for Claude Code navigation."""
    total_results: int
    current_page: int
    page_size: int
    total_pages: int
    has_next_page: bool
    has_previous_page: bool
    
    def as_dict(self) -> Dict[str, Any]:
        return {
            "total_results": self.total_results,
            "current_page": self.current_page, 
            "page_size": self.page_size,
            "total_pages": self.total_pages,
            "has_next_page": self.has_next_page,
            "has_previous_page": self.has_previous_page,
            "showing_results": f"{(self.current_page - 1) * self.page_size + 1}-{min(self.current_page * self.page_size, self.total_results)}"
        }

class ResponseManager:
    """
    Biological-aware response truncation and management.
    
    Based on wikidata-mcp's 97% size reduction while maintaining 100% agent readability.
    """
    
    # Field priority classification for semantic web / biological data
    ESSENTIAL_FIELDS: Set[str] = {
        "success", "entity_id", "@id", "name", "identifier", 
        "uniprot_id", "protein_name", "resolved_url", "@type",
        "error", "message",  # Always preserve error information
        "entities", "query", "total_found", "result_count",  # Core search/query results
        "sparql_results", "columns", "endpoint"  # SPARQL results
    }
    
    HIGH_PRIORITY_FIELDS: Set[str] = {
        "biological_properties", "uniprot_data", "molecular_function",
        "hasSequence", "Protein", "Gene", "data", "metadata",
        "context_id", "vocab", "content", "signature", "reasoning_hints",
        "entity_type", "domain_type", "confidence_score", "property_count",
        "vocab_count", "has_signature", "entity", "domain_context",
        "cross_references", "claims_count", "variables", "bindings",  # Important result data
        # SPARQL result field names (preserve individual binding keys)
        "item", "itemLabel", "protein", "proteinLabel", "gene", "geneLabel", 
        "pathway", "pathwayLabel", "compound", "compoundLabel", "value", "type",
        "xml:lang", "datatype"  # Common SPARQL result binding fields
    }
    
    MEDIUM_PRIORITY_FIELDS: Set[str] = {
        "suggestions", "reasoning_context", "research_workflows",
        "next_tools", "domain_suggestions", "workflow_guidance",
        "cross_domain_opportunities", "discovery_strategy", "confidence_score",
        "reasoning_patterns", "claude_guidance", "next_actions", "reasoning_hints"
    }
    
    LOW_PRIORITY_FIELDS: Set[str] = {
        "execution_time_ms", "debug_info", "cache_metadata",
        "performance_stats", "technical_details", "internal_state"
    }
    
    def __init__(self):
        self.token_targets = {
            ResponseLevel.SUMMARY: (500, 1000),    # 500-1000 tokens
            ResponseLevel.DETAILED: (1500, 3000),  # 1500-3000 tokens  
            ResponseLevel.FULL: (None, None)       # No limit
        }
        self.default_page_size = 25  # Claude Code friendly page size
    
    def estimate_tokens(self, data: Any) -> int:
        """Estimate token count for response data."""
        if isinstance(data, str):
            # Rough approximation: 1 token ≈ 4 characters
            return len(data) // 4
        elif isinstance(data, dict):
            json_str = json.dumps(data, separators=(',', ':'))
            return len(json_str) // 4
        elif isinstance(data, (list, tuple)):
            return sum(self.estimate_tokens(item) for item in data)
        else:
            return len(str(data)) // 4
    
    def truncate_response(
        self, 
        response: Dict[str, Any], 
        level: ResponseLevel = ResponseLevel.DETAILED,
        preserve_structure: bool = True
    ) -> Tuple[Dict[str, Any], TruncationMetadata]:
        """
        Truncate response while preserving agent readability.
        
        Args:
            response: Full response to truncate
            level: Detail level for truncation
            preserve_structure: Keep object structure intact
            
        Returns:
            Tuple of (truncated_response, truncation_metadata)
        """
        original_size = self.estimate_tokens(response)
        
        if level == ResponseLevel.FULL:
            # No truncation needed
            metadata = TruncationMetadata(
                original_size=original_size,
                truncated_size=original_size,
                reduction_ratio=1.0,
                level=level,
                preserved_fields=self._count_fields(response),
                total_fields=self._count_fields(response)
            )
            return response, metadata
        
        # Apply field-priority based truncation
        truncated = self._truncate_by_priority(response, level, preserve_structure)
        truncated_size = self.estimate_tokens(truncated)
        
        # Calculate metadata
        metadata = TruncationMetadata(
            original_size=original_size,
            truncated_size=truncated_size,
            reduction_ratio=truncated_size / original_size if original_size > 0 else 1.0,
            level=level,
            preserved_fields=self._count_fields(truncated),
            total_fields=self._count_fields(response)
        )
        
        # Add truncation metadata to response for agent awareness
        if preserve_structure and "metadata" in truncated:
            if isinstance(truncated["metadata"], dict):
                truncated["metadata"]["truncation"] = metadata.as_dict()
        
        reduction_pct = f"{(1 - metadata.reduction_ratio) * 100:.1f}%"
        log.debug(f"Truncated response: {reduction_pct} reduction "
                 f"({original_size} → {truncated_size} tokens)")
        
        return truncated, metadata
    
    def _truncate_by_priority(
        self, 
        data: Dict[str, Any], 
        level: ResponseLevel,
        preserve_structure: bool
    ) -> Dict[str, Any]:
        """Apply priority-based field truncation."""
        
        if level == ResponseLevel.SUMMARY:
            # Summary: Only essential fields
            return self._filter_fields(data, self.ESSENTIAL_FIELDS, preserve_structure, "")
        
        elif level == ResponseLevel.DETAILED:
            # Detailed: Essential + high priority + medium priority fields (preserve most data)
            allowed_fields = self.ESSENTIAL_FIELDS | self.HIGH_PRIORITY_FIELDS | self.MEDIUM_PRIORITY_FIELDS
            # For detailed level, only filter out low priority fields to preserve agent readability
            filtered = self._filter_fields(data, allowed_fields, preserve_structure, "")
            # If filtering removed too much, return more data
            if not filtered or not filtered.get("data"):
                return data  # Return original if filtering broke essential structure
            return filtered
        
        else:
            return data
    
    def _filter_fields(
        self, 
        data: Any, 
        allowed_fields: Set[str],
        preserve_structure: bool,
        context_path: str = ""
    ) -> Any:
        """Recursively filter fields based on priority."""
        
        if isinstance(data, dict):
            # SPARQL Results Preservation: Never filter SPARQL bindings content
            if any(sparql_key in context_path for sparql_key in ["sparql_results", "bindings"]):
                return data  # Preserve complete SPARQL binding structure
            
            filtered = {}
            
            for key, value in data.items():
                current_path = f"{context_path}.{key}" if context_path else key
                
                # Check if field should be preserved
                if (key in allowed_fields or 
                    any(allowed in key.lower() for allowed in allowed_fields) or
                    key.startswith('@')):  # Always preserve JSON-LD keywords
                    
                    # Recursively filter nested structures
                    if isinstance(value, (dict, list)):
                        filtered[key] = self._filter_fields(value, allowed_fields, preserve_structure, current_path)
                    else:
                        filtered[key] = value
                
                elif preserve_structure and key in ["data", "metadata", "suggestions"]:
                    # Keep structure but filter contents
                    if isinstance(value, dict):
                        nested = self._filter_fields(value, allowed_fields, preserve_structure, current_path)
                        if nested:  # Only include if not empty
                            filtered[key] = nested
            
            return filtered
        
        elif isinstance(data, list):
            # SPARQL Results Preservation: Don't filter SPARQL binding arrays
            if any(sparql_key in context_path for sparql_key in ["sparql_results", "bindings"]):
                return data  # Preserve complete SPARQL results array
            
            # For other lists, filter each item but preserve essential structure
            return [
                self._filter_fields(item, allowed_fields, preserve_structure, f"{context_path}[{i}]") 
                for i, item in enumerate(data[:10])  # Limit list length in truncated responses
            ]
        
        else:
            return data
    
    def _count_fields(self, data: Any) -> int:
        """Count total number of fields in nested structure."""
        if isinstance(data, dict):
            return len(data) + sum(self._count_fields(v) for v in data.values())
        elif isinstance(data, list):
            return sum(self._count_fields(item) for item in data)
        else:
            return 0
    
    def create_agent_summary(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Create agent-optimized summary response."""
        summary, metadata = self.truncate_response(response, ResponseLevel.SUMMARY)
        
        # Add agent guidance about the truncation
        if "suggestions" not in summary:
            summary["suggestions"] = {}
        
        summary["suggestions"]["response_info"] = {
            "level": "summary",
            "full_data_available": True,
            "expansion_hint": "Request 'detailed' or 'full' level for complete information",
            "reduction_achieved": metadata.reduction_percentage
        }
        
        return summary
    
    def enhance_for_agent_chain(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance response for agent tool chaining."""
        # Ensure context_id is available for chaining
        if "context_id" not in response and "metadata" in response:
            # Generate context handle if missing
            context_data = {
                "last_response": response.get("data", {}),
                "suggestions": response.get("suggestions", {}),
                "timestamp": response.get("metadata", {}).get("timestamp", "")
            }
            
            import hashlib
            context_str = str(sorted(context_data.items()))
            context_id = f"ctx_{hashlib.sha256(context_str.encode()).hexdigest()[:16]}"
            response["context_id"] = context_id
        
        # Add tool chaining hints
        if "suggestions" in response and "next_tools" in response["suggestions"]:
            response["suggestions"]["chaining_context"] = {
                "use_context_id": response.get("context_id"),
                "preserve_domain_context": True,
                "recommended_tool_sequence": response["suggestions"]["next_tools"][:3]
            }
        
        return response
    
    def paginate_results(
        self, 
        data: List[Any], 
        page: int = 1, 
        page_size: Optional[int] = None,
        claude_code_mode: bool = True
    ) -> Tuple[List[Any], PaginationMetadata]:
        """
        Paginate results for Claude Code navigation.
        
        Args:
            data: List of results to paginate
            page: Current page number (1-based)
            page_size: Results per page (defaults to 25 for Claude Code)
            claude_code_mode: If True, use Claude Code friendly defaults
            
        Returns:
            Tuple of (paginated_data, pagination_metadata)
        """
        if page_size is None:
            page_size = self.default_page_size if claude_code_mode else 10
        
        total_results = len(data)
        total_pages = max(1, (total_results + page_size - 1) // page_size)
        
        # Ensure page is within bounds
        page = max(1, min(page, total_pages))
        
        # Calculate pagination bounds
        start_idx = (page - 1) * page_size
        end_idx = min(start_idx + page_size, total_results)
        
        # Extract page data
        paginated_data = data[start_idx:end_idx]
        
        # Create pagination metadata
        pagination_metadata = PaginationMetadata(
            total_results=total_results,
            current_page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next_page=page < total_pages,
            has_previous_page=page > 1
        )
        
        return paginated_data, pagination_metadata
    
    def add_pagination_guidance(
        self, 
        response: Dict[str, Any], 
        pagination: PaginationMetadata,
        base_command: str
    ) -> Dict[str, Any]:
        """Add pagination navigation guidance to response."""
        
        # Add pagination metadata
        if "metadata" not in response:
            response["metadata"] = {}
        response["metadata"]["pagination"] = pagination.as_dict()
        
        # Add navigation suggestions
        if "suggestions" not in response:
            response["suggestions"] = {}
        
        nav_tools = []
        if pagination.has_previous_page:
            nav_tools.append(f"{base_command} --page {pagination.current_page - 1}")
        if pagination.has_next_page:
            nav_tools.append(f"{base_command} --page {pagination.current_page + 1}")
            
        if nav_tools:
            response["suggestions"]["pagination_navigation"] = nav_tools
        
        # Add Claude guidance for pagination
        if "claude_guidance" not in response:
            response["claude_guidance"] = {}
        
        guidance_messages = [
            f"Showing page {pagination.current_page} of {pagination.total_pages} ({pagination.as_dict()['showing_results']} of {pagination.total_results} results)"
        ]
        
        if pagination.has_next_page:
            guidance_messages.append(f"Use --page {pagination.current_page + 1} to see more results")
        if pagination.total_pages > 1:
            guidance_messages.append(f"Use --page-size to adjust results per page (current: {pagination.page_size})")
            
        response["claude_guidance"]["pagination_status"] = guidance_messages
        
        return response

# Global response manager instance
response_manager = ResponseManager()