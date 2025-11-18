from machine import Pin, I2C
import ssd1306
import time

# ایجاد I2C با پین‌های 21 و 22
i2c = I2C(1, scl=Pin(22), sda=Pin(21), freq=400000)

print("I2C scan:", i2c.scan())  # باید یک آدرس مثل 0x3C یا 0x3D بده

oled = ssd1306.SSD1306_I2C(128, 64, i2c)

oled.fill(0)
oled.text("Hello ESP32!", 0, 0)
oled.text("Audio Player", 0, 16)
oled.show()

print("======== I2C [OLED] PASS! ========")

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

print("======== SPI [SD CARD] PASS! ========")