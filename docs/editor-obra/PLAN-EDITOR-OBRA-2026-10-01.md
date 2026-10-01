# Editor de la obra: auditoría, diseño y plan (2026-10-01)

Editor web de gameplay y narrativa para Soul Charger. Lo usan Beltrán y su socio (editor de cine) para ordenar la obra, ajustar el timing y decidir cuándo aparece cada cosa, siempre en sincronía con Unreal.

- **Maqueta navegable:** `web/editor-obra/mockup/`.
  - `preview.html` se sirve con la configuración `editor-obra` de `.claude/launch.json`, en el puerto 8767.
  - `editor-obra-mockup.html` es la versión para publicar como artifact.
  - Se arma con `build.py` a partir de `src-body.html` y del CSS de ISP.
- **Informes de la auditoría:** `docs/editor-obra/anexos/` (01 a 10).
- **Regla:** donde un anexo contradiga este documento, manda este documento.

---

## 0. Decisiones en una tabla

| Tema | Decisión |
|---|---|
| Lenguaje visual | **El código de diseño de Immersive Studio Pro / VEATION.** El CSS de `index.html:15-1202` se copia tal cual; se usan sus clases, medidas y componentes (barras de 28 px, Geist 11 px con números tabulares, 3 superficies, 2 acentos). Encima va una capa mínima con lo que ISP no tiene. |
| Idioma | **La app va en inglés**, como ISP. Los documentos del equipo siguen en español. |
| Mayúsculas | **Ningún texto en mayúscula sostenida.** Se pisa el `text-transform:uppercase` de ISP en metadatos y grupos. |
| Qué se trae de ISP | **Solo lo que se usa en la obra.** Fuera: cuchilla, recorte/slip/slide, riel de herramientas, pestañas de secuencia, salida de video, mute y solo. |
| Mute y solo | **No existen.** La partitura es el orden de la obra en Unreal, y apagar una pista la rompería. Queda el **candado**, que solo protege de ediciones. |
| Organización del timeline | **Grupos → sub-pistas.** Los grupos son Interaction, Voice, Instruction, Alma, Objects, Environment, Visual FX, Path, Sound, Music y Haptics. Las sub-pistas las crea el usuario, van separadas por líneas suaves (`--line-soft`) y su nombre es solo una etiqueta: el significado va en el inspector. |
| Solape | **Nunca se monta ni recorta.** Al mover, si el destino está ocupado, el fantasma se pone rojo y no cae. Para crear una sub-pista se suelta en la ranura de abajo. Lo que se agrega sin posición va a la sub-pista libre más cercana del grupo (`laneLibreCerca` de ISP, app.js:17545). |
| Tiempo interactivo | **Esperas elásticas.** Se dibujan como bloque rayado (lo esperado), cola cian (lo que decide el usuario) y línea roja (el cortafuegos). Un **usuario simulado** (Fast · Typical · Slow · Idle) mueve todo lo anclado y el total. |
| Fuente de verdad | **Partitura en texto en el repo** (`obra/score/`). La base del artifact es la mesa de trabajo y Unreal es el compilado. Cada documento tiene un solo dueño. |
| Sincronización con Unreal | **Por lote, en el turno de la cola del editor.** Nunca en vivo sobre el editor compartido. La web ve Unreal en solo lectura, y lo que la web cambia llega a Unreal como propuesta. |
| Runtime en el Quest | **Datos cocinados.** Una DataTable de cues `{Mark, Offset, Action…}` más perillas. `BP_ScorePlayer_SC` dispara las cues a partir de las marcas que emite la Obra. |
| Ventanas | **MVP todo en uno.** Las dos pestañas (3D / Timeline) llegan en la fase 2, una vez probado el canal en el host real. |
| Stack | **Vanilla JS sin build**, como ISP (ADR-0001), y three r128. El timeline es propio, escrito sobre las clases de ISP; no se trasplanta `renderTimeline`. |

---

## 1. Lo que hay hoy (hallazgos que cambian el diseño)

### 1.1 El prototipo web (`web/prototipo-narrativo/`)

