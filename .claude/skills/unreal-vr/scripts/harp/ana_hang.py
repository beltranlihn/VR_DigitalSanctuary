# Analisis del .wav del hang (sonido 3): golpes, nota de cada golpe, nivel, proporciones de parciales, T60 por nota, batido de la octava.
# Uso: python -I ana_hang.py <wav> [etiqueta]
import struct, sys
import numpy as np

NOTES = {'D3': 146.83, 'A3': 220.0, 'Bb3': 233.08, 'C4': 261.63, 'D4': 293.66, 'E4': 329.63, 'F4': 349.23, 'G4': 392.0, 'A4': 440.0}


def load(fn):
    f = open(fn, 'rb').read()
    pos = 12; fmt = None; data = None
    while pos < len(f):
        cid = f[pos:pos + 4]; sz = struct.unpack('<I', f[pos + 4:pos + 8])[0]
        if cid == b'fmt ': fmt = struct.unpack('<HHIIHH', f[pos + 8:pos + 24])
        if cid == b'data': data = f[pos + 8:pos + 8 + sz]
        pos += 8 + sz + (sz & 1)
    x = np.frombuffer(data, dtype='<f4').reshape(-1, fmt[1]).astype(np.float64)
    return x[:, 0], x, fmt[2]


def band_env(x, sr, f0, bw=4.0, hop=0.005):
    # envolvente de una banda angosta alrededor de f0 (demodulacion + pasabajos)
    n = np.arange(len(x)); z = x * np.exp(-2j * np.pi * f0 * n / sr)
    k = int(sr / bw); w = np.hanning(k); w /= w.sum()
    e = np.abs(np.convolve(z, w, mode='same')) * 2
    h = int(hop * sr)
    return e[::h], h / sr


def main():
    fn = sys.argv[1]; tag = sys.argv[2] if len(sys.argv) > 2 else ''
    x, xs, sr = load(fn)
    print('%s %s  sr %d  dur %.1f s  peak %.3g  rms %.3g' % (tag, fn.split('/')[-1], sr, len(x) / sr, np.abs(xs).max(), np.sqrt(np.mean(x ** 2))))
    # golpes: subida brusca de energia de alta frecuencia (diferencia)
    d = np.diff(x, prepend=0.0)
    e = np.sqrt(np.convolve(d ** 2, np.ones(240) / 240, mode='same'))
    # golpe = subida local de la energia de la derivada (x4 sobre 30 ms antes), con 0,4 s de refractario: no depende del golpe mas fuerte
    lag = int(0.03 * sr); on = []; i = lag
    while i < len(e):
        if e[i] > 4.0 * e[i - lag] + 1e-9 and e[i] > 1e-6:
            on.append(i); i += int(0.4 * sr)
        else:
            i += 1
    print('golpes:', len(on), ' cada', np.round(np.diff(on) / sr, 2)[:6] if len(on) > 1 else '')
    hits = []
    for o in on:
        seg = x[o + int(0.02 * sr):o + int(0.32 * sr)]
        if len(seg) < 1000: continue
        S = np.abs(np.fft.rfft(seg * np.hanning(len(seg)), 1 << 17)); fr = np.fft.rfftfreq(1 << 17, 1 / sr)
        # nota = la fundamental con mas energia nueva respecto de antes del golpe
        pre = x[max(0, o - int(0.31 * sr)):o - int(0.01 * sr)]
        P = np.abs(np.fft.rfft(pre * np.hanning(len(pre)), 1 << 17)) if len(pre) > 1000 else S * 0
        best = max(NOTES, key=lambda nm: (S[np.abs(fr - NOTES[nm]) < 3].max() - P[np.abs(fr - NOTES[nm]) < 3].max()))
        hits.append((o, best))
    print('notas:', ' '.join(nm for o, nm in hits[:12]))
    # por nota: el primer golpe que no sea el primero de la grabacion
    done = set()
    for idx, (o, nm) in enumerate(hits):
        if idx == 0 or nm in done: continue
        done.add(nm)
        f0 = NOTES[nm]
        seg = x[o + int(0.02 * sr):o + int(0.42 * sr)]
        S = np.abs(np.fft.rfft(seg * np.hanning(len(seg)), 1 << 18)); fr = np.fft.rfftfreq(1 << 18, 1 / sr)
        def pk(f, tol):
            m = np.abs(fr - f) < tol
            j = np.argmax(S * m)
            return fr[j], S[j]
        f1, a1 = pk(f0, 4)
        rows = []
        for r in [2.0, 3.0, 7.5, 8.16]:
            fp, ap = pk(f1 * r, 0.03 * f1 * r)
            rows.append('x%.3f %+.1fdB' % (fp / f1, 20 * np.log10(ap / a1 + 1e-12)))
        # T60 de la fundamental: pendiente de la envolvente en dB hasta el proximo golpe de la misma nota
        nxt = [p for p, n2 in hits if p > o and n2 == nm]
        end = (nxt[0] if nxt else len(x)) - int(0.05 * sr)
        env, dt = band_env(x[o:end], sr, f1, bw=3.0)
        db = 20 * np.log10(env + 1e-15)
        t = np.arange(len(db)) * dt
        m = (t > 0.4) & (t < min(3.0, t[-1])) & (db > db.max() - 45)
        t60 = -60.0 / np.polyfit(t[m], db[m], 1)[0] if m.sum() > 20 else float('nan')
        # batido de la octava: modulacion de su envolvente en 0,1-2 s
        e2, dt2 = band_env(x[o:min(end, o + int(2.2 * sr))], sr, 2 * f1, bw=40.0)
        tt = np.arange(len(e2)) * dt2
        mm = (tt > 0.1) & (tt < 2.0)
        am = 'n/a'
        if mm.sum() > 50:
            y = 20 * np.log10(e2[mm] + 1e-15); y = y - np.polyval(np.polyfit(tt[mm], y, 2), tt[mm])
            Y = np.abs(np.fft.rfft(y * np.hanning(len(y)), 8192)); fq = np.fft.rfftfreq(8192, dt2)
            band = (fq > 0.8) & (fq < 15)
            am = '%.1f Hz (prof %.1f dB)' % (fq[band][np.argmax(Y[band])], 2 * np.std(y))
        lvl = np.sqrt(np.mean(x[o:o + int(0.3 * sr)] ** 2))
        print('%-4s f1 %.2f (%+.1f c)  rms0.3s %.3g  %s  T60 %.2f s  batido oct %s' % (nm, f1, 1200 * np.log2(f1 / f0), lvl, '  '.join(rows), t60, am))


main()
