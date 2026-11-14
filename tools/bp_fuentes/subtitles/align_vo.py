# align_vo.py (Narrativa, 2026-10-01) - subtitulos: tiempos por palabra de cada VO con la alineacion forzada de ElevenLabs.
# Entrada: vo_final/vo_lista.json (id + texto) y el wav FINAL de cada VO en Content (el corte del master de Ableton).
# Salida: align/<id>.json con la respuesta cruda (words: text/start/end) + align/_resumen.txt.
# Uso: python align_vo.py [id ...]   (sin ids = todas; las que ya tienen json se saltan)
import json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))          # VR_Test
CONTENT = os.path.join(ROOT, 'Content')
LISTA = os.path.join(ROOT, 'Saved', 'ClaudeScripts', 'vo_final', 'vo_lista.json')
OUT = os.path.join(HERE, 'align')
KEY = open(os.path.expanduser('~/.secrets/elevenlabs.txt'), encoding='utf-8').read().strip()

def find_wavs():
    m = {}
    for d, _, fs in os.walk(CONTENT):
        for f in fs:
            if f.lower().startswith('vo_') and f.lower().endswith('.wav'):
                m[f[:-4]] = os.path.join(d, f)
    return m

def align(path, text):
    r = subprocess.run(['curl', '-s', '-X', 'POST', 'https://api.elevenlabs.io/v1/forced-alignment',
                        '-H', 'xi-api-key: ' + KEY, '-F', 'file=@' + path, '-F', 'text=' + text],
                       capture_output=True, text=True, encoding='utf-8')
    return json.loads(r.stdout)

def main():
    os.makedirs(OUT, exist_ok=True)
    lista = json.load(open(LISTA, encoding='utf-8'))
    wavs = find_wavs()
    want = set(sys.argv[1:])
    rows = []
    for v in lista:
        i = v['id']
        if want and i not in want:
            continue
        dst = os.path.join(OUT, i + '.json')
        if os.path.exists(dst) and not want:
            rows.append(i + ' ya estaba'); continue
        if i not in wavs:
            rows.append(i + ' SIN WAV'); continue
        try:
            d = align(wavs[i], v['text'])
        except Exception as e:
            rows.append(i + ' ERROR ' + str(e)[:80]); continue
        if 'words' not in d:
            rows.append(i + ' ERROR ' + json.dumps(d)[:160]); continue
        d['_id'] = i; d['_text'] = v['text']; d['_wav'] = os.path.relpath(wavs[i], CONTENT)
        json.dump(d, open(dst, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        w = [x for x in d['words'] if x['text'].strip()]
        rows.append('%s ok  %d palabras  %.2f-%.2f s  loss %.3f' % (i, len(w), w[0]['start'], w[-1]['end'], d.get('loss', 0)))
    print('\n'.join(rows))
    with open(os.path.join(OUT, '_resumen.txt'), 'a', encoding='utf-8') as f:
        f.write('\n'.join(rows) + '\n')

main()
