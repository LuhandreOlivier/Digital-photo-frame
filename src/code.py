import os
import time
import gc
import re
import supervisor

import wifi
import socketpool
import rtc
import displayio
import terminalio
import busio
import board
import pwmio
import digitalio
import sdcardio
import storage
import adafruit_ntp
import adafruit_requests
import adafruit_connection_manager

from fourwire import FourWire
from adafruit_ili9341 import ILI9341
from adafruit_display_text import label


# ---------------- Configuration ----------------

MODE = "IMAGE"   # "IMAGE" or "BIBLE"

IMAGE_ROTATION = 90
IMAGE_INTERVAL_SECONDS = 10

VERSE_ROTATION = 90        # 0, 90, 180, or 270
VERSE_SHADE_PERCENT = 45   # 0 = no shade, 100 = black

TIMEZONE_OFFSET = 2

DISPLAY_WIDTH = 320
DISPLAY_HEIGHT = 240

BACKLIGHT_PIN = board.IO3

SPI_CLOCK = board.IO7
SPI_MOSI = board.IO11
SPI_MISO = board.IO9

DISPLAY_DC = board.IO5
DISPLAY_CS = board.IO12
DISPLAY_RESET = board.IO1

SD_CS = board.IO6

BUTTON_PIN = board.IO14
BUTTON_DEBOUNCE_SECONDS = 0.25

NAVY = 0x0A1628
GOLD = 0xFFD700
WHITE = 0xFFFFFF
RED = 0xFF3333
BLACK = 0x000000

ILI9341_CASET = 0x2A
ILI9341_PASET = 0x2B
ILI9341_RAMWR = 0x2C


# ---------------- Globals ----------------

sd_card = None
framebuffer = None

last_button_value = True
last_button_time = 0


# ---------------- Hardware Setup ----------------

backlight = pwmio.PWMOut(BACKLIGHT_PIN, frequency=5000)
backlight.duty_cycle = 0

button = digitalio.DigitalInOut(BUTTON_PIN)
button.direction = digitalio.Direction.INPUT
button.pull = digitalio.Pull.UP

displayio.release_displays()

spi = busio.SPI(
    clock=SPI_CLOCK,
    MOSI=SPI_MOSI,
    MISO=SPI_MISO,
)

display_bus = FourWire(
    spi,
    command=DISPLAY_DC,
    chip_select=DISPLAY_CS,
    reset=DISPLAY_RESET,
)

display = ILI9341(
    display_bus,
    width=DISPLAY_WIDTH,
    height=DISPLAY_HEIGHT,
    auto_refresh=False,
)

display.root_group = displayio.Group()


# ---------------- Backlight ----------------

def fade_in(steps=20, delay=0.03):
    for i in range(steps + 1):
        backlight.duty_cycle = int(65535 * i / steps)
        time.sleep(delay)


def fade_out(steps=20, delay=0.02):
    for i in range(steps, -1, -1):
        backlight.duty_cycle = int(65535 * i / steps)
        time.sleep(delay)


# ---------------- Status Display ----------------

def make_background(color):
    bmp = displayio.Bitmap(DISPLAY_WIDTH, DISPLAY_HEIGHT, 1)
    pal = displayio.Palette(1)
    pal[0] = color
    return displayio.TileGrid(bmp, pixel_shader=pal)


def show_status(msg, color=WHITE):
    splash = displayio.Group()
    splash.append(make_background(NAVY))

    lbl = label.Label(
        terminalio.FONT,
        text=str(msg),
        color=color,
        anchor_point=(0.5, 0.5),
        anchored_position=(160, 120),
    )

    splash.append(lbl)
    display.root_group = splash
    display.refresh()

    if backlight.duty_cycle < 20000:
        backlight.duty_cycle = 20000


def show_error(title, err):
    print(title, err)

    msg = str(err)
    if len(msg) > 80:
        msg = msg[:80]

    splash = displayio.Group()
    splash.append(make_background(NAVY))

    title_lbl = label.Label(
        terminalio.FONT,
        text=str(title),
        color=RED,
        anchor_point=(0.5, 0.5),
        anchored_position=(160, 90),
    )

    msg_lbl = label.Label(
        terminalio.FONT,
        text=msg,
        color=WHITE,
        anchor_point=(0.5, 0.5),
        anchored_position=(160, 125),
    )

    splash.append(title_lbl)
    splash.append(msg_lbl)

    display.root_group = splash
    display.refresh()

    if backlight.duty_cycle < 20000:
        backlight.duty_cycle = 20000


