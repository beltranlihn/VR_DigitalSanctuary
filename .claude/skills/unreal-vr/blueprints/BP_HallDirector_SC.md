# BP_HallDirector_SC — el director del Inicio, el Hall y el Regreso (Hall/)

> `/Game/SoulCharger/Hall/Blueprints/BP_HallDirector_SC` · sesión "Inicio y Hall de acceso" · creado 2026-09-30 (noche, plan de Narrativa `docs/PLAN-NOCHE-2026-09-30.md`).
> Una instancia en `Test_Hall` (`HallDirector`), en el **centro del hall** (origen de `SM_HallShell_SC`): todo lo que mueve es relativo a ese punto, así el mismo actor sirve en la celda 0 de `L_SoulCharger_Obra`.

## Estado
🟢 **Construido y probado en PIE (T1 ~08:40 + T2 ~09:50, 2026-09-30)**: `HallIntro` 0→30 → `bHallDone` (timbre, sensor y **elección del alma** resueltos por sus cortafuegos; `ChosenSoul` 0 = centro; el alma se va al nacer el HUD; niebla sube y baja) · `HallReturn` 0→6 → `bReturnDone` (`LeadActor` termina 1,8 m frente a `StopCard`) · `HallExit` 0→3 → `bExitDone` (`LeadActor` delante de `StopExit`, niebla encendida). 0 Accessed None. ⬜ Visor. ⬜ Hints VO_01h/03h y el sensor que viaja 0,2 s a la mano (cirugía chica en `HallTickTouch`/`HallGrab`).
Fuentes (reconstruibles): `VR_Test/Saved/ClaudeScripts/Hall/` → `hall_director_plan.json` (78 variables, 12 componentes, 28 funciones), `hall_director.dsl` (+ `dsl/<grafo>.dsl`), `hall_apply_A/B/C.py`, `hall_level.py`, `hall_tile_material.py`, `hall_grooves.py`, `TURNO_T1.md`.

### Lo que se corrigió en el turno
- `HallApplyTile`: `SetScalarParameterValue` sobre la MID resolvía al overload de MPC → **`SetScalarParameterValuebyInfo` + `MakeMaterialParameterInfo`** (gotchas §524).
- `HallTickSteps`: la espera de caminata era por FLANCO (la abría `HallTickWalk` al llegar) y se perdía si la caminata terminaba antes de que el paso la pidiera (PIE 1: trabado en el paso 5). Ahora se resuelve **por estado cada cuadro**: `Gate ← Gate or (WaitWalk and WalkT ≥ WalkDur)` (gotchas §527). Se reescribió el grafo borrando sus nodos (salvo la entrada) y escribiendo en vacío: sin cambio estructural.
- `TestSpeed` rinde ~2× y no 4× por el clamp `Dt ≤ 1/30` (gotchas §528).

## API (la llama el director de la Obra, `BP_Obra_SC`)
| Llamada | Qué hace | Termina con |
|---|---|---|
| `HallIntro()` | Desde el vacío hasta cruzar la puerta Este, con el HUD nacido (guion V5 §1.4-2.9) | `bHallDone = true` |
| `HallReturn()` | Teleport a 4 m de la puerta Este, la puerta se ilumina y se abre sola (sin timbre), caminar hasta adentro; **baldosas abajo y apagadas** (pedido de Beltrán 2026-10-01: en los resultados no van elevadas ni iluminadas → `HallTiles 5 0.0` en el paso 1 de `HallEnterReturn`) | `bReturnDone = true` |
| `HallExit()` | Se abre la puerta Oeste y se sale al espacio etéreo; el hall se apaga detrás; niebla azul | `bExitDone = true` |
| `bHudBorn` (bool) | Se pone true en el paso 24 de HallIntro: **el momento en que nace el HUD**. El Hall NO toca el HUD; la Obra lo conecta a `BP_SoulHUD3D_SC` | — |
| `StopExit` (componente) | Dónde queda el pawn al terminar HallExit (créditos/constelación de la Obra): `GetStopExit` → `GetWorldLocation/Rotation` | — |
| `ChosenSoul` (int) | Índice del alma elegida (-1 = ninguna) | — |
| `DoorW` / `DoorE` (float 0..1) | 🔴 **Los LEE la Obra** (no renombrar): ambiente del Hall (AMB_03) desde `DoorW > 0,3` en el inicio, silencio con `DoorE > 0,05` en la salida; rama SHARE espera `DoorW ≥ 0,99` tras llamar `HallDoor(East = false, Open = 1)` | — |
| `bRightHanded` (bool) | La mano que tomó el sensor | — |
| `LeadActor` (Actor) | Lo que va delante en el regreso/salida (el anillo con el alma) — T2 | — |
Cada una se prueba sola en `Test_Hall` con `bTestIntro` / `bTestReturn` / `bTestExit` (+ `TestDelay`, `TestSpeed` = dilatación global del tiempo; **dejar en false / 1 al guardar**).

