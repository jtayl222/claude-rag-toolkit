"""
Unit tests for the SessionManager class.
"""

import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch
from datetime import datetime

from utils.session_manager import SessionManager, SessionState


class TestSessionState:
    """Test cases for SessionState dataclass."""

    def test_session_state_creation(self):
        """Test SessionState creation with required fields."""
        session = SessionState(
            session_id="test-123",
            name="Test Session",
            start_time="2024-01-01T10:00:00"
        )
        
        assert session.session_id == "test-123"
        assert session.name == "Test Session"
        assert session.start_time == "2024-01-01T10:00:00"
        assert session.status == "active"
        assert session.end_time is None
        assert session.objectives == []
        assert session.progress_log == []
        assert session.blockers == []
        assert session.decisions == []

    def test_session_state_with_optional_fields(self):
        """Test SessionState creation with all fields."""
        session = SessionState(
            session_id="test-456",
            name="Full Session",
            start_time="2024-01-01T10:00:00",
            end_time="2024-01-01T11:00:00",
            status="completed",
            description="Test description",
            objectives=["Goal 1", "Goal 2"],
            initial_branch="main",
            initial_commit="abc123"
        )
        
        assert session.description == "Test description"
        assert session.objectives == ["Goal 1", "Goal 2"]
        assert session.initial_branch == "main"
        assert session.initial_commit == "abc123"


