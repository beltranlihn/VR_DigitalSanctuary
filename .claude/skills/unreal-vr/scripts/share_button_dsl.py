# share_button_dsl.py - genera el DSL de BP_ShareButton_SC (los botones SHARE / DON'T SHARE del cuadro de resultados;
# blender-3d/assets/share-button.md). API pedida por Narrativa (2026-09-30):
#   funciones Appear() · Vanish() · SetHover(On) · Press() ; dispatcher OnConfirmed ; perilla bDontShare ;
#   reloj AppearLuz.AppearT. SIN Tick cuando esta quieto (el actor y su AppearLuz se duermen solos).
# La placa la mueve SOLO PoseButton (no lleva el tag AppearMover): asoma con los tiempos del AppearMover del SAVE
# (0,52-0,80, ease_out_back 1,2) y le suma hover (+1 mm) y apretado (-4 mm). El cuerpo (AppearBody) y el trazo
# (AppearTrace) los anima BPC_AppearLuz_SC. Ejes del actor: cara +X, arriba +Z.
# Estados (los del SAVE MELODY): reposo Glow 0,7 · hover +1 mm, Glow 1,0, texto de luz calida · confirmacion
# -4 mm, Glow 1,4, la luz da la vuelta al perimetro (Progress 0->1 en 0,45 s) -> OnConfirmed -> Vanish.
# Uso: python share_button_dsl.py <Grafo> [id_de_SetComponentTickEnabled]
import sys

G = "(Variables|Default|Get%s)"
COMP_TICK = sys.argv[2] if len(sys.argv) > 2 else "Components|Tick|SetComponentTickEnabled"
DT = "(Math|Float|Min(Float) DeltaSeconds 0.0333)"


def cl(x):
    return "(Math|Float|Clamp(Float) %s 0.0 1.0)" % x


def seg(v, a, b):
    return cl("(/ (- %s %s) %s)" % (v, a, round(b - a, 4)))


def S(x):
    return "(* %s (* %s (- 3.0 (* 2.0 %s))))" % (x, x, x)


def appear_t():
    return "(Class|BPCAppearLuzSC|GetAppearT %s)" % (G % "AppearLuz")


GRAPHS = {}

GRAPHS["ConstructionScript"] = """(fn ConstructionScript ()
  (CallFunction|SetupButton))
"""

GRAPHS["SetupButton"] = """(fn SetupButton ()
  (Rendering|Material|SetMaterial (Variables|Default|GetPlate) 1 (select (Variables|Default|GetbDontShare) (Variables|Default|GetTopDontShare) (Variables|Default|GetTopShare)))
  (Collision|SetCollisionEnabled (Variables|Default|GetBase) "NoCollision")
  (Collision|SetCollisionEnabled (Variables|Default|GetPlate) "NoCollision")
  (Collision|SetCollisionEnabled (Variables|Default|GetSlider) "NoCollision")
  (Collision|SetCollisionEnabled (Variables|Default|GetTrace) "NoCollision")
  (Collision|SetCollisionEnabled (Variables|Default|GetHit) "QueryOnly")
  (Collision|SetCollisionObjectType (Variables|Default|GetHit) "ECC_Destructible")
  (Collision|SetCollisionResponsetoAllChannels (Variables|Default|GetHit) "ECR_Ignore"))
"""


def pose_button():
    L = ["(fn PoseButton (T)",
         " (bind t %s)" % cl("T"),
         " (bind um %s)" % seg("t", 0.52, 0.80),
         " (bind m (- um 1.0))",
         " (bind km (+ 1.0 (+ (* 2.2 (* m (* m m))) (* 1.2 (* m m)))))",
         " (bind p %s)" % (G % "PressK"),
         " (bind q (- 1.0 p))",
         " (bind pe (- 1.0 (* q (* q q))))",
         " (bind ps %s)" % S("p"),
         " (bind r (- 2.0 (* 2.0 p)))",
         " (bind pio (select (< p 0.5) (* 4.0 (* p (* p p))) (- 1.0 (* 0.5 (* r (* r r))))))",
         " (bind h %s)" % (G % "HoverK"),
         " (bind hs %s)" % S("h"),
         " (bind dx (+ (* -1.2 (- 1.0 km)) (- (* 0.1 (* hs q)) (* 0.4 pe))))",
         " (bind pl %s)" % (G % "Plate"),
         " (Rendering|SetVisibility pl (> um 0.0))",
         " (Transformation|SetRelativeTransform pl (Math|Transform|ComposeTransforms %s (Math|Transform|MakeTransform :Location (Math|Vector|MakeVector dx 0.0 0.0))))" % (G % "PlateRest"),
         " (Rendering|Material|SetScalarParameterValueonMaterials pl \"Flash\" (* 0.35 (- 1.0 %s)))" % S("um"),
         " (bind lit (Math|Float|Max(Float) hs ps))",
         " (Rendering|Material|SetScalarParameterValueonMaterials %s \"Glow\" (+ 0.7 (+ (* 0.3 hs) (* 0.7 ps))))" % (G % "Base"),
         " (Rendering|Material|SetScalarParameterValueonMaterials pl \"InkGlow\" (+ 0.35 (* 0.85 lit)))",
         " (Rendering|Material|SetVectorParameterValueonMaterials pl \"Ink\" (Math|Vector|MakeVector (+ 0.93 (* 0.32 lit)) (- 0.91 (* 0.01 lit)) (- 0.87 (* 0.3075 lit))))",
         " (Rendering|Material|SetScalarParameterValueonMaterials %s \"Progress\" pio))" % (G % "Slider")]
    return "\n".join(L) + "\n"


