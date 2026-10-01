> Anexo de la auditoría del 2026-10-01 (propuesta de arquitectura (antes de la crítica)). Lo que manda es [PLAN-EDITOR-OBRA-2026-10-01.md](../PLAN-EDITOR-OBRA-2026-10-01.md); donde este anexo lo contradiga, gana el plan.

# Diseño de arquitectura e integración: editor de la obra (partitura, Unreal, ISP)

## 0. Decisiones en una línea

| Tema | Decisión |
|---|---|
| Fuente de verdad | **Partitura en texto en el repo** (`obra/score/`). La base del artifact es la mesa de trabajo y Unreal es el compilado. Cada documento tiene **un solo dueño** que escribe. |
| Runtime en Unreal | `BP_ScorePlayer_SC` dispara cues a partir de **marcas** que emite la Obra, más una capa de **perillas** que lee `BP_Obra_SC`. Los datos van en una DataTable cocinada. |
| Interfaz | **Se trasplanta el código de ISP**: CSS completo, esqueleto DOM y funciones de timeline, inspector, transporte, menús y estado, copiadas con su línea de origen. No se imita su aspecto. |
| Stack | Vanilla JS sin build (ADR-0001 de ISP), scripts clásicos por dominio y three r128. Un motor puro que también corre en Node. |
| Ventanas | Patrón **un solo realm, dos ventanas** de ISP (`openViewerWindow`), con BroadcastChannel como respaldo. |
| Hosting | El mismo artifact (`editor.html` junto al `index.html` viejo, la misma base) y, más adelante, un puente local opcional solo para Beltrán. |

---

## 1. Fuente de verdad: la partitura

| | A. JSON en el repo; la web lo edita; Unreal lo importa | B. Unreal es la verdad; la web es una vista por Remote Control | C. Híbrido: dueño por campo |
|---|---|---|---|
| A favor | Texto que se puede diffear y mergear. El socio no necesita Unreal. Se cocina en el APK. Es el patrón de Theatre.js: un editor y dos runtimes. | Cero duplicación de valores. | Respeta que el espacio y el look **son** de Unreal. |
| En contra | Exige migrar los literales de `BP_Obra_SC`; sin eso, el editor es un dibujo. | RemoteControl no está activo y jamás corre en Quest (`RemoteControl.uplugin:44-47`). El editor es único y compartido. Los tiempos son **literales en grafos** (536 floats), no propiedades. El socio necesitaría Unreal abierto. | Más complejo de explicar. |

**Elijo A con la regla de propiedad de C.** El tiempo y la estructura viven en la partitura. Las posiciones, el look y los umbrales de las mecánicas viven en Unreal y la web los ve en modo lectura. La regla de propiedad se aplica **por documento**, no por campo suelto: cada colección tiene una sola clase de escritor, así que no hay conflictos entre fuentes.

| Colección (base del artifact) | Escribe | Contenido |
|---|---|---|
| `score/*` | el editor (Beltrán, socio) | actos, momentos, grupos, sub-pistas, elementos, esperas, ramas, marcadores, looks |
| `unreal/*` | **solo** la cosecha (sesión de Claude en su turno) | poses de TP y actores con tag, duración real de cada VO, `ImportedRev`, valores de instancia de las perillas, trazas `SCORE\|t\|marca` |
| `proposals/*` | el editor | cambios espaciales ("mover `sc3_alma_side` 40 cm a la izquierda") que una sesión aplica en Unreal y que vuelven por la cosecha |
| `audio/*` | el editor (como hoy) | audios de vista previa, `sc-audio-v1` (`timeline.js:433-450`) |
| `presence/*`, `versions/*` | el editor | presencia, bloqueos suaves, versiones con nombre |

**El repo es el registro canónico.** Una sesión vuelca `score/*` a `obra/score/*.json` en cada hito y lo commitea. Unreal importa **desde ese archivo**, nunca desde la base. Así, lo que corre en el APK siempre corresponde a un commit.

**Unreal propone y la partitura decide; nada se pisa en silencio.** Si Beltrán cambia una perilla en el panel de Detalles, la cosecha detecta que el valor de la instancia no coincide con el de la DataTable y el editor ofrece adoptarlo. Esto cumple la regla de que los valores de los niveles de test son finales.

**Las duraciones de VO son de Unreal:** las mide `GetDuration`, se suman al snapshot y el editor no las deja editar (es la única excepción a "tiempos por timeline").

---

## 2. Modelo de datos (schema 2)

Este esbozo es ilustrativo, no un JSON válido.

