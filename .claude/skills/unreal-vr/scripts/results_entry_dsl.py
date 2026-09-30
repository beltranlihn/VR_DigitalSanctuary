# results_entry_dsl.py - genera el DSL de BP_ResultsArt_SC (el CUADRO DE RESULTADOS, blender-3d/assets/results.md):
#   PoseResults(T)  la entrada por piezas con los MISMOS tiempos que blender-3d/scripts/render_results.py:
#     lamina    0,42-0,66  se abre desde el centro hacia arriba y abajo (escala Z 0 -> 1, ease in-out cubica)
#     ventanas  en cascada de arriba abajo, 0,22 cada una: calma 0,48 · latido 0,54 · respiracion 0,60 · melodia 0,66;
#               a lo ancho desde el centro (escala Y, ease out cubica), el alto de 0,15 a 1 (desde el 30 % de su tramo),
#               destello 0,6 * seno(pi u) en su contorno
#     cajita    solo con el panel entero (t 0,80-0,95) y abierta por TipK (0..1, lo mueve TickTip): igual que una ventana
#     K*        0..1 para que Narrativa funda SUS contenidos: KTitle (0,56-0,80), KCalm/KHeart/KBreath/KMelody (desde el
#               fin de su ventana - 0,06, durante 0,14), KTip (= la apertura de la cajita)
#   SetupCollision (el laser: ventanas QueryOnly + Destructible + Ignore; el resto sin colision) ·
#   TickWait(Dt) · TickTip(Dt) · EventGraph (BeginPlay, Tick con Dt = min(DeltaSeconds, 1/30), ResultsAppear,
#   ResultsVanish, ResultsHideNow, TipShow, TipHide)
# El marco (AppearBody) y el trazo (AppearTrace) los anima BPC_AppearLuz_SC. Ejes del actor: cara +X, arriba +Z, ancho Y.
# Uso: python results_entry_dsl.py <PoseResults|TickWait|TickTip|EventGraph>
import sys

G = "(Variables|Default|Get%s)"
SETV = "(Variables|Default|Set%s %s)"
WINS = [("WinCalm", "Calm", 0.48, 0.70), ("WinHeart", "Heart", 0.54, 0.76), ("WinBreath", "Breath", 0.60, 0.82),
        ("WinMelody", "Melody", 0.66, 0.88)]
TIP_OPEN_S = 0.35
DT_MAX = 0.0333


def cl(x):
    return "(Math|Float|Clamp(Float) %s 0.0 1.0)" % x


def seg(v, a, b):
    return cl("(/ (- %s %s) %s)" % (v, a, round(b - a, 4)))


def S(x):
    return "(* %s (* %s (- 3.0 (* 2.0 %s))))" % (x, x, x)


def EOC(x):
    return "(- 1.0 (* (- 1.0 %s) (* (- 1.0 %s) (- 1.0 %s))))" % (x, x, x)


def scale_pose(comp, rest, sx, sy, sz):
    return (" (Transformation|SetRelativeTransform %s (Math|Transform|ComposeTransforms (Math|Transform|MakeTransform "
            ":Scale (Math|Vector|MakeVector %s %s %s)) %s))" % (comp, sx, sy, sz, G % rest))


