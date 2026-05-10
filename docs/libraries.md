# Libraries

## Overview

CircuitPython separates its core (built into the firmware) from optional libraries (copied into the `lib/` folder on the CIRCUITPY drive). This project uses both.

---

## Built-in (no installation needed)

These modules are built into CircuitPython 10 on the S2 Mini and do not require any files in `lib/`:

| Module | Purpose |
|---|---|
| `sdcardio` | SPI SD card driver |
| `storage` | Filesystem mounting |
| `wifi` | WiFi radio control |
| `socketpool` | TCP/IP socket management |
| `ssl` | TLS/HTTPS support |
| `busio` | SPI, I2C, UART hardware buses |
| `board` | Pin name definitions for your board |
| `displayio` | Display framebuffer and rendering |
| `pwmio` | PWM output (used for backlight) |
| `supervisor` | Runtime control (reload, etc.) |
| `gc` | Garbage collector / memory management |

---

## External Libraries (copy to `lib/`)

### Download the Bundle

Go to **https://circuitpython.org/libraries** and download the bundle that matches your CircuitPython version (e.g. the `9.x` bundle for CircuitPython 9, `10.x` for CircuitPython 10). Unzip the bundle on your PC.

### Files to copy

From the unzipped bundle, copy the following into `CIRCUITPY/lib/`:

| File / Folder | Type | Purpose |
|---|---|---|
| `adafruit_ili9341.mpy` | Single file | ILI9341 display driver |
| `adafruit_requests.mpy` | Single file | HTTP/HTTPS requests |
| `adafruit_connection_manager.mpy` | Single file | WiFi socket/SSL pool manager |
| `adafruit_display_text/` | Folder | Text label rendering |
| `adafruit_bitmap_font/` | Folder | Custom bitmap fonts (optional) |

### Version matching is critical

The `.mpy` files in the bundle are compiled for a specific CircuitPython version. Copying a `9.x` bundle library into a `10.x` CircuitPython installation (or vice versa) will cause an `Invalid .mpy file` import error. Always use the bundle that matches your installed firmware version exactly.

---

## Verifying Installation

After copying the libraries, your `lib/` folder should look like this:

```
CIRCUITPY/lib/
├── adafruit_bitmap_font/
│   ├── __init__.mpy
│   └── bitmap_font.mpy
├── adafruit_display_text/
│   ├── __init__.mpy
│   ├── label.mpy
│   └── wrap_text_to_lines.mpy
├── adafruit_connection_manager.mpy
├── adafruit_ili9341.mpy
└── adafruit_requests.mpy
```

If an import fails on boot, check the serial console — CircuitPython will print the exact missing module name.
