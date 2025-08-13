#!/bin/bash
# Project Setup Script for Claude RAG Toolkit
# This script initializes RAG system in any project repository

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(pwd)"
CLAUDE_RAG_DIR="$PROJECT_ROOT/.claude-rag"

echo "🚀 Setting up Claude RAG system..."
echo "📁 Project: $PROJECT_ROOT"

# Check if already initialized
if [ -f "$CLAUDE_RAG_DIR/config.json" ]; then
    echo "✅ RAG system already initialized"
    echo "💡 Use 'claude-rag reindex' to update or 'claude-rag init --force' to reinitialize"
    exit 0
fi

# Check if claude-rag toolkit is available
if ! command -v claude-rag &> /dev/null; then
    echo "❌ claude-rag command not found"
    echo "📦 Installing Claude RAG Toolkit..."
    
    # Try to install from source if available
    if [ -f "$SCRIPT_DIR/../setup.py" ]; then
        pip install -e "$SCRIPT_DIR/.."
    else
        echo "❌ Claude RAG Toolkit source not found"
        echo "💡 Please install manually: pip install claude-rag-toolkit"
        exit 1
    fi
fi

# Initialize RAG system
echo "📚 Initializing RAG system..."
claude-rag init

# Success message
echo ""
echo "✅ RAG system setup complete!"
echo ""
echo "🔥 Next steps:"
echo "  • Search: claude-rag search 'your query'"
echo "  • Troubleshoot: claude-rag troubleshoot 'error message'"
echo "  • Context: claude-rag context 'file.md'"
echo "  • Commands: claude-rag commands kubectl"
echo ""
echo "🛠️  For MCP integration with Claude Code:"
echo "  • See: .claude-rag/README_MCP.md"
echo "  • Run: claude-rag setup-mcp"