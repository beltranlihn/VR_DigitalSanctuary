# -*- coding: utf-8 -*-
"""vida_dsl_sim.py - EJECUTA vida.dsl (los grafos de BP_ValleyLife_SC) SIN Unreal y lo compara con vida_model.VidaBP.

Usa el interprete de dsl_sim.py (NO lo modifica: importa su clase BP, sus nodos nativos y su lint; aca solo se registran
los nodos que la capa de vida agrega). Semantica que respeta: un bind se re-evalua en cada uso (lee el estado de ese
momento), un Set es inmediato, select evalua las dos ramas, las llamadas propias van por keyword, un nodo que el
interprete no conoce FALLA.

Uso:  python vida_dsl_sim.py      -> tiene que decir TODO OK antes de pegar nada en Unreal
"""
import math
import os
import sys

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import dsl_sim as ds  # noqa: E402
import vida_model as vm  # noqa: E402

TEXTO = open(os.path.join(AQUI, "vida.dsl"), encoding="utf-8").read()
VALLEY_CLS = "/Game/SoulCharger/Mechanics/Breath/Valley/BP_BreathValley_SC.BP_BreathValley_SC_C"
BLOB_CLS = "/Game/SoulCharger/Mechanics/Breath/BP_BreathBlob_SC.BP_BreathBlob_SC_C"
RIG_CLS = "/Game/SoulCharger/Mechanics/Breath/BP_BreathRig_SC.BP_BreathRig_SC_C"
CAM_OFF = np.array([4.0, -3.0, 2.0])     # la cabeza del usuario un poco corrida del actor (el ciclopeo NO es el actor)
fallas = []


def chk(lbl, ok, info=""):
    print(("OK    " if ok else "FALLA ") + lbl + ("  " + info if info else ""))
    if not ok:
        fallas.append(lbl)


# ---------------------------------------------------------------------------------------------
# nodos que agrega la capa de vida (los de dsl_sim.py siguen iguales)
# ---------------------------------------------------------------------------------------------
N = ds._n


def _actor(bp, target):
    return target if target is not None else bp.extern["_self"]


N("Transformation|GetActorLocation")(lambda bp, target=None: np.array(_actor(bp, target).loc, float))
N("Transformation|GetActorRotation")(lambda bp, target=None: ds.Rot(0.0, _actor(bp, target).yaw))
N("Transformation|GetActorTransform")(lambda bp, target=None: ds.Xf(_actor(bp, target).loc, ds.Rot(0.0, _actor(bp, target).yaw)))
N("Transformation|GetActorScale3D")(lambda bp, target=None: np.full(3, float(getattr(_actor(bp, target), "scale", 1.0))))
N("Math|Trig|Cos(Degrees)")(lambda bp, x: math.cos(math.radians(x)))
N("Math|Trig|Sin(Degrees)")(lambda bp, x: math.sin(math.radians(x)))
N("Math|Float|Absolute(Float)")(lambda bp, x: abs(x))
N("Math|Float|Truncate")(lambda bp, x: int(math.trunc(x)))
N("Utilities|Array|Length")(lambda bp, arr: len(arr))


@N("Utilities|Array|Get(acopy)")
def _aget(bp, arr, i):
    if not (0 <= i < len(arr)):
        raise IndexError("Get(acopy) fuera de rango: %s de %d" % (i, len(arr)))
    return arr[i]


@N("Math|Integer|%(Integer)")
def _imod(bp, a, b):
    if not isinstance(a, int) or not isinstance(b, int):
        raise TypeError("%(Integer) con no-enteros")
    if b == 0:
        raise ZeroDivisionError("%(Integer) por 0")
    return a % b


@N("Transformation|SetWorldLocation")
def _swl(bp, comp, loc, **k):
    comp.world_loc = np.asarray(loc, float).copy()


@N("Audio|Components|Audio|SetSound")
def _ssnd(bp, comp, snd):
    comp.sound = snd


@N("Audio|Components|Audio|SetPitchMultiplier")
def _spitch(bp, comp, p):
    comp.pitch = float(p)


@N("Audio|Components|Audio|SetVolumeMultiplier")
def _svol(bp, comp, v):
    comp.volume = float(v)


@N("Audio|Components|Audio|Play")
def _play(bp, comp, t=0.0):
    comp.plays.append((bp.v["Clock"], comp.sound, comp.pitch, comp.volume, tuple(comp.world_loc)))