## Paradas (ArrowComponent, se arrastran en el viewport; el pawn mira hacia la flecha)
`StopStart` (−3600, 0) · `StopDoor` (−980, 0) · `StopInside` (−300, 0) · `StopFar` (1300, 0) · `StopReturn` (1130, 0, yaw 180) · `StopCard` (300, 0, yaw 180) · `StopExit` (−1500, 0, yaw 180). Z = el piso del PlayerStart. Entrada = puerta **Oeste** (−X), salida = **Este** (+X).
Caminata con **perfil trapecio** (acelera `AccelTime`, frena `BrakeTime` con desaceleración constante: la frenada física que pidió Beltrán, nunca exponencial) + loop `Pasos`.

## Secuencia de HallIntro (pasos de `HallEnterIntro`, avanza cuando `StepTime ≥ StepDur` Y `bGate`)
0 teleport a StopStart, puertas cerradas, baldosas abajo, hall apagado, Alma oculta, niebla · 1 caminata 26 s + niebla a negro · 2-4 VO_01a/b/c · 5 se enciende el hall (portal), espera llegar · 6 **timbre** alcanzable (48 cm al frente, 28 cm bajo los ojos, cara a los ojos) + VO_01d; sostener `BellHold` s (soltar = baja), cortafuegos `FW_Bell` · 7 campana + el timbre se va · 8 abre la puerta Oeste · 9 caminata 7 s · 10 Alma aparece en el centro · 11 cierra la puerta + VO_02 · 12 Alma al costado + **sensor** alcanzable + VO_03; tocarlo = queda en esa mano (`bRightHanded`), cortafuegos `FW_Tool` → derecha · 14 VO_04 + elección (T2) · 15 VO_05 · 16-22 VO_06a..g con las **baldosas** subiendo de a una (Lift 3 cm + TileGlow en su color + nombre de etapa encima) · 23 bajan juntas · 24 nace el HUD (`HudBirth`) · 25 VO_07 · 26 Alma a la puerta Este, vidrio frío · 27 Alma desaparece, abre la puerta Este · 28 caminata 13 s · 29 se apaga el hall detrás · 30 cierra, **`bHallDone`**.

## Baldosas: Lift + TileGlow por MID de slot
`M_Hall_Tile_SC` gana `Lift` (WPO en Z, cm) y `TileGlow` (emisivo extra = `TileColor.RGB × TileGlow`, sumado después de lo que ya iba al emisivo). Default 0 = igual que antes; los MI de Beltrán no se tocan. El director crea una MID por slot (0 Entering · 1 Recognizing · 2 Loving · 3 Attracting · 4 Surrounding; azimut local 180/108/36/324/252°, r 175 cm, datos de Mesh 3D) y anima `TileCur → TileTgt` en `TileTime` con ease in-out. Los nombres de etapa son 5 planos (`Title0..4`) con `MI_TourTitle_<ETAPA>` (`Reveal`).

## Referencias que cachea `HallBoot` (por clase o tag → sirve en la Obra)
Pawn (`BP_VRPawn_SC`) · Alma (`BP_Alma_SC`, una sola: en Test_Hall hay una **TestOnly**) · Lights (`BP_HallLights_SC`) · Picker · hojas de puerta = tag **`hall_leaf`** (Movable; signo de apertura = sign(x·y) del centro de sus bounds) · baldosas = tag **`hall_tiles`** · TargetPoints de Alma: `hall_alma_center` / `hall_alma_side` / `hall_alma_exit`.

