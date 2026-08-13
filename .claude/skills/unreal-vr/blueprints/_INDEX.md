# 🗺️ Mapa de Blueprints del proyecto Soul Charger

Índice de **todos los Blueprints que existen** en el proyecto: qué es cada uno, dónde está, para qué sirve y su estado. El **detalle profundo** (variables por categoría, estructura de grafos, qué palanca ajusta qué) vive en el **tracker por-BP** de esta misma carpeta (`blueprints/<BP>.md`); este archivo es el **índice que los mapea**.

> 🔴 **REGLA (mantener vivo):** cada vez que crees o modifiques un Blueprint, **actualizá su fila acá** (estado, propósito) **y su tracker** (`blueprints/<BP>.md`). Si un BP no tiene tracker y lo vas a tocar, crealo (modelo: `BP_BreathSensor_V2.md`, plantilla: `_TEMPLATE.md`). Así, al retomar un BP viejo, sabés su estado sin releer el grafo.
>
> **Leyenda estado:** 🟢 funcional/validado · 🟡 en progreso · 🧩 stub/scaffold vacío · ⚪ existe pero sin auditar (completar al tocarlo) · 🗑️ deprecado.
> **Tracker:** ✓ = tiene tracker detallado · — = todavía no.

---

## Core — infraestructura compartida (`Content/SoulCharger/Core/`)
> ⚠️ Estos son **compartidos entre stages** → coordinar antes de tocar (ver `docs/WORKFLOW-EQUIPO.md`). Varios están **sin auditar en detalle** — auditar y documentar al primer trabajo sobre ellos.

| Blueprint | Ruta | Qué hace | Estado | Tracker |
|---|---|---|---|---|
| **BP_VRPawn_SC** | `Core/Pawn/` | El pawn VR de la obra (derivado del VR template; obra sentada). | ⚪ | — |
| **BP_SoulChargerGameMode** | `Core/Flow/` | GameMode; `DefaultPawnClass = BP_VRPawn_SC`. | ⚪ | — |
| **BP_FlowDirector** | `Core/Flow/` | 🔴 **AUDITADO 2026-08-11: es un SMOKE TEST, no el director.** Delays hardcodeados de 5/8/3 s que cargan `L_Test_Stage` y hacen un fade. Solo 2 variables. **Valor real: probó que `LoadLevelInstance(byName)` y `BP_FadeSphere.StartFade` funcionan.** Tiene el bug de llamar `LoadLevelInstance` **sin** `OptionalLevelNameOverride` → filtra un paquete nuevo por llamada. Lo reemplaza `BP_StageDirector` (§9.4). | 🗑️ a deprecar | — |

## 🦴 Esqueleto de la obra — paso 1 del orden de construcción (`Core/`, rama `core/esqueleto`)
> Nivel persistente + caminata entre salas. Es el **mayor riesgo técnico de la obra** y todo lo demás cuelga de ahí (`docs/OBRA-SOUL-CHARGER.md` §10). Empezado 2026-08-11.

