# -*- coding: utf-8 -*-
"""split_ghost.py - parte ghost_player.dsl / ghost_recorder.dsl en {grafo: codigo} y copia la spec a Saved/, donde
AssetTools.read_file la puede leer desde el editor (solo lee bajo Saved/ o /Game, y solo .json/.py/.txt...).

Salida: VR_Test/Saved/ClaudeScripts/ghost/{ghost_spec.json, ghost_player_graphs.json, ghost_recorder_graphs.json}
Cada graphs.json = {"order": [refs], "code": {ref: codigo}}. Los eventos van juntos en el grafo EventGraph."""
import io
import json
import os
import re
import shutil

AQUI = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(AQUI, '..', '..', '..', '..', '..', 'VR_Test', 'Saved', 'ClaudeScripts', 'ghost'))
BS = chr(92)


def strip_comments(src):
    lines = []
    for ln in src.split('\n'):
        if ln.lstrip().startswith(';;'):
            continue
        ln = re.sub(r'\s+;;.*$', '', ln)
        lines.append(ln)
    return '\n'.join(lines)


def blocks(src):
    out = []
    i, n = 0, len(src)
    while i < n:
        if src[i] == '(':
            depth, j, instr = 0, i, False
            while j < n:
                c = src[j]
                if instr:
                    if c == BS:
                        j += 1
                    elif c == '"':
                        instr = False
                else:
                    if c == '"':
                        instr = True
                    elif c == '(':
                        depth += 1
                    elif c == ')':
                        depth -= 1
                        if depth == 0:
                            break
                j += 1
            out.append(src[i:j + 1])
            i = j + 1
        else:
            i += 1
    return out


def split(dsl, bp_ref):
    src = strip_comments(io.open(os.path.join(AQUI, dsl), encoding='utf-8').read())
    code, order, events = {}, [], []
    for b in blocks(src):
        m = re.match(r'\((fn|event)\s+([A-Za-z0-9_|]+)', b)
        if not m:
            continue
        kind, name = m.groups()
        if kind == 'event':
            events.append(b)
            continue
        g = bp_ref + ':' + ('UserConstructionScript' if name == 'ConstructionScript' else name)
        code[g] = b
        order.append(g)
    if events:
        g = bp_ref + ':EventGraph'
        code[g] = '\n'.join(events)
        order.append(g)
    return {'order': order, 'code': code}


def node_ids(dsl):
    """Los nombres de nodo (cabeza de cada lista con '|') que hay que verificar en el editor: todo menos las variables
    propias (Variables|<cat>|, salvo los componentes en Variables|Default|), las funciones propias y las de las clases
    de los fantasmas (el indice de find_node_types puede no tenerlas: gotcha §560; el write las resuelve igual)."""
    src = strip_comments(io.open(os.path.join(AQUI, dsl), encoding='utf-8').read())
    src = re.sub(r'"[^"]*"', '""', src)
    toks = re.findall(r'[^\s()"]+(?:\(\w+\))?|\(|\)', src)
    out = []
    for i, t in enumerate(toks):
        if i == 0 or toks[i - 1] != '(' or '|' not in t:
            continue
        if t.startswith('CallFunction|') or t.startswith('Class|BPGhost'):
            continue
        if t.startswith('Variables|') and not t.startswith('Variables|Default|'):
            continue
        if t not in out:
            out.append(t)
    return sorted(out)


def main():
    os.makedirs(OUT, exist_ok=True)
    shutil.copy(os.path.join(AQUI, 'ghost_spec.json'), os.path.join(OUT, 'ghost_spec.json'))
    G = '/Game/SoulCharger/Mechanics/Ghost/'
    for dsl, bp in [('ghost_player.dsl', 'BP_GhostPlayer_SC'), ('ghost_recorder.dsl', 'BP_GhostRecorder_SC')]:
        d = split(dsl, G + bp + '.' + bp)
        name = dsl.replace('.dsl', '_graphs.json')
        io.open(os.path.join(OUT, name), 'w', encoding='utf-8').write(json.dumps(d, ensure_ascii=False))
        print(name, len(d['order']), 'grafos')
    ids = {'ghost_player': node_ids('ghost_player.dsl'), 'ghost_recorder': node_ids('ghost_recorder.dsl')}
    io.open(os.path.join(OUT, 'node_ids.json'), 'w', encoding='utf-8').write(json.dumps(ids, ensure_ascii=False, indent=1))
    print('node_ids.json:', {k: len(v) for k, v in ids.items()})
    print('->', OUT)


if __name__ == '__main__':
    main()