- **`guion.js` es código, no datos.** Al ejecutarse produce 10 actos, 73 momentos y **592 clips**. De esos clips, 220 tienen el comportamiento en closures `apply` que no se pueden editar ni pasar a Unreal.
- **Duración total: 1029 s (≈17:09).** La meta es 15:00.
- **Hay 9 pistas fijas, por tipo de medio.** Los carriles los calcula `computeLanes` según el zoom, así que **un clip salta de carril al soltarlo**. Ese es el problema de "se superponen o saltan".
- **Los ajustes se guardan como una capa encima del código.** Viven en `EDITS[uid]` y las keys `#n` dependen del orden de declaración, por eso son frágiles.
  - La base `timeline/main` v78 tiene **17 edits, todos en los primeros 2 minutos**. 4 de ellos no tienen efecto.
  - Hay 116 audios (32,7 MB).
- **El guardado es "gana el último"**, sobre el documento entero. Dos personas a la vez se pisan.
- **El timing que se edita en la web nunca llega a Unreal.**
- **Las ramas no son ramas de verdad.** SHARE y DON'T SHARE ocupan el mismo horario, y el momento dura lo que la más larga.

Detalle en el anexo 01 (y el 02 para `world.js`).

### 1.2 Unreal

- **No hay timeline: hay tres máquinas de estados.** `BP_Obra_SC` (fases 0-16 más orquestadores paralelos), `BP_HallDirector_SC` (31 pasos) y cada etapa con su contrato.
- **Hay 536 literales de punto flotante en 122 grafos.** Parte del tiempo es dato (instancia o CDO) y parte está cableada (el orden, qué VO suena, los cortafuegos 180/120/240, el título…).
- **El puente actual va en una sola dirección y es manual.** `ensayo_export.py` → `gen_ensayo_js.py` → `ensayo.js`. Encima, `ensayo_export.py` **cambia el nivel abierto del editor compartido**, y `gen_ensayo_js.py` vive en el scratchpad de otra sesión.
- **La deriva ya se puede medir:**
  - cortafuegos de Recognizing: 150 en la web contra 180 en Unreal;
  - aviso: 20 s contra 9 s;
  - `G_SENSOR` 15 contra `FW_Tool` 20, y `G_CHOOSE` 30 contra `FW_Choose` 25;
  - largos de VO distintos de la mezcla final;
  - el título del runner y el de la Obra ya no coinciden.
- **Plugins:**
  - RemoteControl está apagado y nunca corre en el Quest.
  - JsonBlueprintUtilities está apagado (es Beta).
  - AndroidFileServer está **apagado**.
  - OSC funciona en el APK.

Detalle en el anexo 03.

### 1.3 La obra como datos (taxonomía)

- **Tipos de elemento:** VO, FX, AMB, HAP, VFX, entorno/look/velo, objetos (aparecer, vivir, salir), títulos, Alma (estados), fantasmas, esperas, mecánicas biométricas, cargas, ramas, modulación, datos que pasan de una parte a otra.
- **Relaciones:** anclas, cadenas de VO, "durar hasta", disparos por evento, ayuda por inactividad, cortafuegos, interrupción de la voz, bucles, capas de aparición y el contrato de etapa R1-R9.
- **Reglas que el editor hace cumplir:**
  - los tiempos los manda el timeline, salvo la VO;
  - toda espera tiene ayuda y cortafuegos;
  - toda demostración va con voz;
  - los textos dentro del visor van en inglés;
  - nada aparece de golpe;
  - nunca dos apariciones en el mismo instante;
  - la música es continua;
  - los IDs llevan prefijo.
- **Lecciones de la prueba del 10-01** (cada una se vuelve un aviso del editor): aire muerto, Alma que habla antes de aparecer, un háptico sin final, huecos de música, estados de manos duplicados.

Detalle en el anexo 04.

---

## 2. Diseño de la interfaz

### 2.1 Layout (ver la maqueta)

