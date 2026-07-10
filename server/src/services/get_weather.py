"""
天气查询服务 —— 基于和风天气 API。

流程：
1. 通过 Geo API 查询城市经纬度
2. 爬取和风天气网页获取实时天气 + 7天预报
3. 缓存结果避免频繁请求
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

# ── 天气代码映射 https://dev.qweather.com/docs/resource/icons/ ──
WEATHER_CODE_MAP = {
    "100": "晴", "101": "多云", "102": "少云", "103": "晴间多云", "104": "阴",
    "150": "晴", "151": "多云", "152": "少云", "153": "晴间多云",
    "300": "阵雨", "301": "强阵雨", "302": "雷阵雨", "303": "强雷阵雨",
    "304": "雷阵雨伴有冰雹", "305": "小雨", "306": "中雨", "307": "大雨",
    "308": "极端降雨", "309": "毛毛雨/细雨", "310": "暴雨", "311": "大暴雨",
    "312": "特大暴雨", "313": "冻雨", "314": "小到中雨", "315": "中到大雨",
    "316": "大到暴雨", "317": "暴雨到大暴雨", "318": "大暴雨到特大暴雨",
    "350": "阵雨", "351": "强阵雨", "399": "雨",
    "400": "小雪", "401": "中雪", "402": "大雪", "403": "暴雪",
    "404": "雨夹雪", "405": "雨雪天气", "406": "阵雨夹雪", "407": "阵雪",
    "408": "小到中雪", "409": "中到大雪", "410": "大到暴雪",
    "456": "阵雨夹雪", "457": "阵雪", "499": "雪",
    "500": "薄雾", "501": "雾", "502": "霾", "503": "扬沙", "504": "浮尘",
    "507": "沙尘暴", "508": "强沙尘暴", "509": "浓雾", "510": "强浓雾",
    "511": "中度霾", "512": "重度霾", "513": "严重霾", "514": "大雾", "515": "特强浓雾",
    "900": "热", "901": "冷", "999": "未知",
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36"
    )
}

# ── 简单内存缓存 ──
_cache: dict = {}


def _fetch_city_info(location: str, api_host: str, api_key: str) -> dict | None:
    """通过和风天气 Geo API 获取城市信息。"""
    url = f"https://{api_host}/geo/v2/city/lookup?key={api_key}&location={location}&lang=zh"
    resp = requests.get(url, headers=HEADERS, timeout=10)
    data = resp.json()
    if data.get("code") != "200":
        print(f"[weather] Geo API 错误: {data}")
        return None
    locations = data.get("location", [])
    return locations[0] if locations else None


def _fetch_weather_page(url: str) -> BeautifulSoup | None:
    """抓取和风天气网页。"""
    resp = requests.get(url, headers=HEADERS, timeout=10)
    return BeautifulSoup(resp.text, "html.parser") if resp.ok else None


def _parse_weather(soup: BeautifulSoup) -> str:
    """解析天气网页，返回格式化的天气文本。"""
    try:
        city = soup.select_one("h1.c-submenu__location")
        city_name = city.get_text(strip=True) if city else "未知城市"

        # 当前天气
        current = soup.select_one(".c-city-weather-current .current-abstract")
        current_abstract = current.get_text(strip=True) if current else "未知"

        # 当前详细参数
        details = []
        for item in soup.select(".c-city-weather-current .current-basic .current-basic___item"):
            parts = item.get_text(strip=True, separator=" ").split(" ")
            if len(parts) == 2:
                key, value = parts[1], parts[0]
                if value and value != "0":
                    details.append(f"  · {key}: {value}")

        # 7天预报
        forecasts = []
        for row in soup.select(".city-forecast-tabs__row")[:7]:
            date_el = row.select_one(".date-bg .date")
            icon_el = row.select_one(".date-bg .icon")
            temps = [span.get_text(strip=True) for span in row.select(".tmp-cont .temp")]

            date = date_el.get_text(strip=True) if date_el else ""
            code = icon_el["src"].split("/")[-1].split(".")[0] if icon_el else "999"
            weather = WEATHER_CODE_MAP.get(code, "未知")
            high, low = (temps[0], temps[-1]) if len(temps) >= 2 else ("?", "?")
            forecasts.append(f"{date}: {weather}，{low}~{high}")

        lines = [f"{city_name}当前天气：{current_abstract}"]
        if details:
            lines.append("详细参数：")
            lines.extend(details)
        if forecasts:
            lines.append("\n未来7天预报：")
            lines.extend(forecasts)

        return "\n".join(lines)
    except Exception as e:
        print(f"[weather] 解析天气页面失败: {e}")
        return ""


def get_weather(
    location: str = "北京",
    api_host: str = "mj7p3y7naa.re.qweatherapi.com",
    api_key: str = "",
) -> str:
    """获取指定城市的天气信息（带缓存）。

    Args:
        location: 城市名，如"北京"、"广州"
        api_host: 和风天气 API Host
        api_key: 和风天气 API Key

    Returns:
        格式化的天气文本，失败时返回空字符串
    """
    if not api_key:
        print("[weather] 未配置和风天气 API Key，跳过天气查询")
        return ""

    cache_key = f"{location}"
    # 缓存 30 分钟
    if cache_key in _cache:
        cached_time, cached_text = _cache[cache_key]
        if datetime.now() - cached_time < timedelta(minutes=30):
            return cached_text

    try:
        city_info = _fetch_city_info(location, api_host, api_key)
        if not city_info:
            print(f"[weather] 未找到城市: {location}")
            return ""

        fx_link = city_info.get("fxLink", "")
        if not fx_link:
            print(f"[weather] 无天气链接: {location}")
            return ""

        soup = _fetch_weather_page(fx_link)
        if not soup:
            print(f"[weather] 无法获取天气页面: {fx_link}")
            return ""

        weather_text = _parse_weather(soup)
        if weather_text:
            _cache[cache_key] = (datetime.now(), weather_text)
            print(f"[weather] 天气获取成功: {location}")
        return weather_text

    except requests.exceptions.Timeout:
        print(f"[weather] 请求超时: {location}")
        return ""
    except requests.exceptions.RequestException as e:
        print(f"[weather] 请求失败: {e}")
        return ""
    except Exception as e:
        print(f"[weather] 获取异常: {e}")
        return ""
