# Las 4 subclases nuevas de etapa (Core/Stages/, 2026-08-13 noche) — tracker compartido

> Hermanas de [[BP_Stage_Entering]] y [[BP_Stage_Hall]]. Todas siguen el MISMO patrón: hija de [[BP_StageBase]], override de `RunStage` vía `add_event` (evento `EventRunStage` → función `<X>RunBody`), `EventDestroyed` → `Cleanup<X>` (cortafuegos con limpieza total), y `ExtendTimeout(DirectorRef, <X>Timeout)` como primera línea del body. El director las spawnea por índice en `SpawnEnteringOrBase` (cadena de `elif` anidados — así se anida el elif en el DSL). Verificadas por log en corrida completa 16:20-16:23, cero `Accessed None`, cero residuos.

## BP_Stage_Loving (índice 3) — contemplativa, 3 preguntas
- **Mecánica**: spawnea un `TextRenderActor` en el anchor `QuestionSpawn` de `L_Room_Loving` (M_TextUnlit, WorldSize 10, centrado), muestra `Questions[i]` y avanza por timer. Al agotar las preguntas → `CleanupLoving` + `StageDone()` (cierre por camino real, ÚNICA de las 4 que cierra sola).
- **Variables**: `Questions` (array de Text, CDO: 3 preguntas en inglés) · `QuestionTime` (10 s) · `LovingTimeout` (60 s) · `QuestionIdx` · `PanelRef`.
- Cumple la "ruptura del patrón" §2.4: sin sensor, sin instrucciones largas.

## 🆕 Recognizing v3 (2026-08-13, pedido de Beltrán): LA MECÁNICA REAL DE HEART, con el sensor persistente ya en mano
Reemplaza al gate ciego de v2 ("no sucedió nada"). Trae la cadena PROBADA de `Stages/Heart/` con el patrón de Breath/Entering:
- **`BP_HeartSensor` ganó `ForceAttachToHand(bRight)`** (copiado de `BP_BreathSensor_V2`) y **`BP_HeartInstructions` ganó `SpawnSensorInHand`**: la página 0 spawnea el sensor de latido y lo engancha a la mano hábil (GameInstance) — **no hay que tomarlo**; la página de "toma el sensor" (su `SpawnSensor` del case 1) se eliminó. El detector corre **INVISIBLE** (el `CheckHeart` de la etapa lo esconde por poll) — el objeto visible es el sensor persistente del Hall.
- **Flujo**: widget 5 páginas (tag `WidgetSpawn` de la sala) → calibración (quietud) → **zona segura head-relative** (esfera debug verde/rojo activa, `bDebugSafeZone`) → en zona: háptico + late a BPM del OSC (test fijo 75.5, sin dispositivo) → `CheckHeart` (0.25 s) hace `DriveDescent(bWasInZone)`: **las columnas descienden+pulsan SOLO en zona** → a `MaxBeatCount` (4 test / 15 real) → `bStageComplete|bFinishing` → `RecogDone` → `StageDone` (el poll le gana a los 2 s del cierre-de-nivel viejo del sensor, y el cleanup lo destruye antes).
- **Anchors por sublevel** (regla reforzada): los tags `SensorSpawn`/`WidgetSpawn`/`BoxSpawn` ya NO viven en el persistente — cada sala tiene los suyos DENTRO de su mapa (Hall: SensorSpawn del sensor de mano; Entering: Widget/Box/Sensor de Breath; Recognizing: Widget[=TP_HeartInstr]/Sensor/Box de Heart). Así la búsqueda por tag es per-sala por visibilidad.
- ⚠ `BP_HeartInstructions.InitRefs` llama `GotoPage` con etiqueta de clase cruzada en el read (colisión de nombres documentada) — compila y corre; verificado por log (`INIT OK`/`IMC ACTIVE`).
- **MaxBreathCount de `BP_BreathSensor_V2` bajado a 1** (CDO) para test rápido — subir al valor real después.