**Todo en uno, a 1600×900:**
- **Barra superior (28 px):** menús File · Edit · Experience · Window; selector de ventana [All-in-one | 3D view | Timeline]; presencia del socio; píldora de sincronía ("3 differences with Unreal"); título, revisión y total.
- **Biblioteca (292 px, el panel Media de ISP):** pestañas Scenes · Roles · Sounds · Actions y la fila de crear [Add ⇧A | Sound | Wait | Note].
- **Visor 3D** al centro.
- **Inspector (320 px)** a la derecha, a toda la altura, con pestañas Inspector · Notes.
- **Transporte (28 px):** usuario simulado a la izquierda; inicio, play, fin, seguir, timecode con desfase relativo ("+3.1 s in G_BREATH"), bucle y nota en el centro; Anchors · Logic · Fit y zoom a la derecha.
- **Timeline (402 px)** y **barra de estado (22 px)** con la ayuda contextual de ISP.

**Pestaña 3D:** visor grande, transporte compacto, mapa de la obra con los momentos y el cabezal, e inspector plegado en un riel de 34 px.

**Pestaña Timeline:** transporte arriba, y Biblioteca, timeline e inspector a toda la altura.

### 2.2 Timeline

- **Encabezado:** banda de actos (los velos marcados), regla de tiempo y banda de momentos (al hacer clic en un momento se selecciona entero).
- **Fila de grupo (22 px):** chevron para plegar, nombre en caja normal, `+` para crear sub-pista y candado al pasar el mouse. Plegado, el grupo queda en una fila resumen con los clips como bandas.
- **Sub-pistas:**
  - número y nombre editable;
  - separadas por una línea de 0,5 px a `--line-soft` (pedido de Beltrán);
  - se crean con `+`, con Alt+T (Ctrl+T no se puede interceptar en Chrome) o soltando en la ranura;
  - se borran solo si están vacías.
- **Clips:** el `.clip` de ISP, con banda de título del tono del tipo (`CLIP_HUE` de ISP reasignado) y cuerpo más oscuro.
  - **VO:** onda y texto. Dura lo que su audio, con candado.
  - **FX:** un rombo instantáneo; la cola del WAV no mueve nada.
  - **Háptica:** un trazo cuya altura es la amplitud.
  - **Fantasma:** una muesca por bucle.
  - **Mecánica:** doble borde y muescas por ciclo.
  - **Velo y look:** un degradado.
- **Espera:** rayado claro, cola cian discontinua hasta el cortafuegos, línea roja con "timeout 25 s" y un rombo de ayuda.
- **Ramas:** una chapa por toma; se ve una a la vez o ambas. El final del momento sigue a la rama elegida.
- **Anclas:** al seleccionar se dibujan curvas; tinta para el tiempo autoral, cian para lo que dispara el usuario. Los hijos llevan contorno discontinuo para que se vea la familia antes de soltar.

### 2.3 Agregar elementos (seis puertas, un solo comando)

Todas las puertas llaman a `create(type, when, where, anchor)` con los mismos valores por defecto.

1. **Arrastrar desde la Biblioteca** a una sub-pista. Con doble clic se agrega en el cabezal. Un rol arrastrado a la vista 3D crea "Appear here" con una marca nueva.
2. **Clic derecho:**
   - en el hueco de una sub-pista: *Add here ▸* (solo lo válido para ese grupo) · *Paste here* · *New lane below* · *Marker here* · *Note for the team*;
   - en un clip: *Add after ▸ / Add in parallel ▸ / Reaction ▸*;
   - en una espera: *+ Help / + On done / + On timeout*.
3. **Botones:** `Add ⇧A`, `Sound`, `Wait` y `Note` en la Biblioteca, `+` en cada grupo y botones del inspector según el tipo.
4. **Teclado:**
   - **Shift+A** abre *Quick add* con buscador en el cabezal (la convención de Blender);
   - M marcador, Shift+M nota;
   - Alt+T sub-pista;
   - Ctrl+K paleta de comandos.
5. **Vista 3D:** lo que nace ahí aparece en su sub-pista.
6. **Nodos:** arrastrar desde una salida (Done / Late / Timeout) abre *Quick add* filtrado.

