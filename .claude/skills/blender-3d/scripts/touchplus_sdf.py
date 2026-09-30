# touchplus_sdf.py - paso 2 del mando (3a version): funde los paneles del Touch Plus oficial en UNA cascara lisa.
#   1. muestrea cada triangulo como superficie CURVA (Phong tessellation con las normales del artista), no plana:
#      la malla oficial es low-poly y su suavidad venia de las normales; asi no aparecen facetas
#   2. las tiras oscuras del fondo de las juntas entre paneles se ACUESTAN sobre el panel vecino (proyeccion a su
#      plano tangente): sellan la junta y la dejan al ras -> la cascara se lee continua
#   3. pozos de los botones de la tapa (A/B/Meta/stick): corta el pozo + 1,5 mm y tapa con una cuadrica ajustada en
#      posicion Y pendiente a la corona de 1,5-4,5 mm (empalma sin escalon ni quiebre). La ranura del gatillo se
#      queda con su bolsillo original (el gatillo entra ahi al apretar); el ojal de la correa y la boca del gatillo
#      se cierran en abanico (quedan adentro, no se ven)
#   4. campo de distancia CON SIGNO en grilla de 0,3 mm: distancia punto-plano a la muestra mas cercana en una banda
#      de 1,5 mm; fuera de la banda, adentro/afuera por relleno desde el borde de la grilla
#   5. marching cubes -> componente mayor (sin burbujas) -> OBJ en metros + por vertice la altura (mm) sobre la
#      linea de la tapa (mascara, positiva = tapa) -> tp_body_R.obj / tp_body_R_cap.npy / tp_trigger_R.obj
# Uso: python touchplus_sdf.py <dir con tp_src.npz/json>   (Python del sistema: numpy, scipy, scikit-image)
import json
import math
import sys

import numpy as np
from scipy import ndimage
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree
from skimage import measure

D = sys.argv[1] if len(sys.argv) > 1 else "."
H = 0.1              # mm, separacion de muestras
VOX = 0.3            # mm, grilla del campo
BAND = 5.0           # voxeles de banda (cierra juntas de hasta ~3 mm)
ALPHA = 0.75         # Phong tessellation (0 = plano)
SIGMA = 0.7          # voxeles, suavizado del campo
PANELS = (0, 1, 2, 3, 6, 10, 12, 13)  # paneles de verdad (6 = boton de grip: queda fundido al mango)
POCKET = 14          # bolsillo de la ranura del gatillo (se conserva)
STRIPS = "drop"      # "drop" | "flatten" (acostarlas sobre el panel vecino)
WELL_MARGIN = 1.5    # mm mas alla del borde del pozo
RING = (1.5, 4.5)    # mm, corona para ajustar la cuadrica
CLOSE_R = 1.0        # mm, cierre morfologico del cuerpo (rellena lo que queda de las ranuras de las juntas)
BODY_PANELS = (0, 2, 3, 6, 10, 13)
GRIP_PANEL = 6       # boton de grip: se corre ENTERO hasta quedar al ras del mango

TRIM = 1.5           # mm de borde de panel que se recorta en cada junta (su curva hacia la ranura)
TRIM_GRIP = 1.5      # mm alrededor del boton de grip y de la pieza de la correa
FILL_PANELS = (6, 10)  # boton de grip y pieza de la correa: su zona se suaviza fuerte en el campo
SOFT = {"juntas": (3.0, 1.5), "boton_grip": (4.0, 3.0)}  # (alcance, sigma) en mm del suavizado local del campo
POISSON_SIGMA = 1.5  # voxeles, suavizado del campo de normales antes de Poisson

_bary = {}


def bary(n):
    if n not in _bary:
        i, j = np.meshgrid(np.arange(n + 1), np.arange(n + 1), indexing='ij')
        m = (i + j) <= n
        u, v = i[m] / n, j[m] / n
        _bary[n] = np.stack([u, v, 1 - u - v], 1)
    return _bary[n]


