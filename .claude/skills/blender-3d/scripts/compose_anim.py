# compose_anim.py - arma la presentacion de una animacion de aparicion (cuadros de anim_palette_base.render_anim):
#   <dir>/anim.gif     entrada (1,5 s) -> reposo 0,8 s -> SALIDA = la misma al reves -> negro 0,5 s, en bucle
#   <dir>/sheet.png    hoja de contacto: 12 cuadros de la entrada con su tiempo
#   control: el ULTIMO cuadro tiene que ser igual al reposo (rest.png) y el PRIMERO casi negro (la pieza no nacio)
# Uso (Python del sistema): python compose_anim.py <dir> [titulo] [fps=30]
import glob
import os
import sys

from PIL import Image, ImageChops, ImageDraw, ImageStat

D = sys.argv[1]
TITLE = sys.argv[2] if len(sys.argv) > 2 else os.path.basename(os.path.normpath(D))
FPS = float(sys.argv[3]) if len(sys.argv) > 3 else 30.0
fr = sorted(glob.glob(os.path.join(D, "f_*.png")))
ims = [Image.open(f).convert("RGB") for f in fr]
rest = Image.open(os.path.join(D, "rest.png")).convert("RGB")
diff = ImageChops.difference(ims[-1], rest)
d_mean = sum(ImageStat.Stat(diff).mean) / 3
d_max = max(b[1] for b in diff.getextrema())
first = sum(ImageStat.Stat(ims[0]).mean) / 3
rest_b = sum(ImageStat.Stat(rest).mean) / 3
dt = int(round(1000 / FPS))
black = Image.new("RGB", ims[0].size, (0, 0, 0))
seq = ims + [ims[-1]] * int(0.8 * FPS) + ims[::-1] + [black] * int(0.5 * FPS)
gw = ims[0].width * 2 // 3
gh = ims[0].height * 2 // 3
seq = [s.resize((gw, gh), Image.LANCZOS) for s in seq]
seq[0].save(os.path.join(D, "anim.gif"), save_all=True, append_images=seq[1:], duration=dt, loop=0, optimize=True)
n = len(ims)
pick = [round(i * (n - 1) / 11) for i in range(12)]
tw, th = ims[0].width // 2, ims[0].height // 2
sheet = Image.new("RGB", (tw * 4, th * 3 + 30), (0, 0, 0))
dr = ImageDraw.Draw(sheet)
dr.text((8, 8), "%s  (entrada 1,5 s; la salida es la misma al reves)" % TITLE, fill=(235, 230, 220))
for k, i in enumerate(pick):
    x, y = (k % 4) * tw, 30 + (k // 4) * th
    sheet.paste(ims[i].resize((tw, th), Image.LANCZOS), (x, y))
    dr.text((x + 6, y + 4), "t = %.2f s" % (i / FPS), fill=(235, 230, 220))
sheet.save(os.path.join(D, "sheet.png"))
print("COMPOSE_OK cuadros %d  ultimo_vs_reposo media %.3f max %d  brillo_primer_cuadro %.2f (reposo %.2f)" % (n, d_mean, d_max, first, rest_b))
