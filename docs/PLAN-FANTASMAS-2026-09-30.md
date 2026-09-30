# Plan: sistema de grabación y reproducción de los FANTASMAS (instrucciones demostrativas)

> 2026-09-30, noche. Encargo de Beltrán vía Narrativa: *"quiere terminar esta noche una primera versión completa"*. Lo arma la sesión **Drawing**.
>
> Base de diseño: `docs/GUION-V5-2026-09-29.md` §7.0b.
> - Fantasma translúcido con borde de luz, en el color de la etapa.
> - **~11 poses/s con 4 ecos**: opacidad 1 · 0,6 · 0,35 · 0,15 · 0,05.
> - Gesto de 4-6 s en bucle, con 1 s de pausa.
> - Una línea de texto debajo.
> - **Termina cuando el usuario hace el gesto.**
>
> Incluye también el encargo chico del dibujo en el cuadro de resultados (§8).

## 1. Piezas (todo en `/Game/SoulCharger/Mechanics/Ghost/`)

| Pieza | Qué es | Va en la obra |
|---|---|---|
| `BP_GhostTake_SC` | Clase **Data Asset** (padre `PrimaryDataAsset`), con los datos de una grabación. | sí (datos) |
| `Takes/DA_Ghost_<ID>` | Un asset por gesto (10, lista en §6). Se crean vacíos con `DataAssetTools.create`. | sí (se cocinan en el APK) |
| `BP_GhostPlayer_SC` | El **reproductor**: los mandos fantasma entrecortados con ecos, el haz opcional y la línea de texto. | sí |
| `M_Ghost_SC` | Material unlit translúcido con borde fresnel. Parámetros `Color`, `Opacity`, `Pressed` (el gatillo se ilumina). | sí |
| `BP_GhostRecorder_SC` | El **grabador** (herramienta, tag `TestOnly`), con controles por **mirada**. | no |
| `L_GhostRec_SC` | Nivel de grabación: pawn de la obra, grabador y reproductor de vista previa, con marcadores de referencia por gesto. | no |
| `scripts/ghost_dump.py` | Script del MCP: asegura y guarda los DA y deja un respaldo JSON en el repo. | no |

**Mallas del fantasma.**
- La pose actual usa el mando de la obra: `SM_QuestCtrl_Body_{R,L}_SC` más `SM_QuestCtrl_Trigger_{R,L}_SC`. El gatillo se anima con la bisagra de `BP_QuestCtrl_SC`: eje, pivote y `PressSign` −1.
- Los 4 ecos por mano usan la misma malla de cuerpo.
  - Con la malla actual son ~51k triángulos en demo con 2 mandos (15,3k por cuerpo).
  - 💡 **Pedido opcional a Mesh 3D:** `SM_QuestCtrl_Ghost_{R,L}_SC`, cuerpo y gatillo fundidos en reposo, ~2k triángulos, solo para los ecos. Baja a ~20k.
- Por ahora, **mando** para todos los gestos, incluidos los de "mano" (timbre y sensor). Beltrán graba con los mandos en la mano.

## 2. Formato de los datos (`BP_GhostTake_SC`)

| Variable | Tipo | Qué |
|---|---|---|
| `Id` | Name | p. ej. `GHOST_BREATH` |
| `Text` | String | La línea de instrucción, en inglés: *Rest the sensor on your belly* |
| `Hz` | float | 30 |
| `Frames` | int | Cantidad de cuadros |
| `Stride` | int | 28 |
| `Data` | float[] | `Frames × 28` |
| `bRight` / `bLeft` | bool | Qué mandos se muestran |
| `bBeamR` / `bBeamL` | bool | Haz fantasma desde el Aim (apuntar: `PICK`, `ATTRACT`, `SHARE`) |
| `Note` | String | Fecha y versión de la grabación |

