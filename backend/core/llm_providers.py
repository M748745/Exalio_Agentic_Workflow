"""
Multi-LLM Provider Support (AI Planet Feature)
Supports 300k+ models from multiple providers:
- Ollama (local/Colab)
- OpenAI
- Anthropic Claude
- Cohere
- HuggingFace (300k+ models)
- Google VertexAI
"""

from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
import logging
import os

logger = logging.getLogger(__name__)


class LLMProvider(ABC):
    """Base class for LLM providers"""

    def __init__(self, api_key: Optional[str] = None, **kwargs):
        self.api_key = api_key
        self.config = kwargs

    @abstractmethod
    async def query(
        self,
        prompt: str,
        model: str,
        temperature: float = 0.3,
        max_tokens: int = 1024,
        **kwargs
    ) -> str:
        """Query the LLM"""
        pass

    @abstractmethod
    def list_models(self) -> List[str]:
        """List available models"""
        pass


class OllamaProvider(LLMProvider):
    """Ollama provider (local/Colab deployment)"""

    def __init__(self, base_url: str = "http://localhost:11434", **kwargs):
        super().__init__(**kwargs)
        self.base_url = base_url
        from ..core.ollama_service import OllamaService
        self.service = OllamaService(base_url)

    async def query(self, prompt: str, model: str, temperature: float = 0.3, max_tokens: int = 1024, **kwargs) -> str:
        return await self.service.query(
            prompt=prompt,
            model=model,
            temperature=temperature,
            num_predict=max_tokens,
            **kwargs
        )

    def list_models(self) -> List[str]:
        return self.service.list_models()


class OpenAIProvider(LLMProvider):
    """OpenAI provider (GPT-3.5, GPT-4, GPT-4o, o1, etc.)"""

    def __init__(self, api_key: Optional[str] = None, **kwargs):
        super().__init__(api_key or os.getenv("OPENAI_API_KEY"), **kwargs)

    async def query(self, prompt: str, model: str, temperature: float = 0.3, max_tokens: int = 1024, **kwargs) -> str:
        try:
            import openai
            openai.api_key = self.api_key

            response = await openai.ChatCompletion.acreate(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"OpenAI query failed: {e}")
            return f"[ERROR] {str(e)}"

    def list_models(self) -> List[str]:
        return [
            "gpt-3.5-turbo",
            "gpt-4",
            "gpt-4-turbo",
            "gpt-4o",
            "gpt-4o-mini",
            "o1-preview",
            "o1-mini"
        ]


class AnthropicProvider(LLMProvider):
    """Anthropic Claude provider (Claude 3 family)"""

    def __init__(self, api_key: Optional[str] = None, **kwargs):
        super().__init__(api_key or os.getenv("ANTHROPIC_API_KEY"), **kwargs)

    async def query(self, prompt: str, model: str, temperature: float = 0.3, max_tokens: int = 1024, **kwargs) -> str:
        try:
            import anthropic

            client = anthropic.Anthropic(api_key=self.api_key)

            response = await client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}],
                **kwargs
            )

            return response.content[0].text

        except Exception as e:
            logger.error(f"Anthropic query failed: {e}")
            return f"[ERROR] {str(e)}"

    def list_models(self) -> List[str]:
        return [
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307",
            "claude-3-5-sonnet-20241022",
            "claude-3-5-haiku-20241022"
        ]


class CohereProvider(LLMProvider):
    """Cohere provider"""

    def __init__(self, api_key: Optional[str] = None, **kwargs):
        super().__init__(api_key or os.getenv("COHERE_API_KEY"), **kwargs)

    async def query(self, prompt: str, model: str, temperature: float = 0.3, max_tokens: int = 1024, **kwargs) -> str:
        try:
            import cohere

            client = cohere.Client(self.api_key)

            response = client.chat(
                model=model,
                message=prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )

            return response.text

        except Exception as e:
            logger.error(f"Cohere query failed: {e}")
            return f"[ERROR] {str(e)}"

    def list_models(self) -> List[str]:
        return [
            "command",
            "command-light",
            "command-nightly",
            "command-r",
            "command-r-plus"
        ]


class HuggingFaceProvider(LLMProvider):
    """HuggingFace provider (300k+ models)"""

    def __init__(self, api_key: Optional[str] = None, **kwargs):
        super().__init__(api_key or os.getenv("HUGGINGFACE_API_KEY"), **kwargs)

    async def query(self, prompt: str, model: str, temperature: float = 0.3, max_tokens: int = 1024, **kwargs) -> str:
        try:
            import requests

            API_URL = f"https://api-inference.huggingface.co/models/{model}"
            headers = {"Authorization": f"Bearer {self.api_key}"}

            payload = {
                "inputs": prompt,
                "parameters": {
                    "temperature": temperature,
                    "max_new_tokens": max_tokens,
                    **kwargs
                }
            }

            response = requests.post(API_URL, headers=headers, json=payload, timeout=30)

            if response.status_code == 200:
                return response.json()[0]["generated_text"]
            else:
                return f"[ERROR] HTTP {response.status_code}"

        except Exception as e:
            logger.error(f"HuggingFace query failed: {e}")
            return f"[ERROR] {str(e)}"

    def list_models(self) -> List[str]:
        # Popular models (HF has 300k+ total)
        return [
            "meta-llama/Llama-3.2-3B-Instruct",
            "meta-llama/Llama-3.1-8B-Instruct",
            "mistralai/Mistral-7B-Instruct-v0.3",
            "mistralai/Mixtral-8x7B-Instruct-v0.1",
            "google/gemma-2-9b-it",
            "Qwen/Qwen2.5-7B-Instruct",
            "microsoft/Phi-3-mini-4k-instruct"
        ]


