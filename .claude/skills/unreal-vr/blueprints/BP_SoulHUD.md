# BP_SoulHUD — el HUD físico con gráficos en tiempo real (Core/UI/)

## Purpose
El guión (acto 3): al calibrar en el Hall nace un HUD que acompaña TODA la experiencia, **pegado a la cabeza como objeto físico** (decisión de Beltrán 2026-08-14: no es UI de pantalla — es un actor world-space attacheado a la cámara, como las instrucciones pero head-locked).

## 🔴 v2 (2026-08-14, pedido de Beltrán): es UN WidgetComponent + WBP_SoulHUD — no meshes
La v1 de 21 StaticMeshes se reemplazó por **UMG**: el actor tiene UN componente **`HudWidget`** (`WidgetComponent`, Space=World, `WBP_SoulHUD`, DrawSize 800×400, escala 0.0004 ≈ **32×16 cm físicos**, **TickMode=Automatic explícito** (la trampa de widgets-vr), `RedrawTime 0.05` = redraw capado a 20 Hz, Transparent, TwoSided, yaw 180). **Diagramación = la lámina del guión (p.3)**:

| Widget (en `WBP_SoulHUD`) | Dónde (lienzo 800×400) | Qué es |
|---|---|---|
| `DotConn` (Image RoundedBox círculo) | arriba-izquierda (60,36) 24px | **Sensor conectado**: verde/rojo vía `SetConnectedW(On)` |
| `ImgSlot` (Image círculo translúcido) | arriba-derecha (680,30) 90px | **Espacio Proto Ameba** (el slot) |
| `BarCharge` (ProgressBar **BottomToTop**) | derecha (742,130) 18×220 | **Barra de carga vertical** vía `SetChargeW(P)` |
| `GraphPill` (Border píldora azul) + **onda por `OnPaint`+`DrawLines`** | abajo-centro (250,316) 300×60 | **Gráfico de calma tipo EEG** (refe de Beltrán): curva suave que corre de DERECHA a IZQUIERDA. `PushCalmW(Sample)` agrega al buffer `SamplesW` (48 muestras ≈ 6 s a 8 Hz), `TrimSamples` recorta, `RebuildPoints` reconstruye `PointsW` (la muestra nueva pegada al borde derecho x=536, y = 322+44·(1−v)) y **`OnPaint` dibuja `DrawLines(PointsW)`** con antialias, grosor 2.5 |
| `ImgPulse` (Image círculo blanco) | abajo-izquierda (186,322) 48px | **Pulso cardíaco** vía `SetPulseW(S)` (RenderScale) |

- **Los círculos y la píldora son `RoundedBox` con `roundingType=HalfHeightRadius`** — cero texturas.
- **Todo event-driven** (regla widgets-vr): el BP llama `SetChargeW`/`SetConnectedW`/`SetPulseW`/`PushCalmW`; cero bindings.
- El BP cachea el widget en **`CacheWidget`** (BeginPlay, con reintento a 0.2 s; al cachear **re-aplica `SetCharge(Charge01)`** por si la carga llegó antes que el widget).
- 🔴 **La receta del override `OnPaint` por MCP** (inversa a la de `RunStage`): `add_event("OnPaint")` FALLA con *"inherited function-shape override; must be placed as a function graph"* → **`add_function_graph("OnPaint")`** lo crea ya con su param `Context` y su `(return)`. El cuerpo: `(Painting|DrawLines Context (GetPointsW) tint true 2.5)`. Los puntos se reconstruyen SOLO al llegar muestra (8 Hz), no por paint.

