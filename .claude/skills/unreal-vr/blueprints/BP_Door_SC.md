# BP_Door_SC — la puerta entre salas (Core/Doors/)

## Purpose
La puerta que se cruza al pasar de una sala a la siguiente: **dos hojas que se abren de lado a lado**, el vidrio que **pasa de negro a su color**, un sonido **in situ** y un **título** arriba que cambia por sala.

Sucede a [[BP_Door]] (el placeholder de paneles del esqueleto viejo). Usa el arte real de Beltrán: `/Game/SoulCharger/Asset/Door/`.

## Status
🟡 **Compila, arranca sin errores y está colocada en los 5 sublevels.** Verificado en PIE: las 5 puertas loguean `PUERTA: lista` y **cero `Accessed None`**. **Falta el test en visor** — la apertura, el color y el calce con la pasada del usuario sólo se juzgan ahí.

## Dónde vive cada puerta — y por qué en el sublevel
🔴 **Decisión de Beltrán, y coincide con el contrato del proyecto: cada puerta vive DENTRO del sublevel de la sala a la que da entrada.**
- El mapa de la sala **ya es la autoridad de posición** en este proyecto. Si la puerta vive ahí, viaja con la sala cuando se mueve, y no hay dos archivos que sincronizar (que es justo el problema que dieron los TargetPoints en el persistente).
- Aparece y desaparece **con el streaming de su sala**, así que la mecánica de aparición se construye junto con el nivel.

| Sublevel | Actor | X | `StageName` |
|---|---|---|---|
| `L_Entering_SC` | `Door_ENTERING` | 1500 | ENTERING |
| `L_Recognizing_SC` | `Door_RECOGNIZING` | 3000 | RECOGNIZING |
| `L_Loving_SC` | `Door_LOVING` | 4500 | LOVING |
| `L_Attracting_SC` | `Door_ATTRACTING` | 6000 | ATTRACTING |
| `L_Surrounding_SC` | `Door_SURROUNDING` | 7500 | SURROUNDING |

Están puestas **en la posición de la sala** como punto de partida; Beltrán las mueve donde corresponda. La puerta de acceso al **Hall** será otro BP.

⚠ **Cómo se colocan por MCP** (no es obvio): `add_to_scene_from_asset` siempre agrega **al nivel actual**, y no hay tool para cambiar el "nivel actual" dentro del persistente. La vía que funciona es **abrir el sublevel como mapa** (`SceneTools.load_level`), colocar, guardar, y al terminar volver a abrir el persistente.

## Anatomía
| Componente | Qué es |
|---|---|
| `Frame` | `Marco_General` — el marco fijo (2,4 m de ancho × 3,4 m de alto) |
| `LeafL` / `LeafR` | `VentanaIzq` / `VentanaDer` — las dos hojas, 114 cm cada una. Cerradas están las dos en X=0 |
| `Title` | `WidgetComponent` en **World space** con `WBP_DoorTitle`, a 3,9 m de altura. El título se dibuja **en arco** (ver abajo) |
| `DoorAudio` | `AudioComponent` con `DoorOpen`, **espacializado y con atenuación propia** → se oye donde está la puerta |

## Materiales — dos maestros propios, ultrasimples (2026-08-17)
Los originales eran los de **importación FBX** (parent Phong, **45 parámetros**), lo contrario de lo que la obra necesita. Se reemplazaron por dos maestros mínimos en `Asset/Door/`, y se aplicaron **instancias** a cada slot de cada malla para que Beltrán las ajuste sin tocar el material.

| Maestro | Tipo | Parámetros — **y no más que esos** |
|---|---|---|
| **`M_DoorSolid`** | opaco, lit | `BaseColor` · `Specular` · `Roughness` · `Emissive` (multiplica al BaseColor) |
| **`M_DoorGlass`** | **Unlit + Translucent + TwoSided** | `Color` · `Opacity` · `Emissive` |

**Instancias aplicadas a los slots:**
| Malla / slot | Instancia | Valores |
|---|---|---|
| `Marco_General` / MarcoFuera | `MI_MarcoFuera` | gris profundo 0.12 · Spec 0.1 · Rough 0.5 · Emis 0.01 |
| `VentanaIzq` y `VentanaDer` / Marco | `MI_Marco` | idem |
| `VentanaIzq` y `VentanaDer` / Vidrio | `MI_Vidrio` | Color negro · Opacity 0.25 · Emis 0.01 |

🔴 **El vidrio es Unlit**, que es exactamente "translúcido sin ninguna reflexión": no tiene specular ni recibe luz, así que no hay reflejo posible. Es además lo más barato para Quest.
⚠ **Ojo con `Emissive` del vidrio en 0.01**: al ser unlit, ese escalar multiplica **todo** el color visible, así que a 0.01 el vidrio se ve casi negro. Para ver el color a pleno hay que subirlo cerca de 1 — es la palanca de intensidad del panel.
🔴 **El BP anima el parámetro `Color`** del vidrio (antes eran `DiffuseColor`/`EmissiveColor` del material FBX). Si se cambia el maestro, hay que actualizar los dos nodos `SetVectorParameterValue` de `Apply`.

