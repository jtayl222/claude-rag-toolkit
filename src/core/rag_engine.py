#!/usr/bin/env python3
"""
Multi-Repository RAG Engine for Claude Code
Core engine that adapts to different project types and provides intelligent search.
"""

import os
import json
import hashlib
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any
from collections import defaultdict
import subprocess

# Handle both relative and absolute imports
try:
    from utils.repo_detector import RepositoryDetector
except ImportError:
    from ..utils.repo_detector import RepositoryDetector


class MultiRepoRAGEngine:
    """
    Core RAG engine that adapts to different repository types.
    Provides project-aware indexing and intelligent search capabilities.
    """
    
    def __init__(self, project_root: str = ".", config_file: str = None):
        self.project_root = Path(project_root).resolve()
        self.rag_dir = self.project_root / ".claude-rag"
        self.config_file = config_file or self.rag_dir / "config.json"
        self.index_file = self.rag_dir / "index.json"
        self.cache_file = self.rag_dir / "cache.json"
        
        # Initialize repository detector first (needed for config creation)
        self.repo_detector = RepositoryDetector(project_root)
        
        # Load or create configuration
        self.config = self._load_or_create_config()
        self.index = self._load_or_create_index()
    
    def _load_or_create_config(self) -> Dict:
        """Load existing config or create new one with auto-detection."""
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                return json.load(f)
        
        # Auto-detect repository type and create config
        print("🔍 Auto-detecting repository type...")
        repo_type, confidence, analysis = self.repo_detector.detect_repository_type()
        print(f"📋 Detected: {repo_type} (confidence: {confidence:.2f})")
        
        config = self.repo_detector.generate_config(repo_type)
        
        # Save config
        self.rag_dir.mkdir(exist_ok=True)
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        # Create .gitignore for generated files
        gitignore_path = self.rag_dir / ".gitignore"
        with open(gitignore_path, 'w') as f:
            f.write("index.json\ncache.json\n*.log\n")
        
        return config
    
    def _load_or_create_index(self) -> Dict:
        """Load existing index or create new one."""
        if self.index_file.exists():
            try:
                with open(self.index_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                pass
        
        return {
            "version": "2.0",
            "repo_type": self.config.get("repo_type", "unknown"),
            "created": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "documents": {},
            "knowledge_graph": {},
            "command_index": {},
            "error_solutions": {},
            "cross_references": {},
            "project_stats": {}
        }
    
    def compute_file_hash(self, filepath: Path) -> str:
        """Compute hash for change detection."""
        try:
            return hashlib.md5(filepath.read_bytes()).hexdigest()
        except:
            return "error"
    
    def should_index_file(self, filepath: Path) -> bool:
        """Determine if file should be indexed based on configuration."""
        relative_path = str(filepath.relative_to(self.project_root))
        
        # Check exclude paths
        for exclude in self.config.get("exclude_paths", []):
            if exclude in relative_path:
                return False
        
        # Check file patterns
        for pattern in self.config.get("file_patterns", ["*.md"]):
            if filepath.match(pattern) or any(filepath.glob(pattern)):
                return True
        
        return False
    
    def extract_knowledge(self, content: str, filepath: str) -> Dict:
        """Extract knowledge adapted to repository type."""
        knowledge = {
            "concepts": [],
            "commands": [],
            "configurations": [],
            "troubleshooting": [],
            "dependencies": [],
            "cross_references": [],
            "api_endpoints": [],
            "functions": []
        }
        
        lines = content.split('\n')
        repo_type = self.config.get("repo_type", "documentation")
        
        # Repository-specific extraction
        if repo_type == "mlops-platform":
            knowledge.update(self._extract_mlops_knowledge(lines, filepath))
        elif repo_type == "ml-model":
            knowledge.update(self._extract_ml_model_knowledge(lines, filepath))
        elif repo_type == "web-app":
            knowledge.update(self._extract_webapp_knowledge(lines, filepath))
        
        # Common extraction patterns
        knowledge.update(self._extract_common_knowledge(lines, filepath))
        
        return knowledge
    
    def _extract_mlops_knowledge(self, lines: List[str], filepath: str) -> Dict:
        """Extract MLOps-specific knowledge patterns."""
        knowledge = {
            "ansible_tasks": [],
            "kubernetes_resources": [],
            "service_endpoints": [],
            "network_policies": []
        }
        
        in_task = False
        current_task = None
        
        for i, line in enumerate(lines):
            # Ansible task detection
            if line.strip().startswith("- name:"):
                task_name = line.split("- name:", 1)[1].strip()
                knowledge["ansible_tasks"].append({
                    "name": task_name,
                    "line": i,
                    "file": filepath
                })
            
            # Kubernetes resource detection
            if line.strip().startswith("apiVersion:") or line.strip().startswith("kind:"):
                knowledge["kubernetes_resources"].append({
                    "line": i,
                    "content": line.strip(),
                    "file": filepath
                })
            
            # Service endpoint detection
            if "loadbalancer_ip" in line.lower() or "nodeport" in line.lower():
                knowledge["service_endpoints"].append({
                    "line": i,
                    "content": line.strip(),
                    "file": filepath
                })
        
        return knowledge
    
    def _extract_ml_model_knowledge(self, lines: List[str], filepath: str) -> Dict:
        """Extract ML model-specific knowledge patterns."""
        knowledge = {
            "model_configs": [],
            "training_scripts": [],
            "api_endpoints": [],
            "data_schemas": []
        }
        
        for i, line in enumerate(lines):
            # Python function definitions
            if line.strip().startswith("def ") and any(keyword in line.lower() for keyword in ["train", "predict", "model", "feature"]):
                knowledge["functions"].append({
                    "name": line.strip(),
                    "line": i,
                    "file": filepath,
                    "type": "ml_function"
                })
            
            # API endpoint detection
            if "@app.route" in line or "@api.route" in line:
                knowledge["api_endpoints"].append({
                    "endpoint": line.strip(),
                    "line": i,
                    "file": filepath
                })
            
            # Model configuration
            if any(keyword in line.lower() for keyword in ["model_config", "hyperparameters", "training_config"]):
                knowledge["model_configs"].append({
                    "line": i,
                    "content": line.strip(),
                    "file": filepath
                })
        
        return knowledge
    
    def _extract_webapp_knowledge(self, lines: List[str], filepath: str) -> Dict:
        """Extract web application-specific knowledge patterns."""
        knowledge = {
            "components": [],
            "api_routes": [],
            "configurations": []
        }
        
        for i, line in enumerate(lines):
            # React/Vue component detection
            if "export default" in line and any(keyword in line for keyword in ["Component", "function", "const"]):
                knowledge["components"].append({
                    "name": line.strip(),
                    "line": i,
                    "file": filepath
                })
            
            # API route detection
            if any(method in line for method in ["app.get", "app.post", "router.get", "router.post"]):
                knowledge["api_routes"].append({
                    "route": line.strip(),
                    "line": i,
                    "file": filepath
                })
        
        return knowledge
    
    def _extract_common_knowledge(self, lines: List[str], filepath: str) -> Dict:
        """Extract common patterns across all repository types."""
        knowledge = {
            "concepts": [],
            "commands": [],
            "troubleshooting": [],
            "cross_references": []
        }
        
        in_code_block = False
        code_block_lang = None
        
        for i, line in enumerate(lines):
            # Code block detection
            if line.startswith('```'):
                if not in_code_block:
                    in_code_block = True
                    code_block_lang = line[3:].strip()
                else:
                    in_code_block = False
                continue
            
            if in_code_block and code_block_lang in ['bash', 'shell', 'sh']:
                # Extract commands
                if line.strip() and not line.strip().startswith('#'):
                    knowledge["commands"].append({
                        "command": line.strip(),
                        "file": filepath,
                        "line": i,
                        "type": self._classify_command(line.strip())
                    })
                continue
            
            # Header detection (concepts)
            if line.startswith('#'):
                level = len(line) - len(line.lstrip('#'))
                concept = line.strip('#').strip()
                knowledge["concepts"].append({
                    "name": concept,
                    "level": level,
                    "line": i,
                    "file": filepath
                })
            
            # Troubleshooting detection
            if any(word in line.lower() for word in ['error', 'failed', 'issue', 'problem', 'fix', 'solution']):
                knowledge["troubleshooting"].append({
                    "line": i,
                    "content": line.strip(),
                    "type": self._classify_troubleshooting(line),
                    "file": filepath
                })
            
            # Cross-reference detection
            if '.md' in line or '.yml' in line or 'see' in line.lower():
                refs = self._extract_references(line, filepath)
                knowledge["cross_references"].extend(refs)
        
        return knowledge
    
    def _classify_command(self, command: str) -> str:
        """Classify command type based on content."""
        cmd_lower = command.lower()
        if 'kubectl' in cmd_lower:
            return 'kubernetes'
        elif 'docker' in cmd_lower:
            return 'docker'
        elif 'ansible' in cmd_lower:
            return 'ansible'
        elif 'git' in cmd_lower:
            return 'git'
        elif 'python' in cmd_lower or 'pip' in cmd_lower:
            return 'python'
        else:
            return 'shell'
    
    def _classify_troubleshooting(self, line: str) -> str:
        """Classify troubleshooting entry type."""
        line_lower = line.lower()
        if 'error' in line_lower or 'failed' in line_lower:
            return 'error'
        elif 'fix' in line_lower or 'solution' in line_lower:
            return 'solution'
        else:
            return 'issue'
    
    def _extract_references(self, line: str, current_file: str) -> List[Dict]:
        """Extract file references from line."""
        refs = []
        patterns = [
            r'([a-zA-Z0-9_\-/.]+\.md)',
            r'([a-zA-Z0-9_\-/.]+\.ya?ml)',
            r'([a-zA-Z0-9_\-/.]+\.sh)',
            r'([a-zA-Z0-9_\-/.]+\.py)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, line)
            for match in matches:
                refs.append({
                    "target_file": match,
                    "source_file": current_file,
                    "context": line.strip(),
                    "type": "file_reference"
                })
        
        return refs
    
    def index_project(self, force_reindex: bool = False) -> Dict:
        """Index the entire project with repository-specific optimizations."""
        print(f"🔍 Indexing {self.config.get('repo_type', 'unknown')} repository...")
        
        # Find files to index
        files_to_index = []
        for pattern in self.config.get("file_patterns", ["*.md"]):
            files_to_index.extend(self.project_root.rglob(pattern))
        
        # Filter by exclusions
        files_to_index = [
            f for f in files_to_index 
            if self.should_index_file(f)
        ]
        
        print(f"📚 Found {len(files_to_index)} files to index")
        
        indexed_count = 0
        for filepath in files_to_index:
            try:
                relative_path = str(filepath.relative_to(self.project_root))
                content = filepath.read_text(encoding='utf-8', errors='ignore')
                file_hash = self.compute_file_hash(filepath)
                
                # Skip if already indexed and unchanged
                if not force_reindex and relative_path in self.index["documents"]:
                    if self.index["documents"][relative_path].get("hash") == file_hash:
                        continue
                
                print(f"  📄 {relative_path}")
                
                # Extract knowledge
                knowledge = self.extract_knowledge(content, relative_path)
                
                # Store in index
                self.index["documents"][relative_path] = {
                    "hash": file_hash,
                    "size": len(content),
                    "lines": content.count('\n'),
                    "last_indexed": datetime.now().isoformat(),
                    "knowledge": knowledge
                }
                
                indexed_count += 1
                
            except Exception as e:
                print(f"  ❌ Error indexing {filepath}: {e}")
        
        # Build knowledge graph and cross-references
        self._build_knowledge_graph()
        self._build_command_index()
        
        # Update index metadata
        self.index["last_updated"] = datetime.now().isoformat()
        self.index["project_stats"] = self._compute_project_stats()
        
        # Save index
        self._save_index()
        
        print(f"✅ Indexed {indexed_count} files")
        self._print_stats()
        
        return {
            "indexed_files": indexed_count,
            "total_files": len(files_to_index),
            "repo_type": self.config.get("repo_type")
        }
    
    def _build_knowledge_graph(self):
        """Build relationships between concepts and files."""
        graph = defaultdict(list)
        
        # Build concept relationships
        for doc_path, doc_info in self.index["documents"].items():
            knowledge = doc_info.get("knowledge", {})
            
            for concept in knowledge.get("concepts", []):
                concept_name = concept["name"].lower()
                
                # Link to commands
                for cmd in knowledge.get("commands", []):
                    if any(word in cmd["command"].lower() for word in concept_name.split()):
                        graph[concept_name].append({
                            "type": "command",
                            "file": doc_path,
                            "line": cmd["line"],
                            "content": cmd["command"]
                        })
                
                # Link to configurations
                for config in knowledge.get("configurations", []):
                    if concept_name in config.get("content", "").lower():
                        graph[concept_name].append({
                            "type": "configuration",
                            "file": doc_path,
                            "line": config["line"],
                            "content": config["content"]
                        })
        
        self.index["knowledge_graph"] = dict(graph)
    
    def _build_command_index(self):
        """Build searchable command index."""
        commands = defaultdict(list)
        
        for doc_path, doc_info in self.index["documents"].items():
            knowledge = doc_info.get("knowledge", {})
            
            for cmd in knowledge.get("commands", []):
                cmd_type = cmd.get("type", "shell")
                commands[cmd_type].append({
                    "command": cmd["command"],
                    "file": doc_path,
                    "line": cmd["line"]
                })
        
        self.index["command_index"] = dict(commands)
    
    def _compute_project_stats(self) -> Dict:
        """Compute project statistics."""
        total_docs = len(self.index["documents"])
        total_commands = sum(
            len(doc.get("knowledge", {}).get("commands", [])) 
            for doc in self.index["documents"].values()
        )
        total_concepts = sum(
            len(doc.get("knowledge", {}).get("concepts", [])) 
            for doc in self.index["documents"].values()
        )
        
        return {
            "total_documents": total_docs,
            "total_commands": total_commands,
            "total_concepts": total_concepts,
            "repo_type": self.config.get("repo_type"),
            "last_updated": datetime.now().isoformat()
        }
    
    def _save_index(self):
        """Save index to disk."""
        self.rag_dir.mkdir(exist_ok=True)
        with open(self.index_file, 'w') as f:
            json.dump(self.index, f, indent=2)
    
    def _print_stats(self):
        """Print indexing statistics."""
        stats = self.index.get("project_stats", {})
        print(f"""
📊 Indexing Complete:
  Repository Type: {stats.get('repo_type', 'unknown')}
  Documents: {stats.get('total_documents', 0)}
  Commands: {stats.get('total_commands', 0)}
  Concepts: {stats.get('total_concepts', 0)}
  Knowledge Graph Nodes: {len(self.index.get('knowledge_graph', {}))}
        """)
    
    def search(self, query: str, limit: int = 10) -> Dict[str, List[Dict]]:
        """Search across all indexed knowledge."""
        results = {
            'concept_matches': [],
            'command_matches': [],
            'configuration_matches': [],
            'troubleshooting_matches': []
        }
        query_lower = query.lower()
        
        for doc_path, doc_info in self.index["documents"].items():
            knowledge = doc_info.get("knowledge", {})
            
            # Search concepts
            for concept in knowledge.get("concepts", []):
                if query_lower in concept["name"].lower():
                    results['concept_matches'].append({
                        "file": doc_path,
                        "line": concept.get("line", "?"),
                        "concept": concept["name"],
                        "score": 10
                    })
            
            # Search commands
            for cmd in knowledge.get("commands", []):
                if query_lower in cmd["command"].lower():
                    results['command_matches'].append({
                        "file": doc_path,
                        "line": cmd.get("line", "?"),
                        "command": cmd["command"],
                        "type": cmd.get("type", "shell"),
                        "score": 5
                    })
            
            # Search configurations
            for config in knowledge.get("configurations", []):
                if query_lower in config.get("content", "").lower():
                    results['configuration_matches'].append({
                        "file": doc_path,
                        "line": config.get("line", "?"),
                        "content": config.get("content", ""),
                        "score": 3
                    })
            
            # Search troubleshooting
            for trouble in knowledge.get("troubleshooting", []):
                if query_lower in trouble.get("content", "").lower():
                    results['troubleshooting_matches'].append({
                        "file": doc_path,
                        "line": trouble.get("line", "?"),
                        "content": trouble.get("content", ""),
                        "type": trouble.get("type", "issue"),
                        "score": 3
                    })
        
        # Sort and limit each category
        for category in results:
            results[category].sort(key=lambda x: x["score"], reverse=True)
            results[category] = results[category][:limit]
        
        return results
    
    def get_file_context(self, filepath: str) -> Dict:
        """Get context and relationships for a specific file."""
        if filepath not in self.index["documents"]:
            return {"error": f"File not indexed: {filepath}"}
        
        doc = self.index["documents"][filepath]
        knowledge = doc.get("knowledge", {})
        
        # Find related files
        related_files = set()
        for ref in knowledge.get("cross_references", []):
            target = ref.get("target_file", "")
            if target and target != filepath:
                related_files.add(target)
        
        # Find files that reference this one
        for other_path, other_doc in self.index["documents"].items():
            if other_path == filepath:
                continue
            other_refs = other_doc.get("knowledge", {}).get("cross_references", [])
            for ref in other_refs:
                if ref.get("target_file") == filepath:
                    related_files.add(other_path)
        
        return {
            "file_info": {
                "size": doc.get("size", 0),
                "lines": doc.get("lines", 0),
                "type": self._classify_file_type(filepath),
                "last_indexed": doc.get("last_indexed", "unknown")
            },
            "concepts": knowledge.get("concepts", []),
            "commands": knowledge.get("commands", []),
            "configurations": knowledge.get("configurations", []),
            "troubleshooting": knowledge.get("troubleshooting", []),
            "related_files": list(related_files)
        }
    
    def _classify_file_type(self, filepath: str) -> str:
        """Classify file type based on extension."""
        path = Path(filepath)
        extension = path.suffix.lower()
        
        type_mapping = {
            '.md': 'markdown',
            '.py': 'python',
            '.yml': 'yaml',
            '.yaml': 'yaml', 
            '.sh': 'shell',
            '.js': 'javascript',
            '.json': 'json',
            '.txt': 'text',
            '.ipynb': 'jupyter_notebook'
        }
        
        return type_mapping.get(extension, 'unknown')