```json
{ "schema": 2, "rev": 44, "hash": "sha1…",
  "acts":   [{ "id":"act_4", "name":"Entering", "beats":["bt_01J…"] }],
  "beats":  { "bt_01J…": { "key":"4.R5", "title":"…", "at":{"mark":"S0.P6","off":0} } },
  "groups": [{ "id":"grp_alma", "name":"Alma", "family":"video", "accepts":["obj","vo","title"],
               "lanes":["ln_a1","ln_a2"], "collapsed":false, "mute":false, "solo":false, "lock":false }],
  "lanes":  { "ln_a1": { "name":"Alma 1", "h":28 } },
  "elements": { "el_01J…": {
      "key":"VO_11h", "type":"vo", "beat":"bt_01J…", "lane":"ln_a2",
      "at":{ "ref":"el_GBREATH", "edge":"start", "off":12 },
      "dur":{ "mode":"audio" },
      "target":"role:alma", "action":{ "id":"alma.say", "p":{ "sound":"VO_11h" } },
      "help":"el_GBREATH", "branch":null,
      "legacy":{ "uid":"2.R4/VO_11h", "src":"guion.js:370" } } },
  "gates":   { "el_GBREATH": { "cond":"sensor.inBelly", "expected":6, "helpAfter":12, "fw":25,
               "onFw":"same-as-done", "outs":["done","late","fw"] } },
  "branches":{ "br_share": { "gate":"el_GSHARE", "takes":{ "yes":{}, "no":{ "default":true } } } },
  "markers": { "mk_…": { "at":{"ref":"bt_…","off":3.2}, "dur":0, "note":"…", "author":"socio", "state":"open" } },
  "looks":   { "intro": { "fogTop":"#…" } },
  "roles":   { "role:alma": { "web":"alma", "unreal":{ "tag":"Alma", "class":"BP_Alma_SC" } } },
  "catalog": "catalog@7" }
```

**Entidades y reglas**
- **Elemento.** Tiene `type` ∈ {`vo`, `sfx`, `amb`, `hap`, `obj`, `title`, `veil`, `ghost`, `pawn`, `look`, `gate`, `mech`, `marker`}. Tres campos que hoy están mezclados quedan separados:
  - `lane` es **dónde se dibuja**;
  - `target` es **sobre qué actúa**, un rol que Unreal resuelve por tag, como los bindings Replaceable de Sequencer;
  - `action` es **qué hace**: un id de un catálogo cerrado (~25-30 comportamientos) con un esquema de parámetros.
  
  Por eso mover un clip de sub-pista nunca cambia su comportamiento.
- **Duración.** `dur.mode` ∈ `fixed | audio | until | elastic`.
  - `audio` solo se permite en `vo`; el validador rechaza un FX que "dura su WAV".
  - `until` reemplaza al `end` actual (`timeline.js:73-74`).
  - `elastic` es solo para esperas y mecánicas.
- **Ancla.** `{ref, edge, off}` en **segundos reales**, sin el factor `k`. Hoy `d` se guarda como "tiempo base dividido por `k`" (`timeline.js:736`, `:864`), así que el mismo número cambia de sentido si se mueve un locator. El warp de los locators deja de ser un estado y pasa a ser una **operación** ("Estirar sección"), que reescribe los desfases una vez y entra en el deshacer.
- **Marca.** Es la raíz de todo ancla y **el puente con Unreal**. Vocabulario cerrado que emite la Obra:
  - `OBRA.START`
  - `S<K>.P<n>` (entrada a la fase n de la etapa K)
  - `HALL.<modo>.<paso>`
  - `GATE.<id>.<done|late|fw>`
  - `VO.<id>.end`
  - `MECH.<K>.<evento>` (`DONE`, `INK>0.3`)
  - `FINAL.<estado>`
  
  Casi coincide con el índice `DebugStart` (`TRK/BP_Obra_SC.md:129-160`), que da gratis "Probar desde aquí".
- **Espera (gate).** `expected` sirve solo para simular las personas (rápido, típico, lento, ausente). `fw` es una perilla que se exporta. `cond` se elige de un vocabulario que sale del contrato de cada mecánica, nunca de un closure. Las salidas tienen nombre: `done`, `late`, `fw`.
- **Rama.** Tomas alternativas con duración propia. Hoy las dos ramas ocupan el mismo horario y el fin del momento es el de la más larga (`timeline.js:115`). En la UI cada toma es una pestaña de secuencia.
- **Grupo → sub-pistas.** Ver §5.3. El clip referencia `lane` por **id**. Ojo: en ISP los clips referencian la pista por **índice** (`c.lane===li` en `app.js:5480`; `startLaneDrag` remapea índices en `app.js:6820`), y eso hay que cambiarlo al trasplantar.
- **Identificadores.** ULID con prefijo (`el_`, `bt_`, `ln_`, `grp_`, `mk_`). El `key` legible (`VO_11h`) es un campo editable, sin valor de llave. Se acaban los `#n` por orden de declaración.
- **Versionado.** `schema` entero, migraciones puras `migrate[n](doc)` y un `catalog@N` aparte, porque los comportamientos evolucionan más rápido que el esquema. `rev` sube en cada guardado y `hash` es el SHA-1 del JSON canónico (claves ordenadas).

