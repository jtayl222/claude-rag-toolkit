# Claude RAG Toolkit

A multi-repository documentation management system that provides Claude Code with intelligent search capabilities across different project types.

## Overview

This toolkit solves documentation drift problems by providing:
- **Project-aware indexing** of documentation, code, and configuration files
- **Semantic search** across project knowledge base
- **MCP integration** for Claude Code
- **Multi-repository support** with isolated databases per project
- **Repository type detection** with tailored configurations

## Supported Repository Types

### MLOps Platform
- **Keywords**: k3s, harbor, istio, seldon, kubeadm, metallb
- **Files**: `*.yml`, `*.yaml`, `*.md`, `*.sh`, Ansible roles
- **Focus**: Infrastructure, deployment, monitoring, troubleshooting

### ML Model Projects  
- **Keywords**: model, pipeline, deployment, training, inference
- **Files**: `*.py`, `*.ipynb`, `*.yaml`, `*.md`, `requirements.txt`
- **Focus**: Model development, experimentation, deployment

### General Documentation
- **Keywords**: configurable
- **Files**: `*.md`, `*.txt`, `*.yaml`, `*.json`
- **Focus**: Generic documentation search

## Architecture

```
claude-rag-toolkit/                    # Shared tool repository
├── src/
│   ├── core/
│   │   ├── rag_engine.py             # Core indexing engine
│   │   ├── knowledge_extractor.py    # Content analysis
│   │   └── search_engine.py          # Query processing
│   ├── integrations/
│   │   ├── mcp_server.py             # MCP protocol server
│   │   └── cli_interface.py          # Command line tools
│   ├── config/
│   │   ├── repo_types.yaml           # Repository configurations
│   │   └── extraction_rules.yaml    # Content extraction rules
│   └── utils/
│       ├── repo_detector.py          # Auto-detect project type
│       └── file_scanner.py           # Efficient file processing
├── templates/
│   ├── project_setup.sh             # Per-project setup script
│   ├── mcp_config.json              # MCP configuration template
│   └── gitignore_template           # .gitignore additions
├── tests/
│   ├── test_multi_repo.py          # Multi-repo functionality
│   └── fixtures/                   # Test data
└── docs/
    ├── installation.md
    ├── configuration.md
    └── api_reference.md

project-repo/                         # Any target project
├── .claude-rag/                     # Project-specific RAG data
│   ├── config.json                  # Project configuration
│   ├── index.json                   # Knowledge base (gitignored)
│   ├── cache.json                   # Query cache (gitignored)
│   └── .gitignore                   # Ignore generated files
└── .gitignore                       # Add .claude-rag/ (except config)
```

## Installation

### 1. Install Shared Toolkit

#### Basic Installation (Zero Dependencies)
```bash
# Clone the toolkit
git clone https://github.com/yourusername/claude-rag-toolkit.git /home/user/REPOS/claude-rag-toolkit
cd /home/user/REPOS/claude-rag-toolkit

# Basic installation - uses only Python standard library
pip install -e .
```

#### Enhanced Installation Options
```bash
# Install with rich CLI output and better UX
pip install -e ".[rich]"

# Install with performance and validation enhancements  
pip install -e ".[enhanced]"

# Install with all enhancements (recommended)
pip install -e ".[full]"

# Development installation
pip install -e ".[dev]"
```

#### Package Options
- **Basic**: Zero external dependencies, uses Python standard library only
- **Rich**: Enhanced CLI with `rich` terminal output and `click` argument parsing
- **Enhanced**: Performance boost with `pydantic` validation, `orjson` JSON parsing, `rapidfuzz` search
- **Full**: All enhancements combined (rich + enhanced)
- **Dev**: Development tools including testing, linting, and pre-commit hooks

### 2. Setup in Target Project
```bash
# Navigate to your project
cd /home/user/REPOS/ml-platform

# Initialize RAG system
claude-rag init

# Or manually with specific type
claude-rag init --repo-type=mlops-platform
```

### 3. Configure Claude Code
```bash
# Add MCP server to Claude Code configuration
claude-rag setup-mcp
```

