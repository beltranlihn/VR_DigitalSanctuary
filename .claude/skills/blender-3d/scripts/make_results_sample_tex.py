# make_results_sample_tex.py - contenidos DE MUESTRA del cuadro de resultados, SOLO para la vista previa de Blender
# (render_results.py). Los contenidos reales (graficos, textos, el gusano) los pone Narrativa en Unreal/web: esto copia
# a grandes rasgos su propuesta de la web (world.js, "RESULTADOS", paso 9.4) para juzgar el marco con contenido.
# Un PNG RGBA por abertura (tamano de la abertura de la ventana, 1,5 px/mm): res_title, res_calm, res_heart,
# res_breath, res_melody, res_tip. Python del sistema (PIL).
# Uso: python make_results_sample_tex.py <dir_salida>
import math
import os
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

OUT = sys.argv[1] if len(sys.argv) > 1 else "."
PX = 1.5                                   # px por mm
WIN_IN = 1030.0 - 8.0                      # ancho de la abertura (contorno de 4 mm)
COL = {"calm": "#9a6ee6", "heart": "#e0566b", "breath": "#5d7fe0", "melody": "#e8a04e"}
NAME = {"calm": "CALM", "heart": "HEART RATE", "breath": "BREATH", "melody": "YOUR MELODY"}
H = {"calm": 210.0, "heart": 210.0, "breath": 170.0, "melody": 190.0}
F_HEAD = "C:/Windows/Fonts/bahnschrift.ttf"
F_TEXT = "C:/Windows/Fonts/segoeui.ttf"
SPANS = [(.10, .28), (.28, .44), (.44, .62), (.62, .80), (.80, .97)]
STAGE_COLS = ["#5d7fe0", "#e0566b", "#9a6ee6", "#e8a04e", "#4fc28f"]


def rgb(h, a=255):
    return (int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16), a)


def canvas(w_mm, h_mm):
    im = Image.new("RGBA", (int(w_mm * PX), int(h_mm * PX)), (0, 0, 0, 0))
    return im, ImageDraw.Draw(im)


def font(path, mm):
    return ImageFont.truetype(path, int(mm * PX))


