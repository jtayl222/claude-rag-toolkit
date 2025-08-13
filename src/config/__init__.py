#!/usr/bin/env python3
"""
Configuration module for the Claude RAG Toolkit.
"""

# Configuration constants and default settings
DEFAULT_CONFIG = {
    "version": "2.0",
    "extraction_focus": ["general"],
    "max_file_size_mb": 10,
    "index_batch_size": 100,
    "search_result_limit": 20
}

__all__ = ["DEFAULT_CONFIG"]