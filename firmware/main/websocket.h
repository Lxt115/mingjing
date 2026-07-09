#pragma once
#include <stdint.h>
#include <stdbool.h>

typedef void (*ws_on_text_cb_t)(const char *text, int len);
typedef void (*ws_on_binary_cb_t)(const uint8_t *data, int len);
typedef void (*ws_on_state_cb_t)(bool connected);

void websocket_init(const char *url, ws_on_text_cb_t on_text, ws_on_binary_cb_t on_binary);
void websocket_set_state_callback(ws_on_state_cb_t on_state);
void websocket_deinit(void);
bool websocket_is_connected(void);
void websocket_send_text(const char *data, int len);
void websocket_send_binary(const uint8_t *data, int len);
