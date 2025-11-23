# main.py - این فایل را هم روی ESP32 آپلود کنید
# این فایل به صورت خودکار بعد از boot اجرا می‌شود

import network
import time
from ftp_server import SimpleFTPServer

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

# اطلاعات WiFi خود را وارد کنید
WIFI_SSID = 'GoodNetUwU'
WIFI_PASSWORD = 's1864.5149'

def connect_wifi():
    sta_if = network.WLAN(network.STA_IF)
    if not sta_if.isconnected():
        print('Connecting to WiFi...')
        sta_if.active(True)
        sta_if.connect(WIFI_SSID, WIFI_PASSWORD)
        
        # صبر برای اتصال
        timeout = 20
        while not sta_if.isconnected() and timeout > 0:
            time.sleep(1)
            timeout -= 1
            print('.', end='')
        
        print()
        
    if sta_if.isconnected():
        print('WiFi connected!')
        print('Network config:', sta_if.ifconfig())
        return True
    else:
        print('Failed to connect to WiFi')
        return False

# اتصال به WiFi
if connect_wifi():
    # شروع سرور FTP
    print('\n' + '='*40)
    print('Starting FTP Server...')
    print('='*40)
    
    server = SimpleFTPServer(port=21)
    server.start()
else:
    print('Cannot start FTP server without WiFi connection')