# ---------------------------------------------------------------------------------------------
# el mundo: el actor, el valle, el metaball
# ---------------------------------------------------------------------------------------------
def variables():
    v = {}
    for k, x in vm.BP.items():
        v[k] = x
    v.update(GustSounds=["G0", "G1", "G2"], BreathSounds=["B0"])
    est = dict(Clock=0.0, Wait=0.0, bGusting=False, GustIdx=0.0, GustKind=0.0, Front=0.0, Front0=0.0, Front1=0.0,
               FrontV=0.0, GW=0.0, E0=0.0, E1=0.0, Ramp=0.0, Lf0=0.0, Lf1=0.0, Life=0.0, OrgW=np.zeros(3),
               DirW=np.zeros(3), SndOffW=np.zeros(3), SndMin=0.0, Amp=0.0, Tm=0.0, Rate=0.0, GlobBase=0.0, Glob=0.0,
               ActUser=0.0, VSig=0.0, VGate=0.0, Sprev=0.0, bPrimed=False, Vel=0.0, VelF=0.0, Flow=0.0, InhHold=0.0,
               bExhOnset=False, PerfMode=0, bSndWarned=False, Valley=None, Blob=None, Rig=None, Hold=0.0,
               HoldPh=0.0, HoldV=0.0, HoldRate=0.0, bForce=False)
    v.update(est)
    return v


def mundo(actor_yaw=0.0, actor_loc=vm.ACTOR, valley=True, valley_loc=(0.0, 0.0, vm.VALLE_Z), valley_yaw=0.0,
          blob=True, blob_scale=1.0, texto=None, perillas=None, rig=True, cam_ref=True):
    selfo = ds.Obj("self", loc=np.asarray(actor_loc, float), yaw=actor_yaw)
    dust = ds.Obj("DustMesh", params={}, visible=True, sort=0, collision=None)
    audio = ds.Obj("GustAudio", world_loc=np.zeros(3), sound=None, pitch=1.0, volume=1.0, plays=[])
    w = {}
    vobj = bobj = None
    if valley:
        vobj = ds.Obj("Valley", loc=np.asarray(valley_loc, float), yaw=valley_yaw, Ground=ds.Obj("Ground", params={}))
        w[VALLEY_CLS] = vobj
    if blob:
        bobj = ds.Obj("Blob", loc=vm.SOUL_W.copy(), yaw=0.0, scale=blob_scale)
        w[BLOB_CLS] = bobj
    cam_w = np.asarray(actor_loc, float) + CAM_OFF
    if rig:
        camo = ds.Obj("Camera", world=ds.Xf(cam_w, ds.Rot(-5.0, actor_yaw + 10.0))) if cam_ref else None
        w[RIG_CLS] = ds.Obj("Rig", CamRef=camo)
    mpc = {"S": 0.0, "On": 0.0}
    vars_ = variables()
    if perillas:
        vars_.update(perillas)

    def vida_mpc(bp):
        bp.v["VSig"], bp.v["VGate"] = mpc["S"], mpc["On"]
    bp = ds.BP(texto or TEXTO, vars_, {"DustMesh": dust, "GustAudio": audio},
               extern={"VidaMPC": vida_mpc, "_world": w, "_self": selfo})
    model = vm.VidaBP(actor=vm.Xf(actor_loc, actor_yaw), valley=vm.Xf(valley_loc, valley_yaw), with_valley=valley,
                      soul=(vm.SOUL_W if blob else None), soul_scale=blob_scale, bp=perillas,
                      cam=(cam_w if (rig and cam_ref) else None))
    return bp, model, dust, audio, vobj, mpc


def dif_dust(dust, ref):
    return max(float(np.abs(np.asarray(dust.params[k]) - ref[k]).max()) for k in ref)


def dif_valley(vobj, ref):
    if ref is None:
        return 0.0 if not vobj or not vobj.Ground.params else 1e9
    return max(float(np.abs(np.asarray(vobj.Ground.params[k]) - ref[k]).max()) for k in ref)


# ---------------------------------------------------------------------------------------------
# 0. lint: ninguna funcion impura inline como argumento de datos
# ---------------------------------------------------------------------------------------------
malos = ds.lint_impuros(TEXTO)
chk("lint: ninguna funcion impura inline como argumento de datos en vida.dsl", not malos, "; ".join(malos))
viejo = TEXTO.replace('  (bind _v (Actor|GetActorOfClass :ActorClass "%s"))\n  (Variables|Z-Vida|SetValley _v)' % VALLEY_CLS,
                      '  (Variables|Z-Vida|SetValley (Actor|GetActorOfClass :ActorClass "%s"))' % VALLEY_CLS)
chk("lint, control negativo: SetValley con GetActorOfClass inline se detecta",
    viejo != TEXTO and any("GetActorOfClass" in m for m in ds.lint_impuros(viejo)))


