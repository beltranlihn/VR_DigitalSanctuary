# BP_BreathSensor_V2 — progress tracker

- **refPath**: `/Game/SoulCharger/Stages/Breath/BP_BreathSensor_V2.BP_BreathSensor_V2`  ·  **parent**: Actor  ·  **en nivel**: no (se spawnea en runtime, ver abajo)
- **Propósito**: sensor físico (prop agarrable) + detector de respiración fusionados en un solo actor. Es la arquitectura VIGENTE — superó al split `BP_BreathProbe`/`BP_BreathSensor` documentado en `BP_BreathProbe.md` (ese tracker quedó desactualizado, ver nota al final).
- **Estado**: 🟢 detección validada (heredada) · 🟢 sistema de conteo de respiraciones (2026-07-20, ver Session log)

## Cómo se coloca en el nivel
NO está pre-colocado. `BP_Instructions` lo **spawnea** en la página 2 (`SpawnSensor`, sobre un `TargetPoint` tag `SensorSpawn`) y lo deja vivo cuando el widget se autodestruye al terminar la página 5. Se auto-adjunta a la mano que lo toca por proximidad (`TouchRadius`), sin botón de grab.

## 🔑 Registro de variables (auditado desde `Step` el 2026-07-20 — usar ESTO, no re-leer el grafo)

### Agarre / adjuntado
- `AttachedController` (MotionControllerComponent) — el mando al que se pegó el sensor; TODA la geometría de `Step` se lee de acá.
- `LeftGrip` / `RightGrip` — refs a los grips del pawn (cacheados en `AcquireControllers`).
- `bAttached` (bool) — ya se pegó a una mano.
- `bIsRightHand` (bool) — mano derecha (define el `Hand` del háptico).
- `TouchRadius` (float) — distancia de proximidad para auto-adjuntarse.

### Quietud (still) y tracking
- `LinSpeed` / `AngSpeed` (float, estado) — velocidad lineal/angular **suavizada con ataque-rápido/caída-lenta** (EMA con `StillTau`, pero `max(instantáneo, EMA)` para detectar movimiento en 1 frame).
- `StillLinThreshold` (8 cm/s) / `StillAngThreshold` (25 °/s) — umbrales de "quieto". `bStill = LinSpeed<lin AND AngSpeed<ang`.
- `StillTau` (0.3) — tau del suavizado de velocidad.
- `bTracked` = ambos bool de retorno de `GetLinearVelocity`/`GetAngularVelocity` (mando despierto). Quietud efectiva = `bStill AND bTracked`.

### Señal de respiración (band-pass sobre la inclinación)
- Señal cruda = una de las 3 componentes Z de los ejes del mando (`Forward.Z`/`Right.Z`/`Up.Z`), elegida por `LockedAxis` (**FIJO, sin auto-selección** — ver `BP_BreathProbe.md` test 16-17).
- `SlowV` / `FastV` (float, estado) — dos EMA de la señal cruda (`TauSlow` / `TauFast`). `BreathV = FastV − SlowV` = band-pass (la oscilación de respiración centrada en 0). **Solo corre si quieto+trackeado; si no, reseed** (`SlowV=FastV=raw`, `BreathV=0`) → mata transitorios.
- `TauSlow` (90) / `TauFast` (0.4) — taus del band-pass. `TauSlow` alto sostiene el "aguante" ~32 s.
- `Amplitude` (float, estado) = EMA de `|BreathV|` con `TauAmp` (4) → mide cuánta oscilación hay. **Compuerta de amplitud del umbral.**
- `MinAmplitude` (0.003) — piso de `Amplitude` para permitir entrar al umbral.
- `BreathV`/`RunExtreme`/`DirFrac` — usados por `DetectBreathDir` (el ZigZag que setea `bInhaling`; ese detector vive en la función `DetectBreathDir`, no en `Step`).

