from typing import Any, Optional

import httpx

from backend.ai.providers.base import BaseProvider, KeyState


class OpenRouterProvider(BaseProvider):
    name = "openrouter"
    models = [
        "mistralai/mistral-large",
        "meta-llama/llama-3-70b-instruct",
        "google/gemini-pro",
    ]
    free_models = [
        "mistralai/mistral-7b-instruct",
        "huggingfaceh4/zephyr-7b-beta",
    ]

    def __init__(self, api_keys: list[str]):
        super().__init__(api_keys)
        self.base_url = "https://openrouter.ai/api/v1"
        self.models = self.models + self.free_models

    async def chat(self, messages: list[dict[str, str]], model: Optional[str] = None) -> dict[str, Any]:
        if not self.keys:
            return {"error": "No API keys configured for OpenRouter"}
        key = self.get_available_key()
        if not key:
            return {"error": "All OpenRouter keys are rate-limited"}
        model = model or self.models[0]
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                r = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {key.api_key}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "https://the-eye.local",
                        "X-Title": "THE EYE",
                    },
                    json={
                        "model": model,
                        "messages": messages,
                        "max_tokens": 2048,
                    },
                )
                if r.status_code == 429:
                    retry_after = int(r.headers.get("Retry-After", "60"))
                    key.mark_rate_limited(retry_after)
                    return {"error": f"Rate limited, retry after {retry_after}s"}
                if r.status_code != 200:
                    key.consecutive_failures += 1
                    return {"error": f"OpenRouter API error: {r.status_code} - {r.text}"}
                data = r.json()
                key.mark_success()
                return {
                    "content": data["choices"][0]["message"]["content"],
                    "model": data.get("model", model),
                    "tokens": data.get("usage", {}),
                    "provider": self.name,
                }
            except Exception as e:
                key.consecutive_failures += 1
                return {"error": f"OpenRouter request failed: {str(e)}"}
