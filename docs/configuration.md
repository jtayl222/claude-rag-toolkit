# Configuration Guide

## Overview

The Claude RAG Toolkit uses repository-specific configuration files to optimize indexing and search for different project types.

## Configuration File Location

Each project has its configuration in `.claude-rag/config.json`:

```
your-project/
├── .claude-rag/
│   ├── config.json          # Project configuration
│   ├── index.json           # Generated index (gitignored)
│   └── cache.json           # Search cache (gitignored)
└── ...
```

## Configuration Structure

```json
{
  "repo_type": "mlops-platform",
  "keywords": ["k3s", "harbor", "istio", "seldon"],
  "file_patterns": ["*.yml", "*.yaml", "*.md", "*.sh"],
  "exclude_paths": [".git", "__pycache__", "venv"],
  "extraction_focus": ["ansible_tasks", "kubernetes_resources"]
}
```

## Repository Types

### MLOps Platform
**Auto-detected from**: Ansible roles, Kubernetes manifests, infrastructure code

```json
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
  "extraction_focus": [
    "ansible_tasks", "kubernetes_resources", "service_endpoints"
  ]
}
```

### ML Model Project
**Auto-detected from**: Python ML files, notebooks, model configs

```json
{
  "repo_type": "ml-model",
  "keywords": [
    "model", "training", "inference", "prediction",
    "pytorch", "tensorflow", "scikit-learn"
  ],
  "file_patterns": [
    "*.py", "*.ipynb", "*.yaml", "*.md",
    "requirements.txt", "Dockerfile"
  ],
  "extraction_focus": [
    "python_functions", "jupyter_cells", "model_configs"
  ]
}
```

### Kubernetes
**Auto-detected from**: K8s manifests, Helm charts

```json
{
  "repo_type": "kubernetes",
  "keywords": [
    "kubernetes", "k8s", "kubectl", "helm", "kustomize"
  ],
  "file_patterns": [
    "*.yaml", "*.yml", "Chart.yaml", "values.yaml"
  ],
  "extraction_focus": [
    "kubernetes_resources", "helm_charts"
  ]
}
```

## Customization

### Adding File Patterns

```json
{
  "file_patterns": [
    "*.md",           // Markdown files
    "*.yml",          // YAML files
    "docs/**/*.md",   // Recursive docs
    "src/**/*.py"     // Python source
  ]
}
```

### Excluding Paths

```json
{
  "exclude_paths": [
    ".git",           // Git directory
    "node_modules",   // Dependencies
    "__pycache__",    // Python cache
    "*.log",          // Log files
    "tmp/"            // Temporary directory
  ]
}
```

### Custom Keywords

```json
{
  "keywords": [
    "your-product",
    "custom-service",
    "domain-specific-term"
  ]
}
```

### Extraction Focus

Optimize extraction for specific content types:

```json
{
  "extraction_focus": [
    "ansible_tasks",        // Ansible task definitions
    "kubernetes_resources", // K8s resource specs
    "python_functions",     // Python function definitions
    "shell_commands",       // Shell commands in docs
    "api_endpoints",        // API endpoint definitions
    "troubleshooting"       // Error solutions
  ]
}
```

## Advanced Settings

### Performance Tuning

```json
{
  "max_file_size_mb": 5,      // Skip files larger than 5MB
  "index_batch_size": 50,     // Process files in batches
  "search_result_limit": 25,  // Maximum search results
  "cache_ttl_hours": 24       // Cache validity period
}
```

### Content Processing

```json
{
  "content_processing": {
    "extract_code_blocks": true,
    "follow_cross_references": true,
    "build_knowledge_graph": true,
    "index_file_names": true
  }
}
```

## Repository-Specific Examples

### Large Monorepo
```json
{
  "exclude_paths": [
    ".git", "node_modules", "venv", "__pycache__",
    "build/", "dist/", "*.log", "tmp/",
    "services/legacy/", "archived/"
  ],
  "max_file_size_mb": 2,
  "index_batch_size": 25
}
```

### Documentation Site
```json
{
  "file_patterns": [
    "*.md", "*.rst", "*.txt",
    "docs/**/*", "wiki/**/*"
  ],
  "extraction_focus": [
    "documentation_structure",
    "cross_references",
    "tutorials"
  ]
}
```

### Multi-Language Project
```json
{
  "file_patterns": [
    "*.py", "*.js", "*.go", "*.rs",
    "*.md", "*.yml", "*.json"
  ],
  "keywords": [
    "api", "service", "component",
    "python", "javascript", "golang", "rust"
  ]
}
```

## Manual Configuration

### Force Repository Type
```bash
# Override auto-detection
claude-rag init --repo-type ml-model

# Edit configuration manually
vim .claude-rag/config.json
claude-rag reindex --force
```

### Validate Configuration
```bash
# Analyze project with current config
claude-rag analyze

# Test search with current index
claude-rag search "test query"

# Check statistics
claude-rag stats
```

## Troubleshooting

### Poor Search Results
1. Check keywords match your domain
2. Verify file patterns include relevant files
3. Ensure extraction focus matches content type

### Slow Indexing
1. Add more exclusion patterns
2. Reduce max_file_size_mb
3. Increase exclude patterns for large directories

### Missing Content
1. Check file patterns are comprehensive
2. Verify paths aren't excluded
3. Test with `claude-rag analyze`

## Migration

### From Old RAG System
```bash
# Use migration script
./templates/migrate_from_old_rag.sh
```

### Between Repository Types
```bash
# Change type and reindex
claude-rag init --repo-type new-type --force
```