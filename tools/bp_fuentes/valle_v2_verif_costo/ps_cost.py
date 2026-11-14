# ps_cost.py - costo de PIXELES del valle: lanes del rasterizador (raster_cost.json) x op-eq por camino (cost_ops.json)
# convertido a ms con la calibracion MEDIDA del simplex (calib_simplex.json: op-eq por reloj). A 456 MHz.
# Dos ordenes de dibujo: cielo DESPUES del suelo (early-Z tapa el cielo) y cielo ANTES (todo el cuadro paga el cielo).
import json
from pathlib import Path
import cost_ops as co

OUT = Path(__file__).resolve().parent
ops = {r["camino"]: r for r in json.loads((OUT / "cost_ops.json").read_text())}
cal = json.loads((OUT / "calib_simplex.json").read_text())
thetas = sorted(cal["theta"].values())          # op-eq por reloj (rango)
cases = json.loads((OUT / "raster_cost.json").read_text())

# camino v1 "suelo cercano" (Dist <= FogStart: calcula la niebla pero no el cielo)
p1 = co.HL1 / "ValleyPS.hlsl"
ins, body = co.parse(p1)
b = co.specialize(body, co.P2 + [(co.FOG1, "if (true)\n{\n  fog"), (co.SKY, "if (false)"), (co.PART, "if (false)\n{\n  float cosA"), (co.MOON, "if (false)")])
s, a, _ = co.compile_count(co.wrapper(ins, b, "ps", "float3"), "ps", "v1_ps_cercano")
v1near = {"sfu": sum(s.values()), "alu": a}
print("v1 PS suelo cercano: SFU %d ALU %d" % (v1near["sfu"], a))


def oe(r, k):
    return r["alu"] + k * r["sfu"]


PATHS = {"v2": (ops["v2 PS suelo cercano"], ops["v2 PS suelo lejano"], ops["v2 PS cielo"]),
         "v1": (v1near, ops["v1 PS suelo (con niebla)"], ops["v1 PS cielo"])}
rows = []
for c in cases:
    near, far, sky = PATHS[c["version"]]
    for k in (1, 4):
        eye_after = c["lanes_near"] * oe(near, k) + c["lanes_far"] * oe(far, k) + c["lanes_sky_despues"] * oe(sky, k)
        eye_before = c["lanes_near"] * oe(near, k) + c["lanes_far"] * oe(far, k) + c["lanes_sky_antes"] * oe(sky, k)
        ideal = c["px_near"] * oe(near, k) + c["px_far"] * oe(far, k) + c["px_sky"] * oe(sky, k)
        fr = 2.0  # dos ojos
        ms = lambda ops_eye: [fr * ops_eye / (t * 456e6) * 1e3 for t in thetas]
        rows.append(dict(version=c["version"], cam_z=c["cam_z"], yaw=c["yaw"], pitch=c["pitch"], k=k,
                         ms_cielo_despues=ms(eye_after), ms_cielo_antes=ms(eye_before), ms_ideal_sin_cuadrantes=ms(ideal),
                         op_eq_por_px_despues=eye_after / (2064 * 2208), op_eq_por_px_antes=eye_before / (2064 * 2208)))
        print("%s z%.0f yaw%3d pitch%3d k=%d | op-eq/px: %.0f (cielo despues) %.0f (cielo antes) | ms a 456 MHz: "
              "%.2f-%.2f (despues) / %.2f-%.2f (antes) / ideal sin cuadrantes %.2f-%.2f"
              % (c["version"], c["cam_z"], c["yaw"], c["pitch"], k, eye_after / (2064 * 2208), eye_before / (2064 * 2208),
                 min(ms(eye_after)), max(ms(eye_after)), min(ms(eye_before)), max(ms(eye_before)), min(ms(ideal)), max(ms(ideal))))
(OUT / "ps_cost.json").write_text(json.dumps(rows, indent=1), encoding="utf-8")