## Status
🟢 **FUNCIONANDO — validado por Beltrán en editor y en Play (2026-08-14, cierre)**: los 5 elementos visibles y en su lugar (barra = cápsula vertical `FixedRadius` 9), la onda EEG dibujando, HUD a 30 cm verificado por `VerifyHudPose`, la proto ameba anclada al slot (32,76 cm por `VerifySoulPose`). ⬜ Falta: test con casco puesto (comodidad/legibilidad), nacimiento animado en la calibración del Hall (hoy `bDebugHudAlways`), desaparición animada en la carga final, arte.
🔴 **Al editar el layout a mano: solo DENTRO del recuadro punteado de 800×400 del Designer** — fuera de él el render target del componente recorta (gotcha #15a; así se "perdieron" 4 elementos hoy).

## 🎯 El anchor de distancia — el CUBO es la cabeza (rediseño pedido por Beltrán, 2026-08-14)
**La cadena en runtime (v2 corregida): cámara ← HUD (directo), y cámara ← cubo (solo referencia).**
🔴 **El HUD NO se cuelga del cubo**: colgarlo multiplicaba el offset por la **escala 0.15 del cubo** → HUD a 4,5 cm del ojo, invisible (gotcha #13). `AttachSelfTo` attachea **directo al CameraComponent del pawn** con `HudOffset` sin escalar. El cubo sigue pegándose a la cámara (`AttachCube`) como referencia visual, nada más.
**Verificación espacial permanente: `VerifyHudPose`** (timer 1 s tras el attach) loguea `HUD POSE: distancia a la camara cm = ...` — verificado 30.0 cm con el offset autoral (30, 0, −3). Es la aserción que atrapó el bug del padre escalado Y antes el de la escala 0.0004 del widget (100× más chico — comparado contra el `Panel` de BP_Instructions: 800px × **0.04** = 32 cm, no 0.0004).
- El **cubo de referencia de cabeza sentada** (`StaticMeshActor_0` del persistente, tag **`HeadRef`**, hoy en (−2235, 0, 160) junto al menú, **mobility Movable** — requisito del attach) se **pega a la cámara VR** en `AttachCube` (snap a cero = exactamente la cabeza; sigue Hidden In Game).
- El **HUD se cuelga del cubo** (`AttachSelfTo`, attach al `StaticMeshComponent0` del cubo) con offset = **`TP_HudAnchor` − cubo**, leído de sus posiciones de editor ANTES del attach.
- **Cómo se ajusta**: en el editor, el cubo y el `TP_HudAnchor` están uno al lado del otro (anchor hoy en (−2195, 0, 152) = cubo + (40,0,−8)) → **arrastrar el TP mirando el cubo da la referencia visual exacta de cuánto se mueve el HUD respecto de la cabeza.** Si Beltrán mueve el cubo, mover el TP con él (el offset es la RESTA de ambos).
- Fallbacks: sin cubo → attach directo a la cámara con `HeadRefLoc` fija del CDO; sin TP → `HudOffset` default (40,0,−8).
- Funciones: `ReadAnchor` (cachea cubo por tag + `HeadRefLoc` = su posición real) → `ReadAnchorOffset` (TP − HeadRefLoc) · `AttachHead` → `AttachCube(Cam)` + `AttachSelfTo(Cam)`.
- Verificado por log (2026-08-14): cubo encontrado → offset del TP → "cubo pegado a la cabeza VR" → "colgado del cubo con el offset autoral", cero `Accessed None`.

### 🖼️ El preview de editor — ver el HUD sin dar Play
**`SoulHUD_Preview`** (instancia de este BP en `L_Persistent`, **hija del `TP_HudAnchor`** en el outliner, `bEditorPreview = true`): se ve en el editor exactamente donde va a estar el HUD respecto del cubo de cabeza, y **arrastrar el TP mueve el preview con él**. En BeginPlay el flag la **autodestruye** (patrón `bEditorPreview` de [[BP_Room]]) — en juego solo existe el HUD que spawnea el director. Verificado: una sola secuencia de arranque del HUD en el log, cero residuos. ⚠ `bEditorPreview` es **false en el CDO** (los spawneados viven) y **true solo en la instancia preview** — no tocar ese default.

## Registro de variables
| Variable | Default | Rol |
|---|---|---|
| `BioRef` | — | El BioHub, cacheado en BeginPlay (`CacheBio`). TODAS las señales salen de él. |
| `BarsRef` | [] | Las 16 barras, recolectadas por tag en `CollectBars`. ⚠ El orden = orden de creación de componentes (Bar00..15); si algún día se reordenan los componentes, el gráfico se desordena. |
| `HudOffset` | (40,0,−8) | Offset relativo a la cámara. Lo pisa `ReadAnchor` si existe `TP_HudAnchor`. |
| `HeadRefLoc` | (0,0,185) | La referencia de cabeza sentada (= el cubo del persistente). |
| `Charge01` | 0 | Carga acumulada 0–1. Solo la escribe `SetCharge`. |
| `BeatPhase` / `GraphCursor` | 0 | Estado del pulso / del anillo del gráfico. |
| `GraphRate` | 8 Hz | Frecuencia de muestreo del gráfico (16 barras = ventana de 2 s). |

## Estructura de grafos
- **BeginPlay** — `CacheBio` · `CollectBars` · `ReadAnchor` · `AttachHead` · timers loop `GraphStep` (1/GraphRate) y `ConnStep` (0.5 s).
- **Tick** — `UpdateHud(Δ)` (pulso del corazón; gateado por IsValid del BioRef).
- **`AttachHead`** — receta de `BP_FadeSphere`: pawn → `GetComponentByClass(CameraComponent)` → `AttachActorToComponent(self, cam, Snap/Snap/KeepWorld)` → `SetActorRelativeLocation(HudOffset)`. Guard de pawn (Simulate: queda suelto y avisa).
- **`GraphStep` → `GraphPaint(Calm)`** — el guard IsValid extraído a función (regla del multi-exec).
- **`SetCharge(NewCharge)`** — clamp + escala/posición del fill + log.

## ⚠ Trampas pagadas al construirlo (2026-08-14)
1. 🔴🔴 **`Utilities|IsValid` en posición de EXPRESIÓN resuelve al MACRO multi-exec y el write produce un grafo ROTO que COMPILA**: el cuerpo entero quedó como isla desconectada (la función quedó vacía) y el primer PIE "verde" nunca pintó el gráfico. **Lo delató el barrido de huérfanos** (20 borrados, quedaban 3) + el `read_graph_dsl`. Regla: IsValid SIEMPRE como statement con `(:"Is Valid")`, y el guard en expresión se extrae a función. **Después de CADA write, leer el grafo.**
2. **`Actor|GetComponentsbyTag` por posicionales pierde los DOS args en silencio** (quedó `ComponentClass=ActorComponent, Tag=None` → 0 barras). Fix por `set_pin_value`. Verificar pins de nodos con args de clase+name.
3. **`collisionEnabled` no existe como propiedad plana del template** — es **`BodyInstance.collisionEnabled`** (anidada). El set plano falla; el anidado funciona (21/21 verificado).
4. `Transformation|SetActorRelativeLocation` y las llamadas a funciones propias con expresiones → **usar keyword args** (`:NewRelativeLocation`, `:Suffix`…) o el parser intenta conectar al pin `self`.
5. No existe `Utilities|Conversions|ToFloat(Integer)` — el operador `(* 0.2 int)` promueve solo.
6. **`CaptureViewport` durante PIE capturó el viewport del EDITOR** (con gizmo de ejes), no la vista del juego — inútil para verificar el HUD. El visual es territorio del visor.

## TODO
- [ ] 🔴 **Visor**: tamaños, distancia (arrastrar `TP_HudAnchor`), legibilidad, comodidad head-locked (¿lag suave? hoy es attach rígido 1:1).
- [ ] Nacimiento animado elemento por elemento (calibración del Hall, guión acto 3) + muerte animada (carga final).
- [x] ~~Anclar la proto ameba elegida al slot~~ → hecho por `BecomeHud()` de [[BP_ProtoSoul]] (2026-08-14).
- [ ] Quién lo spawnea en la obra real: el Hall durante la calibración. Hoy solo lo spawnea `SeedHud` del salto debug (con `SeedHudCharge` = `0.2·(etapa−1)`, la carga de las etapas **ya vividas**).
- [ ] **La muerte animada del HUD** en la carga final (etapa 5 → 100 %), guión acto 8.

## 🔌 Quién llama `SetCharge` (2026-08-14 tarde)
| Llamador | Cuándo | Valor |
|---|---|---|
| `BP_StageDirector.SeedHudCharge` | salto debug, al sembrar | `0.2 × (DebugStartStage − 1)` — de una |
| **[[BP_Ceremony]]`.ApplyCharge`** | durante la ceremonia de carga | **rampa** `lerp((n−1)×0.2 → n×0.2)` en pasos de 0,1 s durante `RingTime` (2,6 s), en paralelo con el anillo que se dibuja |
⚠ `SetCharge` **loguea en cada llamada**, así que una ceremonia deja ~26 líneas `HUD: carga ...` en el log. Es deliberado (se ve la rampa subir), pero si algún día molesta, ahí está el ruido.
- [ ] Arte real de los 5 elementos (hoy basic shapes + MI_Sensor).

## Relacionados
- [[BP_BioHub]] (todas las señales) · [[BP_StageDirector]] (`SeedHud` en el salto debug; la ceremonia de carga llamará `SetCharge`) · [[BP_ProtoSoul]] (el ocupante futuro del slot) · `TP_HudAnchor` en `L_Persistent`
