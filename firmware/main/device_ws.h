#pragma once
#include <stdbool.h>

/**
 * @brief 设备管理消息回调
 * @param type  消息类型: "welcome", "agent_switch"
 * @param json  完整 JSON 字符串
 */
typedef void (*device_ws_cb_t)(const char *type, const char *json);

/**
 * @brief 初始化设备管理 WebSocket 连接
 * @param device_id  设备 UUID
 * @param host       服务器 IP
 * @param port       服务器端口
 * @param bind_code  设备绑定码
 * @param callback   消息回调
 */
void device_ws_init(const char *device_id, const char *host, const char *port,
                    const char *bind_code, device_ws_cb_t callback);

/**
 * @brief 关闭设备管理 WebSocket
 */
void device_ws_deinit(void);
