"""
Grounded Answer Agent - Generate answers with citations from knowledge base
For HR Assistant and RAG workflows
"""

from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class GroundedAnswerAgent:
    """Generate answers grounded in retrieved documents with citations"""

    def __init__(self, ollama_service):
        self.ollama_service = ollama_service

    async def execute(self, state_data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate grounded answer with citations

        Args:
            state_data: Workflow state data
            config: Agent configuration
                - input_key: Key for retrieved documents
                - question_key: Key for user question
                - role_filter: User role for filtered answers

        Returns:
            Answer with citations and source documents
        """
        question_key = config.get('question_key', 'input')
        retrieved_key = config.get('retrieved_key', 'retrieved_docs')

        question = state_data.get(question_key, {}).get('question', '')
        retrieved_docs = state_data.get(retrieved_key, [])

        if not retrieved_docs:
            return {
                'answer': 'I could not find relevant information to answer your question.',
                'citations': [],
                'confidence': 0.0
            }

        # Build context from retrieved documents
        context = '\n\n'.join([
            f"[Document {i+1}]: {doc.get('text', '')}"
            for i, doc in enumerate(retrieved_docs[:5])
        ])

        prompt = f"""Answer the question using ONLY information from the provided documents.
Include citations [Document N] for each fact.

Question: {question}

Documents:
{context}

Provide:
1. Direct answer
2. Citations for each fact
3. Confidence level

JSON format:
{{
  "answer": "answer with [Document N] citations",
  "citations": [
    {{"document_id": 1, "quote": "relevant quote", "relevance": "why this supports the answer"}}
  ],
  "confidence": 0.0-1.0
}}"""

        response = await self.ollama_service.query(
            prompt=prompt,
            model=config.get('model', 'llama3.2:3b'),
            temperature=0.2,
            num_predict=1024
        )

        # Parse JSON
        import json
        import re
        try:
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                # Add source documents
                result['source_documents'] = retrieved_docs
                return result
        except Exception as e:
            logger.error(f"Parse failed: {e}")

        return {'answer': response, 'citations': [], 'confidence': 0.5}
