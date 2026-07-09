#pragma once
#include "driver/i2c_master.h"

#define DISPLAY_I2C_ADDR  0x3C
#define DISPLAY_WIDTH     128
#define DISPLAY_HEIGHT    64

/**
 * Initialize the SSD1306 OLED display on the shared I2C bus.
 * Call this after audio_init() so the I2C bus is ready.
 */
void display_init(i2c_master_bus_handle_t i2c_bus);

/**
 * Show status on line 0, separator on line 1, and message on lines 2-7.
 * Supports UTF-8 Chinese text via the included 16x16 font.
 * If text is too wide, it stays static (call display_tick for scroll).
 * Pass NULL for any parameter to keep previous content.
 */
void display_show(const char *status, const char *message);

/**
 * Advance horizontal scroll by one step for the message area.
 * Call this periodically (~50ms) when message text is wider than display.
 */
void display_tick(void);

/**
 * Clear the entire display buffer and flush.
 */
void display_clear(void);
