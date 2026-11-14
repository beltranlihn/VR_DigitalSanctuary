"""subs_bilingue.py - subtitulos de la demo en ingles + espanol en un solo juego de arreglos para BP_DemoVoice_SC.

  python tools/demo/subs_bilingue.py

Ingles: tools/demo/subs_demo.json (lo arma gen_vo_demo.py). Espanol: textos de tools/demo/vo_demo_es.json y tiempos por palabra
de VR_Test/Saved/ClaudeScripts/Demo2/vo_es/words_es.json (los devuelve ElevenLabs al generar cada voz). Las voces en espanol
se llaman VO_<id>_ES (asset y subtitulo); las pistas, HINT_<id>_ES. BP_DemoVoice_SC busca el subtitulo por el nombre del
sonido que suena, asi que con Lang = espanol encuentra solo las tarjetas _ES.
HINT_START queda bilingue (se ve antes de elegir idioma). Salida: tools/demo/subs_demo_ue_bi.json (VoIds, VoC0, ... WS)."""
import json, os, re, sys, wave

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, HERE)
import gen_vo_demo as g   # tokens(), cards(), HINT_STEP

VO_ES = os.path.join(ROOT, 'VR_Test', 'Saved', 'ClaudeScripts', 'Demo2', 'vo_es')
HINT_LANG = 'Choose your language · Elige tu idioma'


def hint(text):
    ws = [[w, round(k * g.HINT_STEP, 3), round(k * g.HINT_STEP + g.HINT_STEP, 3)] for k, w in enumerate(g.tokens(text))]
    return {'text': text, 'dur': 0.0, 'cards': [{'start': 0.0, 'end': 9999.0, 'words': ws}]}


def main():
    subs = json.load(open(os.path.join(HERE, 'subs_demo.json'), encoding='utf-8'))
    subs['HINT_START'] = hint(HINT_LANG)
    words = json.load(open(os.path.join(VO_ES, 'words_es.json'), encoding='utf-8'))
    malos = []
    for v in json.load(open(os.path.join(HERE, 'vo_demo_es.json'), encoding='utf-8')):
        i, text = v['id'], v['text']
        if i.startswith('HINT_'):
            subs[i + '_ES'] = hint(HINT_LANG if i == 'HINT_START' else text)
            continue
        al = [x for x in (words.get(i) or []) if x['text'].strip() and not re.fullmatch(r'[.…,;:!?¿¡-]+', x['text'].strip())]
        tk = g.tokens(text)
        if len(al) != len(tk):
            malos.append('%s: %d palabras alineadas vs %d' % (i, len(al), len(tk))); continue
        ws = [[w, round(a['start'], 3), round(a['end'], 3)] for w, a in zip(tk, al)]
        with wave.open(os.path.join(VO_ES, i + '.wav')) as w:
            d = w.getnframes() / w.getframerate()
        subs[i + '_ES'] = {'text': text, 'dur': round(d, 3), 'cards': g.cards(ws)}
    A = {k: [] for k in ['VoIds', 'VoC0', 'VoCN', 'CS', 'CE', 'CW0', 'CWN', 'Words', 'WS']}
    for vid, v in subs.items():
        A['VoIds'].append(vid); A['VoC0'].append(len(A['CS'])); A['VoCN'].append(len(v['cards']))
        for c in v['cards']:
            A['CS'].append(c['start']); A['CE'].append(c['end'])
            A['CW0'].append(len(A['Words'])); A['CWN'].append(len(c['words']))
            for w in c['words']:
                A['Words'].append(w[0]); A['WS'].append(w[1])
    json.dump(A, open(os.path.join(HERE, 'subs_demo_ue_bi.json'), 'w', encoding='utf-8'), ensure_ascii=False)
    print('ids', len(A['VoIds']), 'tarjetas', len(A['CS']), 'palabras', len(A['Words']))
    print('problemas:', malos or 'ninguno')


if __name__ == '__main__':
    main()
