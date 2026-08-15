# BP_BreathPacer — el ritmo guiado de Entering (Stages/Breath/)

## Purpose
El rework 🔧🔧 del **Acto 4** del guión: *"la mecánica ya NO cierra por conteo"*. Aparece un **anillo que marca el tiempo** — 4 s inhalar / 4 s aguantar / 4 s exhalar, ×5 — y **avanza solo**, sea cual sea lo que haga el usuario. El sensor de respiración sigue moviendo el objeto en tiempo real; lo que cambia es **quién decide que la etapa terminó**: antes el contador de respiraciones, ahora el reloj.

🔴 **La diferencia no es técnica, es autoral.** Con el cierre por conteo, quien no lograba la respiración sostenida quedaba atrapado. Con el ritmo guiado, la etapa **dura lo que dura** y la respiración del usuario se convierte en algo que *acompaña* en vez de algo que *aprueba*. Es la regla transversal de "cero callejones sin salida".

## Status
🟡 **Construido y compilando; ciclo verificado por log en PIE.** ⬜ Falta visor (tamaño del anillo, distancia, legibilidad del texto, si el ritmo se siente natural) y los clips de audio.

## Cómo corre
```
BP_Stage_Entering.CheckBreathDone (poll 0,5 s)
  └ el sensor ya tiene bCountingEnabled (= las instrucciones terminaron)
      └ EnsurePacer → SpawnPacer (TargetPoint tag PacerSpawn) → SpawnPacerAt

BP_BreathPacer.BeginPlay: CachePacerStage · StartPacer   ← se arranca SOLO, nadie lo enciende
BP_BreathPacer.Tick → PacerStep → (si bRunning) PacerAdvance → PacerApply
    fase 0 INHALE : Progress 0 → 1.05   (el anillo se dibuja)
    fase 1 HOLD   : Progress = 1.05     (queda entero)
    fase 2 EXHALE : Progress 1.05 → 0   (el anillo se retrae por donde vino)
    al terminar cada fase → PacerNextPhase; al terminar la 2 → PacerCycleEnd (+SCountBreath)
    al llegar a Cycles → PacerFinish → NotifyPacerStage → Stage.PacerFinished() → BreathComplete → StageDone
```
🔴 **`PacerFinish` esconde el anillo y el texto pero NO destruye el actor** — lo destruye `CleanupEntering` del stage, junto con instrucciones, sensor y caja. Un solo dueño de la limpieza.

## 🔴 Por qué el pacer llama a la etapa y no al revés
Mismo motivo que [[BP_Ceremony]]: el registro de nodos del MCP **no ve las funciones de una clase de BP creada en la misma sesión**, así que `BP_Stage_Entering` no podía llamar `Class|BPBreathPacer|StartPacer`. La dependencia se invirtió:
- la etapa **spawnea** el actor (eso sí funciona: `SpawnActorFromClass` toma la clase por path, no por registro) y lo guarda como **`Actor` pelado** en `PacerRef` — sin cast, porque tampoco hay `CastToBP_BreathPacer`;
- el pacer **se arranca solo** en BeginPlay y **avisa** llamando `Class|BPStageEntering|PacerFinished` (función nueva sobre una clase **vieja** — eso sí resuelve).

Ventaja lateral: si el `TargetPoint` falta y el pacer nunca nace, la etapa **igual cierra** por el cortafuegos de 240 s del director.

## Registro de variables
| Variable | Default | Rol |
|---|---|---|
| `InhaleTime` / `HoldTime` / `ExhaleTime` | **4.0** c/u | Los tres tramos del ciclo. Son el corazón del ejercicio: cambiarlos cambia la respiración que se pide. |
| `Cycles` | **5** | Cuántos ciclos completos. El guión dice 5, y **2 para probar** — se edita en Class Defaults del BP (el actor se spawnea, así que no hay instancia que overridee). |
| `CycleIndex` / `Phase` / `PhaseT` | 0 | Estado: ciclo actual, fase (0 inhala · 1 aguanta · 2 exhala) y tiempo dentro de la fase. |
| `bRunning` / `bDone` | false | Corriendo / terminado. |
| `InhaleColor` | azul (0.25,0.6,1) | Color del anillo al inhalar. |
| `HoldColor` | ámbar (0.9,0.85,0.55) | Al aguantar — **cálido a propósito**: es el tramo que cuesta y el color lo sostiene. |
| `ExhaleColor` | verde agua (0.35,0.95,0.8) | Al exhalar (soltar). |
| `StageRef` | — | La etapa, cacheada en BeginPlay. Es la única vía de vuelta. |
| `VoClip` | vacío | 🔊 **VO 9** (la instrucción del ritmo). Vacío = silencio + `AUDIO: falta clip VO 9`. |
| `CountSfx` | vacío | 🔊 **SCountBreath**, al cerrar cada ciclo. Vacío = silencio + log. |

