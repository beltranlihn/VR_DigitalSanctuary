# BP_Sequencer_SC — la etapa Attracting de la versión limpia (Core/Attracting/)

📊 **Performance: MEDIDA en visor el 2026-09-24 y no llega.** 24,85 ms contra un presupuesto de
13,9 (40 fps de 72), **fill-rate bound** confirmado. Numeros, palancas probadas y pendientes en
[`docs/PERF-ATTRACTING-2026-09-24.md`](../../../../docs/PERF-ATTRACTING-2026-09-24.md).

> Ecosistema completo de la sala 4 (2026-08-26): **`BP_Sequencer_SC`** (director de la sala) + **`BP_SoundOrb_SC`** (la esfera con sonido) + **`BP_SeqSlot_SC`** (el slot) + **`BP_SaveMelody_SC`** (el botón SAVE MELODY). Todo en `/Game/SoulCharger/Core/Attracting/`.
> Colocados en **`MapsV2/RoomsV2/L_Attracting_SC`**: `Sequencer_Attracting` (5720,0,60) · 8 `SeqSlot_0..7` (X=5720, Y=−105..+105 cada 30, Z=85, `StepIndex` 0-7 izquierda→derecha) · `SaveMelody_Attracting` (5720,0,62, pitch 90) · `TP_orb_intro_attracting` (5745,0,115, en el panel) · **20 `BP_Anchor` `TP_orb_attracting_01..20` DETRÁS del widget** (x 5850-6250, y ±180, z 105-190 — una por sonido del módulo).
> **Estado: 🟢 flujo intro → pad alineado → esferas verificado en PIE por log y medición; beam en DOS manos verificado con manos posadas; 🔴 falta visor (todo el tacto).**

## La mecánica (spec de Beltrán, 2026-08-26)
1. Al entrar aparece Alma (flujo normal del guión).
2. Al **moverse Alma al costado** (`ShowPanel`, sub 2): aparecen **instrucciones (1 sola página, sin botón)** + **los 8 slots** + el botón SAVE MELODY, se **enciende el beam** ([[BP_Sensor_Soul]] modo 4) y aparece **UNA esfera sola, junto al widget de instrucciones**.
3. El usuario **arrastra esa esfera a cualquier slot** → la instrucción termina (el panel se va **por mecánica, sin botón**), esa esfera desaparece (y su slot se libera), **aparecen las 12 esferas alrededor, arranca el pad** y sigue la mecánica normal (hover = preview, gatillo = far-grab, soltar cerca de un slot = colocar/swap, lejos = vuelve a casa).
4. La etapa **no cierra por step**: cierra el botón **SAVE MELODY** (apuntar + hold 3 s, disponible desde el primer slot ocupado). Al confirmar: las esferas sueltas desaparecen, **los slots con sus esferas viajan al frente y un poco más arriba** (`FinalOffset`), suenan **2 pasadas completas** del loop, y todo desaparece → `StepTimeDone` del director → **comienza la carga** (paso 4 del guión).

## 🔴 La alineación del pad — por construcción, no por ajuste
`PadM1` mide **5,3333 s en loop = exactamente 8 pasos a 90 BPM**. `Boot` calcula **`StepDur = Duration(PadSound) / NumSteps`** (lee la propiedad `Duration` del SoundBase) y `StartPad` hace `Play(0)` + `CurrentStep=0` + `StepFire()` en el mismo frame → **el paso 0 cae con el arranque del loop del pad**. Cambiar de módulo = cambiar `PadSound` y listo. Verificado en PIE: `StepDur = 0.66666`.
⚠ El playhead corre por **acumulador de Tick** (no Quartz — la suscripción al metrónomo requiere un paso manual que el MCP no puede hacer). Sobre una etapa de minutos el drift es inaudible; si algún día molesta, la migración a Quartz es local a `TickSeq`/`StartPad`.

## BP_Sequencer_SC — el director de la sala
**Componentes:** `PadAudio` (AudioComponent, `bAutoActivate` false, `Sound` = PadM1).
**Fases (`Phase`):** 0 dormido · 1 intro (slots+botón+esfera única) · 2 tocando (pad + esferas) · 3 cerrando (2 pasadas finales) · 4 cerrado.

| Cat | Variables | Rol |
|---|---|---|
| 0 - Config (IE) | `ModuleSounds` (los 20 M1S1..M1S20) · `PadSound` (PadM1) · `NumSteps` 8 · `FinalPasses` 2 · `FinalOffset` (−120,0,35) · `OrbTag` orb_attracting · `IntroTag` orb_intro_attracting · `PanelTag` instr_attracting · `PadFadeIn` 1 · `PadFadeOut` 2 | las palancas |
| Z - Estado | `StepDur` `StepTimer` `CurrentStep` `Phase` `PassCount` `SpawnIdx` · `Slots[]` (por StepIndex) · `SensorRef` `ButtonRef` `IntroOrb` `PanelRef` `DirRef` | |

**Grafos:** `Boot` (timer 0,3 s: refs + `SetSound` + `StepDur` + cachea slots por `StepIndex` con `SetArrayElem bSizeToFit`) · `SeqIntro()` **API que llama el director** (`ArmBeam`): Phase 1, `ShowSlots` + `CachePanel` + `SpawnIntroOrb` (spawnea en el TP `orb_intro_attracting` con el clip 0) · `NotifyPlaced(Orb)` (lo llama la esfera al colocarse; en Phase 1 → `IntroDone`) · `IntroDone` (Phase 2: `FinishPanel` → `panel.Finish()`, `DropIntroOrb` → Vanish + libera slot, `SpawnOrbs` → una por TP `orb_attracting`, clip = `ModuleSounds[i % 20]`, `StartPad`) · `TickSeq(DT)` (watchdog + acumulador; wrap → `AdvanceStep` → `StepFire` = Pulse del slot + `PulseOnBeat` del ocupante; en paso 0 → `HandleWrap`) · **`TickIntro`** (fallback: si Phase 1 y el panel ya no existe —autotest o cierre externo— completa la intro sola) · `SaveMelody()` (**API que llama el botón**: Phase 3, `ClearLoose` = Vanish de toda esfera `!Placed`, `RaiseSlots` = `GoTo(pos+FinalOffset)` de cada slot y su ocupante) · `HandleWrap` (Phase 3: `PassCount++`; > `FinalPasses` → `CloseOut`) · `CloseOut` = `CloseGuts` + `TellDirector` (`Director_Story.StepTimeDone()`) · **`WatchStage`** (si Phase 1-3 y `Sensor.Mode != 4` → la etapa cerró por fuera → `CloseGuts`) · `CloseGuts` (Phase 4: `AdjustVolume(PadFadeOut, 0)` del pad — **por cirugía con `declaring_class=AudioComponent`**, ver trampas — + `HideSlots` + `HideNow` del botón + `VanishAll`).

