# -*- coding: utf-8 -*-
"""verify_outer.py - verificacion numerica de la envoltura exterior (V4 integrado: ameba con pseudopodos,
StrandCurl v4, particulas que se deslizan, Win.x minimo; revision 2026-09-28: GroupScale robusto, ancla
inclinada, suavidad p 8 -> 3 con default 0,8).

Para muchas configuraciones al azar (estado, tiempo, Agitation, tamanos, SizeVariation, curl, 1-10 grupos,
posiciones segun la geometria del BP) muestrea TODO lo que dibuja la celula:
  - membrana del nucleo (CentreR + 10 Mound + CentreGap)             -> 'nucleo'
  - pelicula del brazo = hebra + cuello + ENVOLTURA de la bolsa, los vertices REALES de LovingArmVS
    (7 bisecciones + secante, con el curl aplicado)                   -> 'brazo'
  - las bolas opacas (cada esfera completa: superconjunto de la union) -> 'bolas'
  - la nube de particulas (LovingDustVS, las 4 esquinas de cada sprite)-> 'polvo'
y mide el HUECO RADIAL hasta la envoltura: r(u) - |P - C| (analitica) y contra la malla TRIANGULADA
(icoesfera de 2562 y de 10242 vertices, radio por el triangulo plano que cruza el rayo).
Tambien reporta el hueco "euclideo" aproximado = hueco radial * (N . u).

Uso: python verify_outer.py [n_config] [semilla]
"""
import sys
import time
import numpy as np
import lvport as L

N_CFG = 300
SEED = 11
OUTER_MARGIN = 3.0


# ---------------------------------------------------------------- icoesfera con jerarquia
def icosphere_levels(levels):
    t = (1.0 + 5 ** 0.5) / 2.0
    V = np.array([[-1, t, 0], [1, t, 0], [-1, -t, 0], [1, -t, 0], [0, -1, t], [0, 1, t], [0, -1, -t], [0, 1, -t],
                  [t, 0, -1], [t, 0, 1], [-t, 0, -1], [-t, 0, 1]], float)
    V = V / np.linalg.norm(V, axis=1, keepdims=True)
    F = np.array([[0, 11, 5], [0, 5, 1], [0, 1, 7], [0, 7, 10], [0, 10, 11], [1, 5, 9], [5, 11, 4], [11, 10, 2],
                  [10, 7, 6], [7, 1, 8], [3, 9, 4], [3, 4, 2], [3, 2, 6], [3, 6, 8], [3, 8, 9], [4, 9, 5],
                  [2, 4, 11], [6, 2, 10], [8, 6, 7], [9, 8, 1]])
    # orientar hacia afuera
    for i, f in enumerate(F):
        a, b, c = V[f]
        if np.dot(np.cross(b - a, c - a), a + b + c) < 0:
            F[i] = [f[0], f[2], f[1]]
    verts = [v for v in V]
    Fs = [F]
    cache = {}

    def mid(i, j):
        key = (min(i, j), max(i, j))
        if key not in cache:
            m = verts[i] + verts[j]
            verts.append(m / np.linalg.norm(m))
            cache[key] = len(verts) - 1
        return cache[key]

    for _ in range(levels):
        Fn = []
        for a, b, c in Fs[-1]:
            ab, bc, ca = mid(a, b), mid(b, c), mid(c, a)
            Fn += [[a, ab, ca], [ab, b, bc], [ca, bc, c], [ab, bc, ca]]
        Fs.append(np.array(Fn))
    return np.array(verts), Fs


