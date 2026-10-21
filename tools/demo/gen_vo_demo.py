"""gen_vo_demo.py - las voces de la demo (BDW): las genera con ElevenLabs, las deja listas en Content y arma sus subtitulos.

  python tools/demo/gen_vo_demo.py                 # genera las que faltan + subtitulos
  python tools/demo/gen_vo_demo.py VO_D02 VO_DB1   # regenera solo esas (pisa el wav)
  python tools/demo/gen_vo_demo.py --solo-subs     # no genera audio: solo vuelve a alinear y armar los subtitulos

Textos: tools/demo/vo_demo.json (las entradas con "hint": true no tienen audio: son pistas que muestra ShowHint). Voz: Soul Charger Woman, receta S2 (multilingual v2, stability .75, similarity .80,
style 0, speed .925), sin de-esser (pedido de Beltran). El wav se iguala en volumen a las VO de la Obra (-21 LUFS,
pico -3 dBTP) y queda en 48 kHz mono en VR_Test/Content/SoulCharger/Demo/Audio/VO/<id>.wav (Unreal lo importa solo).
Subtitulos: tiempos por caracter que devuelve la misma sintesis (/with-timestamps) -> tarjetas como las de la Obra
(VR_Test/Saved/ClaudeScripts/subtitles/build_subs.py) -> tools/demo/subs_demo_ue.json, los arreglos paralelos que lee
BP_Subtitles_SC (VoIds, VoC0, VoCN, CS, CE, CW0, CWN, Words, WS).
"""
import base64, json, os, re, subprocess, sys, tempfile, time, urllib.request, wave

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
DEST = os.path.join(ROOT, 'VR_Test', 'Content', 'SoulCharger', 'Demo', 'Audio', 'VO')
ALIGN = os.path.join(ROOT, 'VR_Test', 'Saved', 'ClaudeScripts', 'Demo2', 'align')
KEY = open(os.path.expanduser('~/.secrets/elevenlabs.txt'), encoding='utf-8').read().strip()
VOICE = 'vJQtyq8I9JyhL0Xpkd5I'          # Soul Charger Woman
SET = dict(stability=0.75, similarity_boost=0.80, style=0.0, speed=0.925, use_speaker_boost=True)

CARD_CHARS, CARD_GAP, LEAD, TAIL = 74, 0.55, 0.12, 0.45   # los de la Obra
HINT_STEP = 0.07                                          # pistas sin audio ("hint": true en vo_demo.json)


def tts(text, out_wav):
    """Sintesis con tiempos por caracter (/with-timestamps): la clave no tiene permiso de forced_alignment.
    Devuelve las palabras con su inicio y fin, o None si fallo."""
    body = {'text': text, 'model_id': 'eleven_multilingual_v2', 'voice_settings': SET}
    r = urllib.request.Request('https://api.elevenlabs.io/v1/text-to-speech/%s/with-timestamps?output_format=pcm_24000' % VOICE,
                               data=json.dumps(body).encode(), headers={'xi-api-key': KEY, 'Content-Type': 'application/json'})
    for intento in range(3):
        try:
            with urllib.request.urlopen(r, timeout=180) as resp:
                d = json.loads(resp.read())
            b = base64.b64decode(d['audio_base64'])
            raw = out_wav + '.24k.wav'
            with wave.open(raw, 'wb') as w:
                w.setnchannels(1); w.setsampwidth(2); w.setframerate(24000); w.writeframes(b)
            subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', raw,
                            '-af', 'loudnorm=I=-21:TP=-3:LRA=11,aresample=48000:resampler=soxr',
                            '-ac', '1', '-ar', '48000', '-c:a', 'pcm_s16le', out_wav], check=True)
            os.remove(raw)
            al = d['alignment']
            ch, t0, t1 = al['characters'], al['character_start_times_seconds'], al['character_end_times_seconds']
            words, cur, a = [], '', None
            for c, s0, s1 in zip(ch, t0, t1):
                if c.isspace():
                    if cur: words.append({'text': cur, 'start': a, 'end': e}); cur = ''
                    continue
                if not cur: a = s0
                cur += c; e = s1
            if cur: words.append({'text': cur, 'start': a, 'end': e})
            return {'words': words}
        except Exception as ex:
            print('  reintento', intento + 1, str(ex)[:160]); time.sleep(3)
    return None