## BP_SoundOrb_SC — la esfera
**Componentes:** `Body` (esfera 16 cm, `QueryOnly`+`BlockAll` → **frena el trace del beam**, así se puede apuntar) · `Voice` (AudioComponent, su clip).
**Knobs (IE):** `GrabHoldDist` 80 · `GrabSpeed` 3 · `TravelSpeed` 6 · `ReturnSpeed` 3 · `PlaceRadius` 25 · `HoverScale` 1.15 · `PulseAmount` 0.35 · `SlotZOffset` 12 (cuánto flota sobre el marker del slot).
**Los patrones heredados del `BP_SoundBubble` probado en visor** (mismos números): **un solo `VInterpTo`** para todo movimiento (`StepMove`; agarrar cancela el viaje, llegada con snap a <1 cm), velocidades separadas por origen del viaje (`MoveSpeed` = estado, lo escribe cada `PlaceInSlot`/`ReturnHome`/`GoTo`), colocación por **mínimo corriente** (`ScanSlot` sobre `Seq.Slots`, arranca en `PlaceRadius`), **swap** (colocarse en slot ocupado → el viejo `ReturnHome()`), soltar lejos → a casa, y la escala única `BaseScale × RevealT × pulso × hover` (el multiplicativo de `UpdatePulse`).
🔄 **`UpdateSpin(DT)`** (2026-09-24, primero en el Tick): `SpinRate ← FInterpTo(SpinRate, Grabbed ? SpinFast : SpinSlow, DT, SpinAccel)`, `SpinAngle += SpinRate*DT` (mod 360) y `Body.SetRelativeRotation(RotatorFromAxisAndAngle(SpinAxis, SpinAngle))`. El eje y las tres velocidades los copia `Setup` del director ([[BP_OrbDirector_SC]]); sin director quedan los defaults del CDO (22/150/4) y un eje inclinado fijo. Gira el **componente `Body`**, nunca el actor, para no tocar nada que lea la transformada del actor. Y como el material es un raymarch en espacio LOCAL, girar la malla gira la deformacion — por eso se ve.

**API:** `Setup(Sensor, Seq, Clip, ClipId)` · `Reveal()`/`Vanish()` (nace/muere por escala; `Vanish` destruye al llegar a 0) · `GrabStart()`/`GrabEnd()` (las llama el sensor; `GrabStart` libera su slot) · `PulseOnBeat()` (PulseT=1 + `Play()` si está colocada) · `GoTo(Loc)` (el viaje del cierre). Hover: polling de `Sensor.BeamHitActor == self` con flanco → preview `Play()` una vez (solo suelta). 🔒 **Y desde el 2026-09-24 la mano que sostiene una esfera no puede hoverear ninguna otra**: `HeldEndR`/`HeldEndL` del sensor clavan `BeamHitActor` en `HeldOrb` (ver [[BP_Sensor_Soul]]) — antes, al arrastrar sobre el secuenciador, el rayo pasaba de largo y encendia las esferas ya ancladas.

## BP_SeqSlot_SC — el slot
`Marker` (cilindro chato 20 cm, NoCollision — no roba el trace). `StepIndex` (IE, por instancia) · `Occupant` (lo escribe la esfera) · `Pulse()` (late al pasar el playhead, ocupado o no) · `Show()`/`Hide()` (escala) · `GoTo(Loc)` (el viaje del cierre) · `ClearOccupant()`.

## BP_SaveMelody_SC — el botón
Disco r=8 con `Label` TextRender **"SAVE MELODY"**. Aparece con los slots (`Show()`, lo llama `ShowSlots`). **Disponible desde el PRIMER slot ocupado** (`RefreshAvail` poll-ea `Seq.Slots`, solo en Phase 2) — la decisión del 2026-08-15. Apuntar + **hold 3 s** (`HoldDuration`): el sensor le avisa `BeginHold`/`EndHold`; `UpdateHold` cancela si deja de apuntarlo o deja de estar disponible. Escala = `BaseScale × Reveal × (1+AvailT×0.25) × (1+HoverT×0.12) × (1+progreso×HoldGrow)` — comunica disponible/hover/progreso como el original. `Confirm()` → `Seq.SaveMelody()` + se esconde (visibilidad + **colisión off**, si no el beam sigue chocando un botón invisible).

## Lo que cambió AFUERA de esta carpeta
- **[[BP_Sensor_Soul]]**: `TickBeam` ahora publica **`BeamStart`** y **`BeamHitActor`** (cirugía: 2 sets colgados tras `SetBeamHitLoc`, `HitActor` sale del `BreakHitResult` que ya existía). Vars nuevas `HeldOrb`/`HeldBtn`. **`BeamPress(Right)`/`BeamRelease(Right)`** colgados de los `then` libres de los `LabelOn`/`LabelOff` de los eventos `IA_Shoot_*`: solo mano hábil + modo 4; press = cast del `BeamHitActor` a esfera (grab + `Pulse()` háptico) o a botón (`BeginHold`); release = suelta ambos.
- **[[BP_Director_Story]]**: **`ArmBeam()`** colgada del `else` de `ArmHeart` — en `ShowPanel` de la sala 4 hace `SetStage(4)` + `MaybeInput()` (arma el IMC del gatillo) + `SeqIntro()`. **`StepTimes[4] = 300`** (cortafuegos; el cierre real es el botón → `StepTimeDone`, con la guarda `WaitFor=="time"` de siempre).
- **`WBP_Instructions` / panel de `L_Attracting_SC`**: la instancia quedó **`StartIndex 6 / EndIndex 6`** (una página); `Txt_6` con el texto en inglés (apuntar, gatillo, llevar al slot). **`InstrButton_Attracting` se ELIMINÓ del sublevel** (pedido explícito: en esta sala la instrucción termina por mecánica). El `Finish()` del panel busca el botón por tag y no lo encuentra → no-op, sin error.

## Verificado (2026-08-26, PIE `DebugStartRoom=4` + autotest)
`SEQ: boot slots=8` → `ArmBeam` → `SEQ: intro` + esfera de instrucciones → (autotest fuerza el panel) → `TickIntro` detecta el panel muerto → `SEQ: intro completada` → **`esferas=12`** → **`pad ON, paso 0 alineado`**. Medición directa en la instancia PIE: `Phase 2`, `StepDur 0.66666`, `CurrentStep` avanzando, `SpawnIdx 12`. Cero `Accessed None` de esta corrida.
⚠ Lo que PIE no prueba: hover/preview, far-grab, colocación/swap, el hold del botón, las 2 pasadas finales por el camino del botón (en PIE se verificó el cierre por watchdog) — **visor**.

## Trampas pagadas acá (las nuevas van a gotchas.md)
- 🔴🔴 **TODO el `execute_tool_script` es UNA transacción**: una excepción de PYTHON no atrapada (un `TypeError` de formato `%`, fuera de los `T()`) disparó el Undo y **revirtió el lote entero de writes** — y el mismo Undo se comió el actor `Director_Story` del persistente (repuesto; ver [[BP_Director_Story]]). El `try/except BaseException` por llamada NO cubre los errores del propio script.
- El `%` **no es operador del DSL** → `Math|Integer|%(Integer)`.
- `FadeIn`/`FadeOut`/`AdjustVolume` de AudioComponent: el DSL agarra el overload de **SynthComponent** ("Could not connect pin PadAudio to self") → cirugía con `declaring_class=/Script/Engine.AudioComponent`. `Play` y `SetSound` sí resuelven bien.
- `(Variables|X|SetObjeto)` **sin argumento = escribe null** — compila y funciona (así se limpian `Occupant`/`MySlot`/`HeldOrb`).
- `(for e arr ...)` existe en el DSL y **admite statements después del loop**; el cuerpo admite un multi-exec al final.
- §147 en actores del nivel: `RelativeLocation` por `set_properties` **solo aplica el PRIMER campo** → tres llamadas (x, luego y, luego z). Verificar con `get_actor_transform`.
- `Class|SoundBase|GetDuration` se materializa como **lectura de propiedad** `Duration` (el read lo etiqueta como GeometryCache — colisión del lector).

