#!/usr/bin/env python3
"""
Setup script for Claude RAG Toolkit
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
long_description = (Path(__file__).parent / "README.md").read_text()

setup(
    name="claude-rag-toolkit",
    version="1.0.0",
    description="Multi-repository documentation management system for Claude Code",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Claude RAG Toolkit Team",
    author_email="noreply@example.com",
    url="https://github.com/yourusername/claude-rag-toolkit",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.8",
    install_requires=[
        # No dependencies by default - all optional
    ],
    extras_require={
        # Enhanced CLI experience with rich output and progress bars
        "rich": [
            "rich>=13.0.0",           # Better terminal output, tables, progress bars
            "click>=8.0.0",           # Enhanced CLI argument parsing
        ],
        
        # Performance and validation enhancements
        "enhanced": [
            "pydantic>=2.0.0",        # Configuration validation and data models
            "orjson>=3.9.0",          # Faster JSON parsing for large files
            "rapidfuzz>=3.0.0",       # Better fuzzy matching for search
        ],
        
        # All enhancements combined
        "full": [
            "rich>=13.0.0",
            "click>=8.0.0", 
            "pydantic>=2.0.0",
            "orjson>=3.9.0",
            "rapidfuzz>=3.0.0",
        ],
        
        # MCP protocol support (future)
        "mcp": [
            # Commented out since these packages don't exist yet
            # "mcp>=1.0.0",
            # "orjson>=3.9.0",
        ],
        
        # Development dependencies
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "pytest-mock>=3.10.0", 
            "black>=22.0.0",
            "flake8>=4.0.0",
            "flake8-docstrings>=1.7.0",
            "pre-commit>=3.0.0",
        ],
        
        # Testing only
        "test": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "pytest-mock>=3.10.0",
            "pytest-asyncio>=0.21.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "claude-rag=cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Documentation",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Text Processing :: Indexing",
    ],
    keywords=[
        "claude", "documentation", "rag", "search", "knowledge-management",
        "multi-repository", "mlops", "machine-learning", "ansible", "kubernetes"
    ],
    project_urls={
        "Bug Reports": "https://github.com/yourusername/claude-rag-toolkit/issues",
        "Source": "https://github.com/yourusername/claude-rag-toolkit",
        "Documentation": "https://github.com/yourusername/claude-rag-toolkit/blob/main/README.md",
    },
)