## Grafos (orden del pipeline)
- **BeginPlay** → `HallBoot` (cachea; NO anima) → solo si hay flag de test: `Delay(TestDelay)` → `SetGlobalTimeDilation(TestSpeed)` → la API.
- **Tick** → `Dt = min(DeltaSeconds, 1/30)` (regla de la obra) → `HallTickWalk` → `HallTickDoors` → `HallTickTiles` → `HallTickTouch` (→ `HallTickPick`) → `HallTickLead` → `HallTickSteps`.
- **`HallTickSteps`**: `StepTime += Dt`; espera de caminata por estado; si `StepTime ≥ StepDur` y `bGate` → `Step++`, log `HALL: modo M paso N` → `HallEnterIntro/Return/Exit` (un `switch` por paso: cada caso fija `StepDur`/`bGate`/`bWaitWalk`).
- **`HallSay(I)`**: `StepDur = duración del clip + VOAir`; suena con `SpawnSoundAtLocation` en Alma (2D si no hay Alma).
- **Timbre** (`HallSpawnBell` + rama de `HallTickTouch`): `BP_BellArt_SC` spawneado alcanzable, `Appear.Prepare` + `Appear`; carga `BellHold` s con la mano a < `TouchRadius` (soltar = −2/s), `Slider.Progress` y `Base.Glow` 0,7 → 1,6, háptico que sube con la carga; `FW_Bell`.
- **Sensor** (`HallSpawnSensor` + `HallGrab`): `BP_BioSensorArt_SC` alcanzable; tocarlo = `AttachActorToComponent` al grip de esa mano (Snap), `bRightHanded`, `HallPulse`; `FW_Tool` → derecha. Se destruye al final de HallIntro (las etapas muestran su propio sensor).
- **Puertas** (`HallDoor` + `HallTickDoors`): `DoorW/E` → objetivo en `DoorTime` (lineal) con ease in-out al aplicar; yaw = base + signo × `DoorOpenDeg` × ease.

## Registro de variables (categoría Default; todo lo editable es perilla de autor)
- **API**: `bHallDone`, `bReturnDone`, `bExitDone`, `bHudBorn`, `ChosenSoul`, `bRightHanded`, `LeadActor`.
- **Prueba**: `bTestIntro/Return/Exit`, `TestDelay` (2), `TestSpeed` (1).
- **Tiempos**: `JourneyTime` 26 · `EnterTime` 7 · `OutTime` 13 · `ReturnTime` 9 · `ExitTime` 14 · `AccelTime` 2,5 · `BrakeTime` 3 · `VOAir` 0,8.
- **Puertas/baldosas**: `DoorOpenDeg` 16,5 · `DoorTime` 3 · `TileLiftCm` 3 · `TileGlowMax` 0,35 · `ReturnGlow` 0,6 · `TileTime` 1,5 · `DoorWarm` (1; 0,72; 0,40) = el `DoorColor` de `MPC_Hall_SC` · `DoorCold` (0,03; 0,05; 0,10).
- **Alcance/cortafuegos**: `ReachFwd` 48 · `ReachDown` 28 · `TouchRadius` 14 · `BellHold` 3 · `FW_Bell` 25 · `FW_Tool` 20 · `FW_Choose` 25.
- **Sonido**: `VO` (21 clips, índice en el `.dsl`) · `SndDoor` (DoorOpen) · `SndBell` (Bell) · `SndSteps` (Pasos, loop).
- **Estado interno**: `Mode`, `Step`, `StepTime`, `StepDur`, `bGate`, `bWaitWalk`, `WalkA/B/T/Dur`, `DoorW/E/WT/ET`, `TileCur/Tgt`, `TileGain`, `bTitles`, `BellCharge`, `bBellLive`, `bSensorLive`, `bPickLive`, `ReachLoc`, `EyeLoc`, refs (`Pawn`, `Alma`, `Lights`, `Bell`, `Sensor`, `Picker`, `Fog`, `StepsAudio`, `Leaves`, `LeafYaw/Sign/East`, `TileMIDs`, `TitleComps`, `Souls`).