## 🔴 CORRECCIÓN 2026-08-14 (noche): el anillo NO se construye, se REUSA el de Calibration
**Feedback de Beltrán en visor:** *"Fíjate en el widget de la calibración, ahí ya habíamos creado un anillo que tiene marcado los distintos pasos de la respiración y que iba avanzando en infinito. **No crees cosas desde cero si ya existen**, y ya te había comentado que ahí estaba."* Tenía razón, y **no fue un descuido**: el plan decía "el radial slider ya existe en el widget de Calibration → reusar", se leyó, y se construyó uno nuevo igual.

**Lo que se reusa** (era todo un sistema ya hecho, no un widget suelto):
| Pieza | De dónde |
|---|---|
| `BreathRing` — `RadialSlider` full 360°, locked, sin handle | `WBP_CalibInstructions` |
| `RingTicks` + **`M_RingTicks`** — divisores polares (`atan2` + `Distance`), params `TickCount`/`TickWidth`/`TickLength`/`Radius`/`Color` | idem |
| **`ShowCountdownScreen(true)`** — la pantalla de respiración guiada **ya armada**: colapsa lo de calibración y muestra título + contador + anillo + divisores | idem |
| `SetBreathRing(V)` · `SetCountdown(N)` | idem |

- **Copiado a `Stages/Breath/Widget/`** como `WBP_BreathPacer` + su propio `M_RingTicks` (**dependencias cortadas**, misma regla que `BP_TouchInstrPanel`: lo del stage vive en el stage). Verificado que el brush apunta a la copia de Breath.
- **`TickCount` bajado de 4 → 3** en la copia, porque el guión pide **3 fases** (4 inhala / 4 aguanta / 4 exhala) y el anillo de Calibration implementaba **4** (aguanta/inhala/aguanta/exhala, un cuarto cada una). ⚠ **Decisión abierta para Beltrán**: si el ciclo real es de 4 fases (box breathing, como el que él construyó), se vuelve a 4 y `PacerApply` divide por 4 en vez de 3.
- **El mapeo es una línea**: `SetBreathRing((Phase + A) / 3)` — cada fase ocupa un tercio exacto, así el puntero **cambia de velocidad** con la duración real de cada tramo y siempre cae en la marca al cambiar de fase (la propiedad que hace bueno al diseño original).
- **Se fueron el `Ring` (StaticMesh) y el `Label` (TextRender)** que había construido: el anillo lo dibuja el widget y **el texto de fase se eliminó a propósito** — el anillo con sus divisores ya dice en qué tramo estás, y menos palabras es más fiel a la obra. El contador del centro muestra **los ciclos que faltan**.
- 💡 **El bloqueo del registro NO existía**: `find_node_types` no lista las funciones de un widget, pero **`create_node` con el id construido a mano SÍ las crea** (el gotcha ya estaba documentado en `BP_BreathSensor_V2.md`). No hizo falta reiniciar el editor.
- ⚠ El `BreathTitle` del widget viene con el texto de Calibration (español). **Textos in-headset van en inglés** → pendiente.

### ✅ HILO CERRADO — el widget SÍ se cachea (2026-08-14, cierre)
El log dio **`PACER: widget del anillo guiado cacheado`**: `GetUserWidgetObject(Panel)` devuelve el widget en BeginPlay y el cast a `WBP_BreathPacer` pasa, así que **`SetBreathRing` tiene un target válido**. Cero `Accessed None`.
🔴 **Por qué antes no aparecía la línea: la corrida de PIE estaba usando una compilación VIEJA del Blueprint.** El síntoma engañaba porque el resto del pacer (que no había cambiado) sí corría y logueaba normal. **Lección de método: cuando una línea de log nueva no aparece pero el resto del grafo sí corre, sospechar del binario stale ANTES que de la lógica** — `StopPIE` → `compile` → `save` → `StartPIE`, en ese orden, y confirmar que el texto del log es el de la versión nueva (por eso conviene que cada versión de un mensaje sea distinguible).
**Endurecido de todas formas** (patrón de `BP_SoulHUD.CacheWidget`): `CachePacerWidget` ahora **cuenta intentos y reintenta cada 0,2 s** vía `RetryPacerWidget`, con tope de 25 (5 s), y el bind quedó extraído a `BindPacerWidget(W)`, que además deja el widget en modo respiración (`ShowCountdownScreen(true)`). Así el cacheo no depende de que el `WidgetComponent` haya creado su widget justo en ese frame.
⬜ **Lo que sigue sin verificar es lo VISUAL**: que el anillo se vea y que el barrido de fases se lea. Eso es territorio del visor.

## Componentes
- **`Ring`** — Plane + **`M_SoulRing`** (el mismo material del anillo de carga de la ceremonia), `relativeRotation` pitch 90 para que mire al usuario, escala 0.6 ≈ **45 cm de anillo**, sin sombra, sin colisión.
  💡 **Se reusó `M_SoulRing` en vez del radial de Calibration** (`M_RingTicks`, que vive dentro de un widget UMG): el de la ceremonia ya es world-space, unlit aditivo y con **barrido angular**, que es exactamente lo que un marcapasos necesita — y esquiva todo el costo/las trampas de un `WidgetComponent` en Quest. ⚠ Si Beltrán prefiere el look con ticks del de Calibration, el cambio es de material, no de lógica.
