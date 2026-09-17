# BP_BreathManager_SC + MPC_Breath — la respiración PORTABLE (Mechanics/Breath/)

> `/Game/SoulCharger/Mechanics/Breath/BP_BreathManager_SC` + `/Game/SoulCharger/Mechanics/Breath/MPC_Breath` · creado 2026-09-17 · **una instancia** en `/Game/TestMeshes` (`GAL_BreathManager`, carpeta `Galeria/_Sistema`, sin tags de estación).
> Pedido de Beltrán: *"vamos a traer la mecánica de respiración… que la mecánica incluya el umbral, haptic, etc. Lo que ya habíamos hablado que debe tener para traspasar de un proyecto a otro"*. Es el **paso 3 del plan de extracción** de [`docs/MECANICAS-PORTABLES.md`](../../../../docs/MECANICAS-PORTABLES.md).
> **Estado: 🟢 portado y verificado en PIE** (manos y cámara resueltas sin cast al pawn, `BREATH: listo` una sola vez, respiración de prueba publicando −1↔+1, cero `Accessed None`). ⬜ **Falta el visor**: el umbral con el mando en la panza y la háptica solo se validan en gafas.
> Plan y diseño por estación: [`docs/PLAN-GALERIA-RESPIRACION-2026-09-17.md`](../../../../docs/PLAN-GALERIA-RESPIRACION-2026-09-17.md).

## Qué es
El motor de señal + umbral + háptica de la esfera de Entering (modo 1 de [[BP_Sensor_Soul]]), **sacado del sensor y sin nada de la obra**: no conoce al pawn por clase, no conoce directores, no es dueño del input y no tiene metas ni práctica. Publica la respiración de dos formas:
- **Variables públicas** (categoría `Y - Publicado`) para Blueprints que quieran leerla con `GetActorOfClass`.
- **`MPC_Breath`** para que CUALQUIER material o Blueprint la lea sin conocer esta clase. Es el bus de la galería: los efectos no referencian al manager, solo al MPC.

`BP_Sensor_Soul` **no se tocó**: la obra sigue con su copia. Migrarla a consumidora de este manager es un paso posterior, después del visor.

## Cómo se instala en un nivel nuevo (la receta)
1. Copiar la carpeta `Mechanics/Breath/` (manager + MPC). Depende solo de `/Game/XRFramework/Haptics/GrabHapticEffect` (perilla `HapticEffect`, reemplazable).
2. El pawn tiene que tener una cámara (`CameraComponent`) y dos SceneComponents llamados **`HandRight`/`HandLeft` hijos de su MotionController Grip** (el contrato de `FindHand`, el mismo del rig). Cumplen `BP_VRPawn_SC` y `BP_XRPawn`.
3. Colocar **una** instancia en el nivel persistente. Nace con los valores del CDO, que son los afinados en visor.
4. PIE: tiene que aparecer **una vez** `BREATH: listo (camara + manos del pawn)`. Si no aparece, el pawn no cumple el contrato del punto 2 (el manager reintenta en silencio cada tick).
5. Consumidores: leer `MPC_Breath` (materiales: `CollectionParameter`; BPs: `GetScalarParameterValue` con `declaring_class=KismetMaterialLibrary`) o las variables `Y - Publicado` del actor.

## API — lo que publica
| Señal | Dónde | Rango | Uso |
|---|---|---|---|
| `bBreathing` | var | bool | umbral confirmado (zona + quietud + amplitud, con debounce) |
| `BreathLevel` | var | 0..1, 0,5 neutro | la señal cruda validada (lo que lee la esfera de Entering) |
| `BreathDrive` | var | 0..1, 0,5 en reposo | `FInterpTo(select(bBreathing, BreathLevel, 0.5), DriveFollow)` — **el seguimiento de la esfera** |
| `BreathSigned` / `Signed` | var + MPC | −1..+1, 0 en reposo | `clamp((Drive−0,5)·2·SignedGain)`. **+ = inhala, − = exhala** |
| `BreathOn` / `On` | var + MPC | 0..1 | presencia suavizada (tau ~0,5 s): 1 mientras hay umbral |
| `FlowIn` / `FlowOut` | var + MPC | segundos | `∫max(S,0)dt` y `∫max(−S,0)dt` — para modular VELOCIDADES sin saltos (ver abajo) |

