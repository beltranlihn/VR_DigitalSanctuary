# -*- coding: utf-8 -*-
"""sim_vida.py - mediciones y previsualizaciones de la CAPA DE VIDA (polvo + rafagas) SIN Unreal (2026-09-28).

Todo sale de vida_model.py (verificado contra el HLSL por hlsl/Vida_check.py y contra el DSL por vida_dsl_sim.py) y del
valle de valley_model.py (el de preview_breath_valley.py, con el LOOK ACTUAL de Test_Entering).

Uso:
  python sim_vida.py medir      -> confort, legibilidad, agenda de 15 min y costo (imprime y escribe medidas.txt)
  python sim_vida.py linea      -> escribe preview/timeline.json: los estados que render_vida_valle.py tiene que dibujar
  (Blender)  render_vida_valle.py -- lee el timeline y dibuja el valle (con la franja de la rafaga) cuadro por cuadro
  python sim_vida.py componer   -> dibuja el polvo con su tamano angular REAL sobre esos cuadros: GIF + MP4 desde los
                                   ojos, cuadros clave rotulados, recortes x3 del polvo y el mapa de la franja
Salidas: VR_Test/Saved/ClaudeScripts/vida/ (preview/, medidas.txt, vida_rafaga.gif, vida_rafaga.mp4, vida_cuadros_clave.png,
         vida_polvo_detalle.png, vida_franja.png, vida_soplo.png)
"""
import json
import math
import os
import subprocess
import sys

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import vida_model as vm  # noqa: E402

SALIDA = os.path.abspath(os.path.join(AQUI, "..", "..", "..", "..", "VR_Test", "Saved", "ClaudeScripts", "vida"))
PREV = os.path.join(SALIDA, "preview")
LOOK = dict(FogStart=800.0, FogDist=20000.0, FogMax=0.93, HFogDist=15000.0, HFogFall=2500.0, MorphAmt=0.3)
T_VALLE0 = 40.0
CAM_GIF = dict(hfov=70.0, w=900, h=660, pitch=-3.0, yaw=0.0)
CAM_KEY = dict(hfov=90.0, w=1052, h=862, pitch=-2.0, yaw=0.0)
PXDEG_QUEST = 16.2        # 1680 px / ~104 grados (swapchain real del APK, gotcha 445)


def tabla(txt, lineas):
    print(txt)
    lineas.append(txt)


# ---------------------------------------------------------------------------------------------
# cosas comunes
# ---------------------------------------------------------------------------------------------
SD = vm.seeds()
ENC = vm.encode(SD)
CENT = {k: (v[::4] if isinstance(v, np.ndarray) and v.shape[0] == ENC["LP"].shape[0] else v) for k, v in ENC.items()}


def dust_centros(pv, camL=(0.0, 0.0, 0.0), game_time=0.0, mat=None):
    """el VS evaluado en el centro de cada mota (esquina 0: el centro se recupera exacto)."""
    return vm.dust_vs(CENT, pv, camL, mat, game_time=game_time)


def base_cam(cam):
    p, y = math.radians(cam["pitch"]), math.radians(cam["yaw"])
    F = np.array([math.cos(p) * math.cos(y), math.cos(p) * math.sin(y), math.sin(p)])
    R = np.array([-math.sin(y), math.cos(y), 0.0])
    U = np.cross(R, F)
    U = np.array([-math.sin(p) * math.cos(y), -math.sin(p) * math.sin(y), math.cos(p)])
    return F, R, U


def proyectar(P, cam):
    """P (n, 3) relativo al ojo (UE: x adelante, y derecha, z arriba) -> pixeles (x, y), profundidad."""
    F, R, U = base_cam(cam)
    z = P @ F
    f = (cam["w"] / 2.0) / math.tan(math.radians(cam["hfov"]) / 2.0)
    x = cam["w"] / 2.0 + (P @ R) / np.maximum(z, 1e-6) * f
    y = cam["h"] / 2.0 - (P @ U) / np.maximum(z, 1e-6) * f
    return x, y, z, f