### Migración sin perder los ajustes de Beltrán
1. **Extracción.** `tools/score/extract_v1.mjs` evalúa `world`-stub + `guion.js` en Node, como ya hizo la auditoría. Los ayudantes (`vo`, `fx`, `walk`, `gate`, `ghostSpan`, `teleport`, `veilBeat`…) se envuelven para registrar el ayudante, los argumentos y la línea de llamada (`legacy.src`).
2. **Clasificación.** Los ayudantes se mapean solos. Los `clip({apply})` literales (147) se mapean a mano en `legacy_map.json`. Lo que quede sin mapear se marca `action:{id:"legacy"}`: la vista previa web sigue ejecutando el closure original por `legacy.uid`, con el patrón *strangler*, y la UI lo marca como "solo web, no portado a Unreal".
3. **Ajustes.** Se aplica `timeline/main` v78 sobre los uids: 17 edits, con los `#n` resueltos en el mismo orden de declaración que hoy. Se informan los 4 que no tienen efecto (los `dur` de `AMB_01/02/03` y `VO_01c`). Los 9 locators están en k = 1, así que no cambian nada. `LOOK.intro` pasa a `looks`. `audio/*` no se toca: se sigue indexando por soundId.
4. **Prueba dorada.** El motor nuevo tiene que resolver los 592 elementos con inicio y fin iguales a `computeSchedule` (±1 ms), con y sin los edits. Sin eso no hay fase 1.
5. **Reconciliación con Unreal** (después de la prueba dorada). Se ingiere el snapshot (§3). Donde Unreal ejecuta el valor, **gana Unreal**, porque es lo aprobado. Cada diferencia queda como **divergencia en ámbar** para que Beltrán la resuelva:
   - largos de VO;
   - cortafuegos de Recognizing 150 contra 180;
   - aviso 20 contra 9;
   - `G_SENSOR` 15 contra 20;
   - `G_CHOOSE` 30 contra 25;
   - los 17 edits del Hall contra los `Pace*` de `BP_HallDirector_SC`.
   
   Son unas 30 decisiones, una vez.
6. **`ensayo.js` desaparece**, reemplazado por `unreal/snapshot`. `ensayo_export.py` vive en `VR_Test/Saved/ClaudeScripts/obra/`, que **está en `.gitignore`** (`.gitignore:10`), y `gen_ensayo_js.py` está en el scratchpad de otra sesión. Los dos se reescriben como `tools/unreal/harvest_score.py`, versionado. La cosecha lee los subniveles ya cargados y no hace `load_level` (`ensayo_export.py:37,61` cambia hoy el nivel del editor compartido).

---

## 3. Sincronización con Unreal

### 3.1 Compilación: Unreal no resuelve anclas
`tools/score/compile.mjs` usa el mismo motor puro que la web. Aplana cada cue a `{Mark, Offset}`: recorre la cadena de anclas de duración fija hasta la marca más cercana. Las cadenas que pasan por algo no determinista (fin de una VO, salida de una espera) **son** marcas. El resultado, `obra/score/build/score_unreal.json`, tiene dos tablas:
- **Cues:** `Id, Mark, Offset, Action, Target, Asset, P1..P4, Note`.
- **Perillas:** `Name, Value, Note`. Son los ~30 literales que importan al montajista: título y velo, Alma a T 5,8, cortafuegos 180/120/240, cierre 69→71,5, velo de la última carga, `FlowShare`/`FlowConst` y el aviso.

Así el runtime del Quest no hace más que comparar tiempos.

### 3.2 Formato cocinado
- **Preferido: DataTable con *Reimport*.** Beltrán crea a mano, una sola vez, dos structs: `F_ScoreCue_SC` y `F_ScoreKnob_SC`. El MCP no crea structs (`gotchas.md:305`, `:670`). Con eso, `DT_ScoreCues_SC` y `DT_ScoreKnobs_SC` apuntan a su JSON fuente, y **Beltrán reimporta solo, sin Claude y sin pedir turno en la cola**. Para una sesión, también se puede importar con `DataTableTools.import_file`.
- **Plan B sin paso humano:** un DataAsset con arrays paralelos de primitivos, como el precedente `DA_Ghost_*` (`TRK/BP_GhostPlayer_SC.md:53-54`).
- La tabla queda **referenciada en firme** por `BP_ScorePlayer_SC`, así que se cocina sola. No hace falta tocar el staging ni los `.ini` temporales.
- El proyecto **no tiene `Source/`** (solo Blueprints). Leer JSON en runtime exigiría JsonBlueprintUtilities (Beta, no activo), por eso queda para la fase opcional.

