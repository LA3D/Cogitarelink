"""Test cogitarelink entry point and session management.

Test the research agent integration with Claude Code through session management
and instruction enhancement.
"""

import json
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Any

import pytest


def run_cogitarelink_command(command: str, args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    """Run cogitarelink command and return result."""
    cmd = ["uv", "run", "cogitarelink", command] + args
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=30,
        cwd=cwd
    )


def parse_json_output(result: subprocess.CompletedProcess) -> Dict[str, Any]:
    """Parse JSON output from command (if any)."""
    if result.returncode != 0:
        pytest.fail(f"Command failed: {result.stderr}")
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        # Not JSON output, return empty dict
        return {}


class TestCogitareLinkEntry:
    """Test cogitarelink entry point commands."""
    
    def test_cogitarelink_help(self):
        """Test cogitarelink --help shows all commands."""
        result = run_cogitarelink_command("--help", [], Path.cwd())
        
        assert result.returncode == 0
        assert "CogitareLink: Transform Claude Code" in result.stdout
        assert "init" in result.stdout
        assert "status" in result.stdout
        assert "remind" in result.stdout
        assert "resume" in result.stdout
    
    def test_cogitarelink_init_biology(self):
        """Test initializing biology research session."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            result = run_cogitarelink_command(
                "init", 
                ["biology", "--goal", "Test biology research"],
                temp_path
            )
            
            assert result.returncode == 0
            assert "Research session initialized" in result.stdout
            assert "biology" in result.stdout
            assert "DISCOVERY-FIRST RESEARCH PATTERN" in result.stdout
            assert "BIOLOGY RESEARCH WORKFLOW PATTERNS" in result.stdout
            
            # Check session file was created
            session_file = temp_path / ".cogitarelink" / "session.json"
            assert session_file.exists()
            
            with open(session_file) as f:
                session_data = json.load(f)
                
            assert session_data["researchDomain"] == "biology"
            assert session_data["researchGoal"] == "Test biology research"
            assert "discovery_first" in session_data["activeInstructions"]
            assert "biology_workflow" in session_data["activeInstructions"]
    
    def test_cogitarelink_init_chemistry(self):
        """Test initializing chemistry research session."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            result = run_cogitarelink_command(
                "init",
                ["chemistry", "--goal", "Drug discovery workflow"],
                temp_path
            )
            
            assert result.returncode == 0
            assert "chemistry" in result.stdout
            assert "CHEMISTRY RESEARCH WORKFLOW PATTERNS" in result.stdout
            
            # Check session file
            session_file = temp_path / ".cogitarelink" / "session.json"
            with open(session_file) as f:
                session_data = json.load(f)
                
            assert session_data["researchDomain"] == "chemistry"
            assert "chemistry_workflow" in session_data["activeInstructions"]
    
    def test_cogitarelink_init_general(self):
        """Test initializing general research session."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            result = run_cogitarelink_command(
                "init",
                ["general"],
                temp_path
            )
            
            assert result.returncode == 0
            assert "general" in result.stdout
            
            # Check session file
            session_file = temp_path / ".cogitarelink" / "session.json"
            with open(session_file) as f:
                session_data = json.load(f)
                
            assert session_data["researchDomain"] == "general"
            assert "general_workflow" in session_data["activeInstructions"]


class TestSessionManagement:
    """Test research session state management."""
    
    def test_status_with_active_session(self):
        """Test status command with active research session."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Initialize session first
            init_result = run_cogitarelink_command(
                "init",
                ["biology", "--goal", "Test session status"],
                temp_path
            )
            assert init_result.returncode == 0
            
            # Check status
            status_result = run_cogitarelink_command("status", [], temp_path)
            assert status_result.returncode == 0
            
            assert "Research Session Status" in status_result.stdout
            assert "biology" in status_result.stdout
            assert "Test session status" in status_result.stdout
            assert "Tool Usage:" in status_result.stdout
            assert "cl_discover: 0" in status_result.stdout
            assert "Research Progress:" in status_result.stdout
            assert "Active Instructions:" in status_result.stdout
    
    def test_status_without_session(self):
        """Test status command without active session."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            result = run_cogitarelink_command("status", [], temp_path)
            assert result.returncode == 0
            assert "No active research session found" in result.stdout
            assert "Use 'cogitarelink init" in result.stdout
    
    def test_resume_with_session(self):
        """Test resume command with existing session."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Initialize session first
            init_result = run_cogitarelink_command(
                "init",
                ["biology", "--goal", "Resume test"],
                temp_path
            )
            assert init_result.returncode == 0
            
            # Resume session
            resume_result = run_cogitarelink_command("resume", [], temp_path)
            assert resume_result.returncode == 0
            
            assert "Resuming research session" in resume_result.stdout
            assert "biology" in resume_result.stdout
            assert "Resume test" in resume_result.stdout
            assert "RESEARCH CONTEXT RESTORED" in resume_result.stdout
    
    def test_resume_without_session(self):
        """Test resume command without existing session."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            result = run_cogitarelink_command("resume", [], temp_path)
            assert result.returncode == 0
            assert "No research session found to resume" in result.stdout


class TestInstructionIndex:
    """Test instruction pattern system."""
    
    def test_remind_list_patterns(self):
        """Test remind command without arguments lists patterns."""
        result = run_cogitarelink_command("remind", [], Path.cwd())
        
        assert result.returncode == 0
        assert "Available Instruction Patterns" in result.stdout
        assert "discovery_first" in result.stdout
        assert "biology_workflow" in result.stdout
        assert "chemistry_workflow" in result.stdout
    
    def test_remind_discovery_pattern(self):
        """Test remind with discovery_first pattern."""
        result = run_cogitarelink_command("remind", ["discovery_first"], Path.cwd())
        
        assert result.returncode == 0
        assert "DISCOVERY-FIRST RESEARCH PATTERN" in result.stdout
        assert "cl_discover" in result.stdout
        assert "Never query without schema understanding" in result.stdout
    
    def test_remind_biology_workflow(self):
        """Test remind with biology_workflow pattern."""
        result = run_cogitarelink_command("remind", ["biology_workflow"], Path.cwd())
        
        assert result.returncode == 0
        assert "BIOLOGY RESEARCH WORKFLOW PATTERNS" in result.stdout
        assert "Protein Research Chain-of-Thought" in result.stdout
        assert "spike protein" in result.stdout
    
    def test_remind_chemistry_workflow(self):
        """Test remind with chemistry_workflow pattern."""
        result = run_cogitarelink_command("remind", ["chemistry_workflow"], Path.cwd())
        
        assert result.returncode == 0
        assert "CHEMISTRY RESEARCH WORKFLOW PATTERNS" in result.stdout
        assert "Chemical Compound Analysis" in result.stdout
    
    def test_remind_with_hyphens(self):
        """Test remind with hyphenated pattern names."""
        result = run_cogitarelink_command("remind", ["biology-workflow"], Path.cwd())
        
        assert result.returncode == 0
        assert "BIOLOGY RESEARCH WORKFLOW PATTERNS" in result.stdout
    
    def test_remind_partial_match(self):
        """Test remind with partial pattern matching."""
        result = run_cogitarelink_command("remind", ["biology"], Path.cwd())
        
        assert result.returncode == 0
        assert "BIOLOGY RESEARCH WORKFLOW PATTERNS" in result.stdout
    
    def test_remind_multiple_matches(self):
        """Test remind with multiple partial matches."""
        result = run_cogitarelink_command("remind", ["workflow"], Path.cwd())
        
        assert result.returncode == 0
        assert "Multiple patterns match" in result.stdout
        assert "biology_workflow" in result.stdout
        assert "chemistry_workflow" in result.stdout
    
    def test_remind_invalid_pattern(self):
        """Test remind with invalid pattern name."""
        result = run_cogitarelink_command("remind", ["nonexistent"], Path.cwd())
        
        assert result.returncode == 0
        assert "Pattern 'nonexistent' not found" in result.stdout


class TestSessionPersistence:
    """Test session file persistence and format."""
    
    def test_session_file_structure(self):
        """Test session.json file has correct structure."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Initialize session
            result = run_cogitarelink_command(
                "init",
                ["biology", "--goal", "Structure test"],
                temp_path
            )
            assert result.returncode == 0
            
            # Check session file structure
            session_file = temp_path / ".cogitarelink" / "session.json"
            with open(session_file) as f:
                session_data = json.load(f)
            
            # Required fields
            required_fields = [
                "sessionId", "claudeSessionId", "originalCwd", "cwd",
                "researchDomain", "researchGoal", "createdAt", 
                "lastInteractionTime", "sessionCounter", "toolUsage",
                "discoveredEndpoints", "activeInstructions", "researchProgress"
            ]
            
            for field in required_fields:
                assert field in session_data, f"Missing required field: {field}"
            
            # Tool usage structure
            expected_tools = ["cl_discover", "cl_search", "cl_fetch", "cl_query", "cl_resolve"]
            for tool in expected_tools:
                assert tool in session_data["toolUsage"]
                assert isinstance(session_data["toolUsage"][tool], int)
            
            # Research progress structure
            progress_fields = ["entitiesDiscovered", "relationshipsFound", "workflowsCompleted"]
            for field in progress_fields:
                assert field in session_data["researchProgress"]
                assert isinstance(session_data["researchProgress"][field], int)
    
    def test_session_directory_creation(self):
        """Test .cogitarelink directory is created properly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Should not exist initially
            session_dir = temp_path / ".cogitarelink"
            assert not session_dir.exists()
            
            # Initialize session
            result = run_cogitarelink_command(
                "init",
                ["general"],
                temp_path
            )
            assert result.returncode == 0
            
            # Should exist now
            assert session_dir.exists()
            assert session_dir.is_dir()
            
            # Session file should exist
            session_file = session_dir / "session.json"
            assert session_file.exists()
            assert session_file.is_file()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])