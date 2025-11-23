# from pydub import AudioSegment

# def convert_mp3_for_esp32(input_mp3, output_wav):
#     from pydub import AudioSegment

#     audio = AudioSegment.from_mp3(input_mp3)

#     # 🔹 کیفیت CD — بهترین حالت پایدار برای ESP32
#     audio = audio.set_frame_rate(44100)   # یا 48000
#     audio = audio.set_channels(2)         # استریو
#     audio = audio.set_sample_width(2)     # 16-bit

#     audio.export(output_wav, format="wav")

#     print("Done!")
#     print("Saved:", output_wav)


# # مثال:
# # convert_mp3_for_esp32(
# #     "01. Narvent - Fainted (You’re Wonderful).mp3", 
# #     "output.wav")
# convert_mp3_for_esp32(
#     "Last Night.mp3", 
#     "LastNight_44100_2.wav")


from pydub import AudioSegment

def convert_mp3_for_esp32(input_mp3, output_wav):
    # MP3 را بخوان
    audio = AudioSegment.from_mp3(input_mp3)

    # تنظیمات با کیفیت دوبرابر بهتر
    audio = audio.set_frame_rate(32000)   # 32kHz (دوبرابر 16kHz)
    audio = audio.set_channels(1)         # مونو
    audio = audio.set_sample_width(2)     # 16-bit (2 bytes per sample)

    # خروجی WAV استاندارد PCM
    audio.export(output_wav, format="wav")

    print("✅ Done!")
    print(f"   Saved: {output_wav}")
    print(f"   Format: 32kHz Mono 16-bit")
    print(f"   Bitrate: 512 kbps (32000 × 1 × 16)")

# اجرا
convert_mp3_for_esp32(
    "Last Night.mp3", 
    "LastNight3.wav"
)