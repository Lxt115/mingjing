#include "i2s_audio.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "driver/i2s_std.h"
#include "driver/i2c_master.h"
#include "driver/gpio.h"
#include "esp_log.h"
#include "esp_efuse_table.h"
#include "esp_codec_dev.h"
#include "esp_codec_dev_defaults.h"
#include "es8311_codec.h"

static const char *TAG = "audio";

static i2s_chan_handle_t s_tx_chan = NULL;
static i2s_chan_handle_t s_rx_chan = NULL;

static i2c_master_bus_handle_t s_i2c_bus  = NULL;
static const audio_codec_if_t *s_codec_if = NULL;
static esp_codec_dev_handle_t  s_codec_dev = NULL;

static bool s_playing    = false;

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

    /* ── 2. PA pin (NS4150) — VDD_SPI reconfigured as GPIO ── */
    esp_efuse_write_field_bit(ESP_EFUSE_VDD_SPI_AS_GPIO);
    gpio_reset_pin(PA_EN_PIN);
    gpio_set_direction(PA_EN_PIN, GPIO_MODE_OUTPUT);
    gpio_set_level(PA_EN_PIN, 0);

    /* ── 3. I2S duplex channels  ── */
    i2s_chan_config_t chan_cfg = {
        .id = I2S_NUM_0,
        .role = I2S_ROLE_MASTER,
        .dma_desc_num = 6,
        .dma_frame_num = 240,
        .auto_clear_after_cb = true,
        .auto_clear_before_cb = false,
        .intr_priority = 0,
    };
    i2s_std_config_t std_cfg = {
        .clk_cfg = {
            .sample_rate_hz = DEVICE_AUDIO_SAMPLE_RATE,
            .clk_src = I2S_CLK_SRC_DEFAULT,
            .mclk_multiple = I2S_MCLK_MULTIPLE_256,
        },
        .slot_cfg = {
            .data_bit_width = I2S_DATA_BIT_WIDTH_16BIT,
            .slot_bit_width = I2S_SLOT_BIT_WIDTH_AUTO,
            .slot_mode = I2S_SLOT_MODE_STEREO,
            .slot_mask = I2S_STD_SLOT_BOTH,
            .ws_width = I2S_DATA_BIT_WIDTH_16BIT,
            .ws_pol = false,
            .bit_shift = true,
            .left_align = true,
            .big_endian = false,
            .bit_order_lsb = false,
        },
        .gpio_cfg = {
            .mclk = I2S_MCLK,
            .bclk = bck_io, .ws = ws_io,
            .dout = dout_io, .din = din_io,
            .invert_flags = {
                .mclk_inv = false,
                .bclk_inv = false,
                .ws_inv = false,
            },
        },
    };
    ESP_ERROR_CHECK(i2s_new_channel(&chan_cfg, &s_tx_chan, &s_rx_chan));
    ESP_ERROR_CHECK(i2s_channel_init_std_mode(s_tx_chan, &std_cfg));
    ESP_ERROR_CHECK(i2s_channel_init_std_mode(s_rx_chan, &std_cfg));
    /* Enable both now — ES8311 needs I2S clock for ADC/DAC */
    ESP_ERROR_CHECK(i2s_channel_enable(s_tx_chan));
    ESP_ERROR_CHECK(i2s_channel_enable(s_rx_chan));

    /* ── 4. Interfaces ── */
    audio_codec_i2s_cfg_t i2s_cfg = {
        .port = I2S_NUM_0, .rx_handle = s_rx_chan, .tx_handle = s_tx_chan,
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
        .pa_pin     = GPIO_NUM_NC,    /* don't let codec touch PA — we control it */
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

    /* ── 6. esp_codec_dev (IN_OUT) — activates ADC + DAC paths ── */
    esp_codec_dev_cfg_t dev_cfg = {
        .dev_type = ESP_CODEC_DEV_TYPE_IN_OUT,
        .codec_if = s_codec_if, .data_if = data_if,
    };
    s_codec_dev = esp_codec_dev_new(&dev_cfg);
    if (!s_codec_dev) { ESP_LOGE(TAG, "Failed to create codec device"); return; }

    esp_codec_dev_sample_info_t fs = {
        .bits_per_sample = 16,
        .channel         = 1,
        .channel_mask    = 0,
        .sample_rate     = DEVICE_AUDIO_SAMPLE_RATE,
        .mclk_multiple   = 0,
    };
    ESP_ERROR_CHECK(esp_codec_dev_open(s_codec_dev, &fs));
    esp_codec_dev_set_in_gain(s_codec_dev, 30.0f);
    esp_codec_dev_set_out_vol(s_codec_dev, 100);  /* 扬声器输出音量，范围 0-100 */

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

/* ── Record: esp_codec_dev_read ── */

void i2s_record_start(void) {
    if (s_codec_if && s_codec_if->mute) s_codec_if->mute(s_codec_if, true);
}

void i2s_record_stop(void) {
    if (s_codec_if && s_codec_if->mute) s_codec_if->mute(s_codec_if, false);
}

int i2s_record_read(int16_t *buf, int samples) {
    if (!s_codec_dev) return 0;
    esp_err_t ret = esp_codec_dev_read(s_codec_dev, buf, samples * sizeof(int16_t));
    if (ret == ESP_CODEC_DEV_OK) {
        return samples;
    }
    return 0;
}

/* ── Playback: esp_codec_dev_write (via data_if to I2S TX → ES8311 DAC → NS4150 → speaker) ── */

void i2s_playback_start(void) {
    if (s_playing) return;
    if (s_codec_if && s_codec_if->mute) s_codec_if->mute(s_codec_if, false);
    gpio_set_level(PA_EN_PIN, 1);
    s_playing = true;
    ESP_LOGI(TAG, "playback on");
}

void i2s_playback_stop(void) {
    if (!s_playing) return;
    gpio_set_level(PA_EN_PIN, 0);
    if (s_codec_if && s_codec_if->mute) s_codec_if->mute(s_codec_if, true);
    s_playing = false;
    ESP_LOGI(TAG, "playback off");
}

int i2s_playback_write(const uint8_t *data, int len) {
    if (!s_codec_dev || !s_playing) return 0;
    /* esp_codec_dev_write → data_if → I2S TX → ES8311 DACDAT → DAC → analog out → NS4150 → speaker */
    return esp_codec_dev_write(s_codec_dev, (void *)data, len);
}

i2c_master_bus_handle_t i2s_audio_get_i2c_bus(void) {
    return s_i2c_bus;
}
