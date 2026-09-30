# -*- coding: utf-8 -*-
"""make_mind_sounds.py - sonidos de la celula de Mind (Loving): APARECE y SE VA (2026-09-30).

Estandar de Beltran para la noche: "experiencia high end... toda entrada y salida con curva, con sonido".
Familia sonora del proyecto (medida en Recursos/Audio Calibration): La mayor con 6a y 7a (Pad: A2 E3 A3 C#4 F#4 G#4;
Inicio: La add9). Aca:
  SND_MindAppear (3,4 s) - "floracion acuosa": soplo de agua (ruido rosa en banda que sube 700 -> 2400 Hz) + acorde
      La add9 (A3 E4 B4 C#5 E5) que entra en arpegio ascendente (0,12 s entre voces), cada voz = dos senos desafinados
      +-2,5 cents abiertos en estereo + 2o armonico suave; vibrato leve despues del ataque; unas gotas de cristal
      (A6 E6 B6 C#7) que caen un poco de altura.
  SND_MindVanish (3,2 s) - "floracion al reves": inhalacion de anticipacion (banda que sube 500 -> 1800 Hz en 0,9 s,
      sincronizada con la hinchazon del 5 % de StageOutro), el acorde sostenido que se DISUELVE de agudo a grave
      hundiendose 0,6 semitonos, y un soplo de aire que se cierra.
Todas las curvas son suaves (smootherstep / exponenciales), sin clics: 10 ms de entrada y 150 ms de salida a cero exacto.
48 kHz, 16 bits, estereo (se reproducen 2D con PlaySound2D). Pico normalizado a 0,28.
Uso: python make_mind_sounds.py <carpeta_salida>
"""
import os
import sys
import wave
import numpy as np

SR = 48000
RNG = np.random.default_rng(2930)


def smoother(x):
    x = np.clip(x, 0.0, 1.0)
    return x * x * x * (x * (x * 6.0 - 15.0) + 10.0)


def pink(n):
    # ruido rosa por el filtro de Paul Kellet sobre ruido blanco
    w = RNG.standard_normal(n)
    b = np.zeros(7)
    out = np.empty(n)
    for i in range(n):
        x = w[i]
        b[0] = 0.99886 * b[0] + x * 0.0555179
        b[1] = 0.99332 * b[1] + x * 0.0750759
        b[2] = 0.96900 * b[2] + x * 0.1538520
        b[3] = 0.86650 * b[3] + x * 0.3104856
        b[4] = 0.55000 * b[4] + x * 0.5329522
        b[5] = -0.7616 * b[5] - x * 0.0168980
        out[i] = b[0] + b[1] + b[2] + b[3] + b[4] + b[5] + b[6] + x * 0.5362
        b[6] = x * 0.115926
    return out / np.max(np.abs(out))


def band_sweep(x, fc_of_t, octaves=1.0):
    """Filtro pasabanda que se mueve en el tiempo: STFT (Hann, 75 %) con una ventana gaussiana en log-frecuencia."""
    N, H = 2048, 512
    win = np.hanning(N)
    pad = np.concatenate([np.zeros(N), x, np.zeros(N)])
    out = np.zeros_like(pad)
    norm = np.zeros_like(pad)
    f = np.fft.rfftfreq(N, 1.0 / SR)
    lf = np.log2(np.maximum(f, 1.0))
    for s in range(0, len(pad) - N, H):
        t = (s + N / 2 - N) / SR
        fc = fc_of_t(max(t, 0.0))
        m = np.exp(-0.5 * ((lf - np.log2(fc)) / (octaves * 0.5)) ** 2)
        X = np.fft.rfft(pad[s:s + N] * win)
        out[s:s + N] += np.fft.irfft(X * m, N) * win
        norm[s:s + N] += win * win
    out = out / np.maximum(norm, 1e-6)
    return out[N:N + len(x)]


def voice(t, f0, t0, att, dec_tau, amp, detune_c=2.5, vib_c=3.0, drift_semi=None, fade_end=None):
    """Una voz: dos senos desafinados abiertos en estereo + 2o armonico, ataque smootherstep, caida exponencial."""
    tt = t - t0
    on = tt >= 0
    env = np.where(on, smoother(tt / att) * np.exp(-np.maximum(tt - att, 0.0) / dec_tau), 0.0)
    if fade_end is not None:
        env = env * (1.0 - smoother((t - fade_end[0]) / (fade_end[1] - fade_end[0])))
    vib = 1.0 + (2 ** (vib_c / 1200.0) - 1.0) * np.sin(2 * np.pi * 4.6 * t) * smoother((tt - att) / 0.6)
    drift = 1.0 if drift_semi is None else 2 ** (drift_semi(t) / 12.0)
    L = np.zeros_like(t)
    R = np.zeros_like(t)
    for side, c in ((0, -detune_c), (1, +detune_c)):
        f = f0 * 2 ** (c / 1200.0) * vib * drift
        ph = 2 * np.pi * np.cumsum(f) / SR
        s = np.sin(ph) + 0.12 * np.sin(2 * ph + 0.7)
        if side == 0:
            L += s
        else:
            R += s
    return np.stack([L, R], 1) * (amp * env)[:, None]


