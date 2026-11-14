# vs_cost.py - costo de VERTICES del valle v2 (y v1) calibrado contra la medicion de Heart v2
# (banco: vertices ~5,4 ms = m0 - m1, o 3,8 ms = m2 - m3, con 78.849 vertices) usando la misma regla de conteo.
import json, math
from pathlib import Path

OUT = Path(__file__).resolve().parent
ops = {r["camino"]: r for r in json.loads((OUT / "cost_ops.json").read_text())}
heart = json.loads((OUT / "heart_ops.json").read_text())


def radios_v2():
    S = 144
    qB, qC = 1 + 2 * math.pi / S, 1 + 0.6 * 2 * math.pi / S
    rs = [60.0 * j for j in range(1, 19)]
    r = rs[-1]
    while True:
        q = qB if r < 6000 else qC
        r2 = r * q
        if r2 >= 59000 - 0.5 * (r2 - r):
            break
        r = r2
        rs.append(r)
    rs.append(59000.0)
    rs += [59000 + 5000 * j / 4 for j in range(1, 5)]
    return rs, S


rs, S = radios_v2()
nv = 1 + len(rs) * S
print("v2: anillos %d, vertices %d, triangulos %d" % (len(rs), nv, S + 2 * S * (len(rs) - 1)))
print("   primeros geometricos %.2f ; ultimos %s" % (rs[18], [round(x, 1) for x in rs[-7:]]))


def band(r):
    H = 4500 < r < 26000
    F = 28000 < r < 59000
    Sw = 1500 < r < 59000
    if H and Sw:
        return "colinas+oleaje"
    if F and Sw:
        return "lejos+oleaje"
    if Sw:
        return "oleaje"
    return "ninguna"


cnt = {}
for r in rs:
    cnt[band(r)] = cnt.get(band(r), 0) + S
cnt["ninguna"] = cnt.get("ninguna", 0) + 1
print("   vertices por camino:", {k: "%d (%.1f %%)" % (v, 100.0 * v / nv) for k, v in cnt.items()})

# costo del camino 'ninguna': sqrt + comparaciones + retiro (dxc lo pliega a 0 porque h = 0 se conoce): se estima a mano
NONE = {"sfu": 1, "alu": 12}


def c(name, k):
    if name.endswith("ninguna"):
        return NONE["alu"] + k * NONE["sfu"]
    r = ops[name]
    return r["alu"] + k * r["sfu"]


res = {}
for k in (1, 4):
    hv = sum(cnt[b] * c("v2 ValleyHeightVS " + b, k) for b in cnt) / nv
    gv = sum(cnt[b] * c("v2 ValleyGradVS " + b, k) for b in cnt) / nv
    h1 = ops["v1 ValleyHeightVS"]["alu"] + k * ops["v1 ValleyHeightVS"]["sfu"]
    g1 = ops["v1 ValleyGradVS"]["alu"] + k * ops["v1 ValleyGradVS"]["sfu"]
    hh = heart["HeartHeightVS"]["alu"] + k * heart["HeartHeightVS"]["sfu"]
    hg = heart["HeartGradVS"]["alu"] + k * heart["HeartGradVS"]["sfu"]
    hx = heart["HeartXVS"]["alu"] + k * heart["HeartXVS"]["sfu"]
    # por vertice y por vista: pasada de dibujo (todas las salidas) + binning (solo la posicion = Height)
    w2 = nv * (hv + gv + hv)
    w1 = 15169 * (h1 + g1 + h1)
    wh = 78849 * (hh + hg + 2 * hx + hh)
    res[k] = dict(v2_por_vertice=hv + gv + hv, v1_por_vertice=h1 + g1 + h1, heart_por_vertice=hh + hg + 2 * hx + hh,
                  v2_total=w2, v1_total=w1, heart_total=wh,
                  v2_ms_si_heart_5p4=5.4 * w2 / wh, v2_ms_si_heart_3p8=3.8 * w2 / wh,
                  v1_ms_si_heart_5p4=5.4 * w1 / wh, v2_sobre_v1=w2 / w1)
    print("\nk(SFU) = %d  -> op-eq por vertice y vista (dibujo + binning):  v2 %.0f  v1 %.0f  Heart v2 %.0f"
          % (k, hv + gv + hv, h1 + g1 + h1, hh + hg + 2 * hx + hh))
    print("   trabajo total  v2/v1 = %.2f   v2/Heart = %.4f" % (w2 / w1, w2 / wh))
    print("   ms de vertices del valle v2, escalado de Heart (al reloj de Heart): %.2f (con 5,4 ms) / %.2f (con 3,8 ms)"
          % (5.4 * w2 / wh, 3.8 * w2 / wh))
    print("   a 456 MHz si Heart se midio a 640 MHz: x1,40 -> %.2f / %.2f ms" % (5.4 * w2 / wh * 640 / 456, 3.8 * w2 / wh * 640 / 456))
    print("   v1 escalado igual: %.2f ms (al reloj de Heart)" % (5.4 * w1 / wh))
# peor caso: todos los vertices pagan todas las capas (perillas que solapan bandas)
for k in (1, 4):
    worst = (ops["v2 ValleyHeightVS TODAS (peor)"]["alu"] + k * ops["v2 ValleyHeightVS TODAS (peor)"]["sfu"]) * 2 + \
            ops["v2 ValleyGradVS TODAS (peor)"]["alu"] + k * ops["v2 ValleyGradVS TODAS (peor)"]["sfu"]
    print("peor caso k=%d: %.0f op-eq por vertice (%.2fx el promedio con defaults)" % (k, worst, worst / res[k]["v2_por_vertice"]))
(OUT / "vs_cost.json").write_text(json.dumps({"conteo": cnt, "res": res}, indent=1), encoding="utf-8")
