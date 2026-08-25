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

    def __init__(
        self,
        base_url: str = None,
        model: str = None,
        timeout: float = 45.0
    ):
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
        """Sends prompt to local Ollama API."""
        endpoint = f"{self.base_url}/api/chat"
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "stream": False,
            "options": {
                "temperature": temperature,
            }
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(endpoint, json=payload)
                response.raise_for_status()
                data = response.json()
                return data.get("message", {}).get("content", "").strip()
        except httpx.ConnectError:
            raise RuntimeError(
                f"Cannot connect to Ollama at {self.base_url}. Please ensure Ollama is running (`ollama serve`)."
            )
        except Exception as e:
            raise RuntimeError(f"Ollama generation error: {str(e)}")


class CloudLLMClient(BaseLLMClient):
    """Client for Cloud LLM providers (Anthropic Claude / OpenAI)."""

    def __init__(
        self,
        provider: str = "anthropic",
        model: Optional[str] = None,
        api_key: Optional[str] = None
    ):
        self.provider = provider.lower()
        if self.provider == "anthropic":
            self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY", "")
            self.model = model or os.getenv("CLOUD_MODEL", "claude-3-5-sonnet-20241022")
        else:
            self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
            self.model = model or os.getenv("CLOUD_MODEL", "gpt-4o")

    @property
    def model_name(self) -> str:
        return f"{self.provider}/{self.model}"

    async def generate(self, system_prompt: str, user_prompt: str, temperature: float = 0.3) -> str:
        if not self.api_key:
            raise ValueError(
                f"Missing API key for cloud provider '{self.provider}'. Set {self.provider.upper()}_API_KEY in .env"
            )

        if self.provider == "anthropic":
            headers = {
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            }
            payload = {
                "model": self.model,
                "max_tokens": 4096,
                "system": system_prompt,
                "messages": [{"role": "user", "content": user_prompt}],
                "temperature": temperature
            }
            async with httpx.AsyncClient(timeout=45.0) as client:
                res = await client.post("https://api.anthropic.com/v1/messages", headers=headers, json=payload)
                res.raise_for_status()
                data = res.json()
                return data["content"][0]["text"].strip()
        else:
            # OpenAI compatible endpoint
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": temperature
            }
            async with httpx.AsyncClient(timeout=45.0) as client:
                res = await client.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
                res.raise_for_status()
                data = res.json()
                return data["choices"][0]["message"]["content"].strip()


def get_llm_client(provider_override: Optional[str] = None) -> BaseLLMClient:
    """
    Factory function returning the appropriate LLM client.
    Defaults to Ollama (100% free local execution).
    """
    provider = (provider_override or os.getenv("DEFAULT_LLM_PROVIDER", "ollama")).lower()

    if provider.startswith("anthropic") or provider.startswith("claude"):
        return CloudLLMClient(provider="anthropic")
    elif provider.startswith("openai") or provider.startswith("gpt"):
        return CloudLLMClient(provider="openai")
    else:
        return OllamaLLMClient()
