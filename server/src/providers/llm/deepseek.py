from collections.abc import AsyncGenerator

from openai import AsyncOpenAI

from src.config import settings
from src.providers.llm.base import LLMProvider


class DeepSeekLLMProvider(LLMProvider):
    MODEL = settings.deepseek_model

    def _get_client(self) -> AsyncOpenAI:
        return AsyncOpenAI(
            api_key=settings.deepseek_api_key,
            base_url=settings.openai_base_url or "https://api.deepseek.com/v1",
        )

    async def chat(self, messages: list[dict], system_prompt: str | None = None) -> str:
        if not settings.deepseek_api_key:
            return "[DeepSeek LLM 未配置 API Key]"

        full_messages = messages.copy()
        if system_prompt:
            full_messages.insert(0, {"role": "system", "content": system_prompt})

        try:
            client = self._get_client()
            response = await client.chat.completions.create(
                model=self.MODEL,
                messages=full_messages,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            return f"[DeepSeek LLM 异常: {e}]"

    async def chat_stream(
        self, messages: list[dict], system_prompt: str | None = None,
    ) -> AsyncGenerator[str, None]:
        import asyncio

        if not settings.deepseek_api_key:
            yield "[DeepSeek LLM 未配置 API Key]"
            return

        full_messages = messages.copy()
        if system_prompt:
            full_messages.insert(0, {"role": "system", "content": system_prompt})

        queue: asyncio.Queue = asyncio.Queue()
        stop_event = asyncio.Event()

        async def _call():
            try:
                client = self._get_client()
                stream = await client.chat.completions.create(
                    model=self.MODEL,
                    messages=full_messages,
                    stream=True,
                )
                async for chunk in stream:
                    if stop_event.is_set():
                        break
                    if chunk.choices and chunk.choices[0].delta.content:
                        await queue.put(("chunk", chunk.choices[0].delta.content))
                await queue.put(("done", None))
            except Exception as e:
                await queue.put(("error", str(e)))

        task = asyncio.create_task(_call())

        try:
            while True:
                msg_type, data = await queue.get()
                if msg_type == "chunk":
                    yield data
                elif msg_type == "error":
                    yield f"[DeepSeek LLM 异常: {data}]"
                    return
                elif msg_type == "done":
                    return
        finally:
            stop_event.set()
            task.cancel()