# ---------------- Button ----------------

def button_pressed_event():
    global last_button_value
    global last_button_time

    current_value = button.value
    now = time.monotonic()
    pressed = False

    if last_button_value and not current_value:
        if now - last_button_time > BUTTON_DEBOUNCE_SECONDS:
            pressed = True
            last_button_time = now

    last_button_value = current_value
    return pressed


def switch_mode():
    global MODE

    if MODE == "IMAGE":
        MODE = "BIBLE"
    else:
        MODE = "IMAGE"

    show_status("Mode: " + MODE)
    time.sleep(0.5)


def responsive_sleep(seconds):
    start = time.monotonic()

    while time.monotonic() - start < seconds:
        if button_pressed_event():
            switch_mode()
            return True

        time.sleep(0.05)

    return False


# ---------------- Text Helpers ----------------

def wrap_text(text, chars_per_line):
    words = text.split()
    lines = []
    current = ""

    for word in words:
        extra = 1 if current else 0

        if len(current) + len(word) + extra <= chars_per_line:
            if current:
                current += " "
            current += word
        else:
            if current:
                lines.append(current)
            current = word

    if current:
        lines.append(current)

    return lines


FONT_5X7 = {
    " ": [0, 0, 0, 0, 0],
    "!": [0, 0, 95, 0, 0],
    '"': [0, 7, 0, 7, 0],
    "'": [0, 0, 7, 0, 0],
    ",": [0, 160, 96, 0, 0],
    ".": [0, 96, 96, 0, 0],
    "-": [8, 8, 8, 8, 8],
    ":": [0, 54, 54, 0, 0],
    ";": [0, 182, 102, 0, 0],
    "?": [2, 1, 81, 9, 6],
    "(": [0, 28, 34, 65, 0],
    ")": [0, 65, 34, 28, 0],
    "/": [32, 16, 8, 4, 2],
    "[": [0, 127, 65, 65, 0],
    "]": [0, 65, 65, 127, 0],

    "0": [62, 81, 73, 69, 62],
    "1": [0, 66, 127, 64, 0],
    "2": [98, 81, 73, 73, 70],
    "3": [34, 65, 73, 73, 54],
    "4": [24, 20, 18, 127, 16],
    "5": [39, 69, 69, 69, 57],
    "6": [60, 74, 73, 73, 48],
    "7": [1, 113, 9, 5, 3],
    "8": [54, 73, 73, 73, 54],
    "9": [6, 73, 73, 41, 30],

    "A": [126, 9, 9, 9, 126],
    "B": [127, 73, 73, 73, 54],
    "C": [62, 65, 65, 65, 34],
    "D": [127, 65, 65, 34, 28],
    "E": [127, 73, 73, 73, 65],
    "F": [127, 9, 9, 9, 1],
    "G": [62, 65, 73, 73, 122],
    "H": [127, 8, 8, 8, 127],
    "I": [0, 65, 127, 65, 0],
    "J": [32, 64, 65, 63, 1],
    "K": [127, 8, 20, 34, 65],
    "L": [127, 64, 64, 64, 64],
    "M": [127, 2, 12, 2, 127],
    "N": [127, 4, 8, 16, 127],
    "O": [62, 65, 65, 65, 62],
    "P": [127, 9, 9, 9, 6],
    "Q": [62, 65, 81, 33, 94],
    "R": [127, 9, 25, 41, 70],
    "S": [70, 73, 73, 73, 49],
    "T": [1, 1, 127, 1, 1],
    "U": [63, 64, 64, 64, 63],
    "V": [31, 32, 64, 32, 31],
    "W": [63, 64, 56, 64, 63],
    "X": [99, 20, 8, 20, 99],
    "Y": [7, 8, 112, 8, 7],
    "Z": [97, 81, 73, 69, 67],
}


def rgb565(color):
    r = (color >> 16) & 255
    g = (color >> 8) & 255
    b = color & 255
    return ((r & 248) << 8) | ((g & 252) << 3) | (b >> 3)