**Un cuadro (28 floats), todo en el ESPACIO DEL ANCLA:**
```
 0- 5  mando R (grip): x y z · pitch yaw roll
 6-11  mando L (grip)
12-14  aim R: pitch yaw roll          (el haz)
15-17  aim L: pitch yaw roll
18-21  gatillo R, gatillo L, grip R, grip L   (0/1)
22-27  cabeza: x y z · pitch yaw roll          (referencia y diagnóstico)
```
- **Ancla** = posición de la **cabeza** (cámara) al empezar la toma, más el **yaw del pawn**.
  - Pitch y roll no entran, así que el ancla no gira si la cabeza cabecea.
  - Relativo a la cabeza: sirve **sentado y a cualquier altura** (guion). Los objetos de la obra también se ubican relativos a los ojos (p. ej. el timbre, 48 cm al frente y 28 cm bajo los ojos), así que el fantasma cae sobre ellos.
  - El yaw sale del **pawn**, no de la mirada: si el usuario mira de costado al empezar, la demo igual se arma hacia el frente de la etapa.
- **Por qué floats y no Transform ni Vector:** un arreglo de números se escribe y lee seguro por el MCP. Con structs y vectores en JSON hay trampas conocidas: solo la primera componente, structs no editables.
- **Tamaño:** 8 s × 30 Hz × 28 = 6.720 floats por gesto (~27 KB). Los 10 gestos, ~270 KB en el APK.
- **Espejo para zurdos** (`bRightHanded` del Hall): se intercambian R y L, se niega la y, y en la rotación yaw y roll cambian de signo. No hace falta grabar dos veces.

## 3. Por qué queda COCINADO (y no en SaveGame)
- Los `DA_Ghost_<ID>` son assets de `/Game`. `BP_GhostPlayer_SC` los referencia en `Takes` (referencias duras), así que el cocinado los mete en el APK.
- **Camino de los datos:**
  - En PIE, un Data Asset es **el mismo objeto** que en el editor: los assets no se duplican, solo el mundo.
  - Al aprobar una toma, el grabador escribe `Data` y `Frames` **directo en el DA**. Eso sobrevive al Stop del PIE.
  - Después, `ghost_dump.py` marca los DA como modificados (un `set_properties` de `Note`), los guarda con rutas explícitas y escribe un **respaldo JSON** por gesto en `.claude/skills/unreal-vr/scripts/ghost_takes/`.
  - Los datos nunca pasan por mi contexto: el script lee y escribe adentro del editor.
- **Riesgo:** si el editor se cae antes de guardar, se pierden las tomas de esa sesión. Por eso se guarda al terminar cada tanda de 2-3 gestos, no al final de todo.

## 4. El grabador (`BP_GhostRecorder_SC` en `L_GhostRec_SC`)

**Controles por MIRADA (dwell de 1,2 s con anillo que se llena).** No se usan botones del mando:
- El input de este proyecto es frágil: solo `IA_Shoot_*` llega confiable a un actor, y en Quest la tecla XR da 0.
- Las manos quedan libres para el gesto.
- Los botones flotan a ~1,2 m, **por encima de la mirada de trabajo**, para no dispararse durante un gesto.

**Pantalla:**
- `◀ GHOST_BREATH (4/10) ▶`, el texto de la instrucción y la duración.
- Botones `● REC` · `✓ OK` · `↺ REDO`, más un ✓ al lado de cada gesto ya aprobado.

**Flujo (Beltrán solo, con el visor puesto, en PIE por Quest Link):**
0. Sentado, mirando al frente, **recentra** (mantener el botón Oculus). El grabador marca el frente con una flecha en el piso.
1. Mira `◀ ▶` para elegir el gesto. Aparecen sus **marcadores de referencia**: esferas o discos translúcidos donde van el sensor, el timbre, la mesa, los slots, SAVE o SHARE, ubicados como en la obra respecto de los ojos.
2. Mira `● REC` → **3 · 2 · 1** (con tic) → graba `DemoTime` segundos. Cada gesto tiene su duración; termina solo, con un bip.
3. **Vista previa automática:** el fantasma repite la toma en bucle, con el aspecto final (entrecortado, con ecos).
4. `✓ OK` guarda en el DA y pasa al siguiente gesto. `↺ REDO` vuelve al paso 2 sin tocar el DA.
5. Cuando termina (o cada 2-3 gestos), avisa "listo" → yo corro `ghost_dump.py` con el PIE todavía abierto y después se detiene el PIE.

