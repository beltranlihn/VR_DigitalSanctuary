# -*- coding: utf-8 -*-
"""dsl_sim.py - EJECUTA un archivo .dsl de Blueprint (el subconjunto que usa este proyecto) SIN Unreal y lo compara
con su modelo de referencia. Es la gotcha 473 ("verificar logica de Blueprint sin nivel ni PIE: portar el DSL a
Python"), pero sin portar a mano: el interprete lee el MISMO texto que se pega en write_graph_dsl.

Semantica que respeta (las trampas que ya costaron):
  - un (bind x expr) NO es una asignacion: guarda la EXPRESION y la re-evalua en cada uso, leyendo el estado de ese
    momento (memoria "el bind del DSL no es una asignacion"). Un Set es inmediato.
  - los Get de variables leen el estado vivo; select evalua las dos ramas (como el nodo Select).
  - las llamadas a funciones propias van como sentencia; sus argumentos por keyword.
  - un nombre de nodo que el interprete no conoce FALLA (no se inventa).

Uso:
  python dsl_sim.py aire    -> breath_air.dsl contra breath_air_model (paso a paso con la cadena rig -> MPC, vista
                               previa del Construction Script, montaje y banco)
  python dsl_sim.py valle   -> valley_live.dsl contra valley_model.live_desde_S / live_paso
"""
import math
import os
import re
import sys

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)


# ---------------------------------------------------------------------------------------------
# lector de S-expresiones
# ---------------------------------------------------------------------------------------------
def tokens(txt):
    txt = "\n".join(l.split(";;")[0] if not l.lstrip().startswith(";;") else "" for l in txt.split("\n"))
    # un nombre de nodo puede terminar en un sufijo entre parentesis sin espacios: Math|Float|Clamp(Float)
    return re.findall(r':"[^"]*"|"[^"]*"|[^\s()"]+(?:\(\w+\))?|\(|\)', txt)


def parse(txt):
    toks = tokens(txt)
    pos = 0

    def one():
        nonlocal pos
        t = toks[pos]
        pos += 1
        if t == "(":
            lst = []
            while toks[pos] != ")":
                lst.append(one())
            pos += 1
            return lst
        return t
    out = []
    while pos < len(toks):
        out.append(one())
    return out


def secciones(txt):
    """{nombre de grafo: texto} usando las lineas ';; ===== GRAFO: <nombre>'."""
    out, cur, buf = {}, None, []
    for l in txt.split("\n"):
        m = re.match(r";; ===== GRAFO: (\w+)", l)
        if m:
            if cur:
                out[cur] = "\n".join(buf)
            cur, buf = m.group(1), []
        elif cur:
            buf.append(l)
    if cur:
        out[cur] = "\n".join(buf)
    return out


# ---------------------------------------------------------------------------------------------
# valores de Unreal
# ---------------------------------------------------------------------------------------------
class Rot:
    def __init__(self, pitch, yaw, roll=0.0):
        self.pitch, self.yaw, self.roll = float(pitch), float(yaw), float(roll)


class Xf:
    """FTransform sin escala: loc + rotacion (pitch, yaw), roll 0."""

    def __init__(self, loc, rot):
        self.loc, self.rot = np.asarray(loc, float), rot

    def axes(self):
        return _axes(self.rot)


def _axes(r):
    if abs(r.roll) > 1e-9:
        raise ValueError("el simulador solo soporta roll 0")
    p, y = math.radians(r.pitch), math.radians(r.yaw)
    F = np.array([math.cos(p) * math.cos(y), math.cos(p) * math.sin(y), math.sin(p)])
    R = np.array([-math.sin(y), math.cos(y), 0.0])
    U = np.array([-math.sin(p) * math.cos(y), -math.sin(p) * math.sin(y), math.cos(p)])
    return F, R, U


class Obj:
    def __init__(self, name, **k):
        self.name = name
        self.__dict__.update(k)


def normalize_axis(a):
    a = math.fmod(a, 360.0)
    if a < 0.0:
        a += 360.0
    if a > 180.0:
        a -= 360.0
    return a


# ---------------------------------------------------------------------------------------------
# interprete
# ---------------------------------------------------------------------------------------------
class Thunk:
    def __init__(self, expr, env):
        self.expr, self.env = expr, env


