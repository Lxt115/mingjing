#pragma once
#include "esp_err.h"
#include "freertos/FreeRTOS.h"
#include "freertos/event_groups.h"

#define WIFI_CONNECTED_BIT BIT0
#define WIFI_FAIL_BIT      BIT1

extern EventGroupHandle_t wifi_event_group;

/**
 * @brief 初始化 WiFi（带 NVS 凭据管理 + AP 配网模式）
 *
 * 启动流程：
 *   1. 尝试从 NVS 读取已保存的 SSID/密码
 *   2. 如果 NVS 中有凭据 → 尝试连接 Station 模式
 *   3. 如果 NVS 中无凭据 → 回退到 Kconfig 编译期默认值（向后兼容）
 *   4. 如果连接失败 → 自动进入 AP 配网模式
 *
 * AP 配网模式：
 *   - SSID: "Aidoll-Config"
 *   - 无需密码（OPEN）
 *   - 手机连上后访问 http://192.168.4.1/ 进行配网
 *   - 提交后凭据写入 NVS，设备自动重启
 *
 * 返回值：阻塞直到连接成功（或进入 AP 配网模式时立即返回）
 */
void wifi_init(void);

/**
 * @brief 保存 WiFi 凭据到 NVS
 */
esp_err_t wifi_save_credentials(const char *ssid, const char *password);

/**
 * @brief 从 NVS 加载 WiFi 凭据
 * @return true 表示 NVS 中有凭据
 */
bool wifi_load_credentials(char *ssid_out, size_t ssid_size,
                           char *pwd_out, size_t pwd_size);

/**
 * @brief 清除 NVS 中的 WiFi 凭据
 */
void wifi_erase_credentials(void);

/**
 * @brief 获取设备绑定码（永久，首次调用时自动生成并存入 NVS）
 * @return 6 位数字字符串，设备生命周期内不变
 */
const char* wifi_get_bind_code(void);
