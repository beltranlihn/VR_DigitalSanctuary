# El cierre de la experiencia — plan maestro (2026-08-27)

> Diseño dictado por Beltrán el 2026-08-27, con sus 15 respuestas ya incorporadas.
> Este archivo es **la entrada** para las sesiones de construcción: leerlo entero antes
> de tocar nada. Reemplaza al tramo "final" de `docs/PLAN-GUION-2026-08-14.md` y a los
> TODO del tracker `BP_SoulArchive.md`.

---

## 1. Qué es

Cuando termina Surrounding, la obra deja de medir al usuario y **le devuelve su rastro**:
su ameba cargada, su firma dibujada, sus curvas de calma y ritmo, sus ciclos de
respiración y su melodía. Después le pide compartirla, y al hacerlo aparece la
**constelación** de los 20 usuarios anteriores, que puede explorar de a uno.

> *"No es bueno ni malo, correcto ni incorrecto. Es lo que es."* — Beltrán

## 2. El guión, momento a momento

| # | Qué pasa | Espera |
|---|---|---|
| 1 | Termina Surrounding: el dibujo se disuelve **pero queda guardado** (ya funciona) | — |
| 2 | Última carga de anillo (5º) | `ring` |
| 3 | Termina la carga → **desaparece la arquitectura** (`CloseRoomNow`, ya existe) | — |
| 4 | **`Voice_Over_31`** + el **retrato**: la ameba (en `TP_soul_pick_5_surrounding`) se corre unos cm a la izquierda; a su derecha **reaparece el dibujo**; abajo aparece el **panel de resultados**; suena la **melodía en loop** | ~20 s |
| 5 | **`Voice_Over_32`**: instrucción de tomar la ameba y llevarla al corazón | `vo` |
| 6 | **Atracción por gesto**: apuntar la ameba con cualquier mano, **sin gatillo ni beam visible** → el retrato desaparece, queda sólo la ameba, que **viaja suave a la mano** y queda attached | gesto |
| 7 | Llevarla al **corazón** y sostener **3 s** → se comparte y viaja a su lugar de la constelación (`TP_soul_pick_6_final`) | zona |
| 8 | Al llegar: **aparecen las ~20 amebas guardadas**, ordenadas **al frente** (como las esferas de Attracting), de a una | — |
| 9 | **Exploración con beam** (láser visible, como Attracting): hover sobre una ameba → **crece, se corre a la izquierda** y aparece **su** dibujo + **su** retrato + suena **su** melodía (crossfade corto al cambiar) | 60 s (knob) |
| 10 | Se apaga la constelación suavemente, **VO final (33)** y a negro (`FinaleOut` → `ReloadLevel`, ya existe) | — |

**La rotación del archivo** ocurre **como dato, no como escena**: al terminar (paso 7,
cuando el usuario comparte) se hace el *append* del retrato propio y el archivo
**descarta el más viejo** si ya hay 20. Nadie ve viajar nada.

---

## 3. 🔴 Lo que YA EXISTE — reusar, no reconstruir

Regla del proyecto (`CLAUDE.md` §7.b): antes de construir, buscar. Ya hay mucho hecho,
casi todo del esqueleto viejo (`Core/Flow/`, nivel `L_Persistent`) y **verificado**:

