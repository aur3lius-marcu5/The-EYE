from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Optional


@dataclass
class KeyState:
    key_id: str
    api_key: str
    last_used_at: Optional[datetime] = None
    consecutive_failures: int = 0
    rate_limited_until: Optional[datetime] = None

    @property
    def is_available(self) -> bool:
        if self.rate_limited_until and datetime.utcnow() < self.rate_limited_until:
            return False
        return True

    def mark_rate_limited(self, retry_after: int = 60):
        self.rate_limited_until = datetime.utcnow() + timedelta(seconds=retry_after)
        self.consecutive_failures += 1

    def mark_success(self):
        self.consecutive_failures = 0
        self.last_used_at = datetime.utcnow()


class BaseProvider(ABC):
    name: str = ""
    models: list[str] = []
    keys: list[KeyState] = []
    current_key_index: int = 0

    def __init__(self, api_keys: list[str]):
        self.keys = [
            KeyState(key_id=f"{self.name}_{i}", api_key=key)
            for i, key in enumerate(api_keys) if key
        ]

    def get_available_key(self) -> Optional[KeyState]:
        for _ in range(len(self.keys)):
            key = self.keys[self.current_key_index]
            self.current_key_index = (self.current_key_index + 1) % len(self.keys)
            if key.is_available:
                return key
        return None

    @abstractmethod
    async def chat(self, messages: list[dict[str, str]], model: str) -> dict[str, Any]:
        ...
