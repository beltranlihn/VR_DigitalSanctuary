# -*- coding: utf-8 -*-
"""preview_breath_valley.py - previsualiza el valle de la respiracion (Entering), v2 (revision 2026-09-28), en
Blender headless, SIN Unreal. Especificacion: docs/PLAN-VALLE-ENTERING-2026-09-27.md.

QUE HACE
  1. Construye la malla real (reusa construir() de gen_breath_valley.py: misma topologia, mismos radios) y le
     aplica la ALTURA del modelo de referencia (valley_model.py = la cuenta de los tres Custom) en cada vertice.
  2. Colorea cada vertice con el sombreado de ValleyPS (suelo) evaluado para la camara de CADA vista, con la
     sombra falsa del metaball y la niebla. El cielo es una esfera de 900 m con el color de ValleyPS (cielo).
     El color se interpola entre vertices (Gouraud); en el GPU se interpola el gradiente y el color sale por
     pixel. Con celdas de ~2 grados la diferencia es chica, pero el juicio fino de sombreado es el render por
     pixel del modelo o el visor.
  3. Pone una esfera blanca de 1,1 m de radio en el lugar del metaball (380, 0, 125 cm) con un sombreado
     envolvente simple (solo para ubicar la masa: NO es el metaball real).
  4. Renderiza con Workbench (luz FLAT + color de vertice, vista 'Standard' = sin tonemapper, como el APK).
  5. Antes de renderizar CONTROLA el modelo contra valores de la seccion 12 y mide: silueta sobre el horizonte
     (720 azimuts), margen del borde de la malla, piso quieto, velocidad de la silueta (y su sube y baja en toda la
     vuelta y en ventanas de 90 grados) y la cota rigurosa de la velocidad vertical (oleaje + respiracion).
     Todo se imprime con el prefijo PREVIEW.

EJES. La especificacion usa los ejes de Unreal (X adelante, Y DERECHA, Z arriba; mano izquierda). Blender es de
mano derecha: un punto UE (x, y, z) cm va a Blender como (x, -y, z)/100 m, asi la imagen no sale espejada.

SALIDAS (VR_Test/Saved/ClaudeScripts/), <tag> = sufijo:
  preview_valle_t0<tag>.png / preview_valle_t5<tag>.png  1052x862, vista del usuario (0,0,120), yaw 0, pitch -2,
                                                          HFOV 90 (= cap_valle_frente.png), en t0 y t0 + dt
  preview_valle_dif<tag>.png                              |t5 - t0|: arriba la diferencia x12 en gris, abajo en
                                                          rojo sobre la vista t0 apagada
  preview_valle_lado<tag>.png                             1052x862, camara (380,-700,70), yaw 90, pitch 0, HFOV 90
                                                          (= cap_exhala_lado.png)
  preview_valle_vuelta_t0<tag>.png                        1920x360, 4 vistas de 90 (atras, izq, frente, der)
  preview_valle_cenital_t0<tag>.png                       1024x1024 planta de TODO el disco (1280 m), color por
                                                          altura (casi negro = h 0 exacto; azul -> blanco = 0 ->
                                                          80 m; violeta = valles del oleaje hasta -15 m);
                                                          y ..._cenital_zoom_t0<tag>.png, +-120 m

USO (headless, no toca la sesion de Blender del usuario):
  "C:\\Program Files\\Blender Foundation\\Blender 5.2\\blender.exe" --background --factory-startup --python preview_breath_valley.py -- tag=_v2
  Capa viva (2026-09-28): respira=<S> (-1 exhalado .. +1 inhalado; 0 = la v2 exacta, con los controles de la seccion
  12) aplica live_desde_S + efectivos del modelo (docs/PLAN-RESPIRACION-ENTORNO-2026-09-28.md); carpeta=<ruta>
  cambia la carpeta de salida.
  Perillas: despues de "--", pares clave=valor que pisan los defaults de la tabla 7.1 (los vectores van como
  0.4,0.5,0.8), mas estas opciones de escena:
    tag=<sufijo>   sufijo de los archivos              t0=<s>   instante base (0 por defecto)
    dt=<s>         segundo instante = t0 + dt (5)       solo=principal  solo t0, t5 y la diferencia
    mbR=<cm>       radio de la esfera de referencia (110)
    valleZ=<cm>    altura del ACTOR del valle (-50 = el piso baja 50 cm; ojos y metaball quedan donde estan,
                   asi que en local suben y ShadowCenter local sube con ellos)
  Con perillas pisadas, los controles de la seccion 12 se saltean (valen solo con los defaults).
"""
import math
import os
import sys

