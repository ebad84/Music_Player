from machine import I2S, Pin
import time

# ================ تنظیمات I2S ==================
audio_out = I2S(
    0,                                 # I2S شماره 0
    sck=Pin(26),                       # BCLK
    ws=Pin(25),                        # LRCLK
    sd=Pin(22),                        # DIN
    mode=I2S.TX,                       
    bits=16,                           # 16 بیت
    format=I2S.STEREO,                   # <<<<<< مونو
    rate=44100,                        # همان نرخ خروجی که WAV داشتی
    ibuf=4096
)

# ================ پخش فایل WAV ================
def play_wav(path):
    print("Playing:", path)

    with open(path, "rb") as f:
        # رد شدن از هدر WAV (44 بایت)
        f.read(44)

        while True:
            data = f.read(4096)
            if not data:
                print("breaking")
                break

            audio_out.write(data)

    print("Done!")


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
    
    
# اجرای تست
play_wav("sd/LastNight_44100_2.wav")

