#!/bin/bash
# Migrate from old .claude/ RAG system to new multi-repo toolkit

PROJECT_ROOT="${1:-$(pwd)}"
TOOLKIT_PATH="${2:-/home/user/REPOS/claude-rag-toolkit}"

echo "🔄 Migrating RAG system to multi-repo toolkit..."
echo "Project: $PROJECT_ROOT"

cd "$PROJECT_ROOT"

# Check if old system exists
if [ ! -d ".claude" ]; then
    echo "❌ No old .claude/ directory found"
    echo "Use project_setup.sh for new installations"
    exit 1
fi

# Backup old system
echo "💾 Backing up old RAG system..."
if [ -d ".claude-backup" ]; then
    rm -rf ".claude-backup"
fi
cp -r ".claude" ".claude-backup"
echo "✅ Backup created at .claude-backup/"

# Extract useful data from old system
OLD_INDEX=".claude/rag_index.json"
OLD_CONFIG=".claude/config.json"

# Initialize new system
echo "🔧 Setting up new RAG system..."
export PYTHONPATH="$TOOLKIT_PATH/src:$PYTHONPATH"
python3 "$TOOLKIT_PATH/src/integrations/cli_interface.py" init --force

# Import old data if available
if [ -f "$OLD_INDEX" ]; then
    echo "📊 Attempting to import old index data..."
    
    # Create migration script
    cat > .claude-rag/migrate_data.py << 'EOF'
#!/usr/bin/env python3
import json
import sys
from pathlib import Path

def migrate_old_index():
    """Migrate data from old RAG index format."""
    old_index_path = Path(".claude/rag_index.json")
    new_index_path = Path(".claude-rag/index.json")
    
    if not old_index_path.exists():
        print("No old index to migrate")
        return
    
    with open(old_index_path, 'r') as f:
        old_index = json.load(f)
    
    with open(new_index_path, 'r') as f:
        new_index = json.load(f)
    
    print(f"Old index: {len(old_index.get('documents', {}))} documents")
    print(f"New index: {len(new_index.get('documents', {}))} documents")
    
    # Merge knowledge where possible
    migrated_count = 0
    for doc_path, doc_data in old_index.get("documents", {}).items():
        if doc_path in new_index["documents"]:
            # Merge knowledge sections
            old_knowledge = doc_data.get("knowledge", {})
            new_knowledge = new_index["documents"][doc_path].get("knowledge", {})
            
            # Preserve old troubleshooting entries
            if "troubleshooting" in old_knowledge:
                if "troubleshooting" not in new_knowledge:
                    new_knowledge["troubleshooting"] = []
                new_knowledge["troubleshooting"].extend(old_knowledge["troubleshooting"])
                migrated_count += 1
    
    # Save updated index
    with open(new_index_path, 'w') as f:
        json.dump(new_index, f, indent=2)
    
    print(f"✅ Migrated knowledge for {migrated_count} documents")

if __name__ == "__main__":
    migrate_old_index()
EOF
    
    python3 .claude-rag/migrate_data.py
    rm .claude-rag/migrate_data.py
fi

# Update .gitignore
echo "📝 Updating .gitignore..."
if [ -f ".gitignore" ]; then
    # Remove old entries
    sed -i '/^\.claude\/rag_index\.json$/d' .gitignore 2>/dev/null || true
    sed -i '/^\.claude\/rag_cache\.json$/d' .gitignore 2>/dev/null || true
    sed -i '/^\.claude\/doc_index\.json$/d' .gitignore 2>/dev/null || true
    
    # Add new entries
    if ! grep -q ".claude-rag/" .gitignore; then
        echo "" >> .gitignore
        echo "# Claude RAG generated files" >> .gitignore
        echo ".claude-rag/index.json" >> .gitignore
        echo ".claude-rag/cache.json" >> .gitignore
        echo ".claude-rag/*.log" >> .gitignore
    fi
fi

# Create project CLI wrapper
cat > claude-rag << 'EOF'
#!/bin/bash
# Project-specific Claude RAG wrapper
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
TOOLKIT_PATH="${CLAUDE_RAG_TOOLKIT_PATH:-/home/user/REPOS/claude-rag-toolkit}"

export PYTHONPATH="$TOOLKIT_PATH/src:$PYTHONPATH"
cd "$SCRIPT_DIR"

python3 "$TOOLKIT_PATH/src/integrations/cli_interface.py" "$@"
EOF

chmod +x claude-rag

# Clean up old system (optional)
echo ""
read -p "🗑️ Remove old .claude/ directory? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    rm -rf ".claude"
    echo "✅ Old .claude/ directory removed"
    echo "📁 Backup still available at .claude-backup/"
else
    echo "⚠️ Old .claude/ directory preserved alongside new system"
fi

echo ""
echo "✅ Migration complete!"
echo ""
echo "📋 What changed:"
echo "  • Old location: .claude/"
echo "  • New location: .claude-rag/"
echo "  • New CLI: ./claude-rag <command>"
echo "  • Improved multi-repo support"
echo "  • Better project type detection"
echo ""
echo "🔧 Test the new system:"
echo "  ./claude-rag stats"
echo "  ./claude-rag search 'your topic'"