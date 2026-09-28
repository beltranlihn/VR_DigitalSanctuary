import math
import os
import struct
import sys
import wave

SR = 48000
A2, A3, E4, A4, A5 = 110.0, 220.0, 329.63, 440.0, 880.0


def smooth(x):
    return x * x * (3.0 - 2.0 * x)


def env(n, i, fin, fout):
    t = i / SR
    total = n / SR
    a = 1.0
    if t < fin:
        a = 0.5 - 0.5 * math.cos(math.pi * t / fin)
    if t > total - fout:
        a = min(a, 0.5 - 0.5 * math.cos(math.pi * max(total - t, 0.0) / fout))
    return a


def write(path, samples):
    peak = max(abs(s) for s in samples)
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(b"".join(struct.pack("<h", int(max(-1.0, min(1.0, s)) * 32767)) for s in samples))
    print(os.path.basename(path), f"{len(samples) / SR:.2f}s peak {peak:.3f}")


def glide(dur, f0, f1, amp, fin=0.35, fout=0.6):
    n = int(dur * SR)
    ph = ph_sub = 0.0
    out = []
    for i in range(n):
        f = f0 * (f1 / f0) ** smooth(i / (n - 1))
        ph += 2.0 * math.pi * f / SR
        ph_sub += 2.0 * math.pi * f * 0.5 / SR
        s = math.sin(ph) + 0.15 * math.sin(2.0 * ph) + 0.3 * math.sin(ph_sub)
        out.append(s / 1.45 * amp * env(n, i, fin, fout))
    return out


def hold(dur, amp, fin=0.35, fout=0.6):
    n = int(dur * SR)
    out = []
    for i in range(n):
        t = i / SR
        s = (math.sin(2 * math.pi * A3 * t) + 0.6 * math.sin(2 * math.pi * E4 * t)
             + 0.25 * math.sin(2 * math.pi * A2 * t))
        out.append(s / 1.85 * amp * env(n, i, fin, fout))
    return out


def pulse(dur, amp):
    n = int(dur * SR)
    out = []
    for i in range(n):
        t = i / SR
        att = min(t / 0.004, 1.0)
        dec = math.exp(-t / 0.09)
        s = math.sin(2 * math.pi * A4 * t) + 0.25 * math.sin(2 * math.pi * A5 * t) * math.exp(-t / 0.04)
        out.append(s / 1.25 * amp * att * dec)
    return out


if __name__ == "__main__":
    dest = sys.argv[1]
    inhale, hold_t, exhale = float(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4])
    os.makedirs(dest, exist_ok=True)
    write(os.path.join(dest, "SND_PacerPulse.wav"), pulse(0.45, 0.16))
    write(os.path.join(dest, "SND_PacerInhale.wav"), glide(inhale, A3, E4, 0.2))
    write(os.path.join(dest, "SND_PacerHold.wav"), hold(hold_t, 0.14))
    write(os.path.join(dest, "SND_PacerExhale.wav"), glide(exhale, E4, A3, 0.2))
