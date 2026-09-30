# -*- coding: utf-8 -*-
"""alma_aura_model.py - el AURA de Alma: modelo de referencia (semillas, codificacion en la malla y el vertex shader en
numpy). Lo usan gen_alma_aura.py (la malla) y el chequeo de abajo (python alma_aura_model.py). 2026-09-30.

QUE ES. Una nube de N motas diminutas y muy translucidas alrededor de Alma, en un cascaron de 1,3 a 1,8 radios, que se
mueven con CURL NOISE (el rotor de un potencial de senos: un flujo sin divergencia, las motas vecinas se mueven juntas
como humo) mas un giro lento y diferencial del cascaron. Todo vive en el vertex shader (scripts/hlsl/AuraVS.hlsl): un
draw call, cero CPU, se anima en el viewport del editor. Receta de la gotcha 477 (SM_LovingDust_SC / SM_ValleyDust_SC).

ESPACIO. La malla va en un componente `Aura` colgado del `Body` de BP_Alma_SC, asi que hereda su escala (Size) y su
aparicion: las unidades de la malla son las del Body, donde SM_AlmaSphere tiene RADIO 50. El cascaron va de 65 a 90.

CODIFICACION (invariante a la V invertida del importador, gotcha 302, y a las UV en fp16):
  posicion = centro de la mota + esquina (0, +-0,2, +-0,2)       el VS resta la esquina (la saca de la U de UV0)
  UV0 = (esquina k 0..3, 0.5)   UV1 = (b, ph1)   UV2 = (tw, ph2)   (lo asimetrico en U; en V solo fases uniformes)
  esquinas k = 0 (-,-), 1 (+,-), 2 (+,+), 3 (-,+) en (Y, Z)
"""
import numpy as np

K = dict(N=900, RIn=66.0, ROut=90.0, Corner=0.2, Seed=20260930)

# parametros del material (defaults de M_AlmaAura_SC) y sus grupos
MAT = {
    "AuraAlpha": 0.35, "SizeDeg": 0.16, "SizeMinDeg": 0.10, "SizeVar": 0.35, "Twinkle": 0.45,
    "ShellScale": 1.0, "Breath": 0.03, "ColA": (1.0, 0.94, 0.86), "ColB": (1.0, 0.80, 0.62), "AuraGlow": 1.0,
    "CurlAmp": 5.5, "CurlFreq": 1.6, "FlowSpeed": 0.35, "SwirlSpeed": 0.08,
    "SpeakCurl": 0.6, "SpeakExpand": 0.05, "SpeakGlow": 0.6,
}
MAT_INTERNO = {"AuraSpeak": 0.0, "AuraPhase": 0.0, "AuraReveal": 1.0}
GRUPOS = {}
for _k in ("AuraAlpha", "SizeDeg", "SizeMinDeg", "SizeVar", "Twinkle", "ShellScale", "Breath", "ColA", "ColB", "AuraGlow"):
    GRUPOS[_k] = "1 - Nube"
for _k in ("CurlAmp", "CurlFreq", "FlowSpeed", "SwirlSpeed"):
    GRUPOS[_k] = "2 - Curl"
for _k in ("SpeakCurl", "SpeakExpand", "SpeakGlow"):
    GRUPOS[_k] = "3 - Voz"
for _k in MAT_INTERNO:
    GRUPOS[_k] = "9 - Interno (lo escribe el BP)"


def corner_xy(k):
    k = np.floor(np.asarray(k) + 0.5)
    cx = (k >= 0.5) * (k <= 2.5) * 1.0
    cy = (k >= 1.5) * 1.0
    return cx, cy


def seeds():
    rng = np.random.default_rng(K["Seed"])
    n = K["N"]
    i = np.arange(n) + 0.5
    # esfera de Fibonacci + un poco de ruido (sin reticula visible)
    z = 1.0 - 2.0 * i / n
    phi = np.pi * (3.0 - np.sqrt(5.0)) * i
    rxy = np.sqrt(np.maximum(1.0 - z * z, 0.0))
    d = np.stack([rxy * np.cos(phi), rxy * np.sin(phi), z], 1)
    d += rng.normal(0.0, 0.06, d.shape)
    d /= np.linalg.norm(d, axis=1, keepdims=True)
    u = rng.random(n)
    r = K["RIn"] + (K["ROut"] - K["RIn"]) * u ** 1.3      # mas densas cerca del borde interior
    P0 = d * r[:, None]
    return dict(P0=P0, b=rng.random(n), ph1=rng.random(n), tw=rng.random(n), ph2=rng.random(n))


