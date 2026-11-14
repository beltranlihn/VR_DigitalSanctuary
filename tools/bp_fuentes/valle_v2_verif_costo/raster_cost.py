# raster_cost.py - cuantos LANES de pixel shader paga el valle (v2 y v1) en el eye buffer REAL de la Quest 3,
# con cuadrantes 2x2 (sobre-sombreado de triangulos chicos), MSAA 4x (cobertura por muestra) y early-Z en el
# orden de indices de la malla (anillo por anillo, de adentro hacia afuera).
# Rasterizador de software en numpy. No usa Unreal ni Blender. Salida: raster_cost.json + consola.
#   eye buffer: xr.SecondaryScreenPercentage.HMDRenderTarget=125 -> ~2064 x 2208 por ojo (AndroidEngine.ini)
#   FOV por ojo (ojo izquierdo, aproximado Quest 3): izq 52, der 43, arriba 45, abajo 52 grados
import math, sys, types, json, time
from pathlib import Path
import numpy as np

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[3]
SCRIPTS = ROOT / ".claude" / "skills" / "unreal-vr" / "scripts"
BACKUP = ROOT / "VR_Test" / "Saved" / "ClaudeScripts" / "valle_v1_backup"

# ---- modelos: v2 (valley_model) y v1 (preview v1 del respaldo, con bpy/mathutils de mentira) ----
sys.path.insert(0, str(SCRIPTS))
import valley_model as vm  # noqa: E402
sys.modules["bpy"] = types.ModuleType("bpy")
mu = types.ModuleType("mathutils"); mu.Vector = object; sys.modules["mathutils"] = mu
sys.path.insert(0, str(BACKUP))
for k in ("gen_breath_valley", "preview_breath_valley"):
    sys.modules.pop(k, None)
import importlib.util  # noqa: E402
spec = importlib.util.spec_from_file_location("v1gen", BACKUP / "gen_breath_valley.py")
v1gen = importlib.util.module_from_spec(spec); spec.loader.exec_module(v1gen)
sys.modules["gen_breath_valley"] = v1gen
spec = importlib.util.spec_from_file_location("v1p", BACKUP / "preview_breath_valley.py")
v1p = importlib.util.module_from_spec(spec); spec.loader.exec_module(v1p)

W, H = 2064, 2208
TL, TR, TU, TD = -math.tan(math.radians(52)), math.tan(math.radians(43)), math.tan(math.radians(45)), -math.tan(math.radians(52))
NEAR = 10.0
SAMPLES = np.array([(0.375, 0.125), (0.875, 0.375), (0.125, 0.625), (0.625, 0.875)])


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
    return np.array(rs), S


def radios_v1():
    rs, _ = v1gen.radios()
    return np.array(rs) * 100.0, v1gen.SECTORES


def malla(rs, S, hfun, t):
    ang = 2 * np.pi * np.arange(S) / S
    x = np.concatenate([[0.0], (rs[:, None] * np.cos(ang)[None, :]).ravel()])
    y = np.concatenate([[0.0], (rs[:, None] * np.sin(ang)[None, :]).ravel()])
    z = hfun(x, y, t)
    idx = lambda i, s: 1 + i * S + (s % S)
    tris = [(0, idx(0, s), idx(0, s + 1)) for s in range(S)]
    for i in range(len(rs) - 1):
        for s in range(S):
            a, b, c, d = idx(i, s), idx(i + 1, s), idx(i + 1, s + 1), idx(i, s + 1)
            tris.append((a, b, c)); tris.append((a, c, d))
    return np.stack([x, y, z], 1), np.array(tris)


def camara(eye, yaw, pitch):
    cy, sy, cp, sp = math.cos(math.radians(yaw)), math.sin(math.radians(yaw)), math.cos(math.radians(pitch)), math.sin(math.radians(pitch))
    f = np.array([cp * cy, cp * sy, sp])
    rgt = np.array([-sy, cy, 0.0])            # UE: Y a la derecha
    up = np.cross(rgt, f); up = -up if up[2] < 0 else up
    return np.asarray(eye, float), f, rgt, up


def clip_near(P):
    out = []
    n = len(P)
    for i in range(n):
        a, b = P[i], P[(i + 1) % n]
        ina, inb = a[2] >= NEAR, b[2] >= NEAR
        if ina:
            out.append(a)
        if ina != inb:
            t = (NEAR - a[2]) / (b[2] - a[2])
            out.append(a + t * (b - a))
    return out


def to_px(p):
    xn, yn = p[0] / p[2], p[1] / p[2]
    return np.array([(xn - TL) / (TR - TL) * W, (TU - yn) / (TU - TD) * H, 1.0 / p[2]])


