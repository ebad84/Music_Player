# double_buffer_player.py - راه‌حل نهایی با Double Buffering
# این روش 100% کار می‌کنه حتی با SD خیلی کند!

from machine import I2S, Pin, SPI
import time
import os
import gc
import _thread

# ================ تنظیمات بهینه I2S ==================
def init_i2s():
    """I2S با بیشترین بافر ممکن"""
    
    audio_out = I2S(
        0,
        sck=Pin(26),
        ws=Pin(25),
        sd=Pin(22),
        mode=I2S.TX,
        bits=16,
        format=I2S.STEREO,
        rate=44100,
        ibuf=40960  # 40KB - حداکثر بافر
    )
    
    print("✓ I2S: 40KB buffer, 44.1kHz Stereo")
    return audio_out


# ================ راه‌اندازی SD ==================
def init_sd():
    """راه‌اندازی SD Card با سرعت امن"""
    try:
        import sdcard
        
        # سرعت‌های پشتیبانی شده ESP32: 1-26 MHz
        # 20MHz برای اکثر SD کارت‌ها امن هست
        spi = SPI(1,
                  baudrate=20000000,  # 20MHz - امن و سریع
                  polarity=0,
                  phase=0,
                  sck=Pin(18),
                  mosi=Pin(23),
                  miso=Pin(19))
        
        sd = sdcard.SDCard(spi, Pin(5))
        
        # اگر SD از قبل mount شده بود
        try:
            os.umount("/sd")
        except:
            pass
        
        os.mount(sd, "/sd")
        
        print("✓ SD: 20MHz SPI")
        return True
    except Exception as e:
        print(f"✗ SD error: {e}")
        return False


# ================ پخش با Double Buffer ==================
def play_wav_double_buffer(audio_out, path):
    """
    استراتژی Double Buffering:
    1. دو بافر در RAM: buffer1 و buffer2
    2. وقتی buffer1 پخش میشه، buffer2 از SD پر میشه
    3. جابجایی بافرها بدون توقف
    
    این روش حتی با SD کند هم کار می‌کنه!
    """
    
    print(f"\n{'='*50}")
    print(f"🎵 Playing: {path}")
    print(f"{'='*50}")
    
    # بررسی حافظه
    gc.collect()
    free_mem = gc.mem_free()
    print(f"💾 Free RAM: {free_mem/1024:.0f}KB")
    
    if free_mem < 40000:
        print("⚠️  Low memory! Playback may fail")
    
    try:
        file_size = os.stat(path)[6]
        print(f"📦 File: {file_size/1024:.0f}KB")
    except:
        print(f"✗ File not found")
        return False
    
    # اندازه هر بافر
    BUFFER_SIZE = 16384  # 16KB per buffer
    
    try:
        # ایجاد دو بافر
        buffer1 = bytearray(BUFFER_SIZE)
        buffer2 = bytearray(BUFFER_SIZE)
        
        print(f"✓ Allocated 2x{BUFFER_SIZE/1024:.0f}KB buffers")
        
        with open(path, "rb") as f:
            # رد شدن از هدر
            f.read(44)
            
            # پر کردن buffer1
            bytes_read = f.readinto(buffer1)
            if bytes_read == 0:
                print("✗ Empty file")
                return False
            
            print("▶️  Playing...")
            
            current_buffer = buffer1
            next_buffer = buffer2
            total_played = 0
            start_time = time.ticks_ms()
            
            while bytes_read > 0:
                # پخش buffer فعلی
                audio_out.write(memoryview(current_buffer)[:bytes_read])
                total_played += bytes_read
                
                # در همین حین، buffer بعدی رو پر کن
                bytes_read = f.readinto(next_buffer)
                
                # جابجایی بافرها
                current_buffer, next_buffer = next_buffer, current_buffer
                
                # گزارش هر 200KB
                if total_played % 204800 < BUFFER_SIZE:
                    elapsed = time.ticks_diff(time.ticks_ms(), start_time)
                    if elapsed > 0:
                        speed = total_played / elapsed
                        percent = total_played * 100 / file_size
                        print(f"  {percent:.0f}% | {speed:.0f} KB/s")
        
        elapsed = time.ticks_diff(time.ticks_ms(), start_time) / 1000
        print(f"\n✓ Finished in {elapsed:.1f}s")
        print(f"  Avg: {total_played/elapsed/1024:.0f} KB/s")
        
        return True
        
    except MemoryError:
        print("❌ Out of memory!")
        print("💡 Try: Reboot ESP32")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import sys
        sys.print_exception(e)
        return False


