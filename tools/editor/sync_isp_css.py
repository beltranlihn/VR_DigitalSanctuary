"""Copy the design system of Immersive Studio Pro (VEATION) into the editor: index.html lines 16-1201 (its <style> block),
without comments, with a provenance header. Re-run when ISP's design system changes.
Usage: python tools/editor/sync_isp_css.py"""
import os, re, subprocess, time
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
ISP = os.path.abspath(os.path.join(ROOT, '..', 'Immersive Studio Pro'))
OUT = os.path.join(ROOT, 'web', 'editor-obra', 'app', 'css', 'isp.css')
lines = open(os.path.join(ISP, 'index.html'), encoding='utf-8').read().splitlines()
css = '\n'.join(lines[15:1201])
css = re.sub(r'/\*.*?\*/', '', css, flags=re.S)
css = '\n'.join(l.rstrip() for l in css.splitlines() if l.strip())
try:
    rev = subprocess.check_output(['git', '-C', ISP, 'rev-parse', '--short', 'HEAD'], text=True).strip()
except Exception:
    rev = 'unknown'
head = ('/* origin: Immersive Studio Pro (VEATION) index.html:16-1201 @%s, copied %s by tools/editor/sync_isp_css.py.\n'
        '   Do not edit here: change it in ISP and re-sync. The Soul Charger layer lives in editor.css. */\n') % (rev, time.strftime('%Y-%m-%d'))
os.makedirs(os.path.dirname(OUT), exist_ok=True)
open(OUT, 'w', encoding='utf-8').write(head + css + '\n')
print('isp.css', len(css), 'bytes @', rev)
