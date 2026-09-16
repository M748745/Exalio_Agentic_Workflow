"""
Ollama Service - Connection management and LLM operations
Based on the Colab deployment pattern from data_storytelling app
Supports local and remote (Colab with tunnels) deployments
"""

import requests
import hashlib
import threading
import time
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import logging

logger = logging.getLogger(__name__)


# Global concurrency control
NUM_PARALLEL = 4  # Match Colab server's NUM_PARALLEL setting
_global_llm_semaphore = threading.Semaphore(NUM_PARALLEL)

# Shared HTTP session with connection pooling
_http_session = requests.Session()
_http_adapter = HTTPAdapter(
    pool_connections=NUM_PARALLEL,
    pool_maxsize=NUM_PARALLEL,
    max_retries=Retry(total=0)
)
_http_session.mount('http://', _http_adapter)
_http_session.mount('https://', _http_adapter)


def is_cloudflare_url(url: str) -> bool:
    """Check if URL is Cloudflare tunnel"""
    return "trycloudflare.com" in url.lower() or "cloudflare" in url.lower()


def is_ngrok_url(url: str) -> bool:
    """Check if URL is ngrok tunnel"""
    return "ngrok" in url.lower()


def is_localtunnel_url(url: str) -> bool:
    """Check if URL is localtunnel"""
    return "loca.lt" in url.lower() or "localtunnel" in url.lower()


def check_ollama_connection(ollama_url: str) -> bool:
    """Basic connectivity check to Ollama server"""
    try:
        is_remote = is_cloudflare_url(ollama_url) or is_ngrok_url(ollama_url) or \
                   is_localtunnel_url(ollama_url) or ollama_url.startswith("https://")
        timeout = 20 if is_remote else 5
        response = requests.get(f"{ollama_url}/api/tags", timeout=timeout)
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Connection check failed: {e}")
        return False


def verify_ollama_health(ollama_url: str) -> Dict[str, Any]:
    """Comprehensive health check of Ollama server"""
    health = {
        'connected': False,
        'models_available': False,
        'models': [],
        'model_count': 0,
        'connection_type': 'unknown',
        'error': None
    }

    try:
        # Dynamic timeout based on connection type
        is_cf = is_cloudflare_url(ollama_url)
        is_ng = is_ngrok_url(ollama_url)
        is_lt = is_localtunnel_url(ollama_url)
        is_https = ollama_url.startswith("https://")
        timeout = 20 if (is_cf or is_ng or is_lt or is_https) else 10

        if is_cf:
            health['connection_type'] = 'cloudflare'
        elif is_ng:
            health['connection_type'] = 'ngrok'
        elif is_lt:
            health['connection_type'] = 'localtunnel'
        else:
            health['connection_type'] = 'local'

        response = requests.get(f"{ollama_url}/api/tags", timeout=timeout)
        if response.status_code == 200:
            health['connected'] = True
            data = response.json()
            if 'models' in data and len(data['models']) > 0:
                health['models_available'] = True
                health['models'] = [m['name'] for m in data['models']]
                health['model_count'] = len(health['models'])

    except requests.exceptions.Timeout:
        health['error'] = "Connection timeout (check URL and network)"
    except requests.exceptions.ConnectionError:
        health['error'] = "Connection refused (is Ollama running?)"
    except Exception as e:
        health['error'] = str(e)

    return health


def get_available_models(ollama_url: str) -> List[str]:
    """Get list of available models from Ollama"""
    try:
        health = verify_ollama_health(ollama_url)
        return health['models'] if health['models_available'] else []
    except:
        return []


def generate_cache_key(prompt: str, model: str, temperature: float) -> str:
    """Generate cache key for LLM responses"""
    cache_str = f"{prompt}|{model}|{temperature:.2f}"
    return hashlib.md5(cache_str.encode()).hexdigest()