# ---------------------------------------------------------------------------------------------
# MEDIR: confort, legibilidad, agenda, costo
# ---------------------------------------------------------------------------------------------
def medir():
    L = []
    tabla("=== CAPA DE VIDA: mediciones del modelo (vida_model.py = HLSL = DSL) ===", L)
    ojos = [np.array([0.0, -vm.IPD / 2, 0.0]), np.array([0.0, vm.IPD / 2, 0.0])]
    cam = dict(CAM_KEY)

    def en_vista(r, ojo=None):
        F, R, U = base_cam(dict(cam, hfov=104.0))
        Dn = r["Dn"]
        z = Dn @ F
        ax = np.degrees(np.arctan2(Dn @ R, z))
        ay = np.degrees(np.arctan2(Dn @ U, z))
        return (z > 0) & (np.abs(ax) < 52) & (np.abs(ay) < 48)

    def flujo(r, cam_):
        """velocidad angular 2D en la imagen (grados/s) de cada mota: la proyeccion de V perpendicular a la mirada."""
        F, R, U = base_cam(cam_)
        Dn, V, dist = r["Dn"], r["V"], r["dist"]
        vp = V - Dn * (V * Dn).sum(1)[:, None]
        return np.degrees(np.stack([vp @ R, vp @ U], 1) / dist[:, None])

    def resumen(tag, estados):
        vis_n, dmin, om_all, coh, cob, amax, cnt = [], [], [], [], [], 0.0, []
        cerca110, bino = 0, []
        for pv, gt in estados:
            rr = [dust_centros(pv, ojo, gt) for ojo in ojos]
            vv = ((rr[0]["al"] > 0.05) | (rr[1]["al"] > 0.05)) & (en_vista(rr[0], ojos[0]) | en_vista(rr[1], ojos[1]))
            if vv.any():
                dd_ = np.abs(rr[0]["al"] - rr[1]["al"]) / np.maximum(np.maximum(rr[0]["al"], rr[1]["al"]), 1e-6)
                bino.append(float(dd_[vv].max()))
            for r in rr:
                cerca110 += int(((r["al"] > 0.002) & (r["dist"] < 110.0)).sum())
            for ojo in ojos:
                r = dust_centros(pv, ojo, gt)
                v = (r["al"] > 0.02)
                iv = v & en_vista(r, ojo)
                cnt.append(int(((r["al"] > 0.05) & en_vista(r, ojo)).sum()))
                if v.any():
                    dmin.append(float(r["dist"][v].min()))
                    om_all.append(r["om"][iv])
                    fl = flujo(r, cam)[iv]
                    w = r["al"][iv]
                    if w.sum() > 0:
                        media = (fl * w[:, None]).sum(0) / w.sum()
                        mag = (np.linalg.norm(fl, axis=1) * w).sum() / w.sum()
                        coh.append((float(np.linalg.norm(media)), float(mag)))
                    amax = max(amax, float(r["al"].max()))
                # cobertura del buffer del ojo (px del Quest): area del sprite x perfil medio (1-r^2)^2 ~ 0,33
                lado = 2.0 * np.degrees(np.arctan(r["hsz"] / r["dist"])) * PXDEG_QUEST
                cob.append(float((lado[iv] ** 2).sum()) / (1680.0 * 1760.0))
                vis_n.append(int(iv.sum()))
        om = np.concatenate(om_all) if om_all else np.zeros(1)
        cm = np.array(coh) if coh else np.zeros((1, 2))
        tabla("%-26s visibles en vista (alfa > 0,05) %4.0f (%d-%d) | mas cercana %.0f cm | alfa max %.2f | vel. angular p50 %.2f "
              "p90 %.2f p99 %.2f max %.2f grados/s | flujo COHERENTE (media vectorial) %.2f grados/s de %.2f | cobertura %.2f %% del ojo"
              " | motas visibles a < 110 cm de un ojo (el volumen del aliento): %d | alfa distinto entre ojos (max relativo): %.2f"
              % (tag, np.mean(cnt), min(cnt), max(cnt), min(dmin) if dmin else float("nan"), amax, np.percentile(om, 50),
                 np.percentile(om, 90), np.percentile(om, 99), om.max(), cm[:, 0].max(), cm[:, 1].max(), 100 * max(cob),
                 cerca110, max(bino) if bino else 0.0), L)
        return om

    # calma: 60 s de meandro (con el punto ciclopeo, como en el juego: la camara del rig entre los ojos)
    CAM = dict(cam=vm.ACTOR)
    bp = vm.VidaBP(**CAM)
    bp.Glob = 1.0
    calma = []
    for t in np.linspace(0, 60, 13):
        bp.Tm = t
        calma.append((bp.push_dust(), 0.0))
    resumen("calma", calma)
    # la velocidad angular PROPIA del polvo en calma por distancia (rev. 2: el meandro crece lejos, nada queda congelado)
    r = dust_centros(calma[3][0], (0.0, 0.0, 0.0))
    vis = (r["al"] > 0.05) & en_vista(r, None)
    bandas = []
    for a, b in ((130, 300), (300, 1000), (1000, 2000), (2000, 4000)):
        m = vis & (r["distC"] >= a) & (r["distC"] < b)
        bandas.append("%g-%g m: %d motas, p50 %.3f grados/s" % (a / 100.0, b / 100.0, int(m.sum()),
                                                                np.percentile(r["om"][m], 50) if m.any() else float("nan")))
    tabla("calma, velocidad angular propia por distancia: " + " | ".join(bandas), L)
    # rafaga lateral: el frente recorre todo el camino
    bp = vm.VidaBP(**CAM)
    bp.Glob = 1.0
    bp.start_lateral()
    lat = []
    for fr in np.linspace(0, 1, 25):
        bp.S = bp.S0 + (bp.S1 - bp.S0) * fr
        bp.Tm = fr * bp.Life
        bp.Rate = 1.0 + vm.BP["GustStir"] * vm.gust_act((bp.actor.loc + bp.actor.axes()[0] * vm.PROBE_FWD)[:2], bp.gust())
        lat.append((bp.push_dust(), 0.0))
    resumen("rafaga lateral (entera)", lat)
    bp.S = 0.0
    bp.Rate = 1.0 + vm.BP["GustStir"]
    resumen("rafaga lateral (en el pico)", [(bp.push_dust(), 0.0)])
    # la relajacion: la deriva vuelve a su lugar (Hold 1 -> 0 en DriftRelax s)
    bp.S = bp.S1
    bp.Rate = 1.0
    rel = []
    T_rel = vm.BP["DriftRelax"]
    for ph in np.linspace(0, 1, 13):
        bp.Hold = 1.0 - ph ** 3 * (ph * (6 * ph - 15) + 10)
        bp.HoldV = -30.0 * ph * ph * (1 - ph) * (1 - ph) / T_rel
        rel.append((bp.push_dust(), 0.0))
    resumen("relajacion de la deriva", rel)
    bp.Hold = 1.0
    bp.HoldV = 0.0
    dcor = np.linalg.norm(dust_centros(bp.push_dust())["G"], axis=1)
    tabla("deriva al terminar el frente (lo que el viento se llevo): p50 %.0f cm, p90 %.0f cm, max %.0f cm"
          % (np.percentile(dcor[dcor > 0.1], 50), np.percentile(dcor[dcor > 0.1], 90), dcor.max()), L)
    # soplo
    bp = vm.VidaBP(**CAM)
    bp.Glob = 1.0
    bp.start_breath()
    sop = []
    for fr in np.linspace(0, 1, 25):
        bp.S = bp.S0 + (bp.S1 - bp.S0) * fr
        bp.Rate = 1.0 + vm.BP["GustStir"] * vm.gust_act((bp.actor.loc + bp.actor.axes()[0] * vm.PROBE_FWD)[:2], bp.gust())
        sop.append((bp.push_dust(), 0.0))
    resumen("soplo (entero)", sop)

    # ---- la franja en el llano: contraste y velocidad angular (modelo del valle con el look actual)
    tabla("--- la franja de la rafaga en el llano (valley_model con el look actual, ojos a 2,10 m del piso) ---", L)
    import valley_model as vl
    q = vl.params(**LOOK)
    eye = np.array([0.0, 0.0, 120.0 - vm.VALLE_Z])
    for tipo in ("lateral", "soplo"):
        bp = vm.VidaBP()
        (bp.start_lateral if tipo == "lateral" else bp.start_breath)()
        # grilla polar del llano (coordenadas del valle); se sigue la CRESTA de la franja (el punto de mayor cambio de
        # luminancia) cuadro a cuadro y se mide su velocidad angular EN LA VISTA (azimut y elevacion) mientras se ve
        az = np.radians(np.arange(-70.0, 70.01, 1.0))
        rr = 1500.0 * np.power(20000.0 / 1500.0, np.linspace(0.0, 1.0, 70))
        X = rr[:, None] * np.cos(az)[None, :]
        Y = rr[:, None] * np.sin(az)[None, :]
        gx, gy, h, hf = vl.valley_grad(X.ravel(), Y.ravel(), T_VALLE0, q)
        G = np.stack([gx, gy, h, hf], 1)
        base = vl.suelo(X.ravel(), Y.ravel(), gx, gy, h, hf, eye, q)
        b8 = np.array([vl.srgb8(c) for c in base]).mean(1).reshape(X.shape)
        el = np.degrees(np.arctan2(h.reshape(X.shape) - eye[2], rr[:, None]))
        azd = np.degrees(np.broadcast_to(az[None, :], X.shape))
        # el metaball (radio de referencia 110 cm a 3,8 m) TAPA lo que queda dentro de su disco: no cuenta como visible
        el_soul = math.degrees(math.atan2(125.0 - 120.0, 380.0))
        tapado = np.hypot(azd, el - el_soul) < math.degrees(math.asin(110.0 / 380.0))
        fr_s = np.linspace(0, 1, 89)
        dt = (bp.S1 - bp.S0) / bp.Sdot / (len(fr_s) - 1)
        prev = None
        prevI = None
        dmax, v_all, vn_all, vn_w, el_vis = 0.0, [], [], [], []
        # malla de angulos de la vista (grados) para el flujo NORMAL del patron de luz: v_n = -dI/dt / |grad I|
        daz = np.gradient(azd, axis=1)
        delr = np.gradient(el, axis=0)
        for fr in fr_s:
            bp.S = bp.S0 + (bp.S1 - bp.S0) * fr
            pvv = bp.push_valley()
            G2 = vm.gust_lean_vs(G, np.stack([X.ravel(), Y.ravel(), np.zeros(X.size)], 1), 0.0, pvv)
            c = vl.suelo(X.ravel(), Y.ravel(), G2[:, 0], G2[:, 1], G2[:, 2], G2[:, 3], eye, q)
            lin = c.reshape(X.shape + (3,)).mean(2)
            d8 = np.array([vl.srgb8(cc) for cc in c]).mean(1).reshape(X.shape) - b8
            d8[tapado] = 0.0
            dmax = max(dmax, float(np.abs(d8).max()))
            if np.abs(d8).max() >= 3.0:
                el_vis.append(el[np.abs(d8) >= 3.0])
            I = vl.srgb(lin) * 255.0
            if prevI is not None:
                gi_a = np.gradient(I, axis=1) / np.where(np.abs(daz) > 1e-9, daz, 1e-9)
                gi_e = np.gradient(I, axis=0) / np.where(np.abs(delr) > 1e-9, delr, 1e-9)
                gm = np.sqrt(gi_a ** 2 + gi_e ** 2)
                It = (I - prevI) / dt
                m = (gm > 0.3) & (np.abs(It) > 0.2) & (np.abs(azd) < 52) & ~tapado
                if m.any():
                    vn_all.append(np.abs(It[m]) / gm[m])
                    vn_w.append(np.abs(It[m]))
            prevI = I
            # la CRESTA de la franja (rev. 2; el centroide de la rev. 1 saltaba cuando la franja crecia desde los costados o
            # entraba/salia de detras del metaball: su "p90 26,7" no era movimiento). La lateral cruza en AZIMUT: por cada
            # anillo (fila) el azimut del maximo; el soplo se aleja en ELEVACION: por cada columna la elevacion del maximo.
            # Solo cuenta si la cresta existe (>= 3 niveles) en los dos cuadros y se movio poco (la misma cresta).
            A = np.abs(d8)

            def cresta(Am, coord):
                """por fila: la posicion del maximo refinada con el centroide local (+-4 muestras) -> sin cuantizar a 1 grado"""
                out = np.full(Am.shape[0], np.nan)
                for i_ in range(Am.shape[0]):
                    j_ = int(Am[i_].argmax())
                    if Am[i_, j_] < 3.0:
                        continue
                    a_, b_ = max(j_ - 4, 0), min(j_ + 5, Am.shape[1])
                    w_ = np.clip(Am[i_, a_:b_] - 0.5 * Am[i_, j_], 0.0, None)
                    out[i_] = float((coord[i_, a_:b_] * w_).sum() / max(w_.sum(), 1e-9))
                return out
            cr = cresta(A, azd) if tipo == "lateral" else cresta(A.T, el.T)
            if prev is not None:
                dcr = np.abs(cr - prev)
                ok_ = np.isfinite(dcr) & (dcr < 5.0)
                v_all.extend((dcr[ok_] / dt).tolist())
            prev = cr
        v_all = np.array(v_all) if v_all else np.zeros(1)
        vn = np.concatenate(vn_all)
        wn = np.concatenate(vn_w)
        o = np.argsort(vn)
        cw = np.cumsum(wn[o]) / wn.sum()
        pct = lambda p: float(vn[o][np.searchsorted(cw, p)])
        ev = np.concatenate(el_vis) if el_vis else np.zeros(1)
        tabla("%-8s contraste max %+.1f niveles (8 bits, FUERA del disco del metaball) | elevacion de lo visible (>= 3 niveles): "
              "%.1f a %.1f grados (p10-p90) | FLUJO NORMAL del patron de luz (ponderado por cuanto cambia): "
              "p50 %.1f, p90 %.1f, p99 %.1f grados/s | la CRESTA visible (%s, %d muestras): "
              "mediana %.1f, p90 %.1f grados/s"
              % (tipo, dmax, np.percentile(ev, 10), np.percentile(ev, 90), pct(0.5), pct(0.9), pct(0.99),
                 "en azimut" if tipo == "lateral" else "en elevacion", len(v_all),
                 np.median(v_all), np.percentile(v_all, 90)), L)

    # ---- la agenda de 15 minutos, respirando y sin respirar
    tabla("--- agenda de rafagas, 15 min ---", L)
    for tag, on in (("respirando 4-3-4-3", 1.0), ("sin respiracion detectada", 0.0)):
        bp = vm.VidaBP()
        dt = 1.0 / 72.0
        activo = 0
        for i in range(int(900 / dt)):
            t = i * dt
            bp.step(dt, vm.belly(t), on)
            activo += int(bp.bGustOn)
        ts = [s[0] for s in bp.sounds]
        tipos = [s[1] for s in bp.sounds]
        iv = np.diff(ts)
        tabla("%-26s %d rafagas (%d soplos) | entre comienzos: %.0f-%.0f s (media %.0f) | con rafaga el %.0f %% del tiempo"
              % (tag, len(ts), sum(tipos), iv.min(), iv.max(), iv.mean(), 100.0 * activo * dt / 900.0), L)

    # ---- costo
    tabla("--- costo (estimado; se mide con el banco) ---", L)
    txt = open(os.path.join(AQUI, "hlsl", "DustVS.hlsl"), encoding="ascii").read()
    cuerpo = "\n".join(l for l in txt.split("\n") if not l.lstrip().startswith("//"))
    ops = len([c for c in cuerpo if c in "+-*/"]) + 8 * sum(cuerpo.count(f) for f in ("sin(", "cos(", "pow(", "asin(", "acos(", "tan(", "sqrt(", "normalize(", "length("))
    nverts = ENC["LP"].shape[0]
    inv = nverts * 3        # dos vistas (multiview) + el binning, que re-ejecuta la posicion (gotcha 454)
    tabla("DustVS: ~%d op-eq por vertice (con la rama de la rafaga; conteo grueso del codigo) x %d vertices x 3 (dos ojos + "
          "binning) = %.1f M op-eq por cuadro -> 0,03-0,09 ms (el aliento: 4,6 M op-eq -> 0,025-0,05 ms estimados)"
          % (ops, nverts, ops * inv / 1e6), L)
    tabla("DustPS: cobertura max ~0,20 % del ojo (tabla de arriba) x ~12 op-eq x 3 (quads chicos) -> < 0,005 ms", L)
    tabla("GustLeanVS: 21.601 vertices del valle x 2-3 x ~45 op-eq con rafaga (rama uniforme: 0 sin rafaga) = ~2,9 M op-eq -> ~0,005-0,01 ms", L)
    tabla("CPU (Blueprint): VidaTick ~300-400 nodos por cuadro + 12 vectores a dos MIDs -> 0,1-0,25 ms de hilo de juego, sin medir", L)
    open(os.path.join(SALIDA, "medidas.txt"), "w", encoding="utf-8").write("\n".join(L) + "\n")


