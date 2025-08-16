#!/usr/bin/env python3
"""
Repository Type Detection
Automatically determines the type of repository and appropriate RAG configuration.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class RepositoryDetector:
    """
    Detects repository type based on file structure, content, and patterns.
    Supports multiple project types with confidence scoring.
    """
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
    
    def detect_repository_type(self) -> Tuple[str, float, Dict]:
        """
        Detect repository type based on file patterns and structure.
        Returns (type, confidence, analysis).
        """
        detectors = [
            self._detect_mlops_platform,
            self._detect_ml_model,
            self._detect_kubernetes,
            self._detect_ansible,
            self._detect_python,
            self._detect_nodejs,
            self._detect_documentation
        ]
        
        results = []
        for detector in detectors:
            repo_type, confidence, evidence = detector()
            if confidence > 0:
                results.append((repo_type, confidence, evidence))
        
        if not results:
            return "generic", 0.0, {"evidence": [], "message": "No specific type detected"}
        
        # Sort by confidence and return highest
        results.sort(key=lambda x: x[1], reverse=True)
        best_match = results[0]
        
        analysis = {
            "evidence": best_match[2],
            "alternatives": results[1:3],  # Show alternatives
            "detection_details": {
                "total_indicators": len(best_match[2]),
                "confidence_breakdown": f"Based on {len(best_match[2])} indicators"
            }
        }
        
        return best_match[0], best_match[1], analysis

    def detect_repo_type(self) -> str:
        """Legacy method for backward compatibility."""
        repo_type, confidence, _ = self.detect_repository_type()
        print(f"🔍 Detected repository type: {repo_type} (confidence: {confidence:.2f})")
        return repo_type
    
    def _detect_mlops_platform(self) -> Tuple[str, float, List[str]]:
        """Detect MLOps platform repository (like ml-platform)."""
        evidence = []
        score = 0.0
        
        # Strong indicators
        strong_patterns = [
            "infrastructure/cluster/site.yml",
            "infrastructure/cluster/site-multiplatform.yml", 
            "infrastructure/cluster/roles/",
            "inventory/production/hosts",
            "scripts/bootstrap-*.sh"
        ]
        
        for pattern in strong_patterns:
            if self._path_exists(pattern):
                evidence.append(pattern)
                score += 0.3
        
        # MLOps-specific patterns
        mlops_patterns = [
            ("roles/mlops/", 0.25),
            ("roles/platform/seldon", 0.2),
            ("roles/platform/harbor", 0.2),
            ("roles/platform/istio", 0.2),
            ("roles/monitoring/prometheus", 0.15),
            ("values/", 0.1)
        ]
        
        for pattern, weight in mlops_patterns:
            if self._path_exists(pattern):
                evidence.append(pattern)
                score += weight
        
        # File content indicators
        if self._file_contains("CLAUDE.md", ["MLOps", "K3s", "Harbor", "Seldon"]):
            evidence.append("CLAUDE.md contains MLOps keywords")
            score += 0.2
        
        if self._file_contains("README.md", ["ansible-playbook", "infrastructure", "k3s"]):
            evidence.append("README.md contains infrastructure keywords")
            score += 0.15
        
        return "mlops-platform", min(score, 1.0), evidence
    
    def _detect_ml_model(self) -> Tuple[str, float, List[str]]:
        """Detect ML model/data science repository."""
        evidence = []
        score = 0.0
        
        # Python ML indicators
        ml_files = [
            ("requirements.txt", 0.1),
            ("setup.py", 0.1),
            ("pyproject.toml", 0.1),
            ("environment.yml", 0.15),
            ("Pipfile", 0.1)
        ]
        
        for filename, weight in ml_files:
            if self._path_exists(filename):
                evidence.append(filename)
                # Check for ML libraries
                if self._file_contains(filename, [
                    "sklearn", "pandas", "numpy", "tensorflow", "torch", 
                    "keras", "mlflow", "airflow", "jupyterlab"
                ]):
                    score += weight * 2
                    evidence.append(f"{filename} contains ML libraries")
                else:
                    score += weight
        
        # Directory structure
        ml_dirs = [
            ("models/", 0.2),
            ("notebooks/", 0.2),
            ("data/", 0.15),
            ("pipelines/", 0.15),
            ("experiments/", 0.1),
            ("src/", 0.1)
        ]
        
        for dirname, weight in ml_dirs:
            if self._path_exists(dirname):
                evidence.append(dirname)
                score += weight
        
        # Specific files
        ml_specific = [
            ("*.ipynb", 0.2),
            ("Dockerfile", 0.1),
            ("docker-compose.yml", 0.1)
        ]
        
        for pattern, weight in ml_specific:
            if self._has_files_matching(pattern):
                evidence.append(f"files matching {pattern}")
                score += weight
        
        # README content
        if self._file_contains("README.md", [
            "model", "machine learning", "ML", "training", "inference",
            "fraud", "prediction", "classification", "regression"
        ]):
            evidence.append("README.md contains ML keywords")
            score += 0.2
        
        return "ml-model", min(score, 1.0), evidence
    
    def _detect_kubernetes(self) -> Tuple[str, float, List[str]]:
        """Detect Kubernetes-focused repository."""
        evidence = []
        score = 0.0
        
        k8s_patterns = [
            ("k8s/", 0.3),
            ("kubernetes/", 0.3),
            ("manifests/", 0.2),
            ("charts/", 0.2),
            ("kustomize/", 0.2)
        ]
        
        for pattern, weight in k8s_patterns:
            if self._path_exists(pattern):
                evidence.append(pattern)
                score += weight
        
        # Helm charts
        if self._path_exists("Chart.yaml") or self._path_exists("values.yaml"):
            evidence.append("Helm chart files")
            score += 0.25
        
        # Kubernetes manifests
        if self._has_files_matching("*.yaml") or self._has_files_matching("*.yml"):
            yaml_files = list(self.project_root.rglob("*.yaml")) + list(self.project_root.rglob("*.yml"))
            k8s_keywords = ["apiVersion", "kind:", "metadata:", "spec:"]
            
            k8s_yaml_count = 0
            for yaml_file in yaml_files[:10]:  # Sample first 10
                try:
                    content = yaml_file.read_text()
                    if any(keyword in content for keyword in k8s_keywords):
                        k8s_yaml_count += 1
                except:
                    pass
            
            if k8s_yaml_count > 0:
                evidence.append(f"{k8s_yaml_count} Kubernetes YAML files")
                score += min(k8s_yaml_count * 0.1, 0.3)
        
        return "kubernetes", min(score, 1.0), evidence
    
    def _detect_ansible(self) -> Tuple[str, float, List[str]]:
        """Detect Ansible repository."""
        evidence = []
        score = 0.0
        
        ansible_patterns = [
            ("playbook.yml", 0.3),
            ("site.yml", 0.3),
            ("roles/", 0.25),
            ("inventory/", 0.2),
            ("group_vars/", 0.2),
            ("host_vars/", 0.15)
        ]
        
        for pattern, weight in ansible_patterns:
            if self._path_exists(pattern):
                evidence.append(pattern)
                score += weight
        
        # Ansible configuration
        if self._path_exists("ansible.cfg"):
            evidence.append("ansible.cfg")
            score += 0.15
        
        # Requirements
        if self._path_exists("requirements.yml"):
            evidence.append("requirements.yml")
            score += 0.1
        
        return "ansible", min(score, 1.0), evidence
    
    def _detect_python(self) -> Tuple[str, float, List[str]]:
        """Detect Python project."""
        evidence = []
        score = 0.0
        
        python_files = [
            ("setup.py", 0.2),
            ("pyproject.toml", 0.2), 
            ("requirements.txt", 0.15),
            ("Pipfile", 0.15),
            ("poetry.lock", 0.15)
        ]
        
        for filename, weight in python_files:
            if self._path_exists(filename):
                evidence.append(filename)
                score += weight
        
        # Python source files
        if self._has_files_matching("*.py"):
            py_files = list(self.project_root.rglob("*.py"))
            if py_files:
                evidence.append(f"{len(py_files)} Python files")
                score += min(len(py_files) * 0.02, 0.3)
        
        return "python", min(score, 1.0), evidence
    
    def _detect_nodejs(self) -> Tuple[str, float, List[str]]:
        """Detect Node.js project."""
        evidence = []
        score = 0.0
        
        if self._path_exists("package.json"):
            evidence.append("package.json")
            score += 0.4
        
        if self._path_exists("node_modules"):
            evidence.append("node_modules")
            score += 0.2
        
        if self._path_exists("yarn.lock") or self._path_exists("package-lock.json"):
            evidence.append("lock files")
            score += 0.2
        
        return "nodejs", min(score, 1.0), evidence
    
    def _detect_documentation(self) -> Tuple[str, float, List[str]]:
        """Detect documentation-focused repository."""
        evidence = []
        score = 0.0
        
        # Documentation patterns
        docs_patterns = [
            ("docs/", 0.2),
            ("documentation/", 0.2),
            ("wiki/", 0.15)
        ]
        
        for pattern, weight in docs_patterns:
            if self._path_exists(pattern):
                evidence.append(pattern)
                score += weight
        
        # Markdown files
        if self._has_files_matching("*.md"):
            md_files = list(self.project_root.rglob("*.md"))
            if len(md_files) > 5:  # Lots of markdown = docs repo
                evidence.append(f"{len(md_files)} Markdown files")
                score += min(len(md_files) * 0.03, 0.4)
        
        # Documentation generators
        docs_tools = [
            ("mkdocs.yml", 0.3),
            ("_config.yml", 0.2),  # Jekyll
            ("sphinx/", 0.2),
            ("gitbook/", 0.2)
        ]
        
        for pattern, weight in docs_tools:
            if self._path_exists(pattern):
                evidence.append(pattern)
                score += weight
        
        return "documentation", min(score, 1.0), evidence
    
    def _path_exists(self, pattern: str) -> bool:
        """Check if a path pattern exists in the project."""
        path = self.project_root / pattern
        return path.exists()
    
    def _has_files_matching(self, pattern: str) -> bool:
        """Check if any files match the given pattern."""
        try:
            files = list(self.project_root.rglob(pattern))
            return len(files) > 0
        except:
            return False
    
    def _file_contains(self, filename: str, keywords: List[str]) -> bool:
        """Check if a file contains any of the given keywords."""
        try:
            filepath = self.project_root / filename
            if not filepath.exists():
                return False
            
            content = filepath.read_text(encoding='utf-8', errors='ignore').lower()
            return any(keyword.lower() in content for keyword in keywords)
        except:
            return False
    
    def get_repository_info(self) -> Dict:
        """Get comprehensive repository information."""
        info = {
            "project_root": str(self.project_root),
            "detected_type": self.detect_repo_type(),
            "file_counts": {},
            "directory_structure": [],
            "git_info": {}
        }
        
        # Count files by type
        file_types = {}
        for filepath in self.project_root.rglob("*"):
            if filepath.is_file():
                suffix = filepath.suffix or "no_extension"
                file_types[suffix] = file_types.get(suffix, 0) + 1
        
        info["file_counts"] = dict(sorted(file_types.items(), 
                                         key=lambda x: x[1], reverse=True)[:10])
        
        # Get top-level directory structure
        try:
            info["directory_structure"] = [
                d.name for d in self.project_root.iterdir() 
                if d.is_dir() and not d.name.startswith('.')
            ]
        except:
            pass
        
        # Git information
        try:
            import subprocess
            result = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                capture_output=True, text=True, cwd=self.project_root
            )
            if result.returncode == 0:
                info["git_info"]["remote"] = result.stdout.strip()
        except:
            pass
        
        return info
    
    def generate_config(self, repo_type: str) -> Dict:
        """Generate configuration for detected repository type."""
        configs = {
            "mlops-platform": {
                "repo_type": "mlops-platform",
                "keywords": [
                    "k3s", "harbor", "istio", "seldon", "kubeadm", "metallb",
                    "prometheus", "grafana", "jupyterhub", "argo", "sealed-secrets",
                    "calico", "cilium", "ansible", "kubernetes"
                ],
                "file_patterns": [
                    "*.yml", "*.yaml", "*.md", "*.sh", 
                    "roles/**/*.yml", "inventory/**/*.yml",
                    "scripts/*.sh", "docs/*.md"
                ],
                "exclude_paths": [
                    # Version control and package managers
                    ".git", ".svn", ".hg", ".bzr",
                    "node_modules", "bower_components", "jspm_packages",
                    # Python environments and cache
                    "__pycache__", "*.pyc", "*.pyo", "*.pyd", ".Python",
                    "venv", "env", ".venv", ".env", "virtualenv", ".virtualenv",
                    ".tox", ".pytest_cache", ".coverage", ".cache",
                    "pip-log.txt", "pip-delete-this-directory.txt",
                    # Build artifacts and temporary files
                    "build/", "dist/", "*.egg-info/", "target/", "out/",
                    "tmp/", "temp/", "*.tmp", "*.log", "*.swp", "*.swo",
                    # Additional caches
                    ".mypy_cache",
                    # IDE and editor files
                    ".vscode", ".idea", "*.sublime-*", ".vs",
                    # Platform-specific
                    ".ansible", "fetched_tokens",
                    # RAG system files
                    ".claude-rag"
                ],
                "extraction_focus": [
                    "ansible_tasks", "kubernetes_resources", "shell_commands",
                    "troubleshooting_sections", "configuration_examples",
                    "service_endpoints", "network_policies"
                ]
            },
            "ml-model": {
                "repo_type": "ml-model",
                "keywords": [
                    "model", "pipeline", "training", "inference", "deployment",
                    "fraud", "feature", "prediction", "validation", "monitoring",
                    "pytorch", "tensorflow", "scikit-learn", "pandas", "numpy"
                ],
                "file_patterns": [
                    "*.py", "*.ipynb", "*.yaml", "*.yml", "*.md", 
                    "requirements.txt", "Dockerfile", "*.json",
                    "notebooks/*.ipynb", "src/**/*.py"
                ],
                "exclude_paths": [
                    # Version control
                    ".git", ".svn", ".hg",
                    # Python environments and cache
                    "__pycache__", "*.pyc", "*.pyo", "*.pyd", ".Python",
                    "venv", "env", ".venv", ".env", "virtualenv", ".virtualenv",
                    ".tox", ".pytest_cache", ".coverage", ".cache",
                    # Jupyter and ML artifacts
                    ".ipynb_checkpoints", "mlruns", "wandb", "tensorboard_logs",
                    # Additional caches
                    ".mypy_cache",
                    "models/saved", "models/checkpoints", "data/raw", "data/cache",
                    # Build and dependencies
                    "build", "dist", "*.egg-info", "node_modules",
                    # IDE files
                    ".vscode", ".idea", "*.sublime-*",
                    # Temporary files
                    "tmp/", "temp/", "*.tmp", "*.log", "*.swp",
                    # RAG system files
                    ".claude-rag"
                ],
                "extraction_focus": [
                    "python_functions", "jupyter_cells", "model_configs",
                    "pipeline_definitions", "api_endpoints", "training_scripts"
                ]
            },
            "kubernetes": {
                "repo_type": "kubernetes",
                "keywords": [
                    "kubernetes", "k8s", "kubectl", "helm", "kustomize",
                    "deployment", "service", "ingress", "configmap", "secret"
                ],
                "file_patterns": [
                    "*.yaml", "*.yml", "*.md", "Chart.yaml", "values.yaml",
                    "k8s/**/*.yaml", "manifests/**/*.yaml"
                ],
                "exclude_paths": [
                    # Version control
                    ".git", ".svn", ".hg",
                    # Node.js dependencies
                    "node_modules", "bower_components", "jspm_packages",
                    # Kubernetes and Helm artifacts
                    ".helm/", "charts/*/charts/", ".kube/",
                    # Build artifacts
                    "build/", "dist/", "target/", "out/",
                    # Cache and temporary files
                    ".cache/", ".mypy_cache", "tmp/", "temp/", "*.tmp", "*.log",
                    # IDE files
                    ".vscode", ".idea", "*.sublime-*",
                    # RAG system files
                    ".claude-rag"
                ],
                "extraction_focus": [
                    "kubernetes_resources", "helm_charts", "kustomize_configs"
                ]
            },
            "ansible": {
                "repo_type": "ansible",
                "keywords": [
                    "ansible", "playbook", "role", "task", "handler",
                    "inventory", "vars", "template", "module"
                ],
                "file_patterns": [
                    "*.yml", "*.yaml", "*.md", "*.j2", "*.sh",
                    "roles/**/*.yml", "playbooks/**/*.yml",
                    "inventory/**/*", "group_vars/**/*.yml"
                ],
                "exclude_paths": [
                    # Version control
                    ".git", ".svn", ".hg",
                    # Ansible artifacts
                    ".ansible", "*.retry", "*.log", "ansible.log",
                    # Python environments (common in Ansible projects)
                    "__pycache__", "*.pyc", "venv", "env", ".venv",
                    # Dependencies
                    "node_modules", "bower_components",
                    # Build and cache
                    "build/", "dist/", ".cache/", ".mypy_cache", "tmp/", "temp/",
                    # IDE files
                    ".vscode", ".idea", "*.sublime-*",
                    # RAG system files
                    ".claude-rag"
                ],
                "extraction_focus": [
                    "ansible_tasks", "playbook_structure", "role_definitions"
                ]
            },
            "python": {
                "repo_type": "python",
                "keywords": [
                    "python", "pip", "setup", "package", "module",
                    "django", "flask", "fastapi", "pytest", "unittest"
                ],
                "file_patterns": [
                    "*.py", "*.md", "*.txt", "*.cfg", "*.ini",
                    "requirements.txt", "setup.py", "pyproject.toml"
                ],
                "exclude_paths": [
                    # Version control
                    ".git", ".svn", ".hg", ".bzr",
                    # Python environments and cache
                    "__pycache__", "*.pyc", "*.pyo", "*.pyd", ".Python",
                    "venv", "env", ".venv", ".env", "virtualenv", ".virtualenv",
                    ".tox", ".pytest_cache", ".coverage", ".cache", ".mypy_cache",
                    "pip-log.txt", "pip-delete-this-directory.txt",
                    # Build artifacts
                    "build", "dist", "*.egg-info", "*.egg", "*.whl",
                    # Dependencies
                    "node_modules", "bower_components",
                    # IDE and editor files
                    ".vscode", ".idea", "*.sublime-*", ".vs", ".spyderproject",
                    # OS and temporary files
                    ".DS_Store", "Thumbs.db", "tmp/", "temp/", "*.tmp", "*.log",
                    "*.swp", "*.swo", "*~",
                    # RAG system files
                    ".claude-rag"
                ],
                "extraction_focus": [
                    "python_functions", "class_definitions", "api_endpoints"
                ]
            },
            "documentation": {
                "repo_type": "documentation", 
                "keywords": [
                    "documentation", "docs", "guide", "tutorial", "reference",
                    "readme", "wiki", "knowledge", "manual"
                ],
                "file_patterns": [
                    "*.md", "*.rst", "*.txt", "*.html",
                    "docs/**/*.md", "wiki/**/*.md"
                ],
                "exclude_paths": [
                    # Version control
                    ".git", ".svn", ".hg",
                    # Node.js dependencies
                    "node_modules", "bower_components", "jspm_packages",
                    # Documentation site generators
                    "_site/", ".jekyll-cache/", "_build/", ".sphinx-build/",
                    ".docusaurus/", "public/", ".next/", ".nuxt/",
                    # Build artifacts
                    "build/", "dist/", "out/", "target/",
                    # Cache and temporary files
                    ".cache/", ".mypy_cache", "tmp/", "temp/", "*.tmp", "*.log",
                    # IDE files
                    ".vscode", ".idea", "*.sublime-*",
                    # OS files
                    ".DS_Store", "Thumbs.db",
                    # RAG system files
                    ".claude-rag"
                ],
                "extraction_focus": [
                    "documentation_structure", "cross_references", "tutorials"
                ]
            }
        }
        
        return configs.get(repo_type, configs["documentation"])
    
    def analyze_project(self) -> Dict:
        """Comprehensive project analysis."""
        repo_type, confidence, analysis = self.detect_repository_type()
        config = self.generate_config(repo_type)
        
        # File statistics
        file_counts = {}
        total_files = 0
        total_size = 0
        
        for filepath in self.project_root.rglob("*"):
            if filepath.is_file():
                try:
                    size = filepath.stat().st_size
                    total_size += size
                    total_files += 1
                    
                    suffix = filepath.suffix or "no_extension"
                    file_counts[suffix] = file_counts.get(suffix, 0) + 1
                except:
                    pass
        
        return {
            "detection": {
                "repo_type": repo_type,
                "confidence": confidence,
                "evidence": analysis.get("evidence", []),
                "alternatives": analysis.get("alternatives", [])
            },
            "config": config,
            "statistics": {
                "total_files": total_files,
                "project_size": {
                    "total_size_bytes": total_size,
                    "total_size_mb": round(total_size / (1024 * 1024), 2)
                },
                "file_counts": dict(sorted(file_counts.items(), 
                                         key=lambda x: x[1], reverse=True)[:10])
            }
        }