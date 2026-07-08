"""TTS 文本预处理 —— MarkdownCleaner 和分句逻辑。

在文本送入 TTS 之前进行清理，确保语音合成质量：
1. Markdown 清理：去除 **加粗**、- 列表、``` 代码块
2. 文本替换：correct_words 正则替换
3. 按标点分句：用于流式 TTS 首句快速响应
"""

import re
from typing import Optional


# ── Markdown 清理 ──
MD_BOLD_RE = re.compile(r"\*\*(.+?)\*\*")
MD_ITALIC_RE = re.compile(r"\*(.+?)\*")
MD_CODE_RE = re.compile(r"```[\s\S]*?```")
MD_INLINE_CODE_RE = re.compile(r"`(.+?)`")
MD_HEADER_RE = re.compile(r"^#{1,6}\s+", re.MULTILINE)
MD_LIST_RE = re.compile(r"^[\s]*[-*+]\s+", re.MULTILINE)
MD_LINK_RE = re.compile(r"\[(.+?)\]\(.+?\)")
PAREN_ACTION_RE = re.compile(r"[（(][^）)]*?(?:说|笑|叹|想|道|无奈|开心|生气)[^）)]*?[）)]")


def clean_tts_text(text: str) -> str:
    """清理文本中的 Markdown 格式和动作描写，使其适合 TTS 朗读。"""
    text = MD_CODE_RE.sub("", text)
    text = MD_INLINE_CODE_RE.sub(r"\1", text)
    text = MD_BOLD_RE.sub(r"\1", text)
    text = MD_ITALIC_RE.sub(r"\1", text)
    text = MD_HEADER_RE.sub("", text)
    text = MD_LIST_RE.sub("", text)
    text = MD_LINK_RE.sub(r"\1", text)
    # 去除括号内的动作描写
    text = PAREN_ACTION_RE.sub("", text)
    return text.strip()


# ── 分句逻辑 ──
def split_sentences(text: str, is_first: bool = True) -> list[str]:
    """将文本按标点切分为句子列表，首句使用弱标点切分以降低延迟。

    - 首句：允许逗号/顿号等弱标点切分，优先快速响应
    - 后续句：仅按强标点切分
    """
    if not text:
        return []

    sentences: list[str] = []
    remaining = text

    if is_first:
        # 首句：弱标点 + 强标点都可以切
        pattern = re.compile(r"([^。？！!?；;，,、：:]+[。？！!?；;，,、：:])")
    else:
        # 后续句：仅强标点切分
        pattern = re.compile(r"([^。？！!?；;]+[。？！!?；;])")

    matches = pattern.findall(remaining)
    for m in matches:
        sentences.append(m.strip())
        remaining = remaining[len(m):]

    # 剩余文本作为最后一句
    remaining = remaining.strip()
    if remaining:
        sentences.append(remaining)

    return sentences


# ── 文本替换 ──
def apply_correct_words(text: str, correct_words: Optional[list[str]] = None) -> str:
    """应用文本替换规则（如纠正 TTS 发音不准的词）。

    config 示例: correct_words: ["小智|小志", "AI|人工智能"]
    格式: 原始词|替换词
    """
    if not correct_words:
        return text
    for rule in correct_words:
        if "|" in rule:
            original, replacement = rule.split("|", 1)
            text = text.replace(original, replacement)
    return text