### 3.3 `BP_ScorePlayer_SC` (actor nuevo; el director no lo conoce)
- **BeginPlay**
  - Indexa los cues por marca en arrays ordenados por desfase.
  - Escribe `ImportedRev` y `ImportedHash` en el log.
- **Tick**
  - Observa los flancos de `Obra.Phase/Stage/PT`, `Hall.Mode/Step`, `bStageDone`, el fin de VO y las salidas de las esperas. Es el patrón observador ya probado en `BP_HallTitle_SC`, `BP_HallGlow_SC` y `BP_HallAmbience_SC`.
  - En cada marca arranca un cursor. Por cuadro solo mira **el próximo índice** de cada cursor activo: O(cursores), sin buscar en Map.
- **Acciones:** vocabulario cerrado.
  - VO: `Alma.SayClip` o 2D.
  - SFX en un rol, con `ATT_Objeto_SC`.
  - Cambio de ambiente con crossfade.
  - Mostrar u ocultar un rol (con su animación de entrada; nada aparece de golpe).
  - Rampa de un parámetro escalar.
  - Fantasma Play/Stop.
  - Subtítulo.
- **Presupuesto Quest**
  - Como mucho **una aparición por cuadro**; las siguientes se encolan para respetar "nunca dos apariciones en el mismo instante".
  - Nada arranca en el cuadro en que se enciende una celda.
  - `Dt ≤ 1/30`.
- **Traza:** `SCORE|t|marca|cue`, desde el PIE o desde logcat. El editor la superpone como "lo que pasó de verdad".

### 3.4 Refactor incremental de `BP_Obra_SC`
Ninguna fase cambia lo que se ve. Cada una se demuestra con un **diff de trazas** contra la de referencia, no por inspección.

| Fase U | Qué se toca | Control |
|---|---|---|
| U0 | Nada. Se vuelve a volcar `BP_Obra_SC` (el volcado es de las 13:07; después se agregaron fantasmas y manos). Se graba una traza PIE de referencia con `bSimulated` y cada `DebugStart` clave. | Traza archivada en el repo |
| U1 | Se coloca `BP_ScorePlayer_SC` **sin cues**, solo emitiendo marcas. | Sus marcas coinciden 1:1 con los `OBRA:` del log |
| U2 | Perillas: ~30 variables en la categoría "Partitura", **en una sola tanda estructural con la Obra cerrada** (gotcha 402). Los valores por defecto son los literales actuales. `ScoreApply()` al comienzo de `StartObra`, que no hace nada si la tabla está vacía. Cirugía de nodos literal → getter en ~8 grafos (regla de oro 2: no se reescribe). | Instancia contra CDO contra tabla, valor por valor (las variables nuevas nacen en 0: `gotchas.md:1438`). La traza es idéntica. |
| U3 | Una familia de cues: ambientes (`AmbPick`). Un `bLegacyAmb` corta la llamada vieja (cirugía de un nodo). | A/B de trazas con el bool |
| U4 | VO de `StageCues`, `CueAttract` y `CueDraw`; después `FlowBye` y `FlowShare`. | Ídem, por familia |
| U5 | `BP_StageRunner_SC` y `BP_HallRunner_SC` leen **las mismas** perillas. Así se corta la divergencia del título (1→5,5 en el runner contra 0,5→1,8 en la Obra). | Traza del runner = tramo de la Obra |

### 3.5 Editor, PIE y APK
- **Editor (por lote, siempre).**
  - `score_push`: commit → compilar → DataTable (Reimport de Beltrán o MCP en el turno de la cola).
  - `unreal_harvest`: Unreal → `unreal/*`.
  
  Las dos son skills que ejecuta **la sesión que tiene el turno**, con el protocolo de la casa: pedir el turno a Narrativa, contar actores antes y después, guardar con rutas explícitas, `try/except BaseException` y **no escribir nunca** `DebugStart`, `bSimulated` ni otras banderas de debug.
  - Las `proposals/*` espaciales se aplican igual: diff visible, aprobación de Beltrán y aplicación en el turno.
- **PIE.** "Probar desde aquí" en el editor calcula el `DebugStart` del momento seleccionado y lo deja en la cola. La sesión de turno arranca el PIE y trae la traza. Remote Control (en PIE, `WRITE_ACCESS` sin transacción) queda como opcional para la fase 6: hoy no está activo y no aporta nada al Quest.
- **APK.** Siempre horneado: la DataTable va con el commit. El editor muestra "APK en rev 41 · partitura en rev 44", leyendo `ImportedRev` de la traza o del log.
- **Opcional, solo en builds Development:** un override en caliente (`score_override.json` subido por adb, ya que AndroidFileServer está activo en el `.uproject`) leído con JsonBlueprintUtilities, para iterar tiempos en el visor sin reempaquetar. Hay que verificar la ruta escribible en Quest antes de diseñar sobre esto.

