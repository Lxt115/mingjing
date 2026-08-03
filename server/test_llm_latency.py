# -*- coding: utf-8 -*-
"""首帧音频延迟对比测试：DeepSeek vs 阿里百炼(qwen) vs 豆包(火山方舟)

测量口径与生产 pipeline 一致：LLM 流式开始 -> 生成完第一句话 -> 火山 TTS 第一块音频出来。
输出每家 3 轮的：TTFT / 首句完成 / TTS首块 / 首帧音频延迟(=首句+TTS) / 全文生成完成。
"""
import asyncio
import json
import os
import statistics
import sys
import time
import uuid

import httpx

sys.stdout.reconfigure(encoding="utf-8")

ENV_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env.production")
SENTENCE_BOUNDARIES = "。！？!?；;\n"
PROMPT = "用一句话介绍你自己，50字以内。"
N_ROUNDS = 3
TIMEOUT = 30.0

# 火山 TTS 参数（与 src/providers/tts/volcano.py 保持一致）
TTS_URL = "https://openspeech.bytedance.com/api/v3/tts/unidirectional"
TTS_VOICE = "zh_female_vv_uranus_bigtts"


def load_env(path: str) -> dict:
    env = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            env[k.strip()] = v.strip()
    return env


def find_boundary(s: str):
    """返回字符串中第一个句边界字符的下标，没有则 None"""
    idx = None
    for c in SENTENCE_BOUNDARIES:
        i = s.find(c)
        if i != -1 and (idx is None or i < idx):
            idx = i
    return idx


async def measure_llm(base_url: str, api_key: str, model: str, prompt: str, extra: dict | None = None):
    """流式调用 LLM，返回 (ttft, first_sentence_at, first_sentence_text, total, err)"""
    url = base_url.rstrip("/") + "/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": True,
        "max_tokens": 200,
    }
    if extra:
        body.update(extra)
    t0 = time.perf_counter()
    ttft = None
    first_sentence_at = None
    first_sentence_text = ""
    buf = ""
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            async with client.stream("POST", url, json=body, headers=headers) as resp:
                if resp.status_code != 200:
                    raw = (await resp.aread()).decode(errors="ignore")[:200]
                    return None, None, "", None, f"HTTP {resp.status_code}: {raw}"
                async for line in resp.aiter_lines():
                    if not line.startswith("data:"):
                        continue
                    data = line[5:].strip()
                    if data == "[DONE]":
                        break
                    try:
                        obj = json.loads(data)
                        delta = obj["choices"][0]["delta"].get("content", "")
                    except (json.JSONDecodeError, KeyError, IndexError, TypeError):
                        continue
                    if not delta:
                        continue
                    now = time.perf_counter()
                    if ttft is None:
                        ttft = now - t0
                    buf += delta
                    if first_sentence_at is None:
                        idx = find_boundary(buf)
                        if idx is not None:
                            first_sentence_at = now - t0
                            first_sentence_text = buf[: idx + 1]
    except Exception as e:  # noqa: BLE001
        return None, None, "", None, f"异常: {e}"
    total = time.perf_counter() - t0
    if first_sentence_at is None and buf:
        first_sentence_at = total
        first_sentence_text = buf
    return ttft, first_sentence_at, first_sentence_text, total, None


async def tts_first_chunk(text: str, api_key: str):
    """火山 TTS 流式合成，返回首块耗时(秒)或错误"""
    if not text:
        return None, "无文本"
    headers = {
        "X-Api-Key": api_key,
        "X-Api-Resource-Id": "seed-tts-2.0",
        "X-Api-Request-Id": uuid.uuid4().hex[:32],
        "Content-Type": "application/json",
    }
    payload = {
        "req_params": {
            "text": text,
            "speaker": TTS_VOICE,
            "audio_params": {"format": "pcm", "sample_rate": 16000},
        }
    }
    t0 = time.perf_counter()
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            async with client.stream("POST", TTS_URL, json=payload, headers=headers) as resp:
                if resp.status_code != 200:
                    raw = (await resp.aread()).decode(errors="ignore")[:200]
                    return None, f"TTS HTTP {resp.status_code}: {raw}"
                async for line in resp.aiter_lines():
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if obj.get("data"):
                        return time.perf_counter() - t0, None
    except Exception as e:  # noqa: BLE001
        return None, f"TTS 异常: {e}"
    return None, "TTS 未返回音频块"


async def _run_rounds(provider: dict, model: str, label: str, volcano_key: str, extra) -> list:
    """对单个模型跑 N_ROUNDS 轮，返回带 label 的结果行"""
    rows = []
    print(f"  [{label}] 使用 model={model}")
    for i in range(1, N_ROUNDS + 1):
        ttft, fst, text, total, err = await measure_llm(
            provider["base_url"], provider["api_key"], model, PROMPT, extra
        )
        if err:
            print(f"  第{i}轮失败: {err[:100]}")
            continue
        tts_time, tts_err = await tts_first_chunk(text, volcano_key)
        if tts_err:
            print(f"  第{i}轮 TTS 失败: {tts_err}（首句: {text[:20]}…）")
        first_audio = (fst or 0) + (tts_time or 0)
        rows.append(
            {
                "label": label,
                "round": i,
                "ttft": ttft,
                "first_sentence": fst,
                "tts": tts_time,
                "first_audio": first_audio if tts_time else None,
                "total": total,
            }
        )
        print(
            f"  第{i}轮: TTFT={ttft*1000:.0f}ms 首句={fst*1000:.0f}ms "
            f"TTS首块={tts_time*1000 if tts_time else None:.0f}ms "
            f"首帧音频={first_audio*1000 if first_audio else None:.0f}ms "
            f"全文完成={total*1000:.0f}ms | 首句: {text[:24]}"
        )
    return rows


