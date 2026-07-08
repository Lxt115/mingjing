#include "wifi.h"
#include "wifi_config_page.h"
#include <string.h>
#include <stdlib.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/event_groups.h"
#include "esp_system.h"
#include "esp_wifi.h"
#include "esp_event.h"
#include "esp_log.h"
#include "esp_netif.h"
#include "lwip/ip4_addr.h"
#include "nvs_flash.h"
#include "nvs.h"
#include "esp_http_server.h"
#include "esp_mac.h"
#include "cJSON.h"

static const char *TAG = "wifi";

/* ── NVS ── */
#define WIFI_NVS_NAMESPACE  "wifi_cfg"
#define WIFI_NVS_KEY_SSID   "ssid"
#define WIFI_NVS_KEY_PWD    "password"
#define WIFI_NVS_KEY_APMODE "ap_mode"

/* ── AP 配网 ── */
#define WIFI_AP_SSID        "Aidoll-Config"
#define WIFI_AP_MAX_CONN    4

/* Station 连接超时 (秒) */
#define STATION_CONNECT_TIMEOUT_S 60

EventGroupHandle_t wifi_event_group;
static int s_retry_num = 0;

/* ── NVS 凭据管理 ── */

bool wifi_load_credentials(char *ssid_out, size_t ssid_size,
                           char *pwd_out, size_t pwd_size) {
    nvs_handle_t handle;
    esp_err_t err = nvs_open(WIFI_NVS_NAMESPACE, NVS_READONLY, &handle);
    if (err != ESP_OK) return false;

    size_t len = ssid_size;
    err = nvs_get_str(handle, WIFI_NVS_KEY_SSID, ssid_out, &len);
    if (err != ESP_OK) {
        nvs_close(handle);
        return false;
    }

    len = pwd_size;
    err = nvs_get_str(handle, WIFI_NVS_KEY_PWD, pwd_out, &len);
    nvs_close(handle);
    return (err == ESP_OK);
}

esp_err_t wifi_save_credentials(const char *ssid, const char *password) {
    nvs_handle_t handle;
    esp_err_t err = nvs_open(WIFI_NVS_NAMESPACE, NVS_READWRITE, &handle);
    if (err != ESP_OK) return err;

    /* 保存凭据同时清除 AP 模式标记 */
    err = nvs_set_str(handle, WIFI_NVS_KEY_SSID, ssid);
    if (err == ESP_OK) {
        err = nvs_set_str(handle, WIFI_NVS_KEY_PWD, password);
    }
    /* 清除 AP 模式标记（如果不存在则忽略错误，不影响 commit） */
    nvs_erase_key(handle, WIFI_NVS_KEY_APMODE);
    if (err == ESP_OK) {
        err = nvs_commit(handle);
    }
    nvs_close(handle);
    return err;
}

void wifi_erase_credentials(void) {
    nvs_handle_t handle;
    if (nvs_open(WIFI_NVS_NAMESPACE, NVS_READWRITE, &handle) == ESP_OK) {
        nvs_erase_all(handle);
        nvs_commit(handle);
        nvs_close(handle);
    }
}

static bool nvs_get_ap_mode_flag(void) {
    nvs_handle_t handle;
    if (nvs_open(WIFI_NVS_NAMESPACE, NVS_READONLY, &handle) != ESP_OK) return false;
    uint8_t val = 0;
    esp_err_t err = nvs_get_u8(handle, WIFI_NVS_KEY_APMODE, &val);
    nvs_close(handle);
    return (err == ESP_OK && val == 1);
}

static void nvs_set_ap_mode_flag(void) {
    nvs_handle_t handle;
    if (nvs_open(WIFI_NVS_NAMESPACE, NVS_READWRITE, &handle) == ESP_OK) {
        nvs_set_u8(handle, WIFI_NVS_KEY_APMODE, 1);
        nvs_commit(handle);
        nvs_close(handle);
    }
}

/* ── 设备绑定码（永久，存 NVS）── */
#define WIFI_NVS_KEY_BINDCODE "bind_code"

