# Genera mascaras de texto con el mismo layout que T_Share_Text (2048x509, Avenir Book, mayusculas espaciadas).
from PIL import Image, ImageDraw, ImageFont
import os
FONT = os.path.expanduser(r"~\AppData\Local\Microsoft\Windows\Fonts\Avenir Book.ttf")
W, H, TOP, BOT = 2048, 509, 190, 306          # caja de la letra en la referencia
def render(txt, size, track):
    f = ImageFont.truetype(FONT, size)
    im = Image.new("L", (W, H), 0); d = ImageDraw.Draw(im)
    widths = [d.textlength(c, font=f) for c in txt]
    total = sum(widths) + track * (len(txt) - 1)
    x = (W - total) / 2
    for c, w in zip(txt, widths):
        d.text((x, 0), c, font=f, fill=255); x += w + track
    bb = im.getbbox()
    im2 = Image.new("L", (W, H), 0); im2.paste(im.crop((0, bb[1], W, bb[3])), (0, TOP))
    return im2
def fit():
    ref = Image.open("../ShareButton/T_Share_Text.png").getbbox()
    best = None
    for size in range(120, 200):
        f = ImageFont.truetype(FONT, size)
        bb = f.getbbox("SHARE")
        if abs((bb[3] - bb[1]) - (BOT - TOP)) <= 1:
            for track in range(0, 120, 2):
                g = render("SHARE", size, track).getbbox()
                err = abs((g[2] - g[0]) - (ref[2] - ref[0]))
                if best is None or err < best[0]: best = (err, size, track, g)
    return best
if __name__ == "__main__":
    err, size, track, g = fit(); print("ajuste SHARE: err", err, "size", size, "track", track, "bbox", g)
    for txt, name in [("START", "T_Start_Text"), ("BACK", "T_Back_Text"), ("SHARE", "T_ShareCheck_Text")]:
        im = render(txt, size, track); im.save(name + ".png"); print(name, im.getbbox())