## Las palancas
### A - Sala (instance-editable)
| Variable | Rol |
|---|---|
| `StageName` | **El texto del título**, por instancia. Es lo que se escribe en el widget. |
| `AccentColor` | **"Su color"** — el destino del degradado del vidrio. Arranca en blanco. |

## El título en arco (`WBP_DoorTitle.BuildArc`)
🔴 **UMG no tiene texto sobre un path** — ni UMG ni el motor traen nada nativo (confirmado en el foro de Epic y en la doc). Text3D sí tiene transformación por carácter, pero **su plugin no está habilitado en este proyecto** y genera malla por glifo, caro en Quest.

**Lo que se hizo** es el patrón que documenta el propio Epic (*Arranging Widgets in a Circle*): el widget tiene un `CanvasPanel` llamado **`Arc`** y `BuildArc(Texto, Radius, ArcDeg)` construye **un `TextBlock` por letra** sobre la circunferencia:
- `paso = ArcDeg / (n−1)` y el ángulo de la letra *i* es `(i − (n−1)/2) · paso` → **simétrico alrededor de 0, así que la palabra queda centrada sea cual sea su largo**.
- Cada letra: anclas y alineación al **centro** (0.5, 0.5), posición `(R·sin a, R − R·cos a)` y **rotada su propio ángulo**, de modo que sigue la tangente del arco.
- Se reconstruye entero en cada llamada (`ClearChildren` primero), así que **cambiar el texto funciona en caliente**.

| Variable (en la puerta) | Default | Rol |
|---|---|---|
| `TitleRadius` | 220 | Radio de la circunferencia. Más grande = arco más abierto y plano. |
| `TitleArc` | 45° | Grados que abarca la palabra completa. **0 = texto recto**; 120° = casi herradura. |

⚠ **La cuenta del ángulo tiene que ser en float.** La primera versión salió con el índice del bucle en entero y el DSL truncaba los ángulos; se fuerza con `ToFloat(Integer)` sobre el índice. Se detecta leyendo el grafo: aparecía un `ToFloat(Integer)` justo antes del `SetRenderTransformAngle`.

**Verificado en PIE:** las 5 puertas construyen su arco con la cantidad correcta de letras (8 ENTERING · 11 RECOGNIZING · 6 LOVING · 10 ATTRACTING · 11 SURROUNDING), dos veces cada una (el reintento a 1 s que cubre el doble `Construct` del `WidgetComponent`), y cero `Accessed None`. **La forma del arco es juicio visual: falta el visor.**

### B - Apertura (instance-editable)
| Variable | Default | Rol |
|---|---|---|
| 🆕 `bOpenByBell` | **false** | 🔴 **Cómo se abre esta puerta.** false = por **distancia** al pawn (lo de siempre) · true = **sólo por el timbre** ([[BP_Bell]]); el chequeo de distancia queda apagado. El timbre la encuentra por **actor tag** (su `BellTag`, default `bell`), así que la puerta tiene que llevar ese tag.
⚠ **Verificar el valor por instancia**: al agregar esta variable, la puerta suelta del persistente apareció en `true` en vez del default `false` — ver `gotchas.md` §119. |
| `OpenWidth` | **114** | 🔴 **Cuánto se corre cada hoja.** 114 = el ancho exacto de la hoja, o sea vano completamente libre. Menos = abre parcial. |
| `OpenTime` | 2.5 s | Cuánto tarda en abrir del todo. |
| `EasePower` | 2.0 | 🔴 **El easing, con un solo número**: `s = tᵖ / (tᵖ + (1−t)ᵖ)`. **1 = lineal · 2 = suave · 3+ = arranque y llegada más marcados.** Siempre simétrico (ease in = ease out) y siempre va de 0 a 1. |
| `OpenDistance` | 900 cm | 🔴 **A qué distancia del usuario empieza a abrirse.** Es la palanca para calzarla con la pasada: más grande = se abre antes. |
| `ColorTime` | 2.5 s | Cuánto tarda el vidrio en ir de negro a `AccentColor`. Independiente de `OpenTime` a propósito. |

### C - Audio (instance-editable) — hasta dónde se escucha
| Variable | Default | Rol |
|---|---|---|
| `AudioInner` | 400 cm | **Radio interno**: dentro de esta esfera el sonido está a volumen pleno. |
| `AudioOuter` | 3600 cm | **Caída**: cuánto más allá del radio interno tarda en llegar al silencio. Es el alcance real de la puerta. |
| `AudioSpread` | 200 cm | **Expansión estéreo**: qué tan separados se colocan los canales L y R en el espacio. Más grande = imagen más ancha; 0 = suena como un punto. |
| `SoundVolume` | 1.0 | Volumen. |

La atenuación se arma en `ApplyAudio()` y se aplica con `AdjustAttenuation` al arrancar: esfera, caída lineal, espacializado. 💡 **`AudioSpread` importa acá porque `DoorOpen` es estéreo** — y en este proyecto no hay spatializer con HRTF, así que la ubicación se resuelve por paneo (ver `audio-quest.md`).
⚠ Se aplican **en el arranque**: cambiarlos en el editor durante el play no se oye hasta el siguiente play.

