# hud_entry_dsl.py - genera el DSL de BP_HUDArt_SC.PoseHUD(T): la ENTRADA DEL HUD por piezas (blender-3d/scripts/anim_hud.py,
# tabla en blender-3d/assets/hud.md), con los MISMOS tiempos. El borde (AppearBody) y el trazo (AppearTrace) los anima
# BPC_AppearLuz_SC con su coreografia generica (mismos tramos); aca van las piezas propias del HUD, leidas del mismo reloj
# (Appear.AppearT):
#   marco del EEG 0,40-0,62: se abre a lo largo desde el centro (escala X 0 -> 1, Y 0,15 -> 1)
#   lamina        0,48-0,74: se extiende desde el centro (escala X, ease in-out)
#   nidos         0,50-0,78: salen de las puntas del marco del EEG (x = 0,5935 * x_reposo, escala 0,25) y viajan a su lugar
#                            con clac (ease_out_back 1,1); CustomPrimitiveData[0] = x actual (lo lee el doblez del HUD)
#   destello del marco y los collares: 0,6 * seno(0,40..0,78) * (1 - S(0,70..0,80))
# Todo RELATIVO al reposo capturado en BeginPlay (RestBezel/RestGlass/RestNest/RestSeat).
# Uso: python hud_entry_dsl.py > poses.dsl  (GET = getter de componente propio; CPD = setter de custom primitive data)
import sys

GET = "(Variables|Default|Get%s)"
CPD = "Rendering|Material|SetCustomPrimitiveDataFloat"


def cl(x):
    return "(Math|Float|Clamp(Float) %s 0.0 1.0)" % x


def seg(v, a, b):
    return cl("(/ (- %s %s) %s)" % (v, a, round(b - a, 4)))


def S(x):
    return "(* %s (* %s (- 3.0 (* 2.0 %s))))" % (x, x, x)


def EOC(x):
    return "(- 1.0 (* (- 1.0 %s) (* (- 1.0 %s) (- 1.0 %s))))" % (x, x, x)


L = []
B = L.append
B("(fn PoseHUD (T)")
B(" (bind t %s)" % cl("T"))
# marco del EEG
B(" (bind u1 %s)" % seg("t", 0.40, 0.62))
B(" (bind k1 (Math|Float|Max(Float) %s 0.001))" % EOC("u1"))
B(" (bind v1 %s)" % seg("u1", 0.3, 1.0))
B(" (bind sy1 (+ 0.15 (* 0.85 %s)))" % EOC("v1"))
B(" (bind a2 (Math|Trig|Sin(Radians) (* 3.14159 %s)))" % seg("t", 0.40, 0.78))
B(" (bind fl (* (* 0.6 a2) (- 1.0 %s)))" % S(seg("t", 0.70, 0.80)))
B(" (bind bz %s)" % (GET % "Bezel"))
B(" (Rendering|SetVisibility bz (> u1 0.0))")
B(" (Transformation|SetRelativeTransform bz (Math|Transform|ComposeTransforms (Math|Transform|MakeTransform :Scale (Math|Vector|MakeVector k1 sy1 1.0)) (Variables|Default|GetRestBezel)))")
B(" (Rendering|Material|SetScalarParameterValueonMaterials bz \"Flash\" fl)")
# lamina
B(" (bind u2 %s)" % seg("t", 0.48, 0.74))
B(" (bind q2 (- 2.0 (* 2.0 u2)))")
B(" (bind e2 (Math|Float|Max(Float) (select (< u2 0.5) (* 4.0 (* u2 (* u2 u2))) (- 1.0 (* 0.5 (* q2 (* q2 q2))))) 0.001))")
B(" (bind gl %s)" % (GET % "Glass"))
B(" (Rendering|SetVisibility gl (> u2 0.0))")
B(" (Transformation|SetRelativeTransform gl (Math|Transform|ComposeTransforms (Math|Transform|MakeTransform :Scale (Math|Vector|MakeVector e2 1.0 1.0)) (Variables|Default|GetRestGlass)))")
# nidos
B(" (bind u3 %s)" % seg("t", 0.50, 0.78))
B(" (bind m3 (- u3 1.0))")
B(" (bind k3 (+ 1.0 (+ (* 2.1 (* m3 (* m3 m3))) (* 1.1 (* m3 m3)))))")
B(" (bind s3 (+ 0.25 (* 0.75 %s)))" % EOC("u3"))
for nm in ("Nest", "Seat"):
    lo = nm.lower()
    B(" (bind %s (Variables|Default|GetRest%s))" % (lo + "R", nm))
    B(" (bind %sX (.x (.location %sR)))" % (lo, lo))
    B(" (bind %sPos (- (* %sX (+ 0.5935 (* 0.4065 k3))) %sX))" % (lo, lo, lo))  # x actual - x reposo
    B(" (bind %sC %s)" % (lo, GET % nm))
    B(" (Rendering|SetVisibility %sC (> u3 0.0))" % lo)
    B(" (Transformation|SetRelativeTransform %sC (Math|Transform|ComposeTransforms (Math|Transform|ComposeTransforms (Math|Transform|MakeTransform :Scale (Math|Vector|MakeVector s3 s3 s3)) %sR) (Math|Transform|MakeTransform :Location (Math|Vector|MakeVector %sPos 0.0 0.0))))" % (lo, lo, lo))
    B(" (%s %sC 0 (+ %sX %sPos))" % (CPD, lo, lo, lo))
    B(" (Rendering|Material|SetScalarParameterValueonMaterials %sC \"Flash\" fl)" % lo)
L[-1] = L[-1] + ")"
print("\n".join(L))