### 🎯 Calibración + zona segura (LO QUE SE AJUSTA para "no entrar tan fácil")
Geometría, todo relativo a la **cámara/cabeza** (`GetPlayerCameraManager`):
- `horizDist` = distancia horizontal (XY) cabeza→sensor. `VDrop` = cámara.z − sensor.z (cuánto está el sensor por debajo de la cabeza). `dist` = distancia 3D total cabeza→sensor.
- `CalDist` (float, estado) — el `dist` capturado al calibrar (log: ~49cm). Se setea en runtime, el default no importa.
- `bCalibrated` (bool, estado) — ya calibró. La calibración corre mientras estás en zona segura + quieto durante `CalHold` s continuos.
- `CalHold` (4.5) — segundos que hay que aguantar en zona para calibrar.
- `CalTimer` (estado) — acumulador de la calibración.
- `CalGap` (2) — cooldown tras calibrar; `CalCooldown` (estado) cuenta hacia 0. Mientras `CalCooldown>0`, el umbral NO puede activar (evita entrar de una apenas calibrás).
- **Zona segura PRE-calibración** = `horizDist ≤ SafeHorizMax` **AND** `SafeVDropMin ≤ VDrop ≤ SafeVDropMax`.
- **Zona segura POST-calibración** (la que gatea el umbral en juego) = `|dist − CalDist| ≤ SafeTol` **AND** `horizDist ≤ SafeHorizMax` **AND** `VDrop ≥ SafeVDropMin`. 🔴 **OJO: post-calibración NO chequea `SafeVDropMax`** — solo el mínimo.
- **`SafeTol`** (⚠ era 15, **ajustado a 9** el 2026-07-20) — tolerancia de distancia a la cabeza. **Es la palanca #1 para acotar**, porque es RELATIVA a tu calibración (se adapta a cada persona). El muslo sentado está ~13cm más lejos de la cabeza que el abdomen → con 15 caía dentro (entraba fácil), con 9 queda afuera.
- **`SafeHorizMax`** (era 33, **ajustado a 28**) — tope de distancia horizontal. El muslo está más adelante que el abdomen.
- **`SafeVDropMin`** (24) — el sensor tiene que estar al menos 24cm por debajo de la cabeza. `SafeVDropMax` (62) — solo pre-cal.
- 💡 **Si el muslo sigue entrando:** el discriminador de fondo es que el muslo está MÁS ABAJO (mayor `VDrop`) que el abdomen. La zona post-cal NO usa `SafeVDropMax` → el fix estructural (cirugía) sería agregar `VDrop ≤ SafeVDropMax` a la zona post-cal y bajar `SafeVDropMax` a ~50. No aplicado aún (primero se probó apretar `SafeTol`/`SafeHorizMax`).

### Umbral de dos capas (lo que consume el gameplay)
- `bInThreshold` (crudo/por-frame, implícito en `Step`) = `bStill AND bTracked AND zonaSegura AND Amplitude≥MinAmplitude AND CalCooldown==0`.
- `bBreathing` (bool, **el estado confirmado con debounce**) — entra tras `ActivateDelay` (0.5) s continuos en umbral (`InTimer`), sale tras `DeactivateDelay` (0.5) s continuos fuera (`OutTimer`). Al entrar: `"UMBRAL IN"` + fade-in del audio Umbral. Al salir: `"UMBRAL OUT"` + fade-out. Nota: una vez `bBreathing=true`, se mantiene aunque salgas de la zona (`or bBreathing zonaSegura`) — la zona solo gatea la ENTRADA.
- `bInhaling` (bool) — fase de inhalación del ZigZag (la setea `DetectBreathDir`). **Es la señal que consume el conteo** (`UpdateBreathCount`) y `Box_Breath`.
- `InTimer` / `OutTimer` (estado) — debounce de entrada/salida.

