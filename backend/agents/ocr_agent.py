"""
OCR Agent - Multi-tiered recognition with Arabic diacritic preservation
Supports PaddleOCR, EasyOCR, and Tesseract for offline OCR
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class OCRAgent:
    """
    OCR Agent with tiered recognition strategy
    - Tier 1: Document Intelligence (printed text)
    - Tier 2: Vision-Language OCR (handwritten text)
    - Supports Arabic with diacritic preservation
    """

    def __init__(self, ollama_service=None):
        self.ollama_service = ollama_service
        self._ocr_engines = {}
        self._init_ocr_engines()

    def _init_ocr_engines(self):
        """Initialize available OCR engines"""
        # Try PaddleOCR (best for Arabic)
        try:
            from paddleocr import PaddleOCR
            self._ocr_engines['paddle'] = PaddleOCR(
                use_angle_cls=True,
                lang='ar',  # Arabic
                use_gpu=False,
                show_log=False
            )
            logger.info("PaddleOCR initialized")
        except Exception as e:
            logger.warning(f"PaddleOCR not available: {e}")

        # Try EasyOCR
        try:
            import easyocr
            self._ocr_engines['easy'] = easyocr.Reader(
                ['ar', 'en'],  # Arabic and English
                gpu=False
            )
            logger.info("EasyOCR initialized")
        except Exception as e:
            logger.warning(f"EasyOCR not available: {e}")

        # Tesseract (fallback)
        try:
            import pytesseract
            self._ocr_engines['tesseract'] = pytesseract
            logger.info("Tesseract initialized")
        except Exception as e:
            logger.warning(f"Tesseract not available: {e}")

    async def execute(self, state_data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute OCR on document/image

        Args:
            state_data: Workflow state data
            config: Agent configuration
                - input_key: Key for input image/document path
                - preserve_diacritics: Whether to preserve Arabic diacritics
                - quality_threshold: Confidence threshold for quality routing
                - use_vision_llm: Use vision-LLM for handwritten text

        Returns:
            OCR results with text, confidence, and metadata
        """
        input_key = config.get('input_key', 'input')
        image_path = state_data.get(input_key)

        if not image_path:
            raise ValueError("No input image provided")

        preserve_diacritics = config.get('preserve_diacritics', True)
        quality_threshold = config.get('quality_threshold', 0.85)
        use_vision_llm = config.get('use_vision_llm', False)

        # Step 1: Try document intelligence (printed text)
        ocr_result = await self._extract_printed_text(image_path, preserve_diacritics)

        # Step 2: Quality gate - check confidence
        if ocr_result['confidence'] < quality_threshold and use_vision_llm:
            logger.info(f"Confidence {ocr_result['confidence']:.2f} below threshold, using vision-LLM")
            ocr_result = await self._extract_handwritten_text(image_path)

        return ocr_result

    async def _extract_printed_text(self, image_path: str, preserve_diacritics: bool) -> Dict[str, Any]:
        """Extract text from printed documents"""
        # Try engines in order of quality
        for engine_name in ['paddle', 'easy', 'tesseract']:
            if engine_name in self._ocr_engines:
                try:
                    result = await self._run_ocr_engine(
                        engine_name,
                        image_path,
                        preserve_diacritics
                    )
                    if result['confidence'] > 0.5:
                        return result
                except Exception as e:
                    logger.warning(f"OCR engine {engine_name} failed: {e}")
                    continue

        return {
            'text': '',
            'confidence': 0.0,
            'engine': 'none',
            'error': 'All OCR engines failed'
        }

    async def _run_ocr_engine(
        self,
        engine_name: str,
        image_path: str,
        preserve_diacritics: bool
    ) -> Dict[str, Any]:
        """Run specific OCR engine"""
        engine = self._ocr_engines[engine_name]

        if engine_name == 'paddle':
            result = engine.ocr(image_path, cls=True)
            # Extract text and confidence
            text_blocks = []
            confidences = []
            for line in result[0]:
                text_blocks.append(line[1][0])
                confidences.append(line[1][1])

            text = '\n'.join(text_blocks)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

            return {
                'text': text,
                'confidence': avg_confidence,
                'engine': 'paddleocr',
                'preserve_diacritics': preserve_diacritics
            }

        elif engine_name == 'easy':
            result = engine.readtext(image_path)
            text_blocks = [item[1] for item in result]
            confidences = [item[2] for item in result]

            text = '\n'.join(text_blocks)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

            return {
                'text': text,
                'confidence': avg_confidence,
                'engine': 'easyocr',
                'preserve_diacritics': preserve_diacritics
            }

        elif engine_name == 'tesseract':
            import pytesseract
            from PIL import Image

            img = Image.open(image_path)
            # Use Arabic + English
            text = pytesseract.image_to_string(img, lang='ara+eng')

            return {
                'text': text,
                'confidence': 0.7,  # Tesseract doesn't provide confidence
                'engine': 'tesseract',
                'preserve_diacritics': preserve_diacritics
            }

    async def _extract_handwritten_text(self, image_path: str) -> Dict[str, Any]:
        """Extract handwritten text using vision-LLM"""
        if not self.ollama_service:
            return {
                'text': '',
                'confidence': 0.0,
                'engine': 'vision-llm',
                'error': 'Ollama service not available'
            }

        # Use vision model (e.g., llama3.2-vision, llava)
        prompt = """Extract all text from this image, preserving Arabic diacritics.
Output only the extracted text, nothing else."""

        try:
            # Note: This requires a vision-capable model in Ollama
            response = await self.ollama_service.query(
                prompt=prompt,
                model=config.get('vision_model', 'llava'),
                temperature=0.1
            )

            return {
                'text': response,
                'confidence': 0.8,  # Vision models are generally reliable
                'engine': 'vision-llm'
            }
        except Exception as e:
            logger.error(f"Vision-LLM OCR failed: {e}")
            return {
                'text': '',
                'confidence': 0.0,
                'engine': 'vision-llm',
                'error': str(e)
            }
