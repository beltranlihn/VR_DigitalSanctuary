# -*- coding: utf-8 -*-
"""b2_flow.py - flujo optico por bloques sobre los cuadros guardados (frames_yaw*.npz), con control de APERTURA:
el tensor de estructura del bloque decide si el desplazamiento 2D es confiable (lambda2/lambda1 >= 0.15) o si solo
vale la componente NORMAL (proyeccion sobre el gradiente dominante). Mide velocidades de rasgos visibles (deg/s),
flujo medio, componente coherente de gran campo (traslacion, expansion, giro) y el cambio en 5 s por zona."""
import json
import math
import os

import numpy as np
from scipy.signal import correlate

AQUI = os.path.dirname(os.path.abspath(__file__))
W, H = 1052, 862
F, CX, CY = 526.0, 526.0, 431.0


def row_of_el(el):
    return CY - F * math.tan(math.radians(el))


def px2deg(xc, ycp, dx, dy):
    """desplazamiento (dx derecha, dy abajo) en px en el punto (xc, ycp) relativo al centro (ycp arriba +) -> grados
    (az, el) con la proyeccion exacta del trazador por columnas (pitch 0)."""
    az0 = math.atan(xc / F)
    az1 = math.atan((xc + dx) / F)
    el0 = math.atan(ycp / math.hypot(F, xc))
    el1 = math.atan((ycp - dy) / math.hypot(F, xc + dx))
    return math.degrees(az1 - az0), math.degrees(el1 - el0)


def bloques(I0, I1, dt, r0, r1, ph=16, pw=32, sy=8, sx=16, ry=12, rx=56, min_std=0.75, min_ncc=0.6):
    gy, gx = np.gradient(I0)
    out = []
    for y0 in range(int(r0), int(r1) - ph, sy):
        for x0 in range(rx, W - rx - pw, sx):
            T = I0[y0:y0 + ph, x0:x0 + pw]
            sd = float(T.std())
            if sd < min_std:
                continue
            Gx = gx[y0:y0 + ph, x0:x0 + pw]
            Gy = gy[y0:y0 + ph, x0:x0 + pw]
            J = np.array([[(Gx * Gx).sum(), (Gx * Gy).sum()], [(Gx * Gy).sum(), (Gy * Gy).sum()]])
            ev, evec = np.linalg.eigh(J)
            l1, l2 = ev[1], ev[0]
            e1 = evec[:, 1]                                  # (x, y) direccion del gradiente dominante
            iso = l2 / (l1 + 1e-12)
            ya, yb = max(0, y0 - ry), min(H, y0 + ph + ry)
            R = I1[ya:yb, x0 - rx:x0 + pw + rx]
            Tz = T - T.mean()
            num = correlate(R, Tz, mode="valid", method="fft")
            ones = np.ones_like(T)
            s1 = correlate(R, ones, mode="valid", method="fft")
            s2 = correlate(R * R, ones, mode="valid", method="fft")
            varR = np.maximum(s2 - s1 * s1 / T.size, 1e-9)
            ncc = num / (np.sqrt(varR) * math.sqrt(float((Tz * Tz).sum())) + 1e-9)
            iy, ix = np.unravel_index(int(np.argmax(ncc)), ncc.shape)
            best = float(ncc[iy, ix])
            cy0, cx0 = y0 - ya, rx
            if best < min_ncc or ix in (0, ncc.shape[1] - 1) or iy in (0, ncc.shape[0] - 1):
                continue

            def para(a, b_, c):
                d = a - 2 * b_ + c
                return 0.0 if abs(d) < 1e-12 else 0.5 * (a - c) / d
            dxp = ix - cx0 + para(ncc[iy, ix - 1], ncc[iy, ix], ncc[iy, ix + 1])
            dyp = iy - cy0 + para(ncc[iy - 1, ix], ncc[iy, ix], ncc[iy + 1, ix])
            xc = x0 + pw / 2 - CX
            ycp = CY - (y0 + ph / 2)
            vx, vy = px2deg(xc, ycp, dxp, dyp)
            dn = dxp * e1[0] + dyp * e1[1]
            nx, ny = px2deg(xc, ycp, dn * e1[0], dn * e1[1])
            out.append((y0 + ph / 2, x0 + pw / 2, vx / dt, vy / dt, math.hypot(nx, ny) / dt, best, sd, iso,
                        math.degrees(math.atan(xc / F)), math.degrees(math.atan(ycp / math.hypot(F, xc)))))
    return np.array(out) if out else np.zeros((0, 10))