def ping(t, f0, t0, amp, pan):
    tt = t - t0
    env = np.where(tt >= 0, smoother(tt / 0.006) * np.exp(-np.maximum(tt, 0.0) / 0.18), 0.0)
    f = f0 * 2 ** (-30.0 / 1200.0 * smoother(tt / 0.25))
    ph = 2 * np.pi * np.cumsum(f) / SR
    s = np.sin(ph) * env * amp
    return np.stack([s * (1.0 - pan), s * (1.0 + pan)], 1) * 0.5


def master(y):
    n = len(y)
    t = np.arange(n) / SR
    # paso bajo de un polo a 9 kHz (sin aspereza)
    a = np.exp(-2 * np.pi * 9000.0 / SR)
    for ch in range(2):
        z = 0.0
        col = y[:, ch]
        for i in range(n):
            z = (1 - a) * col[i] + a * z
            col[i] = z
    fade = smoother(t / 0.010) * (1.0 - smoother((t - (t[-1] - 0.150)) / 0.150))
    y = y * fade[:, None]
    y = y / np.max(np.abs(y)) * 0.28
    return y


def write(path, y):
    d = (np.clip(y, -1, 1) * 32767).astype('<i2')
    with wave.open(path, 'wb') as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(d.tobytes())


def appear():
    dur = 3.4
    t = np.arange(int(dur * SR)) / SR
    y = np.zeros((len(t), 2))
    # soplo de agua
    nz = band_sweep(pink(len(t)), lambda s: 700.0 * (2400.0 / 700.0) ** smoother(s / 1.3), 1.1)
    env = smoother(t / 1.0) * np.exp(-np.maximum(t - 1.0, 0.0) / 0.6)
    y += np.stack([nz, np.roll(nz, 311)], 1) * (0.10 * env)[:, None]
    # acorde La add9 en arpegio ascendente
    chord = [220.0, 329.63, 493.88, 554.37, 659.25]
    amps = [0.30, 0.24, 0.18, 0.15, 0.12]
    for k, (f0, a) in enumerate(zip(chord, amps)):
        y += voice(t, f0, 0.12 * k, 0.9, 1.1, a, fade_end=(2.6, 3.35))
    # gotas de cristal
    for f0, t0, a, p in ((1760.0, 0.42, 0.05, -0.5), (1318.5, 0.71, 0.04, 0.4), (1975.5, 0.98, 0.035, -0.2),
                         (2217.5, 1.22, 0.03, 0.6), (1760.0, 1.47, 0.025, -0.6), (1318.5, 1.66, 0.02, 0.2)):
        y += ping(t, f0, t0, a, p)
    return master(y)


def vanish():
    dur = 3.2
    t = np.arange(int(dur * SR)) / SR
    y = np.zeros((len(t), 2))
    # inhalacion de anticipacion (0 - 0,9 s) y soplo que se cierra al final
    nz = pink(len(t))
    inh = band_sweep(nz, lambda s: 500.0 * (1800.0 / 500.0) ** smoother(s / 0.9), 1.0)
    env_i = smoother(t / 0.9) * (1.0 - smoother((t - 0.9) / 0.5))
    rel = band_sweep(np.roll(nz, 977), lambda s: 1600.0 * (600.0 / 1600.0) ** smoother((s - 1.8) / 1.3), 1.3)
    env_r = smoother((t - 1.7) / 0.5) * (1.0 - smoother((t - 2.4) / 0.75))
    y += np.stack([inh, np.roll(inh, 211)], 1) * (0.34 * env_i)[:, None]
    y += np.stack([np.roll(rel, 97), rel], 1) * (0.14 * env_r)[:, None]
    # el acorde se disuelve de agudo a grave y se hunde 0,6 semitonos
    chord = [220.0, 329.63, 493.88, 554.37, 659.25]
    amps = [0.30, 0.24, 0.18, 0.15, 0.12]
    drift = lambda s: -0.6 * smoother((s - 0.9) / 2.0)
    for k, (f0, a) in enumerate(zip(chord, amps)):
        end0 = 3.1 - 0.3 * k            # la voz mas aguda se apaga primero (1,9 s); la mas grave al final (3,1 s)
        y += voice(t, f0, 0.35, 0.6, 3.0, a, drift_semi=drift, fade_end=(end0 - 0.8, end0))
    return master(y)


if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else '.'
    os.makedirs(out, exist_ok=True)
    write(os.path.join(out, 'SND_MindAppear.wav'), appear())
    write(os.path.join(out, 'SND_MindVanish.wav'), vanish())
    print('ok', out)