### Hápticos
- `GrabPulse` (float, estado) — pulso de agarre/conteo: se setea a 0.2 (`PlayGrabHaptic`) y decae con DT. Mientras >0 → háptico a amplitud 1.0.
- `bHapticOn` (bool) — el háptico está sonando (para cortarlo al salir).
- `HapticAmplitude` (0.25) — amplitud del háptico continuo mientras `bBreathing`. `SetHapticsByValue(Frequency=0)` = zumbido nativo del Quest (ver `gotchas.md` §háptico).

### Estado del conteo (NUEVAS, sección aparte abajo)
`ContinuousInhaleTime` `MaxBreathCount` `BreathCount` `InhaleHoldTimer` `bHoldCounted` `bCountingEnabled` `bStageComplete` — documentadas en "Variables — NUEVAS".

## Estructura de `Step(DT)` — orden del pipeline (para no re-leer)
`Step` es UNA función larga, frágil (**no reescribir desde el read, es lossy** — cirugía de nodos). Orden:
1. Lee ejes del mando (`Forward/Right/Up . Z`) y velocidades (`GetLinear/AngularVelocity`, con sus bool de tracking).
2. Suaviza `LinSpeed`/`AngSpeed` (ataque rápido/caída lenta) → `bStill`. `bTracked` = ambos bool de velocidad.
3. Calcula geometría cabeza→sensor: `horizDist`, `VDrop`, `dist`, `|dist−CalDist|`.
4. Evalúa zona segura (pre y post-cal) y selecciona la señal cruda del eje `LockedAxis`.
5. **Band-pass**: si `bStill AND bTracked` → actualiza `SlowV`/`FastV`/`BreathV`; si no → reseed a 0.
6. Actualiza `Amplitude` (EMA de |BreathV|).
7. **Si NO calibrado**: acumula `CalTimer` mientras (quieto AND zona) → al llegar a `CalHold` captura `CalDist`, `bCalibrated=true`, arranca `CalGap` cooldown, pulso háptico, log `CALIBRATED`.
8. **Si calibrado**: baja `CalCooldown`; evalúa umbral (`bStill AND (bBreathing OR zona) AND Amplitude≥MinAmplitude AND cooldown==0`) con debounce `InTimer`/`OutTimer` → setea `bBreathing` + logs UMBRAL IN/OUT + fades de audio.
9. Llama `DetectBreathDir` (ZigZag → `bInhaling`).
10. Decae `GrabPulse`; aplica háptico (continuo si `GrabPulse>0` o `bBreathing`, apaga si no).

## Variables — NUEVAS (sistema de conteo, 2026-07-20)
- `ContinuousInhaleTime` (float, **instance-editable**, default **4.0**) — segundos continuos de `bInhaling` para contar una respiración.
- `MaxBreathCount` (int, **instance-editable**, default **5**) — objetivo de la etapa.
- `BreathCount` (int, estado) — contador actual.
- `InhaleHoldTimer` (float, estado) — acumulador de tiempo continuo inhalando.
- `bHoldCounted` (bool, estado) — evita contar más de una vez la misma sostenida (se resetea al soltar `bInhaling`).
- `bCountingEnabled` (bool, estado, default false) — gate: no cuenta hasta que `StartBreathStage()` lo activa.
- `bStageComplete` (bool, estado, default false) — true cuando `BreathCount >= MaxBreathCount`. Gatea `Step` (el sensor deja de procesar) y fuerza `bBreathing`/`bInhaling` a false.

