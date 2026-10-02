# BP_SeqRig_SC — el "sensor" PORTABLE de la etapa del secuenciador

**Ruta:** `/Game/SoulCharger/Mechanics/Sequencer/Blueprints/BP_SeqRig_SC`
**Colocado en:** `/Game/SoulCharger/Mechanics/Sequencer/Maps/Test_Sequencer` como `GAL_12_SeqRig`
**Nació:** 2026-09-27 · Plan: [`docs/PLAN-SECUENCIADOR-PORTABLE.md`](../../../../docs/PLAN-SECUENCIADOR-PORTABLE.md)
**Estado:** 🟢 Fase 1 construida y verificada en PIE (instalación, input, mandos y botón en la mano) · ⬜ Fase 2 (esfera/botón/secuenciador todavía leen al sensor) · ⬜ visor

---

## Por qué existe
Pedido de Beltrán: *"un sensor que solo es de esta etapa, que integra el line trace para seleccionar y toda la interacción con las esferas y el secuenciador… que si lo arrastro a cualquier otro proyecto con un VR Pawn reconozca instantáneamente el VR Pawn y funcione"*. `BP_Sensor_Soul` tiene 90 funciones y 5 mecánicas y conoce al pawn y al director por clase. Este rig es solo lo del secuenciador, **copiado del sensor probado en visor** (no reinventado), con dos cambios: encontrar las manos sin el pawn, y traer su propio input.

Modelo: `BP_TBDrawRig` (dibujo de Neural Canvas, validado 2026-09-26). Contrato: **colocar el actor, nada más.**

## Diseño de mano dominante (Beltrán, 2026-09-27)
- `bRightHanded` (default true) + verbo público **`SetHandedness(bRight)`** — Soul Charger lo define en otra etapa y se lo pasa.
- **Solo la mano dominante tiene láser e interactúa** con las esferas.
- **La otra mano lleva el botón Save Melody anclado** (`MountButton`, offset `BtnOffset`), sin láser. Se presiona **apuntándole con el láser y sosteniendo el gatillo hasta que cargue** (el `BeginHold`/`EndHold` de siempre del botón).

## Cómo se instala (solo, en el Tick, con reintento)
`RigTick` → si no está instalado: **`Install`** → `GetPlayerPawn(0)` → `GetComponentsByClass(MotionControllerComponent)` → clasifica por **`MotionSource`** (`RightAim`/`LeftAim`/`RightGrip`/`LeftGrip`, la convención del VRTemplate; verificada igual en `BP_VRPawn_SC` y en `BP_XRPawn`) → `FinishInstall` (monta mandos; instalado = hay Aim de la mano dominante).
Ya instalado: **`RigRun`** → `MaybeInput` (si `bOwnInput` y falta) → `MaybeMount` (el botón, si falta) → si `bActive`, `TickBeamR` **o** `TickBeamL` según la mano dominante.

**Input propio:** `EnsureInput` = `EnableInput(self, PC)` (el PC en SU pin) + `AddMappingContext(IMC_Weapon_Right/Left, 1000, …ForceImmediately)` + autoverificación con `HasMappingContext`. Eventos `IA_Shoot_Right/Left` (`Started` → `Press(bRight)`, `Completed` → `Release(bRight)`), con `bRight` escrito en el pin. **No depende de `Config/DefaultInput.ini`.**

## API pública
| Verbo | Qué hace |
|---|---|
| `SetRigActive(bOn)` | enciende/apaga láser y trace (reemplaza `Sensor.SetStage(4)` / `SetStage(-1)`); al apagar suelta todo y limpia los hits |
| `SetHandedness(bRight)` | cambia la mano dominante; suelta lo agarrado y se reinstala (re-monta mandos y botón) |
| `Press(bRight)` / `Release(bRight)` | los verbos del gatillo (los llama su propio input; un anfitrión puede llamarlos con `bOwnInput` = false) |

