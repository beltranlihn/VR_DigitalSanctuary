# Las 4 subclases nuevas de etapa (Core/Stages/, 2026-08-13 noche) — tracker compartido

> Hermanas de [[BP_Stage_Entering]] y [[BP_Stage_Hall]]. Todas siguen el MISMO patrón: hija de [[BP_StageBase]], override de `RunStage` vía `add_event` (evento `EventRunStage` → función `<X>RunBody`), `EventDestroyed` → `Cleanup<X>` (cortafuegos con limpieza total), y `ExtendTimeout(DirectorRef, <X>Timeout)` como primera línea del body. El director las spawnea por índice en `SpawnEnteringOrBase` (cadena de `elif` anidados — así se anida el elif en el DSL). Verificadas por log en corrida completa 16:20-16:23, cero `Accessed None`, cero residuos.

## BP_Stage_Loving (índice 3) — contemplativa, 3 preguntas
- **Mecánica**: spawnea un `TextRenderActor` en el anchor `QuestionSpawn` de `L_Room_Loving` (M_TextUnlit, WorldSize 10, centrado), muestra `Questions[i]` y avanza por timer. Al agotar las preguntas → `CleanupLoving` + `StageDone()` (cierre por camino real, ÚNICA de las 4 que cierra sola).
- **Variables**: `Questions` (array de Text, CDO: 3 preguntas en inglés) · `QuestionTime` (10 s) · `LovingTimeout` (60 s) · `QuestionIdx` · `PanelRef`.
- Cumple la "ruptura del patrón" §2.4: sin sensor, sin instrucciones largas.

## BP_Stage_Recognizing (índice 2) — la ilusión de ascenso
- **Mecánica placeholder**: spawnea **`BP_Descent`** (Core/Rooms/: 4 columnas-cilindro r12×h500 a radio 300, `MI_Ghost`, sin colisión) en el anchor `DescentSpawn`; su Tick baja el actor a `DescendSpeed` (30 cm/s) mientras `bDescending` — **el pawn NO se mueve, el entorno desciende**. Timer `RecogDone` a `RecogSeconds` (25 s) → cleanup + `StageDone`.
- ⚠ El timer de cierre está cableado con **fan-in** desde ambas ramas del if (la primera escritura lo dejó solo en el else — trampa del DSL: statements después de un if caen en la última rama).
- **Falta**: la mecánica de latido real (mando al pecho, OSC) — esto es el esqueleto de la ilusión.

## BP_Stage_Attracting (índice 4) — la mecánica de Touch integrada
- **El ecosistema vive EN `L_Room_Attracting`** (se carga/descarga con la sala): 5 `BP_SeqSlot` (fila X=4855, Y −60..60, Z 75, `StepIndex` 0-4 verificado por instancia) · `BP_SaveButton` (4855,0,55) · 2 `BP_TouchSensor` (4860,±25,110, `bIsRight` por instancia) · 2 `BP_AimBeam` (4800,±30,100) · **8 anchors `BubbleSpawn`** en arco ±80°, radio 170, alturas 115-175 · anchor `AttractSpawn` (4800,0,50).
- La subclase spawnea **`BP_AttractDirector`** en `AttractSpawn` (registra IMC_Touch, cachea slots, spawnea burbujas en los 8 puntos, corre el beat).
- **Cierre**: cortafuegos extendido (`AttractTimeout` 240 s) — el FINISH MELODY → `StageDone` es el TODO R6 pendiente. `CleanupAttract`: cadena de 12 `KillOneBubble` **síncronos** (un loop por timer moriría con el actor destruido) + destroy del AttractDirector.
- ⚠ El `AddMappingContext(IMC_Touch)` del AttractDirector no se remueve al cerrar (anotado, inofensivo por ahora).

## BP_Stage_Surrounding (índice 5) — el dibujo 3D
- Spawnea **`BP_BrushTool`** en el anchor `BrushSpawn` de `L_Room_Surrounding` (6060,0,110); el pincel se auto-adjunta por proximidad y **spawnea su propio `BP_DrawCanvas` en identidad** (requisito de coordenadas del ProceduralMesh).
- **Cierre**: cortafuegos extendido (`SurroundTimeout` 240 s — dibujar necesita visor). `CleanupSurr`: `KillIfValid(BrushRef)` + `KillIfValid(GetActorOfClass BP_DrawCanvas)`.

## Trampas del DSL pagadas en esta tanda
1. `add_event("Destroyed")` crea un **CustomEvent inútil** — el evento real va por `create_node("AddEvent|EventDestroyed")`.
2. El pin exec de salida de un nodo de EVENTO es **index 1** (el 0 es el delegate).
3. `elif` se ANIDA dentro del cuerpo del if/elif anterior, como última forma — no son hermanos.
4. Statements después de un `(if)` caen dentro de la última rama — cablear fan-in por cirugía si deben correr en ambas.
5. Un `(Utilities|IsValid ...)` que no sea la última forma hace el resto "unreachable" para el parser — ponerlo al final o extraer a función (`KillIfValid`).
