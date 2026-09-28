# -*- coding: utf-8 -*-
"""tb_tour_sim.py - EJECUTA tb_tour.dsl (contrato TOUR de BP_TBDirector_NC) con el interprete de dsl_sim.py y el resto del
director como STUBS con el comportamiento leido de sus grafos (CheckController/DoInstall/InstallInput/RemoveDrawIMC/
MountHands/InstallTip/TB_ReleaseFrom/ChargeStop/HandsStep). Un stub que se llama en un estado imposible (herramienta sin
armar, audio None) registra un "Accessed None", como en Unreal.

Escenarios: A sin TOUR = igual que hoy · B con TOUR: dormido, despertar, dormir dibujando, despertar de nuevo,
idempotencia de las dos · C sistema cerrado (bSystemDone): despertar no muestra nada · D bHidePawnHands false: dormir no
toca las manos del pawn · E bForceTour sin actor TOUR.
Uso:  python tb_tour_sim.py
"""
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import dsl_sim as ds  # noqa: E402

DSL = os.path.join(AQUI, "tb_tour.dsl")
fallas = []


def chk(lbl, ok, info=""):
    print(("OK    " if ok else "FALLA ") + lbl + ("  " + info if info else ""))
    if not ok:
        fallas.append(lbl)


class O:
    def __init__(self, name, **k):
        self.name = name
        self.visible = True
        self.hidden = False
        self.tick = True
        self.__dict__.update(k)


class TourBP(ds.BP):
    """dsl_sim + 'for' + 'self'."""

    def stmt(self, s, env):
        if s[0] == "for":
            var, coll, body = s[1], self.ev(s[2], env), s[3:]
            for x in coll:
                e2 = dict(env)
                e2[var] = x
                self.block(body, e2)
            return
        return super().stmt(s, env)

    def ev(self, e, env):
        if e == "self":
            return self.actor
        return super().ev(e, env)


W = {}   # el mundo de la prueba


def natives():
    n = ds._n
    n("Actor|GetAllActorswithTag")(lambda bp, tag: [a for a in W["actors"] if tag in a.tags])
    n("Utilities|Array|Length")(lambda bp, a: len(a))
    n("Game|GetPlayerController")(lambda bp, i: W["pc"])
    n("Game|GetPlayerPawn")(lambda bp, i: W["pawn"])
    n("Actor|GetComponentsByClass")(lambda bp, a, cls: list(a.skel))
    n("Utilities|Casting|CastToSkeletalMeshComponent")(lambda bp, x: x)

    def setvis(bp, c, v, prop=False):
        if c is None:
            bp.log.append("Accessed None: SetVisibility")
            return
        c.visible = bool(v)
    n("Rendering|SetVisibility")(setvis)

    def hid(bp, a, h):
        a.hidden = bool(h)
    n("Rendering|SetActorHiddenInGame")(hid)

    def atick(bp, a, on):
        a.tick = bool(on)
    n("Actor|Tick|SetActorTickEnabled")(atick)
    n("Components|Tick|SetComponentTickEnabled")(atick)
    n("Game|Feedback|SetHapticsByValue")(lambda bp, pc, f, a, hand="Left": W["haptic"].__setitem__(hand, a))

    def dis(bp, a, pc):
        W["input"] = False
    n("Input|DisableInput")(dis)



def stubs():
    def install(bp):
        W["n_install"] += 1
        bp.v["bReady"] = True
        bp.run_fn("InstallInput")
        W["palette"] = O("Palette")
        bp.v["Palette"] = W["palette"]
        bp.run_fn("MountHands")
        bp.run_fn("InstallTip")
        bp.run_fn("ApplyHands")

    def check(bp):
        if not bp.v["bReady"] and W["controllers"]:
            install(bp)

    def inst_input(bp):
        W["n_input"] += 1
        W["input"] = True
        W["imc"] = True

    def rm_imc(bp):
        W["imc"] = False

    def mount(bp):
        if not bp.v["bReady"]:
            bp.log.append("MountHands sin instalar")
        bp.comps["SMRHand"].visible = True

    def tip(bp):
        bp.comps["SMTip"].visible = True

    def release(bp, FromLeft):
        if not bp.v["bReady"]:
            bp.log.append("Accessed None: TB_ReleaseFrom sin herramienta")
        W["tool"].drawing = False

    def apply_hands(bp):                   # AddDrawIMC + FixHands + MirrorPalette (leidos 2026-09-29)
        W["imc"] = True
        dom, other = ("SMLHand", "SMRHand") if bp.v["bLeftHanded"] else ("SMRHand", "SMLHand")
        bp.comps[other].visible = False
        bp.comps[dom].visible = True

    def loop_stop(bp):
        if bp.v["LoopComp"] is not None:
            bp.v["LoopComp"].playing = False
            bp.v["LoopComp"] = None

    def charge_stop(bp):
        if bp.v["ChargeComp"] is not None:        # ChargeStop trae su IsValid
            bp.v["ChargeComp"].playing = False
    return {"CheckController": check, "InstallInput": inst_input, "RemoveDrawIMC": rm_imc, "MountHands": mount,
            "InstallTip": tip, "TBReleaseFrom": release, "ChargeStop": charge_stop, "ApplyHands": apply_hands,
            "LoopStop": loop_stop}