| Pieza | Dónde | Estado | Qué aporta |
|---|---|---|---|
| **`BP_SoulArchive` + `SG_Constellation`** | `Core/Flow/` | 🟢 **round-trip de disco verificado entre corridas** | El esqueleto de la persistencia: `LoadArchive`/`AppendMe`/`SaveArchive`/`TrimArchive`, `MaxEntries`, `MyIndex`, y flags de debug para sembrar y borrar el slot |
| **`BP_Constellation`** | `Core/Flow/` | 🟢 verificado por log | Spawnea una ameba por entrada en **TargetPoints tagueados `ConstSpot`** (transform completo, autorable a mano) + **aparición gradual** (`StarGap`) |
| **`BP_ConstExplorer`** | `Core/Flow/` | 🟢 verificado por log | Selección **por ángulo** (no line trace) y disparo de la melodía del vecino |
| **`BP_BioHub`** | `Core/` (colocado en el persistente) | 🟡 bins construidos y verificados | 🔴 **Ya graba las series**: 180 casillas × `BinSeconds` (5 s) = 15 min, con `Sum/Count/Min/Max` de calma y ritmo + `BinStage`. **Faltan los getters de promedio** (`GetBinAverage(i)`) |
| **`WBP_SoulHUD_SC`** | `Core/UI/` | 🟡 verificado en PIE | El patrón del gráfico: **curva por `OnPaint`+`DrawLines`** que **sigue a un marco (`GraphArea`) vía `SyncBox`** → se diagrama arrastrando en el Designer. Es exactamente el "fácil de editar" que pidió Beltrán |
| **`BP_ProtoSoul_SC`** | `Core/ProtoSoul/` | 🟡 | `MoveTo(tag)` (sigue un TargetPoint vivo, tamaño = escala del punto), `DrawRing`, hover con `FresnelPower`, `Configure(malla,color)`, `SeedRings` |
| **`BP_Sensor_Soul`** | `Core/Sensor/` | 🟢 | **Toda la interacción vive acá** (directiva de Beltrán): beam Niagara ×2 manos con `LineTrace` (modo 4), zona de corazón (modo 2), háptica, gatillo |
| **`BP_Sequencer_SC` + `BP_SaveMelody_SC`** | `Core/Attracting/` | 🟢 validado en visor | La melodía y su botón de guardado; `BP_SoundOrb_SC` son las esferas reales con sus clips |
| **`BP_DrawCanvas`** | `Stages/Movement/` | 🟢 | Los arrays `Pt*` **ya son el formato** de la firma; `ShowSignature()` del sensor ya la recoloca y escala |
| **`BP_Director_Story`** | `Core/Flow/` | 🟢 | `RunEnding` subs 6-11 con VO 31/32/33, `CloseRoom`, `FinaleOut`, `ReloadLevel` |

**Consecuencia para el plan:** esto **no es construir de cero**, es *portar y ampliar*.
Lo que se porta a la versión limpia (`_SC`, en `L_SoulCharger`) y lo que se amplía está
en la §6.

---

## 4. Decisiones tomadas (Beltrán, 2026-08-27)

1. **Persistencia real a disco**, últimos **20 usuarios**. Anillo FIFO: cuando entra el 21,
   sale el más viejo. Hasta llegar a 20 sólo se acumula.
2. El dibujo guardado se **decima** (menos puntos), con la cantidad **como variable** para
   poder probar. La forma se conserva.
3. Curvas **normalizadas por usuario** (su propio mín/máx). No se comparan personas.
4. Se construye con la **señal simulada** del BioHub; el día del OSC real es cambiar
   `bFakeSignal` en la instancia.
5. **Puntaje de respiración por ciclo** = fracción del ciclo dentro del umbral (0..1) → es
   el radio del círculo interior dentro del anillo del ciclo.
6. Las esferas de la melodía son **las reales** (`BP_SoundOrb_SC`), no dibujos de UI.
7. Melodía en **loop** mientras el retrato está visible; **crossfade corto** al cambiar de
   ameba.
8. El panel se hace **editable en el Designer** (patrón `WBP_SoulHUD_SC`: marcos + `SyncBox`).
9. Atracción por gesto: **cualquier mano**, cono de ~10°, ~1 s de permanencia. Sin gatillo.
10. Las 20 amebas van **al frente, ordenadas**, como las esferas de Attracting (no rodeando).
11. La rotación del archivo es **sólo dato**, y se hace **al final de la corrida** (cuando
    el usuario comparte), no al arrancar la siguiente.
12. Mientras el archivo no esté lleno se muestran **sólo las ocupadas** — incluida la que
    el usuario acaba de crear, para poder testear desde la primera corrida.
13. La ameba propia **también se puede apuntar y ver** en la constelación.
14. Exploración de **60 s**, como variable.
15. VO **31** (retrato) · **32** (tomar la ameba) · **33** (final). Si cambian, avisa.

**Nota de rendimiento resuelta por diseño:** nunca hay 20 dibujos a la vez. Simultáneo
sólo se ven las **amebas con sus anillos**; el dibujo y el retrato son **de a uno**, en hover.

---

## 5. El modelo de datos

### `SG_Portrait_SC` (SaveGame nuevo, ampliación de `SG_Constellation`)
Arrays **paralelos**, una entrada por usuario. 🔴 Paralelos y no un struct porque
**el MCP no puede agregar miembros a un `UserDefinedStruct`** (`F_SoulPortrait` sigue
vacío). Las series de largo variable van como **string CSV**, que es el criterio que el
proyecto ya usa para la melodía.

