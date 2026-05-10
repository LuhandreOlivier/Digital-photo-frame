# Hardware Guide

## Components

| Component | Details |
|---|---|
| Microcontroller | LOLIN S2 Mini (ESP32-S2FN4R2) |
| CPU | Single-core Xtensa LX7 @ up to 240MHz |
| RAM | 320KB SRAM + 2MB PSRAM |
| Flash | 4MB |
| Connectivity | WiFi 802.11 b/g/n (2.4GHz). No Bluetooth. |
| Display | 2.4" Waveshare ILI9341 SPI TFT, 320×240 pixels |
| SD Card Module | Generic SPI SD card module, 3.3V native |
| Firmware | CircuitPython 10.x |

---

## Pin Map

| S2 Mini Pin | Connects To | Function |
|---|---|---|
| 3.3V | Display VCC → SD VCC | Power (daisy chained) |
| GND | Display GND → SD GND | Ground (daisy chained) |
| IO7 | Display CLK → SD CLK | SPI clock (shared) |
| IO11 | Display DIN → SD MOSI | SPI data out (shared) |
| IO9 | SD MISO only | SPI data in (display is write-only) |
| IO12 | Display CS | Display chip select |
| IO6 | SD Card CS | SD chip select |
| IO5 | Display DC | Data/Command select |
| IO1 | Display RST | Display reset |
| IO3 | Display BLK | Backlight (PWM controlled) |

---

## Wiring Notes

### Shared SPI Bus
The display and SD card share the same SPI bus (CLK, MOSI). This works because each device has its own dedicated CS (chip select) line — only the device whose CS is pulled low is active at any time.

The software handles this by:
1. Mounting the SD card and reading the full image into RAM
2. Unmounting and deinitialising the SD card (releasing the SPI bus)
3. Sending the framebuffer to the display

This avoids the conflict that would occur if both devices tried to use the bus simultaneously.

### Display DIN vs MOSI
The Waveshare ILI9341 labels its data pin **DIN**, not MOSI. It is the same signal — connect it to IO11 (MOSI). The display is write-only and has no MISO pin.

### Backlight (BLK)
The backlight is connected to IO3 and controlled via PWM. This allows the firmware to:
- Start with the backlight off while content loads
- Fade in smoothly once the image or verse is ready
- Dim the display in future (planned feature)

If you do not need brightness control, connect BLK directly to 3.3V for always-on operation and remove the PWM backlight code.

### Power
Both the display and SD card module run on **3.3V**. The S2 Mini's 3.3V pin supplies both. Do not connect either device to 5V.

---

## Known Issues

### IO12 / IO13 Silkscreen Swap (S2 Mini v1.0)
Some early revision S2 Mini boards have the IO12 and IO13 silkscreen labels printed in the wrong positions. If your display shows nothing or garbage, swap the CS wire between the IO12 and IO13 physical pins and retest.

### SD Card Initialisation Order
The SD card must be initialised **after** the SPI bus is set up, and the display must be initialised first. Initialising in the wrong order can prevent the SD card from being detected.

### OnDiskBitmap vs Framebuffer
Early versions of this project used `displayio.OnDiskBitmap` to stream images directly from the SD card. This fails when the SD card and display share an SPI bus, because the display tries to read pixel data over the bus at the same time the SD card is being accessed. The solution is to load the full image into a RAM framebuffer first, then send it to the display after the SD card is unmounted.
