"""
联网搜索服务。

支持的提供商：
- metaso: 秘塔搜索（国内，中文质量好）
- tavily: Tavily（海外，带AI摘要）

触发方式：LLM 在回复中输出 <SEARCH>关键词</SEARCH>，pipeline 会自动拦截并执行搜索。
"""

import re

import requests

from src.config import settings

SEARCH_TAG_RE = re.compile(r"<SEARCH>(.*?)</SEARCH>", re.DOTALL)


def extract_search_query(text: str) -> str | None:
    """从 LLM 回复中提取搜索词。返回 None 表示不需要搜索。"""
    match = SEARCH_TAG_RE.search(text)
    if match:
        return match.group(1).strip()
    return None


def _search_metaso(api_key: str, query: str, max_results: int) -> str:
    """调用秘塔搜索API。"""
    url = "https://metaso.cn/api/v1/search"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "q": query,
        "size": max_results,
        "stream": False,
        "scope": "webpage",
        "includeSummary": True,
        "includeRawContent": False,
        "conciseSnippet": False,
    }
    response = requests.post(url, json=payload, headers=headers, timeout=15)
    response.raise_for_status()
    data = response.json()

    webpages = data.get("webpages", [])
    if not webpages:
        return "未找到相关搜索结果。"

    lines = ["【联网搜索结果】"]
    for i, item in enumerate(webpages, 1):
        title = item.get("title", "无标题")
        snippet = item.get("summary", "")
        date = item.get("date", "")
        lines.append(f"{i}. 标题：{title}")
        if date:
            lines.append(f"   日期：{date}")
        if snippet:
            lines.append(f"   摘要：{snippet}")

    return "\n".join(lines)


def _search_tavily(api_key: str, query: str, max_results: int) -> str:
    """调用Tavily搜索API。"""
    url = "https://api.tavily.com/search"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "query": query,
        "max_results": max_results,
        "search_depth": "advanced",
    }
    response = requests.post(url, json=payload, headers=headers, timeout=15)
    response.raise_for_status()
    data = response.json()

    answer = data.get("answer", "")
    results = data.get("results", [])
    if not results:
        return "未找到相关搜索结果。"

    lines = [f"【联网搜索结果】\n总结：{answer}" if answer else "【联网搜索结果】"]
    for i, item in enumerate(results, 1):
        title = item.get("title", "无标题")
        content = item.get("content", "")
        lines.append(f"{i}. 标题：{title}")
        if content:
            lines.append(f"   摘要：{content}")

    return "\n".join(lines)


def search(query: str) -> str:
    """执行联网搜索，返回格式化后的结果文本。"""
    provider = settings.search_provider
    api_key = settings.search_api_key
    max_results = settings.search_max_results

    if not api_key:
        return "[联网搜索未配置API Key，请在 .env 中设置 SEARCH_API_KEY]"

    if provider == "metaso":
        search_fn = lambda: _search_metaso(api_key, query, max_results)
    elif provider == "tavily":
        search_fn = lambda: _search_tavily(api_key, query, max_results)
    else:
        return f"[不支持的搜索提供商: {provider}]"

    try:
        return search_fn()
    except requests.exceptions.Timeout:
        print(f"[web_search] 搜索请求超时: {query}")
        return "[联网搜索请求超时，请稍后重试。]"
    except requests.exceptions.HTTPError as e:
        print(f"[web_search] HTTP错误 {e.response.status_code if e.response else '?'}: {e}")
        status_code = e.response.status_code if e.response else 0
        if status_code == 401 or status_code == 403:
            return "[联网搜索API Key无效或已过期，请检查配置。]"
        return f"[联网搜索请求失败（HTTP {status_code}），请稍后重试。]"
    except requests.exceptions.RequestException as e:
        print(f"[web_search] 请求失败: {e}")
        return "[联网搜索请求失败，请稍后重试。]"
    except Exception as e:
        print(f"[web_search] 搜索异常: {e}")
        return "[联网搜索出现异常，请稍后重试。]"
