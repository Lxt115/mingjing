idf_component_register(
    SRCS main.c wifi.c websocket.c i2s_audio.c protocol.c
    INCLUDE_DIRS .
    REQUIRES nvs_flash esp_wifi esp_netif driver mbedtls esp_timer json
)
