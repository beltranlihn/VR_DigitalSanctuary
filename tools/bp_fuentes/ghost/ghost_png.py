# -*- coding: utf-8 -*-
"""ghost_png.py - decodifica las capturas que escribe ghost_show.py (base64 dentro de un JSON en un .txt) a PNG.
Uso: python ghost_png.py [prefijo]   -> VR_Test/Saved/ClaudeScripts/ghost/cap_<prefijo>*.txt -> mismo nombre .png"""
import base64
import glob
import io
import json
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
DIR = os.path.normpath(os.path.join(AQUI, '..', '..', '..', '..', '..', 'VR_Test', 'Saved', 'ClaudeScripts', 'ghost'))


def find_b64(o):
    if isinstance(o, dict):
        for k in ('data', 'image'):
            if k in o:
                r = find_b64(o[k])
                if r:
                    return r
        for v in o.values():
            r = find_b64(v)
            if r:
                return r
    if isinstance(o, str) and len(o) > 1000:
        return o
    return None


def main():
    pre = sys.argv[1] if len(sys.argv) > 1 else ''
    for p in sorted(glob.glob(os.path.join(DIR, 'cap_' + pre + '*.txt'))):
        raw = io.open(p, encoding='utf-8').read()
        try:
            o = json.loads(raw)
            if isinstance(o, str):
                o = json.loads(o)
        except ValueError:
            o = raw
        b = find_b64(o)
        if not b:
            print('sin imagen:', os.path.basename(p))
            continue
        out = p[:-4] + '.png'
        io.open(out, 'wb').write(base64.b64decode(b))
        print(out)


if __name__ == '__main__':
    main()
