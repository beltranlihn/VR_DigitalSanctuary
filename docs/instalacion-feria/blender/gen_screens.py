"""Imágenes de las dos pantallas circulares (EEG adentro, marca en recepción)."""
import math, os
from PIL import Image, ImageDraw, ImageFilter, ImageFont

OUT = os.path.dirname(os.path.abspath(__file__))
S = 1024


def radial_bg(c0, c1, c2):
    im = Image.new('RGB', (S, S))
    px = im.load()
    for y in range(S):
        for x in range(S):
            d = math.hypot(x - S / 2, y - S / 2) / (S / 2)
            if d < 0.6:
                t = d / 0.6; a, b = c0, c1
            else:
                t = min(1, (d - 0.6) / 0.4); a, b = c1, c2
            px[x, y] = tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))
    return im


# --- EEG ---
im = radial_bg((42, 29, 107), (20, 15, 56), (7, 6, 26))
glow = Image.new('RGB', (S, S), (0, 0, 0))
g = ImageDraw.Draw(glow)
cols = [(255, 122, 217), (143, 182, 255), (180, 140, 255)]
for k in range(3):
    pts = []
    for x in range(0, S + 1, 8):
        t = 1.3
        y = S / 2 + math.sin(x * 0.009 + t * 1.3 + k * 1.7) * (80 + k * 36) * math.sin(t * 0.4 + k + 0.6) + math.sin(x * 0.025 - t * 2 + k) * 20 + (k - 1) * 60
        pts.append((x, y))
    g.line(pts, fill=cols[k], width=14 if k == 1 else 8)
im = Image.blend(im, Image.composite(glow, im, glow.convert('L').point(lambda v: 255 if v > 0 else 0)), 0.9)
im = Image.composite(Image.blend(im, glow.filter(ImageFilter.GaussianBlur(10)), 0.0), im, Image.new('L', (S, S), 255))
d = ImageDraw.Draw(im)
d.ellipse((S / 2 - 18, 230 - 18, S / 2 + 18, 230 + 18), fill=(255, 111, 168))
im.save(os.path.join(OUT, 'screen_eeg.png'))

# --- marca ---
im = radial_bg((112, 132, 230), (26, 23, 72), (7, 6, 26))
d = ImageDraw.Draw(im)
def font(sz, bold=False):
    for f in (['segoeuisb.ttf', 'seguisb.ttf', 'arialbd.ttf'] if bold else ['segoeui.ttf', 'arial.ttf']):
        try:
            return ImageFont.truetype(f, sz)
        except OSError:
            pass
    return ImageFont.load_default()
f1, f2 = font(118, True), font(36)
for txt, y, f in (('Digital', 440, f1), ('Sanctuary', 572, f1)):
    w = d.textlength(txt, font=f)
    d.text((S / 2 - w / 2, y - 70), txt, font=f, fill=(244, 242, 255))
sub = 'S O U L   C H A R G E R'
w = d.textlength(sub, font=f2)
d.text((S / 2 - w / 2, 700), sub, font=f2, fill=(205, 205, 235))
im.save(os.path.join(OUT, 'screen_brand.png'))
print('ok')
