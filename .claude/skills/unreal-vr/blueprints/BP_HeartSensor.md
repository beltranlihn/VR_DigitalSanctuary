# BP_HeartSensor — progress tracker

- **refPath**: `/Game/SoulCharger/Stages/Heart/BP_HeartSensor.BP_HeartSensor` (clase `BP_HeartSensor_C`; en node ids es `BPHeartSensor`) · **parent**: Actor · **en nivel**: no (se spawnea en runtime, igual que el de Breath)
- **Propósito**: sensor físico agarrable del stage Heart. Es un **duplicado de `BP_BreathSensor_V2`** (ver ese tracker para la anatomía base: agarre, quietud, calibración/zona segura, hápticos, conteo) al que se le agregó la lógica de LATIDO por BPM y un VISUALIZADOR DE DEBUG de la zona segura.
- **Estado**: 🟢 gameplay Heart funcional end-to-end · 🟡 visualizador de debug construido pero con bug de anclaje (ver abajo)

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