## Usage

### Command Line Interface

#### MLOps Platform Examples
```bash
# Search for specific infrastructure setup
claude-rag search "harbor registry authentication"
# Results: Harbor admin passwords, registry secrets, authentication methods

claude-rag search "metallb loadbalancer configuration" 
# Results: MetalLB IP pools, service configurations, troubleshooting

# Find troubleshooting information for common issues
claude-rag troubleshoot "x509 certificate signed by unknown authority"
# Results: K3s certificate issues, kubeconfig fixes, TLS troubleshooting

claude-rag troubleshoot "DNS resolution failures"
# Results: Network policies, CoreDNS issues, cross-namespace communication

# Get context for specific configuration files
claude-rag context "infrastructure/cluster/roles/foundation/k3s_control_plane/tasks/main.yml"
# Results: Related Ansible tasks, variable dependencies, role relationships

# List commands for specific technologies
claude-rag commands kubectl
# Results: Kubernetes commands used in project, with context and examples

claude-rag commands ansible-playbook
# Results: Playbook commands, deployment patterns, tag usage
```

#### Python Project Examples
```bash
# Search for implementation patterns
claude-rag search "session management implementation"
# Results: SessionManager class, state persistence, Git integration

claude-rag search "testing fixtures and mocks"
# Results: Test setup patterns, conftest.py, mock configurations

# Get file relationships and dependencies
claude-rag context "src/utils/session_manager.py"
# Results: Import dependencies, test files, CLI integration points

# Find troubleshooting solutions
claude-rag troubleshoot "import error relative import"
# Results: Python import fixes, package structure solutions
```

#### Development Workflow Examples
```bash
# Start tracking a development session
claude-rag session start "implementing-vector-search" -d "Adding semantic search with embeddings"

# Search for related implementation examples during development
claude-rag search "vector embeddings similarity search"

# Update session progress
claude-rag session update "Implemented basic vector store, need to add similarity scoring"

# Find configuration examples
claude-rag search "pydantic configuration validation"

# Check project statistics and coverage
claude-rag stats

# End session with summary
claude-rag session end -s "Completed vector search implementation with 85% test coverage"
```

### MCP (Model Context Protocol) Integration

#### Quick Setup
```bash
# Initialize RAG system in your project
claude-rag init

# Configure MCP server for Claude Code
claude-rag setup-mcp

# Restart Claude Code to load the new tools
```

#### Available MCP Tools

When configured, Claude Code gains these intelligent tools:

1. **search_documentation** - Search project knowledge base
   - Parameters: query, category (optional), limit (optional)
   - Example: "Search for harbor registry configuration"
   
2. **troubleshoot_error** - Find solutions for errors
   - Parameters: error message
   - Example: "Help me fix port 6443 connection refused"
   
3. **get_file_context** - Understand file relationships
   - Parameters: filepath
   - Example: "Explain infrastructure/cluster/site.yml"
   
4. **get_related_commands** - Find technology-specific commands
   - Parameters: technology, limit (optional)
   - Example: "Show kubectl commands in this project"
   
5. **get_project_stats** - View index statistics
   - No parameters required
   - Shows indexed files, concepts, and last update time
   
6. **reindex_project** - Update documentation index
   - Parameters: force (optional)
   - Rebuilds the knowledge base with latest changes

### Enhanced Git Workflow

With RAG integration, git workflows become intelligence-driven:

```markdown
## RAG-Enhanced Git Workflow

### Pre-Commit Intelligence
1. `search_documentation("atomic commit patterns")` - Learn project conventions
2. `get_file_context("modified_file.yml")` - Understand change impact
3. `troubleshoot_error("current error")` - Find related fixes

### Intelligent Commit Grouping
- RAG identifies related files that should be committed together
- Suggests documentation updates needed for consistency
- Recommends commit message patterns from project history

### Documentation Sync Detection
- Automatically detects when code changes require doc updates
- Suggests which README/docs files need attention
- Prevents documentation drift through proactive recommendations
```

## Repository Configurations

