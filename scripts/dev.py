#!/usr/bin/env python3
"""Development helper script for fast.ai style development."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
import click


def run_cmd(cmd: str, check: bool = True) -> subprocess.CompletedProcess:
    """Run shell command with proper error handling."""
    print(f"🔧 Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=False)
    if check and result.returncode != 0:
        print(f"❌ Command failed with code {result.returncode}")
        sys.exit(result.returncode)
    return result


@click.group()
def cli():
    """Development tools for CogitareLink."""
    pass


@cli.command()
def setup():
    """Set up development environment (fast.ai style)."""
    print("🚀 Setting up CogitareLink development environment...")
    
    # Install in development mode
    run_cmd("uv pip install -e '.[dev]'")
    
    # Verify installation
    run_cmd("python -c 'import cogitarelink; print(f\"✅ CogitareLink {cogitarelink.__version__} installed\")'")
    
    print("✅ Development environment ready!")
    print("\n📝 Next steps:")
    print("  - Run tests: python scripts/dev.py test")
    print("  - Format code: python scripts/dev.py format")
    print("  - Interactive development: python scripts/dev.py iterate")


@cli.command()
def test():
    """Run tests with fast feedback."""
    print("🧪 Running tests...")
    
    # Run unit tests first (fast feedback)
    run_cmd("pytest tests/unit -v")
    
    # Then integration tests
    run_cmd("pytest tests/integration -v")
    
    print("✅ All tests passed!")


@cli.command()
@click.option('--module', '-m', help='Specific module to test')
def test_one(module: str = None):
    """Run tests for one module (fast.ai iteration style)."""
    if module:
        print(f"🧪 Testing {module}...")
        run_cmd(f"pytest tests/unit/{module} -v")
    else:
        print("❌ Please specify a module with -m")


@cli.command()
def format():
    """Format code with black and ruff."""
    print("🎨 Formatting code...")
    run_cmd("black cogitarelink/ tests/ scripts/")
    run_cmd("ruff check cogitarelink/ tests/ scripts/ --fix")
    print("✅ Code formatted!")


@cli.command()
def check():
    """Run all quality checks."""
    print("🔍 Running quality checks...")
    
    # Type checking
    run_cmd("mypy cogitarelink/")
    
    # Linting
    run_cmd("ruff check cogitarelink/ tests/")
    
    # Format check
    run_cmd("black --check cogitarelink/ tests/")
    
    print("✅ All checks passed!")


@cli.command()
def iterate():
    """Interactive development mode (fast.ai style)."""
    print("🔄 Starting interactive development...")
    print("📝 This will:")
    print("  1. Install package in development mode")
    print("  2. Run tests")
    print("  3. Make CLI tools available for testing")
    
    # Development installation
    run_cmd("uv pip install -e '.[dev]'")
    
    # Quick test
    run_cmd("pytest tests/unit -x")  # Stop on first failure
    
    print("\n✅ Ready for interactive development!")
    print("\n🛠️  Available CLI tools:")
    print("  - cl_discover (once implemented)")
    print("  - cl_sparql (once implemented)")
    print("  - etc.")
    
    print("\n📋 Development workflow:")
    print("  1. Edit code")
    print("  2. Run: python scripts/dev.py test-one -m core")
    print("  3. Test CLI: cl_discover 'test query'")
    print("  4. Iterate!")


@cli.command()
def clean():
    """Clean build artifacts."""
    print("🧹 Cleaning build artifacts...")
    
    patterns = [
        "**/__pycache__",
        "**/*.pyc",
        "**/*.pyo", 
        "dist/",
        "build/",
        "*.egg-info/",
        ".pytest_cache/",
        ".coverage",
        "htmlcov/",
        ".mypy_cache/",
        ".ruff_cache/"
    ]
    
    for pattern in patterns:
        run_cmd(f"find . -name '{pattern}' -exec rm -rf {{}} + 2>/dev/null || true", check=False)
    
    print("✅ Cleaned!")


if __name__ == "__main__":
    cli()