## Funciones NUEVAS
- **`StartBreathStage()`** — `bCountingEnabled = true`. La llama `BP_Instructions` (`UpdateFade`) en el instante exacto en que terminan las 5 páginas del widget (antes de `SpawnBox`).
- **`UpdateBreathCount(DT)`** — el timer/contador. Si `bCountingEnabled AND bInhaling`: acumula `InhaleHoldTimer += DT`. Si no: resetea `InhaleHoldTimer=0` y `bHoldCounted=false`. Al cruzar `InhaleHoldTimer >= ContinuousInhaleTime` (una sola vez por sostenida, guardado por `bHoldCounted`): `BreathCount += 1`, imprime `"SN 3: Respiracion N/MaxN"` (log + pantalla, sin gate de `bDebug` — este BP no tiene esa variable), dispara `PlayGrabHaptic()` (reusa el pulso de agarre existente — pedido explícito del usuario, no se creó un pulso nuevo), y si `BreathCount >= MaxBreathCount` llama `CompleteBreathStage()`.
- **`CompleteBreathStage()`** — `bStageComplete=true`, `bBreathing=false`, `bInhaling=false`, `SetActorHiddenInGame(true)`, `SetActorEnableCollision(false)`. El sensor "desaparece y deja de funcionar" tal como lo pidió el usuario.

## Cirugía en `EventTick` (sin reescribir el grafo)
La rama `else` (sensor agarrado) pasó de `(CallFunction|Step DeltaSeconds)` a:
```
(elif (not bStageComplete)
  (CallFunction|Step DeltaSeconds)
  (CallFunction|UpdateBreathCount DeltaSeconds))
```
Un `Branch` + `NOT bStageComplete` nuevos, insertados quirúrgicamente entre el `IfThenElse` de agarre existente y la llamada a `Step` (que se redirigió a través del nuevo Branch). `Step` en sí **no se tocó** — sigue siendo el pipeline frágil de detección, intacto.

## Gotcha nuevo de esta sesión
`find_node_types` con filtro específico (`"BPBreathSensorV2|GetStageComplete"`) **no encontró** el getter cross-clase de una variable recién agregada, ni siquiera tras compilar y guardar el asset — el índice de búsqueda del MCP no se refresca en caliente para miembros nuevos de otra clase. `create_node` con el type_id construido a mano (`Class|BPBreathSensorV2|GetStageComplete`, mismo patrón que los getters ya confirmados) **sí funcionó** igual. Lección: si `find_node_types` no encuentra un miembro que sabés que existe (recién creado), no asumir que no existe — probar `create_node` directo con el patrón conocido antes de descartarlo.

## Nota sobre `BP_BreathProbe.md`
Ese tracker asumía que el pipeline validado se iba a extraer a `BP_BreathSource`/`BP_BreathChannel` y que `BP_BreathProbe` se tiraría. Eso NO pasó: la evolución real fue fusionar sensor+detector+calibración+hápticos directo en `BP_BreathSensor_V2` (este archivo). `BP_BreathProbe.md` sigue siendo valioso como **bitácora de los 26 tests que descubrieron el modelo de señal** (ZigZag, ventana de armado, band-pass adaptativo, etc. — todo eso se heredó conceptualmente), pero su sección de arquitectura/estado está desactualizada. Consultarlo por el "por qué" del detector, no por el "dónde está el código hoy".