## En Test_Hall (2026-09-30)
Instancia `HallDirector` (`BP_HallDirector_SC_C_0`) en (0,0,0) · `TP_hall_alma_center` (0,0,180) · `TP_hall_alma_side` (−180,−120,170) · `TP_hall_alma_exit` (560,0,200) · `Alma_HallTest` (TestOnly) · hojas `StaticMeshActor_2..5` con tag `hall_leaf` y **Mobility Static → Movable** · baldosas `StaticMeshActor_7` con tag `hall_tiles`. PlayerStart en z 76,97 → las flechas están a esa z.

## T2 (hecho) — alma, niebla, LeadActor
- **Elección del alma**: `HallSoul_0..4` en Test_Hall (BP_ProtoSoul_SC, tags `soul_pick` + **`soul_idx_N`**, colores de Beltrán copiados de `L_SoulCharger_V3`, `Size` 0,15 para que sean alcanzables) + `HallSoulPicker` (`bAwakeOnStart` false, `ChosenTag` `hall_soul_present`) + `TP_hall_soul_present` (−230, 0, 167). `HallPickStart` arma `Souls` POR TAG `soul_idx_0..4` (orden determinista: 0 = centro, 1 izq, 2 der, 3 más izq, 4 más der), las coloca en arco con `HallReach` (19 cm entre sí; el arco se aleja 3 cm por paso) mientras están dormidas y llama `Picker.Awake`. `HallTickPick`: `Picker.bChosen` → `ChosenSoul = FindItem(Souls, Picker.Winner)`; pasado `FW_Choose` → `Picker.ForceChoose` (elige `Souls[0]` del picker = el centro, porque se colocó primero; verificado en PIE).
  - Mapa índice → V3: 0 ← SoulPick_3 · 1 ← SoulPick_2 · 2 ← SoulPick_4 · 3 ← SoulPick_1 · 4 ← SoulPick_0 (`Saved/ClaudeScripts/Hall/souls_v3_min.json`).
  - Para la Obra: `director.Souls[ChosenSoul]` es el actor elegido (vivo, oculto tras `HallHudBirth`): de ahí se leen `CoreColor/EdgeColor/GradColorA/GradColorB/Mesh`.
- **`HallHudBirth`** (reescrito en vacío): además de `bHudBorn`, el alma elegida hace `Disappear` mientras nace el HUD (el HUD usa su propia alma, pedido de Narrativa).
- **Niebla**: `HallFogSet(Lit)` → `BP_HallFog_SC.FogOn/FogOff` (ver abajo).
- **`HallTickLead`** (contrato con la Obra): en Mode 2 (pasos 0-2 lo COLOCA delante del pawn; desde el 3 `VInterpTo` 1,5) y Mode 3 (desde el paso 1): 2,5 m delante del pawn rumbo a `StopCard + fwd·180` / `StopExit + fwd·220`, z = pawn + 110. Solo posición; se suelta con Mode 0.

## BP_HallFog_SC + M_HallFog_SC (Mechanics/Hall)
Esfera del motor ×12 (r 6 m) pegada a la cámara en el Tick; `M_HallFog_SC` = duplicado de `M_TourVeil_SC` con **`bDisableDepthTest` false** (las manos y lo que está a < 6 m se dibujan; el hall queda tapado); `TranslucencySortPriority` −10; colisión apagada en BeginPlay (la plantilla no acepta `CollisionEnabled` por `set_properties`). Variables: `Amount`/`Target` (0..1, con ease in-out al aplicar), `FadeIn` 2 · `FadeOut` 6 · `CTopFog` (0,004; 0,006; 0,018) · `CHorFog` (0,012; 0,018; 0,045) — **azul noche casi negro**, pedido de Beltrán · `bStartOn` false (nace apagada para no tapar las pruebas de otros en Test_Hall). API: `FogOn()` / `FogOff()`. Instancia `HallFog` en Test_Hall.

