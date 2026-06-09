#include <string.h>
#include <stdlib.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/queue.h"
#include "freertos/event_groups.h"
#include "esp_system.h"
#include "esp_log.h"
#include "esp_timer.h"
#include "nvs_flash.h"
#include "driver/gpio.h"

#include "esp_opus_enc.h"
#include "esp_opus_dec.h"
#include "esp_audio_enc.h"
#include "esp_audio_dec.h"

#include "wifi.h"
#include "websocket.h"
#include "i2s_audio.h"
#include "protocol.h"

#define WS_URL_MAX 256

#define PIN_BTN     9
#define PIN_LED     2

#define OPUS_FRAME_DURATION_MS 60
#define OPUS_SAMPLE_RATE       16000
#define OPUS_FRAME_SAMPLES     (OPUS_SAMPLE_RATE * OPUS_FRAME_DURATION_MS / 1000)

static const char *TAG = "app";

static QueueHandle_t s_playback_queue = NULL;
static TaskHandle_t s_record_task = NULL;
static bool s_recording = false;

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
        ESP_LOGI(TAG, "transcript: %s", msg.text);
        break;
    case PROTO_MSG_TEXT_CHUNK:
        break;
    case PROTO_MSG_AUDIO_DONE: {
        audio_chunk_t stop = { .data = NULL, .len = 0 };
        xQueueSend(s_playback_queue, &stop, 0);
        break;
    }
    case PROTO_MSG_ERROR:
        ESP_LOGW(TAG, "server error: %s", msg.text);
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

    /* Notify server: recording starts */
    char json_buf[256];
    proto_build_audio_start(json_buf, sizeof(json_buf));
    websocket_send_text(json_buf, strlen(json_buf));

    /* Stop playback if any */
    {
        audio_chunk_t stop = { .data = NULL, .len = 0 };
        xQueueSend(s_playback_queue, &stop, 0);
    }
    i2s_record_start();

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

    proto_build_audio_end(json_buf, sizeof(json_buf));
    websocket_send_text(json_buf, strlen(json_buf));

    free(rx_buf); free(opus_buf);
    s_record_task = NULL;
    vTaskDelete(NULL);
}

static void btn_init(void) {
    gpio_reset_pin(PIN_BTN);
    gpio_set_direction(PIN_BTN, GPIO_MODE_INPUT);
    gpio_set_pull_mode(PIN_BTN, GPIO_PULLUP_ONLY);
}

static void app_main_task(void *arg) {
    static char ws_url[WS_URL_MAX];

    const char *agent_id = CONFIG_DEVICE_AGENT_ID;
    const char *server_host = CONFIG_DEVICE_SERVER_HOST;
    const char *server_port = CONFIG_DEVICE_SERVER_PORT;

    snprintf(ws_url, sizeof(ws_url), "ws://%s:%s/ws/voice/%s",
             server_host, server_port, agent_id);

    ESP_LOGI(TAG, "Wi-Fi connected, starting WS → %s", ws_url);

    websocket_init(ws_url, on_websocket_text, on_websocket_binary);

    led_blink(3);

    while (websocket_is_connected() == false) {
        vTaskDelay(pdMS_TO_TICKS(500));
    }
    led_blink(1);
    ESP_LOGI(TAG, "WebSocket connected");

    bool stable = true;
    int  debounce = 0;

    while (1) {
        bool raw = gpio_get_level(PIN_BTN);

        if (raw == stable) {
            debounce = 0;
        } else {
            debounce++;
            if (debounce >= 4) {
                if (stable && !raw) {
                    /* Button pressed */
                    if (!s_recording) {
                        s_recording = true;
                        i2s_playback_stop();
                        xQueueReset(s_playback_queue);
                        xTaskCreatePinnedToCore(record_task, "record", 32768, NULL, 5,
                                                &s_record_task, tskNO_AFFINITY);
                        ESP_LOGI(TAG, "recording started");
                    }
                } else if (!stable && raw) {
                    /* Button released */
                    if (s_recording) {
                        s_recording = false;
                        ESP_LOGI(TAG, "recording stopped, waiting for response");
                    }
                }
                stable = raw;
                debounce = 0;
            }
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

    wifi_init_sta();

    audio_init(I2S_BCK, I2S_WS, I2S_DIN, I2S_DOUT);

    xTaskCreatePinnedToCore(app_main_task, "app_main", 8192, NULL, 3, NULL, tskNO_AFFINITY);
}