def encode(sd):
    n = sd["P0"].shape[0]
    k = np.tile(np.arange(4.0), n)
    idx = np.repeat(np.arange(n), 4)
    cx, cy = corner_xy(k)
    c = K["Corner"]
    LP = sd["P0"][idx] + np.stack([np.zeros(4 * n), (2 * cx - 1) * c, (2 * cy - 1) * c], 1)
    return dict(LP=LP, UV0=np.stack([k, np.full(4 * n, 0.5)], 1),
                UV1=np.stack([sd["b"][idx], sd["ph1"][idx]], 1),
                UV2=np.stack([sd["tw"][idx], sd["ph2"][idx]], 1), idx=idx)


def flip_half(enc):
    """Como llega a Unreal: V invertida (gotcha 302) y UV en fp16."""
    out = dict(enc)
    for c in ("UV0", "UV1", "UV2"):
        uv = np.stack([enc[c][:, 0], 1.0 - enc[c][:, 1]], 1)
        out[c] = uv.astype(np.float16).astype(np.float64)
    return out


def aura_vs(enc, camL, Tt, phase=0.0, speak=0.0, reveal=1.0, mat=None):
    """Lo mismo que AuraVS.hlsl, vectorizado por vertice. Devuelve dict con P (centro animado), dst, al, hsz."""
    q_ = dict(MAT)
    if mat:
        q_.update(mat)
    m = q_
    LP = enc["LP"]
    k = np.floor(enc["UV0"][:, 0] + 0.5)
    cx, cy = corner_xy(k)
    P0 = LP - np.stack([np.zeros(len(k)), (2 * cx - 1) * 0.2, (2 * cy - 1) * 0.2], 1)
    bs, ph1 = enc["UV1"][:, 0], enc["UV1"][:, 1]
    tws, ph2 = enc["UV2"][:, 0], enc["UV2"][:, 1]
    sp = np.clip(speak, 0, 1)
    rv = np.clip(reveal, 0, 1)
    Tf = Tt + phase
    ax = np.array([0.35 * np.sin(0.041 * Tf + 1.3), 0.45 * np.cos(0.029 * Tf + 0.4), 1.0])
    ax /= np.linalg.norm(ax)
    th = Tf * m["SwirlSpeed"] * (0.6 + 0.8 * np.mod(bs * 3.7 + ph1, 1.0))
    sth, cth = np.sin(th)[:, None], np.cos(th)[:, None]
    Pr = P0 * cth + np.cross(np.broadcast_to(ax, P0.shape), P0) * sth + ax[None, :] * (P0 @ ax)[:, None] * (1 - cth)
    Pr = Pr * (m["ShellScale"] * (1.0 + m["Breath"] * np.sin(0.45 * Tf + 2 * np.pi * ph2) + m["SpeakExpand"] * sp))[:, None]
    q = Pr * (m["CurlFreq"] / 50.0)
    t1 = Tf * m["FlowSpeed"]
    C1 = np.stack([1.5 * np.cos(1.5 * q[:, 1] + 0.71 * t1 + 0.9) - 1.7 * np.cos(1.7 * q[:, 2] - 0.53 * t1 + 2.9),
                   1.9 * np.cos(1.9 * q[:, 2] + 0.61 * t1 + 4.2) - 2.0 * np.cos(2.0 * q[:, 0] - 0.67 * t1 + 3.3),
                   1.1 * np.cos(1.1 * q[:, 0] + 0.83 * t1 + 5.1) - 1.3 * np.cos(1.3 * q[:, 1] - 0.97 * t1 + 0.4)], 1)
    q2 = q * 2.13 + np.array([3.1, 1.7, 5.3])
    t2 = t1 * 1.37
    C2 = np.stack([1.5 * np.cos(1.5 * q2[:, 1] - 0.59 * t2 + 2.2) - 1.7 * np.cos(1.7 * q2[:, 2] + 0.77 * t2 + 0.3),
                   1.9 * np.cos(1.9 * q2[:, 2] - 0.87 * t2 + 1.6) - 2.0 * np.cos(2.0 * q2[:, 0] + 0.49 * t2 + 5.7),
                   1.1 * np.cos(1.1 * q2[:, 0] - 0.63 * t2 + 3.9) - 1.3 * np.cos(1.3 * q2[:, 1] + 0.91 * t2 + 2.6)], 1)
    D = (C1 + 0.45 * C2) * (m["CurlAmp"] * (1.0 + m["SpeakCurl"] * sp) / 2.8)
    P = Pr + D
    tw = 1.0 - m["Twinkle"] * 0.5 * (1.0 + np.sin(Tf * (0.35 + 0.5 * tws) + 2 * np.pi * ph1))
    br = 0.45 + 0.55 * np.mod(bs * 7.1 + ph2, 1.0)
    Dv = P - np.asarray(camL)[None, :]
    dist = np.maximum(np.linalg.norm(Dv, axis=1), 1e-3)
    nearF = np.clip((dist - 8.0) / 22.0, 0, 1)
    nearF = nearF * nearF * (3 - 2 * nearF)
    al = np.minimum(m["AuraAlpha"] * br * tw * (1.0 + m["SpeakGlow"] * sp) * rv * nearF, 0.9)
    sdeg = np.maximum(m["SizeDeg"] * (1.0 + m["SizeVar"] * (2.0 * np.mod(bs * 3.1 + ph1, 1.0) - 1.0)) * (1.0 + 0.25 * sp),
                      m["SizeMinDeg"])
    hsz = 0.5 * dist * np.tan(np.radians(sdeg)) * np.clip(rv * 2.0, 0, 1) * (al >= 0.002)
    return dict(P0=P0, P=P, D=D, al=al, hsz=hsz, dist=dist, sdeg=sdeg)