## 2026-09-30 (mañana): título, salida blanco azulada, almas desaturadas
- **`HallTickDoors`** (reescrito en vacío): además de las puertas, en Mode 1 escribe `MPC_Hall_SC.DoorColor = Lerp(DoorWarm, DoorCold, ease(a))` con `a` = 0 antes del paso 25, `StepTime/3` en el 25 y 1 después (el vidrio de la salida pasa a blanco azulado en 3 s cuando Alma dice "Follow me"). **`DoorCold` (0,03; 0,05; 0,10) → (0,55; 0,64; 0,82)** en el CDO y en la instancia (el color con que abre el velo de Entering, pedido de Narrativa/Beltrán). El `SetVectorParameterValue` del paso 26 quedó redundante (escribe el mismo valor final).
- **`BP_HallTitle_SC`** (título SOUL CHARGER / CENTER) y **`BP_HallGlow_SC`** (el afuera blanco azulado por la puerta de salida): BPs nuevos que LEEN `Mode`/`Step`/`bHallDone`/`bReturnDone`/`bExitDone` del director; el director no los conoce. Ver `_INDEX.md`.
- **Almas del Hall:** colores desaturados (S × 0,55 en HSV, mismo tono y valor; el Core de la verde girado a 150°) y anillos viejos apagados. Tabla en `Saved/ClaudeScripts/Hall/souls_desat.json` (índice → Core/Edge/GradA/GradB).

## 2026-09-30 (tarde): inicio corregido tras el visor (pedido de Beltrán vía Narrativa) — probado en PIE de la Obra
- **`HallEnterIntro`, `HallWalk` y `HallEnterExit` reescritos EN VACÍO** (`Saved/ClaudeScripts/Hall/dsl/`):
  - paso 0: 12 s quieto con la niebla, que la Obra abre en PT 3,5 → 5,5;
  - paso 1: `HallWalk` sin pasos (`HallWalk` no lanza `SndSteps` en Mode 1 paso 1) + `HallFogSet(false)`;
  - paso 4: `HallLight(true)` + pasos (`SpawnSound2D SndSteps 0.6`);
  - paso 5: espera la llegada;
  - `HallEnterExit` paso 0 no reabre ni hace sonar la Oeste si ya está abierta (`DoorWT` ≥ 0,5, rama SHARE).
- **Tiempos medidos (Obra, PIE)**, desde `HallIntro`:
  - paso 1 en 13,7 (las HighResShot de `bPhotos` meten ~1,7 s; sin fotos, 12);
  - Hall visible en 25,7;
  - paso 4 en 36,8;
  - llegada ~39,7;
  - campana 46,4.
- **La arquitectura se oculta/muestra desde `BP_HallAmbience_SC`** (tag `hall_arch`), sin tocar el director.
- En Test_Hall:
  - `BP_HallLights_SC_C_0.AutoOnDelay` 2 → **−1** (se prendía sola a los 2 s: por eso el Hall se veía en el viaje);
  - `BP_HallFog_SC.FadeOut` 6 → **12** (CDO + instancia).
- `MPC_Hall_SC` + `GrooveFront` (2000, id 9E4ABC17-…) + `DustLight` (0, id F65416BF-…): hoy no los lee ningún material.

## T4 (2026-09-30, noche) — agilidad, ensayo, ritmo en el panel, timbre que se hunde, puerta por el LeadActor
- **Tanda estructural única** (gotcha 402, con respaldo en `Saved/ClaudeScripts/Hall/director_overrides.json`): 25 variables; la instancia sobrevivió (canario 48).
  - Prueba: `TestFromStep` (int; CDO −1, instancia de Test_Hall **6** = el timbre; getter del DSL = **`GetTestfromStep`**, con "from" en minúscula).
  - Ritmo:
    - `IntroHold` 12;
    - `PaceWalkToVO` 3 · `PaceJourneyPause` 1,5 · `PaceArrive` 0,5 · `PaceBellVO` 0,5 · `PaceBellRing` 0,8;
    - `PaceDoorOpen` 1,5 (intro 8 y 27, exit 0) · `PaceAlmaAppear` 2,5 · `PaceAfterTool` 0,5 · `PaceTilesOff` 1,5 · `PaceHudBirth` 3;
    - `PaceFollowMe` 2 · `PaceLightsOffOut` 5 · `PaceReturnDark` 2 · `PaceReturnLight` 1,5 · `PaceReturnDoor` 1 · `PaceReturnVO` 1;
    - `PaceDoorClose` 1 · `PaceExitLightsOff` 6 · `DoorLeadDist` 620.
  - Timbre: `BellPressDepth` 1 cm · `BellPressTime` 0,12 s.
  - Internas: `BellPress`, `BellRest` (Vector).
  - Categorías: pendientes (el DSL escribe en Default).
