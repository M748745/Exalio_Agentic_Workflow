"""
Voice Integration Agent (AI Planet Feature)
Speech-to-text transcription supporting Arabic and English

Features:
- Whisper model support (OpenAI Whisper)
- Multi-language support (Arabic, English, 90+ languages)
- Multiple model sizes (tiny, base, small, medium, large)
- Audio preprocessing and enhancement
- Real-time and batch transcription
- Speaker diarization (optional)
- Timestamp generation
"""

from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from pathlib import Path
import logging
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class TranscriptionResult:
    """Speech-to-text transcription result"""
    text: str
    language: str
    confidence: float
    segments: List[Dict[str, Any]]  # Timestamped segments
    duration_seconds: float
    processing_time_seconds: float
    model_used: str


class VoiceIntegrationAgent:
    """
    Voice Integration Agent
    Speech-to-text using Whisper models (Arabic + English support)
    """

    SUPPORTED_LANGUAGES = [
        'ar',  # Arabic
        'en',  # English
        'fr', 'es', 'de', 'it', 'pt', 'ru', 'zh', 'ja', 'ko',
        # ... 90+ languages supported by Whisper
    ]

    MODEL_SIZES = {
        'tiny': 'whisper-tiny',      # 39M params, ~1GB RAM
        'base': 'whisper-base',      # 74M params, ~1GB RAM
        'small': 'whisper-small',    # 244M params, ~2GB RAM
        'medium': 'whisper-medium',  # 769M params, ~5GB RAM
        'large': 'whisper-large-v3', # 1550M params, ~10GB RAM
    }

    def __init__(
        self,
        model_size: str = 'base',
        device: str = 'cpu',  # 'cpu' or 'cuda'
        compute_type: str = 'int8'  # int8, int16, float16, float32
    ):
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self._model = None

        logger.info(f"Voice Integration Agent initialized (model={model_size}, device={device})")

    def _load_model(self):
        """Lazy load Whisper model"""
        if self._model is not None:
            return

        try:
            import faster_whisper
            from faster_whisper import WhisperModel

            logger.info(f"Loading Whisper model: {self.model_size}")

            # Load model using faster-whisper (optimized with CTranslate2)
            self._model = WhisperModel(
                self.model_size,
                device=self.device,
                compute_type=self.compute_type
            )

            logger.info("Whisper model loaded successfully")

        except ImportError:
            logger.warning("faster-whisper not available, falling back to openai-whisper")

            # Fallback to original OpenAI Whisper
            import whisper
            self._model = whisper.load_model(self.model_size, device=self.device)

        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            raise

    async def transcribe(
        self,
        audio_path: Union[str, Path],
        language: Optional[str] = None,
        task: str = 'transcribe',  # 'transcribe' or 'translate'
        return_timestamps: bool = True,
        word_level_timestamps: bool = False
    ) -> TranscriptionResult:
        """
        Transcribe audio to text

        Args:
            audio_path: Path to audio file (mp3, wav, m4a, etc.)
            language: Language code (e.g., 'ar', 'en'). Auto-detect if None
            task: 'transcribe' (same language) or 'translate' (to English)
            return_timestamps: Include segment timestamps
            word_level_timestamps: Include word-level timestamps

        Returns:
            TranscriptionResult with text and metadata
        """
        import time
        start_time = time.time()

        # Load model if not loaded
        self._load_model()

        audio_path = Path(audio_path)
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        logger.info(f"Transcribing audio: {audio_path} (language={language}, task={task})")

        # Get audio duration
        duration = self._get_audio_duration(audio_path)

        # Transcribe using faster-whisper or openai-whisper
        if hasattr(self._model, 'transcribe'):
            # faster-whisper API
            segments, info = self._model.transcribe(
                str(audio_path),
                language=language,
                task=task,
                word_timestamps=word_level_timestamps,
                vad_filter=True,  # Voice activity detection
                vad_parameters=dict(min_silence_duration_ms=500)
            )

            # Convert generator to list
            segments_list = []
            full_text = []

            for segment in segments:
                segment_dict = {
                    'start': segment.start,
                    'end': segment.end,
                    'text': segment.text,
                    'confidence': getattr(segment, 'avg_logprob', 0.0)
                }

                if word_level_timestamps and hasattr(segment, 'words'):
                    segment_dict['words'] = [
                        {
                            'word': word.word,
                            'start': word.start,
                            'end': word.end,
                            'confidence': getattr(word, 'probability', 0.0)
                        }
                        for word in segment.words
                    ]

                segments_list.append(segment_dict)
                full_text.append(segment.text)

            detected_language = info.language
            confidence = info.language_probability

        else:
            # Original OpenAI Whisper API
            result = self._model.transcribe(
                str(audio_path),
                language=language,
                task=task,
                word_timestamps=word_level_timestamps
            )

            full_text = [result['text']]
            segments_list = result.get('segments', [])
            detected_language = result.get('language', language or 'unknown')
            confidence = 0.95  # OpenAI Whisper doesn't provide confidence

        processing_time = time.time() - start_time

        return TranscriptionResult(
            text=' '.join(full_text).strip(),
            language=detected_language,
            confidence=confidence,
            segments=segments_list,
            duration_seconds=duration,
            processing_time_seconds=processing_time,
            model_used=self.model_size
        )

    async def transcribe_realtime(
        self,
        audio_stream,
        language: Optional[str] = None,
        chunk_duration_seconds: float = 5.0
    ):
        """
        Real-time transcription from audio stream

        Args:
            audio_stream: Audio stream iterator
            language: Language code
            chunk_duration_seconds: Process audio in chunks of this duration

        Yields:
            TranscriptionResult for each chunk
        """
        self._load_model()

        # Process audio stream in chunks
        chunk_buffer = []
        chunk_duration = 0

        async for audio_chunk in audio_stream:
            chunk_buffer.append(audio_chunk)
            chunk_duration += len(audio_chunk) / 16000  # Assuming 16kHz sample rate

            if chunk_duration >= chunk_duration_seconds:
                # Concatenate chunks
                audio_data = np.concatenate(chunk_buffer)

                # Transcribe chunk
                result = await self._transcribe_array(
                    audio_data,
                    language=language
                )

                yield result

                # Reset buffer
                chunk_buffer = []
                chunk_duration = 0

    async def _transcribe_array(
        self,
        audio_array: np.ndarray,
        language: Optional[str] = None
    ) -> TranscriptionResult:
        """Transcribe audio from numpy array"""
        import tempfile
        import soundfile as sf

        # Save to temporary WAV file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
            sf.write(tmp.name, audio_array, 16000)
            result = await self.transcribe(tmp.name, language=language)

        return result

    def _get_audio_duration(self, audio_path: Path) -> float:
        """Get audio duration in seconds"""
        try:
            import soundfile as sf
            info = sf.info(str(audio_path))
            return info.duration
        except Exception:
            # Fallback to librosa
            try:
                import librosa
                duration = librosa.get_duration(path=str(audio_path))
                return duration
            except Exception as e:
                logger.warning(f"Could not get audio duration: {e}")
                return 0.0

    async def detect_language(self, audio_path: Union[str, Path]) -> Dict[str, float]:
        """
        Detect spoken language in audio

        Returns:
            Dict of language codes -> confidence scores
        """
        self._load_model()

        if hasattr(self._model, 'detect_language'):
            # faster-whisper
            audio_path = str(audio_path)
            language, probability = self._model.detect_language(audio_path)
            return {language: probability}
        else:
            # OpenAI Whisper - transcribe first 30 seconds
            result = await self.transcribe(audio_path, language=None)
            return {result.language: result.confidence}

    async def translate_to_english(
        self,
        audio_path: Union[str, Path],
        source_language: Optional[str] = None
    ) -> TranscriptionResult:
        """
        Translate audio to English text

        Args:
            audio_path: Path to audio file
            source_language: Source language (auto-detect if None)

        Returns:
            TranscriptionResult with English translation
        """
        return await self.transcribe(
            audio_path,
            language=source_language,
            task='translate'  # Translate to English
        )

    async def add_punctuation(self, text: str, language: str = 'en') -> str:
        """
        Add punctuation to raw transcription

        Args:
            text: Raw transcription text
            language: Text language

        Returns:
            Text with proper punctuation
        """
        # This would use a separate punctuation restoration model
        # For now, return as-is (can be enhanced with models like deepmultilingualpunctuation)
        try:
            from deepmultilingualpunctuation import PunctuationModel

            model = PunctuationModel()
            punctuated = model.restore_punctuation(text)
            return punctuated
        except ImportError:
            logger.warning("Punctuation restoration not available (install deepmultilingualpunctuation)")
            return text

    async def diarize_speakers(
        self,
        audio_path: Union[str, Path],
        num_speakers: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Speaker diarization (identify who spoke when)

        Args:
            audio_path: Path to audio file
            num_speakers: Expected number of speakers (auto-detect if None)

        Returns:
            List of segments with speaker labels
        """
        try:
            from pyannote.audio import Pipeline

            # Load pretrained pipeline
            pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-3.1",
                use_auth_token=None  # Requires HuggingFace token
            )

            # Apply diarization
            diarization = pipeline(str(audio_path), num_speakers=num_speakers)

            # Convert to segments
            segments = []
            for turn, _, speaker in diarization.itertracks(yield_label=True):
                segments.append({
                    'start': turn.start,
                    'end': turn.end,
                    'speaker': speaker
                })

            return segments

        except ImportError:
            logger.warning("Speaker diarization not available (install pyannote-audio)")
            return []
        except Exception as e:
            logger.error(f"Speaker diarization failed: {e}")
            return []

    async def enhance_audio(
        self,
        audio_path: Union[str, Path],
        output_path: Optional[Path] = None
    ) -> Path:
        """
        Enhance audio quality (denoise, normalize)

        Args:
            audio_path: Input audio file
            output_path: Output path (auto-generate if None)

        Returns:
            Path to enhanced audio file
        """
        import soundfile as sf
        import noisereduce as nr

        # Load audio
        audio_data, sample_rate = sf.read(str(audio_path))

        # Reduce noise
        reduced_noise = nr.reduce_noise(y=audio_data, sr=sample_rate)

        # Normalize volume
        normalized = reduced_noise / np.max(np.abs(reduced_noise))

        # Save enhanced audio
        if output_path is None:
            audio_path = Path(audio_path)
            output_path = audio_path.parent / f"{audio_path.stem}_enhanced{audio_path.suffix}"

        sf.write(str(output_path), normalized, sample_rate)

        logger.info(f"Enhanced audio saved to: {output_path}")
        return output_path

    def get_supported_formats(self) -> List[str]:
        """Get list of supported audio formats"""
        return [
            'mp3', 'wav', 'flac', 'm4a', 'aac',
            'ogg', 'opus', 'wma', 'webm'
        ]

    def estimate_transcription_time(
        self,
        audio_duration_seconds: float
    ) -> float:
        """
        Estimate transcription processing time

        Returns:
            Estimated time in seconds
        """
        # Rough estimates based on model size (on CPU)
        speed_factors = {
            'tiny': 0.1,    # 10x faster than real-time
            'base': 0.2,    # 5x faster than real-time
            'small': 0.5,   # 2x faster than real-time
            'medium': 1.0,  # Real-time
            'large': 2.0,   # 2x slower than real-time
        }

        factor = speed_factors.get(self.model_size, 1.0)

        # Adjust for device
        if self.device == 'cuda':
            factor *= 0.2  # 5x speedup on GPU

        return audio_duration_seconds * factor