# ---------------------------------------------------------------------------------------------
# LINEA DE TIEMPO para el render del valle
# ---------------------------------------------------------------------------------------------
def escenario_lateral(fps=5.0, antes=2.5, despues=8.0):
    """Una rafaga lateral con las perillas por defecto, desde los ojos. Devuelve una lista de (t, pv_polvo, pv_valle)."""
    bp = vm.VidaBP(bp=dict(FirstGap=antes))
    dt = 1.0 / 72.0
    out = []
    total = antes + vm.BP["GustLife"] + despues
    sig = int(round(72.0 / fps))
    for i in range(int(total / dt) + 1):
        t = i * dt
        bp.step(dt, 0.0, 0.0)
        if i < 72 * 3:
            bp.GlobBase = bp.Glob = 1.0        # el polvo ya presente (sin el fundido de entrada del BeginPlay)
        if i % sig == 0:
            fase = "rafaga" if bp.bGustOn else ("relaja" if bp.Hold > 0.0 else "calma")
            out.append((t, bp.push_dust(), bp.push_valley(), fase, bp.S))
    return out


def linea():
    os.makedirs(PREV, exist_ok=True)
    fr = []
    for i, (t, pd, pvv, on, s) in enumerate(escenario_lateral()):
        fr.append(dict(id="gif_%03d" % i, t=T_VALLE0 + t, pv={k: list(map(float, v)) for k, v in pvv.items()}, cam=CAM_GIF))
    # cuadros clave (90 grados): calma, entra, pasa, se va; y el soplo
    bp = vm.VidaBP()
    bp.start_lateral()
    claves = [("clave_calma", None)]
    for nombre, s in (("clave_entra", -2600.0), ("clave_pasa", 0.0), ("clave_sale", 2600.0)):
        claves.append((nombre, s))
    for nombre, s in claves:
        if s is None:
            pvv = {k: list(v) for k, v in vm.GUST_MAT.items()}
        else:
            bp.S = s
            pvv = {k: list(map(float, v)) for k, v in bp.push_valley().items()}
        fr.append(dict(id=nombre, t=T_VALLE0 + 12.0, pv=pvv, cam=CAM_KEY))
    bp = vm.VidaBP()
    bp.start_breath()
    for nombre, s in (("soplo_1", 400.0), ("soplo_2", 3000.0), ("soplo_3", 5000.0)):
        bp.S = s
        fr.append(dict(id=nombre, t=T_VALLE0 + 12.0, pv={k: list(map(float, v)) for k, v in bp.push_valley().items()}, cam=CAM_KEY))
    json.dump(dict(look=LOOK, valleZ=vm.VALLE_Z, frames=fr), open(os.path.join(PREV, "timeline.json"), "w"), indent=0)
    print("timeline: %d cuadros -> %s" % (len(fr), os.path.join(PREV, "timeline.json")))


