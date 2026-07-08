"""记忆服务 —— 每次对话结束后由 LLM 自动总结，按角色持久化存储。

- 保存：LLM 非流式总结本轮对话，与历史记忆合并
- 查询：直接返回角色的完整记忆文本
- 存储：data/.memory/{agent_id}.json，按角色隔离
"""

import json
import re
import time
import uuid
from pathlib import Path
from typing import Optional


# ── 记忆总结提示词 ──
MEMORY_SUMMARIZE_PROMPT = """# 时空记忆编织者

## 核心使命
构建可生长的动态记忆网络，在有限空间内保留关键信息的同时，智能维护信息演变轨迹
根据对话记录，总结user的重要信息，以便在未来的对话中提供更个性化的服务

## 记忆法则
### 1. 三维度记忆评估（每次更新必执行）
| 维度       | 评估标准                  | 权重分 |
|------------|---------------------------|--------|
| 时效性     | 信息新鲜度（按对话轮次） | 40%    |
| 情感强度   | 含重要标记/重复提及次数   | 35%    |
| 关联密度   | 与其他信息的连接数量      | 25%    |

### 2. 动态更新机制
- 当检测到名称变更、身份变化、重要事件时，更新对应字段
- 将旧信息移入历史记录，保留时间轴
- 记忆立方追加重要事件，标注时间戳

### 3. 空间优化策略
- **信息压缩术**：用符号体系提升密度，避免冗余描述
- **淘汰预警**：当总字数≥900时触发，删除权重分<60且3轮未提及的信息，合并相似条目

## 记忆结构
输出格式必须为可解析的json字符串，不需要解释、注释和说明，保存记忆时仅从对话提取信息，不要混入示例内容
```json
{
  "时空档案": {
    "身份图谱": {
      "现用名": "",
      "特征标记": []
    },
    "记忆立方": [
      {
        "事件": "简要描述",
        "时间戳": "YYYY-MM-DD",
        "情感值": 0.0,
        "关联项": [""],
        "保鲜期": 30
      }
    ]
  },
  "关系网络": {
    "高频话题": {},
    "暗线联系": [""]
  },
  "待响应": {
    "紧急事项": [],
    "潜在关怀": []
  },
  "高光语录": []
}
```"""

MEMORY_INJECT_PROMPT = """<memory_context>
以下是该角色的历史记忆摘要，请在对话中自然地参考这些信息，让对话更有连贯性和个性化。
注意：不要生硬地复述记忆内容，而是像老朋友一样自然地体现对这些信息的了解。

{memory_text}
</memory_context>"""


# ── 工具函数 ──
def _memory_dir() -> Path:
    """返回记忆文件存放目录，确保存在。"""
    d = Path(__file__).resolve().parent.parent.parent / "data" / ".memory"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _memory_path(agent_id: uuid.UUID) -> Path:
    return _memory_dir() / f"{agent_id}.json"


def _extract_json(text: str) -> Optional[str]:
    """从 LLM 返回文本中提取 JSON。"""
    # 尝试匹配 ```json ... ``` 代码块
    m = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
    if m:
        json_str = m.group(1)
        try:
            json.loads(json_str)
            return json_str
        except json.JSONDecodeError:
            pass
    # 尝试匹配 ``` ... ```
    m = re.search(r"```\s*(.*?)\s*```", text, re.DOTALL)
    if m:
        json_str = m.group(1)
        try:
            json.loads(json_str)
            return json_str
        except json.JSONDecodeError:
            pass
    # 尝试直接解析整段文本
    try:
        json.loads(text)
        return text
    except json.JSONDecodeError:
        pass
    return None


# ── 公开 API ──
def load_memory(agent_id: uuid.UUID) -> str:
    """加载指定角色的记忆文本。返回空字符串表示无记忆。"""
    path = _memory_path(agent_id)
    if not path.exists():
        return ""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data.get("memory", "")
    except (json.JSONDecodeError, OSError):
        return ""


def save_memory_raw(agent_id: uuid.UUID, memory_text: str) -> None:
    """直接写入记忆文本（用于 LLM 总结后的结果）。"""
    path = _memory_path(agent_id)
    path.write_text(
        json.dumps({"memory": memory_text, "updated_at": time.strftime("%Y-%m-%d %H:%M:%S")},
                   ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


async def summarize_and_save(
    agent_id: uuid.UUID,
    messages: list[dict],
    llm,  # LLMProvider 实例
) -> Optional[str]:
    """调用 LLM 总结对话并保存记忆。

    Args:
        agent_id: 角色 ID
        messages: 本轮对话消息列表 [{"role": "user"/"assistant", "content": "..."}, ...]
        llm: LLMProvider 实例

    Returns:
        本次总结的 JSON 字符串，失败返回 None
    """
    if len(messages) < 2:
        return None

    # 构建输入文本
    msg_parts = []
    for msg in messages:
        role_label = "User" if msg["role"] == "user" else "Assistant"
        content = msg.get("content", "")
        if content:
            msg_parts.append(f"{role_label}: {content}")
    msg_str = "\n".join(msg_parts)

    # 历史记忆
    existing_memory = load_memory(agent_id)
    if existing_memory:
        msg_str += "\n历史记忆：\n" + existing_memory

    time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    msg_str += f"\n当前时间：{time_str}"

    try:
        result = await llm.chat(
            messages=[{"role": "user", "content": msg_str}],
            system_prompt=MEMORY_SUMMARIZE_PROMPT,
        )

        # 检查是否 LLM 错误
        if result.startswith("["):
            print(f"[memory] LLM 总结失败: {result}")
            return None

        json_str = _extract_json(result)
        if json_str is None:
            print(f"[memory] 无法从响应中提取 JSON: {result[:200]}")
            return None

        # 验证 JSON 有效
        json.loads(json_str)

        # 保存
        save_memory_raw(agent_id, json_str)
        print(f"[memory] 角色 {agent_id} 记忆保存成功")
        return json_str

    except Exception as e:
        print(f"[memory] 总结异常: {e}")
        return None


def build_memory_injection(agent_id: uuid.UUID) -> str:
    """构建可注入到 system_prompt 的记忆上下文文本。"""
    memory_text = load_memory(agent_id)
    if not memory_text:
        return ""
    return MEMORY_INJECT_PROMPT.format(memory_text=memory_text)


def clear_memory(agent_id: uuid.UUID) -> None:
    """清除指定角色的所有记忆。"""
    path = _memory_path(agent_id)
    if path.exists():
        path.unlink()
