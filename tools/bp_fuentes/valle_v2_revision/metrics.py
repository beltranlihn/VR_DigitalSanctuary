# Uso: python metrics.py '<json de perillas>' [emfb]  -> e: bordes de oclusion en 360 grados (t 0/20/40),
#      f: frente 5 min, m: silueta (velocidad, heave 360 y en ventanas de 90), b: cambio de la imagen en 5 s por banda.
# Metricas de diseno para variantes del valle (modelo experimental vexp).
import sys, math, json, time
import numpy as np
import vexp as vm
import vrx as vr

EZ = 120.0

def pano_geo(q, t, az_deg, el_deg, ez=EZ, J=3000, rho_min=20.0):
    """distancia horizontal vista por pixel (el filas x az columnas); inf = cielo."""
    rho = rho_min * np.power(64100.0 / rho_min, np.arange(J) / (J - 1.0))
    a = np.radians(az_deg)
    X = rho[:, None] * np.cos(a)[None, :]; Y = rho[:, None] * np.sin(a)[None, :]
    H = vm.valley_grad(X, Y, t, q)[2]
    s = (H - ez) / rho[:, None]
    M = np.maximum.accumulate(s, axis=0)
    sl = np.tan(np.radians(el_deg))
    D = np.empty((el_deg.size, az_deg.size))
    for k in range(az_deg.size):
        j = np.searchsorted(M[:, k], sl)
        D[:, k] = np.where(j < J, rho[np.clip(j, 0, J - 1)], np.inf)
    return D

def edges_360(q, ts=(0.0, 20.0, 40.0), ez=EZ):
    az = np.arange(-180.0, 180.0, 0.25)
    el = np.arange(0.5, -6.0, -0.04)
    out = []
    for t in ts:
        D = pano_geo(q, t, az, el, ez)
        ok = np.isfinite(D[:-1]) & np.isfinite(D[1:])
        edge = ok & (D[:-1] / D[1:] > 1.25)
        # excluir la zona del metaball (|az| < 17 y D < 7 m no aplica: el metaball no esta en el modelo)
        any_ = edge.any(0)
        # elevacion del borde mas alto por columna
        row = np.where(any_, np.argmax(edge, axis=0), -1)
        elb = np.where(any_, el[np.clip(row, 0, el.size - 1)], np.nan)
        # distancia antes/despues del borde
        c = np.arange(az.size)
        dnear = np.where(any_, D[np.clip(row + 1, 0, el.size - 1), c], np.nan)
        dfar = np.where(any_, D[np.clip(row, 0, el.size - 1), c], np.nan)
        # luminancia a cada lado (modelo de sombreado)
        stp = np.full(az.size, np.nan)
        if any_.any():
            ia = np.flatnonzero(any_)
            A = np.radians(az[ia])
            def col(d):
                x = d * np.cos(A); y = d * np.sin(A)
                gx, gy, h, hf = vm.valley_grad(x, y, t, q)
                c3 = vm.suelo(x, y, gx, gy, h, hf, np.array([0.0, 0.0, ez]), q)
                L = 255.0 * vm.srgb(c3)
                return 0.2126 * L[:, 0] + 0.7152 * L[:, 1] + 0.0722 * L[:, 2]
            stp[ia] = np.abs(col(dnear[ia]) - col(dfar[ia]))
        vis = any_ & (stp >= 3.0)
        # tramos continuos (0,25 grados por columna)
        runs = []
        i = 0; W = az.size
        while i < W:
            if not vis[i]:
                i += 1; continue
            j = i
            while j + 1 < W and vis[j + 1] and abs(elb[j + 1] - elb[j]) < 0.2:
                j += 1
            e = elb[i:j + 1]
            runs.append(((j - i + 1) * 0.25, float(e.max() - e.min()), float(np.median(e)), float(np.median(stp[i:j + 1])), float(np.median(dnear[i:j + 1]) / 100)))
            i = j + 1
        runs.sort(reverse=True)
        rect = [r for r in runs if r[0] >= 5.0 and r[1] < 0.3]
        out.append(dict(t=t, pct_edge=100 * any_.mean(), pct_vis3=100 * vis.mean(),
                        step_p50=float(np.nanmedian(stp[vis])) if vis.any() else 0.0,
                        step_max=float(np.nanmax(stp[vis])) if vis.any() else 0.0,
                        rectas=len(rect), recta_max=max([r[0] for r in rect], default=0.0),
                        top_runs=runs[:4]))
    return out