| Blueprint | Ruta | Qué hace | Estado | Tracker |
|---|---|---|---|---|
| **BP_Room** | `Core/Rooms/` | La sala placeholder: piso disco de 10 m con patrón + cilindro de muro de 4,5 m sin techo, en el origen. `SetLight(Alpha)` sube y baja su luz; `Configure(Nombre, Acento)` la pinta desde el director. 🆕 `Dissolve(WaitTime)`: el caso terminal — apaga y **esconde** piso y muro para devolver el exterior. Se instancia como **streaming sublevel**: **6 mapas propios** (`Maps/Rooms/L_Room_{Hall,Entering,Recognizing,Loving,Attracting,Surrounding}`). 🔴 2026-08-13: **cada mapa guarda su sala EN SU POSICIÓN MUNDIAL real** (0·1200·…·6000, puerta +460) — el mapa es la autoridad; el director no mueve nada; parada del Journey y preview deben coincidir. Beltrán diseña cada sala en su mapa, en sus coordenadas reales. | 🟡 falta visor | [✓](BP_Room.md) |
| **BP_Walker** | `Core/Movement/` | La caminata: spline + rampa smoothstep + bob vertical y giro **acoplados a la cadencia del paso** + viñeta. Rango por tramo (`StartWalk(From, To, RampIn, RampOut)`) porque la caminata son **dos tramos de 5 m** con el negro en el medio. Todo parametrizable, incluido a cero. Vive en el persistente. | 🟡 falta visor | [✓](BP_Walker.md) |
| **BP_Vignette** | `Core/UI/` | Viñeta de comodidad: esfera pegada a la cámara (patrón de `BP_FadeSphere`), máscara **geométrica** (correcta en estéreo, no screen-space). Sin colisión para no tapar los line traces. | 🟡 falta visor + medición | [✓](BP_Vignette.md) |
| **BP_Door** | `Core/Doors/` | §9.8: dos paneles de 3×4 m con 10 cm de espesor, cartel `TextRender` con `StageName`, plano negro detrás, marco que **se traza** con barras que crecen. `Reveal`/`Open`/`Close`/`Configure` + `OnPawnPassed` por producto punto (no por overlap: el pawn se mueve con SetActorLocation). Una instancia en `L_Room_Placeholder` en X=460. | 🟡 falta visor | [✓](BP_Door.md) |
| **BP_StageDirector** | `Core/Flow/` | §9.4/§9.2: el ciclo **completo** precarga invisible → baja la luz + traza el marco → caminar hacia la **puerta CERRADA** → abre al llegar (`DoorOpenDelay`) con el negro cayendo → swap + reposiciona el pawn → sube la luz. Encadenado con `SetTimerByFunctionName`. 🆕 **2026-08-12 (revisión): 6 SALAS** (Hall + 5 etapas; el final NO es sala) vía **`RoomMaps`** (un `.umap` por sala, indexado por `PreloadNext(Suffix)`); `FinishObra` → **`BP_Room.Dissolve`**: la arquitectura se deshace en el lugar y queda el exterior. Serial monótono para las instancias y descarga bajo negro. | 🟡 3 recorridos completos verificados por log, falta visor | [✓](BP_StageDirector.md) |
| 🆕 **BP_Alma** | `Core/Amoeba/` | La GUÍA de la obra (≠ Proto Soul, decisión 2026-08-12). Placeholder: esfera unlit cálida de 35 cm (M_ProtoSoul), sin colisión, spawneada en `TP_Alma` por el Hall. La entidad real llega con arte + VO. | 🧩 placeholder funcional | — (ver BP_Stage_Hall.md) |
| 🆕 **BP_Anchor** | `Core/Debug/` | **El punto de spawn que se ve en el editor**: hereda de `TargetPoint` (por eso todas las búsquedas por tag siguen andando sin tocar nada), con esfera fantasma + su tag rotulado por Construction Script, ambos **Hidden in Game**. Los 14 TargetPoints de `L_Persistent` son ahora anchors. | 🟢 verificado en PIE | [✓](BP_Anchor.md) |
| 🆕 **BP_Journey** | `Core/Movement/` | **El recorrido completo de la obra en UN spline** con 8 paradas que se arrastran en el viewport + `LegTimes` por tramo (con fallback, agregar puntos no rompe). API por *input key*, nunca por distancia. 🆕 2026-08-13 (narrativa): paradas `[−2300, −560, 0, 1200..6000]` — aparición lejos en el vacío, llegada frente a la puerta del Center, Hall calzando con su preview. El director lo usa para TODO (corredor incluido). | 🟢 verificado en PIE por log; falta visor | [✓](BP_Journey.md) |
| 🆕 **BP_Stage_Entering** | `Core/Stages/` | La primera etapa REAL (paso 4): integra la cadena probada de Breath (`BP_Instructions` 5 páginas → `BP_BreathSensor_V2` → `Box_Breath`) al ciclo de salas; cierra por respiraciones completas (`bStageComplete` → `StageDone`) o por el cortafuegos EXTENDIDO (`ExtendTimeout` 240 s). El director la spawnea en el índice 1. | 🟡 ciclo verificado por log; la respiración necesita visor | [✓](BP_Stage_Entering.md) |
| 🆕 **BP_Stage_Hall** | `Core/Stages/` | §3 escena 3, primera subclase de `BP_StageBase` (paso 4): sobreescribe `RunStage` — acá **nacen** el HUD ProtoSoul, los 2 sensores y la elección (`BP_SoulChoice` spawneado, poll de `bChosen`, cierre por elección o cortafuegos con limpieza total). | 🟡 timeout verificado por log; la elección real necesita visor | [✓](BP_Stage_Hall.md) |
| 🆕 **BP_StageBase** | `Core/Stages/` | §9.4: la clase base de las etapas — *instrucciones → ejercicio → carga → aviso al director* (placeholder por prints, paso 3 del §10). **La spawnea el director en cada sala y se autodestruye al completar**; cierra vía `ForceComplete` (camino real) y el timer del director quedó como **cortafuegos** (`CurDuration + TimeoutMargin`). En paso 4, cada etapa sobreescribe `RunStage`. | 🟡 recorrido completo verificado por log, falta visor | [✓](BP_StageBase.md) |
| 🆕🧪 **BP_SelfTest** | `Core/Debug/` | **Batería de aserciones por log** (`TEST PASS/FAIL/SKIP/SUMMARY`). Permite verificar **funcionamiento sin visor y sin humano**: `StartPIE` → `GetLogEntries("TEST ")` → `StopPIE`. 🔴 **Correr también en `bSimulate:true`** — ya encontró un bug que el PIE normal escondía. 24 aserciones. **Ya cazó 5 bugs**, dos de ellos fatales: el del streaming que dejaba la obra en negro para siempre, y una duración en 0 que la dejaba clavada en el Hall. | 🟢 24 pass / 0 fail en PIE | [✓](BP_SelfTest.md) |
| **BP_DebugDirector** | `Core/Debug/` | §9.9: dispara `ForceComplete` del director (que cierra por el **mismo camino** que una finalización real, nunca teletransporta). Combo de **dos gatillos sostenidos** + modo **soak** para dejar el ciclo corriendo solo. 🆕 **HUD de debug** (2026-08-12): `TextRender` unlit pegado a la cámara con sala/tiempo/EEG/calma/ritmo, palanca `bShowHud`, refresh 0.25 s. Suelto en el persistente: se borra y listo, cero código de debug en las etapas. | 🟢 ForceComplete + HUD verificados por log · 🟡 combo y HUD sin visor | [✓](BP_DebugDirector.md) |
| 🆕 **BP_BioHub** | `Core/Signals/` | §9.3: **única fuente de verdad de calma y ritmo**. Servidor OSC propio, despacho por **comparación de string** (no `SwitchOnString`, que no se puede poblar por API), EMA de suavizado y flag de conexión con watchdog. Direcciones como variables → cambiar de dispositivo es tocar datos. Falta el binning de §9.5. | 🟡 ingesta y suavizado verificados en PIE | [✓](BP_BioHub.md) |
| **BP_SignalProvider** | `Core/Signals/` | Abstracción de la señal biométrica (respiración/latido/EEG) que consumen los stages. **Revisar antes de construir un mock del BioHub: puede que ya esté hecho.** | ⚪ por auditar | — |
| **BP_SignalProvider_Fake** | `Core/Signals/` | Mock de señal para testear sin sensor real. | ⚪ por auditar | — |
| **BP_FadeSphere** | `Core/UI/` | Esfera de fade a negro (transiciones). Compartida por los stages. | 🟢 | — |
| **BP_IntroFade** | `Core/UI/` | Fade de entrada al stage + spawnea el widget de instrucciones en su TargetPoint. | 🟢 | — |

