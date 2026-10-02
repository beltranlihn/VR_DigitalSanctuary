# Soul Charger Editor (app)

Editor web de la obra: timeline por grupos y sub-pistas, inspector, integridad contra Unreal y vista 3D del prototipo. Plan y diseño en [`docs/editor-obra/PLAN-EDITOR-OBRA-2026-10-01.md`](../../../docs/editor-obra/PLAN-EDITOR-OBRA-2026-10-01.md).

## Abrirlo
- **Windows:** doble clic en `tools/editor/abrir-editor.bat`. Cerrar esa ventana apaga el editor.
- **Terminal:** `python tools/editor/serve_editor.py --open` (puerto 8767 por defecto) → http://localhost:8767/editor-obra/app/
- **Segunda pestaña solo con la vista 3D:** `Window ▸ Open the 3D view in a new tab`. Las dos pestañas comparten cabezal, play y ediciones.

Solo usa la biblioteca estándar de Python y JS sin build (ADR-0001 de ISP).

## Archivos
| Ruta | Qué es |
|---|---|
| `obra/score/score.json` | **La partitura** (fuente de verdad). Ctrl+S la guarda; la versión anterior va a `obra/score/history/`. |
| `obra/unreal/contract.json` | Qué está cableado o es perilla en Unreal y qué rompe cada edición (capa C3 de integridad). |
| `obra/unreal/roles.json` | Perillas reales por rol, con dueño y candado de valor final (solo lectura hasta el puente F3). |
| `obra/audio/inbox/` | WAV nuevos cargados desde el editor; se importan a Unreal más adelante, en la cola. |
| `js/engine.js` | Motor de tiempos: misma semántica que `prototipo-narrativo/timeline.js`. Lo verifica `node tools/score/golden_test.mjs`. |
| `js/integrity.js` | Problemas estáticos (C1/C2/C3) e ítems de la tarjeta de impacto. |
| `js/app.js` | Estado, verbos de edición (todo pasa por `commit` → integridad), deshacer, guardar, 3D, teclado. |
| `js/ui.js` | Render (top, librería, transporte, timeline, inspector, Problems) e interacciones con el puntero. |
| `css/isp.css` | CSS literal de ISP. **No se edita a mano:** se regenera con `python tools/editor/sync_isp_css.py`. |
| `css/editor.css` | Solo lo que ISP no tiene. |

Para regenerar la partitura desde el prototipo se usa `node tools/score/extract_v1.mjs`. **Ojo:** pisa las ediciones.

## Atajos
| Atajo | Acción |
|---|---|
| Espacio | play |
| Home / End | ir al inicio o al final |
| ←/→ | mover el cabezal 0,1 s (con Shift, 1 s) |
| Alt+←/→ | mover el elemento seleccionado |
| Shift+A | agregar |
| M | marcador |
| Shift+M | nota |
| Alt+T | pista nueva |
| Supr | borrar |
| Ctrl+Z / Ctrl+Shift+Z | deshacer / rehacer |
| Ctrl+S | guardar |
| F8 | Problems |
| A | curvas de anclas |
| Ctrl+rueda | zoom |
| Doble clic en el nombre de una pista | renombrarla |
