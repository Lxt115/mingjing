#include <string.h>
#include <stdlib.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/queue.h"
#include "freertos/event_groups.h"
#include "esp_system.h"
#include "esp_log.h"
#include "nvs_flash.h"
#include "driver/gpio.h"

#include "esp_opus_enc.h"
#include "esp_opus_dec.h"
#include "esp_audio_enc.h"
#include "esp_audio_dec.h"

#include "wifi.h"
#include "websocket.h"
#include "device_ws.h"
#include "i2s_audio.h"
#include "protocol.h"
#include "display.h"
#include "cJSON.h"

#define WS_URL_MAX 256

#define PIN_BTN     9
#define PIN_LED     2

#define OPUS_FRAME_DURATION_MS 60
#define OPUS_SAMPLE_RATE       16000
#define OPUS_FRAME_SAMPLES     (OPUS_SAMPLE_RATE * OPUS_FRAME_DURATION_MS / 1000)

static const char *TAG = "app";

// WebSocket URL，由 app_main_task 初始化，HandleStartListeningEvent 重连时使用
static char g_ws_url[WS_URL_MAX] = {0};

/* 设备管理 WebSocket 的持久连接信息 */
static char g_agent_id[64] = "";
static char g_server_host[64] = "";
static char g_server_port[16] = "";

static QueueHandle_t s_playback_queue = NULL;
static bool s_recording = false;
static volatile bool s_aborted = false;  // 打断标志：阻止 playback_task 在打断后重新播放

// 响应期望标志：session_id 机制
// 只有当前录音结束后期望一个响应时才接受 transcript
// 新录音开始或打断时清除，确保旧录音的延迟响应被忽略
static bool s_has_pending_response = false;

/* ── 显示文本缓冲区 ── */
static char g_disp_status[32] = "Ready";    // 当前状态文本
static char g_disp_asr[128] = {0};          // 语音识别结果
static char g_disp_tts[384] = {0};          // 语音合成文本（累积）

// ── 设备状态机（DeviceState 枚举值）──
typedef enum {
    kDeviceStateIdle = 0,        // 空闲
    kDeviceStateConnecting = 1,  // 连接中（发送 audio_start 后等待服务端就绪）
    kDeviceStateListening = 2,   // 录音中
    kDeviceStateSpeaking = 3,    // 播放中
} DeviceState;

static DeviceState s_device_state = kDeviceStateIdle;

// ── 事件位定义 (FreeRTOS EventGroup) ──
#define MAIN_EVENT_START_LISTENING    (1 << 0)
#define MAIN_EVENT_STOP_LISTENING     (1 << 1)
#define MAIN_EVENT_WS_DISCONNECTED    (1 << 2)  // WebSocket 断连
#define MAIN_EVENT_AGENT_SWITCH       (1 << 3)  // 角色切换

static EventGroupHandle_t s_event_group = NULL;

// Opus 编码器/解码器
static void *s_opus_enc = NULL;
static void *s_opus_dec = NULL;
static int s_enc_frame_size = 0;
static int s_enc_outbuf_size = 0;
static int s_dec_frame_size = 0;

typedef struct {
    uint8_t *data;
    int len;
} audio_chunk_t;

/* ── 前向声明 ── */
static void record_task(void *arg);
static void led_blink(int times);
static void on_websocket_text(const char *text, int len);
static void on_websocket_binary(const uint8_t *data, int len);

/* ── 刷新显示屏：状态行 + ASR/TTS 文本 ── */

static void refresh_display(void) {
    char msg[512] = {0};
    int off = 0;
    if (g_disp_asr[0]) {
        off += snprintf(msg + off, sizeof(msg) - off, "%s\n", g_disp_asr);
    }
    if (g_disp_tts[0]) {
        off += snprintf(msg + off, sizeof(msg) - off, "%s", g_disp_tts);
    }
    display_show(g_disp_status, msg[0] ? msg : NULL);
}

/* ── 状态机 ── */

