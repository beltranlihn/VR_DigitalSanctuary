# BP_UserTool_SC — el objeto que el usuario lleva en la mano dominante (mando → sensor)

**Ruta:** `/Game/SoulCharger/Mechanics/UserTool/BP_UserTool_SC`
**Nació:** 2026-09-30 (noche), sesión Breath, aprobado por Narrativa (director de la noche; plan `docs/PLAN-NOCHE-2026-09-30.md`).
**Colocado en:** `/Game/Test_Entering` como `Entering_UserTool` (carpeta `Entering`, **tag `TestOnly`**, `bShowMandoOnBegin` true: flag SOLO de test). En la Obra lo coloca Narrativa en el persistente (uno solo).
**Estado:** 🟢 compila (`warnings_as_errors`), PIE verificado con el contrato de Entering · ⬜ visor (pose del sensor en la mano, tamaño, aparición).

## Qué es y por qué uno solo
Según el guion V5 el usuario toma el mando en el Hall y lo lleva hasta el fin de Recognizing; en Entering **el mando se convierte en el sensor** (audio de Beltrán del 2026-09-30) y Heart usa el mismo sensor, rojizo. Un solo actor persistente evita que cada etapa monte y desmonte su propio objeto (y los parpadeos entre celdas).

| Quién | Llama | Efecto |
|---|---|---|
| Hall (al tomar el mando) | `ShowMando(bRight)` | el mando crece en la mano (ease-out, `MorphTime` 0,8 s) + sonido `MandoSound` (Tomado) |
| Breath `StageIntro` (+1,5 s) | `ToSensor(Color)` azulado (0,35, 0,7, 1) | el mando se achica (1−t²) y viaja al centro del sensor mientras el sensor nace con la aparición **luz primero** (`BPC_AppearLuz_SC`, 1,5 s, sonido ProtoSelect) |
| Heart `StageIntro` | `SetSensorColor(Color)` rojizo | fundido de color de las luces en `ColorTime` 1,2 s (smoothstep) |
| Heart `StageOutro` | `Release()` | el sensor se va (Vanish luz primero, sonido VR_shep_scale_down_02); a los 1,6 s vuelve la mano del pawn |

## Arquitectura (clave)
- **Duplicado de `BP_BioSensorArt_SC`** (Mesh 3D): trae `Body`/`Button`/`Waves`/`Trace` con sus tags `AppearBody`/`AppearMover`/`AppearLate`/`AppearTrace` y `Appear` (`BPC_AppearLuz_SC`, FaceAxis (0,0,−1), PivotDepth 0,608, MoverHide (0,0,1,7)).
- 🔴 **La RAÍZ del actor es el marco del SENSOR**: la aparición luz primero calcula el párpado en el marco del dueño y escala alrededor de `FaceAxis·PivotDepth` desde el origen; si el sensor no estuviera en el origen del actor, se deformaría mal. Por eso el actor se cuelga del **grip** con `SensorXf` y todo lo demás va como hijo con `Compose(XfEnGrip, Invert(SensorXf))`.
- Mando: `MandoBodyR/L` (`SM_QuestCtrl_Body_R/L_SC`) con `MandoTrigR/L` hijo en la bisagra (R (1,565, 2,432, −0,145), L con x negado). Las transformadas en el grip son las de `SM_RHand/SM_LHand` del dibujo (`BP_TBDirector_NC`, validadas en visor): `MandoXfR` (5,686, 0,540, −1,678) (P −13,566, Y −83,539, R 64,231) ×1,0875 · `MandoXfL` (5,877, −1,567, −2,050) (P 0, Y −95, R 65) ×1,0875.
- Sensor en el grip = **centro del cilindro viejo del rig** (`/Game/BreathR`, validado en visor 2026-09-27) con la cara (−Z) donde el rig la espera: `FacingOK` usa −Right(GripR) / +Right(GripL) → `SensorXfR` (4,325, −1,685, −2,335) Roll +90 · `SensorXfL` (4,325, +1,685, −2,335) Roll −90. La detección del rig NO depende de esta malla (usa el grip), así que moverla no rompe el umbral.
- `HandGhost` (SKM_MannyXR_right, oculto en juego) = la mano del pawn (`HandRelR` = `HandRight` del `BP_VRPawn_SC` respecto del grip) vista desde el sensor: **para ajustar la pose en el viewport**, editar `SensorXfR` y mirar el fantasma y el mando (el CS los recoloca).
- Cálculo offline: `VR_Test/Saved/ClaudeScripts/usertool/ue_xf.py` (convención de `FRotationMatrix`, verificada) + `poses.py` → `poses.json`.

## Variables
`A-Herramienta` (instance-editable): `bRight` true · `bShowMandoOnBegin` false (**solo test**) · `MorphTime` 0,8 · `ColorTime` 1,2 · `LightColor` (1, 0,72, 0,45) (el color de Mesh 3D) · `SensorXfR/L` · `MandoXfR/L` · `MandoSound` (Tomado).
`Z-Estado`: `HandRelR` · `Mode` (0 nada, 1 mando, 2 sensor, 3 soltado) · `ModeReq` (−1 = sin pedido) · `PrevMode` · `bMounted` · `MorphT` · `ColorT` · `ColorFrom/To` · `MandoRest` · `Hand` · `Grip`.
Las transformadas se escriben con JSON `{"location":{..},"rotation":{"pitch","yaw","roll"},"scale":{..}}` (el formato de texto `(Rotation=…)` NO se aplica).

