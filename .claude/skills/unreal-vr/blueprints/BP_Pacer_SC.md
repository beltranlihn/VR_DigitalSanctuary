# BP_Pacer_SC + M_Pacer_SC — el pacer de respiración de 3 modos (Mechanics/Pacer/)

> Creado 2026-09-25 por Nico, brief `Downloads/PROMPT-NICO-PACER.md`. Un **reloj guía** de respiración (le dice al usuario cuándo inhalar), NO un sensor. Tres estéticas elegibles por `Mode` sobre **un solo reloj de fases**. Portado 1:1 de `docs/efectos-nico/pacer/pacer-glsl.js` (la fuente de verdad) + `pacers.html` (la galería SVG de referencia).
> **Estado: 🟡 material + BP compilados sin errores, 3 instancias (Aros/Órbita/Arco) en `L_PacerTest_Nico`, corrido en PIE 5 s sin un solo `Accessed None`, material validado a ojo contra la referencia. Falta el visor y el juicio de Beltrán.**

## Arquitectura: dos piezas
**El material dibuja; el Blueprint piensa.** El BP corre el reloj (Tick) y empuja `Lung/Cycle/Phase/PhasePos/Segs` al MID; el material no sabe nada de tiempo, sólo dibuja el espacio polar.

`BP_Pacer_SC` (Actor) · `M_Pacer_SC` (material) · `MI_Pacer_SC` (instancia base con los defaults del fondo oscuro; el BP crea su MID desde ella) · el `Panel` es el `Plane` del motor.

## 🔴 El material `M_Pacer_SC` es un NODO CUSTOM HLSL, no un grafo de nodos
Decisión clave, documentada porque diverge del "hacelo con Material Functions" del brief §4:
- La **fuente de verdad ES GLSL** (`pacer-glsl.js`), y el README del paquete dice explícitamente *"traducible a un Material de Unreal (**Custom HLSL node** o Material Function)"*. Porté `pacerAlpha` **tal cual** a un nodo `MaterialExpressionCustom` (HLSL ≈ GLSL: `fract`→`frac`, `mix`→`lerp`, `vec2`→`float2`, `atan`→`atan2`). Es la máxima fidelidad posible a la estética aprobada, y evita ~150 nodos frágiles armados por MCP.
- Sigue siendo **ramas por-píxel sobre un escalar `Mode`** (dentro del HLSL: `if(M==1/2/3)`), que es lo que el brief pide; **NO static switch** (un MID dinámico no puede cambiarlo, y hay que ver el modo cambiar en el panel). Si el fill molesta en visor, se hornea un MIC por modo — después, con medición.
- Propiedades: `Unlit · Translucent · Float Precision = Full` (brief §4). El centro se descarta temprano (`return 0`) → el costo vive sólo en la banda del anillo.
- **Inputs del Custom** (11): `UV, AA, Mode, Clear, Width, Lung, Cycle, Phase, PhasePos, Segs(float4)` + un pin `None` a constante (los inputs de un Custom no pueden quedar sueltos). **Output `float2(alpha, accent)`**: fuera del Custom, `Emissive = lerp(PacerColor, AccentColor, accent) · Brightness · alpha` y `Opacity = alpha · Opacity`.
- 🔴🔴 **Trampa MCP pagada:** setear el array `Inputs` de un `MaterialExpressionCustom` por `set_properties` **falla** ("ArrayAdd: elements changed alongside the size change") si cambiás tamaño y contenido a la vez. **Funciona** dando cada elemento **completo** (con el sub-struct `input`) y dejando el elemento 0 como el `None` por defecto (tamaño crece, elemento 0 idéntico → append puro).
- **Parámetros expuestos (13, los empuja el BP):** `Mode, ClearCenter, LineWidth, AAWidth, Lung, Cycle, Phase, PhasePos` (escalares animados/estáticos) · `Brightness, Opacity` · `PacerColor, AccentColor, Segs` (vectores). `Segs` se empuja con `SetColorParameterValueOnMaterials` (un LinearColor de 4 canales = a,b,e,h; la variante `Vector…OnMaterials` sólo lleva 3).