def pose_results():
    L = []
    B = L.append
    B("(fn PoseResults (T)")
    B(" (bind t %s)" % cl("T"))
    # lamina
    B(" (bind u0 %s)" % seg("t", 0.42, 0.66))
    B(" (bind q0 (- 2.0 (* 2.0 u0)))")
    B(" (bind e0 (Math|Float|Max(Float) (select (< u0 0.5) (* 4.0 (* u0 (* u0 u0))) (- 1.0 (* 0.5 (* q0 (* q0 q0))))) 0.001))")
    B(" (bind gl %s)" % (G % "Glass"))
    B(" (Rendering|SetVisibility gl (> u0 0.0))")
    B(scale_pose("gl", "RestGlass", "1.0", "1.0", "e0"))
    # ventanas en cascada
    for comp, key, a, b in WINS:
        u, k, s, c = "u" + key, "k" + key, "s" + key, "c" + key
        B(" (bind %s %s)" % (u, seg("t", a, b)))
        B(" (bind %s (Math|Float|Max(Float) %s 0.001))" % (k, EOC(u)))
        B(" (bind %s (+ 0.15 (* 0.85 %s)))" % (s, EOC(seg(u, 0.3, 1.0))))
        B(" (bind %s %s)" % (c, G % comp))
        B(" (Rendering|SetVisibility %s (> %s 0.0))" % (c, u))
        B(scale_pose(c, "Rest" + comp, "1.0", k, s))
        B(" (Rendering|Material|SetScalarParameterValueonMaterials %s \"Flash\" (* 0.6 (Math|Trig|Sin(Radians) (* 3.14159 %s))))" % (c, u))
        B(" " + SETV % ("K" + key, S(seg("t", round(b - 0.06, 2), round(b + 0.08, 2)))))
    B(" " + SETV % ("KTitle", S(seg("t", 0.56, 0.80))))
    # la cajita: solo con el panel entero, abierta por TipK
    B(" (bind kt (* %s %s))" % (G % "TipK", S(seg("t", 0.80, 0.95))))
    B(" (bind et (Math|Float|Max(Float) %s 0.001))" % EOC("kt"))
    B(" (bind st (+ 0.15 (* 0.85 %s)))" % EOC(seg("kt", 0.3, 1.0)))
    B(" (bind tp %s)" % (G % "Tip"))
    B(" (Rendering|SetVisibility tp (> kt 0.0))")
    B(scale_pose("tp", "RestTip", "1.0", "et", "st"))
    B(" (Rendering|Material|SetScalarParameterValueonMaterials tp \"Flash\" (* 0.5 (Math|Trig|Sin(Radians) (* 3.14159 kt))))")
    B(" " + SETV % ("KTip", "kt") + ")")
    return "\n".join(L) + "\n"


def tick_wait():
    return ("(fn TickWait (Dt)\n"
            "  (if (Variables|Default|GetWaiting)\n"
            "    (Variables|Default|SetWaitLeft (- (Variables|Default|GetWaitLeft) Dt))\n"
            "    (if (<= (Variables|Default|GetWaitLeft) 0.0)\n"
            "      (Variables|Default|SetWaiting false)\n"
            "      (Class|BPCAppearLuzSC|Appear (Variables|Default|GetAppear)))))\n")


def tick_tip():
    # TipK va hacia TipTarget (0 o 1) en TIP_OPEN_S segundos; el clamp absorbe el ultimo paso
    return ("(fn TickTip (Dt)\n"
            "  (if (!= (Variables|Default|GetTipK) (Variables|Default|GetTipTarget))\n"
            "    (Variables|Default|SetTipK (Math|Float|Clamp(Float) (+ (Variables|Default|GetTipK) "
            "(select (> (Variables|Default|GetTipTarget) (Variables|Default|GetTipK)) (/ Dt %s) (/ Dt -%s))) 0.0 1.0))))\n"
            % (TIP_OPEN_S, TIP_OPEN_S))


