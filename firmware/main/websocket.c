#include "websocket.h"
#include "esp_log.h"
#include "esp_websocket_client.h"
#include <string.h>

static const char *TAG = "websocket";

static esp_websocket_client_handle_t s_client = NULL;
static ws_on_text_cb_t s_on_text = NULL;
static bool s_connected = false;

static void websocket_event_handler(void *arg, esp_event_base_t event_base,
                                    int32_t event_id, void *event_data) {
    esp_websocket_event_data_t *data = (esp_websocket_event_data_t *)event_data;

    switch (event_id) {
    case WEBSOCKET_EVENT_CONNECTED:
        ESP_LOGI(TAG, "WEBSOCKET_EVENT_CONNECTED");
        s_connected = true;
        break;
    case WEBSOCKET_EVENT_DISCONNECTED:
        ESP_LOGI(TAG, "WEBSOCKET_EVENT_DISCONNECTED");
        s_connected = false;
        break;
    case WEBSOCKET_EVENT_DATA:
        if (data->op_code == 0x01 && s_on_text) {
            s_on_text(data->data_ptr, data->data_len);
        }
        break;
    case WEBSOCKET_EVENT_ERROR:
        ESP_LOGI(TAG, "WEBSOCKET_EVENT_ERROR");
        s_connected = false;
        break;
    default:
        break;
    }
}

void websocket_init(const char *url, ws_on_text_cb_t on_text) {
    s_on_text = on_text;

    esp_websocket_client_config_t ws_cfg = {
        .uri = url,
        .reconnect_timeout_ms = 2000,
        .network_timeout_ms = 5000,
        .ping_interval_sec = 10,
        .task_stack = 8192,
        .buffer_size = 8192,
    };

    s_client = esp_websocket_client_init(&ws_cfg);
    esp_websocket_register_events(s_client, WEBSOCKET_EVENT_ANY,
                                  websocket_event_handler, NULL);
    esp_websocket_client_start(s_client);
}

void websocket_deinit(void) {
    if (s_client) {
        esp_websocket_client_stop(s_client);
        esp_websocket_client_destroy(s_client);
        s_client = NULL;
    }
    s_connected = false;
}

bool websocket_is_connected(void) {
    return s_connected;
}

void websocket_send_text(const char *data, int len) {
    if (s_client && s_connected) {
        esp_websocket_client_send_text(s_client, data, len, portMAX_DELAY);
    }
}