### Lo que se portó y CORRIGIÓ respecto del GLSL
- 🔴 **Los 4 arcos de fase de la Órbita** (el `uPacSegs`): el GLSL los declara pero `pacerAlpha` **nunca los dibuja** — están sólo en el SVG (`pacerOrbit`). Portados desde ahí: gap 0.004 en `u`, opacidad 0.28 pares / 0.12 impares, se saltan los segmentos ≤0.008 (holds en cero).
- 🔴 **Las marcas del Arco**: el `major` del GLSL (`step(0.5, abs(fract(u*4)-0.5)*2+0.5)`) da **siempre 1** (todas largas). Usé la versión del SVG/README: `major = 1 - step(0.5/15, abs(frac(u*4+0.5)-0.5))` → mayor cada 15 (a las 12/3/6/9).
- **Sin una sola letra** (brief §6): el SVG dibuja "Inhala/Sostén/Exhala"; NO se portó. Puro geométrico.

## El reloj de fases (BP) — portado de `createBreathClock`
Cuatro fases en bucle inhale→hold→exhale→hold. Suavizado **quíntico** `x³(x(6x−15)+10)` inlineado (🔴 **NO `SmoothStep`**, que es cúbico — se siente mecánico).
🔴 **Anti-deriva: `T -= Total`, nunca `T = 0`** (misma lección que [[BP_BreathPacer]]/[[BP_BreathRing_SC]]). El ciclo dura **exactamente `Total = a+b+e+h`** por construcción; 6-0-6-0 = **12.0 s** sin deriva.

