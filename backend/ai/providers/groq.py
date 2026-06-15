from typing import Any, Optional

import httpx

from backend.ai.providers.base import BaseProvider, KeyState


class GroqProvider(BaseProvider):
    name = "groq"
    models = ["llama3-70b-8192", "mixtral-8x7b-32768", "gemma2-9b-it"]

    def __init__(self, api_keys: list[str]):
        super().__init__(api_keys)
        self.base_url = "https://api.groq.com/openai/v1"

    async def chat(self, messages: list[dict[str, str]], model: Optional[str] = None) -> dict[str, Any]:
        if not self.keys:
            return {"error": "No API keys configured for Groq"}
        key = self.get_available_key()
        if not key:
            return {"error": "All Groq keys are rate-limited"}
        model = model or self.models[0]
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                r = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {key.api_key}",
                        "Content-Type": "application/json",
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
                    return {"error": f"Groq API error: {r.status_code} - {r.text}"}
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
                return {"error": f"Groq request failed: {str(e)}"}
