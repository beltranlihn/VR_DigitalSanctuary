# Pedidos del editor web al Director (sesión de Unreal)

**Fecha:** 2026-10-14, al cerrar el lote 5 del editor ([anexo 18](anexos/18-auditoria-app.md), "Estado del lote 5"). **Ya quedó dicho en el [ADR-001](ADR-001-partitura-y-unreal.md):** el editor web no escribe `.uasset`, no habla con Unreal y no aplica nada; lo que Beltrán decida mandar sigue yendo por **Send to Unreal** y `partitura_propuesta.json`.

Este archivo existe porque `obra/unreal/LEEME.md` es del Director y la web no lo edita. Todo lo de abajo se contesta o se hace en el turno del Director, cuando Beltrán lo pida. Ninguno es urgente para que la web funcione: cada pedido dice qué habilita.

**Lo que la web no tocó:** `partitura.json`, `perillas.json`, `traza.json`, `LEEME.md`, `partitura_propuesta.json`, `VR_Test/`, `tools/unreal/`. De `VR_Test/` solo lee archivos (ver la sección D).

## A. Para la tabla de `obra/unreal/LEEME.md`

Archivos que el editor web escribe o genera. Los cinco primeros ya figuran en la tabla; el contenido de algunos cambió. Los demás son nuevos y hay que anotarlos.

| Archivo | Lo escribe | Qué es |
|---|---|---|
| `contract.json` | web, con `tools/score/bind_ids.mjs` | Ya figura. Ahora enlaza por id de elemento (`ids`, `idKeys`, `idsFrom`, `excludeKeys`) y suma tres entradas: `vo.unused`, `vo.noasset` (ver B2 y B3) y `help.after` (ver B1). |
| `roles.json` | web | Ya figura. Sin cambios en este lote. |
| `partitura_def.json` | web, con `tools/editor/sync_partitura.py` | Ya figura. Sin cambios. |
| `partitura_binding.json` | web, con `bind_ids.mjs` | Ya figura. Ahora fija por id, por etapa, qué elemento gobierna cada perilla. Sigue siendo un borrador que valida el Director (ver B6). |
| `partitura_drift.json` | web, con `tools/editor/partitura_drift.mjs` | Ya figura. No se volvió a generar en este lote. |
| `idmap.json` | web, con `node tools/score/idmap.mjs --deps auto` | **Nuevo.** Qué asset de Unreal es cada sonido de la partitura (185 assets, 1 ambiguo). Es una foto: `--check` dice cuándo está vieja. |
| `idmap_aliases.json` | una persona de la web; lo revisa el Director | **Nuevo.** Los 19 sonidos cuyo nombre en la partitura difiere del asset (`FX_BELLRING` es `Bell`). Ver B5. |
| `knobs.json` | web, con `node tools/score/knobs.mjs` | **Nuevo.** El catálogo de perillas en un formato que lee una máquina: 60 de la Partitura (las únicas proponibles), 50 de instancias, 4 literales y 1.203 de las clases (de `perillas.json`). |

Fuera de `obra/unreal/`, por si el Director los ve en el repo: `obra/score/seed/marks-v1.json` (la semilla de marcas por momento, "proposed, pending owner review"), `obra/audio/media_map.json` (qué archivo suena en el 3D del editor para cada efecto y ambiente) y `obra/score/score.extracted.json` (la extracción de `guion.js`, ignorada por git).

## B. Confirmaciones (un sí, un no o un dato)