Publica (mismos nombres que el sensor, para que esfera y botón solo cambien de clase): `BeamStart`/`BeamStartL`, `BeamDirR`/`L`, `BeamHitLoc`/`L`, `BeamHitActor`/`L`, `BeamEndR`/`L`, `bBeamHit`/`BeamHitL`, `HeldOrb`/`L`, `HeldBtn`.

## Perillas
- `0-Rig`: `TraceDistance` **2500** (era 692: con el domo agrandado a 976 cm de radio el láser no llegaba; tiene que ser mayor que `DomeRadius` + desorden) · `bOwnInput` ✅ · `bShowControllers` ✅ · `bStartActive` ❌ · `bRightHanded` ✅ · `bMountButton` ✅ · `BtnOffset` (2,0,7) escala 0,5 · `CtrlOffsetR` (3,56,−0,8,−2,87 / 0,−90,55) · `CtrlOffsetL` (espejo, **estimado**) · `CtrlMeshR/L` (`/Game/SoulCharger/Shared/QuestController/ControllerR/L`) · `HapticEffect` (`GrabHapticEffect`) · `IMCRight/Left` (`IMC_Weapon_*`).
- `1-Puntero`: los valores afinados del sensor de `Test_Sequencer` (`PtrLen` 40, `PtrWidth` 0,45, `PtrOpacity` 0,58, `PtrDotSize` 1,14, `PtrDotPersp` 0,604…) + `PtrBeamMat`/`PtrDotMat`.
- `CtrlOffsetR` sale de componer la mano del pawn respecto del Grip con el mando del rig de dibujo respecto de la mano. **El izquierdo es un espejo estimado**: ajustar en visor.

## Dependencias medidas (`get_dependencies`)
IA/IMC/haptics del XRFramework, `ControllerL/R`, `M_Pointer_SC`/`M_PointerDot_SC`, `BP_SoundOrb_SC`, `BP_SaveMelody_SC`. **Nada del sensor, del pawn ni de directores.**

## ✅ Verificado en PIE (efecto, no solo ejecución)
En la instancia de PIE: `AimR/AimL/GripR/GripL` = los cuatro mandos del pawn · `CtrlR` hijo de `MotionControllerRightGrip`, `CtrlL` de `LeftGrip` · **el botón Save Melody hijo de `MotionControllerLeftGrip`**, a 7 cm y escala 0,5 · `bInputReady` true.

## Trampas de esta construcción
- 🔴 **Llamar a una función PROPIA con argumento posicional: el primero va al pin `self`.** `(CallFunction|Pulse true)` dejó `bRight` en false (es la causa de fondo del "literal que se pierde" de antes). **Siempre con nombre:** `(CallFunction|ShowPointer :bOn x)`.
- `elif` va **anidado** dentro del anterior, no como hermano.
- El evento de input se crea como **`Input|EnhancedActionEvents|IA_Shoot_Right`** (el read lo muestra como `EnhancedInputActionIA_Shoot_Right`, que no se puede crear).
- Un Actor nuevo trae 3 eventos fantasma en el EventGraph: borrarlos antes de escribir.
- `BreakHitResult` por posición: `Location` = 4, `HitActor` = 9.

### 2026-09-29: contrato TOUR (para `Test_Recorrido`, que carga `Test_Sequencer` como LevelInstance)
Pedido del orquestador (sesión Narrativa). Variables nuevas `Z-Estado`: `TourDormant`, `TourChecked`.
- `TourCheck()` (una sola vez, al primer tick de `RigTick`): `TourDormant = Length(GetAllActorsWithTag("TOUR")) > 0`.
- `RigTick` = `TourCheck` → si **no** está dormido: instalar/correr como siempre. Dormido = ni `Install` ni `RigRun`: sin mandos, sin IMC, sin esconder manos.
- **`RigSleep()`**: `TourDormant` true → `SetRigActive(false)` → `DropInput` (`RemoveMappingContext` IMC R/L + `DisableInput` + `bInputReady` false) → `ShowHands` (`ShowHandsOf(Grip)`: `SetVisibility(true)` + `SetHiddenInGame(false)` a cada SkeletalMesh hijo) → `CtrlRevealT/Tgt` 0 y `CtrlR/L` invisibles.
- **`RigWake()`**: `TourDormant` false → `CtrlRevealTgt` 1 → si ya estaba instalado, `HideHands`; el IMC vuelve solo (`MaybeInput` ve `bInputReady` false).
- Los llama `BP_Sequencer_SC.TourWake/TourSleep`, nadie más. Verificado en PIE (ver el tracker del secuenciador).