## 🔧 2026-08-26 (2ª pasada, tras el primer visor de Beltrán)
Reporte: *"El beam no aparece… Los slot y el botón están con un color negro… Las esferas deben estar por detrás del widget"*. Tres causas, tres fixes:
1. 🔴🔴 **El beam era invisible porque el trace nacía DENTRO del muro de la sala.** `Cylinder_001` (el anillo de muro de `Asset/RoomBase`, compartido por las 6 salas) tenía `CollisionTraceFlag = UseDefault` → su colisión simple es un **sólido convexo que llena todo el interior**: cualquier line-trace lanzado dentro de la sala pegaba a distancia 0 (medido: `BeamHitLoc == BeamStart`, largo 0 → mesh de escala z=0 = invisible). Era el **primer** line-trace dentro de una sala de RoomBase, por eso nunca se vio. ✅ Fix: **`CTF_UseComplexAsSimple` en el BodySetup de `Cylinder_001`** — los traces pegan en la superficie real del anillo; beneficia a las 6 salas; sin física que lo necesite. Verificado en PIE con la mano posada (truco del robot): trace de 8 m limpio, mesh visible escala (0.012, 0.012, 8), y apuntando a la esfera → `BeamHitActor = BP_SoundOrb_SC_C_0` + `Hovered=true`/`HoverT=1`. Ver gotcha §238.
2. **Slots/botón/esferas negros**: tenían el material default (que en el mundo horneado rinde negro). Ahora **3 MIs de `M_Beam_SC`** (unlit emisivo) en `Core/Attracting/`: `MI_AttractSlot` (gris tenue 0.12), `MI_AttractOrb` (cálido 0.55/0.50/0.38), `MI_AttractButton` (naranja 0.8/0.4/0.12 — el acento de la sala). Es placeholder digno; el arte final es de Beltrán (se cambia en la MI, sin tocar BPs).
3. **Las esferas van DETRÁS del widget** (pedido explícito): las 12 anclas se movieron de "arco alrededor del usuario" a **ocupar el fondo de la sala detrás del panel** — x 5850..6250, y −170..+150, z 105..185. Siguen siendo `BP_Anchor` arrastrables.

### 🎛️ MÓDULOS (pedido de Beltrán: "en attracting serán distintos módulos, y cada módulo tiene 20 sonidos")
El secuenciador es ahora **data-driven por módulo**: `ModuleIndex` (IE, 0) + `ClipsPerModule` (IE, 20) + **`ModulePads`** (array, un pad por módulo; hoy `[PadM1]`). `PickPad` (insertada al inicio de `Boot` por cirugía) elige `PadSound = ModulePads[ModuleIndex]`; los spawns toman los clips del bloque `ModuleSounds[ModuleIndex×20 .. +19]` (con fallback a `% Length` si el bloque no existe). **Agregar el Módulo 2 = pegar sus 20 clips al final de `ModuleSounds` y su pad a `ModulePads`; cambiar de módulo = `ModuleIndex`**. El `StepDur` sigue saliendo del pad del módulo activo, así cada módulo puede tener otro tempo/loop.

### 🔴🔴 El incidente repetido: OTRO script crasheado, OTRO actor comido (y dos reposiciones)
El mismo mecanismo del §231 mordió DOS veces más en esta pasada: un `.get()` con default (que el sandbox `_StrictDict` **no soporta**) crasheó el lote de módulos → su Undo **se comió `Sensor_Soul` del persistente**; y la instancia `Sequencer_Attracting` del sublevel también desapareció (recompiles con el nivel cargado + save posterior — la gotcha vieja de "recompilar borra actores en memoria"). **Ambos repuestos y verificados**: el sensor heredó del CDO sus 28 knobs EXACTOS a la tabla del tracker (verificado uno por uno) y `bDebugBreath` se apagó en el CDO (la instrumentación ya validada); el secuenciador heredó módulos/clips/pad completos. Diff de actores contra HEAD en los DOS mapas: cero faltantes restantes.

## 🙌 2026-08-26 (3ª pasada) — DOS MANOS, háptico por mano, beam terminando en la esfera, 20 esferas
Reporte de Beltrán: háptico en la mano contraria · el beam y la mecánica deben existir en las DOS manos · los slots no toman las esferas · el beam debe terminar en la esfera agarrada · 20 esferas (los 20 sonidos del módulo) · slots/botón más visibles. Lo que ya estaba resuelto en el viejo `L_Touch` (2 beams, mano por beam) y se había recortado al pasar en limpio — repuesto:
- **Beam en las dos manos** ([[BP_Sensor_Soul]]): componente nuevo `BeamMeshL`; las vars existentes (`BeamStart`/`BeamHitLoc`/`BeamHitActor`/`HeldOrb`) quedan como **DERECHA** y se agregan `BeamStartL`/`BeamHitLocL`/`BeamHitActorL`/`HeldOrbL`/`BeamHitL` + **`BeamEndR`/`BeamEndL`** (el fin VISUAL). `TickBeam` es ahora el despachador (`TickBeamR` + `TickBeamL`); cada mano lee su Aim directo del pawn (`GetMotionControllerRight/LeftAim`), traza, publica y dibuja su mesh (`HeldEndR/L` → si esa mano sostiene una esfera, **el beam termina EN la esfera**; el `BeamHitLoc` crudo queda intacto para el follow). `SetStage` prende/apaga los dos meshes. Gatillo: `BeamPress/Release(Right)` ramifican por mano — grab, botón y suelto por mano.
- 🔴 **El háptico iba a la mano contraria porque `Pulse(Right)` se llamaba SIN argumento** (default false = izquierda). Ahora `GrabTryR/L` llaman `Pulse` con el literal por **`Math|Boolean|MakeLiteralBool`** (un literal bool directo a función propia SE PIERDE — gotcha conocida; la conexión quedó verificada con `get_node_infos`).\n- **La esfera sabe qué mano la tiene** (`GrabbedRight`, param nuevo de `GrabStart`); `FollowBeam` y el hover leen el par de vars de SU mano (hover = cualquiera de las dos).\n- **Slots**: la lógica de colocación estaba bien cableada (verificada nodo a nodo) — se subió `PlaceRadius` 25→**40** y se instrumentó el suelto: `ORB: suelto - slot mas cercano a N` en el log → **el próximo visor dice el número real** y se calibra con dato, no a ojo.\n- **20 esferas**: 8 anclas más (`TP_orb_attracting_13..20`), total **20** detrás del widget — una por sonido del módulo (`i % ClipsPerModule` recorre 0..19).\n- **Materiales visibles**: los overrides del CDO **no llegan a instancias ya colocadas** (§294) → se escribieron POR INSTANCIA en los 8 slots y el botón; colores emisivos brillantes: slot cian (0.4/0.9/1.2), esfera cálida (1.2/1.0/0.6), botón naranja (1.5/0.6/0.12). ⚠ El `BeamMesh` derecho tenía colisión activa pese al tracker (declarado ≠ aplicado) — ambos beams ahora NoCollision.\n- ✅ Verificado en PIE con las DOS manos posadas: trazas independientes (starts y=10 / y=−15), ambas ven la esfera, `BeamMeshL` visible con largo real (0,61 m hasta la esfera), hover sostenido por la izquierda sola. Huérfanos barridos (`identical=true` en los 6 grafos tocados).\n- ⚠ Edge conocido sin resolver: la segunda mano puede \"robar\" una esfera ya agarrada por la otra (sin guarda anti-doble-grab). Anotado para visor.\n\n## TODO\n- [ ] 🔴 **Visor**: todo el tacto en DOS manos (hover, grab por mano, háptico por mano, soltar en slot — leer el `ORB: suelto` del log, swap, botón, pasadas finales).\n- [ ] Guarda anti-doble-grab (una esfera agarrada no debería ser agarrable por la otra mano).
- [ ] Arte: materiales de esfera/slot/botón (hoy gris default), posición fina de todo (datos de autor de Beltrán).
- [ ] La entrada de **AmbientClips de la parada de Attracting** en [[BP_Director_Music]]: decidir si se vacía (en el esqueleto viejo la sala no llevaba ambiente: manda la música del pad).
- [ ] Persistencia de la melodía (ClipId por slot ya existe; falta SG si se quiere guardar).
- [ ] Quartz si el drift pad↔playhead se oye en sesiones largas.

