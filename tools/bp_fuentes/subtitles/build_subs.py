# build_subs.py (Narrativa, 2026-10-01) - subtitulos de la Obra: tiempos por palabra de cada VO, SIN servicios externos.
# Metodo: en el wav FINAL de cada VO (el corte del master de Ableton que se importo a Unreal) se detecta donde hay voz
# (envolvente RMS con umbral relativo al pico); las palabras del texto se reparten SOLO sobre el tiempo con voz,
# proporcional a sus silabas. Las pausas del audio quedan como pausas: ningun subtitulo cae sobre un silencio.
# Si existe align/<id>.json (alineacion forzada de ElevenLabs, ver align_vo.py) se usa esa en vez de la estimada.
# Salida: subs.json (para Unreal y la web) + subs_resumen.txt
import json, os, re, wave
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
CONTENT = os.path.join(ROOT, 'Content')
LISTA = os.path.join(ROOT, 'Saved', 'ClaudeScripts', 'vo_final', 'vo_lista.json')

FRAME = 0.01          # s
THR_DB = -30.0        # voz = envolvente sobre (pico - 30 dB)
MERGE_GAP = 0.18      # huecos mas cortos que esto son parte de la palabra
MIN_SEG = 0.06
CARD_CHARS = 74       # una tarjeta = hasta 2 lineas de ~37
CARD_GAP = 0.55       # una pausa mas larga corta la tarjeta
LEAD = 0.12           # la tarjeta aparece un poco antes de la primera palabra
TAIL = 0.45           # y se queda un poco despues de la ultima

def find_wavs():
    m = {}
    for d, _, fs in os.walk(CONTENT):
        for f in fs:
            if f.lower().startswith('vo_') and f.lower().endswith('.wav'):
                m[f[:-4]] = os.path.join(d, f)
    return m

def read_wav(p):
    with wave.open(p, 'rb') as w:
        sr, n, ch, sw = w.getframerate(), w.getnframes(), w.getnchannels(), w.getsampwidth()
        raw = w.readframes(n)
    x = np.frombuffer(raw, dtype={2: np.int16, 4: np.int32}[sw]).astype(np.float32)
    if ch > 1:
        x = x.reshape(-1, ch).mean(axis=1)
    return x / (np.abs(x).max() + 1e-9), sr

def speech_segments(x, sr):
    hop = int(sr * FRAME)
    nf = len(x) // hop
    rms = np.sqrt(np.mean(x[:nf * hop].reshape(nf, hop) ** 2, axis=1) + 1e-12)
    rms = np.convolve(rms, np.ones(3) / 3, mode='same')
    db = 20 * np.log10(rms + 1e-9)
    on = db > (db.max() + THR_DB)
    segs, i = [], 0
    while i < nf:
        if on[i]:
            j = i
            while j < nf and on[j]:
                j += 1
            segs.append([i * FRAME, j * FRAME])
            i = j
        else:
            i += 1
    out = []
    for s in segs:
        if out and s[0] - out[-1][1] < MERGE_GAP:
            out[-1][1] = s[1]
        else:
            out.append(s)
    return [s for s in out if s[1] - s[0] >= MIN_SEG], nf * FRAME

def syllables(w):
    w = re.sub(r'[^a-z]', '', w.lower())
    if not w:
        return 1
    n = len(re.findall(r'[aeiouy]+', w))
    if w.endswith('e') and n > 1 and not w.endswith(('le', 'ee')):
        n -= 1
    return max(1, n)

def tokens(text):
    # palabras visibles (con su puntuacion pegada); "..." cuenta como pausa, no como palabra
    t = text.replace('…', '...')
    return [w for w in re.split(r'\s+', t.strip()) if w and not re.fullmatch(r'[.…,;:!?-]+', w)]

def estimate(words, segs):
    total = sum(e - s for s, e in segs)
    wts = [syllables(w) + 0.35 for w in words]
    W = sum(wts)
    acc, out = 0.0, []
    def real(t):          # tiempo-de-voz -> tiempo real
        for s, e in segs:
            if t <= e - s + 1e-9:
                return s + t
            t -= (e - s)
        return segs[-1][1]
    for w, k in zip(words, wts):
        a = acc / W * total
        acc += k
        b = acc / W * total
        out.append([w, round(real(a), 3), round(real(b - 1e-6), 3)])
    return out

