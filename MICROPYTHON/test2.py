from machine import I2S, Pin, I2C
import time, struct, math, os, machine, sdcard, random
import ssd1306

# ----------------------------------------
# OLED SSD1306 init (128x64)
# ----------------------------------------
i2c = I2C(0, scl=Pin(22), sda=Pin(21))
oled = ssd1306.SSD1306_I2C(128, 64, i2c)

def draw_screen(song_name):
    """
    این تابع صفحه را آپدیت می‌کند:
    - اسکرول اسم آهنگ در 1/3 بالا
    - نمودار فرکانسی فیک در پایین
    """
    global scroll_x, text_len

    oled.fill(0)

    # --- 1/3 بالا — اسکرول اسم آهنگ ---
    gap = 20
    oled.text(song_name, -scroll_x, 0)
    oled.text(song_name, -scroll_x + text_len + gap, 0)

    scroll_x += 2
    if scroll_x > text_len + gap:
        scroll_x = 0

    # --- 2/3 پایین — ویژوالایزر ---
    graph_height = 44
    bars = 16
    bar_w = 7

    for i in range(bars):
        h = random.randint(5, graph_height)
        x = i * bar_w
        y = 64 - h
        oled.fill_rect(x, y, bar_w - 2, h, 1)

    oled.show()


# ----------------------------------------
# I2S setup
# ----------------------------------------
audio = I2S(
    0,
    sck=Pin(26),   # BCK
    ws=Pin(25),    # LRCLK
    sd=Pin(27),    # DIN
    mode=I2S.TX,
    bits=16,
    format=I2S.MONO,
    rate=16000,
    ibuf=40000
)

# ----------------------------------------
# SD CARD
# ----------------------------------------
spi = machine.SPI(1,
                  baudrate=10_000_000,
                  polarity=0,
                  phase=0,
                  sck=machine.Pin(18),
                  mosi=machine.Pin(23),
                  miso=machine.Pin(19))

sd = sdcard.SDCard(spi, machine.Pin(5))  # CS = 5
os.mount(sd, "/sd")
print("SD mounted:", os.listdir("/sd"))


# ----------------------------------------
# WAV creator (اختیاری)
# ----------------------------------------
def create_wav(filename="tone.wav", seconds=2, freq=440):
    rate = 16000
    amp = 10000
    samples = int(rate * seconds)

    with open(filename, "wb") as f:
        f.write(b"RIFF")
        f.write(struct.pack("<I", 36 + samples*2))
        f.write(b"WAVE")
        f.write(b"fmt ")
        f.write(struct.pack("<I", 16))
        f.write(struct.pack("<H", 1))
        f.write(struct.pack("<H", 1))
        f.write(struct.pack("<I", rate))
        f.write(struct.pack("<I", rate*2))
        f.write(struct.pack("<H", 2))
        f.write(struct.pack("<H", 16))
        f.write(b"data")
        f.write(struct.pack("<I", samples * 2))

        for n in range(samples):
            sample = int(amp * math.sin(2*math.pi*freq*(n/rate)))
            f.write(struct.pack("<h", sample))


# ----------------------------------------
# پخش WAV + آپدیت OLED
# ----------------------------------------
def play_wav(filename):
    global scroll_x, text_len
    song_name = filename.split("/")[-1]

    scroll_x = 0
    text_len = len(song_name) * 8
    show_it = 0

    with open(filename, "rb") as f:
        f.read(44)  # skip header

        while True:
            data = f.read(1024)
            if not data:
                break

            audio.write(data)

            # آپدیت صفحه در حین پخش
            if show_it == 5:
                draw_screen(song_name)
                show_it = 0
            show_it+=1

# ----------------------------------------
# اجرای برنامه
# ----------------------------------------
play_wav("sd/output.wav")

