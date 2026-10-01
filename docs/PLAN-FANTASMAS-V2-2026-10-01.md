# Plan v2: los FANTASMAS de las instrucciones

> 2026-10-01. Rediseño a partir de lo que Beltrán quiere ver en cada instrucción.
> Reemplaza a [`PLAN-FANTASMAS-2026-09-30.md`](PLAN-FANTASMAS-2026-09-30.md) (v1): se conservan el formato de datos, el grabador por mirada y el reproductor entrecortado. Cambian el ancla, lo que lleva cada mano y dónde vive cada fantasma.
> Tracker: [`blueprints/BP_GhostPlayer_SC.md`](../.claude/skills/unreal-vr/blueprints/BP_GhostPlayer_SC.md).

## 1. Las 7 instrucciones

| ID | Qué se ve | Ancla | Vive en | Desaparece cuando | Lo apaga |
|---|---|---|---|---|---|
| `GHOST_BELL` | Una **mano** se acerca al timbre y lo aprieta | el timbre (sigue a `hall_bell`) | Test_Hall | el usuario apoya la mano | `BP_HallDirector_SC` |
| `GHOST_TAKE` | Una **mano** se acerca al sensor | el sensor (sigue a `hall_sensor`, solo posición: el sensor gira) | Test_Hall | lo toma (`HallGrab`) | `BP_HallDirector_SC` |
| `GHOST_PICK` | Un **mando** se acerca a la proto ameba y gira un poco para mostrar que aprieta el gatillo | la ameba central | Test_Hall | elige (`HallTickPick`) | `BP_HallDirector_SC` |
| `GHOST_BREATH` | El **sensor** al frente se acerca al estómago e inhala y exhala rápido, varias veces | la cabeza | Test_Entering | entra al umbral por primera vez | la etapa |
| `GHOST_HEART` | El mismo gesto, al pecho | la cabeza | Test_Heart | entra al umbral por primera vez | la etapa |
| `GHOST_ATTRACT` | El **mando** muestra el gatillo, apunta a una esfera y la arrastra; después apunta al **botón SAVE** (que se ve en la otra mano) y aprieta | colocado en el nivel | Test_Sequencer | la primera esfera llega a un slot (el evento que ya cierra la instrucción) | `BP_Sequencer_SC` |
| `GHOST_DRAW` | Frente al usuario, el **mando** usa la **paleta** (en la otra mano) y dibuja un trazo corto | colocado en el nivel, frente al asiento | L_TBTest_SC | primer trazo | `BP_TBDirector_NC` |

- Las celdas de la Obra **son** los niveles de test, así que un fantasma colocado en su nivel de test queda en la experiencia sin pasos extra. **No llevan tag `TestOnly`.**
- `DA_Ghost_Loving`, `DA_Ghost_Save` y `DA_Ghost_Share` quedan sin uso. No se borran sin que Beltrán lo pida.

## 2. Aspecto
- **Las mismas mallas de la experiencia:**
  - mano: `SKM_MannyXR_right`, la misma del pawn, quieta en una pose abierta;
  - mando: `SM_QuestCtrl_Body_*` con su gatillo en la bisagra;
  - sensor: el cuerpo de `BP_BioSensorArt_SC`;
  - SAVE: la malla de `BP_SaveMelody_SC`, en la mano izquierda (7 cm, escala 0,5, como en `BP_SeqRig_SC`);
  - paleta: las mallas de `BP_DrawPalette_SC`, en la mano izquierda;
  - esfera: la de `BP_SoundOrb_SC`.
- **Material:** translúcido suave, blanco azulado (`GhostColor`, `GhostOpacity`).
- **Solo el gatillo** lleva color y brillo (`TriggerColor`, `TriggerGlow`): se hunde en su bisagra y brilla más mientras está apretado.
- **Movimiento tipo gif:** salta de pose en pose a `StepHz` 11 y repite en bucle con una pausa (`LoopGap`). Los ecos quedan como perilla (`EchoCount`, 0 = gif puro); se deciden en la primera prueba, mirando.
- Ojo: la mano real del usuario también es blanca translúcida (`MI_Hand_SC`). El fantasma se distingue por el tinte azul y por moverse a saltos.