def phong(P, N, C):
    pts, nrm, cid = [], [], []
    for p, nn, c in zip(P, N, C):
        L = max(np.linalg.norm(p[0] - p[1]), np.linalg.norm(p[1] - p[2]), np.linalg.norm(p[2] - p[0]))
        B = bary(max(1, int(math.ceil(L / H))))
        q = B @ p
        acc = np.zeros_like(q)
        for a in range(3):
            acc += B[:, a:a + 1] * (q - np.sum((q - p[a]) * nn[a], 1, keepdims=True) * nn[a])
        nr = B @ nn
        pts.append((1 - ALPHA) * q + ALPHA * acc)
        nrm.append(nr / np.linalg.norm(nr, axis=1, keepdims=True))
        cid.append(np.full(len(B), c, np.int16))
    return np.concatenate(pts), np.concatenate(nrm), np.concatenate(cid)


def pca_frame(loop):
    c = loop.mean(0)
    _, _, vt = np.linalg.svd(loop - c)
    return c, vt[0], np.cross(vt[2], vt[0]), vt[2]


def quad_fit(x, y, z, gx, gy, s):
    """z = cuadrica(x, y) ajustada a posiciones y pendientes (coordenadas normalizadas por s)."""
    X, Y = x / s, y / s
    o, zr = np.ones_like(X), np.zeros_like(X)
    A = np.stack([X * X, X * Y, Y * Y, X, Y, o], 1)
    Ax = np.stack([2 * X, Y, zr, o, zr, zr], 1)
    Ay = np.stack([zr, X, 2 * Y, zr, o, zr], 1)
    k = np.linalg.lstsq(np.concatenate([A, Ax, Ay]), np.concatenate([z, gx * s, gy * s]), rcond=None)[0]
    f = lambda x, y: k[0] * (x / s) ** 2 + k[1] * (x / s) * (y / s) + k[2] * (y / s) ** 2 + k[3] * x / s + k[4] * y / s + k[5]
    g = lambda x, y: ((2 * k[0] * x / s + k[1] * y / s + k[3]) / s, (k[1] * x / s + 2 * k[2] * y / s + k[4]) / s)
    return f, g


def fan(loop, away):
    """Cierra un lazo con un abanico al centroide (normales hacia afuera del solido)."""
    c = loop.mean(0)
    pts, nrm = [], []
    for i in range(len(loop)):
        tri = np.array([c, loop[i], loop[(i + 1) % len(loop)]])
        n = np.cross(tri[1] - tri[0], tri[2] - tri[0])
        if np.linalg.norm(n) < 1e-9:
            continue
        n /= np.linalg.norm(n)
        if n @ (tri.mean(0) - away) < 0:
            n = -n
        L = max(np.linalg.norm(tri[0] - tri[1]), np.linalg.norm(tri[1] - tri[2]), np.linalg.norm(tri[2] - tri[0]))
        B = bary(max(1, int(math.ceil(L / H))))
        pts.append(B @ tri)
        nrm.append(np.repeat(n[None], len(B), 0))
    return np.concatenate(pts), np.concatenate(nrm)


def in_poly(X, Y, px, py):
    ins = np.zeros(len(X), bool)
    j = len(px) - 1
    for i in range(len(px)):
        c = ((py[i] > Y) != (py[j] > Y)) & (X < (px[j] - px[i]) * (Y - py[i]) / (py[j] - py[i] + 1e-12) + px[i])
        ins ^= c
        j = i
    return ins


def poly_sdist(X, Y, px, py):
    """Distancia con signo al poligono (negativa adentro)."""
    d = np.full(len(X), np.inf)
    for i in range(len(px)):
        j = (i + 1) % len(px)
        dx, dy = px[j] - px[i], py[j] - py[i]
        t = np.clip(((X - px[i]) * dx + (Y - py[i]) * dy) / (dx * dx + dy * dy + 1e-12), 0, 1)
        d = np.minimum(d, np.hypot(X - px[i] - t * dx, Y - py[i] - t * dy))
    return np.where(in_poly(X, Y, px, py), -d, d)


