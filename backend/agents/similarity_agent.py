"""
Similarity Agent - Match content against corpus using semantic, structural, and stylistic similarity
Uses local embeddings (sentence-transformers) for offline operation
"""

from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import logging

logger = logging.getLogger(__name__)


class SimilarityAgent:
    """
    Multi-dimensional similarity matching
    - Textual similarity (semantic)
    - Semantic similarity (embeddings)
    - Structural similarity (format, layout)
    - Stylistic similarity (writing style)
    """

    def __init__(self, ollama_service=None):
        self.ollama_service = ollama_service
        self._embedding_model = None
        self._init_embedding_model()

    def _init_embedding_model(self):
        """Initialize local embedding model"""
        try:
            from sentence_transformers import SentenceTransformer
            # Use multilingual model for Arabic + English
            self._embedding_model = SentenceTransformer(
                'paraphrase-multilingual-mpnet-base-v2'
            )
            logger.info("Sentence transformer model loaded")
        except Exception as e:
            logger.warning(f"Failed to load embedding model: {e}")

    async def execute(self, state_data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Find similar content in corpus

        Args:
            state_data: Workflow state data
            config: Agent configuration
                - input_key: Key for input text
                - corpus_key: Key for corpus data
                - top_k: Number of top matches to return
                - similarity_types: List of similarity types to compute

        Returns:
            Similarity results with matches and scores
        """
        input_key = config.get('input_key', 'ocr_output')
        corpus_key = config.get('corpus_key', 'corpus')
        top_k = config.get('top_k', 5)
        similarity_types = config.get('similarity_types', ['semantic', 'textual', 'structural'])

        input_text = state_data.get(input_key, {}).get('text', '')
        corpus = state_data.get(corpus_key, [])

        if not input_text or not corpus:
            return {
                'matches': [],
                'error': 'Missing input text or corpus'
            }

        # Compute similarities
        matches = []
        for similarity_type in similarity_types:
            if similarity_type == 'semantic':
                matches.extend(await self._semantic_similarity(input_text, corpus, top_k))
            elif similarity_type == 'textual':
                matches.extend(await self._textual_similarity(input_text, corpus, top_k))
            elif similarity_type == 'structural':
                matches.extend(await self._structural_similarity(input_text, corpus, top_k))
            elif similarity_type == 'stylistic':
                matches.extend(await self._stylistic_similarity(input_text, corpus, top_k))

        # Aggregate and rank matches
        aggregated = self._aggregate_matches(matches, top_k)

        return {
            'matches': aggregated,
            'input_text': input_text,
            'corpus_size': len(corpus)
        }

    async def _semantic_similarity(
        self,
        query: str,
        corpus: List[Dict[str, Any]],
        top_k: int
    ) -> List[Dict[str, Any]]:
        """Compute semantic similarity using embeddings"""
        if not self._embedding_model:
            return []

        try:
            # Generate embeddings
            query_embedding = self._embedding_model.encode([query])[0]
            corpus_texts = [item.get('text', '') for item in corpus]
            corpus_embeddings = self._embedding_model.encode(corpus_texts)

            # Compute cosine similarity
            from sklearn.metrics.pairwise import cosine_similarity
            similarities = cosine_similarity([query_embedding], corpus_embeddings)[0]

            # Get top-k matches
            top_indices = np.argsort(similarities)[-top_k:][::-1]

            matches = []
            for idx in top_indices:
                matches.append({
                    'corpus_id': corpus[idx].get('id', str(idx)),
                    'text': corpus[idx].get('text', ''),
                    'score': float(similarities[idx]),
                    'type': 'semantic'
                })

            return matches

        except Exception as e:
            logger.error(f"Semantic similarity failed: {e}")
            return []

    async def _textual_similarity(
        self,
        query: str,
        corpus: List[Dict[str, Any]],
        top_k: int
    ) -> List[Dict[str, Any]]:
        """Compute textual similarity using character/word overlap"""
        from difflib import SequenceMatcher

        matches = []
        for idx, item in enumerate(corpus):
            corpus_text = item.get('text', '')
            similarity = SequenceMatcher(None, query, corpus_text).ratio()

            matches.append({
                'corpus_id': item.get('id', str(idx)),
                'text': corpus_text,
                'score': similarity,
                'type': 'textual'
            })

        # Sort and return top-k
        matches.sort(key=lambda x: x['score'], reverse=True)
        return matches[:top_k]

    async def _structural_similarity(
        self,
        query: str,
        corpus: List[Dict[str, Any]],
        top_k: int
    ) -> List[Dict[str, Any]]:
        """Compute structural similarity (line breaks, formatting, etc.)"""
        def get_structure_features(text: str) -> Dict[str, float]:
            lines = text.split('\n')
            return {
                'line_count': len(lines),
                'avg_line_length': sum(len(l) for l in lines) / len(lines) if lines else 0,
                'has_bullets': int(any('•' in l or '-' in l[:2] for l in lines)),
                'has_numbers': int(any(l.strip()[:1].isdigit() for l in lines))
            }

        query_features = get_structure_features(query)

        matches = []
        for idx, item in enumerate(corpus):
            corpus_text = item.get('text', '')
            corpus_features = get_structure_features(corpus_text)

            # Compute feature similarity
            similarity = 1.0 - sum(
                abs(query_features[k] - corpus_features[k]) / max(query_features[k], corpus_features[k], 1)
                for k in query_features.keys()
            ) / len(query_features)

            matches.append({
                'corpus_id': item.get('id', str(idx)),
                'text': corpus_text,
                'score': max(0, similarity),
                'type': 'structural'
            })

        matches.sort(key=lambda x: x['score'], reverse=True)
        return matches[:top_k]

    async def _stylistic_similarity(
        self,
        query: str,
        corpus: List[Dict[str, Any]],
        top_k: int
    ) -> List[Dict[str, Any]]:
        """Compute stylistic similarity using LLM"""
        if not self.ollama_service:
            return []

        try:
            # Use LLM to analyze writing style
            prompt = f"""Analyze the writing style of the following text and rate its similarity (0-1) to the query.
Consider: formality, vocabulary complexity, sentence structure, tone.

Query text: {query[:500]}

Corpus texts:
"""
            for idx, item in enumerate(corpus[:top_k]):
                prompt += f"\n{idx+1}. {item.get('text', '')[:300]}"

            prompt += "\n\nReturn only JSON format: [{\"corpus_id\": id, \"score\": similarity}]"

            response = await self.ollama_service.query(
                prompt=prompt,
                temperature=0.1,
                num_predict=512
            )

            # Parse JSON response
            import json
            import re
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                results = json.loads(json_match.group())
                matches = []
                for result in results:
                    corpus_id = result['corpus_id']
                    matches.append({
                        'corpus_id': corpus_id,
                        'text': corpus[int(corpus_id)-1].get('text', ''),
                        'score': result['score'],
                        'type': 'stylistic'
                    })
                return matches

        except Exception as e:
            logger.error(f"Stylistic similarity failed: {e}")

        return []

    def _aggregate_matches(self, matches: List[Dict[str, Any]], top_k: int) -> List[Dict[str, Any]]:
        """Aggregate matches from different similarity types"""
        # Group by corpus_id
        aggregated = {}
        for match in matches:
            corpus_id = match['corpus_id']
            if corpus_id not in aggregated:
                aggregated[corpus_id] = {
                    'corpus_id': corpus_id,
                    'text': match['text'],
                    'scores': {},
                    'overall_score': 0.0
                }

            aggregated[corpus_id]['scores'][match['type']] = match['score']

        # Compute overall score (average)
        for item in aggregated.values():
            scores = list(item['scores'].values())
            item['overall_score'] = sum(scores) / len(scores) if scores else 0.0

        # Sort by overall score
        result = list(aggregated.values())
        result.sort(key=lambda x: x['overall_score'], reverse=True)

        return result[:top_k]