## Stage Breath 🟢 (`Content/SoulCharger/Stages/Breath/`) — plantilla de la obra
| Blueprint | Ruta | Qué hace | Estado | Tracker |
|---|---|---|---|---|
| **BP_BreathSensor_V2** | `Stages/Breath/` | Sensor agarrable + detector de respiración + calibración/zona segura + conteo + hápticos, fusionado. Corazón del stage. `Step` frágil (no reescribir). | 🟢 | ✓ |
| **Box_Breath** | `Stages/Breath/` | La esfera visual; consumidor tonto que lee el sensor y anima escala + material emisivo + Niagara. | 🟢 | ✓ |
| **BP_Instructions** | `Stages/Breath/` | Máquina de 5 páginas (driver del widget world-space): `GotoPage/InitRefs/UpdateFade` + spawnea sensor/esfera. | 🟢 | — (ver memoria instructions-widget) |
| **WBP_BreathInstructions** | `Stages/Breath/Widget/` | El widget UMG de 5 páginas (visual). | 🟢 | — |
| **BP_BreathStageManager** | `Stages/Breath/` | Orquesta el cierre: fin de conteo → esfera a 0 → fade → reinicia. | 🟢 | ✓ |
| **BP_BreathProbe** | `Stages/Breath/Deprecated/` | Bitácora de los 26 tests que descubrieron el modelo de señal (ZigZag). Conceptualmente heredado por V2. | 🗑️ | ✓ |
| **BP_BreathSensor** | `Stages/Breath/Deprecated/` | Versión previa a la fusión en V2. | 🗑️ | — |