def mundo(tour=False, force=False, hide_hands=True, pawn_hands_visible=True):
    W.clear()
    tbl = O("DrawTable")
    W.update(actors=[O("Tour", tags=["TOUR"])] if tour else [O("Algo", tags=[])], pc=O("PC"),
             pawn=O("Pawn", skel=[O("HandL", visible=pawn_hands_visible), O("HandR", visible=pawn_hands_visible)]),
             controllers=True, n_install=0, n_input=0, input=False, imc=False, haptic={"Left": 0.0, "Right": 0.0},
             tool=O("TBTool", drawing=False), palette=None, table=tbl)
    director = O("Director")
    v = {"bTourMode": False, "bAwake": False, "bForceTour": force, "bReady": False, "bSystemDone": False,
         "bHidePawnHands": hide_hands, "bLeftHanded": False, "bCharging": False, "ChargeComp": None, "LoopComp": None,
         "Palette": None, "DrawTable": tbl}
    comps = {"SMRHand": O("SMRHand", visible=False), "SMLHand": O("SMLHand", visible=False),
             "SMTip": O("SMTip", visible=False), "TBTool": W["tool"]}
    bp = TourBP(open(DSL, encoding="utf-8").read(), v, comps, extern=stubs())
    bp.actor = director
    return bp


def begin_play(bp):
    bp.run_fn("TourBegin")          # la cirugia: EventBeginPlay -> TourBegin (antes: CheckController)


def tick(bp, n=3):
    """El Tick de hoy: DirectorStep (con HandsStep) + CheckController. Solo si el actor tickea."""
    for _ in range(n):
        if not bp.actor.tick:
            return
        for h in W["pawn"].skel:                               # HandsStep
            h.visible = h.visible and not bp.v["bHidePawnHands"]
        bp.extern["CheckController"](bp)


def estado(bp):
    return dict(awake=bp.v["bAwake"], tick=bp.actor.tick, tooltick=W["tool"].tick, input=W["input"], imc=W["imc"],
                ready=bp.v["bReady"], installs=W["n_install"], hands=[h.visible for h in W["pawn"].skel],
                rhand=bp.comps["SMRHand"].visible, tip=bp.comps["SMTip"].visible,
                pal=(None if W["palette"] is None else (not W["palette"].hidden, W["palette"].tick)),
                table=not W["table"].hidden)