class TestSessionManager:
    """Test cases for SessionManager."""

    def test_init_creates_directories(self, temp_dir):
        """Test SessionManager initialization creates necessary directories."""
        manager = SessionManager(str(temp_dir))
        
        assert manager.project_root == temp_dir
        assert manager.sessions_dir.exists()
        assert manager.sessions_index.exists()
        
        # Check initial sessions index
        with open(manager.sessions_index) as f:
            sessions = json.load(f)
        assert sessions == []

    def test_init_with_existing_index(self, temp_dir):
        """Test SessionManager initialization with existing sessions index."""
        sessions_dir = temp_dir / "sessions"
        sessions_dir.mkdir()
        
        # Create existing index
        index_file = sessions_dir / "index.json"
        existing_sessions = [{"session_id": "existing-123", "name": "Existing"}]
        with open(index_file, 'w') as f:
            json.dump(existing_sessions, f)
        
        manager = SessionManager(str(temp_dir))
        sessions = manager._load_sessions_index()
        
        assert len(sessions) == 1
        assert sessions[0]["session_id"] == "existing-123"

    @patch('subprocess.run')
    def test_get_git_info_success(self, mock_run, temp_dir):
        """Test successful git information retrieval."""
        # Mock successful git commands
        mock_run.side_effect = [
            Mock(stdout="main\n", returncode=0),
            Mock(stdout="abc123def456\n", returncode=0)
        ]
        
        manager = SessionManager(str(temp_dir))
        git_info = manager._get_git_info()
        
        assert git_info["branch"] == "main"
        assert git_info["commit"] == "abc123def456"

    @patch('subprocess.run')
    def test_get_git_info_failure(self, mock_run, temp_dir):
        """Test git information retrieval when git fails."""
        # Mock git command failure
        from subprocess import CalledProcessError
        mock_run.side_effect = CalledProcessError(1, 'git')
        
        manager = SessionManager(str(temp_dir))
        git_info = manager._get_git_info()
        
        assert git_info["branch"] == "unknown"
        assert git_info["commit"] == "unknown"

    @patch('subprocess.run')
    def test_get_git_status(self, mock_run, temp_dir):
        """Test git status retrieval."""
        # Mock git status output
        mock_run.return_value = Mock(
            stdout="M  file1.py\n?? file2.py\nD  file3.py\n",
            returncode=0
        )
        
        manager = SessionManager(str(temp_dir))
        status = manager._get_git_status()
        
        assert status["clean"] is False
        assert "M  file1.py" in status["modified_files"]
        assert "?? file2.py" in status["modified_files"]
        assert "D  file3.py" in status["modified_files"]

    @patch('subprocess.run')
    def test_get_git_diff_stats(self, mock_run, temp_dir):
        """Test git diff statistics."""
        # Mock git diff output
        mock_run.return_value = Mock(
            stdout="10\t5\tfile1.py\n3\t2\tfile2.py\n",
            returncode=0
        )
        
        manager = SessionManager(str(temp_dir))
        stats = manager._get_git_diff_stats("abc123", "def456")
        
        assert stats["lines_added"] == 13  # 10 + 3
        assert stats["lines_removed"] == 7  # 5 + 2

    @patch('subprocess.run')
    @patch('uuid.uuid4')
    def test_start_session(self, mock_uuid, mock_run, temp_dir):
        """Test starting a new session."""
        # Mock UUID and git  
        mock_uuid.return_value = "test-session-id"
        mock_run.side_effect = [
            Mock(stdout="main\n", returncode=0),
            Mock(stdout="abc123\n", returncode=0)
        ]
        
        manager = SessionManager(str(temp_dir))
        
        with patch('utils.session_manager.datetime') as mock_datetime:
            mock_datetime.now.return_value.isoformat.return_value = "2024-01-01T10:00:00"
            
            session = manager.start_session(
                name="Test Session",
                description="Test description",
                objectives=["Goal 1", "Goal 2"]
            )
        
        assert session.name == "Test Session"
        assert session.description == "Test description"
        assert session.objectives == ["Goal 1", "Goal 2"]
        assert session.initial_branch == "main"
        assert session.initial_commit == "abc123"
        assert session.status == "active"
        
        # Check current session file
        with open(manager.current_session_file) as f:
            current_id = f.read().strip()
        assert current_id == "test-session-id"

    def test_get_current_session_none(self, temp_dir):
        """Test getting current session when none exists."""
        manager = SessionManager(str(temp_dir))
        current = manager.get_current_session()
        assert current is None

    @patch('subprocess.run')
    @patch('uuid.uuid4')
    def test_update_session(self, mock_uuid, mock_run, temp_dir):
        """Test updating current session with progress."""
        mock_uuid.return_value = "test-session-id"
        mock_run.side_effect = [
            Mock(stdout="main\n", returncode=0),
            Mock(stdout="abc123\n", returncode=0),
            Mock(stdout="M  file.py\n", returncode=0)  # For git status in update
        ]
        
        manager = SessionManager(str(temp_dir))
        
        # Start a session first
        with patch('utils.session_manager.datetime') as mock_datetime:
            mock_datetime.now.return_value.isoformat.return_value = "2024-01-01T10:00:00"
            manager.start_session("Test Session")
        
        # Update the session
        with patch('utils.session_manager.datetime') as mock_datetime:
            mock_datetime.now.return_value.isoformat.return_value = "2024-01-01T10:05:00"
            
            success = manager.update_session(
                notes="Made progress",
                blocker="Found an issue",
                decision="Decided to proceed"
            )
        
        assert success is True
        
        # Verify session was updated
        session = manager.get_current_session()
        assert len(session.progress_log) == 1
        assert session.progress_log[0]["notes"] == "Made progress"
        assert len(session.blockers) == 1
        assert session.blockers[0]["description"] == "Found an issue"
        assert len(session.decisions) == 1
        assert session.decisions[0]["description"] == "Decided to proceed"

    def test_update_session_no_active(self, temp_dir):
        """Test updating session when no active session exists."""
        manager = SessionManager(str(temp_dir))
        success = manager.update_session("No active session")
        assert success is False

    @patch('subprocess.run')
    @patch('uuid.uuid4')
    def test_end_session(self, mock_uuid, mock_run, temp_dir):
        """Test ending current session."""
        mock_uuid.return_value = "test-session-id"
        # Use a more flexible mock approach
        def mock_subprocess(*args, **kwargs):
            cmd = ' '.join(args[0]) if args and isinstance(args[0], list) else str(args)
            if '--abbrev-ref HEAD' in cmd:
                return Mock(stdout="main\n", returncode=0)
            elif 'rev-parse HEAD' in cmd and 'abc123' not in cmd:
                return Mock(stdout="def456\n", returncode=0)
            elif 'rev-parse HEAD' in cmd:
                return Mock(stdout="abc123\n", returncode=0)
            elif '--numstat' in cmd:
                return Mock(stdout="5\t3\tfile.py\n", returncode=0)
            else:
                return Mock(stdout="", returncode=0)
        
        mock_run.side_effect = mock_subprocess
        
        manager = SessionManager(str(temp_dir))
        
        # Start a session
        with patch('utils.session_manager.datetime') as mock_datetime:
            mock_datetime.now.return_value.isoformat.return_value = "2024-01-01T10:00:00"
            manager.start_session("Test Session")
        
        # End the session
        with patch('utils.session_manager.datetime') as mock_datetime:
            mock_datetime.now.return_value.isoformat.return_value = "2024-01-01T11:00:00"
            
            session = manager.end_session("Session completed")
        
        assert session.status == "completed"
        assert session.end_time == "2024-01-01T11:00:00"
        assert session.final_commit == "def456"
        assert session.lines_added == 5
        assert session.lines_removed == 3
        
        # Verify summary was added to progress log
        assert len(session.progress_log) == 1
        assert "SESSION SUMMARY: Session completed" in session.progress_log[0]["notes"]
        
        # Verify current session file is cleared
        assert not manager.current_session_file.exists()

    def test_end_session_none_active(self, temp_dir):
        """Test ending session when none is active."""
        manager = SessionManager(str(temp_dir))
        session = manager.end_session()
        assert session is None

    @patch('subprocess.run')
    @patch('uuid.uuid4')
    def test_pause_and_resume_session(self, mock_uuid, mock_run, temp_dir):
        """Test pausing and resuming sessions."""
        mock_uuid.return_value = "test-session-id"
        mock_run.side_effect = [
            Mock(stdout="main\n", returncode=0),
            Mock(stdout="abc123\n", returncode=0)
        ]
        
        manager = SessionManager(str(temp_dir))
        
        # Start session
        with patch('utils.session_manager.datetime') as mock_datetime:
            mock_datetime.now.return_value.isoformat.return_value = "2024-01-01T10:00:00"
            manager.start_session("Test Session")
        
        # Pause session
        with patch('utils.session_manager.datetime') as mock_datetime:
            mock_datetime.now.return_value.isoformat.return_value = "2024-01-01T10:30:00"
            success = manager.pause_session("Taking a break")
        
        assert success is True
        assert not manager.current_session_file.exists()
        
        # Resume session
        with patch('utils.session_manager.datetime') as mock_datetime:
            mock_datetime.now.return_value.isoformat.return_value = "2024-01-01T11:00:00"
            success = manager.resume_session("test-session-id")
        
        assert success is True
        assert manager.current_session_file.exists()
        
        session = manager.get_current_session()
        assert session.status == "active"
        assert len(session.progress_log) == 2  # Pause and resume entries

    def test_resume_nonexistent_session(self, temp_dir):
        """Test resuming a session that doesn't exist."""
        manager = SessionManager(str(temp_dir))
        success = manager.resume_session("nonexistent-id")
        assert success is False

    def test_list_sessions(self, temp_dir):
        """Test listing all sessions."""
        manager = SessionManager(str(temp_dir))
        
        # Add some sessions to the index
        sessions = [
            {"session_id": "id1", "name": "Session 1", "status": "completed"},
            {"session_id": "id2", "name": "Session 2", "status": "active"}
        ]
        manager._save_sessions_index(sessions)
        
        result = manager.list_sessions()
        assert len(result) == 2
        assert result[0]["name"] == "Session 1"
        assert result[1]["name"] == "Session 2"

    def test_generate_session_report(self, temp_dir):
        """Test generating session report."""
        manager = SessionManager(str(temp_dir))
        
        # Create a test session file
        session_data = {
            "session_id": "test-id",
            "name": "Test Session",
            "start_time": "2024-01-01T10:00:00",
            "end_time": "2024-01-01T11:00:00",
            "status": "completed",
            "description": "Test description",
            "objectives": ["Goal 1", "Goal 2"],
            "initial_branch": "main",
            "initial_commit": "abc123",
            "final_commit": "def456",
            "lines_added": 10,
            "lines_removed": 5,
            "progress_log": [
                {"timestamp": "2024-01-01T10:30:00", "notes": "Made progress"}
            ],
            "blockers": [],
            "decisions": [],
            "files_modified": []
        }
        
        session_file = manager.sessions_dir / "test-id.json"
        with open(session_file, 'w') as f:
            json.dump(session_data, f)
        
        report = manager.generate_session_report("test-id")
        
        assert "# Session Report: Test Session" in report
        assert "test-id" in report
        assert "completed" in report
        assert "Goal 1" in report
        assert "Made progress" in report

    def test_generate_report_nonexistent_session(self, temp_dir):
        """Test generating report for nonexistent session."""
        manager = SessionManager(str(temp_dir))
        report = manager.generate_session_report("nonexistent")
        assert report == "Session not found."

    def test_get_session_details(self, temp_dir):
        """Test getting detailed session information."""
        manager = SessionManager(str(temp_dir))
        
        # Create a test session file
        session_data = {
            "session_id": "test-id",
            "name": "Test Session",
            "start_time": "2024-01-01T10:00:00",
            "status": "active",
            "objectives": [],
            "progress_log": [],
            "blockers": [],
            "decisions": [],
            "files_modified": []
        }
        
        session_file = manager.sessions_dir / "test-id.json"
        with open(session_file, 'w') as f:
            json.dump(session_data, f)
        
        session = manager.get_session_details("test-id")
        
        assert session is not None
        assert session.name == "Test Session"
        assert session.session_id == "test-id"

    def test_get_session_details_nonexistent(self, temp_dir):
        """Test getting details for nonexistent session."""
        manager = SessionManager(str(temp_dir))
        session = manager.get_session_details("nonexistent")
        assert session is None