**Qué graba cada cuadro:**
- **Mandos:** los `MotionController` (Grip y Aim) del pawn poseído, por componente y no por clase de pawn. Es la misma receta de `BP_TBDirector_NC`: *"usa los del pawn poseído"*.
- **Cabeza:** la cámara del `PlayerCameraManager`.
- **Gatillos:** `IA_Shoot_{Right,Left}` Started/Completed, lo único confiable. **Grips:** `IA_Grab_*`, como mejor esfuerzo.
- Muestreo a 30 Hz fijo: se toma la pose del tick que cruza cada 1/30 s. Con 72 fps, el error es ≤ 14 ms.

## 5. El reproductor (`BP_GhostPlayer_SC`): API para la Obra y los niveles de test

| Llamada | Qué hace |
|---|---|
| `Play(DemoId: Name, Color: LinearColor, bMirror: bool)` | Busca el DA, **ancla** a la cabeza actual más el yaw del pawn y aparece en 0,4 s con curva y sonido (`FX_GHOSTAPPEAR`). Queda en bucle: gesto, pausa `LoopGap` (1 s, con fundido), gesto… |
| `Stop()` | Se disuelve en 0,6 s con curva y sonido (`FX_GHOSTOUT`). Después queda oculto y sin Tick. Idempotente. |
| `bPlaying` · `LoopCount` | Para la regla del guion: a los **2 bucles** sin gesto, Alma ayuda (`VO_xxh`). El que decide es el director. |
| `Reanchor()` | Vuelve a tomar el ancla, por si el usuario se movió mucho. Opcional. |
| `PreviewData(Data, Frames)` | Solo para el grabador: reproduce datos en memoria. |

- **Entrecortado:** `StepHz` 11, instance-editable. En cada salto, la copia más vieja pasa a la pose nueva, y las opacidades se asignan por edad (`EchoAlpha` [1, .6, .35, .15, .05]). La pose del paso k es el cuadro `round(k/11 × 30)`, sin interpolación: lo entrecortado es el punto.
- **Gatillo:** la copia actual gira el gatillo por la bisagra (0 → 14°) y sube `Pressed` en el material.
- **Haz** (`bBeamR/L`): un cilindro fino con el material fantasma, desde el Aim. Se ve en la copia actual y se desvanece con los ecos.
- **Texto:** `TextRender` bajo el fantasma, con el `Text` del DA, fundido de entrada y salida. `bShowText` lo apaga si la Obra usa su propio sistema de texto.
- **Reglas de carga:**
  - Nada en BeginPlay (oculto y sin Tick). Tick solo mientras hay demo.
  - `Dt = min(DeltaTime, 1/30)`.
  - Toda entrada y salida lleva curva y sonido; no hay saltos de un cuadro. Antes de mostrar, se escribe la pose y la opacidad 0 en el mismo cuadro.
- **Sonidos:** `FX_GHOSTAPPEAR` y `FX_GHOSTOUT` no existen todavía (⬜ en el guion). Van como variables instance-editable `AppearSound`/`VanishSound`. Los provisorios los elige Narrativa. `SBubbleHover*` quedan fuera porque son exclusivos del cuadro de resultados; si no hay elección, uso los de la paleta (`VR_shep_scale_up/down_02`).
- **Dónde va:** **uno solo** en el persistente de la Obra, fuera de las celdas, así no lo duerme el apagado de celdas. Una copia `TestOnly` en cada nivel de test que lo use. El director lo llama en R4 (fase 5, instrucciones) y llama `Stop()` cuando la etapa detecta el gesto.
  - La detección ya la tiene cada mecánica: umbral del sensor, primera esfera, primer trazo, etc.
  - **El botón real que brilla en el mando del usuario** (punto 3 del guion) es aparte: es del mando o herramienta del usuario, no del fantasma.

## 6. Los gestos