**Sonido vacío (pedido de Beltrán):**
- *Add ▸ Empty sound…* o el botón *Sound* crean un sonido en el cabezal.
- Se le pone nombre (se normaliza a `FX_…`) y se le carga un WAV: se suelta o se usa *Load WAV…*.
- Queda marcado como **not in Unreal yet**. En el próximo push se importa como SoundWave en `Content/SoulCharger/Audio` con ese nombre, y su cue entra en la partitura.
- Su duración la manda el timeline; el archivo suena entero desde su cue.

**Plantillas:** *Demonstrated interaction*, *Layered reveal* y *Stage mold R1-R9*. Nacen cumpliendo las reglas.

**Lo que no se hace:**
- crear con doble clic en el vacío (se dispara solo al hacer scrub);
- crear dibujando un rectángulo (ese gesto ya es la selección por rango).

### 2.4 Inspector

Es el inspector de ISP: `.selhead`, `.sechead` y `.prow` con etiqueta de 60 px, fader del color del parámetro y valor sobre `--s0`.

**Secciones por tipo:**

| Tipo | Secciones |
|---|---|
| Todos | **Time:** Starts (chip de ancla), Duration, Lane |
| VO | **Voice:** texto, audio, From, Volume, Lead-in |
| Espera | **Wait:** frase "When [the sensor] [touches zone] [belly] for [1 s]", Expected, Help after, Timeout, On timeout, If early, tabla de usuarios simulados · **Outputs:** Done / Late / Timeout · línea de lectura en cian |
| Objetos y roles | **Knobs:** las perillas reales de Unreal |
| Todos | **Advanced**, plegado |

**Perillas de Unreal (pedido de Beltrán).** Cada objeto muestra las variables que ya existen, con un nombre comprensible. Al pasar el mouse se ve la variable real.
- **Timbre:** Appear 1.5 s (`BPC_AppearLuz_SC`) · Press depth 1.0 cm (`BellPressDepth`) · Press time 0.12 s (`BellPressTime`) · Hold to ring 3.0 s (`BellHold`) · Timeout 25 s (`FW_Bell`).
- **Pacer:** Cycles 5 · Rhythm 4-3-4-3 · Lead-in 3 s · Count 3 s.
- **Alma:** Size 1.0 · Brightness 1.5 · Stays VO + 3 s.

El catálogo completo de perillas sale de los trackers de cada BP (`blueprints/*.md`) y de la cosecha (§3.3). **Cambiar una perilla genera una propuesta**, que se aplica en Unreal en el turno de la cola.

**Origen de cada valor:**
- sin marca: igual a Unreal;
- **ámbar:** editado aquí y todavía no en Unreal;
- **candado:** valor final aprobado en un nivel de test (cambiarlo pide un motivo, que queda como nota).

### 2.5 Lógica (nodos)

- **El grafo es otra vista del mismo dato**, no un Blueprint libre: una arista es un ancla o un disparo.
- Vive en el **cajón Logic** (G), con el patrón `.curvedrawer` de ISP: lista del momento a la izquierda y grafo a la derecha.
- La espera tiene tres salidas, Done (cian), Late (gris) y Timeout (rojo).
- Arriba va una **frase de lectura** tipo hoja de cues.
- Va en la fase 5: no es MVP.

### 2.6 Vista 3D

- Cámaras **POV · Free · Plan**.
- Superposiciones: anclas y TargetPoints, *Live now* (lo activo en el cabezal) y campo visual (±30°/±60°).
- **El gizmo edita la marca, no el objeto**, en el marco de la parada ("2.20 m front · 0.90 m left · +0.05 m").
- **Edit / Play:** en Play, el mouse es la mano y las esperas se resuelven en vivo, con la píldora "Waiting… [Complete ⏎]".

### 2.7 Atajos

| Atajo | Acción |
|---|---|
| Espacio · Home · End | Reproducir o pausar · ir al inicio · ir al final |
| ← / → | Mueve solo el cabezal |
| Alt+← / → | Mueve la selección con su familia |
| ↑ / ↓ | Momento anterior o siguiente |
| M / Shift+M | Marcador / nota |
| Shift+A | Agregar |
| G | Cajón Logic |
| A | Todas las anclas |
| Alt+T | Nueva sub-pista |
| Ctrl+K | Paleta de comandos |
| Ctrl+Z / Ctrl+Shift+Z | Deshacer / rehacer: cubre look, sub-pistas, audio y notas |