class OllamaService:
    """
    Service for interacting with Ollama LLM server
    Handles connection management, health monitoring, and LLM queries
    """

    def __init__(self, ollama_url: str, default_model: str = "llama3.2:3b"):
        self.ollama_url = ollama_url
        self.default_model = default_model
        self._cache: Dict[str, str] = {}
        self._monitor = None

    def start_monitoring(self, check_interval: int = 30):
        """Start connection health monitoring"""
        self._monitor = OllamaConnectionMonitor(
            url=self.ollama_url,
            check_interval=check_interval,
            keep_alive=True
        )
        self._monitor.start()
        logger.info(f"Started Ollama connection monitoring (interval: {check_interval}s)")

    def stop_monitoring(self):
        """Stop connection monitoring"""
        if self._monitor:
            self._monitor.stop()
            self._monitor = None

    def health_check(self) -> Dict[str, Any]:
        """Check Ollama server health"""
        return verify_ollama_health(self.ollama_url)

    def list_models(self) -> List[str]:
        """List available models"""
        return get_available_models(self.ollama_url)

    async def query(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.3,
        num_predict: int = 1024,
        top_p: float = 0.9,
        top_k: int = 40,
        use_cache: bool = True,
        stream: bool = False,
        system_message: Optional[str] = None
    ) -> str:
        """
        Query Ollama LLM with optimized parameters

        Args:
            prompt: Input prompt
            model: Model name (uses default if not specified)
            temperature: Sampling temperature
            num_predict: Maximum tokens to generate
            top_p: Nucleus sampling parameter
            top_k: Top-k sampling parameter
            use_cache: Use cached responses
            stream: Stream response
            system_message: System message/instructions

        Returns:
            LLM response text
        """
        model = model or self.default_model

        # Check cache
        if use_cache:
            cache_key = generate_cache_key(prompt, model, temperature)
            if cache_key in self._cache:
                logger.debug(f"Cache hit for prompt (model={model})")
                return self._cache[cache_key]

        # Build request payload
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": stream,
            "options": {
                "temperature": temperature,
                "num_predict": num_predict,
                "top_p": top_p,
                "top_k": top_k,
                "num_ctx": 32768,  # Match Colab canonical options
                "num_batch": 512,
            }
        }

        if system_message:
            payload["system"] = system_message

        # Determine timeout based on connection type
        is_remote = is_cloudflare_url(self.ollama_url) or \
                   is_ngrok_url(self.ollama_url) or \
                   is_localtunnel_url(self.ollama_url) or \
                   self.ollama_url.startswith("https://")

        base_timeout = 120
        timeout = base_timeout * 6 if is_remote else base_timeout

        try:
            # Use global semaphore for concurrency control
            with _global_llm_semaphore:
                headers = {"Content-Type": "application/json"}

                response = _http_session.post(
                    f"{self.ollama_url}/api/generate",
                    json=payload,
                    headers=headers,
                    timeout=timeout,
                    stream=stream
                )

                if response.status_code == 200:
                    if stream:
                        # Collect streamed response
                        full_response = ""
                        for line in response.iter_lines():
                            if line:
                                try:
                                    chunk = line.decode('utf-8')
                                    import json
                                    data = json.loads(chunk)
                                    if 'response' in data:
                                        full_response += data['response']
                                    if data.get('done', False):
                                        break
                                except:
                                    continue
                        result = full_response
                    else:
                        # Non-streaming response
                        import json
                        data = json.loads(response.text)
                        result = data.get('response', '')

                    # Cache result
                    if use_cache:
                        cache_key = generate_cache_key(prompt, model, temperature)
                        self._cache[cache_key] = result

                    return result
                else:
                    logger.error(f"Ollama returned HTTP {response.status_code}")
                    return f"[ERROR] HTTP {response.status_code}"

        except requests.exceptions.Timeout:
            logger.error("Request timeout - Ollama server not responding")
            return "[ERROR] Request timeout"
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection failed: {e}")
            return f"[ERROR] Connection failed"
        except Exception as e:
            logger.error(f"Query failed: {e}")
            return f"[ERROR] {str(e)}"

    def clear_cache(self):
        """Clear response cache"""
        self._cache.clear()
        logger.info("Cleared LLM response cache")


class OllamaConnectionMonitor:
    """Background thread to monitor and maintain Ollama connection"""

    def __init__(self, url: str, check_interval: int = 15, keep_alive: bool = True, ping_interval: int = 30):
        self.url = url
        self.check_interval = check_interval
        self.keep_alive = keep_alive
        self.ping_interval = ping_interval
        self._thread = None
        self._stop_event = threading.Event()
        self.status = {
            'connected': False,
            'last_check': None,
            'last_keepalive': None,
            'consecutive_failures': 0
        }

    def start(self):
        """Start monitoring thread"""
        if self._thread and self._thread.is_alive():
            logger.warning("Monitor already running")
            return

        self._stop_event.clear()
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        logger.info("Ollama connection monitor started")

    def stop(self):
        """Stop monitoring thread"""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("Ollama connection monitor stopped")

    def _monitor_loop(self):
        """Main monitoring loop"""
        last_check_time = 0
        last_keepalive = 0
        consecutive_failures = 0

        while not self._stop_event.is_set():
            current_time = time.time()

            # Keep-alive ping
            if self.keep_alive and (current_time - last_keepalive) >= self.ping_interval:
                try:
                    requests.get(f"{self.url}/api/tags", timeout=5)
                    self.status['last_keepalive'] = datetime.now()
                except:
                    pass
                last_keepalive = current_time

            # Health check
            if (current_time - last_check_time) >= self.check_interval:
                health = verify_ollama_health(self.url)
                self.status['last_check'] = datetime.now()

                if health['connected']:
                    self.status['connected'] = True
                    consecutive_failures = 0
                else:
                    self.status['connected'] = False
                    consecutive_failures += 1
                    logger.warning(f"Ollama health check failed: {health.get('error')}")

                self.status['consecutive_failures'] = consecutive_failures
                last_check_time = current_time

            time.sleep(1)

    def get_status(self) -> Dict[str, Any]:
        """Get current monitoring status"""
        return self.status.copy()