def main():
    natives()
    # A. sin TOUR: igual que hoy
    bp = mundo(tour=False)
    begin_play(bp)
    tick(bp)
    e = estado(bp)
    chk("A sin TOUR: despierto, tick, instalado una vez, input+IMC, manos del pawn ocultas, paleta y mesa visibles",
        e["awake"] and e["tick"] and e["installs"] == 1 and e["input"] and e["imc"] and e["hands"] == [False, False]
        and e["pal"] == (True, True) and e["table"] and e["rhand"] and e["tip"], str(e))
    chk("A sin TOUR: log limpio", not bp.log, str(bp.log))
    # B. con TOUR
    bp = mundo(tour=True)
    begin_play(bp)
    tick(bp)
    e = estado(bp)
    chk("B TOUR al empezar: dormido, sin tick (actor y herramienta), sin instalar, sin input ni IMC, manos del pawn intactas",
        not e["awake"] and not e["tick"] and not e["tooltick"] and e["installs"] == 0 and not e["input"] and not e["imc"]
        and e["hands"] == [True, True] and not e["rhand"] and not e["tip"] and not e["table"], str(e))
    chk("B TOUR al empezar: log limpio (nada de Accessed None)", not bp.log, str(bp.log))
    bp.run_fn("TourSleep")
    chk("B TourSleep dormido = no hace nada", estado(bp) == e and not bp.log)
    bp.run_fn("TourWake")
    tick(bp)
    e = estado(bp)
    chk("B TourWake: instala como hoy (1 vez), tick, input+IMC, oculta las manos, paleta/mesa/punta visibles",
        e["awake"] and e["tick"] and e["tooltick"] and e["installs"] == 1 and e["input"] and e["imc"]
        and e["hands"] == [False, False] and e["pal"] == (True, True) and e["table"] and e["tip"], str(e))
    bp.run_fn("TourWake")
    tick(bp)
    chk("B TourWake dos veces = una (idempotente)", estado(bp) == e and W["n_input"] == 1, "inputs %d" % W["n_input"])
    # dormir en medio de un trazo, con la carga del Guardar y el loop sonando y vibrando
    W["tool"].drawing = True
    bp.v["ChargeComp"] = O("Charge", playing=True)
    bp.v["LoopComp"] = O("Loop", playing=True)
    bp.v["bCharging"] = True
    W["haptic"].update(Left=0.4, Right=0.4)
    loop = bp.v["LoopComp"]
    bp.run_fn("TourSleep")
    tick(bp)
    e = estado(bp)
    chk("B TourSleep dibujando: suelta el trazo, corta carga, loop y haptica",
        not W["tool"].drawing and not bp.v["ChargeComp"].playing and not loop.playing
        and not bp.v["bCharging"] and W["haptic"] == {"Left": 0.0, "Right": 0.0})
    chk("B TourSleep: sin input ni IMC, manos DEVUELTAS, paleta oculta y sin tick, mesa/mando/punta ocultos, sin tick",
        not e["awake"] and not e["tick"] and not e["tooltick"] and not e["input"] and not e["imc"]
        and e["hands"] == [True, True] and e["pal"] == (False, False) and not e["table"] and not e["rhand"] and not e["tip"], str(e))
    bp.run_fn("TourSleep")
    chk("B TourSleep dos veces = una (idempotente)", estado(bp) == e)
    bp.run_fn("TourWake")
    tick(bp)
    e = estado(bp)
    chk("B TourWake despues de dormir: reinstala SOLO el input (no DoInstall), vuelve a mostrar y a ocultar las manos",
        e["awake"] and e["installs"] == 1 and W["n_input"] == 2 and e["input"] and e["imc"] and e["hands"] == [False, False]
        and e["pal"] == (True, True) and e["table"] and e["rhand"] and e["tip"], str(e))
    chk("B log limpio en todo el recorrido", not bp.log, str(bp.log))
    # C. sistema cerrado (despues de Guardar): despertar no muestra nada nuevo (5r)
    bp.v["bSystemDone"] = True
    bp.run_fn("TourSleep")
    bp.run_fn("TourWake")
    e = estado(bp)
    chk("C con el sistema cerrado, TourWake no vuelve a mostrar paleta, mesa, mando ni punta",
        e["pal"] == (False, False) and not e["table"] and not e["rhand"] and not e["tip"], str(e))
    # D. el director no oculta manos: dormir no toca las del pawn (aunque el pawn las tuviera ocultas)
    bp = mundo(tour=False, hide_hands=False, pawn_hands_visible=False)
    begin_play(bp)
    tick(bp)
    bp.run_fn("TourSleep")
    chk("D bHidePawnHands false: TourSleep no toca las manos del pawn", [h.visible for h in W["pawn"].skel] == [False, False])
    # E. bForceTour sin actor TOUR (prueba en L_TBTest_SC)
    bp = mundo(tour=False, force=True)
    begin_play(bp)
    tick(bp)
    chk("E bForceTour: dormido al empezar aunque no haya actor TOUR", not bp.v["bAwake"] and W["n_install"] == 0)
    # el lint de dsl_sim no conoce 'for': sus sentencias de cuerpo salen como "dentro de for" (falso positivo)
    malos = [m for m in ds.lint_impuros(open(DSL, encoding="utf-8").read()) if not m.endswith("dentro de for")]
    chk("lint: sin impuros inline como dato (salvo cuerpos de for, que son sentencias)", not malos, str(malos))
    print("\n%s" % ("TODO OK" if not fallas else "%d FALLAS: %s" % (len(fallas), fallas)))
    return 1 if fallas else 0


if __name__ == "__main__":
    sys.exit(main())
