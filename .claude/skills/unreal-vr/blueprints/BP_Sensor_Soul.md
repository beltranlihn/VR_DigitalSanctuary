# BP_Sensor_Soul — el sensor que se toma con la mano hábil (Core/Sensor/)

> `/Game/SoulCharger/Core/Sensor/BP_Sensor_Soul` · creado 2026-08-19 · **una instancia** en `MapsV2/L_SoulCharger` (`Sensor_Soul`, en **50/0/100**, o sea 50 cm delante del pawn cuando está parado en el centro del Hall).
> **Estado: 🟡 toma forzada verificada en PIE por log (`SENSOR: tomado con la DERECHA`, el guión siguió); falta el visor para la toma real con la mano.**

## Qué es
La versión **mínima** del sensor para la maqueta (pedido de Beltrán, 2026-08-19): *"una esfera de 10 cm que al tocarla se attachea a nuestra mano hábil, y hace que crezca otro sensor en la mano ajena. Por ahora sólo el sensor que se attachea y marca un timing."* Reemplaza, para la versión limpia, al `BP_Sensor` viejo (uno por mano + modos por etapa), que queda en `L_Persistent` como referencia.

## Cómo funciona
- **Dos mallas en UN actor**: `Body` (la que se ve y se toma) y `Twin` (la gemela de la otra mano). Las dos son la esfera del motor a escala 0,1 (10 cm), material **`MI_Sensor`** (el blanco tibio que ya distinguía sensores de amebas), `NoCollision` (pegado a la mano se interpondría en los punteros), sin sombra. **Cero spawn**: al tomar, `Body` se attachea a la mano que tocó y `Twin` a la otra, las dos por `AttachComponentToComponent(Snap, Snap, KeepWorld)` — un componente puede colgar de un componente de OTRO actor (el `MotionController` del pawn).
- **Detección por distancia, no por colisión** (la gramática de `BP_Sensor`/`BP_Bell`): `CheckHands` compara la distancia² de cada grip del pawn (`GetMotionControllerRightGrip/LeftGrip` de `BP_VRPawn_SC`) contra `TakeRadius²`. La derecha gana si las dos están dentro.
- **Nace invisible** (`bStartHidden`) y **`Appear()`** la hace crecer en `AppearTime`; `StepAppear` mueve `AppearT` (Body) y `TwinT` (Twin, que sólo crece cuando `bTaken`) con `FInterpToConstant` y escribe **`SetWorldScale3D`** cada tick — por eso no hace falta guardar nada al attachear (la escala mundial se mantiene aunque el padre esté a 1,5).
- **`Take(Right)`** es pública (la usa el autotest: `Take(true)`); internamente `TakeBody` → `AttachHands` → sonido (`TakeSound` = `Trigger_Select`) + háptica (`Pulse`, `GrabHapticEffect` del XRFramework, en la mano que tocó) → **`OnTaken`** (dispatcher, sin params; `bTookRight` dice cuál fue).

## Registro de variables
| Cat | Variable | Default | Rol |
|---|---|---|---|
| A - Sensor | `TakeRadius` | 12 cm | radio de toma |
| | `BodyScale` | 0,1 | escala de la esfera del motor = 10 cm |
| | `AppearTime` | 0,8 s | crecimiento (y el de la gemela) |
| | `bStartHidden` | true | nace en escala 0 hasta `Appear()` |
| | `Volume` · `TakeSound` · `HapticEffect` | 1 · `Trigger_Select` · `GrabHapticEffect` | feedback |
| Z - Estado interno | `bShown` · `bTaken` · `bTookRight` · `AppearT` · `TwinT` · `PawnSC` | | |

## Grafos
`BeginPlay`: Twin a 0; si `bStartHidden` → Body a 0, si no → `Appear`. · `Tick`: `StepAppear(DT)`; si `bShown && !bTaken && AppearT>0.9` → `TryTake` (IsValid pawn → `CheckHands`, si no → `CachePawn`). · Funciones: `CachePawn` · `Appear` · `StepAppear` · `TryTake` · `CheckHands` · `Take` · `TakeBody` · `AttachHands` · `Pulse`.

## Trampas
- `(CallFunction|Take true)` **perdió el literal** (`Right` llegó `false`): se arregló con `set_pin_value`. Regla general en `gotchas.md`.
- `add_event_dispatcher` lleva el parámetro **`name`** (no `dispatcher_name`).

## TODO
- [ ] Visor: tomar con la mano, que la gemela aparezca en la otra.
- [ ] Material/forma reales; hoy es la esferita blanca de `MI_Sensor`.
- [ ] `Release()` / `Disappear()` si algún día hace falta soltarlo (hoy `bShown=false` lo encogería, pero no hay verbo público).
