# player_optimized.py - پخش WAV بدون لرزش
# حل مشکل Buffer Underrun با تنظیمات بهینه

from machine import I2S, Pin, SPI
import time
import os
import gc

# ================ تنظیمات I2S با بافرهای بزرگتر ==================
def init_i2s_optimized():
    """
    راه‌اندازی I2S با تنظیمات بهینه برای جلوگیری از لرزش
    
    کلید حل مشکل:
    1. ibuf بزرگ‌تر = بافر داخلی بیشتر
    2. خواندن chunk های بزرگ‌تر از SD
    3. پیش‌بارگذاری بافر قبل از شروع پخش
    """
    
    audio_out = I2S(
        0,
        sck=Pin(26),                 # BCLK
        ws=Pin(25),                  # LRCLK  
        sd=Pin(22),                  # DIN
        mode=I2S.TX,
        bits=16,
        format=I2S.STEREO,
        rate=44100,
        ibuf=20480                   # 🔥 20KB به جای 4KB = کلید حل مشکل!
    )
    
    print("✓ I2S initialized (Optimized)")
    print(f"  Internal buffer: 20KB")
    print(f"  Format: 16-bit Stereo @ 44.1kHz")
    
    return audio_out


# ================ راه‌اندازی SD Card با سرعت بالاتر ================
def init_sd_card_fast():
    """راه‌اندازی SD با baudrate بالاتر"""
    try:
        import sdcard
        
        # 🔥 20MHz به جای 10MHz
        spi = SPI(1,
                  baudrate=20000000,     # دو برابر سریع‌تر!
                  polarity=0,
                  phase=0,
                  sck=Pin(18),
                  mosi=Pin(23),
                  miso=Pin(19))
        
        sd = sdcard.SDCard(spi, Pin(5))
        os.mount(sd, "/sd")
        
        print("✓ SD Card mounted (Fast mode: 20MHz)")
        
        files = os.listdir("/sd")
        print(f"  Files: {len(files)}")
        
        return True
        
    except Exception as e:
        print(f"✗ SD Card error: {e}")
        return False


# ================ پخش بدون لرزش ================
def play_wav_smooth(audio_out, path):
    """
    پخش روان بدون قطع و وصل
    
    تکنیک‌های کلیدی:
    1. Chunk بزرگ (8KB)
    2. پیش‌بارگذاری بافر
    3. GC قبل از شروع
    4. خواندن سریع از SD
    """
    
    print(f"\n{'='*50}")
    print(f"🎵 Playing: {path}")
    print(f"{'='*50}")
    
    # 🔥 پاک کردن حافظه قبل از شروع
    gc.collect()
    print(f"💾 Free memory: {gc.mem_free()} bytes")
    
    try:
        file_size = os.stat(path)[6]
        print(f"📦 File size: {file_size:,} bytes")
    except:
        print(f"✗ File not found: {path}")
        return False
    
    try:
        with open(path, "rb") as f:
            # رد شدن از هدر
            header = f.read(44)
            
            # استخراج اطلاعات
            if len(header) >= 44:
                sample_rate = int.from_bytes(header[24:28], 'little')
                channels = int.from_bytes(header[22:24], 'little')
                bit_depth = int.from_bytes(header[34:36], 'little')
                
                print(f"📊 {sample_rate}Hz, {channels}ch, {bit_depth}bit")
                
                if sample_rate != 44100 or channels != 2:
                    print(f"⚠️  Warning: File format mismatch!")
            
            # 🔥 پیش‌بارگذاری بافر (Pre-buffering)
            # این خیلی مهمه! قبل از شروع پخش، بافر I2S رو پر می‌کنیم
            print("⏳ Pre-buffering...")
            prebuffer_size = 16384  # 16KB
            prebuffer = f.read(prebuffer_size)
            audio_out.write(prebuffer)
            print("✓ Buffer ready")
            
            # 🔥 اندازه chunk بزرگ‌تر = خواندن کمتر از SD = روان‌تر
            CHUNK_SIZE = 8192  # 8KB به جای 1KB
            
            print(f"▶️  Playing... (chunk: {CHUNK_SIZE} bytes)")
            
            bytes_played = prebuffer_size
            start_time = time.time()
            last_report = 0
            
            while True:
                # خواندن chunk بزرگ
                data = f.read(CHUNK_SIZE)
                
                if not data:
                    break
                
                # نوشتن به I2S (بدون delay!)
                audio_out.write(data)
                bytes_played += len(data)
                
                # گزارش هر 200KB
                if bytes_played - last_report > 204800:
                    percent = (bytes_played / file_size) * 100
                    elapsed = time.time() - start_time
                    rate = bytes_played / elapsed / 1024
                    print(f"  {percent:.0f}% | {rate:.0f} KB/s")
                    last_report = bytes_played
            
            # آمار نهایی
            elapsed = time.time() - start_time
            avg_rate = bytes_played / elapsed / 1024
            
            print(f"\n✓ Finished!")
            print(f"  Time: {elapsed:.1f}s")
            print(f"  Avg rate: {avg_rate:.0f} KB/s")
            print(f"  Free memory: {gc.mem_free()} bytes")
            print(f"{'='*50}\n")
            
            return True
            
    except MemoryError:
        print(f"\n❌ Out of memory!")
        print(f"💡 Try rebooting ESP32")
        return False
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import sys
        sys.print_exception(e)
        return False