## 🎯 2026-08-26 (4ª pasada) — EL BUG DE LOS SLOTS: el desalojo se desalojaba A SÍ MISMO
El log del visor de Beltrán fue la prueba: **los sueltos caían a 1,6-14 cm del slot** (bien adentro del radio) y la colocación se REGISTRABA (la intro terminó por `NotifyPlaced`), pero las esferas volvían a casa. Causa: **la gotcha #1 del proyecto** (un nodo puro se evalúa POR CONSUMIDOR) — en `PlaceInSlot`, `(bind _occ (GetOccupant slot))` se evaluaba recién en el `IsValid` del final, DESPUÉS de `SetOccupant(self)` → `_occ == self` → **la esfera recién colocada se mandaba a sí misma a casa**, quedando como ocupante del slot (por eso pulsaba y sonaba con el secuenciador desde su anchor — el síntoma "está en el mundo y no en el slot"). En la intro no mordía porque `DropIntroOrb` limpiaba el slot antes de esa evaluación.
✅ **Fix**: el ocupante anterior se snapshotea en la variable **`EvictOrb`** con una ESCRITURA EXEC antes del `SetOccupant`, y el desalojo lleva guarda `!= self`.
- **Los traces ignoran al pawn** (`ActorsToIgnore=[PawnSC]` en `TickBeamR/L`): arregla el choque del beam con los dedos del mannequin y la causa más probable del **beam izquierdo invisible** (nacía dentro de la mano → largo 0).
- **Instrumentación sembrada** (leer el log tras cada visor): `ORB: agarrada mano DERECHA/IZQUIERDA` · `ORB: suelto - slot mas cercano a N` · `ORB: colocada en slot K` · `ORB: swap - la anterior vuelve a casa` · `ORB: vuelvo a casa` · `ORB: vanish` · `SEQ: la esfera de instrucciones se va y su slot queda libre` / `SEQ: OJO - la esfera de instrucciones no es valida`. Apagar cuando el visor apruebe.
- ✅ PIE post-fix: ambos beams sanos con manos posadas (derecha pega en la esfera intro a 87 cm; izquierda corre los 800 libres, ignorando al pawn).

## 🔍 2026-08-26 (5ª pasada) — beam izquierdo y choques con la mano: la §294 en la INSTANCIA del sensor
Visor de Beltrán: slots ✓, save melody ✓, etapa cierra ✓; faltaban el beam izquierdo y los choques con la mano. Medición en la instancia `Sensor_Soul` del persistente (no en el CDO):
- **`BeamMeshL` en la instancia tenía `OverrideMaterials: []`** — el material M_Beam_SC quedó solo en el template del CDO; la instancia repuesta heredó el componente SIN material → cilindro con material default LIT = negro en la sala oscura = **"el beam izquierdo no existe"**. ✅ Escrito en la instancia.
- **Ambos `BeamMesh` en la instancia seguían `QueryAndPhysics`/`BlockAllDynamic`** pese al NoCollision del CDO (§294). ✅ NoCollision en la instancia.
- El pawn está sano: `MotionSource` correcto en los 4 controllers, manos y HMD `NoCollision` de fábrica → **el choque con la mano NO viene del pawn** (y los traces además lo ignoran por `ActorsToIgnore`). Para nombrar al culpable real quedó sembrado **`DbgShortR/L`**: cuando un beam pega a <40 cm, imprime **`BEAM R/L corto contra: <actor>`** (con flanco por nombre, sin spam). El próximo visor lo dice.
- ✅ PIE: ambas trazas sanas, `BeamMeshL` visible y con material, colisiones apagadas.

## 🧿 2026-08-26 (6ª pasada) — la VIÑETA era el colisionador, preview con retardo, y el destino final por TargetPoint
Visor de Beltrán: la mecánica FUNCIONA (mano izquierda agarra, slots toman, save melody cierra la etapa). Tres ajustes:
1. 🔴 **El colisionador fantasma era la ESFERA DE LA VIÑETA** (`Vignette` de [[BP_Director_Movement]], pegada a la cámara): tenía `QueryAndPhysics` — la viñeta original (`BP_Vignette`) decía explícitamente *"sin colisión para no tapar los line traces"* y el duplicado limpio lo perdió. Explicaba el beam chocando "con la mano" **y** el beam izquierdo invisible (el aim izquierdo en reposo queda dentro de la esfera → trace a distancia 0 → mesh de largo 0). ✅ `NoCollision` en CDO **y** en la instancia del persistente.
2. **"A veces suena una melodía completa"** = la CASCADA DE PREVIEWS al barrer el beam por el campo de 20 esferas (cada hover disparaba su clip; se verificó que NO hay ningún reproductor de melodías viejas en los mapas). ✅ **`PreviewDelay` 0,25 s** (IE): el preview suena solo si el hover se sostiene — barrer ya no dispara nada. Vars nuevas `HoverAge`/`PreviewDone`.
3. **El destino del cierre lo define un TargetPoint**: `TP_seq_final_attracting` (BP_Anchor, tag `seq_final_attracting`, colocado en 5770/0/135 — Beltrán lo mueve a gusto). `RaiseSlots → FindFinalTP`: si el TP existe, cada slot viaja a `TP + (su posición − la del secuenciador)` (la fila conserva su forma alrededor del punto); sin TP, cae al `FinalOffset` viejo. Var `FinalTag` (IE) escrita en CDO e instancia. Antes iban a `FinalOffset` (−120 en X) que caía DETRÁS del pawn.
✅ PIE: intro + spawn sanos, cero `Accessed None`. ⬜ Falta visor de estos 3 + confirmar el beam izquierdo visible.

## 🧨 2026-08-26 (7ª pasada) — el colisionador de verdad: LA PROTO AMEBA DE LA CARA (cuerpo + 5 anillos en BlockAll)
Tras el reporte de regresión de Beltrán se ENUMERARON todos los componentes con colisión cerca del usuario (barrido por clase, no adivinando):
- 🔴 **`BP_ProtoSoul_SC`: `Body` (BlockAllDynamic) + `Ring0..4` (ProceduralMesh, BlockAll)** — la ameba anclada a la CARA, a ~30 cm de la vista. Explica de una vez: el beam derecho "chocando con algo cerca mío", el **beam izquierdo invisible** (la mano izquierda en reposo cruza esa zona → trace a cm → mesh largo ~0) y **la izquierda sin poder agarrar** (`BeamHitActorL` = la ameba → los casts a esfera/botón fallan). El `BP_ProtoSoul` viejo era sin colisión POR DISEÑO (el ConstExplorer selecciona por ángulo justamente para no dársela); la versión limpia la heredó de los defaults. ✅ `NoCollision` en CDO + **las 5 candidatas colocadas** (§294) + verificado en la ganadora sembrada en PIE.
- **`XRDeviceVisualizationLeft/Right` del pawn** también colisionaban (BlockAllDynamic) → `NoCollision` (el trace ya ignoraba al pawn, pero nada las necesita).
- **La "melodía constante"**: las esferas llevan los clips EN ORDEN (M1S1→20) y están agrupadas frente al usuario → cualquier barrido las toca en orden = su melodía. ✅ `PreviewDelay` 0,25→**0,6 s** y el preview a **volumen 0,5** (`SetVolumeMultiplier` por cirugía con `declaring_class=AudioComponent` — mismo overload trap que los Fades); el beat repone volumen 1.
- ✅ PIE sembrado: rayo derecho cruzando la zona de la cara → pega SOLO en la esfera de instrucciones; rayo izquierdo en pose de reposo → llega a la esfera (hover/grab izquierdo desbloqueado). Canario: 5 candidatas + sensor + director intactos tras los compiles.
⬜ Visor: beam izquierdo visible, agarre izquierdo, sin choques cerca del cuerpo, preview discreto. Los prints de diagnóstico siguen activos.

