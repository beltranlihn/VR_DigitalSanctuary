# sheet_demo_card.py - arma democard_sheet.png (reposo / hover / confirmacion / variante Full) con las vistas de
# render_demo_card.py, como share_sheet.png. Python del SISTEMA (PIL).
# Uso: python sheet_demo_card.py <prefijo_de_las_vistas> <salida.png>     (prefijo: ruta sin "_reposo.png")
import sys

from PIL import Image, ImageDraw, ImageFont

pre, out = sys.argv[1], sys.argv[2]
rows = [("reposo", "reposo: ENTERING y SURROUNDING, 300 x 190 mm (mascara solo con el titulo = el contrato)"),
        ("hover", "hover en ENTERING: la placa sube 1 mm, la cinta y el texto se encienden"),
        ("confirma", "ENTERING apretado = confirmacion (-4 mm, la luz da la vuelta al borde)"),
        ("full", "OPCIONAL: misma placa con la mascara Full (icono + titulo + subtitulo); textos de ejemplo")]
Y0, Y1 = 120, 530
font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 16)
ims = [Image.open("%s_%s.png" % (pre, k)).convert("RGB").crop((0, Y0, 1500, Y1)) for k, _ in rows]
H = sum(i.height + 34 for i in ims)
sheet = Image.new("RGB", (1500, H), (0, 0, 0))
d = ImageDraw.Draw(sheet)
y = 0
for (k, label), im in zip(rows, ims):
    d.text((12, y + 8), label, font=font, fill=(235, 235, 235))
    sheet.paste(im, (0, y + 34))
    y += im.height + 34
sheet.save(out)
print("SHEET_OK", sheet.size)