## Instrumentación de captura de datos de calibración (2026-07-22)
Para levantar data etiquetada (ground-truth) y tunear umbrales con datos reales.
- **Var `bCalibLog`** (bool, instance-editable). Cuando true, loguea una línea CSV por frame. **Default puesto en `true` para el test — VOLVER A `false` al terminar** (spamea el log si queda ON).
- **Función `CalibLog(DT)`** (auto-gateada por `bCalibLog`): imprime al LOG (no a pantalla) una línea con tag **`BRLOG,`** y campos: `t` (GetGameTimeInSeconds), `L=`/`R=` (valor analógico 0-1 de los gatillos izq/der vía `GetInputAnalogKeyState` con FKeys `MotionController_Left/Right_Trigger` — **no necesita EnableInput**, lee el estado crudo de la tecla), `br=`/`in=`/`cal=` (bBreathing/bInhaling/bCalibrated), y las señales `amp=`(Amplitude) `bv=`(BreathV) `sv=`(SlowV) `fv=`(FastV) `ls=`(LinSpeed) `as=`(AngSpeed) `re=`(RunExtreme) `df=`(DirFrac).
- **Label = trigger de la mano libre** → var `bLabel`. 🔴 **Cómo leer el gatillo (aprendido a la mala):** OpenXR NO popula los FKeys legacy → `GetInputAnalogKeyState("MotionController_Left_Trigger")` da **0 siempre**. Los **value getters** `Input|EnhancedActionValues|GetIA_X` también dieron 0 (el IMC del arma no está activo fuera del arma; los curls de dedo son hand-tracking). **Lo que SÍ funciona = los EVENTOS Enhanced Input** `Input|EnhancedActionEvents|IA_Shoot_Left` (los mismos que usan las instrucciones para el trigger-hold): `Triggered → SetbLabel(true)`, `Completed → SetbLabel(false)`. Requiere que el actor reciba input → **`AutoReceiveInput=Player0`** en el CDO (el sensor no lo tenía). Verificado: `lbl=` alterna limpio.
- **Cirugía en tick:** `CallFunction|CalibLog` insertado DESPUÉS de `UpdateBreathCount` (su `then` estaba libre), `DT ← DeltaSeconds`. Step/UpdateBreathCount intactos.
- **Análisis:** leer `VR_Test/Saved/Logs/*.log`, grep `BRLOG`, parsear CSV. Ej1 (reposo vs respirando) → distribución de `amp`/`ls`/`as` por estado → umbral de reposo con histéresis. Ej2 (inhale vs exhale) → forma/timing de `bv`/`re`/`df` → tunear ZigZag y medir lag en cambios bruscos.

## Session log (fix 2026-07-20, misma sesión)
- Usuario reportó: "queda estancado en la página 4, el trigger no avanza". Auditoría completa de `EventGraph`/`UpdateBreathCount` de este BP: **intactos, sin relación con el trigger-hold** (páginas 1-4 usan Enhanced Input `IA_Shoot_Left/Right`→`bTrigHeld`→`THold`, nada de eso se tocó esta sesión). El único riesgo real estaba en `BP_Instructions.UpdateFade` (ver ahí): la llamada nueva a `Sensor.StartBreathStage()` podía cortar la cadena de ejecución en silencio si `Sensor` no era válido en ese instante, dejando `SpawnBox`/`DestroyActor` sin ejecutarse — **eso sí encaja con "queda estancado sin avanzar"** en la ÚLTIMA página (case 4 interno), no en la 1-4. Blindado con `IsValid` (ver `instructions-widget.md`). Si el problema persiste y es realmente en la página de "inflar/desinflar panza" (case 3), no hay causa estructural encontrada — pedir más detalle del síntoma exacto.

## Session log — ajuste de calibración (2026-07-20)
- Usuario: "la calibración está muy abierta, con la mano en el muslo entra muy fácil al umbral". Auditado `Step` (registro de variables arriba). Causa: la zona segura post-cal es holgada y NO filtra por altura (`SafeVDropMax` solo pre-cal). **Fix aplicado (solo valores, sin tocar grafo):** `SafeTol` 15→9 (palanca #1, relativa a la calibración), `SafeHorizMax` 33→28. En CDO + compile + save (el sensor se spawnea → hereda del CDO, no hay instancia de nivel). Fallback estructural si no alcanza: agregar `VDrop≤SafeVDropMax` a la zona post-cal (ver 💡 en el registro de variables).

## Session log
- 2026-07-20: agregado el sistema de conteo de respiraciones (contador 0→`MaxBreathCount`, sostenida de `ContinuousInhaleTime` s, pulso háptico por incremento, auto-ocultamiento + stop al completar). Ver también `Box_Breath.md` y `BP_BreathStageManager.md` (nuevo) para el resto de la cadena (esfera a escala 0, fade a negro, reinicio de nivel). Smoke-test en PIE Simulate: compila limpio, `BeginPlay` corre sin errores nuevos (no se pudo probar la detección real de respiración desde el editor — requiere el usuario en el visor).
