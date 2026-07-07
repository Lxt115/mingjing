#include "device_ws.h"
#include "esp_log.h"
#include "esp_websocket_client.h"
#include <string.h>
#include <stdio.h>
#include "cJSON.h"

static const char *TAG = "device_ws";

static esp_websocket_client_handle_t s_client = NULL;
static device_ws_cb_t s_callback = NULL;
static bool s_connected = false;
static char s_url[256] = {0};
static char s_bind_code[8] = {0};

static void send_device_info(void) {
    if (!s_connected || !s_client) return;
    char msg[64];
    snprintf(msg, sizeof(msg), "{\"type\":\"device_info\",\"bind_code\":\"%s\"}", s_bind_code);
    esp_websocket_client_send_text(s_client, msg, strlen(msg), portMAX_DELAY);
    ESP_LOGI(TAG, "sent device_info, bind_code=%s", s_bind_code);
}

static void event_handler(void *arg, esp_event_base_t event_base,
                          int32_t event_id, void *event_data) {
    esp_websocket_event_data_t *data = (esp_websocket_event_data_t *)event_data;

    switch (event_id) {
    case WEBSOCKET_EVENT_CONNECTED:
        ESP_LOGI(TAG, "connected");
        s_connected = true;
        send_device_info();
        break;
    case WEBSOCKET_EVENT_DISCONNECTED:
        ESP_LOGI(TAG, "disconnected");
        s_connected = false;
        break;
    case WEBSOCKET_EVENT_DATA:
        if (data->op_code == 0x01 && s_callback) {
            cJSON *root = cJSON_ParseWithLength(data->data_ptr, data->data_len);
            if (root) {
                cJSON *type = cJSON_GetObjectItem(root, "type");
                const char *type_str = (type && cJSON_IsString(type)) ? type->valuestring : "";
                s_callback(type_str, data->data_ptr);
                cJSON_Delete(root);
            }
        }
        break;
    case WEBSOCKET_EVENT_ERROR:
        ESP_LOGI(TAG, "error");
        s_connected = false;
        break;
    default:
        break;
    }
}

void device_ws_init(const char *device_id, const char *host, const char *port,
                    const char *bind_code, device_ws_cb_t callback) {
    if (s_client) return;
    s_callback = callback;
    strncpy(s_bind_code, bind_code ? bind_code : "000000", sizeof(s_bind_code) - 1);

    snprintf(s_url, sizeof(s_url), "ws://%s:%s/ws/device/%s", host, port, device_id);
    ESP_LOGI(TAG, "connecting to %s", s_url);

    esp_websocket_client_config_t cfg = {
        .uri = s_url,
        .reconnect_timeout_ms = portMAX_DELAY,
        .network_timeout_ms = 5000,
        .ping_interval_sec = 30,
        .task_stack = 4096,
        .buffer_size = 2048,
    };
    s_client = esp_websocket_client_init(&cfg);
    esp_websocket_register_events(s_client, WEBSOCKET_EVENT_ANY, event_handler, NULL);
    esp_websocket_client_start(s_client);
}

void device_ws_deinit(void) {
    if (s_client) {
        esp_websocket_client_stop(s_client);
        esp_websocket_client_destroy(s_client);
        s_client = NULL;
    }
    s_connected = false;
}