- **J/K/L e I/O de ISP:** quedan como atajos, sin botones.
- **Combinaciones del navegador** (Ctrl+T, Ctrl+W, Ctrl+N): no se usan. El resto de las combinaciones se prueba en el iframe real.

---

## 3. Arquitectura

### 3.1 Fuente de verdad: la partitura

- **El tiempo y la estructura** viven en `obra/score/*.json` (texto, versionado, se puede hacer diff).
- **Las posiciones, el look y los umbrales de las mecánicas** son de Unreal; la web los ve en solo lectura.

| Colección (base del artifact) | Quién escribe |
|---|---|
| `score/*` | el editor (Beltrán, socio) |
| `unreal/*` | solo la cosecha (una sesión en su turno) |
| `proposals/*` | el editor; una sesión las aplica en Unreal |
| `audio/*` | el editor (vista previa y WAV nuevos) |
| `notes/*` | el editor |

- **El repo es el registro canónico:** cada hito vuelca la partitura a `obra/score/` y se commitea. Unreal importa **desde el repo**, nunca desde la base.
- **La duración de la VO es de Unreal** (`GetDuration`).

### 3.2 Modelo de datos (schema 2)

**Entidades:** `acts`, `beats` (momentos), `groups` → `lanes` (sub-pistas, por id), `elements`, `gates`, `branches`, `markers`, `looks`, `roles`.

**Un elemento separa tres cosas que hoy están mezcladas:**
- `lane`: dónde se dibuja;
- `target`: un rol que Unreal resuelve por tag;
- `action`: un id de un catálogo cerrado con parámetros.

Por eso cambiar de sub-pista **nunca** cambia el comportamiento.

**Duración:** `fixed | audio (solo VO) | until | elastic (esperas y mecánicas)`.

**Ancla:** `{ref, edge, off}` en segundos reales. El warp de los locators pasa a ser una **operación** ("Stretch section"), no un estado.

**Marcas** (la raíz de toda ancla y el puente con Unreal): `OBRA.START`, `S<K>.P<n>`, `HALL.<modo>.<paso>`, `GATE.<id>.<done|late|fw>`, `VO.<id>.end`, `MECH.<K>.<evento>`, `FINAL.<estado>`. Casi coinciden con `DebugStart`.

**Identificadores:** ULID con prefijo. El `key` legible (`VO_11h`) es editable y no es llave, así que desaparecen los `#n`.

**Migración sin perder nada:**
1. Extraer `guion.js` en Node con stubs, como ya hizo la auditoría.
2. Mapear los ayudantes y clasificar a mano los closures. Lo que no tenga equivalente queda como `legacy`, ejecutado por un shim.
3. Aplicar los 17 edits de v78.
4. **Prueba dorada:** los 592 inicios y fines iguales (±1 ms), usando un fixture con la duración real de los audios de la base.
5. Reconciliar con Unreal: unas 30 divergencias que resuelve Beltrán una sola vez.

### 3.3 Unreal

**Compilación.** `compile.mjs` aplana cada cue a `{Mark, Offset}` y genera dos tablas: **Cues** (`Mark, Offset, Action, Target, Asset, P1..P4`) y **Knobs** (`Name, Value`).
- **Preferido:** DataTable con Reimport. Beltrán crea a mano, una vez, los dos structs, porque el MCP no crea structs.
- **Plan B:** un DataAsset con arrays, con el precedente `DA_Ghost_*`.
- La tabla queda referenciada en firme por `BP_ScorePlayer_SC`, así que se cocina sola.

**`BP_ScorePlayer_SC`.**
- La Obra emite **`OnMark(Name)`** por dispatcher, con cirugía de un nodo por transición. No se observa con Tick, porque se pierden flancos: `FinalFlow` corre unas 1,5 veces por cuadro.
- Cursor por marca, sin búsquedas por cuadro.
- Como mucho una aparición por cuadro, con tolerancia de ±1 cuadro en las trazas.
- Las acciones son **Spawn/Destroy**, no mostrar u ocultar (regla "cargar por etapa").
- Traza `SCORE|t|marca|cue` hacia el log y logcat.