static void SetDeviceState(DeviceState new_state) {
    if (s_device_state == new_state) return;
    DeviceState old = s_device_state;
    s_device_state = new_state;
    ESP_LOGI(TAG, "State: %d → %d", old, new_state);

    switch (new_state) {
    case kDeviceStateIdle:
        strcpy(g_disp_status, "Ready");
        break;
    case kDeviceStateConnecting:
        strcpy(g_disp_status, "Connecting...");
        break;
    case kDeviceStateListening:
        strcpy(g_disp_status, "Listening...");
        break;
    case kDeviceStateSpeaking:
        strcpy(g_disp_status, "Speaking...");
        break;
    default:
        break;
    }
    refresh_display();
}

/* ── WebSocket 连接状态回调（运行在 websocket 任务上下文）── */

static void on_ws_state_changed(bool connected) {
    if (!connected) {
        xEventGroupSetBits(s_event_group, MAIN_EVENT_WS_DISCONNECTED);
    }
    // 连接成功由 HandleStartListeningEvent 中的等待循环处理，不通过事件
}

/* ── 断连清理：销毁连接 + 停止所有活动 + 复位状态 ── */

static void HandleWsDisconnected(void) {
    ESP_LOGW(TAG, "WebSocket disconnected, closing audio channel...");

    // 1. 销毁 WebSocket
    websocket_deinit();
    device_ws_deinit();

    // 2. 停止正在进行的录音
    if (s_recording) {
        s_recording = false;
    }

    // 3. 终止播放：清空播放队列 + 停止硬件
    xQueueReset(s_playback_queue);
    i2s_playback_stop();

    // 4. 状态复位到 Idle
    SetDeviceState(kDeviceStateIdle);

    // 5. 提示用户
    g_disp_asr[0] = '\0';
    g_disp_tts[0] = '\0';
    display_show("Disconnected", "Press btn to retry");
}

/* ── 打断播放：通知服务器 + 停止本地播放 + 清空播放队列 ── */

static void AbortSpeaking(void) {
    ESP_LOGI(TAG, "Abort speaking");
    // 1. 先设打断标志，防止 playback_task 收到新数据后重新启动播放
    s_aborted = true;
    // 2. 通知服务器停止推送 TTS
    char buf[64];
    proto_build_abort(buf, sizeof(buf));
    websocket_send_text(buf, strlen(buf));
    // 3. 先清空播放队列（丢弃所有未播放的音频数据）
    xQueueReset(s_playback_queue);
    // 4. 立即停止扬声器硬件
    i2s_playback_stop();
    // 5. 清除响应期望标志：打断后的旧响应不应再被接受
    //    新会话开始，旧会话作废
    s_has_pending_response = false;
    // 6. 清除显示文本
    g_disp_tts[0] = '\0';
    ESP_LOGI(TAG, "abort sent, queue cleared, playback stopped");
}

/* ── 事件处理：开始录音 ── */

static void HandleStartListeningEvent(void) {
    if (s_device_state == kDeviceStateSpeaking) {
        // ★ 打断：正在播放时按下按钮 → 先中断
        AbortSpeaking();
    }

    if (s_device_state == kDeviceStateListening ||
        s_device_state == kDeviceStateConnecting) {
        // 已经在录音或正在连接中，忽略重复按下
        return;
    }

    // 如果 WebSocket 未连接，先建连再开始录音
    if (!websocket_is_connected()) {
        ESP_LOGI(TAG, "WebSocket not connected, reconnecting...");
        display_show("Connecting...", NULL);
        led_blink(3);

        websocket_init(g_ws_url, on_websocket_text, on_websocket_binary);
        websocket_set_state_callback(on_ws_state_changed);

        // 阻塞等待连接（10s 超时）
        int retry = 0;
        while (!websocket_is_connected() && retry < 100) {  // 最多等约 10 秒
            vTaskDelay(pdMS_TO_TICKS(100));
            retry++;
        }

        if (!websocket_is_connected()) {
            ESP_LOGE(TAG, "Reconnect failed");
            websocket_deinit();
            display_show("Connect failed", "Press btn to retry");
            return;
        }

        ESP_LOGI(TAG, "WebSocket (re)connected");
        led_blink(1);
    }

    // Idle 或被中断后 → 开始录音流程（同步启动，不等 task 回调）
    if (!s_recording) {
        s_recording = true;
        s_has_pending_response = false;
        g_disp_asr[0] = '\0';
        g_disp_tts[0] = '\0';
        s_aborted = false;

        /* 同步发送 audio_start + 启动 I2S 录音，然后直接切到 Listening
         * abort → open channel → SetDeviceState(Listening) 一气呵成 */
        char json_buf[256];
        proto_build_audio_start(json_buf, sizeof(json_buf));
        websocket_send_text(json_buf, strlen(json_buf));

        audio_chunk_t stop = { .data = NULL, .len = 0 };
        xQueueSend(s_playback_queue, &stop, 0);
        i2s_record_start();

        SetDeviceState(kDeviceStateListening);  // 直接在调用线程切状态，零延迟

        xTaskCreatePinnedToCore(record_task, "record", 32768, NULL, 5,
                                NULL, tskNO_AFFINITY);
        ESP_LOGI(TAG, "recording started");
    }
}

