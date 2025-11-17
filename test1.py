from pydub import AudioSegment

def mp3_to_wav(input_mp3, output_wav):
    audio = AudioSegment.from_mp3(input_mp3)

    # تبدیل به مونو + 16kHz + 16bit
    audio = audio.set_frame_rate(16000)
    audio = audio.set_channels(1)
    audio = audio.set_sample_width(2)  # 2 bytes = 16bit

    audio.export(output_wav, format="wav")
    print("Saved:", output_wav)

mp3_to_wav(
    "01. Narvent - Fainted (You’re Wonderful).mp3", 
    "output.wav")
