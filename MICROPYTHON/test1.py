from machine import I2S, Pin
import time

# --- I2S setup ---
# audio = I2S(
#     0,                                  # I2S ID → فقط 0 یا 1
#     sck=Pin(18),                        # BCLK
#     ws=Pin(19),                         # LRCLK / WSEL
#     sd=Pin(23),                         # DIN
#     mode=I2S.TX,                        # ارسال صدا
#     bits=16,                            # 16-bit audio
#     format=I2S.MONO,                    # تک‌کاناله
#     rate=16000,                         # 16kHz
#     ibuf=40000                          # بافر
# )
# I2S با پین‌های جدید (جدای از SD)
audio = I2S(
    0,
    sck=Pin(26),   # BCK
    ws=Pin(25),    # LRCLK / WSEL
    sd=Pin(27),    # DIN
    mode=I2S.TX,
    bits=16,
    format=I2S.MONO,
    rate=16000,
    ibuf=40000
)
import struct
import math

if 1:
    import machine, os
    import sdcard

    spi = machine.SPI(1,
                      baudrate=10000000,
                      polarity=0,
                      phase=0,
                      sck=machine.Pin(18),
                      mosi=machine.Pin(23),
                      miso=machine.Pin(19))

    sd = sdcard.SDCard(spi, machine.Pin(5))  # CS = 5
    os.mount(sd, "/sd")

    print("SD mounted!")
    print("Files:", os.listdir("/sd"))

def create_wav(filename="tone.wav", seconds=2, freq=440):
    rate = 16000
    amp = 10000
    samples = int(rate * seconds)

    # header ساختن
    with open(filename, "wb") as f:
        # RIFF header
        f.write(b"RIFF")
        f.write(struct.pack("<I", 36 + samples*2))
        f.write(b"WAVE")

        # fmt chunk
        f.write(b"fmt ")
        f.write(struct.pack("<I", 16))
        f.write(struct.pack("<H", 1))     # PCM
        f.write(struct.pack("<H", 1))     # MONO
        f.write(struct.pack("<I", rate))  # sample rate
        f.write(struct.pack("<I", rate*2))
        f.write(struct.pack("<H", 2))
        f.write(struct.pack("<H", 16))    # bits

        # data chunk
        f.write(b"data")
        f.write(struct.pack("<I", samples * 2))

        # نوشتن نمونه‌ها
        for n in range(samples):
            sample = int(amp * math.sin(2 * math.pi * freq * (n / rate)))
            f.write(struct.pack("<h", sample))

# create_wav()
# print("tone.wav ساخته شد!")
def play_wav(filename):
    with open(filename, "rb") as f:
        f.read(44)   # رد کردن WAV header

        while True:
            data = f.read(1024)
            if not data:
                break
            audio.write(data)

# play_wav("tone.wav")
# os.unmount(sd, "/sd")
# time.sleep(3)
play_wav("sd/output.wav")
