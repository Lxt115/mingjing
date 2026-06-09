#include "i2s_audio.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "driver/i2s_std.h"
#include "driver/i2c_master.h"
#include "driver/gpio.h"
#include "esp_log.h"
#include "esp_codec_dev.h"
#include "esp_codec_dev_defaults.h"
#include "es8311_codec.h"
#include <string.h>

static const char *TAG = "audio";

static i2s_chan_handle_t s_tx_chan = NULL;
static i2s_chan_handle_t s_rx_chan = NULL;

static i2c_master_bus_handle_t s_i2c_bus  = NULL;
static const audio_codec_if_t *s_codec_if = NULL;
static esp_codec_dev_handle_t  s_codec_dev = NULL;

static bool s_playing    = false;
static bool s_rx_enabled = false;
static bool s_tx_enabled = false;

void audio_init(int bck_io, int ws_io, int din_io, int dout_io) {
    /* ── 1. I2C master bus ── */
    i2c_master_bus_config_t i2c_cfg = {
        .clk_source = I2C_CLK_SRC_DEFAULT,
        .i2c_port   = I2C_NUM_0,
        .scl_io_num = I2C_SCL,
        .sda_io_num = I2C_SDA,
        .glitch_ignore_cnt = 7,
        .flags.enable_internal_pullup = true,
    };
    ESP_ERROR_CHECK(i2c_new_master_bus(&i2c_cfg, &s_i2c_bus));

    /* ── 2. PA pin (NS4150) ── */
    gpio_reset_pin(PA_EN_PIN);
    gpio_set_direction(PA_EN_PIN, GPIO_MODE_OUTPUT);
    gpio_set_level(PA_EN_PIN, 0);

    /* ── 3. I2S duplex channels ── */
    i2s_chan_config_t chan_cfg = I2S_CHANNEL_DEFAULT_CONFIG(I2S_NUM_0, I2S_ROLE_MASTER);
    i2s_std_config_t std_cfg = {
        .clk_cfg  = I2S_STD_CLK_DEFAULT_CONFIG(DEVICE_AUDIO_SAMPLE_RATE),
        .slot_cfg = I2S_STD_PHILIPS_SLOT_DEFAULT_CONFIG(I2S_DATA_BIT_WIDTH_16BIT, I2S_SLOT_MODE_STEREO),
        .gpio_cfg = {
            .mclk = I2S_MCLK,
            .bclk = bck_io, .ws = ws_io,
            .dout = dout_io, .din = din_io,
        },
    };
    ESP_ERROR_CHECK(i2s_new_channel(&chan_cfg, &s_tx_chan, &s_rx_chan));
    ESP_ERROR_CHECK(i2s_channel_init_std_mode(s_tx_chan, &std_cfg));
    ESP_ERROR_CHECK(i2s_channel_init_std_mode(s_rx_chan, &std_cfg));

    /* ── 4. I2S data interface — only RX, TX left free for manual write ── */
    audio_codec_i2s_cfg_t i2s_cfg = {
        .port = I2S_NUM_0, .rx_handle = s_rx_chan, .tx_handle = NULL,
    };
    const audio_codec_data_if_t *data_if = audio_codec_new_i2s_data(&i2s_cfg);

    audio_codec_i2c_cfg_t ctrl_cfg = {
        .port = I2C_NUM_0, .addr = ES8311_CODEC_DEFAULT_ADDR, .bus_handle = s_i2c_bus,
    };
    const audio_codec_ctrl_if_t *ctrl_if = audio_codec_new_i2c_ctrl(&ctrl_cfg);
    const audio_codec_gpio_if_t *gpio_if = audio_codec_new_gpio();

    /* ── 5. ES8311 codec ── */
    es8311_codec_cfg_t es8311_cfg = {
        .ctrl_if = ctrl_if, .gpio_if = gpio_if,
        .codec_mode = ESP_CODEC_DEV_WORK_MODE_BOTH,
        .pa_pin     = PA_EN_PIN,
        .pa_reverted = false,
        .master_mode = false,
        .use_mclk   = true,
        .digital_mic = false,
        .invert_mclk = false,
        .invert_sclk = false,
        .hw_gain    = { .pa_voltage = 5.0, .codec_dac_voltage = 3.3 },
    };
    s_codec_if = es8311_codec_new(&es8311_cfg);
    if (!s_codec_if) { ESP_LOGE(TAG, "ES8311 init failed!"); return; }

    /* ── 6. esp_codec_dev: activates ADC/DAC (required for recording) ── */
    esp_codec_dev_cfg_t dev_cfg = {
        .dev_type = ESP_CODEC_DEV_TYPE_IN_OUT,
        .codec_if = s_codec_if, .data_if = data_if,
    };
    s_codec_dev = esp_codec_dev_new(&dev_cfg);
    if (!s_codec_dev) { ESP_LOGE(TAG, "Failed to create codec device"); return; }

    esp_codec_dev_sample_info_t fs = {
        .bits_per_sample = 16,
        .channel         = 2,
        .channel_mask    = 0,
        .sample_rate     = DEVICE_AUDIO_SAMPLE_RATE,
        .mclk_multiple   = 0,
    };
    ESP_ERROR_CHECK(esp_codec_dev_open(s_codec_dev, &fs));
    esp_codec_dev_set_in_gain(s_codec_dev, 30.0f);

    /* Channels are now enabled by data_if via esp_codec_dev_open */
    s_tx_enabled = true;
    s_rx_enabled = true;

    ESP_LOGI(TAG, "ES8311+I2S ready, SR=%d", DEVICE_AUDIO_SAMPLE_RATE);
}

