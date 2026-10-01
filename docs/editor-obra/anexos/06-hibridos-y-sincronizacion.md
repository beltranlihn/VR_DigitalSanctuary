> Anexo de la auditoría del 2026-10-01 (investigación: herramientas híbridas y sincronización). Lo que manda es [PLAN-EDITOR-OBRA-2026-10-01.md](../PLAN-EDITOR-OBRA-2026-10-01.md); donde este anexo lo contradiga, gana el plan.

# Auditoría (parte web): editores híbridos de pistas y lógica, y sincronización con Unreal

## 0. Lo que el prototipo ya tiene

Antes de comparar, conviene ver qué tiene hoy el prototipo, porque varias de las herramientas externas ya están a medio copiar ahí.

- **Los carriles se calculan solos y no se guardan.** `computeLanes()` reparte los clips de cada pista con un empaquetado voraz cada vez que se redibuja (`web/prototipo-narrativo/timeline.js:591-599`). Si mueves un clip, el reparto cambia y los demás clips cambian de carril. De ahí viene que los elementos se superpongan o "salten" al moverlos. Las pistas creadas por el usuario resuelven exactamente esto.
- **Las esperas son clips, pero su condición está en código.** `gate(key,label,expected,fw,g)` crea un clip de la pista `int` con duración esperada y un tope `fw` (`timeline.js:50`). Lo que dispara cada espera es una función JS: `tick: () => S.down` (`guion.js:369`), `tick: () => !!S.carry` (`guion.js:474`), etc. El socio no puede leer ni editar esas condiciones.
- **El tiempo ya es relativo.** `EDITS` guarda por uid `{d, dur, fw, at:{ref,edge,off}}` (`timeline.js:84`), así que un clip ya puede ir anclado al borde de otro. La vista ya dibuja las líneas entre anclas (`timeline.js:702-704`). Es el auto-follow de QLab con otro nombre.
- **Ya hay tres tipos de condición, implícitos.** Un clip puede ser una espera, una ayuda ("solo si el usuario tarda") o `simOnly` ("en vivo lo dispara el usuario") (`timeline.js:587`). El editor debería convertir estos tres tipos en objetos visibles con nombre.
- **El guardado es "gana el último".** El estado se guarda entero en `timeline/main` (`timeline.js:920`), con copia en `localStorage` (`timeline.js:907`). Para elegir entre las dos versiones solo se compara `savedAt` (`timeline.js:939`). Si dos personas editan a la vez, una pierde todo lo suyo, no solo lo que se superpuso.
- **El puente con Unreal es manual y va en un solo sentido.** La cadena es `ensayo_export.py → gen_ensayo_js.py → publicar` (`README.md:18`).
- **Immersive Studio Pro es la app de Beltrán** (hoy se llama VEATION, `Immersive Studio Pro/README.md:1`). Ya tiene el vocabulario de timeline que el socio entendería:
  - seis herramientas: select, trackselect, hand, trim, razor y zoom (`COMPONENTS.md:61`);
  - cabeceras de pista con añadir, duplicar y reordenar (`COMPONENTS.md:64-65`);
  - imán (`:77`), marcadores con nombre (`:82`), pestañas de secuencia (`:83`) y carriles de automatización (`:87`).
  
  Hay una regla que hay que invertir: en ISP, cuando sueltas un clip encima de otro, el que se mueve recorta al quieto (`COMPONENTS.md:71`). Aquí un solape nunca debe cortar. Debe mandar el clip a otro carril o pedir que se cree uno.

---

## A. Cómo resuelven otros "timeline autoral + eventos interactivos"