## 3. El fantasma en el nivel (lo que Beltrán mueve)
- **Un `BP_GhostPlayer_SC` por instrucción**, colocado en su nivel, con su toma elegida en la instancia (`Take` = referencia directa al DA, sin búsqueda por nombre).
- **En el editor, sin Play,** muestra la toma como una cronofotografía:
  - el recorrido entero, tenue;
  - una pose sólida en `PreviewTime` (slider 0-1);
  - el trazo y la esfera también, cuando la toma los tiene.
  - Mover el actor mueve la demostración entera.
- **Ancla en el nivel** (Bell, Take, Pick, Attract, Draw): el actor **es** el ancla.
  - `FollowTag`: si el director mueve el objeto real en el juego (el timbre y el sensor suben o bajan a la altura de los ojos del usuario), el fantasma lo acompaña y conserva la distancia que quedó en el editor.
- **Ancla en la cabeza** (Breath, Heart): en el editor, el origen del actor representa los ojos de un usuario sentado, solo para previsualizar. En el juego se ancla a la cabeza real más el yaw del pawn, como en v1.
- **Carga:**
  - la previsualización del editor se borra al dar Play;
  - en el juego no hay mallas hasta que la etapa llama `Play()`, y `Stop()` las quita al terminar de disolverse. Así se respeta la regla de cargar por etapa.
- **API:** `Play(bMirror)` · `Stop()` · `bPlaying` · `LoopCount` (para que Alma ayude a los 2 bucles).

## 4. Lo que no se graba: se reconstruye
- **Trazo fantasma** (`GHOST_DRAW`): el recorrido de la punta del pincel mientras el gatillo está apretado.
  - Se usa la misma punta que el pincel real.
  - Crece mientras se dibuja y se desvanece al final de cada bucle.
- **Esfera fantasma** (`GHOST_ATTRACT`):
  - reposa en `OrbRest`, un punto del actor que se mueve en el editor;
  - cuando el haz aprieta el gatillo, viaja a 80 cm sobre el haz, con los mismos `GrabHoldDist` y `GrabSpeed` de la esfera real;
  - sigue al haz y queda donde se soltó.
- El formato de v1 se **amplía**: 34 floats por cuadro (30 Hz). Se agrega la posición del **aim** de cada mano (28-33), porque el haz y la punta del pincel salen del aim, no del grip (`SM_Tip` es hijo de `RightAim`). Los 10 DA están vacíos: no hay nada que migrar.

## 5. Cómo se graba (`L_GhostRec_SC`, el estudio)
- **Una estación por instrucción.**
  - Tiene una copia del objeto real a su distancia real de los ojos: el timbre, el sensor y la ameba, con las posiciones de Test_Hall; una esfera con los slots.
  - Breath, Heart y Draw no necesitan objeto.
  - Junto al objeto está el fantasma de esa instrucción.
  - Solo se ve la estación elegida.
- **En tus manos, lo mismo que va a tener el fantasma.** El grabador lo monta en tus mandos al elegir la instrucción:
  - el sensor en Breath y Heart;
  - el SAVE en la izquierda en Attract;
  - la paleta en la izquierda en Draw.
  - Así tocas el color real con la punta real.
- **Controles por mirada,** como en v1: `<` `>` `REC` `OK` `REDO`, con las manos libres.
- **Cuenta 3-2-1 antes de grabar** (pedido de Beltrán; v1 ya la tiene, se ajusta):
  - los números grandes aparecen **en la estación**, donde vas a hacer el gesto, no en el panel de arriba: así bajas la vista y pones las manos en posición mientras cuenta;
  - un tic por número y un **bip distinto en el "ya"**: la grabación empieza exactamente ahí;
  - mientras graba, el número de la estación muestra los segundos que quedan ("REC 4"); al terminar, otro bip;
  - `CountTime` editable (3 s por defecto) por si necesitas más margen.