### MLOps Platform Example
```yaml
# .claude-rag/config.json
{
  "repo_type": "mlops-platform",
  "keywords": [
    "k3s", "harbor", "istio", "seldon", "kubeadm", "metallb",
    "prometheus", "grafana", "jupyterhub", "argo", "sealed-secrets"
  ],
  "file_patterns": [
    "*.yml", "*.yaml", "*.md", "*.sh", 
    "roles/**/*.yml", "inventory/**/*.yml"
  ],
  "exclude_paths": [
    ".git", "node_modules", "__pycache__", "venv",
    "*.log", "tmp/", ".cache/"
  ],
  "extraction_focus": [
    "ansible_tasks", "kubernetes_resources", "shell_commands",
    "troubleshooting_sections", "configuration_examples"
  ],
  "cross_references": {
    "ansible_roles": "infrastructure/cluster/roles/*/",
    "scripts": "scripts/*.sh",
    "documentation": "*.md"
  }
}
```

### ML Model Project Example  
```yaml
# .claude-rag/config.json
{
  "repo_type": "ml-model",
  "keywords": [
    "model", "pipeline", "training", "inference", "deployment",
    "fraud", "feature", "prediction", "validation", "monitoring"
  ],
  "file_patterns": [
    "*.py", "*.ipynb", "*.yaml", "*.md", 
    "requirements.txt", "Dockerfile", "*.json"
  ],
  "exclude_paths": [
    ".git", "__pycache__", "venv", "env", ".pytest_cache",
    "*.pyc", "models/saved/", "data/raw/"
  ],
  "extraction_focus": [
    "python_functions", "jupyter_cells", "model_configs",
    "pipeline_definitions", "api_endpoints"
  ],
  "cross_references": {
    "notebooks": "notebooks/*.ipynb",
    "models": "models/**/*.py", 
    "configs": "config/*.yaml"
  }
}
```

## Key Features

### 1. **Automatic Repository Detection**
- Scans project structure to determine type
- Loads appropriate configuration automatically
- Supports custom configurations for unique projects

### 2. **Intelligent Content Extraction**
- **Ansible Projects**: Tasks, variables, templates, handlers
- **Python Projects**: Functions, classes, docstrings, imports
- **Kubernetes**: Resources, configurations, network policies
- **Documentation**: Headers, code blocks, cross-references

### 3. **Cross-Repository Learning**
- Shared patterns across similar project types
- Common troubleshooting database
- Best practice recommendations

### 4. **Change Detection & Notifications**
- Git integration to track documentation changes
- Alerts when code changes may require doc updates
- Prevents documentation drift proactively

## Benefits

1. **Prevents Documentation Drift**: Proactive detection of outdated docs
2. **Accelerates Development**: Find solutions and patterns instantly  
3. **Improves Code Quality**: Context-aware commit recommendations
4. **Knowledge Preservation**: Captures and indexes tribal knowledge
5. **Team Collaboration**: Shared understanding through searchable knowledge
6. **Multi-Project Consistency**: Learn patterns across repositories

## Integration Examples

### With VSCode/Cursor
```json
// settings.json
{
  "claude-rag.enableAutoIndex": true,
  "claude-rag.indexOnSave": ["*.md", "*.yml"],
  "claude-rag.showContextOnHover": true
}
```

### With Git Hooks
```bash
# .git/hooks/pre-commit
#!/bin/bash
claude-rag check-docs-sync
```

### With CI/CD
```yaml
# .github/workflows/docs-check.yml
- name: Check Documentation Consistency
  run: claude-rag validate-docs
```

## Development

### Development Setup
```bash
# Clone and setup development environment
git clone https://github.com/yourusername/claude-rag-toolkit.git
cd claude-rag-toolkit

# Install with development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Verify setup
make test
```

### Development Workflow

#### Session Management
Track your development sessions with built-in session management:
```bash
# Start a development session
make session-start  # Interactive prompts for name/description
# Or directly: claude-rag session start "feature-name" -d "Description"

# Log progress during development
make session-update  # Interactive prompt for notes
# Or: claude-rag session update "Implemented X, fixed Y"

# End session with summary
make session-end  # Interactive prompt for summary
# Or: claude-rag session end -s "Completed feature implementation"

# View session history
claude-rag session list
claude-rag session report <session-id>
```