def polyfit(x, y, z, gx, gy, deg, s):
    """z = polinomio(x, y) de grado deg ajustado a posiciones y pendientes (coordenadas normalizadas por s)."""
    terms = [(i, j) for i in range(deg + 1) for j in range(deg + 1 - i)]

    def basis(X, Y):
        return np.stack([X ** i * Y ** j for i, j in terms], 1)

    def dbasis(X, Y):
        return (np.stack([i * X ** max(i - 1, 0) * Y ** j if i else 0 * X for i, j in terms], 1),
                np.stack([j * X ** i * Y ** max(j - 1, 0) if j else 0 * X for i, j in terms], 1))
    bx, by = dbasis(x / s, y / s)
    k = np.linalg.lstsq(np.concatenate([basis(x / s, y / s), bx, by]), np.concatenate([z, gx * s, gy * s]), rcond=None)[0]
    f = lambda X, Y: basis(X / s, Y / s) @ k

    def g(X, Y):
        bx, by = dbasis(X / s, Y / s)
        return bx @ k / s, by @ k / s
    return f, g


def boundary_segments(P, C, comps):
    """Aristas de borde de cada panel (usadas por un solo triangulo del panel) -> (a, b, panel)."""
    out = []
    for k in comps:
        T = P[C == k]
        e = np.concatenate([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]])
        q = np.round(e * 1000).astype(np.int64)
        a, b = q[:, 0], q[:, 1]
        gt = (a[:, 0] > b[:, 0]) | ((a[:, 0] == b[:, 0]) & ((a[:, 1] > b[:, 1]) | ((a[:, 1] == b[:, 1]) & (a[:, 2] > b[:, 2]))))
        key = np.concatenate([np.where(gt[:, None], b, a), np.where(gt[:, None], a, b)], 1)
        _, inv, cnt = np.unique(key, axis=0, return_inverse=True, return_counts=True)
        once = cnt[inv.ravel()] == 1
        out += [(s_[0], s_[1], k) for s_ in e[once]]
    return out


def taubin(v, f, w, iters, lam=0.5, mu=-0.53):
    """Suavizado de Taubin (no encoge) con peso por vertice (0 = quieto)."""
    e = np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]])
    e = np.concatenate([e, e[:, ::-1]])
    A = coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(len(v), len(v))).tocsr()
    A.data[:] = 1.0
    deg = np.asarray(A.sum(1)).ravel()[:, None]
    for _ in range(iters):
        for s in (lam, mu):
            v = v + s * w[:, None] * (A @ v / deg - v)
    return v


def field(pts, nrm, lo, shape, band_vox):
    """Distancia con signo: punto-plano a la muestra mas cercana en la banda; afuera/adentro por relleno fuera de ella."""
    occ = np.ones(shape, bool)
    ix = np.floor((pts - lo) / VOX + 0.5).astype(int)
    ok = np.all((ix >= 0) & (ix < shape), 1)
    occ[ix[ok, 0], ix[ok, 1], ix[ok, 2]] = False
    band = ndimage.distance_transform_edt(occ) <= band_vox
    lab, _ = ndimage.label(~band)
    brd = np.unique(np.concatenate([lab[0].ravel(), lab[-1].ravel(), lab[:, 0].ravel(), lab[:, -1].ravel(),
                                    lab[:, :, 0].ravel(), lab[:, :, -1].ravel()]))
    sd = np.where(np.isin(lab, brd[brd > 0]), band_vox * VOX, -band_vox * VOX).astype(np.float32)
    bi = np.nonzero(band)
    Xv = lo + np.stack(bi, 1) * VOX
    _, j = cKDTree(pts).query(Xv, k=1, workers=-1)
    sd[bi] = np.sum((Xv - pts[j]) * nrm[j], 1)
    return sd


def level(sd, lo):
    """Superficie cero del campo -> vertices (mm), caras, normales hacia afuera (gradiente del campo)."""
    v, f, _, _ = measure.marching_cubes(sd, 0.0, spacing=(VOX, VOX, VOX), gradient_direction='ascent')
    g = np.stack(np.gradient(sd), 0)
    n = np.stack([ndimage.map_coordinates(g[k], (v / VOX).T, order=1) for k in range(3)], 1)
    n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
    return v + lo, f[:, [0, 2, 1]], n


