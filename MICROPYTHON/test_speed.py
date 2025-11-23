# sd_speed_test.py - تست سرعت SD Card
# اول این رو اجرا کن ببینیم SD چقدر سریعه

from machine import SPI, Pin
import time
import os

def test_sd_speed():
    """تست سرعت خواندن از SD Card"""
    
    print("\n" + "="*50)
    print("🔬 SD Card Speed Test")
    print("="*50 + "\n")
    
    # راه‌اندازی SD با سرعت‌های مختلف
    baudrates = [10000000, 20000000, 40000000]
    
    for baudrate in baudrates:
        try:
            print(f"\n📊 Testing at {baudrate/1000000}MHz...")
            
            import sdcard
            
            spi = SPI(1,
                      baudrate=baudrate,
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
            
            # پیدا کردن یک فایل برای تست
            files = [f for f in os.listdir("/sd") if f.endswith('.wav')]
            if not files:
                print("  ❌ No WAV file found")
                continue
            
            test_file = f"/sd/{files[0]}"
            file_size = os.stat(test_file)[6]
            
            print(f"  File: {files[0]} ({file_size/1024:.0f}KB)")
            
            # تست خواندن
            with open(test_file, "rb") as f:
                chunk_sizes = [512, 1024, 2048, 4096, 8192]
                
                for chunk_size in chunk_sizes:
                    f.seek(44)  # رد شدن از هدر
                    
                    bytes_read = 0
                    chunks = 0
                    start = time.ticks_ms()
                    
                    # خواندن 500KB برای تست
                    while bytes_read < 512000 and bytes_read < file_size - 44:
                        data = f.read(chunk_size)
                        if not data:
                            break
                        bytes_read += len(data)
                        chunks += 1
                    
                    elapsed = time.ticks_diff(time.ticks_ms(), start)
                    
                    if elapsed > 0:
                        speed = bytes_read / elapsed  # bytes per ms = KB/s
                        print(f"    Chunk {chunk_size:5d}: {speed:.0f} KB/s ({chunks} chunks)")
            
            print(f"  ✓ Test complete")
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    print("\n" + "="*50)
    print("💡 Good speed: > 150 KB/s")
    print("💡 For 44100Hz stereo 16-bit: Need ~172 KB/s minimum")
    print("="*50 + "\n")


if __name__ == '__main__':
    test_sd_speed()