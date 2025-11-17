from pydub import AudioSegment

def convert_mp3_for_esp32(input_mp3, output_wav):
    # MP3 را بخوان
    audio = AudioSegment.from_mp3(input_mp3)

    # تنظیمات دقیق سازگار با ESP32
    audio = audio.set_frame_rate(16000)   # نرخ نمونه‌برداری
    audio = audio.set_channels(1)         # مونو
    audio = audio.set_sample_width(2)     # 16-bit (2 bytes per sample)

    # خروجی WAV استاندارد PCM
    audio.export(output_wav, format="wav")

    print("Done!")
    print("Saved:", output_wav)

# مثال:
convert_mp3_for_esp32("input.mp3", "output.wav")