## Stage Heart 🟡 (`Content/SoulCharger/Stages/Heart/`)
| Blueprint | Ruta | Qué hace | Estado | Tracker |
|---|---|---|---|---|
| **BP_HeartSensor** | `Stages/Heart/` | Beat desde OSC + visualizador de zona segura (debug). 🟡 la esfera de debug queda fija en el mundo (pendiente que siga la cabeza). | 🟡 | ✓ |
| **Ball_Heart** | `Stages/Heart/` | Pulso de escala por latido (consumidor visual). | 🟡 | ✓ (`Ball.md`) |
| **BP_HeartInstructions** | `Stages/Heart/` | Driver del widget de instrucciones (duplicado de Breath). | 🟡 | — |
| **WBP_HeartInstructions** | `Stages/Heart/Widget/` | Widget UMG (duplicado de Breath). | 🟡 | — |
| **BP_HeartIntroFade** | `Stages/Heart/` | Fade + spawn del widget (duplicado). | 🟡 | — |
| **BP_HeartStageManager** | `Stages/Heart/` | Cierre del stage (duplicado de Breath). | 🟡 | — |

## Stage Touch = "Attracting" 🧩 (`Content/SoulCharger/Stages/Touch/`) — scaffold
> Plan completo: `docs/stages/touch-attracting.md`. Los stubs están vacíos, listos para construir por fase.
> 🆕 **2026-08-04 — la mecánica se rearmó** (sensores flotantes que encienden el beam, botón FINISH MELODY, sacar burbujas a mano, interp en TODOS los movimientos) y se cerró la **arquitectura de audio** (§3.b del brief). Fases nuevas **R1-R8** en el §4.b. Antes de tocar `BP_SoundBubble` o `BP_AimBeam`, leer la sección "Rearmado" de su tracker.

