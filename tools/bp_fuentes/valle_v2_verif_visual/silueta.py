import numpy as np, vrender as vr
for tag in ("v1_t0_p25", "v2_t0_p25", "v2_t20_p25", "v2_t40_p25"):
    lin = np.load("pano_%s_lin.npy" % tag).astype(np.float64)
    dist = np.load("pano_%s_dist.npy" % tag).astype(np.float64)
    Hh, W = dist.shape
    el = 14.0 - (np.arange(Hh) + 0.5) / 25.0
    Lm = 255 * vr.srgb(lin); Lm = 0.2126 * Lm[..., 0] + 0.7152 * Lm[..., 1] + 0.0722 * Lm[..., 2]
    Yl = vr.Y(lin)
    ter = np.isfinite(dist) & ~((dist < 700.0) & (el[:, None] > -9.0))
    # columnas sin esfera delante del horizonte: |az| > 20
    az = -180.0 + (np.arange(W) + 0.5) / 25.0
    cols = np.abs(az) > 20.0
    top = np.argmax(ter, axis=0)           # primera fila de terreno (desde arriba)
    c = np.arange(W)
    elt = el[top]; dt = dist[top, c] / 100.0
    # contraste silueta-cielo: 3 px arriba (cielo) vs 3 px abajo (terreno)
    up = Yl[np.clip(top - 3, 0, Hh - 1), c]; dn = Yl[np.clip(top + 3, 0, Hh - 1), c]
    wc = np.abs(dn - up) / np.maximum(up, 1e-6) * 100
    dl = np.abs(Lm[np.clip(top + 3, 0, Hh - 1), c] - Lm[np.clip(top - 3, 0, Hh - 1), c])
    # hueco: cielo DEBAJO del horizonte (el < -0.05) en alguna columna
    hueco = (~np.isfinite(dist)) & (el[:, None] < -0.05)
    lejos = np.isfinite(dist) & (dist > 58000)
    print("%s  silueta: elev p10 %.2f p50 %.2f p90 %.2f deg | dist p10 %.0f p50 %.0f p90 %.0f m | contraste Weber silueta/cielo p50 %.1f%% p90 %.1f%% | salto de luma p50 %.1f niv"
          % (tag, *np.percentile(elt[cols], [10, 50, 90]), *np.percentile(dt[cols], [10, 50, 90]),
             np.median(wc[cols]), np.percentile(wc[cols], 90), np.median(dl[cols])))
    print("      pixeles de cielo bajo el horizonte (hueco): %d ; pixeles de terreno a > 580 m (zona de retiro/borde): %d" % (hueco.sum(), lejos.sum()))