---

## 4. Sincronización entre ventanas y entre personas

### 4.1 Dos ventanas o todo en uno
- **Patrón principal: el de ISP, un solo realm.** ISP abre `window.open('about:blank')` y la ventana principal pinta dentro de la emergente; el bombeo usa **el rAF de la emergente** (`app.js:2486-2600`, `w.requestAnimationFrame(viewerPump)` en `:2584`). Así funciona aunque la ventana principal pase a segundo plano.
  - Aplicado aquí: el `WebGLRenderer` de three se crea **sobre un canvas del documento emergente**, con el THREE del realm principal.
  - Hay un solo estado, un solo reloj y un solo audio, y **no hay nada que sincronizar**.
  - La reconstrucción del documento cuando Chromium lo sustituye ya está resuelta en `viewerBuildDoc` (`app.js:2495-2500`).
- **Todo en uno:** la misma vista 3D vuelve al panel central. Es un cambio de host del canvas, no otro programa.
- **Respaldo si el sandbox del artifact bloquea la emergente:** dos pestañas del mismo artifact con roles (`?view=3d`, `?view=timeline`) sobre **BroadcastChannel**.
  - La pestaña de timeline es la líder: tiene el reloj, el audio y el guardado.
  - Los mensajes son por evento (`{playing, t0, wall0, speed}`, selección, hover, `docRev`), nunca por cuadro.
  - Las esperas en vivo las resuelve la 3D, que emite `{gate, out, t}`.
  - **Hay que probar en el host real** si la emergente y el canal funcionan antes de construir encima (primer entregable de la fase 2).
- **Reloj.** Se ancla a `AudioContext.currentTime`. Hoy se integra `dt` con un tope de 0,05 s (`timeline.js:984-987`): se atrasa por debajo de 20 fps y se para en segundo plano.

### 4.2 Personas (Beltrán y el socio, remotos)
- **Documentos granulares:** uno por elemento, grupo, sub-pista y marcador, cada uno con `rev`. Se escribe con condición de versión o con relectura previa (hay que verificar qué ofrece el `db` del runtime). Termina el `set` del documento entero de hoy (`timeline.js:920`) y el "gana el último por `savedAt`" (`:939`).
- **Presencia:** `presence/<usuario>` con latido (acto, grupo y selección). **Bloqueo suave por grupo o acto:** el otro ve un candado y puede pedir el turno, pero no queda bloqueado.
- **Deshacer por usuario y por comandos:** `{op, before, after, docs}`. No se usa el snapshot JSON completo de ISP (`app.js:15654`), que su propio ARCHITECTURE §9 cuenta como deuda. Un comando escribe exactamente los documentos que tocó, así que la granularidad sale sola.
- **Historial:**
  - respaldos automáticos (`bk-…`, ya existen: `timeline.js:914-917`);
  - **versiones con nombre** ("Corte del socio 03-oct") como snapshot completo y diff visual por elemento;
  - git como historial duro, con un commit en cada hito vía `/commit`.
- **Yjs, Hocuspocus u otro CRDT:** no se usa. Para dos personas que casi nunca editan a la vez es sobrediseño, y queda como salida si el bloqueo suave no alcanza.
- **Hosting:** el mismo artifact (`1BGkcExUptjr3U9Snjy1xd`), para conservar la base, `timeline/main` y los 116 audios (32,7 MB). El editor nuevo se publica como **`editor.html` dentro de los `files` del mismo artifact**, y el `index.html` viejo sigue vivo hasta la paridad.
  - **Verificar:** que las dos páginas compartan la base, y que el socio pueda escribir en ella con acceso de edición.
  - Los modelos siguen como `.glb.json`, porque el artifact no sirve `.glb`.
  - La fuente Geist sale de los woff2 de ISP (`assets/fonts/geist-400/500/600.woff2`, `index.html:10-12`) como archivos publicados.

---

## 5. Prototipo, ISP y stack

### 5.1 Qué se conserva del prototipo
- **Semántica del motor:** anclas, `end`, momentos encadenados, memoización con detección de ciclos (`timeline.js:58-146`), esperas en vivo y simuladas, ayuda, corte de voz (`:314-338`). Se reescribe como **`engine/score-engine.js` puro**, sin DOM ni three. Expone `resolve(score, persona) → schedule` y `evaluate(schedule, t) → W`. Corre en Node para la prueba dorada y para `compile.mjs`.
- **`world.js`:** escena, `install…()` de los 7 GLB, subsistemas deterministas (APPEAR, POP, HALO, FISH). Queda detrás de `world.apply(W)` y `world.tick(dt)`.
  - Las 51 mutaciones directas de `guion.js` pasan a campos de `W`, como ya hacen FISH y POP.
  - Las posiciones de `guion.js:11-24` pasan a `roles` y anclas espaciales.
  - Se corta la dependencia circular (`world.js:148`, `:826`).
  - La simulación por cuadro sale de `timeline.js:983-1081` y vuelve a `world.js`.