## 🎯 2026-08-26 (8ª pasada) — EL LOG LO NOMBRÓ: `SoulHUD_SC`
El print `BEAM R/L corto contra:` de la 5ª pasada entregó al culpable con nombre y apellido: **cientos de líneas `BEAM R/L corto contra: SoulHUD_SC`** en todas las corridas de visor de Beltrán. El **HUD pegado a la cámara** (`BP_SoulHUD_SC`, `Core/HUD/` — su `WidgetComponent` de 40×16 cm frente a la vista) **bloqueaba el canal Visibility** (la gotcha §54 de los WidgetComponents). Explicaba TODO lo restante: el beam derecho cortándose al cruzar la vista, y el izquierdo **permanentemente invisible** (la mano en reposo apunta a través del panel → muñón de ~20 cm). El código del beam izquierdo siempre fue idéntico al derecho — el bloqueo era físico.
✅ **`NoCollision` en `Hud` y `HeadRef`**: instancia del persistente + CDO (`Core/HUD/BP_SoulHUD_SC` — ojo: NO está en `Core/UI/`), compilado, y verificado EN VIVO en PIE (`collisionEnabled: NoCollision`, `Visibility: ECR_Ignore`).
📚 Moraleja de la saga completa de colisionadores fantasma (viñeta → ameba+anillos → HUD): **todo lo que viaja pegado al pawn/cámara en este proyecto debe nacer `NoCollision`** — viñeta, HUD, proto ameba y anillos, beams, visualizadores de mandos. Ninguno lo era. El diagnóstico correcto desde el principio habría sido el print con nombre (una pasada) en vez de hipótesis por turno.
⬜ Visor: beams en ambas manos completos y sin cortes. Los prints de diagnóstico siguen activos; apagarlos al aprobar.

## ✅ 2026-08-26 (cierre de jornada) — iteración EN VIVO con Beltrán en el visor: la etapa quedó FUNCIONANDO
Tarde de ping-pong visor↔MCP (él probaba, yo leía el log y corregía). Estado final: **mecánica completa validada en visor por Beltrán** — dos beams, agarre y háptico por mano, snap, colocación, swap, SAVE MELODY, pasadas finales y cierre. Lo que quedó construido en esta última tanda:

### 🔦 El beam ES el Niagara `LineTrace` (nunca más un mesh)
Decisión explícita de Beltrán (*"quedamos en no usar un mesh como láser"*). Los cilindros `BeamMesh/BeamMeshL` se **eliminaron**; el sensor lleva **`BeamFxR`/`BeamFxL`** (NiagaraComponent, asset **`Stages/Touch/VFX/LineTrace`** — el probado; config copiada de `BP_TouchSensor`: `bAutoActivate=false`). Manejo por tick en `DrawBeamR/L`: `SetWorldLocation(FX, BeamStart)` + **`SetNiagaraVariable(Position)` con nombre PELADO `"Beam_End"`** (la receta textual de `BP_TouchSensor.UpdateBeamEnd`; el sistema tiene `User.Beam_End` NiagaraPosition y `User.Beam_Starts` Vector3f que nadie escribe — el origen es la posición del componente). `BeamEndR/L` ya traen el override "termina en la esfera agarrada".
🔴 **`SetStage` maneja activación Y VISIBILIDAD** de ambos FX con el bool `==4`: `Deactivate` solo corta el spawn y el ribbon (vida ~infinita) **queda congelado en el aire** — la visibilidad lo esconde al instante en todos los cierres.

### 🎛️ La intro definitiva (enseña la mecánica completa)
`SeqIntro` → **`IntroDelay` 2 s** (el VO respira) → `SeqIntroGo` muestra TODO (panel incluido — el director ya no lo muestra en la sala 4: rama `(not (Room==4))` en `ShowPanel`, bind intacto) + arma el beam. **Colocar la esfera ya no termina la intro**: activa el botón (disponible en Phase 1 y 2); **el hold de SAVE la termina** (`Confirm` ramifica por fase: Phase 1 → `IntroDone` y el botón SE QUEDA; Phase 2 → el cierre real). `TickIntro` (fallback autotest) ahora exige `IntroReady`.

### 🧲 Snap con háptico + zona visible y editable
- Arrastrando, si el punto del beam entra en la **`SnapZone`** de un slot (SphereComponent wireframe, sin colisión): pulso háptico en la mano que arrastra (también al cambiar de slot vecino) y la esfera **se ancla al encaje** con **`SnapSpeed` 16** (dura y rápida; el arrastre libre sigue a `GrabSpeed` 3). Soltar ahí = queda (el scan la encuentra encima); salir del radio = se despega sola.\n- 🔴 **La zona es LO QUE SE VE**: snap Y encaje usan la esfera del slot (`GetScaledSphereRadius`); **`ZoneRadius`** (var por instancia, 30) la redibuja desde el Construction Script sin Play, y el componente se puede mover/achatar a mano. Los radios fijos `SnapRadius`/`PlaceRadius` del orb quedaron **dormidos**.\n- **Háptico al colocar** (`PlacePulse`, en la mano que soltó) además del snap.\n- **Color de estado**: agarrada/colocada = `ColorActive` (cian 0.35/0.9/1.3), libre/en casa = `ColorFree` (cálido 1.2/1.0/0.6) — `SetVectorParameterValueonMaterials` sobre `BeamColor`, knobs Vector por instancia.\n\n### 🎬 SAVE MELODY = fin de la interacción\n`SaveMelody` llama **`BeamOff`**: `Sensor.SetStage(-1)` (beams fuera — activación+visibilidad) + anula `BeamHitActor/L` (sin hovers congelados). El **watchdog vigila solo fases 1-2** (si no, este mismo apagado cerraría la mesa antes de las 2 pasadas). El destino final lo define **`TP_seq_final_attracting`** (la fila conserva su forma alrededor del punto; fallback `FinalOffset`).\n\n### 🔊 Sonidos\n- **Preview INSTANTÁNEO** (pedido de Beltrán: `PreviewDelay` 0.0; el candado una-vez-por-hover sigue) a **volumen 0.5**; el clip del beat a volumen 1 (`SetVolumeMultiplier` por cirugía — mismo overload trap de los Fades).\n- Clips vigentes: **`M1S10v3`** y **`M1S18v2`** (los reemplazados se ELIMINARON tras actualizar CDO + instancia + el `BP_AttractDirector` viejo y verificar referencers en cero).\n\n### ⚠ La trampa que mordió DOS veces hoy y hay que grabarse (§240)\n**Un componente agregado a un BP que ya tiene instancias colocadas llega a la instancia CON LAS PROPIEDADES PELADAS**: `BeamMeshL` llegó con `StaticMesh=None` (por eso el beam izquierdo mesh nunca se vio) y `BeamFxR/L` llegaron con `Asset=None` y `bAutoActivate=true`. 👉 Después de agregar un componente, **verificar en LA INSTANCIA** el asset/mesh y las props clave, siempre.\n\n### TODO / pendientes de la etapa\n- [ ] Apagar los prints de diagnóstico (`ORB:`, `BEAM corto contra`, `SEQ:`) cuando Beltrán dé el visto bueno final.\n- [ ] Guarda anti-doble-grab (dos manos sobre la misma esfera).\n- [ ] Arte fino (materiales/posiciones son de autor) · AmbientClip de la parada · Quartz si el drift se oye · Módulo 2 (pegar 20 clips + pad, `ModuleIndex`).