def locate(d, V, Fs):
    """indice del triangulo del ultimo nivel cuyo cono contiene cada direccion d."""
    def score(fidx):
        f = Fs_l[fidx]                          # (n, k, 3)
        a, b, c = V[f[..., 0]], V[f[..., 1]], V[f[..., 2]]
        dd = d[:, None, :]
        s1 = np.einsum('nkj,nkj->nk', np.cross(a, b), dd)
        s2 = np.einsum('nkj,nkj->nk', np.cross(b, c), dd)
        s3 = np.einsum('nkj,nkj->nk', np.cross(c, a), dd)
        return np.minimum(np.minimum(s1, s2), s3)
    n = len(d)
    Fs_l = Fs[0]
    cand = np.tile(np.arange(20), (n, 1))
    best = cand[np.arange(n), np.argmax(score(cand), axis=1)]
    for lvl in range(1, len(Fs)):
        Fs_l = Fs[lvl]
        cand = best[:, None] * 4 + np.arange(4)[None, :]
        best = cand[np.arange(n), np.argmax(score(cand), axis=1)]
    return best


def mesh_radius(d, C, V, F, rV, tri):
    """radio del triangulo PLANO desplazado a lo largo de d (desde C)."""
    f = F[tri]
    Pa = V[f[:, 0]] * rV[f[:, 0], None]
    Pb = V[f[:, 1]] * rV[f[:, 1], None]
    Pc = V[f[:, 2]] * rV[f[:, 2], None]
    nn = np.cross(Pb - Pa, Pc - Pa)
    return np.einsum('ij,ij->i', nn, Pa) / np.einsum('ij,ij->i', nn, d)


# ---------------------------------------------------------------- configuraciones
def hashf(n, a, b):
    return L.frac(np.sin(n * a + b) * 43758.5453)


def random_config(rng, defaults=False):
    c = {}
    if defaults:
        c.update(S=0.3, ph=rng.uniform(0, 2 * np.pi), Ag=0.0, GSz=1.0, Spread=1.0, CA=1.0, CS=1.0, Rc0=16.0,
                 MT=1.0, NA=1.0, OM=1.0, hug=0.8, SV=0.5, K=1.0, N=5, T=rng.uniform(0, 3000),
                 DustK=np.array([0.35, 0.55, 0.6, 2.0]), OuterK=np.array([3.0, 8.0, 0.8, 1.0]))
    else:
        c.update(S=rng.uniform(0, 1), ph=rng.uniform(0, 2 * np.pi), Ag=rng.uniform(0, 1), GSz=rng.uniform(0.6, 1.6),
                 Spread=rng.uniform(0.8, 1.3), CA=rng.uniform(0, 1.5), CS=rng.uniform(0.5, 2.0), Rc0=rng.uniform(12, 22),
                 MT=rng.uniform(0.3, 2.0), NA=rng.uniform(0, 2), OM=rng.uniform(0, 2), hug=rng.uniform(0, 1),
                 SV=rng.uniform(0, 1), K=rng.uniform(0, 2), N=int(rng.integers(1, 11)), T=rng.uniform(0, 5000),
                 DustK=np.array([rng.uniform(0.2, 0.6), 0.55, rng.uniform(0, 1.2), rng.uniform(0, 3.0)]),
                 OuterK=np.array([OUTER_MARGIN, rng.uniform(0, 15), rng.uniform(0, 1), rng.uniform(0, 2)]))
    return build_from(c, rng)


