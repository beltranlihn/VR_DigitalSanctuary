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
| `BreathSigned` / `Signed` | var + MPC | −1..+1, 0 en reposo | **(4ª pasada: GANANCIA AUTOMÁTICA por usuario)** `bp = HFast − HSlow` (cm) · `AmpEMA = EMA(|bp|, AmpTau 8 s)` solo mientras hay umbral · `x = bp / max(AmpEMA·π/2, AmpFloorCm) · SignedGain` → una respiración NORMAL de este usuario da `x ≈ ±1` al final de la inhalación, sea de 0,5 o de 3 cm. *(3ª pasada, reemplazada: `x = (HFast − HSlow)·SignedGain` en cm fijos — con la respiración de Beltrán (~3 cm) cruzaba el codo en el primer tercio: "no he terminado de inhalar y ya llegó")* → objetivo `x / (1 + |x|³)^(1/3)` (lineal hasta ~0,7, codo suave) → **resorte críticamente amortiguado** `SVel += (ω²·(obj − S) − 2ω·SVel)·dt; S += SVel·dt` con `ω = SmoothFreq`. **+ = inhala, − = exhala**. Acompaña una respiración lenta: llega al máximo al final de la inhalación, no antes |
| `BreathOn` / `On` | var + MPC | 0..1 | presencia suavizada (tau ~0,5 s): 1 mientras hay umbral |
| `FlowIn` / `FlowOut` | var + MPC | segundos | `∫pos(S)dt` y `∫neg(S)dt` con partes positiva/negativa SUAVES (`(0,5·(±S + √(S²+0,01)) − 0,05)/0,95249`, sin quiebre en 0) — para modular VELOCIDADES sin saltos |

🔴 **Cómo modula un consumidor, la convención de toda la galería (2ª pasada):** `valor · m`, con **`m = 1 + S·lerp(−Out, In, smoothstep((S+1)/2))`**. `In`/`Out` = cuánto cambia (±fracción) a inhalación/exhalación **plena**. Con `S = 0` el valor es **exactamente el autorado**, y aunque `In` y `Out` sean muy distintos no hay quiebre al pasar por el centro.
🔴🔴 **La lección de la 2ª pasada (Beltrán: *"llegó muy duro a los máximos y mínimos"*)**: la v1 hacía `clamp(gain·y, −1, 1)` y los consumidores `max(S,0)·In + max(−S,0)·Out`. Con ganancia 1,5 una respiración normal **chocaba contra el clamp y quedaba plana** — se siente como un tope. La esfera de Entering nunca tuvo tope: su nivel sale de una saturación suave. **Nada que sea biofeedback lleva un clamp duro ni una función por tramos con quiebre.**
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
| **B - Senal** | `TauFast` / `HorizTau` | 0,4 / **8 s** (4ª pasada; la obra usa 3) | el band-pass sobre `GeomHoriz` (la panza empuja el mando). Con 3 s la base alcanzaba a una respiración lenta a mitad de la inhalación y el pico llegaba antes de tiempo |
| | `TauAmp` | 4 | EMA de `|band-pass|` → `HAmp` |
| | `GainK` | 0,5 cm | ganancia de la saturación suave `x/(1+|x|)` |
| | `LevelFollow` | 5 | seguimiento de `BreathLevel` |
| | `HoldSlow` / `HoldMovK` | 0,25 / 1 | el sostenido no se desinfla (frena la base cuando el mando se queda quieto) |
| | `bFlipSign` | false | escape manual del signo |
| **C - Haptica** | `bHaptics` | true | apaga zumbido y pulso sin tocar la lógica |
| | `HapticAmp` | 0,25 | zumbido continuo mientras `bBreathing` |
| | `HapticEffect` | `GrabHapticEffect` | el pulso del flanco IN |
| **D - Salida** | `DriveFollow` | 4 | seguimiento del Drive (el de la esfera, "excelente") |
| | `SignedGain` | **1,0** (4ª pasada: SIN unidades) | **cuánto de la respiración normal de ESTE usuario = el codo de la curva**. 1 = su respiración normal llega a ~0,8; subirlo = llega antes al extremo; bajarlo = hace falta respirar más profundo |
| | `SmoothFreq` | **4** (era 6) | frecuencia del resorte que suaviza `S` (más alto = más inmediato; más bajo = más "flotante"). Sin rebote en ningún valor |
| **B - Senal** | `AmpTau` 🆕 | 8 s | memoria de la ganancia automática (cuántos segundos de respiración promedia para aprender la amplitud del usuario) |
| | `AmpFloorCm` 🆕 | 0,3 cm | piso de la amplitud aprendida: evita amplificar ruido si alguien respira casi sin mover la panza o sostiene mucho |
| **E - Prueba** | `FakeAmpCm` 🆕 | 1,5 cm | amplitud en cm de la respiración de prueba — ahora pasa por la MISMA ganancia automática que la real (la de la 3ª pasada inyectaba `x` directo y por eso el PIE no mostraba el problema) |
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


## 🔴 2026-09-18 — LA LEY DE LOS FLUJOS: de "mitad negativa de S" a "cuánto llevo bajado desde el pico"
Beltrán, probando los túneles en visor: *"en el exhalar, recién se activa la velocidad rápida al llegar al final de la exhalación. Debería ir aumentando según voy exhalando. Lo mismo con el giro del túnel circular."*