| Herramienta | Patrón clave | Qué tomar para Soul Charger |
|---|---|---|
| **Unreal Sequencer (5.5+)** | Event tracks en dos variantes: **Trigger** (dispara en un cuadro) y **Repeater** (dispara cada cuadro mientras dura la sección). La lógica vive en *endpoints* del **Director Blueprint**, con parámetros y bindings ([doc](https://dev.epicgames.com/documentation/en-us/unreal-engine/cinematic-event-track-in-unreal-engine)). Desde 5.5 hay **Conditions** por pista o sección: Group (con compuertas lógicas), Platform, Scalability y condiciones a medida en el Director, más "Editor Force True" e "Invert" ([foro 5.5](https://forums.unrealengine.com/t/talks-and-demos-sequencer-5-5-features-at-a-glance/2119028)). También hay bindings **Replaceable/Custom**: en edición se usa un actor de vista previa y en runtime se enlaza al real ([Dynamic Binding](https://dev.epicgames.com/documentation/unreal-engine/dynamic-binding-in-sequencer)). | (1) Dos tipos de evento: puntual y "mientras dure". (2) **La condición se adjunta al clip o a la pista**, no es un nodo aparte. (3) **Bindings por rol**: el editor habla de "Alma", "Sensor" o "Puerta 2", no de actores concretos. **No** conviene que una Level Sequence sea la fuente de verdad: es un `.uasset` binario y el editor es compartido. |
| **Unity Timeline** | **Markers** y **Signals** (emisor en la pista, receptor en el objeto). Una espera se arma con una señal que pone `speed=0` en el PlayableDirector y otra que la devuelve a 1 ([guía de Unity](https://unity.com/blog/engine-platform/how-to-use-timeline-signals)). Hay una muestra oficial de **marcadores Jump/Destination** ([repo](https://github.com/Unity-Technologies/TimelineMarkerCustomization/tree/master/Assets/6-JumpMarker)). | Los marcadores son objetos de primera clase, distintos de los clips, y se ven en la regla. Conviene tener un tipo de marcador "salto / bucle hasta". |
| **Reality Composer Pro (visionOS 2)** | **Timelines** de acciones, más un componente **Behaviors** cuyos disparadores (OnTap, OnCollision, OnAddedToScene, OnNotification) **lanzan una timeline**, sin código ([WWDC24](https://developer.apple.com/videos/play/wwdc2024/10102/)). | Es el modelo más claro para un editor de cine: **cada interacción es una mini-timeline que lanza un disparador.** "Cuando toma el sensor → reproducir [VO + FX + luz]". |
| **Theatre.js** | Project → Sheet → Sequence. El **studio está separado del runtime**: el estado es un JSON que se exporta (`createContentOfSaveFile`) y el runtime solo lee ese JSON ([Projects](https://www.theatrejs.com/docs/latest/manual/projects), [API studio](https://www.theatrejs.com/docs/latest/api/studio)). `attachAudio` mantiene el audio sincronizado con la secuencia ([sequences](https://www.theatrejs.com/docs/latest/manual/sequences)), y los marcadores tienen etiqueta desde la 0.6. La 0.7 se presentó como versión de mantenimiento antes de una 1.0 ([releases](https://www.theatrejs.com/docs/latest/releases)), y su extensión r3f apunta a three r155, mientras el prototipo usa r128. | Copiar **la arquitectura, no la librería**: un editor (studio) y dos runtimes (la vista previa web y Unreal) que leen **el mismo JSON**. No conviene adoptarla como dependencia: el ritmo de mantenimiento es incierto y no tiene concepto de disparadores ni esperas. |
| **Flow Graph (MothCocoon, UE)** | Cada nodo es un UObject que **encapsula lógica y datos**. Es **asíncrono por diseño**: se suscribe a delegados y dispara sus pines de salida ([repo](https://github.com/MothCocoon/FlowGraph), [concepto](https://mothcocoon.github.io/FlowGraph/Overview/Concept.html)). | El nodo "Esperar X" debería tener **salidas con nombre** (`Hecho`, `Tarde→Ayuda`, `Tope`), no un booleano. Si algún día Unreal necesita un runtime de nodos, Flow es el candidato, pero agrega una dependencia de plugin en 5.8. |
| **StateTree (UE)** | Estados con **tareas concurrentes**. Las transiciones saltan al completarse un estado, al recibir un evento o por condición, con **retardo y prioridad** ([overview](https://dev.epicgames.com/documentation/unreal-engine/overview-of-state-tree-in-unreal-engine)). | Sirve para la macroestructura (acto o etapa = estado con tareas concurrentes). No para el detalle del timing. |
| **articy:draft / Yarn / Ink / Twine** | articy pone **condiciones en los pines de entrada e instrucciones en los de salida**, sobre variables globales ([pines](https://www.articy.com/help/adx/Flow_Objects_FlowFragment.html)). Yarn tiene `<<wait>>`, `<<jump>>` y comandos ([docs](https://yarnspinner.dev/docs/yarn/02-fundamentals/10-commands/)). Ink tiene knots, diverts, `#tags` y funciones externas que Unreal enlaza vía Inkpot ([Inkpot](https://github.com/The-Chinese-Room/InkpotDemo)). | La obra es casi lineal, así que una herramienta de ramificación sobra. Lo que sí conviene tomar son los **"hechos" o variables con nombre** (`almaElegida`, `tardóEnRespirar`, `trazos>0`) y la regla de que **la condición vive en la entrada y el efecto en la salida.** |
| **QLab** | Lista de cues con **pre-wait, post-wait, auto-continue y auto-follow**, y grupos en **modo Timeline** donde todos los hijos arrancan juntos ([cue sequences](https://qlab.app/docs/v5/fundamentals/cue-sequences/), [group cues](https://qlab.app/docs/v5/fundamentals/group-cues/)). | Es el idioma que ya conoce cualquiera que haya hecho teatro, sala o cine expandido. Las anclas actuales equivalen a auto-follow con offset, y una espera es un cue **sin continue** que espera el "GO" del usuario. Vale la pena una **vista de lista de cues** como alternativa a las pistas. |
| **disguise** | La timeline se divide en **secciones entre cues**. En modo **"play to end of section"** el playhead llega al final de la sección y queda en **hold**; también hay **loop section** ([transport OSC](https://help.disguise.one/designer/timeline-tracks-transports/osc/controlling)). | **Este es el patrón exacto de una espera:** la sección se queda en hold o en bucle (ambiente y respiración de luz) hasta que se cumple la condición, y entonces sigue. En pantalla: un bloque con borde rayado que "puede estirarse". |
| **TouchDesigner, Timer CHOP** | Segmentos con `delay/length/cycle/cyclelimit`, un **cue point** al que saltar con un pulso, y callbacks `onSegmentEnter`/`onDone` ([doc](https://docs.derivative.ca/Timer_CHOP)). | Una **espera con ciclo**: repite su bucle y, a los N ciclos, lanza la ayuda. Encaja con `fw`. |
| **Ableton Live** | Clips de Session con **launch quantization** y **Follow Actions**, y modos Trigger, Gate, Toggle y Repeat ([manual](https://www.ableton.com/en/manual/launching-clips/)). | La **cuantización del lanzamiento**: cuando el usuario cumple la condición, la respuesta entra en el próximo pulso, compás o ciclo de respiración, no en el cuadro exacto. Encaja con lo contemplativo y con "tiempos por timeline, nunca por sonido". |
| **Rive** | En un mismo archivo conviven **timelines** y una **state machine** con **inputs tipados** (number, bool, trigger), listeners y capas que corren en paralelo ([state machine](https://rive.mintlify.dev/docs/editor/state-machine/state-machine)). | **El contrato son los inputs tipados.** Cada mecánica expone sus entradas y salidas, y el editor solo habla con ellas. Es lo mismo que el "contrato de etapa" que ya usa el proyecto. |
| **Notch** | Grafo de nodos más timeline. Un **Block** es una pieza encapsulada que expone parámetros y se usa en la timeline de un media server como si fuera un clip de video ([Blocks](https://www.notch.one/features/notch-blocks)). | **Una mecánica es un bloque con parámetros expuestos.** El socio ve "Respiración: ciclo 6 s, 3 fases" y no el grafo interno. |

### Síntesis: el modelo híbrido que conviene

Son cuatro capas sobre **un solo documento**:

1. **La partitura.** Grupos (Voz, Sonido, Música, Háptica, Mundo, Objeto, Instrucción, Interacción) con **carriles persistentes que crea el usuario**, más clips, marcadores y secciones. Es el terreno del socio.
2. **Esperas.** Una sección elástica con hold o bucle (disguise / TD), una condición con nombre en la entrada (articy), salidas `Hecho / Tarde / Tope` (Flow), y opcionalmente cuantización a ciclo o compás (Ableton).
3. **Reacciones.** Un disparador lanza una mini-timeline (RCP / Unity Signals).
4. **Mecánicas como bloques.** Cada una con inputs y outputs tipados y parámetros expuestos (Rive / Notch).

**Los nodos no son un Blueprint libre.** Son **otra vista del mismo dato**: dependencias (anclas), esperas y reacciones dibujadas como grafo. Si editas una arista en el grafo, cambia el ancla en la timeline, y al revés. Así el socio nunca ve dos verdades.

---

## B. Sincronizar la web con el editor de Unreal

### Mecanismos disponibles

| Vía | Qué permite | Límites relevantes |
|---|---|---|
| **Remote Control API** | HTTP en el **30010**: `/remote/object/property`, `/remote/object/call`, `/remote/batch`, `/remote/search/assets`, `/remote/object/describe`. Hay tres modos de escritura: `READ_ACCESS`, `WRITE_ACCESS` y `WRITE_TRANSACTION_ACCESS`; el último entra al Undo y se replica en Multi-User ([HTTP ref](https://dev.epicgames.com/documentation/en-us/unreal-engine/remote-control-api-http-reference-for-unreal-engine)). WebSocket en el **30020**: `Preset.Register` → eventos `PresetFieldsChanged/Added/Removed/Renamed` ([WS ref](https://dev.epicgames.com/documentation/en-us/unreal-engine/remote-control-api-websocket-reference-for-unreal-engine)). | En el editor, la propiedad tiene que ser `EditAnywhere` (en BP, "Instance Editable"). **En PIE** basta `BlueprintVisible`, pero la ruta lleva el prefijo **`UEDPIE_0_`**. Escucha solo en `127.0.0.1` por defecto. **Viene apagado en builds empaquetados y en `-game`**; se enciende con `-RCWebControlEnable -RCWebInterfaceEnable` ([foro](https://forums.unrealengine.com/t/packaging-with-remote-control-api-rcwebcontrolenable/1956885)). El WebSocket está en Beta. |
| **Python Remote Execution** | Descubre editores por UDP multicast en `239.0.0.1:6766` y ejecuta Python por TCP. Se activa con "Enable Remote Execution" ([explicación](https://tianc377.github.io/posts/RemoteExecutionBetweenUnrealandDCC/)). | Ejecuta código arbitrario en el editor compartido, con el mismo riesgo que el MCP. |
| **DataTable desde JSON o CSV (Python)** | `fill_data_table_from_json_string/_file` y `..._csv_...` ([API](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/DataTableFunctionLibrary?application_version=5.4)). | **Solo funciona en el editor.** En un build empaquetado falla ([foro](https://forums.unrealengine.com/t/filldatatablefromjsonfile-causes-an-error-when-it-has-packaged/432515)). En runtime se lee la tabla ya cocinada. |
| **JSON crudo empaquetado** | Se agrega con "Additional Non-Asset Directories" y se lee con `FFileHelper` desde `ProjectContentDir`, que en build lee del pak. En Android queda dentro del OBB ([foro](https://forums.unrealengine.com/t/package-non-asset-file-and-load-them-at-runtime/320576), [Streeting 2026](https://www.stevestreeting.com/2026/09/11/loading-non-uasset-files-in-unreal-engine/)). | Desde Blueprint hace falta el plugin JSON Blueprint Utilities o un poco de C++. |
| **Generar la Sequence por Python** | `SequencerTools.create_event` y `create_quick_binding` ([API](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/SequencerTools?application_version=5.1)). | Es posible, pero produce binarios regenerados y no se lleva bien con las esperas. **No se recomienda.** |
| **Multi-User Editing** | Replica transacciones entre editores ([overview](https://dev.epicgames.com/documentation/unreal-engine/multi-user-editing-overview-for-unreal-engine?lang=en-US)). | Obliga a ambos a tener Unreal abierto. No sirve para el socio. |
| **Pixel Streaming del editor** | Transmite el editor al navegador (experimental) ([doc](https://dev.epicgames.com/documentation/en-us/unreal-engine/pixel-streaming-in-editor)). | Sirve como "mirar Unreal a distancia", no para sincronizar datos, y pesa mucho. |
| **Live Link** | Transmite animación y transforms en vivo. | No sirve para datos autorales. Se descarta. |

### Recomendación

1. **Una sola fuente de verdad en texto: `obra.json`, la partitura.** Va versionada en git porque es texto y se mergea, a diferencia de los `.uasset`. Usa **uids estables**: ya existe la regla de no renombrar keys (`README.md` del prototipo). Unreal y la vista previa web son **runtimes** que leen esa partitura (patrón Theatre.js).
2. **Web → Unreal por importación, no por escritura en vivo.** Un botón tipo Editor Utility, "Traer partitura", corre Python: JSON → DataTable o DataAsset, que `BP_Obra_SC` lee. Se ejecuta **solo cuando el turno del editor es tuyo** (la cola compartida). Así se respeta que un script fallido puede disparar un Undo y llevarse trabajo del nivel (CLAUDE.md §2.b).
3. **Unreal → web con un snapshot.** Conviene generalizar `ensayo_export.py` para que emita `unreal-snapshot.json`: TargetPoints `sc<K>_*`, duración real de cada audio importado, mecánicas con sus parámetros expuestos y la revisión de partitura importada. La web lo compara con el documento y muestra un **diff por elemento** ("Unreal tiene `sc3_door` 40 cm más a la izquierda", "VO_22 dura 0,8 s más que el clip").
4. **Modo en vivo opcional, más adelante.** Un Remote Control Preset que exponga **solo** los parámetros del director (ir a etapa X, DebugStart, play/pausa) y la posición de los locators:
   - la **lectura** va por `PresetFieldsChanged`;
   - la **escritura** solo durante PIE y con `WRITE_ACCESS`, sin transacción, para que nada entre al historial de Undo del nivel.
   
   Así la web funciona como mando a distancia del ensayo, sin tocar el `.umap`.
5. **Quest standalone: los datos van cocinados.** La DataTable se cocina con el APK. Además, **solo en builds Development**, `BP_Obra_SC` podría preferir un JSON de **override** en una carpeta escribible del APK (se sube con `adb push`) para ajustar timing en visor sin reempaquetar. La ruta exacta en Quest hay que verificarla antes. Para mandar órdenes en vivo al visor ya existe OSC en el proyecto, pero un navegador no envía UDP, así que haría falta el puente local.
6. **Hace falta un puente local (Node) en el PC de Beltrán.** El navegador no escribe en el repo, no envía OSC y no tiene un acceso confiable a `localhost` desde un sitio público: Chrome 142+ pide permiso de **Local Network Access** para HTTPS público → loopback ([Chrome](https://developer.chrome.com/blog/local-network-access)). Además, no está verificado si el CSP del Artifact permite esas conexiones. El puente lee y escribe `obra.json`, sirve el editor desde `localhost` y habla con Remote Control.
7. **Las revisiones tienen que ser visibles.** Cada guardado incrementa `rev` y guarda un hash. Al importar, Unreal guarda `importedRev`. La web muestra "Unreal en rev 41, partitura en rev 44" para que nadie pruebe en visor una versión vieja sin saberlo.

---

## C. Sincronizar pestañas, personas y alojamiento

### Dos pestañas (vista 3D y timeline) o todo en uno

- **Un documento, N vistas.** "Todo en uno" no es otro programa: son las mismas dos vistas en una ventana.
- **El transporte se pasa por `BroadcastChannel`.** Playhead, play/pausa, selección y hover son efímeros y no se persisten. Funciona entre pestañas del **mismo origen**, con clonado estructurado ([MDN](https://developer.mozilla.org/en-US/docs/Web/API/Broadcast_Channel_API)). Cada Artifact tiene su propio origen, así que dos pestañas del mismo Artifact sí comparten canal.
- **El documento lo maneja una sola pestaña.** Una **pestaña líder** (o un `SharedWorker`) guarda la única conexión al backend y el único **audio**. Si no, el sonido se duplica: hay que definir **qué pestaña suena**, que debería ser la de la vista 3D o la líder.
- **El reloj lo publica la líder.** Las demás pestañas interpolan su playhead a partir de ese reloj, sin tener uno propio.

### Dos personas

- **Lo de hoy no aguanta edición simultánea.** Hoy se escribe el documento entero y gana el último (`timeline.js:920/939`).
- **Opción 1, simple: documentos granulares.** Un documento por clip, carril o espera, cada uno con `rev`, y **bloqueo optimista**: si la `rev` cambió, se pide confirmación, al estilo `If-Match` ([MDN](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/If-Match)). Se suma presencia ("Socio está en Acto 2") y **bloqueo suave por grupo o acto**. Para dos personas que casi nunca editan a la vez, alcanza.
- **Opción 2, colaboración real: Yjs.**
  - Un `Y.Map` por elemento.
  - Un **`Y.UndoManager` por usuario**, que solo deshace lo propio.
  - Una capa **awareness** para cursores y selección, que no se persiste ([Yjs docs](https://docs.yjs.dev/)).
  - Servidor propio: Hocuspocus v4 (MIT; corre en Node, Bun o Cloudflare Workers) ([npm](https://www.npmjs.com/package/@hocuspocus/server)), Y-Sweet (persiste a S3 o disco) o y-websocket ([repo](https://github.com/yjs/y-websocket)). Servicio alojado: Liveblocks ([liveblocks.io](https://liveblocks.io/)).
  - Si importa poder **viajar en el historial**, Automerge ([automerge.org](https://automerge.org/)).
- **El versionado tipo git:** el historial "duro" es el **repo**, porque el puente commitea `obra.json` en los hitos. Dentro del editor hacen falta **versiones con nombre** ("Corte del socio 03-oct"), que es lo que ya insinúa el backup `timeline/<id>` (`timeline.js:914-916`), y un **diff visual** entre dos versiones.

### Alojamiento

| Opción | A favor | En contra |
|---|---|---|
| Artifact de claude.ai (como hoy) | Privado, se comparte, la base es compartida, cero infraestructura | Gana el último si no se rediseña. Llegar a `localhost` no es confiable. Depende de la plataforma. |
| Local en el PC de Beltrán + **Tailscale Serve** (privado, el socio entra a la tailnet) o **Cloudflare Tunnel** (requiere dominio) ([comparativa](https://dev.to/mechcloud_academy/cloudflare-tunnel-vs-ngrok-vs-tailscale-choosing-the-right-secure-tunneling-solution-4inm)) | El puente, Unreal y git están en la misma máquina | Si el PC está apagado, el socio no trabaja |
| Nube (documento en Workers, Y-Sweet o Liveblocks) + puente local como **cliente** | El socio trabaja a cualquier hora. Unreal se sincroniza cuando el puente se conecta. | Más piezas que mantener |

**Recomendación:** el documento en la nube (o en la base del Artifact rediseñada en documentos granulares) y el puente local como un cliente más, que conecta repo y Unreal. El socio **nunca** necesita tener Unreal.

---

## D. Recomendaciones concretas

1. **Modelo de datos primero (`obra.json` v2).** Cada `grupo` tiene `carriles[]` **persistentes** (con id, nombre y orden) y cada clip tiene un `laneId`. Al soltar sobre un carril ocupado, el editor ofrece "nuevo carril" o "empujar". **Nunca corta** (al revés que ISP). Esto elimina el reparto de `computeLanes`.
2. **Cinco tipos de objeto, nada más:**
   - **Clip**: VO, FX, música, háptica o luz, con duración.
   - **Marcador**: un punto, una etiqueta o un salto.
   - **Espera**: sección elástica, condición con nombre, bucle, `ayudaTras` (`fw`) y salidas `Hecho/Tarde/Tope`.
   - **Reacción**: disparador → mini-timeline.
   - **Bloque de mecánica**: inputs y outputs tipados y parámetros expuestos.
3. **Un vocabulario cerrado de condiciones** sale del contrato de cada mecánica (`sensor.enPecho`, `orbe.agarrado`, `trazos>0`, `save.sostenido>=3s`). El socio elige de una lista, no escribe código. Las lambdas de `guion.js` pasan a implementar ese vocabulario en la vista previa web, y Unreal lo implementa en cada BP.
4. **Tiempo relativo como regla.** Anclas de borde con offset, cuantización opcional de la reacción ("al próximo ciclo de respiración" o "al próximo compás"), y la duración esperada de cada espera (`expected`) para simular el recorrido. Al simular, el editor deja elegir el comportamiento del usuario: rápido, típico o lento (el lento muestra cuándo salta la ayuda).
5. **Tres vistas del mismo documento:** Pistas (estilo ISP), Nodos (grafo de anclas, esperas y reacciones) y Lista de cues (estilo QLab, para leer la obra de corrido). Se suma un **inspector único** que explica cada parámetro en lenguaje de sala ("cuánto tarda en aparecer", no "FadeInTime").
6. **Roles en lugar de actores.** El documento referencia `role: "Alma"` y Unreal resuelve el actor, igual que los bindings Replaceable de Sequencer. Si un actor cambia de nombre en el nivel, la partitura no se rompe.
7. **Puente local versionado.** Hace `obra.json` ↔ git, la importación a DataTable con un botón, `unreal-snapshot.json` → diff en la web, y un modo en vivo con Remote Control **solo en PIE** y sin transacciones.
8. **Pestañas:** pestaña líder con audio y reloj, `BroadcastChannel` para el transporte, y diseño de "un documento, N vistas".
9. **Colaboración en dos fases.** Fase 1: documentos granulares, `rev`, bloqueo suave por acto, versiones con nombre y diff. Fase 2, solo si de verdad editan a la vez: Yjs con Hocuspocus o Y-Sweet y UndoManager por usuario.
10. **Reutilizar el núcleo de timeline de ISP/VEATION** (herramientas, imán, marcadores, zoom con rueda, automatización) en lugar de escribir uno nuevo, cambiando solo la regla de solape.

## Riesgos

- **Dos verdades.** Si Unreal sigue teniendo tiempos "a mano" en sus BPs, la partitura se desincroniza sin avisar. Hace falta una auditoría de qué tiempos de `BP_Obra_SC` pasan a leerse de datos. Sin esa migración, el editor es un dibujo.
- **Escribir en vivo sobre el editor compartido.** Escribir con `WRITE_TRANSACTION_ACCESS` mezcla el Undo de la web con el de otras sesiones. Por eso: solo PIE, o solo importación por turno.
- **Vista previa web y Unreal que divergen.** La web es una aproximación en three r128. Cada condición del vocabulario necesita dos implementaciones, y conviene marcar en la UI qué está "verificado en visor".
- **Audio en el Quest.** La duración real de los assets manda. Si la partitura y el `.uasset` no coinciden, el diff tiene que avisar.
- **Remote Control en build.** Viene apagado, es Beta en WebSocket y no está pensado para Android. No hay que contar con él en el Quest.
- **Chrome LNA y CSP del Artifact.** Un Artifact no llega a `localhost` sin permiso, y puede que su CSP lo impida del todo. Conviene servir el editor desde el puente, o verificarlo antes de diseñar sobre esa conexión.
- **Theatre.js y otras dependencias de terceros.** El ritmo de mantenimiento es incierto y la versión de three no coincide. Hay que tomar los patrones, no las librerías.
- **Sobrediseño.** Yjs, Flow Graph o un StateTree completo agregan piezas que una obra casi lineal de unos 15 min probablemente no necesita. Conviene empezar por los carriles persistentes, las esperas como objetos y la sincronización por archivo.