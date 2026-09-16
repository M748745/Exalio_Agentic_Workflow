"""
RAG Evaluation Framework (BeyondLLM / AI Planet Feature)
Comprehensive metrics for evaluating RAG pipelines:
- Context Relevance
- Answer Relevance
- Groundedness
- Ground Truth
- Hit Rate (embeddings)
- MRR (Mean Reciprocal Rank)
"""

from typing import Dict, Any, List, Optional
import numpy as np
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class RAGEvaluationResult:
    """Results from RAG evaluation"""
    context_relevance: float
    answer_relevance: float
    groundedness: float
    ground_truth_score: Optional[float] = None
    faithfulness: float = 0.0
    completeness: float = 0.0
    overall_score: float = 0.0


@dataclass
class EmbeddingEvaluationResult:
    """Results from embedding evaluation"""
    hit_rate: float
    mrr: float  # Mean Reciprocal Rank
    precision_at_k: Dict[int, float]
    recall_at_k: Dict[int, float]
    ndcg: float


class RAGEvaluator:
    """
    Evaluate RAG pipeline performance
    Based on AI Planet's BeyondLLM evaluation framework
    """

    def __init__(self, llm_provider=None):
        self.llm_provider = llm_provider

    async def evaluate(
        self,
        query: str,
        retrieved_contexts: List[str],
        generated_answer: str,
        ground_truth: Optional[str] = None
    ) -> RAGEvaluationResult:
        """
        Comprehensive RAG evaluation

        Args:
            query: User query
            retrieved_contexts: Retrieved documents
            generated_answer: LLM-generated answer
            ground_truth: Optional reference answer

        Returns:
            RAGEvaluationResult with all metrics
        """

        # Evaluate context relevance
        context_relevance = await self._evaluate_context_relevance(query, retrieved_contexts)

        # Evaluate answer relevance
        answer_relevance = await self._evaluate_answer_relevance(query, generated_answer)

        # Evaluate groundedness
        groundedness = await self._evaluate_groundedness(retrieved_contexts, generated_answer)

        # Evaluate faithfulness (no hallucinations)
        faithfulness = await self._evaluate_faithfulness(retrieved_contexts, generated_answer)

        # Evaluate completeness
        completeness = await self._evaluate_completeness(query, generated_answer)

        # Optional: Ground truth comparison
        ground_truth_score = None
        if ground_truth:
            ground_truth_score = await self._evaluate_ground_truth(generated_answer, ground_truth)

        # Compute overall score
        overall_score = (
            context_relevance * 0.25 +
            answer_relevance * 0.25 +
            groundedness * 0.25 +
            faithfulness * 0.15 +
            completeness * 0.10
        )

        return RAGEvaluationResult(
            context_relevance=context_relevance,
            answer_relevance=answer_relevance,
            groundedness=groundedness,
            ground_truth_score=ground_truth_score,
            faithfulness=faithfulness,
            completeness=completeness,
            overall_score=overall_score
        )

    async def _evaluate_context_relevance(self, query: str, contexts: List[str]) -> float:
        """Evaluate how relevant retrieved contexts are to the query"""

        if not contexts:
            return 0.0

        if self.llm_provider:
            # Use LLM as evaluator
            prompt = f"""Rate the relevance of each context to the query (0-1 scale).

Query: {query}

Contexts:
{chr(10).join([f"{i+1}. {ctx[:200]}" for i, ctx in enumerate(contexts)])}

Respond with JSON: {{"scores": [0.9, 0.7, ...], "average": 0.8}}"""

            response = await self.llm_provider.query(
                prompt=prompt,
                temperature=0.1,
                max_tokens=256
            )

            # Parse JSON
            import json
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                return result.get("average", 0.5)

        # Fallback: Simple keyword overlap
        from difflib import SequenceMatcher
        scores = [SequenceMatcher(None, query, ctx).ratio() for ctx in contexts]
        return sum(scores) / len(scores) if scores else 0.0

    async def _evaluate_answer_relevance(self, query: str, answer: str) -> float:
        """Evaluate how well the answer addresses the query"""

        if self.llm_provider:
            prompt = f"""Rate how well this answer addresses the query (0-1 scale).

Query: {query}

Answer: {answer}

Respond with JSON: {{"relevance": 0.9, "explanation": "..."}}"""

            response = await self.llm_provider.query(
                prompt=prompt,
                temperature=0.1,
                max_tokens=256
            )

            import json
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                return result.get("relevance", 0.5)

        # Fallback
        from difflib import SequenceMatcher
        return SequenceMatcher(None, query, answer).ratio()

    async def _evaluate_groundedness(self, contexts: List[str], answer: str) -> float:
        """Evaluate if answer is grounded in retrieved contexts"""

        if not contexts:
            return 0.0

        if self.llm_provider:
            prompt = f"""Rate how well the answer is grounded in the provided contexts (0-1 scale).
Answer should only contain information present in contexts.

Contexts:
{chr(10).join([f"{i+1}. {ctx[:200]}" for i, ctx in enumerate(contexts)])}

Answer: {answer}

Respond with JSON: {{"groundedness": 0.9, "unsupported_claims": []}}"""

            response = await self.llm_provider.query(
                prompt=prompt,
                temperature=0.1,
                max_tokens=256
            )

            import json
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                return result.get("groundedness", 0.5)

        # Fallback: Check overlap with contexts
        combined_contexts = " ".join(contexts)
        answer_words = set(answer.lower().split())
        context_words = set(combined_contexts.lower().split())
        overlap = len(answer_words & context_words)
        return overlap / len(answer_words) if answer_words else 0.0

    async def _evaluate_faithfulness(self, contexts: List[str], answer: str) -> float:
        """Evaluate if answer is faithful (no hallucinations)"""

        if self.llm_provider:
            prompt = f"""Check if the answer contains any hallucinations or unsupported claims (0-1 scale, 1=no hallucinations).

Contexts:
{chr(10).join([f"{i+1}. {ctx[:200]}" for i, ctx in enumerate(contexts)])}

Answer: {answer}

Respond with JSON: {{"faithfulness": 0.95, "hallucinations": []}}"""

            response = await self.llm_provider.query(
                prompt=prompt,
                temperature=0.1,
                max_tokens=256
            )

            import json
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                return result.get("faithfulness", 0.5)

        # Fallback
        return await self._evaluate_groundedness(contexts, answer)

    async def _evaluate_completeness(self, query: str, answer: str) -> float:
        """Evaluate if answer fully addresses the query"""

        if self.llm_provider:
            prompt = f"""Rate how completely the answer addresses the query (0-1 scale).

Query: {query}

Answer: {answer}

Respond with JSON: {{"completeness": 0.9}}"""

            response = await self.llm_provider.query(
                prompt=prompt,
                temperature=0.1,
                max_tokens=128
            )

            import json
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                return result.get("completeness", 0.5)

        return 0.7  # Default

    async def _evaluate_ground_truth(self, answer: str, ground_truth: str) -> float:
        """Compare generated answer to ground truth"""

        if self.llm_provider:
            prompt = f"""Rate the similarity between the generated answer and ground truth (0-1 scale).

Generated: {answer}

Ground Truth: {ground_truth}

Respond with JSON: {{"similarity": 0.85}}"""

            response = await self.llm_provider.query(
                prompt=prompt,
                temperature=0.1,
                max_tokens=128
            )

            import json
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                return result.get("similarity", 0.5)

        # Fallback: Semantic similarity
        from difflib import SequenceMatcher
        return SequenceMatcher(None, answer, ground_truth).ratio()


