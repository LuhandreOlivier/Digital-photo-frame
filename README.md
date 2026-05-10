# Bible Verse Display

> ESP32‑S2 + CircuitPython powered smart Bible verse and image display with WiFi syncing, slideshow mode, PWM backlight fading, and dual API integration.

---

## Features

- 📖 Fetches the YouVersion Verse of the Day automatically
- 🌐 Uses YouVersion + Scripture API architecture
- 🖼️ SD card slideshow mode for BMP images
- 🔁 Physical button toggles between IMAGE and BIBLE modes
- 💡 PWM backlight fade in / fade out transitions
- 📡 WiFi reconnect and retry handling
- 🧠 Optimised framebuffer rendering for shared SPI buses
- 🛠️ Built with CircuitPython 10.x on the ESP32‑S2

---

## Hardware

| Component | Part |
|---|---|
| MCU | LOLIN S2 Mini (ESP32‑S2) |
| Display | 2.4\" Waveshare ILI9341 TFT |
| Storage | SPI SD card module |
| Firmware | CircuitPython 10.x |

See [`docs/hardware.md`](docs/hardware.md) for full wiring and pin mappings.

---

## Project Structure

```text
bible-display/
├── src/
│   ├── code.py
│   └── settings.toml.example
├── docs/
│   ├── api.md
│   ├── firmware.md
│   ├── hardware.md
│   ├── libraries.md
│   ├── setup.md
│   └── troubleshooting.md
├── website/
│   └── index.html
└── README.md
```

---

## Quick Start

1. Flash CircuitPython onto the LOLIN S2 Mini
2. Wire the TFT display and SD card
3. Install the required CircuitPython libraries
4. Create `settings.toml`
5. Copy `src/code.py` onto the `CIRCUITPY` drive
6. Reboot the device

---

## New Firmware Capabilities

The updated firmware now includes:

- Runtime mode switching using a hardware button
- Improved framebuffer text rendering
- Better WiFi recovery handling
- NTP time syncing
- Verse overlay rendering on slideshow backgrounds
- Shared SPI conflict avoidance using RAM framebuffers

---

## APIs Used

### YouVersion API
Returns the Verse of the Day reference.

### Scripture API
Resolves the reference into readable verse text.

Detailed setup instructions are available in [`docs/api.md`](docs/api.md).

---

## License

MIT License