class BP:
    def __init__(self, texto, vars_, comps, extern=None):
        self.fns = {}
        self.events = {}
        for graf, t in secciones(texto).items():
            for form in parse(t):
                if form[0] == "fn":
                    self.fns[form[1]] = (form[2], form[3:])
                elif form[0] == "event":
                    # (event X (P1 P2) cuerpo...) o (event X () cuerpo...) o (event X cuerpo...)
                    es_params = len(form) > 2 and isinstance(form[2], list) and all(
                        isinstance(p, str) and "|" not in p for p in form[2])
                    if es_params:
                        self.events[form[1]] = (form[2], form[3:])
                    else:
                        self.events[form[1]] = ([], form[2:])
        self.v = dict(vars_)          # variables del BP por nombre (sin categoria)
        self.comps = comps            # componentes: nombre -> Obj(world=Xf, params={}, visible, sort, parent)
        self.extern = extern or {}    # funciones reemplazadas (puentes de create_node) y objetos del mundo
        self.log = []
        self.calls = {}

    # ---- variables
    def _var(self, head):
        m = re.match(r"Variables\|[\w\-]+\|(Get|Set)(\w+)$", head)
        if not m:
            return None
        name = m.group(2)
        for cand in (name, "b" + name):
            if cand in self.v:
                return m.group(1), cand
        if name in self.comps:
            return m.group(1), name
        raise KeyError("variable inexistente: %s (ni b%s)" % (name, name))

    def run_fn(self, name, **args):
        self.calls[name] = self.calls.get(name, 0) + 1
        if name in self.extern:
            return self.extern[name](self, **args)
        params, body = self.fns[name]
        for p in params:
            if p not in args:
                raise TypeError("%s: falta el argumento %s" % (name, p))
        env = dict(args)
        self.block(body, env)

    def run_event(self, name, **args):
        params, body = self.events[name]
        self.block(body, dict(args))

    def block(self, stmts, env):
        for s in stmts:
            self.stmt(s, env)

    def stmt(self, s, env):
        head = s[0]
        if head == "bind":
            if isinstance(s[1], list):
                raise NotImplementedError("bind multiple")
            env[s[1]] = Thunk(s[2], dict(env))
            return
        if head == "if":
            rest = s[2:]
            ramas = [x for x in rest if isinstance(x, list) and x and x[0] in ("elif", "else")]
            cuerpo = [x for x in rest if x not in ramas]
            if self.ev(s[1], env):
                self.block(cuerpo, env)
                return
            for r in ramas:
                if r[0] == "elif" and self.ev(r[1], env):
                    self.block(r[2:], env)
                    return
                if r[0] == "else":
                    self.block(r[1:], env)
                    return
            return
        if head == "Utilities|IsValid":
            ok = self.ev(s[1], env) is not None
            for r in s[2:]:
                lab = r[0]
                if (lab == ':"Is Valid"' and ok) or (lab == ':"Is Not Valid"' and not ok):
                    self.block(r[1:], env)
            return
        v = self._var(head) if head.startswith("Variables|") else None
        if v and v[0] == "Set":
            self.v[v[1]] = self.ev(s[1], env) if len(s) > 1 else None
            return
        self.ev(s, env)

    def kw(self, args, env):
        pos, kws = [], {}
        i = 0
        while i < len(args):
            a = args[i]
            if isinstance(a, str) and a.startswith(":") and not a.startswith(':"'):
                kws[a[1:]] = self.ev(args[i + 1], env)
                i += 2
            else:
                pos.append(self.ev(a, env))
                i += 1
        return pos, kws

    def ev(self, e, env):
        if isinstance(e, str):
            if e.startswith('"'):
                return e[1:-1]
            if e == "true":
                return True
            if e == "false":
                return False
            if e in env:
                x = env[e]
                return self.ev(x.expr, dict(x.env)) if isinstance(x, Thunk) else x
            try:
                return float(e)
            except ValueError:
                raise NameError("simbolo desconocido: " + e)
        head, args = e[0], e[1:]
        ops = {"+": lambda a, b: a + b, "-": lambda a, b: a - b, "*": lambda a, b: a * b, "/": lambda a, b: a / b,
               "<": lambda a, b: a < b, ">": lambda a, b: a > b, "<=": lambda a, b: a <= b, ">=": lambda a, b: a >= b,
               "==": lambda a, b: a == b, "!=": lambda a, b: a != b}
        if head in ops:
            a, b = self.ev(args[0], env), self.ev(args[1], env)
            return ops[head](a, b)
        if head == "and":
            a, b = self.ev(args[0], env), self.ev(args[1], env)   # los dos se evaluan (nodo AND puro)
            return bool(a) and bool(b)
        if head == "or":
            a, b = self.ev(args[0], env), self.ev(args[1], env)
            return bool(a) or bool(b)
        if head == "not":
            return not self.ev(args[0], env)
        if head == "neg":
            return -self.ev(args[0], env)
        if head == "select":
            c, a, b = self.ev(args[0], env), self.ev(args[1], env), self.ev(args[2], env)
            return a if c else b
        if head in (".x", ".y", ".z"):
            return float(self.ev(args[0], env)["xyz".index(head[1])])
        if head in (".pitch", ".yaw", ".roll"):
            return getattr(self.ev(args[0], env), head[1:])
        if head == ".rotation":
            return self.ev(args[0], env).rot
        if head == ".location":
            return self.ev(args[0], env).loc
        if head.startswith("Variables|"):
            g, name = self._var(head)
            if g == "Get":
                return self.v[name] if name in self.v else self.comps[name]
        if head.startswith("CallFunction|"):
            pos, kws = self.kw(args, env)
            if pos:
                raise TypeError("llamada propia con argumento POSICIONAL (cae en el pin self): " + str(e))
            return self.run_fn(head.split("|", 1)[1], **kws)
        m = re.match(r"Class\|(\w+)\|Get(\w+)$", head)
        if m:
            obj = self.ev(args[0], env)
            return None if obj is None else getattr(obj, m.group(2))
        pos, kws = self.kw(args, env)
        return NATIVOS[head](self, *pos, **kws)