## 🆕 2026-08-27 — `SerializeMelody()` : la melodía como dato (F1 del plan de cierre)
Una función nueva, sin tocar nada de lo que ya andaba. Recorre `Slots`, y por cada slot **con
`Occupant` válido** emite **`StepIndex:ClipId`**; junta con comas sobre la variable de andamio `Tmp`
(String[]). Ejemplo real: `0:1,2:6,4:12,7:4`.

- Los slots vacíos **no aparecen** (no se emite un hueco): la melodía es "qué esferas hay y dónde".
- Rangos: `NumSteps` = 8 slots (0..7), `ClipsPerModule` = 20 ids (0..19).
- Lo consume [[BP_SoulArchive_SC]] (`TakeSeq`) para el campo `Melody` del `.sav`.
- ⚠ Al escribirlo: las variables de este BP están **en categorías**, así que el getter del array de
  slots es `Variables|Z-Estado|GetSlots`, **no** `Variables|Default|GetSlots` (el `Default` falla con
  "does not exist"). Y hay colisión de nombres con el `BP_SeqSlot` viejo: usar `Class|BPSeqSlotSC|…`.

---

## 🔊 2026-09-24 — el clip suena al AGARRAR, ya no al hacer hover
Pedido de Beltran: *"cada vez que hacemos hover en una esfera, suena el sonido de esa esfera. Eliminemos el
sonido cuando hace hover. Solo que suene una vez cada vez que agarramos una esfera."*

- **`UpdateHover(DT)`** quedo reducida a lo visual: `RefreshHover()` + el `FInterpTo` de `HoverT`. Se le saco
  todo el bloque del preview.
- **`GrabStart(Right)`** arranca ahora con `SetVolumeMultiplier(Voice, 0.5)` + `Play(Voice)`, **antes** de
  `SetGrabbed(true)`. Suena en cada agarre, tambien al re-agarrar una esfera ya anclada.
- El beat del secuenciador no cambia: `PulseOnBeat` pone `SetVolumeMultiplier(Voice, 1.0)` antes de sonar
  cuando la esfera esta `Placed`, asi que el 0,5 del agarre **no se queda pegado**.

⚠ **Quedaron huerfanos y NO se borraron** (la regla del proyecto es preguntar antes de sacar): la funcion
**`PlayPreview`**, las variables **`HoverAge`** y **`PreviewDone`**, y la perilla **`PreviewDelay`**
(`0-Config`). Son justo lo que habria que reconectar para devolver el preview al hover, asi que sirven de
documentacion de como estaba. Si el cambio se da por definitivo, se sacan las cuatro cosas juntas.

🚩 **La trampa del overload en `SetVolumeMultiplier`** (ya estaba anotada para los Fades y volvio a
morder): `find_node_types` devuelve **`Audio|Components|Audio|SetVolumeMultiplier` DOS veces**, y
`write_graph_dsl` elige la que no va — falla con *"Could not connect pin Voice to self"*. ✅ Se resuelve con
**cirugia de nodos pasandole `declaring_class`** (`/Script/Engine.AudioComponent`) a `create_node`.

---

## ✨ 2026-09-24 — `NS_OrbAttract_SC`: las particulas que van del orbe a la mano
Pedido con dibujo: *"cuando tengamos agarrada una esfera, que aparezcan sprites muy pequenitos que se vienen
hacia nuestra mano — el attracting. Si suelto, se desvanecen hasta desaparecer. Del color de la esfera."*

**No se construyo de cero: es un DUPLICADO de `NS_BreathParticles`**, que ya era lo que hacia falta — un
emisor CPU de sprites con el spawn rate expuesto a Blueprint (`User.SpawnRate`). De attracting no habia nada,
pero el esqueleto si. Cambios sobre el duplicado:
- `GravityForce` **deshabilitado**.
- **`PointAttractionForce` (la version V2)** agregado al `ParticleUpdateScript`, antes de `SolveForces`.
  🔴 **La V2 y no la vieja a proposito:** el `AttractorPosition` de la legacy es **`Vector3f`**, y la
  estacion esta a **362.000 cm del origen** — las posiciones de mundo alli van en `NiagaraPosition` (LWC).
  La V2 expone `Attractor Position` como `NiagaraPosition`, que calza con el user param sin conversiones.
- Ajustes: atraccion 1500, radio 400, **Kill Within Radius** con radio 3 (mueren al llegar a la mano),
  vida 0,7-1,3 s, sprite 1,2-3 cm, velocidad inicial 30 (un soplido leve para que se abran alrededor del orbe).

**User params y quien los consume** (verificado con `GetModuleInputValues`, no supuesto):
| Param | Tipo | Lo consume |
|---|---|---|
| `User.SpawnRate` | Float | modulo `SpawnRate` (heredado del original) |
| `User.Target` | **NiagaraPosition** | `PointAttractionForce → Attractor Position` |
| `User.OrbColor` | LinearColor | `InitializeParticle → Color` (Color Mode ya estaba en *Direct Set*) |

**Lado Blueprint** (`BP_SoundOrb_SC`), componente `Attract` (`bAutoActivate` false):
- **`GrabStart`** → `Activate(Attract)` + `SetNiagaraVariable(LinearColor)("OrbColor", OrbColor)`.
- **`UpdateAttract()`** en el Tick → `SpawnRate = Grabbed ? AttractRate : 0` y, si esta agarrada,
  `Target` = la mano (`BeamStart` o `BeamStartL` segun `GrabbedRight`).
- **El desvanecido sale gratis**: al soltar, el rate va a 0 y las particulas vivas terminan su vida y
  desaparecen solas. No hace falta codigo de fade.
- `AttractRate` (120) lo copia `Setup` del director, como las perillas de giro.

🔴 **`SetNiagaraVariable` va SIN el prefijo `User.`** — con prefijo busca `User.User.X` y es un no-op
silencioso. Por eso los literales son `"SpawnRate"`, `"Target"`, `"OrbColor"`.

⚠ **`bLocalSpace` del emisor es `false`** (heredado) y eso es lo que queremos: las particulas nacen en el
orbe y quedan en el mundo, asi que la atraccion las arrastra hacia la mano en vez de viajar pegadas al orbe.

### 1a pasada de ajuste (misma jornada)
*"muchisimo mas pequenas, muchisimo · mas lenta la velocidad · se deben ver por delante de la esfera · y con
transparencia los sprites"*.

| | antes | ahora |
|---|---|---|
| sprite | 1,2 - 3 cm | **0,15 - 0,4 cm** |
| atraccion | 1500 | **220** |
| velocidad inicial | 30 | **10** |
| vida | 0,7 - 1,3 s | **1,6 - 2,6 s** (mas lentas, mas tiempo para llegar) |

🔴 **Por delante de la esfera = `TranslucencySortPriority` del COMPONENTE, no del material.** Es el mismo
mecanismo del punto del puntero (gotcha 368): entre translucidos no hay test de profundidad, manda la
prioridad. El componente `Attract` va en **40**, encima de las esferas (20) y debajo del puntero (100).