### Z - Estado interno
`Elapsed` · `bOpening` · `bDone` · `PawnRef` · `MID_L` / `MID_R` (los materiales dinámicos del vidrio) · `CurColor`.

## Estructura de grafos
- **`EventGraph`** — `BeginPlay` → timer 0,3 s → `Boot`. `Tick` → `TickDoor(DeltaSeconds)`.
- **`Boot()`** — cachea el pawn, crea los **MID del slot 0 (el vidrio)** de cada hoja, **apaga la colisión del widget** (🔴 obligatorio: un `WidgetComponent` en world-space bloquea los line traces de los punteros, y ponerlo en el CDO no alcanza), deja la puerta cerrada y en negro, y escribe el título.
- **`TickDoor(DT)`** — si está abriendo, avanza `Elapsed` y llama a `Apply`; si no, mira la distancia al pawn.
- **`CheckPawn()` / `CheckDistance()`** — el guard de validez y la distancia; si es menor que `OpenDistance` → `StartOpen`.
- **`StartOpen()`** — prende el flag, resetea el tiempo y **suena `DoorOpen` en la puerta**.
- **`Apply(T)`** — 🔴 el corazón: `s = EaseCurve(T/OpenTime)` mueve `LeafL` a −`OpenWidth·s` y `LeafR` a +`OpenWidth·s`; y `ColorAt(T)` tiñe los dos MID (`EmissiveColor` **y** `DiffuseColor`).
  - 🐛 **Guarda `IsValid(MID_L)` sobre el teñido (2026-08-21).** `BeginPlay` no crea los MID: agenda `Boot` a **0,3 s**, y ahí nacen. Pero el `Tick` corre **desde el frame 1** y llama a `Apply`, que los lee → `Accessed None` durante esos 0,3 s. En la obra normal nunca se ve porque al llegar caminando a la puerta hace rato que pasaron los 0,3 s. Lo destapó el **salto de debug** de [[BP_Director_Story]], que deja al pawn pegado a la puerta en el primer frame: catarata de errores en el log de Beltrán. La guarda va sobre `MID_L` y cubre a los dos, porque nacen juntos en `Boot`. **El movimiento de las hojas queda FUERA de la guarda** — eso no depende de los materiales y debe seguir corriendo.
- **`EaseCurve(T)`** / **`ColorAt(T)`** — la curva y el color, aparte para poder tocarlos sin abrir el resto.
- **`RefreshTitle()`** — escribe `StageName` en el `TextBlock` del widget. Se llama en `Boot` **y otra vez al segundo**, porque un `WidgetComponent` puede crear su widget dos veces al arrancar.
- 🆕 **`ApplyTitleLight(L)`** (2026-08-17) — **el título se enciende y se apaga con la sala.** `SetTintColorAndOpacity(Title, (L,L,L,L))`: a 0 el texto queda negro **y transparente**, a 1 a pleno. 🔴 **No la llama la puerta: se la llama [[BP_Director_Rooms]]** desde su `ApplyLight(V)`, que barre todas las puertas del mundo. El motivo es que el `WidgetComponent` es UMG y **no lo pinta ningún material nuestro**, así que la perilla global `MPC_Room.RoomLight` no le llega sola — y hacer que la puerta LEYERA la colección no funciona (`GetScalarParameterValue` devuelve 0.0 siempre; el post-mortem está en el tracker del director).
  ⚠ El `Title` del CDO quedó con `tintColorAndOpacity = (0,0,0,0)` para que la puerta que entra por streaming **nazca apagada** y no destelle en blanco durante el negro.

## 🐛 Dos colisiones de nombre que cazó el `read` (y no el compilador)
1. 🔴 **`Ease` chocó con el nodo `Ease` DEL MOTOR** (`Math|Interpolation|Ease`). El DSL resolvió a la función nativa, así que **`EasePower` no se estaba usando** y el easing era el del motor. Se renombró a **`EaseCurve`**. Es la misma familia del caso `SetVignette` (§109): **no nombrar una función propia como algo que ya existe en el motor.**
2. **`SetVectorParameterValue` está duplicado** y el DSL agarró el de *Material Parameter Collection* (pines `Collection`/`ParameterName`/`ParameterValue`). Se resolvió con `create_node` + `declaring_class = /Script/Engine.MaterialInstanceDynamic`.

## TODO
- [ ] 🔴 **Visor**: ajustar `OpenDistance` y `OpenTime` contra la velocidad real de la pasada, y `EasePower` a gusto.
- [ ] Definir el `AccentColor` de cada sala (hoy las 5 están en blanco).
- [ ] Cerrar la puerta al pasar, si hace falta (hoy abre una vez y queda abierta).
- [ ] El widget del título: revisar tamaño de fuente en visor (18 px es el piso legible según Meta) y el costo — cada `WidgetComponent` es un render target aparte.
- [ ] La puerta de acceso al **Hall** (BP aparte, pendiente).

## Relacionados
- [[BP_Door]] — el placeholder viejo del esqueleto. · [[BP_Director_Movement]] — quien mueve al pawn que dispara la apertura.