1. **`HelpAfter`: ¿cuenta desde el fin de `VO_11b` o desde su inicio?** El tracker de `BP_BreathStage_SC` dice "`VO_11h` `HelpAfter` s después" y la web lo lee como "después de que **termina** `VO_11b`" (`SayEndAt`). Habilita **Match Unreal** sobre `VO_11h` (3:50,1 a 3:57,1; el lento deja de oírla). Si cuenta desde el inicio, cambia una palabra en la entrada `help.after` de `contract.json` y nada más.
2. **Las 10 voces que `BP_Obra_SC` ya no llama** (`VO_01d`, `VO_01h`, `VO_04b`, `VO_06a`, `VO_24`, `VO_34c`, `VO_35c`, `VO_36`, `VO_36c`, `VO_36d`). La web las pasó de "cableadas" a **no están en Unreal** (`vo.unused`), según la línea "VO viejas que quedan sin uso" del tracker de `BP_Obra_SC`. `bind_ids.mjs` la vuelve a leer en cada corrida: si el tracker cambia, la web lo nota. Confirmar la lista.
3. **`VO_12b`, `VO_17b` y `VO_21` no tienen grabación** en `Content` ni en los plugins (`vo.noasset`). ¿Son `VO_12f1` y `VO_12f2` (Breath), se descartaron o falta importarlas? Mientras no se sepa, la web las marca "sin grabación en Unreal".
4. **`VO_12c` existe dos veces**, en `Mechanics/Breath/Audio` y en `Obra/Audio`, con bytes distintos. ¿Cuál es la viva? Mientras tanto el `idmap` la marca ambigua y la partitura no la enlaza a ningún asset. (Del otro lado: `VO_35a`, `VO_12f1` y `VO_12f2` están en Unreal y no en la partitura. ¿Deberían estar?)
5. **Los alias de `idmap_aliases.json`** (su campo `reviewed` está en `null`): revisarlos y anotar la fecha. Por ejemplo, `FX_CHARGE_1` a `FX_CHARGE_4` apuntan al mismo `Charge1` (Unreal reproduce un solo sonido de carga para las cuatro etapas) y `AMB_01` a `AMB_09` a los `Ambient_Clip_*`.
6. **`partitura_binding.json`**: validar los 31 enlaces (qué elemento de la partitura gobierna cada perilla), en especial los marcados como aproximados (`~` en `partitura_drift.mjs`).
7. **Qué voces van en 2D** (`vo_2d`, sin Alma): la web supone `VO_33`, `VO_35a`, `VO_35b` y `VO_37`, por la frase "las VO siguen en 2D" del tracker.
8. **`ALMA_GONE` y `ALMA_BACK`** (6 movimientos de Alma en la partitura: `ALMA_GONE` en el outro de las etapas 0 a 3 y en `FINAL.EXIT`, y `ALMA_BACK` en `FINAL.RESULTS`): ¿los hace solo `BP_Obra_SC` (`AlmaIn`, `AlmaOut`, `FlowShare`)? Si es así, una entrada `wired` del contrato (`alma.verbs`) los saca de los "cue-ready" y la cuenta vuelve de 18 a 12.
9. **Las esperas de SAVE** (`G_SAVE4` y `G_SAVE5`): ¿qué perilla es el tiempo de espera, `Etapa_Tope` más `Corte_Espera`, u otra? Hoy la web les pone una condición pero ninguna perilla, porque es ambiguo.
10. **Las esperas del Hall**: la partitura tiene `G_SENSOR` en 15 s (`FW_Tool` vale 20) y `G_CHOOSE` en 30 s (`FW_Choose` vale 25). Es un asunto del dueño (la web ya lo muestra como `C3.DRIFT` con **Match Unreal**), pero conviene confirmar que 20 y 25 son los valores de la obra.
11. **El final de la rama de SHARE.** La web quiere ofrecer más adelante filas "Match Unreal" y necesita confirmar lo que hace Unreal: `ShareAnswer` ya no reproduce `VO_36c` ni `VO_36d`; en DON'T SHARE no suena `VO_35c` y `VO_37` va en PT 8; en SHARE, `VO_35b` va en PT 8 y `VO_37` en 8 + duración de `VO_35b` + 0,6 s.
12. **Seguimientos de Entering** (sin urgencia): `VO_27h` a los 20 s y `VO_32h` a los 15 s (`cues.34`), y el `SayGap` de `VO_11b` (0,5 s: movería 435 elementos de la partitura +0,5 s). ¿Siguen valiendo esos números?

## C. Trabajo en Unreal, cuando haya turno

13. **`smoke_obra.py --traza`: más datos.** Solo Python, sin cambios de Blueprint. La web ya sabe leerlos si aparecen y los ignora si no están (`js/marks.js`, `traceInfo` y `traceSubs`):
    - `config`: el objeto de la línea `OBRA CONFIG:` (`bSimulated`, `bDisclaimer`, `Speed`, `DebugStart`).
    - `partitura_hash`: el `hash` de `partitura.json` en el momento de la corrida (para decir "la corrida es anterior a la última exportación").
    - `hall`: `[{ mode, step, reloj_obra_s }]` de las líneas `HALL: modo M paso N`.
    - `vo`: `[{ clip, reloj_obra_s, dur }]` de las líneas `ALMA: SayClip`.
    - `marks`: `[{ name: 'S<K>.REQEND', reloj_obra_s }]` de la línea "se le pide que cierre".
    - **Historial:** guardar cada corrida como `obra/unreal/trazas/traza-<tag>.json` y dejar `traza.json` como la última (la web mide el ruido entre corridas y sube sola sus umbrales).