- **Agilidad** (regla: solo la VO dura lo que su audio):
  - `VOAir` 0,8→0,5 · `OutTime` 13→11 · `ReturnTime` 9→8 · `ExitTime` 14→12 (CDO + instancia; la CDO NO propaga a la instancia, hay que setear las dos).
  - La campana llega a t ≈ 38,5 (antes 43,5).
- **Ensayo**: con `bTestIntro` + `TestFromStep` > 1, el paso 0:
  - reinicia puertas y baldosas y enciende el Hall;
  - pone el pawn en el TargetPoint con tag **`hall_pawn`** (`TP_hall_pawn`, (−980, 0, 76,97), movible a mano) o, si no existe, en StopDoor (< 10) / StopInside;
  - salta a ese paso al cuadro siguiente.
  `BP_HallAmbience_SC` "encaja" la onda y las motas también en ese paso.
- **Timbre**:
  - `HallSpawnBell` guarda `BellRest` = posición relativa del `Button` (`Class|SceneComponent|GetRelativeLocation`; `Transformation|GetRelativeLocation` NO existe).
  - `HallTickTouch` hunde el `Button` `BellPressDepth` con ease mientras la mano está cerca (el apretar real; el cortafuegos no lo hunde) y lo devuelve al soltar. Solo escribe si está apretado o volviendo, así no pelea con la aparición.
- **HallExit + LeadActor (el pez)**: el paso 0 ya no abre la Oeste si hay `LeadActor`. La abre `HallTickLead` cuando el pez queda a < `DoorLeadDist` de `StopDoor`. Sin pez, abre en el paso 0 como antes. Nunca reabre si `DoorWT` ≥ 0,5.
- **Ameba elegida**: `TP_hall_soul_present` (−230, 0, 167) escala **1** → **(0, 0, 160) escala 0,3**. La escala 1 del TargetPoint era la causa de "muy grande y cerca": el alma copia la escala X de su punto como `Size`.

## Mini-turno (2026-09-30, noche): cortafuegos de la elección → la del centro · HallExit sin VO_35a
- **Causa del "alma elegida 4"**: `picker.ForceChoose` elige `Souls[0]` del PICKER, que junta las almas por tag en orden de nivel. La primera colocada es el índice 4 del director.
- **Arreglo** (`HallTickPick`, reescrito en vacío):
  - en el cortafuegos, `Cast(director.Souls[0]) → BP_ProtoSoul_SC` → `SetHovering(true)` → `picker.Judge(S)`;
  - si el cast falla, `ForceChoose`;
  - print `HALL: alma elegida N` de vuelta.
  - `picker.Souls = director.Souls` NO compila: son `Actor[]` contra `BP_ProtoSoul_SC[]`.
  - Probado en PIE: `alma elegida 0`.
- **HallExit**: sin `HallSay 20` (VO_35a). Con el final nuevo, Alma no vuelve después de los resultados.

## T5 (2026-09-30, noche): la voz se funde si el usuario resuelve antes (auditoría, pedido de Beltrán 09-29)
| Dónde | Antes | Después |
|---|---|---|
| `HallSay` | `SpawnSoundAtLocation` en Alma (sin manija) | **`Alma.SayClip(Clip)`** (sin Alma: 2D). Paso = clip + `VOAir` |
| Paso 6 (timbre + VO_01d) | `StepDur` = `PaceBellVO` 0,5: la VO sonaba encima de la puerta | `StepDur` = VO + aire; el timbre la corta |
| Timbre cargado · mando tomado (`HallGrab`) · alma elegida (`HallTickPick`) | esperaban el resto de la VO | si `StepTime < StepDur`: `StepDur = StepTime + 0,3` + `Alma.FadeVoice(0,3)` + `HALL: voz cortada` |
| Cortafuegos | — | sin cambio: saltan después de la VO |
- PIE (ensayo desde el paso 14, TestSpeed 4):
  - control NEGATIVO (FW_Choose 25): sin "voz cortada";
  - POSITIVO (FW_Choose 5 solo en la prueba): "voz cortada" + "ALMA: la voz se va en fade" en el mismo cuadro, y los pasos siguen.
  - FW_Choose de vuelta en 25.
- `PaceBellVO` quedó sin uso (no se borra: sería estructural). El 0,3 es literal.
- `FadeVoice` no dispara `OnVOFinished`, y el Hall no lo usa (avanza por `StepDur`).