import bpy
import numpy as np
from mathutils import Euler, Vector

AQUI = os.path.dirname(os.path.abspath(__file__))
if AQUI not in sys.path:
    sys.path.insert(0, AQUI)
import gen_breath_valley as gen  # noqa: E402  (misma malla que el FBX)
import valley_model as vm  # noqa: E402  (la misma cuenta que los tres Custom)

SALIDA = os.path.abspath(os.path.join(AQUI, "..", "..", "..", "..", "VR_Test", "Saved", "ClaudeScripts"))
P = vm.params()
OJOS_DEF = np.array([0.0, 0.0, 120.0])      # cm, usuario sentado en el origen (camara de la seccion 12)
OJOS = OJOS_DEF.copy()                      # en coordenadas LOCALES del valle (cambia con valleZ)
METABALL = np.array([380.0, 0.0, 125.0])    # cm, centro del metaball (local)
METABALL_RADIO = 110.0                      # cm, esfera de referencia (~2,2 m de tamano)
CIELO_RADIO = 90000.0                       # cm, esfera del cielo del preview (fuera de todo el terreno: 640 m)
OPCIONES_ESCENA = ("tag", "t0", "dt", "solo", "valleZ", "mbR", "respira", "carpeta")


def leer_argumentos():
    opts = {"tag": "", "t0": 0.0, "dt": 5.0, "solo": "", "valleZ": 0.0, "mbR": METABALL_RADIO, "respira": 0.0, "carpeta": ""}
    pisadas = False
    if "--" not in sys.argv:
        return opts, pisadas
    for par in sys.argv[sys.argv.index("--") + 1:]:
        if "=" not in par:
            continue
        k, v = par.split("=", 1)
        if k in opts:
            opts[k] = v if k in ("tag", "solo", "carpeta") else float(v)
            print("PREVIEW opcion %s = %s" % (k, opts[k]))
        elif k in P:
            P[k] = tuple(float(c) for c in v.split(",")) if isinstance(P[k], tuple) else float(v)
            pisadas = True
            print("PREVIEW perilla %s = %s" % (k, P[k]))
        else:
            print("PREVIEW (ignorado) %s" % par)
    return opts, pisadas


# ---------------------------------------------------------------------------------------------
# Controles contra la seccion 12 (el modelo es la referencia; esto asegura que el preview use la spec vigente)
# ---------------------------------------------------------------------------------------------
CONTROL_ALTURA = (  # (x, y, t, h, dh/dx, dh/dy, hf)
    (0, 0, 0, 0.000, 0.0, 0.0, 0.0),
    (1300, -700, 30, 0.000, 0.0, 0.0, 0.0),
    (3000, 1200, 0, 0.000, 0.025176, 0.048426, 0.000000),
    (-9000, 6000, 45.5, 374.301, -0.345389, 0.087435, 0.170137),
    (21000, -12000, 120, 0.000, 0.033414, 0.085065, 0.000000),
    (26400, 23800, 120, -124.940, 0.030688, 0.014694, 0.007105),
    (-30000, -20000, 300, 2001.182, -0.201757, -0.451845, 0.177124),
    (46000, 9000, 600, 3524.110, -0.008876, -0.579483, 0.324981),
    (60000, 10000, 0, 0.000, 0.0, 0.0, 0.0),
)
CONTROL_SUELO = (  # (x, y, t, color lineal, O)
    (380, 0, 0, (0.2157, 0.2651, 0.5575), 0.4743),
    (3000, 1200, 0, (0.4296, 0.4542, 0.7010), 0.0),
    (46000, 9000, 600, (0.6155, 0.5655, 0.7810), 0.0),
)
CONTROL_CIELO = ((0, 0, (0.7595, 0.6629, 0.8501)), (-40, 7, (0.6269, 0.6178, 0.8274)), (0, 90, (0.2160, 0.3280, 0.5970)))


