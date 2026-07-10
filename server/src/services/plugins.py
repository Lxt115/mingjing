"""插件系统 —— 支持 LLM 通过文本标签触发工具调用。

插件检测格式：<TOOL:name>参数</TOOL:name>
LLM 在回复中自然输出工具标签，后台拦截执行后将结果注入对话继续。

Action 类型：
- RESPONSE (2): 直接回复，不调用 LLM
- REQLLM  (3): 执行后结果交给 LLM 二次加工
"""

import json
import re
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any, Callable, Awaitable


class Action(IntEnum):
    """插件执行后的行为。"""
    NONE = 1       # 啥也不干
    RESPONSE = 2   # 直接返回结果
    REQLLM = 3     # 结果交给 LLM 继续生成


@dataclass
class ActionResponse:
    """插件执行结果。"""
    result: str = ""
    result_type: str = "text"  # text | audio
    action: Action = Action.RESPONSE
    emotion: str = ""
    tts_text: str = ""


@dataclass
class PluginDef:
    """插件定义。"""
    name: str
    func: Callable[..., Awaitable[ActionResponse]]
    description: str = ""
    parameters: dict = field(default_factory=dict)
    action: Action = Action.REQLLM


# ── 全局插件注册表 ──
_plugins: dict[str, PluginDef] = {}

TOOL_TAG_RE = re.compile(r"<TOOL:(\w+)>(.*?)</TOOL:\1>", re.DOTALL)


def register(name: str, description: str = "", action: Action = Action.REQLLM):
    """装饰器：注册插件函数。"""
    def decorator(func):
        _plugins[name] = PluginDef(name=name, func=func, description=description, action=action)
        return func
    return decorator


def get_plugin(name: str) -> PluginDef | None:
    return _plugins.get(name)


def list_plugins() -> list[PluginDef]:
    return list(_plugins.values())


def extract_tool_calls(text: str) -> list[tuple[str, str]]:
    """从 LLM 输出中提取工具调用。返回 [(tool_name, params_text), ...]"""
    return TOOL_TAG_RE.findall(text)


def remove_tool_tags(text: str) -> str:
    """移除文本中的工具调用标签。"""
    return TOOL_TAG_RE.sub("", text).strip()


def build_tools_prompt() -> str:
    """构建工具列表提示词，注入 system_prompt。"""
    if not _plugins:
        return ""
    lines = ["\n## 可用工具"]
    for name, p in _plugins.items():
        lines.append(f"- {name}: {p.description}")
    lines.append("调用格式: <TOOL:工具名>参数</TOOL:工具名>")
    return "\n".join(lines)


async def execute_tool(name: str, params_text: str, **kwargs) -> ActionResponse | None:
    """执行指定工具。"""
    plugin = _plugins.get(name)
    if not plugin:
        print(f"[plugin] 未知工具: {name}")
        return None
    try:
        # 尝试解析 params_text 为 JSON，失败则作为纯文本传递
        try:
            params = json.loads(params_text)
        except (json.JSONDecodeError, ValueError):
            params = params_text
        if isinstance(params, str):
            return await plugin.func(params_text=params, **kwargs)
        else:
            return await plugin.func(**params, **kwargs)
    except Exception as e:
        print(f"[plugin] 执行 {name} 失败: {e}")
        return ActionResponse(result=f"工具执行失败: {e}", action=Action.RESPONSE)


# ── 内置插件 ──

@register(name="exit", description="用户说要离开/再见时调用。参数: say_goodbye（告别语）", action=Action.RESPONSE)
async def handle_exit(say_goodbye: str = "", params_text: str = "", **kwargs) -> ActionResponse:
    goodbye = say_goodbye or params_text or "再见，期待下次聊天！"
    return ActionResponse(result=goodbye, action=Action.RESPONSE)


@register(name="get_news", description="查看新闻。参数: source（新闻源，如'澎湃新闻''百度热搜'，可选）, detail（true获取上一条详情，可选）", action=Action.REQLLM)
async def handle_get_news(source: str = "", detail: bool = False, params_text: str = "", **kwargs) -> ActionResponse:
    from src.services.get_news import get_news

    if isinstance(detail, str):
        detail = detail.lower() == "true"
    news_text = get_news(source=source, detail=detail)
    return ActionResponse(result=news_text, action=Action.REQLLM)


@register(name="get_lunar", description="查询黄历/农历。参数: date（日期YYYY-MM-DD，默认今天）, query（查询内容如'宜忌''八字''节气'，可选）", action=Action.REQLLM)
async def handle_get_lunar(date: str = "", query: str = "", params_text: str = "", **kwargs) -> ActionResponse:
    from src.services.get_lunar import get_lunar

    date = date or None
    query = query or params_text or None
    lunar_text = get_lunar(date_str=date, query=query)
    return ActionResponse(result=lunar_text, action=Action.REQLLM)