void audio_deinit(void) {
    i2s_playback_stop();
    i2s_record_stop();
    if (s_codec_dev) { esp_codec_dev_close(s_codec_dev); s_codec_dev = NULL; }
    if (s_rx_chan)   { i2s_del_channel(s_rx_chan); s_rx_chan = NULL; }
    if (s_tx_chan)   { i2s_del_channel(s_tx_chan); s_tx_chan = NULL; }
    if (s_i2c_bus)   { i2c_del_master_bus(s_i2c_bus); s_i2c_bus = NULL; }
}

/* ── Record: uses raw i2s_channel_read (proven to work with this setup) ── */

void i2s_record_start(void) {
    if (s_codec_if && s_codec_if->mute) s_codec_if->mute(s_codec_if, true);
}

void i2s_record_stop(void) {
    if (s_codec_if && s_codec_if->mute) s_codec_if->mute(s_codec_if, false);
}

int i2s_record_read(int16_t *buf, int samples) {
    if (!s_rx_chan) return 0;
    size_t bytes_read = 0;
    esp_err_t ret = i2s_channel_read(s_rx_chan, buf, samples * sizeof(int16_t),
                                     &bytes_read, pdMS_TO_TICKS(100));
    if (ret == ESP_OK) {
        return (int)(bytes_read / sizeof(int16_t));
    }
    return 0;
}

/* ── Playback: uses esp_codec_dev_write (goes through data_if to avoid conflict) ── */

void i2s_playback_start(void) {
    if (s_playing) return;
    /* Enable TX channel first, then unmute DAC, then PA */
    if (s_tx_chan && !s_tx_enabled) {
        i2s_channel_enable(s_tx_chan);
        s_tx_enabled = true;
    }
    if (s_codec_if && s_codec_if->mute) s_codec_if->mute(s_codec_if, false);
    gpio_set_level(PA_EN_PIN, 1);
    s_playing = true;
    ESP_LOGI(TAG, "playback on");
}

void i2s_playback_stop(void) {
    if (!s_playing) return;
    gpio_set_level(PA_EN_PIN, 0);
    if (!s_rx_enabled && s_tx_chan && s_tx_enabled) {
        i2s_channel_disable(s_tx_chan);
        s_tx_enabled = false;
    }
    s_playing = false;
    ESP_LOGI(TAG, "playback off");
}

int i2s_playback_write(const uint8_t *data, int len) {
    if (!s_tx_chan || !s_playing) return 0;
    size_t bytes_written = 0;
    i2s_channel_write(s_tx_chan, data, len, &bytes_written, pdMS_TO_TICKS(200));
    return (int)bytes_written;
}