- **`Label`** — `TextRenderComponent` con **`M_TextUnlit`** (🔴 obligatorio: el material de fábrica es Lit y la obra no tiene luces → texto negro sobre negro, ver [[BP_IntroSequence]]), yaw 180 para mirar al usuario, 42 cm debajo del anillo. Muestra **INHALE / HOLD / EXHALE** (textos in-headset en inglés, regla del proyecto).

## Dónde se autora la posición
**`TP_PacerSpawn`** — un `BP_Anchor` con tag `PacerSpawn` **dentro de `L_Room_Entering`**, en **(1310, 0, 165)** = 1,1 m delante del centro de la sala y a la altura de los ojos. Arrastrarlo mueve el marcapasos; cero código. (Es 25 cm más arriba que el `ChargeSpot` de la misma sala a propósito: no comparten momento, pero sí encuadre.)

## ⚠ Trampas pagadas
1. 🔴 **`Class|BPStageEntering|PacerFinished does not exist`** al escribir `NotifyPacerStage`: hay que **crear primero la función en el otro BP**. El orden importa cuando dos Blueprints se llaman.
2. **`Game|DestroyActor` no existe** — es `Actor|DestroyActor` (lo confirmó copiar el `CleanupBox` que ya andaba, en vez de adivinar).
3. **Nombres únicos**: todo lo del pacer lleva el prefijo `Pacer*` justamente para no repetir el bug de la ceremonia (el DSL resolviendo un nombre homónimo a otra clase).

## TODO
- [ ] 🔴 **Visor**: si 4/4/4 se siente natural, si 45 cm a 1,1 m es el tamaño correcto, si el texto se lee.
- [ ] Los clips: `VoClip` (VO 9) y `CountSfx` (SCountBreath).
- [ ] Haptics por fase (patrón "hover" suave al cambiar de tramo) cuando exista el framework 1.d.
- [ ] ¿El anillo debería también **respirar con el usuario** (grosor modulado por `BreathV` del sensor) además de marcar el tiempo? Es la pregunta autoral que deja abierta este diseño: hoy el reloj y el cuerpo están separados a propósito.

## Relacionados
[[BP_Stage_Entering]] (quien lo spawnea y a quien avisa) · `BP_BreathSensor_V2` (el que mueve el objeto; su auto-cierre por conteo quedó **apagado**) · `M_SoulRing` · [[BP_Ceremony]] (mismo patrón de dependencia invertida)

## 🆕 El anillo y su sonido, calzados (2026-08-15)
Pedido de Beltrán: *"el anillo ahora tiene que estar dividido en 3 — eso se hace con una textura que yo armaré después. Simplemente hay que lograr que la fase completa del anillo dure los 12 segundos"*.

**El anillo ya daba una vuelta completa por ciclo**: `PacerApply` manda `(Phase + A) / 3` a `SetBreathRing`, o sea 0→1 a lo largo de las tres fases. Con 4+4+4 eso son **12 s exactos por vuelta**. La división visual en tres la va a dar la textura; el valor que la alimenta ya está bien.

### 🔴 Lo que SÍ había que arreglar: el anillo derivaba
`PacerNextPhase` hacía **`PhaseT = 0`** al cambiar de fase, y eso **tira el sobrante del frame**. Cada fase duraba 4 s *más lo que sobrara de un frame*; con 15 fases en los 5 ciclos, la deriva acumulada llega a ~0,25 s a 60 fps. Contra un loop de audio de 12 s exactos, eso se **escucha** desfasado hacia el final.
**Arreglado:** `PhaseT = PhaseT − PhaseDur()` — arrastra el resto en vez de descartarlo. Se extrajo **`PhaseDur()`** (la duración de la fase actual, con piso 0,05) y ahora la usan `PacerAdvance` y `PacerNextPhase`, que además deja el grafo más corto.
⚠ En `PacerNextPhase` el `PhaseDur()` se calcula **antes** de incrementar `Phase`; si se reordena, se resta la duración equivocada.

### El sonido
- **`LBreath`** (el clip `BreathCount`, loop de 12 s) entra por **`BreathAudioOn`** colgado de `PacerShowRing` — que es lo que `StartPacer` llama justo al abrir el anillo, así que **audio y anillo arrancan en el mismo latido**. Fade in de 0,08 s: casi seco, para no correr el ataque.
- Se apaga en **`BreathAudioOff`**, colgado de `NotifyPacerStage`, con 1,2 s de fade.
- 🔴 **`PacerPlayCount` ya no dispara audio**: antes tocaba el clip **al final de cada ciclo**, que era lo correcto para un one-shot y es lo incorrecto para un loop continuo. Quedó sólo como log de vuelta completa.
- Se colgó de `PacerShowRing` y `NotifyPacerStage` porque `StartPacer` y `PacerFinish` contienen setters de bools con prefijo `b` y **no se pueden reescribir por DSL** (gotcha §62).

### Estado
🟡 Compila y los valores están verificados en el CDO (4/4/4, 5 ciclos, `LBreath`).
⬜ **No se pudo probar en PIE**: el pacer arranca después de las páginas de instrucciones, que se pasan con el gatillo — y sin visor no hay mandos. **El calce audio-anillo se juzga en el casco.**