## BP_Stage_Recognizing (índice 2) — v2 con UMBRAL DE QUIETUD (SUPERSEDIDA por v3; queda como historia)
- **v2 (2026-08-13 visor)**: panel de instrucciones (`TextRenderActor` en anchor `HeartInstrSpawn`, texto `HeartText`: "Place your sensor on your heart. Be still...") + **gate por quietud**: poll `CheckStill` (0.25 s) → `CheckOneSensor` sobre los 2 `BP_Sensor` persistentes: dentro de la **zona del pecho** (`pawn + (0,0,ChestHeight 145)`, radio `ZoneRadius` 28) **y quieto** (`StillThreshold` 3 cm/poll) → `ApplyStill`/`StillActive`: las columnas de `BP_Descent` **descienden y pulsan a 60 bpm** (`SetRun(true)` + `PulseStep` en su Tick) y se acumula `InZoneTime`; **fuera del umbral no pasa NADA** (`StillInactive` → `SetRun(false)`). El panel se destruye al primer logro del umbral. Cierre: `InZoneTime ≥ RecogSeconds` (25 s acumulados) → `RecogDone` → `StageDone`. Cortafuegos `RecogTimeout` 120 s.
- `BP_Descent` ahora nace **detenido** (`bDescending` false en CDO) con API `SetRun(bOn)` y pulso de escala (±4%, 1 Hz) vía `PulseStep`.
- **Falta**: el latido real por OSC (el pulso hoy es placeholder a 60 bpm) y el look de la zona segura.

## 🆕 Attracting v2 (feedback visor 2026-08-13): instrucciones + mesa visible + beam visible + cierre real
- **Panel de instrucciones** al entrar (anchor `AttractInstrSpawn`, texto `AttractText` en inglés), se retira a los `InstrTime` (18 s) o al cleanup.
- 🔴 **Corrección de Beltrán (mismo día): NADA de meshes ni actores colocados — TODO por TargetPoints, como el nivel de prueba.** Se eliminaron del mapa la mesa-mesh, los 5 marcadores Y los `BP_SeqSlot` colocados. Lo que hay: **5 anchors `SlotSpawn0..4`** (fila 4855, Y −60..60, Z 75) — **la etapa spawnea los `BP_SeqSlot` ahí** (`SpawnSlots` → `SpawnOneSlot(Tag, Idx)` con el `StepIndex` por punto, ANTES de spawnear el AttractDirector para que su `CacheSlots` los encuentre) — y **20 anchors `BubbleSpawn`** (arco ±95°, radio 150-210, alturas 105-185, la distribución probada de `L_Touch`). Cleanup: 5 `KillOneSlot` encadenados. La mesa visual sigue siendo `BP_SeqTable` (pendiente, como siempre fue).
- **Beam visible**: `BP_AimBeam` ganó `DrawBeamLine()` (llamada al inicio de su Tick): `DrawDebugLine` celeste `BeamStart→BeamEnd` cuando `bEquipped`. ⚠ Debug line = visible en PIE/Development, NO en Shipping — el visual real sigue pendiente (`BP_HandPointer`/material).
- **Cierre REAL**: `BindMelody` (timer a 1 s desde `AttractIntro`) bindea el dispatcher **`OnConfirmed` de `BP_SaveButton`** con su nodo Assign → al confirmarse FINISH MELODY → `StageDone`. Primera vez que el cierre R6 existe.
- **También** (turno del negro): `GoBlack` del director ya NO funde a negro — con la sala siguiente pre-mostrada y en su lugar, el fundido era redundante y se sentía como "recarga" al llegar al centro. El swap ocurre a espaldas del usuario.

