# import network
# import urequests
# import os
# import time
# 
# # ------------------------------------------
# #  اتصال به وایفای
# # ------------------------------------------
# def wifi_connect(ssid, password):
#     wlan = network.WLAN(network.STA_IF)
#     wlan.active(True)
#     wlan.connect(ssid, password)
#     print("Connecting to WiFi", ssid, "...")
# 
#     t0 = time.time()
#     while not wlan.isconnected():
#         time.sleep(0.2)
#         if time.time() - t0 > 15:
#             print("WiFi connection failed!")
#             return False
# 
#     print("Connected! IP:", wlan.ifconfig()[0])
#     return True
# 
# 
# # ------------------------------------------
# #  دانلود فایل حجیم با مدیریت حافظه
# # ------------------------------------------
# def download_file(url, path, chunk_size=1024):
#     import urequests
#     import gc
#     import os
# 
#     print("Connecting to server:", url)
# 
#     r = urequests.get(url, stream=True)
# 
#     total = int(r.headers.get("Content-Length", "0"))
#     if total == 0:
#         print("Server did not send Content-Length")
#         return False
# 
#     print("File size:", total, "bytes")
# 
#     # ایجاد پوشه مقصد
#     folder = path.rsplit("/", 1)[0]
#     try:
#         os.mkdir(folder)
#     except:
#         pass
# 
#     f = open(path, "wb")
# 
#     downloaded = 0
#     percent_step = 10
#     next_percent = percent_step
# 
#     try:
#         while downloaded < total:
#             gc.collect()
# 
#             chunk = r.raw.read(chunk_size)
#             if not chunk:
#                 break
# 
#             # جلوگیری از انفجار حافظه
#             if len(chunk) > 4096:
#                 print("Error: server sent too large chunk:", len(chunk))
#                 return False
# 
#             f.write(chunk)
#             downloaded += len(chunk)
# 
#             percent = int(downloaded * 100 / total)
#             if percent >= next_percent:
#                 print(percent, "%")
#                 next_percent += percent_step
# 
#         print("Download complete:", path)
#         f.close()
#         r.close()
#         return True
# 
#     except Exception as e:
#         print("Download Error:", e)
#         f.close()
#         r.close()
#         return False
# 
# 
# 
# # ----------------------------------------------------------------
# #  استفاده
# # ----------------------------------------------------------------
# SSID = "GoodUwUNet"
# PASSWORD = "s1864.5149"
# 
# if wifi_connect(SSID, PASSWORD):
#     input(1001)
#     download_file(
#         url="http://10.173.27.197:8000/file",
#         path="sd/LastNight_44100.wav"
#     )
#









# download.py - روی ESP32 اجرا کنید
# نسخه بهبود یافته با مدیریت بهتر حافظه و خطا

import network
import urequests
import os
import time
import gc
import machine

# ------------------------------------------
#  اتصال به وایفای
# ------------------------------------------
def wifi_connect(ssid, password, timeout=20):
    """اتصال به WiFi با مدیریت خطا"""
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    
    # قطع اتصال قبلی
    if wlan.isconnected():
        wlan.disconnect()
        time.sleep(1)
    
    print(f"Connecting to WiFi: {ssid}")
    wlan.connect(ssid, password)
    
    t0 = time.time()
    dots = 0
    while not wlan.isconnected():
        if time.time() - t0 > timeout:
            print("\n❌ WiFi connection timeout!")
            return False
        
        print(".", end="")
        dots += 1
        if dots % 50 == 0:
            print()
        time.sleep(0.2)
    
    print(f"\n✓ Connected!")
    print(f"  IP: {wlan.ifconfig()[0]}")
    print(f"  Signal: {wlan.status('rssi')} dBm")
    return True


# ------------------------------------------
#  ایجاد پوشه (با پشتیبانی از nested folders)
# ------------------------------------------
def ensure_dir(path):
    """ایجاد پوشه و زیرپوشه‌ها"""
    parts = path.split('/')
    current = ''
    for part in parts[:-1]:  # آخری فایل است
        if part:
            current += '/' + part if current else part
            try:
                os.mkdir(current)
                print(f"📁 Created folder: {current}")
            except OSError:
                pass  # پوشه از قبل وجود دارد


