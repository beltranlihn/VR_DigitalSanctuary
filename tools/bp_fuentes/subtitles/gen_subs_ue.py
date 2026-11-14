# gen_subs_ue.py (Narrativa, 2026-10-01) - aplana subs.json en arrays paralelos para BP_Subtitles_SC
# (add_variable no acepta structs ni objetos: los datos van como arrays de String/int/float en el CDO).
#   VoIds[v] (nombre del SoundWave, ej. "VO_02") -> tarjetas VoC0[v] .. VoC0[v]+VoCN[v]-1
#   tarjeta c: CS[c] (aparece) CE[c] (se va) -> palabras CW0[c] .. CW0[c]+CWN[c]-1
#   palabra w: Words[w] (con su puntuacion) y WS[w] (cuando se dice, s desde que arranca el clip)
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
subs = json.load(open(os.path.join(HERE, 'subs.json'), encoding='utf-8'))
A = {k: [] for k in ['VoIds', 'VoC0', 'VoCN', 'CS', 'CE', 'CW0', 'CWN', 'Words', 'WS']}
for vid, v in subs.items():
    A['VoIds'].append(vid); A['VoC0'].append(len(A['CS'])); A['VoCN'].append(len(v['cards']))
    for c in v['cards']:
        A['CS'].append(c['start']); A['CE'].append(c['end'])
        A['CW0'].append(len(A['Words'])); A['CWN'].append(len(c['words']))
        for w in c['words']:
            A['Words'].append(w[0]); A['WS'].append(w[1])
json.dump(A, open(os.path.join(HERE, 'subs_ue.json'), 'w', encoding='utf-8'), ensure_ascii=False)
print({k: len(x) for k, x in A.items()}, 'max palabras/tarjeta', max(A['CWN']))
