import struct, math

def create_tiny_wav():
    filename = "tiny.wav"
    rate = 16000
    duration = 0.5  # نیم ثانیه
    samples = int(rate * duration)
    amp = 8000

    with open(filename, "wb") as f:
        # RIFF header
        f.write(b"RIFF")
        f.write(struct.pack("<I", 36 + samples * 2))
        f.write(b"WAVE")

        # fmt chunk
        f.write(b"fmt ")
        f.write(struct.pack("<I", 16))
        f.write(struct.pack("<H", 1))     # PCM
        f.write(struct.pack("<H", 1))     # MONO
        f.write(struct.pack("<I", rate))
        f.write(struct.pack("<I", rate * 2))
        f.write(struct.pack("<H", 2))
        f.write(struct.pack("<H", 16))    # 16bit

        # data chunk
        f.write(b"data")
        f.write(struct.pack("<I", samples * 2))

        # samples
        for n in range(samples):
            sample = int(amp * math.sin(2 * math.pi * 440 * (n / rate)))
            f.write(struct.pack("<h", sample))

    print("tiny.wav ساخته شد! حجم حدود 16KB")

create_tiny_wav()