def fair(v, f, free):
    """Alisado de placa delgada SOLO por la normal: cada vertice libre se mueve t_i sobre su normal, con t que minimiza
    la curvatura (bilaplaciano cotangente) con el borde fijo -> continua la curvatura de alrededor (C1), no se hunde
    como una membrana y no desliza los vertices por la superficie."""
    from scipy.sparse import diags
    from scipy.sparse.linalg import spsolve
    n = len(v)
    i, j, k = f[:, 0], f[:, 1], f[:, 2]

    def cot(a, b, c):
        u, w = v[b] - v[a], v[c] - v[a]
        return np.clip(np.sum(u * w, 1) / (np.linalg.norm(np.cross(u, w), axis=1) + 1e-12), 0.0, 5.0)
    ci, cj, ck = cot(i, j, k), cot(j, k, i), cot(k, i, j)
    W = coo_matrix((0.5 * np.concatenate([ci, ci, cj, cj, ck, ck]),
                    (np.concatenate([j, k, k, i, i, j]), np.concatenate([k, j, i, k, j, i]))), shape=(n, n)).tocsr()
    C = (W - diags(np.asarray(W.sum(1)).ravel())).tocsr()
    fn = np.cross(v[j] - v[i], v[k] - v[i])
    area = np.linalg.norm(fn, axis=1) / 2.0
    M = np.bincount(np.concatenate([i, j, k]), np.repeat(area / 3.0, 3), minlength=n) + 1e-6
    vn = np.zeros_like(v)
    for c_ in (i, j, k):
        np.add.at(vn, c_, fn)
    vn /= np.linalg.norm(vn, axis=1, keepdims=True) + 1e-12
    F = np.nonzero(free)[0]
    CF = C[:, F].tocsc()
    Minv = diags(1.0 / M)
    Q = (CF.T @ Minv @ CF).tocoo()
    nF = vn[F]
    S = coo_matrix((Q.data * np.sum(nF[Q.row] * nF[Q.col], 1), (Q.row, Q.col)), shape=Q.shape).tocsc()
    r = C @ v
    rhs = np.zeros(len(F))
    for d in range(3):
        rhs -= nF[:, d] * (CF.T @ (r[:, d] / M))
    t = spsolve(S + diags(np.full(len(F), 1e-9)), rhs)
    out = v.copy()
    out[F] += t[:, None] * nF
    print("ALISADO vertices", len(F), "por_normal_mm p95 %.3f max %.3f" % (np.percentile(np.abs(t), 95), np.abs(t).max()))
    return out


