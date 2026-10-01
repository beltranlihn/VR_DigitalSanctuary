# Arma la maqueta: CSS literal de Immersive Studio Pro (index.html:16-1201, sin comentarios) + capa Soul Charger.
# Salidas: editor-obra-mockup.html (fuente del artifact, sin <html>/<head>/<body>) y preview.html (para servir local).
import re, pathlib
here=pathlib.Path(__file__).parent
isp=pathlib.Path(r"C:/Users/beltr/Desktop/Alma Digital Studio/Projects/Immersive Studio Pro/index.html").read_text(encoding='utf-8').splitlines()
css="\n".join(isp[15:1201])                      # líneas 16..1201 = el contenido del <style> grande
css=re.sub(r"/\*.*?\*/","",css,flags=re.S)       # sin comentarios
css="\n".join(l.rstrip() for l in css.splitlines() if l.strip())
body=(here/"src-body.html").read_text(encoding='utf-8')
head=('<title>Soul Charger Editor</title>\n'
      '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
      '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600&display=swap">\n'
      '<style>\n/* Sistema de diseño de Immersive Studio Pro / VEATION — copia literal de index.html:16-1201 (sin comentarios) */\n'+css+'\n</style>\n')
art=head+body
(here/"editor-obra-mockup.html").write_text(art,encoding='utf-8')
(here/"preview.html").write_text('<!doctype html>\n<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">\n'+head+'</head><body>\n'+body+'\n</body></html>',encoding='utf-8')
print('css', len(css), 'bytes · artifact', len(art.encode('utf-8')), 'bytes')