def _n(name):
    def deco(f):
        NATIVOS[name] = f
        return f
    return deco


NATIVOS = {}
_n("Math|Float|Max(Float)")(lambda bp, a, b: max(a, b))
_n("Math|Float|Min(Float)")(lambda bp, a, b: min(a, b))
_n("Math|Float|Clamp(Float)")(lambda bp, x, lo=0.0, hi=1.0: min(max(x, lo), hi))
_n("Math|Float|Exp")(lambda bp, x: math.exp(x))
_n("Math|Float|Fraction")(lambda bp, x: x - math.floor(x))
_n("Math|Float|Lerp")(lambda bp, a, b, t: a + (b - a) * t)
_n("Math|Rotator|NormalizeAxis")(lambda bp, a: normalize_axis(a))
_n("Math|Vector|MakeVector")(lambda bp, x=0.0, y=0.0, z=0.0: np.array([x, y, z], float))
_n("Math|Color|MakeColor")(lambda bp, r, g, b, a=1.0: np.array([r, g, b, a], float))


@_n("Math|Rotator|MakeRotator")
def _mkrot(bp, *pos, Roll=0.0, Pitch=0.0, Yaw=0.0):
    if pos:
        raise TypeError("MakeRotator con posicionales: el orden es (Roll, Pitch, Yaw), gotcha 297")
    return Rot(Pitch, Yaw, Roll)


_n("Math|Vector|GetForwardVector")(lambda bp, r: _axes(r)[0])
_n("Math|Vector|GetRightVector")(lambda bp, r: _axes(r)[1])
_n("Math|Vector|GetUpVector")(lambda bp, r: _axes(r)[2])


@_n("Math|Transform|TransformLocation")
def _tl(bp, t, p):
    F, R, U = t.axes()
    return t.loc + p[0] * F + p[1] * R + p[2] * U


@_n("Math|Transform|InverseTransformLocation")
def _itl(bp, t, p):
    F, R, U = t.axes()
    d = np.asarray(p, float) - t.loc
    return np.array([d @ F, d @ R, d @ U])


@_n("Math|Transform|InverseTransformDirection")
def _itd(bp, t, d):
    F, R, U = t.axes()
    d = np.asarray(d, float)
    return np.array([d @ F, d @ R, d @ U])


_n("Transformation|GetWorldTransform")(lambda bp, c: c.world)


@_n("Rendering|Material|SetColorParameterValueonMaterials")
def _scol(bp, c, name, val):
    c.params[name] = np.asarray(val, float)[:4]


@_n("Rendering|Material|SetVectorParameterValueonMaterials")
def _svec(bp, c, name, val):
    c.params[name] = np.asarray(val, float)[:3]


@_n("Rendering|Material|SetScalarParameterValueonMaterials")
def _ssca(bp, c, name, val):
    c.params[name] = float(val)


@_n("Rendering|SetVisibility")
def _svis(bp, c, vis, prop=False):
    c.visible = bool(vis)


@_n("Rendering|SetTranslucentSortPriority")
def _ssort(bp, c, v):
    c.sort = int(v)


@_n("Collision|SetCollisionEnabled")
def _scoll(bp, c, mode):
    c.collision = mode


@_n("Development|SetHiddeninGame")  # type_id real en 5.8 (find_node_types, 2026-09-28)
def _shig(bp, c, hidden, prop=False):
    c.hidden_in_game = bool(hidden)


_n("Utilities|String|ToString(Float)")(lambda bp, x: "%f" % x)
_n("Utilities|String|Append")(lambda bp, a, b: a + b)


@_n("Utilities|Time|GetWorldDeltaSeconds")
def _gwds(bp):
    return bp.extern["_dt"]


@_n("Development|PrintString")
def _print(bp, txt, **k):
    bp.log.append(txt)


@_n("Actor|GetActorOfClass")
def _gaoc(bp, ActorClass=None):
    return bp.extern["_world"].get(ActorClass)


@_n("Actor|Tick|AddTickPrerequisiteActor")
def _atp(bp, PrerequisiteActor=None):
    bp.extern.setdefault("_prereq", []).append(PrerequisiteActor)


@_n("Transformation|AttachComponentToComponent")
def _attach(bp, c, parent, LocationRule=None, RotationRule=None, ScaleRule=None):
    if (LocationRule, RotationRule, ScaleRule) != ("SnapToTarget",) * 3:
        raise ValueError("reglas de attach inesperadas")
    c.parent = parent


# ---------------------------------------------------------------------------------------------
# AIRE: breath_air.dsl contra breath_air_model
# ---------------------------------------------------------------------------------------------
fallas = []


def chk(lbl, ok, info=""):
    print(("OK    " if ok else "FALLA ") + lbl + ("  " + info if info else ""))
    if not ok:
        fallas.append(lbl)