## Registro de variables (por categoría)
- **A - Ritmo:** `Mode`(int,1) 1 Aros·2 Órbita·3 Arco (clampeado 1-3) · `Preset`(int,1) 0 Custom·1 Coherente 6-0-6-0·2 Box 4-4-4-4·3 4-7-8·4 Larga 5-2-8-2 (si≠0 el CS pisa los tiempos) · `InhaleTime`/`Hold1Time`/`ExhaleTime`/`Hold2Time`(s) · `Cycles`(int,0=∞) · `bAutoPlay`(true = arranca solo; **en la obra va false**, manda `PacerPlay`).
- **B - Forma:** `SizeCm`(60, →escala del plano cm/100, actor en escala 1) · `ClearCenter`(0.62) · `LineWidth`(0.008) · `AAWidth`(0.0035).
- **C - Color:** `PacerColor`(#E7D3C6) · `AccentColor`(#E29A72) · `Opacity`(0.85) · `Brightness`(1.0). *(defaults del SVG sobre fondo `#0B0806`.)*
- **D - Audio:** `SndInhale`/`SndExhale`/`SndHold`/`SndPulse`(SoundBase) · `PulseMode`(0 metrónomo cada `PulseInterval` · 1 sólo en cambio de fase) · `PulseInterval`(1.0) · `SfxVolume`(1.0). 🔴 Entrada vacía = silencio + `Print "AUDIO: falta clip Pacer"` (data-driven: se testea sin un solo wav). Anti-deriva en el pulso (`PulseT -= PulseInterval`). Sonidos por `SpawnSoundAttached` (uno no corta al otro). ⚠ fuentes espacializadas en Quest = **mono**.
- **E - Enlace:** `bUseExternalLung`/`ExternalLung` — puerta para atar el pacer a la respiración real (`MPC_Breath`/`BP_BreathManager_SC`); no conectada aún.
- **Estado:** `T`(instance-editable a propósito: scrubbealo y el viewport muestra ese instante, como [[BP_BreathRing_SC]]) · `PulseT · Total · CycleIndex · CurPhase · CurFramePhase · bRunning · MID`.

## Estructura de funciones (todas con prefijo `Pacer`)
🔴🔴 **`PacerApply`/`PacerAdvance` COLISIONAN con [[BP_BreathPacer]]** (tiene funciones con esos nombres exactos). El DSL las resolvía mal (§291 de BreathRing). Renombradas a **`PacerRenderFrame`** y **`PacerStepClock`** (verificado únicos con `find_node_types`). El resto (`PacerRecalc, PacerPushStatic, PacerApplyPreset, PacerPlaySnd, PacerPhaseAudio, PacerPulseAudio, PacerWrap`) no colisiona.
- `PacerRenderFrame()` — 🔴 el corazón: computa fase/lung/cycle/phasePos desde `T` (con quíntico) y empuja los 4 animados. Sin audio, sin avanzar. Lo llaman el CS (frame estático scrubeable) y el Tick.
- `PacerStepClock(Dt)` — el Tick: `T+=Dt` → `PacerWrap` → `PacerRenderFrame` → `PacerPhaseAudio` → `PacerPulseAudio`.
- `PacerWrap()` — envuelve `T` (`-=Total`), cuenta ciclo (`OnPacerCycle`), y al llegar a `Cycles` dispara `OnPacerFinished` y frena.
- `PacerRecalc()` — `Total` + `Segs` al MID. `PacerPushStatic()` — Mode/forma/colores al MID. `PacerApplyPreset()` — pisa los 4 tiempos según `Preset`.
- `PacerPlaySnd(Snd,Vol)` — IsValid→SpawnSoundAttached / else Print. `PacerPhaseAudio(NewPhase)` — al cambiar de fase: `OnPacerPhase` + sonido de fase. `PacerPulseAudio(Dt)` — metrónomo (PulseMode 0).

## API pública
Funciones (no eventos custom — necesitan parámetros tipados, que el MCP sólo da en funciones; se llaman igual): **`PacerPlay` · `PacerPause` · `PacerStop` · `PacerSetMode(int)` · `PacerSetTimes(f,f,f,f)`**. Dispatchers: **`OnPacerPhase` · `OnPacerCycle` · `OnPacerFinished`** (sin parámetro — el listener lee `CurPhase`/`CycleIndex`; el MCP no expone dispatchers con parámetros tipados). `BeginPlay`: ApplyPreset→Recalc→PushStatic→RenderFrame→ si `bAutoPlay`, `PacerPlay`.

## ⚠ Animación en el viewport sin Play
El BP maneja el reloj, así que en el **editor** (sin Play) el pacer muestra **el frame de `T` actual** (el CS lo empuja) — se autora **scrubbeando `T`**, igual que [[BP_BreathRing_SC]]. La **animación continua** corre en **PIE/visor** (Tick). Un Actor de BP no puede tickear en el viewport del editor sin C++ (`ShouldTickIfViewportsOnly`). Si Beltrán quiere animación continua en el editor, la vía es un **reloj propio en el material** (Time node) con un switch — pero eso duplica el reloj y va contra "el BP piensa"; se decide con él.

## Session log
- **2026-09-25 (Nico):** creado de cero en `Mechanics/Pacer/` (rama `fx/nico-pacer`, salida de `core/esqueleto`). Nivel `L_PacerTest_Nico` (duplicado de L_Test_Stage, despejado a vacío negro). Material como Custom HLSL (validado con un plano de prueba en modo Órbita — track/aro/cabeza/acento correctos). BP con reloj + audio data-driven + API. Colisión `PacerApply/Advance` con BP_BreathPacer detectada por lectura del grafo y resuelta con renombre. PIE 5 s: 0 `Accessed None`, 0 warnings del material. 3 instancias colocadas. Capturas en `docs/efectos-nico/pacer/cap_*.png`.

## TODO
- [ ] 🔴 **Visor + juicio de Beltrán.** Comparar a ojo contra `pacers.html` con el mismo ritmo.
- [ ] **Medir el ciclo en PIE**: 6-0-6-0 debe dar 12.0 s (es 12.0 por construcción; confirmar con medición como se hizo con el anillo).
- [ ] Rangos UIMin/UIMax de los sliders a mano en el editor (el MCP no expone esa metadata).
- [ ] Cargar los 4 wav y probar el audio (hoy imprime "falta clip"). Confirmar mono para spatialización en Quest.
- [ ] Fill-rate del translúcido a pantalla parcial en visor; si molesta, MIC por modo (static switch).
- [ ] `bUseExternalLung`: atar a `MPC_Breath` cuando se integre a la obra (lo hace Beltrán).

## Relacionados
[[BP_BreathRing_SC]] (patrón del reloj/`T` scrubeable/`bAutoPlay`/anti-deriva) · [[BP_BreathPacer]] (el antecesor; **cuidado: colisión de nombres `PacerApply/Advance`**) · `docs/efectos-nico/pacer/` (fuente de verdad: `pacer-glsl.js`, `pacers.html`, README).
