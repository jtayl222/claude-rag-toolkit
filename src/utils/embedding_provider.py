#!/usr/bin/env python3
"""
Embedding Provider for Semantic Search
Handles text embeddings using Sentence Transformers for improved search capabilities.
"""

import os
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime
import logging

# Optional dependencies - gracefully handle imports
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    np = None

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    SentenceTransformer = None

try:
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    cosine_similarity = None


class EmbeddingProvider:
    """
    Provides text embeddings for semantic search using Sentence Transformers.
    Falls back to basic search if dependencies are not available.
    """
    
    def __init__(self, project_root: str, model_name: str = "all-MiniLM-L6-v2"):
        self.project_root = Path(project_root)
        self.model_name = model_name
        self.cache_dir = self.project_root / ".claude-rag" / "embeddings"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.model = None
        self.embeddings_cache = {}
        self.document_embeddings = {}
        
        # Initialize model if dependencies are available
        self._initialize_model()
        
        # Load cached embeddings
        self._load_cache()
    
    def _initialize_model(self):
        """Initialize the Sentence Transformer model if available."""
        if not self._check_dependencies():
            logging.info("Semantic search dependencies not available. Using basic text search.")
            return
        
        try:
            # Use a lightweight, fast model by default
            self.model = SentenceTransformer(self.model_name)
            logging.info(f"Initialized embedding model: {self.model_name}")
        except Exception as e:
            logging.warning(f"Failed to initialize embedding model: {e}")
            self.model = None
    
    def _check_dependencies(self) -> bool:
        """Check if all required dependencies are available."""
        return all([
            NUMPY_AVAILABLE,
            SENTENCE_TRANSFORMERS_AVAILABLE, 
            SKLEARN_AVAILABLE
        ])
    
    def is_available(self) -> bool:
        """Check if semantic search is available."""
        return self.model is not None and self._check_dependencies()
    
    def _load_cache(self):
        """Load cached embeddings from disk."""
        cache_file = self.cache_dir / "embeddings.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    cached_data = json.load(f)
                    
                # Load document embeddings
                embeddings_file = self.cache_dir / "document_embeddings.npz"
                if embeddings_file.exists() and NUMPY_AVAILABLE:
                    embeddings_data = np.load(embeddings_file)
                    for doc_id, embedding in embeddings_data.items():
                        self.document_embeddings[doc_id] = embedding
                    
                self.embeddings_cache = cached_data
                logging.info(f"Loaded {len(self.document_embeddings)} cached embeddings")
                
            except Exception as e:
                logging.warning(f"Failed to load embedding cache: {e}")
                self.embeddings_cache = {}
                self.document_embeddings = {}
    
    def _save_cache(self):
        """Save embeddings cache to disk."""
        try:
            # Save metadata
            cache_file = self.cache_dir / "embeddings.json"
            with open(cache_file, 'w') as f:
                json.dump(self.embeddings_cache, f, indent=2)
            
            # Save embeddings as numpy arrays
            if self.document_embeddings and NUMPY_AVAILABLE:
                embeddings_file = self.cache_dir / "document_embeddings.npz"
                np.savez_compressed(embeddings_file, **self.document_embeddings)
                
        except Exception as e:
            logging.warning(f"Failed to save embedding cache: {e}")
    
    def _compute_text_hash(self, text: str) -> str:
        """Compute hash for text to check if embeddings need updating."""
        return hashlib.md5(text.encode('utf-8')).hexdigest()
    
    def get_document_embedding(self, doc_id: str, text: str, force_recompute: bool = False) -> Optional[np.ndarray]:
        """
        Get or compute embedding for a document.
        
        Args:
            doc_id: Unique identifier for the document
            text: Document text content
            force_recompute: Force recomputation even if cached
            
        Returns:
            Document embedding as numpy array, or None if not available
        """
        if not self.is_available():
            return None
            
        text_hash = self._compute_text_hash(text)
        
        # Check if we have a valid cached embedding
        if not force_recompute and doc_id in self.embeddings_cache:
            cached_hash = self.embeddings_cache[doc_id].get('text_hash')
            if cached_hash == text_hash and doc_id in self.document_embeddings:
                return self.document_embeddings[doc_id]
        
        # Compute new embedding
        try:
            # Truncate very long documents to avoid memory issues
            max_length = 5000  # characters
            if len(text) > max_length:
                text = text[:max_length] + "..."
                
            embedding = self.model.encode([text])[0]
            
            # Cache the embedding
            self.document_embeddings[doc_id] = embedding
            self.embeddings_cache[doc_id] = {
                'text_hash': text_hash,
                'model_name': self.model_name,
                'computed_at': datetime.now().isoformat()
            }
            
            return embedding
            
        except Exception as e:
            logging.error(f"Failed to compute embedding for {doc_id}: {e}")
            return None
    
    def get_query_embedding(self, query: str) -> Optional[np.ndarray]:
        """
        Get embedding for a search query.
        
        Args:
            query: Search query text
            
        Returns:
            Query embedding as numpy array, or None if not available
        """
        if not self.is_available():
            return None
            
        try:
            return self.model.encode([query])[0]
        except Exception as e:
            logging.error(f"Failed to compute query embedding: {e}")
            return None
    
    def compute_similarity(self, query_embedding: np.ndarray, document_embeddings: Dict[str, np.ndarray]) -> Dict[str, float]:
        """
        Compute cosine similarity between query and document embeddings.
        
        Args:
            query_embedding: Query embedding vector
            document_embeddings: Dictionary of doc_id -> embedding
            
        Returns:
            Dictionary of doc_id -> similarity_score
        """
        if not self.is_available() or not document_embeddings:
            return {}
            
        similarities = {}
        
        try:
            # Reshape query embedding for sklearn
            query_vector = query_embedding.reshape(1, -1)
            
            for doc_id, doc_embedding in document_embeddings.items():
                doc_vector = doc_embedding.reshape(1, -1)
                similarity = cosine_similarity(query_vector, doc_vector)[0][0]
                similarities[doc_id] = float(similarity)
                
        except Exception as e:
            logging.error(f"Failed to compute similarities: {e}")
            
        return similarities
    
    def find_similar_documents(self, query: str, document_texts: Dict[str, str], top_k: int = 10, similarity_threshold: float = 0.3) -> List[Tuple[str, float]]:
        """
        Find documents most similar to a query using semantic search.
        
        Args:
            query: Search query
            document_texts: Dictionary of doc_id -> document_text
            top_k: Maximum number of results to return
            similarity_threshold: Minimum similarity score to include
            
        Returns:
            List of (doc_id, similarity_score) tuples, sorted by similarity
        """
        if not self.is_available():
            return []
            
        # Get query embedding
        query_embedding = self.get_query_embedding(query)
        if query_embedding is None:
            return []
        
        # Get or compute document embeddings
        doc_embeddings = {}
        for doc_id, text in document_texts.items():
            embedding = self.get_document_embedding(doc_id, text)
            if embedding is not None:
                doc_embeddings[doc_id] = embedding
        
        # Compute similarities
        similarities = self.compute_similarity(query_embedding, doc_embeddings)
        
        # Filter and sort results
        results = [
            (doc_id, score) for doc_id, score in similarities.items()
            if score >= similarity_threshold
        ]
        results.sort(key=lambda x: x[1], reverse=True)
        
        return results[:top_k]
    
    def expand_query_with_embeddings(self, query: str, document_texts: Dict[str, str], expansion_limit: int = 5) -> List[str]:
        """
        Expand a query with semantically similar terms found in the document corpus.
        
        Args:
            query: Original search query
            document_texts: Available document texts
            expansion_limit: Maximum number of expansion terms
            
        Returns:
            List of expansion terms to add to the search
        """
        if not self.is_available():
            return []
            
        # Find semantically similar documents
        similar_docs = self.find_similar_documents(query, document_texts, top_k=3, similarity_threshold=0.4)
        
        expansion_terms = set()
        
        # Extract key terms from similar documents
        for doc_id, similarity in similar_docs:
            if doc_id in document_texts:
                text = document_texts[doc_id].lower()
                
                # Simple keyword extraction - could be enhanced with NLP
                words = text.split()
                
                # Look for terms related to the query
                query_words = set(query.lower().split())
                for word in words:
                    if (len(word) > 3 and 
                        word not in query_words and 
                        word.isalpha() and
                        len(expansion_terms) < expansion_limit):
                        expansion_terms.add(word)
        
        return list(expansion_terms)
    
    def save_cache(self):
        """Public method to save cache."""
        self._save_cache()
    
    def clear_cache(self):
        """Clear all cached embeddings."""
        self.embeddings_cache = {}
        self.document_embeddings = {}
        
        # Remove cache files
        cache_file = self.cache_dir / "embeddings.json"
        embeddings_file = self.cache_dir / "document_embeddings.npz"
        
        if cache_file.exists():
            cache_file.unlink()
        if embeddings_file.exists():
            embeddings_file.unlink()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about cached embeddings."""
        return {
            "is_available": self.is_available(),
            "model_name": self.model_name,
            "cached_documents": len(self.document_embeddings),
            "cache_size_mb": sum(
                embedding.nbytes for embedding in self.document_embeddings.values()
            ) / (1024 * 1024) if self.document_embeddings and NUMPY_AVAILABLE else 0,
            "dependencies": {
                "numpy": NUMPY_AVAILABLE,
                "sentence_transformers": SENTENCE_TRANSFORMERS_AVAILABLE,
                "sklearn": SKLEARN_AVAILABLE
            }
        }