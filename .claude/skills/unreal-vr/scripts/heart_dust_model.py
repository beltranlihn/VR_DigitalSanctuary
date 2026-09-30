# -*- coding: utf-8 -*-
"""heart_dust_model.py - el POLVO de la etapa del latido: modelo de referencia (semillas, codificacion en la malla y el
vertex shader en numpy). Lo usan gen_heart_dust.py (la malla), plan_heart_dust.py (el material) y el chequeo de abajo
(python heart_dust_model.py). 2026-10-01, pedido de Beltran: "agrega particulas y polvo que ayuden a entender que
estamos girando".

QUE ES. Motas FIJAS al mar (espacio local de BP_HeartScape_SC: origen = la esfera central, z = 0 el agua). Cuando la
VUELTA rota y baja el actor, las motas cercanas pasan de costado y las lejanas despacio: el paralaje dice "estoy girando
y subiendo". Dos poblaciones en UNA malla y UN draw call (receta de la gotcha 477, como el aura de Alma):
  kind 0 = POLVO: muchas, diminutas, casi transparentes.
  kind 1 = PARTICULAS: pocas, un poco mas grandes y brillantes, con titileo lento.
Casi quietas (una deriva de pocos cm): si se movieran mucho, se leeria el viento y no el giro.

ESPACIO. El espectador esta en local (-600, 0, ~140) al empezar; la vuelta lo aleja hasta ~1200 del centro y lo sube
~400. Las motas llenan un anillo alrededor del centro, densas donde pasa el espectador.

CODIFICACION (invariante a la V invertida del importador, gotcha 302, y a las UV en fp16):
  posicion = centro de la mota + esquina (0, +-0,2, +-0,2)       el VS resta la esquina (la saca de la U de UV0)
  UV0 = (esquina k 0..3, 0.5)   UV1 = (kind 0/1, ph1)   UV2 = (b, ph2)
"""
import numpy as np

K = dict(ND=3900, NS=500, Corner=0.2, Seed=20261001,
         RIn=150.0, ROut=2800.0, RCoreIn=400.0, RCoreOut=1400.0, ZLo=10.0, ZHi=950.0, ZCoreLo=60.0, ZCoreHi=620.0,
         CoreFrac=0.8)

MAT = {
    "DustAlpha": 0.22, "DustSizeDeg": 0.10, "DustColor": (1.0, 0.88, 0.84),
    "SparkAlpha": 0.55, "SparkSizeDeg": 0.20, "SparkColor": (1.0, 0.72, 0.66), "Twinkle": 0.6,
    "SizeMinDeg": 0.07, "SizeVar": 0.35,
    "DriftAmp": 6.0, "DriftSpeed": 0.18,
    "NearFade": 60.0, "FarFade": 2600.0, "Glow": 1.0,
}
MAT_INTERNO = {"DustReveal": 1.0}
GRUPOS = {}
for _k in ("DustAlpha", "DustSizeDeg", "DustColor"):
    GRUPOS[_k] = "1 - Polvo"
for _k in ("SparkAlpha", "SparkSizeDeg", "SparkColor", "Twinkle"):
    GRUPOS[_k] = "2 - Particulas"
for _k in ("SizeMinDeg", "SizeVar", "DriftAmp", "DriftSpeed", "NearFade", "FarFade", "Glow"):
    GRUPOS[_k] = "3 - Comun"
for _k in MAT_INTERNO:
    GRUPOS[_k] = "9 - Interno (lo escribe el BP)"


def corner_xy(k):
    k = np.floor(np.asarray(k) + 0.5)
    cx = (k >= 0.5) * (k <= 2.5) * 1.0
    cy = (k >= 1.5) * 1.0
    return cx, cy


def _ring(rng, n, r0, r1, z0, z1):
    th = rng.random(n) * 2 * np.pi
    r = np.sqrt(r0 * r0 + (r1 * r1 - r0 * r0) * rng.random(n))     # uniforme en AREA
    z = z0 + (z1 - z0) * rng.random(n)
    return np.stack([r * np.cos(th), r * np.sin(th), z], 1)


def seeds():
    rng = np.random.default_rng(K["Seed"])
    n = K["ND"] + K["NS"]
    nc = int(round(n * K["CoreFrac"]))
    P = np.concatenate([_ring(rng, nc, K["RCoreIn"], K["RCoreOut"], K["ZCoreLo"], K["ZCoreHi"]),
                        _ring(rng, n - nc, K["RIn"], K["ROut"], K["ZLo"], K["ZHi"])])
    rng.shuffle(P)
    kind = np.zeros(n)
    kind[rng.choice(n, K["NS"], replace=False)] = 1.0
    return dict(P0=P, kind=kind, ph1=rng.random(n), b=rng.random(n), ph2=rng.random(n))