/* ── 事件处理：停止录音 ── */

static void HandleStopListeningEvent(void) {
    if (s_device_state == kDeviceStateListening && s_recording) {
        s_recording = false;
        s_has_pending_response = true;  // 录音结束，期望一个对应的响应
        SetDeviceState(kDeviceStateIdle);
        ESP_LOGI(TAG, "recording stopped, waiting for response");
    }
}

static void led_init(void) {
    gpio_reset_pin(PIN_LED);
    gpio_set_direction(PIN_LED, GPIO_MODE_OUTPUT);
    gpio_set_level(PIN_LED, 0);
}

static void led_blink(int times) {
    for (int i = 0; i < times; i++) {
        gpio_set_level(PIN_LED, 1);
        vTaskDelay(pdMS_TO_TICKS(80));
        gpio_set_level(PIN_LED, 0);
        vTaskDelay(pdMS_TO_TICKS(80));
    }
}

static void opus_init(void) {
    /* ── Encoder: 22050 Hz mono 60ms ── */
    esp_opus_enc_config_t enc_cfg = {
        .sample_rate      = OPUS_SAMPLE_RATE,
        .channel          = ESP_AUDIO_MONO,
        .bits_per_sample  = ESP_AUDIO_BIT16,
        .bitrate          = ESP_OPUS_BITRATE_AUTO,
        .frame_duration   = ESP_OPUS_ENC_FRAME_DURATION_60_MS,
        .application_mode = ESP_OPUS_ENC_APPLICATION_VOIP,
        .complexity       = 0,
        .enable_fec       = false,
        .enable_dtx       = true,
        .enable_vbr       = true,
    };
    esp_err_t ret = esp_opus_enc_open(&enc_cfg, sizeof(enc_cfg), &s_opus_enc);
    if (s_opus_enc && ret == ESP_AUDIO_ERR_OK) {
        esp_opus_enc_get_frame_size(s_opus_enc, &s_enc_frame_size, &s_enc_outbuf_size);
        s_enc_frame_size /= sizeof(int16_t);
        ESP_LOGI(TAG, "Opus enc ready: frame=%d samples outbuf=%d", s_enc_frame_size, s_enc_outbuf_size);
    } else {
        ESP_LOGE(TAG, "Opus enc init failed: %d", ret);
    }

    /* ── Decoder: 22050 Hz mono 60ms ── */
    esp_opus_dec_cfg_t dec_cfg = {
        .sample_rate    = OPUS_SAMPLE_RATE,
        .channel        = ESP_AUDIO_MONO,
        .frame_duration = ESP_OPUS_DEC_FRAME_DURATION_60_MS,
        .self_delimited = false,
    };
    ret = esp_opus_dec_open(&dec_cfg, sizeof(dec_cfg), &s_opus_dec);
    if (s_opus_dec && ret == ESP_AUDIO_ERR_OK) {
        s_dec_frame_size = OPUS_FRAME_SAMPLES;
        ESP_LOGI(TAG, "Opus dec ready: frame=%d samples", s_dec_frame_size);
    } else {
        ESP_LOGE(TAG, "Opus dec init failed: %d", ret);
    }
}

/* ── Playback: receive binary Opus → decode → I2S ── */