- **Audio:** asignación por nombre, `audio/<ID>`, envolventes y crossfades (`timeline.js:353-515`), aislado como `audio.js`. Se le agrega forma de onda; la de ISP es `drawAudioWaveInto`.
- **Vocabulario visual de las esperas:** rayado, marca roja de cortafuegos, ayuda punteada, rombo de evento instantáneo.

### 5.2 Qué se reescribe
- El editor DOM: `buildEditor`, `place`, `computeLanes`, el inspector con `innerHTML` y el teclado. Lo reemplaza el código de ISP.
- `guion.js` como código se reemplaza por la partitura como datos.
- La capa `EDITS` se elimina.
- Los diálogos nativos `prompt`/`confirm`/`alert` (`timeline.js:674`, `:810`, `:962`, `:1111`) se reemplazan por los de ISP.

### 5.3 Qué se extrae de ISP (código propio: se copia y se adapta)

**Cómo está acoplado.** `app.js` tiene **19 504 líneas** y 1268 funciones de primer nivel, todas sobre un `state` global con repintado manual (ARCHITECTURE §7). `ESTRUCTURA-DEL-CODIGO.md` todavía dice 14 499 y COMPONENTS cita líneas viejas: `renderTimeline` figura en L1876 y hoy está en `app.js:5452`.

`renderTimeline` (`5452-5617`) llama directamente a decodificadores (`reconcileVinst`), migraciones de automatización, proxys, caché de nests, `attachClipAuto`, `redrawAudioWaves`, `raInvalidate`, `render()` y `reschedAudio()`.

**Conclusión:** no se puede importar como librería. Se **trasplanta con lista de cortes**:
- cada función se copia a un script por dominio con un encabezado `// origen: ISP app.js:<línea> @<commit>`;
- se conservan sus nombres y el subconjunto de `state` que usan: `state.tl.{pxPerSec,tool,tcMode}`, `state.playhead`, `state.selIds/selId/selLane`, `state.markers`;
- se borran las ramas de medios, proxys, nests, salas, automatización y Reactive FX.

Es el "partir en varios `<script>` por dominio sin bundler" que el propio ADR-0001 deja como futuro.

