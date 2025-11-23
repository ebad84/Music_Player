# smart_player.py - تشخیص خودکار تنظیمات فایل و تنظیم I2S

from machine import I2S, Pin, SPI
import os
import gc

print("\n" + "="*50)
print("Smart Audio Player")
print("Auto-detect file settings")
print("="*50 + "\n")

# ================ راه‌اندازی SD Card ==================
print("📂 SD Card...")
try:
    import sdcard
    
    spi = SPI(1,
              baudrate=10000000,
              polarity=0,
              phase=0,
              sck=Pin(18),
              mosi=Pin(23),
              miso=Pin(19))
    
    sd = sdcard.SDCard(spi, Pin(5))
    
    try:
        os.umount("/sd")
    except:
        pass
    
    os.mount(sd, "/sd")
    print("✓ SD mounted\n")
    
except Exception as e:
    print(f"✗ SD Error: {e}")
    import sys
    sys.exit()


# ================ تابع استخراج اطلاعات فایل ==================
def get_wav_info(path):
    """خواندن اطلاعات از هدر WAV"""
    try:
        with open(path, "rb") as f:
            header = f.read(44)
            
            # استخراج اطلاعات از هدر WAV
            sample_rate = int.from_bytes(header[24:28], 'little')
            channels = int.from_bytes(header[22:24], 'little')
            bit_depth = int.from_bytes(header[34:36], 'little')
            
            return {
                'sample_rate': sample_rate,
                'channels': channels,
                'bit_depth': bit_depth
            }
    except Exception as e:
        print(f"✗ Error reading file: {e}")
        return None


# ================ پخش هوشمند ==================
def play_smart(path):
    """
    پخش فایل با تشخیص خودکار تنظیمات
    I2S را بر اساس فایل تنظیم می‌کند
    """
    
    print(f"▶️  {path}")
    print("="*50)
    
    # 1. خواندن اطلاعات فایل
    info = get_wav_info(path)
    
    if not info:
        print("✗ Cannot read file info")
        return False
    
    sample_rate = info['sample_rate']
    channels = info['channels']
    bit_depth = info['bit_depth']
    
    print(f"📊 File detected:")
    print(f"   Sample rate: {sample_rate} Hz")
    print(f"   Channels: {channels} ({'Mono' if channels == 1 else 'Stereo'})")
    print(f"   Bit depth: {bit_depth} bit")
    print()
    
    # 2. تنظیم I2S بر اساس فایل
    print(f"🔧 Configuring I2S...")
    
    try:
        # تعیین فرمت I2S
        if channels == 1:
            i2s_format = I2S.MONO
        elif channels == 2:
            i2s_format = I2S.STEREO
        else:
            print(f"✗ Unsupported channel count: {channels}")
            return False
        
        # ساخت I2S با تنظیمات فایل
        audio_out = I2S(
            0,
            sck=Pin(26),
            ws=Pin(25),
            sd=Pin(22),
            mode=I2S.TX,
            bits=bit_depth,           # 🔥 از فایل
            format=i2s_format,        # 🔥 از فایل
            rate=sample_rate,         # 🔥 از فایل
            ibuf=20480
        )
        
        print(f"✓ I2S configured: {sample_rate}Hz, {channels}ch, {bit_depth}bit")
        print()
        
    except Exception as e:
        print(f"✗ I2S Error: {e}")
        return False
    
    # 3. پخش فایل
    print("🎵 Playing...")
    
    gc.collect()
    
    try:
        f = open(path, "rb")
        f.read(44)  # رد شدن از هدر
        
        file_size = os.stat(path)[6] - 44
        
        CHUNK = 4096
        played = 0
        
        while True:
            chunk = f.read(CHUNK)
            if not chunk:
                break
            
            audio_out.write(chunk)
            played += len(chunk)
            
            # گزارش هر 100KB
            if played % 102400 < CHUNK:
                percent = played * 100 / file_size
                print(f"  {percent:.0f}% ({played/1024:.0f}KB)")
        
        f.close()
        
        print()
        print("✓ Playback finished!")
        
        # deinit I2S برای پخش بعدی
        audio_out.deinit()
        
        return True
        
    except Exception as e:
        print(f"\n✗ Playback error: {e}")
        import sys
        sys.print_exception(e)
        return False


# ================ پخش Playlist ==================
def play_playlist(folder="/sd"):
    """پخش تمام فایل‌های WAV با تنظیمات خودکار"""
    
    files = [f for f in os.listdir(folder) if f.endswith('.wav')]
    
    if not files:
        print("✗ No WAV files found")
        return
    
    print(f"🎵 Found {len(files)} files\n")
    
    for i, filename in enumerate(files, 1):
        filepath = f"{folder}/{filename}"
        
        print(f"\n[{i}/{len(files)}] {filename}")
        print("-" * 50)
        
        play_smart(filepath)
        
        print()
    
    print("✅ Playlist complete!")


# ================ نمایش لیست فایل‌ها ==================
def list_files(folder="/sd"):
    """نمایش فایل‌های WAV با اطلاعات"""
    
    print("📁 Available files:")
    print("="*50)
    
    files = [f for f in os.listdir(folder) if f.endswith('.wav')]
    
    if not files:
        print("  (no WAV files)")
        return
    
    for filename in files:
        filepath = f"{folder}/{filename}"
        
        try:
            size = os.stat(filepath)[6]
            info = get_wav_info(filepath)
            
            if info:
                print(f"\n🎵 {filename}")
                print(f"   Size: {size/1024:.0f}KB")
                print(f"   {info['sample_rate']}Hz, {info['channels']}ch, {info['bit_depth']}bit")
        except:
            print(f"\n? {filename}")
    
    print("\n" + "="*50 + "\n")


# ================ اجرای خودکار ==================

# نمایش فایل‌های موجود
list_files()

# پخش یک فایل
play_smart("/sd/LastNight3.wav")

# یا پخش همه فایل‌ها:
# play_playlist("/sd")

print("\n" + "="*50)