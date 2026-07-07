#pragma once
#include "esp_err.h"
#include "driver/i2c_master.h"
#include <stdint.h>

#define DEVICE_AUDIO_SAMPLE_RATE  16000
#define DEVICE_AUDIO_BIT_WIDTH    16
#define DEVICE_AUDIO_CHUNK_MS     40
#define DEVICE_AUDIO_CHUNK_BYTES  (DEVICE_AUDIO_SAMPLE_RATE * (DEVICE_AUDIO_BIT_WIDTH / 8) * DEVICE_AUDIO_CHUNK_MS / 1000)

/* Xmini C3 pin definitions */
#define I2S_BCK      8
#define I2S_WS       6
#define I2S_DIN      7
#define I2S_DOUT     5
#define I2S_MCLK    10

#define I2C_SDA      3
#define I2C_SCL      4

#define PA_EN_PIN   11   /* VDD_SPI pin, reconfigured as GPIO */

void audio_init(int bck_io, int ws_io, int din_io, int dout_io);
void audio_deinit(void);
void i2s_record_start(void);
void i2s_record_stop(void);
int  i2s_record_read(int16_t *buf, int samples);
void i2s_playback_start(void);
void i2s_playback_stop(void);
int  i2s_playback_write(const uint8_t *data, int len);

/** Get the I2C master bus handle (for sharing with display) */
i2c_master_bus_handle_t i2s_audio_get_i2c_bus(void);