| Blueprint | Ruta | Qué hace (previsto) | Estado | Tracker |
|---|---|---|---|---|
| **BP_AttractDirector** | `Stages/Touch/` | Cerebro: registra `IMC_Touch`, **spawnea las burbujas por TargetPoint** (tag `BubbleSpawn`), cachea los slots por `StepIndex` y corre el playhead. Sigue **por timer**: Quartz bloqueado por un paso manual en el editor. | 🟡 | ✓ |
| **BP_SoundBubble** | `Stages/Touch/` | Burbuja sonora. Hover **push** (`HoverCount`, sirve a las 2 manos), far-grab siguiendo **el beam que la agarró**, colocación en el **slot más cercano**, **swap**, y pulso audioreactivo. La spawnea el Director, no se coloca a mano. 🆕 **2026-08-04: todo el movimiento pasó a una sola función `UpdateMove` con un único `VInterpTo`** (se acabaron los teleports) + **soltarla lejos de la mesa la manda de vuelta a casa**. Falta test en visor. | 🟢 | ✓ |
| **BP_SeqSlot** | `Stages/Touch/` | Un slot (data: `StepIndex` + `Occupant`). 5 en `L_Touch` en fila (X=55, Z=75), StepIndex 0-4 coincidiendo con el orden espacial. | 🟢 | ✓ |
| **BP_SeqTable** | `Stages/Touch/` | Mesa visual bajo los slots. **Sin construir** (los slots funcionan sin ella). | 🧩 stub | — |
| 🗺️ *(no es BP)* **Spawn de burbujas** | `L_Touch` | **20 `TargetPoint` con tag `BubbleSpawn`** (2026-08-05, eran 6). `BP_AttractDirector` en BeginPlay hace `GetAllActorsOfClassWithTag(TargetPoint, "BubbleSpawn")` y spawnea una `BP_SoundBubble` en cada uno. **Para cambiar cuántas/dónde flotan: se agregan o mueven TargetPoints, no se toca ningún Blueprint.** Repartidos en arco de ±95° alrededor del usuario sentado, radio 150-210, altura 105-185. | 🟢 | — |
| **BP_AimBeam** | `Stages/Touch/` | Láser de apuntado por mano. **2 instancias** (`bIsRight`), **attacheadas al pawn** en BeginPlay. Trace desde la pose *Aim*, hover push hacia la burbuja, y far-grab con **trigger sostenido** (`IA_Shoot_L/R` del XRFramework). 🆕 **2026-08-04: arranca APAGADO** (`bEquipped=false`) — lo enciende `BP_TouchSensor` vía `Equip()`. | 🟢 | ✓ |
| 🆕 **BP_TouchSensor** | `Stages/Touch/` | Sensor flotante que se toma **por contacto** (por distancia, sin colisión en el pawn). 2 en `L_Touch`, uno por mano (`bIsRight` instance-editable), y **cada uno solo responde a SU mano**: se attachea a ese mando, su mesh es la herramienta visible y **enciende el beam de esa mano** (`Equip`). | 🟡 falta visor | [✓](BP_TouchSensor.md) |
| 🆕 **BP_HandPointer** | `Stages/Touch/` | **Arranque limpio del puntero (2026-08-05).** Solo el **line trace por canal** que sale de la mano: se attachea al aim del pawn, traza `TraceDistance` hacia adelante y publica `TraceStart`/`TraceEnd`/`HitLocation`. Hoy se ve por **debug draw**; el visual va encima. Nace porque el Niagara de `BP_AimBeam` nunca se pudo hacer ver y su asset `LineTrace` quedó dañado. | 🟡 falta visor | [✓](BP_HandPointer.md) |
| 🆕 **BP_SaveButton** | `Stages/Touch/` | Botón **"FINISH MELODY"**. **Siempre presente**, al centro de la fila de slots y 20 cm más abajo; al llenarse los 5 slots **crece** (se "activa") en vez de aparecer, y crece un poco más al hover. Se confirma con **hold de 3 s** del gatillo apuntándolo → destruye las esferas sueltas, se esconde y dispara `OnConfirmed` (lo consume R6). | 🟢 | [✓](BP_SaveButton.md) |
| 🆕 **BP_TouchInstrPanel** | `Stages/Touch/` | **Panel de instrucciones (R7).** Copia de Calibration **con las dependencias a `Calibration/` cortadas**. Página 1 avanza al tomar un sensor; el resto con **gatillo sostenido** (radial). El **largo de `PageTexts` define cuántas páginas hay**. Al terminar se esconde y habilita `bGrabEnabled` en los beams. | 🟡 falta visor | [✓](BP_TouchInstrPanel.md) |
| **WBP_TouchInstr** | `Stages/Touch/Widget/` | El widget de las páginas (`SetScreen`/`SetInstruction`/`SetIconMaterial`/`SetTriggerProgress`). Sin dependencias a otros stages. | 🟡 | ver panel |
| 🗑️ **`Stages/Touch/Deprecated/`** | — | **Carpeta de descarte del stage (2026-08-05).** Todo lo de acá tiene **cero referencias** y no entra en la obra: `BP_TouchInstructions` + `WBP_TouchInstructions` (driver viejo duplicado de Breath, reemplazado por `BP_TouchInstrPanel`), `NS_TouchBeam` (el intento de beam abandonado) y `Ref/` (material de consulta de otro proyecto, con referencias rotas — era riesgo de cook). **No borrar sin avisar; queda como historia.** | 🗑️ | — |
| **WBP_TouchInstructions** | `Stages/Touch/Widget/` | Widget de instrucciones (fondo naranja). **Textos por definir.** | 🧩 | — |
| **SG_Melody** | `Stages/Touch/` | SaveGame de la melodía (array de 5 clip-IDs). **Falta el array.** | 🧩 stub | — |

## Stage Movement = "Surrounding" 🧩 (`Content/SoulCharger/Stages/Movement/`) — scaffold
> Plan completo: `docs/stages/movement-surrounding.md`. Sistema de dibujo 3D (cinta plana con frame por transporte paralelo, ProceduralMesh).

