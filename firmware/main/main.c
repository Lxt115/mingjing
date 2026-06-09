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
#include "mbedtls/base64.h"

#include "wifi.h"
#include "websocket.h"
#include "i2s_audio.h"
#include "protocol.h"

#define WS_URL_MAX 256

#define PIN_BTN     9
#define PIN_LED     2

static const char *TAG = "app";

static QueueHandle_t s_playback_queue = NULL;
static TaskHandle_t s_record_task = NULL;
static bool s_recording = false;

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

static void playback_task(void *arg) {
    audio_chunk_t chunk;

    while (1) {
        if (xQueueReceive(s_playback_queue, &chunk, portMAX_DELAY) == pdTRUE) {
            if (chunk.data == NULL) {
                /* Stop marker: disable TX to kill DAC idle noise */
                i2s_playback_stop();
                continue;
            }
            i2s_playback_start();
            i2s_playback_write(chunk.data, chunk.len);
            free(chunk.data);
        }
    }

    vTaskDelete(NULL);
}

static void on_websocket_text(const char *text, int len) {
    static proto_msg_t msg;
    memset(&msg, 0, sizeof(msg));
    if (!proto_parse(text, len, &msg)) return;

    switch (msg.type) {
    case PROTO_MSG_AUDIO_CHUNK: {
        if (msg.content_len > 0) {
            size_t decoded_len = 0;
            mbedtls_base64_decode(NULL, 0, &decoded_len,
                                  (const unsigned char *)msg.content, msg.content_len);
            uint8_t *decoded = malloc(decoded_len);
            if (decoded && mbedtls_base64_decode(decoded, decoded_len, &decoded_len,
                                                  (const unsigned char *)msg.content,
                                                  msg.content_len) == 0) {
                audio_chunk_t chunk = { .data = decoded, .len = (int)decoded_len };
                if (xQueueSend(s_playback_queue, &chunk, 0) != pdTRUE) {
                    free(decoded);
                }
            } else {
                free(decoded);
            }
        }
        break;
    }
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

static void record_task(void *arg) {
    TickType_t last_wake = xTaskGetTickCount();
    int mono_samples = DEVICE_AUDIO_CHUNK_BYTES / sizeof(int16_t);
    /* I2S is stereo, read 2x buffer then extract left channel */
    int16_t *rx_buf = malloc(mono_samples * sizeof(int16_t) * 2);
    size_t b64_buf_size = (DEVICE_AUDIO_CHUNK_BYTES * 4 / 3) + 4;
    uint8_t *b64_buf = malloc(b64_buf_size);
    char *json_buf = malloc(PROTO_BUF_SIZE);

    if (!rx_buf || !b64_buf || !json_buf) {
        ESP_LOGE(TAG, "record_task: malloc failed");
        free(rx_buf); free(b64_buf); free(json_buf);
        vTaskDelete(NULL);
        return;
    }

    proto_build_audio_start(json_buf, PROTO_BUF_SIZE);
    websocket_send_text(json_buf, strlen(json_buf));

    /* Tell playback to stop */
    {
        audio_chunk_t stop = { .data = NULL, .len = 0 };
        xQueueSend(s_playback_queue, &stop, 0);
    }
    i2s_record_start();

    int chunk_count = 0;
    int total_read = 0;
    int i2s_slots = mono_samples * 2;  /* stereo: read 2x slots */
    while (s_recording) {
        int read = i2s_record_read(rx_buf, i2s_slots);
        if (read >= i2s_slots) {
            /* Extract left channel from stereo interleaved (L,R,L,R,...) */
            for (int i = 0; i < mono_samples; i++) {
                rx_buf[i] = rx_buf[i * 2];
            }
            chunk_count++;
            total_read += mono_samples;
            size_t olen = 0;
            mbedtls_base64_encode(b64_buf, b64_buf_size, &olen,
                                  (const unsigned char *)rx_buf, mono_samples * sizeof(int16_t));
            int json_len = proto_build_audio_chunk(json_buf, PROTO_BUF_SIZE, b64_buf, olen);
            websocket_send_text(json_buf, json_len);
        }
        vTaskDelayUntil(&last_wake, pdMS_TO_TICKS(DEVICE_AUDIO_CHUNK_MS));
    }

    i2s_record_stop();
    ESP_LOGI(TAG, "record done: chunks=%d total_samples=%d", chunk_count, total_read);
    proto_build_audio_end(json_buf, PROTO_BUF_SIZE);
    websocket_send_text(json_buf, strlen(json_buf));

    free(rx_buf); free(b64_buf); free(json_buf);
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

    websocket_init(ws_url, on_websocket_text);

    led_blink(3);

    while (websocket_is_connected() == false) {
        vTaskDelay(pdMS_TO_TICKS(500));
    }
    led_blink(1);
    ESP_LOGI(TAG, "WebSocket connected");

    bool stable = true;   /* debounced stable state (true = not pressed) */
    int  debounce = 0;

    while (1) {
        bool raw = gpio_get_level(PIN_BTN);

        /* ── software debounce: state must be stable for 4 consecutive reads (80ms) ── */
        if (raw == stable) {
            debounce = 0;
        } else {
            debounce++;
            if (debounce >= 4) {
                /* Edge detected */
                if (stable && !raw) {
                    /* Falling edge: button pressed */
                    if (!s_recording) {
                        s_recording = true;
                        i2s_playback_stop();
                        xQueueReset(s_playback_queue);
                        xTaskCreatePinnedToCore(record_task, "record", 8192, NULL, 5,
                                                &s_record_task, tskNO_AFFINITY);
                        ESP_LOGI(TAG, "recording started");
                    }
                } else if (!stable && raw) {
                    /* Rising edge: button released */
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

    s_playback_queue = xQueueCreate(32, sizeof(audio_chunk_t));
    xTaskCreatePinnedToCore(playback_task, "playback", 6144, NULL, 4, NULL, tskNO_AFFINITY);

    wifi_init_sta();

    audio_init(I2S_BCK, I2S_WS, I2S_DIN, I2S_DOUT);

    xTaskCreatePinnedToCore(app_main_task, "app_main", 8192, NULL, 3, NULL, tskNO_AFFINITY);
}
