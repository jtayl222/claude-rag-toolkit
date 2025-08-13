"""
Pytest configuration and shared fixtures for Claude RAG Toolkit tests.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock

# Test data directory
TEST_DATA_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test isolation."""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    shutil.rmtree(temp_path)


@pytest.fixture
def sample_project_dir(temp_dir):
    """Create a sample project directory structure for testing."""
    project_dir = temp_dir / "sample_project"
    project_dir.mkdir()
    
    # Create some sample files
    (project_dir / "README.md").write_text("# Sample Project\nThis is a test project.")
    (project_dir / "setup.py").write_text("from setuptools import setup\nsetup(name='sample')")
    (project_dir / "requirements.txt").write_text("pytest>=7.0.0\nrequests>=2.28.0")
    
    # Create source directory
    src_dir = project_dir / "src"
    src_dir.mkdir()
    (src_dir / "__init__.py").write_text("")
    (src_dir / "main.py").write_text("def main():\n    print('Hello World')")
    
    return project_dir


@pytest.fixture
def mock_git_repo(temp_dir, monkeypatch):
    """Mock a git repository for testing."""
    git_dir = temp_dir / ".git"
    git_dir.mkdir()
    
    # Mock git commands
    def mock_run(cmd, *args, **kwargs):
        if "rev-parse --abbrev-ref HEAD" in " ".join(cmd):
            result = Mock()
            result.stdout = "main"
            result.returncode = 0
            return result
        elif "rev-parse HEAD" in " ".join(cmd):
            result = Mock()
            result.stdout = "abc123def456"
            result.returncode = 0
            return result
        elif "status --porcelain" in " ".join(cmd):
            result = Mock()
            result.stdout = "M  file.py\n?? newfile.py"
            result.returncode = 0
            return result
        return Mock(returncode=0, stdout="")
    
    import subprocess
    monkeypatch.setattr(subprocess, "run", mock_run)
    
    return temp_dir


@pytest.fixture
def sample_markdown_content():
    """Sample markdown content for testing knowledge extraction."""
    return """# Test Document

This is a test document for knowledge extraction.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
pytest tests/

# Deploy application  
kubectl apply -f deployment.yaml
```

## Configuration

```yaml
# config.yaml
server:
  port: 8080
  host: localhost
database:
  url: postgresql://localhost/test
```

## Troubleshooting

### Error: Connection Failed
If you see "Connection failed" errors, check:
1. Database is running
2. Credentials are correct
3. Network connectivity

### Solution: Restart Services
```bash
systemctl restart postgresql
systemctl restart application
```
"""


@pytest.fixture
def sample_python_content():
    """Sample Python content for testing knowledge extraction."""
    return '''"""
Sample Python module for testing.
"""

import os
import sys
from typing import Dict, List


class SampleClass:
    """A sample class for testing."""
    
    def __init__(self, name: str):
        self.name = name
    
    def process_data(self, data: Dict[str, List[str]]) -> bool:
        """Process data and return success status."""
        try:
            for key, values in data.items():
                print(f"Processing {key}: {values}")
            return True
        except Exception as e:
            print(f"Error: {e}")
            return False


def main():
    """Main entry point."""
    sample = SampleClass("test")
    data = {"items": ["a", "b", "c"]}
    success = sample.process_data(data)
    print(f"Success: {success}")


if __name__ == "__main__":
    main()
'''


@pytest.fixture
def sample_rag_config():
    """Sample RAG configuration for testing."""
    return {
        "repo_type": "python",
        "keywords": ["python", "pytest", "testing"],
        "file_patterns": ["*.py", "*.md", "*.txt"],
        "exclude_paths": [".git", "__pycache__", "venv"],
        "extraction_focus": ["python_functions", "class_definitions"]
    }