# ---------------------------------------------------------------------------------------------
# COMPONER: el polvo sobre los cuadros del valle
# ---------------------------------------------------------------------------------------------
def srgb_a_lin(c):
    c = np.asarray(c, dtype=np.float64)
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def lin_a_srgb(c):
    c = np.clip(c, 0.0, 1.0)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * np.power(c, 1.0 / 2.4) - 0.055)


def dibujar_polvo(img_lin, r, cam, sub=4):
    """splat de cada mota: el quad del VS (lado 2 hsz, mirando al ojo) con el perfil del PS (1 - r^2)^2, premultiplicado
    y compuesto en LINEAL (como el Quest: r.MobileHDR False, mezcla en lineal)."""
    col_lit, col_dim = np.array(vm.MAT["ColLit"]), np.array(vm.MAT["ColDim"])
    x, y, z, f = proyectar(r["P"], cam)
    h, w = img_lin.shape[:2]
    orden = np.argsort(-z)          # de lejos a cerca
    n = 0
    for i in orden:
        a0 = r["al"][i]
        if a0 < 0.002 or z[i] <= 1.0:
            continue
        hs = r["hsz"][i] / z[i] * f
        cx, cy = x[i], y[i]
        if cx < -5 or cy < -5 or cx > w + 5 or cy > h + 5:
            continue
        x0, x1 = int(math.floor(cx - hs)), int(math.ceil(cx + hs))
        y0, y1 = int(math.floor(cy - hs)), int(math.ceil(cy + hs))
        x0, y0 = max(x0, 0), max(y0, 0)
        x1, y1 = min(x1, w - 1), min(y1, h - 1)
        if x1 < x0 or y1 < y0:
            continue
        gx = x0 + (np.arange((x1 - x0 + 1) * sub) + 0.5) / sub
        gy = y0 + (np.arange((y1 - y0 + 1) * sub) + 0.5) / sub
        U, V = np.meshgrid((gx - cx) / max(hs, 1e-6), (gy - cy) / max(hs, 1e-6))
        m = np.clip(1.0 - (U * U + V * V), 0.0, 1.0) ** 2
        a = np.clip(m * a0, 0.0, 1.0)
        a = a.reshape(y1 - y0 + 1, sub, x1 - x0 + 1, sub).mean(axis=(1, 3))
        col = col_dim + (col_lit - col_dim) * min(max(r["hgn"][i], 0.0), 1.0)
        reg = img_lin[y0:y1 + 1, x0:x1 + 1]
        img_lin[y0:y1 + 1, x0:x1 + 1] = col[None, None, :] * a[..., None] + reg * (1.0 - a[..., None])
        n += 1
    return n