#### Testing
```bash
# Run full test suite with coverage (>80% required)
make test-cov

# Run tests in watch mode during development
make test-watch

# Run specific test modules
pytest tests/unit/utils/test_session_manager.py -v
pytest tests/unit/core/ -v

# Check test coverage
pytest --cov=src --cov-report=html
# Open htmlcov/index.html to view detailed coverage
```

#### Code Quality
```bash
# Format code (automatically via pre-commit)
make format

# Check formatting without changes
make format-check

# Run linting
make lint

# Run all quality checks
make lint && make format-check && make test
```

### Contributing

#### 1. Setup and Branching
```bash
# Fork repository and create feature branch
git checkout -b feature/new-repo-type

# Start development session
claude-rag session start "new-repo-type" -d "Adding support for new repository type"
```

#### 2. Development Process
1. **Write tests first**: Add tests in `tests/unit/` or `tests/integration/`
2. **Implement feature**: Follow existing patterns and maintain >80% test coverage
3. **Update documentation**: Add examples and update README if needed
4. **Log progress**: Use `claude-rag session update` to track milestones

#### 3. Quality Assurance
```bash
# Ensure all checks pass
make test-cov  # Must achieve >80% coverage
make lint      # Must pass without errors
make format-check  # Code must be properly formatted

# Pre-commit hooks will automatically run on commit
git commit -m "feat: add new repository type support"
```

#### 4. Submission
```bash
# End development session
claude-rag session end -s "Completed new repository type implementation with tests"

# Push and create pull request
git push origin feature/new-repo-type
```

### Adding New Repository Types

#### 1. Detection Logic
Add detection patterns in `src/utils/repo_detector.py`:
```python
def _detect_my_repo_type(self) -> float:
    """Detect my custom repository type."""
    score = 0.0
    
    # Check for characteristic files
    if self._path_exists("my-config.yaml"):
        score += 0.3
    
    # Check for specific content patterns
    if self._file_contains("README.md", ["my-framework"]):
        score += 0.2
        
    return min(score, 1.0)
```

#### 2. Configuration
Add repository configuration in `generate_config()` method:
```python
elif repo_type == "my-repo-type":
    return {
        "repo_type": "my-repo-type",
        "keywords": ["my-framework", "specific-terms"],
        "file_patterns": ["*.yaml", "*.md"],
        "exclude_paths": [".cache", "build/"],
        "extraction_focus": ["configurations", "commands"]
    }
```

#### 3. Testing
Create comprehensive tests in `tests/unit/utils/test_repo_detector.py`:
```python
def test_detect_my_repo_type(self, temp_dir):
    """Test detection of my repository type."""
    # Create characteristic files
    (temp_dir / "my-config.yaml").write_text("framework: my-framework")
    
    detector = RepositoryDetector(str(temp_dir))
    repo_type, confidence, analysis = detector.detect_repository_type()
    
    assert repo_type == "my-repo-type"
    assert confidence > 0.3
```

### Testing Guidelines

#### Test Structure
```
tests/
├── unit/                    # Unit tests (fast, isolated)
│   ├── core/               # Core functionality tests
│   ├── utils/              # Utility module tests
│   └── conftest.py         # Shared fixtures
├── integration/            # Integration tests (slower, end-to-end)
│   └── test_cli.py        # CLI integration tests
└── fixtures/               # Test data and mock repositories
    ├── sample_python/      # Python project fixture
    └── sample_mlops/       # MLOps project fixture
```

#### Test Requirements
- **Coverage**: Maintain >80% code coverage
- **Isolation**: Tests must not depend on external services
- **Fast execution**: Unit tests should complete in <5 seconds
- **Clear assertions**: Each test should verify specific behavior

#### Writing Tests
```python
def test_specific_behavior(self, temp_dir):
    """Test specific behavior with clear assertion."""
    # Arrange: Set up test conditions
    detector = RepositoryDetector(str(temp_dir))
    
    # Act: Execute the behavior being tested
    result = detector.some_method()
    
    # Assert: Verify expected outcome
    assert result.expected_property == "expected_value"
```