💡 **La transparencia sin tocar la curva de vida.** El alpha final del sprite es
`Particles.Initial.Color.a × la curva del modulo ScaleColor`. Como `Initial.Color` viene linkeado a
`User.OrbColor`, alcanza con **empujar el color con el alpha ya bajado** desde Blueprint
(`Math|Color|NewOpacity`, un solo nodo) — queda la transparencia global Y se conserva el desvanecido por
vida que ya traia el sistema. Perilla: **`AttractAlpha`** (0,35).

⚠ Tambien se apago **`bCastShadows`** del sprite renderer, que venia en true: particulas que proyectan
sombra en un renderer movil fill-rate bound es gasto puro.

### 2a pasada: **el `Drag` era la causa comun de dos quejas**
*"si movemos la mano, el target debe seguir siendo la mano; al mover la mano quedan fuera"* + *"la velocidad
mas lenta"*.

🔴 **`Drag` estaba en 0,25 — casi nada — y eso explica LAS DOS cosas.** Con friccion baja la particula
acumula inercia: se pasa de largo del atractor y orbita, asi que al mover la mano la masa de particulas
**sale disparada fuera** en vez de reencauzarse. Y como el modelo es `v_terminal ≈ Fuerza / Drag`, con 0,25 la
velocidad terminal eran ~440 cm/s: rapidisimas.
✅ **`Drag` a 2,5** → terminal ~44 cm/s con la fuerza en 110. Lentas **y** obedientes: sin inercia acumulada,
la particula sigue la direccion de la fuerza, o sea la mano, cuadro a cuadro.
💡 **La leccion:** *"va muy rapido"* y *"no sigue al objetivo"* suenan a dos problemas y en un sistema
de fuerzas suelen ser **el mismo**: falta de amortiguacion. Bajar la fuerza sola no arregla el seguimiento,
solo hace que tarde mas en pasarse de largo.

⚠ Con vida corta + poca fuerza las particulas **mueren antes de llegar**. Por eso la vida subio a
**1,8-3,0 s**. Si vuelven a quedarse a mitad de camino, la perilla correcta es **subir la fuerza**, no la vida.

| | antes | ahora |
|---|---|---|
| Drag | 0,25 | **2,5** |
| atraccion | 220 | **110** |
| velocidad inicial | 10 | **6** |
| sprite | 0,15-0,4 cm | **0,35-0,8 cm** |
| vida | 1,6-2,6 s | **1,8-3,0 s** |

### 📈 La curva 0-1-0 en escala y opacidad
- **Opacidad**: el `Scale Alpha` de `ScaleColor` dejo de ser una curva y pasa a la entrada dinamica
  **`RampInOut`**, que Niagara trae hecha justamente para esto (sube suave, se sostiene, baja suave).
- **Escala**: se agrego el modulo **`ScaleSpriteSize`**, que ya viene en modo *Uniform Curve* indexado por
  `Particles.NormalizedAge`. Su curva **se escribe como JSON por MCP** — no hace falta abrir el editor:
  tres claves `(0,0) (0.5,1) (1,0)` con `RCIM_Cubic` + `RCTM_Auto` para que sea suave.
  💡 **Ese es el truco reutilizable:** un input de tipo `NiagaraDataInterfaceCurve` se lee y se escribe
  entero como `_DataInterface` con su `propertyValues`, asi que **cualquier curva de Niagara es editable por
  MCP** sin tocar la UI.

📍 Tambien se movio `UpdateAttract` al **final** del Tick (antes era el primero) y ahora escribe
`Target` **siempre**, no solo cuando esta agarrada: el dato que usa es el mas fresco del cuadro.

### 3a pasada: LOCAL SPACE + el cono termina ANTES de la mano
Dos correcciones de Beltran, y la segunda fue suya y mejor que mi plan:

**1. 🔴 Error de runtime:** *"Attempted to access Attract… not valid (pending kill or garbage)"*. La
esfera se **destruye** al terminar (`Vanish`), y el Tick alcanza a correr un cuadro mas con el componente ya
muerto. ✅ Todo el cuerpo de `UpdateAttract` vive ahora dentro de un `IsValid(Attract)`.

**2. 💡 `bLocalSpace = true` — idea de Beltran.** Yo venia persiguiendo el problema por el lado
equivocado: recalcular un punto de destino en MUNDO cada cuadro para que el cono no se despegara al mover la
mano. Con el emisor en **espacio local** el problema desaparece de raiz: se rota el **componente** para que
su eje +X apunte a la mano, y el cono entero queda rigido a ese eje. Mover la mano rota el marco de
simulacion completo — no hay nada que perseguir.
🚩 **La forma general:** cuando un efecto tiene que **mantenerse alineado** a algo que se mueve, no se
persigue con posiciones de mundo por tick: se pone el emisor en local y se **orienta el componente**.

**3. El cono NO llega a la mano.** Termina donde muere la linea del beam. Como el emisor es local, el
atractor es un punto **local** sobre +X: `(|mano - orbe| - AttractStop, 0, 0)`. Con `AttractStop` = 50 cm y
la esfera a `GrabHoldDist` 80, el cono corre de 80 a 50 cm de la mano — y ahi mueren (Kill Radius 3).
Perilla nueva: **`AttractStop`** (50).

⚠ **El precio del local space**, que hay que saber: las particulas **se mueven con la esfera**. Si la
esfera pega un salto (el imantado a un slot), el cono salta con ella en vez de quedar atras. Es el
intercambio que Beltran eligio a cambio de que el cono nunca se desalinee.

### 4a pasada: los DOS "chorros" eran el local space + la esfera viajando
Reporte: *"al agarrar sale un chorro desde mi mano hacia la esfera, luego se forma el cono, luego la suelto y
sale otro chorro"*.

🔴 **Diagnostico: el local space suelda la nube de particulas a la esfera, y la esfera VIAJA.** Al
agarrarla vuela desde su sitio en la constelacion hasta la mano (`StepMove` con `GrabSpeed` 3, casi un
segundo cruzando la sala); al soltarla vuelve a casa. En espacio local el cono entero se arrastra rigido en
esos dos viajes — y eso, visto desde adentro, es exactamente un chorro que sale y otro que vuelve.

✅ **Vuelta a `bLocalSpace = false`** + **compuerta de emision**: solo se emite si
`Grabbed AND dist(esfera, mano) < AttractMax` (130 cm). Asi:
- **mientras la esfera vuela hacia la mano**: no hay particulas. El primer chorro desaparece.
- **una vez cerca**: el cono se forma y se sostiene.
- **al soltar**: el rate va a 0 al instante y las particulas vivas **se quedan donde estan** y se apagan.
  El segundo chorro desaparece, porque en espacio de mundo nadie las arrastra.

El cono sigue alineado sin local space porque el **destino se recalcula cada cuadro sobre la linea
esfera→mano**: `Target = mano + normalize(esfera - mano) * AttractStop`. Y siguen la direccion de la fuerza
sin inercia gracias al `Drag` 2,5 de la pasada anterior.

🚩 **La leccion, que me costo dos rondas:** el local space resuelve la ALINEACION pero regala el
DESACOPLE. Sirve cuando el emisor esta quieto o se mueve poco; con un emisor que hace viajes largos, todo lo
emitido viaja con el. **Antes de elegir el espacio de simulacion hay que preguntarse cuanto se mueve el
emisor, no solo como debe verse el efecto.**

Perilla nueva: **`AttractMax`** (130) — la distancia esfera-mano por debajo de la cual se emite.

### 5a pasada: LOCAL SPACE **+ compuerta** — las dos piezas juntas, no una o la otra
Beltran dibujo la diferencia: en espacio de mundo, al mover la mano *"deja de existir el cono y las
particulas deambulan por el espacio"*; lo que quiere es el cono **rigido**, que se reorienta entero.

