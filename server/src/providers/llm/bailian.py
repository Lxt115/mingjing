import asyncio
import threading
from collections.abc import AsyncGenerator

from dashscope import MultiModalConversation

from src.config import settings
from src.providers.llm.base import LLMProvider


class BailianLLMProvider(LLMProvider):
    MODEL = "qwen3.5-flash"

    @staticmethod
    def _extract_text(content) -> str:
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            return "".join(
                item.get("text", "") if isinstance(item, dict) else str(item)
                for item in content
            )
        return str(content)

    async def chat(self, messages: list[dict], system_prompt: str | None = None) -> str:
        if not settings.dashscope_api_key:
            return "[百炼 LLM 未配置 API Key]"

        full_messages = messages.copy()
        if system_prompt:
            full_messages.insert(0, {"role": "system", "content": system_prompt})

        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: MultiModalConversation.call(
                    model=self.MODEL,
                    messages=full_messages,
                    result_format="message",
                    enable_thinking=False,
                ),
            )

            if response.status_code == 200 and response.output:
                choices = response.output.get("choices", [])
                if choices:
                    content = choices[0].get("message", {}).get("content", "")
                    return self._extract_text(content) or ""
            return f"[百炼 LLM 错误: {response.message}]"
        except Exception as e:
            return f"[百炼 LLM 异常: {e}]"

    async def chat_stream(
        self, messages: list[dict], system_prompt: str | None = None,
    ) -> AsyncGenerator[str, None]:
        if not settings.dashscope_api_key:
            yield "[百炼 LLM 未配置 API Key]"
            return

        full_messages = messages.copy()
        if system_prompt:
            full_messages.insert(0, {"role": "system", "content": system_prompt})

        loop = asyncio.get_running_loop()
        queue: asyncio.Queue = asyncio.Queue()
        # 对应 xiaozhi 的 client_abort 标志：用于通知后台线程停止迭代
        stop_event = threading.Event()

        def _call():
            try:
                responses = MultiModalConversation.call(
                    model=self.MODEL,
                    messages=full_messages,
                    result_format="message",
                    stream=True,
                    incremental_output=True,
                    enable_thinking=False,
                )
                for resp in responses:
                    # 对应 xiaozhi connection.py chat() 中的 if self.client_abort: break
                    if stop_event.is_set():
                        break
                    if resp.status_code == 200 and resp.output:
                        choices = resp.output.get("choices", [])
                        if choices:
                            content = choices[0].get("message", {}).get("content", "")
                            if content:
                                text = self._extract_text(content)
                                if text:
                                    asyncio.run_coroutine_threadsafe(
                                        queue.put(("chunk", text)), loop
                                    )
                asyncio.run_coroutine_threadsafe(queue.put(("done", None)), loop)
            except Exception as e:
                asyncio.run_coroutine_threadsafe(
                    queue.put(("error", str(e))), loop
                )

        loop.run_in_executor(None, _call)

        try:
            while True:
                msg_type, data = await queue.get()
                if msg_type == "chunk":
                    yield data
                elif msg_type == "error":
                    yield f"[百炼 LLM 异常: {data}]"
                    return
                elif msg_type == "done":
                    return
        finally:
            # 对应 xiaozhi 的 clear_queues + client_abort：
            # 当异步生成器被废弃时（Task 被 cancel），通知后台线程停止迭代 LLM 流
            stop_event.set()