def front_time(q, ez=EZ, T=300.0, dt=5.0):
    az = np.concatenate([np.arange(-60.0, -17.0, 0.5), np.arange(17.5, 60.01, 0.5)])
    el = np.arange(0.5, -6.0, -0.04)
    res = []
    for t in np.arange(0.0, T, dt):
        D = pano_geo(q, t, az, el, ez)
        ok = np.isfinite(D[:-1]) & np.isfinite(D[1:])
        edge = ok & (D[:-1] / D[1:] > 1.25)
        res.append(edge.any(0))
    res = np.array(res)
    deg = res.sum(1) * 0.5
    return dict(frac=100 * res.mean(), inst10=100 * (deg >= 10).mean(), p50=float(np.median(deg)), p90=float(np.percentile(deg, 90)))

def silueta(q, t, az, ez=EZ, J=1600, rho_min=40.0):
    rho = rho_min * np.power(64000.0 / rho_min, np.arange(J) / (J - 1.0))
    X = rho[:, None] * np.cos(az)[None, :]; Y = rho[:, None] * np.sin(az)[None, :]
    H = vm.valley_grad(X, Y, t, q)[2]
    e = np.degrees(np.arctan2(H - ez, rho[:, None]))
    j = np.argmax(e, axis=0)
    return e[j, np.arange(az.size)], rho[j]

def mov(q, n=30, T=600.0):
    az = np.radians(np.arange(0, 360, 1.0))
    rng = np.random.default_rng(3)
    v = []; heave = []; hv90 = []
    for t in rng.uniform(0.0, T, n):
        a, _ = silueta(q, t, az); b, _ = silueta(q, t + 1.0, az)
        d = b - a
        v.append(np.abs(d))
        heave.append(abs(d.mean()) / max(np.abs(d).mean(), 1e-9))
        for y0 in range(0, 360, 15):
            idx = (np.arange(y0 - 45, y0 + 45)) % 360
            hv90.append(abs(d[idx].mean()) / max(np.abs(d[idx]).mean(), 1e-9))
    v = np.array(v)
    sil, rs = silueta(q, 0.0, az)
    borde = math.degrees(math.atan2(-EZ, 64000.0))
    return dict(med=float(np.median(v)), p90=float(np.percentile(v, 90)), gt01=100 * float((v > 0.1).mean()),
                heave=float(np.median(heave)), heave90=float(np.median(hv90)), sil_min=float(sil.min()), sil_med=float(np.median(sil)),
                sil_max=float(sil.max()), dist_med=float(np.median(rs)) / 100, dist_min=float(rs.min()) / 100, margen=float(sil.min() - borde))

def bandas(q, ez=EZ, dt=5.0, t0=0.0, ppd=12.5):
    eye = np.array([0.0, 0.0, ez])
    az, sl, el = vr.cilindrica(-60.0, 60.0, -14.0, 14.0, ppd)
    m = vr.Modelo("v2", q)
    L = {}; Dd = {}
    for t in (t0, t0 + dt):
        img, dist, _ = vr.render_cols(m, eye, az, sl, t, rho_min=20.0, J=3000, chunk=64)
        Lm = 255.0 * vr.srgb(img)
        L[t] = 0.2126 * Lm[..., 0] + 0.7152 * Lm[..., 1] + 0.0722 * Lm[..., 2]
        Dd[t] = np.isfinite(dist)
    d = np.abs(L[t0 + dt] - L[t0])
    b = {"cerca(<-3)": el < -3.0, "llano(-3..-0.4)": (el >= -3.0) & (el < -0.4), "horiz(>=-0.4)": el >= -0.4}
    out = {}
    for nb, bb in b.items():
        sel = bb[:, None] & (Dd[t0] | Dd[t0 + dt])
        out[nb] = (round(100 * float((d[sel] >= 1).mean()), 1), round(100 * float((d[sel] >= 3).mean()), 1))
    return out

if __name__ == "__main__":
    over = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    what = sys.argv[2] if len(sys.argv) > 2 else "emfb"
    q = vm.params(**over)
    t0 = time.time()
    if "e" in what:
        for r in edges_360(q):
            print("EDGES t=%g: col con borde %.1f%%, visibles(>=3 niv) %.1f%%, escalon p50 %.1f max %.1f, rectas(>=5deg, rango<0.3) %d, la mas larga %.1f deg" % (r["t"], r["pct_edge"], r["pct_vis3"], r["step_p50"], r["step_max"], r["rectas"], r["recta_max"]))
            print("   tramos mas largos (largo deg, rango el, el med, escalon, dist m):", [tuple(round(v, 2) for v in x) for x in r["top_runs"]])
    if "f" in what:
        print("FRENTE:", front_time(q))
    if "m" in what:
        print("MOV:", {k: round(v, 3) for k, v in mov(q).items()})
    if "b" in what:
        print("BANDAS dt5 (>=1, >=3 niveles %):", bandas(q))
    print("(%.0f s)" % (time.time() - t0))