### 2026-09-27 (tarde): mandos emisivos, manos escondidas, retiro animado, izquierdo corregido
- 🔴 **El mando izquierdo estaba dado vuelta**: yo lo había "espejado" invirtiendo yaw y roll, y la malla `ControllerL` NO es un espejo simple. Corregido **componiendo con los datos reales** del rig de dibujo izquierdo (mando respecto de la mano: (−2,79, 9,5, −4,3) / (90, 10, 0)) con la mano del pawn respecto del Grip → **`CtrlOffsetL` = (3,56, 0,8, −2,87) / (0, −90, 55)**: la MISMA rotación que el derecho, solo se espeja la Y. Lección: **no deducir un espejo; componer con la fuente**.
- **Emisivo**: material propio del paquete **`M_SeqCtrl_SC`** (unlit, `Emissive = CtrlColor × CtrlBrightness`). `PaintCtrls` lo pone en los dos slots de cada mando y empuja `CtrlColor` (cian 0,35/0,8/1) y `CtrlBrightness` 1,5 (perillas en `0-Rig`). Verificado en PIE: los dos slots de `CtrlR` con `MID_M_SeqCtrl_SC`.
- **Manos escondidas** (`bHideHands`, por defecto sí): `HideHands` recorre los hijos de cada Grip y esconde los `SkeletalMeshComponent` — sirve para cualquier pawn del template (las manos cuelgan de los Grips en `BP_VRPawn_SC` y en `BP_XRPawn`). 🔴 **`SetVisibility(false)` NO alcanza: el pawn las vuelve a prender** (medido en PIE: `bVisible` volvió a true). Lo que se sostiene es **`SetHiddenInGame(true)`** (medido: queda en true).
- **Retiro animado**: `Retire()` = `SetRigActive(false)` + `CtrlRevealTgt` 0; `StepCtrlReveal` (en `RigRun`) interpola `CtrlRevealT` con `RetireSpeed` 4 y escala los dos mandos. Al instalar crecen de 0 a 1. El secuenciador lo llama desde `BeamOff` al guardar la melodía.
- **Solo el mando de la mano dominante** (Beltrán: *"en la izquierda no debe aparecer el motion controller, solo el botón"*): `StepCtrlReveal` multiplica la escala por 1/0 según `bRightHanded` y apaga la visibilidad del otro. Verificado en PIE (diestro): `CtrlR` visible escala 1, `CtrlL` invisible escala 0.
- **El botón en la cara plana del mando**: la malla `ControllerL` mide X ±3,4 · Y −8,5…+3,5 (el mango hacia −Y) · Z −5,1…**+1,85** → la cara plana es el tope Z, cerca de la cabeza (Y ≈ 0,5). `BtnOffset` = ese punto (0, 0,5, 2,1) compuesto con `CtrlOffsetL` → **(5,57, 0,8, −2,08) / (0, −90, 55) / escala 0,4** (≈6,4 cm, el ancho de la cabeza del mando). `MountButton` espeja la Y si es zurdo (los dos mandos comparten rotación). Verificado en PIE: hijo de `MotionControllerLeftGrip` con esa pose exacta.


