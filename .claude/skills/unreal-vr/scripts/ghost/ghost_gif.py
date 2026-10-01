# -*- coding: utf-8 -*-
"""ghost_gif.py - arma un GIF animado con las capturas cap_<prefijo>_NNN.png (las saca ghost_show en llamadas separadas:
dentro de UN script el editor no redibuja y todas las capturas salen iguales). Recorta al centro, achica y marca el
cuadro. Uso: python ghost_gif.py <prefijo> [ms_por_cuadro]  -> VR_Test/Saved/ClaudeScripts/ghost/<prefijo>.gif"""
import glob
import os
import sys

from PIL import Image

AQUI = os.path.dirname(os.path.abspath(__file__))
DIR = os.path.normpath(os.path.join(AQUI, '..', '..', '..', '..', '..', 'VR_Test', 'Saved', 'ClaudeScripts', 'ghost'))


def main():
    pre = sys.argv[1]
    ms = int(sys.argv[2]) if len(sys.argv) > 2 else 90
    files = sorted(glob.glob(os.path.join(DIR, 'cap_' + pre + '_*.png')))
    if not files:
        print('sin capturas para', pre)
        return
    frames = []
    for f in files:
        im = Image.open(f).convert('RGB')
        w, h = im.size
        s = min(w, h)
        im = im.crop(((w - s) // 2, (h - s) // 2, (w - s) // 2 + s, (h - s) // 2 + s)).resize((480, 480))
        frames.append(im)
    out = os.path.join(DIR, pre + '.gif')
    frames[0].save(out, save_all=True, append_images=frames[1:], duration=ms, loop=0)
    print(out, len(frames), 'cuadros')


if __name__ == '__main__':
    main()
