# chk_isvalid.py <codes.json...> - gotcha 590: marca sentencias del DSL cuya ejecucion puede terminar dentro de un IsValid
# y que tienen sentencias DESPUES (el writer las cuelga del else / las pierde). Uso: python chk_isvalid.py VR_Test/Saved/ClaudeScripts/Demo2/*_codes.json
import json, re, sys, os

TOK = re.compile(r'"(?:[^"\\]|\\.)*"|[()]|[^\s()]+')


def parse(s):
    st = [[]]
    for t in TOK.findall(s):
        if t == '(':
            st.append([])
        elif t == ')':
            x = st.pop()
            st[-1].append(x)
        else:
            st[-1].append(t)
    return st[0]


def ends_isvalid(x):
    """True si alguna rama de ejecucion de x termina adentro de un IsValid (la continuacion se pierde)"""
    if not isinstance(x, list) or not x or not isinstance(x[0], str):
        return False
    h = x[0]
    if h == 'Utilities|IsValid':
        return True
    if h in ('if', 'elif'):
        stm = [y for y in x[2:] if isinstance(y, list) and y and y[0] != 'elif']
        el = [y for y in x[2:] if isinstance(y, list) and y and y[0] == 'elif']
        return (bool(stm) and ends_isvalid(stm[-1])) or any(ends_isvalid(e) for e in el)
    if h.startswith(':'):
        stm = [y for y in x[1:] if isinstance(y, list)]
        return bool(stm) and ends_isvalid(stm[-1])
    return False


def walk(x, name, out):
    if not isinstance(x, list):
        return
    for i, y in enumerate(x):
        if isinstance(y, list) and ends_isvalid(y):
            later = [z for z in x[i + 1:] if isinstance(z, list) and z and z[0] != 'elif']
            if later and isinstance(x[0], str) and x[0] not in ('select', 'and', 'or'):
                out.append((name, str(y)[:100], str(later[0])[:100]))
        walk(y, name, out)


for f in sys.argv[1:]:
    d = json.load(open(f, encoding='utf-8'))
    codes = dict(d.get('codes', {}))
    if d.get('evg'):
        codes['EventGraph'] = d['evg']
    for n, c in codes.items():
        out = []
        for top in parse(c):
            walk(top, n, out)
        for o in out:
            print(os.path.basename(f), o[0], '|', o[1], '|| SIGUE:', o[2])