## Grafos (DSL completo en `VR_Test/Saved/ClaudeScripts/usertool/usertool.dsl`)
- **EventGraph:** `BeginPlay` → `ToolHide` (todo oculto: mandos, `Appear.Prepare()`; ModeReq 1 si `bShowMandoOnBegin`) · `Tick` → `ToolTick(DT)`.
- **`ToolTick(DT)`**: `dt = min(DT, 1/30)` (regla de la obra) · sin montar: `ToolMount` + `ToolAttach` · montado: `ToolApply` → `ToolMorph(dt)` → `ToolAnim(dt)`.
- **`ToolMount`**: la búsqueda probada del rig (`FindHand`): componente del pawn por nombre `HandRight`/`HandLeft` → `Hand`, su padre → `Grip`.
- **`ToolAttach`**: `IsValid(Grip)` → `AttachActorToComponent` (Snap/Snap/KeepWorld) + `SetActorRelativeTransform(SensorXf)` + `ToolPose` + `bMounted`.
- **`ToolApply`**: aplica el pedido una vez (switch sobre `Mode − 1`: el switch int trae solo 3 salidas) · 0 mando · 1 sensor (`Appear()`, MorphT 0 si venía del mando) · 2 `Vanish()`.
- **`ToolMorph(DT)`**: el reloj `MorphT` → transformada del mando (crece / se achica y viaja al centro) · al terminar: visibilidad del mando y de la mano.
- **`ToolAnim(DT)`**: fundido de color. **`PushColor(C)`**: `Color` en `Body`, `Button`, `Waves` (M_SCLight_SC y M_BioSensorWaves_SC; M_SCObject_SC no tiene `Color`, el hormigón no se tiñe).
- **`ToolPose`** (CS y montaje): `MandoRest`, mandos y fantasma en el marco del sensor. **CS**: `ToolPose` + visibilidad para autorar + `PushColor(LightColor)`.
- API: `ShowMando(Right)` (si cambia la mano, re-monta) · `ToSensor(Color)` · `SetSensorColor(Color)` · `Release()`.

## Verificado (2026-09-30, PIE en Test_Entering, `bContractTest`)
Log: `USERTOOL: listo` → `montado en el grip` → `mando en la mano` → (StageIntro) → +1,48 s `el mando se convierte en el sensor`; fin de PIE con `Mode` 2, `AppearT` 1, `LightColor` azul, `bMounted` true; cero `Accessed None`. Captura del editor: `Saved/ClaudeScripts/usertool/cap_tool.png`.

## Pendiente / límites
- ⬜ Visor: pose del sensor contra la mano real (ajustar `SensorXfR` mirando `HandGhost`), escala (Ø19 cm), la transformación.
- La mano del pawn se oculta/aparece de golpe (`SetHiddenInGame`), igual que en todos los rigs; un fundido pediría tocar el pawn (Core, compartido).
- `ShowMando` cambiando de mano con el objeto ya montado deja oculta la mano vieja (la mano se elige una vez en el Hall).
- `Test_Recorrido` (carga Test_Entering) no tiene herramienta: ahí Entering queda sin mando visible (el rig ya no dibuja el suyo).

- **2026-09-30 (tarde) — en la Obra:** `UserTool_Obra` (persistente de `L_SoulCharger_Obra`, lo colocó Narrativa) tiene los mismos valores de autor que `Entering_UserTool` de Test_Entering (ambos = CDO; las diferencias de transform de `MandoBodyR/L` en la instancia de test son del CS, no de autor). `bShowMandoOnBegin` false. ⚠ **Heart todavía NO llama `SetSensorColor`/`Release`**: su `StageIntro`/`StageOutro` tienen solo un print de hueco (avisado a Narrativa). Mesh 3D agrega `ToolTrigger` (gatillo con el eje real) en el turno siguiente.

## Gatillo animado del mando (2026-09-30 noche, Mesh 3D; aprobado por Narrativa y Breath)
Regla de Beltrán: *"cada vez que se interactúe con botones, que sea con animación"*.
- **`ToolTrigger(DT)`** (grafo nuevo), llamado después de `ToolAnim` en `ToolTick` (con el `DT` ya recortado a 1/30).
  - Lee el eje real del gatillo con el nodo PURO `Input|EnhancedActionValues|IA_Hand_IndexCurl_Right/Left` (según `bRight`; Axis1D en `Trigger_Axis` vía `IMC_Hands` del pawn). Sin nodos de evento: no consume input.
  - Objetivo = eje solo con `Mode` 1 (mando); en 0/2/3 vuelve a 0. `TrigV = FInterpTo(TrigV, objetivo, DT, TrigFollow)`.
  - `MandoTrigR/L.SetRelativeRotation(RotatorFromAxisAndAngle(TrigAxisR/L, TrigSign · TrigV · TrigDegrees))` (reposo 0; el origen de la malla está en la bisagra) + `Pressed` = TrigV en su material.
  - `EnableInput(self, PlayerController 0)` una sola vez (`bTrigInput`), con el actor ya montado.
- Variables (instance-editable, Default): `TrigDegrees` 14 · `TrigSign` −1 · `TrigFollow` 25 · `TrigAxisR` (0,976, −0,2177, −0,0083) · `TrigAxisL` (0,976, 0,2177, 0,0083). Estado: `TrigV`, `bTrigInput`. Receta de `BP_QuestCtrl_SC`.
- ✅ Compila; PIE en la Obra: montado, `bTrigInput` true, `TrigV` 0 en Mode 0, cero warnings. ⬜ Visor: el giro con el gatillo real (en PIE no hay eje).
- ⚠ Los getters de las variables viejas llevan su categoría: `Variables|A-Herramienta|GetRight`, `Variables|Z-Estado|GetMode` (el índice de `find_node_types` desde otro grafo puede mostrar `Default`: es viejo).