class VertexAIProvider(LLMProvider):
    """Google VertexAI provider (Gemini models)"""

    def __init__(self, project_id: str, location: str = "us-central1", **kwargs):
        super().__init__(**kwargs)
        self.project_id = project_id
        self.location = location

    async def query(self, prompt: str, model: str, temperature: float = 0.3, max_tokens: int = 1024, **kwargs) -> str:
        try:
            from google.cloud import aiplatform
            from vertexai.preview.generative_models import GenerativeModel

            aiplatform.init(project=self.project_id, location=self.location)

            model_instance = GenerativeModel(model)

            response = model_instance.generate_content(
                prompt,
                generation_config={
                    "temperature": temperature,
                    "max_output_tokens": max_tokens,
                    **kwargs
                }
            )

            return response.text

        except Exception as e:
            logger.error(f"VertexAI query failed: {e}")
            return f"[ERROR] {str(e)}"

    def list_models(self) -> List[str]:
        return [
            "gemini-1.5-pro",
            "gemini-1.5-flash",
            "gemini-1.0-pro",
            "gemini-pro-vision"
        ]


class LLMProviderManager:
    """
    Manages multiple LLM providers (AI Planet feature)
    Provides unified interface to 300k+ models
    """

    def __init__(self):
        self.providers: Dict[str, LLMProvider] = {}

    def register_provider(self, name: str, provider: LLMProvider):
        """Register an LLM provider"""
        self.providers[name] = provider
        logger.info(f"Registered LLM provider: {name}")

    def get_provider(self, name: str) -> Optional[LLMProvider]:
        """Get a provider by name"""
        return self.providers.get(name)

    async def query(
        self,
        prompt: str,
        provider: str,
        model: str,
        temperature: float = 0.3,
        max_tokens: int = 1024,
        **kwargs
    ) -> str:
        """Query any LLM provider"""
        llm_provider = self.get_provider(provider)

        if not llm_provider:
            raise ValueError(f"Provider not found: {provider}")

        return await llm_provider.query(
            prompt=prompt,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )

    def list_all_models(self) -> Dict[str, List[str]]:
        """List all models from all providers"""
        return {
            provider_name: provider.list_models()
            for provider_name, provider in self.providers.items()
        }

    def list_providers(self) -> List[str]:
        """List all registered providers"""
        return list(self.providers.keys())


# Global instance
llm_manager = LLMProviderManager()


def initialize_default_providers(config: Dict[str, Any]):
    """Initialize default LLM providers from config"""

    # Ollama (always available for local deployment)
    if config.get("ollama", {}).get("enabled", True):
        ollama_url = config["ollama"].get("url", "http://localhost:11434")
        llm_manager.register_provider("ollama", OllamaProvider(base_url=ollama_url))

    # OpenAI
    if config.get("openai", {}).get("enabled", False):
        api_key = config["openai"].get("api_key") or os.getenv("OPENAI_API_KEY")
        if api_key:
            llm_manager.register_provider("openai", OpenAIProvider(api_key=api_key))

    # Anthropic
    if config.get("anthropic", {}).get("enabled", False):
        api_key = config["anthropic"].get("api_key") or os.getenv("ANTHROPIC_API_KEY")
        if api_key:
            llm_manager.register_provider("anthropic", AnthropicProvider(api_key=api_key))

    # Cohere
    if config.get("cohere", {}).get("enabled", False):
        api_key = config["cohere"].get("api_key") or os.getenv("COHERE_API_KEY")
        if api_key:
            llm_manager.register_provider("cohere", CohereProvider(api_key=api_key))

    # HuggingFace
    if config.get("huggingface", {}).get("enabled", False):
        api_key = config["huggingface"].get("api_key") or os.getenv("HUGGINGFACE_API_KEY")
        if api_key:
            llm_manager.register_provider("huggingface", HuggingFaceProvider(api_key=api_key))

    # VertexAI
    if config.get("vertexai", {}).get("enabled", False):
        project_id = config["vertexai"].get("project_id")
        location = config["vertexai"].get("location", "us-central1")
        if project_id:
            llm_manager.register_provider("vertexai", VertexAIProvider(project_id=project_id, location=location))

    logger.info(f"Initialized {len(llm_manager.list_providers())} LLM providers")