| Campo | Tipo | Contenido |
|---|---|---|
| `Variants` | int[] | Malla elegida en el Hall |
| `Colors` | LinearColor[] | Color de esa ameba |
| `Rings` | int[] | Cuántos anillos cargó (0..5) |
| `Calm` | string[] | CSV de ~180 valores 0..1 (una casilla de 5 s cada uno) |
| `Heart` | string[] | CSV de ~180 valores de BPM |
| `Breath` | string[] | CSV de N puntajes 0..1, uno por ciclo de Entering |
| `Melody` | string[] | CSV `slot:clipId` de la melodía guardada |
| `Draw` | string[] | Trazos separados por `;`, puntos por `\|`, `x,y,z` con 1 decimal |
| `Stamp` | int[] | Contador de corrida — define quién es "el más viejo" |

⚠ **Trampa ya documentada** (`BP_SoulArchive.md` §37): `Array|Add` sobre el array de
**otro objeto** opera sobre una copia y no acumula. El patrón correcto es
**leer → agregar → volver a escribir**, y el `Set` cruzado exige *keywords*.

### De dónde sale cada dato
- **Calma / Ritmo** → los **bins del `BP_BioHub`** (ya se graban). Falta `GetBinAverage(i)`
  y un serializador a CSV que corte en la casilla en la que terminó Surrounding.
- **Respiración** → nuevo: `BP_BreathRing_SC` / `BP_BreathPacer` cierran cada ciclo; hay que
  acumular *tiempo dentro del umbral / duración del ciclo* leyendo el `bBreathing` del sensor.
- **Melodía** → `BP_Sequencer_SC` (slots + clip ids).
- **Dibujo** → `BP_DrawCanvas` (`Pt*`), decimado.
- **Variante / color / anillos** → `BP_ProtoSoul_SC` de la ganadora.

---

## 6. Fases

> Cada fase termina con una verificación concreta. El robot (`BP_Robot`, rutina 3) sirve
> para el tramo de dibujo; para el resto, `DebugStartRoom=5` + los flags de debug del
> archivo. **Restaurar siempre las flags de Beltrán al terminar.**

### F1 — Los datos (sin nada visual) — ✅ **CERRADA (2026-08-27)**
> Verificación en PIE, tres corridas, cero `Accessed None`. Detalle completo en el tracker
> [`blueprints/BP_SoulArchive_SC.md`](../.claude/skills/unreal-vr/blueprints/BP_SoulArchive_SC.md),
> que además **fija el contrato de los CSV** (separadores, `-1` = hueco, redondeos) — leerlo
> antes de escribir el lector de F2/F5.
>
> Correcciones al plan que salieron de construirlo:
> - **Los getters de promedio del BioHub YA existían** (`GetCalmBinAvg`/`GetHeartBinAvg`/`BinHas*`).
>   Lo que faltaba era el serializador: **`Series(bHeart)`**.
> - 🔴 **`Pt*` de `BP_DrawCanvas` NO era el formato del dibujo**: son un buffer por sección que
>   se resetea en cada trazo. Hubo que crear el acumulado (`SavePts`/`SaveBreaks`).
> - El **`TrimArchive` del `BP_SoulArchive` viejo estaba roto** (`RemoveIndex` sobre una copia):
>   nunca recortó nada. El nuevo usa leer→modificar→reescribir.
> - Buena noticia para F3: **`BP_ProtoSoul_SC` ya tiene `StartCarry`/`StepCarry`/`EndCarry`/`Shared`/
>   `OnShared`/`ShareRadius`**, y el picker tiene `bShareMode`. El gesto está casi entero — **buscar
>   antes de construir**.

- `GetBinAverage(i)` + serializadores CSV en `BP_BioHub`.
- Puntaje por ciclo de respiración en Entering.
- Serializador/decimador del dibujo en `BP_DrawCanvas` (+ knobs `SaveEveryNth`, `SaveMaxPoints`).
- Serializador de la melodía en `BP_Sequencer_SC`.
- **`BP_SoulArchive_SC` + `SG_Portrait_SC`** (portado del viejo, con los 9 campos y FIFO de 20).
- ✅ **Listo cuando**: una corrida escribe el `.sav` con los 9 campos alineados y la
  siguiente lo lee; con 21 corridas simuladas quedan 20 y se fue la más vieja.

