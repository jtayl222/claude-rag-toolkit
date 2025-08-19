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
        Simplified universal repository detection.
        Returns universal type for all repositories.
        """
        # Count different file types to provide some insight
        file_counts = {}
        for filepath in self.project_root.rglob("*"):
            if filepath.is_file():
                suffix = filepath.suffix.lower()
                file_counts[suffix] = file_counts.get(suffix, 0) + 1
        
        # Generate simple evidence based on what we found
        evidence = []
        if file_counts.get('.md', 0) > 0:
            evidence.append(f"{file_counts['.md']} Markdown files")
        if file_counts.get('.py', 0) > 0:
            evidence.append(f"{file_counts['.py']} Python files")
        if file_counts.get('.yml', 0) + file_counts.get('.yaml', 0) > 0:
            evidence.append(f"{file_counts.get('.yml', 0) + file_counts.get('.yaml', 0)} YAML files")
        if file_counts.get('.html', 0) > 0:
            evidence.append(f"{file_counts['.html']} HTML files")
        if file_counts.get('.pdf', 0) > 0:
            evidence.append(f"{file_counts['.pdf']} PDF files")
        
        analysis = {
            "evidence": evidence,
            "alternatives": [],  # No alternatives needed
            "detection_details": {
                "total_indicators": len(evidence),
                "confidence_breakdown": "Universal configuration for all project types"
            }
        }
        
        return "universal", 1.0, analysis

    def detect_repo_type(self) -> str:
        """Legacy method for backward compatibility."""
        repo_type, confidence, _ = self.detect_repository_type()
        print(f"🔍 Detected repository type: {repo_type} (confidence: {confidence:.2f})")
        return repo_type
    
    def _detect_mlops_platform(self) -> Tuple[str, float, List[str]]:
        """Legacy method - no longer used."""
        return "universal", 0.0, []

    def _detect_ml_model(self) -> Tuple[str, float, List[str]]:
        """Legacy method - no longer used."""
        return "universal", 0.0, []

    def _detect_kubernetes(self) -> Tuple[str, float, List[str]]:
        """Legacy method - no longer used."""
        return "universal", 0.0, []

    def _detect_ansible(self) -> Tuple[str, float, List[str]]:
        """Legacy method - no longer used."""
        return "universal", 0.0, []

    def _detect_python(self) -> Tuple[str, float, List[str]]:
        """Legacy method - no longer used."""
        return "universal", 0.0, []

    def _detect_nodejs(self) -> Tuple[str, float, List[str]]:
        """Legacy method - no longer used."""
        return "universal", 0.0, []

    def _detect_documentation(self) -> Tuple[str, float, List[str]]:
        """Legacy method - no longer used."""
        return "universal", 0.0, []
    
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
        """Generate universal configuration that works for all repository types."""
        # Universal configuration that works for all project types
        return {
            "repo_type": "universal",
            "keywords": [
                # Common technical terms
                "api", "database", "server", "client", "service", "config", "deploy",
                "docker", "kubernetes", "k8s", "ansible", "terraform", "helm",
                "python", "javascript", "typescript", "java", "go", "rust",
                "ml", "model", "training", "inference", "pipeline", "data",
                "test", "build", "ci", "cd", "git", "github", "gitlab"
            ],
            "file_patterns": [
                # Documentation
                "*.md", "*.rst", "*.txt", "*.html", "*.pdf",
                # Configuration  
                "*.yml", "*.yaml", "*.json", "*.toml", "*.ini", "*.cfg",
                # Code
                "*.py", "*.js", "*.ts", "*.java", "*.go", "*.rs", "*.sh",
                # Notebooks and data
                "*.ipynb", "*.csv", "*.sql",
                # Directory patterns
                "docs/**/*", "_data/**/*", "src/**/*", "scripts/**/*",
                "config/**/*", "configs/**/*", "examples/**/*"
            ],
            "exclude_paths": [
                # Version control
                ".git", ".svn", ".hg", ".bzr",
                # Dependencies and packages
                "node_modules", "bower_components", "jspm_packages",
                "vendor", "packages", "deps",
                # Python environments and cache
                "__pycache__", "*.pyc", "*.pyo", "*.pyd", ".Python",
                "venv", "env", ".venv", ".env", "virtualenv", ".virtualenv",
                ".tox", ".pytest_cache", ".coverage", ".cache", ".mypy_cache",
                "pip-log.txt", "pip-delete-this-directory.txt",
                # Build artifacts
                "build", "dist", "target", "out", "bin", "obj",
                "*.egg-info", "*.egg", "*.whl",
                # Generated sites and docs
                "_site", ".jekyll-cache", "_build", ".sphinx-build",
                ".docusaurus", "public", ".next", ".nuxt",
                # Temporary and log files
                "tmp", "temp", "logs", "*.tmp", "*.log", "*.swp", "*.swo", "*~",
                # IDE and editor files
                ".vscode", ".idea", "*.sublime-*", ".vs", ".spyderproject",
                # OS files
                ".DS_Store", "Thumbs.db", "ehthumbs.db",
                # Language-specific
                ".terraform", ".ansible", "Cargo.lock", "package-lock.json",
                # RAG system files
                ".claude-rag"
            ],
            "extraction_focus": [
                "documentation_structure", "code_functions", "configuration_examples",
                "troubleshooting_sections", "installation_instructions", "api_endpoints",
                "shell_commands", "workflow_steps", "best_practices"
            ],
            "semantic_search": {
                "enabled": True,
                "model": "all-MiniLM-L6-v2",
                "similarity_threshold": 0.3,
                "max_results": 10
            }
        }
    
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