### 2026-09-30 (noche): láser del cuadro de resultados + clamp
- **`ResultsBeam(bOn)`**: ON = `RigWake` + `SetRigActive(true)` + sonido: el mando de la mano hábil con su láser, **sin agarrar esferas ni el SAVE** (`Press` ignora el gatillo con `bResultsMode`). OFF = `Retire` + `ShowHands` + sonido. Re-prende su propio Tick.
- **`TickBeamRes`** (lo elige `RigRun` con `bResultsMode`): `LineTraceForObjects` con **Object Type Destructible** (`BytetoEnumEObjectTypeQuery 5`, ignora al pawn) → publica `bBeamHit`, `BeamHitActor`, **`BeamHitComp`** (nueva, PrimitiveComponent) y `BeamHitLoc`, y dibuja el puntero de la mano hábil. Esferas (BlockAll), gusano y pawn no cortan el rayo: solo pega en el cuadro (QueryOnly + Destructible). El punto se pega al impacto si el actor tiene tag `Aimable`.
- `StepCtrlReveal` con **Dt = min(DeltaTime, 1/30)** (regla del director). `RigRun` reescrito con ids escribibles (`Variables|Z-Estado|GetActive`, `Variables|0-Rig|GetRightHanded`).
- Paleta (instancia): `CtrlColor` #a0e7ff → **#ffdcb4**; `PtrColor` #b3edff (el default; el valor previo de la instancia no quedó registrado) → **#ffdcb4**.

## 2026-09-30 (noche, 3er turno) — láser de resultados visible + ResPressN
- **`RigUnhide()`**: `SetVisibleinSceneCaptureOnly(false)` en cada PrimitiveComponent del rig. `ResultsBeam` ON la llama primero (la Obra deja la celda de Attracting en solo-captura; ver `BP_Sequencer_SC.md`). OFF no restaura. Verificado en PIE: `PtrBeamR/PtrDotR/CtrlR/CtrlL` con `bVisibleInSceneCaptureOnly` false.
- **`ResPressN`** (int, Z-Estado, público, no IE): en `Press`, si el rig está activo, es la mano hábil y está en `bResultsMode` → +1 (no agarra); fuera de resultados agarra como siempre. **Nunca se resetea**: la Obra (SHARE / DON'T SHARE) compara contra el último valor leído. Verificado por read + compilado estricto; sin gatillo real en PIE.
- ✅ **Mando de la obra con gatillo animado** (vuelta 2, aprobado por Narrativa; pedido de Beltrán "cada interacción con botones, con animación"):
  - **`MountQCtrl(bL)`**: spawnea `BP_QuestCtrl_SC` en el grip → `SetLeft` + `ApplyHand` (no depende del Construction Script) → `AttachActorToComponent` KeepRelative → `SetActorRelativeTransform(QCtrlLoc*, QCtrlRot*, escala 0)` → oculto → `QCtrlR/L`.
  - **`QCtrlHand(bL)`** (desde `StepCtrlReveal`, con `bQuestCtrl` y `bCtrlMounted`): escala `CtrlRevealT × QCtrlScale`, oculto si `!bShowControllers` o escala < 0,01; `Target` del mando = `Clamp(IA_Hand_IndexCurl_R/L)` (nodo de valor de Enhanced Input, sin eventos). Si no existe → `MountQCtrl`.
  - 🔴 `Class|BPQuestCtrlSC|SetTrigger` es AMBIGUO (función `SetTrigger` vs setter del componente `Trigger`): se escribe `Class|BPQuestCtrlSC|SetTarget :Target v` (es lo único que hace `SetTrigger`).
  - `StepCtrlReveal`: el mando cian viejo en escala 0 e invisible mientras `bQuestCtrl`. 🔴 `Math|Vector|vector*vector` (lo que muestra el read) NO se puede escribir: usar `*`.
  - Vars 0-Rig: **`bQuestCtrl`** (IE, true; en la instancia de Test_Sequencer: true) · `QCtrlLocR` (5.686, 0.540, −1.678) · `QCtrlRotR` (P −13.566, Y −83.539, R 64.231) · `QCtrlLocL` (5.877, −1.567, −2.050) · `QCtrlRotL` (0, −95, 65) · `QCtrlScale` 1.0875 (marco del Touch Plus, validado en visor en el dibujo). Z-Estado: `QCtrlR/L`.
  - ✅ PIE en la Obra: `BP_QuestCtrl_SC_C_0` colgado del grip derecho, escala 1,0875, sin errores. ⬜ Visor: el gatillo real y cómo queda en la mano.