### F2 — El retrato (lo que ve el usuario de sí mismo) — ✅ **CERRADA (2026-08-27)**
> Construido y verificado en PIE: `BP_Portrait_SC` + `WBP_Portrait_SC` + el enganche en `RunEnding` sub 6
> + **la melodía en loop con las esferas reales**.
> Detalle en [`blueprints/BP_Portrait_SC.md`](../.claude/skills/unreal-vr/blueprints/BP_Portrait_SC.md).
> **Queda para pulido**: escalar el dibujo al alto de la ameba+anillos, el **crossfade** al cambiar de
> vecino (es de F5), y la diagramación fina de Beltrán + el visor.
>
> Decisiones que se tomaron construyendo:
> - El retrato **no recolecta nada**: le pide `CollectOnly()` al archivo. Una sola puerta para el dato
>   real y para el ficticio.
> - El dibujo se muestra **reusando `ShowSignature()` del sensor**, sin tocarlo — pero eso obliga a
>   **mover `TP_signature_spot`** junto al retrato (hoy está al lado de `soul_pick_6`).
> - La espera del paso 4 se hizo con **`PortraitHold` = 20 s** (timer), no con el fin del VO 31.
> - La melodía **saca su tempo del pad** (`PadSound.Duration / MelodySteps` = 0,667 s por paso), igual que
>   `BP_Sequencer_SC.Boot`: suena al mismo ritmo al que el usuario la armó.
> - ⚠ `MelodySounds` es una **copia** de `BP_Sequencer_SC.ModuleSounds`: el secuenciador vive en el
>   sublevel de Attracting, que ya está descargado. Si se agrega el Módulo 2, actualizar las dos listas.

- **`BP_Portrait_SC`**: actor que orquesta la ameba (corrida a la izquierda), el dibujo a la
  derecha **escalado para que su alto máximo iguale al de la ameba+anillos**, el panel y la
  fila de esferas reales sonando en loop.
- **`WBP_Portrait_SC`**: dos curvas por `OnPaint`+`DrawLines` (calma, ritmo) siguiendo marcos
  `SyncBox`, la fila de anillos de respiración (anillo = ciclo, círculo interior = puntaje) y
  los marcos vacíos para que Beltrán diagrame arrastrando.
- Enganche en `RunEnding` tras la 5ª carga: VO 31 + retrato.
- ✅ **Listo cuando**: al terminar Surrounding aparece el retrato con datos **reales de esa
  corrida** y la melodía en loop, y Beltrán puede mover todo en el Designer sin tocar nodos.

### F3 — El gesto: de la mano al corazón — ✅ **CERRADA (2026-08-27)**
> 🔴 **La corrección grande al plan: el gesto YA EXISTÍA casi entero y estaba cableado al director.**
> `Picker.Rearm` → `bShareMode` → hover + gatillo → `Winner.StartCarry` → `CarryBody` lleva la ameba a la
> mano y comparte al entrar en la zona del pecho. **No se construyó de cero: se le cambió el disparador.**
>
> Lo que se hizo:
> - **Atracción por ÁNGULO, sin gatillo** (`AimTry`/`AimScan`/`AimAccum`/`AimHook`), cualquier mano,
>   `AimConeDeg` 10° y `AimDwell` 1 s como knobs. Mismo criterio que ya usaba `BP_ConstExplorer`.
> - Al enganchar: **el retrato se apaga** (panel + melodía) y la ameba viaja a la mano.
> - **La zona del corazón ahora exige sostener `ShareHold` = 3 s** (`ShareZone` en `BP_ProtoSoul_SC`),
>   con reset al salir. Antes compartía en el instante de entrar.
> - **`SaveMyPortrait()`** en el sub 8 del director: el `.sav` gana la entrada al compartir.
>
> ⚠ **Se hizo en `BP_SoulPicker_SC`, no en `BP_Sensor_Soul` como decía el plan**: `bShareMode`, `Winner`
> y el Tick ya viven ahí, y el sensor no conoce a la ganadora. Moverlo al sensor sería reconstruir un
> camino probado — se puede hacer, pero conviene saber que esto ya funciona.
>
> ✅ Verificado dos veces: el gesto aislado (enganche a +1,0 s, compartida a +3,05 s — clavados en sus
> knobs) y **la corrida completa del final** con el `.sav` ganándose la entrada. Cero `Accessed None`.
> ⬜ Falta visor: si 10° y 1 s se sienten bien con las manos de verdad.
- **Modo nuevo en `BP_Sensor_Soul`** (confirmar número libre; 4=beam, 5=dibujo): apuntar por
  **ángulo** con cualquier mano, cono y permanencia como knobs, **sin beam visible**.
