# Claude RAG Toolkit - Quick Reference

## Activation
```bash
cd /home/user/REPOS/claude-rag-toolkit
source venv/bin/activate
```

## Core Commands
```bash
claude-rag init                    # Initialize in any project
claude-rag search "query"          # Search documentation  
claude-rag troubleshoot "error"    # Find error solutions
claude-rag context "filepath"      # Get file relationships
claude-rag commands kubectl        # Find tech-specific commands
claude-rag stats                   # Show index statistics
claude-rag reindex                 # Rebuild index
```

## Adaptive Search Strategy
```bash
# ✅ GOOD: Start broad, then narrow
claude-rag search "prerequisites"     # 19 results
claude-rag search "kubeadm"          # 18 results  
claude-rag search "safety check"     # Specific context

# ❌ AVOID: Too specific initially  
claude-rag search "kubeadm prerequisites validation"  # 0 results
```

## Documentation Gap Detection
```bash
# Few results = needs documentation!
claude-rag search "new feature"      # 0-2 results → document it
claude-rag search "integration"      # Check existing patterns
```

## Commit Workflow Integration
```bash
# Analyze changes
git diff --name-only | while read f; do
  claude-rag search "$(basename $(dirname $f))"
done

# Validate completeness
claude-rag search "component config defaults"
claude-rag search "old_value_being_changed"

# Check documentation needs
claude-rag search "new_functionality"  # Low hits = add docs
```

## Result Count Guidelines
- **0 results**: Broaden search terms OR document new functionality
- **1-10 results**: Good specificity, use these results
- **>10 results**: Narrow with more specific terms or use `--limit`

## Project Types Auto-Detected
- `mlops-platform`: Ansible + Kubernetes + MLOps tools
- `ml-model`: Python ML projects with models/training
- `kubernetes`: K8s manifests and Helm charts
- `ansible`: Playbooks and roles
- `python`: General Python projects
- `documentation`: Docs-focused repositories

## Quick Troubleshooting
```bash
claude-rag reindex                    # Fix missing results
claude-rag stats                      # Check index health
claude-rag --help                     # Command reference
```