# ================ پخش Playlist روان ================
def play_playlist_smooth(audio_out, folder="/sd"):
    """پخش playlist بدون لرزش"""
    
    files = [f for f in os.listdir(folder) if f.endswith('.wav')]
    
    if not files:
        print(f"✗ No WAV files in {folder}")
        return
    
    print(f"\n🎵 Playlist: {len(files)} songs")
    print("=" * 50)
    
    for i, filename in enumerate(files, 1):
        print(f"\n[{i}/{len(files)}] {filename}")
        
        # پاک کردن حافظه قبل از هر آهنگ
        gc.collect()
        
        filepath = f"{folder}/{filename}"
        play_wav_smooth(audio_out, filepath)
        
        # وقفه کوتاه
        time.sleep(0.5)
    
    print("\n✓ Playlist complete!")


# ================ حالت Debug ================
def play_wav_debug(audio_out, path):
    """
    حالت Debug برای یافتن مشکلات
    نمایش دقیق تایمینگ خواندن و نوشتن
    """
    
    print(f"\n🔍 DEBUG MODE: {path}")
    print("=" * 50)
    
    with open(path, "rb") as f:
        f.read(44)  # هدر
        
        CHUNK_SIZE = 8192
        chunks_read = 0
        total_read_time = 0
        total_write_time = 0
        
        for _ in range(10):  # فقط 10 chunk برای تست
            # زمان خواندن
            t1 = time.ticks_us()
            data = f.read(CHUNK_SIZE)
            t2 = time.ticks_us()
            read_time = time.ticks_diff(t2, t1)
            
            if not data:
                break
            
            # زمان نوشتن
            t1 = time.ticks_us()
            audio_out.write(data)
            t2 = time.ticks_us()
            write_time = time.ticks_diff(t2, t1)
            
            chunks_read += 1
            total_read_time += read_time
            total_write_time += write_time
            
            print(f"Chunk {chunks_read}:")
            print(f"  Read:  {read_time/1000:.1f}ms")
            print(f"  Write: {write_time/1000:.1f}ms")
            print(f"  Ratio: {write_time/read_time:.1f}x")
    
    if chunks_read > 0:
        avg_read = total_read_time / chunks_read / 1000
        avg_write = total_write_time / chunks_read / 1000
        
        print(f"\n📊 Average:")
        print(f"  Read:  {avg_read:.1f}ms")
        print(f"  Write: {avg_write:.1f}ms")
        
        # تشخیص مشکل
        if avg_read > avg_write:
            print(f"\n⚠️  SD Card is TOO SLOW!")
            print(f"   Try: Higher SPI baudrate")
        elif avg_write > avg_read * 2:
            print(f"\n⚠️  I2S buffer filling too fast!")
            print(f"   Try: Larger ibuf parameter")
        else:
            print(f"\n✓ Timing looks OK")


# ================ تابع اصلی ================
def main():
    """راه‌اندازی و پخش بهینه"""
    
    print("\n" + "=" * 50)
    print("ESP32 Smooth Audio Player")
    print("No stuttering, no gaps!")
    print("=" * 50 + "\n")
    
    # راه‌اندازی SD با سرعت بالا
    if not init_sd_card_fast():
        print("⛔ Cannot continue")
        return
    
    # راه‌اندازی I2S با بافر بزرگ
    audio_out = init_i2s_optimized()
    
    print("\n" + "=" * 50)
    
    # === حالت 1: پخش عادی ===
    play_wav_smooth(audio_out, "/sd/LastNight_44100_2.wav")
    
    # === حالت 2: Debug ===
    # play_wav_debug(audio_out, "/sd/LastNight_44100_2.wav")
    
    # === حالت 3: Playlist ===
    # play_playlist_smooth(audio_out, "/sd")
    
    print("\n✓ All done!")


# ================ اجرا ================
if __name__ == '__main__':
    main()