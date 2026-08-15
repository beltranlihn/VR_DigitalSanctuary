# BP_HeartSensor — progress tracker

- **refPath**: `/Game/SoulCharger/Stages/Heart/BP_HeartSensor.BP_HeartSensor` (clase `BP_HeartSensor_C`; en node ids es `BPHeartSensor`) · **parent**: Actor · **en nivel**: no (se spawnea en runtime, igual que el de Breath)
- **Propósito**: sensor físico agarrable del stage Heart. Es un **duplicado de `BP_BreathSensor_V2`** (ver ese tracker para la anatomía base: agarre, quietud, calibración/zona segura, hápticos, conteo) al que se le agregó la lógica de LATIDO por BPM y un VISUALIZADOR DE DEBUG de la zona segura.
- **Estado**: 🟢 gameplay Heart funcional end-to-end · 🟡 visualizador de debug construido pero con bug de anclaje (ver abajo)

## 🔴🔴 2026-08-15 — por qué la etapa Recognizing quedaba ATASCADA (dos candados en serie)
Beltrán se quedó trabado en visor: puso el sensor en el corazón, dentro del umbral, y **no hubo pulso, ni háptico, ni sonido, ni avance**. No era el sensor: era que **todo el latido vive dentro de dos condiciones que nadie cerraba**.

```
UpdateHeartbeat (cada tick, ya agarrado)
  if IsValid(OSCRef)                 ← CANDADO 1
      BeatInterval = 60 / (OSCRef.HeartRate / 2)
      if bBreathing                  ← el umbral de quietud (este SÍ se cerraba)
          ...timer... → bBeatPulse · GrabPulse · Play(AudioHeartBeat)
              if bCountingEnabled    ← CANDADO 2
                  BeatCount++ · log "HB: Latido n/15" · MaybeFinishHeart
```

**Candado 1 — `OSCRef` era `None`.** La rama `Is Not Valid` se auto-cachea con `GetActorOfClass(BP_OSCReceiver)`, pero **no había ninguna instancia de `BP_OSCReceiver` en el nivel**, así que el cache devolvía null para siempre y el bloque entero no corría nunca. → **Arreglado**: `BP_OSCReceiver` colocado en `L_Persistent` (carpeta `02 Hubs`, etiqueta "OSCReceiver (fuente de latido)").

**Candado 2 — `bCountingEnabled` sólo lo enciende `StartBreathStage()`, y Recognizing no lo llamaba.** O sea que aun con el receptor puesto, el latido habría sonado pero **`BeatCount` no habría subido nunca** → `PumpBeats` nunca dispara `FireJump` → sin salto de columnas, sin háptico, sin `SPulse` y **sin final de etapa**. → **Arreglado**: `BP_Stage_Recognizing.PumpBeats` ahora abre con `Class|BPHeartSensor|StartBreathStage(S)` (idempotente, sólo pone el bool en true; corre cada 0,25 s con el sensor ya válido, así que se auto-cura si el sensor aparece tarde).

💡 **Lo que descartó al tercer sospechoso, sin teorizar:** el log de SU corrida mostraba `[BP_HeartSensor_C_0] UMBRAL IN` a las 18:33:18 y `UMBRAL OUT` **48 s después**. O sea `bBreathing` estaba en true casi un minuto: el umbral de quietud **no era el problema**, y no hubo que tocar `Step` (el pipeline frágil). Regla que queda: **antes de tocar el detector, buscar sus flancos en el log** — `Step` ya loguea `UMBRAL IN/OUT` y eso convierte una teoría en un dato.

⚠ Y `MaxBeatCount = 15`: con ~68 bpm el intervalo es `60/(68/2)` ≈ **1,76 s** → la etapa pide unos **26 s de latido en zona**.