14. **Correr `smoke_obra.py --speed 1 --traza` dos veces.** Con una sola corrida no se sabe cuánto es ruido (regla "una línea de base son dos pasadas"). Los umbrales de la web (3 s por etapa, 1 s por segmento) quedan provisorios hasta tener las dos.
15. **`tools/unreal/deps.py` para los plugins.** Hoy solo lee `/Game`: los assets de `SC_Base`, `SC_Draw`, `SC_Breath` y `SC_Sequencer` salen con `referencedBy: null` y la web los trata como "llamados por Unreal" (del lado seguro). Afecta a cinco elementos (`FX_CHARGE_1` a `FX_CHARGE_4` y `FX_CHARGEFINAL`).
16. **Más adelante (F4, no este lote):**
    - emitir las marcas `SHARE.ASK`, `SHARE.YES` y `SHARE.NO` desde `FlowShare`;
    - una cosecha de las perillas de **instancia** (hoy son solo lectura en la web, con los valores que alguien anotó en `roles.json`);
    - decidir si `BP_ScorePlayer_SC` llega a existir. Mientras no exista, todo cue de la web sale con estado `no-player`.

## D. Para que lo sepa (sin pedido)

- **La web solo lee `VR_Test/`.** `idmap.mjs` recorre los `.uasset` de las carpetas `Audio/` (y los `DA_Ghost_*`) de `Content` y de los plugins, y corre `tools/unreal/deps.py` en una carpeta temporal para `referencedBy` (sin reescribirlo). El servidor del editor sirve, en solo lectura, los archivos de audio que nombra `media_map.json` (algunos con ruta `unreal:`, dentro de `VR_Test/`).
- **Rutas que escribe la web en sus archivos:** al 2026-10-07 las únicas son tres carpetas de voces, en el mensaje de `vo.wired` (`/Game/SoulCharger/Obra/Audio`, `/Game/SoulCharger/Mechanics/Breath/Audio`, `/Game/SoulCharger/Hall/Audio`), y siguen en su lugar. `roles.json` y `partitura_binding.json` guardan nombres de Blueprints, no rutas; si algo se mueve, `bind_ids.mjs` lo informa. Dueños de hoy: `BP_Pacer_SC` está en `/SC_Breath/Blueprints`; `BP_BreathStage_SC` sigue en `/Game/.../Mechanics/Breath/Blueprints`.
- **Los nombres `SND_PacerPad` y `SND_PacerPluck`** de `roles.json` son nombres de familia: cada uno son tres assets (`...Inhale`, `...Hold`, `...Exhale`), hoy en `/SC_Breath/Audio`.
- **Lo que pasó con los tiempos:** el editor ya puede mejorar la partitura a schema 3 y enlazarla con marcas de Unreal, pero ninguna de las dos operaciones está aplicada (la partitura real sigue en schema 2) y ninguna cambia lo que Unreal hace. Lo único que llega a Unreal es lo que Beltrán envíe con **Send to Unreal**.
- **Dónde está el detalle:** el anexo 18 ("Decisiones que necesito de Beltrán", la lista de las decisiones del dueño), el [ADR-001](ADR-001-partitura-y-unreal.md) y los diseños del lote 5 (anexos [19](anexos/19-lote5-diseno-unreal.md) y [20](anexos/20-lote5-diseno-partitura.md), §10 y §12).

## Respuestas del 2026-10-15 (aplicadas en la partitura rev 3)
Los puntos B1, B3, B4 (en parte), B8, B9, B10 y B11 quedaron respondidos y aplicados (detalle en el anexo 18).

**Siguen abiertos:**
- **B2:** `VO_01h` y `VO_04b` (`BP_HallDirector_SC` todavía los referencia).
- **B7:** si `VO_35b` y `VO_37` van en 2D.
- **B5 y B6:** idmap y enlaces de la Partitura.
- **B12:** seguimientos de Entering.
- **Sección C completa.**
