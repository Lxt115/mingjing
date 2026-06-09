#pragma once
#include "esp_err.h"
#include <stdint.h>
#include <stdbool.h>

typedef void (*ws_on_text_cb_t)(const char *text, int len);
typedef void (*ws_on_binary_cb_t)(const uint8_t *data, int len);

void websocket_init(const char *url, ws_on_text_cb_t on_text, ws_on_binary_cb_t on_binary);
void websocket_deinit(void);
bool websocket_is_connected(void);
void websocket_send_text(const char *data, int len);
void websocket_send_binary(const uint8_t *data, int len);
