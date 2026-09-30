# qc_fit.py - mando de la obra (4a version, 2026-09-29): SUPERFICIE DE SUBDIVISION CALCULADA sobre el Touch Plus oficial.
# Enfoque (pedido de Beltran: "modelarlo de 0 con un approach claro"): el mando es una superficie Catmull-Clark con
# ~2.000 puntos de control (jaula de qc_cage.py). La superficie es lisa POR CONSTRUCCION: no puede tener ranuras ni
# botones (son mas chicos que la jaula). La POSICION de cada punto de control se CALCULA para que la superficie pase por
# los puntos medidos del modelo oficial de Meta (el "plano" mas preciso que existe), sin usar su geometria como malla:
#   datos = paneles del cuerpo muestreados como superficie curva (Phong con las normales del artista), SIN botones, SIN
#   tiras de juntas, SIN bolsillo del gatillo, SIN la pieza del boton de grip, SIN 1,2 mm de borde de cada pieza
#   (donde se curvan hacia las ranuras); los pozos de A/B/Meta/stick se reemplazan por la tapa ajustada (cuadrica)
#   ajuste = ICP punto-plano sobre la superficie subdividida (nivel 3) + suavidad de la jaula, resuelto como minimos
#   cuadrados dispersos; se repite con correspondencias nuevas hasta converger.
# Salida: qc_*_fit_L{1,2}.obj (malla subdividida en quads), jaula ajustada, mascara de la tapa y el desvio en mm.
# Uso: python qc_fit.py <dir>   (Python del sistema: numpy, scipy)
import json
import math
import sys

import numpy as np
from scipy.sparse import coo_matrix, diags, hstack, identity, kron
from scipy.sparse.linalg import spsolve
from scipy.spatial import cKDTree

D = sys.argv[1] if len(sys.argv) > 1 else "."
H = 0.1              # mm, separacion de muestras de los paneles
EXCL = 1.2           # mm de borde de pieza que no se usa
DOWN = 0.35          # mm, submuestreo de los datos
LEVEL = 3            # nivel de subdivision para las correspondencias
ITERS = 12
LAM = 0.02           # suavidad de la jaula (relativa a datos por punto de control)
MU = 0.002           # amortiguacion (relativa)
MAXD = 3.0           # mm, correspondencia maxima
_bary = {}


def bary(n):
    if n not in _bary:
        i, j = np.meshgrid(np.arange(n + 1), np.arange(n + 1), indexing='ij')
        m = (i + j) <= n
        _bary[n] = np.stack([i[m] / n, j[m] / n, 1 - i[m] / n - j[m] / n], 1)
    return _bary[n]


def phong(P, N, C, alpha=0.75):
    pts, nrm, cid = [], [], []
    for p, nn, c in zip(P, N, C):
        L = max(np.linalg.norm(p[0] - p[1]), np.linalg.norm(p[1] - p[2]), np.linalg.norm(p[2] - p[0]))
        B = bary(max(1, int(math.ceil(L / H))))
        q = B @ p
        acc = np.zeros_like(q)
        for a in range(3):
            acc += B[:, a:a + 1] * (q - np.sum((q - p[a]) * nn[a], 1, keepdims=True) * nn[a])
        nr = B @ nn
        pts.append((1 - alpha) * q + alpha * acc)
        nrm.append(nr / np.linalg.norm(nr, axis=1, keepdims=True))
        cid.append(np.full(len(B), c, np.int16))
    return np.concatenate(pts), np.concatenate(nrm), np.concatenate(cid)


def boundary_points(P, C, comps, step=0.2):
    out = []
    for k in comps:
        T = P[C == k]
        if not len(T):
            continue
        e = np.concatenate([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]])
        q = np.round(e * 1000).astype(np.int64)
        a, b = q[:, 0], q[:, 1]
        gt = (a[:, 0] > b[:, 0]) | ((a[:, 0] == b[:, 0]) & ((a[:, 1] > b[:, 1]) | ((a[:, 1] == b[:, 1]) & (a[:, 2] > b[:, 2]))))
        key = np.concatenate([np.where(gt[:, None], b, a), np.where(gt[:, None], a, b)], 1)
        _, inv, cnt = np.unique(key, axis=0, return_inverse=True, return_counts=True)
        for s0, s1 in e[cnt[inv.ravel()] == 1]:
            n = max(1, int(np.linalg.norm(s1 - s0) / step))
            t = np.linspace(0, 1, n + 1)[:, None]
            out.append(s0 * (1 - t) + s1 * t)
    return np.concatenate(out)