def set_fb_pixel(fb, x, y, color565):
    if x < 0 or x >= DISPLAY_WIDTH or y < 0 or y >= DISPLAY_HEIGHT:
        return

    index = ((y * DISPLAY_WIDTH) + x) * 2
    fb[index] = color565 >> 8
    fb[index + 1] = color565 & 255


def get_verse_canvas_size():
    if VERSE_ROTATION in (90, 270):
        return 240, 320

    return 320, 240


def set_verse_pixel(fb, x, y, color565):
    canvas_w, canvas_h = get_verse_canvas_size()

    if x < 0 or x >= canvas_w or y < 0 or y >= canvas_h:
        return

    if VERSE_ROTATION == 0:
        px = x
        py = y

    elif VERSE_ROTATION == 90:
        px = DISPLAY_WIDTH - 1 - y
        py = x

    elif VERSE_ROTATION == 180:
        px = DISPLAY_WIDTH - 1 - x
        py = DISPLAY_HEIGHT - 1 - y

    elif VERSE_ROTATION == 270:
        px = y
        py = DISPLAY_HEIGHT - 1 - x

    else:
        return

    set_fb_pixel(fb, px, py, color565)


def darken_whole_frame(fb, shade_percent=45):
    if shade_percent <= 0:
        return

    if shade_percent > 100:
        shade_percent = 100

    keep_percent = 100 - shade_percent

    for i in range(0, len(fb), 2):
        color = (fb[i] << 8) | fb[i + 1]

        r = (color >> 11) & 31
        g = (color >> 5) & 63
        b = color & 31

        r = (r * keep_percent) // 100
        g = (g * keep_percent) // 100
        b = (b * keep_percent) // 100

        color = (r << 11) | (g << 5) | b
        fb[i] = color >> 8
        fb[i + 1] = color & 255


def normalize_char(ch):
    if ch >= "a" and ch <= "z":
        return chr(ord(ch) - 32)

    if ch in ("’", "‘", "`"):
        return "'"

    if ch in ("“", "”"):
        return '"'

    if ch in ("–", "—"):
        return "-"

    return ch


def draw_char_verse(fb, ch, x, y, color565, scale=2):
    ch = normalize_char(ch)

    if ch not in FONT_5X7:
        ch = "?"

    columns = FONT_5X7[ch]

    for col in range(5):
        bits = columns[col]

        for row in range(7):
            if bits & (1 << row):
                px = x + col * scale
                py = y + row * scale

                for sy in range(scale):
                    for sx in range(scale):
                        set_verse_pixel(fb, px + sx, py + sy, color565)


def draw_text_verse(fb, text, x, y, color565, scale=2):
    cursor_x = x

    for ch in text:
        draw_char_verse(fb, ch, cursor_x, y, color565, scale)
        cursor_x += 6 * scale


def display_verse(text, reference):
    global framebuffer

    if framebuffer is None:
        show_status("No image background", RED)
        return

    verse_fb = bytearray(framebuffer)

    canvas_w, canvas_h = get_verse_canvas_size()

    scale = 2
    line_height = 18
    text_color = rgb565(WHITE)
    shadow_color = rgb565(BLACK)
    ref_color = rgb565(GOLD)

    chars_per_line = canvas_w // (6 * scale)
    lines = wrap_text(text, chars_per_line)

    darken_whole_frame(verse_fb, VERSE_SHADE_PERCENT)

    y = 34

    for line in lines:
        text_width = len(line) * 6 * scale
        x = (canvas_w - text_width) // 2

        if x < 0:
            x = 0

        draw_text_verse(verse_fb, line, x + 2, y + 2, shadow_color, scale)
        draw_text_verse(verse_fb, line, x, y, text_color, scale)

        y += line_height

        if y > canvas_h - 70:
            break

    ref_width = len(reference) * 6 * scale
    ref_x = (canvas_w - ref_width) // 2

    if ref_x < 0:
        ref_x = 0

    ref_y = canvas_h - 36

    draw_text_verse(verse_fb, reference, ref_x + 2, ref_y + 2, shadow_color, scale)
    draw_text_verse(verse_fb, reference, ref_x, ref_y, ref_color, scale)

    draw_framebuffer(verse_fb)