### El diagnóstico
`FlowOut` integraba `neg(S)` (la parte negativa suave de la señal). Pero **al EMPEZAR a exhalar `S` está en su máximo POSITIVO** — acaba de terminar la inhalación — y no cruza cero hasta la mitad de la exhalación. O sea que **la primera mitad de cada exhalación integraba exactamente cero**: el empujón aparecía recién al final. Igual el giro del túnel, que sale del mismo `FlowOut`.

### 🔑 Por qué no alcanzaba con cambiar los números (ni la curva)
Se buscó una `f(S)` que fuera **(a)** cero en reposo, **(b)** creciente desde el primer instante de la exhalación y **(c)** no negativa. **Es imposible**: si `f` es monótona y `f(0)=0`, entonces `f(S)<0` para todo `S>0`, que es justo la primera mitad de la exhalación. Una función **sin memoria de `S`** no puede distinguir "estoy arriba y subiendo" de "estoy arriba y empezando a bajar". 🚩 **Hace falta estado.**

### La ley nueva — progreso desde el pico, normalizado por la amplitud real
Función **`StepFlows(S, DT)`** (nueva, llamada desde `Publish` entre `SetBreathOn` y `PushMPC`):
```
k   = clamp(DT / 12)                       // el pico sube al instante y decae lento
SPeak   = max(S, SPeak   + (S − SPeak)·k)
SValley = min(S, SValley + (S − SValley)·k)
amp = max(SPeak − SValley, 0.2)
v = clamp((S − SValley)/amp)   FlowIn  += v · BreathOn · DT      // progreso de la INHALACIÓN
u = clamp((SPeak   − S)/amp)   FlowOut += u · BreathOn · DT      // progreso de la EXHALACIÓN
```
- **`u` vale 0 al tope de la inhalación y 1 al fondo de la exhalación, subiendo lineal en el medio.** Es "cuánto llevo exhalado", no "dónde estoy".
- **Reposo exacto**: sin respirar `BreathOn → 0` y además `SPeak/SValley → S`, así que los flujos se congelan y todo queda en lo autorado.
- **Normaliza por la amplitud real** (`amp`), igual que `AmpEMA` hace con la señal: un suspiro y una respiración corta recorren los dos el mismo 0→1.
- Variables nuevas `SPeak` / `SValley` (cat. *Z - Estado*).

### ✅ Medido en PIE con `bFakeBreath` (período 6 s), leyendo el actor del mundo de PIE
| `S` | dónde está | `u` con la ley vieja | `u` ahora |
|---|---|---|---|
| +0,73 | tope de la inhalación | 0 | **0,00** |
| **+0,15** | **primera mitad de la exhalación** | **0** | **0,26** |
| −0,70 | fondo de la exhalación | ~1 | **1,00** |

El punto del medio es el que antes valía cero: ahí está el arreglo. `SPeak` sigue los máximos y `SValley` los mínimos (verificado: cuando sube, `S = SPeak`; cuando baja, `S = SValley`).

### Alcance del cambio (quiénes consumen los flujos)
Solo los mapeos de **VELOCIDAD/FASE**, que son los tres que tenían el defecto: **velocidad de los túneles** (`BreathPhase`), **giro del túnel circular** (`BreathRandOff`) y **giro del VoidField** (`BreathSpin`). Los mapeos de POSICIÓN leen `Signed` directo y **no cambian** (tamaño, apertura, brillo, densidad, oleaje, largo de la sombra).
⚠ El giro del VoidField (estaciones 04/05) cambia también, aunque Beltrán no lo mencionó: tenía el mismo defecto y se corrige con la misma ley. Si molesta, la perilla sigue siendo `BreathSpinOut`.
⬜ Sin visor.

## 🔌 2026-09-19 — apagado por estación (`bEnabled` + oculto)
Pedido de Beltrán: en la estación 12 (`GAL_11_PulseField`, la del latido) la respiración **no debe correr** — compite por el mismo mando y sus zonas se solapan (pecho `VDrop` 10-45 vs panza `SafeVDrop` 33-63).

**Primer intento, que NO alcanzó:** taguear el manager como actor de estación (`GALSTATION` + `GAL_0`…`GAL_10`) y confiar en que `BP_GalleryDirector_SC.GalHideAll` le apague el tick. **Medido: lo OCULTA (`bHidden=true`) pero sigue tickeando** — el log mostraba `BREATH: UMBRAL IN/OUT` en plena estación 11. El pin `bEnabled` de su `SetActorTickEnabled` está en `false`, así que el director sí lo intenta; algo vuelve a habilitar el tick y no se investigó hasta el fondo.

**La salida, que no depende de eso:** `EventTick` ahora llama **`TickBreathGated`**:
```
si (bEnabled AND NO estoy oculto) -> TickBreath   ; lo de siempre
si no                             -> BreathSleep
```
- **`bEnabled`** (`A - Umbral`, true) = apagado manual para un nivel sin director.
- **El "oculto" es la señal que SÍ se verificó que llega** (`GalHideAll` lo pone, `GalShow` lo saca en la estación que toca). En un nivel sin director el actor nunca está oculto → el manager corre siempre, como antes.
- **`BreathSleep`** actúa **una sola vez** (se guarda con `bBreathing`): baja `bBreathing` y manda `SetHapticsByValue 0` a las dos manos, para que no quede un zumbido pegado si el tick se corta en pleno umbral. No repite nada por tick, así no pisa los `PlayHapticEffect` de otras mecánicas.

✅ Verificado en PIE con `StartAt = 11`: sale `HEART: listo` y **no sale ninguna línea de BREATH**. En las estaciones 0-10 `GalShow` lo destapa y vuelve a funcionar igual que antes.
