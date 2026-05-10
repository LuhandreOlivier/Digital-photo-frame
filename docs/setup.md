# Setup Guide

## Prerequisites

- Windows PC (this guide uses Windows; adjust COM port steps for macOS/Linux)
- USB-C cable
- Python 3 installed (for esptool)
- VSCode with the [CircuitPython extension](https://marketplace.visualstudio.com/items?itemName=joedevivo.vscode-circuitpython) recommended

---

## Flashing CircuitPython

The S2 Mini does not ship with TinyUF2, so the `.uf2` drag-and-drop method does not work on first flash. CircuitPython must be flashed via `esptool` using the `.bin` file.

### 1. Install esptool

```bash
pip install esptool
```

### 2. Download CircuitPython

Go to [https://circuitpython.org/board/lolin_s2_mini/](https://circuitpython.org/board/lolin_s2_mini/) and download the latest stable `.bin` file.

### 3. Put the board into bootloader mode

- Hold the **BOOT (0)** button
- Press and release **RST**
- Release **BOOT**

A new COM port will appear in Device Manager. Note the port number (e.g. `COM4`).

### 4. Erase the flash

```bash
esptool --chip esp32s2 --port COM4 --baud 460800 erase_flash
```

### 5. Flash CircuitPython

```bash
esptool --chip esp32s2 --port COM4 --baud 460800 write_flash -z 0x0 adafruit-circuitpython-lolin_s2_mini-en_US-10.x.x.bin
```

Replace the filename with the one you downloaded.

### 6. Verify

Press **RST**. The board will reboot and appear as a `CIRCUITPY` drive in Windows Explorer. You're done — future CircuitPython updates can use `.uf2` drag-and-drop.

---

## Libraries

Download the CircuitPython Library Bundle matching your firmware version from [https://circuitpython.org/libraries](https://circuitpython.org/libraries). Unzip it, then copy the following into the `lib/` folder on your `CIRCUITPY` drive:

| File / Folder | Type |
|---|---|
| `adafruit_ili9341.mpy` | single file |
| `adafruit_display_text/` | folder |
| `adafruit_bitmap_font/` | folder |
| `adafruit_requests.mpy` | single file |
| `adafruit_connection_manager.mpy` | single file |

> `sdcardio` and `storage` are built into CircuitPython 10 on this board — no extra library needed.

---

## CIRCUITPY Drive Structure

After setup, your `CIRCUITPY` drive should look like this:

```
CIRCUITPY/
├── code.py
├── settings.toml
└── lib/
    ├── adafruit_ili9341.mpy
    ├── adafruit_requests.mpy
    ├── adafruit_connection_manager.mpy
    ├── adafruit_display_text/
    └── adafruit_bitmap_font/
```

---

## Settings

Create a `settings.toml` file in the root of `CIRCUITPY`:

```toml
WIFI_SSID = "YourWiFiName"
WIFI_PASSWORD = "YourWiFiPassword"
YOUVERSION_APP_KEY = "your-youversion-api-key"
SCRIPTURE_API_KEY = "your-scripture-api-bible-key"
```

This file is the standard CircuitPython credentials store. Keep it out of version control — it is already listed in `.gitignore` in this repo.

See [`docs/api.md`](api.md) for how to obtain the API keys.

---

## Serial Console (Debugging)

The serial console is essential for debugging. Every `print()` statement and error traceback appears here.

**In VSCode:**
1. Install the CircuitPython extension
2. Open the Command Palette (`Ctrl+Shift+P`) → `CircuitPython: Select Serial Port`
3. Choose your board's COM port
4. The serial console appears at the bottom of VSCode automatically

**In Thonny:**
1. Go to Tools → Options → Interpreter
2. Select `CircuitPython (generic)` and your COM port
3. The shell at the bottom shows serial output

Press `Ctrl+C` in the console to interrupt the running script. Press `Ctrl+D` to soft-reset and restart.

---

## Preparing Images for the SD Card

1. Format your SD card as **FAT32**
2. Convert your images to **24-bit uncompressed BMP**:
   - Open in **MS Paint** → File → Save As → BMP Picture (Paint always saves as 24-bit uncompressed — no settings needed)
   - Or use **GIMP**: File → Export As → `.bmp` → uncheck "Run-Length Encoding", select 24-bit
3. Resize to match your rotation setting:
   - `IMAGE_ROTATION = 90` or `270`: images must be **240×320** pixels
   - `IMAGE_ROTATION = 0` or `180`: images must be **320×240** pixels
4. Copy BMP files to the **root** of the SD card (not inside any folder)
5. Files display in sorted filename order — prefix with numbers to control sequence (e.g. `01_sunrise.bmp`, `02_mountains.bmp`)