def groups_of(words):
    # grupos de pausa: cortan despues de una palabra con puntuacion (... . , ? ! ; :)
    gs, cur = [], []
    for k, w in enumerate(words):
        cur.append(k)
        if re.search(r'[.,;:!?…]["\')]*$', w):
            gs.append(cur); cur = []
    if cur:
        gs.append(cur)
    return gs

def estimate_grouped(words, segs):
    # Cada grupo de pausa se queda con un tramo CONTIGUO de segmentos de voz (programacion dinamica: la duracion de
    # cada tramo lo mas parecida a la que le toca por silabas). Adentro del grupo, reparto proporcional.
    gs = groups_of(words)
    G, S = len(gs), len(segs)
    if G < 2 or S < G:
        return estimate(words, segs)
    wts = [sum(syllables(words[k]) + 0.35 for k in g) for g in gs]
    total = sum(e - s for s, e in segs)
    exp = [w / sum(wts) * total for w in wts]
    pre = [0.0]
    for s, e in segs:
        pre.append(pre[-1] + (e - s))
    INF = 1e18
    dp = [[INF] * (S + 1) for _ in range(G + 1)]
    bk = [[0] * (S + 1) for _ in range(G + 1)]
    dp[0][0] = 0.0
    for g in range(1, G + 1):
        for j in range(g, S - (G - g) + 1):
            for i in range(g - 1, j):
                if dp[g - 1][i] >= INF:
                    continue
                d = pre[j] - pre[i]
                c = dp[g - 1][i] + ((d - exp[g - 1]) / max(exp[g - 1], 0.15)) ** 2
                if c < dp[g][j]:
                    dp[g][j], bk[g][j] = c, i
    cuts, j = [], S
    for g in range(G, 0, -1):
        i = bk[g][j]
        cuts.append((i, j)); j = i
    cuts.reverse()
    out = [None] * len(words)
    for g, (i, j) in zip(gs, cuts):
        part = estimate([words[k] for k in g], segs[i:j])
        for k, w in zip(g, part):
            out[k] = w
    return out

def from_align(d, words):
    al = [x for x in d['words'] if x['text'].strip() and not re.fullmatch(r'[.…,;:!?-]+', x['text'].strip())]
    if len(al) != len(words):
        return None
    return [[w, round(a['start'], 3), round(a['end'], 3)] for w, a in zip(words, al)]

def cards(ws):
    out, cur = [], []
    for k, w in enumerate(ws):
        if cur:
            gap = w[1] - cur[-1][2]
            chars = sum(len(x[0]) + 1 for x in cur) + len(w[0])
            prev_end = re.search(r'[.!?…]$', cur[-1][0]) is not None
            if gap > CARD_GAP or chars > CARD_CHARS or (prev_end and chars > 28):
                out.append(cur); cur = []
        cur.append(w)
    if cur:
        out.append(cur)
    res = []
    for i, c in enumerate(out):
        start = max(0.0, c[0][1] - LEAD)
        end = c[-1][2] + TAIL
        if i + 1 < len(out):
            end = min(end, out[i + 1][0][1] - LEAD - 0.02)
        res.append({'start': round(start, 3), 'end': round(end, 3), 'words': c})
    return res

def main():
    lista = json.load(open(LISTA, encoding='utf-8'))
    wavs = find_wavs()
    subs, rows = {}, []
    for v in lista:
        i = v['id']
        words = tokens(v['text'])
        if i not in wavs:
            rows.append('%-8s SIN WAV (no se subtitula)' % i); continue
        x, sr = read_wav(wavs[i])
        segs, dur = speech_segments(x, sr)
        src = 'estimado'
        ws = None
        ap = os.path.join(HERE, 'align', i + '.json')
        if os.path.exists(ap):
            ws = from_align(json.load(open(ap, encoding='utf-8')), words)
            if ws:
                src = 'elevenlabs'
        if ws is None:
            ws = estimate_grouped(words, segs)
        cs = cards(ws)
        subs[i] = {'text': v['text'], 'dur': round(dur, 3), 'src': src, 'cards': cs}
        rows.append('%-8s %5.2f s  voz %4.1f-%4.1f  %2d segs  %2d palabras  %d tarjetas  %s' % (
            i, dur, segs[0][0], segs[-1][1], len(segs), len(ws), len(cs), src))
    json.dump(subs, open(os.path.join(HERE, 'subs.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    open(os.path.join(HERE, 'subs_resumen.txt'), 'w', encoding='utf-8').write('\n'.join(rows) + '\n')
    print('\n'.join(rows))
    print('VO con subtitulos:', len(subs))

main()