const char* wifi_get_bind_code(void) {
    static char s_code[8] = {0};
    if (s_code[0]) return s_code;

    nvs_handle_t handle;
    if (nvs_open(WIFI_NVS_NAMESPACE, NVS_READONLY, &handle) == ESP_OK) {
        size_t len = sizeof(s_code);
        if (nvs_get_str(handle, WIFI_NVS_KEY_BINDCODE, s_code, &len) == ESP_OK) {
            nvs_close(handle);
            return s_code;
        }
        nvs_close(handle);
    }

    /* 首次生成：随机 6 位数字 */
    snprintf(s_code, sizeof(s_code), "%06lu", (unsigned long)(esp_random() % 1000000));
    if (nvs_open(WIFI_NVS_NAMESPACE, NVS_READWRITE, &handle) == ESP_OK) {
        nvs_set_str(handle, WIFI_NVS_KEY_BINDCODE, s_code);
        nvs_commit(handle);
        nvs_close(handle);
    }
    ESP_LOGI(TAG, "bind code: %s", s_code);
    return s_code;
}

/* ── Station 模式事件处理 ── */

static void sta_event_handler(void *arg, esp_event_base_t event_base,
                              int32_t event_id, void *event_data) {
    if (event_base == WIFI_EVENT && event_id == WIFI_EVENT_STA_START) {
        esp_wifi_connect();
    } else if (event_base == WIFI_EVENT && event_id == WIFI_EVENT_STA_DISCONNECTED) {
        if (s_retry_num < 5) {
            esp_wifi_connect();
            s_retry_num++;
            ESP_LOGI(TAG, "retry %d to connect", s_retry_num);
        } else {
            ESP_LOGW(TAG, "station connect failed after %d retries", s_retry_num);
            xEventGroupSetBits(wifi_event_group, WIFI_FAIL_BIT);
        }
    } else if (event_base == IP_EVENT && event_id == IP_EVENT_STA_GOT_IP) {
        ip_event_got_ip_t *event = (ip_event_got_ip_t *)event_data;
        ESP_LOGI(TAG, "got ip:" IPSTR, IP2STR(&event->ip_info.ip));
        s_retry_num = 0;
        xEventGroupSetBits(wifi_event_group, WIFI_CONNECTED_BIT);
    }
}

/* ── AP 模式事件处理 ── */

static void ap_event_handler(void *arg, esp_event_base_t event_base,
                             int32_t event_id, void *event_data) {
    if (event_base == WIFI_EVENT && event_id == WIFI_EVENT_AP_START) {
        ESP_LOGI(TAG, "AP started");
    } else if (event_base == WIFI_EVENT && event_id == WIFI_EVENT_AP_STACONNECTED) {
        wifi_event_ap_staconnected_t *event = (wifi_event_ap_staconnected_t *)event_data;
        ESP_LOGI(TAG, "station connected to AP, MAC=" MACSTR, MAC2STR(event->mac));
    }
}

/* ── HTTP 服务器 (AP 配网模式) ── */

static esp_err_t http_scan_handler(httpd_req_t *req) {
    wifi_scan_config_t scan_cfg = {
        .ssid = NULL,
        .bssid = NULL,
        .channel = 0,
        .show_hidden = false,
        .scan_type = WIFI_SCAN_TYPE_ACTIVE,
        .scan_time.active.min = 100,
        .scan_time.active.max = 300,
    };

    esp_wifi_scan_start(&scan_cfg, true);
    uint16_t ap_count = 0;
    esp_wifi_scan_get_ap_num(&ap_count);

    wifi_ap_record_t *ap_list = malloc(sizeof(wifi_ap_record_t) * ap_count);
    if (!ap_list) {
        httpd_resp_send_500(req);
        return ESP_FAIL;
    }
    esp_wifi_scan_get_ap_records(&ap_count, ap_list);

    cJSON *root = cJSON_CreateArray();
    for (int i = 0; i < ap_count; i++) {
        cJSON *item = cJSON_CreateObject();
        cJSON_AddStringToObject(item, "ssid", (char *)ap_list[i].ssid);
        cJSON_AddNumberToObject(item, "rssi", ap_list[i].rssi);
        cJSON_AddNumberToObject(item, "auth", ap_list[i].authmode);
        cJSON_AddItemToArray(root, item);
    }

    free(ap_list);

    char *json_str = cJSON_PrintUnformatted(root);
    cJSON_Delete(root);

    httpd_resp_set_type(req, "application/json");
    httpd_resp_send(req, json_str, strlen(json_str));
    free(json_str);

    return ESP_OK;
}