🔴 **Mi error fue tratarlo como una disyuntiva.** Probe local space (cono rigido ✅, pero dos chorros al
viajar la esfera ❌), despues mundo (sin chorros ✅, pero el cono se deshace ❌), y las presente como opciones
excluyentes. **No lo eran:** los chorros no venian del local space en si, sino de que la esfera **viaja**
largo al agarrarla y al soltarla, y en local space se arrastra lo emitido. La **compuerta de distancia**
(`AttractMax`) ya apaga la emision durante esos viajes — o sea que ya no hay casi nada que arrastrar.

✅ **Configuracion final: `bLocalSpace = true` Y la compuerta.**
- `SetWorldRotation(Attract, MakeRotFromX(mano - esfera))` cada cuadro → el eje +X local apunta a la mano y
  **el cono entero gira con el**, rigido, pase lo que pase con la mano.
- El atractor vuelve a ser un punto **local** sobre +X: `(|mano-esfera| - AttractStop, 0, 0)`.
- La compuerta mantiene el rate en 0 mientras la esfera viaja, asi que los dos chorros no reaparecen.

⚠ Queda un residuo conocido: al soltar, las **pocas** particulas vivas se van con la esfera de vuelta a
casa. Duran poco (convergen al atractor y mueren ahi), asi que es un borron breve en vez del chorro de antes.
Si molesta, la palanca es acortar la vida, no cambiar de espacio.

🚩 **La leccion, que me costo dos pasadas enteras:** cuando dos soluciones parecen excluyentes, vale la
pena preguntarse **si el defecto de una viene de la otra dimension del problema**. Aca el defecto del local
space dependia de *cuanto viaja el emisor*, y eso se podia controlar por separado. Presente un trade-off
donde habia una combinacion.

### 6a pasada: velocidad CONSTANTE, y la compuerta de distancia se elimina
Reporte de Beltran: *"el attract max hace que vayan mas rapido. Yo quiero que vayan a velocidad constante
suave. Pero que aparezcan apenas tomo la esfera"*.

**Tenia razon, y el acoplamiento era real aunque indirecto.** `AttractMax` no tocaba ninguna velocidad: era
la compuerta de emision. Pero al subirla, las particulas empiezan a nacer con la esfera **mas lejos**, el
atractor queda a mas distancia, y `PointAttractionForce` tiene mas pista para acelerar. Encima el modulo
tenia **`Use Falloff` activo** (exponente 0,5): la fuerza depende de la distancia al blanco. Y
`InitializeParticle` daba **masa aleatoria 0,75-1,25**, asi que `SolveForcesAndVelocity` repartia
aceleraciones distintas por particula. Tres fuentes de variacion de velocidad, ninguna controlable desde el
panel.

✅ **Se cambio el motor del movimiento: de FUERZA a VELOCIDAD FIJA AL NACER.**
- `AddVelocity` (Particle Spawn) pasa de "desde el emisor a 6 cm/s" a **`Velocity Origin` = `User.Target`**
  con **`Velocity Speed` = `User.Pull`**. El modo "From Point" calcula `normalize(pos - punto) * speed`, asi
  que con **speed NEGATIVA** la particula sale **hacia** el punto, a rapidez exacta y constante.
- `Drag` **desactivado y en 0** — cualquier drag hace decaer la velocidad, que es justo lo contrario.
- `PointAttractionForce` queda con **`Attraction Strength` = 0**: ya no empuja, solo sobrevive como
  **matador** (`Kill Within Radius`, radio 3 → 5) para limpiar lo que llega al blanco.
- La masa aleatoria deja de importar: no hay fuerzas que dividir por ella.

Como la velocidad ya no depende de nada, **el recorrido y la vida se pueden atar**: el BP empuja
**`User.Life` = recorrido / velocidad**, y `Lifetime Min` y `Lifetime Max` quedan los dos linkeados a ese
parametro. Resultado: la particula muere **siempre a la misma altura del cono**, se mueva la mano o no.
La punta no queda dura porque nacen repartidas en una esfera de radio 9, asi que mueren repartidas en ±9 cm.

🔴 **`AttractMax` se ELIMINO de los dos Blueprints.** La compuerta ahora es solo `Grabbed` — *"que aparezcan
apenas tomo la esfera"*. Los dos chorros de la 4a/5a pasada **no vuelven**: ya no hay que apagar la emision
mientras la esfera viaja, porque las particulas nacen apuntadas al blanco y con vida = recorrido/velocidad,
de modo que se consumen solas dentro del cono en vez de acumularse y ser arrastradas.

🚩 **La leccion:** *"la perilla X cambia Y"* puede ser cierto por un camino que no esta en el nombre de la
perilla. `AttractMax` era una **distancia de compuerta** y terminaba fijando una **velocidad de llegada**,
porque quien mandaba era una fuerza con falloff. Cuando una magnitud tiene que ser estable, no se pide a un
sistema de fuerzas que la mantenga: **se la escribe directo** (aca, velocidad al nacer) y se deja la fuerza
para lo que no es medible a ojo.

### 🎛️ Perillas del efecto, y donde vive cada una
**En el director (`GAL_12_OrbDirector`, `0-Config`)** — viajan por Blueprint, se copian en el `Setup` de cada
esfera, asi que **hay que reentrar a PIE** para que tomen: `AttractRate` (cuantas nacen por segundo) ·
`AttractAlpha` (opacidad del color) · `AttractStop` (cuantos cm antes de la mano termina el cono) ·
**`AttractSpeed`** (cm/s, constante — 25) · **`AttractSizeMin`/`AttractSizeMax`**.
🔴 `AttractMax` **ya no existe**: la emision arranca al agarrar, sin condicion de distancia.

**En el asset `NS_OrbAttract_SC`** — se ven en vivo en el preview del editor de Niagara, sin dar play:
`Shape Location` (radio 9 = boca del cono), `Add Velocity` (ya linkeado, no tocar), `Point Attraction Force`
(solo `Kill Radius`; su `Attraction Strength` **debe quedar en 0**), y las dos curvas. `Drag` esta apagado a
proposito. La **vida ya no se edita aca**: la calcula el BP (`User.Life`).

🔧 **Como se mapea una perilla de BP a un input de MODULO de Niagara** (no es un user param de fabrica):
1. `AddUserVariables` crea `User.X` del tipo del input.
2. `SetStackInputData` sobre el input del modulo con `_StackInputData_Linked` → `User.X`.
3. El BP empuja con `SetNiagaraVariable(...)` y **el nombre SIN el prefijo `User.`**.
Asi se hizo con `Uniform Sprite Size Min/Max` → `User.SizeMin`/`User.SizeMax`, y despues con
`Velocity Origin`/`Velocity Speed` → `User.Target`/`User.Pull` y `Lifetime Min`/`Max` → `User.Life`.
✅ Verificado leyendo el modulo: los dos inputs figuran como `Linked` a sus user params.

⚠ El emisor sigue llamandose **`BreathEmitter`** (herencia del duplicado) — nombre enganoso, renombrarlo
cuando se cierre el efecto.
⚠ Beltran **edita el asset a mano en paralelo** (la vida ya no es la que dejo este agente): no pisar
valores del asset sin leerlos antes. Es [[no-pisar-los-valores-del-editor]] aplicado a Niagara.

### ⬜ Sin ver
Compila limpio (`GetSystemCompileState`: sin errores ni warnings) y los tres params estan **linkeados**, que
es la verificacion que exige el gotcha de Niagara. Pero **nadie lo vio correr**: los numeros son una primera
apuesta y seguro haya que moverlos mirando.
