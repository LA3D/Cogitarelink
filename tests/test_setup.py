"""Test that development setup works correctly."""

from __future__ import annotations

import pytest
from .conftest import assert_eq


def test_package_imports():
    """Test that package can be imported."""
    import cogitarelink
    
    # Should have version
    assert hasattr(cogitarelink, '__version__')
    assert_eq(cogitarelink.__version__, "0.1.0")


def test_fastcore_available():
    """Test that fastcore is available for fast.ai style testing."""
    from fastcore.test import test_eq as fc_test_eq
    
    # Should work
    fc_test_eq(1, 1)


def test_pytest_markers():
    """Test that pytest markers are working."""
    from tests.conftest import unit, integration, interactive, slow
    
    # Should be callable markers
    assert callable(unit)
    assert callable(integration)
    assert callable(interactive)
    assert callable(slow)


def test_development_dependencies():
    """Test that all development dependencies are available."""
    # Core dependencies
    import click
    import pydantic
    import httpx
    
    # Development dependencies
    import pytest
    import black  # type: ignore
    import mypy  # type: ignore
    
    # Testing utilities
    from fastcore.test import test_eq
    
    # Should not raise ImportError
    assert True


@pytest.mark.unit
def test_fast_ai_test_utilities():
    """Test fast.ai style test utilities."""
    from .conftest import assert_eq, assert_ne, assert_fail
    
    # assert_eq
    assert_eq(1, 1)
    assert_eq("hello", "hello")
    
    # assert_ne  
    assert_ne(1, 2)
    assert_ne("hello", "world")
    
    # assert_fail
    def failing_func():
        raise ValueError("test error")
    
    assert_fail(failing_func, contains="test error")


if __name__ == "__main__":
    # Fast.ai style: run tests directly
    test_package_imports()
    test_fastcore_available()
    test_pytest_markers()
    test_development_dependencies()
    test_fast_ai_test_utilities()
    print("✅ All setup tests passed!")