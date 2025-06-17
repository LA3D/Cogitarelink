"""Input validation pipeline following Claude Code patterns.

Provides fail-fast validation with LLM-friendly error messages.
Performance target: <1ms validation time for typical inputs.
"""

from typing import Any, Dict, Type, TypeVar, Union
from pydantic import BaseModel, ValidationError as PydanticValidationError
import time
from ..core.debug import get_logger

log = get_logger("validators")

T = TypeVar('T', bound=BaseModel)


class ValidationError(Exception):
    """Custom validation error with LLM-friendly formatting."""
    
    def __init__(self, message: str, field: str = None, input_value: Any = None):
        self.message = message
        self.field = field
        self.input_value = input_value
        super().__init__(message)


def validate_tool_input(schema_class: Type[T], input_data: Dict[str, Any]) -> T:
    """Validate tool input using Pydantic schema with performance tracking.
    
    Args:
        schema_class: Pydantic model class for validation
        input_data: Input data to validate
        
    Returns:
        Validated data instance
        
    Raises:
        ValidationError: If validation fails with LLM-friendly message
    """
    start_time = time.time()
    
    try:
        validated = schema_class(**input_data)
        validation_time = (time.time() - start_time) * 1000
        
        log.debug(f"Input validation completed in {validation_time:.2f}ms")
        
        # Performance warning if validation is slow
        if validation_time > 5.0:
            log.warning(f"Slow validation detected: {validation_time:.2f}ms for {schema_class.__name__}")
            
        return validated
        
    except PydanticValidationError as e:
        validation_time = (time.time() - start_time) * 1000
        log.debug(f"Input validation failed in {validation_time:.2f}ms")
        
        # Convert Pydantic errors to LLM-friendly format
        error_msg = format_pydantic_error(e)
        raise ValidationError(error_msg)
    except Exception as e:
        log.error(f"Unexpected validation error: {e}")
        raise ValidationError(f"Input validation failed: {str(e)}")


def format_pydantic_error(error: PydanticValidationError) -> str:
    """Format Pydantic validation errors for LLM consumption.
    
    Following Claude Code's pattern of clear, actionable error messages.
    """
    if len(error.errors()) == 1:
        # Single error - format concisely
        err = error.errors()[0]
        field = '.'.join(str(loc) for loc in err['loc'])
        msg = err['msg']
        
        return f"Invalid {field}: {msg}"
    
    # Multiple errors - format as list
    error_lines = []
    for err in error.errors():
        field = '.'.join(str(loc) for loc in err['loc'])
        msg = err['msg']
        error_lines.append(f"  - {field}: {msg}")
    
    return f"Input validation failed:\n" + "\n".join(error_lines)


def validate_endpoint_accessible(endpoint: str) -> bool:
    """Quick accessibility check for SPARQL endpoints.
    
    Returns:
        True if endpoint appears accessible, False otherwise
    """
    try:
        import httpx
        
        with httpx.Client(timeout=5.0) as client:
            # Try a simple HEAD request first
            response = client.head(endpoint)
            return response.status_code < 500
            
    except Exception as e:
        log.debug(f"Endpoint accessibility check failed for {endpoint}: {e}")
        return False


def validate_sparql_syntax(query: str) -> tuple[bool, str]:
    """Basic SPARQL syntax validation.
    
    Returns:
        (is_valid, error_message)
    """
    try:
        # Basic syntax checks
        query = query.strip()
        
        if not query:
            return False, "Query cannot be empty"
            
        # Check for balanced braces
        brace_count = query.count('{') - query.count('}')
        if brace_count != 0:
            return False, f"Unbalanced braces in query (missing {abs(brace_count)} {'closing' if brace_count > 0 else 'opening'} brace(s))"
            
        # Check for basic SPARQL keywords
        query_upper = query.upper()
        sparql_keywords = ['SELECT', 'ASK', 'DESCRIBE', 'CONSTRUCT', 'WHERE']
        
        if not any(keyword in query_upper for keyword in sparql_keywords):
            return False, "Query must contain valid SPARQL keywords (SELECT, ASK, DESCRIBE, etc.)"
            
        # Check for dangerous operations
        dangerous_ops = ['DELETE', 'INSERT', 'DROP', 'CREATE', 'CLEAR', 'LOAD']
        if any(op in query_upper for op in dangerous_ops):
            return False, f"Modification operations not allowed: {', '.join(op for op in dangerous_ops if op in query_upper)}"
            
        return True, ""
        
    except Exception as e:
        return False, f"SPARQL syntax validation failed: {str(e)}"


class PerformanceTracker:
    """Track validation performance following Claude Code patterns."""
    
    def __init__(self):
        self.validation_times = []
        self.error_counts = {}
        
    def record_validation(self, schema_name: str, duration_ms: float, success: bool):
        """Record validation performance metrics."""
        self.validation_times.append({
            'schema': schema_name,
            'duration_ms': duration_ms,
            'success': success,
            'timestamp': time.time()
        })
        
        # Keep only recent records (last 1000)
        if len(self.validation_times) > 1000:
            self.validation_times = self.validation_times[-1000:]
            
        # Track error patterns
        if not success:
            self.error_counts[schema_name] = self.error_counts.get(schema_name, 0) + 1
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get validation performance statistics."""
        if not self.validation_times:
            return {'no_data': True}
            
        successful_validations = [v for v in self.validation_times if v['success']]
        
        return {
            'total_validations': len(self.validation_times),
            'success_rate': len(successful_validations) / len(self.validation_times),
            'avg_duration_ms': sum(v['duration_ms'] for v in successful_validations) / len(successful_validations) if successful_validations else 0,
            'error_patterns': self.error_counts,
            'slow_validations': len([v for v in successful_validations if v['duration_ms'] > 5.0])
        }


# Global performance tracker
performance_tracker = PerformanceTracker()