static esp_err_t http_submit_handler(httpd_req_t *req) {
    char buf[512] = {0};
    int received = httpd_req_recv(req, buf, sizeof(buf) - 1);
    if (received <= 0) {
        httpd_resp_send_500(req);
        return ESP_FAIL;
    }
    buf[received] = '\0';

    cJSON *root = cJSON_Parse(buf);
    if (!root) {
        httpd_resp_send_500(req);
        return ESP_FAIL;
    }

    cJSON *ssid_json = cJSON_GetObjectItem(root, "ssid");
    cJSON *pwd_json = cJSON_GetObjectItem(root, "password");

    const char *resp;
    if (ssid_json && cJSON_IsString(ssid_json) && strlen(ssid_json->valuestring) > 0) {
        const char *ssid = ssid_json->valuestring;
        const char *pwd = (pwd_json && cJSON_IsString(pwd_json)) ? pwd_json->valuestring : "";

        esp_err_t err = wifi_save_credentials(ssid, pwd);
        if (err == ESP_OK) {
            ESP_LOGI(TAG, "WiFi credentials saved: SSID=\"%s\"", ssid);
            resp = "{\"status\":\"ok\"}";
        } else {
            resp = "{\"status\":\"error\",\"message\":\"NVS save failed\"}";
        }
    } else {
        resp = "{\"status\":\"error\",\"message\":\"invalid ssid\"}";
    }

    cJSON_Delete(root);

    httpd_resp_set_type(req, "application/json");
    httpd_resp_send(req, resp, strlen(resp));

    /* 延迟 1 秒后重启，进入 STA 模式连接 */
    if (strstr(resp, "\"ok\"") != NULL) {
        vTaskDelay(pdMS_TO_TICKS(1000));
        esp_restart();
    }

    return ESP_OK;
}

static esp_err_t http_root_handler(httpd_req_t *req) {
    httpd_resp_set_type(req, "text/html; charset=utf-8");
    httpd_resp_send(req, WIFI_CONFIG_HTML, strlen(WIFI_CONFIG_HTML));
    return ESP_OK;
}

/* GET /bindcode - 返回设备绑定码 */
static esp_err_t http_bindcode_handler(httpd_req_t *req) {
    const char *code = wifi_get_bind_code();
    char json[32];
    snprintf(json, sizeof(json), "{\"code\":\"%s\"}", code);
    httpd_resp_set_type(req, "application/json");
    httpd_resp_send(req, json, strlen(json));
    return ESP_OK;
}

static void start_http_server(void) {
    httpd_config_t config = HTTPD_DEFAULT_CONFIG();
    config.max_open_sockets = 4;  /* LWIP_MAX_SOCKETS=8, HTTP server 自身用 3 个 */
    config.max_uri_handlers = 8;
    config.lru_purge_enable = true;

    httpd_handle_t server = NULL;
    if (httpd_start(&server, &config) != ESP_OK) {
        ESP_LOGE(TAG, "failed to start HTTP server");
        return;
    }

    httpd_uri_t root_uri = {
        .uri       = "/",
        .method    = HTTP_GET,
        .handler   = http_root_handler,
        .user_ctx  = NULL,
    };
    httpd_register_uri_handler(server, &root_uri);

    httpd_uri_t scan_uri = {
        .uri       = "/scan",
        .method    = HTTP_GET,
        .handler   = http_scan_handler,
        .user_ctx  = NULL,
    };
    httpd_register_uri_handler(server, &scan_uri);

    httpd_uri_t submit_uri = {
        .uri       = "/submit",
        .method    = HTTP_POST,
        .handler   = http_submit_handler,
        .user_ctx  = NULL,
    };
    httpd_register_uri_handler(server, &submit_uri);

    httpd_uri_t bindcode_uri = {
        .uri       = "/bindcode",
        .method    = HTTP_GET,
        .handler   = http_bindcode_handler,
        .user_ctx  = NULL,
    };
    httpd_register_uri_handler(server, &bindcode_uri);

    ESP_LOGI(TAG, "HTTP server started on AP");
}

/* ── 纯 AP 配网模式（仅创建 AP netif + AP 模式 WiFi）── */