def pca_frame(loop):
    c = loop.mean(0)
    _, _, vt = np.linalg.svd(loop - c)
    return c, vt[0], np.cross(vt[2], vt[0]), vt[2]


def quad_fit(x, y, z, gx, gy, s):
    X, Y = x / s, y / s
    o, zr = np.ones_like(X), np.zeros_like(X)
    A = np.stack([X * X, X * Y, Y * Y, X, Y, o], 1)
    Ax = np.stack([2 * X, Y, zr, o, zr, zr], 1)
    Ay = np.stack([zr, X, 2 * Y, zr, o, zr], 1)
    k = np.linalg.lstsq(np.concatenate([A, Ax, Ay]), np.concatenate([z, gx * s, gy * s]), rcond=None)[0]
    f = lambda x, y: k[0] * (x / s) ** 2 + k[1] * (x / s) * (y / s) + k[2] * (y / s) ** 2 + k[3] * x / s + k[4] * y / s + k[5]
    g = lambda x, y: ((2 * k[0] * x / s + k[1] * y / s + k[3]) / s, (k[1] * x / s + 2 * k[2] * y / s + k[4]) / s)
    return f, g


def downsample(P, N, vox):
    key = np.floor(P / vox).astype(np.int64)
    _, first = np.unique(key, axis=0, return_index=True)
    return P[first], N[first]


# ---------------------------------------------------------------- Catmull-Clark como matriz dispersa
def cc_step(nv, faces):
    """Un nivel de Catmull-Clark (malla cerrada): S (nuevos x viejos) y las caras nuevas (quads)."""
    edges, E, fedges = {}, [], []
    for f in faces:
        fe = []
        for k in range(len(f)):
            a, b = f[k], f[(k + 1) % len(f)]
            key = (a, b) if a < b else (b, a)
            if key not in edges:
                edges[key] = len(E)
                E.append(key)
            fe.append(edges[key])
        fedges.append(fe)
    ne, nf = len(E), len(faces)
    ef = [[] for _ in range(ne)]
    vf = [[] for _ in range(nv)]
    ve = [[] for _ in range(nv)]
    for fi, fe in enumerate(fedges):
        for e in fe:
            ef[e].append(fi)
        for v in faces[fi]:
            vf[v].append(fi)
    for ei, (a, b) in enumerate(E):
        ve[a].append(ei)
        ve[b].append(ei)
    R, Cc, V = [], [], []
    for fi, f in enumerate(faces):
        for v in f:
            R.append(nv + ne + fi); Cc.append(v); V.append(1.0 / len(f))
    for ei, (a, b) in enumerate(E):
        assert len(ef[ei]) == 2, "malla no cerrada"
        R += [nv + ei, nv + ei]; Cc += [a, b]; V += [0.25, 0.25]
        for fi in ef[ei]:
            for v in faces[fi]:
                R.append(nv + ei); Cc.append(v); V.append(0.25 / len(faces[fi]))
    for v in range(nv):
        n, k = len(ve[v]), len(vf[v])
        for fi in vf[v]:
            for u in faces[fi]:
                R.append(v); Cc.append(u); V.append(1.0 / (k * len(faces[fi]) * n))
        for ei in ve[v]:
            a, b = E[ei]
            R += [v, v]; Cc += [a, b]; V += [1.0 / (n * n), 1.0 / (n * n)]
        R.append(v); Cc.append(v); V.append((n - 3.0) / n)
    S = coo_matrix((V, (R, Cc)), shape=(nv + ne + nf, nv)).tocsr()
    newf = []
    for fi, f in enumerate(faces):
        fe = fedges[fi]
        m = len(f)
        for k in range(m):
            newf.append([f[k], nv + fe[k], nv + ne + fi, nv + fe[(k - 1) % m]])
    return S, newf


def subdivision(nv, faces, levels):
    mats, fs, S, n = [], [faces], None, nv
    for _ in range(levels):
        Sk, faces = cc_step(n, faces)
        S = Sk if S is None else Sk @ S
        n = Sk.shape[0]
        mats.append(S.tocsr())
        fs.append(faces)
    return mats, fs