- Al enganchar: se apaga el retrato, la ameba viaja suave a la mano y queda attached.
- Zona de corazón + **3 s** (reusar la zona de Recognizing) → `AppendMe` → viaje a
  `TP_soul_pick_6_final`.
- ✅ **Listo cuando**: el ciclo corre entero en PIE sin gatillo y el `.sav` gana una entrada.

### F4 — La constelación — ✅ **CERRADA (2026-08-27)**
- **`BP_Constellation_SC`** (`Core/Flow/`, colocado en `L_SoulCharger`) + **20 TargetPoints**
  `TP_const_00..19` con el tag `ConstSpot`: arco de 72° en dos filas (elevaciones 17° y 30°,
  radio ~646 cm desde el usuario, escala 1,2). 🔴 **La posición y escala finales las autora Beltrán.**
- Aparición gradual (`StarGap` 0,35 s → 7 s en total), sólo ranuras ocupadas, y **`bSkipMine`**:
  la entrada propia se saltea porque **la ameba real ya viajó sola** a `soul_pick_6`.
- El `Variant` guardado se resuelve a malla con un **`MeshBank`** que se cachea en `BeginPlay+0,6 s`
  desde `Picker.Souls[i].Mesh`, **antes** de que `ForceChoose` destruya a las 4 perdedoras.
- ✅ **Verificado**: por el guión real → `mi ameba ya viajo sola - salteo su entrada` →
  `cielo completo, estrellas = 19` (19 + la propia = 20), con los anillos de cada entrada.
- 🔴 **Corrección al plan**: se fusionó con F5 en **un solo actor**, no dos. El explorador necesita
  `Indices` (qué entrada del archivo es cada estrella), que es estado del constructor.

### F5 — La exploración — ✅ **CERRADA (2026-08-27)**
- **Beam visible** (`Sensor.ExploreOn` + `AimBeams`, sin `LineTrace`) pero **selección por ÁNGULO**
  (`AimConeDeg` 9°, cualquier mano) — las amebas no tienen colisión y dársela arriesga el agarre.
- Hover → el vecino **baja al atril** (`FocusTag` = **`portrait_soul`**, el mismo punto donde el usuario
  acaba de leer su propio retrato), el anterior **vuelve a su estrella**; se reconstruye **su** dibujo en
  el canvas reusado (`BP_DrawCanvas.RebuildFrom`), se llena el panel con **sus** datos
  (`BP_Portrait_SC.ShowIndex`) y arranca **su** melodía con las esferas reales.
- Reloj de **`ExploreSeconds`** (60 s, knob del director) → `StopExploring` + `FadeOut` → VO 33 →
  `StartStepTime` → `FinaleOut`.
- ✅ **Verificado**: **12 vecinos** seguidos, cada uno con series distintas (`180/180/4`, `/5`, `/6`,
  `/7`…), melodías distintas y su dibujo (`secciones = 3` + `la firma aparece junto al alma`).
  **Sin fugas**: las esferas viejas se destruyen solas y `SaveMaxPoints=0` durante la reconstrucción
  impide que el dibujo del vecino pise la firma propia. Cero `Accessed None`.
- 🔴 **Corrección al plan**: la exploración vive en `BP_Constellation_SC`, no en el sensor; el sensor
  sólo aporta el beam (dos funciones, cero cirugía sobre `SetStage`/`TickMech`).
- ⬜ **Falta el crossfade** de melodía al cambiar de vecino (hoy corta y arranca), y el **visor**.
- ⬜ **Insumo de Beltrán**: mover `TP_signature_spot` — hoy sigue arriba junto a `soul_pick_6`, y ahora
  es el atril del dibujo (propio y del vecino), así que va **junto al panel**.

### F6 — Pulido — ✅ **CERRADA (2026-08-27)**, salvo la pasada de gafas