def poisson_solid(pts, nrm, name, cap=None, fair_sets=(), soften=()):
    """Reconstruccion de Poisson en grilla (FFT): el campo de normales splateado y suavizado es el gradiente de una
    funcion indicadora; su nivel medio en las muestras es la superficie. Cierra con superficie lisa donde NO hay
    muestras (juntas recortadas, huecos chicos) sin fugas ni ranuras."""
    lo = pts.min(0) - 6.0
    shape = np.ceil((pts.max(0) + 6.0 - lo) / VOX).astype(int) + 1
    shape = np.array([int(2 ** math.ceil(math.log2(n))) if n <= 64 else int(math.ceil(n / 16) * 16) for n in shape])
    g = (pts - lo) / VOX
    i0 = np.floor(g).astype(int)
    fr = (g - i0).astype(np.float32)
    V = np.zeros((3,) + tuple(shape), np.float32)
    for dx in (0, 1):
        for dy in (0, 1):
            for dz in (0, 1):
                w = (fr[:, 0] if dx else 1 - fr[:, 0]) * (fr[:, 1] if dy else 1 - fr[:, 1]) * (fr[:, 2] if dz else 1 - fr[:, 2])
                idx = (i0[:, 0] + dx, i0[:, 1] + dy, i0[:, 2] + dz)
                for k in range(3):
                    np.add.at(V[k], idx, w * nrm[:, k])
    for k in range(3):
        V[k] = ndimage.gaussian_filter(V[k], POISSON_SIGMA)
    kx = [2 * np.pi * np.fft.fftfreq(n, d=VOX) for n in shape[:2]] + [2 * np.pi * np.fft.rfftfreq(shape[2], d=VOX)]
    KX, KY, KZ = np.meshgrid(kx[0].astype(np.float32), kx[1].astype(np.float32), kx[2].astype(np.float32), indexing='ij')
    div = 1j * KX * np.fft.rfftn(V[0]) + 1j * KY * np.fft.rfftn(V[1]) + 1j * KZ * np.fft.rfftn(V[2])
    del V
    k2 = KX * KX + KY * KY + KZ * KZ
    k2[0, 0, 0] = 1.0
    chi = np.fft.irfftn(-div / k2, s=tuple(shape)).astype(np.float32)
    del div, k2, KX, KY, KZ
    iso = float(np.median(ndimage.map_coordinates(chi, g.T, order=1)))
    for P_, r_, sig_ in soften:
        # suavizado LOCAL del campo (liso, sin bandas): peso 1 sobre la zona, 0 a r_ mm; desenfoque sig_ mm
        occ = np.ones(tuple(shape), bool)
        ix = np.clip(np.floor((P_ - lo) / VOX + 0.5).astype(int), 0, shape - 1)
        occ[ix[:, 0], ix[:, 1], ix[:, 2]] = False
        u_ = np.clip(1.0 - ndimage.distance_transform_edt(occ).astype(np.float32) * VOX / r_, 0, 1)
        del occ
        wgt = u_ * u_ * (3 - 2 * u_)
        del u_
        chi += wgt * (ndimage.gaussian_filter(chi, sig_ / VOX) - chi)
        del wgt
        print("SUAVIZADO_CAMPO alcance_mm", r_, "sigma_mm", sig_, "puntos", len(P_))
    v, f, _ = level(chi - iso, lo)
    e = np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]])
    nc, labv = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(len(v), len(v))), directed=False)
    cnt = np.bincount(labv)
    keep = labv == np.argmax(cnt)
    f = f[keep[f[:, 0]]]
    remap = -np.ones(len(v), int)
    remap[keep] = np.arange(keep.sum())
    v, f = v[keep], remap[f]
    if fair_sets:
        free = np.zeros(len(v), bool)
        for P_, r_ in fair_sets:
            free |= cKDTree(P_).query(v, k=1, workers=-1)[0] < r_
        v = fair(v, f, free)
    area2 = np.linalg.norm(np.cross(v[f[:, 1]] - v[f[:, 0]], v[f[:, 2]] - v[f[:, 0]]), axis=1)
    vol = np.sum(np.einsum('ij,ij->i', v[f[:, 0]], np.cross(v[f[:, 1]], v[f[:, 2]]))) / 6.0
    dv, _ = cKDTree(pts).query(v, k=1, workers=-1)
    with open(f"{D}/{name}.obj", "w") as fh:
        fh.write("".join("v %.6f %.6f %.6f\n" % tuple(p / 1000.0) for p in v))
        fh.write("".join("f %d %d %d\n" % (a + 1, b + 1, c + 1) for a, b, c in f))
    if cap is not None:
        np.save(f"{D}/{name}_cap.npy", cap(v).astype(np.float32))
    print("POISSON", name, "grilla", tuple(shape), "componentes", nc, "tris", len(f), "degenerados", int((area2 < 1e-6).sum()),
          "vol_cm3 %.2f" % (vol / 1000.0), "desvio_mm media %.3f p95 %.3f p99 %.3f" % (dv.mean(), np.percentile(dv, 95), np.percentile(dv, 99)),
          "bbox_cm", np.round(v.min(0) / 10, 2), np.round(v.max(0) / 10, 2))