| Blueprint | Ruta | Qué hace | Estado | Tracker |
|---|---|---|---|---|
| **BP_DrawCanvas** | `Stages/Movement/` | Motor de geometría: dueño del `ProceduralMeshComponent` y de los datos del dibujo. `BuildTriangles`/`BeginStroke`/`AddPoint`/`EndStroke` + 3 auxiliares (`WriteRing`/`CollapseRing`/`PushMesh`) **construidos y compilando**; falta probarlo en visor. | 🟡 Fase 1 | ✓ |
| **BP_BrushTool** | `Stages/Movement/` | La herramienta: prop agarrable por proximidad que define la mano hábil, lee el gatillo y emite puntos al canvas. Auto-attach + gatillo por mano + `BeginStroke`/`AddPoint`/`EndStroke` **construidos y compilando**; ancho fijo, sin presión ni calma todavía. | 🟡 Fase 1 | ✓ |
| **BP_BrushPalette** | `Stages/Movement/` | La paleta de configuración: grilla plana de 9 celdas (3 color · 3 grosor · 3 pincel) en la mano no hábil, selección por toque. 4.1-4.3 hechas y probadas: **color funciona**; 🐛 **grosor no responde** (bug pendiente, ver tracker) — sospecha #1 = pose/alcance. | 🟡 4.3 + bug | ✓ |
| **BP_MovementIntro** | `Stages/Movement/` | Duplicado de `Core/UI/BP_IntroFade` recortado: **sólo el fade from black**. Se le sacó el spawn del `BP_Instructions` de Breath y los dos `OpenSource` de los MediaPlayer de Breath. En Fase 6 volverá a spawnear, pero el driver de páginas de Movement. | 🟢 ok | — |
| **WBP_MovementInstructions** | `Stages/Movement/Widget/` | Duplicado del widget de instrucciones de Breath, con el Border `BG` en **verde** (0.04/0.30/0.16, a 0.5). Es sólo el visual; el driver de páginas está sin hacer (Fase 6). Material propio: `Widget/Material/W_MovementInstruction`. | 🧩 scaffold | — |

## Herramienta Calibration 🟢 (`Content/SoulCharger/Calibration/`) — no es stage
| Blueprint | Ruta | Qué hace | Estado | Tracker |
|---|---|---|---|---|
| **BP_CalibDirector** | `Calibration/` | Máquina de estados de 7 segmentos guiados + persistencia por usuario. | 🟢 (falta test visor) | ✓ (cubre el sistema) |
| **BP_CalibProbe** | `Calibration/` | Sensor duplicado de V2 + `RecOn/RecOff`; calcula features para la captura. | 🟢 | ✓ (en `BP_CalibDirector.md`) |
| **SG_CalibSession** / **SG_CalibIndex** | `Calibration/` | Persistencia: un `.sav` por usuario + contador. | 🟢 | ✓ (en `BP_CalibDirector.md`) |
| **WBP_CalibInstructions** | `Calibration/Widget/` | Widget de instrucciones world-space (duplicado de Breath, Mode 1 icono+texto). Lo maneja el Director. | 🟢 (falta test visor + íconos) | ✓ (en `BP_CalibDirector.md`) |
| **BP_CalibInstrPanel** | `Calibration/` | Host del widget (WidgetComponent). El Director lo **spawnea en el TargetPoint `WidgetSpawn`** en runtime (patrón de los otros stages). | 🟢 (falta test visor) | ✓ (en `BP_CalibDirector.md`) |

## Externo
| Blueprint | Ruta | Qué hace | Estado | Tracker |
|---|---|---|---|---|
| **BP_OSCReceiver** | `/Game/OSC/` | Recepción de datos por OSC (única referencia funcionando del cableado del delegate). | 🟢 | ✓ |

---

