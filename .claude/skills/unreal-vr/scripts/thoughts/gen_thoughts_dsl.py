import re, json, sys, os
# gen_thoughts_dsl.py (2026-10-30) - copia de Feed/gen_feed_dsl.py para BP_ThoughtsDirector_SC. Las categorias salen de VARS de
# build_thoughts.py (una sola lista). Expande (G X)/(S X v) y escribe thoughts_dsl.json.
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, '.')
from build_thoughts import VARS
CAT = {}
for n, t, c, ed, arr in VARS:
    key = n[1:] if (n.startswith('b') and n[1:2].isupper()) else n
    if key in CAT: sys.exit('collision ' + key)
    CAT[key] = c
src = open('thoughts_src.dsl', encoding='utf-8').read()
blocks, cur = {}, None
for line in src.splitlines():
    m = re.match(r';;@\s*(\S+)', line)
    if m:
        cur = m.group(1); blocks[cur] = []; continue
    if line.strip().startswith(';;') or cur is None: continue
    blocks[cur].append(line)
def expand(code):
    def g(m):
        n = m.group(1)
        if n not in CAT: raise SystemExit('unknown var ' + n)
        return '(Variables|%s|Get%s)' % (CAT[n], n)
    def s(m):
        n = m.group(1)
        if n not in CAT: raise SystemExit('unknown var ' + n)
        return '(Variables|%s|Set%s ' % (CAT[n], n)
    code = re.sub(r'\(G ([A-Za-z0-9]+)\)', g, code)
    code = re.sub(r'\(S ([A-Za-z0-9]+) ', s, code)
    return code
out = {k: expand('\n'.join(v).strip()) for k, v in blocks.items()}
for k, v in out.items():
    if v.count('(') != v.count(')'): sys.exit('paren mismatch in ' + k)
    if '(G ' in v or '(S ' in v: sys.exit('unexpanded in ' + k)
json.dump(out, open('thoughts_dsl.json', 'w', encoding='utf-8'), indent=1)
print(len(out), 'graphs:', ', '.join(out.keys()))