def solid(pts, nrm, name, cap=None, close_r=0.0, seams=None):
    lo = pts.min(0) - 4.0
    shape = np.ceil((pts.max(0) + 4.0 - lo) / VOX).astype(int) + 1
    sd = ndimage.gaussian_filter(field(pts, nrm, lo, shape, BAND), SIGMA)
    if close_r > 0:
        # cierre morfologico: inflar close_r y desinflar close_r rellena ranuras de hasta ~2*close_r sin tocar lo convexo
        v1, _, n1 = level(sd - close_r, lo)
        sd = ndimage.gaussian_filter(field(v1, n1, lo, shape, BAND + close_r / VOX + 2) + close_r, 0.5)
    if seams is not None and len(seams):
        # juntas: el campo se mezcla con su version desenfocada cerca de ellas (peso 1 sobre la junta, 0 a SEAM_R)
        occ = np.ones(shape, bool)
        ix = np.clip(np.floor((seams - lo) / VOX + 0.5).astype(int), 0, np.array(shape) - 1)
        occ[ix[:, 0], ix[:, 1], ix[:, 2]] = False
        u_ = np.clip(1.0 - ndimage.distance_transform_edt(occ) * VOX / SEAM_R, 0, 1)
        wgt = (u_ * u_ * (3 - 2 * u_)).astype(np.float32)
        sd = sd * (1 - wgt) + ndimage.gaussian_filter(sd, SEAM_SIGMA / VOX) * wgt
    v, f, _ = level(sd, lo)
    e = np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]])
    nc, labv = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(len(v), len(v))), directed=False)
    cnt = np.bincount(labv)
    keep = labv == np.argmax(cnt)
    f = f[keep[f[:, 0]]]
    remap = -np.ones(len(v), int)
    remap[keep] = np.arange(keep.sum())
    v, f = v[keep], remap[f]
    area2 = np.linalg.norm(np.cross(v[f[:, 1]] - v[f[:, 0]], v[f[:, 2]] - v[f[:, 0]]), axis=1)
    vol = np.sum(np.einsum('ij,ij->i', v[f[:, 0]], np.cross(v[f[:, 1]], v[f[:, 2]]))) / 6.0
    dv, _ = cKDTree(pts).query(v, k=1, workers=-1)
    with open(f"{D}/{name}.obj", "w") as fh:
        fh.write("".join("v %.6f %.6f %.6f\n" % tuple(p / 1000.0) for p in v))
        fh.write("".join("f %d %d %d\n" % (a + 1, b + 1, c + 1) for a, b, c in f))
    if cap is not None:
        np.save(f"{D}/{name}_cap.npy", cap(v).astype(np.float32))
    print("SOLIDO", name, "cierre_mm", close_r, "grilla", tuple(shape), "componentes", nc, "descartadas", sorted(cnt)[-4:-1],
          "tris", len(f), "degenerados", int((area2 < 1e-6).sum()), "vol_cm3 %.2f" % (vol / 1000.0),
          "desvio_mm media %.3f p99 %.3f max %.3f" % (dv.mean(), np.percentile(dv, 99), dv.max()),
          "bbox_cm", np.round(v.min(0) / 10, 2), np.round(v.max(0) / 10, 2))


src = np.load(f"{D}/tp_src.npz")
meta = json.load(open(f"{D}/tp_src.json"))
pb, nb, cb = phong(src["Pb"] * 1000.0, src["Nb"], src["Cb"])
pt, nt, _ = phong(src["Pt"] * 1000.0, src["Nt"], src["Ct"])
trig_c = pt.mean(0)
panel = np.isin(cb, PANELS)
tp_, pp, pn = cKDTree(pb[panel]), pb[panel], nb[panel]
# bolsillo del gatillo: sus normales miran hacia el gatillo (el "afuera" del bolsillo)
m = cb == POCKET
if (np.sum(nb[m] * (trig_c - pb[m]), 1)).mean() < 0:
    nb[m] = -nb[m]
# tiras oscuras (15-24): unas son el fondo de las juntas y otras piezas INTERNAS (p.ej. la 23 es un piso bajo la tapa);
# se sacan todas y las juntas las cierra la banda (continua el plano de los paneles)
drop = ~panel & (cb != POCKET)
if STRIPS == "drop":
    print("TIRAS fuera", sorted(set(np.unique(cb[drop]).tolist())), "muestras", int(drop.sum()))
