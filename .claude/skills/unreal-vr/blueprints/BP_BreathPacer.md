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