**Perillas sin pisar a Beltrán:** reconciliación de tres vías. `ScoreApply` escribe una perilla solo si el valor de la instancia es igual al de la última importación. Si Beltrán la cambió en Detalles, gana la instancia y se registra una divergencia.

**Doble disparo:** cada familia que migra corta su llamada vieja con `bLegacy<Familia>` (AMB, VO de etapa, SFX…).

**"Probar desde aquí":** una variable `ProbeStart` que nunca se guarda. `DebugStart` es una palanca de Beltrán y no se toca.

**Alcance honesto.** Cada elemento lleva la insignia *reaches Unreal* o *preview only*, y la barra de estado dice cuántos llegan (por ejemplo, "142 of 592 reach Unreal"). Hasta que una familia no migra, lo que se edita es previs, y eso se ve.

**Cosecha (Unreal → web).** `harvest_score.py` va versionado en el repo. Lee los subniveles ya cargados de la Obra **sin `load_level`** y trae:
- poses de TargetPoints y actores con tag;
- perillas de instancia;
- duraciones de VO (también de `duraciones_mezcla.txt`);
- `ImportedRev`.

Reemplaza a `ensayo_export.py` y a `gen_ensayo_js.py`.

### 3.4 Ventanas y personas

- **La base del artifact es "gana el último":** no tiene transacciones y admite 256 KiB por documento. Por eso:
  - documentos granulares (uno por elemento, sub-pista y nota);
  - `acquire` como bloqueo suave por acto;
  - versiones con nombre guardadas como asset JSON.
- **Presencia y transporte entre pestañas:** la capacidad `room` o BroadcastChannel, **después de probarlo en el host real**. La ventana solo-visor de ISP copia un canvas 2D y renderiza dos veces por cuadro: no sirve para three a 60 fps.
- **Permisos:** el socio necesita acceso de **Editor** para subir audio, y hay que confirmar si está en la organización.

### 3.5 Stack y reuso de ISP

- **Se copia tal cual:** el CSS completo (con la poda de ADR-0008), el chrome (barras, menús, paleta, diálogos, barra de estado e ICO) y funciones puras (`fmtTime`, imán, zoom, `inlineEdit`, `laneLibreCerca`).
- **Se escribe propio, sobre las clases de ISP:** el timeline y el inspector por esquema. ISP mueve clips sobre `start` absoluto y `renderTimeline` llama a unos 80 ayudantes de medios: no se puede trasplantar "tal cual".
- **Se conserva del prototipo:** la semántica de anclas y esperas (como motor puro), la vista 3D de `world.js` (detrás de `world.apply(W)` cuando haga falta) y el pipeline de audio.
- **Se elimina:** la capa `EDITS`, `computeLanes` y los `prompt`/`confirm`/`alert`.
- **Procedencia:** cada archivo copiado de ISP lleva un encabezado de origen (`// origin: ISP index.html:<línea> @<commit>`). La sesión de Immersive Studio Pro se ofreció a extraer el CSS cuando se construya.

---

## 4. Plan por fases

