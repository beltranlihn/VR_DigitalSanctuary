# -*- coding: utf-8 -*-
"""gen_heart_dust_demo.py - SM_HeartDust_Demo_SC: el polvo del latido con MAS VOLUMEN, solo para la demo BDW (2026-10-21).

Pedido de Beltran (arreglo 1 de docs/demo/ARREGLOS-2026-10-21.md): "cuando se sube con la camara, el usuario se sale de
las particulas". La vuelta sube al espectador ~400 cm y lo aleja ~600 (local: de (-600, 0, 140) a ~(-1200, 0, 540)); el
nucleo de SM_HeartDust_SC llega a z 620 y el resto a 950, asi que arriba de la vuelta queda casi todo el polvo debajo.

Misma codificacion, mismo material (MI_HeartDust_SC), misma semilla: solo cambian las cantidades y el volumen.
  nucleo (80 %): r 350-1700, z 40-900   (antes r 400-1400, z 60-620)  -> ~86 % de la densidad de antes
  resto:         r 150-5000, z 10-2200  (antes r 150-2800, z 10-950)
  8900 motas = 35.600 vertices (antes 4400 = 17.600): 1 draw call, VS liviano. Sin medir en visor.
La Obra NO cambia: BP_DemoFlow_SC.HeartTick le pone esta malla al polvo al arrancar la demo.

Uso (headless):
  "C:\\Program Files\\Blender Foundation\\Blender 5.2\\blender.exe" --background --factory-startup --python gen_heart_dust_demo.py
Salida: VR_Test/Saved/ClaudeScripts/Heart/SM_HeartDust_Demo_SC.fbx (+ VERIF por reimportacion).
"""
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import gen_heart_dust as g  # noqa: E402

g.am.K.update(ND=7900, NS=1000, RIn=150.0, ROut=5000.0, RCoreIn=350.0, RCoreOut=1700.0,
              ZLo=10.0, ZHi=2200.0, ZCoreLo=40.0, ZCoreHi=900.0, CoreFrac=0.8)


def main():
    carpeta = os.path.abspath(os.path.join(AQUI, "..", "..", "..", "..", "VR_Test", "Saved", "ClaudeScripts", "Heart"))
    os.makedirs(carpeta, exist_ok=True)
    sd = g.am.seeds()
    enc = g.am.encode(sd)
    g.limpiar()
    ob = g.nube("SM_HeartDust_Demo_SC", enc)
    ruta = g.exportar(ob, carpeta)
    print("LISTO %s verts=%d polys=%d -> %s" % (ob.name, len(ob.data.vertices), len(ob.data.polygons), ruta))
    g.verificar(ruta, enc, sd)


if __name__ == "__main__":
    main()