# ------------------------------------------
#  دانلود فایل با مدیریت بهتر حافظه
# ------------------------------------------
def download_file(url, path, chunk_size=512):
    """
    دانلود فایل با chunk های کوچک‌تر و بهتر
    chunk_size=512 برای ESP32 امن‌تر است
    """
    print(f"\n{'='*50}")
    print(f"📥 Starting download...")
    print(f"   URL: {url}")
    print(f"   Save to: {path}")
    print(f"{'='*50}\n")
    
    # پاک کردن حافظه
    gc.collect()
    print(f"💾 Free memory: {gc.mem_free()} bytes")
    
    # ایجاد پوشه
    ensure_dir(path)
    
    # درخواست HTTP
    try:
        print("🔗 Connecting to server...")
        r = urequests.get(url, stream=True)
        
        if r.status_code != 200:
            print(f"❌ HTTP Error: {r.status_code}")
            r.close()
            return False
        
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False
    
    # دریافت حجم فایل
    total = int(r.headers.get("Content-Length", "0"))
    if total == 0:
        print("⚠️  Warning: Server didn't send file size")
        # ادامه می‌دهیم بدون نمایش درصد
    else:
        print(f"📦 File size: {total:,} bytes ({total/1024:.1f} KB)")
    
    # باز کردن فایل برای نوشتن
    try:
        f = open(path, "wb")
    except Exception as e:
        print(f"❌ Can't create file: {e}")
        r.close()
        return False
    
    # دانلود
    downloaded = 0
    last_percent = -1
    last_gc = 0
    start_time = time.time()
    
    try:
        while True:
            # پاک کردن حافظه هر 10KB
            if downloaded - last_gc > 10240:
                gc.collect()
                last_gc = downloaded
            
            # خواندن chunk
            chunk = r.raw.read(chunk_size)
            
            if not chunk:
                break
            
            # نوشتن در فایل
            f.write(chunk)
            downloaded += len(chunk)
            
            # نمایش پیشرفت
            if total > 0:
                percent = int(downloaded * 100 / total)
                if percent != last_percent and percent % 5 == 0:
                    elapsed = time.time() - start_time
                    speed = downloaded / elapsed if elapsed > 0 else 0
                    print(f"  {percent}% - {downloaded:,}/{total:,} bytes - {speed/1024:.1f} KB/s")
                    last_percent = percent
            else:
                # اگر حجم مشخص نیست، هر 10KB گزارش بده
                if downloaded % 10240 == 0:
                    print(f"  Downloaded: {downloaded:,} bytes")
        
        # بستن فایل
        f.close()
        r.close()
        
        # محاسبه آمار
        elapsed = time.time() - start_time
        speed = downloaded / elapsed if elapsed > 0 else 0
        
        print(f"\n{'='*50}")
        print(f"✅ Download complete!")
        print(f"   File: {path}")
        print(f"   Size: {downloaded:,} bytes ({downloaded/1024:.1f} KB)")
        print(f"   Time: {elapsed:.1f} seconds")
        print(f"   Speed: {speed/1024:.1f} KB/s")
        print(f"   Free memory: {gc.mem_free()} bytes")
        print(f"{'='*50}\n")
        
        return True
        
    except MemoryError:
        print("\n❌ Out of memory!")
        print("💡 Try:")
        print("   1. Use smaller chunk_size (256)")
        print("   2. Delete unused files")
        print("   3. Reboot ESP32")
        f.close()
        r.close()
        return False
        
    except Exception as e:
        print(f"\n❌ Download error: {e}")
        print(f"   Downloaded: {downloaded} bytes before error")
        f.close()
        r.close()
        return False


# ------------------------------------------
#  تابع کمکی: لیست فایل‌ها
# ------------------------------------------
def list_files(path='.'):
    """نمایش فایل‌های موجود"""
    print(f"\n📂 Files in '{path}':")
    try:
        files = os.listdir(path)
        if not files:
            print("   (empty)")
        for f in files:
            try:
                stat = os.stat(f"{path}/{f}" if path != '.' else f)
                size = stat[6]
                is_dir = stat[0] & 0x4000
                print(f"   {'📁' if is_dir else '📄'} {f} ({size:,} bytes)")
            except:
                print(f"   ? {f}")
    except Exception as e:
        print(f"   Error: {e}")
    print()


# ------------------------------------------
#  تابع کمکی: حذف فایل
# ------------------------------------------
def delete_file(path):
    """حذف فایل"""
    try:
        os.remove(path)
        print(f"🗑️  Deleted: {path}")
        return True
    except Exception as e:
        print(f"❌ Can't delete: {e}")
        return False



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

# ------------------------------------------
#  تابع اصلی
# ------------------------------------------
def main():
    # تنظیمات WiFi
    SSID = "GoodUwUNet"
    PASSWORD = "s1864.5149"
    
    # تنظیمات دانلود
    SERVER_IP = "10.173.27.197"  # IP کامپیوتر شما
    SERVER_PORT = 8000
    
    print("\n" + "="*50)
    print("ESP32 File Downloader")
    print("="*50)
    
    # اتصال به WiFi
    if not wifi_connect(SSID, PASSWORD):
        print("⛔ Can't continue without WiFi")
        return
    
    # نمایش فایل‌های فعلی
    list_files()
    
    # دانلود فایل
    # فرمت: http://IP:PORT/filename.ext
    success = download_file(
        url=f"http://{SERVER_IP}:{SERVER_PORT}/LastNight3.wav",
        path="sd/LastNight3.wav",
        chunk_size=512  # کاهش chunk برای جلوگیری از MemoryError
    )
    
    if success:
        # نمایش فایل‌های بعد از دانلود
        list_files('sd')
    else:
        print("\n💡 Tips:")
        print("   • Check server is running on PC")
        print("   • Check IP address is correct")
        print("   • Try reducing chunk_size to 256")
        print("   • Check file exists on server")
    
    # GC نهایی
    gc.collect()
    print(f"💾 Final free memory: {gc.mem_free()} bytes")


# ------------------------------------------
#  اجرا
# ------------------------------------------
if __name__ == '__main__':
    main()