def vnormals(P, F):
    F = np.asarray(F)
    fn = np.cross(P[F[:, 2]] - P[F[:, 0]], P[F[:, 3]] - P[F[:, 1]])
    vn = np.zeros_like(P)
    for c in range(4):
        np.add.at(vn, F[:, c], fn)
    return vn / (np.linalg.norm(vn, axis=1, keepdims=True) + 1e-12)


def read_obj(path):
    V, F = [], []
    for line in open(path):
        if line.startswith("v "):
            V.append([float(x) for x in line.split()[1:4]])
        elif line.startswith("f "):
            F.append([int(x.split("/")[0]) - 1 for x in line.split()[1:]])
    return np.array(V) * 1000.0, F


def write_obj(path, P, F):
    with open(path, "w") as fh:
        fh.write("".join("v %.6f %.6f %.6f\n" % tuple(p / 1000.0) for p in P))
        fh.write("".join("f " + " ".join(str(i + 1) for i in f) + "\n" for f in F))


def fit(name, data_p, data_n, cap=None):
    X, F0 = read_obj(f"{D}/qc_cage_{name}_R.obj")
    n = len(X)
    mats, fs = subdivision(n, F0, LEVEL)
    S = mats[-1]
    FL = fs[-1]
    # suavidad de la jaula: laplaciano uniforme
    e = set()
    for f in F0:
        for k in range(len(f)):
            a, b = f[k], f[(k + 1) % len(f)]
            e.add((min(a, b), max(a, b)))
    e = np.array(sorted(e))
    A = coo_matrix((np.ones(2 * len(e)), (np.concatenate([e[:, 0], e[:, 1]]), np.concatenate([e[:, 1], e[:, 0]]))), shape=(n, n)).tocsr()
    Lc = identity(n) - diags(1.0 / np.asarray(A.sum(1)).ravel()) @ A
    LtL = kron(identity(3), (Lc.T @ Lc).tocsr())
    tree_d = cKDTree(data_p)
    for it in range(ITERS + 1):
        P = S @ X
        N = vnormals(P, FL)
        d, j = cKDTree(P).query(data_p, k=1, workers=-1)
        ok = (d < MAXD) & (np.sum(data_n * N[j], 1) > 0.3)
        r = np.sum(data_n * (P[j] - data_p), 1)
        # desvio en ambos sentidos: datos -> superficie (punto-plano) y superficie -> datos (hay superficie sin datos cerca?)
        ds, _ = tree_d.query(P, k=1, workers=-1)
        print("ITER", it, "validos %.3f" % ok.mean(), "desvio_mm |punto-plano| media %.3f p95 %.3f p99 %.3f" %
              (np.abs(r[ok]).mean(), np.percentile(np.abs(r[ok]), 95), np.percentile(np.abs(r[ok]), 99)),
              "sup->datos p50 %.2f p95 %.2f" % (np.median(ds), np.percentile(ds, 95)))
        if it == ITERS:
            break
        Sj = S[j[ok]]
        nd = data_n[ok]
        Aj = hstack([diags(nd[:, 0]) @ Sj, diags(nd[:, 1]) @ Sj, diags(nd[:, 2]) @ Sj]).tocsr()
        b = np.sum(nd * data_p[ok], 1)
        w = len(b) / n
        x0 = np.concatenate([X[:, 0], X[:, 1], X[:, 2]])
        M = (Aj.T @ Aj) + (LAM * w) * LtL + (MU * w) * identity(3 * n)
        rhs = Aj.T @ b + (MU * w) * x0
        x = spsolve(M.tocsc(), rhs)
        X = np.stack([x[:n], x[n:2 * n], x[2 * n:]], 1)
    write_obj(f"{D}/qc_cage_{name}_R_fit.obj", X, F0)
    # MALLA FINAL: topologia del nivel 1 (quads limpios) con cada vertice en su posicion LIMITE (la del nivel 3, que ya
    # convergio) y la normal de la superficie limite -> interpola la superficie lisa exacta con pocos triangulos
    P3 = mats[2] @ X
    N3 = vnormals(P3, fs[3])
    n1 = mats[0].shape[0]
    write_obj(f"{D}/qc_{name}_R_final.obj", P3[:n1], fs[1])
    np.save(f"{D}/qc_{name}_R_final_nrm.npy", N3[:n1].astype(np.float32))
    if cap is not None:
        np.save(f"{D}/qc_{name}_R_final_cap.npy", cap(P3[:n1]).astype(np.float32))
    print("FINAL", name, "verts", n1, "quads", len(fs[1]), "tris", 2 * len(fs[1]))
    for L in (1, 2):
        PL = mats[L - 1] @ X
        write_obj(f"{D}/qc_{name}_R_fit_L{L}.obj", PL, fs[L])
        if cap is not None:
            np.save(f"{D}/qc_{name}_R_fit_L{L}_cap.npy", cap(PL).astype(np.float32))
        print("MALLA", name, "nivel", L, "verts", len(PL), "quads", len(fs[L]))
    np.save(f"{D}/qc_{name}_R_resid.npy", np.concatenate([data_p, r[:, None], ok[:, None]], 1).astype(np.float32))