async def run_provider(provider: dict, volcano_key: str) -> list:
    """运行一个 provider。
    - 支持 model_groups：[(label, [候选model...])]，每组选第一个可用模型跑 N_ROUNDS
    - 否则按 models 列表跑第一个可用模型
    返回结果行列表。
    """
    rows = []
    extra = provider.get("extra")
    groups = provider.get("model_groups")
    if groups is not None:
        for label, models in groups:
            chosen = None
            for model in models:
                _, _, _, _, err = await measure_llm(
                    provider["base_url"], provider["api_key"], model, PROMPT, extra
                )
                if err:
                    print(f"  [{label}] model={model} 不可用: {err[:90]}")
                    continue
                chosen = model
                break
            if chosen is None:
                print(f"  [{label}] 所有候选模型均不可用")
                continue
            rows.extend(await _run_rounds(provider, chosen, label, volcano_key, extra))
        return rows

    chosen = None
    for model in provider["models"]:
        _, _, _, _, err = await measure_llm(
            provider["base_url"], provider["api_key"], model, PROMPT, extra
        )
        if err:
            print(f"  [{provider['name']}] model={model} 不可用: {err[:90]}")
            continue
        chosen = model
        break
    if chosen is None:
        return rows
    rows.extend(await _run_rounds(provider, chosen, provider["name"], volcano_key, extra))
    return rows


async def main():
    env = load_env(ENV_FILE)
    volcano_key = env.get("VOLCANO_API_KEY", "")

    providers = [
        {
            "name": "DeepSeek (deepseek-chat)",
            "base_url": "https://api.deepseek.com/v1",
            "api_key": env.get("DEEPSEEK_API_KEY", ""),
            "models": [env.get("DEEPSEEK_MODEL", "deepseek-chat")],
        },
        {
            "name": "阿里百炼 (qwen3.5-flash)",
            "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "api_key": env.get("DASHSCOPE_API_KEY", ""),
            "models": ["qwen3.5-flash"],
            "extra": {"enable_thinking": False},
        },
        {
            "name": "豆包 (火山方舟)",
            "base_url": "https://ark.cn-beijing.volces.com/api/v3",
            # 优先用环境变量 ARK_API_KEY，其次 .env.production 的 ARK_API_KEY
            "api_key": os.environ.get("ARK_API_KEY") or env.get("ARK_API_KEY", ""),
            "extra": {"thinking": {"type": "disabled"}},
            "model_groups": [
                ("Seed-2.1-turbo", ["doubao-seed-2-1-turbo-260628", "doubao-seed-2-1-turbo"]),
                ("Seed-Character", [
                    "doubao-seed-character-1-0-250815",
                    "doubao-seed-character-250815",
                    "doubao-seed-character",
                    "doubao-seed-character-1-0",
                ]),
                ("Seed-2.0-lite", [
                    "doubao-seed-2-0-lite-260128",
                    "doubao-seed-2-0-lite-250815",
                    "doubao-seed-2-0-lite",
                ]),
                ("Seed-2.0-mini", [
                    "doubao-seed-2-0-mini-260128",
                    "doubao-seed-2-0-mini-250815",
                    "doubao-seed-2-0-mini",
                ]),
                ("Seed-2.0-pro", [
                    "doubao-seed-2-0-pro-260128",
                    "doubao-seed-2-0-pro-250815",
                    "doubao-seed-2-0-pro",
                ]),
            ],
        },
    ]

    summary = []
    for p in providers:
        print(f"\n===== {p['name']} =====")
        if not p["api_key"]:
            print("  缺少 API Key，跳过")
            continue
        rows = await run_provider(p, volcano_key)
        if not rows:
            print("  无可用模型/全部失败")
            continue
        # 按 label 分组求平均
        by_label: dict[str, list] = {}
        for r in rows:
            by_label.setdefault(r["label"], []).append(r)
        for label, rws in by_label.items():
            avg = lambda k: statistics.mean([r[k] for r in rws if r.get(k) is not None])  # noqa: E731
            fa = [r["first_audio"] for r in rws if r.get("first_audio") is not None]
            summary.append(
                {
                    "name": label,
                    "ttft": avg("ttft"),
                    "first_sentence": avg("first_sentence"),
                    "tts": avg("tts"),
                    "first_audio": statistics.mean(fa) if fa else None,
                    "total": avg("total"),
                    "n": len(rws),
                }
            )

    print("\n\n========== 汇总（平均值, ms） ==========")
    print(f"{'provider':<26}{'n':>3}{'TTFT':>8}{'首句':>8}{'TTS首块':>8}{'首帧音频':>10}{'全文完成':>10}")
    for s in summary:
        fmt = lambda v: f"{v*1000:.0f}" if v is not None else "N/A"  # noqa: E731
        print(
            f"{s['name']:<26}{s['n']:>3}{fmt(s['ttft']):>8}{fmt(s['first_sentence']):>8}"
            f"{fmt(s['tts']):>8}{fmt(s['first_audio']):>10}{fmt(s['total']):>10}"
        )


if __name__ == "__main__":
    asyncio.run(main())
