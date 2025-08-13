# Claude RAG Toolkit Usage Instructions

## For Claude Sessions Working in This Directory

When Claude is running in `/home/user/REPOS/claude-rag-toolkit`, use this toolkit to enhance development workflows with intelligent documentation search.

## Activation

```bash
# Activate the virtual environment
source venv/bin/activate

# Verify installation
claude-rag --help
```

## Core Search Strategies

### Adaptive Search Pattern
Based on our analysis, always use **progressive search refinement**:

```bash
# 1. Start with specific terms
claude-rag search "component specific feature"

# 2. Check result count and adapt:
# - 0 results: Broaden terms
# - 1-10 results: Good specificity, use results
# - >10 results: Add more specific terms
```

### Example: Component Analysis
```bash
# Too specific initially (may return 0)
claude-rag search "kubeadm prerequisites validation"  # ❌ 0 results

# Better: Start broad, then refine
claude-rag search "prerequisites"                    # ✅ 19 results!
claude-rag search "kubeadm"                         # ✅ 18 results
claude-rag search "safety validation"               # Find specific context
```

### Documentation Gap Detection
**Key Insight**: Few/no RAG results for new functionality indicates documentation needs:

```bash
# New feature with no results = document it!
claude-rag search "seldon harbor integration"       # 0 results → needs docs
claude-rag search "seldon custom images"           # 0 results → needs docs
claude-rag search "seldon custom"                  # 2 results → some coverage
```

## Commit Workflow Enhancement

### RAG-Powered Commit Analysis
When analyzing changes for commits:

1. **Context Analysis**
```bash
# For each changed file, understand its role
git diff --name-only | while read file; do
  component=$(basename $(dirname $file))
  filename=$(basename $file .yml .yaml .py .sh)
  
  claude-rag search "$component"
  claude-rag search "$filename"
  claude-rag context "$file"
done
```

2. **Dependency Detection**
```bash
# Find integration points and dependencies
claude-rag search "component1 component2 integration"
claude-rag search "defaults main.yml"
claude-rag search "tasks prerequisites"
```

3. **Completeness Validation**
```bash
# Check for missing related files
claude-rag search "component_name config"
claude-rag search "component_name defaults"
claude-rag search "component_name tasks"

# Verify no orphaned references
claude-rag search "old_value_being_changed"
```

## Project-Agnostic Usage

### Initialize in Any Project
```bash
cd /path/to/any/project
claude-rag init
```

The toolkit will:
- Auto-detect repository type (mlops-platform, ml-model, kubernetes, etc.)
- Generate appropriate configuration
- Index relevant file types
- Create searchable knowledge base

### Search Patterns by Project Type

**MLOps Platform:**
```bash
claude-rag search "ansible tasks"
claude-rag search "kubernetes resources"
claude-rag search "harbor registry"
claude-rag commands kubectl
```

**ML Model Project:**
```bash
claude-rag search "training pipeline"
claude-rag search "model deployment"
claude-rag search "inference endpoint"
claude-rag commands python
```

**General Documentation:**
```bash
claude-rag search "installation guide"
claude-rag search "troubleshooting"
claude-rag search "configuration example"
```

## Advanced Techniques

### Troubleshooting Workflow
```bash
# Find solutions for specific errors
claude-rag troubleshoot "port 6443 connection refused"
claude-rag troubleshoot "certificate authority"
claude-rag troubleshoot "network policy"
```

### File Relationship Analysis
```bash
# Understand file context and dependencies
claude-rag context "infrastructure/cluster/site.yml"
claude-rag context "roles/platform/seldon/defaults/main.yml"
```

### Command Discovery
```bash
# Find technology-specific commands
claude-rag commands kubectl
claude-rag commands ansible-playbook
claude-rag commands docker
```

## Integration with Commit Workflow

### Detect Documentation Needs
```bash
# If search returns 0-2 results for new functionality:
if [ "$(claude-rag search 'new_feature' | grep -o 'Total results: [0-9]*' | cut -d: -f2 | tr -d ' ')" -lt 3 ]; then
  echo "📝 Documentation needed for new_feature"
  echo "Consider updating README, CLAUDE.md, or creating docs/"
fi
```

### Validate Atomic Commits
```bash
# Before committing, verify completeness
claude-rag search "component being changed"
claude-rag search "configuration dependencies"
claude-rag search "integration requirements"
```

## Best Practices

### Search Strategy
1. **Start broad** - Use general terms that likely exist in docs
2. **Check result count** - Adapt search specificity based on hits
3. **Use project vocabulary** - Search with terms from your domain
4. **Multiple angles** - Try component names, actions, file types

### Documentation Strategy  
1. **Gap detection** - 0 results = needs documentation
2. **Context validation** - Use existing results to understand patterns
3. **Integration focus** - Document how components work together
4. **Examples matter** - Include configuration and usage examples

### Performance Tips
1. **Reindex after major changes**: `claude-rag reindex`
2. **Use specific categories**: `--category troubleshooting`
3. **Limit results appropriately**: `--limit 15` for commands
4. **Cache-friendly searches**: Consistent terminology improves speed

This toolkit transforms documentation from static files into an intelligent, searchable knowledge base that enhances every development workflow.