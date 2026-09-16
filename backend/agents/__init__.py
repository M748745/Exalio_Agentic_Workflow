"""
Pre-built Agents for Agentic Workflow Platform
All agents use Ollama-based models (offline/local)
"""

from .ocr_agent import OCRAgent
from .similarity_agent import SimilarityAgent
from .ai_detection_agent import AIDetectionAgent
from .scoring_agent import ScoringAgent
from .rubric_agent import RubricAgent
from .benchmarking_agent import BenchmarkingAgent
from .recommendation_agent import RecommendationAgent
from .intent_agent import IntentAgent
from .entity_extraction_agent import EntityExtractionAgent
from .grounded_answer_agent import GroundedAnswerAgent

__all__ = [
    'OCRAgent',
    'SimilarityAgent',
    'AIDetectionAgent',
    'ScoringAgent',
    'RubricAgent',
    'BenchmarkingAgent',
    'RecommendationAgent',
    'IntentAgent',
    'EntityExtractionAgent',
    'GroundedAnswerAgent',
]