def controles_seccion12(pisadas):
    if pisadas:
        print("PREVIEW controles seccion 12: SALTEADOS (hay perillas pisadas)")
        return True
    eh = eg = ec = eo = es = 0.0
    for (x, y, t, h0, gx0, gy0, hf0) in CONTROL_ALTURA:
        gx, gy, h, hf = vm.valley_grad(np.array([x], float), np.array([y], float), t, P)
        eh = max(eh, abs(h[0] - h0))
        eg = max(eg, abs(gx[0] - gx0), abs(gy[0] - gy0), abs(hf[0] - hf0))
    for (x, y, t, c0, o0) in CONTROL_SUELO:
        X, Y = np.array([x], float), np.array([y], float)
        gx, gy, h, hf = vm.valley_grad(X, Y, t, P)
        c, pp = vm.suelo(X, Y, gx, gy, h, hf, OJOS_DEF, P, partes=True)
        ec = max(ec, float(np.max(np.abs(c[0] - np.array(c0)))))
        eo = max(eo, abs(pp["O"][0] - o0))
    for (az, el, c0) in CONTROL_CIELO:
        c = vm.cielo(vm.dir_d(az, el)[None, :], P)
        es = max(es, float(np.max(np.abs(c[0] - np.array(c0)))))
    ok = eh <= 0.002 and eg <= 2e-6 and ec <= 1e-3 and eo <= 1e-3 and es <= 1e-3
    print("PREVIEW controles seccion 12: %s  |dh|max=%.2e cm  |grad,hf|max=%.2e  |color suelo|max=%.2e"
          "  |O|max=%.2e  |color cielo|max=%.2e" % ("OK" if ok else "FALLA", eh, eg, ec, eo, es))
    return ok


def _silueta(t, az, J=1600, rho_min=40.0):
    rho = rho_min * np.power(gen.R_MAX * 100.0 / rho_min, np.arange(J) / (J - 1.0))
    X = rho[:, None] * np.cos(az)[None, :]
    Y = rho[:, None] * np.sin(az)[None, :]
    H = vm.valley_h(X, Y, t, P)
    el = np.degrees(np.arctan2(H - OJOS[2], rho[:, None]))
    j = np.argmax(el, axis=0)
    return el[j, np.arange(az.size)], rho[j], H


def medir_composicion(t, etiqueta):
    az = np.radians(np.arange(720) * 0.5)
    sil, rsil, H = _silueta(t, az)
    borde = math.degrees(math.atan2(-OJOS[2], gen.R_MAX * 100.0))
    i_min = int(np.argmin(sil))
    g = np.linspace(-1000, 1000, 81)
    GX, GY = np.meshgrid(g, g)
    disco = np.hypot(GX, GY) <= 1000.0                  # disco de 10 m, centrado en el usuario y en el metaball
    hz = vm.valley_h(np.concatenate([GX[disco], GX[disco] + METABALL[0]]),
                     np.concatenate([GY[disco], GY[disco] + METABALL[1]]), t, P)
    print("PREVIEW %s t=%.1f s  silueta min %.2f deg (az %+.1f)  mediana %.2f  max %.2f  |  distancia de la silueta "
          "mediana %.0f m (min %.0f)  |  borde de malla a %.3f deg -> margen %.2f deg  |  h max a <= 10 m del "
          "usuario y del metaball = %.4f cm  |  h max del terreno %.0f cm"
          % (etiqueta, t, sil[i_min], _az_ue(np.degrees(az[i_min])), float(np.median(sil)), float(sil.max()),
             float(np.median(rsil)) / 100.0, float(rsil.min()) / 100.0, borde, sil[i_min] - borde,
             float(np.abs(hz).max()), float(H.max())))


