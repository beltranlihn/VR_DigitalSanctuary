# split_journey.py - parte journey_content_body.dsl en {grafo: codigo} para el script de escritura del editor.
import re, json, io, os
ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, '..', '..', '..', '..', '.claude', 'skills', 'unreal-vr', 'scripts', 'journey_content_body.dsl')
src = io.open(os.path.normpath(SRC), encoding='utf-8').read()
rep = {
    'Canvas|TextSize': 'Canvas|ClippedTextSize',
    'Math|Color|MakeLinearColor': 'Utilities|Struct|MakeLinearColor',
    'Math|Conversions|ToString(Integer)': 'Utilities|String|ToString(Integer)',
    'Utilities|String|Concatenate': 'Utilities|String|Append',
    'Math|Color|LinearColorLerp': 'Math|Color|Lerp(LinearColor)',
    'Utilities|GetActorOfClass': 'Actor|GetActorOfClass',
}
for a, b in rep.items():
    src = src.replace(a, b)
lines = []
for ln in src.split('\n'):
    if ln.lstrip().startswith(';;'):
        continue
    ln = re.sub(r'\s+;;.*$', '', ln)
    lines.append(ln)
src = '\n'.join(lines)
BS = chr(92)
blocks = []
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
        blocks.append(src[i:j + 1])
        i = j + 1
    else:
        i += 1
B = '/Game/SoulCharger/Mechanics/Results/BP_JourneyContent_SC.BP_JourneyContent_SC:'
code, order = {}, []
for b in blocks:
    m = re.match(r'\((fn|event)\s+([A-Za-z0-9_|]+)', b)
    if not m:
        continue
    kind, name = m.groups()
    if kind == 'event':
        g = B + 'EventGraph'
    elif name == 'ConstructionScript':
        g = B + 'UserConstructionScript'
    else:
        g = B + name
    code[g] = b
    order.append(g)
code[B + 'JcSetTex'] = '(fn JcSetTex (M Tx)\n  (Rendering|Material|SetTextureParameterValue M "Card" Tx))'
code[B + 'JcSetFade'] = '(fn JcSetFade (M V)\n  (Rendering|Material|SetScalarParameterValue M "Fade" V))'
order = [B + 'JcSetTex', B + 'JcSetFade'] + order
out = os.path.join(ROOT, 'journey_graphs.json')
json.dump({'order': order, 'code': code}, io.open(out, 'w', encoding='utf-8'), ensure_ascii=False)
print(len(order), 'grafos:', [o.split(':')[-1] for o in order])
