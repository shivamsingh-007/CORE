from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class LLMMessage:
    role: str
    content: str


@dataclass
class LLMResponse:
    content: str
    model: str
    usage: Optional[dict] = None


class BaseLLMProvider(ABC):
    @abstractmethod
    def chat(self, messages: list[LLMMessage], **kwargs) -> LLMResponse:
        ...

    @abstractmethod
    def check_health(self) -> bool:
        ...