class EmbeddingEvaluator:
    """
    Evaluate embedding/retrieval performance
    Metrics: Hit Rate, MRR, Precision@K, Recall@K, NDCG
    """

    def evaluate(
        self,
        query: str,
        retrieved_docs: List[Dict[str, Any]],
        relevant_docs: List[str],
        k_values: List[int] = [1, 3, 5, 10]
    ) -> EmbeddingEvaluationResult:
        """
        Evaluate retrieval quality

        Args:
            query: Search query
            retrieved_docs: Retrieved documents (ordered by relevance)
            relevant_docs: Ground truth relevant document IDs
            k_values: K values for Precision@K and Recall@K

        Returns:
            EmbeddingEvaluationResult
        """

        retrieved_ids = [doc.get('id', str(i)) for i, doc in enumerate(retrieved_docs)]

        # Hit Rate: Was at least one relevant doc retrieved?
        hit_rate = 1.0 if any(doc_id in relevant_docs for doc_id in retrieved_ids) else 0.0

        # MRR: Mean Reciprocal Rank
        mrr = self._calculate_mrr(retrieved_ids, relevant_docs)

        # Precision@K and Recall@K
        precision_at_k = {}
        recall_at_k = {}
        for k in k_values:
            precision_at_k[k] = self._calculate_precision_at_k(retrieved_ids, relevant_docs, k)
            recall_at_k[k] = self._calculate_recall_at_k(retrieved_ids, relevant_docs, k)

        # NDCG
        ndcg = self._calculate_ndcg(retrieved_ids, relevant_docs)

        return EmbeddingEvaluationResult(
            hit_rate=hit_rate,
            mrr=mrr,
            precision_at_k=precision_at_k,
            recall_at_k=recall_at_k,
            ndcg=ndcg
        )

    def _calculate_mrr(self, retrieved: List[str], relevant: List[str]) -> float:
        """Calculate Mean Reciprocal Rank"""
        for i, doc_id in enumerate(retrieved):
            if doc_id in relevant:
                return 1.0 / (i + 1)
        return 0.0

    def _calculate_precision_at_k(self, retrieved: List[str], relevant: List[str], k: int) -> float:
        """Calculate Precision@K"""
        retrieved_at_k = retrieved[:k]
        relevant_retrieved = sum(1 for doc_id in retrieved_at_k if doc_id in relevant)
        return relevant_retrieved / k if k > 0 else 0.0

    def _calculate_recall_at_k(self, retrieved: List[str], relevant: List[str], k: int) -> float:
        """Calculate Recall@K"""
        retrieved_at_k = retrieved[:k]
        relevant_retrieved = sum(1 for doc_id in retrieved_at_k if doc_id in relevant)
        return relevant_retrieved / len(relevant) if relevant else 0.0

    def _calculate_ndcg(self, retrieved: List[str], relevant: List[str], k: int = 10) -> float:
        """Calculate Normalized Discounted Cumulative Gain@K"""
        retrieved_at_k = retrieved[:k]

        # DCG
        dcg = 0.0
        for i, doc_id in enumerate(retrieved_at_k):
            relevance = 1.0 if doc_id in relevant else 0.0
            dcg += relevance / np.log2(i + 2)  # i+2 because i starts at 0

        # IDCG (ideal DCG)
        ideal_relevance = [1.0] * min(len(relevant), k) + [0.0] * max(0, k - len(relevant))
        idcg = sum(rel / np.log2(i + 2) for i, rel in enumerate(ideal_relevance))

        return dcg / idcg if idcg > 0 else 0.0
