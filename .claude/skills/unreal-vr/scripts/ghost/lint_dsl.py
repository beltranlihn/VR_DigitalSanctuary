# -*- coding: utf-8 -*-
"""lint_dsl.py - revisa un .dsl de Blueprint contra las trampas del parser que ya costaron viajes al editor.

Uso:  python lint_dsl.py archivo.dsl [spec.json BPNAME]

Chequea (references/dsl.md + gotchas):
  1. if / elif / for / while / switch / IsValid / cast con ramas terminan su lista de sentencias (nada despues).
  2. (bind x <literal>) no vale: el literal va inline.
  3. (CallFunction|X ...) propia: el primer argumento posicional es self o _self (sin self, el primer literal cae en
     el pin self y se pierde).
  4. (neg x) puede crear un restar vectorial: usar (* x -1.0).
  5. switch int: solo :0 :1 :2 :Default (nace con 3 salidas).
  6. Llamadas a funciones propias que no tienen su '(fn ...)' en el archivo.
  7. Con spec: variables Variables|Cat|Get/SetX que no estan declaradas (bool bX -> GetX) y parametros de fn.
  8. (v2) Literal pasado a una funcion PROPIA (dsl.md §4: se pierde en silencio) y cantidad de argumentos.
  9. (v2) Componentes de la spec = Variables|Default|Get<Comp>; Class|BPGhostPlayerSC|X y Class|BPGhostTakeSC|X contra
     la spec de esa clase.
"""
import io
import json
import re
import sys

BRANCHY = ('if', 'for', 'while', 'switch')


def tokens(txt):
    out = []
    for l in txt.split('\n'):
        if l.lstrip().startswith(';;'):
            continue
        l = re.sub(r'\s;;.*$', '', l)
        out.append(l)
    txt = '\n'.join(out)
    return re.findall(r':"[^"]*"|"[^"]*"|[^\s()"]+(?:\(\w+\))?|\(|\)', txt)


def parse(txt):
    toks = tokens(txt)
    pos = 0

    def one():
        nonlocal pos
        t = toks[pos]
        pos += 1
        if t == '(':
            lst = []
            while pos < len(toks) and toks[pos] != ')':
                lst.append(one())
            if pos >= len(toks):
                raise SyntaxError('parentesis sin cerrar')
            pos += 1
            return lst
        if t == ')':
            raise SyntaxError('parentesis de mas')
        return t
    out = []
    while pos < len(toks):
        out.append(one())
    return out


def is_literal(x):
    if isinstance(x, list):
        return False
    if x in ('true', 'false'):
        return True
    if x.startswith('"'):
        return True
    try:
        float(x)
        return True
    except ValueError:
        return False


def is_branch(stmt):
    if not isinstance(stmt, list) or not stmt:
        return False
    h = stmt[0]
    if not isinstance(h, str):
        return False
    if h in BRANCHY:
        return True
    if h == 'Utilities|IsValid':
        return True
    # un nodo con salidas de ejecucion con nombre (:then, :CastFailed, :"Is Valid"...)
    if any(isinstance(a, list) and a and isinstance(a[0], str) and a[0].startswith(':') for a in stmt[1:]):
        return True
    if h == 'bind' and len(stmt) >= 3 and is_branch(stmt[2]):
        return True
    return False


class Lint:
    def __init__(self, name):
        self.name = name
        self.errs = []
        self.calls = set()
        self.vars = set()
        self.callargs = []      # (fn, n_args_posicionales_sin_self, where)
        self.classrefs = set()

    def err(self, where, msg):
        self.errs.append('%s :: %s :: %s' % (self.name, where, msg))

    def stmts(self, lst, where):
        for i, s in enumerate(lst):
            if is_branch(s) and i != len(lst) - 1:
                self.err(where, 'rama que no es la ULTIMA de su lista: (%s ...) y siguen %d sentencias' % (s[0], len(lst) - 1 - i))
            self.stmt(s, where)

    def stmt(self, s, where):
        if not isinstance(s, list) or not s:
            return
        h = s[0]
        if h == 'bind':
            if len(s) >= 3 and is_literal(s[2]):
                self.err(where, 'bind de un literal: (bind %s %s)' % (s[1], s[2]))
            if len(s) >= 3:
                self.expr(s[2], where)
            for extra in s[3:]:
                self.branch_list(extra, where)
            return
        if h == 'if':
            self.expr(s[1], where)
            body = s[2:]
            self.body_with_elif(body, where + '/if')
            return
        if h in ('for', 'while'):
            if h == 'for':
                self.expr(s[2], where)
                self.stmts(s[3:], where + '/for')
            else:
                self.expr(s[1], where)
                self.stmts(s[2:], where + '/while')
            return
        if h == 'switch':
            kind = s[1]
            cases = [c for c in s[3:] if isinstance(c, list)]
            for c in cases:
                lab = c[0] if c else ''
                if kind == 'int' and lab not in (':0', ':1', ':2', ':Default'):
                    self.err(where, 'switch int con el caso %s: nace con 3 salidas (0,1,2)' % lab)
                self.stmts(c[1:], where + '/switch' + str(lab))
            return
        self.expr(s, where)
        for a in s[1:]:
            self.branch_list(a, where)

    def branch_list(self, a, where):
        if isinstance(a, list) and a and isinstance(a[0], str) and a[0].startswith(':'):
            self.stmts(a[1:], where + '/' + a[0])

    def body_with_elif(self, body, where):
        # (if c a b (elif c2 d (else e))) : elif/else solo como ultima forma
        for i, s in enumerate(body):
            if isinstance(s, list) and s and s[0] in ('elif', 'else'):
                if i != len(body) - 1:
                    self.err(where, '(%s ...) no es la ultima forma del cuerpo' % s[0])
                if s[0] == 'elif':
                    self.expr(s[1], where)
                    self.body_with_elif(s[2:], where + '/elif')
                else:
                    self.stmts(s[1:], where + '/else')
                return self.stmts(body[:i], where)
        self.stmts(body, where)

    def expr(self, e, where):
        if not isinstance(e, list) or not e:
            if isinstance(e, str) and e.startswith('Variables|'):
                self.vars.add(e)
            return
        h = e[0]
        if isinstance(h, str):
            if h == 'neg':
                self.err(where, '(neg x): usar (* x -1.0)')
            if h.startswith('Variables|'):
                self.vars.add(h)
            if h.startswith('Class|BPGhost'):
                self.classrefs.add((h, where))
            if h.startswith('CallFunction|'):
                fn = h.split('|', 1)[1]
                self.calls.add(fn)
                pos = [a for a in e[1:] if not (isinstance(a, str) and a.startswith(':'))]
                if not pos or pos[0] not in ('self', '_self'):
                    self.err(where, 'CallFunction|%s sin self primero (los literales se pierden)' % fn)
                for a in pos[1:]:
                    if is_literal(a):
                        self.err(where, 'CallFunction|%s con el LITERAL %s: se pierde (dsl.md §4); pasar un valor cableado' % (fn, a))
                self.callargs.append((fn, len(pos) - 1, where))
        for a in e[1:]:
            if isinstance(a, list):
                if a and isinstance(a[0], str) and a[0].startswith(':'):
                    continue
                self.expr(a, where)


