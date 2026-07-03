import os
from typing import Optional
import httpx

from .base import BaseLLMProvider, LLMMessage, LLMResponse

OPENROUTER_BASE = "https://openrouter.ai/api/v1"


class OpenAICompatibleProvider(BaseLLMProvider):
    def __init__(self, base_url: str, api_key: str = "", model: str = "qwen2.5-coder:7b"):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self._client: Optional[httpx.Client] = None

    @property
    def client(self) -> httpx.Client:
        if self._client is None:
            self._client = httpx.Client(timeout=120)
        return self._client

    def chat(self, messages: list[LLMMessage], **kwargs) -> LLMResponse:
        body = {
            "model": kwargs.get("model", self.model),
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 4096),
        }
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
            if "openrouter" in self.base_url:
                headers["HTTP-Referer"] = "https://github.com/shivamsingh-007/CORE"
                headers["X-Title"] = "Loop-Agent"

        try:
            resp = self.client.post(
                f"{self.base_url}/chat/completions", json=body, headers=headers
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            return LLMResponse(content=f"[ERROR: Provider returned {e}]", model=self.model, usage=None)
        choice = data["choices"][0]
        return LLMResponse(
            content=choice["message"]["content"],
            model=data.get("model", self.model),
            usage=data.get("usage"),
        )

    def check_health(self) -> bool:
        try:
            if "openrouter" in self.base_url and self.api_key:
                resp = self.client.get(
                    f"{self.base_url}/models",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    timeout=5,
                )
            else:
                resp = self.client.get(f"{self.base_url}/models", timeout=5)
            return resp.status_code == 200
        except Exception:
            return False


def _pick_default_model() -> str:
    or_key = os.environ.get("OPENROUTER_API_KEY", "")
    if or_key:
        return "qwen/qwen2.5-coder-7b-instruct"
    try:
        import httpx
        r = httpx.get("http://localhost:11434/api/tags", timeout=3)
        if r.status_code == 200:
            models = [m["name"] for m in r.json().get("models", [])]
            for pref in ["minimax-m3:cloud", "qwen2.5-coder:7b", "llama3.2:3b"]:
                if any(pref in m for m in models):
                    return pref
    except Exception:
        pass
    return "qwen2.5-coder:7b"


def provider_from_config(config_path: str = "") -> OpenAICompatibleProvider:
    or_key = os.environ.get("OPENROUTER_API_KEY", "")
    base_url = os.environ.get("LLM_BASE_URL", OPENROUTER_BASE if or_key else "http://localhost:11434/v1")
    api_key = os.environ.get("LLM_API_KEY", or_key)
    model = os.environ.get("LLM_MODEL", _pick_default_model())
    return OpenAICompatibleProvider(base_url=base_url, api_key=api_key, model=model)
