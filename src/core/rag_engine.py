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
    from utils.embedding_provider import EmbeddingProvider
except ImportError:
    from ..utils.repo_detector import RepositoryDetector
    from ..utils.embedding_provider import EmbeddingProvider


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
        
        # Initialize embedding provider for semantic search
        self.embedding_provider = EmbeddingProvider(project_root)
        
        # Track if semantic search is enabled
        self.semantic_search_enabled = self.config.get("semantic_search", {}).get("enabled", True)
    
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
        
        # Check file patterns - support both simple and complex patterns
        for pattern in self.config.get("file_patterns", ["*.md"]):
            # Simple pattern like *.yml
            if '*' in pattern and '/' not in pattern:
                if filepath.match(pattern):
                    return True
            # Complex pattern like roles/**/*.yml or inventory/**/*.yml
            elif '**' in pattern:
                import fnmatch
                if fnmatch.fnmatch(relative_path, pattern):
                    return True
            # Exact match
            elif relative_path == pattern:
                return True
            # Simple suffix match
            elif pattern.startswith('*.'):
                if filepath.suffix == pattern[1:]:
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
            "network_policies": [],
            "storage_configs": [],
            "harbor_configs": [],
            "variables": []
        }
        
        in_task = False
        current_task = None
        
        for i, line in enumerate(lines):
            line_lower = line.lower()
            
            # Ansible task detection
            if line.strip().startswith("- name:"):
                task_name = line.split("- name:", 1)[1].strip()
                knowledge["ansible_tasks"].append({
                    "name": task_name,
                    "line": i,
                    "file": filepath,
                    "type": "ansible_task"
                })
            
            # Kubernetes resource detection
            if line.strip().startswith("apiVersion:") or line.strip().startswith("kind:"):
                knowledge["kubernetes_resources"].append({
                    "line": i,
                    "content": line.strip(),
                    "file": filepath,
                    "type": "k8s_resource"
                })
            
            # Storage and persistence detection
            if any(keyword in line_lower for keyword in ['persistentvolumeclaim', 'pvc', 'storage:', 'storageclass', 'volumeclaim', 'persistent']):
                knowledge["storage_configs"].append({
                    "line": i,
                    "content": line.strip(),
                    "file": filepath,
                    "type": "storage_config",
                    "keywords": [kw for kw in ['persistentvolumeclaim', 'pvc', 'storage', 'storageclass', 'volumeclaim', 'persistent'] if kw in line_lower]
                })
            
            # Harbor-specific configurations
            if any(keyword in line_lower for keyword in ['harbor', 'registry', 'docker_registry', 'container_registry']):
                knowledge["harbor_configs"].append({
                    "line": i,
                    "content": line.strip(),
                    "file": filepath,
                    "type": "harbor_config"
                })
            
            # Ansible variables detection (including Jinja2 templates)
            if '{{' in line and '}}' in line:
                import re
                variables = re.findall(r'{{\s*([^}]+)\s*}}', line)
                for var in variables:
                    knowledge["variables"].append({
                        "variable": var.strip(),
                        "line": i,
                        "file": filepath,
                        "context": line.strip(),
                        "type": "jinja2_variable"
                    })
            
            # Service endpoint detection
            if "loadbalancer_ip" in line_lower or "nodeport" in line_lower:
                knowledge["service_endpoints"].append({
                    "line": i,
                    "content": line.strip(),
                    "file": filepath,
                    "type": "service_endpoint"
                })
        
        return knowledge
    
    def _extract_ml_model_knowledge(self, lines: List[str], filepath: str) -> Dict:
        """Extract ML model-specific knowledge patterns."""
        knowledge = {
            "model_configs": [],
            "training_scripts": [],
            "api_endpoints": [],
            "data_schemas": [],
            "functions": []
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
    
    def _expand_search_terms(self, query: str) -> List[str]:
        """Expand search terms with synonyms for better matching."""
        # MLOps/Infrastructure synonyms
        synonyms = {
            'persistence': ['persistent', 'pvc', 'persistentvolumeclaim', 'storage', 'volume'],
            'storage': ['persistent', 'pvc', 'persistentvolumeclaim', 'persistence', 'volume'],
            'harbor': ['registry', 'docker_registry', 'container_registry', 'image_registry'],
            'registry': ['harbor', 'docker_registry', 'container_registry'],
            'loadbalancer': ['lb', 'load_balancer', 'metallb', 'service'],
            'kubernetes': ['k8s', 'kubectl', 'kube'],
            'ansible': ['playbook', 'role', 'task'],
            'monitoring': ['prometheus', 'grafana', 'metrics', 'observability'],
            'security': ['tls', 'ssl', 'certificate', 'cert', 'secret'],
            'deployment': ['deploy', 'rollout', 'install', 'setup']
        }
        
        query_terms = query.lower().split()
        expanded_terms = set(query_terms)
        
        for term in query_terms:
            if term in synonyms:
                expanded_terms.update(synonyms[term])
            # Also check if term is a synonym of something
            for key, values in synonyms.items():
                if term in values:
                    expanded_terms.add(key)
                    expanded_terms.update(values)
        
        return list(expanded_terms)
    
    def _create_searchable_text(self, knowledge: Dict) -> str:
        """Create searchable text from extracted knowledge for semantic search."""
        text_parts = []
        
        # Add concepts
        for concept in knowledge.get("concepts", []):
            text_parts.append(concept.get("name", ""))
        
        # Add command text
        for cmd in knowledge.get("commands", []):
            text_parts.append(cmd.get("command", ""))
        
        # Add configuration content
        for config in knowledge.get("configurations", []):
            text_parts.append(config.get("content", ""))
        
        # Add troubleshooting content
        for trouble in knowledge.get("troubleshooting", []):
            text_parts.append(trouble.get("content", ""))
        
        # Add MLOps-specific content
        for task in knowledge.get("ansible_tasks", []):
            text_parts.append(task.get("name", ""))
        
        for storage in knowledge.get("storage_configs", []):
            text_parts.append(storage.get("content", ""))
        
        for harbor in knowledge.get("harbor_configs", []):
            text_parts.append(harbor.get("content", ""))
        
        # Add ML model-specific content
        for func in knowledge.get("functions", []):
            text_parts.append(func.get("name", ""))
        
        # Filter out empty strings and join
        filtered_parts = [part for part in text_parts if part.strip()]
        return " ".join(filtered_parts)
    
    def _extract_pdf_knowledge(self, filepath: Path, relative_path: str) -> Dict:
        """Extract knowledge from PDF files using text extraction."""
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
        
        try:
            pdf_text = ""
            
            # Try pdfplumber first (better for complex layouts)
            try:
                import pdfplumber
                with pdfplumber.open(filepath) as pdf:
                    for page in pdf.pages:
                        if page.extract_text():
                            pdf_text += page.extract_text() + "\n"
                print(f"  📑 Extracted text using pdfplumber")
                
            except ImportError:
                # Fall back to PyPDF2
                try:
                    import PyPDF2
                    with open(filepath, 'rb') as file:
                        reader = PyPDF2.PdfReader(file)
                        for page in reader.pages:
                            pdf_text += page.extract_text() + "\n"
                    print(f"  📑 Extracted text using PyPDF2")
                    
                except ImportError:
                    # Basic metadata extraction only
                    print(f"  ⚠️  No PDF libraries available, indexing metadata only")
                    knowledge["concepts"].append({
                        "name": f"PDF Document: {filepath.stem}",
                        "line": 1,
                        "type": "document",
                        "metadata": {
                            "filename": filepath.name,
                            "size": filepath.stat().st_size,
                            "path": relative_path
                        }
                    })
                    return knowledge
            
            # If we extracted text, process it like any other document
            if pdf_text.strip():
                # Parse the extracted text as if it were a regular text document
                lines = pdf_text.split('\n')
                text_knowledge = self.extract_knowledge(pdf_text, relative_path)
                
                # Merge the extracted knowledge
                for key, value in text_knowledge.items():
                    if isinstance(value, list):
                        knowledge[key].extend(value)
                
                # Add PDF-specific metadata
                knowledge["concepts"].append({
                    "name": f"PDF Document: {filepath.stem}",
                    "line": 1,
                    "type": "pdf_document",
                    "metadata": {
                        "filename": filepath.name,
                        "size": filepath.stat().st_size,
                        "pages": len(pdf_text.split('\f')) if '\f' in pdf_text else 1,
                        "path": relative_path,
                        "text_length": len(pdf_text)
                    }
                })
            
        except Exception as e:
            print(f"  ⚠️  Warning: Could not process PDF {relative_path}: {e}")
            # Still index basic metadata
            knowledge["concepts"].append({
                "name": f"PDF Document: {filepath.stem}",
                "line": 1,
                "type": "pdf_error",
                "metadata": {
                    "filename": filepath.name,
                    "error": str(e),
                    "path": relative_path
                }
            })
        
        return knowledge
    
    def index_project(self, force_reindex: bool = False, verbose: bool = False) -> Dict:
        """Index the entire project with repository-specific optimizations."""
        print(f"🔍 Indexing {self.config.get('repo_type', 'unknown')} repository...")
        
        # Find files to index - handle both simple and complex patterns
        files_to_index = []
        for pattern in self.config.get("file_patterns", ["*.md"]):
            # Simple pattern like *.yml or *.md
            if '*' in pattern and '/' not in pattern:
                files_to_index.extend(self.project_root.rglob(pattern))
            # Complex pattern with directory structure like roles/**/*.yml
            elif '**' in pattern:
                # Extract the base pattern for rglob
                # roles/**/*.yml -> *.yml for rglob, then filter with full pattern
                base_pattern = pattern.split('/')[-1] if '/' in pattern else pattern
                for f in self.project_root.rglob(base_pattern):
                    if self.should_index_file(f):
                        files_to_index.append(f)
            # Specific file pattern
            else:
                specific_file = self.project_root / pattern
                if specific_file.exists():
                    files_to_index.append(specific_file)
        
        # Remove duplicates and filter by exclusions
        files_to_index = list(set(files_to_index))
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
                
                # Handle PDF files differently
                if filepath.suffix.lower() == '.pdf':
                    knowledge = self._extract_pdf_knowledge(filepath, relative_path)
                else:
                    knowledge = self.extract_knowledge(content, relative_path)
                
                # Store in index
                self.index["documents"][relative_path] = {
                    "hash": file_hash,
                    "size": len(content),
                    "lines": content.count('\n'),
                    "last_indexed": datetime.now().isoformat(),
                    "knowledge": knowledge
                }
                
                # Compute and cache document embedding for semantic search
                if self.semantic_search_enabled and self.embedding_provider.is_available():
                    doc_embedding = self.embedding_provider.get_document_embedding(relative_path, content)
                    if doc_embedding is not None:
                        print(f"  🧠 Computed embedding for semantic search")
                
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
        
        # Save embedding cache if semantic search was used
        if self.semantic_search_enabled and self.embedding_provider.is_available():
            self.embedding_provider.save_cache()
            print(f"💾 Saved embedding cache")
        
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
    
    def search(self, query: str, limit: int = 10, use_semantic: bool = None) -> Dict[str, List[Dict]]:
        """Search across all indexed knowledge with hybrid exact + semantic matching."""
        results = {
            'concept_matches': [],
            'command_matches': [],
            'configuration_matches': [],
            'troubleshooting_matches': [],
            'semantic_matches': []
        }
        
        # Determine if we should use semantic search
        if use_semantic is None:
            use_semantic = self.semantic_search_enabled and self.embedding_provider.is_available()
        
        # Expand query with synonyms for better matching
        expanded_queries = self._expand_search_terms(query)
        query_lower = query.lower()
        
        # Semantic search component
        semantic_scores = {}
        if use_semantic:
            document_texts = {}
            for doc_path, doc_info in self.index["documents"].items():
                # Create searchable text from document
                searchable_text = self._create_searchable_text(doc_info.get("knowledge", {}))
                if searchable_text:
                    document_texts[doc_path] = searchable_text
            
            if document_texts:
                semantic_results = self.embedding_provider.find_similar_documents(
                    query, 
                    document_texts, 
                    top_k=limit * 2,  # Get more candidates for filtering
                    similarity_threshold=self.config.get("semantic_search", {}).get("similarity_threshold", 0.3)
                )
                
                # Convert to scores dict and add to results
                for doc_path, similarity in semantic_results:
                    semantic_scores[doc_path] = similarity
                    results['semantic_matches'].append({
                        "file": doc_path,
                        "similarity": similarity,
                        "score": int(similarity * 10)  # Convert to integer score
                    })
        
        for doc_path, doc_info in self.index["documents"].items():
            knowledge = doc_info.get("knowledge", {})
            
            # Helper function for enhanced matching
            def matches_query(text):
                text_lower = text.lower()
                return any(term in text_lower for term in expanded_queries)
            
            # Calculate base score boost from semantic similarity
            semantic_boost = int(semantic_scores.get(doc_path, 0) * 5)  # 0-5 boost
            
            # Search concepts with semantic matching
            for concept in knowledge.get("concepts", []):
                concept_text = concept["name"].lower()
                if query_lower in concept_text or matches_query(concept["name"]):
                    score = 10 if query_lower in concept_text else 5  # Exact match gets higher score
                    score += semantic_boost  # Add semantic similarity boost
                    results['concept_matches'].append({
                        "file": doc_path,
                        "line": concept.get("line", "?"),
                        "concept": concept["name"],
                        "score": score
                    })
            
            # Search commands
            for cmd in knowledge.get("commands", []):
                if query_lower in cmd["command"].lower():
                    score = 5 + semantic_boost
                    results['command_matches'].append({
                        "file": doc_path,
                        "line": cmd.get("line", "?"),
                        "command": cmd["command"],
                        "type": cmd.get("type", "shell"),
                        "score": score
                    })
            
            # Search configurations
            for config in knowledge.get("configurations", []):
                if query_lower in config.get("content", "").lower():
                    score = 3 + semantic_boost
                    results['configuration_matches'].append({
                        "file": doc_path,
                        "line": config.get("line", "?"),
                        "content": config.get("content", ""),
                        "score": score
                    })
            
            # Search troubleshooting
            for trouble in knowledge.get("troubleshooting", []):
                if query_lower in trouble.get("content", "").lower():
                    score = 3 + semantic_boost
                    results['troubleshooting_matches'].append({
                        "file": doc_path,
                        "line": trouble.get("line", "?"),
                        "content": trouble.get("content", ""),
                        "type": trouble.get("type", "issue"),
                        "score": score
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