| Fase | Entregable verificable | Riesgo principal |
|---|---|---|
| **F0 · Congelar y medir** (sin UI) | Extracción a partitura con IDs estables y shim `legacy`; prueba dorada de los 592; `harvest_score.py` en el repo; lista de divergencias; volcado nuevo de `BP_Obra_SC` y traza PIE de referencia | Closures inclasificables (se cubren con el shim) |
| **F1 · MVP para el socio** | Chrome y CSS de ISP; timeline propio con grupos y sub-pistas persistentes; mover y recortar con imán sin solape; esperas elásticas con usuario simulado y total contra 15:00; inspector Time / Voice / Wait / Knobs (solo lectura); agregar por las seis puertas; sonido vacío con WAV; notas; columna Unreal en solo lectura con divergencias en ámbar e insignia de alcance; la vista 3D actual en el centro | Rendimiento del DOM: render por ventana visible desde el día 1 |
| **F2 · Ventanas y personas** | Prueba en el host real (`room` / BroadcastChannel); dos pestañas; documentos granulares; presencia; bloqueo suave; versiones con nombre | Sandbox del artifact |
| **F3 · Unreal → web completo** | Cosecha periódica (poses, perillas, VO, revisión); trazas PIE superpuestas | Cosecha desactualizada (se muestra su antigüedad) |
| **F4 · Web → Unreal** | Structs y DataTable; `compile.mjs`; `BP_ScorePlayer_SC` con `OnMark`; perillas con reconciliación de tres vías; primera familia (ambientes) con A/B de trazas; import de WAV nuevos | Gotcha 402 y variables que nacen en 0 (una sola tanda, con la Obra cerrada, en la cola) |
| **F5 · Interacción completa** | Ramas como tomas; cajón Logic; lista de cues; linter de reglas; VO de etapa y runners leyendo la misma partitura | Alcance: el grafo es una vista, no un Blueprint |
| **F6 · Opcionales** | "Probar desde aquí" (`ProbeStart` + PIE en la cola); override JSON en el APK Development (requiere JsonBlueprintUtilities y AndroidFileServer, hoy apagados) | Plugins en configuración compartida |

**Corte del MVP:** cuando F1 está en uso, el prototipo viejo pasa a **solo lectura por código** y la única forma de cambiar un tiempo es la partitura.

---

## 5. Riesgos (de más a menos grave)

1. **Ilusión de control.** El socio monta algo que el APK no reproduce. *Mitigación:* insignia por elemento y alcance en la barra de estado.
2. **`ScoreApply` pisa a Beltrán.** *Mitigación:* reconciliación de tres vías.
3. **Doble runtime (web y Unreal) mantenido por una sesión.** *Mitigación:* al principio, un catálogo de 10 acciones como máximo; las mecánicas entran como caja con duración simulada.
4. **El observador pierde marcas.** *Mitigación:* dispatcher `OnMark`.
5. **Sandbox del artifact** (pestañas, `editor.html` dentro de `files`). *Mitigación:* una prueba de 30 minutos antes de F2. Plan B: un artifact nuevo copiando los assets en el servidor.
6. **Base sin transacciones.** *Mitigación:* documentos granulares y `acquire`.
7. **Gotcha 402 con la Obra en edición activa.** *Mitigación:* U2 en una sola tanda, en la cola, con la Obra cerrada.
8. **Audio provisorio contra la mezcla final.** *Mitigación:* la cosecha sube la mezcla final y marca *temp* por ID.

---

## 6. Decisiones abiertas para Beltrán

| # | Pregunta | Recomendación |
|---|---|---|
| 1 | ¿Quién manda en las perillas que ya son de instancia (`Pace*`, `FW_*`, `ChargeTimes`, `BellPress*`)? | La instancia de Unreal. La partitura propone, con reconciliación de tres vías. |
| 2 | ¿Qué familias llegan primero a Unreal? | Ambientes, VO de etapa y título/velo. El resto queda como previs con insignia. |
| 3 | ¿Dónde vive el editor? | El mismo artifact (base y 116 audios) como `editor.html`, si la prueba del host sale bien. Si no, un artifact nuevo copiando los assets. |
| 4 | ¿Qué acceso tiene el socio? | Editor, si va a subir WAV. Hay que confirmar si está en la organización. |
| 5 | Título de etapa: ¿cuál es el final, el del runner (1→5,5 s) o el de la Obra (0,5→1,8 s)? | Define U5. Decisión de autor. |
| 6 | ¿Banda de actos + regla + momentos (58 px) o regla única con regiones, al estilo de ISP? | Las tres bandas: el socio piensa en actos y momentos. |
| 7 | ¿El inspector a 320 px (ISP usa 300)? | 320. Con la app en inglés las etiquetas vuelven a los 60 px de ISP. |

---

## 7. Próximo paso

**F0 no necesita el editor de Unreal**, salvo la cosecha y la traza PIE, que van en la cola de Narrativa. Puede arrancar ya.

En paralelo, la maqueta sigue siendo el lugar donde Beltrán decide la interfaz. Cada cambio que pide entra primero ahí (`web/editor-obra/mockup/src-body.html` → `build.py`).
