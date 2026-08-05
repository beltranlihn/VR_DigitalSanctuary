# 🗺️ Inventario de lo que YA EXISTE y es reusable

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

⚠ **`IMC_Default` e `IMC_Weapon_*` (XRFramework) tienen la lista de mapeos VACÍA** en este proyecto. `IA_Shoot_*`, `IA_Grab_*` etc. existen como assets pero **no están mapeadas a ninguna tecla**. No asumas que funcionan por venir del framework.

**Para un stage nuevo:** duplicar `IA_Continue`/`IMC_Continue` a `Stages/<Stage>/Input/` (así se hizo `IA_Attract_{Left,Right}` + `IMC_Touch`), y **copiar la config de arriba**.

## 🔊 Audio

| Dónde | Qué hay | Estado |
|---|---|---|
| `Calibration/Audio/` | 11 SoundWaves: `Pad` (68 s, **looping**, stereo), `Inhala`, `Exhala`, `Conteo`, `Trigger`, `Inicio`, `Termino`, `Tomado`, `Aparece`, `Aguanta1`, `Aguanta_2` | ✅ **probados en visor** |
| `Stages/Breath/Audio/` | `Inhale`, `Exhale`, `Umbral` | ✅ probados |
| `Stages/Touch/Audio/` | `MS_Synth`, `MS_Perc` — MetaSounds **procedurales** (sin dependencias externas) | ⚠ se llaman pero **no se comprobó que suenen** |
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

### 🔴🔴 Para escribir un array de Niagara: `SetNiagaraArrayVector` (array ENTERO), NO el setter por índice
Verificado 2026-08-04 comparando contra el beam que **sí funciona** en el proyecto viejo Soul Charger (`Content/VRPawnSC.uasset` manejando `Content/Asset/FX/LineTrace.uasset`):
- ✅ **Lo que funciona:** **`SetNiagaraArrayVector`** (`NiagaraDataInterfaceArrayFunctionLibrary`) — recibe un **`TArray<FVector>`** y **reemplaza el array completo**, así que **siempre queda bien dimensionado**.
- ❌ **Lo que falla en silencio:** `NiagaraSetVectorArrayValue` (setter **por índice**) con **`bSizeToFit=false`** → si el array viene sin dimensionar, **la escritura se descarta sin error ni warning**.
- 🔴 **Y el daño no termina ahí:** un módulo que muestrea un array **vacío** produce **posiciones NaN**, y Niagara entonces **MATA el sistema** → `IsActive()` pasa a `false` y **no vuelve**. Síntoma: "el efecto no se ve y no hay ningún error". Diagnosticalo logueando **`IsActive` del componente**, no solo los valores que mandás.
- **Regla:** el array **nunca debe quedar vacío mientras el sistema simula** — sembralo en `BeginPlay` con valores válidos aunque el efecto todavía no se use.
- El pawn que funciona **llama `Activate` y NUNCA `Deactivate`**; el gateo visual lo hace con `SetVisibility`.

## 🎨 Materiales reusables
- `XRFramework/Materials/M_VRCursor` — cursor del puntero.
- `Stages/Touch/Materials/M_TouchUnlit` — base **Unlit + Emissive** con parámetros `EmissiveColor` y `Brightness`; instancias `MI_Laser`, `MI_Bubble`, `MI_Slot`. Patrón correcto para Quest (ver `materials-vr.md`).
- `Stages/Movement/Materials/M_Brush_Light` — unlit + Fresnel, aditivo con borde suave (validado en visor dibujando).

## 🕹️ Pawn — accesores que ya existen (`BP_VRPawn_SC`)
`Class|BPVRPawnSC|GetMotionController{Left,Right}{Grip,Aim}` → devuelve el `MotionControllerComponent`. **Grip** = dónde está la mano · **Aim** = el rayo para punteros.

🔴 **NO pongas un `MotionControllerComponent` propio en un actor suelto del nivel**: solo consulta el tracking si su actor tiene *local net owner*, cosa que se cumple en el Pawn y no en un actor del nivel → `IsTracked()=false` y pose en cero, para siempre. **Leé el componente del pawn.** (Costó una tarde en Touch.)

## 💾 Persistencia
Patrón de SaveGame en `Calibration/` (`SG_CalibSession`). `bUseExternalFilesDir=True` ya está en `DefaultEngine.ini`.
⚠ El brief de Touch dice que `add_variable` por MCP no crea arrays — **es falso**: se crean pasando `container_type: "Array"`.
