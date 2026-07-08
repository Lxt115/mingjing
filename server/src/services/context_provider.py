"""上下文数据提供者 —— 从配置的外部 API 拉取动态数据注入 prompt。

- 配置项 context_providers 是一个 URL 列表
- 自动携带 device-id 请求头
- 返回 JSON 格式 {code:0, data:{...}} → 格式化为 "- **key：** value"
"""

from typing import Any

import httpx


class ContextDataProvider:
    """从外部 API 获取动态上下文数据。"""

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}
        self.cached_data: str = ""
        self._last_fetch_time: float = 0

    async def fetch_all(self, agent_id: str = "", device_id: str = "") -> str:
        """获取所有配置的上下文数据并格式化为文本。

        Args:
            agent_id: 角色 ID（会作为 agent-id 头发送）
            device_id: 设备 ID（会作为 device-id 头发送）

        Returns:
            格式化的多行上下文文本，无数据时返回空字符串
        """
        providers = self.config.get("context_providers", [])
        if not providers:
            return ""

        lines: list[str] = []
        async with httpx.AsyncClient(timeout=5) as client:
            for provider in providers:
                url = provider.get("url", "")
                if not url:
                    continue

                headers = {}
                if isinstance(provider.get("headers"), dict):
                    headers = provider["headers"].copy()
                if agent_id:
                    headers["agent-id"] = str(agent_id)
                if device_id:
                    headers["device-id"] = str(device_id)

                try:
                    resp = await client.get(url, headers=headers)
                    if resp.status_code == 200:
                        data = resp.json()
                        if isinstance(data, dict):
                            if data.get("code") == 0:
                                inner = data.get("data", {})
                                if isinstance(inner, dict):
                                    for k, v in inner.items():
                                        lines.append(f"- **{k}：** {v}")
                                elif isinstance(inner, list):
                                    for item in inner:
                                        lines.append(f"- {item}")
                                else:
                                    lines.append(f"- {inner}")
                            else:
                                print(f"[context] API {url} 返回错误: {data.get('msg')}")
                        else:
                            print(f"[context] API {url} 返回非字典数据")
                    else:
                        print(f"[context] API {url} 请求失败: {resp.status_code}")
                except Exception as e:
                    print(f"[context] 获取 {url} 失败: {e}")

        self.cached_data = "\n".join(lines)
        return self.cached_data


# 全局单例
_context_provider: ContextDataProvider | None = None


def get_context_provider(config: dict[str, Any] | None = None) -> ContextDataProvider:
    global _context_provider
    if _context_provider is None:
        _context_provider = ContextDataProvider(config)
    elif config is not None:
        _context_provider.config = config
    return _context_provider