## 2026-10-01 (Narrativa) — marcas de autor + ensayo del Hall
- **`HallSpawnBell`, `HallSpawnSensor` y `HallPickStart`** (reescritos en vacío con Test_Hall CERRADO; respaldo de lo anterior en `Saved/ClaudeScripts/Obra/spawn/hall_live.txt`; fuente nueva `Saved/ClaudeScripts/Obra/hallmarks.json`). Calculan como siempre con `HallReach` y, si hay una marca `BP_AuthorMark_SC` con su tag, la usan:
  - timbre: `mark_hall_bell`;
  - sensor: `mark_hall_sensor` (posición + giro + escala);
  - almas: `mark_hall_soul_0..4` (solo posición).
  La altura se corrige: `z + (EyeLoc.z − (pawn.z + 120))`. Log `HALL: timbre/sensor en su marca`. Ver [[BP_AuthorMark_SC]].
- **Construction script** (antes vacío): `Title0..4` con `Reveal` 1 → los nombres de etapa sobre las baldosas se ven en el editor; `HallBoot` los apaga al dar Play. Lo mismo en `BP_HallTitle_SC` (SOUL CHARGER / CENTER): `Reveal` 1 en el editor, su BeginPlay lo vuelve a 0.
- **El ensayo del Hall en Test_Hall es `BP_HallRunner_SC`** (título, música, HUD, velo, bucle y `DebugStart` 2-9 por pasos). Dejar `bTestIntro` en false en la instancia: si queda en true, el ensayo no llama `HallIntro` para no arrancarlo dos veces.
- El salto `TestFromStep` no deja hecho lo de los pasos saltados (Alma, sensor, almas, HUD) ni mueve al pawn adentro si existe `TP_hall_pawn`: lo completa `BP_HallRunner_SC.HRPrep` desde afuera, con llamadas públicas (`HallAlmaAppear`, `HallSpawnSensor`, `HallGrab`, `SetSouls`, `SetChosenSoul`, `SetHudBorn`, `HallTeleport`).

## T6 (2026-10-01, Narrativa) — timbre y sensor = objetos REALES colocados
- `HallSpawnBell` / `HallSpawnSensor` reescritos (fuente `Saved/ClaudeScripts/Obra/step2.json`; respaldo de la versión con marcas en `spawn/step2_backup.json` y `hallmarks.json`):
  - si hay un actor con tag `hall_bell` / `hall_sensor` (en Test_Hall: `Timbre` = `BP_BellArt_SC`, `Sensor` = `BP_BioSensorArt_SC`, carpeta `Ajustes`, **Actor Hidden In Game**), lo usan tal cual: `SetBell`/`SetSensor`, `HallReach 0 0 0` (para `EyeLoc`), altura `+ (EyeLoc.z − (pawn.z + 120))`, lo muestran. Log `HALL: timbre/sensor colocado en el nivel`.
  - si no hay, spawnean como antes con `HallReach(ReachFwd, ReachDown)`.
  - después, igual que siempre: `BellRest`, `Appear.Prepare` + `Appear`, `BellLive`/`SensorLive`, `Gate`.
- Se destruyen como antes: el timbre con `SetLifeSpan 2` en el paso 7, el sensor con `SetLifeSpan 0,1` en el paso 30. Por eso no reaparecen al volver al Hall.
- ✅ PIE (ensayo de Test_Hall): `DebugStart` 3 → timbre visible en (−932, 0, 48,97) · 5 → sensor visible en (−252, 0, 48,97), girando como siempre · 6 → sensor en la mano. 0 errores.
- Las marcas `BP_AuthorMark_SC` ya no existen en Test_Hall.

## 2026-10-01 (Narrativa) — paso 6: timbre y puertas suenan en su lugar
- `HallEnterIntro` paso 7: `SndBell` → `PlaySoundAtLocation` en el timbre (`GetActorLocation(Bell)`), por cirugía.
- `HallDoor(East, Open)` reescrita: `SndDoor` (0,8) en la puerta. La Oeste está en el punto medio de `StopDoor` y `StopInside`; la Este a 55 % de `StopReturn` hacia `StopCard`. `SndSteps` (tus pasos) sigue en 2D.
- `Bell` y `DoorOpen` llevan `ATT_Objeto_SC`. ✅ PIE (Obra 63): puerta del SHARE, 0 errores.