def lint_editor(texto):
    """Dos formas que el write_graph_dsl del editor RECHAZA y este interprete acepta (gotcha 490, 2026-09-29):
    (a) mas de una rama elif/else directa en un mismo (if ...): el DSL admite UNA, y va ultima;
    (b) (* <vector> <operador float>) / (* <operador float> <vector>): 'Could not connect pin ReturnValue to B'."""
    malos = []
    OPS = ("+", "-", "*", "/", "neg", "select")

    def es_vector(e):
        return isinstance(e, list) and e and e[0] in ("Math|Vector|MakeVector", "Variables|Z-Vida|GetOrgW",
                                                      "Variables|Z-Vida|GetDirW", "Variables|Z-Vida|GetSndOffW",
                                                      "Transformation|GetActorLocation")

    def mira(e, donde, binds):
        if not isinstance(e, list) or not e:
            return
        if e[0] == "fn" or e[0] == "event":
            donde = str(e[1])
            binds = {}
        if e[0] == "bind" and isinstance(e[1], str):
            binds[e[1]] = e[2]
        if e[0] in ("if", "elif"):
            ramas = [x for x in e[2:] if isinstance(x, list) and x and x[0] in ("elif", "else")]
            if len(ramas) > 1 or (ramas and e[-1] is not ramas[-1]):
                malos.append(donde + ": if con %d ramas elif/else (el DSL admite una, al final)" % len(ramas))
        if e[0] == "*" and len(e) == 3:
            a, b = [binds[x] if isinstance(x, str) and x in binds else x for x in e[1:]]
            for v, f in ((a, b), (b, a)):
                if es_vector(v) and isinstance(f, list) and f and f[0] in OPS:
                    malos.append(donde + ": (* vector <operador float>)")
        for x in e[1:]:
            mira(x, donde, binds)
    for forma in ds.parse(TEXTO if texto is None else texto):
        mira(forma, "?", {})
    return malos


malos_ed = lint_editor(TEXTO)
chk("lint editor: un solo elif por if y ningun (* vector <operador float>) en vida.dsl", not malos_ed, "; ".join(malos_ed))
neg_ed = lint_editor("(fn X () (bind _m (+ 1.0 2.0)) (Variables|Z-Vida|SetOrgW (* (Math|Vector|MakeVector 1.0 0.0 0.0) _m))"
                     " (if a (b) (elif c (d)) (elif e (f))))")
chk("lint editor, control negativo: los dos patrones rechazados se detectan", len(neg_ed) == 2, "; ".join(neg_ed))

# ---------------------------------------------------------------------------------------------
# 1. vista previa (Construction Script) = VidaBP.preview
# ---------------------------------------------------------------------------------------------
peor = 0.0
casos = 0
for pg in (0.0, 0.25, 0.5, 0.8, 1.0):
    for kind in (0.0, 1.0):
        for pdir in (1.0, -1.0):
            for yaw, vyaw in ((0.0, 0.0), (35.0, -20.0)):
                per = dict(PreviewGust=pg, PreviewKind=kind, PreviewDir=pdir)
                bp, model, dust, audio, vobj, _ = mundo(actor_yaw=yaw, valley_yaw=vyaw, valley_loc=(120.0, -80.0, vm.VALLE_Z),
                                                        perillas=per)
                bp.run_fn("ConstructionScript")
                rd, rv = model.preview()
                peor = max(peor, dif_dust(dust, rd), dif_valley(vobj, rv))
                casos += 1
                if pg == 0.0 and kind == 0.0 and pdir > 0 and yaw == 0.0:
                    chk("vista previa sin rafaga (PreviewGust 0): Amp 0 -> la franja del valle NEUTRA (GustK = 0)",
                        np.array_equal(np.asarray(vobj.Ground.params["GustK"]), np.zeros(4)) and dust.params["VidaS"][3] == 0.0)
                    chk("vista previa: el polvo visible en el editor (Glob = VidaAmount, Live 0: el meandro anima con el reloj del editor)",
                        dust.visible and dust.params["VidaT"][2] == 1.0 and dust.params["VidaT"][3] == 0.0 and dust.sort == 5)
                    chk("vista previa: el Construction Script NO toca el sonido", not audio.plays)
                    chk("vista previa: sin punto ciclopeo en el editor (VidaC.w = 0: cada ojo usa su camara) y sin "
                        "prerrequisito de tick (eso va en BeginPlay)", np.array_equal(dust.params["VidaC"], np.zeros(4))
                        and not bp.extern.get("_prereq"))
chk("Construction Script (VidaPreview) = VidaBP.preview del modelo (%d casos: rafaga lateral/soplo, ida/vuelta, actor y valle girados)" % casos,
    peor < 1e-9, "max |dif| %.1e" % peor)

# ---------------------------------------------------------------------------------------------
# 2. juego: BeginPlay + Tick con la respiracion, contra VidaBP cuadro a cuadro
# ---------------------------------------------------------------------------------------------
FPS = 72.0
DT = 1.0 / FPS