🔴 **Cómo modula un consumidor, la convención de toda la galería:** `valor · (1 + max(S,0)·In + max(−S,0)·Out)`. `In`/`Out` = cuánto cambia (±fracción) a inhalación/exhalación **plena**. Con `S = 0` el valor es **exactamente el autorado**.
🔴 **Velocidades:** nunca multiplicar un `Speed` que el shader usa como `Time × Speed` (salta la fase entera). Sumar a la fase `Speed · (In·FlowIn + Out·FlowOut)`: la velocidad efectiva queda `Speed·(1 + In·max(S,0) + Out·max(−S,0))` y en reposo no cambia nada.

## Registro de variables
| Cat | Variable | Default | Rol |
|---|---|---|---|
| **A - Umbral** | `SafeHorizMax` | 23 | distancia horizontal máx. cabeza→mando (cm) para estar en zona |
| | `SafeVDropMin` / `SafeVDropMax` | 33 / 63 | caída vertical cabeza→mando (cm) — la panza de los 14 usuarios |
| | `StillLin` / `StillAng` | 14 cm/s / 45 °/s | quietud (subirlos = más tolerante al moverse) |
| | `StillTau` | 0,3 | caída del EMA de velocidad (el ataque es instantáneo) |
| | `MinHAmp` | 0,02 | amplitud mínima de la señal para ENTRAR (medida en vivo, no extrapolada) |
| | `ActivateDelay` / `DeactivateDelay` | 1,5 / 0,2 s | debounce: entrar lento, salir rápido |
| **B - Senal** | `TauFast` / `HorizTau` | 0,4 / 3 s | el band-pass sobre `GeomHoriz` (la panza empuja el mando) |
| | `TauAmp` | 4 | EMA de `|band-pass|` → `HAmp` |
| | `GainK` | 0,5 cm | ganancia de la saturación suave `x/(1+|x|)` |
| | `LevelFollow` | 5 | seguimiento de `BreathLevel` |
| | `HoldSlow` / `HoldMovK` | 0,25 / 1 | el sostenido no se desinfla (frena la base cuando el mando se queda quieto) |
| | `bFlipSign` | false | escape manual del signo |
| **C - Haptica** | `bHaptics` | true | apaga zumbido y pulso sin tocar la lógica |
| | `HapticAmp` | 0,25 | zumbido continuo mientras `bBreathing` |
| | `HapticEffect` | `GrabHapticEffect` | el pulso del flanco IN |
| **D - Salida** | `DriveFollow` | 4 | seguimiento del Drive (el de la esfera, "excelente") |
| | `SignedGain` | 1,5 | **una perilla para toda la galería**: cuánto mueve una respiración normal (la señal real ronda 0,18↔0,81 → ±0,6 sin ganancia) |
| | `bAutoHand` | true | usa la primera mano que entra a la zona; cambia solo fuera del umbral |
| | `bRightHand` | true | mano inicial (y la única si `bAutoHand` = false) |
| **E - Prueba** | `PreviewBreath` | 0 | **−1..+1: el Construction Script lo escribe al MPC → las estaciones de material respiran en el viewport sin Play** |
| | `bFakeBreath` / `FakePeriod` | false / 6 s | respiración sintética (0,1↔0,9) para PIE sin gafas; también prende `On` |
| **Y - Publicado** | `bBreathing` · `BreathLevel` · `BreathDrive` · `BreathSigned` · `BreathOn` | | ver API |
| **Z - Estado** | `HandR`/`HandL` (MotionController) · `CamRef` (Camera) · `bRight` · `LinSpeed`/`AngSpeed` · `bQuiet` · `GeomHoriz`/`GeomVDrop` · `bZone` · `HFast`/`HSlow` · `HAmp` · `MovAvg` · `InTimer`/`OutTimer` · `bWasBreathing` · `FlowIn`/`FlowOut` | | internos |

## Estructura de grafos
- **ConstructionScript** → `PushMPC(PreviewBreath, PreviewBreath≠0 ? 1 : 0, 0, 0)`.
- **BeginPlay** → `PushMPC(0,0,0,0)` (limpia lo que haya dejado la vista previa).
- **Tick** → `TickBreath(DT)`: `IsValid(HandR)` → **sí**: `SenseHand` → `UpdateLevel` → `BreathThreshold` → `BreathHaptic` → `PickHand` → `Publish` · **no**: `Acquire` → `Publish`.