COLS = ["fila", "col", "vx", "vy", "vn", "ncc", "std", "iso", "az", "el"]


def main():
    res = {}
    todos = []
    for yaw in (0, 90, 180, 270):
        z = np.load(os.path.join(AQUI, "frames_yaw%d.npz" % yaw))
        L, Dm, t0s, dts = z["L"], z["D"], z["t0s"], list(z["dts"])
        j025, j05, j5 = dts.index(0.25), dts.index(0.5), dts.index(5.0)
        el_row = np.degrees(np.arctan((CY - (np.arange(H) + 0.5)) / F))[:, None] * np.ones((1, W))
        vis = []
        for i, t0 in enumerate(t0s):
            I0 = L[i, 0].astype(np.float64)
            d5 = np.abs(L[i, j5] - L[i, 0])
            D = Dm[i]
            zonas = dict(cielo=~np.isfinite(D), lejos=np.isfinite(D) & (D > 25000),
                         medio=(D > 4500) & (D <= 25000), cerca=(D > 1500) & (D <= 4500), piso_quieto=D <= 1500)
            st = dict(t0=float(t0), dif5_max=float(d5.max()), frac_img_mayor_2=float(np.mean(d5 > 2)),
                      frac_img_mayor_5=float(np.mean(d5 > 5)))
            for k, m in zonas.items():
                st["dif5_%s" % k] = [float(m.mean()), float(d5[m].max()) if m.any() else 0.0,
                                     float(np.mean(d5[m] > 2)) if m.any() else 0.0]
            fl = bloques(I0, L[i, j05].astype(np.float64), 0.5, row_of_el(16.0), row_of_el(-4.8))
            fl25 = bloques(I0, L[i, j025].astype(np.float64), 0.25, row_of_el(16.0), row_of_el(-4.8))
            for f_, tag in ((fl, "05"), (fl25, "025")):
                if not len(f_):
                    continue
                dd = D[f_[:, 0].astype(int), f_[:, 1].astype(int)]
                f2 = f_[f_[:, 7] >= 0.15]
                sp2 = np.hypot(f2[:, 2], f2[:, 3]) if len(f2) else np.zeros(0)
                vn = f_[:, 4]
                w = f_[:, 6] ** 2
                st["lag" + tag] = dict(
                    n=int(len(f_)), n2d=int(len(f2)),
                    vn_mediana=float(np.median(vn)), vn_p90=float(np.percentile(vn, 90)),
                    vn_p99=float(np.percentile(vn, 99)), vn_max=float(vn.max()),
                    vn_max_contraste_ge2=float(vn[f_[:, 6] >= 2].max()) if (f_[:, 6] >= 2).any() else 0.0,
                    v2d_mediana=float(np.median(sp2)) if len(sp2) else None,
                    v2d_p90=float(np.percentile(sp2, 90)) if len(sp2) else None,
                    v2d_max=float(sp2.max()) if len(sp2) else None,
                    vec_medio_2d=[float(f2[:, 2].mean()), float(f2[:, 3].mean())] if len(f2) else None,
                    vec_medio_ponderado_todos=[float((f_[:, 2] * w).sum() / w.sum()), float((f_[:, 3] * w).sum() / w.sum())],
                    coherencia_2d=float(math.hypot(f2[:, 2].mean(), f2[:, 3].mean()) / (sp2.mean() + 1e-9)) if len(f2) else None,
                    rapidos_vn_mayor_2p5=dict(
                        frac=float(np.mean(vn > 2.5)),
                        el=[float(v) for v in np.percentile(f_[vn > 2.5, 9], [0, 50, 100])] if (vn > 2.5).any() else None,
                        dist_m=[float(v) for v in np.nanpercentile(np.where(np.isfinite(dd[vn > 2.5]), dd[vn > 2.5], np.nan) / 100, [0, 50, 100])] if (vn > 2.5).any() else None,
                        std=[float(v) for v in np.percentile(f_[vn > 2.5, 6], [0, 50, 100])] if (vn > 2.5).any() else None),
                )
                if tag == "05" and len(f2) >= 6:
                    A = np.stack([np.ones(len(f2)), f2[:, 8], f2[:, 9]], 1)
                    cx_, *_ = np.linalg.lstsq(A, f2[:, 2], rcond=None)
                    cy_, *_ = np.linalg.lstsq(A, f2[:, 3], rcond=None)
                    st["afin_2d"] = dict(traslacion=[float(cx_[0]), float(cy_[0])],
                                         divergencia_1s=float(math.radians(1) * 0 + math.radians(cx_[1] + cy_[2]) / math.radians(1)),
                                         giro_1s=float(cy_[1] - cx_[2]))
                    per = np.abs(f2[:, 8]) > 15
                    if per.any():
                        st["periferia_vec_medio_2d"] = [float(f2[per, 2].mean()), float(f2[per, 3].mean())]
                if tag == "05":
                    todos.append(np.column_stack([f_, np.full(len(f_), yaw), np.full(len(f_), t0), dd]))
            vis.append(st)
            l5 = st.get("lag05", {})
            print("yaw %3d t0 %6.1f | dif5 max %.1f, >2 niv %.2f%% img; piso quieto max %.3f | lag0.5: n %d (2D %d) "
                  "vn med %.2f p90 %.2f p99 %.2f max %.2f (contraste>=2: %.2f) | 2D: med %s p90 %s max %s, vec medio %s, "
                  "coher %s | afin %s" % (
                      yaw, t0, st["dif5_max"], 100 * st["frac_img_mayor_2"], st["dif5_piso_quieto"][1],
                      l5.get("n", 0), l5.get("n2d", 0), l5.get("vn_mediana", 0), l5.get("vn_p90", 0), l5.get("vn_p99", 0),
                      l5.get("vn_max", 0), l5.get("vn_max_contraste_ge2", 0),
                      None if l5.get("v2d_mediana") is None else round(l5["v2d_mediana"], 2),
                      None if l5.get("v2d_p90") is None else round(l5["v2d_p90"], 2),
                      None if l5.get("v2d_max") is None else round(l5["v2d_max"], 2),
                      None if l5.get("vec_medio_2d") is None else np.round(l5["vec_medio_2d"], 3),
                      None if l5.get("coherencia_2d") is None else round(l5["coherencia_2d"], 2),
                      st.get("afin_2d")), flush=True)
            r = l5.get("rapidos_vn_mayor_2p5")
            if r and r["el"]:
                print("        vn>2.5: %.1f%% de bloques; el %s deg; dist %s m; std %s niv" % (
                    100 * r["frac"], np.round(r["el"], 2), np.round(r["dist_m"], 0), np.round(r["std"], 1)))
            r = st.get("lag025", {})
            if r:
                print("        lag0.25: vn med %.2f p99 %.2f max %.2f; 2D max %s" % (
                    r["vn_mediana"], r["vn_p99"], r["vn_max"], None if r["v2d_max"] is None else round(r["v2d_max"], 2)))
        res[str(yaw)] = vis
    A = np.concatenate(todos)
    np.save(os.path.join(AQUI, "flujo_bloques_lag05.npy"), A)
    vn = A[:, 4]
    m2 = A[:, 7] >= 0.15
    sp2 = np.hypot(A[m2, 2], A[m2, 3])
    g = dict(n=int(len(A)), vn_mediana=float(np.median(vn)), vn_p90=float(np.percentile(vn, 90)),
             vn_p99=float(np.percentile(vn, 99)), vn_max=float(vn.max()),
             v2d_mediana=float(np.median(sp2)), v2d_p90=float(np.percentile(sp2, 90)), v2d_max=float(sp2.max()),
             frac_vn_mayor_1=float(np.mean(vn > 1)), frac_vn_mayor_2p5=float(np.mean(vn > 2.5)))
    # por banda de distancia
    dd = A[:, 12] / 100.0
    bandas = {}
    for a, b_ in ((15, 45), (45, 100), (100, 250), (250, 700)):
        m = (dd >= a) & (dd < b_)
        if m.any():
            bandas["%d-%d m" % (a, b_)] = dict(n=int(m.sum()), vn_mediana=float(np.median(vn[m])),
                                              vn_p90=float(np.percentile(vn[m], 90)), vn_max=float(vn[m].max()),
                                              std_mediana=float(np.median(A[m, 6])))
    m = ~np.isfinite(dd)
    if m.any():
        bandas["cielo (bloque con cielo en el centro)"] = dict(n=int(m.sum()), vn_mediana=float(np.median(vn[m])),
                                                               vn_max=float(vn[m].max()))
    g["por_distancia"] = bandas
    res["global"] = g
    print("GLOBAL", json.dumps(g, indent=1))
    with open(os.path.join(AQUI, "b2_resultados.json"), "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1)


if __name__ == "__main__":
    main()
