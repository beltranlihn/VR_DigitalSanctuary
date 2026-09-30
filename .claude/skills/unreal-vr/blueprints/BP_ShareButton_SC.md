# BP_ShareButton_SC — los botones SHARE / DON'T SHARE del cuadro de resultados

- **Ruta**: `/Game/SoulCharger/Mechanics/Results/BP_ShareButton_SC`.
- **Estado**: 🟢 construido y compilando (2026-09-30 noche) · 🟢 dos instancias en `L_SoulCharger_Obra` · ⬜ prueba de hover/press en PIE · ⬜ visor.
- **Modelo y look**: `blender-3d/assets/share-button.md`. Los grafos los genera `unreal-vr/scripts/share_button_dsl.py`.
- **Es arte + interacción mínima.** La Obra (Narrativa) decide el hover con el láser de resultados (`BP_SeqRig_SC.ResultsBeam` → `BeamHitActor`) y llama a la API.

## API (pedida por Narrativa)
| | |
|---|---|
| `Appear()` / `Vanish()` | entra / sale con "luz primero" (1,5 s; sonidos `SBubbleHoverOn/Out`). `Appear` reinicia el estado |
| `SetHover(On)` | solo actúa en el CAMBIO y si el botón está entero y no se apretó. Con `On` suena `HoverSound` (`VR_click1`) |
| `Press()` | solo si está entero y no se apretó. Suena `PressSound` (`ChargeFinal`, el "completo" del SAVE). La confirmación dura 0,45 s → `OnConfirmed` → `Vanish()` solo |
| `OnConfirmed` | dispatcher al terminar la confirmación. La Obra hace SHARE → alma a la constelación / DON'T → desvanecer, y le da `Vanish()` al OTRO botón |
| Variables | `bDontShare` (perilla: false = SHARE, true = DON'T SHARE; cambia el material del tope también en el editor, vía Construction Script) · `Confirmed` · `AppearLuz.AppearT` |
| Prueba suelta | `AppearOnPlay` + `AppearDelay` (instance-editable), como el resto del arte |

- **Sin Tick en reposo.** `SleepTicks` apaga el Tick del actor y el de `AppearLuz` cuando no hay nada que animar (ni hover, ni confirmación, ni aparición, ni espera). `WakeTicks` los prende en cada llamada de la API.

## Componentes (cara del actor = +X, arriba = +Z; origen = centro de la espalda)
| Componente | Qué | Tag / colisión |
|---|---|---|
| `Base` | `SM_ShareButton_Base_SC` (Body + Ring) | `AppearBody` · NoCollision |
| `Plate` | `SM_ShareButton_Plate_SC`. La mueve SOLO `PoseButton`: asoma con los tiempos del AppearMover del SAVE (0,52-0,80, ease_out_back 1,2) + hover/press | NoCollision |
| `Slider` | `SM_ShareButton_Slider_SC` (`Progress` = la confirmación) | NoCollision |
| `Trace` | `SM_ShareButton_Trace_SC` → `M_AppearTrace_SC` | `AppearTrace` · NoCollision |
| `Hit` | BoxComponent en (0,9, 0, 0), extensión (0,95, 11,2, 3,7) cm, oculto en juego | **QueryOnly + `ECC_Destructible` + todo Ignore** (el trazo por objetos del láser de resultados) |
| `AppearLuz` | `BPC_AppearLuz_SC`: FaceAxis (1,0,0), PivotDepth 1,5, Duration 1,5 | se llama AppearLuz para que la función `Appear()` no choque con el nombre del componente |

- Tag del actor: **`Aimable`** (el punto del láser se pega al impacto).
- MI (en `Results/`, con los valores del SAVE): `MI_ShareButton_Body_SC`, `_PlateSide_SC`, `_PlateTopShare_SC` / `_PlateTopDontShare_SC` (con `T_Share_Text` / `T_DontShare_Text`), `_Ring_SC` (Glow 0,7), `_Slider_SC`.

## En la Obra (pedido de Narrativa)
- `BP_ShareButton_SC_C_0` (SHARE, tag de actor **`share_yes`**) y `BP_ShareButton_SC_C_1` (DON'T SHARE, `bDontShare` true, tag **`share_no`**), los dos con `Aimable`, `AppearOnPlay` false.
- Estacionados bajo el cuadro estacionado: (0, ±15, −5064), pitch 15, cara +X (SHARE a la izquierda del usuario). Narrativa los ubica en el turno B.
- Ocultos hasta `Appear()`: `BeginPlay` → `Prepare` del AppearLuz + `PoseButton(0)` (placa oculta) + `SleepTicks`.
- ⚠ El `Hit` responde al trazo aunque el botón esté oculto: la Obra solo apunta cuando `AppearLuz.AppearT` ≥ 0,999.

## Trampas de la construcción
4. `Math|Float|NegateFloat` creado por `create_node` trae pines de EXEC: fuera de la cadena no corre y devuelve 0 → `Dt/0`, `HoverK` pegado en 1 y el botón nunca se dormía (6240 "Divide by zero"). ✅ `Utilities|Operators|Multiply` con B −1.
5. Los literales del DSL son nodos `Math|Float|MakeLiteralFloat`: para cambiarlos por una variable se conecta el getter al CONSUMIDOR y se borra el literal. Los getters de variables con categoría llevan la categoría en el id (`Variables|Timing|GetHoverinTime`, con la i minúscula).
1. `Default|CallOnConfirmed` se cableó al dispatcher **`OnConfirmed` de `BP_SaveButton_C`** (colisión de nombres; compila con error *"This blueprint (self) is not a BP_SaveButton_C"*). ✅ Nodo nuevo con `create_node` + `declaring_class` = `BP_ShareButton_SC_C`.
2. El getter de `bDontShare` es `Variables|Default|GetDontShare` (el DSL saca la b).
3. El `read_graph_dsl` muestra `Class|BPProtoSoulSC|StepHover`, `Class|BPSensorSoul|Appear` donde se escribió `CallFunction|…`: es el READ que miente; los pines `self` son "Self Object Reference" (verificado con `get_node_infos`).

## Tiempos y recorridos = variables de autor (2026-09-30, regla de Beltrán: el timeline manda, no el sonido)
| Variable (Timing, instance-editable) | Valor | Dónde |
|---|---|---|
| `HoverInTime` / `HoverOutTime` | 0,12 / 0,18 s | `StepHover` (la salida: `Dt / (HoverOutTime × −1)`) |
| `PressTime` | 0,45 s | `StepPress`: la confirmación dura esto → `OnConfirmed` → `Vanish` |
| `PressDepth` / `HoverLift` | 0,4 / 0,1 cm | `PoseButton` (hundido con ease-out, subida en hover) |
| Aparecer / irse | `AppearLuz.Duration` 1,5 s | el componente |
- Los sonidos son de un disparo: ningún tiempo sale de su largo.
- **`bDemoPress`** (categoría Test, false): SOLO prueba. Con el botón entero, hover a 0,6 s y press a 1,8 s (`DemoStep`, llamado después de `IdleCheck`). Encendido solo en las 2 instancias de `Test_Results`.
- ✅ PIE (Test_Results): hover +1 mm, press → OnConfirmed → Vanish, y al final todo en reposo y dormido. ⬜ Visor: si el hundido de 4 mm se lee a 1,9 m.

## Pendientes
- [ ] Visor: tamaño y legibilidad a 2 m.