def render(V, T, cam, fog_start):
    eye, f, rgt, up = cam
    Q = V - eye
    C = np.stack([Q @ rgt, Q @ up, Q @ f], 1)        # (x, y, z) de camara
    zbuf = np.zeros((H, W))                          # 1/z; 0 = vacio (cielo)
    far_px = np.zeros((H, W), bool)
    lanes = {"near": 0, "far": 0}
    quads_n = {"near": 0, "far": 0}
    pix_shaded = 0
    tri_vis = 0
    for tri in T:
        P = C[tri]
        if (P[:, 2] < NEAR).all():
            continue
        poly = [P[0], P[1], P[2]] if (P[:, 2] >= NEAR).all() else clip_near([P[0], P[1], P[2]])
        if len(poly) < 3:
            continue
        pp = [to_px(p) for p in poly]
        for k in range(1, len(pp) - 1):
            a, b, c = pp[0], pp[k], pp[k + 1]
            xs, ys = (a[0], b[0], c[0]), (a[1], b[1], c[1])
            x0, x1 = max(int(math.floor(min(xs))), 0), min(int(math.ceil(max(xs))), W - 1)
            y0, y1 = max(int(math.floor(min(ys))), 0), min(int(math.ceil(max(ys))), H - 1)
            if x0 > x1 or y0 > y1:
                continue
            area = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
            if abs(area) < 1e-12:
                continue
            gx, gy = np.meshgrid(np.arange(x0, x1 + 1, dtype=float), np.arange(y0, y1 + 1, dtype=float))
            cov = np.zeros(gx.shape, bool)
            for sx, sy in SAMPLES:
                px, py = gx + sx, gy + sy
                w0 = (b[0] - px) * (c[1] - py) - (b[1] - py) * (c[0] - px)
                w1 = (c[0] - px) * (a[1] - py) - (c[1] - py) * (a[0] - px)
                w2 = (a[0] - px) * (b[1] - py) - (a[1] - py) * (b[0] - px)
                if area > 0:
                    cov |= (w0 >= 0) & (w1 >= 0) & (w2 >= 0)
                else:
                    cov |= (w0 <= 0) & (w1 <= 0) & (w2 <= 0)
            if not cov.any():
                continue
            px, py = gx + 0.5, gy + 0.5
            l0 = ((b[0] - px) * (c[1] - py) - (b[1] - py) * (c[0] - px)) / area
            l1 = ((c[0] - px) * (a[1] - py) - (c[1] - py) * (a[0] - px)) / area
            iz = l0 * a[2] + l1 * b[2] + (1 - l0 - l1) * c[2]
            iz = np.maximum(iz, 1e-9)
            zb = zbuf[y0:y1 + 1, x0:x1 + 1]
            ok = cov & (iz > zb * (1 + 1e-7))
            if not ok.any():
                continue
            tri_vis += 1
            zb[ok] = iz[ok]
            xn = TL + (px / W) * (TR - TL); yn = TU - (py / H) * (TU - TD)
            dist = (1.0 / iz) * np.sqrt(1 + xn * xn + yn * yn)
            fr = dist > fog_start
            far_px[y0:y1 + 1, x0:x1 + 1][ok] = fr[ok]
            iy, ix = np.nonzero(ok)
            qid = ((iy + y0) >> 1) * (W >> 1) + ((ix + x0) >> 1)
            qf = fr[iy, ix]
            uq, inv = np.unique(qid, return_inverse=True)
            qfar = np.zeros(len(uq), bool)
            np.logical_or.at(qfar, inv, qf)
            nf = int(qfar.sum()); nn = len(uq) - nf
            quads_n["far"] += nf; quads_n["near"] += nn
            lanes["far"] += 4 * nf; lanes["near"] += 4 * nn
            pix_shaded += int(ok.sum())
    ground = zbuf > 0
    px_near = int((ground & ~far_px).sum()); px_far = int((ground & far_px).sum()); px_sky = int((~ground).sum())
    # cielo DESPUES del suelo: cuadrantes con al menos un pixel vacio (early-Z / LRZ rechaza lo tapado)
    g2 = ground[: H // 2 * 2, : W // 2 * 2].reshape(H // 2, 2, W // 2, 2)
    sky_quads_after = int((~g2.all(axis=(1, 3))).sum())
    return dict(px_near=px_near, px_far=px_far, px_sky=px_sky, lanes_near=lanes["near"], lanes_far=lanes["far"],
                lanes_sky_despues=4 * sky_quads_after, lanes_sky_antes=W * H, pix_shaded=pix_shaded, tris_visibles=tri_vis,
                silueta_far_rows=int(np.nonzero((ground & far_px).any(axis=1))[0].min()) if (ground & far_px).any() else -1)


def main():
    ops = {r["camino"]: r for r in json.loads((OUT / "cost_ops.json").read_text())}
    extra = json.loads((OUT / "cost_ops_extra.json").read_text()) if (OUT / "cost_ops_extra.json").exists() else {}
    casos = []
    rs2, S2 = radios_v2(); rs1, S1 = radios_v1()
    for ver, rs, S, hfun, fs in (("v2", rs2, S2, lambda x, y, t: vm.valley_h(x, y, t), 1500.0),
                                  ("v1", rs1, S1, lambda x, y, t: v1p.valley_grad(x, y, t)[2], 1000.0)):
        V, T = malla(rs, S, hfun, 0.0)
        for camz, yaw, pitch in ((120.0, 0, 0), (120.0, 0, -15), (120.0, 180, 0), (210.4, 0, 0)):
            if ver == "v1" and (camz != 120.0 or pitch != 0):
                continue
            t0 = time.time()
            r = render(V, T, camara((0, 0, camz), yaw, pitch), fs)
            r.update(version=ver, cam_z=camz, yaw=yaw, pitch=pitch, seg=round(time.time() - t0, 1))
            tot = W * H
            print("%s cam z %.1f yaw %d pitch %d (%.0f s): suelo<FogStart %.1f %% | suelo lejano %.1f %% | cielo %.1f %% | "
                  "lanes/px: cerca %.2f lejos %.2f | tris visibles %d"
                  % (ver, camz, yaw, pitch, r["seg"], 100 * r["px_near"] / tot, 100 * r["px_far"] / tot, 100 * r["px_sky"] / tot,
                     r["lanes_near"] / max(r["px_near"], 1), r["lanes_far"] / max(r["px_far"], 1), r["tris_visibles"]))
            casos.append(r)
    (OUT / "raster_cost.json").write_text(json.dumps(casos, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