def medir_movimiento(t0, n=12, dt=1.0):
    """Velocidad angular de la silueta (grados/s) en n instantes al azar de 10 min, su sube y baja coherente (heave:
    |media| / media de |cambio|) en toda la vuelta y en ventanas de 90 grados (lo que entra en el campo visual), y la
    cota rigurosa de la velocidad vertical (oleaje + respiracion)."""
    az = np.radians(np.arange(0, 360, 1.0))
    rng = np.random.default_rng(3)
    v, hv, hv90 = [], [], []
    for t in rng.uniform(0.0, 600.0, n):
        a, _, _ = _silueta(t, az)
        b, _, _ = _silueta(t + dt, az)
        d = (b - a) / dt
        v.append(np.abs(d))
        hv.append(abs(d.mean()) / max(np.abs(d).mean(), 1e-12))
        for y0 in range(0, 360, 15):
            w = np.arange(y0 - 45, y0 + 45) % 360
            hv90.append(abs(d[w].mean()) / max(np.abs(d[w]).mean(), 1e-12))
    v = np.array(v)
    cota, rc, c_ole, c_res = vm.cota_vel_vertical_deg(P, partes=True)
    print("PREVIEW movimiento: silueta mediana %.3f deg/s, p90 %.3f, max %.3f; %.0f %% de las muestras > 0,1 deg/s  |  "
          "heave 360 %.2f, en ventanas de 90 grados mediana %.2f  |  cota rigurosa de la velocidad vertical %.3f deg/s "
          "(r = %.0f m; oleaje %.3f, respiracion %.3f)  |  deriva neta %.1f %%"
          % (np.median(v), np.percentile(v, 90), v.max(), 100.0 * (v > 0.1).mean(), float(np.median(hv)),
             float(np.median(hv90)), cota, rc / 100.0, c_ole, c_res, 100.0 * vm.deriva_neta(P)))


def medir_malla(rs_m, tiempos=(0.0, 41.5), sub=6):
    """Error de SILUETA de la malla real (triangulos (a,b,c) y (a,c,d), interpolacion lineal) contra la funcion
    continua, en px del Quest 3 (25 px/grado), y el "temblor" de las facetas entre t y t + 1 s. La mirada es
    radial: el rayo cruza las cuerdas de cada anillo y las diagonales; en un triangulo plano la elevacion maxima
    cae en su borde, asi que alcanza con esos cruces."""
    S = gen.SECTORES
    rs = np.asarray(rs_m) * 100.0
    th = 2.0 * np.pi * np.arange(S) / S
    X = rs[:, None] * np.cos(th)[None, :]
    Y = rs[:, None] * np.sin(th)[None, :]
    sp1 = (np.arange(S) + 1) % S
    P0 = np.stack([X, Y], -1)
    P1 = P0[:, sp1, :]
    J = 4000
    rho_c = 40.0 * np.power(rs[-1] / 40.0, np.arange(J) / (J - 1.0))

    def una(t):
        H = vm.valley_h(X, Y, t, P)
        phis, em = [], []
        for k in range(sub):
            phi = th + (k + 0.5) / sub * 2.0 * np.pi / S
            d = np.stack([np.cos(phi), np.sin(phi)], -1)
            best = np.full(S, -90.0)
            for (A, B, hA, hB) in ((P0, P1, H, H[:, sp1]), (P0[:-1], P1[1:], H[:-1], H[1:, sp1])):
                e = B - A
                det = e[..., 0] * (-d[None, :, 1]) + e[..., 1] * d[None, :, 0]
                det = np.where(np.abs(det) < 1e-12, 1e-12, det)
                rx, ry = -A[..., 0], -A[..., 1]
                lam = (rx * (-d[None, :, 1]) + ry * d[None, :, 0]) / det
                rho = (e[..., 0] * ry - e[..., 1] * rx) / det
                ok = (lam >= -1e-9) & (lam <= 1.0 + 1e-9) & (rho > 1.0)
                el = np.degrees(np.arctan2((1.0 - lam) * hA + lam * hB - OJOS[2], rho))
                best = np.maximum(best, np.where(ok, el, -90.0).max(axis=0))
            phis.append(phi)
            em.append(best)
        phi = np.concatenate(phis)
        em = np.concatenate(em)
        ec = np.empty_like(em)
        for i0 in range(0, phi.size, 300):
            pp = phi[i0:i0 + 300]
            h = vm.valley_h(rho_c[:, None] * np.cos(pp)[None, :], rho_c[:, None] * np.sin(pp)[None, :], t, P)
            ec[i0:i0 + 300] = np.degrees(np.arctan2(h - OJOS[2], rho_c[:, None])).max(axis=0)
        return (ec - em) * 25.0

    err, tem = [], []
    for t in tiempos:
        e0 = una(t)
        err.append(np.abs(e0))
        tem.append(np.abs(una(t + 1.0) - e0))
    err = np.concatenate(err)
    tem = np.concatenate(tem)
    print("PREVIEW malla: error de silueta contra la funcion continua (px del Quest, 25 px/grado): p50 %.2f  p90 %.2f"
          "  p99 %.2f  max %.2f  |  temblor de facetas en 1 s: p90 %.2f  p99 %.2f px"
          % (np.median(err), np.percentile(err, 90), np.percentile(err, 99), err.max(),
             np.percentile(tem, 90), np.percentile(tem, 99)))


