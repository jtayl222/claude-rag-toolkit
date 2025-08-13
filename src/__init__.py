"""
Claude RAG Toolkit - Multi-repository documentation management system.
"""

__version__ = "1.0.0"
__author__ = "Claude RAG Toolkit Team"
__description__ = "Multi-repository documentation management system for Claude Code"

from .core.rag_engine import MultiRepoRAGEngine
from .utils.repo_detector import RepositoryDetector

__all__ = ["MultiRepoRAGEngine", "RepositoryDetector"]