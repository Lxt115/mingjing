"""声纹识别服务提供者 —— 对接外部 voiceprint-api 服务。

voiceprint-api 项目地址: https://github.com/xinnan-tech/voiceprint-api
使用 Docker 部署后，通过 HTTP multipart/form-data 接口进行说话人识别。
"""

import time
import io
import wave
from typing import Optional
from urllib.parse import urlparse, parse_qs

import aiohttp


def _pcm_to_wav_bytes(pcm_data: bytes, sample_rate: int = 16000, channels: int = 1, bits: int = 16) -> bytes:
    """在内存中将 PCM 数据转换为 WAV 格式。"""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(bits // 8)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm_data)
    return buf.getvalue()


class VoiceprintProvider:
    """声纹识别服务提供者。

    使用方式:
        provider = VoiceprintProvider(url="http://192.168.1.25:8005/voiceprint/health?key=abcd",
                                       speaker_ids=["uuid1", "uuid2"],
                                       similarity_threshold=0.4)
        speaker_id, score = await provider.identify(pcm_audio_bytes)
    """

    def __init__(
        self,
        url: str,
        speaker_ids: list[str],
        similarity_threshold: float = 0.4,
    ):
        self.speaker_ids = speaker_ids
        self.similarity_threshold = similarity_threshold

        # 解析 API 地址和密钥
        self.api_url = ""
        self.api_key = ""

        if not url:
            self.enabled = False
        else:
            parsed = urlparse(url)
            base_url = f"{parsed.scheme}://{parsed.netloc}"
            query_params = parse_qs(parsed.query)
            self.api_key = query_params.get("key", [""])[0]

            if not self.api_key:
                self.enabled = False
            elif not speaker_ids:
                self.enabled = False
            else:
                self.api_url = f"{base_url}/voiceprint/identify"
                self.enabled = True

    async def identify(self, audio_data: bytes) -> tuple[Optional[str], float]:
        """识别说话人。

        Args:
            audio_data: WAV 格式音频数据

        Returns:
            (speaker_id, score) — 未识别到或出错时 speaker_id 为 None
        """
        if not self.enabled or not self.api_url or not self.api_key:
            return None, 0.0

        try:
            api_start_time = time.monotonic()

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Accept": "application/json",
            }

            data = aiohttp.FormData()
            data.add_field("speaker_ids", ",".join(self.speaker_ids))
            data.add_field("file", audio_data, filename="audio.wav", content_type="audio/wav")

            timeout = aiohttp.ClientTimeout(total=10)

            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(self.api_url, headers=headers, data=data) as response:
                    elapsed = time.monotonic() - api_start_time

                    if response.status == 200:
                        result = await response.json()
                        speaker_id = result.get("speaker_id")
                        score = float(result.get("score", 0))

                        if score < self.similarity_threshold:
                            print(f"[voiceprint] 声纹相似度 {score:.3f} 低于阈值 {self.similarity_threshold}")
                            return None, score

                        print(f"[voiceprint] 识别成功: speaker_id={speaker_id}, score={score:.3f}, 耗时={elapsed:.3f}s")
                        return speaker_id, score
                    else:
                        print(f"[voiceprint] API 错误: HTTP {response.status}")
                        return None, 0.0

        except aiohttp.ClientError as e:
            print(f"[voiceprint] 网络错误: {e}")
            return None, 0.0
        except Exception as e:
            print(f"[voiceprint] 识别失败: {e}")
            return None, 0.0