## Lo específico de Heart (sobre la base de BreathSensor_V2)
- Lee BPM de `BP_OSCReceiver.HeartRate` (test fijo 75.5), lo **divide /2**, y pulsa un háptico fuerte + audio `HeartBeat` a ese ritmo cuando está en zona. Cuenta pulsos; a `MaxBeatCount` (test=4, real=15) espera `FinishDelay` (2s) y cierra el nivel. Función clave: `UpdateHeartbeat(DT)` (llamada desde EventTick en la rama agarrado+no-completo). Detalle fino de esas vars: pendiente de documentar acá (ver transcript 2026-07-20).
- Calibración apretada: `SafeTol=4`, `SafeHorizMax=20`, `SafeVDropMin` heredado. Doble háptico: `HapticAmplitude=0.08` (zumbido continuo en zona) + `GrabPulse=BeatPulseAmount` (pulso fuerte por latido).

## 🔬 Visualizador de debug de zona segura (2026-07-20) — ver memoria [[heart-debug-zone-visualizer]]
Sistema para calibrar el TAMAÑO de la zona sin testear a ciegas. Una esfera traslúcida en el punto de calibración, radio=`SafeTol`, que se pinta **verde/rojo según el test real** de zona (las 3 condiciones) y muestra números en pantalla.

### Componentes / assets nuevos
- **`DebugSphere`** (StaticMeshComponent) — malla `/Engine/BasicShapes/Sphere`, NoCollision, sombra off, `bVisible=false` default, escala 0.08 default.
- **`M_HeartDebugZone`** (`Stages/Heart/`) — material translucent+unlit+two-sided; params `Color` (Vector→Emissive) y `Opacity` (Scalar=0.3→Opacity). El tinte se hace con `SetVectorParameterValueonMaterials` sobre el componente (crea MID interno, sin var MID).

### Variables nuevas
- `bDebugSafeZone` (bool, default true) — master on/off del debug. Apagar al terminar de calibrar.
- `CalLocation` (Vector) — punto de mundo capturado al calibrar (una vez).
- `bDebugCalCaptured` (bool) — guarda para capturar `CalLocation` una sola vez (flanco).
- `bWasInZone` (bool) — estado previo de zona, para loguear solo los FLANCOS.
- ⚠ getters bool = forma larga sin `b`: `GetDebugSafeZone`, `GetDebugCalCaptured`, `GetWasinZone` (ojo casing).

### Función `UpdateDebugZone(DT)`
Llamada por cirugía desde `EventGraph` **después de `UpdateHeartbeat`** (`UpdateHeartbeat.then → UpdateDebugZone.execute`, `DT ← DeltaSeconds`). Lógica:
1. `SetVisibility(DebugSphere, bDebugSafeZone AND bCalibrated)` — oculta hasta calibrar.
2. Si `bDebugSafeZone AND bCalibrated`: captura `CalLocation` una vez; recomputa geometría head-relative (cámara viva → `horiz`, `dist`, `vdrop`, `ddist=|dist−CalDist|`); `inZone = ddist≤SafeTol AND horiz≤SafeHorizMax AND vdrop≥SafeVDropMin`; `inSphere = dist(sensor,CalLocation)≤SafeTol` (cruce geométrico); posiciona la esfera en `CalLocation`, escala `SafeTol/50`; pinta verde/rojo; PrintString pantalla `in= esf= d= cal= h= vd=` (key "DBGZONE") + log de flancos.

### 🔴 BUG conocido — esfera fija en el mundo
`SetWorldLocation(DebugSphere, CalLocation)` clava la esfera en un punto de MUNDO, pero la zona real es **head-relative** → al mover/inclinar la cabeza se separan. **Fix planeado** (ver [[heart-debug-zone-visualizer]]): anclar la esfera a `cameraLoc_actual + CalOffset` (opción A: solo traslación; opción B: + yaw). Retomar mañana.

## Pendientes
- Arreglar el follow head-relative de la esfera (prioridad, mañana).
- Documentar acá las vars de `UpdateHeartbeat` (BeatInterval/BeatTimer/BeatCount/etc.) con el mismo detalle que BreathSensor_V2.
- Subir `MaxBeatCount` 4→15. Limpiar prints `HB:`. Apagar `bDebugSafeZone` al cerrar calibración.

## Session log
- 2026-07-20: creado el visualizador de debug (componente + material + 4 vars + función `UpdateDebugZone` + cirugía en EventGraph). Compila y guarda limpio. Probado en visor: la esfera se crea y colorea, pero queda fija en el mundo al mover la cabeza. Gotcha DSL de bools registrado en `references/dsl.md`.
