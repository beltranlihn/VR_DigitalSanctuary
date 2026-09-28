# -*- coding: utf-8 -*-
"""verify_flare.py - el ancla del ENSANCHE de la hebra contra la membrana del nucleo (revision 2026-09-28).

StrandR es un cilindro de radio rEnd hasta zCs y despues cae. Con la ameba V4 la membrana tiene pendiente: si el
ancla solo mira el EJE, el borde del cilindro asoma del lado que baja (un "munon"). ArmSetup inclina el ancla:
zCs(n) = AP5.x + tilt . n (tilt = gAx rEnd/rAx) y baja AP5.x en rEnd^2/rAx. Aca, con el espejo lvport.ArmSetup:
  pared = max sobre el borde del cilindro (48 azimuts, 13 alturas hasta 3 cm debajo) de |P| - membrana, con
  membrana = CentreR + abultamiento PROPIO + CentreGap (los vecinos solo SUBEN la membrana en el eje).
CONTROL del instrumento: el mismo barrido con el ancla de la primera integracion (solo el eje, sin inclinar)
tiene que dar paredes > 1 cm; si no, el instrumento no ve el defecto.
Criterio: pared max <= 0,25 cm en los casos normales (el extremo NoiseAmount 2 + Agitation 1 se reporta aparte).
Uso: python verify_flare.py [ensayos por caso]
"""
import sys
import numpy as np
import lvport as L


def nrm(v):
    return v / np.linalg.norm(v)


def run(NA, ag, sv, S, ntr, seed=21):
    rng = np.random.default_rng(seed)
    W = {'final': [], 'control_eje': []}
    tl = []
    for _ in range(ntr):
        T = rng.uniform(0, 20000); a = nrm(rng.normal(size=3)); idx = float(rng.integers(0, 10))
        LV0 = np.array([0, 0, 0, 16.0]); LV1 = np.array([S, rng.uniform(0, 6.28), ag, 0]); LV2 = np.array([1.0, 1, 1, 1])
        LV3 = np.array([1, 1, NA, 1]); LV4 = np.array([0.966, 0, 0.259, 0.8]); LV5 = np.array([sv, 1.0, 0, 0])
        G = a * 60.0
        AP, B = L.ArmSetup(G, idx, LV0, LV1, LV2, LV3, LV4, LV5, T)
        sh = AP['sh']; gC = L.CentreGap(LV1, LV3, sh['Rc']); rEnd = AP['AP3'][1]; MH = sh['MoundH']
        ax = nrm(G - LV0[:3])
        e1 = nrm(np.cross(ax, [0.3, 0.2, 0.9])); e2 = np.cross(ax, e1)
        ph = np.linspace(0, 2 * np.pi, 48, endpoint=False)
        nn = np.outer(np.cos(ph), e1) + np.outer(np.sin(ph), e2)
        rAx, _ = L.CentreR(ax[None], sh['Rc'], LV1, LV3, T)
        tl.append(np.linalg.norm(AP['tilt']))
        for key, zc in (('final', AP['AP5'][0] + nn @ AP['tilt']), ('control_eje', np.full(48, rAx[0] + gC + 0.8 * MH))):
            best = -1e9
            for dz in np.linspace(-3.0, 0.0, 13):
                P = ax[None] * (zc + dz)[:, None] + rEnd * nn
                Ln = np.linalg.norm(P, axis=1); u = P / Ln[:, None]
                rm, _ = L.CentreR(u, sh['Rc'], LV1, LV3, T)
                gm = np.zeros_like(u)
                rm = rm + L.Mound(u, ax, MH, 0.55, gm)
                best = max(best, (Ln - (rm + gC)).max())
            W[key].append(best)
    f = np.array(W['final']); c = np.array(W['control_eje']); tl = np.array(tl)
    print('NA %.0f Ag %.0f SV %.1f S %.2f | pared FINAL p50 %5.2f p99 %5.2f max %5.2f cm | control (ancla solo en el eje) max %5.2f | |tilt| p50 %.2f max %.2f cm'
          % (NA, ag, sv, S, np.median(f), np.percentile(f, 99), f.max(), c.max(), np.median(tl), tl.max()))
    sys.stdout.flush()
    return f.max(), c.max()


if __name__ == "__main__":
    ntr = int(sys.argv[1]) if len(sys.argv) > 1 else 500
    ok = True
    for cfg in [(1.0, 0.0, 0.5, 0.3), (1.0, 0.0, 0.5, 0.0), (1.0, 1.0, 0.5, 0.0), (1.0, 0.0, 1.0, 0.0), (1.0, 0.0, 1.0, 0.45)]:
        fm, cm = run(*cfg, ntr=ntr)
        ok &= (fm <= 0.25) and (cm > 1.0)
    run(2.0, 1.0, 1.0, 0.0, ntr=ntr)          # extremo: se reporta, no entra al criterio
    print("\n%s" % ("TODO OK" if ok else "HAY FALLAS"))
    sys.exit(0 if ok else 1)