# ---------------------------------------------------------------------------------------------
# LINT: una funcion IMPURA (con pines de exec) inline como argumento de DATOS queda con el pin desconectado, compila
# limpio y el read no lo muestra (gotcha "UNA FUNCION IMPURA INLINE COMO ARGUMENTO DE DATOS"). Se permite solo como
# sentencia o como (bind _x (impura ...)) de primer nivel.
# ---------------------------------------------------------------------------------------------
IMPUROS = ("CallFunction|", "Actor|GetActorOfClass", "Rendering|", "Collision|", "Transformation|AttachComponentToComponent",
           "Actor|Tick|", "Development|", "Utilities|IsValid")


def _impuro(head):
    if not isinstance(head, str):
        return False
    if re.match(r"Variables\|[\w\-]+\|Set", head):
        return True
    return head.startswith(IMPUROS)


def lint_impuros(texto):
    malos = []

    def mira(expr, donde):
        if not isinstance(expr, list) or not expr:
            return
        for a in expr[1:]:
            if isinstance(a, list) and a:
                if _impuro(a[0]):
                    malos.append("%s: %s dentro de %s" % (donde, a[0], expr[0]))
                mira(a, donde)

    for graf, t in secciones(texto).items():
        for form in parse(t):
            cuerpo = form[3:] if form[0] == "fn" else form[2:]
            pila = list(cuerpo)
            while pila:
                st = pila.pop()
                if not isinstance(st, list) or not st:
                    continue
                if st[0] == "bind":
                    mira(st[2] if isinstance(st[2], list) else [], graf)
                    continue
                if st[0] in ("if", "Utilities|IsValid"):
                    mira([st[0], st[1]], graf)
                    for r in st[2:]:
                        if isinstance(r, list) and r and isinstance(r[0], str) and (r[0].startswith(':') or r[0] in ("elif", "else")):
                            pila.extend(r[1:])
                        else:
                            pila.append(r)
                    continue
                mira(st, graf)
    return malos


