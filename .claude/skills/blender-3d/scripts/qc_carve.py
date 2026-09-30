# qc_carve.py - mando de la obra (4a version): talla el VACIO DEL GATILLO en la forma organica ya calculada (qc_fit.py).
# Idea de Beltran: primero la forma organica completa (sin botones), despues el vacio para el boton. El vacio es el
# volumen que BARRE el gatillo al apretarlo (0..PRESS grados sobre su bisagra, la del hueso del gatillo oficial) mas una
# holgura, restado del cuerpo con union suave (borde redondeado). Asi el gatillo entra en su hueco sin atravesar nada.
#   cuerpo y gatillo -> campos de distancia con signo (punto-plano sobre su superficie de subdivision, grilla 0,25 mm)
#   barrido = min sobre angulos del campo del gatillo rotado; cuerpo' = max_suave(cuerpo, HOLGURA - barrido, REDONDEO)
#   marching cubes -> componente mayor -> qc_body_R_carved.obj + mascara de la tapa (altura sobre la linea de la tapa)
# Uso: python qc_carve.py <dir>
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
VOX = 0.25       # mm
H = 0.12         # mm, muestreo de las superficies
BAND = 5.0       # voxeles
CLEAR = 0.7      # mm de holgura entre gatillo y cuerpo
FILLET = 1.0     # mm de redondeo del borde del vacio
PRESS = 16.0     # grados que cubre el vacio (el BP usa hasta 14)
STEP = 1.0       # grados entre copias del barrido
_bary = {}


def bary(n):
    if n not in _bary:
        i, j = np.meshgrid(np.arange(n + 1), np.arange(n + 1), indexing='ij')
        m = (i + j) <= n
        _bary[n] = np.stack([i[m] / n, j[m] / n, 1 - i[m] / n - j[m] / n], 1)
    return _bary[n]


def read_quads(path):
    V, F = [], []
    for line in open(path):
        if line.startswith("v "):
            V.append([float(x) for x in line.split()[1:4]])
        elif line.startswith("f "):
            F.append([int(x.split("/")[0]) - 1 for x in line.split()[1:]])
    V, F = np.array(V) * 1000.0, np.array(F)
    fn = np.cross(V[F[:, 2]] - V[F[:, 0]], V[F[:, 3]] - V[F[:, 1]])
    vn = np.zeros_like(V)
    for c in range(4):
        np.add.at(vn, F[:, c], fn)
    vn /= np.linalg.norm(vn, axis=1, keepdims=True)
    T = np.concatenate([F[:, [0, 1, 2]], F[:, [0, 2, 3]]])
    return V, T, vn


def samples(V, T, N, alpha=0.75):
    """Superficie curva (Phong) sobre los triangulos con las normales de la superficie de subdivision."""
    L = np.max(np.stack([np.linalg.norm(V[T[:, a]] - V[T[:, b]], axis=1) for a, b in ((0, 1), (1, 2), (2, 0))], 1), 1)
    nsub = np.maximum(1, np.ceil(L / H).astype(int))
    pts, nrm = [], []
    for n in np.unique(nsub):
        B = bary(n)
        tt = T[nsub == n]
        p = V[tt]                     # (t,3,3)
        nn = N[tt]
        q = np.einsum('kc,tcd->tkd', B, p)
        acc = np.zeros_like(q)
        for a in range(3):
            d = np.sum((q - p[:, a:a + 1]) * nn[:, a:a + 1], 2, keepdims=True)
            acc += B[None, :, a:a + 1] * (q - d * nn[:, a:a + 1])
        nr = np.einsum('kc,tcd->tkd', B, nn)
        pts.append(((1 - alpha) * q + alpha * acc).reshape(-1, 3))
        nrm.append((nr / np.linalg.norm(nr, axis=2, keepdims=True)).reshape(-1, 3))
    return np.concatenate(pts), np.concatenate(nrm)


def field(pts, nrm, lo, shape, band_vox):
    occ = np.ones(shape, bool)
    ix = np.floor((pts - lo) / VOX + 0.5).astype(int)
    ok = np.all((ix >= 0) & (ix < shape), 1)
    occ[ix[ok, 0], ix[ok, 1], ix[ok, 2]] = False
    band = ndimage.distance_transform_edt(occ) <= band_vox
    del occ
    lab, _ = ndimage.label(~band)
    brd = np.unique(np.concatenate([lab[0].ravel(), lab[-1].ravel(), lab[:, 0].ravel(), lab[:, -1].ravel(),
                                    lab[:, :, 0].ravel(), lab[:, :, -1].ravel()]))
    sd = np.where(np.isin(lab, brd[brd > 0]), band_vox * VOX, -band_vox * VOX).astype(np.float32)
    del lab
    bi = np.nonzero(band)
    Xv = lo + np.stack(bi, 1) * VOX
    _, j = cKDTree(pts).query(Xv, k=1, workers=-1)
    sd[bi] = np.sum((Xv - pts[j]) * nrm[j], 1)
    return sd


def rot(axis, deg):
    a = axis / np.linalg.norm(axis)
    t = math.radians(deg)
    K = np.array([[0, -a[2], a[1]], [a[2], 0, -a[0]], [-a[1], a[0], 0]])
    return np.eye(3) + math.sin(t) * K + (1 - math.cos(t)) * K @ K


def smin(a, b, k):
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0, 1)
    return b + (a - b) * h - k * h * (1 - h)