| ID | Etapa / momento | Mandos | Haz | Duración | Referencias en `L_GhostRec_SC` |
|---|---|---|---|---|---|
| `GHOST_BELL` | Hall, timbre | R | — | 6 s | timbre: 48 cm al frente, 28 bajo los ojos |
| `GHOST_TAKE` | Entering, tomar el sensor | R | — | 5 s | sensor (su posición en la etapa) |
| `GHOST_PICK` | Hall, elegir el alma | R | R | 6 s | 5 candidatas en arco |
| `GHOST_BREATH` | Entering | R | — | 8 s | estómago (≈ 55 cm bajo los ojos) |
| `GHOST_HEART` | Recognizing | R | — | 6 s | pecho izquierdo |
| `GHOST_LOVING` | Loving, las manos mueven partículas | R+L | — | 8 s | la célula (2 m al frente) |
| `GHOST_ATTRACT` | Attracting: apuntar, gatillo, llevar a un slot | R | R | 8 s | esferas, gusano y slots |
| `GHOST_SAVE` | Attracting y Surrounding, mantener SAVE | R+L | — | 5 s | SAVE en la mano no dominante |
| `GHOST_DRAW` | Surrounding: color en la paleta y trazo | R+L | — | 10 s | mesa (50 cm al frente) y paleta en la izquierda |
| `GHOST_SHARE` | resultados: SHARE / DON'T SHARE | R | R | 6 s | cuadro a 1,9 m con los dos botones |

- Las posiciones de los marcadores las saco en el turno de cada nivel de test; por ahora son aproximadas y editables en el grabador. Si alguna demo necesita contacto preciso, se puede grabar **en su propio nivel de test**: el grabador es portable, se suelta con tag `TestOnly`. `L_GhostRec_SC` es el camino rápido para hoy: una sola sesión y un solo volcado.
- Para `GHOST_DRAW`, la versión 1 muestra los dos mandos y los ecos (la estela ya dibuja el recorrido). El **trazo fantasma** que queda y se desvanece (guion) va en la versión 1.5, con una cinta procedural desde la punta mientras el gatillo está apretado.

## 7. Orden de trabajo y tiempos

1. **Fuera del editor (ya):** DSL de los 3 BPs, script de creación de los DA y del material, `ghost_dump.py` y este plan.
2. **Turno A, ~60-75 min:**
   - (a) el encargo chico §8 (~15 min);
   - (b) `BP_GhostTake_SC` y los 10 DA;
   - (c) `M_Ghost_SC`;
   - (d) `BP_GhostPlayer_SC`, probado en PIE con una **toma sintética** (una curva generada) sin visor;
   - (e) `BP_GhostRecorder_SC` y `L_GhostRec_SC`, probados en PIE sin visor: la mirada y el 3-2-1 se prueban con el mouse; la captura da poses nulas sin visor.
3. **Sesión de grabación, Beltrán con Quest Link, ~20-30 min:** yo con el turno del editor para volcar al final de cada tanda.
4. **Integración (Narrativa):** `Play`/`Stop` en R4 de la Obra, con el color de la etapa y `bMirror` = zurdo.

## 8. Encargo chico: el dibujo aparece y se va con su animación en el cuadro

- Hoy `PlaceSketch(Xf, Size)` coloca el dibujo de golpe.
- **Nuevo en `BP_TBDirector_NC`:**
  - `SketchAppear()`: todos los trazos del `SketchSet` pasan a `Reveal` 0 **antes** de hacerse visibles, en el mismo cuadro para que no haya chispazo. Después `Reveal` 0 → 1 en `ShowTime`, con smoothstep y `ShowSound`: la misma animación que el `SketchShow` de la etapa.
  - `SketchVanish()`: `Reveal` 1 → 0 en `HideTime`, con `HideSound`, y al final quedan ocultos (como `SketchHide`/`SketchOut`).
  - `bSketchFxBusy` indica si todavía corre la animación.
- **Reloj propio:** un timer que se detiene solo, no el Tick del director. La celda del dibujo está dormida durante los resultados, y despertar su Tick volvería a correr la lógica de la etapa.
- **Uso desde la Obra:** `PlaceSketch(Xf, Size)` → `SketchAppear()` en `ResultsShow`, y `SketchVanish()` en la salida de resultados.
- En el turno se lee cómo `SketchHide`/`SketchShow` escriben el `Reveal` por trazo, para reusar exactamente eso, y cómo quedan visibles los trazos después de `PlaceSketch`.

## 9. Decisiones abiertas (para Narrativa / Beltrán)
1. ¿Ancla con yaw del **pawn** (propuesto) o de la **mirada** al empezar?
2. ¿`GHOST_LOVING` va? El guion V5 dice que Loving no tiene R4; la lista de hoy lo incluye.
3. ¿El texto lo pone el fantasma (`bShowText`) o el sistema de textos de la Obra?
4. ¿Malla fantasma liviana de Mesh 3D (opcional) o la del mando para todo?
