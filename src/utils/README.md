# Utilities

Core utility modules for the Claude RAG Toolkit.

## Modules

### `repo_detector.py`
Automatically detects repository types and characteristics.

**Features:**
- Repository type detection (MLOps, Python, Documentation, Generic)
- Confidence scoring based on file patterns and technology markers
- Configuration generation for detected repository types
- Support for complex project structures

**Usage:**
```python
from utils.repo_detector import RepositoryDetector

detector = RepositoryDetector('.')
repo_type, confidence, analysis = detector.detect_repository_type()
config = detector.generate_config(repo_type)
```

### `session_manager.py`
Tracks development sessions with Git integration and progress logging.

**Features:**
- Session lifecycle management (start, update, pause, resume, end)
- Git integration (branch tracking, commit diffs, file changes)
- Progress logging with timestamps
- Blocker and decision tracking
- Session reporting and history

**Usage:**
```python
from utils.session_manager import SessionManager

manager = SessionManager('.')
session = manager.start_session("implement-feature", 
                               description="Add new functionality",
                               objectives=["Goal 1", "Goal 2"])
manager.update_session("Progress notes", blocker="Issue found")
manager.end_session("Implementation complete")
```

**Session Storage:**
- Sessions stored in `sessions/` directory
- Individual session files: `sessions/<session-id>.json`
- Session index: `sessions/index.json`
- Current session pointer: `sessions/.current_session`