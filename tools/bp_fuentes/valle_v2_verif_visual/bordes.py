# Bordes de oclusion suelo-suelo en la panorama (25 px/grado): donde la distancia vista salta, hay una linea.
import sys, numpy as np, vrender as vr
tags = sys.argv[1:]
for tag in tags:
    lin = np.load("pano_%s_lin.npy" % tag).astype(np.float64)
    dist = np.load("pano_%s_dist.npy" % tag).astype(np.float64)
    L = 255.0 * vr.srgb(lin)
    Lm = 0.2126 * L[..., 0] + 0.7152 * L[..., 1] + 0.0722 * L[..., 2]
    Hh, W = Lm.shape
    el = 14.0 - (np.arange(Hh) + 0.5) / 25.0
    suelo = np.isfinite(dist)
    # la esfera de referencia: dist ~ 3,8 m; se excluye (dist < 600 y el > -8)
    esf = suelo & (dist < 700.0) & (el[:, None] > -9.0)
    ok = suelo & ~esf
    rat = np.where(ok[:-1] & ok[1:], dist[:-1] / np.maximum(dist[1:], 1.0), 1.0)
    # escalon: media de 2 filas arriba vs 2 filas abajo del corte
    up = 0.5 * (np.roll(Lm, 1, 0) + Lm)[:-1]
    dn = 0.5 * (Lm[1:] + np.roll(Lm, -1, 0)[1:])
    step = np.abs(up - dn)
    edge = (rat > 1.25) & (el[:-1, None] < 0.5)
    cols_any = edge.any(0)
    stp = np.where(edge, step, 0.0)
    best = stp.max(0)
    rows = stp.argmax(0)
    elb = el[rows]
    print("== %s ==" % tag)
    print("  columnas con borde suelo-suelo (salto de distancia >1,25x, bajo el horizonte): %.1f %%" % (100 * cols_any.mean()))
    for th in (2, 3, 4, 6, 8):
        print("    con escalon >= %d niveles sRGB: %.1f %% de los azimuts" % (th, 100 * (best >= th).mean()))
    sel = best >= 3
    if sel.any():
        print("  elevacion de esos bordes (>=3 niveles): p10 %.2f  p50 %.2f  p90 %.2f deg" % tuple(np.percentile(elb[sel], [10, 50, 90])))
        rec = sel & (np.abs(elb + 1.74) < 0.12)
        print("  de ellos, en la franja recta -1,74 +-0,12 deg: %.1f %% de los azimuts" % (100 * rec.mean()))
        # tramos continuos de la linea recta
        runs, cur = [], 0
        for v in np.concatenate([rec, rec[:1]]):
            if v: cur += 1
            elif cur: runs.append(cur); cur = 0
        if cur: runs.append(cur)
        runs = sorted(runs, reverse=True)[:5]
        print("  tramos continuos mas largos de la linea recta: %s grados" % ", ".join("%.1f" % (r / 25.0) for r in runs))
        print("  escalon en esos bordes: p50 %.1f  p90 %.1f  max %.1f niveles" % (np.median(best[sel]), np.percentile(best[sel], 90), best.max()))
    np.save("bordes_%s_best.npy" % tag, best); np.save("bordes_%s_el.npy" % tag, elb)
