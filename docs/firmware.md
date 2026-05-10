# Firmware Setup

## Overview

The LOLIN S2 Mini does not ship with TinyUF2, so the usual drag-and-drop `.uf2` method does not work for the initial flash. CircuitPython must be flashed using **esptool** over USB serial using the `.bin` file. After the first flash, future CircuitPython updates can use the `.uf2` drag-and-drop method normally.

---

## Requirements

- Python installed on your PC (Python 3.8+)
- A USB-C cable (data capable, not charge-only)
- Windows Device Manager or equivalent to identify the COM port

---

## Step 1 — Install esptool

```bash
pip install esptool
```

---

## Step 2 — Download CircuitPython

Go to the official CircuitPython board page and download the latest stable `.bin` file:

**https://circuitpython.org/board/lolin_s2_mini/**

Make sure you download the `.bin` file, not the `.uf2`.

---

## Step 3 — Put the board into boot mode

1. Hold the **0** (BOOT) button on the S2 Mini
2. While holding BOOT, press and release the **RST** button
3. Release the BOOT button

The board will enter ROM bootloader mode. A new COM port should appear in Windows Device Manager (look under Ports).

---

## Step 4 — Erase the flash

Replace `COM4` with your actual COM port number.

```bash
esptool --chip esp32s2 --port COM4 --baud 460800 erase_flash
```

---

## Step 5 — Flash CircuitPython

Replace `COM4` with your port and update the filename to match the version you downloaded.

```bash
esptool --chip esp32s2 --port COM4 --baud 460800 write_flash -z 0x0 adafruit-circuitpython-lolin_s2_mini-en_US-10.x.x.bin
```

---

## Step 6 — Confirm the flash

After flashing completes, press the **RST** button. The board should reboot and appear as a USB drive called `CIRCUITPY` in Windows Explorer.

If it does not appear, try pressing RST again or reconnecting the USB cable.

---

## CIRCUITPY Drive Structure

Once mounted, your `CIRCUITPY` drive should be set up as follows:

```
CIRCUITPY/
├── code.py              ← main application
├── settings.toml        ← WiFi and API credentials
└── lib/
    ├── adafruit_ili9341.mpy
    ├── adafruit_requests.mpy
    ├── adafruit_connection_manager.mpy
    ├── adafruit_display_text/
    └── adafruit_bitmap_font/
```

---

## Serial Console

CircuitPython prints all output (print statements, errors, tracebacks) to the USB serial port. To see this output:

**VSCode (recommended):**
Install the CircuitPython extension by joedevivo. Open the command palette (`Ctrl+Shift+P`) and run **CircuitPython: Select Serial Port**. The serial console appears in the VSCode terminal panel.

**Thonny:**
Open Thonny, go to Tools → Options → Interpreter, select CircuitPython (generic), and choose your COM port. The shell panel at the bottom shows serial output.

**Any serial terminal:**
Connect to the board's COM port at **115200 baud**.

---

## Updating CircuitPython in Future

After the first esptool flash, the board supports `.uf2` updates:

1. Double-press the **RST** button quickly — the board enters UF2 bootloader mode and appears as `RPI-RP2`
2. Drag the new `.uf2` file onto the drive
3. The board reboots into the new firmware automatically