**Entrada propia de cada ameba** — 🔴 era un BUG, no un pulido: `bStartAsleep` del CDO de
`BP_ProtoSoul_SC` está en `true`, así que cada estrella spawneada corría `Sleep()` y quedaba en
**escala 0**. Corrió tres veces logueando `estrellas = 20` **sin que se viera nada**. Ahora cada una
entra con su `Appear`, y `Report` loguea el **tamaño real**, no la cantidad.

**Legibilidad** — se midió en vez de opinar: el usuario está en **X = 7151,7** (no 7500 como se había
supuesto: 3,5 m de error), y la escala se estaba aplicando **dos veces** (spawn + `Size`). Con los dos
números corregidos, la disposición quedó en **5 filas × 4 columnas sin columna central** (el hueco del
medio es para la ameba propia), separación mínima **120 cm** contra anillos de **83 cm**.

**🔁 Cambio de arquitectura (pedido de Beltrán mirando el PIE):** la tarjeta de resultados **vive dentro
de `BP_ProtoSoul_SC`**, no en un atril compartido. Cada ameba tiene la suya; sólo la enfocada instancia
el widget (`WidgetClass = None` → `SetWidget` → `SetWidget(None)`), así que hay **un solo render target**.
La estrella apuntada **se acerca por su propio rumbo** (`FocusPull`), y la tarjeta y el dibujo viajan con
ella. Detalle en [[BP_Constellation_SC]] §"2ª tanda".

**Otros ajustes**: título del vecino `SOMEONE WHO WAS HERE` (el propio sigue `YOUR TRACE`), fila más alta
de 34° a **29°**, la melodía **no corta** al cambiar de vecino (`SwapMelody` conserva el compás), y los
prints que disparan por-item pasaron a **sólo log** para no taparle el cielo al usuario en el visor.

⬜ **Falta**: la pasada de gafas de Beltrán y la medición de draw calls / fill-rate en APK.
⬜ **Deuda conocida**: las esferas de la melodía siguen naciendo en el atril viejo (es lo único del
conjunto que no viaja con la estrella), y la reconstrucción del dibujo cuesta ~60 ms de hitch.

---

## 6.b 🧪 Modo debug: el retrato se llena solo (pedido de Beltrán, 2026-08-27)

🔴 **Requisito de primera clase, no un extra**: si se arranca directo en esta etapa para
probar (`DebugStartRoom`), **no hay corrida previa** — no hay bins de calma, ni ciclos de
respiración, ni melodía, ni dibujo. El retrato aparecería vacío y no se podría juzgar
**cómo se ve**, que es justamente lo que Beltrán quiere mirar.

Entonces: **`bFakeData`** (flag del retrato/archivo). Cuando está activo, cada dato que
falta se rellena con un valor **ficticio pero plausible**, y el retrato se dibuja completo:
- **Calma**: ~180 valores de un seno suave con ruido (0,15..0,9), no una recta.
- **Ritmo**: ~180 valores alrededor de 68 ±9 BPM con deriva lenta.
- **Respiración**: N ciclos con puntajes variados (p. ej. 0,4 / 0,9 / 0,65 / 1,0 / 0,8) —
  **nunca todos iguales**, si no el gráfico no muestra nada.
- **Melodía**: una secuencia de esferas de ejemplo con clips reales, para oír el loop.
- **Dibujo**: si no hay firma en memoria, un garabato de ejemplo generado (o el último
  guardado en el archivo).
- **Ameba**: variante y color de ejemplo, anillos = 5 (carga completa).

Dos usos, el mismo interruptor:
1. **Retrato propio** sin haber jugado la obra → estética del panel.
2. **Constelación poblada**: sembrar N entradas falsas **completas y distintas entre sí**
   (ampliando el `DebugAppendFake` que ya existe en `BP_SoulArchive`) para poder explorar
   los 20 vecinos sin necesitar 20 corridas reales.

⚠ El dato falso **entra por la misma puerta que el real** (los mismos serializadores y el
mismo `.sav`), nunca escribiendo las variables finales del widget: si no, el modo debug no
probaría nada de lo que importa. Es el mismo criterio que ya usa `bFakeSignal` del BioHub.
⚠ `bFakeData` **jamás** debe escribir entradas falsas en el archivo real de una corrida
normal — gatearlo igual que los flags de debug existentes y dejarlo en `false`.

