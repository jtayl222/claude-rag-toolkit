# Test Fixtures

This directory contains test fixtures and sample data for the Claude RAG Toolkit test suite.

## Contents

- Sample project structures for different repository types
- Example configuration files
- Mock data for testing knowledge extraction
- Test documents in various formats

## Usage

Fixtures are automatically loaded by pytest through the conftest.py configuration.
Individual test modules can access fixtures via dependency injection.

Example:
```python
def test_something(sample_project_dir, mock_git_repo):
    # Test code here
    pass
```