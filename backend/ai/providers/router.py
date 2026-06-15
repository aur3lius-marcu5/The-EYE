import logging
from typing import Any, Optional

from backend.ai.providers.groq import GroqProvider
from backend.ai.providers.openrouter import OpenRouterProvider
from backend.ai.providers.template import TemplateFallback

logger = logging.getLogger(__name__)

PROVIDER_MAP = {
    "groq": GroqProvider,
    "openrouter": OpenRouterProvider,
    "template": TemplateFallback,
}


class AIRouter:
    def __init__(self, config: dict[str, Any]):
        self.providers: list[Any] = []
        priority = config.get("priority", "groq,openrouter,template").split(",")
        for name in priority:
            name = name.strip()
            if name == "groq":
                keys = [k for k in [config.get("groq_api_key_1"), config.get("groq_api_key_2")] if k]
                if keys:
                    self.providers.append(GroqProvider(keys))
            elif name == "openrouter":
                keys = [k for k in [config.get("openrouter_api_key_1"), config.get("openrouter_api_key_2")] if k]
                if keys:
                    self.providers.append(OpenRouterProvider(keys))
            elif name == "template":
                self.providers.append(TemplateFallback())

    async def chat(
        self,
        messages: list[dict[str, str]],
        context: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        for provider in self.providers:
            if hasattr(provider, "keys") and not provider.keys:
                continue
            try:
                if provider.name == "template":
                    result = await provider.chat(messages, context)
                else:
                    result = await provider.chat(messages)
                if "error" in result:
                    logger.warning(f"Provider {provider.name} failed: {result['error']}")
                    continue
                logger.info(f"Used provider: {provider.name} model: {result.get('model', 'unknown')}")
                return result
            except Exception as e:
                logger.warning(f"Provider {provider.name} raised exception: {e}")
                continue
        return {
            "content": "All AI providers unavailable. Please check API keys and try again later.",
            "model": "none",
            "tokens": {},
            "provider": "none",
        }