- **Se graba relativo al ancla:** al fantasma de la estación, o a la cabeza en Breath y Heart.
  - Para llevarlo a la Obra, se coloca el fantasma en su nivel de test con la misma distancia al objeto real, y el contacto se conserva.
  - Esa colocación la hago yo; después Beltrán lo ajusta mirando.
- **Duraciones** (editables, `DemoTimes`): Bell 5 s · Take 5 s · Pick 6 s · Breath 16 s · Heart 12 s · Attract 12 s · Draw 10 s.
- Después de cada `REC`, **la vista previa en el visor es inmediata:** el fantasma repite tu toma en su estación, con el aspecto final. Después `OK` o `REDO`.

## 6. La primera prueba (pedido de Beltrán)
1. Pido el turno del editor a Narrativa y abro `L_GhostRec_SC`.
2. **Tú:** visor puesto, PIE por Quest Link, sentado y recentrado. Eliges `GHOST_BELL` y miras `REC`. En el timbre aparece 3 · 2 · 1 (con tic), suena el bip de inicio, la mano va al timbre y un bip marca el final.
3. **En el visor, al instante:** el fantasma repite tu toma sobre el timbre. `OK` o `REDO`.
4. **Paras el Play.** Yo guardo el DA (`ghost_dump.py`, con respaldo JSON) y refresco el fantasma del timbre en el editor. Lo ves en tu viewport y te mando una captura encuadrada (~1 min).
5. Para verlo moverse sin visor: Simulate (Alt+S) en el mismo nivel, con `bAutoPlay` en el fantasma.
6. Ajustamos el aspecto mirando (color, brillo del gatillo, ecos, `StepHz`) y después grabamos las otras seis.

## 7. Cambios técnicos
- El Construction Script no puede crear componentes. Por eso el reproductor usa **componentes fijos**: `BodyR/L` (instancias: la pose actual + 4 ecos, con la opacidad de cada eco por instancia), `TrigR/L`, `HandR/L`, `PropR/L`, `BeamR/L`, `Orb`, `Stroke`, `Path` (los puntos del recorrido, solo en el editor) y `Label`. Lo que no se usa queda a escala 0 o sin instancias.
- El sensor, el SAVE y la paleta se funden en una malla cada uno (`SM_GhostSensor_SC`, `SM_GhostSave_SC`, `SM_GhostPalette_SC`).
- Hoja del turno: `.claude/skills/unreal-vr/scripts/ghost/TURNO-V2.md`.

| Pieza | Cambio |
|---|---|
| `BP_GhostTake_SC` | + `bHeadAnchor`, `HoldR`/`HoldL` (0 nada · 1 mano · 2 mando · 3 sensor · 4 mando + SAVE · 5 mando + paleta), `Extra` (0 · 1 esfera · 2 trazo) |
| `BP_GhostPlayer_SC` | `Take` (DA directo), `FollowTag`, `PreviewTime`, `bAutoPlay`, `EchoCount`, `TriggerColor`/`TriggerGlow`, `OrbRest`; Construction Script de previsualización; mallas según `Hold`; esfera y trazo; `Play(bMirror)`/`Stop()` |
| `M_Ghost_SC` | translúcido suave en vez de aditivo; el gatillo con su propio color y brillo |
| `BP_GhostRecorder_SC` | ancla por instrucción (estación o cabeza); monta en tus mandos lo que va a sostener el fantasma; muestra solo la estación elegida |
| `L_GhostRec_SC` | 7 estaciones (copias del arte real) y 7 fantasmas |

- Los grafos existentes se tocan con cirugía, no se reescriben con `write_graph_dsl`.
- Reglas del turno de v1: una llamada MCP por vez, canario de actores, guardado con rutas explícitas, PIE detenido antes de compilar.

## 8. Después de grabar
- Colocar cada fantasma en su nivel de test, junto al objeto real.
- Integración (con Narrativa):
  - el Hall director prende y apaga Bell, Take y Pick;
  - cada etapa prende y apaga el suyo con su propia detección.
- Sonidos `AppearSound`/`VanishSound`: Narrativa.
