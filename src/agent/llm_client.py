import os
import json
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import httpx

class BaseLLMClient(ABC):
    """Abstract Base Class for LLM providers."""
    @abstractmethod
    async def generate(self, system_prompt: str, user_prompt: str, temperature: float = 0.3) -> str:
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        pass

class OllamaLLMClient(BaseLLMClient):
    """Async client for local Ollama server."""
    def __init__(self, base_url: str = None, model: str = None, timeout: float = 180.0):
        self.base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
        self.model = model or os.getenv("OLLAMA_MODEL", "llama3.2")
        self.timeout = timeout

    @property
    def model_name(self) -> str:
        return f"ollama/{self.model}"

    async def is_available(self) -> bool:
        """Checks if local Ollama server is running and reachable."""
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                res = await client.get(f"{self.base_url}/api/tags")
                return res.status_code == 200
        except Exception:
            return False

    async def generate(self, system_prompt: str, user_prompt: str, temperature: float = 0.3) -> str:
        """Sends prompt to local Ollama API with generous timeout for long-form generation."""
        endpoint = f"{self.base_url}/api/chat"
        payload = {
            "model": self.model,
            "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
            "stream": False,
            "options": {"temperature": temperature}
        }
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(self.timeout, connect=10.0)) as client:
                response = await client.post(endpoint, json=payload)
                response.raise_for_status()
                data = response.json()
                return data.get("message", {}).get("content", "").strip()
        except httpx.ConnectError:
            raise RuntimeError(f"Cannot connect to Ollama at {self.base_url}. Please ensure Ollama is running (`ollama serve`).")
        except Exception as e:
            raise RuntimeError(f"Ollama generation error: {str(e)}")

class CloudLLMClient(BaseLLMClient):
    """Client for Cloud LLM providers (Anthropic Claude / OpenAI)."""
    def __init__(self, provider: str = "anthropic", model: Optional[str] = None, api_key: Optional[str] = None):
        self.provider = provider.lower()
        self.api_key = api_key or (os.getenv("ANTHROPIC_API_KEY") if self.provider == "anthropic" else os.getenv("OPENAI_API_KEY"))
        self._model = model or ("claude-3-5-sonnet-20241022" if self.provider == "anthropic" else "gpt-4o")

    @property
    def model_name(self) -> str:
        return f"{self.provider}/{self._model}"

    async def generate(self, system_prompt: str, user_prompt: str, temperature: float = 0.3) -> str:
        if not self.api_key:
            raise ValueError(f"API key missing for provider: {self.provider}")
        if self.provider == "anthropic":
            url = "https://api.anthropic.com/v1/messages"
            headers = {"x-api-key": self.api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"}
            payload = {"model": self._model, "max_tokens": 3000, "temperature": temperature, "system": system_prompt, "messages": [{"role": "user", "content": user_prompt}]}
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(url, headers=headers, json=payload)
                resp.raise_for_status()
                data = resp.json()
                return "".join([b["text"] for b in data.get("content", []) if b.get("type") == "text"])
        else:
            url = "https://api.openai.com/v1/chat/completions"
            headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
            payload = {"model": self._model, "temperature": temperature, "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]}
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(url, headers=headers, json=payload)
                resp.raise_for_status()
                data = resp.json()
                return data["choices"][0]["message"]["content"].strip()

def get_llm_client(model_override: Optional[str] = None) -> BaseLLMClient:
    provider = os.getenv("DEFAULT_LLM_PROVIDER", "ollama")
    if model_override:
        if model_override.startswith("ollama/"):
            return OllamaLLMClient(model=model_override.replace("ollama/", ""))
        elif model_override.startswith("anthropic/"):
            return CloudLLMClient(provider="anthropic", model=model_override.replace("anthropic/", ""))
        elif model_override.startswith("openai/"):
            return CloudLLMClient(provider="openai", model=model_override.replace("openai/", ""))
    if provider == "anthropic" and os.getenv("ANTHROPIC_API_KEY"):
        return CloudLLMClient(provider="anthropic")
    elif provider == "openai" and os.getenv("OPENAI_API_KEY"):
        return CloudLLMClient(provider="openai")
    return OllamaLLMClient()