def _az_ue(a):
    return (a + 180.0) % 360.0 - 180.0


# ---------------------------------------------------------------------------------------------
# Escena Blender
# ---------------------------------------------------------------------------------------------
def ue_a_blender(p):
    """cm UE (x, y derecha, z) -> m Blender (x, -y, z): la imagen sale sin espejar."""
    p = np.asarray(p, dtype=np.float64)
    return np.stack([p[..., 0], -p[..., 1], p[..., 2]], axis=-1) / 100.0


def blender_a_ue(p):
    p = np.asarray(p, dtype=np.float64) * 100.0
    return np.stack([p[..., 0], -p[..., 1], p[..., 2]], axis=-1)


def poner_color(me, nombre, rgb):
    """Atributo de color por vertice (lineal, FLOAT_COLOR) y lo deja activo para Workbench."""
    attr = me.color_attributes.get(nombre)
    if attr is None:
        attr = me.color_attributes.new(name=nombre, type='FLOAT_COLOR', domain='POINT')
    rgba = np.ones((len(me.vertices), 4), dtype=np.float32)
    rgba[:, :3] = np.clip(rgb, 0.0, 1.0)
    attr.data.foreach_set("color", rgba.ravel())
    activar_color(me, nombre)


def activar_color(me, nombre):
    ca = me.color_attributes
    for k in range(len(ca)):
        if ca[k].name == nombre:
            for prop in ("active_color_index", "render_color_index"):
                try:
                    setattr(ca, prop, k)
                except Exception:  # noqa: BLE001
                    pass
    try:
        ca.active_color_name = nombre
    except Exception:  # noqa: BLE001
        pass


def material_color_vertice(nombre, attr):
    """Emision del color de vertice: si se cambia a Eevee, se ve igual que en Workbench FLAT."""
    mat = bpy.data.materials.new(nombre)
    mat.use_nodes = True
    nt = mat.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    a = nt.nodes.new("ShaderNodeAttribute")
    a.attribute_name = attr
    em = nt.nodes.new("ShaderNodeEmission")
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(a.outputs["Color"], em.inputs["Color"])
    nt.links.new(em.outputs["Emission"], out.inputs["Surface"])
    return mat


def preparar_render():
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_WORKBENCH'
    sh = sc.display.shading
    sh.light = 'FLAT'
    sh.color_type = 'VERTEX'
    for prop, val in (("show_cavity", False), ("show_object_outline", False),
                      ("show_specular_highlight", False), ("show_shadows", False),
                      ("show_backface_culling", False), ("show_xray", False)):
        try:
            setattr(sh, prop, val)
        except Exception:  # noqa: BLE001
            pass
    try:
        sc.display.render_aa = '16'
    except Exception:  # noqa: BLE001
        pass
    sc.view_settings.view_transform = 'Standard'     # sin tonemapper, como el APK
    sc.view_settings.look = 'None'
    sc.view_settings.exposure = 0.0
    sc.view_settings.gamma = 1.0
    sc.display_settings.display_device = 'sRGB'
    sc.render.image_settings.file_format = 'PNG'
    sc.render.image_settings.color_mode = 'RGB'
    sc.render.resolution_percentage = 100
    sc.render.film_transparent = False


def camara_nueva():
    cd = bpy.data.cameras.new("CamUsuario")
    cd.lens_unit = 'FOV'
    cd.sensor_fit = 'HORIZONTAL'
    cd.clip_start = 0.05
    cd.clip_end = 2000.0                        # m: el terreno llega a 640 m y el cielo del preview esta a 900 m
    cam = bpy.data.objects.new("CamUsuario", cd)
    bpy.context.collection.objects.link(cam)
    bpy.context.scene.camera = cam
    return cam