def corrida(segundos, senal, on, **kw):
    bp, model, dust, audio, vobj, mpc = mundo(**kw)
    bp.run_event("EventBeginPlay")
    pe, pv, ps, pk = 0.0, 0.0, 0.0, None
    vis_ok = True
    rec = dict(t=[], gust=[], act=[], front=[])
    for k in range(int(segundos * FPS)):
        t = k * DT
        S, On = senal(t), on(t)
        mpc["S"], mpc["On"] = S, On
        bp.run_event("EventTick", DeltaSeconds=DT)
        model.step(DT, S, On)
        d = dif_dust(dust, model.push_dust())
        v = dif_valley(vobj, model.push_valley())
        s = float(np.abs(audio.world_loc - model.sound_pos()).max())
        if max(d, v) > max(pe, pv):
            pk = (k, d, v)
        pe, pv, ps = max(pe, d), max(pv, v), max(ps, s)
        vis_m = model.PerfMode != 1 and (model.Glob > 0.0005 or model.PerfMode == 2)
        vis_ok = vis_ok and (dust.visible == vis_m)
        rec["t"].append(t)
        rec["gust"].append(model.GustKind if model.bGustOn else -1.0)
        rec["act"].append(model.ActUser)
        rec["front"].append(model.S)
    return bp, model, dust, audio, vobj, pe, pv, ps, vis_ok, pk, rec


def sonidos_iguales(audio, model):
    dsl = [(round(c, 6), snd, round(p, 9), round(v, 9)) + tuple(np.round(loc, 6)) for c, snd, p, v, loc in audio.plays]
    ref = [(round(c, 6), ("B%d" if kind == 1 else "G%d") % var, round(p, 9), round(v, 9)) + tuple(np.round(pos, 6))
           for c, kind, var, p, v, pos in model.sounds]
    return dsl == ref, len(dsl)


belly = lambda t: vm.belly(t)
siempre = lambda t: 1.0
nunca = lambda t: 0.0
T = 360.0
bp, model, dust, audio, vobj, pe, pv, ps, vis_ok, pk, rec = corrida(T, belly, siempre)
g = np.array(rec["gust"])
n_lat = int(np.sum((g[1:] == 0) & (g[:-1] != 0)))
n_sop = int(np.sum((g[1:] == 1) & (g[:-1] != 1)))
chk("juego: EventTick del DSL = VidaBP del modelo, %d s respirando 4-3-4-3 (7 vectores del polvo + 5 del valle, cada cuadro)" % T,
    pe < 1e-9 and pv < 1e-9, "polvo %.1e  valle %.1e  (peor en %s)" % (pe, pv, pk))
chk("juego: la fuente del sonido viaja con el frente igual que en el modelo", ps < 1e-9, "max |dif| %.1e cm" % ps)
chk("juego: la visibilidad del polvo sigue a la presencia", vis_ok)
iguales, nplays = sonidos_iguales(audio, model)
chk("juego: los sonidos (cuando, cual, pitch, volumen, desde donde) = el modelo (%d rafagas: %d laterales, %d soplos)"
    % (nplays, n_lat, n_sop), iguales and nplays >= 5 and n_sop >= 2 and n_lat >= 2)
chk("juego: el log dice 'VIDA: lista' una vez", sum("VIDA: lista" in x for x in bp.log) == 1, str(bp.log[:3]))
chk("juego: tickea DESPUES del rig (AddTickPrerequisiteActor(rig) en BeginPlay, una vez: lee MPC_Breath del mismo cuadro)",
    [o.name for o in bp.extern.get("_prereq", [])] == ["Rig"])
vc = np.asarray(dust.params["VidaC"])
chk("juego: el punto ciclopeo (VidaC) = la camara del rig en el espacio del actor, w = 1",
    np.allclose(vc[:3], vm.Xf(vm.ACTOR, 0.0).inv_loc(vm.ACTOR + CAM_OFF), atol=1e-9) and vc[3] == 1.0, str(vc))
bpr, *_rr = mundo(rig=True, cam_ref=False)
bpr.run_event("EventBeginPlay")
bpr.run_event("EventTick", DeltaSeconds=DT)
bpn, *_rn = mundo(rig=False)
bpn.run_event("EventBeginPlay")
bpn.run_event("EventTick", DeltaSeconds=DT)
chk("sin rig, o con el rig todavia sin CamRef: VidaC.w = 0 (cada ojo su camara), sin prerrequisito, sin errores",
    np.array_equal(_rr[1].params["VidaC"], np.zeros(4)) and np.array_equal(_rn[1].params["VidaC"], np.zeros(4))
    and not bpn.extern.get("_prereq"))
