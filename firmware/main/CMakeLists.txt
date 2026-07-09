idf_component_register(
    SRCS main.c wifi.c websocket.c device_ws.c i2s_audio.c protocol.c display.c
    INCLUDE_DIRS .
    REQUIRES nvs_flash esp_wifi esp_netif driver json efuse esp_audio_codec esp_http_server
)