| Destino | Origen ISP | Qué se hace |
|---|---|---|
| `ui/isp.css` | `index.html:15-1202` completo | **Se copia entero** y se poda por la regla de ADR-0008. Se quedan: tokens `:root` (`:27-82`, superficies s0/s1/s2, tintas, líneas, los 2 acentos, `--state-on/hover`, `--sp-*`, `--toggle-on`, `--audio-tint`, `--floor-tint`, `--bar`, `--p-*`), base y sliders (`:83-112`), `.top`, `.seg/.vseg/.well` (`:122-149`), `.ibtn` (`:143-145`), `.vptool` (`:223`), `.sechead` (`:292`, `:317-318`), `.prow` y `.box` (`:321-349`), `.insEmpty` (`:353`), `.transport/.tccenter/.tcbox` (`:356-366`), `.timeline/.tlmain/.toolrail/.trackhdr/.lanehdr` (`:412-453`), `.tlvzoom` (`:543`), barra de zoom (`:556`), `.ruler` (`:564`), `.lane` (`:570-574`), `.clip` completo (`:593-663`), `.playhead/.snapline` (`:664-668`), `.seqtabs/.seqtab` (`:670-703`), `.status` (`:792`), `.overlay/.modal` (`:800`, `:974-1008`), `.menu` (`:1114-1119`), `.iosw` (`:1121-1123`). Se van: ruedas de color (`:372-410`), NDI y salida, grilla de medios. Los selectores de automatización (`:491-534`) quedan para los looks con keyframes. |
| `editor.html` | esqueleto `index.html:1205-1453` | `.top` con menús File/Edit/Obra/Window y título + "rev 44 · Unreal rev 41". El panel `#mediaPane` (`:1227`) pasa a **Biblioteca de la obra** (roles, audios, comportamientos). `main` con `.vptool` y el canvas three. `#inspPane` (`:1355`), `.transport` (`:1381`), `.timeline` (`:1409-1438`), `.status` (`:1439`). |
| `ui/chrome.js` | `T()` `app.js:167`; `ICO()` `index.html:1458`; `openMenu/closeMenu` `16861-16864`; `openAppMenu` `16936`; `commandList/openPalette` `17185/17216`; `appPrompt/appConfirm/appConfirm3/appAlert` `5677-5750`; `setFocusPane` `5594`; `flashStatus/updStatus` `15781/15786`; `TOOL_HINTS` + ayuda en estado `16297`, `18546-18583` | Casi tal cual. La barra de estado reemplaza CPU/RAM/GPU por **sincronía**: "Partitura rev 44 · Unreal rev 41 · 3 divergencias · Socio en Acto 4". |
| `ui/timeline.js` | `renderTimeline` `5452-5617`; `fmtTime/drawRuler` `5379/5383`; `positionPlayhead` `6862`; marcadores `6848/6858/7745`; `drag` y el despacho de `pointerdown` de `#tracks` `6904-6905`; `startTimeSelect` `7008`; `snapTargets/gridSec/applySnap/showSnap` `7048-7075`; fantasmas `7281-7282`; `onTLMove/onTLUp` `7318/7433`; `positionClips` `7383`; `startFadeDrag` `7498`; `tlZoomAt/renderZoomBar/startZoomBarDrag/startZoomCapDrag/startPan/startMarquee` `7671-7706`; `wheelResizeLanes` `7764`; `neededSec/applyToolCursor` `7817/7823`; `renderVZoom/fitAll/clampTimelineH` `16248/16287/16452`; `setTool` `16305`; carriles `addLane/trackCreateItems/removeLane/renameLane/duplicateLane/startLaneDrag` `5619-6820`; `renderSeqBar` `14195` | Se adapta: el bucle de pistas pasa a **grupo → sub-pistas**; las pistas se referencian por id; se corta todo lo de medios y automatización. **Se invierte `cutOverlapsOnDrop` (`7409`):** en ISP el clip quieto se recorta, y aquí un solape **nunca** corta. Las pestañas de secuencia pasan a vistas: Obra · toma SHARE · toma DON'T SHARE · interior de una espera. |
| `ui/inspector.js` | `renderInspector/_renderInspectorMain` `8154-8155`; `buildRows` `8982`; `editNumberBox/refreshInspector/startValDrag` `9030-9086`; `insColState/applySecCollapse/wireSecHeads` `15993-15997`; `pintarRangos` `16151` | `buildRows` ya funciona por esquema (`[key,label,unit,min,max]`), así que se generaliza al esquema de parámetros del `catalog`. Secciones: **Qué hace** (lenguaje llano) · **Tiempo** (ancla, inicio, duración, cortafuegos; TC absoluto + "+00:04:12 desde «G_BREATH»") · **Acción** · **Sonido** · **En Unreal** (plegada: BP, variable, asset, estado de sincronía). |
| No se copia | `pushUndo/snapshot/restore` `15654-15667`; motor GL, export, proxys | Deshacer por comandos; three r128 propio. |

### 5.4 Sub-pistas (pedido de Beltrán), sobre el código de ISP
- **Grupo** = la `.lanehdr` de ISP (barra de color, chevron, nombre, M/S), más un **`+` de 16 px** con la forma de `.ms` (`index.html:448`). Debajo van sus sub-pistas: filas `.lane` separadas por la línea suave que ISP **ya usa**, `border-bottom:.5px solid var(--line-soft)` (`index.html:570`). El grupo plegado muestra una sola fila con los clips en miniatura.
- **Crear sub-pistas:**
  - con el `+`;
  - **soltando un clip en la franja libre bajo la última**: el fantasma de `showMoveGhosts` muestra la fila "+ nueva sub-pista";
  - con el menú contextual.
- **Borrar:** solo las vacías; la opción aparece deshabilitada si no lo está. **Renombrar:** doble clic, como `renameLane`. **Reordenar:** con `startLaneDrag` adaptado a ids.
- **Mover:** el clip se queda en su sub-pista; solo cambia si lo arrastras en vertical. Si el destino está ocupado, el fantasma sale con borde `--danger`, la barra de estado dice "Ocupado: suelta debajo para crear una sub-pista" y al soltar **se rechaza**. No hay recorte ni reacomodo automático: desaparece `computeLanes` (`timeline.js:591-607`), cuyo reparto cambiaba con el zoom y al soltar. "Ordenar sub-pistas" queda como comando explícito.
- **Moverse entre grupos:** solo si el grupo acepta el `type` (`accepts`), igual que la compatibilidad `wantKind` de `onTLMove` (R231).
- **Color por familia,** como `LANE_COL` de ISP (`app.js:88`): gris = visual o mundo, verde (`--audio-tint`) = VO, sonido, música y háptica, rojo (`--floor-tint`) = interacción y esperas. El clip lleva su propio color en la franja de título, como en ISP.
- **Solo dos acentos:** cian = vivo, arrastrable o enlazado a Unreal; ámbar = **diverge de Unreal o está anulado localmente**. No se agrega un tercero.

