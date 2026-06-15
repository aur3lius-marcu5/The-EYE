import logging
from typing import Any, Optional

from backend.ai.providers.router import AIRouter
from backend.core.config import settings

logger = logging.getLogger(__name__)

_router: Optional[AIRouter] = None


def get_router() -> AIRouter:
    global _router
    if _router is None:
        _router = AIRouter({
            "priority": settings.ai_provider_priority,
            "groq_api_key_1": settings.groq_api_key_1,
            "groq_api_key_2": settings.groq_api_key_2,
            "openrouter_api_key_1": settings.openrouter_api_key_1,
            "openrouter_api_key_2": settings.openrouter_api_key_2,
        })
    return _router


async def analyze_with_ai(
    system_prompt: str,
    user_message: str,
    context: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    router = get_router()
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]
    result = await router.chat(messages, context)
    return result
