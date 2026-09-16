"""
LLM Caching System (AI Planet Feature)
Reduce LLM inference costs by up to 60x through intelligent response caching
Features:
- Semantic similarity-based caching
- Exact match caching
- TTL (time-to-live) management
- Cache hit rate tracking
- Cost savings analytics
"""

from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import hashlib
import logging
import json

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Cached LLM response"""
    key: str
    prompt: str
    response: str
    model: str
    temperature: float
    created_at: datetime
    last_accessed: datetime
    access_count: int
    tokens_saved: int
    cost_saved_usd: float


class LLMCache:
    """
    Intelligent LLM response caching system
    AI Planet Feature: Up to 60x cost reduction
    """

    def __init__(
        self,
        max_size: int = 10000,
        ttl_seconds: int = 3600,
        enable_semantic_matching: bool = True,
        semantic_threshold: float = 0.95
    ):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.enable_semantic_matching = enable_semantic_matching
        self.semantic_threshold = semantic_threshold

        self._cache: Dict[str, CacheEntry] = {}
        self._embedding_cache: Dict[str, Any] = {}  # For semantic matching

        # Analytics
        self.total_requests = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self.total_tokens_saved = 0
        self.total_cost_saved_usd = 0.0

        logger.info(f"LLM Cache initialized (max_size={max_size}, ttl={ttl_seconds}s)")

    def _generate_cache_key(
        self,
        prompt: str,
        model: str,
        temperature: float,
        **kwargs
    ) -> str:
        """Generate cache key from prompt + params"""
        # Include all relevant parameters
        cache_str = f"{prompt}|{model}|{temperature:.2f}"

        # Add other parameters
        for key, value in sorted(kwargs.items()):
            if key not in ['use_cache', 'stream']:
                cache_str += f"|{key}:{value}"

        return hashlib.sha256(cache_str.encode()).hexdigest()

    def _is_expired(self, entry: CacheEntry) -> bool:
        """Check if cache entry has expired"""
        age = (datetime.utcnow() - entry.created_at).total_seconds()
        return age > self.ttl_seconds

    def _evict_oldest(self):
        """Evict oldest cache entry when max size reached"""
        if not self._cache:
            return

        # Find oldest entry
        oldest_key = min(
            self._cache.keys(),
            key=lambda k: self._cache[k].last_accessed
        )

        del self._cache[oldest_key]
        logger.debug(f"Evicted cache entry: {oldest_key}")

    def _find_semantic_match(
        self,
        prompt: str,
        model: str,
        temperature: float
    ) -> Optional[CacheEntry]:
        """Find semantically similar cached response"""

        if not self.enable_semantic_matching:
            return None

        # Generate embedding for current prompt
        try:
            from sentence_transformers import SentenceTransformer

            # Lazy load embedding model
            if not hasattr(self, '_embedding_model'):
                self._embedding_model = SentenceTransformer(
                    'paraphrase-multilingual-mpnet-base-v2'
                )

            current_embedding = self._embedding_model.encode(prompt)

            # Find best match in cache
            best_match = None
            best_similarity = 0.0

            for entry in self._cache.values():
                # Only compare same model + similar temperature
                if entry.model != model or abs(entry.temperature - temperature) > 0.1:
                    continue

                # Check if we have embedding cached
                if entry.key not in self._embedding_cache:
                    entry_embedding = self._embedding_model.encode(entry.prompt)
                    self._embedding_cache[entry.key] = entry_embedding
                else:
                    entry_embedding = self._embedding_cache[entry.key]

                # Calculate cosine similarity
                from sklearn.metrics.pairwise import cosine_similarity
                similarity = cosine_similarity(
                    [current_embedding],
                    [entry_embedding]
                )[0][0]

                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match = entry

            # Return if above threshold
            if best_similarity >= self.semantic_threshold:
                logger.info(f"Semantic cache hit! Similarity: {best_similarity:.3f}")
                return best_match

        except Exception as e:
            logger.warning(f"Semantic matching failed: {e}")

        return None

    def get(
        self,
        prompt: str,
        model: str,
        temperature: float,
        **kwargs
    ) -> Optional[str]:
        """
        Get cached response if available

        Returns:
            Cached response or None if not found/expired
        """
        self.total_requests += 1

        # Try exact match first
        cache_key = self._generate_cache_key(prompt, model, temperature, **kwargs)

        if cache_key in self._cache:
            entry = self._cache[cache_key]

            # Check if expired
            if self._is_expired(entry):
                del self._cache[cache_key]
                logger.debug(f"Cache entry expired: {cache_key}")
            else:
                # Cache hit!
                entry.last_accessed = datetime.utcnow()
                entry.access_count += 1

                self.cache_hits += 1
                self.total_tokens_saved += entry.tokens_saved
                self.total_cost_saved_usd += entry.cost_saved_usd

                logger.info(f"Cache HIT (exact match) - Saved ${entry.cost_saved_usd:.4f}")
                return entry.response

        # Try semantic match
        semantic_match = self._find_semantic_match(prompt, model, temperature)
        if semantic_match:
            semantic_match.last_accessed = datetime.utcnow()
            semantic_match.access_count += 1

            self.cache_hits += 1
            self.total_tokens_saved += semantic_match.tokens_saved
            self.total_cost_saved_usd += semantic_match.cost_saved_usd

            return semantic_match.response

        # Cache miss
        self.cache_misses += 1
        logger.debug(f"Cache MISS for prompt: {prompt[:50]}...")
        return None

    def set(
        self,
        prompt: str,
        response: str,
        model: str,
        temperature: float,
        tokens_used: int,
        cost_usd: float,
        **kwargs
    ):
        """Store response in cache"""

        # Check if cache is full
        if len(self._cache) >= self.max_size:
            self._evict_oldest()

        cache_key = self._generate_cache_key(prompt, model, temperature, **kwargs)

        entry = CacheEntry(
            key=cache_key,
            prompt=prompt,
            response=response,
            model=model,
            temperature=temperature,
            created_at=datetime.utcnow(),
            last_accessed=datetime.utcnow(),
            access_count=0,
            tokens_saved=tokens_used,
            cost_saved_usd=cost_usd
        )

        self._cache[cache_key] = entry
        logger.debug(f"Cached response for prompt: {prompt[:50]}...")

    def clear(self):
        """Clear all cache entries"""
        self._cache.clear()
        self._embedding_cache.clear()
        logger.info("Cache cleared")

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""

        cache_hit_rate = (self.cache_hits / self.total_requests * 100) if self.total_requests > 0 else 0

        # Calculate cost savings multiplier
        if self.cache_misses > 0:
            total_cost_without_cache = self.total_cost_saved_usd + (self.cache_misses * 0.001)  # Estimate
            savings_multiplier = total_cost_without_cache / (total_cost_without_cache - self.total_cost_saved_usd) if total_cost_without_cache > self.total_cost_saved_usd else 1.0
        else:
            savings_multiplier = 1.0

        return {
            "cache_size": len(self._cache),
            "max_size": self.max_size,
            "total_requests": self.total_requests,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "hit_rate_percent": cache_hit_rate,
            "total_tokens_saved": self.total_tokens_saved,
            "total_cost_saved_usd": self.total_cost_saved_usd,
            "cost_savings_multiplier": f"{savings_multiplier:.1f}x",
            "semantic_matching_enabled": self.enable_semantic_matching
        }

    def get_top_cached_prompts(self, top_n: int = 10) -> List[Dict[str, Any]]:
        """Get most frequently cached prompts"""

        sorted_entries = sorted(
            self._cache.values(),
            key=lambda e: e.access_count,
            reverse=True
        )

        return [
            {
                "prompt": entry.prompt[:100] + "..." if len(entry.prompt) > 100 else entry.prompt,
                "model": entry.model,
                "access_count": entry.access_count,
                "cost_saved_usd": entry.cost_saved_usd * entry.access_count,
                "created_at": entry.created_at.isoformat()
            }
            for entry in sorted_entries[:top_n]
        ]

    def export_cache(self, file_path: str):
        """Export cache to file"""
        cache_data = {
            "metadata": {
                "exported_at": datetime.utcnow().isoformat(),
                "cache_size": len(self._cache),
                "stats": self.get_stats()
            },
            "entries": [
                {
                    "prompt": entry.prompt,
                    "response": entry.response,
                    "model": entry.model,
                    "temperature": entry.temperature,
                    "created_at": entry.created_at.isoformat(),
                    "access_count": entry.access_count
                }
                for entry in self._cache.values()
            ]
        }

        with open(file_path, 'w') as f:
            json.dump(cache_data, f, indent=2)

        logger.info(f"Cache exported to: {file_path}")

    def import_cache(self, file_path: str):
        """Import cache from file"""
        with open(file_path, 'r') as f:
            cache_data = json.load(f)

        for entry_data in cache_data['entries']:
            cache_key = self._generate_cache_key(
                entry_data['prompt'],
                entry_data['model'],
                entry_data['temperature']
            )

            entry = CacheEntry(
                key=cache_key,
                prompt=entry_data['prompt'],
                response=entry_data['response'],
                model=entry_data['model'],
                temperature=entry_data['temperature'],
                created_at=datetime.fromisoformat(entry_data['created_at']),
                last_accessed=datetime.utcnow(),
                access_count=entry_data['access_count'],
                tokens_saved=0,  # Unknown from import
                cost_saved_usd=0.0
            )

            self._cache[cache_key] = entry

        logger.info(f"Cache imported from: {file_path} ({len(cache_data['entries'])} entries)")


# Global cache instance
llm_cache = LLMCache(
    max_size=10000,
    ttl_seconds=3600,  # 1 hour
    enable_semantic_matching=True,
    semantic_threshold=0.95
)