def orientar(cam, origen_ue, yaw_deg, pitch_deg):
    """Camara en origen_ue (cm UE) mirando al azimut UE yaw (0 = +X, 90 = +Y derecha) con pitch (+ = arriba)."""
    cam.location = Vector(ue_a_blender(origen_ue).tolist())
    # Blender: la camara mira a -Z local. Rot X 90 la pone mirando a +Y de Blender; el azimut UE a crece hacia -Y
    # de Blender, asi que el giro en Z es (a - 90) con signo cambiado: yaw UE 0 -> mira a +X de Blender.
    cam.rotation_euler = Euler((math.radians(90.0 + pitch_deg), 0.0, math.radians(-90.0 - yaw_deg)), 'XYZ')


def render(ruta, w, h):
    sc = bpy.context.scene
    sc.render.resolution_x = w
    sc.render.resolution_y = h
    sc.render.filepath = ruta
    bpy.ops.render.render(write_still=True)
    print("PREVIEW render -> %s (%dx%d)" % (ruta, w, h))


def leer_png(ruta):
    im = bpy.data.images.load(ruta)
    w, h = im.size
    px = np.empty(w * h * 4, dtype=np.float32)
    im.pixels.foreach_get(px)
    bpy.data.images.remove(im)
    return px.reshape(h, w, 4)


def escribir_png(arr, destino):
    h, w = arr.shape[:2]
    out = bpy.data.images.new("tmp_out", w, h, alpha=False)
    rgba = np.ones((h, w, 4), dtype=np.float32)
    rgba[..., :arr.shape[2]] = arr[..., :min(arr.shape[2], 4)]
    out.pixels.foreach_set(rgba.ravel())
    out.filepath_raw = destino
    out.file_format = 'PNG'
    out.save()
    bpy.data.images.remove(out)


def pegar_horizontal(rutas, destino):
    """Une PNGs del mismo alto en una tira (izquierda -> derecha)."""
    tira = np.concatenate([leer_png(r) for r in rutas], axis=1)
    escribir_png(tira, destino)
    for r in rutas:
        try:
            os.remove(r)
        except OSError:
            pass
    print("PREVIEW render -> %s (%dx%d, de izquierda a derecha: atras, izquierda, frente, derecha)"
          % (destino, tira.shape[1], tira.shape[0]))


def diferencia(ruta_a, ruta_b, destino, ganancia=12.0):
    """|b - a| en niveles de 8 bits: arriba en gris x ganancia; abajo en rojo sobre a apagada. Devuelve stats."""
    a = leer_png(ruta_a)[..., :3]
    b = leer_png(ruta_b)[..., :3]
    d = np.abs(b - a).mean(axis=2) * 255.0          # los pixeles del PNG ya estan en sRGB 0..1
    gris = np.clip(d * ganancia / 255.0, 0.0, 1.0)
    arriba = np.repeat(gris[..., None], 3, axis=2)
    base = 0.35 * a.mean(axis=2, keepdims=True).repeat(3, axis=2)
    k = np.clip(d * ganancia / 255.0, 0.0, 1.0)[..., None]
    abajo = base * (1.0 - k) + k * np.array([1.0, 0.15, 0.1])
    escribir_png(np.concatenate([abajo, arriba], axis=0), destino)   # fila 0 de Blender = abajo de la imagen
    terreno = d > 0.0
    print("PREVIEW diferencia -> %s  media %.2f niveles; %.1f %% de los pixeles cambia > 2 niveles; "
          "entre los que cambian: mediana %.1f, p90 %.1f niveles"
          % (destino, d.mean(), 100.0 * (d > 2.0).mean(), float(np.median(d[terreno])) if terreno.any() else 0.0,
             float(np.percentile(d[terreno], 90)) if terreno.any() else 0.0))