static void on_websocket_binary(const uint8_t *data, int len) {
    if (!s_opus_dec || len == 0) return;
    // 非 Speaking 状态（已打断或空闲）直接丢弃音频数据
    if (s_device_state != kDeviceStateSpeaking) return;

    /* Decode Opus → PCM */
    int16_t *pcm = malloc(s_dec_frame_size * sizeof(int16_t));
    if (!pcm) return;

    esp_audio_dec_in_raw_t raw = {
        .buffer = (uint8_t *)data,
        .len = (uint32_t)len,
        .consumed = 0,
        .frame_recover = ESP_AUDIO_DEC_RECOVERY_NONE,
    };
    esp_audio_dec_out_frame_t out_frame = {
        .buffer = (uint8_t *)pcm,
        .len = (uint32_t)(s_dec_frame_size * sizeof(int16_t)),
        .decoded_size = 0,
    };
    esp_audio_dec_info_t dec_info = {};
    esp_err_t ret = esp_opus_dec_decode(s_opus_dec, &raw, &out_frame, &dec_info);

    if (ret == ESP_AUDIO_ERR_OK && out_frame.decoded_size > 0) {
        audio_chunk_t chunk = {
            .data = (uint8_t *)pcm,
            .len = (int)out_frame.decoded_size,
        };
        if (xQueueSend(s_playback_queue, &chunk, pdMS_TO_TICKS(500)) != pdTRUE) {
            free(pcm);
        }
    } else {
        free(pcm);
    }
}

static void playback_task(void *arg) {
    audio_chunk_t chunk;
    bool started = false;

    while (1) {
        if (xQueueReceive(s_playback_queue, &chunk, portMAX_DELAY) != pdTRUE)
            continue;

        if (chunk.data == NULL) {
            if (started) {
                i2s_playback_stop();
                started = false;
            }
            continue;
        }

        if (!started) {
            if (s_aborted) {
                // 打断后忽略队列中残留的音频数据，不重新启动播放
                s_aborted = false;
                free(chunk.data);
                continue;
            }
            i2s_playback_start();
            started = true;
        }
        i2s_playback_write(chunk.data, chunk.len);
        free(chunk.data);
    }
    vTaskDelete(NULL);
}

/* ── 控制消息 (JSON text frames) ── */

static void on_websocket_text(const char *text, int len) {
    static proto_msg_t msg;
    memset(&msg, 0, sizeof(msg));
    if (!proto_parse(text, len, &msg)) return;

    switch (msg.type) {
    case PROTO_MSG_WELCOME:
        ESP_LOGI(TAG, "server welcome");
        break;
    case PROTO_MSG_TRANSCRIPT:
        // transcript 不应该无条件切换到 Speaking
        // 只有当前在 Idle 且期待响应（当前录音刚结束）时才接受
        // 打断后旧录音的延迟 transcript 会被忽略，不切换状态
        if (s_device_state == kDeviceStateIdle && s_has_pending_response) {
            s_has_pending_response = false;
            // 保存识别结果到显示缓冲区
            strncpy(g_disp_asr, msg.text, sizeof(g_disp_asr) - 1);
            g_disp_asr[sizeof(g_disp_asr) - 1] = '\0';
            g_disp_tts[0] = '\0';  // 新的回复，清空旧 TTS 文本
            SetDeviceState(kDeviceStateSpeaking);
        } else {
            ESP_LOGI(TAG, "transcript ignored (state=%d, pending=%d): %s",
                     s_device_state, s_has_pending_response, msg.text);
        }
        ESP_LOGI(TAG, "transcript: %s", msg.text);
        break;
    case PROTO_MSG_TEXT_CHUNK:
        // 累积 LLM 回复文本到显示缓冲区
        if (strlen(g_disp_tts) + strlen(msg.text) < sizeof(g_disp_tts) - 1) {
            strncat(g_disp_tts, msg.text, sizeof(g_disp_tts) - strlen(g_disp_tts) - 1);
            g_disp_tts[sizeof(g_disp_tts) - 1] = '\0';
            refresh_display();
        }
        break;
    case PROTO_MSG_AUDIO_DONE: {
        // 只有当前在 Speaking 状态时才回 Idle
        // （被打断的旧 session 的 audio_done 可能延迟到达，此时状态已是 Listening，不应切换）
        if (s_device_state == kDeviceStateSpeaking) {
            SetDeviceState(kDeviceStateIdle);
        }
        audio_chunk_t stop = { .data = NULL, .len = 0 };
        xQueueSend(s_playback_queue, &stop, 0);
        break;
    }
    case PROTO_MSG_ERROR:
        ESP_LOGW(TAG, "server error: %s", msg.text);
        break;
    case PROTO_MSG_ABORT:
        // 服务端确认打断，只有当前仍在 Speaking 状态才回 Idle
        // （可能已经通过 HandleStartListeningEvent 进入 Listening 了）
        if (s_device_state == kDeviceStateSpeaking) {
            SetDeviceState(kDeviceStateIdle);
        }
        break;
    default:
        break;
    }
}

