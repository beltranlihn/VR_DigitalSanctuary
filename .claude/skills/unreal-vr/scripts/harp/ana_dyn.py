# Compara la dinamica del hang entre capturas: nivel de los golpes (0,3 s), pico del ataque, centroide y energia sobre 1 kHz.
# Uso: python -I ana_dyn.py ETIQUETA=archivo.wav ... (la primera es la referencia de nivel)
import struct, sys
import numpy as np


def load(fn):
    f = open(fn, 'rb').read(); pos = 12; fmt = None; data = None
    while pos < len(f):
        cid = f[pos:pos + 4]; sz = struct.unpack('<I', f[pos + 4:pos + 8])[0]
        if cid == b'fmt ': fmt = struct.unpack('<HHIIHH', f[pos + 8:pos + 24])
        if cid == b'data': data = f[pos + 8:pos + 8 + sz]
        pos += 8 + sz + (sz & 1)
    return np.frombuffer(data, dtype='<f4').reshape(-1, fmt[1])[:, 0].astype(np.float64), fmt[2]


ref = None
for arg in sys.argv[1:]:
    tag, fn = arg.split('=', 1)
    x, sr = load(fn)
    d = np.diff(x, prepend=0.0); e = np.sqrt(np.convolve(d ** 2, np.ones(240) / 240, mode='same'))
    # golpe = subida local de la energia de la derivada (x4 sobre 30 ms antes), con 0,4 s de refractario: no depende del golpe mas fuerte
    lag = int(0.03 * sr); on = []; i = lag
    while i < len(e):
        if e[i] > 4.0 * e[i - lag] + 1e-9 and e[i] > 1e-6:
            on.append(i); i += int(0.4 * sr)
        else:
            i += 1
    lv = []; cen = []; hi = []; att = []
    for o in on[2:11]:
        seg = x[o:o + int(0.3 * sr)]
        lv.append(np.sqrt(np.mean(seg ** 2)))
        S = np.abs(np.fft.rfft(seg * np.hanning(len(seg)))); fr = np.fft.rfftfreq(len(seg), 1 / sr)
        cen.append((S * fr).sum() / S.sum()); hi.append((S[fr > 1000] ** 2).sum() / (S ** 2).sum())
        att.append(np.abs(x[o:o + int(0.015 * sr)]).max())
    L = np.median(lv)
    ref = ref or L
    print('%-6s golpes %2d  rms0.3 %.4f (%+5.1f dB)  pico ataque %.4f  centroide %4.0f Hz  >1kHz %5.2f%%  pico total %.3f' % (
        tag, len(on), L, 20 * np.log10(L / ref), np.median(att), np.median(cen), 100 * np.median(hi), np.abs(x).max()))