static void wifi_init_ap(void) {
    ESP_LOGI(TAG, "starting pure AP config mode...");

    wifi_event_group = xEventGroupCreate();

    ESP_ERROR_CHECK(esp_netif_init());
    ESP_ERROR_CHECK(esp_event_loop_create_default());
    esp_netif_t *ap_netif = esp_netif_create_default_wifi_ap();

    /* 显式配置 AP 的 IP 并启动 DHCP 服务 */
    esp_netif_ip_info_t ip_info;
    IP4_ADDR(&ip_info.ip, 192, 168, 4, 1);
    IP4_ADDR(&ip_info.gw, 192, 168, 4, 1);
    IP4_ADDR(&ip_info.netmask, 255, 255, 255, 0);
    esp_netif_dhcps_stop(ap_netif);
    ESP_ERROR_CHECK(esp_netif_set_ip_info(ap_netif, &ip_info));
    ESP_ERROR_CHECK(esp_netif_dhcps_start(ap_netif));
    ESP_LOGI(TAG, "AP IP configured: 192.168.4.1, DHCP server started");

    wifi_init_config_t cfg = WIFI_INIT_CONFIG_DEFAULT();
    ESP_ERROR_CHECK(esp_wifi_init(&cfg));

    ESP_ERROR_CHECK(esp_event_handler_instance_register(
        WIFI_EVENT, ESP_EVENT_ANY_ID, &ap_event_handler, NULL, NULL));

    wifi_config_t ap_config = {
        .ap = {
            .ssid = WIFI_AP_SSID,
            .ssid_len = strlen(WIFI_AP_SSID),
            .password = "",
            .max_connection = WIFI_AP_MAX_CONN,
            .authmode = WIFI_AUTH_OPEN,
        },
    };

    ESP_ERROR_CHECK(esp_wifi_set_mode(WIFI_MODE_AP));
    ESP_ERROR_CHECK(esp_wifi_set_config(WIFI_IF_AP, &ap_config));
    ESP_ERROR_CHECK(esp_wifi_start());

    ESP_LOGI(TAG, "AP started: SSID=\"%s\", IP=192.168.4.1", WIFI_AP_SSID);

    start_http_server();

    /* 设 FAIL_BIT 通知上层进入配网模式 */
    xEventGroupSetBits(wifi_event_group, WIFI_FAIL_BIT);
}

/* ── 纯 Station 模式连接 ── */

static void wifi_init_sta(const char *ssid, const char *password) {
    wifi_event_group = xEventGroupCreate();

    ESP_ERROR_CHECK(esp_netif_init());
    ESP_ERROR_CHECK(esp_event_loop_create_default());
    esp_netif_create_default_wifi_sta();

    wifi_init_config_t cfg = WIFI_INIT_CONFIG_DEFAULT();
    ESP_ERROR_CHECK(esp_wifi_init(&cfg));

    ESP_ERROR_CHECK(esp_event_handler_instance_register(
        WIFI_EVENT, ESP_EVENT_ANY_ID, &sta_event_handler, NULL, NULL));
    ESP_ERROR_CHECK(esp_event_handler_instance_register(
        IP_EVENT, IP_EVENT_STA_GOT_IP, &sta_event_handler, NULL, NULL));

    wifi_config_t wifi_config = {0};
    strncpy((char *)wifi_config.sta.ssid, ssid, sizeof(wifi_config.sta.ssid) - 1);
    strncpy((char *)wifi_config.sta.password, password, sizeof(wifi_config.sta.password) - 1);
    wifi_config.sta.threshold.authmode = WIFI_AUTH_WPA2_PSK;

    ESP_LOGI(TAG, "connecting to SSID=\"%s\"", ssid);

    ESP_ERROR_CHECK(esp_wifi_set_mode(WIFI_MODE_STA));
    ESP_ERROR_CHECK(esp_wifi_set_config(WIFI_IF_STA, &wifi_config));
    ESP_ERROR_CHECK(esp_wifi_start());
}

/* ── WiFi 初始化入口 ── */

void wifi_init(void) {
    /* 检查是否需要直接进入 AP 配网模式 */
    if (nvs_get_ap_mode_flag()) {
        ESP_LOGI(TAG, "AP mode flag set, entering config mode directly");
        wifi_init_ap();
        return;
    }

    /* 尝试从 NVS 加载凭据 */
    char ssid[33] = {0};
    char password[65] = {0};
    bool has_nvs = wifi_load_credentials(ssid, sizeof(ssid), password, sizeof(password));

    if (has_nvs && strlen(ssid) > 0) {
        wifi_init_sta(ssid, password);

        EventBits_t bits = xEventGroupWaitBits(wifi_event_group,
                                               WIFI_CONNECTED_BIT | WIFI_FAIL_BIT,
                                               pdFALSE, pdFALSE,
                                               pdMS_TO_TICKS(STATION_CONNECT_TIMEOUT_S * 1000));

        if (bits & WIFI_CONNECTED_BIT) {
            ESP_LOGI(TAG, "connected with NVS credentials");
            return;
        }
        ESP_LOGW(TAG, "NVS credentials failed");
    }

    /* 无凭据或连接失败 → 设置 AP 模式标记并重启 */
    ESP_LOGW(TAG, "unable to connect, restarting into AP config mode...");
    nvs_set_ap_mode_flag();
    vTaskDelay(pdMS_TO_TICKS(500));
    esp_restart();
}
