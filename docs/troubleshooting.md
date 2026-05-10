# Troubleshooting

## Display Issues

### Terminal text appears on screen instead of the image or verse

CircuitPython uses the display as a serial console by default if no `root_group` is assigned early enough. Fix: ensure `display.root_group = displayio.Group()` is set immediately after the display is initialised, before any `print()` calls execute.

### Display is completely blank (backlit but no content)

- Confirm BLK is connected to IO3 (or 3.3V for always-on). If BLK is floating or disconnected, the backlight will not turn on.
- Check that `backlight.duty_cycle` is being set above 0 in your code (or that `fade_in()` is being called).
- Verify CS is on IO12. If the silkscreen labels on your board are swapped (known v1.0 issue), try moving the CS wire to the adjacent pin.

### Display shows garbage / random pixels

- Usually a wiring issue on DC (IO5) or CS (IO12). Double-check both.
- Can also indicate a BMP format problem — see the image section below.

### Image is cut off or offset incorrectly after rotation

- At 90° or 270° rotation, the source image should be **240×320** (portrait), which rotates to fill the 320×240 landscape display.
- At 0° or 180°, the source image should be **320×240**.
- The framebuffer loader will raise a `ValueError` if the rotated output dimensions do not match the display exactly.

---

## SD Card Issues

### SD card fails to mount

- Confirm SD CS is on IO6.
- Make sure SD VCC is connected to 3.3V, not 5V.
- Try reducing the SD baudrate from `4000000` to `1000000` in `mount_sd()`. Some cards are slower to initialise.
- Ensure the SD card is formatted as **FAT32**.

### SD card mounts but no images found

- Confirm images are saved as `.bmp` (lowercase or uppercase — both are matched).
- The image must be a **24-bit uncompressed BMP**. JPEGs and PNGs are not supported by the framebuffer loader.
- Run-length encoded (RLE) BMP compression is not supported. When exporting from GIMP, ensure "Run-Length Encoding" is unchecked.

### Image displays as a single horizontal line

This is the shared SPI bus conflict. It happens when `displayio.OnDiskBitmap` is used with an SD card and display on the same bus. The fix is to load the full image into a RAM framebuffer first, unmount the SD card, then push the framebuffer to the display. See `slideshow.py` for the correct implementation.

---

## WiFi Issues

### WiFi fails to connect

- Check `WIFI_SSID` and `WIFI_PASSWORD` in `settings.toml` for typos (the values are case-sensitive).
- The ESP32-S2 supports **2.4GHz only** — it will not connect to a 5GHz network.
- Open the serial console to see the exact error message.

### WiFi connects but API calls fail

- HTTPS requires a valid system time. If the ESP32's clock is not synced, SSL certificate validation may fail. CircuitPython normally handles NTP time sync automatically on WiFi connect.
- Check that both API keys in `settings.toml` are correct and not truncated.

### Device stops fetching after several hours

The connection manager handles reconnection automatically. If the device stops responding entirely, the watchdog timer or a memory exhaustion crash may be the cause. Check the serial console for a traceback, then press RST to reboot.

---

## API Issues

### YouVersion returns 401 Unauthorized

Your `YOUVERSION_APP_KEY` is incorrect or missing from `settings.toml`. Copy it carefully from the YouVersion developer dashboard — it is case-sensitive.

### Scripture API returns 401 Unauthorized

Your `SCRIPTURE_API_KEY` is incorrect. Verify it in your api.bible dashboard.

### Verse text appears blank on screen

Add a temporary `print(data2)` line after the Scripture API response to see the raw JSON in the serial console. The field name for verse content may differ — look for `content`, `text`, or `value` in the response and update the code accordingly.

---

## Memory Issues

### MemoryError crash during image load

The RGB565 framebuffer for a 320×240 image is 150KB. The S2 Mini has 2MB PSRAM available to CircuitPython, which is sufficient. If you still hit a `MemoryError`, call `gc.collect()` before loading the image and check that no other large buffers are allocated.

### ImportError: invalid .mpy file

The `.mpy` library files were compiled for a different CircuitPython version. Download the library bundle that matches your exact CircuitPython version from https://circuitpython.org/libraries.

---

## General Tips

- **Always open the serial console first** before debugging. Almost every issue prints a clear error message.
- **Press RST** to cleanly reboot the device without unplugging it.
- **Check free memory** by adding `import gc; print(gc.mem_free())` temporarily — this often reveals the cause of mystery crashes.