# ---------------- SD Card ----------------

def mount_sd(retries=3):
    global sd_card

    for attempt in range(retries):
        try:
            sd_card = sdcardio.SDCard(spi, SD_CS, baudrate=4000000)
            vfs = storage.VfsFat(sd_card)
            storage.mount(vfs, "/sd")
            return True

        except Exception as e:
            show_error("SD mount error", e)
            time.sleep(0.5)

    show_status("SD mount failed", RED)
    return False


def unmount_sd():
    global sd_card

    try:
        storage.umount("/sd")
    except Exception:
        pass

    try:
        if sd_card:
            sd_card.deinit()
    except Exception:
        pass

    sd_card = None
    time.sleep(0.2)


def find_bmp_files():
    bmp_files = []

    try:
        for filename in sorted(os.listdir("/sd")):
            if filename.lower().endswith(".bmp"):
                bmp_files.append("/sd/" + filename)

    except Exception as e:
        show_error("SD list error", e)

    return bmp_files


# ---------------- BMP Helpers ----------------

def read_le16(data, offset):
    return data[offset] + (data[offset + 1] * 256)


def read_le32(data, offset):
    return (
        data[offset]
        + (data[offset + 1] * 256)
        + (data[offset + 2] * 65536)
        + (data[offset + 3] * 16777216)
    )


def signed32(value):
    if value >= 2147483648:
        value -= 4294967296
    return value


def rgb888_to_rgb565_bytes(r, g, b):
    color = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
    return color >> 8, color & 0xFF


def map_rotated_pixel(x, y, src_w, src_h, rotation):
    if rotation == 0:
        return x, y

    if rotation == 90:
        return src_h - 1 - y, x

    if rotation == 180:
        return src_w - 1 - x, src_h - 1 - y

    if rotation == 270:
        return y, src_w - 1 - x

    raise ValueError("Rotation must be 0, 90, 180, or 270")