## BP_Stage_Attracting (índice 4) — la mecánica de Touch integrada
- **El ecosistema vive EN `L_Room_Attracting`** (se carga/descarga con la sala): 5 `BP_SeqSlot` (fila X=4855, Y −60..60, Z 75, `StepIndex` 0-4 verificado por instancia) · `BP_SaveButton` (4855,0,55) · 2 `BP_TouchSensor` (4860,±25,110, `bIsRight` por instancia) · 2 `BP_AimBeam` (4800,±30,100) · **8 anchors `BubbleSpawn`** en arco ±80°, radio 170, alturas 115-175 · anchor `AttractSpawn` (4800,0,50).
- La subclase spawnea **`BP_AttractDirector`** en `AttractSpawn` (registra IMC_Touch, cachea slots, spawnea burbujas en los 8 puntos, corre el beat).
- **Cierre**: cortafuegos extendido (`AttractTimeout` 240 s) — el FINISH MELODY → `StageDone` es el TODO R6 pendiente. `CleanupAttract`: cadena de 12 `KillOneBubble` **síncronos** (un loop por timer moriría con el actor destruido) + destroy del AttractDirector.
- ⚠ El `AddMappingContext(IMC_Touch)` del AttractDirector no se remueve al cerrar (anotado, inofensivo por ahora).

## BP_Stage_Surrounding (índice 5) — el dibujo 3D
- Spawnea **`BP_BrushTool`** en el anchor `BrushSpawn` de `L_Room_Surrounding` (6060,0,110); el pincel se auto-adjunta por proximidad y **spawnea su propio `BP_DrawCanvas` en identidad** (requisito de coordenadas del ProceduralMesh).
- **Cierre**: cortafuegos extendido (`SurroundTimeout` 240 s — dibujar necesita visor). `CleanupSurr`: `KillIfValid(BrushRef)` + `KillIfValid(GetActorOfClass BP_DrawCanvas)`.

## 🆕 2026-08-13 (noche 4) — LOS SENSORES PERSISTENTES SON LA HERRAMIENTA (confirmado por Beltrán)
*"Los sensores existen desde el inicio. Simplemente cambiará su acción: en breath cumplen la función de breath, en heart heart, en attracting activan el beam, en dibujo dibujan."*
- El director llama **`ConfigureSensors`** en cada `EnterRoom` (después de `MoveAlma`): `SetMode(StageIndex)` + visibilidad desde `SensorShow` (todo true por defecto) sobre los 2 `BP_Sensor`.
- **Entering**: el `BP_BreathSensor_V2` sigue siendo el motor de detección pero corre **INVISIBLE** (`CheckBreathDone` lo esconde en cada poll) — el objeto visible en la mano es el sensor persistente.
- **Attracting**: los 2 `BP_TouchSensor` **se eliminaron de `L_Room_Attracting`**; la etapa llama **`EquipBeams`** (Equip sobre los 2 `BP_AimBeam` del mapa) tras spawnear el AttractDirector, y `bGrabEnabled` pasó a **true en el CDO** del beam (el gate del panel de instrucciones de Touch no corre en la obra). ⚠ Esto afecta también al nivel de test `L_Touch`.
- **Surrounding**: el pincel sigue siendo un grabable aparte (el refactor sensor-como-pincel queda para cuando la mecánica esté en visor).
- Verificado por log: `SENSOR: modo de etapa aplicado 1..5` en ambos sensores por sala + `beams activados desde la etapa`.

## Trampas del DSL pagadas en esta tanda
1. `add_event("Destroyed")` crea un **CustomEvent inútil** — el evento real va por `create_node("AddEvent|EventDestroyed")`.
2. El pin exec de salida de un nodo de EVENTO es **index 1** (el 0 es el delegate).
3. `elif` se ANIDA dentro del cuerpo del if/elif anterior, como última forma — no son hermanos.
4. Statements después de un `(if)` caen dentro de la última rama — cablear fan-in por cirugía si deben correr en ambas.
5. Un `(Utilities|IsValid ...)` que no sea la última forma hace el resto "unreachable" para el parser — ponerlo al final o extraer a función (`KillIfValid`).