## Troubleshooting

### Installation Issues

#### Import Errors
```bash
# Error: ModuleNotFoundError: No module named 'core'
# Solution: Ensure you're running from the correct directory
cd /path/to/claude-rag-toolkit
pip install -e .

# Or check if package is installed correctly
pip list | grep claude-rag-toolkit
```

#### Zero-Dependency Core Not Working
```bash
# Verify basic installation works
python -c "import sys; print(sys.modules.keys())"
claude-rag --help

# If still failing, check Python version
python --version  # Must be >= 3.8
```

### Runtime Issues

#### Session Management Problems
```bash
# Error: No active session found
# Check if session exists
claude-rag session current

# View all sessions
claude-rag session list

# Resume a previous session
claude-rag session resume <session-id>
```

#### Search Not Finding Results
```bash
# Check if project is indexed
claude-rag stats

# Re-index if no files found
claude-rag reindex

# Verify repository type detection
claude-rag info
```

#### File Permission Errors
```bash
# Error: Permission denied when creating .claude-rag/
# Check directory permissions
ls -la .
chmod 755 .

# Ensure user has write access
touch .claude-rag/.test && rm .claude-rag/.test
```

### Development Issues

#### Tests Failing
```bash
# Common test issues and solutions

# 1. Coverage too low
make test-cov
# Add tests to achieve >80% coverage

# 2. Import path issues in tests
# Ensure conftest.py has correct sys.path modifications

# 3. Mock issues with session manager
# Check that UUID and subprocess mocks are properly configured
```

#### Pre-commit Hook Failures
```bash
# Format issues
make format  # Auto-fix formatting

# Linting issues
make lint    # Show specific linting errors
flake8 src/ tests/ --max-line-length=100

# Hook installation issues
pre-commit install --force
pre-commit run --all-files
```

#### Git Session Tracking Issues
```bash
# Error: Git repository not found
git init  # Initialize git repo if needed

# Error: Git commands failing in session manager
# Check git is installed and working
git --version
git status

# Verify repository has commits
git log --oneline -n 5
```

### Performance Issues

#### Slow Indexing
```bash
# Large repositories taking too long
# 1. Check exclude patterns in config
cat .claude-rag/config.json | grep exclude_paths

# 2. Add more exclusion patterns
claude-rag init --repo-type python  # Regenerate config with better exclusions

# 3. Monitor file count
find . -name "*.py" | wc -l  # Should be reasonable for your project
```

#### Memory Usage
```bash
# High memory usage during indexing
# Monitor with system tools
top -p $(pgrep -f claude-rag)

# For very large repos, consider selective indexing
# Edit .claude-rag/config.json to be more selective with file_patterns
```

### Getting Help

#### Debug Mode
```bash
# Enable verbose output for debugging
export CLAUDE_RAG_DEBUG=1
claude-rag search "your query"

# Check log files
tail -f .claude-rag/logs/debug.log
```

#### Report Issues
Include this information when reporting bugs:
```bash
# System information
python --version
pip list | grep claude-rag-toolkit
git --version

# Project information  
claude-rag info
claude-rag stats

# Error reproduction
# Exact commands that trigger the issue
# Full error messages and stack traces
```

## Roadmap

- [ ] **Vector Embeddings**: Semantic search with sentence transformers
- [ ] **Live Sync**: Real-time index updates on file changes  
- [ ] **Team Sharing**: Shared knowledge base with conflict resolution
- [ ] **Analytics**: Track most searched topics and knowledge gaps
- [ ] **Integration**: Slack/Discord bots for team knowledge sharing
- [ ] **Templates**: Auto-generate documentation templates from code

## License

MIT License - See LICENSE file for details.

## Support

- **Issues**: https://github.com/yourusername/claude-rag-toolkit/issues
- **Discussions**: https://github.com/yourusername/claude-rag-toolkit/discussions
- **Documentation**: https://claude-rag-toolkit.readthedocs.io