meta = json.load(open(f"{D}/tp_src.json"))
bone = meta["bones"]["right_b_trigger_front"]
piv = np.array(bone["head"]) * 1000.0
axes = {k: np.array(bone[k]) for k in "xyz"}
ax = max(axes.values(), key=lambda a: abs(a[0]))
ax = ax * np.sign(ax[0])
Vb, Tb, Nb = read_quads(f"{D}/qc_body_R_fit_L2.obj")
Vt, Tt, Nt = read_quads(f"{D}/qc_trigger_R_fit_L2.obj")
pb, nb = samples(Vb, Tb, Nb)
pt, nt = samples(Vt, Tt, Nt)
lo = pb.min(0) - 3.0
shape = tuple(np.ceil((pb.max(0) + 3.0 - lo) / VOX).astype(int) + 1)
sdb = field(pb, nb, lo, shape, BAND)
# campo del gatillo en su propia grilla (reposo)
lot = pt.min(0) - 4.0
sht = tuple(np.ceil((pt.max(0) + 4.0 - lot) / VOX).astype(int) + 1)
sdt = field(pt, nt, lot, sht, 8.0)
# sentido de "apretar": el que mete el gatillo hacia el cuerpo (mas penetracion)
def pen(deg):
    q = (Vt - piv) @ rot(ax, deg).T + piv
    v = ndimage.map_coordinates(sdb, ((q - lo) / VOX).T, order=1, cval=10.0)
    return (v < 0).mean(), -v.min()
sgn = 1.0 if pen(PRESS)[0] >= pen(-PRESS)[0] else -1.0
for dg in (0.0, 7.0, 14.0):
    fr, mx = pen(sgn * dg)
    print("PENETRACION antes gatillo %2d deg: vertices adentro %.3f max_mm %.2f" % (dg, fr, mx))
# barrido del gatillo sobre la grilla del cuerpo (solo la caja que puede tocar)
box_lo = np.floor((pt.min(0) - 12.0 - lo) / VOX).astype(int).clip(0)
box_hi = np.minimum(np.ceil((pt.max(0) + 12.0 - lo) / VOX).astype(int), np.array(shape))
sl = tuple(slice(a, b) for a, b in zip(box_lo, box_hi))
gi = np.stack(np.meshgrid(*[np.arange(a, b) for a, b in zip(box_lo, box_hi)], indexing='ij'), -1).reshape(-1, 3)
X = lo + gi * VOX
sw = np.full(len(X), 1e3, np.float32)
for dg in np.arange(0.0, PRESS + 1e-6, STEP):
    q = (X - piv) @ rot(ax, -sgn * dg).T + piv          # punto del mundo -> marco del gatillo en reposo
    sw = np.minimum(sw, ndimage.map_coordinates(sdt, ((q - lot) / VOX).T, order=1, cval=1e3))
sub = sdb[sl].reshape(-1)
carved = -smin(-sub, -(CLEAR - sw), FILLET)
sdb[sl] = carved.reshape(sdb[sl].shape)
print("VACIO voxeles tallados", int((carved > sub + 1e-4).sum()), "sentido_apretar", sgn, "eje", np.round(ax, 3), "pivote_mm", np.round(piv, 2))
v, f, _, _ = measure.marching_cubes(sdb, 0.0, spacing=(VOX, VOX, VOX), gradient_direction='ascent')
v += lo
f = f[:, [0, 2, 1]]
e = np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]])
nc, labv = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(len(v), len(v))), directed=False)
keep = labv == np.argmax(np.bincount(labv))
f = f[keep[f[:, 0]]]
remap = -np.ones(len(v), int)
remap[keep] = np.arange(keep.sum())
v, f = v[keep], remap[f]
dv = cKDTree(pb).query(v, k=1, workers=-1)[0]
print("CUERPO_TALLADO componentes", nc, "tris", len(f), "desvio_vs_forma_mm p50 %.3f p99 %.3f max %.2f" % (np.median(dv), np.percentile(dv, 99), dv.max()))
# chequeo: con el vacio, el gatillo ya no toca el cuerpo en todo su recorrido
sdc = sdb
for dg in (0.0, 7.0, 14.0):
    q = (Vt - piv) @ rot(ax, sgn * dg).T + piv
    vv = ndimage.map_coordinates(sdc, ((q - lo) / VOX).T, order=1, cval=10.0)
    print("PENETRACION despues gatillo %2d deg: vertices adentro %.4f holgura_min_mm %.2f" % (dg, (vv < 0).mean(), vv.min()))
with open(f"{D}/qc_body_R_carved.obj", "w") as fh:
    fh.write("".join("v %.6f %.6f %.6f\n" % tuple(p / 1000.0) for p in v))
    fh.write("".join("f %d %d %d\n" % (a + 1, b + 1, c + 1) for a, b, c in f))
cap_ol = np.array(meta["cap_outline"]) * 1000.0
c0 = cap_ol.mean(0)
_, _, vt = np.linalg.svd(cap_ol - c0)
cw = vt[2] if vt[2][2] > 0 else -vt[2]
seg = np.linspace(0, 1, 40)[:, None, None]
dense = (cap_ol[None] * (1 - seg) + np.roll(cap_ol, -1, 0)[None] * seg).reshape(-1, 3)
np.save(f"{D}/qc_body_R_carved_cap.npy", ((v - dense[cKDTree(dense).query(v)[1]]) @ cw).astype(np.float32))
json.dump({"pivot_mm": piv.tolist(), "axis": ax.tolist(), "press_sign": sgn, "clear_mm": CLEAR, "press_deg_max": PRESS},
          open(f"{D}/qc_trigger_hinge.json", "w"))
print("CARVE_OK")