# los soplos arrancan con una exhalacion: el frente sale del usuario en la exhalacion
t_sop = [c for c, kind, *_ in model.sounds if kind == 1]
fase = [((c - 0.4) % 14.0) for c in t_sop]
chk("un solo aire: cada soplo arranca al empezar una exhalacion (fase del ciclo 4-3-4-3 entre 7 y 8,5 s)",
    len(fase) >= 2 and all(7.0 <= f <= 8.5 for f in fase), "fases %s" % np.round(fase, 2).tolist())
# 2b. actor y valle girados y desplazados (las conversiones mundo -> local)
bp2, model2, dust2, audio2, vobj2, pe2, pv2, ps2, vis2, pk2, _ = corrida(200.0, belly, siempre, actor_yaw=30.0,
                                                                          valley_yaw=-20.0, valley_loc=(150.0, 90.0, -90.4))
chk("juego con el actor girado 30 grados y el valle girado -20 y desplazado: DSL = modelo", pe2 < 1e-9 and pv2 < 1e-9 and ps2 < 1e-9,
    "polvo %.1e  valle %.1e  sonido %.1e" % (pe2, pv2, ps2))
# 2c. sin respiracion detectada: solo rafagas laterales, sin esperar exhalaciones
bp3, model3, dust3, audio3, vobj3, pe3, pv3, ps3, vis3, _, rec3 = corrida(240.0, nunca, nunca)
g3 = np.array(rec3["gust"])
chk("sin respiracion detectada (On 0): solo rafagas laterales, DSL = modelo", pe3 < 1e-9 and pv3 < 1e-9 and not np.any(g3 == 1.0)
    and np.any(g3 == 0.0), "polvo %.1e valle %.1e" % (pe3, pv3))
# 2d. sin valle ni metaball en el nivel: nada se rompe, el valle no se toca, el despeje del metaball apagado
bp4, model4, dust4, audio4, vobj4, pe4, pv4, ps4, vis4, _, _ = corrida(120.0, belly, siempre, valley=False, blob=False)
chk("sin valle ni metaball en el nivel: DSL = modelo, VidaSoul con radio 0 (sin despeje), cero errores",
    pe4 < 1e-9 and dust4.params["VidaSoul"][3] == 0.0)
# 2e. metaball a media escala: el despeje se achica con el
bp5, model5, dust5, *_ = corrida(5.0, belly, siempre, blob_scale=0.5)
chk("el despeje del metaball sigue su escala (SoulR x 0,5)", abs(dust5.params["VidaSoul"][3] - 0.5 * vm.BP["SoulR"]) < 1e-9)
# 2f. sin sonidos asignados: un aviso, nada se rompe, las rafagas siguen
bp6, model6, dust6, audio6, vobj6, *_ = mundo(perillas=None)
bp6.v["GustSounds"], bp6.v["BreathSounds"] = [], []
bp6.run_event("EventBeginPlay")
for k in range(int(80 * FPS)):
    bp6.run_event("EventTick", DeltaSeconds=DT)
chk("sin sonidos asignados: UN aviso en el log, cero Play, las rafagas corren igual",
    sum("no tiene sonido" in x for x in bp6.log) == 1 and not audio6.plays and bp6.v["GustIdx"] >= 1.0,
    "rafagas %.0f" % bp6.v["GustIdx"])

# 2g. el boton de panico corta TAMBIEN las rafagas (rev. 2): con bVida false o VidaAmount 0 no sale ninguna nueva
for per, tag in ((dict(bVida=False), "bVida false"), (dict(VidaAmount=0.0), "VidaAmount 0")):
    bpg, modelg, dustg, audiog, vobjg, pe_g, pv_g, ps_g, _, _, recg = corrida(150.0, belly, siempre, perillas=per)
    chk("panico (%s): ni una rafaga en 150 s (ni sonido ni franja), el polvo apagado, DSL = modelo" % tag,
        not audiog.plays and not modelg.sounds and bpg.v["GustIdx"] == 0.0 and not dustg.visible
        and np.array_equal(np.asarray(vobjg.Ground.params["GustK"]), np.zeros(4)) and max(pe_g, pv_g) < 1e-9)