def aire():
    import breath_air_model as am
    txt = open(os.path.join(AQUI, "breath_air.dsl"), encoding="utf-8").read()
    malos = lint_impuros(txt)
    chk("lint: ninguna funcion impura inline como argumento de datos en breath_air.dsl", not malos, "; ".join(malos))
    rig_cls = "/Game/SoulCharger/Mechanics/Breath/BP_BreathRig_SC.BP_BreathRig_SC_C"
    viejo = txt.replace('  (bind _found (Actor|GetActorOfClass :ActorClass "%s"))\n  (Variables|Z-Aliento|SetRig _found)' % rig_cls,
                        '  (Variables|Z-Aliento|SetRig (Actor|GetActorOfClass :ActorClass "%s"))' % rig_cls)
    chk("lint, control negativo: la forma de la rev. 1 (SetRig con GetActorOfClass inline) se detecta",
        viejo != txt and any("GetActorOfClass" in m for m in lint_impuros(viejo)))
    estado = dict(Tin=0.0, Tout=0.0, Fout=0.0, Ein=0.0, Eout=0.0, InRate=0.0, OutRate=0.0, Vel=0.0, VelF=0.0, Flow=0.0,
                  InhHold=0.0, Sprev=0.0, bPrimed=False, Clock=0.0, bOnset=False, Per=0.0, LastOnset=0.0, RateBpm=0.0,
                  RateCalm=0.0, MouthW=np.zeros(3), YawLag=0.0, PitchLag=0.0, YawPrev=0.0, PitchPrev=0.0,
                  TurnRate=0.0, MoveFade=0.0, bLagInit=False, GlobBase=0.0, Glob=0.0, bMounted=False, PerfMode=0,
                  AirSig=0.0, AirGate=0.0, Rig=None, CamXf=None)
    perillas = dict(am.BP)
    import sim_breath_air as sb

    def nuevo(eye, yaw, pitch, texto=None):
        mesh = Obj("AirMesh", world=Xf(eye, Rot(pitch, yaw)), params={}, visible=True, sort=0, parent=None)
        cam = Obj("Camera")
        rig = Obj("Rig", CamRef=cam)
        mpc = {"S": 0.0, "On": 0.0}

        def air_mpc(bp):
            bp.v["AirSig"], bp.v["AirGate"] = mpc["S"], mpc["On"]
        ghosts = {g: Obj(g, params={}) for g in ("HeadGhost", "MouthGhost")}
        bp = BP(texto or txt, dict(estado, **perillas), dict({"AirMesh": mesh}, **ghosts),
                extern={"AirMPC": air_mpc, "_world": {rig_cls: rig}})
        return bp, mesh, cam, rig, mpc

    # ---- 1. vista previa (Construction Script) contra preview_push
    peor = 0.0
    for pb, t in ((0.0, 0.35), (0.7, 0.2), (-1.0, 0.8), (1.0, 0.0), (1.6, 0.5)):
        for yaw, pitch in ((0.0, 0.0), (37.0, -12.0)):
            bp, mesh, _, _, _ = nuevo(np.array([10.0, -5.0, 120.0]), yaw, pitch)
            bp.v["PreviewBreath"], bp.v["PreviewAirT"] = pb, t
            bp.run_fn("ConstructionScript")
            ref = am.preview_push(dict(PreviewBreath=pb, PreviewAirT=t), yaw, pitch)
            for k, v in ref.items():
                peor = max(peor, float(np.abs(mesh.params[k] - v).max()))
            if pb == 0.0:
                chk("vista previa neutra (PreviewBreath 0): Ein = Eout = 0 -> nada dibujado",
                    mesh.params["AirE"][0] == 0.0 and mesh.params["AirE"][1] == 0.0)
    chk("Construction Script (PreviewAir + PushAir) = preview_push del modelo (8 vectores, 10 casos)", peor < 1e-9,
        "max |dif| %.1e" % peor)
    chk("Construction Script: TranslucencySortPriority 20 en AirMesh", mesh.sort == 20)

    # ---- 2. juego: BeginPlay + Tick con la cadena rig -> MPC, contra AirBP (mismo montaje en el cuadro 0)
    def corrida(fuente, n, eventos=True, on_de=None, texto=None, solo=None):
        eye, yaw, pitch, _ = sb.head(0.0, eventos)
        bp, mesh, cam, rig, mpc = nuevo(eye, yaw, pitch, texto)
        bp.run_event("EventBeginPlay")
        air = am.AirBP(eye, yaw, pitch)
        follower = am.RigFollower(s0=-1.0)
        peor, peor_k = 0.0, None
        vis_ok = True
        rec = dict(t=[], ph=[], rin=[], rout=[], rate=[], glob=[], tin=[], tout=[])
        for k in range(n):
            t = k * sb.DT
            tgt, ph = fuente(t, sb.DT)
            S = follower.step(tgt, sb.DT)
            on = 1.0 if on_de is None else on_de(t)
            if on_de is not None and on == 0.0:
                S = 0.0                    # el Retire del rig: PushMPC(0, 0) en UN cuadro
            eye, yaw, pitch, _ = sb.head(t, eventos)
            mesh.world = Xf(eye, Rot(pitch, yaw))
            mpc["S"], mpc["On"] = S, on
            bp.run_event("EventTick", DeltaSeconds=sb.DT)
            if k == 1:
                air.bLagInit = False       # el BP se monto al final del cuadro 0: AirMountCam re-inicia el marco
            air.step(sb.DT, S, on, eye, yaw, pitch, mounted=(k >= 1))
            ref = air.push(eye, yaw, pitch)
            for kk, v in ref.items():
                if solo and kk not in solo:
                    continue
                d = float(np.abs(mesh.params[kk] - v).max())
                if d > peor:
                    peor, peor_k = d, (k, kk)
            vis_ok = vis_ok and (mesh.visible == (air.Glob > 0.0005))
            for kk, vv in (("t", t), ("ph", ph), ("rin", bp.v["InRate"]), ("rout", bp.v["OutRate"]), ("rate", bp.v["RateBpm"]),
                           ("glob", bp.v["Glob"]), ("tin", bp.v["Tin"]), ("tout", bp.v["Tout"])):
                rec[kk].append(vv)
        return bp, mesh, cam, rig, peor, peor_k, vis_ok, {k: np.array(v) for k, v in rec.items()}

    T = 14.0
    n = int((5 * T + 2.0) * sb.FPS)
    bp, mesh, cam, rig, peor, peor_k, vis_ok, _ = corrida(lambda t, dt: am.belly_target(t), n)
    chk("juego: EventTick del DSL = AirBP del modelo, 5 ciclos con giro, mirada al sensor e inclinacion (8 vectores x %d cuadros)" % n,
        peor < 1e-9, "max |dif| %.1e en %s" % (peor, peor_k))
    chk("juego: montado en la camara del rig (SnapToTarget) y tick despues del rig",
        mesh.parent is cam and bp.v["bMounted"] and bp.extern.get("_prereq") == [rig])
    chk("juego: la visibilidad sigue a Glob (sin aire no se dibuja)", vis_ok)
    chk("juego: el log dice que se monto una sola vez", sum("montado" in x for x in bp.log) == 1, str(bp.log))
    # ---- 2b. con la senal REAL: ruido OU + deriva del sostenido (revision costo/confort): DSL = modelo, pausas quietas,
    #          ritmo bien medido
    for sig, dr in ((0.03, 0.2), (0.05, 0.15)):
        src = am.BellyNoisy(sig, dr, seed=4)
        n2 = int(8 * T * sb.FPS)
        _, _, _, _, peor2, pk2, _, rec = corrida(src, n2, eventos=False)
        t = rec["t"]
        seg = []
        for c in range(2, 8):
            t0 = c * T + 0.4
            for ini in (4.0, 11.0):
                m = (t >= t0 + ini + 1.5) & (t < t0 + ini + 3.0)
                seg.append(((rec["rin"][m] > 0) | (rec["rout"][m] > 0)).mean())
        quieto = 1.0 - float(np.mean(seg))
        chk("senal real (ruido %.2f, deriva %.2f): DSL = modelo en %d cuadros; 2a mitad de las pausas quieta %.1f %% (>= 98); "
            "ritmo %.2f resp/min (real 4,29 +-1)" % (sig, dr, n2, 100 * quieto, rec["rate"][-1]),
            peor2 < 1e-9 and quieto >= 0.98 and abs(rec["rate"][-1] - 60.0 / T) <= 1.0, "max |dif| %.1e en %s" % (peor2, pk2))
    # ---- 2c. ritmo en tres frecuencias (sin pausas), senal ideal y con ruido
    for per in (10.0, 6.0, 12.0):
        for sig in (0.0, 0.03):
            src = am.BellyNoisy(sig, 0.0, pacer=(per / 2, 0.0, per / 2, 0.0), seed=2)
            _, _, _, _, _, _, _, rec = corrida(src, int(8 * per * sb.FPS), eventos=False)
            chk("ritmo %.1f resp/min (ruido %.2f): RateBpm %.2f (+-1)" % (60.0 / per, sig, rec["rate"][-1]),
                abs(rec["rate"][-1] - 60.0 / per) <= 1.0)
    # ---- 2d. el Retire del rig: On y Signed caen a 0 en UN cuadro -> nada salta (ni la presencia ni la cinta)
    t_off = 2 * T + 0.4 + 9.0                      # en plena exhalacion
    _, _, _, _, peor3, _, _, rec = corrida(lambda t, dt: am.belly_target(t), int((t_off + 5.0) * sb.FPS), eventos=False,
                                           on_de=lambda t: 1.0 if t < t_off else 0.0)
    m = rec["t"] >= t_off - 0.1
    dg = float(np.abs(np.diff(rec["glob"][m])).max())
    dcin = max(float(np.abs(((np.diff(rec["tin"][m]) + 0.5) % 1.0) - 0.5).max()),
               float(np.abs(((np.diff(rec["tout"][m]) + 0.5) % 1.0) - 0.5).max()))
    chk("escalon del Retire (On 1 -> 0 y Signed -> 0 en un cuadro): la presencia baja <= 3 %% por cuadro (%.4f) y la cinta "
        "no salta (%.4f por cuadro); DSL = modelo" % (dg, dcin), dg <= 0.03 and dcin <= 0.01 and peor3 < 1e-9)
    # ---- 3. banco
    bp.run_event("Custom|PerfE6")
    bp.run_event("EventTick", DeltaSeconds=sb.DT)
    oculto = mesh.visible is False
    bp.run_event("Custom|PerfE5")
    bp.run_event("EventTick", DeltaSeconds=sb.DT)
    lleno = mesh.visible and mesh.params["AirT"][3] == 1.0 and mesh.params["AirE"][0] == 1.0 and mesh.params["AirE"][1] == 1.0
    bp.run_event("Custom|PerfE0")
    ecos = [x for x in bp.log if x.startswith("PERF: entering modo ")]
    bp.run_event("Custom|PerfE5")
    n_log = len(bp.log)
    bp.run_event("Custom|PerfE4")
    vuelve4 = bp.v["PerfMode"] == 0 and len(bp.log) == n_log
    chk("banco: PerfE6 oculta, PerfE5 llena, PerfE0 y PerfE4 (sin eco) vuelven a normal (ecos PERF: entering modo N)",
        oculto and lleno and vuelve4 and [e[20] for e in ecos] == ["6", "5", "0"], str(ecos))
    bp.run_event("Custom|AirDbg")
    chk("depuracion: 'ke * AirDbg' imprime una linea con v, modo y S", bp.log[-1].startswith("AIRE DBG v ") and " modo " in bp.log[-1] and " S " in bp.log[-1], bp.log[-1])
    # ---- 4. sin rig: nunca se monta, nunca se dibuja
    eye, yaw, pitch, _ = sb.head(0.0, True)
    bp2, mesh2, _, _, mpc2 = nuevo(eye, yaw, pitch)
    bp2.extern["_world"] = {}
    bp2.run_event("EventBeginPlay")
    for k in range(200):
        mpc2["S"], mpc2["On"] = math.sin(k * 0.05), 1.0
        bp2.run_event("EventTick", DeltaSeconds=sb.DT)
    chk("sin BP_BreathRig_SC en el nivel: no se monta y no dibuja nada (Glob 0, oculto)",
        not bp2.v["bMounted"] and mesh2.visible is False and mesh2.params["AirT"][3] == 0.0)
    # ---- 5. control negativo: el MISMO DSL con el orden cambiado (Sprev antes de Vel) TIENE que fallar
    txt_mal = txt.replace("  (Variables|Z-Aliento|SetSprev (Variables|Z-Aliento|GetAirSig))\n", "")
    txt_mal = txt_mal.replace("  (bind _dt (Math|Float|Max(Float) DT 0.0001))\n",
                              "  (bind _dt (Math|Float|Max(Float) DT 0.0001))\n  (Variables|Z-Aliento|SetSprev (Variables|Z-Aliento|GetAirSig))\n", 1)
    assert txt_mal != txt
    bp3 = BP(txt_mal, dict(estado, **perillas), {"AirMesh": Obj("AirMesh", world=Xf(eye, Rot(pitch, yaw)), params={}, visible=True, sort=0, parent=None),
                                                 "HeadGhost": Obj("HeadGhost"), "MouthGhost": Obj("MouthGhost")},
             extern={"AirMPC": lambda b: b.v.update(AirSig=math.sin(b.v["Clock"]), AirGate=1.0), "_world": {}})
    bp3.run_event("EventBeginPlay")
    mx = 0.0
    for k in range(100):
        bp3.run_event("EventTick", DeltaSeconds=sb.DT)
        mx = max(mx, abs(bp3.v["Vel"]))
    chk("control negativo: pisar Sprev antes de calcular Vel deja la velocidad en 0 (el simulador lo ve)", mx == 0.0,
        "max |Vel| %.3g" % mx)
    # ---- 6. control negativo: SetMoveFade ANTES de los Set del marco (el bind _k se re-evaluaria con el MoveFade nuevo)
    bloque = "  ;; apagado por giro: baja EN EL MISMO CUADRO y vuelve con TurnBack\n"
    i_a, i_b = txt.index(bloque), txt.index("  (Variables|Z-Aliento|SetYawPrev (.yaw _rot))")
    i_m = txt.index("  (Variables|Z-Aliento|SetMouthW (select _init")
    txt_mal2 = txt[:i_m] + txt[i_a:i_b] + txt[i_m:i_a] + txt[i_b:]
    assert txt_mal2 != txt
    _, _, _, _, d4, _, _, _ = corrida(lambda t, dt: am.belly_target(t), int(36.0 * sb.FPS), texto=txt_mal2,
                                      solo=("LagA", "LagM", "LagR", "LagU"))
    chk("control negativo: mover SetMoveFade antes de los Set del marco cambia el marco en el giro (el simulador lo ve)",
        d4 > 1e-6, "max |marco| %.1e" % d4)