def build_from(c, rng):
    """arma LV0..LV5 y los 10 centroides M_i desde los escalares de c (receta de GroupTarget + vida)."""
    # margen efectivo: lo que el BP empuja (OuterMargin + holgura del polvo)
    dk = c['DustK']
    c['OuterK'][0] = OUTER_MARGIN + max(dk[3], 0) + 1.8 * max(dk[2], 0) + 2.0 * max(dk[0], 0)
    tilt = np.radians(15.0)
    Cc = rng.uniform(-6, 6, 3)
    c['LV0'] = np.array([Cc[0], Cc[1], Cc[2], c['Rc0']])
    c['LV1'] = np.array([c['S'], c['ph'], c['Ag'], 0.0])
    c['LV2'] = np.array([c['GSz'], c['Spread'], c['CA'], c['CS']])
    c['LV3'] = np.array([c['MT'], 1.0, c['NA'], c['OM']])
    c['LV4'] = np.array([np.cos(tilt), 0.0, np.sin(tilt), c['hug']])
    c['LV5'] = np.array([c['SV'], c['K'], 0.0, 0.0])
    sh = L.Shape(c['LV0'], c['LV1'], c['LV2'], c['LV3'])
    gC = L.CentreGap(c['LV1'], c['LV3'], sh['Rc'])
    N = c['N']
    s8 = np.clip(c['S'] / 0.8, 0, 1); sm = s8 * s8 * (3 - 2 * s8)
    Ms = []
    for i in range(10):
        ang = np.pi / 2 + 2 * np.pi * i / N + (hashf(i, 12.9898, 4.1414) - 0.5) * (2.8 / N)
        R = L.lerp(72.0, 48.0 * (1.15 - 0.15 * c['CA']), sm) * c['Spread'] * (0.86 + 0.28 * hashf(i, 7.2331, 1.731))
        R += rng.uniform(-8, 8)                       # vaiven radial + ruido
        ang += rng.uniform(-3, 3) / max(R, 1)          # vaiven tangencial
        dj = (hashf(i, 3.9173, 2.517) - 0.5) * 28.0 + rng.uniform(-8, 8)
        gs = L.GroupScale(float(i), c['LV5'])
        Rbag = (1.85 * 1.12 * 1.2 * 3.4 * c['GSz'] + 0.9 * 3.4 * c['GSz']) * gs
        Wob = L.CoreWob(c['LV1'], c['LV3'])            # V4: el nucleo llega a Rc(1 + A) + MoundH (RMin del BP)
        R = max(R, sh['Rc'] * (1.0 + Wob[0]) + sh['MoundH'] + gC + Rbag + 4.0)   # RMin/RShift: la bolsa no pisa el nucleo
        X = np.cos(tilt) * dj - np.sin(ang) * R * np.sin(tilt)
        Y = np.cos(ang) * R
        Z = np.sin(ang) * R * np.cos(tilt) + dj * np.sin(tilt)
        G = Cc + np.array([X, Y, Z])
        Ms.append(np.array([G[0], G[1], G[2], 1.0 if i < N else 0.0]))
    c['Ms'] = Ms
    return c


def sample_all(c, rng, dense=False):
    LV0, LV1, LV2, LV3, LV4, LV5, Ms, T = c['LV0'], c['LV1'], c['LV2'], c['LV3'], c['LV4'], c['LV5'], c['Ms'], c['T']
    C = LV0[:3]
    out = {}
    u = L.fib_sphere(2000)
    rcm, _, _ = L.core_film_r(u, LV0, LV1, LV2, LV3, Ms, T)
    out['nucleo'] = C + u * rcm[:, None]
    arms, balls = [], []
    for k in range(10):
        if Ms[k][3] < 0.5:
            continue
        if dense:
            dst, AP, B, _ = L.arm_surface(Ms[k][:3], float(k), LV0, LV1, LV2, LV3, LV4, LV5, T, rings=208, sides=72, iters=12)
        else:
            dst, AP, B, _ = L.arm_surface(Ms[k][:3], float(k), LV0, LV1, LV2, LV3, LV4, LV5, T)
        arms.append(dst)
        balls.append(L.balls_points(Ms[k][:3], float(k), LV0, LV1, LV2, LV3, LV4, LV5, T))
    out['brazo'] = np.concatenate(arms, 0)
    out['bolas'] = np.concatenate(balls, 0)
    CamL = np.array([170.0, 0.0, 0.0])
    out['polvo'] = L.dust_points(LV0, LV1, LV2, LV3, LV4, LV5, Ms, T, c['DustK'], CamL, rng=rng)
    return out


