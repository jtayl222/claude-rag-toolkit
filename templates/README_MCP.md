# Claude RAG Toolkit MCP Integration

This document explains how to integrate the Claude RAG Toolkit with Claude Code using the Model Context Protocol (MCP).

## Overview

The Claude RAG Toolkit provides intelligent search capabilities across your project documentation through MCP tools that Claude Code can use directly.

## Available MCP Tools

### 1. `search_documentation(query, category?, limit?)`
Search across all indexed project documentation.
- **query**: Search terms or keywords
- **category**: Limit to specific type (concepts, commands, configurations, troubleshooting)
- **limit**: Maximum results (default: 10)

### 2. `troubleshoot_error(error)`
Find solutions for specific errors or issues.
- **error**: Error message or keyword to search for

### 3. `get_file_context(filepath)`
Get detailed context and relationships for a specific file.
- **filepath**: Path to file relative to project root

### 4. `get_related_commands(technology, limit?)`
Find commands related to a specific technology.
- **technology**: Tool name (kubectl, docker, ansible, etc.)
- **limit**: Maximum commands to return (default: 15)

### 5. `get_project_stats()`
Get project statistics and index health information.

### 6. `reindex_project(force?)`
Rebuild the project documentation index.
- **force**: Force reindex all files (default: false)

## Installation

### 1. Initialize RAG System
```bash
# In your project directory
claude-rag init

# Verify setup
claude-rag stats
```

### 2. Configure Claude Code MCP
Add this to your Claude Code MCP configuration:

```json
{
  "claude-rag-toolkit": {
    "command": "python3",
    "args": [
      "/home/user/REPOS/claude-rag-toolkit/src/mcp_server.py",
      "--project-root", "/path/to/your/project"
    ],
    "env": {
      "PYTHONPATH": "/home/user/REPOS/claude-rag-toolkit/src"
    }
  }
}
```

### 3. Automatic Setup
```bash
# Run automatic MCP configuration
claude-rag setup-mcp
```

## Usage Examples

### In Claude Code
Once configured, you can use these tools naturally in conversation:

**Search Documentation:**
"Search for information about harbor registry setup"
→ Uses `search_documentation("harbor registry setup")`

**Find Error Solutions:**
"Help me troubleshoot port 6443 connection refused"
→ Uses `troubleshoot_error("port 6443 connection refused")`

**Get File Context:**
"Explain the infrastructure/cluster/site.yml file"
→ Uses `get_file_context("infrastructure/cluster/site.yml")`

**Find Related Commands:**
"Show me all kubectl commands in the project"
→ Uses `get_related_commands("kubectl")`

## Repository-Specific Benefits

### MLOps Platform
- Find Ansible playbook tasks and configurations
- Search Kubernetes manifests and Helm charts  
- Troubleshoot infrastructure deployment issues
- Locate service endpoints and network policies

### ML Model Projects
- Search training scripts and model configurations
- Find feature engineering and data pipeline code
- Troubleshoot model deployment issues
- Locate API endpoints and inference code

### General Documentation
- Cross-reference related files and concepts
- Find command examples and troubleshooting guides
- Search across multiple documentation formats
- Track documentation changes and updates

## Advanced Configuration

### Custom Repository Types
Edit `.claude-rag/config.json` to customize:
- File patterns to index
- Keywords for better search
- Extraction focus areas
- Exclusion patterns

### Performance Tuning
For large repositories:
- Add more exclusion patterns
- Limit file types indexed
- Use selective reindexing
- Configure batch processing

## Troubleshooting

### MCP Server Not Starting
```bash
# Check if RAG system is initialized
claude-rag stats

# Verify Python path
echo $PYTHONPATH

# Test server manually
python3 /home/user/REPOS/claude-rag-toolkit/src/mcp_server.py --help
```

### Poor Search Results
```bash
# Rebuild index
claude-rag reindex --force

# Check configuration
cat .claude-rag/config.json

# Verify file patterns
claude-rag analyze
```

### File Not Found Errors
```bash
# Check file paths are relative to project root
pwd
ls -la .claude-rag/

# Re-run initialization
claude-rag init --force
```

## Integration with Other Tools

### Git Hooks
Add to `.git/hooks/post-merge`:
```bash
#!/bin/bash
claude-rag reindex
```

### CI/CD Pipelines
```yaml
- name: Update Documentation Index
  run: claude-rag reindex --force
```

### IDE Integration
Configure your IDE to run `claude-rag search` on selected text for quick documentation lookup.

## Support

- **Issues**: Check logs in `.claude-rag/*.log`
- **Configuration**: Validate with `claude-rag analyze`
- **Performance**: Monitor with `claude-rag stats`
- **Updates**: Reindex with `claude-rag reindex`