src = np.load(f"{D}/tp_src.npz")
meta = json.load(open(f"{D}/tp_src.json"))
BODY = (0, 1, 2, 3, 13)
pb, nb, cb = phong(src["Pb"] * 1000.0, src["Nb"], src["Cb"])
use = np.isin(cb, BODY)
bpts = boundary_points(src["Pb"] * 1000.0, src["Cb"], BODY)
use &= cKDTree(bpts).query(pb, k=1, workers=-1)[0] > EXCL
# tapa: los pozos de A/B/Meta/stick se reemplazan por la cuadrica ajustada a su corona
cap_ol = np.array(meta["cap_outline"]) * 1000.0
cc, cu, cv, cw = pca_frame(cap_ol)
if (nb[cb == 1] @ cw).mean() < 0:
    cw, cv = -cw, -cv
extra_p, extra_n = [], []
for f in meta["fills"]:
    if f["kind"] != "tapa":
        continue
    Lp = np.array(f["loop"]) * 1000.0
    c0 = Lp.mean(0)
    L = pb - c0
    h = L @ cw
    r = np.linalg.norm(L - np.outer(h, cw), axis=1)
    R = np.linalg.norm((Lp - c0) - np.outer((Lp - c0) @ cw, cw), axis=1).max()
    near = (cb == 1) & (np.abs(h) < 5.0)
    use &= ~(near & (r < R + 1.5))
    rg = use & near & (r >= R + 1.5) & (r < R + 4.5)
    Lr = pb[rg] - c0
    nw = nb[rg] @ cw
    fq, gq = quad_fit(Lr @ cu, Lr @ cv, Lr @ cw, -(nb[rg] @ cu) / nw, -(nb[rg] @ cv) / nw, R + 4.5)
    g = np.arange(-R - 1.5, R + 1.5 + H, H)
    Xg, Yg = np.meshgrid(g, g, indexing='ij')
    Xg, Yg = Xg.ravel(), Yg.ravel()
    k = np.hypot(Xg, Yg) < R + 1.5
    Xg, Yg = Xg[k], Yg[k]
    fx, fy = gq(Xg, Yg)
    nr = cw[None] - fx[:, None] * cu[None] - fy[:, None] * cv[None]
    extra_p.append(c0 + Xg[:, None] * cu + Yg[:, None] * cv + fq(Xg, Yg)[:, None] * cw)
    extra_n.append(nr / np.linalg.norm(nr, axis=1, keepdims=True))
dp, dn = downsample(np.concatenate([pb[use]] + extra_p), np.concatenate([nb[use]] + extra_n), DOWN)
print("DATOS cuerpo", len(dp), "(de", len(pb), "muestras de paneles)")
seg = np.linspace(0, 1, 40)[:, None, None]
dense = (cap_ol[None] * (1 - seg) + np.roll(cap_ol, -1, 0)[None] * seg).reshape(-1, 3)
tcap = cKDTree(dense)
fit("body", dp, dn, cap=lambda V: (V - dense[tcap.query(V)[1]]) @ cw)
# gatillo: todo su casco oficial menos 1,2 mm alrededor de su boca (queda adentro del cuerpo)
pt, nt, ct = phong(src["Pt"] * 1000.0, src["Nt"], src["Ct"])
ut = cKDTree(boundary_points(src["Pt"] * 1000.0, src["Ct"], np.unique(src["Ct"]))).query(pt, k=1)[0] > EXCL
tp_, tn_ = downsample(pt[ut], nt[ut], DOWN)
print("DATOS gatillo", len(tp_))
fit("trigger", tp_, tn_)