def smooth(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def bump(t, a, b):
    return smooth((t - a) / .05) * (1 - smooth((t - (b - .05)) / .05))


def series(kind):
    out = []
    for i in range(180):
        t = i / 179
        if kind == "calm":
            out.append(min(max(.3 + .38 * smooth(t * 1.1) + .09 * math.sin(t * 19 + 1) * (1 - .5 * t) + .045 * math.sin(t * 57 + 2)
                               + .14 * bump(t, .44, .62) - .08 * bump(t, .62, .8), 0), 1))
        else:
            out.append(83 - 17 * smooth(t) + 4.5 * math.sin(t * 14 + .5) + 2 * math.sin(t * 41) + 5 * bump(t, .62, .8) - 3 * bump(t, .44, .62))
    return out


def head(d, key, w, meta):
    d.text((22 * PX, 12 * PX), NAME[key], font=font(F_HEAD, 17), fill=rgb(COL[key]))
    f = font(F_TEXT, 15)
    tw = d.textlength(meta, font=f)
    d.text((w - 22 * PX - tw, 13 * PX), meta, font=f, fill=(236, 232, 224, 185))


def graph(key):
    h = H[key] - 8.0
    im, d = canvas(WIN_IN, h)
    W_, H_ = im.size
    data = series(key)
    lo, hi, avg = min(data), max(data), sum(data) / len(data)
    heart = key == "heart"
    head(d, key, W_, "average %d bpm" % round(avg) if heart else "average %d / 100" % round(avg * 100))
    x0, x1, yt, yb = 92 * PX, W_ - 22 * PX, 50 * PX, H_ - 36 * PX
    pad = (hi - lo) * .12
    X = lambda i: x0 + (x1 - x0) * i / (len(data) - 1)                              # noqa: E731
    Y = lambda v: yb - (yb - yt) * (v - (lo - pad)) / ((hi + pad) - (lo - pad))     # noqa: E731
    for v in (hi, lo):                                                              # guias punteadas + su valor
        y = Y(v)
        for xs in range(int(x0), int(x1), int(14 * PX)):
            d.line([(xs, y), (xs + 7 * PX, y)], fill=(236, 232, 224, 70), width=2)
        s = str(round(v)) if heart else str(round(v * 100))
        f = font(F_TEXT, 17)
        d.text((x0 - 14 * PX - d.textlength(s, font=f), y - 11 * PX), s, font=f, fill=(236, 232, 224, 230))
    pts = [(X(i), Y(v)) for i, v in enumerate(data)]
    fill = Image.new("RGBA", im.size, (0, 0, 0, 0))                                 # area con degrade
    fd = ImageDraw.Draw(fill)
    fd.polygon(pts + [(x1, yb), (x0, yb)], fill=rgb(COL[key], 255))
    grad = Image.new("L", im.size, 0)
    gd = ImageDraw.Draw(grad)
    for y in range(int(yt), int(yb)):
        gd.line([(0, y), (W_, y)], fill=int(85 * (1 - (y - yt) / (yb - yt))))
    fill.putalpha(Image.composite(grad, Image.new("L", im.size, 0), fill.split()[3]))
    im.alpha_composite(fill)
    glow = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(glow).line(pts, fill=rgb(COL[key], 150), width=int(9 * PX), joint="curve")
    im.alpha_composite(glow.filter(ImageFilter.GaussianBlur(4)))
    c = rgb(COL[key])
    light = tuple(int(c[k] + (255 - c[k]) * .45) for k in range(3)) + (255,)
    d.line(pts, fill=light, width=int(3.2 * PX), joint="curve")
    ybar = H_ - 20 * PX                                                             # banda de las etapas
    for (a, b), sc in zip(SPANS, STAGE_COLS):
        d.rectangle([x0 + (x1 - x0) * a + 2 * PX, ybar, x0 + (x1 - x0) * b - 2 * PX, ybar + 5 * PX], fill=rgb(sc, 215))
    d.text((22 * PX, ybar - 6 * PX), "start", font=font(F_TEXT, 13), fill=(236, 232, 224, 130))
    return im


def breath():
    h = H["breath"] - 8.0
    im, d = canvas(WIN_IN, h)
    W_, H_ = im.size
    sc = [.62, .83, 1, .71, .96, .88]
    head(d, "breath", W_, "%d cycles  ·  inhale, hold, exhale" % len(sc))
    x0, x1, cy = 70 * PX, W_ - 70 * PX, H_ * .6
    R = min(40 * PX, (x1 - x0) / (len(sc) - 1) * .36)
    c = rgb(COL["breath"])
    for i, s in enumerate(sc):
        x = x0 + (x1 - x0) * i / (len(sc) - 1)
        full = s >= .95
        r = R - 2.5 * PX if full else max(4 * PX, s * (R - 9 * PX))
        if full:
            gl = Image.new("RGBA", im.size, (0, 0, 0, 0))
            ImageDraw.Draw(gl).ellipse([x - R - 6 * PX, cy - R - 6 * PX, x + R + 6 * PX, cy + R + 6 * PX], fill=c[:3] + (120,))
            im.alpha_composite(gl.filter(ImageFilter.GaussianBlur(10)))
        d.ellipse([x - R, cy - R, x + R, cy + R], outline=c[:3] + (230,), width=int((4.2 if full else 3) * PX))
        d.ellipse([x - r, cy - r, x + r, cy + r], fill=tuple(int(c[k] + (255 - c[k]) * .35) for k in range(3)) + (255,))
    return im


def melody():
    h = H["melody"] - 8.0
    im, d = canvas(WIN_IN, h)
    W_, H_ = im.size
    head(d, "melody", W_, "playing")
    mel = [0, 7, 2, -1, 11, 4, -1, 14]
    for k in range(8):                                                              # el gusano (en Unreal: mallas 3D)
        x = W_ / 2 + (-385 + k * 110) * PX
        y = H_ * .58 + math.sin(k * .9) * 10 * PX
        r = 36 * PX
        lit = k == 4
        d.ellipse([x - r, y - r, x + r, y + r], fill=(242, 220, 203, 255 if lit else 205))
        if mel[k] >= 0:
            hue = (20 + mel[k] * 9) / 360.0
            import colorsys
            cc = colorsys.hls_to_rgb(hue, .72, .7)
            rr = 17 * PX
            d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=tuple(int(255 * v) for v in cc) + (255,))
    return im


def title():
    im, d = canvas(1030.0, 95.0)
    W_, _ = im.size
    f = font(F_HEAD, 27)
    t = "YOUR JOURNEY THROUGH SOUL CHARGER"
    d.text(((W_ - d.textlength(t, font=f)) / 2, 8 * PX), t, font=f, fill=(241, 236, 226, 255))
    f2 = font(F_TEXT, 17)
    t2 = "14 min  ·  5 stages  ·  5 lights"
    d.text(((W_ - d.textlength(t2, font=f2)) / 2, 50 * PX), t2, font=f2, fill=(236, 232, 224, 160))
    return im


def tip():
    im, d = canvas(920.0 - 14.0, 170.0 - 14.0)
    W_, H_ = im.size
    c = rgb(COL["calm"])
    d.rectangle([28 * PX, 24 * PX, 33 * PX, H_ - 24 * PX], fill=c)
    d.text((52 * PX, 18 * PX), "CALM", font=font(F_HEAD, 18), fill=c)
    text = ("The calm of your mind across the whole journey, read from your brain activity every few seconds. "
            "The higher the line, the quieter your mind was.")
    f = font(F_TEXT, 21)
    line, y, maxw = "", 50 * PX, W_ - 84 * PX
    for wd in text.split():
        t = (line + " " + wd).strip()
        if d.textlength(t, font=f) > maxw:
            d.text((52 * PX, y), line, font=f, fill=(241, 236, 226, 255))
            line, y = wd, y + 29 * PX
        else:
            line = t
    d.text((52 * PX, y), line, font=f, fill=(241, 236, 226, 255))
    return im


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for name, im in (("res_title", title()), ("res_calm", graph("calm")), ("res_heart", graph("heart")),
                     ("res_breath", breath()), ("res_melody", melody()), ("res_tip", tip())):
        im.save(os.path.join(OUT, name + ".png"))
        print("TEX", name, im.size)