def run(path, spec=None, bpname=None):
    txt = io.open(path, encoding='utf-8').read()
    L = Lint(path.split('/')[-1].split('\\')[-1])
    try:
        forms = parse(txt)
    except SyntaxError as e:
        print('SINTAXIS:', e)
        return 1
    fns = {}
    for f in forms:
        if not isinstance(f, list) or not f:
            continue
        if f[0] == 'fn':
            fns[f[1]] = f[2] if isinstance(f[2], list) else []
            L.stmts(f[3:], f[1])
        elif f[0] == 'event':
            ev = f[1]
            rest = f[2:]
            if rest and isinstance(rest[0], list) and all(isinstance(x, str) for x in rest[0]) and rest[0] and not rest[0][0].startswith(('Variables|', 'CallFunction|')) and '|' not in rest[0][0]:
                rest = rest[1:]
            L.stmts(rest, 'event ' + ev)
    for c in sorted(L.calls):
        if c not in fns:
            L.err('llamadas', 'CallFunction|%s sin (fn %s ...) en el archivo' % (c, c))
    for fn, n, where in L.callargs:
        if fn in fns and n != len(fns[fn]):
            L.err(where, 'CallFunction|%s con %d argumentos y la fn tiene %d %s' % (fn, n, len(fns[fn]), fns[fn]))
    if spec and bpname:
        full = json.load(io.open(spec, encoding='utf-8'))
        sp = full[bpname]
        declared = set()
        for c in sp.get('components', []):
            declared.add('Variables|Default|Get%s' % c['name'])
        def members(bp):
            out = set(full[bp]['functions'].keys())
            for v in full[bp]['vars']:
                n = v['name']
                base = n[1:] if (v['type'] == 'bool' and n.startswith('b') and n[1:2].isupper()) else n
                out.add('Get' + base)
                out.add('Set' + base)
            return out
        cls = {'BPGhostPlayerSC': 'BP_GhostPlayer_SC', 'BPGhostTakeSC': 'BP_GhostTake_SC'}
        for h, where in sorted(L.classrefs):
            parts = h.split('|')
            bp = cls.get(parts[1])
            if bp and parts[2] not in members(bp):
                L.err(where, '%s no existe en la spec de %s' % (h, bp))
        for v in sp['vars']:
            n = v['name']
            cat = v['cat'].replace(' ', '')
            base = n[1:] if (v['type'] == 'bool' and n.startswith('b') and n[1:2].isupper()) else n
            declared.add('Variables|%s|Get%s' % (cat, base))
            declared.add('Variables|%s|Set%s' % (cat, base))
        for u in sorted(L.vars):
            if u not in declared:
                L.err('variables', 'no declarada en la spec: ' + u)
        for fn, params in fns.items():
            if fn == 'ConstructionScript':
                continue
            want = sp['functions'].get(fn)
            if want is None:
                L.err('funciones', '(fn %s) no esta en la spec' % fn)
                continue
            names = [p['name'] for p in want]
            if names != params:
                L.err('funciones', '%s: params DSL %s != spec %s' % (fn, params, names))
        for fn in sp['functions']:
            if fn not in fns:
                L.err('funciones', 'spec declara %s y el DSL no lo escribe' % fn)
    for e in L.errs:
        print(e)
    print('%s: %d funciones, %d llamadas, %d variables usadas, %d errores' % (L.name, len(fns), len(L.calls), len(L.vars), len(L.errs)))
    return 1 if L.errs else 0


if __name__ == '__main__':
    a = sys.argv[1:]
    sys.exit(run(a[0], a[1] if len(a) > 2 else None, a[2] if len(a) > 2 else None))
