#!/usr/bin/env python3
"""
Session Management System for Claude RAG Toolkit
Tracks progress, decisions, and context across development sessions.
"""

import json
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import uuid


@dataclass
class SessionState:
    """Represents the current state of a development session."""
    session_id: str
    name: str
    start_time: str
    end_time: Optional[str] = None
    status: str = "active"  # active, paused, completed, cancelled
    description: str = ""
    
    # Git state
    initial_branch: str = ""
    initial_commit: str = ""
    final_commit: Optional[str] = None
    
    # Progress tracking
    objectives: List[str] = None
    progress_log: List[Dict[str, Any]] = None
    blockers: List[Dict[str, str]] = None
    decisions: List[Dict[str, str]] = None
    
    # Metrics
    files_modified: List[str] = None
    lines_added: int = 0
    lines_removed: int = 0
    
    def __post_init__(self):
        if self.objectives is None:
            self.objectives = []
        if self.progress_log is None:
            self.progress_log = []
        if self.blockers is None:
            self.blockers = []
        if self.decisions is None:
            self.decisions = []
        if self.files_modified is None:
            self.files_modified = []


class SessionManager:
    """Manages development sessions with Git integration."""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.sessions_dir = self.project_root / "sessions"
        self.current_session_file = self.sessions_dir / ".current_session"
        self.sessions_index = self.sessions_dir / "index.json"
        
        # Ensure sessions directory exists
        self.sessions_dir.mkdir(exist_ok=True)
        
        # Initialize sessions index if it doesn't exist
        if not self.sessions_index.exists():
            self._save_sessions_index([])
    
    def _get_git_info(self) -> Dict[str, str]:
        """Get current Git state information."""
        try:
            # Get current branch
            branch_result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True
            )
            branch = branch_result.stdout.strip()
            
            # Get current commit
            commit_result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True
            )
            commit = commit_result.stdout.strip()
            
            return {"branch": branch, "commit": commit}
            
        except (subprocess.CalledProcessError, FileNotFoundError):
            return {"branch": "unknown", "commit": "unknown"}
    
    def _get_git_status(self) -> Dict[str, Any]:
        """Get detailed Git status information."""
        try:
            # Get status
            status_result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True
            )
            
            # Parse status output
            modified_files = []
            for line in status_result.stdout.strip().split('\n'):
                if line:
                    status_code = line[:2]
                    filename = line[3:]
                    modified_files.append(f"{status_code} {filename}")
            
            return {
                "modified_files": modified_files,
                "clean": len(modified_files) == 0
            }
            
        except (subprocess.CalledProcessError, FileNotFoundError):
            return {"modified_files": [], "clean": True}
    
    def _get_git_diff_stats(self, from_commit: str, to_commit: str = "HEAD") -> Dict[str, int]:
        """Get diff statistics between commits."""
        try:
            diff_result = subprocess.run(
                ["git", "diff", "--numstat", f"{from_commit}..{to_commit}"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True
            )
            
            lines_added = 0
            lines_removed = 0
            
            for line in diff_result.stdout.strip().split('\n'):
                if line:
                    parts = line.split('\t')
                    if len(parts) >= 2 and parts[0] != '-' and parts[1] != '-':
                        lines_added += int(parts[0])
                        lines_removed += int(parts[1])
            
            return {"lines_added": lines_added, "lines_removed": lines_removed}
            
        except (subprocess.CalledProcessError, FileNotFoundError, ValueError):
            return {"lines_added": 0, "lines_removed": 0}
    
    def _load_sessions_index(self) -> List[Dict[str, Any]]:
        """Load the sessions index."""
        try:
            with open(self.sessions_index, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def _save_sessions_index(self, sessions: List[Dict[str, Any]]):
        """Save the sessions index."""
        with open(self.sessions_index, 'w') as f:
            json.dump(sessions, f, indent=2)
    
    def _save_session(self, session: SessionState):
        """Save a session to disk."""
        session_file = self.sessions_dir / f"{session.session_id}.json"
        with open(session_file, 'w') as f:
            json.dump(asdict(session), f, indent=2)
    
    def _load_session(self, session_id: str) -> Optional[SessionState]:
        """Load a session from disk."""
        session_file = self.sessions_dir / f"{session_id}.json"
        try:
            with open(session_file, 'r') as f:
                data = json.load(f)
                return SessionState(**data)
        except (FileNotFoundError, json.JSONDecodeError):
            return None
    
    def start_session(self, name: str, description: str = "", objectives: List[str] = None) -> SessionState:
        """Start a new development session."""
        # End any active session first
        current = self.get_current_session()
        if current and current.status == "active":
            self.pause_session("Starting new session")
        
        # Get Git state
        git_info = self._get_git_info()
        
        # Create new session
        session = SessionState(
            session_id=str(uuid.uuid4()),
            name=name,
            start_time=datetime.now().isoformat(),
            description=description,
            objectives=objectives or [],
            initial_branch=git_info["branch"],
            initial_commit=git_info["commit"]
        )
        
        # Save session
        self._save_session(session)
        
        # Update current session pointer
        with open(self.current_session_file, 'w') as f:
            f.write(session.session_id)
        
        # Update sessions index
        sessions = self._load_sessions_index()
        sessions.append({
            "session_id": session.session_id,
            "name": session.name,
            "start_time": session.start_time,
            "status": session.status
        })
        self._save_sessions_index(sessions)
        
        return session
    
    def get_current_session(self) -> Optional[SessionState]:
        """Get the currently active session."""
        try:
            with open(self.current_session_file, 'r') as f:
                session_id = f.read().strip()
            return self._load_session(session_id)
        except FileNotFoundError:
            return None
    
    def update_session(self, notes: str, blocker: str = None, decision: str = None) -> bool:
        """Update the current session with progress notes."""
        session = self.get_current_session()
        if not session or session.status != "active":
            return False
        
        # Add progress entry
        progress_entry = {
            "timestamp": datetime.now().isoformat(),
            "notes": notes
        }
        session.progress_log.append(progress_entry)
        
        # Add blocker if provided
        if blocker:
            blocker_entry = {
                "timestamp": datetime.now().isoformat(),
                "description": blocker,
                "status": "open"
            }
            session.blockers.append(blocker_entry)
        
        # Add decision if provided
        if decision:
            decision_entry = {
                "timestamp": datetime.now().isoformat(),
                "description": decision
            }
            session.decisions.append(decision_entry)
        
        # Update Git status
        git_status = self._get_git_status()
        session.files_modified = git_status["modified_files"]
        
        self._save_session(session)
        return True
    
    def end_session(self, summary: str = "") -> Optional[SessionState]:
        """End the current session."""
        session = self.get_current_session()
        if not session:
            return None
        
        # Update session state
        session.end_time = datetime.now().isoformat()
        session.status = "completed"
        
        # Get final Git state
        git_info = self._get_git_info()
        session.final_commit = git_info["commit"]
        
        # Calculate diff stats
        if session.initial_commit != "unknown" and session.final_commit != "unknown":
            diff_stats = self._get_git_diff_stats(session.initial_commit, session.final_commit)
            session.lines_added = diff_stats["lines_added"]
            session.lines_removed = diff_stats["lines_removed"]
        
        # Add final summary
        if summary:
            summary_entry = {
                "timestamp": datetime.now().isoformat(),
                "notes": f"SESSION SUMMARY: {summary}"
            }
            session.progress_log.append(summary_entry)
        
        # Save session
        self._save_session(session)
        
        # Update sessions index
        sessions = self._load_sessions_index()
        for i, s in enumerate(sessions):
            if s["session_id"] == session.session_id:
                sessions[i]["status"] = "completed"
                sessions[i]["end_time"] = session.end_time
                break
        self._save_sessions_index(sessions)
        
        # Clear current session
        if self.current_session_file.exists():
            self.current_session_file.unlink()
        
        return session
    
    def pause_session(self, reason: str = "") -> bool:
        """Pause the current session."""
        session = self.get_current_session()
        if not session or session.status != "active":
            return False
        
        session.status = "paused"
        
        # Add pause entry
        pause_entry = {
            "timestamp": datetime.now().isoformat(),
            "notes": f"SESSION PAUSED: {reason}" if reason else "SESSION PAUSED"
        }
        session.progress_log.append(pause_entry)
        
        self._save_session(session)
        
        # Update sessions index
        sessions = self._load_sessions_index()
        for i, s in enumerate(sessions):
            if s["session_id"] == session.session_id:
                sessions[i]["status"] = "paused"
                break
        self._save_sessions_index(sessions)
        
        # Clear current session
        if self.current_session_file.exists():
            self.current_session_file.unlink()
        
        return True
    
    def resume_session(self, session_id: str) -> bool:
        """Resume a paused session."""
        session = self._load_session(session_id)
        if not session or session.status != "paused":
            return False
        
        # End any active session first
        current = self.get_current_session()
        if current and current.status == "active":
            self.pause_session("Resuming different session")
        
        session.status = "active"
        
        # Add resume entry
        resume_entry = {
            "timestamp": datetime.now().isoformat(),
            "notes": "SESSION RESUMED"
        }
        session.progress_log.append(resume_entry)
        
        self._save_session(session)
        
        # Update current session pointer
        with open(self.current_session_file, 'w') as f:
            f.write(session.session_id)
        
        # Update sessions index
        sessions = self._load_sessions_index()
        for i, s in enumerate(sessions):
            if s["session_id"] == session.session_id:
                sessions[i]["status"] = "active"
                break
        self._save_sessions_index(sessions)
        
        return True
    
    def list_sessions(self) -> List[Dict[str, Any]]:
        """List all sessions."""
        return self._load_sessions_index()
    
    def get_session_details(self, session_id: str) -> Optional[SessionState]:
        """Get detailed information about a specific session."""
        return self._load_session(session_id)
    
    def generate_session_report(self, session_id: str) -> str:
        """Generate a detailed report for a session."""
        session = self._load_session(session_id)
        if not session:
            return "Session not found."
        
        report = []
        report.append(f"# Session Report: {session.name}")
        report.append(f"**Session ID**: {session.session_id}")
        report.append(f"**Status**: {session.status}")
        report.append(f"**Started**: {session.start_time}")
        
        if session.end_time:
            report.append(f"**Ended**: {session.end_time}")
        
        if session.description:
            report.append(f"**Description**: {session.description}")
        
        # Objectives
        if session.objectives:
            report.append("## Objectives")
            for obj in session.objectives:
                report.append(f"- {obj}")
        
        # Git Information
        report.append("## Git Information")
        report.append(f"- **Branch**: {session.initial_branch}")
        report.append(f"- **Initial Commit**: {session.initial_commit[:8]}")
        if session.final_commit:
            report.append(f"- **Final Commit**: {session.final_commit[:8]}")
        
        if session.lines_added or session.lines_removed:
            report.append(f"- **Changes**: +{session.lines_added} -{session.lines_removed} lines")
        
        # Progress Log
        if session.progress_log:
            report.append("## Progress Log")
            for entry in session.progress_log:
                timestamp = entry["timestamp"][:19].replace('T', ' ')
                report.append(f"- **{timestamp}**: {entry['notes']}")
        
        # Blockers
        if session.blockers:
            report.append("## Blockers")
            for blocker in session.blockers:
                timestamp = blocker["timestamp"][:19].replace('T', ' ')
                status = blocker.get("status", "open")
                report.append(f"- **{timestamp}** [{status}]: {blocker['description']}")
        
        # Decisions
        if session.decisions:
            report.append("## Decisions")
            for decision in session.decisions:
                timestamp = decision["timestamp"][:19].replace('T', ' ')
                report.append(f"- **{timestamp}**: {decision['description']}")
        
        # Modified Files
        if session.files_modified:
            report.append("## Modified Files")
            for file_mod in session.files_modified:
                report.append(f"- {file_mod}")
        
        return "\n".join(report)