## Paso 2 — el trío persistente (`Core/`, rama `core/esqueleto`)
| Blueprint | Ruta | Qué hace | Estado | Tracker |
|---|---|---|---|---|
| 🆕 **BP_ProtoSoul** | `Core/Amoeba/` | 🔴 **`bIsHUD` DEBE quedar false en el CDO** (2026-08-13): en true, CADA instancia se teletransporta por Tick a la posición del HUD frente a la cámara — las 5 candidatas se apilaban en la cara del usuario (3 días de diagnósticos errados, ver post-mortem en [[BP_SoulChoice]]). Solo `SpawnHudSoul` lo pone en true. · §5: **la ameba ES el HUD** — pulso = ritmo, agitación = calma, anillos = carga. Lazy-follow **solo en yaw** (seguir el pitch la pondría en la cara), zona muerta 10°, **pitch fijo −14° por debajo del horizonte**. `SoulMesh`/`SoulMaterial`/`VariantId` por instancia, aplicados en el **Construction Script**, para poder autorar las variantes elegibles lado a lado. Faltan anillos y flujo de elección. | 🟡 verificado en PIE, falta visor | [✓](BP_ProtoSoul.md) |
| 🆕 **BP_Sensor** | `Core/Sensor/` | §9.3: **uno por mano, persistente** — vive en el nivel persistente y **la etapa le dice en qué convertirse** (`SetMode(n)` indexa `ModeMeshes`/`ModeMaterials`, así agregar una etapa es agregar datos y no tocar el grafo). Refactor de `BP_TouchSensor` (§9.7), del que hereda las 5 lecciones ya probadas en visor: emparejamiento por mano, detección por **distancia al cuadrado**, `collisionEnabled=NoCollision` explícito, y verificar los valores **por instancia**. 🆕 tiene `Release()`, que el de Touch no tenía. `Mode` es un int hasta que exista el `UserDefinedEnum` (el API no los crea). 🆕 2026-08-13: mesh con **`MI_Sensor`** (blanco tenue) para que NO se confunda con una Proto Soul. | 🟡 tomar probado en visor; look nuevo sin visor | [✓](BP_Sensor.md) |

| 🆕 **BP_IntroSequence** | `Core/Flow/` | §3 escena 0: **el arranque de la obra** — negro 2 s → 3 logos de 1 s → título + subtítulo, y después llama `StartExperience()` del director (que ahora tiene `bAutoStart=false`). 🔴 **Sin UMG**: plano unlit + `TextRender`, y el fade es **por emisivo contra el fondo negro**, no por transparencia. Se planta solo frente a la mirada (sólo yaw, una vez). Faltan los botones y las imágenes. | 🟡 secuencia medida por log, falta visor | [✓](BP_IntroSequence.md) |
| 🆕 **BP_SoulChoice** | `Core/Amoeba/` | §3 escena 3: spawnea las Proto Souls candidatas **una por `TargetPoint` con tag `SoulSpawn`** (patrón de `BP_AttractDirector`: la composición se autora en el viewport, sin tocar Blueprints), detecta la elección por **proximidad de la mano** y la persiste. 💡 La elegida **no se convierte** en el HUD: el HUD **adopta** su identidad y las candidatas se destruyen. 🆕 2026-08-13: **la cadena de elección se reconstruyó** (nunca había compilado — ver post-mortem del tracker), **armado con manos despejadas**, candidatas 1.6×, arco de TPs cerrado al FOV (radio 80, ±44°). | 🟡 armado verificado por log, el toque necesita visor | [✓](BP_SoulChoice.md) |
| 🆕 **BP_SoulState** | `Core/Flow/` | El **GameInstance** (§9.3): lo único que sobrevive a un cambio de nivel, y por eso el lugar donde vive la elección de Proto Soul del usuario. 🔴 **Hay que registrarlo en `DefaultEngine.ini`** (`GameInstanceClass=`) o el cast falla **en silencio** y la elección no se guarda. | 🟢 compila, sin ejercitar | [✓](BP_SoulState.md) |

## Por clasificar (revisar qué son al tocarlos)
`Core/Flow/F_Beat`, `Core/Signals/F_Signal` — prefijo `F_`. ✅ **`Core/Amoeba/F_SoulPortrait` es un `UserDefinedStruct`** (auditado 2026-08-11): el retrato de datos del usuario. `Stages/Breath/Widget/Deprecated/Widget_1` (🗑️). Auditar y mover a la tabla que corresponda cuando se trabajen.

> Assets que NO son Blueprints (materiales `M_`/`W_`, Niagara `NS_`, audio, input `IA_`/`IMC_`, fuentes) no van en este mapa — se referencian desde el tracker del BP que los usa.