# 2h. 'ke * GustNow': en calma sale en el cuadro siguiente; durante una rafaga, sale apenas termina (la relajacion se
# acelera a 3 s, sin salto); esperando un soplo, sale una lateral en seguida
def ahora(pre_s, respira, esperado_max):
    bpx, modelx, dustx, audiox, vobjx, mpcx = mundo()
    bpx.run_event("EventBeginPlay")
    t = 0.0
    for k in range(int(pre_s * FPS)):
        t = k * DT
        mpcx["S"], mpcx["On"] = (vm.belly(t), 1.0) if respira else (0.0, 0.0)
        bpx.run_event("EventTick", DeltaSeconds=DT)
        modelx.step(DT, mpcx["S"], mpcx["On"])
    n0 = len(audiox.plays)
    bpx.run_event("Custom|GustNow")
    modelx.gust_now()
    k0 = int(pre_s * FPS)
    for k in range(k0, k0 + int(esperado_max * FPS) + 2):
        t = k * DT
        mpcx["S"], mpcx["On"] = (vm.belly(t), 1.0) if respira else (0.0, 0.0)
        bpx.run_event("EventTick", DeltaSeconds=DT)
        modelx.step(DT, mpcx["S"], mpcx["On"])
        if len(audiox.plays) > n0:
            break
    d = dif_dust(dustx, modelx.push_dust())
    lat = len(audiox.plays) > n0 and audiox.plays[-1][1].startswith("G")
    return lat, (k - k0 + 1) * DT, d, bpx.v["bForce"]
ok1, t1, d1, f1 = ahora(3.0, False, 0.05)
chk("GustNow en calma: una lateral en el cuadro siguiente (DSL = modelo)", ok1 and t1 <= 2 * DT + 1e-9 and d1 < 1e-9
    and not f1, "%.3f s" % t1)
ok2, t2, d2, f2 = ahora(20.0, False, 40.0)
chk("GustNow DURANTE una rafaga: no se pierde; sale al terminar ella + a lo sumo 3 s de relajacion (antes: se perdia)",
    ok2 and d2 < 1e-9 and not f2 and t2 < vm.BP["GustLife"] + 3.5, "a los %.1f s del pedido" % t2)
bpw, modelw, *_w = mundo()
bpw.run_event("EventBeginPlay")
# 2h bis: esperando el soplo (turno impar, respiracion detectada, calma cumplida) -> lateral en seguida
for k in range(int(200 * FPS)):
    t = k * DT
    _w[3]["S"], _w[3]["On"] = vm.belly(t), 1.0
    bpw.run_event("EventTick", DeltaSeconds=DT)
    if (not bpw.v["bGusting"]) and bpw.v["Hold"] <= 0.0 and bpw.v["Wait"] < -0.5 and bpw.v["GustIdx"] % 2 == 1:
        break
esperando = (not bpw.v["bGusting"]) and bpw.v["Wait"] < -0.5
n0 = len(_w[1].plays)
bpw.run_event("Custom|GustNow")
bpw.run_event("EventTick", DeltaSeconds=DT)
chk("GustNow mientras se espera un soplo: sale una LATERAL en el cuadro siguiente (no alarga la espera)",
    esperando and len(_w[1].plays) == n0 + 1 and _w[1].plays[-1][1].startswith("G"),
    "esperando %s, espera %.2f" % (esperando, bpw.v["Wait"]))
# 2i. banco: PerfE0..E4 = sin rafagas (FONDO limpio), PerfEEnd = normal
bpq, modelq, dustq, audioq, vobjq, mpcq = mundo()
bpq.run_event("EventBeginPlay")
bpq.run_event("Custom|PerfE0")
for k in range(int(120 * FPS)):
    bpq.run_event("EventTick", DeltaSeconds=DT)
sin = (not audioq.plays) and dustq.visible and np.array_equal(np.asarray(vobjq.Ground.params["GustK"]), np.zeros(4))
bpq.run_event("Custom|PerfEEnd")
for k in range(int(3 * FPS)):
    bpq.run_event("EventTick", DeltaSeconds=DT)
chk("banco: con PerfE0..E4 NINGUNA rafaga en 120 s (polvo visible, franja en 0: FONDO = m0 - m4 sin ruido de la vida); "
    "PerfEEnd la devuelve (sale la que estaba vencida)", sin and len(audioq.plays) == 1, "%d sonidos" % len(audioq.plays))