## 2026-10-01 (Narrativa) — sensor en la mano con la pose buena
- `HallGrab(Right)` reescrita: `AttachActorToComponent(Sensor, grip, Snap, Snap, KeepWorld)` + `SetActorRelativeTransform` con la pose de `BP_UserTool_SC.SensorXfR/L` (derecha (4,325; −1,685; −2,335185) roll 90; izquierda y +1,685, roll −90). Antes la rotación era `KeepWorld` y quedaba la del giro del orbe. ✅ PIE (ensayo 6): relativo al `MotionControllerRightGrip` exacto, 0 errores. ⬜ visor.
- 🔴 Trampa: los setters de bools propios se escriben `Variables|Default|SetRightHanded` (sin la b); el read los muestra como `(|SetbRightHanded ...)`, que NO se puede escribir. Un clear+write con el read como respaldo deja la función vacía.

## 2026-10-01 — `RestDim` en `M_Hall_Tile_SC` (Mesh 3D; el director NO se tocó)
Beltrán: *"las baldosas menos brillantes se brillaron demasiado"* (el reposo y el anillo atenuado). Escalar nuevo **`RestDim`** (default **0,7**) entre `Multiply_0` (la base × `HallLight`) y la entrada A del `Add_0` del emisivo: atenúa SOLO la base; el `TileGlow` de la subida se suma después igual. Los MI por etapa lo heredan. Para volver al brillo de antes: `RestDim` 1.

## 2026-10-01 (mañana, Narrativa) — correcciones de la prueba completa
- `HallWalk`: sin pasos también en el modo 3 (la salida final, pedido de Beltrán).
- Paso 10: `SetStepDur 1.6` → Alma aparece y recién habla (VO_02) 1,6 s después.
- Paso 30: ya no destruye el sensor (`SetLifeSpan` quitado). El sensor sigue en la mano hasta que la herramienta de Entering toma el relevo: la Obra lo oculta en `HandsTick`. También se quitó el `SetLifeSpan` del timbre del paso 7 (el timbre ya se va con `Vanish`).
- `HallTickTouch`: al completarse la carga, `SetVisibility(Slider, false)`: el anillo radial desaparece en el acto.
- Instancia en Test_Hall: `OutTime` 11 → 8, `ExitTime` 12 → 7.
- **Timbre con sonido al tocar (D4):** `HallBellSnd`, llamado al comienzo de `HallTickTouch` mientras `BellLive`. Al entrar la mano (grip, a menos de `TouchRadius` del timbre) hace `SpawnSoundAtLocation(SndBell)` → `BellSnd`; al salir, `AudioComponent.FadeOut(0.5)`; al volver a tocar, parte de nuevo. Variables `BellTouch` y `BellSnd`. El paso 7 ya no dispara `SndBell`.
- **Sensor que gira (D5):** `HallSensorSpin(DT)`, llamado al comienzo de `HallTickTouch`: `AddActorWorldRotation` en yaw a 40°/s mientras `SensorLive`. `HallGrab` fija la pose al tomarlo.

## 2026-10-01 (10:00, Narrativa) — rendimiento de los materiales del Hall (el director NO se tocó)
- Medido en el Quest (APK de la Obra): adentro del Hall había **42 fps** (App 21,8 ms). Quedó en **62,5**.
- `M_Hall_Interior_SC`:
  - `HallGroovesPS` **v7**: la junta de las baldosas solo con `z < 34 && r < 290`; los meridianos con un cos/sin y una rotación fija de 72°.
  - `HallInteriorPS` **v4**: el ruido de valor 3D se lee de **`T_HallNoiseRG_SC`** (nueva entrada `NT` del Custom, conectada a un `TextureObject`).
- `M_Hall_Tile_SC`: `HallTilePS` **v2**, con el mismo ruido por textura.
- Mismo look. El código anterior está en `VR_Test/Saved/ClaudeScripts/Obra/dump/code_*_respaldo.hlsl`.
- Falta ~1 ms para 72: el haz `BP_LightShaft_SC` (`M_LightShaft`, aditivo de dos caras, 176 nodos). Receta completa en `references/materials-vr.md`.