/* ── Record: I2S → Opus encode → binary send ── */

static void record_task(void *arg) {
    TickType_t last_wake = xTaskGetTickCount();
    int16_t *rx_buf = malloc(s_enc_frame_size * sizeof(int16_t));
    uint8_t *opus_buf = malloc(s_enc_outbuf_size);

    if (!rx_buf || !opus_buf) {
        ESP_LOGE(TAG, "record_task: malloc failed");
        free(rx_buf); free(opus_buf);
        vTaskDelete(NULL);
        return;
    }

    /* audio_start + I2S 录音已在 HandleStartListeningEvent 中同步启动，
     * 这里直接进入采集 → 编码 → 发送 循环 */
    int frame_count = 0;
    int total_samples = 0;
    while (s_recording) {
        int read = i2s_record_read(rx_buf, s_enc_frame_size);
        if (read >= s_enc_frame_size) {
            /* Opus encode */
            esp_audio_enc_in_frame_t in = {
                .buffer = (uint8_t *)rx_buf,
                .len = (uint32_t)(s_enc_frame_size * sizeof(int16_t)),
            };
            esp_audio_enc_out_frame_t out = {
                .buffer = opus_buf,
                .len = (uint32_t)s_enc_outbuf_size,
                .encoded_bytes = 0,
            };
            esp_err_t ret = esp_opus_enc_process(s_opus_enc, &in, &out);
            if (ret == ESP_AUDIO_ERR_OK && out.encoded_bytes > 0) {
                websocket_send_binary(opus_buf, out.encoded_bytes);
                frame_count++;
                total_samples += s_enc_frame_size;
            }
        }
        vTaskDelayUntil(&last_wake, pdMS_TO_TICKS(OPUS_FRAME_DURATION_MS));
    }

    i2s_record_stop();
    int duration_ms = (total_samples * 1000) / OPUS_SAMPLE_RATE;
    ESP_LOGI(TAG, "record done: frames=%d samples=%d duration=%dms", frame_count, total_samples, duration_ms);

    {
        char json_buf[256];
        proto_build_audio_end(json_buf, sizeof(json_buf));
        websocket_send_text(json_buf, strlen(json_buf));
    }

    free(rx_buf); free(opus_buf);
    vTaskDelete(NULL);
}

static void btn_init(void) {
    gpio_reset_pin(PIN_BTN);
    gpio_set_direction(PIN_BTN, GPIO_MODE_INPUT);
    gpio_set_pull_mode(PIN_BTN, GPIO_PULLUP_ONLY);
}

/* ── NVS: 持久化 agent_id（重启后恢复绑定角色）── */

static void nvs_save_agent_id(const char *agent_id) {
    nvs_handle_t handle;
    if (nvs_open(WIFI_NVS_NAMESPACE, NVS_READWRITE, &handle) == ESP_OK) {
        nvs_set_str(handle, "agent_id", agent_id);
        nvs_commit(handle);
        nvs_close(handle);
        ESP_LOGI(TAG, "agent_id saved to NVS: %s", agent_id);
    }
}

static const char *nvs_load_agent_id(void) {
    static char buf[64] = "";
    nvs_handle_t handle;
    if (nvs_open(WIFI_NVS_NAMESPACE, NVS_READONLY, &handle) == ESP_OK) {
        size_t len = sizeof(buf);
        if (nvs_get_str(handle, "agent_id", buf, &len) == ESP_OK) {
            nvs_close(handle);
            ESP_LOGI(TAG, "agent_id loaded from NVS: %s", buf);
            return buf;
        }
        nvs_close(handle);
    }
    return NULL;
}