# ---------------------------------------------------------------------------------------------
# 3. el lazo cerrado visto desde el BP: la primera y la ultima rafaga dejan el polvo EXACTO en su lugar
# ---------------------------------------------------------------------------------------------
sd = vm.seeds()
enc = vm.encode(sd)
sub = {k: (v[::16] if isinstance(v, np.ndarray) and v.shape[0] == enc["LP"].shape[0] else v) for k, v in enc.items()}
res3 = {}
# (a) los defaults: la relajacion dura lo mismo que la calma -> la rafaga siguiente arranca en el cuadro en que la
#     deriva llega a 0 (el relevo tambien tiene que ser continuo); (b) calma de 40 s: Amp se apaga a la vista
for tag, per in (("defaults", None), ("calma 40 s", dict(GapMin=40.0, GapMax=40.0))):
    bp7, model7, dust7, *_ = mundo(perillas=per)
    bp7.run_event("EventBeginPlay")
    salto = 0.0
    prevG = None
    cerrado = []
    deriva_max = 0.0
    relevos = 0
    idx0 = 0.0
    for k in range(int(95 * FPS)):
        bp7.run_event("EventTick", DeltaSeconds=DT)
        pvd = {kk: np.asarray(vv, float) for kk, vv in dust7.params.items()}
        if bp7.v["GustIdx"] > idx0:
            relevos += int(idx0 >= 1.0)
            idx0 = bp7.v["GustIdx"]
        if pvd["VidaS"][3] > 0.0 or prevG is not None:
            r = vm.dust_vs(sub, pvd, (0.0, 3.2, 0.0))
            if prevG is not None:
                # un SALTO es lo que la velocidad no explica: |dG - Gv dt| (la deriva rapida pero continua no cuenta)
                salto = max(salto, float(np.abs((r["G"] - prevG) - 0.5 * (r["Gv"] + prevGv) * DT).max()))
            prevG = r["G"]
            prevGv = r["Gv"]
            if (not bp7.v["bGusting"]) and 0.4 < bp7.v["Hold"] < 0.6:
                deriva_max = max(deriva_max, float(np.linalg.norm(r["G"], axis=1).max()))
            if pvd["VidaS"][3] == 0.0:
                cerrado.append(float(np.abs(r["G"]).max()))
                prevG = None
    res3[tag] = (salto, cerrado, deriva_max, relevos)
salto_a, _, deriva_a, relevos_a = res3["defaults"]
salto_b, cerrado_b, deriva_b, _ = res3["calma 40 s"]
chk("el BP termina la rafaga (remolino + deriva) EXACTO: al apagarse Amp, despues de la relajacion, el "
    "desplazamiento de la rafaga ya vale 0 (sin salto)", cerrado_b and max(cerrado_b) == 0.0, "al apagar %s" % cerrado_b[:3])
chk("ninguna mota SALTA (|dG - Gv dt| < 0,01 cm por cuadro) en la rafaga, la relajacion y el arranque de la rafaga "
    "siguiente justo al terminar la relajacion",
    salto_a < 0.01 and salto_b < 0.01 and relevos_a >= 1, "%.1e / %.1e cm, %d arranques despues de una relajacion" % (salto_a, salto_b, relevos_a))
chk("la deriva se ve: a mitad de la relajacion hay motas corridas a favor del viento (control positivo)",
    min(deriva_a, deriva_b) > 20.0, "%.1f / %.1f cm" % (deriva_a, deriva_b))

# ---------------------------------------------------------------------------------------------
# 4. banco y depuracion
# ---------------------------------------------------------------------------------------------
bp8, model8, dust8, audio8, vobj8, mpc8 = mundo()
bp8.run_event("EventBeginPlay")
for k in range(int(6 * FPS)):
    bp8.run_event("EventTick", DeltaSeconds=DT)
bp8.run_event("Custom|PerfE5")
for k in range(10):
    bp8.run_event("EventTick", DeltaSeconds=DT)
lleno = dust8.visible and dust8.params["VidaT"][2] == 1.0 and dust8.params["VidaS"][0] == 0.0 and dust8.params["VidaS"][3] > 0 \
    and vobj8.Ground.params["GustK"][0] > 0
bp8.run_event("Custom|PerfE6")
bp8.run_event("EventTick", DeltaSeconds=DT)
oculto = (not dust8.visible) and np.array_equal(np.asarray(vobj8.Ground.params["GustK"]), np.zeros(4))
bp8.run_event("Custom|PerfE4")
normal = bp8.v["PerfMode"] == 3
n_log = len(bp8.log)
for ev in ("Custom|PerfV1", "Custom|PerfV2", "Custom|PerfV0"):
    bp8.run_event(ev)
ecos = [x for x in bp8.log[n_log:] if x.startswith("VIDA PERF modo ")]
chk("banco: PerfE5 = vida llena (polvo pleno + rafaga quieta en la mitad, franja encendida), PerfE6 = sin vida (polvo "
    "oculto, franja en 0), PerfE4 = sin rafagas (modo 3); PerfV1/V2/V0 con eco 'VIDA PERF modo N'",
    lleno and oculto and normal and [e[15] for e in ecos] == ["1", "2", "0"], str(ecos))
bp8.run_event("Custom|VidaDbg")
chk("depuracion: 'ke * VidaDbg' imprime una linea con el frente, la actividad y la espera",
    bp8.log[-1].startswith("VIDA DBG rafaga ") and " act " in bp8.log[-1] and " espera " in bp8.log[-1]
    and " deriva " in bp8.log[-1], bp8.log[-1])