### 5.5 Stack
- **Vanilla JS, sin bundler ni framework.** El código que se trasplanta es DOM a mano; con React habría que reescribirlo, no reusarlo.
- **Scripts clásicos por dominio** (`engine/`, `world/`, `audio/`, `ui/`, `store/`, `sync/`), con un espacio de nombres `window.SC` en lugar de los ~200 globales actuales.
- **three r128 se mantiene.** r152 cambia la gestión de color calibrada contra Unreal y r151 rompe `uv2` (`world.js:701`, `:1313`). TransformControls y OrbitControls existen en r128.
- **Lint sin build:** JSDoc + `// @ts-check` y `tsc --noEmit`. Validador del esquema en JS, compartido con el Python de la cosecha (JSON Schema).
- **Pruebas:** la prueba dorada del motor en Node, más sondas por CDP como en ISP (`ESTRUCTURA-DEL-CODIGO.md` §8).
- **Puente local opcional** (fase 6), solo para Beltrán: Node sin dependencias que sirve los mismos archivos desde `localhost`, lee y escribe `obra/score/` y hace de proxy a Remote Control en PIE. El socio nunca lo necesita.

**Rendimiento.** En ISP, la reconstrucción completa cuesta ~100 ms con 300 clips (COMPONENTS: renderTimeline, *gotchas*), y aquí hay 592 elementos. Mitigaciones:
- `positionClips` durante el arrastre (ya existe);
- grupos plegados por defecto;
- render horizontal **por ventana visible**: solo los clips que cruzan el viewport, más un margen;
- `evaluate` por índice de tiempo en lugar de O(n) por cuadro.

---

## 6. Plan por fases (MVP primero)

| Fase | Entregable verificable | Riesgos |
|---|---|---|
| **F0 · Congelar y medir** (sin UI) | `extract_v1.mjs`, `legacy_map.json`, `score v0`. **Prueba dorada** de 592 inicios y fines (±1 ms) con los 17 edits. `harvest_score.py` en el repo, sin `load_level`. Lista de divergencias. Volcado nuevo de `BP_Obra_SC` y traza PIE de referencia. | Closures inclasificables (se resuelven con `legacy` + shim). La cosecha en el editor compartido va en la cola. |
| **F1 · MVP: ISP + sub-pistas** | `editor.html` en el mismo artifact: CSS y esqueleto de ISP, timeline trasplantado con grupos y sub-pistas persistentes, mover y recortar sin solape, inspector por esquema, transporte, menús, paleta, barra de estado. La vista 3D de `world.js` vía `world.apply(W)` y el shim `legacy`. **Control:** el socio mueve y recorta, recarga, y nada salta de carril; los ajustes de Beltrán se ven idénticos. | Rendimiento DOM (virtualizar desde el día 1). Que la base no sea compartida entre `index.html` y `editor.html` (se verifica primero). |
| **F2 · Ventanas y personas** | Ventana 3D con el patrón de ISP y respaldo BroadcastChannel (**primero, la prueba en el host**). Reloj anclado a audio. Documentos granulares con `rev`, presencia, bloqueo suave, deshacer por comandos, versiones con nombre y diff. | Sandbox del artifact (emergentes, particionado del canal). Concurrencia de escritura en la base. |
| **F3 · Unreal → web** | `unreal/*` alimenta poses, duraciones de VO e `ImportedRev`. Indicadores ámbar por valor. Resolución de las ~30 divergencias por Beltrán. Las trazas se superponen al timeline. | Que la cosecha se desactualice si no se corre: la barra de estado muestra su antigüedad. |
| **F4 · Web → Unreal** | Structs a mano (Beltrán) o plan B DataAsset. `compile.mjs`, `score_push`. Fases U1-U3: marcas, perillas y ambientes con diff de trazas idénticas. | Gotcha 402, variables que nacen en 0, CDO distinto de la instancia. **Valores finales:** una traza que difiere detiene la fase. |
| **F5 · Interacción** | Esperas y ramas completas (tomas en pestañas), personas simuladas con la meta de 15:00 a la vista, vista de **Nodos** (el mismo dato: anclas, esperas y reacciones como grafo) y **Lista de cues** al estilo QLab, linter de las reglas de la obra (VO ≥ aparición de Alma + 1,5 s, música continua, háptico con fin, nada aparece de golpe). U4-U5: VO de etapa y runners. | Alcance: el grafo es una vista, nunca un Blueprint libre. |
| **F6 · Opcionales** | "Probar desde aquí" (DebugStart + PIE en la cola), puente local, override JSON en caliente en el APK Development, transporte por OSC. | JsonBlueprintUtilities es Beta. La ruta escribible en Quest no está verificada. Remote Control solo en editor. |

**Criterio de corte del MVP:** cuando F1 está en uso, el prototipo viejo deja de recibir cambios de timing. Desde ese momento, la única forma de cambiar un tiempo es la partitura. Hasta F4, Unreal sigue con sus valores, pero **la divergencia se ve**: deja de existir una segunda verdad invisible.