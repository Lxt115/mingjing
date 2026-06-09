from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator


class LLMProvider(ABC):
    @abstractmethod
    async def chat(self, messages: list[dict], system_prompt: str | None = None) -> str:
        ...

    async def chat_stream(
        self, messages: list[dict], system_prompt: str | None = None,
    ) -> AsyncGenerator[str, None]:
        text = await self.chat(messages, system_prompt)
        yield text
