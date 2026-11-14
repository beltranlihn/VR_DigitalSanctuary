# -*- coding: utf-8 -*-
"""sim_air.py - simula 5 ciclos 4-3-4-3 del aliento visible con movimientos de cabeza, mide confort y costo, y dibuja
las imagenes de concepto sobre los renders del valle (render_valle_respira.py). Python del sistema (numpy, PIL,
matplotlib). Todo se escribe en esta carpeta."""
import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFont

import air_model as am

AQUI = os.path.dirname(os.path.abspath(__file__))
FPS = 72.0
DT = 1.0 / FPS
CYCLE = 14.0
LAG = 0.4
EYE0 = np.array([0.0, 0.0, 120.0])
PPD_Q3 = 25.0                  # px/grado en el centro del Quest 3 (pesimista para la cobertura)
Q3_PX = 2064 * 2208


def ss(a, b, x):
    return float(am.smoothstep(a, b, x))


def head(t):
    """Pose de la cabeza: quieta con balanceo chico, y tres pruebas: giro de 30 grados en plena inhalacion (ciclo 3),
    mirar el sensor (pitch -35) en plena exhalacion (ciclo 4) e inclinarse 8 cm hacia adelante (ciclo 5)."""
    yaw = 0.6 * math.sin(2 * math.pi * 0.13 * t)
    pitch = -2.0 + 0.4 * math.sin(2 * math.pi * 0.21 * t)
    eye = EYE0 + np.array([0.4 * math.sin(2 * math.pi * 0.09 * t), 0.3 * math.sin(2 * math.pi * 0.17 * t),
                           0.2 * math.sin(2 * math.pi * 0.11 * t)])
    yaw += 30.0 * (ss(30.0, 30.6, t) - ss(33.6, 34.6, t))
    pitch += -33.0 * (ss(50.0, 50.8, t) - ss(52.8, 53.6, t))
    eye = eye + np.array([8.0, 0.0, -3.0]) * (ss(57.0, 58.0, t) - ss(60.0, 61.0, t))
    moving = (29.9 <= t <= 34.8) or (49.9 <= t <= 53.8) or (56.9 <= t <= 61.2)
    return eye, yaw, pitch, moving