for k in (np.unique(cb[drop]) if STRIPS == "flatten" else []):
    m = np.nonzero(cb == k)[0]
    d, j = tp_.query(pb[m], k=1)
    ok = d < 3.0
    s, n = pp[j[ok]], pn[j[ok]]
    pb[m[ok]] -= np.sum((pb[m[ok]] - s) * n, 1, keepdims=True) * n
    nb[m[ok]] = n
    nb[m[~ok]] *= np.sign(np.sum(nb[m[~ok]] * (pb[m[~ok]] - pb.mean(0)), 1, keepdims=True) + 1e-9)
    print("TIRA", int(k), "muestras", len(m), "acostadas", int(ok.sum()), "altura_media_mm %.2f" % d[ok].mean() if ok.any() else "")
keep = ~drop if STRIPS == "drop" else np.ones(len(pb), bool)
extra_p, extra_n = [], []
# linea de la tapa: plano medio (solo para orientar) + la curva real para la mascara
cap_ol = np.array(meta["cap_outline"]) * 1000.0
cc, cu, cv, cw = pca_frame(cap_ol)
if (nb[cb == 1] @ cw).mean() < 0:
    cw = -cw
    cv = np.cross(cw, cu)
wells = [np.array(f["loop"]) * 1000.0 for f in meta["fills"] if f["kind"] == "tapa"]
geo = []
for Lp in wells:
    c0 = Lp.mean(0)
    L = pb - c0
    h = L @ cw
    r = np.linalg.norm(L - np.outer(h, cw), axis=1)
    R = np.linalg.norm((Lp - c0) - np.outer((Lp - c0) @ cw, cw), axis=1).max()
    near = (cb == 1) & (np.abs(h) < 5.0)
    keep &= ~(near & (r < R + WELL_MARGIN))
    geo.append((c0, R, near, r, h))
for c0, R, near, r, h in geo:
    rg = keep & near & (r >= R + RING[0]) & (r < R + RING[1])
    L = pb[rg] - c0
    x, y, z = L @ cu, L @ cv, L @ cw
    nw = nb[rg] @ cw
    f, g = quad_fit(x, y, z, -(nb[rg] @ cu) / nw, -(nb[rg] @ cv) / nw, R + RING[1])
    res = z - f(x, y)
    X, Y = np.meshgrid(np.arange(-R - WELL_MARGIN - H, R + WELL_MARGIN + 2 * H, H), np.arange(-R - WELL_MARGIN - H, R + WELL_MARGIN + 2 * H, H), indexing='ij')
    X, Y = X.ravel(), Y.ravel()
    k = np.hypot(X, Y) < R + WELL_MARGIN + H
    X, Y = X[k], Y[k]
    fx, fy = g(X, Y)
    nr = cw[None] - fx[:, None] * cu[None] - fy[:, None] * cv[None]
    extra_p.append(c0 + X[:, None] * cu + Y[:, None] * cv + f(X, Y)[:, None] * cw)
    extra_n.append(nr / np.linalg.norm(nr, axis=1, keepdims=True))
    print("POZO R_mm %.1f corona %d residuo_mm rms %.3f max %.3f" % (R, rg.sum(), np.sqrt(np.mean(res ** 2)), np.abs(res).max()))
# JUNTAS entre paneles del cuerpo (tambien el boton de grip, que queda fundido al mango): bordes que lindan con OTRO
# panel del cuerpo (no con la tapa, su anillo ni el bolsillo del gatillo)
segs = boundary_segments(src["Pb"] * 1000.0, src["Cb"], BODY_PANELS)
sp, sc = [], []
for a_, b_, k in segs:
    n = max(1, int(np.linalg.norm(b_ - a_) / 0.2))
    t = np.linspace(0, 1, n + 1)[:, None]
    sp.append(a_ * (1 - t) + b_ * t)
    sc.append(np.full(n + 1, k))