## 7. Riesgos anotados

- **Desalineado de arrays paralelos**: mitigado escribiendo los 9 en una sola función y
  logueando las longitudes (`ReportArchive`).
- **Tamaño del `.sav`**: 20 × (360 valores + ~500 puntos) ≈ 1 MB de texto. Tolerable; si
  crece, bajar `SaveMaxPoints`.
- **Reconstruir el dibujo del vecino en hover** = generar un `ProceduralMesh` en caliente.
  Usar **un solo canvas reutilizado** y un pequeño *debounce* del hover.
- **20 amebas + hasta 100 anillos** a la vez: es lo único simultáneo pesado. Medir en APK.
- **OSC simulado**: las curvas serán bonitas pero falsas hasta el sensor real.
- **`bFakeSignal`, `DebugStartRoom`, `bAutoTest`, `RobotOn`**: son flags de Beltrán.
  Dejarlas como estaban.

## 8. Insumos de Beltrán

- Los archivos `Voice_Over_31/32/33`.
- Posición y escala de los 20 TargetPoints de la constelación (y del ancla del retrato).
- La diagramación fina del panel en el Designer.
- Si llena `F_SoulPortrait` a mano en el editor, migramos de arrays paralelos a un struct.

---

## 9. Lo que queda (al cerrar el 2026-08-27)

Las seis fases están construidas y verificadas por log. Lo que sigue abierto:

### 🔴 Bloqueantes antes de empaquetar
| Qué | Dónde | Detalle |
|---|---|---|
| **`StepTimes[5]` está en 20 s** | `BP_Director_Story` (CDO) | Valor de PRUEBA pedido por Beltrán ("ya con el juego listo las alargamos"). Su valor de obra era **300**. `StepTimes[4]` (Attracting) sigue en 300 por si también molesta. |
| **Los VO 31 / 32 / 33** | `B - VOs sueltos` | Si no están, `Say` loguea "este paso no tiene VO" y el guión avanza igual — o sea que **falta en silencio**. |

### 🎨 Insumos de autor (Beltrán)
- **Posición y escala de los 20 `TP_const_*`** y del `TP_const_anchor` (su escala = el tamaño de la
  estrella enfocada). Hoy están en un arco calculado, no autorado.
- **`TP_soul_pick_6_final` está en escala 1,5** → su halo de anillos mide 250 cm y se le mete ~9 cm a la
  estrella más cercana. Para despejar tendría que estar en ≤ 0,9.
- **`TP_signature_spot`**: durante la exploración lo mueve `PlaceSign` en runtime, pero su posición
  autorada **sigue mandando en el momento del retrato propio**, que ocurre antes.
- **La diagramación fina del panel** en el Designer, y la decisión sobre el **fondo de la tarjeta**
  (queda transparente; sobre el negro de la constelación debería leerse, se decide con gafas puestas).

### ⬜ Pendientes técnicos
- **Visor**: si 9° (`AimConeDeg`) es cómodo para apuntar estrellas a ~9,8 m; si el beam se ve; si 29° de
  elevación en la fila más alta cansa el cuello; si el acercamiento de 400 cm (`FocusPull`) alcanza.
- **APK**: draw calls y fill-rate con 20 amebas + hasta 100 anillos procedurales simultáneos. Es lo único
  pesado y simultáneo de toda la obra.
- **Las esferas de la melodía no viajan**: siguen naciendo relativas a `BP_Portrait_SC`, en el atril
  viejo, mientras la ameba, su tarjeta y su dibujo se movieron. Es lo único del conjunto que quedó atrás.
- **El hitch del dibujo**: `RebuildFrom` cuesta ~60 ms (4 frames perdidos) al cambiar de vecino. Si en
  gafas se siente, bajar `SaveMaxPoints` o meter un debounce del hover.
- **Unificar el retrato propio** con la tarjeta-en-la-ameba: hoy conviven dos caminos (el panel fijo de
  `BP_Portrait_SC` para el propio, la `Card` del alma para los vecinos). Funciona, pero es un camino de
  más; ahora que el modelo nuevo está probado, el propio podría usar el mismo.
- **`F_SoulPortrait`** sigue vacío: la persistencia usa 9 arrays paralelos. Si Beltrán llena el struct a
  mano, se puede migrar.
