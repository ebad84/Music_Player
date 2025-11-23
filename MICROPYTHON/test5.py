# simple_player.py - ساده‌ترین و پایدارترین روش
# بدون هیچ خطای Watchdog!

from machine import I2S, Pin, SPI
import time
import os
import gc

print("\n" + "="*50)
print("Simple Stable Player")
print("="*50 + "\n")

# ================ راه‌اندازی با تنظیمات امن ==================

# 1. SD Card با سرعت امن
print("📂 Initializing SD Card...")
try:
    import sdcard
    
    spi = SPI(1,
              baudrate=10000000,  # 10MHz - خیلی امن!
              polarity=0,
              phase=0,
              sck=Pin(18),
              mosi=Pin(23),
              miso=Pin(19))
    
    sd = sdcard.SDCard(spi, Pin(5))
    
    # Unmount اگر از قبل mount بود
    try:
        os.umount("/sd")
    except:
        pass
    
    os.mount(sd, "/sd")
    print("✓ SD mounted at 10MHz")
    
    # نمایش فایل‌ها
    files = os.listdir("/sd")
    print(f"  Files: {len(files)}")
    for f in files:
        if f.endswith('.wav'):
            size = os.stat(f"/sd/{f}")[6]
            print(f"    🎵 {f} ({size/1024:.0f}KB)")
    
except Exception as e:
    print(f"✗ SD Error: {e}")
    import sys
    sys.exit()

# 2. I2S با تنظیمات محافظه‌کارانه
print("\n🔊 Initializing I2S...")
try:
    audio_out = I2S(
        0,
        sck=Pin(26),
        ws=Pin(25),
        sd=Pin(22),
        mode=I2S.TX,
        bits=16,
        format=I2S.STEREO,
        rate=44100,
        ibuf=20480  # 20KB بافر
    )
    print("✓ I2S ready (44.1kHz Stereo)")
except Exception as e:
    print(f"✗ I2S Error: {e}")
    import sys
    sys.exit()

# ================ تابع پخش ساده ==================

def play_simple(path):
    """پخش با روش ساده و پایدار"""
    
    print(f"\n{'='*50}")
    print(f"▶️  {path}")
    print("="*50)
    
    # پاک کردن حافظه
    gc.collect()
    print(f"💾 Free: {gc.mem_free()/1024:.0f}KB")
    
    try:
        # باز کردن فایل
        f = open(path, "rb")
        
        # رد شدن از هدر
        header = f.read(44)
        
        # اطلاعات فایل
        file_size = os.stat(path)[6] - 44
        print(f"📦 Size: {file_size/1024:.0f}KB")
        
        # تنظیمات بهینه
        CHUNK_SIZE = 4096  # 4KB - تعادل خوب
        
        bytes_played = 0
        last_print = 0
        start = time.ticks_ms()
        
        print("🎵 Playing...")
        
        # حلقه پخش
        while True:
            # خواندن chunk
            chunk = f.read(CHUNK_SIZE)
            
            if not chunk:
                break
            
            # پخش
            audio_out.write(chunk)
            bytes_played += len(chunk)
            
            # گزارش هر 100KB
            if bytes_played - last_print > 102400:
                percent = bytes_played * 100 / file_size
                elapsed = time.ticks_diff(time.ticks_ms(), start)
                if elapsed > 0:
                    speed = bytes_played / elapsed
                print(f"  {percent:.0f}% | {speed:.0f} KB/s")
                last_print = bytes_played
        
        # بستن فایل
        f.close()
        
        # آمار
        elapsed = time.ticks_diff(time.ticks_ms(), start) / 1000
        print(f"\n✓ Done in {elapsed:.1f}s")
        print(f"  Avg: {bytes_played/elapsed/1024:.0f} KB/s")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import sys
        sys.print_exception(e)


# ================ تست سرعت ==================

def test_speed(path):
    """تست سرعت خواندن SD"""
    
    print(f"\n🔬 Speed Test: {path}")
    print("="*50)
    
    try:
        with open(path, "rb") as f:
            f.read(44)  # هدر
            
            # تست با chunk های مختلف
            for chunk_size in [1024, 2048, 4096, 8192]:
                f.seek(44)
                
                total = 0
                start = time.ticks_us()
                
                # خواندن 200KB
                while total < 204800:
                    data = f.read(chunk_size)
                    if not data:
                        break
                    total += len(data)
                
                elapsed = time.ticks_diff(time.ticks_us(), start)
                speed = total / (elapsed / 1000)  # KB/s
                
                print(f"  Chunk {chunk_size:4d}: {speed:6.0f} KB/s")
        
        print("\n💡 Need > 172 KB/s for smooth 44.1kHz stereo")
        
    except Exception as e:
        print(f"✗ Error: {e}")


# ================ اجرای خودکار ==================

# فایل برای پخش
FILE = "/sd/LastNight_44100_2.wav"

# اول تست سرعت
print("\n" + "="*50)
test_speed(FILE)

# سپس پخش
print("\n" + "="*50)
play_simple(FILE)

print("\n✅ All done!")
print("="*50)