def simulate(total=5 * CYCLE + 2.0, keep=None):
    q = am.AIR
    sd = am.Seeds(q)
    eye, yaw, pitch, _ = head(0.0)
    st = am.BPState(eye, yaw, pitch, q)
    prevS, _ = am.breath_S(0.0, lag=LAG)
    prev = None
    rec = dict(mind_eye=1e9, max_el=-90.0, cnt=[], cov=[], spd=[], jump=0.0, lagmax=0.0, t=[], cnt_in=[],
               cnt_out=[], da=0.0)
    snaps = {}
    n = int(total * FPS)
    for k in range(n):
        t = k * DT
        S, ph = am.breath_S(t, lag=LAG)
        dS = (S - prevS) / DT
        prevS = S
        eye, yaw, pitch, moving = head(t)
        st.step(DT, dS, eye, yaw, pitch, on=1.0)
        m = am.motes(st, sd, eye, yaw, pitch, q)
        F, R, U = am.head_basis(yaw, pitch)
        vis = m["alpha"] > 0.02
        D = m["P"] - eye[None, :]
        x = D @ F
        y = D @ R
        z = D @ U
        az = np.degrees(np.arctan2(y, x))
        el = m["el"]
        inview = vis & (x > 0) & (np.abs(az) < 52.0) & (el > -48.0)
        if vis.any():
            for s_eye in (-3.2, 3.2):
                e2 = eye + R * s_eye
                rec["mind_eye"] = min(rec["mind_eye"], float(np.linalg.norm(m["P"][vis] - e2[None, :], axis=1).min()))
            rec["max_el"] = max(rec["max_el"], float(el[vis].max()))
        cov = float(np.sum(np.pi * (0.5 * m["ang"][inview] * PPD_Q3) ** 2)) / Q3_PX
        rec["cnt"].append(int(inview.sum()))
        rec["cnt_in"].append(int(inview[:m["n_in"]].sum()))
        rec["cnt_out"].append(int(inview[m["n_in"]:].sum()))
        rec["cov"].append(cov)
        vis10 = inview & (m["alpha"] > 0.1)
        rec.setdefault("v_in", []).append(int(vis10[:m["n_in"]].sum()))
        rec.setdefault("v_out", []).append(int(vis10[m["n_in"]:].sum()))
        rec["t"].append(t)
        rec["lagmax"] = max(rec["lagmax"], abs((yaw - st.yawLag + 180) % 360 - 180))
        if prev is not None:
            pm, paz, pel, ps, pvis = prev
            ok = vis & pvis & (m["s"] >= ps)          # sin el salto de la cinta (ocurre con alfa 0)
            if ok.any():
                if not moving:
                    dirn = np.stack([az, el], 1)
                    dprev = np.stack([paz, pel], 1)
                    w = np.hypot((dirn[:, 0] - dprev[:, 0]) * np.cos(np.radians(el)), dirn[:, 1] - dprev[:, 1])
                    rec["spd"].extend((w[ok] * FPS).tolist())
                    ok2 = ok & (m["alpha"] > 0.1)
                    rec.setdefault("spd2", []).extend((w[ok2] * FPS).tolist())
                    if ok2.any():
                        kk = np.argmax(np.where(ok2, w, -1))
                        if w[kk] * FPS > rec.get("vmax2", (0,))[0]:
                            rec["vmax2"] = (float(w[kk] * FPS), "in" if kk < m["n_in"] else "out", float(m["s"][kk]),
                                            float(m["dist"][kk]), float(m["alpha"][kk]))
                rec["jump"] = max(rec["jump"], float(np.linalg.norm(m["P"][ok] - pm[ok], axis=1).max()))
            rec["da"] = max(rec["da"], float(np.abs(m["alpha"] - prev_alpha).max()))
        prev = (m["P"].copy(), az, el, m["s"].copy(), vis)
        prev_alpha = m["alpha"].copy()
        if keep and any(abs(t - kt) < DT / 2 for kt in keep):
            kt = min(keep, key=lambda v: abs(v - t))
            snaps[kt] = dict(m=m, eye=eye.copy(), yaw=yaw, pitch=pitch, S=S, ph=ph, Ein=st.Ein, Eout=st.Eout,
                             Fout=st.Fout)
    return rec, snaps


# ---------------------------------------------------------------------------------------------
# Dibujo de las motas sobre los renders (camara del preview: ojos (0,0,120), yaw 0, pitch -2, HFOV 90)
# ---------------------------------------------------------------------------------------------
W, H = 1052, 862
FPX = (W / 2) / math.tan(math.radians(45.0))


def to_lin(a):
    return np.where(a <= 0.04045, a / 12.92, ((a + 0.055) / 1.055) ** 2.4)


def to_srgb(a):
    a = np.clip(a, 0, 1)
    return np.where(a <= 0.0031308, 12.92 * a, 1.055 * a ** (1 / 2.4) - 0.055)


def load(name):
    return to_lin(np.asarray(Image.open(os.path.join(AQUI, name)).convert("RGB")).astype(np.float64) / 255.0)


def project(P, eye):
    F, R, U = am.head_basis(0.0, -2.0)
    D = P - eye[None, :]
    x = D @ F
    return W / 2 + FPX * (D @ R) / x, H / 2 - FPX * (D @ U) / x, x