# ---------------------------------------------------------------------------------------------
# 5. controles negativos: el simulador TIENE que ver estos errores
# ---------------------------------------------------------------------------------------------
# (a) SetFlow antes de SetExhOnset: el inicio de exhalacion se lee con el modo nuevo y nunca dispara -> sin soplos
mal_a = TEXTO.replace("  (Variables|Z-Vida|SetFlow _new))\n", "  )\n", 1).replace(
    "  (Variables|Z-Vida|SetExhOnset (and", "  (Variables|Z-Vida|SetFlow _new)\n  (Variables|Z-Vida|SetExhOnset (and", 1)
assert mal_a != TEXTO
bpa, modela, dusta, audioa, *_ = mundo(texto=mal_a)
bpa.run_event("EventBeginPlay")
for k in range(int(200 * FPS)):
    t = k * DT
    bpa.extern["VidaMPC"] = (lambda b, t=t: b.v.update(VSig=vm.belly(t), VGate=1.0))
    bpa.run_event("EventTick", DeltaSeconds=DT)
chk("control negativo: pisar Flow antes de leer el inicio de exhalacion deja SIN soplos (el simulador lo ve)",
    not any(s == "B0" for _, s, *_ in audioa.plays), "%d sonidos: %s" % (len(audioa.plays), [p[1] for p in audioa.plays]))
# (b) el frente arranca en e0 (no en e0 - 2W): la primera mota salta al empezar
mal_b = TEXTO.replace("(Variables|Z-Vida|SetFront0 (- (Variables|Z-Vida|GetE0) (* 2.0 (Variables|Z-Vida|GetGW))))",
                      "(Variables|Z-Vida|SetFront0 (Variables|Z-Vida|GetE0))", 1)
assert mal_b != TEXTO
bpb, modelb, dustb, *_ = mundo(texto=mal_b)
bpb.run_event("EventBeginPlay")
salto_b = 0.0
prev = None
for k in range(int(20 * FPS)):
    bpb.run_event("EventTick", DeltaSeconds=DT)
    pvd = {kk: np.asarray(vv, float) for kk, vv in dustb.params.items()}
    r = vm.dust_vs(sub, pvd, (0.0, 3.2, 0.0))
    if prev is not None:
        salto_b = max(salto_b, float(np.abs(r["G"] - prev).max()))
    prev = r["G"]
chk("control negativo: si el frente arranca en e0 (sin los 2W de margen) las motas SALTAN al empezar (el simulador lo ve)",
    salto_b > 1.0, "salto %.2f cm" % salto_b)

# (c) Amp a 0 en cuanto termina el frente (la rev. 1): con la deriva las motas vuelven de golpe a su lugar
mal_c = TEXTO.replace("""    (Variables|Z-Vida|SetGusting false)
    (CallFunction|VidaGap)""", """    (Variables|Z-Vida|SetGusting false)
    (Variables|Z-Vida|SetAmp 0.0)
    (CallFunction|VidaGap)""", 1)
assert mal_c != TEXTO
bpc, modelc, dustc, *_ = mundo(texto=mal_c)
bpc.run_event("EventBeginPlay")
salto_c = 0.0
prev = None
for k in range(int(50 * FPS)):
    bpc.run_event("EventTick", DeltaSeconds=DT)
    pvd = {kk: np.asarray(vv, float) for kk, vv in dustc.params.items()}
    r = vm.dust_vs(sub, pvd, (0.0, 3.2, 0.0))
    if prev is not None:
        salto_c = max(salto_c, float(np.abs(r["G"] - prev).max()))
    prev = r["G"]
chk("control negativo: si Amp se apaga al terminar el frente (sin relajacion), la deriva SALTA (el simulador lo ve)",
    salto_c > 5.0, "salto %.1f cm" % salto_c)
# (d) VidaMaybe sin mirar bVida (la rev. 1): el panico deja pasar rafagas
mal_d = TEXTO.replace("(and (Variables|A-Vida|GetVida) (> (Variables|A-Vida|GetVidaAmount) 0.0))", "true", 1)
assert mal_d != TEXTO
bpd, modeld, dustd, audiod, *_ = mundo(texto=mal_d, perillas=dict(bVida=False))
bpd.run_event("EventBeginPlay")
for k in range(int(40 * FPS)):
    bpd.run_event("EventTick", DeltaSeconds=DT)
chk("control negativo: sin la condicion de bVida en VidaMaybe, con bVida false SALEN rafagas (el simulador lo ve)",
    len(audiod.plays) >= 1, "%d sonidos" % len(audiod.plays))

print("\n%s" % ("TODO OK" if not fallas else "%d FALLAS: %s" % (len(fallas), fallas)))
sys.exit(1 if fallas else 0)
