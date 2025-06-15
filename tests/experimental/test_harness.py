#!/usr/bin/env python3
"""
Jeremy Howard Style Experimental Test Harness for CogitareLink CLI Tools

This harness enables rapid experimentation with real biological data to understand
patterns and incrementally improve tool design.

Philosophy:
1. Start with real data, not toy examples
2. Print intermediate results to understand structure
3. Measure everything (time, memory, output size)
4. Refactor only after understanding patterns
"""

import json
import subprocess
import time
import sys
import os
import shlex
from typing import Dict, Any, List, Optional
from pprint import pprint
from pathlib import Path
import psutil

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class CLIExperiment:
    """Base class for CLI tool experimentation"""
    
    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.process = psutil.Process()
        self.results = []
        
    def run_cli(self, command: str) -> Dict[str, Any]:
        """Run a CogitareLink CLI command and capture output"""
        start_time = time.time()
        start_mem = self.process.memory_info().rss / 1024 / 1024  # MB
        
        if self.verbose:
            print(f"\n🚀 Running: {command}")
            
        try:
            # Use shlex to properly handle quoted arguments
            result = subprocess.run(
                shlex.split(command), 
                capture_output=True, 
                text=True,
                check=True
            )
            
            # Try to parse as JSON
            try:
                output = json.loads(result.stdout)
            except json.JSONDecodeError:
                output = {"raw": result.stdout}
                
            elapsed = time.time() - start_time
            end_mem = self.process.memory_info().rss / 1024 / 1024
            
            execution = {
                "command": command,
                "output": output,
                "elapsed_time": elapsed,
                "memory_delta": end_mem - start_mem,
                "stdout_size": len(result.stdout),
                "success": True
            }
            
            if self.verbose:
                print(f"✅ Success in {elapsed:.2f}s (Δmem: {execution['memory_delta']:.1f}MB)")
                print(f"📏 Output size: {len(result.stdout):,} bytes")
                
        except subprocess.CalledProcessError as e:
            execution = {
                "command": command,
                "error": e.stderr,
                "returncode": e.returncode,
                "success": False
            }
            if self.verbose:
                print(f"❌ Failed: {e}")
                
        self.results.append(execution)
        return execution
        
    def run_jq(self, data: Dict[str, Any], filter: str) -> Any:
        """Apply jq filter to data"""
        if self.verbose:
            print(f"\n🔍 jq filter: {filter}")
            
        # Handle the case where filter is wrapped in $()
        if filter.startswith('$(') and filter.endswith(')'):
            # Extract the command from $(...) 
            inner_cmd = filter[2:-1]
            # Run the command to get the actual filter
            try:
                result = subprocess.run(inner_cmd, shell=True, capture_output=True, text=True, check=True)
                filter = result.stdout.strip().strip('"')
            except subprocess.CalledProcessError as e:
                if self.verbose:
                    print(f"❌ Failed to resolve filter command: {e}")
                return None
            
        # Use subprocess to run actual jq for accuracy
        proc = subprocess.Popen(
            ["jq", "-r", filter],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        stdout, stderr = proc.communicate(json.dumps(data))
        
        if proc.returncode != 0:
            if self.verbose:
                print(f"❌ jq error: {stderr}")
            return None
            
        # Try to parse result as JSON, otherwise return as string
        try:
            result = json.loads(stdout.strip())
        except:
            result = stdout.strip()
            
        if self.verbose:
            print(f"➡️  Result: {result}")
            
        return result
    
    def run_cli_with_input(self, command: str, input_data: str) -> Dict[str, Any]:
        """Run CLI command with stdin input and return structured result"""
        start_time = time.time()
        start_mem = self.process.memory_info().rss / 1024 / 1024  # MB
        
        if self.verbose:
            print(f"\n🚀 Running with input: {command}")
            print(f"📥 Input: {input_data[:100]}..." if len(input_data) > 100 else f"📥 Input: {input_data}")
            
        try:
            # Run command with input via stdin, handle quotes properly
            process = subprocess.run(
                shlex.split(command), 
                input=input_data,
                capture_output=True, 
                text=True,
                timeout=30
            )
            
            # Try to parse as JSON
            try:
                output = json.loads(process.stdout)
            except json.JSONDecodeError:
                output = {"raw": process.stdout}
                
            elapsed = time.time() - start_time
            end_mem = self.process.memory_info().rss / 1024 / 1024
            
            if process.returncode == 0:
                execution = {
                    "command": command,
                    "output": output,
                    "elapsed_time": elapsed,
                    "memory_delta": end_mem - start_mem,
                    "stdout_size": len(process.stdout),
                    "success": True
                }
                
                if self.verbose:
                    print(f"✅ Success in {elapsed:.2f}s (Δmem: {execution['memory_delta']:.1f}MB)")
                    print(f"📏 Output size: {len(process.stdout):,} bytes")
            else:
                execution = {
                    "command": command,
                    "error": process.stderr,
                    "returncode": process.returncode,
                    "elapsed_time": elapsed,
                    "success": False
                }
                if self.verbose:
                    print(f"❌ Failed: {process.stderr}")
                    
        except subprocess.TimeoutExpired:
            execution = {
                "command": command,
                "error": "Command timed out",
                "success": False
            }
            if self.verbose:
                print("⏰ TIMEOUT (30s)")
        except Exception as e:
            execution = {
                "command": command,
                "error": str(e),
                "success": False
            }
            if self.verbose:
                print(f"💥 EXCEPTION: {str(e)}")
                
        self.results.append(execution)
        return execution
        
    def profile_pipeline(self, name: str, pipeline: List[str]):
        """Profile a complete pipeline of commands"""
        print(f"\n{'='*60}")
        print(f"📊 Pipeline: {name}")
        print(f"{'='*60}")
        
        pipeline_start = time.time()
        last_output = None
        
        for i, command in enumerate(pipeline):
            # Handle pipe syntax
            if "|" in command and last_output:
                # This is a jq filter on previous output
                filter = command.split("|", 1)[1].strip()
                if filter.startswith("jq"):
                    filter = filter[2:].strip().strip("'\"")
                last_output = self.run_jq(last_output.get("output", {}), filter)
            else:
                result = self.run_cli(command)
                if result["success"]:
                    last_output = result
                    
        total_time = time.time() - pipeline_start
        print(f"\n⏱️  Total pipeline time: {total_time:.2f}s")
        return self.results
        
    def analyze_json_structure(self, data: Dict[str, Any], name: str = ""):
        """Analyze JSON structure for jq navigability"""
        print(f"\n📐 Structure Analysis: {name}")
        print(f"{'='*40}")
        
        def analyze_node(obj, path=".", depth=0):
            indent = "  " * depth
            
            if isinstance(obj, dict):
                print(f"{indent}{path} (object with {len(obj)} keys)")
                if depth < 3:  # Limit depth
                    for key in sorted(obj.keys())[:5]:  # Show first 5 keys
                        analyze_node(obj[key], f"{path}.{key}", depth + 1)
                    if len(obj) > 5:
                        print(f"{indent}  ... and {len(obj) - 5} more keys")
                        
            elif isinstance(obj, list):
                print(f"{indent}{path} (array with {len(obj)} items)")
                if len(obj) > 0 and depth < 3:
                    analyze_node(obj[0], f"{path}[0]", depth + 1)
                    
            else:
                print(f"{indent}{path} = {repr(obj)[:50]}")
                
        analyze_node(data)
        
    def test_jq_patterns(self, data: Dict[str, Any], patterns: Dict[str, str]):
        """Test common jq patterns on data"""
        print(f"\n🧪 Testing jq patterns:")
        print(f"{'='*40}")
        
        for name, pattern in patterns.items():
            print(f"\n{name}:")
            result = self.run_jq(data, pattern)
            if result is not None:
                print(f"  ✓ Pattern works")
            else:
                print(f"  ✗ Pattern failed")
                
    def summarize_results(self):
        """Summarize all experimental results"""
        print(f"\n{'='*60}")
        print(f"📈 Experiment Summary")
        print(f"{'='*60}")
        
        total_time = sum(r.get("elapsed_time", 0) for r in self.results if r.get("success"))
        total_mem = sum(r.get("memory_delta", 0) for r in self.results if r.get("success"))
        successful = sum(1 for r in self.results if r.get("success"))
        failed = sum(1 for r in self.results if not r.get("success"))
        
        print(f"✅ Successful commands: {successful}")
        print(f"❌ Failed commands: {failed}")
        print(f"⏱️  Total execution time: {total_time:.2f}s")
        print(f"💾 Total memory delta: {total_mem:.1f}MB")
        
        # Find slowest operations
        slow_ops = sorted([r for r in self.results if r.get("elapsed_time")], 
                         key=lambda x: x["elapsed_time"], reverse=True)[:3]
        
        if slow_ops:
            print(f"\n🐌 Slowest operations:")
            for op in slow_ops:
                print(f"  - {op['command']}: {op['elapsed_time']:.2f}s")


# Utility functions for common patterns
def explore_entity(entity_id: str, experiment: CLIExperiment):
    """Explore a single entity through multiple tools"""
    print(f"\n🔬 Exploring entity: {entity_id}")
    
    # Basic discovery
    discover = experiment.run_cli(f"cl_discover {entity_id}")
    if discover["success"]:
        experiment.analyze_json_structure(discover["output"], f"cl_discover {entity_id}")
        
        # Test jq patterns
        patterns = {
            "Extract ID": '.data[0]["@id"]',
            "Get name": '.data[0].name',
            "List identifiers": '.data[0].identifiers | keys',
            "Count results": '.count',
            "Get all UniProt IDs": '.data[].identifiers.uniprot'
        }
        experiment.test_jq_patterns(discover["output"], patterns)
        
    return discover


def compare_formats(commands: List[str], experiment: CLIExperiment):
    """Compare output formats of different commands"""
    print(f"\n🔄 Comparing output formats")
    
    outputs = {}
    for cmd in commands:
        result = experiment.run_cli(cmd)
        if result["success"]:
            outputs[cmd] = result["output"]
            
    # Compare structures
    for cmd, output in outputs.items():
        print(f"\n{cmd}:")
        print(f"  Top-level keys: {sorted(output.keys())}")
        if "data" in output:
            print(f"  Data type: {type(output['data'])}")
            if isinstance(output["data"], list) and len(output["data"]) > 0:
                print(f"  First item keys: {sorted(output['data'][0].keys())}")


if __name__ == "__main__":
    # Example usage
    exp = CLIExperiment(verbose=True)
    
    # Test with real biological entity
    explore_entity("insulin", exp)
    
    # Test pipeline
    pipeline = [
        "cl_discover insulin",
        "| jq '.data[0].identifiers.uniprot'",
        # More pipeline steps will be added as we develop
    ]
    
    exp.profile_pipeline("Insulin Discovery Pipeline", pipeline)
    exp.summarize_results()