def splat(img, m, eye, zoom=1.0, x0=0.0, y0=0.0, gain=1.0):
    """Compone las motas (premultiplicado, en lineal) sobre img (lineal). zoom/x0/y0 = recorte ampliado."""
    px, py, depth = project(m["P"], eye)
    px = (px - x0) * zoom
    py = (py - y0) * zoom
    ppd = FPX * math.pi / 180.0 * zoom
    h, w = img.shape[:2]
    for k in np.argsort(-depth):
        a = m["alpha"][k] * gain
        if a < 0.004 or depth[k] <= 0:
            continue
        r = max(0.5 * m["ang"][k] * ppd, 0.35)
        ext = int(math.ceil(2.2 * r)) + 1
        cx, cy = px[k], py[k]
        xa, xb = int(cx) - ext, int(cx) + ext + 1
        ya, yb = int(cy) - ext, int(cy) + ext + 1
        if xb < 0 or yb < 0 or xa >= w or ya >= h:
            continue
        xa, ya = max(xa, 0), max(ya, 0)
        xb, yb = min(xb, w), min(yb, h)
        gx, gy = np.meshgrid(np.arange(xa, xb) + 0.5, np.arange(ya, yb) + 0.5)
        d2 = ((gx - cx) ** 2 + (gy - cy) ** 2) / (r * r)
        al = np.clip(a * np.exp(-2.2 * d2), 0, 1)[..., None]
        if r < 1.0:                       # subpixel: conservar la energia (la mota no desaparece al achicarse)
            al = np.clip(al * (1.0 / max(r, 0.35)) ** 2 * 0.45, 0, 1)
        img[ya:yb, xa:xb] = img[ya:yb, xa:xb] * (1 - al) + m["col"][k][None, None, :] * al
    return img


def font(sz):
    for f in ("C:/Windows/Fonts/segoeui.ttf", "C:/Windows/Fonts/arial.ttf"):
        if os.path.exists(f):
            return ImageFont.truetype(f, sz)
    return ImageFont.load_default()


def label(im, text, sub=None, pos=(14, 10)):
    d = ImageDraw.Draw(im)
    f1, f2 = font(26), font(18)
    d.rectangle([pos[0] - 8, pos[1] - 6, pos[0] + 12 + max(d.textlength(text, font=f1),
                                                              d.textlength(sub or "", font=f2)),
                 pos[1] + (58 if sub else 34)], fill=(20, 22, 40))
    d.text(pos, text, fill=(240, 240, 250), font=f1)
    if sub:
        d.text((pos[0], pos[1] + 32), sub, fill=(200, 200, 220), font=f2)
    return im


def pil(lin):
    return Image.fromarray((to_srgb(lin) * 255.0 + 0.5).astype(np.uint8))


def bg_for(S, neu, inh, exh):
    return neu + (inh - neu) * S if S >= 0 else neu + (exh - neu) * (-S)


