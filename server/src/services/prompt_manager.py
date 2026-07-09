"""系统提示词管理器 —— 支持 Jinja2 模板渲染。

核心功能：
- 加载 agent-base-prompt.txt 模板
- 注入时间（日期/星期/农历）、位置、天气等动态上下文
- 将角色的 system_prompt 作为 {{base_prompt}} 渲染
- 结果缓存避免重复构建
"""

from datetime import datetime
from pathlib import Path
from typing import Optional

from jinja2 import Template

# ── 星期映射 ──
WEEKDAY_MAP = {
    "Monday": "星期一", "Tuesday": "星期二", "Wednesday": "星期三",
    "Thursday": "星期四", "Friday": "星期五", "Saturday": "星期六", "Sunday": "星期日",
}

# ── Emoji 白名单 ──
EMOJI_LIST = [
    "😶", "🙂", "😆", "😂", "😔", "😠", "😭",
    "😍", "😳", "😲", "😱", "🤔", "😉", "😎",
    "😌", "🤤", "😘", "😏", "😴", "😜", "🙄",
]

# ── Emoji → 情绪映射 ──
EMOJI_MAP = {
    "😶": "neutral", "🙂": "happy", "😆": "laughing", "😂": "laughing",
    "😔": "sad", "😠": "angry", "😭": "crying", "😍": "love",
    "😳": "shy", "😲": "surprised", "😱": "shocked", "🤔": "thinking",
    "😉": "wink", "😎": "cool", "😌": "relieved", "🤤": "drooling",
    "😘": "kiss", "😏": "smirk", "😴": "sleepy", "😜": "playful", "🙄": "eyeroll",
}


def _template_dir() -> Path:
    d = Path(__file__).resolve().parent.parent.parent / "data" / "prompts"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _get_current_time_info() -> tuple:
    """获取当前时间信息：日期、星期、农历。"""
    now = datetime.now()
    today_date = now.strftime("%Y-%m-%d")
    today_weekday = WEEKDAY_MAP.get(now.strftime("%A"), now.strftime("%A"))
    # 简化农历（可用 zhdate 库精确计算，这里用简化版本）
    try:
        from zhdate import ZhDate
        lunar = ZhDate.from_datetime(now)
        lunar_str = f"{lunar.lunar()}年{lunar.lunar_month_name}{lunar.lunar_day_name}"
    except ImportError:
        lunar_str = "（农历模块未安装）"
    return today_date, today_weekday, lunar_str


class PromptManager:
    """系统提示词管理器。"""

    def __init__(self):
        self.template: Optional[str] = None
        self._cache: dict = {}  # 简单内存缓存：{agent_id: enhanced_prompt}
        self._load_template()

    def _load_template(self) -> None:
        """加载 Jinja2 模板。"""
        template_path = _template_dir() / "agent-base-prompt.txt"
        if template_path.exists():
            self.template = template_path.read_text(encoding="utf-8")
            print(f"[prompt_manager] 加载模板: {template_path}")
        else:
            print(f"[prompt_manager] 模板文件不存在: {template_path}，使用简单模式")

    def build_enhanced_prompt(
        self,
        base_prompt: str,
        agent_id: str = "",
        location: str = "北京",
        weather: str = "",
        language: str = "中文",
        emoji_enabled: bool = True,
        dynamic_context: str = "",
    ) -> str:
        """构建增强系统提示词。

        Args:
            base_prompt: 角色的 system_prompt
            agent_id: 角色 ID（用于缓存）
            location: 位置（默认北京）
            weather: 天气文本
            language: 回复语言
            emoji_enabled: 是否启用表情
            dynamic_context: 额外动态上下文
        """
        today_date, today_weekday, lunar_date = _get_current_time_info()

        # 简单模板模式（无 agent-base-prompt.txt）
        if not self.template:
            parts = [base_prompt]

            # 动态上下文
            ctx_lines = []
            ctx_lines.append(f"- 当前时间：{datetime.now().strftime('%H:%M')}")
            ctx_lines.append(f"- 今天日期：{today_date}（{today_weekday}）")
            if lunar_date and "农历模块未安装" not in lunar_date:
                ctx_lines.append(f"- 今天农历：{lunar_date}")
            if location:
                ctx_lines.append(f"- 所在地：{location}")
            if weather:
                ctx_lines.append(f"- 本地天气：{weather}")
            if dynamic_context:
                ctx_lines.append(dynamic_context)
            if ctx_lines:
                parts.append("\n\n<context>\n" + "\n".join(ctx_lines) + "\n</context>")

            # 表情约束
            if emoji_enabled:
                parts.append(
                    "\n\n<tts_format>\n"
                    "每段回复开头可插入1个白名单Emoji: " + " ".join(EMOJI_LIST) + "\n"
                    "禁止Markdown排版，禁止括号里的动作描写。\n"
                    "</tts_format>"
                )

            return "\n".join(parts)

        # Jinja2 模板模式
        try:
            template = Template(self.template)
            result = template.render(
                base_prompt=base_prompt,
                current_time=f"{{{{current_time}}}}",
                today_date=today_date,
                today_weekday=today_weekday,
                lunar_date=lunar_date,
                local_address=location,
                weather_info=weather,
                emojiList=EMOJI_LIST,
                device_id=agent_id,
                client_ip="",
                dynamic_context=dynamic_context,
                language=language,
                emoji_enabled=emoji_enabled,
            )
            return result
        except Exception as e:
            print(f"[prompt_manager] 模板渲染失败: {e}，回退到简单模式")
            return base_prompt

    def get_quick_prompt(self, base_prompt: str, agent_id: str = "") -> str:
        """快速获取提示词（使用缓存）"""
        cache_key = f"prompt:{agent_id}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        return base_prompt

    def clear_cache(self, agent_id: str = "") -> None:
        """清除缓存。"""
        if agent_id:
            self._cache.pop(f"prompt:{agent_id}", None)
        else:
            self._cache.clear()


# 全局单例
_prompt_manager: Optional[PromptManager] = None


def get_prompt_manager() -> PromptManager:
    global _prompt_manager
    if _prompt_manager is None:
        _prompt_manager = PromptManager()
    return _prompt_manager