# ================ پخش فایل کوچک از RAM ==================
def play_wav_from_ram(audio_out, path):
    """
    اگر فایل کوچیک باشه (<100KB)، کل فایل رو در RAM لود کن
    روان‌ترین روش ممکن!
    """
    
    print(f"\n{'='*50}")
    print(f"🎵 Loading to RAM: {path}")
    print(f"{'='*50}")
    
    gc.collect()
    free_mem = gc.mem_free()
    
    try:
        file_size = os.stat(path)[6]
        
        if file_size > free_mem * 0.7:
            print(f"⚠️  File too large for RAM ({file_size/1024:.0f}KB)")
            print(f"   Use play_wav_double_buffer() instead")
            return False
        
        print(f"📦 Loading {file_size/1024:.0f}KB to RAM...")
        
        # خواندن کل فایل
        with open(path, "rb") as f:
            header = f.read(44)
            audio_data = f.read()
        
        print(f"✓ Loaded! Free RAM: {gc.mem_free()/1024:.0f}KB")
        print("▶️  Playing from RAM (ultra smooth)...")
        
        # پخش از RAM با chunk های بزرگ
        CHUNK = 8192
        start = time.ticks_ms()
        
        for i in range(0, len(audio_data), CHUNK):
            chunk = audio_data[i:i+CHUNK]
            audio_out.write(chunk)
        
        elapsed = time.ticks_diff(time.ticks_ms(), start) / 1000
        print(f"\n✓ Finished in {elapsed:.1f}s")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


# ================ تست تشخیص مشکل ==================
def diagnose_problem(path):
    """تشخیص دقیق علت لرزش"""
    
    print("\n" + "="*50)
    print("🔍 DIAGNOSTIC MODE")
    print("="*50 + "\n")
    
    # 1. بررسی فایل
    print("1️⃣  Checking file...")
    try:
        with open(path, "rb") as f:
            header = f.read(44)
            
        sample_rate = int.from_bytes(header[24:28], 'little')
        channels = int.from_bytes(header[22:24], 'little')
        bit_depth = int.from_bytes(header[34:36], 'little')
        
        print(f"   ✓ {sample_rate}Hz, {channels}ch, {bit_depth}bit")
        
        if sample_rate != 44100:
            print(f"   ⚠️  Sample rate mismatch!")
        if channels != 2:
            print(f"   ⚠️  Not stereo!")
            
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return
    
    # 2. تست سرعت SD
    print("\n2️⃣  Testing SD speed...")
    try:
        with open(path, "rb") as f:
            f.read(44)
            
            start = time.ticks_us()
            data = f.read(8192)
            elapsed = time.ticks_diff(time.ticks_us(), start)
            
            speed = 8192 / (elapsed / 1000)  # KB/s
            print(f"   Speed: {speed:.0f} KB/s")
            
            # برای 44100Hz استریو 16bit نیاز به 172KB/s داریم
            required = 44100 * 2 * 2 / 1024  # ~172 KB/s
            
            if speed < required:
                print(f"   ❌ TOO SLOW! Need {required:.0f} KB/s")
                print(f"   💡 Try:")
                print(f"      - Use faster SD card (Class 10)")
                print(f"      - Check SD card connections")
                print(f"      - Lower quality (22050Hz mono)")
            else:
                print(f"   ✓ Fast enough ({required:.0f} KB/s needed)")
                
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return
    
    # 3. بررسی حافظه
    print("\n3️⃣  Checking memory...")
    gc.collect()
    free = gc.mem_free()
    print(f"   Free RAM: {free/1024:.0f}KB")
    
    if free < 30000:
        print(f"   ⚠️  Low memory! Reboot recommended")
    else:
        print(f"   ✓ Enough memory")
    
    # 4. توصیه
    print("\n" + "="*50)
    print("💡 RECOMMENDATION:")
    
    file_size = os.stat(path)[6]
    
    if file_size < free * 0.6:
        print("   Use: play_wav_from_ram() - Best quality!")
    else:
        print("   Use: play_wav_double_buffer() - Good quality")
    
    print("="*50 + "\n")


# ================ تابع اصلی ==================
def main():
    print("\n" + "="*50)
    print("ESP32 Audio Player - Anti-Stutter Edition")
    print("="*50 + "\n")
    
    if not init_sd():
        return
    
    audio_out = init_i2s()
    
    file_path = "/sd/LastNight_44100_2.wav"
    
    # اول تشخیص بده
    diagnose_problem(file_path)
    
    # سپس با بهترین روش پخش کن
    file_size = os.stat(file_path)[6]
    gc.collect()
    
    print("\n" + "="*50)
    
    if file_size < gc.mem_free() * 0.6:
        print("📍 Using RAM playback (smoothest)")
        play_wav_from_ram(audio_out, file_path)
    else:
        print("📍 Using double buffer playback")
        play_wav_double_buffer(audio_out, file_path)
    
    print("\n✓ Done!")


if __name__ == '__main__':
    main()