# sheet_instr_card.py - arma instr_sheet.png con las 6 paginas del panel de instrucciones (2 columnas: ENTERING |
# SURROUNDING, 3 filas: P1..P3) y, abajo, el panel en hover y apretado. Vistas de render_instr_card.py.
# Python del SISTEMA (PIL).
# Uso: python sheet_instr_card.py <prefijo_de_las_vistas> <salida.png>     (prefijo: ruta sin "_Entering_P1.png")
import sys

from PIL import Image, ImageDraw, ImageFont

pre, out = sys.argv[1], sys.argv[2]
CW, CH, LAB = 1000, 640, 30                       # celda (la vista recortada y achicada) y franja de la etiqueta
CROP = (80, 110, 1320, 890)                       # recorte de la vista de 1400 x 900
font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 16)


def cell(path):
    return Image.open(path).convert("RGB").crop(CROP).resize((CW, int(CW * (CROP[3] - CROP[1]) / (CROP[2] - CROP[0]))), Image.LANCZOS)


rows = [[("%s_Entering_P%d.png" % (pre, p), "ENTERING p%d" % p), ("%s_Surrounding_P%d.png" % (pre, p), "SURROUNDING p%d" % p)]
        for p in (1, 2, 3)]
rows.append([("%s_hover.png" % pre, "hover (la placa sube 1 mm, la cinta y el texto se encienden)"),
             ("%s_confirma.png" % pre, "apretado = confirmacion (-4 mm, la luz da la vuelta al borde)")])
rows.append([("%s_ctr_ink.png" % pre, "alternativa de contraste A: tinta oscura sobre la placa clara (pagina de SURROUNDING p2)"),
             ("%s_ctr_dark.png" % pre, "alternativa de contraste B: placa oscura, tinta hueso (mismas mascaras)")])
cells = [[cell(p) for p, _ in r] for r in rows]
rh = [max(c.height for c in r) + LAB for r in cells]
sheet = Image.new("RGB", (CW * 2 + 10, sum(rh)), (0, 0, 0))
d = ImageDraw.Draw(sheet)
y = 0
for r, labs, h in zip(cells, rows, rh):
    for k, (im, (_, lab)) in enumerate(zip(r, labs)):
        d.text((k * (CW + 10) + 10, y + 7), lab, font=font, fill=(235, 235, 235))
        sheet.paste(im, (k * (CW + 10), y + LAB))
    y += h
sheet.save(out)
print("SHEET_OK", sheet.size)