def tokens(text):
    t = text.replace('…', '...')
    return [w for w in re.split(r'\s+', t.strip()) if w and not re.fullmatch(r'[.…,;:!?-]+', w)]


def cards(ws):
    out, cur = [], []
    for w in ws:
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


def dur_of(p):
    with wave.open(p, 'rb') as w:
        return w.getnframes() / w.getframerate()


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    solo_subs = '--solo-subs' in sys.argv
    lista = json.load(open(os.path.join(HERE, 'vo_demo.json'), encoding='utf-8'))
    os.makedirs(DEST, exist_ok=True); os.makedirs(ALIGN, exist_ok=True)
    subs, rows = {}, []
    for v in lista:
        i, text = v['id'], v['text']
        if v.get('hint'):
            # pista sin audio (2026-10-20): una sola tarjeta que queda puesta (fin 9999) hasta BP_DemoVoice_SC.HideHint;
            # las palabras entran de a una cada HINT_STEP s
            ws = [[w, round(k * HINT_STEP, 3), round(k * HINT_STEP + HINT_STEP, 3)] for k, w in enumerate(tokens(text))]
            subs[i] = {'text': text, 'dur': 0.0, 'cards': [{'start': 0.0, 'end': 9999.0, 'words': ws}]}
            rows.append('%-10s pista sin audio, %d palabras' % (i, len(ws)))
            continue
        wav = os.path.join(DEST, i + '.wav')
        ap = os.path.join(ALIGN, i + '.json')
        if not solo_subs and (i in args or (not args and not os.path.exists(ap))):
            d = tts(text, wav)
            rows.append('%-8s %s' % (i, 'generada' if d else 'FALLO'))
            if d:
                json.dump(d, open(ap, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        if not os.path.exists(wav) or not os.path.exists(ap):
            rows.append('%-8s SIN WAV O SIN TIEMPOS' % i); continue
        d = json.load(open(ap, encoding='utf-8'))
        words = tokens(text)
        al = [x for x in d.get('words', []) if x['text'].strip() and not re.fullmatch(r'[.…,;:!?-]+', x['text'].strip())]
        if len(al) != len(words):
            rows.append('%-8s ALINEACION NO CALZA (%d vs %d palabras)' % (i, len(al), len(words))); continue
        ws = [[w, round(a['start'], 3), round(a['end'], 3)] for w, a in zip(words, al)]
        cs = cards(ws)
        subs[i] = {'text': text, 'dur': round(dur_of(wav), 3), 'cards': cs}
        rows.append('%-8s %5.2f s  %d tarjetas' % (i, subs[i]['dur'], len(cs)))
    A = {k: [] for k in ['VoIds', 'VoC0', 'VoCN', 'CS', 'CE', 'CW0', 'CWN', 'Words', 'WS']}
    for vid, v in subs.items():
        A['VoIds'].append(vid); A['VoC0'].append(len(A['CS'])); A['VoCN'].append(len(v['cards']))
        for c in v['cards']:
            A['CS'].append(c['start']); A['CE'].append(c['end'])
            A['CW0'].append(len(A['Words'])); A['CWN'].append(len(c['words']))
            for w in c['words']:
                A['Words'].append(w[0]); A['WS'].append(w[1])
    json.dump(subs, open(os.path.join(HERE, 'subs_demo.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    json.dump(A, open(os.path.join(HERE, 'subs_demo_ue.json'), 'w', encoding='utf-8'), ensure_ascii=False)
    print('\n'.join(rows))


if __name__ == '__main__':
    main()