def encode(sd):
    n = sd["P0"].shape[0]
    k = np.tile(np.arange(4.0), n)
    idx = np.repeat(np.arange(n), 4)
    cx, cy = corner_xy(k)
    c = K["Corner"]
    LP = sd["P0"][idx] + np.stack([np.zeros(4 * n), (2 * cx - 1) * c, (2 * cy - 1) * c], 1)
    return dict(LP=LP, UV0=np.stack([k, np.full(4 * n, 0.5)], 1),
                UV1=np.stack([sd["kind"][idx], sd["ph1"][idx]], 1),
                UV2=np.stack([sd["b"][idx], sd["ph2"][idx]], 1), idx=idx)


def flip_half(enc):
    out = dict(enc)
    for c in ("UV0", "UV1", "UV2"):
        uv = np.stack([enc[c][:, 0], 1.0 - enc[c][:, 1]], 1)
        out[c] = uv.astype(np.float16).astype(np.float64)
    return out


def dust_vs(enc, camL, Tt, reveal=1.0, mat=None):
    """Lo mismo que HeartDustVS.hlsl, vectorizado por vertice."""
    m = dict(MAT)
    if mat:
        m.update(mat)
    LP = enc["LP"]
    k = np.floor(enc["UV0"][:, 0] + 0.5)
    cx, cy = corner_xy(k)
    P0 = LP - np.stack([np.zeros(len(k)), (2 * cx - 1) * 0.2, (2 * cy - 1) * 0.2], 1)
    kind = np.floor(enc["UV1"][:, 0] + 0.5)
    ph1 = enc["UV1"][:, 1]
    bs, ph2 = enc["UV2"][:, 0], enc["UV2"][:, 1]
    rv = np.clip(reveal, 0, 1)
    t = Tt * m["DriftSpeed"]
    D = m["DriftAmp"] * np.stack([np.sin(t * (0.7 + 0.6 * bs) + 6.2831853 * ph1),
                                  np.sin(t * (0.9 + 0.5 * ph2) + 6.2831853 * ph2 + 1.7),
                                  0.6 * np.sin(t * (0.5 + 0.4 * ph1) + 6.2831853 * bs + 3.1)], 1)
    P = P0 + D
    Dv = P - np.asarray(camL)[None, :]
    dist = np.maximum(np.linalg.norm(Dv, axis=1), 1e-3)
    nf = np.clip((dist - 0.35 * m["NearFade"]) / (0.65 * m["NearFade"]), 0, 1)
    nf = nf * nf * (3 - 2 * nf)
    ff = np.clip((m["FarFade"] - dist) / (0.35 * m["FarFade"]), 0, 1)
    ff = ff * ff * (3 - 2 * ff)
    tw = 1.0 - m["Twinkle"] * 0.5 * (1.0 + np.sin(Tt * (0.4 + 0.6 * bs) + 6.2831853 * ph1))
    br = 0.5 + 0.5 * np.mod(bs * 7.3 + ph2, 1.0)
    a0 = np.where(kind > 0.5, m["SparkAlpha"] * tw, m["DustAlpha"]) * br
    al = np.minimum(a0 * nf * ff * rv, 0.9)
    s0 = np.where(kind > 0.5, m["SparkSizeDeg"], m["DustSizeDeg"])
    sdeg = np.maximum(s0 * (1.0 + m["SizeVar"] * (2.0 * np.mod(bs * 3.1 + ph1, 1.0) - 1.0)), m["SizeMinDeg"])
    hsz = 0.5 * dist * np.tan(np.radians(sdeg)) * (al >= 0.002)
    return dict(P0=P0, P=P, D=D, al=al, hsz=hsz, dist=dist, sdeg=sdeg, kind=kind)


if __name__ == "__main__":
    sd = seeds()
    enc = flip_half(encode(sd))
    ok = True
    for camL in (np.array([-600.0, 0.0, 140.0]), np.array([-1200.0, 0.0, 540.0])):
        for T in (0.0, 37.3, 912.9):
            r = dust_vs(enc, camL, T)
            bad = not (np.isfinite(r["P"]).all() and np.isfinite(r["hsz"]).all())
            ok = ok and not bad
            vis = r["al"][::4] > 0.002
            near = (r["dist"][::4] < 400) & vis
            print("cam %s T=%6.1f  visibles %d (cerca <4 m: %d)  alfa max %.2f  tamano %.3f..%.3f grados  deriva max %.1f cm  %s"
                  % (camL.astype(int), T, vis.sum(), near.sum(), r["al"].max(), r["sdeg"].min(), r["sdeg"].max(),
                     np.abs(r["D"]).max(), "NaN!" if bad else "ok"))
    kind = sd["kind"]
    print("polvo %d  particulas %d  verts %d" % ((kind < 0.5).sum(), (kind > 0.5).sum(), enc["LP"].shape[0]))
    print("CHEQUEO", "OK" if ok else "FALLA")