def load_bmp_to_rgb565_framebuffer(path, rotation=0):
    gc.collect()

    with open(path, "rb") as f:
        header = f.read(54)

        if len(header) < 54:
            raise ValueError("BMP header too short")

        if header[0] != 66 or header[1] != 77:
            raise ValueError("Not a BMP file")

        pixel_offset = read_le32(header, 10)
        dib_size = read_le32(header, 14)
        bmp_width = signed32(read_le32(header, 18))
        bmp_height = signed32(read_le32(header, 22))
        planes = read_le16(header, 26)
        bit_depth = read_le16(header, 28)
        compression = read_le32(header, 30)

        if dib_size < 40:
            raise ValueError("Unsupported BMP header")

        if planes != 1:
            raise ValueError("Invalid BMP planes")

        if compression != 0:
            raise ValueError("Compressed BMP not supported")

        if bit_depth != 24:
            raise ValueError("Only 24-bit BMP files are supported")

        top_down = False

        if bmp_height < 0:
            top_down = True
            bmp_height = -bmp_height

        if bmp_width < 0:
            bmp_width = -bmp_width

        if rotation in (90, 270):
            out_w = bmp_height
            out_h = bmp_width
        else:
            out_w = bmp_width
            out_h = bmp_height

        if out_w != DISPLAY_WIDTH or out_h != DISPLAY_HEIGHT:
            raise ValueError("Rotated image must be exactly 320x240")

        fb = bytearray(DISPLAY_WIDTH * DISPLAY_HEIGHT * 2)

        row_size = ((bmp_width * 3 + 3) // 4) * 4
        row_buffer = bytearray(row_size)

        for source_row in range(bmp_height):
            if top_down:
                y = source_row
            else:
                y = bmp_height - 1 - source_row

            f.seek(pixel_offset + source_row * row_size)
            bytes_read = f.readinto(row_buffer)

            if bytes_read != row_size:
                raise ValueError("Could not read BMP row")

            src = 0

            for x in range(bmp_width):
                b = row_buffer[src]
                g = row_buffer[src + 1]
                r = row_buffer[src + 2]
                src += 3

                dx, dy = map_rotated_pixel(x, y, bmp_width, bmp_height, rotation)

                fb_index = ((dy * DISPLAY_WIDTH) + dx) * 2
                hi, lo = rgb888_to_rgb565_bytes(r, g, b)

                fb[fb_index] = hi
                fb[fb_index + 1] = lo

    gc.collect()
    return fb


# ---------------- Direct Display Drawing ----------------

def set_address_window(x0, y0, x1, y1):
    display_bus.send(
        ILI9341_CASET,
        bytes([
            x0 >> 8, x0 & 0xFF,
            x1 >> 8, x1 & 0xFF,
        ]),
    )

    display_bus.send(
        ILI9341_PASET,
        bytes([
            y0 >> 8, y0 & 0xFF,
            y1 >> 8, y1 & 0xFF,
        ]),
    )


def draw_framebuffer(fb):
    rows_per_chunk = 16
    bytes_per_row = DISPLAY_WIDTH * 2

    for y in range(0, DISPLAY_HEIGHT, rows_per_chunk):
        h = min(rows_per_chunk, DISPLAY_HEIGHT - y)

        set_address_window(0, y, DISPLAY_WIDTH - 1, y + h - 1)

        start = y * bytes_per_row
        end = start + (h * bytes_per_row)

        display_bus.send(ILI9341_RAMWR, fb[start:end])


# ---------------- Image Mode ----------------

def load_image_list():
    if not mount_sd():
        return []

    files = find_bmp_files()
    unmount_sd()
    return files


def load_framebuffer_from_sd(path):
    fb = None

    if not mount_sd():
        return None

    try:
        fb = load_bmp_to_rgb565_framebuffer(path, IMAGE_ROTATION)

    except Exception as e:
        show_error("Image load error", e)

    unmount_sd()
    return fb


def load_first_image_as_background():
    global framebuffer

    if framebuffer is not None:
        return True

    show_status("Loading background...")

    image_files = load_image_list()

    if len(image_files) == 0:
        show_status("No BMP background", RED)
        return False

    framebuffer = load_framebuffer_from_sd(image_files[0])

    if framebuffer is None:
        show_status("Background failed", RED)
        return False

    draw_framebuffer(framebuffer)
    return True


def show_image(path, first_image=False):
    global framebuffer

    show_status("Loading image...")

    new_framebuffer = load_framebuffer_from_sd(path)

    if new_framebuffer is None:
        show_status("Skipping image", RED)
        return False

    if not first_image:
        fade_out()

    framebuffer = new_framebuffer
    draw_framebuffer(framebuffer)
    fade_in()

    return True


def run_image_mode():
    show_status("Loading images...")

    image_files = load_image_list()

    if len(image_files) == 0:
        show_status("No BMP files found", RED)
        responsive_sleep(2)
        return

    index = 0

    while MODE == "IMAGE":
        show_image(image_files[index], first_image=(index == 0))

        if responsive_sleep(IMAGE_INTERVAL_SECONDS):
            return

        index += 1

        if index >= len(image_files):
            index = 0


# ---------------- Bible Mode ----------------

def day_of_year():
    t = time.localtime()
    days = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]

    leap = (
        t.tm_year % 4 == 0
        and (t.tm_year % 100 != 0 or t.tm_year % 400 == 0)
    )

    day = days[t.tm_mon - 1] + t.tm_mday

    if leap and t.tm_mon > 2:
        day += 1

    return day


def clean_verse(text):
    text = re.sub(r"\[\d+\]", "", text)
    text = text.replace("\n", " ")

    while "  " in text:
        text = text.replace("  ", " ")

    return text.strip()


def connect_wifi(retries=5):
    ssid = os.getenv("WIFI_SSID")
    password = os.getenv("WIFI_PASSWORD")

    if not ssid or not password:
        show_status("Missing WiFi settings", RED)
        return False

    if wifi.radio.ipv4_address:
        return True

    for attempt in range(retries):
        try:
            show_status("WiFi attempt " + str(attempt + 1))
            wifi.radio.connect(ssid, password)
            return True

        except Exception as e:
            show_error("WiFi error", e)
            time.sleep(2 ** attempt)

    return False


