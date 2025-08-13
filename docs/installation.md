# Installation Guide

## Prerequisites

- Python 3.8 or higher
- Git (for repository detection)
- Project with documentation to index

## Install from Source

```bash
# Clone the repository
git clone https://github.com/yourusername/claude-rag-toolkit.git
cd claude-rag-toolkit

# Install in development mode
pip install -e .

# Or install with extras
pip install -e ".[mcp,dev]"
```

## Install from PyPI

```bash
# Basic installation
pip install claude-rag-toolkit

# With MCP support
pip install "claude-rag-toolkit[mcp]"

# With development tools
pip install "claude-rag-toolkit[dev]"
```

## Verify Installation

```bash
# Check if command is available
claude-rag --help

# Test on a project
cd /path/to/your/project
claude-rag init
claude-rag stats
```

## Next Steps

1. [Quick Start Guide](../README.md#usage)
2. [MCP Integration](../templates/README_MCP.md)
3. [Configuration Guide](configuration.md)