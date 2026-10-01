# -*- coding: utf-8 -*-
"""ghost_smooth.py (2026-10-01) - SUAVIZA las tomas de los fantasmas: saca la vibracion de la mano (temblor ~6-12 Hz)
sin cambiar el gesto. Pedido de Beltran: "suavizalos, mi mano vibra mucho".
Entrada: VR_Test/Saved/ClaudeScripts/ghost/<DA>_crudo.json (lo escribe el volcado; la toma CRUDA queda ahi, intacta).
Salida:  <DA>_suave.json (mismo formato, Data suavizada) -> lo escribe en el DA ghost_smooth_write (script del editor).
Filtro: gaussiano en el tiempo, SIGMA cuadros (30 Hz). Posiciones: promedio ponderado. Rotaciones (pitch yaw roll de UE):
a cuaternion (formulas de FRotator::Quaternion / FQuat::Rotator), promedio ponderado con el signo alineado al central,
normalizado, y de vuelta. Gatillos y grips (18-21): SIN tocar (el clic tiene que ser nitido).
Uso: python ghost_smooth.py [sigma] [DA ...]      (sin DA: todas las que tengan _crudo.json)"""
import glob
import io
import json
import math
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
DIR = os.path.normpath(os.path.join(AQUI, '..', '..', '..', '..', '..', 'VR_Test', 'Saved', 'ClaudeScripts', 'ghost'))
POS = [(0, 1, 2), (6, 7, 8), (22, 23, 24), (28, 29, 30), (31, 32, 33)]
ROT = [(3, 4, 5), (9, 10, 11), (12, 13, 14), (15, 16, 17), (25, 26, 27)]   # (pitch, yaw, roll)


def rot_to_quat(p, y, r):
    h = math.pi / 360.0
    sp, cp = math.sin(p * h), math.cos(p * h)
    sy, cy = math.sin(y * h), math.cos(y * h)
    sr, cr = math.sin(r * h), math.cos(r * h)
    return (cr * sp * sy - sr * cp * cy,
            -cr * sp * cy - sr * cp * sy,
            cr * cp * sy - sr * sp * cy,
            cr * cp * cy + sr * sp * sy)


def norm_axis(a):
    a = math.fmod(a, 360.0)
    if a < 0:
        a += 360.0
    if a > 180.0:
        a -= 360.0
    return a


def quat_to_rot(q):
    x, y, z, w = q
    st = z * x - w * y
    yy = 2.0 * (w * z + x * y)
    yx = 1.0 - 2.0 * (y * y + z * z)
    thr = 0.4999995
    d = 180.0 / math.pi
    yaw = math.atan2(yy, yx) * d
    if st < -thr:
        return (-90.0, yaw, norm_axis(-yaw - 2.0 * math.atan2(x, w) * d))
    if st > thr:
        return (90.0, yaw, norm_axis(yaw - 2.0 * math.atan2(x, w) * d))
    pitch = math.asin(max(-1.0, min(1.0, 2.0 * st))) * d
    roll = math.atan2(-2.0 * (w * x + y * z), 1.0 - 2.0 * (x * x + y * y)) * d
    return (pitch, yaw, roll)


def qmat(q):
    x, y, z, w = q
    return [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w),
            2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w),
            2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]


def kernel(sigma):
    r = max(1, int(math.ceil(3 * sigma)))
    return [(k, math.exp(-0.5 * (k / sigma) ** 2)) for k in range(-r, r + 1)]


def smooth(data, frames, stride, sigma):
    out = list(data)
    K = kernel(sigma)

    def at(f, c):
        return data[f * stride + c]
    for f in range(frames):
        win = [(f + k, w) for k, w in K if 0 <= f + k < frames]
        ws = sum(w for _, w in win)
        for grp in POS:
            for c in grp:
                out[f * stride + c] = sum(at(g, c) * w for g, w in win) / ws
        for (pc, yc, rc) in ROT:
            q0 = rot_to_quat(at(f, pc), at(f, yc), at(f, rc))
            acc = [0.0, 0.0, 0.0, 0.0]
            for g, w in win:
                q = rot_to_quat(at(g, pc), at(g, yc), at(g, rc))
                if sum(a * b for a, b in zip(q, q0)) < 0:
                    q = tuple(-v for v in q)
                for i in range(4):
                    acc[i] += q[i] * w
            n = math.sqrt(sum(v * v for v in acc)) or 1.0
            p, y, r = quat_to_rot(tuple(v / n for v in acc))
            out[f * stride + pc], out[f * stride + yc], out[f * stride + rc] = p, y, r
    return out


def selftest(data, frames, stride):
    """Ida y vuelta rotador -> cuaternion -> rotador sobre los datos reales: compara MATRICES (no angulos)."""
    worst = 0.0
    for f in range(frames):
        for (pc, yc, rc) in ROT:
            q = rot_to_quat(data[f * stride + pc], data[f * stride + yc], data[f * stride + rc])
            q2 = rot_to_quat(*quat_to_rot(q))
            m1, m2 = qmat(q), qmat(q2)
            worst = max(worst, max(abs(a - b) for a, b in zip(m1, m2)))
    return worst


def jitter(data, frames, stride, c):
    """Energia de alta frecuencia de un canal: promedio de |segunda diferencia| (cm por cuadro^2)."""
    s = [data[f * stride + c] for f in range(frames)]
    d2 = [abs(s[i - 1] - 2 * s[i] + s[i + 1]) for i in range(1, len(s) - 1)]
    return sum(d2) / max(1, len(d2))


def main():
    args = sys.argv[1:]
    sigma = float(args[0]) if args and args[0].replace('.', '', 1).isdigit() else 2.5
    names = [a for a in args if not a.replace('.', '', 1).isdigit()]
    files = [os.path.join(DIR, n + '_crudo.json') for n in names] if names else sorted(glob.glob(os.path.join(DIR, '*_crudo.json')))
    for fp in files:
        v = json.load(io.open(fp, encoding='utf-8'))
        n, st, d = int(v['Frames']), int(v['Stride']), v['Data']
        err = selftest(d, n, st)
        if err > 1e-6:
            print(os.path.basename(fp), 'ERROR de conversion de rotaciones', err)
            continue
        sd = smooth(d, n, st, sigma)
        before = jitter(d, n, st, 1)
        after = jitter(sd, n, st, 1)
        v2 = dict(v)
        v2['Data'] = sd
        v2['Note'] = 'suavizado gaussiano sigma %.1f cuadros (crudo en %s)' % (sigma, os.path.basename(fp))
        out = fp.replace('_crudo.json', '_suave.json')
        io.open(out, 'w', encoding='utf-8').write(json.dumps(v2))
        print('%-18s %4d cuadros  conv %.1e  temblor grip R y: %.3f -> %.3f' % (os.path.basename(fp).replace('_crudo.json', ''), n, err, before, after))


if __name__ == '__main__':
    main()
