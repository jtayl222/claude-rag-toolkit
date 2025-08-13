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
```bash
# Clone the toolkit
git clone https://github.com/yourusername/claude-rag-toolkit.git /home/user/REPOS/claude-rag-toolkit
cd /home/user/REPOS/claude-rag-toolkit

# Install dependencies
pip install -r requirements.txt

# Install globally (optional)
pip install -e .
```

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
```bash
# Search across project documentation
claude-rag search "harbor registry setup"

# Find troubleshooting information  
claude-rag troubleshoot "port 6443 conflict"

# Get file context and relationships
claude-rag context "infrastructure/cluster/site.yml"

# List available commands for a technology
claude-rag commands kubectl

# Show recent documentation changes
claude-rag recent

# Rebuild index after major changes
claude-rag reindex
```

### MCP Tools for Claude Code

When properly configured, Claude Code gains these tools:

1. **search_documentation(query)** - Search project knowledge
2. **troubleshoot_error(keyword)** - Find error solutions  
3. **get_file_context(filepath)** - Understand file relationships
4. **get_related_commands(tech)** - Find relevant commands
5. **get_recent_changes()** - Track documentation updates
6. **get_project_stats()** - Index health and coverage

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

### Contributing
1. Fork the repository
2. Create feature branch: `git checkout -b feature/new-repo-type`
3. Add tests: `pytest tests/test_new_feature.py`
4. Submit pull request

### Adding New Repository Types
1. Define configuration in `src/config/repo_types.yaml`
2. Add detection logic in `src/utils/repo_detector.py`
3. Create extraction rules in `src/config/extraction_rules.yaml`
4. Add tests in `tests/fixtures/`

### Testing
```bash
# Run all tests
pytest

# Test specific repository type
pytest tests/test_mlops_platform.py

# Test MCP integration
pytest tests/test_mcp_server.py -v
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