if __name__ == "__main__":
    sd = seeds()
    enc = flip_half(encode(sd))
    camL = np.array([-575.0, 0.0, 0.0])   # 2,3 m al frente con escala 0,4 del Body: 230 cm / 0,4
    ok = True
    for T in (0.0, 37.3, 612.9):
        for sp in (0.0, 1.0):
            r = aura_vs(enc, camL, T, phase=0.0, speak=sp)
            bad = not (np.isfinite(r["P"]).all() and np.isfinite(r["hsz"]).all())
            ok = ok and not bad
            rad = np.linalg.norm(r["P"][::4], axis=1)
            dmag = np.linalg.norm(r["D"][::4], axis=1)
            print("T=%6.1f habla=%.0f  radio %.1f..%.1f (x0,4 = %.1f..%.1f cm)  curl rms %.2f max %.2f (unid.)  alfa %.3f..%.3f"
                  "  tamano %.3f..%.3f grados  %s" % (T, sp, rad.min(), rad.max(), rad.min() * 0.4, rad.max() * 0.4,
                                                      np.sqrt((dmag ** 2).mean()), dmag.max(), r["al"].min(), r["al"].max(),
                                                      r["sdeg"].min(), r["sdeg"].max(), "NaN!" if bad else "ok"))
    # velocidad media de una mota (cm/s de mundo, escala 0,4)
    a = aura_vs(enc, camL, 100.0)["P"][::4]
    b = aura_vs(enc, camL, 100.1)["P"][::4]
    v = np.linalg.norm(b - a, axis=1) / 0.1 * 0.4
    a2 = aura_vs(enc, camL, 100.0, phase=0.0, speak=1.0)["P"][::4]
    b2 = aura_vs(enc, camL, 100.1, phase=0.12, speak=1.0)["P"][::4]   # AuraSpeakRate 1,2: +0,12 de fase en 0,1 s
    v2 = np.linalg.norm(b2 - a2, axis=1) / 0.1 * 0.4
    print("velocidad en reposo %.2f cm/s (p95 %.2f)  hablando %.2f cm/s (p95 %.2f)" % (v.mean(), np.percentile(v, 95),
                                                                                    v2.mean(), np.percentile(v2, 95)))
    print("CHEQUEO", "OK" if ok else "FALLA")
