# 🗺️ Inventario de lo que YA EXISTE y es reusable

> 🎧 **La lista de entrega de audio vive en [`docs/AUDIO-QUE-PIDE-EL-MOTOR.md`](../../../../docs/AUDIO-QUE-PIDE-EL-MOTOR.md)** (2026-08-15): las claves exactas de `SfxMap` y `AmbientMap`, los índices 0-based de `VoClips` y el banco de notas, leídos de los valores efectivos de los Blueprints. Si vas a tocar audio, empezá por ahí.

> **Leé esto ANTES de construir cualquier interacción, efecto o sonido.** El `_INDEX.md` mapea los Blueprints; este archivo mapea **assets** (input, audio, VFX, materiales, accesores del pawn). Se creó el 2026-08-03 después de perder horas construyendo desde cero cosas que ya estaban resueltas y **probadas en visor** en otra parte del proyecto.
>
> **Mantenerlo vivo:** cuando descubras un asset reusable o valides algo en visor, agregalo acá.

## 🎮🔴 INPUT — LA RECETA COMPLETA (copiar tal cual en cada stage)

> Esto es lo que hace que el trigger funcione. Los tres puntos son necesarios; con cualquiera mal, **el input no llega y no hay error de compilación ni warning**. Reconstruido el 2026-08-03 a partir de `BP_Instructions` (Breath), que es el que anda en visor.

**1. ¿DÓNDE? En el Tick, NO en BeginPlay.** Breath lo hace desde `InitRefs`, llamada **desde el Tick**. En `BeginPlay` el PlayerController puede no estar listo todavía y **`AddMappingContext` falla EN SILENCIO** (ya lo advierte `input.md` §5). Patrón: función `EnsureInput()` llamada cada Tick, guardada por un bool, que reintenta hasta que quede puesto.

**2. ¿QUÉ? `EnableInput` + `AddMappingContext` en el MISMO actor que tiene los eventos**, y verificar:
```
EnableInput(self, PlayerController)
AddMappingContext(subsystem, IMC, Priority = 1000,
                  bIgnoreAllPressedKeysUntilRelease = False,   // el DEFAULT es True y SUPRIME el input
                  bForceImmediately = True)                    // el DEFAULT es False
bReady = HasMappingContext(subsystem, IMC)   // ← Breath verifica; copiar eso, es la red de seguridad
```

**3. 🔴🔴 ¿CON QUÉ ACCIÓN? CON `IA_Shoot_Right` / `IA_Shoot_Left` DEL XRFRAMEWORK. PUNTO.**
`/Game/XRFramework/Input/Actions/IA_Shoot_{Right,Left}` es **la única acción de trigger que se entrega de verdad** en este proyecto. Un **actor suelto del nivel** la recibe sin problema: así funciona el pincel de Movement, **validado en visor**.

```
BP_BrushTool (Movement) — el patrón que anda:
  evento IA_Shoot_Right . Triggered → TrigOnR   (custom event → bTrigHeld = true)
  evento IA_Shoot_Right . Completed → TrigOffR  (bTrigHeld = false)
  y el Tick actúa mientras bTrigHeld
```
⚠ `Triggered` dispara **cada frame** mientras se sostiene → el handler tiene que ser **idempotente** (setear un bool, o guardar con un `IsValid`), nunca una acción con efecto acumulativo.

🔴 **NO sirve inventar una IA/IMC propios.** Se probó en Touch el 2026-08-03 con `IA_Attract_*` + `IMC_Touch` duplicando el molde de `IA_Continue`: el contexto se registraba (`HasMappingContext` = **true**), las 4 acciones resueltas, `EnableInput` correcto, `DefaultInputComponentClass=EnhancedInputComponent`… **y el evento no disparaba nunca.** Horas perdidas. Con `IA_Shoot_*` anda.

⚠ **Los `Mappings` de los IMC no explican nada**: `IMC_Default` e `IMC_Weapon_*` leen **VACÍOS** en este proyecto — y también en el proyecto original de Soul Charger, donde todo funciona. Las teclas llegan por el sistema de contextos por defecto de UE 5.6+ (`EnhancedInput.EnableDefaultMappingContexts=True` en `DefaultInput.ini`), no por el asset. **No diagnostiques por ahí.**

ℹ️ `IA_Continue` + `IMC_Continue` (Breath) existen y `BP_Instructions` los registra con la config de arriba, pero **ningún BP tiene el evento `IA_Continue`** — lo que Breath escucha es `IA_Shoot_Right`. El IMC quedó vestigial.

## 🎮 Detalle de los assets de input

**`IA_Continue` + `IMC_Continue`** (`Stages/Breath/Input/`) — el trigger que usan Breath, Heart y Calibration para avanzar páginas.
- `IA_Continue`: `ValueType=Boolean`, trigger **`InputTriggerDown`** → `Triggered` cada frame mientras se sostiene, `Completed` al soltar.
- `IMC_Continue`: 4 mapeos → `OculusTouch_{Left,Right}_Trigger_Click` **y** `_Trigger_Axis` (las dos variantes, click digital y eje analógico).

🔴 **La configuración del `AddMappingContext` importa MÁS que el asset.** Así lo agrega Breath (`BP_Instructions.InitRefs`) y **funciona**:
```
AddMappingContext(IMC, Priority = 1000,
                  bIgnoreAllPressedKeysUntilRelease = False,
                  bForceImmediately = True)
```
⚠ **Con los DEFAULTS no funciona**: `bIgnoreAllPressedKeysUntilRelease` viene en **True** y suprime el input hasta soltar y volver a apretar; `bForceImmediately` viene en False. Costó horas en Touch el 2026-08-03.

⚠ **`IMC_Default`, `IMC_Hands`, `IMC_Menu` e `IMC_Weapon_*` (XRFramework) tienen la lista de mapeos VACÍA** en este proyecto. `IA_Shoot_*`, `IA_Grab_*` etc. existen como assets pero **no están mapeadas a ninguna tecla**. No asumas que funcionan por venir del framework.

### 🤚 EL GRAB DEL TEMPLATE **YA ESTÁ CONSTRUIDO** — lo único que falta es el mapeo (auditado 2026-08-15)
🔴 **Corrección importante:** la línea de arriba hacía pensar que "no hay grab". **Falso.** Lo que falta es *data*, no lógica. Auditado en vivo:

| Pieza | Dónde | Estado real |
|---|---|---|
| **La cadena de grab en el pawn** | `BP_VRPawn_SC` **y** `BP_XRPawn` | ✅ **Completa**: los 4 eventos `IA_Grab_{Left,Right}_{Pressed,Released}` → `GetGrabComponentNearMotionController` → `TryGrab` / `TryRelease`. Está en NUESTRO pawn, no hay que migrar nada. |
| **`GetGrabComponentNearMotionController`** | función del pawn | ✅ Sphere trace de **`ObjectTypeQuery4`** alrededor del grip, radio `GrabRadiusfromGripPosition`, y elige el `BP_GrabComponent` **más cercano**. Ese radio **es la distancia de hover**. |
| **`BP_GrabComponent`** | `XRFramework/Blueprints/` | ✅ `TryGrab`/`TryRelease`, dispatchers `OnGrabbed`/`OnDropped`, `GrabType` (Free/Snap/**Custom** = sólo dispara eventos, sin attach), `OnGrabHapticEffect` y `bSimulateOnDrop`. `TryGrab` = `AttachParentToMotionController` + `bIsHeld` + háptica + evento. |
| **`BP_Grabbable_SmallCube`** | `XRFramework/Blueprints/` | ✅ Los "cubos" del template. 💡 **Sus grafos están VACÍOS y no tiene variables**: ser grabbable = **agregarle el `BP_GrabComponent` y nada más**. Ese es el patrón a copiar. |
| **El mapeo a teclas** | `IMC_Hands` / `IMC_Default` / `IMC_Weapon_*` / `IMC_Menu` | ❌ **TODOS vacíos** → por eso el sistema está inerte. En el template de fábrica va al **grip**; acá quedó sin mapear. |

👉 **Para usarlo con el gatillo** (decisión de Beltrán 2026-08-15: *"utilicemos el grab que ya nos funcione … con el IA enhanced que ya existe con el trigger que hemos ajustado"*): **mapear `IA_Grab_*` a las teclas de trigger en un IMC propio**, con la configuración de `AddMappingContext` que SÍ funciona (`Priority=1000` + `bIgnoreAllPressedKeysUntilRelease=False` + `bForceImmediately=True`) — los defaults suprimen el input. **Es un cambio de datos, cero riesgo de grafo.**
⚠ Dos cuidados: (1) el objeto agarrable necesita el **object type del trace** (`ObjectTypeQuery4`); (2) el trigger ya lo consumen `IA_Continue` (`IMC_Continue`, `IMC_MenuTrigger`) e `IA_Attract_*` (`IMC_Touch`) — hay que cuidar qué contextos están activos a la vez.

💡 **Y la lectura de Beltrán es la correcta**: *"quizás simplemente es hacer attach a la mano, y es más simple de lo que pensamos"*. Eso es literalmente lo que hace `TryGrab`. No hay que inventar ninguna mecánica nueva.

### 🔴🔴 NO TOCAR LOS IMC — decisión de Beltrán (2026-08-15)
> *"Ya intentamos una vez cambiar los IMC y todas esas cosas, y era supercomplicado, y no sé cómo terminamos haciendo funcionar el trigger que usamos ahora. Así que tratemos de hacerlo funcionar con el trigger que ya tenemos creado, que estamos usando para los botones y para las demás cosas."*

⚠️ **Esto invalida la ruta "mapear `IA_Grab_*` al trigger en un IMC nuevo".** El mapeo de input de este proyecto es frágil y **nadie sabe reconstruir por qué anda** el que anda — tocarlo es riesgo puro. La regla queda: **no se crean ni se editan IMC; se reusa uno de los que ya existen** (`IMC_Continue` o `IMC_MenuTrigger`), que es el gatillo que ya mueve los botones y las páginas de instrucciones en toda la obra.

### 🟢🟢 ZANJADO 2026-08-19 — "reusar `IA_Continue` + `IMC_Continue`" mezcla DOS cosas distintas
La frase corta se recuerda mal y manda a cablear el evento equivocado. Medido barriendo los `.uasset` (`grep -aoh "IMC_[A-Za-z_]*\|IA_Continue\|IA_Shoot_[A-Za-z]*"`):

| Blueprint | IMC que registra | **Evento que escucha** |
|---|---|---|
| `BP_Instructions` (Breath, **probado en visor**) | `IMC_Continue` | **`IA_Shoot_Left` + `IA_Shoot_Right`** |
| `BP_MenuButton` · `BP_SoulChoice` | `IMC_MenuTrigger` | **`IA_Shoot_*`** |
| `BP_CalibProbe` · `BP_AimBeam` · `BP_BrushTool` · `BP_HeartInstructions` · `BP_TouchInstrPanel` · `BP_DebugDirector` | — | **`IA_Shoot_*`** |
| `BP_Finale` | — | `IA_Continue` (**es el ÚNICO**, y no está probado en visor) |

👉 **Son dos piezas separadas y hay que nombrarlas por separado:**
1. **El `IMC`** es lo que hace que el gatillo físico entre al sistema. Da igual cuál de los dos, pero hay que **registrarlo con los tres flags** (`Priority=1000` + `bIgnoreAllPressedKeysUntilRelease=False` + `bForceImmediately=True`) **desde el Tick**. Esa es la parte que falla en silencio con los defaults, y es lo que de verdad se está copiando cuando se dice "la receta de `IA_Continue`".
2. **La acción que se escucha** es **`IA_Shoot_Right` / `IA_Shoot_Left`**, en el pin **`Started`** (`Triggered` dispara cada frame). `IA_Continue` existe como asset y casi nadie tiene su evento.

⚠ Y el `IMC` que se registra **no tiene que contener** la `IA` que se escucha: `BP_Instructions` registra `IMC_Continue` y escucha `IA_Shoot_*`, y anda en visor. Los mapeos llegan por el sistema de contextos por defecto de UE 5.6+, no por el asset — por eso los `Mappings` de los IMC del framework leen vacíos. **No diagnostiques por ahí.**

👉 **La receta para el grab con el gatillo actual, sin tocar input:**
1. Quien necesite el grab **agrega el contexto existente** `IMC_Continue` con la config probada (`Priority=1000` + `bIgnoreAllPressedKeysUntilRelease=False` + `bForceImmediately=True`) — copiarla del sitio que ya funciona, no de los defaults.
2. En el pawn, un evento **`IA_Continue`** engancha a la cadena de grab **que ya existe**: `Started` → `GetGrabComponentNearMotionController` → `TryGrab` · `Completed` → `TryRelease`. Son cables sobre nodos existentes, no lógica nueva.
3. El objeto agarrable lleva un **`BP_GrabComponent`** y el object type del trace (`ObjectTypeQuery4`). Nada más — el cubo del template no tiene ni una línea propia.

🔴 **DÓNDE VA EL LISTENER: en el actor de la etapa, NO en el pawn.** Principio que fijó Beltrán (2026-08-15): *"como estamos haciendo kill de los elementos de las etapas que ya pasamos, no debería pelear. Esa es la gracia de que estemos spawneando y después haciendo kill: nuestras interacciones quedan libres para lo que venga."* — el **spawn/kill es el árbitro del input**, y por eso no hace falta ningún bool de gateo entre etapas.
⚠ El corolario que importa: **una binding puesta en el PAWN nunca se mata** y quedaría viva toda la obra, rompiendo justamente esa propiedad. Por eso el grab del final **no** va en el pawn.
✅ Y se puede: **los actores de etapa reciben Enhanced Input directamente**. Comprobado en `BP_Instructions` (Breath, **probado en visor**), que tiene sus propios eventos `EnhancedInputActionIA_Shoot_{Left,Right}` en su EventGraph. Alternativa sin input propio: **pollear un bool que otro ya mantiene** — `BP_TouchInstrPanel.AnyTriggerHeld` lee `bTriggerHeld` de los `BP_AimBeam`, y `BP_BrushTool` guarda la presión del gatillo con `SetTrigPressure`. Tres caminos probados, ninguno toca un IMC.


### 🟢🟢🔴 ZANJADO 2026-09-03 — EL MAPA REAL DE TECLAS (medido asset por asset; la tabla de arriba induce a error)
Costó **seis horas y cinco pasadas de visor** montar el gatillo en un actor nuevo por leer la tabla de arriba en vez de los assets. Esto es lo medido, y manda:

| IMC | Acción que mapea | Teclas | Quién lo registra |
|---|---|---|---|
| `IMC_MenuTrigger` | **`IA_Continue`** (una sola acción, NO distingue mano) | gatillo L y R, Click **y** Axis | a mano, con la receta de `AddMappingContext` |
| `IMC_Continue` | **`IA_Continue`** (idéntico al anterior) | igual | a mano |
| `IMC_Touch` | **`IA_Attract_Left`** / **`IA_Attract_Right`** — **por mano** | gatillo de cada mano, Click y Axis | a mano |
| `IMC_Weapon_Left` / `IMC_Weapon_Right` | **`IA_Shoot_Left`** / **`IA_Shoot_Right`** — **por mano** | `OculusTouch_{Left,Right}_Trigger_Click` | 🔴 **SOLOS**: están en `DefaultMappingContexts` de `Config/DefaultInput.ini` |
| `IMC_Default` | grab (`IA_Grab_*_Pressed/Released`), `IA_Move`, `IA_Turn`, menú | — | solo (DefaultMappingContexts) |
| `IMC_Hands` | gestos de mano trackeada | — | solo (DefaultMappingContexts) |

💡 **Por eso los BPs que escuchan `IA_Shoot_*` funcionan sin registrar nada**: los dos `IMC_Weapon_*` se agregan automáticamente a cada jugador. El `AddMappingContext(IMC_MenuTrigger)` que hacen esos mismos BPs es, para el gatillo, **vestigial** — lo que dispara sus eventos es el contexto por defecto.

⚠️ **`get_properties` MIENTE sobre estos dos assets**: devuelve `mappings: []` para `IMC_Weapon_Right` y `IMC_Weapon_Left`, y el binario sí tiene la tecla dentro. Verificar con
`grep -aoh "OculusTouch_[A-Za-z_]*" IMC_X.uasset`. (De ahí salió la afirmación falsa — en la versión vieja de este archivo — de que esos IMC estaban vacíos.)

🔴🔴 **La función a COPIAR, no a reescribir: `BP_Sensor_Soul.EnsureInput`** (7 nodos, probada en gafas):
```
pc  = GetPlayerController(0)
sub = GetEnhancedInputLocalPlayerSubsystem(pc)
EnableInput(self, pc)                      <-- DOS argumentos
AddMappingContext(sub, IMC, 1000, (bIgnoreAllPressedKeysUntilRelease=False, bForceImmediately=True))
bInputReady = HasMappingContext(sub, IMC)  <-- se autoverifica
```
🔴 **`EnableInput` toma (self, PlayerController).** Escribir `(Input|EnableInput pc)` en el DSL pone el PC en el pin **`self`** (que espera el *Actor*) y deja `PlayerController` **vacío** — tipa bien porque un PlayerController *es* un Actor, **compila sin un warning, y el actor nunca entra en la pila de input**. Es el bug que costó la jornada.

🔴 **Y el `BeginPlay` de un actor del nivel corre ANTES de que exista el PlayerController** (medido: el print del actor sale 20 ms antes de `PIE: Server logged in`). `EnableInput` ahí es un no-op silencioso → hacerlo **después de un Delay**, en `Event Possessed`, o con reintento.

⛔ **Las teclas XR NO llegan al buffer clásico del PlayerController**: `IsInputKeyDown` y `GetInputAnalogKeyState` sobre `OculusTouch_Right_Trigger_{Click,Axis}` devuelven **false / 0.0 para siempre**, incluso apretando (medido: 944 frames). El gatillo del mando **solo** viaja por Enhanced Input. No hay atajo por poll de tecla.

**Para un stage nuevo:** duplicar `IA_Continue`/`IMC_Continue` a `Stages/<Stage>/Input/` (así se hizo `IA_Attract_{Left,Right}` + `IMC_Touch`), y **copiar la config de arriba**.

🔴 **2026-09-03 (tarde), medido en visor con `BP_ControllerRig`:** registrar `IMC_Touch` (Priority 1000, receta completa, `EnableInput` verificado pin a pin) y escuchar **`IA_Attract_Left/Right` en un ACTOR no disparó NUNCA** (log: `INIT` sí, `PRESS` 0 veces). La tabla de arriba dice qué mapea cada asset, **no** qué evento está probado. **Lo probado por mano en actores sigue siendo una sola cosa: `IA_Shoot_Left/Right`** (gracias a los `IMC_Weapon_*` automáticos). Para gatillo por mano en cualquier nivel: eventos `IA_Shoot_*` y listo — es lo que usan `BP_Sensor_Soul` (dibujo del Persistent), `BP_Instructions` y ahora `BP_ControllerRig`. Queda abierto POR QUÉ `IA_Attract` no llega a un actor (¿solo llega al pawn?, ¿algo del subsistema?); no gastar otra jornada ahí mientras `IA_Shoot` resuelva el caso.

## 🔊 Audio

| Dónde | Qué hay | Estado |
|---|---|---|
| `Calibration/Audio/` | 11 SoundWaves: `Pad` (68 s, **looping**, stereo), `Inhala`, `Exhala`, `Conteo`, `Trigger`, `Inicio`, `Termino`, `Tomado`, `Aparece`, `Aguanta1`, `Aguanta_2` | ✅ **probados en visor** |
| `Stages/Breath/Audio/` | `Inhale`, `Exhale`, `Umbral` | ✅ probados |
| `Stages/Touch/Audio/` | `MS_Synth`, `MS_Perc` — MetaSounds **procedurales** (sin dependencias externas) | ⚠ se llaman pero **no se comprobó que suenen** |
| 🆕 `Core/Audio/AttractingSounds/Module1/` | **`PadM1`** (5,333 s, **looping**, stereo — **exactamente 8 pasos a 90 BPM**, la base del secuenciador de Attracting) + **los 20 clips `M1S1..M1S20`** (1,33 s, one-shot, stereo; ✅ **`M1S10` ya llegó** — la nota vieja de que faltaba está superada). Cargados en `BP_Sequencer_SC` (`PadSound` + `ModuleSounds`). | 🟡 cableados en la versión limpia, falta visor |
| `Stages/Touch/Ref/` | `BP_Sequencer`, `MS_Kick`, `MS_HiHats`, `M_ON`, `M_OFF` — migrados de terceros | 🔴 **4 referencias rotas**, riesgo de cook |
| `Recursos/Audio Calibration/` | 16 archivos fuente (`.wav` + proyecto de Ableton) | fuente, fuera de Content |

🔴 **Un `AudioComponent` reproduce SU propia propiedad `Sound`.** Tener el asset en una variable del BP **no alcanza** — hay que hacer `SetSound(componente, variable)`. Ver la regla "declarado ≠ aplicado" en `gotchas.md`.
⚠ En Quest, las fuentes espacializadas tienen que ser **mono** (`audio-quest.md`). `Pad` es stereo.

## ✨ VFX / Niagara

| Asset | Qué es | Cómo se maneja |
|---|---|---|
| `XRFramework/VFX/NS_MenuLaser` | **Pointer láser** del menú | 🔴 **NO se maneja por `User.PointArray`** — ver la corrección de abajo. Duplicado a `Stages/Touch/VFX/NS_TouchBeam`. |
| `XRFramework/VFX/NS_TeleportTrace` / `NS_TeleportRing` | Arco y anillo de teleport | — |
| `XRFramework/VFX/NS_PlayAreaBounds` | Límites del área | — |
| `Stages/Breath/NS_BreathParticles` | Partículas de respiración | — |
| 🆕 `Core/VFX/NS_VoidDust` | **Las partículas del EXTERIOR** (2026-08-12): emitter `HangingParticulates` del plugin Niagara, Box Size **(10000, 10000, 600)**, SpawnRate **80** (default 50). Colocado como `FX_VoidDust` en `L_Persistent` en (0,0,250). **Placeholder a la espera de la pasada de arte de Beltrán** — es la firma visual que cierra el arco (mismo cielo al inicio y al final, §6.b). ⚠ Sprite renderer CPU; verificar en APK que la Scalability del emitter no lo apague (`fx.Niagara.QualityLevel` clampeado en Android, ver `niagara-quest.md`). | 🟡 colocado, falta visor/device |
| 🆕 `Core/VFX/NS_NeuralWeb_SC` + `BP_NeuralWeb_SC` + `M_NeuralDot_SC`/`M_NeuralLink_SC` + `MPC_NeuralWeb` | **La red neuronal de Loving** (2026-08-25): puntos + líneas conectadas por topología sembrada desde BP como arrays (`User.NodeHomes`/`PairA`/`PairB`), partículas inmortales sin fuerzas, movimiento entero en el vertex shader (Custom HLSL compartido). **Es LA receta para efectos de "geometría conectada" en Quest** (plexus sin Scratch Pad ni PAR): `SelectVectorFromArray`/`SelectIntFromArray` en modo Direct + sprite `CustomAlignment`+`FaceCameraPosition` para las líneas. Tracker: `blueprints/NS_NeuralWeb_SC.md` (con los 3 gotchas que costaron la sesión). | 🟡 verificado por captura en Simulate, falta visor |

⚠ **El pointer NO trae cursor de impacto.** `BP_Menu` lo resuelve con un `StaticMeshComponent` aparte (esfera + `XRFramework/Materials/M_VRCursor`). Si querés punta, va como componente.

### 🔴🔴 CORRECCIÓN (2026-08-04): `NS_MenuLaser` NO lee `User.PointArray`
La fila de arriba decía que se manejaba con `NiagaraSetVectorArrayValue` sobre `User.PointArray` índices 0/1. **Era falso, y costó una sesión entera de diagnóstico.** Abierto el sistema en el editor, su emitter (`TeleportColor`) es un **Beam emitter** cuya geometría sale del módulo **`Beam Emitter Setup`**:
- **`Beam Start`** = binding a `Simulation Position`, con *Absolute Beam Start* **tildado**.
- **`Beam End`** = vector **hardcodeado `(0,0,100)`**, con *Absolute Beam End* **destildado** (o sea, relativo). **Ese 100 ES el largo fijo del láser.**
- Spawn = **`Spawn Burst Instantaneous`, 5 partículas en t=0** → es un one-shot: si esas partículas mueren, no vuelve nada hasta un `Activate(bReset=true)`.

**Por qué no fallaba nada — y esto es lo insidioso:** `User.PointArray` **SÍ existe** en el sistema (tipo *Niagara Data Interface Array Float 3*), **pero nadie lo consume**. Las escrituras eran válidas y exitosas, y completamente inertes. Ni siquiera había un parámetro fantasma que delatara el problema.

**Cómo se maneja de verdad un beam entre dos puntos de mundo (resuelto y aplicado 2026-08-04):** en el módulo `Beam Emitter Setup`, `Beam Start` y `Beam End` se conectan a **parámetros de usuario** (`BeamStart` / `BeamEnd`) vía `Convert Vector to Position`, con **los dos "Absolute" tildados** (coordenadas de mundo). Desde Blueprint:
```
Niagara|SetNiagaraVariable(Vector3)  <comp>  "User.BeamStart"  <origen>
Niagara|SetNiagaraVariable(Vector3)  <comp>  "User.BeamEnd"    <fin>
```
🔴 Son **`Vector3`, NO `Position`** (por pasar por el `Convert Vector to Position`), y el prefijo **`User.`** va sí o sí aunque el panel los liste sin él. Implementado en `BP_AimBeam.UpdateBeamPoints`.

🔴 **Lección de método:** "ya existe y está probado" vale para el **asset**, pero la **forma de manejarlo** hay que verificarla en el asset, no heredarla de una nota. Esta fila estaba escrita de memoria y nadie la había confirmado.

### 🔴🔴🔴🔴 EL TIPO DEL SETTER TIENE QUE COINCIDIR EXACTO — si no, NO-OP SILENCIOSO
`Position` y `Vector3` **NO son intercambiables**. Escribir un parámetro de tipo **`NiagaraPosition`** con `SetNiagaraVariable(**Vector3**)` **no hace nada, no avisa y no rompe la compilación.**

🔬 **CÓMO VERIFICARLO EN 1 MINUTO — el nodo `GetNiagaraVariable(...)` devuelve un pin `bIsValid`:**
```
(bind (_ok _val) (Niagara|GetNiagaraVariable(Position) _fx "Beam_End"))
```
- **`bIsValid = false`** → el parámetro **no existe con ESE tipo** en el store del componente. Probá el otro tipo.
- **`bIsValid = true`** → existe, y `_val` te dice **si tu escritura llegó de verdad**.

**Medido en `LineTrace` (2026-08-04):**
| Parámetro | Tipo real | Setter correcto |
|---|---|---|
| `Beam_End` | **`NiagaraPosition`** | `SetNiagaraVariable(**Position**)` |
| `Beam_Start` | **`NiagaraPosition`** | `SetNiagaraVariable(**Position**)` |
| `Life` / `Spawn` | Float | `SetNiagaraVariable(Float)` |

> ⚠ **Cambió el 2026-08-04:** antes existía `Beam_Starts` (con **s**, tipo `Vector3f`) y **no estaba conectado a ningún input del emisor** — el beam salía siempre del origen del mundo. Se lo reemplazó por **`Beam_Start`** (singular, `NiagaraPosition`), linkeado explícitamente al input `Beam Start` de `BeamEmitterSetup001`. Ver el bloque de arriba de todo en [`niagara-quest.md`](niagara-quest.md).

⚠ **Dos parámetros del MISMO módulo pueden tener tipos distintos.** Confirmar cada uno con `GetSystemSummary` (da el tipo) o con `bIsValid`.
🔴 **Loguear `bIsValid` + el valor leído de vuelta es EL método para depurar Niagara desde Blueprint.** Loguear lo que uno *manda* no prueba nada — hay que leer lo que el sistema *recibió*. Esto habría ahorrado una sesión entera.
🔴🔴 **PERO `bIsValid=true` NO prueba que el efecto use el parámetro** — solo que existe en el store. El único cierre real es **leer los inputs del módulo** (`GetModuleInputValues`) o **medir dónde se dibuja**. Ver `niagara-quest.md`, bloque "un user parameter puede existir y no estar conectado a nada".

### 🔴🔴🔴 `SetNiagaraVariable(...)` va SIN el prefijo `User.` — con prefijo es un NO-OP SILENCIOSO
Extraído del código del pawn de Soul Charger que **sí funciona** (copiado como texto de Blueprint, 2026-08-04):
```
MemberName="SetVariableVec3"     InVariableName="Beam_End"    ← SIN "User."
MemberName="SetVariableFloat"    InVariableName="Life"        InValue=500.0
```
🔴 **Los nodos `Set Niagara Variable (…)` son métodos del COMPONENTE (`UNiagaraComponent::SetVariableVec3/Float/...`) y agregan el namespace `User.` ellos mismos.** Si vos escribís `"User.Beam_End"`, termina buscando `User.User.Beam_End` → **parámetro fantasma, escritura exitosa, efecto cero**.
⚠ **NO confundir con la familia de ARRAYS** (`SetNiagaraArrayVector`, `NiagaraSetVectorArrayValue`), que son de `NiagaraDataInterfaceArrayFunctionLibrary` y **sí llevan el nombre completo con `User.`**. Dos familias de nodos, dos convenciones opuestas — es la trampa perfecta.
**Regla:** ante un parámetro de Niagara que "se escribe bien y no hace nada", **probar el nombre sin prefijo antes que cualquier otra hipótesis.**

> 🔴 **OJO: este bloque y el de `NS_TouchBeam` de más arriba se CONTRADICEN** — uno dice que el prefijo `User.` va sí o sí y el otro que es un no-op silencioso. **La contradicción sigue sin resolver** (2026-08-15) y el `BP_AimBeam` de hoy escribe **con** prefijo. La forma de cerrarla está construida: `BP_LovingField.ProbeParams` prueba **las dos escrituras** con el pin `bIsValid` de `GetNiagaraVariable` y loguea el resultado. Sobre `NS_VoidDust` los dos dieron `false` **porque ese sistema no expone NINGÚN user parameter** (`GetSystemSummary` → `userVariables: []`), así que no probó nada; en cuanto haya un sistema con parámetros reales, esa línea de log contesta la pregunta de una vez. **Hasta entonces, no confiar en ninguno de los dos bloques: medir con `bIsValid`.**

### 🟢🟢 RESUELTO 2026-08-15 — el prefijo `User.` y la falsedad de `bIsValid`

Se construyeron 3 sistemas con un user parameter **real** (`User.Calm`, confirmado por `GetUserVariables`) y se midió en PIE. Resultado:

| Prueba | Resultado |
|---|---|
| `GetNiagaraVariable(Float)` con `"Calm"` **antes** de escribir | `bIsValid = FALSE` |
| `GetNiagaraVariable(Float)` con `"User.Calm"` **antes** de escribir | `bIsValid = FALSE` |
| `SetNiagaraVariable(Float)` con `"Calm"` (**sin** prefijo) y volver a leer | `bIsValid = TRUE`, valor **0.811109** = la calma viva del BioHub |

**Las dos conclusiones, ahora medidas y no opinadas:**

1. 🔴 **`SetNiagaraVariable(...)` va SIN el prefijo `User.`** — queda zanjada la contradicción que este archivo arrastraba. El bloque de `NS_TouchBeam` que decía *"el prefijo `User.` va sí o sí"* **es falso**. ⚠️ Eso implica que `BP_AimBeam.UpdateBeamPoints`, que hoy escribe `"User.BeamStart"`/`"User.BeamEnd"`, **está escribiendo parámetros fantasma** — es la explicación más probable de que Beltrán no viera el beam en visor. **Corregir a `"BeamStart"`/`"BeamEnd"` y reprobar.**

2. 🔴🔴 **`bIsValid` de `GetNiagaraVariable` NO es una prueba de existencia.** Lee el **store de overrides del componente**, que arranca vacío: devuelve `false` para parámetros que existen perfectamente en el sistema, y pasa a `true` recién **después de que alguien escribe**. La receta *"verificalo en 1 minuto con bIsValid"* que este archivo recomendaba **da falsos negativos**.
   👉 **Qué hacer en su lugar:** (a) para saber si un parámetro existe, `NiagaraToolset_System.GetUserVariables` sobre el **sistema**; (b) para saber si tu escritura llegó, **escribir y leer de vuelta** — eso sí funciona; (c) **no gatear las escrituras con un probe**: un nombre inexistente sólo crea un parámetro fantasma, que es inofensivo, así que **escribir siempre sale más barato que detectar**.
   💡 Además el probe hay que hacerlo **con el componente ya activado**: con `bAutoActivate=false` el store ni siquiera está inicializado.

### 🔴🔴 Para escribir un array de Niagara: `SetNiagaraArrayVector` (array ENTERO), NO el setter por índice
Verificado 2026-08-04 comparando contra el beam que **sí funciona** en el proyecto viejo Soul Charger (`Content/VRPawnSC.uasset` manejando `Content/Asset/FX/LineTrace.uasset`):
- ✅ **Lo que funciona:** **`SetNiagaraArrayVector`** (`NiagaraDataInterfaceArrayFunctionLibrary`) — recibe un **`TArray<FVector>`** y **reemplaza el array completo**, así que **siempre queda bien dimensionado**.
- ❌ **Lo que falla en silencio:** `NiagaraSetVectorArrayValue` (setter **por índice**) con **`bSizeToFit=false`** → si el array viene sin dimensionar, **la escritura se descarta sin error ni warning**.
- 🔴 **Y el daño no termina ahí:** un módulo que muestrea un array **vacío** produce **posiciones NaN**, y Niagara entonces **MATA el sistema** → `IsActive()` pasa a `false` y **no vuelve**. Síntoma: "el efecto no se ve y no hay ningún error". Diagnosticalo logueando **`IsActive` del componente**, no solo los valores que mandás.
- **Regla:** el array **nunca debe quedar vacío mientras el sistema simula** — sembralo en `BeginPlay` con valores válidos aunque el efecto todavía no se use.
- El pawn que funciona **llama `Activate` y NUNCA `Deactivate`**; el gateo visual lo hace con `SetVisibility`.

## 🧱 Esqueleto / salas / movimiento (nuevo 2026-08-11)
| Asset | Qué es | Estado |
|---|---|---|
| `Core/Rooms/BP_Room` + `Maps/Rooms/L_Room_Placeholder` | La sala vacía como **streaming sublevel**, en el origen. `SetLight(Alpha)` / `Configure(Nombre, Acento)`. | 🟡 compila, falta visor |
| `Core/Movement/BP_Walker` | Caminata por spline con rampa + bob acoplado al paso + viñeta. **Antes de construir cualquier locomoción, reusar esto.** | 🟡 compila, falta visor |
| `Core/UI/BP_Vignette` + `M_Vignette` | Viñeta de comodidad pegada a la cámara, máscara geométrica (correcta en estéreo). | 🟡 compila, falta visor |
| `Core/UI/BP_FadeSphere` | ✅ **Ya andaba: el fade a negro de la obra.** Funciones `StartFade(Alpha, Duración, Color)` y `FadeFromBlack`. **Es el patrón canónico de "malla pegada a la cámara"** — copiarlo, no reinventarlo. | 🟢 probado |

🔴 **La receta de attach a la cámara que funciona** (de `BP_FadeSphere`, reusada en `BP_Vignette`):
```
GetPlayerPawn(0) -> Actor|GetComponentByClass("/Script/Engine.CameraComponent")
Transformation|AttachActorToComponent(self, cam, "None", "SnapToTarget", "SnapToTarget", "KeepWorld", false)
```
⚠ Solo desde el **nivel persistente**. Un actor de sublevel attacheado al pawn se desattachea solo al guardar (`streaming-arch.md` §7).
⚠ Si le pones una malla alrededor de la cabeza, **apagale la colisión** o bloquea todos los line traces de los punteros.

## 🌬️ La cadena de Breath, ya integrada a la obra (2026-08-13)
`BP_Stage_Entering` (Core/Stages/) spawnea la cadena PROBADA EN VISOR de `Stages/Breath/` como la mecánica de la sala 1: `BP_Instructions` (widget 5 páginas, autónomo, spawnea el resto) → `BP_BreathSensor_V2` (tag `SensorSpawn`) → `Box_Breath` (tag `BoxSpawn`, el objeto que reacciona a la respiración). Reusable para futuros stages: el patrón "etapa spawnea el orquestador probado + poll de su bool de completitud + `ExtendTimeout` del director". ⚠ `BP_BreathStageManager` NO se usa en la obra (su cierre reinicia el nivel — es solo del test aislado).

## 🎨 Materiales reusables
- 💡🔴 **`Core/Light/M_LightShaft` + `BP_LightShaft_SC` + `SM_ShaftCone/SM_ShaftCylinder/SM_ShaftBox` — EL HAZ DE LUZ / GODRAY / LÁSER.** Ante "necesito un haz de luz, godray, sol entrando, foco, láser, spot": **YA EXISTE y es completo** (v7 2026-09-03): two-sided (se cruza caminando), `Spread` (apertura de cono sobre cualquier malla), `bLaserMode` (línea en el piso que hereda el wobble), pozo de luz y disco fuente con corrección de perspectiva al inclinar, `ShapeIndex` 0/1/2 (cono/cilindro/rectángulo), CamFade/DepthFade/dither/noise. Tracker: [[BP_LightShaft_SC]]. ⚠ El 2026-09-03 se reconstruyó desde cero por no estar listado acá — no repetir. `WobbleAmount` → 0 en haces grandes · `SourceGlowIntensity` ≤0,8 (más alto vira a rosa por el tonemapper).
- 🔦 **`Core/Light/MPC_LightShaft` + `M_BeamReceiver_SC` — MESHES BAÑADOS POR UN HAZ** (2026-09-03): el `BP_LightShaft_SC` con `bDriveMPC=true` publica su haz al MPC; cualquier mesh con `M_BeamReceiver_SC` se tiñe según qué tan dentro del cono está (láser incluido). Un solo slot Beam0 por ahora. 🟡 verificado en editor.
- ☁️ **`Core/Light/BP_CloudPlane_SC` + `M_CloudPlane_SC` + `SM_CloudPlane` — LA NUBE** (2026-09-03): plano denso con noise panneado, erosión, DepthFade y WPO esponjoso. Perillas en el actor (`CloudColor/Density/NoiseScale/Erode/CloudHeight/DepthFadeDist`). Para niebla baja, bancos de nube y velos con volumen. 🟡 sin visor.\n- 🌑🆕 **`Core/Light/BP_ShadowStudy_SC` + `M_FakeShadow_SC` + `M_ShadowSphere_SC` — OSCURIDAD SOBRE CLARO** (2026-09-04): una esfera mate sobre fondo palido con una sombra larga que barre, hecha con un **test rayo-esfera por pixel** en el material del suelo — cero luces. Es el unico efecto del toolkit que trabaja al reves de todo lo demas (que es luz sobre negro). Autocontenido: esfera y suelo en el mismo BP, el Construction Script le pasa la posicion al suelo. ⚠ Una esfera, una sombra: no es un sistema de sombras. 🟡 sin visor.
- 🖼️🆕 **`Gallery/BP_GalleryDirector_SC` + `M_GalleryProp_SC` — EL RECORRIDO DE LA GALERIA** (2026-09-04): seis estaciones en fila en `/Game/TestMeshes` (y=100000, carpeta de outliner `Galeria`, labels `GAL_*`), dos botones que viajan emparentados al director, y teletransporte del pawn al `BP_Anchor` de cada estacion mostrando solo la activa. 🔴 **La pertenencia a una estacion es por TAG DE ACTOR** (`GALSTATION` + `GAL_<n>`): una estacion puede tener cuantos actores quiera y se suma uno duplicandolo y taguandolo, sin tocar el BP. 🟢 arranque verificado en PIE; falta apretar los botones en visor.
- 〰️🆕 **`Core/Light/BP_LineField_SC` + `M_LineGlow_SC` + `SM_LineGrid` — LA LUZ DIBUJADA CON LINEAS** (2026-09-04): superficie que solo existe como 120 tiras paralelas que ondulan por WPO; la forma se lee entera por la deformacion del trazo. Indice de linea sacado de `LocalPosition.Y` (hash por linea sin UV extra), puntas disueltas, `DepthFade` de contacto y **desvanecido por distancia que es la mitigacion principal del titileo**. 🟡 sin visor — 🔴 es el efecto mas expuesto al aliasing de todos, hay que mirarlo con la cabeza en movimiento.
- ✨🆕 **`Core/Light/BP_VoidField_SC` + `M_VoidDots_SC` — PROFUNDIDAD SIN GEOMETRIA** (2026-09-04): tres cascarones CUBICOS concentricos con puntos procedurales (sin textura ni particulas). El paralaje entre capas es lo que hace sentir un vacio enorme. Puntos con jitter por celda (rompe la grilla), `Density` para dejar celdas vacias (sin eso parece ruido, no estrellas), tamaño y brillo variados y centelleo. 3 draw calls en vez de un sistema Niagara. 🟡 sin visor — y el paralaje SOLO se juzga en visor.
- 🌑🆕 **`Core/Light/BP_Ganzfeld_SC` + `M_Ganzfeld_SC` + `SM_GanzShell` — EL CASCARON SIN BORDE** (2026-09-04): la sala donde no encontras la esquina. Gradiente emisivo continuo sobre una esfera invertida de 9k tris, **opaco** (barato: escribe profundidad y mata el overdraw de atras), con **dither R2 medido** que elimina el banding de 8 bits, banda de horizonte opcional y respiracion por WPO. Tamaño en cm (`ShellRadius`/`ShellHeight`). Es el efecto 1.1 de la galeria y la sala donde van a vivir las demas estaciones. 🟡 sin visor.
- 🌫️🆕 **`Core/Light/BP_FogSlab_SC` + `M_FogSlab_SC` — NIEBLA con espesor** (2026-09-04): la losa que imita el exponential fog. Se pone donde haga falta y lo que queda detras se lechea segun la profundidad; donde corta un objeto se disuelve en vez de cortar. Perillas de color, espesor, altura, bruma por distancia, borde (rectangulo o circulo, duro o difuso), ruido y **ola por WPO** (malla propia `SM_FogSlab`, 257×257). Para capas de niebla baja, bruma de fondo y volumenes recorribles (`Mesh` = Cube). 🟡 sin visor. **No confundir con `M_FogVeil_SC`**, que es el velo simple de abajo.
- 🌫️ **`Core/Light/M_FogVeil_SC` — velo de niebla barato** (plano translúcido, máscara radial de EasyFog + DepthFade + `Density`): tapa fondos y da profundidad sin fog real. Y para polvo flotante: **`Core/VFX/NS_VoidDust` ya existe y se ve** (sprites CPU, sin variables).
- 💡 `Tests/LightShafts/M_ApertureGlow_SC` (2026-09-03) — **el disco fuente**: disco + halo radial procedural (Plane, unlit aditivo TwoSided). Vende el óculo del Panteón y la línea de una rendija; acompaña al haz. Perillas `CoreRadius/CoreSoft/CoreBrightness/HaloPower/HaloBrightness/GlowColor`. 🟡 sin visor.
- 💡 `Tests/LightShafts/M_DarkRoom_SC` (2026-09-03) — cuarto oscuro cálido para look-dev (unlit opaco TwoSided, `RoomColor`). El cuarto de prueba armado vive en `/Game/TestMeshes`, outliner `LightShaftTest`.
- `XRFramework/Materials/M_VRCursor` — cursor del puntero.
- `Core/Rooms/Materials/M_RoomFloor` — unlit con **grilla por posición de mundo** (no por UV, así la escala del mesh no la estira). Parámetros `GridSize`/`LineWidth`/`LineColor`/`BaseTone`/`Brightness`.
- `Core/Rooms/Materials/M_RoomWall` — unlit **TwoSided** con gradiente vertical. `WallHeight`/`Falloff`/`WallColor`/`Brightness`.
- 💡 **Truco reusable:** los dos exponen `Brightness` con **el mismo nombre**, así una sola llamada modula toda la sala. Y como el gradiente del muro llega a negro en `WallHeight`, **la tapa del cilindro se vuelve invisible** — se consigue "sin techo" sin recortar geometría.
- `Stages/Touch/Materials/M_TouchUnlit` — base **Unlit + Emissive** con parámetros `EmissiveColor` y `Brightness`; instancias `MI_Laser`, `MI_Bubble`, `MI_Slot`. Patrón correcto para Quest (ver `materials-vr.md`).
- `Stages/Movement/Materials/M_Brush_Light` — unlit + Fresnel, aditivo con borde suave (validado en visor dibujando).
- 🆕 `Core/Pawn/Materials/M_Hand_SC` + **`MI_Hand_SC`** (2026-09-02) — ⚪ **blanco emisivo TRANSLÚCIDO** para las manos del pawn: unlit + `BLEND_Translucent`, **single-sided**, con el **Fresnel en la OPACIDAD** (no en el emisivo) — borde denso, centro lechoso: lee como luz en el aire y no como niebla plana. Parámetros: `HandColor` · `Brightness` (1) · `Opacity` (0,35) · `EdgeBoost` (0,65) · `EdgePower` (3). **Reusable para cualquier cosa que tenga que verse como vidrio/luz sólida**; hoy lo llevan las manos del pawn (`SKM_MannyXR_*`) (no para trazos: para eso está `M_Brush_Light`, que es aditivo). ⚠ Translucidez = ~80% más de GPU por frame que masked (dato de Meta): usarlo en superficies chicas. 🟡 sin visor.
- `Core/Amoeba/Materials/M_ProtoSoul` — unlit opaco con Fresnel + pulso temporal. Parámetros: `SoulColor` (vector), `Brightness` (default 1), `Agitation` (0.25), `AgitationSpeed` (3). Lo usan las amebas Y Alma.
- `Core/Amoeba/Materials/M_SoulRing` (2026-08-14) — 🔵 **el anillo de carga**: unlit **aditivo**, TwoSided, **anillo procedural sin una sola textura** sobre un `/Engine/BasicShapes/Plane`, con **barrido angular** para que se DIBUJE girando en vez de aparecer. Parámetros: `RingColor` · `Brightness` (3) · `Progress` (0→**1.05**, ver gotcha #21) · `Radius` (0.38) · `Thickness` (0.055). **Reusable para cualquier "carga circular"** (el ring slider del timbre de la decisión #4 del guión sale de acá casi gratis).
- `Core/UI/Materials/M_BreathDot_SC` (2026-08-25) — ⚪ **el MEDIO DISCO**: unlit aditivo TwoSided sobre un `Plane`, disco recortado por la mitad con antialias analítico. Parámetros: `Radius` (0.45) · `Soft` (0.03, suavizado del borde) · **`CutDir`** (0,−1,0 — hacia dónde queda la panza) · `DotColor` · `Brightness`. Nació para los divisores y el marcador de [[BP_BreathRing_SC]]; **sirve para cualquier marca o puña sobre una línea**. 🟡 sin visor.
- ✅ **`M_SoulRing` es reusable para CUALQUIER círculo fino, no sólo para la carga** (probado 2026-08-25 en `BP_BreathRing_SC`, que lo usa para sus dos anillos). Las dos cuentas que hay que saber: el radio en cm es **`Radius_uv × 100 × escalaDelPlano`** (con `Radius`=0.4 → escala = `radio_cm/40`), y el grosor **`Thickness = ancho_cm / (100 × escalaDelPlano)`**. `Progress`=1.05 = círculo completo. Un anillo que crece/decrece **no se regenera**: se cambia la **escala uniforme del componente**, una llamada por frame.
- ✅ **Texto sobre una circunferencia (text-on-path) YA ESTÁ RESUELTO** — UMG no lo trae. El patrón vive en `Core/Doors/WBP_DoorTitle.BuildArc` (título de las puertas, arco arriba) y en `Core/UI/WBP_BreathRing_SC.AddLabel` (palabra centrada en **cualquier ángulo** alrededor del centro del lienzo, que es la versión general). Un `TextBlock` por letra, anclas y alineación al centro, posición `(R·sin a, −R·cos a)` y `SetRenderTransformAngle(a)`. **Copiar, no reinventar.**
- `Core/Sensor/MI_Sensor` (2026-08-13) — instancia de M_ProtoSoul para `BP_Sensor`: blanco tibio (0.85/0.82/0.72), Brightness 0.55, Agitation 0.06. 🔴 **Existe para que el sensor NO parezca una Proto Soul** — antes compartían look exacto y Beltrán los confundió dos veces. Si se cambia el look del sensor, mantener la distinción.

## 🔴🔴 REGLA (Beltrán, 2026-08-14): un TargetPoint aporta su TRANSFORM ENTERO, no sólo su Location

*"Los TargetPoints que definen la ubicación de las cosas: debiéramos estar usando el **transform** del TargetPoint para definir dónde se ubica cada elemento. Así, si quiero agrandar o achicar algo, lo puedo hacer directamente agrandando o achicando el TargetPoint, o rotarlo hacia donde yo quiera. **No usemos sólo location**, porque nos queda corto cuando quiera modificar cosas a nivel técnico."*
*"Hay que aplicarlo a **todo**: los objetos y los slots de Attracting, el HUD, donde ponemos el widget con los sensores, **todos** los lugares donde ponemos instrucciones, **todos** los objetos que aparecen en el mundo."*

**Qué significa en código:**
```
❌ (Game|SpawnActorfromClass Clase (Math|Transform|MakeTransform (Transformation|GetActorLocation TP)) …)
✅ (Game|SpawnActorfromClass Clase (Transformation|GetActorTransform TP) …)
```
- Con `TransformScaleMethod = MultiplyWithRoot` (el default que ya usamos), **la escala del TargetPoint multiplica la del actor** → agrandar el TP agranda el objeto. Y su **rotación** orienta el objeto, que es lo que hace falta para paneles e instrucciones que tienen que mirar al usuario.
- Para lo que NO se spawnea sino que se mueve (la ameba al `ChargeSpot`, el pawn a una parada): además de la posición, **leer escala y rotación del punto** y aplicarlas.
- 💡 El beneficio real: **el ajuste fino de la obra pasa a ser arrastrar/escalar/rotar gizmos en el viewport**, sin tocar un solo Blueprint. Es la misma filosofía que ya rige las posiciones de sala (`el mapa es la autoridad`) y los `LegTimes` del Journey.

### 📋 Auditoría de call-sites (2026-08-14) — estado del barrido
| Dónde | Qué coloca | Estado |
|---|---|---|
| `BP_Stage_Entering.SpawnPacerAt` | el ritmo guiado | ✅ ya usaba `GetActorTransform` |
| `BP_Stage_Recognizing.RecogRunBody` | `BP_Descent` (columnas) | ✅ corregido 2026-08-14 |
| `BP_Ceremony.SetSpotFromPoint` | destino de la ameba | ⬜ usa sólo Location — **falta escala/rotación del `ChargeSpot`** (sería la palanca para agrandar la ameba en la ceremonia) |
| `BP_Stage_Entering.SpawnInstructionsAt` | widget de instrucciones de Breath | ✅ ya usaba `GetActorTransform` |
| `BP_Stage_Recognizing.SpawnHeartWidget` | widget de instrucciones de Heart | ✅ corregido 2026-08-14 (tenía location+rotation, **le faltaba la escala**) |
| `BP_Instructions.SpawnBox` | la caja de Breath | ✅ ya usaba `GetActorTransform` |
| `BP_Stage_Attracting.SpawnOneSlot` | los 5 `BP_SeqSlot` | ✅ corregido 2026-08-14 |
| `BP_Stage_Attracting` → spawn del `BP_AttractDirector` | el ecosistema de burbujas | ✅ corregido 2026-08-14 |
| `BP_SoulChoice.SpawnOne` | las candidatas del Hall | ✅ corregido 2026-08-14. 🔴 **Ya usaba `GetActorTransform`, pero después PISABA la escala con un `SetActorScale3D(1.6)` hardcodeado** — el caso más traicionero de esta regla: el transform entra y una línea después se descarta. Se borró el nodo y **el 1.6 se mudó a la escala de los 5 anchors `SoulSpawn`**, así escalar el gizmo cambia el tamaño de esa candidata. |
| `BP_Stage_Surrounding.SurrRunBody` | `BP_BrushTool` | ✅ corregido 2026-08-14 |
| `BP_Stage_Hall` | sensores | ⬜ auditar |
| `BP_SoulHUD` / `BP_ProtoSoul` | anchors `TP_HudAnchor` / `TP_AmebaAnchor` | ⬜ hoy es sólo offset de posición — evaluar escala/rotación |

## 🎖️ La ceremonia de carga (2026-08-14) — reusable entero
| Asset | Qué es | Estado |
|---|---|---|
| `Core/Flow/BP_Ceremony` | **La secuencia de cierre de etapa**: desprender la ameba del HUD → viajar a un punto → dibujar anillo + subir barra → volver. Colocado en `L_Persistent`. | 🟢 verificado por log |
| `BP_ProtoSoul`: `LeaveHud` / `TravelToPoint(Target,Dur)` / `ReturnToHud(Dur)` | **Movimiento suave con smoothstep** de un actor head-locked, incluyendo el regreso a un destino que se recalcula cada tick. Reusable para cualquier objeto que tenga que "salir de la mano/HUD y volver". | 🟢 verificado |
| `BP_ProtoSoul`: `DrawRing(i,dur)` / `SeedRings(n)` / `RingColors` | Anillos acumulativos dibujados por barrido. | 🟢 verificado |
| **Patrón `ChargeSpot`** | Un `BP_Anchor` (hereda `TargetPoint`, oculto en juego) tagueado, **dentro del sublevel de la sala**. `GetAllActorsOfClassWithTag(TargetPoint, tag)` sólo ve el de la sala visible. **Es el patrón para cualquier punto autorable por sala** (ya usado por `AlmaSpawn`, `SensorSpawn`, `BoxSpawn`). | 🟢 probado |
| **Patrón "pedido por variable"** | Cuando un BP viejo tiene que disparar algo de un BP nuevo y el registro de nodos no lo ve (gotcha #17): el viejo publica un `int` en una variable propia, el nuevo lo poll-ea y devuelve el resultado llamando una función del viejo. **Bonus: el viejo sigue andando si el nuevo no existe.** | 🟢 probado |
| **Placeholder de audio data-driven** | `VoClips` (array de `SoundBase` por índice) + `ChargeSfx`: entrada vacía = **silencio + `AUDIO: falta clip X`**. Llenar el array = tener audio, cero código (decisión #8 del guión). **Copiar este patrón en el framework de audio 1.d.** | 🟢 probado |

## 🕹️ Pawn — accesores que ya existen (`BP_VRPawn_SC`)
`Class|BPVRPawnSC|GetMotionController{Left,Right}{Grip,Aim}` → devuelve el `MotionControllerComponent`. **Grip** = dónde está la mano · **Aim** = el rayo para punteros.

🔴 **NO pongas un `MotionControllerComponent` propio en un actor suelto del nivel**: solo consulta el tracking si su actor tiene *local net owner*, cosa que se cumple en el Pawn y no en un actor del nivel → `IsTracked()=false` y pose en cero, para siempre. **Leé el componente del pawn.** (Costó una tarde en Touch.)

## 💾 Persistencia
Patrón de SaveGame en `Calibration/` (`SG_CalibSession`). `bUseExternalFilesDir=True` ya está en `DefaultEngine.ini`.
⚠ El brief de Touch dice que `add_variable` por MCP no crea arrays — **es falso**: se crean pasando `container_type: "Array"`.

---

## 🗂️ Convención del Outliner (2026-08-15)
Los niveles quedaron ordenados en carpetas. **Al agregar un actor nuevo, va a su carpeta y con una etiqueta que diga qué es** — si no, en dos semanas nadie sabe qué es `BP_Anchor_C_17`.

**`L_Persistent`** (lo que vive toda la obra):
| Carpeta | Qué va |
|---|---|
| `01 Flujo` | Director · Finale · Ceremonia · Recorrido (spline) · Caminata |
| `02 Hubs` | BioHub · AudioHub · HapticHub · Archivo de almas · Constelación |
| `03 UI y HUD` | HUD del alma · Panel de resultados · Créditos · Fundido a negro · Viñeta |
| `04 Exterior` | Vacío · FX polvo del vacío · Explorador de la constelación |
| `05 Anclas/Cuerpo` | `TP_HudAnchor` · `TP_AmebaAnchor` · `Ref_CabezaSentado` · `TP_SoulHandSpot` |
| `05 Anclas/Constelacion` | `TP_ConstSpot_0..11` |
| `05 Anclas/Hall y menu` | `A_MenuRoot` · `A_MenuSpawn*` · `A_BellSpawn` · `A_SoulSpawn_1..5` |
| `06 Debug` | DebugDirector · SelfTest |
| `07 Sistema` | PlayerStart |

**Cada `L_Room_*`** usa siempre las mismas tres:
`1 Sala` (la sala y su puerta) · `2 Anclas` (todos los `TP_*`) · `3 Escena` (lo propio de esa etapa: paneles, campos, beams, botones).

**Etiquetas:** el anchor se llama por **lo que ancla**, no por su clase (`TP_DrawSpot`, `TP_ChargeSpot`, `TP_Bubble7`). Cuando un actor se repite, la etiqueta lleva **el dato que lo distingue**, no un número ciego: `CampoLuz_0 (rosa)` / `_1 (violeta)` / `_2 (ámbar)` según su `FieldIndex`, y `AimBeam_Der` / `AimBeam_Izq` según su `bIsRight`. Así el outliner responde la pregunta sin abrir el Details.

---

## 🤲 Mapa de HÁPTICOS de la obra (2026-08-15, auditado)
Todos pasan por **`BP_HapticHub`** (`HapticHover` · `HapticSelect` · `HapticHold`), nunca por la API directa. El patrón en cada BP es el mismo: variable `HapticRef` + una función chica que cachea el hub y dispara.

| Momento | Dónde vive | Pulso |
|---|---|---|
| Hover sobre un botón / salir del hover | `BP_MenuButton.HoverHaptic` | Hover |
| Confirmar un botón | `BP_MenuButton.SelectHaptic` | Select |
| Sostener el timbre | `BP_MenuButton.HoldHapticOn/Off` | Hold |
| Hover / elegir la proto ameba del Hall | `BP_SoulChoice.ChoiceHover/SelectHaptic` | Hover / Select |
| 🆕 **Tomar el sensor** (la calibración) | `BP_Sensor.SensorTakeHaptic` | Select |
| 🆕 **Hover sobre una burbuja** | `BP_SoundBubble.BubbleHoverHaptic` | Hover |
| 🆕 **Agarrar con el beam** (burbuja o botón) | `BP_AimBeam.BeamGrabHaptic` (reemplazó al log de debug) | Select |
| 🆕 **Colocar la burbuja en un slot** | `BP_SoundBubble.BubblePlaceHaptic` | Select |
| Latido reconocido en Recognizing | `BP_Stage_Recognizing.BeatFeedback` | Select |
| 🆕 **Cada fase del ritmo guiado** (4/4/4) | `BP_BreathPacer.PacerHaptic` | Hover |
| 🆕 **Arranque de cada trazo** en Surrounding | `BP_DrawCanvas.DrawHaptic` | Select |
| Invadir la esfera límite | `BP_DrawLimit.CutHaptic` | Select |
| 🆕 **La carga de la ceremonia** | `BP_Ceremony.ChargeHaptic` | Select |
| Tomar la ameba final | `BP_Finale.GrabHaptic` | Select |
| Apuntar una ameba de la constelación | `BP_ConstExplorer.ExploreHaptic` | Hover |

**Deliberadamente SIN háptico:** cruzar puertas, caminar, y el pulso por beat de los slots del secuenciador — serían vibración continua, que cansa y compite con lo que sí importa.
⚠ Casi todos pasan `bRight = true` porque el actor no sabe qué mano lo tocó. Donde **sí** se sabe (botones), va la mano real. **Afinar en visor**: si se siente que vibra la mano equivocada, hay que propagar la mano desde el beam.

## 📡 La señal biológica — el emulador ya está hecho, y el actor tiene que estar EN EL WORLD

**`BP_BioHub`** (`Core/Signals/`) es la única fuente de calma y ritmo. Trae su propio **emulador de sensor**:
`bFakeSignal` + `FakeHz` → `MaybeFake` → `FakeTick` inyecta por el mismo camino que el OSC real
(`Ingest(AddrCalm, 0.5 + 0.4·sin(2π·FakeHz·t))` y `Ingest(AddrHeart, 68 + 9·sin(...))`), y de ahí sale
`CalmSmooth` / `HeartSmooth` suavizados. **No hace falta escribir ninguna simulación nueva: se prende el flag.**

🔴 **Es un Actor: sin instancia colocada en el nivel no corre nada** (el servidor OSC se levanta en su
`BeginPlay` y el emulador vive en su `Tick`). En `MapsV2/L_SoulCharger` está colocado como **`BioHub_SC`**
en (−5355, 200, 120) con `bFakeSignal = true`. Quien necesite la señal lo busca por clase
(`GetActorOfClass` + cast) y lee `CalmSmooth`/`HeartSmooth` — así lo hace [[BP_SoulHUD_SC]].
Cuando llegue el sensor real: apagar `bFakeSignal`, nada más.

## 🪟 `M_HudWidget_SC` — el material para que un WidgetComponent quede por encima de todo
`Core/HUD/M_HudWidget_SC`. Unlit + translúcido + two-sided + **Disable Depth Test** (las manos no lo tapan,
igual que la ameba). Se asigna al componente en **`overrideMaterials[0]`**. 🔴 Sus parámetros tienen nombre
obligatorio (`SlateUI`, `TintColorAndOpacity`, `OpacityFromTexture`): los escribe el motor. Ver gotcha §200.
⚠ **No lo combines con `GeometryMode = Cylinder`**: el cilindro no dibuja a escala chica de componente (gotcha §203).

## 🎛️ Las mecánicas de interacción de la versión limpia viven en `BP_Sensor_Soul` (2026-08-24)
**Antes de construir una mecánica de mano para una etapa de `L_SoulCharger`, mirar ahí**: el sensor de la mano hábil es el contenedor único — respiración+calibración (modo 1, la receta de `BP_BreathSensor_V2` con sus valores afinados), latido por BPM del BioHub (modo 2), beam de apuntado (modo 4). Se activa con `SetStage(n)` desde `BP_Director_Story` y avisa con `OnMechDone` (cierra la etapa) y `OnBeatPulse` (un aviso por latido, libre para visuales). Tracker: `blueprints/BP_Sensor_Soul.md`.
- **`M_Beam_SC`** (`Core/Sensor/`) — material unlit emisivo con param vector `BeamColor` (blanco tibio). Hoy lo usa el cilindro del beam; sirve como material barato para cualquier trazo/línea unlit. 🟡 sin visor.
