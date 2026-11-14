"""gen_vo_ic.py - las voces de Inner Canvas (ingles + espanol), con ElevenLabs, y sus subtitulos.

  python tools/innercanvas/gen_vo_ic.py              # genera las que faltan + subtitulos
  python tools/innercanvas/gen_vo_ic.py IC_02 IC_05  # regenera solo esas (las dos lenguas; pisa el wav)
  python tools/innercanvas/gen_vo_ic.py --solo-subs  # no genera audio: solo arma los subtitulos

Textos: tools/innercanvas/vo_ic.json (id, en, es; "hint": true = pista sin audio).
Voz y receta: las de la demo de BDW (tools/demo/gen_vo_demo.py: Soul Charger Woman, multilingual v2, S2).
2026-11-13, Beltran: el audio va DIRECTO de ElevenLabs, SIN NINGUN PROCESO (ni normalizar, ni filtrar, ni remuestrear): pcm_24000 tal
cual en un wav de 24 kHz mono 16 bit (tts_raw). El nivel se ajusta en Unreal (VolumeMultiplier del componente Voice de BP_ICVoice_IC).
La cuenta no permite pcm_44100 (403). Salida: VR_Test/Content/InnerCanvas/Audio/VO/<id>.wav (ingles) y <id>_ES.wav (espanol);
Unreal los importa solo.
Subtitulos: tools/innercanvas/subs_ic_ue.json = los arreglos paralelos de BP_ICVoice_IC (VoIds, VoC0, VoCN, CS, CE, CW0, CWN,
Words, WS). Las voces en espanol se llaman <id>_ES (asset y subtitulo); las pistas, HINT_<x> y HINT_<x>_ES.
"""
import base64, json, os, re, sys, time, urllib.request, wave

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'tools', 'demo'))
import gen_vo_demo as g   # tts(), cards(), dur_of(), HINT_STEP (misma voz y receta que la demo)

DEST = os.path.join(ROOT, 'VR_Test', 'Content', 'InnerCanvas', 'Audio', 'VO')
ALIGN = os.path.join(ROOT, 'VR_Test', 'Saved', 'ClaudeScripts', 'InnerCanvas', 'align')
PUNCT = r'[.…,;:!?¿¡·-]+'


def tokens(text):
    return [w for w in re.split(r'\s+', text.replace('…', '...').strip()) if w and not re.fullmatch(PUNCT, w)]


def hint(text):
    ws = [[w, round(k * g.HINT_STEP, 3), round(k * g.HINT_STEP + g.HINT_STEP, 3)] for k, w in enumerate(tokens(text))]
    return {'text': text, 'dur': 0.0, 'cards': [{'start': 0.0, 'end': 9999.0, 'words': ws}]}


def tts_raw(text, out_wav):
    """ElevenLabs tal cual (sin proceso): /with-timestamps en pcm_24000 -> wav 24 kHz mono 16 bit con esos mismos bytes.
    Devuelve las palabras con su inicio y fin (para los subtitulos), o None si fallo."""
    body = {'text': text, 'model_id': 'eleven_multilingual_v2', 'voice_settings': g.SET}
    r = urllib.request.Request('https://api.elevenlabs.io/v1/text-to-speech/%s/with-timestamps?output_format=pcm_24000' % g.VOICE,
                               data=json.dumps(body).encode(), headers={'xi-api-key': g.KEY, 'Content-Type': 'application/json'})
    for intento in range(3):
        try:
            with urllib.request.urlopen(r, timeout=180) as resp:
                d = json.loads(resp.read())
            with wave.open(out_wav, 'wb') as w:
                w.setnchannels(1); w.setsampwidth(2); w.setframerate(24000); w.writeframes(base64.b64decode(d['audio_base64']))
            al = d['alignment']
            words, cur, a, e = [], '', None, None
            for c, s0, s1 in zip(al['characters'], al['character_start_times_seconds'], al['character_end_times_seconds']):
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


def one(vid, text, regen, rows, subs):
    wav = os.path.join(DEST, vid + '.wav')
    ap = os.path.join(ALIGN, vid + '.json')
    if regen or not os.path.exists(ap) or not os.path.exists(wav):
        d = tts_raw(text, wav)
        rows.append('%-10s %s' % (vid, 'generada' if d else 'FALLO'))
        if d:
            json.dump(d, open(ap, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    if not os.path.exists(wav) or not os.path.exists(ap):
        rows.append('%-10s SIN WAV O SIN TIEMPOS' % vid); return
    d = json.load(open(ap, encoding='utf-8'))
    words = tokens(text)
    al = [x for x in d.get('words', []) if x['text'].strip() and not re.fullmatch(PUNCT, x['text'].strip())]
    if len(al) != len(words):
        rows.append('%-10s ALINEACION NO CALZA (%d vs %d palabras)' % (vid, len(al), len(words))); return
    ws = [[w, round(a['start'], 3), round(a['end'], 3)] for w, a in zip(words, al)]
    cs = g.cards(ws)
    subs[vid] = {'text': text, 'dur': round(g.dur_of(wav), 3), 'cards': cs}
    rows.append('%-10s %5.2f s  %d tarjetas' % (vid, subs[vid]['dur'], len(cs)))


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    solo = '--solo-subs' in sys.argv
    lista = json.load(open(os.path.join(HERE, 'vo_ic.json'), encoding='utf-8'))
    os.makedirs(DEST, exist_ok=True); os.makedirs(ALIGN, exist_ok=True)
    subs, rows = {}, []
    for v in lista:
        i = v['id']
        if v.get('hint'):
            subs[i] = hint(v['en']); subs[i + '_ES'] = hint(v['es'])
            rows.append('%-10s pista sin audio' % i)
            continue
        regen = (not solo) and (i in args)
        if solo:
            for vid in (i, i + '_ES'):
                if not os.path.exists(os.path.join(ALIGN, vid + '.json')):
                    rows.append('%-10s falta generar' % vid)
        one(i, v['en'], regen, rows, subs) if not (solo and not os.path.exists(os.path.join(ALIGN, i + '.json'))) else None
        one(i + '_ES', v['es'], regen, rows, subs) if not (solo and not os.path.exists(os.path.join(ALIGN, i + '_ES.json'))) else None
    A = {k: [] for k in ['VoIds', 'VoC0', 'VoCN', 'CS', 'CE', 'CW0', 'CWN', 'Words', 'WS']}
    for vid, v in subs.items():
        A['VoIds'].append(vid); A['VoC0'].append(len(A['CS'])); A['VoCN'].append(len(v['cards']))
        for c in v['cards']:
            A['CS'].append(c['start']); A['CE'].append(c['end'])
            A['CW0'].append(len(A['Words'])); A['CWN'].append(len(c['words']))
            for w in c['words']:
                A['Words'].append(w[0]); A['WS'].append(w[1])
    json.dump(subs, open(os.path.join(HERE, 'subs_ic.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    json.dump(A, open(os.path.join(HERE, 'subs_ic_ue.json'), 'w', encoding='utf-8'), ensure_ascii=False)
    print('\n'.join(rows))


if __name__ == '__main__':
    main()