def valle():
    import valley_model as vm
    txt = open(os.path.join(AQUI, "valley_live.dsl"), encoding="utf-8").read()
    malos = lint_impuros(txt)
    chk("lint: ninguna funcion impura inline como argumento de datos en valley_live.dsl", not malos, "; ".join(malos))
    base = dict(bLive=True, LiveAmount=1.0, FogBreath=1.0, GlowBreath=1.0, ShadowBreath=1.0, WarmBreath=1.0,
                LiveTau=vm.LIVE_TAU, PreviewBreath=0.0, LiveS=0.0, LiveSig=0.0, LiveGate=0.0)
    suelo = set(vm.live_desde_S(0.0))
    cielo = set(vm.LIVE_CIELO)

    def comps():
        return {"Ground": Obj("Ground", params={}), "Sky": Obj("Sky", params={})}

    def compara(c, ref):
        """Ground recibe los 9 Live*, Sky solo los 3 del cielo; devuelve el error maximo."""
        if set(c["Ground"].params) != suelo or set(c["Sky"].params) != cielo:
            raise AssertionError("parametros empujados distintos: suelo %s cielo %s" % (sorted(c["Ground"].params), sorted(c["Sky"].params)))
        return max(max(abs(c["Ground"].params[k] - ref[k]) for k in suelo), max(abs(c["Sky"].params[k] - ref[k]) for k in cielo))

    # ---- PushLive(S) = live_desde_S, con familias al azar
    peor = 0.0
    rng = np.random.default_rng(1)
    for caso in range(300):
        g = dict(FogBreath=rng.uniform(0, 2), GlowBreath=rng.uniform(0, 2), ShadowBreath=rng.uniform(0, 2), WarmBreath=rng.uniform(0, 2))
        S = rng.uniform(-1.0, 1.0)
        c = comps()
        bp = BP(txt, dict(base, **g), c)
        bp.run_fn("PushLive", S=S)
        peor = max(peor, compara(c, vm.live_desde_S(S, Fog=g["FogBreath"], Glow=g["GlowBreath"], Shadow=g["ShadowBreath"], Warm=g["WarmBreath"])))
    chk("PushLive del DSL = valley_model.live_desde_S (300 casos; suelo 9 Live*, cielo solo LiveWarm/GlowAmt/GlowPow)",
        peor < 1e-12, "max |dif| %.1e" % peor)
    # ---- StepLive: S sigue a Signed x On x LiveAmount con LiveTau (live_paso), y empuja esa S
    peor = 0.0
    for caso in range(300):
        amt, S0 = rng.uniform(0, 1.2), rng.uniform(-1, 1)
        Sig, On, dt = rng.uniform(-1.2, 1.2), rng.uniform(0, 1), rng.uniform(0.005, 0.05)
        c = comps()
        bp = BP(txt, dict(base, LiveAmount=amt, LiveS=S0), c,
                extern={"LiveMPC": lambda b, s=Sig, o=On: b.v.update(LiveSig=s, LiveGate=o), "_dt": dt})
        bp.run_fn("StepLive")
        Sm = vm.live_paso(S0, max(-1.0, min(1.0, Sig)) * min(max(On * amt, 0.0), 1.0), dt)
        peor = max(peor, abs(bp.v["LiveS"] - Sm), compara(c, vm.live_desde_S(Sm)))
    chk("StepLive del DSL = live_paso + live_desde_S (300 casos: S previa, Signed, On, LiveAmount y DT al azar)",
        peor < 1e-12, "max |dif| %.1e" % peor)
    # ---- el Retire del rig: Signed y On caen a 0 en UN cuadro -> ningun Live* cambia mas de 1,5 % por cuadro
    c = comps()
    mpc = {"S": -1.0, "On": 1.0}
    bp = BP(txt, dict(base), c, extern={"LiveMPC": lambda b: b.v.update(LiveSig=mpc["S"], LiveGate=mpc["On"]), "_dt": 1.0 / 72.0})
    prev, dmax = None, 0.0
    for k in range(72 * 12):
        if k == 72 * 8:
            mpc["S"], mpc["On"] = 0.0, 0.0
        bp.run_fn("StepLive")
        now = dict(c["Ground"].params)
        if prev is not None and k >= 72 * 8 - 2:
            dmax = max(dmax, max(abs(now[kk] - prev[kk]) for kk in now))
        prev = now
    chk("escalon del Retire (Signed -1 -> 0 y On 1 -> 0 en un cuadro): ningun Live* cambia mas de 1,5 %% por cuadro (%.4f)" % dmax,
        dmax <= 0.015)
    # ---- neutros
    neutro = vm.live_desde_S(0.0)
    c = comps()
    bp = BP(txt, dict(base), c)
    bp.run_fn("PreviewLive")
    chk("PreviewLive con PreviewBreath 0 empuja los NEUTROS (= la v2 exacta)",
        compara(c, neutro) == 0.0 and all(neutro[k] == vm.P[k] for k in neutro))
    for pb in (-1.0, 1.0):
        c = comps()
        bp = BP(txt, dict(base, PreviewBreath=pb), c)
        bp.run_fn("PreviewLive")
        chk("PreviewLive con PreviewBreath %+g = live_desde_S(%+g), sin filtro" % (pb, pb), compara(c, vm.live_desde_S(pb)) < 1e-12)
    c = comps()
    bp = BP(txt, dict(base, bLive=False), c, extern={"LiveMPC": lambda b: b.v.update(LiveSig=1.0, LiveGate=1.0), "_dt": 1.0 / 72.0})
    for _ in range(10):
        bp.run_fn("StepLive")
    chk("bLive false: respirando a fondo igual empuja los neutros", compara(c, neutro) == 0.0)
    c = comps()
    bp = BP(txt, dict(base), c, extern={"LiveMPC": lambda b: b.v.update(LiveSig=-1.0, LiveGate=0.0), "_dt": 1.0 / 72.0})
    for _ in range(10):
        bp.run_fn("StepLive")
    chk("sin respiracion detectada (On 0): el valle queda en lo autoral", compara(c, neutro) == 0.0)
    # ---- control negativo: un signo cambiado en una rama de la curva TIENE que fallar
    txt_mal = txt.replace("(Math|Float|Lerp -0.35 -0.1 _u)", "(Math|Float|Lerp 0.35 -0.1 _u)", 1)
    assert txt_mal != txt
    c = comps()
    bp = BP(txt_mal, dict(base), c)
    bp.run_fn("PushLive", S=-1.0)
    chk("control negativo: un signo cambiado en HFogFall se detecta",
        abs(c["Ground"].params["LiveHFogFall"] - vm.live_desde_S(-1.0)["LiveHFogFall"]) > 1e-3)
    # ---- control negativo: sin el filtro (Set directo) el escalon del Retire SI salta
    txt_mal2 = re.sub(r"\(Variables\|L-Respira\|SetLiveS \(\+ \(Variables\|L-Respira\|GetLiveS\).*\n",
                      "(Variables|L-Respira|SetLiveS _tgt)\n", txt, count=1)
    assert txt_mal2 != txt
    c = comps()
    mpc = {"S": -1.0, "On": 1.0}
    bp = BP(txt_mal2, dict(base), c, extern={"LiveMPC": lambda b: b.v.update(LiveSig=mpc["S"], LiveGate=mpc["On"]), "_dt": 1.0 / 72.0})
    bp.run_fn("StepLive")
    a = dict(c["Ground"].params)
    mpc["S"], mpc["On"] = 0.0, 0.0
    bp.run_fn("StepLive")
    salto = max(abs(c["Ground"].params[k] - a[k]) for k in a)
    chk("control negativo: sin el filtro de StepLive el Retire salta en un cuadro (%.3f)" % salto, salto > 0.1)


if __name__ == "__main__":
    que = sys.argv[1:] or ["aire", "valle"]
    if "aire" in que:
        aire()
    if "valle" in que:
        valle()
    print("\n%s" % ("TODO OK" if not fallas else "%d FALLAS: %s" % (len(fallas), fallas)))
    sys.exit(1 if fallas else 0)