/* ── 设备管理 WebSocket 回调 ── */

static void on_device_ws_message(const char *type, const char *json) {
    if (strcmp(type, "agent_switch") == 0) {
        ESP_LOGI(TAG, "received agent_switch: %s", json);
        cJSON *root = cJSON_Parse(json);
        if (root) {
            cJSON *agent = cJSON_GetObjectItem(root, "agent_id");
            if (agent && cJSON_IsString(agent) && strlen(agent->valuestring) > 0) {
                /* 去重：与当前 agent_id 相同时跳过 */
                if (strcmp(g_agent_id, agent->valuestring) == 0) {
                    cJSON_Delete(root);
                    return;
                }
                strncpy(g_agent_id, agent->valuestring, sizeof(g_agent_id) - 1);
                g_agent_id[sizeof(g_agent_id) - 1] = '\0';
                nvs_save_agent_id(g_agent_id);
                ESP_LOGI(TAG, "agent switch queued → %s", g_agent_id);
                /* 不在 WS 回调线程里操作 WS，通过事件让主循环处理 */
                xEventGroupSetBits(s_event_group, MAIN_EVENT_AGENT_SWITCH);
            }
            cJSON_Delete(root);
        }
    } else if (strcmp(type, "welcome") == 0) {
        ESP_LOGI(TAG, "device WS welcome");
    }
}

/* ── app_main_task ── */
static void app_main_task(void *arg) {
    /* 优先从 NVS 读取上次绑定的 agent_id，回退到默认配置 */
    const char *saved_agent = nvs_load_agent_id();
    const char *agent_id = saved_agent ? saved_agent : CONFIG_DEVICE_AGENT_ID;
    const char *server_host = CONFIG_DEVICE_SERVER_HOST;
    const char *server_port = CONFIG_DEVICE_SERVER_PORT;

    /* 保存到全局变量，供设备 WS 回调使用 */
    strncpy(g_agent_id, agent_id, sizeof(g_agent_id) - 1);
    strncpy(g_server_host, server_host, sizeof(g_server_host) - 1);
    strncpy(g_server_port, server_port, sizeof(g_server_port) - 1);

    snprintf(g_ws_url, sizeof(g_ws_url), "ws://%s:%s/ws/voice/%s",
             server_host, server_port, agent_id);

    ESP_LOGI(TAG, "Wi-Fi connected, starting voice WS → %s", g_ws_url);

    websocket_init(g_ws_url, on_websocket_text, on_websocket_binary);
    websocket_set_state_callback(on_ws_state_changed);

    led_blink(3);

    while (websocket_is_connected() == false) {
        vTaskDelay(pdMS_TO_TICKS(500));
    }
    led_blink(1);
    ESP_LOGI(TAG, "voice WebSocket connected");

    /* 同时初始化设备管理 WebSocket（标记设备在线 + 接收角色切换等命令） */
    const char *device_id = CONFIG_DEVICE_ID;
    const char *bind_code = wifi_get_bind_code();
    ESP_LOGI(TAG, "opening device WS for %s, bind_code=%s", device_id, bind_code);
    device_ws_init(device_id, server_host, server_port, bind_code, on_device_ws_message);

    /* OLED 显示绑定码（与配网页面一致） */
    {
        char msg[64];
        snprintf(msg, sizeof(msg), "Bind: %s", bind_code);
        display_show("Device Ready", msg);
    }

    bool stable = true;
    int  debounce = 0;
    int  tick_counter = 0;

    while (1) {
        /* ── 按钮轮询 + 去抖 ── */
        bool raw = gpio_get_level(PIN_BTN);

        if (raw == stable) {
            debounce = 0;
        } else {
            debounce++;
            if (debounce >= 4) {
                if (stable && !raw) {
                    /* 按钮按下 → 发送事件 */
                    xEventGroupSetBits(s_event_group, MAIN_EVENT_START_LISTENING);
                } else if (!stable && raw) {
                    /* 按钮松开 → 发送事件 */
                    xEventGroupSetBits(s_event_group, MAIN_EVENT_STOP_LISTENING);
                }
                stable = raw;
                debounce = 0;
            }
        }

        /* ── 处理事件 ── */
        EventBits_t bits = xEventGroupGetBits(s_event_group);
        if (bits & MAIN_EVENT_START_LISTENING) {
            xEventGroupClearBits(s_event_group, MAIN_EVENT_START_LISTENING);
            HandleStartListeningEvent();
        }
        if (bits & MAIN_EVENT_STOP_LISTENING) {
            xEventGroupClearBits(s_event_group, MAIN_EVENT_STOP_LISTENING);
            HandleStopListeningEvent();
        }
        if (bits & MAIN_EVENT_WS_DISCONNECTED) {
            xEventGroupClearBits(s_event_group, MAIN_EVENT_WS_DISCONNECTED);
            HandleWsDisconnected();
        }
        if (bits & MAIN_EVENT_AGENT_SWITCH) {
            xEventGroupClearBits(s_event_group, MAIN_EVENT_AGENT_SWITCH);
            /* 在 app_main_task 上下文重建连接（不能在 WS 回调线程操作） */
            ESP_LOGI(TAG, "reconnecting voice with new agent: %s", g_agent_id);
            snprintf(g_ws_url, sizeof(g_ws_url), "ws://%s:%s/ws/voice/%s",
                     g_server_host, g_server_port, g_agent_id);

            /* 先停播放/录音 */
            if (s_recording) { s_recording = false; }
            xQueueReset(s_playback_queue);
            i2s_playback_stop();

            /* 重建语音 WS */
            websocket_deinit();
            xEventGroupClearBits(s_event_group, MAIN_EVENT_WS_DISCONNECTED);
            websocket_init(g_ws_url, on_websocket_text, on_websocket_binary);
            websocket_set_state_callback(on_ws_state_changed);

            /* 重建设备 WS（否则下次 agent_switch 推送不到） */
            device_ws_deinit();
            device_ws_init(CONFIG_DEVICE_ID, g_server_host, g_server_port,
                           wifi_get_bind_code(), on_device_ws_message);

            display_show("Reconnecting...", NULL);
        }

        /* 滚动显示屏中文文本（每 ~40ms 一步） */
        if (++tick_counter >= 2) {
            tick_counter = 0;
            display_tick();
        }

        vTaskDelay(pdMS_TO_TICKS(20));
    }
}