def event_graph():
    rest = "".join("  (Variables|Default|SetRest%s (Transformation|GetRelativeTransform (Variables|Default|Get%s)))\n" % (c, c)
                   for c in ["Glass", "WinCalm", "WinHeart", "WinBreath", "WinMelody", "Tip"])
    dt = "(Math|Float|Min(Float) DeltaSeconds %s)" % DT_MAX
    return ("(event EventBeginPlay\n  (CallFunction|SetupCollision)\n" + rest +
            "  (if (Variables|Default|GetAppearonPlay)\n"
            "    (Class|BPCAppearLuzSC|Prepare (Variables|Default|GetAppear))\n"
            "    (CallFunction|PoseResults :T 0.0)\n"
            "    (Variables|Default|SetLastT 0.0)\n"
            "    (Variables|Default|SetWaitLeft (Variables|Default|GetAppearDelay))\n"
            "    (Variables|Default|SetWaiting true)))\n"
            "(event EventTick (DeltaSeconds)\n"
            "  (CallFunction|TickWait :Dt %s)\n"
            "  (CallFunction|TickTip :Dt %s)\n"
            "  (bind at (Class|BPCAppearLuzSC|GetAppearT (Variables|Default|GetAppear)))\n"
            "  (if (or (!= at (Variables|Default|GetLastT)) (!= (Variables|Default|GetTipK) (Variables|Default|GetLastTipK)))\n"
            "    (CallFunction|PoseResults :T at)\n"
            "    (Variables|Default|SetLastT at)\n"
            "    (Variables|Default|SetLastTipK (Variables|Default|GetTipK))))\n"
            "(event Custom|ResultsAppear\n"
            "  (Variables|Default|SetWaiting false)\n"
            "  (Class|BPCAppearLuzSC|Appear (Variables|Default|GetAppear)))\n"
            "(event Custom|ResultsVanish\n"
            "  (Variables|Default|SetWaiting false)\n"
            "  (Variables|Default|SetTipTarget 0.0)\n"
            "  (Class|BPCAppearLuzSC|Vanish (Variables|Default|GetAppear)))\n"
            "(event Custom|ResultsHideNow\n"
            "  (Variables|Default|SetWaiting false)\n"
            "  (Variables|Default|SetTipTarget 0.0)\n"
            "  (Variables|Default|SetTipK 0.0)\n"
            "  (Class|BPCAppearLuzSC|Prepare (Variables|Default|GetAppear))\n"
            "  (CallFunction|PoseResults :T 0.0)\n"
            "  (Variables|Default|SetLastT 0.0))\n"
            "(event Custom|TipShow\n"
            "  (Variables|Default|SetTipTarget 1.0))\n"
            "(event Custom|TipHide\n"
            "  (Variables|Default|SetTipTarget 0.0))\n") % (dt, dt)


def setup_collision():
    """El laser del cuadro (rig de Secuencer: LineTraceForObjects, Object Type Destructible; pedido de Narrativa): las 4
    VENTANAS QueryOnly + Destructible + todas las respuestas en Ignore; el resto sin colision. En BeginPlay (gotcha 353:
    el BodyInstance serializado de una instancia le gana al del Blueprint). Las mallas de ventana llevan un casco
    convexo simple (el trazo por objetos no es complejo)."""
    L = ["(fn SetupCollision ()"]
    for c in ("Glass", "Rim", "Tip", "Trace"):
        L.append("  (Collision|SetCollisionEnabled (Variables|Default|Get%s) \"NoCollision\")" % c)
    for c in ("WinCalm", "WinHeart", "WinBreath", "WinMelody"):
        L.append("  (Collision|SetCollisionEnabled (Variables|Default|Get%s) \"QueryOnly\")" % c)
        L.append("  (Collision|SetCollisionObjectType (Variables|Default|Get%s) \"ECC_Destructible\")" % c)
        L.append("  (Collision|SetCollisionResponsetoAllChannels (Variables|Default|Get%s) \"ECR_Ignore\")" % c)
    L[-1] += ")"
    return "\n".join(L) + "\n"


# BPC_AppearLuz_SC.Prepare v2 (2026-09-30): solo recaptura el reposo si NUNCA capturo o si esta EN REPOSO. La v1
# capturaba siempre: un segundo Prepare con la pieza oculta tomaba la pose de rendija como reposo y el marco no volvia
# a aparecer (HUD: BeginPlay con AppearOnPlay + HUDHideNow del BP de Narrativa).
PREPARE_V2 = ("(fn Prepare ()\n"
              "  (Variables|Default|SetPlaying false)\n"
              "  (Variables|Default|SetDir 1.0)\n"
              "  (if (or (== (Utilities|Array|Length (Variables|Default|GetBodies)) 0) (>= (Variables|Default|GetAppearT) 0.999))\n"
              "    (CallFunction|Capture)\n"
              "    (Variables|Default|SetAppearT 0.0)\n"
              "    (CallFunction|ApplyT :Tin 0.0)\n"
              "    (else\n"
              "      (CallFunction|CaptureEye)\n"
              "      (Variables|Default|SetAppearT 0.0)\n"
              "      (CallFunction|ApplyT :Tin 0.0))))\n")

if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "PoseResults"
    print({"PoseResults": pose_results, "TickWait": tick_wait, "TickTip": tick_tip, "EventGraph": event_graph,
           "SetupCollision": setup_collision, "Prepare": lambda: PREPARE_V2}[which](), end="")