def sync_time():
    try:
        show_status("Setting time...")

        pool = socketpool.SocketPool(wifi.radio)
        ntp = adafruit_ntp.NTP(
            pool,
            server="pool.ntp.org",
            tz_offset=TIMEZONE_OFFSET,
        )

        rtc.RTC().datetime = ntp.datetime

        t = time.localtime()
        show_status(
            str(t.tm_year) + "-"
            + str(t.tm_mon) + "-"
            + str(t.tm_mday)
        )

        time.sleep(1)
        return True

    except Exception as e:
        show_error("Time sync error", e)
        return False


def make_session():
    return adafruit_requests.Session(
        adafruit_connection_manager.get_radio_socketpool(wifi.radio),
        adafruit_connection_manager.get_radio_ssl_context(wifi.radio),
    )


def fetch_verse(session, retries=3):
    app_key = os.getenv("YOUVERSION_APP_KEY")
    scripture_key = os.getenv("SCRIPTURE_API_KEY")

    bible_id = "d6e14a625393b4da-01"
    base = "https://api.youversion.com/v1"
    today = day_of_year()

    if not app_key or not scripture_key:
        show_status("Missing API keys", RED)
        return None, None

    for attempt in range(retries):
        r1 = None
        r2 = None

        try:
            show_status("Fetching verse...")

            r1 = session.get(
                base + "/verse_of_the_days/" + str(today),
                headers={"X-YVP-App-Key": app_key},
            )

            data1 = r1.json()
            r1.close()
            r1 = None

            ref_raw = data1["passage_id"]
            parts = ref_raw.split(".")

            book = parts[0]
            chapter = parts[1]
            verse_num = parts[2]

            gc.collect()

            url = (
                "https://rest.api.bible/v1/bibles/"
                + bible_id
                + "/verses/"
                + ref_raw
                + "?content-type=text&include-notes=false&include-titles=false"
            )

            r2 = session.get(url, headers={"api-key": scripture_key})

            data2 = r2.json()
            r2.close()
            r2 = None

            verse_data = data2.get("data", {})
            verse_text = clean_verse(verse_data.get("content", ""))
            human_ref = verse_data.get(
                "reference",
                book + " " + chapter + ":" + verse_num,
            )

            gc.collect()
            return verse_text, human_ref

        except Exception as e:
            show_error("Fetch error", e)

            if r1:
                try:
                    r1.close()
                except Exception:
                    pass

            if r2:
                try:
                    r2.close()
                except Exception:
                    pass

            gc.collect()

            if attempt < retries - 1:
                time.sleep(3 * (attempt + 1))

    return None, None


def run_bible_mode():
    if framebuffer is None:
        load_first_image_as_background()

    show_status("Starting WiFi...")

    if not connect_wifi():
        show_status("WiFi failed", RED)

        if responsive_sleep(5):
            return

        supervisor.reload()

    if not sync_time():
        show_status("Time sync failed", RED)

        if responsive_sleep(10):
            return

        supervisor.reload()

    session = make_session()
    last_day = -1
    fail_count = 0

    fade_in()

    while MODE == "BIBLE":
        if button_pressed_event():
            switch_mode()
            return

        today = day_of_year()

        if today != last_day:
            verse_text, human_ref = fetch_verse(session)

            if verse_text:
                display_verse(verse_text, human_ref)
                last_day = today
                fail_count = 0

            else:
                fail_count += 1
                show_status("Fetch failed", RED)

                if fail_count >= 3:
                    show_status("Reconnecting...", WHITE)

                    try:
                        wifi.radio.enabled = False
                        time.sleep(1)
                        wifi.radio.enabled = True
                    except Exception as e:
                        show_error("Radio error", e)

                    if connect_wifi():
                        if not sync_time():
                            show_status("Time sync failed", RED)

                            if responsive_sleep(10):
                                return

                            supervisor.reload()

                        session = make_session()
                        fail_count = 0

                    else:
                        show_status("WiFi lost", RED)

                        if responsive_sleep(5):
                            return

                        supervisor.reload()

                if responsive_sleep(300):
                    return

                continue

        if responsive_sleep(3600):
            return


# ---------------- Main ----------------

show_status("Starting up...")
time.sleep(0.5)

while True:
    try:
        if MODE == "IMAGE":
            run_image_mode()

        elif MODE == "BIBLE":
            run_bible_mode()

        else:
            show_status("Bad MODE setting", RED)
            time.sleep(5)

    except Exception as e:
        show_error("Runtime error", e)
        time.sleep(10)