def cargar(id_):
    from PIL import Image
    p = os.path.join(PREV, id_ + ".png")
    return srgb_a_lin(np.asarray(Image.open(p).convert("RGB"), dtype=np.float64) / 255.0)


def a_imagen(lin):
    from PIL import Image
    return Image.fromarray(np.round(lin_a_srgb(lin) * 255.0).astype(np.uint8))


def rotular(im, texto, sub=None):
    from PIL import ImageDraw, ImageFont
    d = ImageDraw.Draw(im)
    try:
        fnt = ImageFont.truetype("arial.ttf", 17)
        fns = ImageFont.truetype("arial.ttf", 13)
    except Exception:  # noqa: BLE001
        fnt = fns = ImageFont.load_default()
    d.rectangle([0, 0, im.width, 26 + (18 if sub else 0)], fill=(20, 22, 40))
    d.text((10, 4), texto, fill=(235, 235, 245), font=fnt)
    if sub:
        d.text((10, 26), sub, fill=(190, 190, 215), font=fns)
    return im


def componer():
    from PIL import Image
    tl = json.load(open(os.path.join(PREV, "timeline.json")))
    frames = {f["id"]: f for f in tl["frames"]}
    # ---- GIF / MP4: la rafaga lateral desde los ojos
    esc = escenario_lateral()
    gif = []
    os.makedirs(os.path.join(PREV, "mp4"), exist_ok=True)
    for i, (t, pd, pvv, on, s) in enumerate(esc):
        img = cargar("gif_%03d" % i)
        r = dust_centros(pd, (0.0, 0.0, 0.0))
        dibujar_polvo(img, r, CAM_GIF)
        im = a_imagen(img)
        estado = {"rafaga": "rafaga: el frente a %+.0f m del usuario" % (s / 100.0),
                  "relaja": "paso el viento: el polvo vuelve despacio a su lugar", "calma": "calma"}[on]
        rotular(im, "Entering, desde los ojos (70 grados) - t = %4.1f s - %s" % (t, estado),
                "polvo suspendido + franja de la rafaga (sin el metaball real: la esfera es de referencia)")
        im.save(os.path.join(PREV, "mp4", "f_%03d.png" % i))
        gif.append(im.resize((720, int(720 * im.height / im.width)), Image.LANCZOS))
    gif[0].save(os.path.join(SALIDA, "vida_rafaga.gif"), save_all=True, append_images=gif[1:], duration=200, loop=0,
                optimize=True)
    try:
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "5", "-i", os.path.join(PREV, "mp4", "f_%03d.png"),
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "16", os.path.join(SALIDA, "vida_rafaga.mp4")], check=True)
    except Exception as e:  # noqa: BLE001
        print("sin mp4:", e)
    # ---- cuadros clave (90 grados) con el polvo en el estado de la rafaga correspondiente
    bp = vm.VidaBP()
    bp.Glob = 1.0
    bp.start_lateral()
    textos = {"clave_calma": ("1. Calma", "polvo suspendido: motas a 1,3-26 m (fuera del aliento), doradas contra la luz baja (derecha)"),
              "clave_entra": ("2. La rafaga entra (frente a 26 m a la izquierda)", "la franja aparece en el llano izquierdo"),
              "clave_pasa": ("3. Pasa por el usuario", "el polvo se enciende y hace su lazo; la franja cruza el llano de enfrente"),
              "clave_sale": ("4. Se va (frente a 26 m a la derecha)", "el polvo quedo corrido a favor del viento (vuelve en ~25 s); la franja se aleja")}
    tiles = []
    for id_, (tt, sub) in textos.items():
        img = cargar(id_)
        if id_ == "clave_calma":
            bp2 = vm.VidaBP()
            bp2.Glob = 1.0
            pd = bp2.push_dust()
        else:
            bp.S = {"clave_entra": -2600.0, "clave_pasa": 0.0, "clave_sale": 2600.0}[id_]
            bp.Rate = 1.0 + vm.BP["GustStir"] * vm.gust_act((bp.actor.loc + bp.actor.axes()[0] * vm.PROBE_FWD)[:2], bp.gust())
            bp.Tm = 7.0
            pd = bp.push_dust()
        r = dust_centros(pd)
        dibujar_polvo(img, r, CAM_KEY)
        tiles.append(rotular(a_imagen(img), tt, sub))
    w, h = tiles[0].size
    hoja = Image.new("RGB", (2 * w, 2 * h))
    for k, t in enumerate(tiles):
        hoja.paste(t, ((k % 2) * w, (k // 2) * h))
    hoja.save(os.path.join(SALIDA, "vida_cuadros_clave.png"))
    # ---- el soplo (3 momentos)
    bps = vm.VidaBP()
    bps.Glob = 1.0
    bps.start_breath()
    ts = []
    for id_, tt in (("soplo_1", "Soplo: exhala -> el aire se mueve delante (frente a 4 m)"),
                    ("soplo_2", "Soplo: la franja sale hacia el horizonte (frente a 30 m)"),
                    ("soplo_3", "Soplo: se aleja (frente a 50 m)")):
        img = cargar(id_)
        bps.S = {"soplo_1": 400.0, "soplo_2": 3000.0, "soplo_3": 5000.0}[id_]
        bps.Rate = 1.0 + vm.BP["GustStir"] * vm.gust_act((bps.actor.loc + bps.actor.axes()[0] * vm.PROBE_FWD)[:2], bps.gust())
        r = dust_centros(bps.push_dust())
        dibujar_polvo(img, r, CAM_KEY)
        ts.append(rotular(a_imagen(img), tt).resize((w * 2 // 3, h * 2 // 3), Image.LANCZOS))
    hs = Image.new("RGB", (3 * ts[0].width, ts[0].height))
    for k, t in enumerate(ts):
        hs.paste(t, (k * ts[0].width, 0))
    hs.save(os.path.join(SALIDA, "vida_soplo.png"))
    # ---- la franja sola: diferencia con la calma, x8
    base = cargar("clave_calma")
    fr = []
    for id_ in ("clave_entra", "clave_pasa", "clave_sale"):
        d = np.abs(lin_a_srgb(cargar(id_)) - lin_a_srgb(base)).mean(2) * 255.0
        g = np.clip(d * 8.0 / 255.0, 0, 1)
        im = a_imagen(np.repeat(srgb_a_lin(g)[..., None], 3, axis=2))
        rotular(im, "%s: |rafaga - calma| x8 (max %.1f niveles)" % (id_.split("_")[1], d.max()))
        fr.append(im.resize((w // 2, h // 2), Image.LANCZOS))
    hf = Image.new("RGB", (3 * fr[0].width, fr[0].height))
    for k, t in enumerate(fr):
        hf.paste(t, (k * fr[0].width, 0))
    hf.save(os.path.join(SALIDA, "vida_franja.png"))
    # ---- detalle del polvo: recortes x3 (calma y pico) alrededor del sol bajo y de la zona cercana
    det = []
    for tag, s in (("calma", None), ("pico de la rafaga", 0.0)):
        img = cargar("clave_calma" if s is None else "clave_pasa")
        b3 = vm.VidaBP()
        b3.Glob = 1.0
        if s is not None:
            b3.start_lateral()
            b3.S = s
            b3.Rate = 1.0 + vm.BP["GustStir"]
            b3.Tm = 7.0
        r = dust_centros(b3.push_dust())
        dibujar_polvo(img, r, CAM_KEY)
        im = a_imagen(img)
        for (x0, y0) in ((600, 250), (300, 520)):
            c = im.crop((x0, y0, x0 + 260, y0 + 180)).resize((780, 540), Image.NEAREST)
            rotular(c, "%s - recorte x3 (%d, %d)" % (tag, x0, y0), "1 px del recorte = 1 px de un render de 11,7 px/grado (el visor tiene ~16)")
            det.append(c)
    hd = Image.new("RGB", (2 * det[0].width, 2 * det[0].height))
    for k, t in enumerate(det):
        hd.paste(t, ((k % 2) * det[0].width, (k // 2) * det[0].height))
    hd.save(os.path.join(SALIDA, "vida_polvo_detalle.png"))
    print("compuesto: vida_rafaga.gif/.mp4, vida_cuadros_clave.png, vida_soplo.png, vida_franja.png, vida_polvo_detalle.png")


if __name__ == "__main__":
    que = sys.argv[1] if len(sys.argv) > 1 else "medir"
    {"medir": medir, "linea": linea, "componer": componer}[que]()
