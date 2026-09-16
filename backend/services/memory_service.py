"""
Memory Service - Provides persistent memory for AI workflows
Supports: Vector DB (ChromaDB), Redis Cache, and Context Store
"""

import json
import hashlib
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
import asyncio

# Vector DB support (ChromaDB)
try:
    import chromadb
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False

# Redis support
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


class MemoryService:
    """
    Unified memory service for AI workflows
    - Vector memory (semantic search)
    - Cache memory (key-value)
    - Context memory (conversation history)
    """

    def __init__(self):
        self.vector_db = None
        self.redis_client = None
        self.context_store = {}  # In-memory fallback

        # Initialize ChromaDB if available
        if CHROMADB_AVAILABLE:
            try:
                # Use new ChromaDB API (v0.4.0+)
                self.vector_db = chromadb.PersistentClient(path="./chroma_db")
                print("✅ ChromaDB initialized for vector memory")
            except Exception as e:
                print(f"⚠️ ChromaDB initialization failed: {e}")

        # Initialize Redis if available
        if REDIS_AVAILABLE:
            try:
                self.redis_client = redis.Redis(
                    host='localhost',
                    port=6379,
                    db=0,
                    decode_responses=True
                )
                self.redis_client.ping()
                print("✅ Redis initialized for cache memory")
            except Exception as e:
                print(f"⚠️ Redis connection failed: {e}")
                self.redis_client = None

    # ==================== VECTOR MEMORY ====================

    async def store_vector(
        self,
        collection_name: str,
        text: str,
        metadata: Optional[Dict] = None,
        doc_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Store text in vector database for semantic search"""

        if not CHROMADB_AVAILABLE or not self.vector_db:
            return {
                "success": False,
                "error": "ChromaDB not available. Install: pip install chromadb"
            }

        try:
            # Get or create collection
            collection = self.vector_db.get_or_create_collection(collection_name)

            # Generate ID if not provided
            if not doc_id:
                doc_id = hashlib.md5(text.encode()).hexdigest()[:16]

            # Add metadata
            if metadata is None:
                metadata = {}
            metadata['timestamp'] = datetime.now().isoformat()

            # Store in vector DB
            collection.add(
                documents=[text],
                metadatas=[metadata],
                ids=[doc_id]
            )

            return {
                "success": True,
                "doc_id": doc_id,
                "collection": collection_name,
                "count": collection.count()
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def search_vector(
        self,
        collection_name: str,
        query: str,
        n_results: int = 5,
        where: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Semantic search in vector database"""

        if not CHROMADB_AVAILABLE or not self.vector_db:
            return {
                "success": False,
                "error": "ChromaDB not available"
            }

        try:
            collection = self.vector_db.get_collection(collection_name)

            results = collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where
            )

            return {
                "success": True,
                "results": [
                    {
                        "id": results['ids'][0][i],
                        "text": results['documents'][0][i],
                        "metadata": results['metadatas'][0][i],
                        "distance": results['distances'][0][i]
                    }
                    for i in range(len(results['ids'][0]))
                ]
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def delete_vector_collection(self, collection_name: str) -> Dict[str, Any]:
        """Delete entire vector collection"""

        if not CHROMADB_AVAILABLE or not self.vector_db:
            return {"success": False, "error": "ChromaDB not available"}

        try:
            self.vector_db.delete_collection(collection_name)
            return {"success": True, "message": f"Collection '{collection_name}' deleted"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ==================== CACHE MEMORY (Redis) ====================

    async def cache_set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> Dict[str, Any]:
        """Store key-value in cache with optional TTL (seconds)"""

        try:
            # Serialize value
            serialized = json.dumps(value) if not isinstance(value, str) else value

            if self.redis_client:
                # Use Redis
                if ttl:
                    self.redis_client.setex(key, ttl, serialized)
                else:
                    self.redis_client.set(key, serialized)
            else:
                # Fallback to in-memory
                expiry = datetime.now() + timedelta(seconds=ttl) if ttl else None
                self.context_store[key] = {
                    "value": serialized,
                    "expiry": expiry
                }

            return {"success": True, "key": key, "ttl": ttl}

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def cache_get(self, key: str) -> Dict[str, Any]:
        """Retrieve value from cache"""

        try:
            if self.redis_client:
                # Use Redis
                value = self.redis_client.get(key)
            else:
                # Fallback to in-memory
                entry = self.context_store.get(key)
                if entry and (not entry['expiry'] or entry['expiry'] > datetime.now()):
                    value = entry['value']
                else:
                    value = None

            if value is None:
                return {"success": False, "error": "Key not found or expired"}

            # Try to deserialize
            try:
                value = json.loads(value)
            except:
                pass  # Keep as string

            return {"success": True, "value": value}

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def cache_delete(self, key: str) -> Dict[str, Any]:
        """Delete key from cache"""

        try:
            if self.redis_client:
                self.redis_client.delete(key)
            else:
                self.context_store.pop(key, None)

            return {"success": True, "message": f"Key '{key}' deleted"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def cache_clear(self) -> Dict[str, Any]:
        """Clear all cache"""

        try:
            if self.redis_client:
                self.redis_client.flushdb()
            else:
                self.context_store.clear()

            return {"success": True, "message": "Cache cleared"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    # ==================== CONTEXT MEMORY (Conversation History) ====================

    async def context_append(
        self,
        context_id: str,
        message: Dict[str, Any],
        max_history: int = 100
    ) -> Dict[str, Any]:
        """Append message to conversation context"""

        try:
            # Get existing context
            result = await self.cache_get(f"context:{context_id}")
            if result['success']:
                history = result['value'] if isinstance(result['value'], list) else []
            else:
                history = []

            # Add timestamp
            message['timestamp'] = datetime.now().isoformat()

            # Append message
            history.append(message)

            # Limit history size
            if len(history) > max_history:
                history = history[-max_history:]

            # Store back
            await self.cache_set(f"context:{context_id}", history)

            return {
                "success": True,
                "context_id": context_id,
                "message_count": len(history)
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def context_get(
        self,
        context_id: str,
        last_n: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get conversation context"""

        try:
            result = await self.cache_get(f"context:{context_id}")
            if not result['success']:
                return {"success": True, "history": []}

            history = result['value'] if isinstance(result['value'], list) else []

            if last_n:
                history = history[-last_n:]

            return {"success": True, "history": history}

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def context_clear(self, context_id: str) -> Dict[str, Any]:
        """Clear conversation context"""

        return await self.cache_delete(f"context:{context_id}")

    # ==================== UTILITIES ====================

    async def get_stats(self) -> Dict[str, Any]:
        """Get memory service statistics"""

        stats = {
            "vector_db": {
                "available": CHROMADB_AVAILABLE and self.vector_db is not None,
                "collections": []
            },
            "cache": {
                "available": self.redis_client is not None or len(self.context_store) > 0,
                "backend": "redis" if self.redis_client else "in-memory",
                "keys": 0
            }
        }

        # Vector DB stats
        if stats["vector_db"]["available"]:
            try:
                collections = self.vector_db.list_collections()
                stats["vector_db"]["collections"] = [
                    {
                        "name": col.name,
                        "count": col.count()
                    }
                    for col in collections
                ]
            except:
                pass

        # Cache stats
        if self.redis_client:
            try:
                stats["cache"]["keys"] = self.redis_client.dbsize()
            except:
                pass
        else:
            stats["cache"]["keys"] = len(self.context_store)

        return stats


# Global instance
memory_service = MemoryService()
