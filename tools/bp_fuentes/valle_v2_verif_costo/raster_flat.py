# raster_flat.py - el modo 1 del banco (vertices baratos: disco PLANO de 640 m) cambia la cobertura y el
# sobre-sombreado del suelo lejano. Cuanto, contra el modo 0? (para leer bien "pixeles = m1 - m3").
import json, time
from pathlib import Path
import numpy as np
import raster_cost as rc

OUT = Path(__file__).resolve().parent
rs, S = rc.radios_v2()
V, T = rc.malla(rs, S, lambda x, y, t: np.zeros_like(x), 0.0)
t0 = time.time()
r = rc.render(V, T, rc.camara((0, 0, 120.0), 0, 0), 1500.0)
tot = rc.W * rc.H
print("PLANO (PerfMode 1) cam z 120: suelo<15 m %.1f %% | suelo lejano %.1f %% | cielo %.1f %% | lanes/px cerca %.2f lejos %.2f | %.0f s"
      % (100 * r["px_near"] / tot, 100 * r["px_far"] / tot, 100 * r["px_sky"] / tot,
         r["lanes_near"] / max(r["px_near"], 1), r["lanes_far"] / max(r["px_far"], 1), time.time() - t0))
(OUT / "raster_flat.json").write_text(json.dumps(r, indent=1))
