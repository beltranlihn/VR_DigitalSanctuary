# -*- coding: utf-8 -*-
"""b_render_flow.py - verificador de confort v2 (parte B).
Renderiza el valle desde los ojos (0, 0, 120), pitch 0, HFOV 90, 1052x862, con un trazador por COLUMNAS (cada columna
es un plano de azimut; oclusion exacta por maximo acumulado; 4 sub-filas por pixel = antialias vertical), color del
modelo (ValleyPS suelo + cielo, sin dither), y mide:
  - cambio en 5 s (niveles de 8 bits sRGB, luma) y en que zona de la imagen;
  - flujo optico por BLOQUES (NCC con FFT, subpixel) en la banda del horizonte entre t y t+0,5 s:
    velocidad de cada rasgo visible (deg/s), maxima, flujo medio, componente COHERENTE (traslacion media,
    expansion y giro de gran campo) y el indice de coherencia |media vectorial| / media de |v|.
Vistas: yaw 0, 90, 180, 270; 3 instantes al azar. Escribe c_*.png y b_resultados.json."""
import json
import math
import os
import sys

import numpy as np
from PIL import Image
from scipy.signal import correlate

AQUI = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(AQUI, "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(REPO, ".claude", "skills", "unreal-vr", "scripts"))
sys.path.insert(0, AQUI)
import valley_model as vm  # noqa: E402
from fastvalley import Grid  # noqa: E402

W, H, SS = 1052, 862, 4
F = 526.0
CX, CY = 526.0, 431.0
EYE = np.array([0.0, 0.0, 120.0])
PXDEG = F * math.tan(math.radians(1.0))
NS = 2200
SAMP = np.geomspace(80.0, 64000.0, NS)
Q = vm.params()

uprime = (np.arange(W) + 0.5) - CX
AZREL = np.degrees(np.arctan(uprime / F))
HYP = np.sqrt(F * F + uprime * uprime)                       # tan(e) = (CY - v) / HYP
VSUB = (np.arange(H * SS) + 0.5) / SS
TROW = (CY - VSUB)[None, :] / HYP[:, None]                  # (W, H*SS): tan de la elevacion de cada sub-fila


class Vista:
    def __init__(self, yaw):
        self.yaw = yaw
        az = np.radians(yaw + AZREL)[:, None]
        self.X = SAMP[None, :] * np.cos(az)
        self.Y = SAMP[None, :] * np.sin(az)
        self.g = Grid(self.X, self.Y)
        # direcciones de mirada de cada sub-pixel (para el cielo)
        e = np.arctan(TROW)
        self.dv = np.stack([np.cos(e) * np.cos(az), np.cos(e) * np.sin(az), np.sin(e)], -1)   # (W, HS, 3)
        self.sky = vm.cielo(self.dv.reshape(-1, 3), Q, con_luna=True).reshape(W, H * SS, 3)

    def render(self, t):
        gx, gy, h, hf = self.g.eval(t)
        col = vm.suelo(self.X, self.Y, gx, gy, h, hf, EYE, Q)                # (W, NS, 3) lineal
        te = (h - EYE[2]) / SAMP[None, :]
        M = np.maximum.accumulate(te, axis=1)
        img = np.empty((W, H * SS, 3))
        idxs = np.empty((W, H * SS), dtype=np.int64)
        for c in range(W):
            # la sub-fila ve la primera muestra cuyo maximo acumulado alcanza su elevacion (TROW decrece hacia abajo)
            idx = np.searchsorted(M[c], TROW[c], side="left")
            idxs[c] = idx
            sky = idx >= NS
            ii = np.minimum(idx, NS - 1)
            img[c] = np.where(sky[:, None], self.sky[c], col[c, ii])
        img = img.reshape(W, H, SS, 3).mean(2).transpose(1, 0, 2)          # (H, W, 3) lineal
        dist = np.where(idxs >= NS, np.inf, SAMP[np.minimum(idxs, NS - 1)]).reshape(W, H, SS)[:, :, SS // 2].T
        return img, dist


def luma8(img):
    s = 255.0 * vm.srgb(img)
    return 0.2126 * s[..., 0] + 0.7152 * s[..., 1] + 0.0722 * s[..., 2]


def row_of_el(el_deg):
    return CY - F * math.tan(math.radians(el_deg))


def bloques(I0, I1, dt, r0, r1, ph=16, pw=32, sy=8, sx=16, ry=12, rx=48, min_std=1.0, min_ncc=0.7):
    """Flujo por bloques NCC entre I0 e I1 (luma 8 bits) en filas [r0, r1). Devuelve lista de
    (fila, col, vx deg/s, vy deg/s (arriba +), ncc, std, ncc_en_cero)."""
    res = []
    for y0 in range(int(r0), int(r1) - ph, sy):
        for x0 in range(rx, W - rx - pw, sx):
            T = I0[y0:y0 + ph, x0:x0 + pw]
            sd = float(T.std())
            if sd < min_std:
                continue
            ya, yb = max(0, y0 - ry), min(H, y0 + ph + ry)
            R = I1[ya:yb, x0 - rx:x0 + pw + rx]
            Tz = T - T.mean()
            num = correlate(R, Tz, mode="valid", method="fft")
            ones = np.ones_like(T)
            s1 = correlate(R, ones, mode="valid", method="fft")
            s2 = correlate(R * R, ones, mode="valid", method="fft")
            n = T.size
            varR = np.maximum(s2 - s1 * s1 / n, 1e-9)
            ncc = num / (np.sqrt(varR) * np.sqrt((Tz * Tz).sum()) + 1e-9)
            iy, ix = np.unravel_index(int(np.argmax(ncc)), ncc.shape)
            best = float(ncc[iy, ix])
            cy0, cx0 = y0 - ya, rx
            n0 = float(ncc[cy0, cx0])
            if best < min_ncc or ix in (0, ncc.shape[1] - 1) or iy in (0, ncc.shape[0] - 1):
                continue

            def para(a, b, c):
                d = a - 2 * b + c
                return 0.0 if abs(d) < 1e-12 else 0.5 * (a - c) / d
            dxp = ix - cx0 + para(ncc[iy, ix - 1], ncc[iy, ix], ncc[iy, ix + 1])
            dyp = iy - cy0 + para(ncc[iy - 1, ix], ncc[iy, ix], ncc[iy + 1, ix])
            # px -> grados (en la posicion del bloque, derivada local de la proyeccion)
            xc = x0 + pw / 2 - CX
            ycp = CY - (y0 + ph / 2)
            degx = math.degrees(math.atan((xc + dxp) / F) - math.atan(xc / F))
            el0 = math.atan(ycp / math.hypot(F, xc))
            el1 = math.atan((ycp - dyp) / math.hypot(F, xc + dxp))
            degy = math.degrees(el1 - el0)
            res.append((y0 + ph / 2, x0 + pw / 2, degx / dt, degy / dt, best, sd, n0))
    return res


def main():
    rng = np.random.default_rng(11)
    T0S = [float(v) for v in rng.uniform(0, 900, 3)]
    YAWS = (0.0, 90.0, 180.0, 270.0)
    r_top, r_bot = row_of_el(16.0), row_of_el(-4.8)
    out = dict(t0s=T0S, vistas={})
    todos = []
    for yaw in YAWS:
        vis = Vista(yaw)
        ov = []
        for t0 in T0S:
            L = {}
            D = {}
            for dt in (0.0, 0.5, 5.0):
                img, dist = vis.render(t0 + dt)
                L[dt] = luma8(img)
                D[dt] = dist
                if yaw == 0.0 and t0 == T0S[0]:
                    Image.fromarray(np.clip(np.round(255 * vm.srgb(img)), 0, 255).astype(np.uint8)).save(
                        os.path.join(AQUI, "c_frente_t%.0f.png" % dt))
            d5 = np.abs(L[5.0] - L[0.0])
            el_row = np.degrees(np.arctan((CY - (np.arange(H) + 0.5)) / F))
            debajo = el_row < -4.57
            if yaw == 0.0 and t0 == T0S[0]:
                g = np.clip(d5 * 12.0, 0, 255).astype(np.uint8)
                Image.fromarray(g).save(os.path.join(AQUI, "c_frente_dif5s_x12.png"))
            st = dict(t0=t0,
                      dif5_max=float(d5.max()),
                      dif5_debajo_zona_quieta_max=float(d5[debajo].max()),
                      frac_img_mayor_2=float(np.mean(d5 > 2)), frac_img_mayor_5=float(np.mean(d5 > 5)),
                      frac_img_mayor_10=float(np.mean(d5 > 10)),
                      filas_con_cambio_mayor_2=[float(el_row[i]) for i in np.where((d5 > 2).any(1))[0][[0, -1]]]
                      if (d5 > 2).any() else None)
            fl = bloques(L[0.0], L[0.5], 0.5, r_top, r_bot)
            fl = np.array(fl) if fl else np.zeros((0, 7))
            mov = fl[np.hypot(fl[:, 2], fl[:, 3]) > 0.05] if len(fl) else fl
            if len(fl):
                sp = np.hypot(fl[:, 2], fl[:, 3])
                st.update(bloques_validos=int(len(fl)), bloques_moviles=int(len(mov)),
                          v_mediana=float(np.median(sp)), v_p90=float(np.percentile(sp, 90)),
                          v_p99=float(np.percentile(sp, 99)), v_max=float(sp.max()),
                          media_vec_x=float(fl[:, 2].mean()), media_vec_y=float(fl[:, 3].mean()),
                          media_abs=float(sp.mean()),
                          coherencia=float(math.hypot(fl[:, 2].mean(), fl[:, 3].mean()) / (sp.mean() + 1e-9)))
                # expansion / giro de gran campo: ajuste afin v = a + B*(x, y) en grados
                xd = np.degrees(np.arctan((fl[:, 1] - CX) / F))
                yd = np.degrees(np.arctan((CY - fl[:, 0]) / F))
                Amat = np.stack([np.ones_like(xd), xd, yd], 1)
                cx_, *_ = np.linalg.lstsq(Amat, fl[:, 2], rcond=None)
                cy_, *_ = np.linalg.lstsq(Amat, fl[:, 3], rcond=None)
                st.update(afin_div_1s=float(math.radians(1) * 0 + (cx_[1] + cy_[2])),
                          afin_giro_1s=float(cy_[1] - cx_[2]))
                # periferia (fuera de +-15 deg del centro: el metaball tapa el centro)
                per = np.abs(xd) > 15
                if per.any():
                    st.update(periferia_media_vec_x=float(fl[per, 2].mean()),
                              periferia_media_abs=float(sp[per].mean()))
                # rapidos: donde estan y con que contraste
                rap = sp > 2.5
                st.update(frac_bloques_mayor_2p5=float(rap.mean()),
                          rapidos_el_deg=[float(v) for v in np.percentile(yd[rap], [0, 50, 100])] if rap.any() else None,
                          rapidos_std_niveles=[float(v) for v in np.percentile(fl[rap, 5], [0, 50, 100])] if rap.any() else None,
                          rapidos_dist_m=[float(v) for v in np.percentile(
                              D[0.0][fl[rap, 0].astype(int), fl[rap, 1].astype(int)] / 100, [0, 50, 100])] if rap.any() else None)
                todos.append(np.column_stack([fl, np.full(len(fl), yaw), yd, xd]))
                if yaw == 0.0 and t0 == T0S[0]:
                    np.save(os.path.join(AQUI, "flujo_frente.npy"), fl)
            ov.append(st)
            print("yaw %3.0f t0 %6.1f | dif5s: max %.1f niv, >2niv %.2f%% img, debajo de -4.57 max %.2f | bloques %d, "
                  "|v| med %.2f p90 %.2f p99 %.2f max %.2f deg/s, vec medio (%+.2f, %+.2f), coher %.2f, div %+.4f, "
                  "giro %+.4f 1/s" % (yaw, t0, st["dif5_max"], 100 * st["frac_img_mayor_2"], st["dif5_debajo_zona_quieta_max"],
                                      st.get("bloques_validos", 0), st.get("v_mediana", 0), st.get("v_p90", 0),
                                      st.get("v_p99", 0), st.get("v_max", 0), st.get("media_vec_x", 0),
                                      st.get("media_vec_y", 0), st.get("coherencia", 0), st.get("afin_div_1s", 0),
                                      st.get("afin_giro_1s", 0)), flush=True)
            if st.get("rapidos_el_deg"):
                print("        rapidos (>2.5 deg/s): %.1f %% de los bloques; elevacion %s deg; contraste std %s niv; "
                      "distancia %s m" % (100 * st["frac_bloques_mayor_2p5"], np.round(st["rapidos_el_deg"], 2),
                                          np.round(st["rapidos_std_niveles"], 1), np.round(st["rapidos_dist_m"], 0)))
        out["vistas"][str(int(yaw))] = ov
    A = np.concatenate(todos)
    np.save(os.path.join(AQUI, "flujo_todos.npy"), A)
    sp = np.hypot(A[:, 2], A[:, 3])
    out["global"] = dict(bloques=int(len(A)), v_mediana=float(np.median(sp)), v_p90=float(np.percentile(sp, 90)),
                         v_p99=float(np.percentile(sp, 99)), v_max=float(sp.max()),
                         frac_mayor_1=float(np.mean(sp > 1)), frac_mayor_2p5=float(np.mean(sp > 2.5)))
    print("GLOBAL bloques %d: |v| mediana %.3f, p90 %.3f, p99 %.3f, max %.3f deg/s; >1 deg/s %.1f%%, >2.5 %.1f%%" % (
        len(A), np.median(sp), np.percentile(sp, 90), np.percentile(sp, 99), sp.max(), 100 * np.mean(sp > 1),
        100 * np.mean(sp > 2.5)))
    with open(os.path.join(AQUI, "b_resultados.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)


if __name__ == "__main__":
    main()