def main():
    # instantes del ciclo 2 (cabeza quieta): inhalar arranca en 14 + LAG
    c = CYCLE + LAG
    keep_panel = {"inh": c + 2.6, "exh": c + 4.0 + 3.0 + 3.2}
    strip = [("Inhala 1,0 s", c + 1.0), ("Inhala 2,5 s", c + 2.5), ("Fin de la inhalación", c + 4.0),
             ("Retiene 2,0 s", c + 6.0), ("Exhala 1,0 s", c + 8.0), ("Exhala 2,5 s", c + 9.5),
             ("Fin de la exhalación", c + 11.0), ("Pausa 2,0 s", c + 13.0)]
    turn = [("Giro 30° en curso (0,3 s)", 30.3), ("Giro terminado (+0,4 s)", 31.0)]
    keep = list(keep_panel.values()) + [t for _, t in strip] + [t for _, t in turn]
    rec, snaps = simulate(keep=keep)

    spd = np.array(rec["spd"]) if rec["spd"] else np.zeros(1)
    spd2 = np.array(rec.get("spd2") or [0.0])
    cov = np.array(rec["cov"])
    cnt = np.array(rec["cnt"])
    q = am.AIR
    nq = q["NIn"] + q["NOut"]
    lines = [
        "SIM aliento visible: 5 ciclos 4-3-4-3 a 72 Hz, con giro de 30 grados (ciclo 3), mirada al sensor pitch -35 "
        "(ciclo 4) e inclinacion de 8 cm (ciclo 5)",
        "  distancia minima de una mota visible (alfa > 0,02) a cualquiera de los dos ojos: %.1f cm" % rec["mind_eye"],
        "  elevacion maxima de una mota visible respecto de la mirada: %.1f grados" % rec["max_el"],
        "  motas visibles en el campo: media %.0f, p95 %.0f, max %d (inhalar max %d, exhalar max %d)"
        % (cnt.mean(), np.percentile(cnt, 95), cnt.max(), max(rec["cnt_in"]), max(rec["cnt_out"])),
        "  cobertura de pantalla (a 25 px/grado): media %.4f %%, max %.4f %%" % (100 * cov.mean(), 100 * cov.max()),
        "  velocidad angular de las motas visibles con la cabeza quieta (grados/s): p50 %.1f  p90 %.1f  p99 %.1f  max %.1f"
        % (np.median(spd), np.percentile(spd, 90), np.percentile(spd, 99), spd.max()),
        "  idem solo motas con alfa > 0,1: p50 %.1f  p90 %.1f  p99 %.1f  max %.1f  (la mas rapida: %s)"
        % (np.median(spd2), np.percentile(spd2, 90), np.percentile(spd2, 99), spd2.max(), str(rec.get("vmax2"))),
        "  salto maximo de una mota visible entre cuadros: %.2f cm; cambio maximo de alfa por cuadro %.3f"
        % (rec["jump"], rec["da"]),
        "  retraso maximo del marco del aire respecto de la cabeza (yaw): %.1f grados" % rec["lagmax"],
        "  costo estimado VS: %d quads x 4 vertices x 2 vistas x 250 op-eq = %.1f M op-eq -> %.3f-%.3f ms"
        % (nq, nq * 8 * 250 / 1e6, nq * 8 * 250 / 1e6 * 0.0055, nq * 8 * 250 / 1e6 * 0.011),
    ]
    tt = np.array(rec["t"])
    for nombre, clave, t_on in (("inhalar", "v_in", CYCLE + LAG), ("exhalar", "v_out", CYCLE + LAG + 7.0)):
        v = np.array(rec[clave])
        idx = np.where((tt >= t_on) & (v >= 20))[0]
        idx2 = np.where((tt >= t_on) & (v >= 150))[0]
        lines.append("  latencia %s (ciclo 2): 20 motas con alfa > 0,1 a los %.2f s del inicio de la fase; 150 motas a los %.2f s"
                     % (nombre, tt[idx[0]] - t_on if len(idx) else -1, tt[idx2[0]] - t_on if len(idx2) else -1))
    with open(os.path.join(AQUI, "sim_air_resultados.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))

    neu, inh, exh = load("preview_valle_t0_neutro.png"), load("preview_valle_t0_inhala.png"), \
        load("preview_valle_t0_exhala.png")

    # ---- 1) panel principal: reposo / inhala / exhala + recortes ampliados + diferencia del valle ----
    si, se = snaps[keep_panel["inh"]], snaps[keep_panel["exh"]]
    im_i = splat(inh.copy(), si["m"], si["eye"])
    im_e = splat(exh.copy(), se["m"], se["eye"])
    x0, y0, cw, ch, z = 176, 470, 700, 392, 2.0
    crop_i = np.kron(inh[y0:y0 + ch, x0:x0 + cw], np.ones((2, 2, 1)))
    crop_e = np.kron(exh[y0:y0 + ch, x0:x0 + cw], np.ones((2, 2, 1)))
    crop_i = splat(crop_i, si["m"], si["eye"], zoom=z, x0=x0, y0=y0)
    crop_e = splat(crop_e, se["m"], se["eye"], zoom=z, x0=x0, y0=y0)
    a8 = to_srgb(inh) * 255.0
    b8 = to_srgb(exh) * 255.0
    d = np.abs(a8 - b8).mean(2)
    k = np.clip(d * 10.0 / 255.0, 0, 1)[..., None]
    diff = (0.35 * to_srgb(neu).mean(2, keepdims=True)) * (1 - k) + k * np.array([1.0, 0.55, 0.2])
    tw = 700
    th = int(H * tw / W)
    P1 = [label(pil(neu).resize((tw, th), Image.LANCZOS), "Reposo", "valle autoral, sin respiración"),
          label(pil(im_i).resize((tw, th), Image.LANCZOS), "Inhala (2,6 s de 4)",
                "motas frías entran a la boca · bruma se abre · resplandor sube"),
          label(pil(im_e).resize((tw, th), Image.LANCZOS), "Exhala (3,2 s de 4)",
                "pluma tibia sale de la boca · bruma se cierra y entibia · sombra se abre")]
    zw = 2 * tw
    zh = int(zw * ch / cw)
    P2 = [label(pil(crop_i).resize((zw, zh), Image.LANCZOS), "Inhala, recorte x2 (banda baja)",
                "tamaño angular real; el Quest tiene ~2,5x más píxeles por grado"),
          label(pil(crop_e).resize((zw, zh), Image.LANCZOS), "Exhala, recorte x2 (banda baja)",
                "la pluma frena, se abre, sube apenas y se apaga hacia 1,1 m")]
    dimg = label(Image.fromarray((np.clip(diff, 0, 1) * 255).astype(np.uint8)).resize((tw, th), Image.LANCZOS),
                 "Valle: inhala vs exhala (x10)", "dónde cambian niebla, resplandor y sombra")
    top_w = 4 * tw
    canvas = Image.new("RGB", (top_w, th + 8 + zh), (14, 15, 26))
    for i_, p in enumerate(P1 + [dimg]):
        canvas.paste(p, (i_ * tw, 0))
    canvas.paste(P2[0], (0, th + 8))
    canvas.paste(P2[1], (zw, th + 8))
    canvas.save(os.path.join(AQUI, "concepto_inhala_exhala.png"))

    # ---- 2) tira del ciclo (recorte ampliado de la banda baja, 8 instantes) ----
    tiles = []
    for (txt, t) in strip:
        sn = snaps[t]
        bg = bg_for(sn["S"], neu, inh, exh)
        cr = np.kron(bg[y0:y0 + ch, x0:x0 + cw], np.ones((2, 2, 1)))
        cr = splat(cr, sn["m"], sn["eye"], zoom=z, x0=x0, y0=y0)
        sub = "S %+.2f · E_in %.2f · E_out %.2f · frente %.2f" % (sn["S"], sn["Ein"], sn["Eout"], min(sn["Fout"], 1.0))
        tiles.append(label(pil(cr).resize((700, 392), Image.LANCZOS), txt, sub))
    strip_im = Image.new("RGB", (4 * 700, 2 * 392 + 6), (14, 15, 26))
    for i_, tl in enumerate(tiles):
        strip_im.paste(tl, ((i_ % 4) * 700, (i_ // 4) * 398))
    strip_im.save(os.path.join(AQUI, "ciclo_aliento_8_instantes.png"))

    # ---- 3) giro de cabeza en plena inhalacion (camara = la cabeza girada) ----
    tiles = []
    for (txt, t) in turn:
        sn = snaps[t]
        m = dict(sn["m"])
        # la camara del render mira a yaw 0: se rota la escena al marco de la cabeza para dibujar lo que ve el usuario
        yaw = math.radians(sn["yaw"])
        Rz = np.array([[math.cos(-yaw), -math.sin(-yaw), 0], [math.sin(-yaw), math.cos(-yaw), 0], [0, 0, 1]])
        m["P"] = (Rz @ (m["P"] - sn["eye"][None, :]).T).T + sn["eye"][None, :]
        cr = np.kron(inh[y0:y0 + ch, x0:x0 + cw], np.ones((2, 2, 1)))
        cr = splat(cr, m, sn["eye"], zoom=z, x0=x0, y0=y0)
        tiles.append(label(pil(cr).resize((700, 392), Image.LANCZOS), txt,
                           "vista desde la cabeza girada %.0f° (el fondo no gira: solo cuentan las motas)" % sn["yaw"]))
    tim = Image.new("RGB", (2 * 700 + 6, 392), (14, 15, 26))
    for i_, tl in enumerate(tiles):
        tim.paste(tl, (i_ * 706, 0))
    tim.save(os.path.join(AQUI, "giro_cabeza_inhalando.png"))
    print("IMAGENES LISTAS")


if __name__ == "__main__":
    main()
