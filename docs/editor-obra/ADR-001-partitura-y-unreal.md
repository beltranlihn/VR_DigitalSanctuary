# ADR-001 · Cómo llegan los tiempos de la partitura a Unreal

**Estado:** propuesto. Lo aprueba Beltrán (decisión 6 de la lista del [anexo 18](anexos/18-auditoria-app.md#decisiones-que-necesito-de-beltrán)).
**Fecha:** borrador del 2026-10-02 (diseño A §8.2, [anexo 19](anexos/19-lote5-diseno-unreal.md)); ajustado a lo construido en el lote 5 el 2026-10-14.
**Deja sin efecto** estas partes del [PLAN](PLAN-EDITOR-OBRA-2026-10-01.md): §3.3 (DataTable, `ScoreApply` y reconciliación de tres vías), la fase F4 de §4 y la decisión 1 de §6.

## Contexto
El PLAN pedía compilar la partitura a una DataTable con structs nuevos, reconciliar en runtime tres valores (el de la partitura, el de la última importación y el de la instancia) y un `ScoreApply` que escribiera perillas de instancia.

El acuerdo del 2026-10-02 con el Director (`obra/unreal/LEEME.md`) y el [anexo 11](anexos/11-herramientas-consolidado.md) dicen otra cosa: manda el DataAsset `DA_Partitura_Obra`, la web propone y Unreal aplica. Donde el PLAN y el acuerdo chocan, este ADR fija lo que se hace.

El lote 5 construyó del lado web todo lo que esa decisión necesita. Este documento deja escrito qué se decidió y qué se construyó, para que nadie tenga que reconstruirlo del código.

## Decisión
1. **Formato.** Los tiempos narrativos que Unreal obedece viven en el DataAsset `DA_Partitura_Obra` (60 perillas, ver `docs/PARTITURA.md`). No hay DataTable ni structs nuevos. Unreal no lee la partitura web en runtime.
2. **Quién escribe.** El editor web nunca escribe `.uasset` ni habla con Unreal. Propone con `obra/unreal/partitura_propuesta.json`, y solo con el botón **Send to Unreal** después de su tarjeta de revisión.
3. **Quién aplica.** Una sesión con el editor de Unreal abierto, solo cuando Beltrán lo pide: respaldo, aplicar, prueba de humo y, si falla, restaurar. Nada se aplica porque un archivo apareció.
4. **Perillas de instancia** (`FW_*`, `ExploreTime`, etc.). Son de solo lectura en la web hasta que exista una cosecha de instancias. No hay reconciliación de tres vías en runtime: si hace falta, ocurre al proponer (el valor base, con su hash, contra el valor vivo).
5. **La partitura** (`obra/score/score.json`) es la fuente de la estructura y del previs. Ninguna herramienta la reescribe. Todo cambio de formato es una operación de la app, con tarjeta y deshacer, y la guarda el usuario:
   - **Upgrade to schema 3**, una sola operación que no mueve ningún tiempo del usuario típico (ramas SHARE / DON'T SHARE, esperas como en Unreal, nombres estables, referencia de "≠ APK" dentro de la partitura);
   - **Bind to Unreal**, un paso aparte y opcional sobre schema 3 (marcas de Unreal por momento y `bind` por elemento). Tampoco mueve nada.
6. **La referencia de "≠ APK" vive dentro de la partitura.** Es `baseline` en schema 3 (`golden` en schema 2) y solo se mueve por una operación explícita, en la misma edición que la compensa (`Edits.shiftBaseline`: las voces reales, **Match Unreal**). No hay un archivo aparte con la foto congelada. Lo que Unreal puede medir se juzga por su cuenta y en capas:
   - lo que gobierna una perilla, contra la Partitura (`C3.PARTITURA`);
   - las fases de la obra, contra `traza.json` (`C3.TRACE.*`);
   - el resto, contra la referencia que lleva la partitura.
7. **Reglas al guardar.** Son las mismas en el navegador (`js/check.js`), en la terminal (`tools/score/check.mjs`) y en el servidor, que ejecuta ese mismo `check.mjs` con `node` dentro de su bloqueo de escritura. No hay un segundo motor en Python. Solo se rechaza (`422`) lo **nuevo** respecto de lo que hay en disco, y si la comprobación no puede correr el guardado sigue y lo dice (falla abierta). El schema solo sube.
8. **Cues por marca.** `compile.mjs` funciona solo en seco: informa qué llegaría a Unreal, qué es previs y por qué, y nunca escribe nada de Unreal. Si en F4 existe `BP_ScorePlayer_SC`, su tabla la escribe el Director a pedido, con el mismo respaldo y la misma prueba de humo.
9. **`guion.js` es una fuente de importación, no la verdad.** Se compara con la partitura (**File ▸ Check guion.js for changes…**) y se toma solo lo que el usuario elige. `traza.json` es la medición de lo que Unreal hace y nunca cambia la partitura.
10. **Contrato y perillas por id.** `contract.json` y `partitura_binding.json` enlazan por id de elemento. El nombre (`key`) es una etiqueta que se puede cambiar sin sacar al elemento de lo que Unreal conoce. El catálogo de perillas que lee una máquina es `obra/unreal/knobs.json`.

## Qué lo cumple (lote 5)
| Decisión | Pieza | Prueba |
|---|---|---|
| 2, 3 | Send to Unreal y su tarjeta (lote anterior); `LEEME.md` | `server_test.py` |
| 5 | `Edits.migrate3` (Problems ▸ Upgrade…), `Edits.bindUnreal` (Experience ▸ Bind to Unreal…) | `migrate3_test.mjs`, `bind_unreal_test.mjs` |
| 6 | `baseline`, `Edits.shiftBaseline`, `Integrity.divergent` por capas, `js/calib.js` | `integrity_test.mjs`, `calib_test.mjs`, `golden_test.mjs` |
| 7 | `js/check.js`, `tools/score/check.mjs`, `full_check()` en `serve_editor.py` | `check_test.mjs`, `server_test.py` |
| 8 | `js/compile.js`, `tools/score/compile.mjs`, `js/reach.js`, `tools/score/idmap.mjs` | `compile_test.mjs`, `reach_test.mjs`, `idmap_test.mjs` |
| 9 | `js/importdiff.js`, `tools/score/import_report.mjs`, `POST /api/guion/scan` | `import_test.mjs`, `server_test.py` |
| 10 | `tools/score/bind_ids.mjs`, `tools/score/knobs.mjs` | `bind_ids_test.mjs`, `knobs_test.mjs` |

El detalle de cada una, lo que se verificó y los límites están en el [anexo 18](anexos/18-auditoria-app.md), "Estado del lote 5".

## Alternativas descartadas
- **DataTable con structs y `ScoreApply` con tres vías** (PLAN §3.3). El MCP no crea structs, habría dos fuentes de verdad en runtime y la reconciliación podía pisar valores que Beltrán puso a mano.
- **La foto congelada en un archivo aparte** (diseño A §6.7, `obra/score/baselines/f0.json`). Las operaciones que mueven la referencia tienen que ir en la misma edición que el cambio que compensan; con dos archivos, deshacer, el borrador, el conflicto de versiones y guardar dejaban de ser una sola operación.
- **Portar la comprobación al servidor en Python.** Los ciclos de anclas dependen del orden exacto de evaluación del motor: en un prototipo, una llamada fuera de lugar movió 2264 tiempos. Un segundo motor habría que mantenerlo idéntico para siempre. Llamar a `node` cuesta unos 0,1 s por guardado, con un solo usuario y en local.
- **Una sola migración con marcas y assets** (diseño A §3.6). Mezclaba un cambio de semántica (esperas, ramas) con un enlace que el dueño todavía no revisó (la semilla de marcas sigue "proposed"). Separadas, se puede mejorar el schema sin decidir las marcas.

## Consecuencias
- El PLAN lleva una nota "superseded by ADR-001" en §0 (fila "Runtime en el Quest"), §3.3, §4 (F4), §5 (riesgo 2) y §6 (decisión 1).
- La partitura real sigue en schema 2. Mejorarla, enlazarla y guardarla son tres pasos del dueño, cada uno con su botón.
- Una pestaña vieja del editor ya no puede guardar sobre un schema 3: después de guardar una mejora hay que recargar las otras pestañas.
- El servidor necesita `node` solo para la comprobación completa al guardar. Sin él guarda con `check: 'structural-only'`.
- Lo que falta del lado de Unreal está en [PEDIDOS-AL-DIRECTOR.md](PEDIDOS-AL-DIRECTOR.md).

## Lo que sigue abierto
- La aprobación de este ADR.
- `BP_ScorePlayer_SC` no existe: cualquier cue sale con estado `no-player`.
- La cosecha de perillas de instancia, las marcas `SHARE.*` y la lectura de `HelpAfter` (ver los pedidos al Director).