def main():
    rng = np.random.default_rng(SEED)
    V4, F4 = icosphere_levels(4)
    V5, F5 = icosphere_levels(5)
    print("icoesferas: nivel 4 -> %d verts, nivel 5 -> %d verts" % (len(V4), len(V5)))
    cats = ['nucleo', 'brazo', 'bolas', 'polvo']
    worst = {k: (1e9, None) for k in cats}
    worstE = {k: 1e9 for k in cats}
    worstM4 = {k: 1e9 for k in cats}
    worstM5 = {k: 1e9 for k in cats}
    worstRel = {k: 1e9 for k in cats}
    rmax_all, rmin_all, chord4, chord5 = [], [], [], []
    t0 = time.time()
    for ci in range(N_CFG):
        c = random_config(rng, defaults=(ci < N_CFG // 10))
        pts = sample_all(c, rng, dense=(ci % 25 == 0))
        C = c['LV0'][:3]
        # malla: radios en los vertices
        rV4, _ = L.outer_r(V4, c['LV0'], c['LV1'], c['LV2'], c['LV3'], c['LV5'], c['Ms'], c['OuterK'], c['T'], LV4=c['LV4'])
        rV5, _ = L.outer_r(V5, c['LV0'], c['LV1'], c['LV2'], c['LV3'], c['LV5'], c['Ms'], c['OuterK'], c['T'], LV4=c['LV4'])
        rmax_all.append(rV5.max()); rmin_all.append(rV5.min())
        for k in cats:
            P = pts[k] - C
            dist = np.linalg.norm(P, axis=1)
            d = P / dist[:, None]
            r, N = L.outer_r(d, c['LV0'], c['LV1'], c['LV2'], c['LV3'], c['LV5'], c['Ms'], c['OuterK'], c['T'], LV4=c['LV4'])
            gap_r = r - dist
            relm = gap_r - (OUTER_MARGIN if k == 'polvo' else c['OuterK'][0])
            worstRel[k] = min(worstRel[k], np.min(relm))
            i = np.argmin(gap_r)
            if gap_r[i] < worst[k][0]:
                worst[k] = (gap_r[i], dict(cfg=ci, S=c['S'], N=c['N'], K=c['K'], SV=c['SV'], Ag=c['Ag'], hug=c['hug'],
                                           GSz=c['GSz'], MT=c['MT'], OM=c['OM'], m=c['OuterK'][0]))
            worstE[k] = min(worstE[k], np.min(gap_r * np.sum(N * d, axis=1)))
            t4 = locate(d, V4, F4)
            t5 = locate(d, V5, F5)
            rm4 = mesh_radius(d, C, V4, F4[-1], rV4, t4)
            rm5 = mesh_radius(d, C, V5, F5[-1], rV5, t5)
            worstM4[k] = min(worstM4[k], np.min(rm4 - dist))
            worstM5[k] = min(worstM5[k], np.min(rm5 - dist))
            if k == 'brazo':
                chord4.append(np.max(r - rm4)); chord5.append(np.max(r - rm5))
        if ci % 50 == 0:
            print("  cfg %d/%d  (%.0f s)" % (ci, N_CFG, time.time() - t0))
    print("\nHUECO RADIAL MINIMO (cm) — analitico | euclideo aprox | malla 2562 | malla 10242")
    for k in cats:
        print("  %-7s %7.2f | %7.2f | %7.2f | %7.2f   peor: %s" % (k, worst[k][0], worstE[k], worstM4[k], worstM5[k], worst[k][1]))
    print("\nHUECO MENOS EL MARGEN PROMETIDO (cm; >= 0 = cumple): peliculas/bolas contra el margen efectivo m, polvo contra OuterMargin (%.0f)" % OUTER_MARGIN)
    for k in cats:
        print("  %-7s %7.2f" % (k, worstRel[k]))
    print("\nerror de cuerda maximo (analitico - malla, sobre el brazo): 2562 -> %.2f cm, 10242 -> %.2f cm"
          % (max(chord4), max(chord5)))
    print("radio de la envoltura (desde C): min %.1f  max %.1f cm  (p50 del maximo %.1f, p95 %.1f)"
          % (min(rmin_all), max(rmax_all), np.percentile(rmax_all, 50), np.percentile(rmax_all, 95)))


if __name__ == "__main__":
    if len(sys.argv) > 1:
        N_CFG = int(sys.argv[1])
    if len(sys.argv) > 2:
        SEED = int(sys.argv[2])
    if len(sys.argv) > 3 and sys.argv[3] == "v4":
        L.CURL_V4 = True
        print("StrandCurl = v4")
    main()
