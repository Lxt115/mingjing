"""
农历黄历查询服务 —— 基于 cnlunar 库。

提供天干地支、生肖、八字、节气、宜忌等黄历信息。
"""

from datetime import datetime, timezone, timedelta

CHINA_TZ = timezone(timedelta(hours=8))


def get_lunar(date_str: str | None = None, query: str | None = None) -> str:
    """获取农历黄历信息。

    Args:
        date_str: 日期 YYYY-MM-DD，默认今天
        query: 查询内容描述，如"宜忌""节气""八字"等
    """
    try:
        import cnlunar
    except ImportError:
        return "农历黄历模块未安装（cnlunar），请安装: pip install cnlunar"

    if date_str:
        try:
            now = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            return f"日期格式错误，请使用 YYYY-MM-DD 格式，例如 2024-01-01"
    else:
        now = datetime.now(CHINA_TZ).replace(tzinfo=None)

    if query is None:
        query = "默认"

    lunar = cnlunar.Lunar(now, godType="8char")

    lines = [
        f"根据以下信息回应用户关于「{query}」的查询：",
        "",
        f"公历：{now.strftime('%Y年%m月%d日')}",
        f"农历：{lunar.lunarYearCn}年{lunar.lunarMonthCn}{lunar.lunarDayCn}",
        f"干支：{lunar.year8Char}年 {lunar.month8Char}月 {lunar.day8Char}日",
        f"生肖：属{lunar.chineseYearZodiac}",
        f"八字：{' '.join([lunar.year8Char, lunar.month8Char, lunar.day8Char, lunar.twohour8Char])}",
    ]

    # 节日
    holidays = list(filter(None, [
        lunar.get_legalHolidays(),
        lunar.get_otherHolidays(),
        lunar.get_otherLunarHolidays(),
    ]))
    if holidays:
        lines.append(f"节日：{'、'.join(h for h in holidays if h)}")

    # 节气
    if lunar.todaySolarTerms:
        lines.append(f"今日节气：{lunar.todaySolarTerms}")
    if lunar.nextSolarTerm:
        lines.append(f"下一节气：{lunar.nextSolarTerm}（{lunar.nextSolarTermYear}年{lunar.nextSolarTermDate[0]}月{lunar.nextSolarTermDate[1]}日）")

    # 黄历
    lines.append(f"星座：{lunar.starZodiac}")
    lines.append(f"纳音：{lunar.get_nayin()}")
    lines.append(f"生肖冲煞：{lunar.chineseZodiacClash}")
    lines.append(f"彭祖百忌：{lunar.get_pengTaboo(delimit='、')}")
    lines.append(f"值日：{lunar.get_today12DayOfficer()[0]}执位")
    lines.append(f"值神：{lunar.get_today12DayOfficer()[1]}（{lunar.get_today12DayOfficer()[2]}）")
    lines.append(f"廿八宿：{lunar.get_the28Stars()}")
    lines.append(f"吉神方位：{' '.join(lunar.get_luckyGodsDirection())}")
    lines.append(f"今日胎神：{lunar.get_fetalGod()}")

    # 宜忌（仅要求时展示）
    if "宜" in query or "忌" in query or "黄历" in query or "择日" in query or "吉日" in query or "日子" in query:
        lines.append(f"宜：{'、'.join(lunar.goodThing[:10])}")
        lines.append(f"忌：{'、'.join(lunar.badThing[:10])}")
    else:
        lines.append("（如需查询今日宜忌，请明确提问）")

    return "\n".join(lines)