def main():
    global OJOS, METABALL
    global SALIDA
    opts, pisadas = leer_argumentos()
    if opts["carpeta"]:
        SALIDA = opts["carpeta"]
    # CAPA VIVA (2026-09-28): respira=S aplica lo que haria el BP (PushLive) + el preshader del material con esa S
    # (-1 exhalado, 0 neutro = la v2 exacta, +1 inhalado). La geometria no cambia.
    S_viva = float(opts["respira"])
    if "respira=" in " ".join(sys.argv):
        viva = vm.live_desde_S(S_viva)
        P.update(vm.efectivos(dict(P, **viva)))
        print("PREVIEW capa viva S = %+.2f -> %s" % (S_viva, ", ".join("%s %.3f" % kv for kv in sorted(viva.items()))))
        pisadas = pisadas or S_viva != 0.0
    tag = opts["tag"]
    t0 = float(opts["t0"])
    t5 = t0 + float(opts["dt"])
    os.makedirs(SALIDA, exist_ok=True)

    ok = controles_seccion12(pisadas)

    z0 = float(opts["valleZ"])
    OJOS = OJOS_DEF - np.array([0.0, 0.0, z0])
    METABALL = METABALL - np.array([0.0, 0.0, z0])
    if "ShadowCenter" not in " ".join(sys.argv):
        P["ShadowCenter"] = tuple(METABALL.tolist())
    mb_r = float(opts["mbR"])
    print("PREVIEW escena local: ojos z=%.0f cm  metaball z=%.0f cm (radio %.0f -> base a %.0f cm del piso)"
          % (OJOS[2], METABALL[2], mb_r, METABALL[2] - mb_r))
    medir_composicion(t0, "t0")
    medir_composicion(t5, "t5")
    medir_movimiento(t0)
    medir_malla(gen.radios()[0])
    if not ok:
        print("PREVIEW AVISO: el modelo no reproduce la seccion 12; las imagenes no son confiables")

    # --- escena ---
    gen.limpiar_escena()
    base, _, _ = gen.construir()
    base.hide_render = True
    valle = base.copy()
    valle.data = base.data.copy()
    valle.name = "Valle_preview"
    bpy.context.collection.objects.link(valle)
    valle.hide_render = False
    me = valle.data
    nv = len(me.vertices)
    co_b = np.empty(nv * 3, dtype=np.float64)
    base.data.vertices.foreach_get("co", co_b)
    co_b = co_b.reshape(nv, 3)
    ue = blender_a_ue(co_b)
    valle.data.materials.append(material_color_vertice("M_ValleVertice", "Col"))

    ojos_b = ue_a_blender(OJOS)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=720, ring_count=360, radius=CIELO_RADIO / 100.0,
                                         location=tuple(ojos_b.tolist()))
    sky = bpy.context.active_object
    sky.name = "Cielo_preview"
    sme = sky.data
    ns = len(sme.vertices)
    sco = np.empty(ns * 3, dtype=np.float64)
    sme.vertices.foreach_get("co", sco)
    sdir = blender_a_ue(sco.reshape(ns, 3))
    sdir = sdir / np.linalg.norm(sdir, axis=1)[:, None]
    poner_color(sme, "Col", vm.cielo(sdir, P))
    sme.materials.append(material_color_vertice("M_CieloVertice", "Col"))

    mb_b = ue_a_blender(METABALL)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=96, ring_count=48, radius=mb_r / 100.0,
                                         location=tuple(mb_b.tolist()))
    mb = bpy.context.active_object
    mb.name = "Metaball_referencia"
    mme = mb.data
    try:
        mme.shade_smooth()
    except AttributeError:
        pass
    nm = len(mme.vertices)
    mco = np.empty(nm * 3, dtype=np.float64)
    mme.vertices.foreach_get("co", mco)
    mn = blender_a_ue(mco.reshape(nm, 3))
    mn = mn / np.linalg.norm(mn, axis=1)[:, None]
    # Luz propia del sustituto, de arriba y del lado del usuario. NO es el sombreado del metaball real.
    Lm = np.array([-0.45, -0.25, 0.86])
    Lm = Lm / np.linalg.norm(Lm)
    wr = vm.sat((mn @ Lm + 0.8) / 1.8)
    poner_color(mme, "Col", vm.lerp(np.array([0.45, 0.50, 0.80]), np.array([0.92, 0.945, 1.0]), np.sqrt(wr)[:, None]))
    mme.materials.append(material_color_vertice("M_MetaballRef", "Col"))

    preparar_render()
    cam = camara_nueva()
    cam.data.angle = math.radians(90.0)
    cache = {}

    def aplicar(t, ojos):
        """Altura de los vertices en t y color visto desde ojos (el sombreado depende de la camara)."""
        if t not in cache:
            cache[t] = vm.valley_grad(ue[:, 0], ue[:, 1], t, P)
        gx, gy, h, hf = cache[t]
        nuevo = co_b.copy()
        nuevo[:, 2] = h / 100.0
        me.vertices.foreach_set("co", nuevo.ravel())
        me.update()
        poner_color(me, "Col", vm.suelo(ue[:, 0], ue[:, 1], gx, gy, h, hf, ojos, P))
        return h

    rutas = {}
    for (t, et) in ((t0, "t0"), (t5, "t5")):
        h = aplicar(t, OJOS)
        orientar(cam, OJOS, 0.0, -2.0)
        rutas[et] = os.path.join(SALIDA, "preview_valle_%s%s.png" % (et, tag))
        render(rutas[et], 1052, 862)
    rv = np.hypot(ue[:, 0], ue[:, 1])
    dh = np.abs(cache[t5][2] - cache[t0][2])
    i = int(np.argmax(dh))
    print("PREVIEW cambio de altura t0 -> t5: max %.0f cm (a %.0f m del usuario); a menos de 15 m: max %.4f cm"
          % (dh[i], rv[i] / 100.0, float(dh[rv < 1500.0].max())))
    diferencia(rutas["t0"], rutas["t5"], os.path.join(SALIDA, "preview_valle_dif%s.png" % tag))
    if opts["solo"] == "principal":
        print("PREVIEW LISTO")
        return

    # vista lateral equivalente a cap_exhala_lado.png: camara (380, -700, 70) cm, yaw 90 (mira a +Y), pitch 0
    cam_lado = np.array([380.0, -700.0, 70.0]) - np.array([0.0, 0.0, z0])
    aplicar(t0, cam_lado)
    orientar(cam, cam_lado, 90.0, 0.0)
    render(os.path.join(SALIDA, "preview_valle_lado%s.png" % tag), 1052, 862)

    # vuelta completa: 4 vistas de 90 grados a la altura de los ojos
    aplicar(t0, OJOS)
    partes = []
    for az in (180.0, -90.0, 0.0, 90.0):
        orientar(cam, OJOS, az, 0.0)
        r = os.path.join(SALIDA, "_vuelta_%d.png" % int(az))
        render(r, 480, 360)
        partes.append(r)
    pegar_horizontal(partes, os.path.join(SALIDA, "preview_valle_vuelta_t0%s.png" % tag))

    # planta: color CONTINUO por altura (casi negro = piso quieto h = 0 exacto; azul -> blanco = 0 -> 80 m;
    # azul -> violeta = valles del oleaje, 0 -> -15 m)
    h = cache[t0][2]
    azul = np.array([0.10, 0.20, 0.45])
    plano = vm.lerp(azul, np.array([1.0, 1.0, 1.0]), np.sqrt(np.clip(h / 8000.0, 0.0, 1.0))[:, None])
    plano = np.where((h < 0.0)[:, None],
                     vm.lerp(azul, np.array([0.60, 0.15, 0.65]), np.sqrt(np.clip(-h / 1500.0, 0.0, 1.0))[:, None]), plano)
    plano = np.where((np.abs(h) <= 1e-9)[:, None], np.array([[0.02, 0.05, 0.16]]), plano)
    poner_color(me, "Alt", plano)
    sky.hide_render = True
    mb.hide_render = True
    cam.data.type = 'ORTHO'
    cam.location = (0.0, 0.0, 300.0)
    cam.rotation_euler = (0.0, 0.0, -math.pi / 2.0)   # adelante (+X) hacia arriba de la imagen
    for (esc, suf) in ((2.0 * gen.R_MAX + 4.0, ""), (240.0, "_zoom")):
        cam.data.ortho_scale = esc
        render(os.path.join(SALIDA, "preview_valle_cenital%s_t0%s.png" % (suf, tag)), 1024, 1024)
    print("PREVIEW LISTO")


if __name__ == "__main__":
    main()