sp, sc = np.concatenate(sp), np.concatenate(sc)
other = np.zeros(len(sp), bool)
okc = keep & np.isin(cb, BODY_PANELS)
bad = cKDTree(pb[np.isin(cb, (1, 12, POCKET))])
for k in np.unique(sc):
    m = sc == k
    d, _ = cKDTree(pb[okc & (cb != k)]).query(sp[m], k=1)
    other[m] = (d < 3.0) & (bad.query(sp[m], k=1)[0] > 2.5)
seams = sp[other]
print("JUNTAS puntos", len(seams), "de", len(sp))
# BOTON DE GRIP: la pieza entera se corre por su normal hasta quedar al ras del mango (mediana del desfase medido en
# su borde contra los paneles vecinos, a menos de 2 mm); su contorno queda en las juntas y lo borra el suavizado local
g6 = np.nonzero(keep & (cb == GRIP_PANEL))[0]
s6 = sp[other & (sc == GRIP_PANEL)]
d6 = cKDTree(s6).query(pb[g6], k=1)[0]
brd = g6[d6 < 1.5]
oth = keep & np.isin(cb, (0, 2, 3))
po, no = pb[oth], nb[oth]
d, j = cKDTree(po).query(pb[brd], k=1, distance_upper_bound=2.0)
ok = np.isfinite(d)
cosn = np.sum(no[j[ok]] * nb[brd[ok]], 1)
t = np.sum((po[j[ok]] - pb[brd[ok]]) * no[j[ok]], 1) / cosn
t = t[np.abs(cosn) > 0.8]
shift6 = float(np.median(t))
pb[g6] += shift6 * nb[g6]
print("BOTON_GRIP desfase_mm mediana %.3f (p10 %.3f p90 %.3f, n %d)" % (shift6, np.percentile(t, 10), np.percentile(t, 90), len(t)))
# recorte de 1 mm de borde en cada junta: ahi el panel se curva hacia la ranura; Poisson cierra el hueco liso
# (alrededor del boton de grip el recorte es mas ancho: su superficie y la del mango se funden en TRIM_GRIP)
near6 = cKDTree(pb[np.isin(cb, FILL_PANELS)]).query(sp, k=1)[0] < 3.0
dseam = np.full(len(pb), np.inf)
trim_of = np.full(len(pb), TRIM)
for k in BODY_PANELS:
    m = cb == k
    for sel, tr in ((other & (sc == k) & ~near6, TRIM), (other & (sc == k) & near6, TRIM_GRIP)):
        if sel.any():
            d = cKDTree(sp[sel]).query(pb[m], k=1)[0]
            cut = d < tr
            dseam[np.nonzero(m)[0][cut]] = 0.0
cutm = np.isin(cb, BODY_PANELS) & (dseam == 0.0)
keep &= ~cutm
# zonas que despues se rehacen por alisado de placa delgada sobre la malla: juntas, boton de grip, pieza de la correa
soften = [(seams, SOFT["juntas"][0], SOFT["juntas"][1]),
          (np.concatenate([pb[np.isin(cb, FILL_PANELS)]]), SOFT["boton_grip"][0], SOFT["boton_grip"][1])]
print("RECORTE juntas muestras", int(cutm.sum()))
for fl in meta["fills"]:
    if fl["kind"] == "gatillo":
        p, n = fan(np.array(fl["loop"]) * 1000.0, trig_c)
        pt, nt = np.concatenate([pt, p]), np.concatenate([nt, n])
pb = np.concatenate([pb[keep]] + extra_p)
nb = np.concatenate([nb[keep]] + extra_n)
print("MUESTRAS cuerpo", len(pb), "gatillo", len(pt))
# mascara: altura sobre la curva de la linea de la tapa (punto mas cercano de la curva, medida en cw)
seg = np.linspace(0, 1, 40)[:, None, None]
dense = (cap_ol[None] * (1 - seg) + np.roll(cap_ol, -1, 0)[None] * seg).reshape(-1, 3)
tc = cKDTree(dense)
cap = lambda V: (V - dense[tc.query(V)[1]]) @ cw
poisson_solid(pb, nb, "tp_body_R", cap=cap, soften=soften)
solid(pt, nt, "tp_trigger_R")
