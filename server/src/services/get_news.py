"""
新闻查询服务 —— 基于 NewsNow API。

支持 50+ 新闻源，随机返回一条新闻标题，支持获取详情。
"""

import random
import requests


CHANNEL_MAP = {
    "V2EX": "v2ex-share", "知乎": "zhihu", "微博": "weibo",
    "联合早报": "zaobao", "酷安": "coolapk", "MKTNews": "mktnews-flash",
    "华尔街见闻": "wallstreetcn-quick", "36氪": "36kr-quick", "抖音": "douyin",
    "虎扑": "hupu", "百度贴吧": "tieba", "今日头条": "toutiao",
    "IT之家": "ithome", "澎湃新闻": "thepaper", "卫星通讯社": "sputniknewscn",
    "参考消息": "cankaoxiaoxi", "远景论坛": "pcbeta-windows11",
    "财联社": "cls-depth", "雪球": "xueqiu-hotstock", "格隆汇": "gelonghui",
    "法布财经": "fastbull-express", "Solidot": "solidot",
    "Hacker News": "hackernews", "Product Hunt": "producthunt",
    "Github": "github-trending-today", "哔哩哔哩": "bilibili-hot-search",
    "快手": "kuaishou", "靠谱新闻": "kaopu", "金十数据": "jin10",
    "百度热搜": "baidu", "牛客": "nowcoder", "少数派": "sspai",
    "稀土掘金": "juejin", "凤凰网": "ifeng", "虫部落": "chongbuluo-latest",
}

DEFAULT_SOURCES = "澎湃新闻;百度热搜;财联社"
HEADERS = {"User-Agent": "Mozilla/5.0"}

# 存储最近一条新闻链接，用于获取详情
_last_news: dict = {}


def fetch_news_list(source_id: str) -> list[dict]:
    """从 NewsNow API 获取新闻列表。"""
    url = f"https://newsnow.busiyi.world/api/s?id={source_id}"
    resp = requests.get(url, headers=HEADERS, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    return data.get("items", [])


def fetch_news_detail(url: str) -> str:
    """获取新闻详情页内容（纯文本清理）。"""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        # 简单清理 HTML 标签
        import re
        text = re.sub(r"<[^>]+>", "", resp.text)
        text = re.sub(r"\s+", " ", text).strip()
        return text[:2000] if text else "无法解析新闻详情"
    except Exception as e:
        print(f"[news] 获取详情失败: {e}")
        return "无法获取详细内容"


def get_news(source: str = "", detail: bool = False) -> str:
    """获取新闻。

    Args:
        source: 新闻源中文名，为空则从默认源随机选
        detail: True 获取上一条新闻详情

    Returns:
        新闻文本
    """
    global _last_news

    # 获取详情模式
    if detail:
        if not _last_news:
            return "抱歉，没有最近查询的新闻记录，请先获取一条新闻。"
        url = _last_news.get("url", "")
        title = _last_news.get("title", "")
        if not url or url == "#":
            return "抱歉，该新闻没有可用的详情链接。"
        detail_content = fetch_news_detail(url)
        return (
            f"新闻标题：{title}\n\n详细内容：\n{detail_content}\n\n"
            f"(请对上述新闻内容进行总结，以自然口语化的方式讲述，就像在和朋友聊天一样)"
        )

    # 正常获取新闻
    sources_list = [s.strip() for s in DEFAULT_SOURCES.split(";") if s.strip()]
    if source and source in CHANNEL_MAP:
        source_id = CHANNEL_MAP[source]
    else:
        # 随机选择一个默认源
        chosen = random.choice(sources_list)
        source_id = CHANNEL_MAP.get(chosen, "thepaper")
        source = chosen if chosen in sources_list else "澎湃新闻"

    try:
        items = fetch_news_list(source_id)
        if not items:
            return f"未能从{source}获取到新闻，请稍后重试。"

        selected = random.choice(items)
        _last_news = {
            "url": selected.get("url", ""),
            "title": selected.get("title", "无标题"),
        }

        return (
            f"新闻来源：{source}\n"
            f"新闻标题：{selected['title']}\n\n"
            f"(请用自然口语向用户播报这条新闻，可以询问用户是否想了解详情)"
        )
    except Exception as e:
        print(f"[news] 获取新闻失败: {e}")
        return f"获取新闻失败（{source}），请稍后重试。"