void app_main(void) {
    esp_err_t ret = nvs_flash_init();
    if (ret == ESP_ERR_NVS_NO_FREE_PAGES || ret == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        ESP_ERROR_CHECK(nvs_flash_erase());
        ret = nvs_flash_init();
    }
    ESP_ERROR_CHECK(ret);

    led_init();
    btn_init();

    opus_init();

    s_playback_queue = xQueueCreate(128, sizeof(audio_chunk_t));
    xTaskCreatePinnedToCore(playback_task, "playback", 6144, NULL, 4, NULL, tskNO_AFFINITY);

    s_event_group = xEventGroupCreate();

    /* ── WiFi 初始化（NVS 凭据 → Kconfig 兜底 → AP 配网模式）── */
    wifi_init();

    /* ── 检查是否进入 AP 配网模式 ── */
    EventBits_t wifi_bits = xEventGroupGetBits(wifi_event_group);
    if ((wifi_bits & WIFI_FAIL_BIT) && !(wifi_bits & WIFI_CONNECTED_BIT)) {
        /* AP 配网模式：显示提示并等待用户配置 */
        led_blink(1);
        audio_init(I2S_BCK, I2S_WS, I2S_DIN, I2S_DOUT);
        display_init(i2s_audio_get_i2c_bus());
        display_show("WiFi Config Mode",
                     "Connect to:\nAidoll-Config\nVisit 192.168.4.1");

        /* 等待用户通过网页配网（配网成功后 esp_restart 会重启设备） */
        while (1) {
            vTaskDelay(pdMS_TO_TICKS(1000));
        }
    }

    /* ── WiFi 已连接：正常启动流程 ── */
    audio_init(I2S_BCK, I2S_WS, I2S_DIN, I2S_DOUT);

    // Initialize OLED display on shared I2C bus
    display_init(i2s_audio_get_i2c_bus());

    xTaskCreatePinnedToCore(app_main_task, "app_main", 8192, NULL, 3, NULL, tskNO_AFFINITY);
}