GRAPHS["PoseButton"] = pose_button()

GRAPHS["StepHover"] = """(fn StepHover (Dt)
  (if (!= (Variables|Default|GetHoverK) (Variables|Default|GetHoverTarget))
    (Variables|Default|SetHoverK (Math|Float|Clamp(Float) (+ (Variables|Default|GetHoverK) (select (> (Variables|Default|GetHoverTarget) (Variables|Default|GetHoverK)) (/ Dt 0.12) (/ Dt -0.18))) 0.0 1.0))))
"""

GRAPHS["StepPress"] = """(fn StepPress (Dt)
  (if (and (Variables|Default|GetPressed) (not (Variables|Default|GetConfirmed)))
    (Variables|Default|SetPressK (Math|Float|Clamp(Float) (+ (Variables|Default|GetPressK) (/ Dt 0.45)) 0.0 1.0))
    (if (>= (Variables|Default|GetPressK) 1.0)
      (Variables|Default|SetConfirmed true)
      (Default|CallOnConfirmed)
      (CallFunction|Vanish))))
"""

GRAPHS["StepWait"] = """(fn StepWait (Dt)
  (if (Variables|Default|GetWaiting)
    (Variables|Default|SetWaitLeft (- (Variables|Default|GetWaitLeft) Dt))
    (if (<= (Variables|Default|GetWaitLeft) 0.0)
      (Variables|Default|SetWaiting false)
      (CallFunction|Appear))))
"""

GRAPHS["IdleCheck"] = """(fn IdleCheck ()
  (if (and (== (Variables|Default|GetHoverK) (Variables|Default|GetHoverTarget)) (and (not (Variables|Default|GetWaiting)) (and (or (not (Variables|Default|GetPressed)) (Variables|Default|GetConfirmed)) (not (Class|BPCAppearLuzSC|GetPlaying (Variables|Default|GetAppearLuz))))))
    (CallFunction|SleepTicks)))
"""

GRAPHS["WakeTicks"] = """(fn WakeTicks ()
  (Actor|Tick|SetActorTickEnabled self true)
  (%s (Variables|Default|GetAppearLuz) true))
""" % COMP_TICK

GRAPHS["SleepTicks"] = """(fn SleepTicks ()
  (Actor|Tick|SetActorTickEnabled self false)
  (%s (Variables|Default|GetAppearLuz) false))
""" % COMP_TICK

GRAPHS["Appear"] = """(fn Appear ()
  (Variables|Default|SetWaiting false)
  (Variables|Default|SetConfirmed false)
  (Variables|Default|SetPressed false)
  (Variables|Default|SetPressK 0.0)
  (Variables|Default|SetHoverTarget 0.0)
  (Variables|Default|SetHoverK 0.0)
  (CallFunction|WakeTicks)
  (Class|BPCAppearLuzSC|Appear (Variables|Default|GetAppearLuz)))
"""

GRAPHS["Vanish"] = """(fn Vanish ()
  (Variables|Default|SetWaiting false)
  (Variables|Default|SetHoverTarget 0.0)
  (CallFunction|WakeTicks)
  (Class|BPCAppearLuzSC|Vanish (Variables|Default|GetAppearLuz)))
"""

GRAPHS["SetHover"] = """(fn SetHover (On)
  (if (and (!= On (> (Variables|Default|GetHoverTarget) 0.5)) (and (not (Variables|Default|GetPressed)) (>= %s 0.999)))
    (Variables|Default|SetHoverTarget (select On 1.0 0.0))
    (CallFunction|WakeTicks)
    (if On
      (Audio|PlaySoundatLocation (Variables|Default|GetHoverSound) (Transformation|GetActorLocation self)))))
""" % appear_t()

GRAPHS["Press"] = """(fn Press ()
  (if (and (not (Variables|Default|GetPressed)) (>= %s 0.999))
    (Variables|Default|SetPressed true)
    (CallFunction|WakeTicks)
    (Audio|PlaySoundatLocation (Variables|Default|GetPressSound) (Transformation|GetActorLocation self))))
""" % appear_t()

GRAPHS["EventGraph"] = """(event EventBeginPlay
  (CallFunction|SetupButton)
  (Variables|Default|SetPlateRest (Transformation|GetRelativeTransform (Variables|Default|GetPlate)))
  (Class|BPCAppearLuzSC|Prepare (Variables|Default|GetAppearLuz))
  (CallFunction|PoseButton :T 0.0)
  (if (Variables|Default|GetAppearonPlay)
    (Variables|Default|SetWaitLeft (Variables|Default|GetAppearDelay))
    (Variables|Default|SetWaiting true)
    (else
      (CallFunction|SleepTicks))))
(event EventTick (DeltaSeconds)
  (CallFunction|StepWait :Dt %s)
  (CallFunction|StepHover :Dt %s)
  (CallFunction|StepPress :Dt %s)
  (CallFunction|PoseButton :T %s)
  (CallFunction|IdleCheck))
""" % (DT, DT, DT, appear_t())

if __name__ == "__main__":
    print(GRAPHS[sys.argv[1]], end="")