| Función | Responsabilidad |
|---|---|
| `Acquire` | pawn poseído → `CamRef` (`GetComponentByClass Camera`), `HandR`/`HandL` (`FindHandMC`), `bRight = bRightHand`. Imprime `BREATH: listo` solo cuando encuentra la mano derecha. |
| `FindHand(bRight)` / `FindHandMC(Right)` | **copiados del rig**: componente del pawn por nombre `HandRight`/`HandLeft` → `GetAttachParent` → cast a MotionController. Sin cast al pawn. |
| `SenseHand(DT)` | quietud (velocidades del grip, ataque instantáneo + caída `StillTau`, y trackeado) + geometría cámara→grip (`GeomHoriz`, `GeomVDrop`) + `bZone`. |
| `UpdateLevel(DT)` | **portado del sensor tal cual**: band-pass con freno de sostenido (`HoldSlow`/`HoldMovK`, sin lazo), `HAmp`, `BreathLevel` con saturación suave, `MovAvg`. |
| `BreathThreshold(DT)` | `in = zona ∧ quietud ∧ (respirando ∨ HAmp ≥ MinHAmp)`, debounce 1,5/0,2 s, `Pulse` + resiembra (`HFast = HSlow = GeomHoriz`, `BreathLevel = 0,5`) en el flanco IN, logs `BREATH: UMBRAL IN/OUT`. |
| `BreathHaptic` | zumbido `SetHapticsByValue(1, HapticAmp)` en la mano activa mientras `bBreathing`; apagado limpio en el flanco (estado actualizado dentro del flanco, §213). |
| `Pulse(Right)` | `PlayHapticEffect(HapticEffect)` en esa mano. |
| `HandInZone(Right)` | la misma prueba de zona para cualquier mano (la usa `PickHand`). |
| `PickHand` | con `bAutoHand`, fuera del umbral y con la mano activa fuera de zona: si la otra está en zona, cambia (`LinSpeed = 999` fuerza la resiembra por quietud, `InTimer = 0`) y loguea `BREATH: mano DERECHA/IZQUIERDA`. |
| `Publish(DT)` | `BreathDrive`, `BreathSigned`, `BreathOn`, `FlowIn`, `FlowOut` y `PushMPC`. |
| `PushMPC(S, On, FIn, FOut)` | 4 `SetScalarParameterValue` de **colección** (hechos por cirugía con `declaring_class`). |

## Qué se portó y qué NO (a propósito)
- ✅ Portado igual: `UpdateLevel` v6 + `HoldSlow`, umbral v4, háptica, pulso, resiembra del flanco IN, los valores del CDO vivo de `BP_Sensor_Soul` (leídos el mismo día, no de un doc).
- ✅ Cambiado por portabilidad: la cámara y los grips se consiguen sin castear a `BP_VRPawn_SC`; la punta es el **grip** (en la obra la esfera se pega al grip con `SnapToTarget`, así que es el mismo punto con que se armó la zona).
- ❌ No viaja: la toma del sensor, `SetStage`/modos, la práctica, la calibración dormida, y **`DetectDir`/`CountBreaths`**: cuentan sostenidos sobre la inclinación del mando, la señal que el análisis descartó (AUC 0,587).

## Verificación hecha (2026-09-17)
- Compila con `warnings_as_errors`. Todas las llamadas propias verificadas con `get_node_infos` (pin `self` = "Self Object Reference"): el `read_graph_dsl` las muestra como `Class|BPSensorSoul|…` / `Class|BPLightShaftSC|PushMPC` — **es la etiqueta equivocada conocida, no el cableado**.
- Literales verificados en el grafo: `"Right"` en háptica y pulso, clase y nombres en `FindHand`.
- PIE en `TestMeshes`: `HandR` = `MotionControllerRightGrip`, `HandL` = `MotionControllerLeftGrip`, `CamRef` = `Camera`; con `bFakeBreath`: `BreathSigned` −1↔+1, `BreathOn` → 1, `FlowIn` crece solo en la fase +, `FlowOut` solo en la −.
- De punta a punta con un consumidor de CPU: los haces de la estación 1 abren el cono y el pozo con los números exactos de la fórmula (ver [[BP_LightShaft_SC]]).

## TODO
- [ ] 🔴 **Visor**: umbral con el mando en la panza (derecha e izquierda), zumbido, pulso del IN, y que el cambio automático de mano no moleste.
- [ ] Afinar `SignedGain` en gafas (hoy 1,5: una respiración normal llega a ±0,8-1).
- [ ] Opción a probar: que el zumbido suba con la inhalación (hoy constante, como lo validó Beltrán).
- [ ] Migrar `BP_Sensor_Soul` (obra) a consumidor de este manager — después del visor.
- [ ] Colapsar la 4ª copia del resolvedor de manos en `Core/Pawn/BPFL_XRHands` (crear a mano: `create` de BlueprintFunctionLibrary por MCP colgó el editor).
