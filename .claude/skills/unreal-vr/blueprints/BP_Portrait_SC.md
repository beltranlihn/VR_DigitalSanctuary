# BP_Portrait_SC + WBP_Portrait_SC — el retrato que la obra le devuelve al usuario (Core/UI/)

> **F2** del plan [`docs/PLAN-CIERRE-2026-08-27.md`](../../../../docs/PLAN-CIERRE-2026-08-27.md).
> Aparece con el **VO 31**, cuando ya cerró Surrounding: la ameba se corre a un punto propio, el
> dibujo reaparece a su lado, y debajo se enciende el panel con **sus** curvas de calma y ritmo y
> **sus** ciclos de respiración.

- **Actor**: `/Game/SoulCharger/Core/UI/BP_Portrait_SC` · colocado en `L_SoulCharger` como
  `BP_Portrait_SC_C_1`, **colocado por Beltrán** — al cierre de esta sesión en (7640, 0, **157**) yaw 180,
  debajo de `TP_soul_pick_5_surrounding`. ⚠ **Es su pose autoral: no pisarla.**
- **Widget**: `/Game/SoulCharger/Core/UI/WBP_Portrait_SC` · lienzo **1600×900 px**, componente a
  escala **0.06** ⇒ **96 × 54 cm**. **1 px = 1 mm.**

## Status
🟢 **Cadena completa verificada en PIE (2026-08-27)**, cero `Accessed None`:
`RETRATO: series cargadas calma/ritmo/respiracion = 180/180/5` con `bFakeData`, y
`curva calma p0/pmed/pfin = X=344 Y=186.7 | X=923 Y=181.5 | X=1496 Y=278.9` — la curva **varía**
y cae **dentro del marco** (`CalmArea` ocupa x 330..1510, y 150..330). La fila de anillos de
respiración se ve en la captura de PIE.
⬜ **Falta la diagramación de Beltrán** (posición, escala y encuadre del panel; ver §Insumos) y el visor.
🟢 **La melodía en loop con las esferas REALES, verificada en PIE (2026-08-27)**:
`melodia 0:3,2:8,4:14,7:5 - esferas reales sembradas = 4`, cada una en su ranura
(Y +56 / +24 / −8 / −56 a 45 cm bajo el panel), y `melodia en loop, paso = 0.666667` con la vuelta de
compás cada **5,33 s** exactos. Cero `Accessed None`.

---

## 🎛️ Cómo se autora (esto es lo que pidió Beltrán)

**El panel se mueve moviendo el ACTOR en el viewport.** No hay nada que tocar en el grafo.

**Lo de adentro se diagrama arrastrando en el Designer del `WBP_Portrait_SC`.** Los tres marcos
(`CalmArea`, `HeartArea`, `BreathArea`) son `Image` con contorno visible, y **todo los sigue**:
- Las dos curvas se dibujan por `OnPaint` + `DrawLines` **leyendo el SLOT del marco**
  (`SlotAsCanvasSlot` → `GetPosition`/`GetSize`), igual que el gráfico EEG de [[BP_SoulHUD_SC]].
- Los anillos de respiración se reparten **dentro de `BreathArea`**: `LayoutRings` calcula la celda
  por ciclo y `OneRing` escribe posición y tamaño de cada par.
🔴 **Los tres marcos están anclados ARRIBA-IZQUIERDA (anchors 0,0 · alignment 0,0)**, que es lo que
hace que `GetPosition` ya sea la coordenada dentro del lienzo. No cambiarlo (gotcha §205).

**Para que un marco desaparezca**: su brush → Outline Settings → Color → alpha a 0. Se sigue
pudiendo seleccionar desde el panel Hierarchy.

---

# WBP_Portrait_SC — el panel

## Árbol (23 widgets, todos hijos de `Root` y anclados arriba-izquierda)
| Widget | px (x, y, ancho, alto) | Qué es |
|---|---|---|
| `Title` | 60, 40, 760×70 | "YOUR TRACE", 44 px |
| `CalmLabel` / `CalmArea` | 60,178 · 330,150 1180×180 | "CALM" y el **marco de la curva de calma** |
| `HeartLabel` / `HeartArea` | 60,408 · 330,380 1180×180 | "RHYTHM" y el **marco de la curva de ritmo** |
| `BreathLabel` / `BreathArea` | 60,648 · 330,620 1180×180 | "BREATH" y el **marco de la fila de anillos** |
| `RingO_0..7` | los reubica `LayoutRings` | el **aro** = un ciclo de respiración |
| `RingI_0..7` | los reubica `LayoutRings` | el **disco interior** = el puntaje de ese ciclo |

💡 **Círculos sin texturas**: brush `RoundedBox` con `outlineSettings.roundingType = HalfHeightRadius`.
El aro es tint alpha 0 + contorno; el disco es tint sólido + contorno 0. Los marcos usan
`FixedRadius` con radio 10.
🎛️ **8 anillos es el máximo** (`Cycles` de [[BP_BreathRing_SC]] hoy es 5). Los que sobran se ponen en
`Collapsed`. Si algún día hay más de 8 ciclos, hay que agregar pares al Designer y a `CollectRings`.

## Variables
| Variable | Default | Rol |
|---|---|---|
| `CalmColor` / `HeartColor` | celeste / salmón | color de cada curva |
| `LineWidth` | 3.0 | grosor de las curvas |
| `Pad` | 14 | margen interno de los tres marcos |
| `RingInnerMin` / `RingInnerMax` | 0.10 / 0.86 | de qué a qué fracción del aro crece el disco interior |
| `CalmS` / `HeartS` / `BreathS` | — | las series ya parseadas y normalizadas (0..1) |
| `PtsCalm` / `PtsHeart` | — | los puntos que dibuja el `OnPaint` |
| `NLo` / `NHi` | — | mín/máx de la serie que se está normalizando |
| `TmpF` / `TmpN` / `TmpP` | — | andamios (parseo, normalizado, puntos) |
| `RingsO` / `RingsI` | — | los 8+8 `Image`, juntados por `CollectRings` |

## API y funciones
| Función | Qué hace |
|---|---|
| **`SetSeries(CalmCSV, HeartCSV, BreathCSV)`** | La única puerta de entrada. Parsea, normaliza, reconstruye y loguea los tres largos. |
| `ParseSeries(CSV) -> float[]` | Corta por comas, `StringToFloat`, y **descarta los `-1`** (los huecos del contrato del `.sav`). |
| `Bounds(In)` | mín y máx de la serie, a mano (ver la trampa de abajo). |
| `Normalize(In) -> float[]` | **Normaliza por el propio mín/máx del usuario** (decisión 3 del plan) con `MapRangeClamped`. Serie plana → 0.5, para que no se dibuje pegada al piso. |
| `BuildCurve(Samples, Area) -> Vector2D[]` | Los puntos, dentro del marco que se le pase. |
| `CollectRings` / `LayoutRings` / `OneRing` | La fila de anillos dentro de `BreathArea`. |
| `Rebuild()` | Las dos curvas + los anillos. Loguea `p0/pmed/pfin` de la curva de calma — **el diagnóstico que caza los bugs de geometría**. |
| `SeedDemo()` | Curvas de demo + 5 puntajes variados (0.4/0.9/0.65/1.0/0.8). La llama `PreConstruct`, así el **Designer nunca se ve vacío**. |
| `OnPaint(Context)` | Dos `DrawLines`. 🔴 `add_event("OnPaint")` falla: va con `add_function_graph`. |

## 🔴🔴 La trampa que costó el bug de la curva plana
**`Math|Float|MinOfFloatArray` y `MaxOfFloatArray` llegan al DSL con salida entera**: al conectarlos a
un pin `double` el escritor mete un **`Math|Conversions|ToFloat(Integer)` en el medio**, que **trunca**.
Con calma en 0..1 eso deja `lo = hi = 0`, el span se va a `0.0001` y **la curva sale plana pegada al
piso** (`Y = BaseY` exacto para las 180 muestras).
- **El síntoma**: la curva de `SeedDemo` se veía bien y la de `SetSeries` salía recta. Lo delató el log
  `p0/pmed/pfin` con los tres Y idénticos — no una hipótesis, una medición.
- **El arreglo**: `Bounds(In)` calcula mín/máx con `Math|Float|Min(Float)`/`Max(Float)` sobre el
  elemento del `for` (que sí es double), y `Normalize` usa `MapRangeClamped`, sin ninguna resta.
- 👉 **Regla que se lleva**: después de escribir aritmética por DSL, **releer el grafo y buscar
  `ToFloat(Integer)` que no escribiste**. Es la firma de una promoción a entero.

---

# BP_Portrait_SC — el actor

## Componente
`Panel` — `WidgetComponent` · `WBP_Portrait_SC` · `Space=World` · `DrawSize 1600×900` ·
escala **0.06** · **`blendMode = Transparent`** (con `Masked`, que es el default, los bordes curvos
salen con diente de sierra — gotcha §214) · `tickMode = Automatic` · **`relativeRotation` yaw 0**.

🔴 **El yaw va en el ACTOR, no en el componente.** Con yaw 180 en los dos, el panel quedaba mirando
para el lado contrario y **no se veía nada** en PIE. Un solo control: el actor.
🔴 **La colisión se apaga por código en `BeginPlay`** (`SetCollisionEnabled = NoCollision`): un
`WidgetComponent` world-space usa el perfil `UI`, que **bloquea el canal Visibility** y se comería el
beam de la exploración de F5 (gotcha §54). Ponerlo en el CDO no alcanza: la instancia lo revierte.

## Variables
| Variable | Default | Rol |
|---|---|---|
| `SoulTag` | `portrait_soul` | El TargetPoint al que se corre la ameba. |
| `FadeTime` | 1.5 s | Cuánto tarda el panel en encenderse/apagarse. |
| `bShowSignature` | true | Si además dispara `ShowSignature()` del sensor. |
| `Opacity` / `FadeGoal` / `bShown` | — | Estado del fundido. |
| `SCalm` / `SHeart` / `SBreath` / `bFed` | — | Los CSV cacheados, para poder **re-alimentar** el widget si el componente lo recrea. |
| `PanelW` / `ArchRef` / `SoulRef` | — | Refs cacheadas. |
| 🧪 `bDebugShowOnPlay` + `DebugShowDelay` | false · 8 s | Muestra el retrato sin recorrer la obra. |

## Estructura
- **`BeginPlay`** — opacidad 0, colisión off, tinte a 0, `MaybeShowOnPlay`.
- **`Tick`** — `CacheWidget` + `StepFade(Dt)`.
- **`CacheWidget`** — relee `GetUserWidgetObject` **cada tick** y, si cambió, re-alimenta.
  🔴 Es a propósito: un `WidgetComponent` puede **crear su widget dos veces** al arrancar (gotcha §34);
  cachear una sola vez deja pintando un widget que ya no es el que se ve.
- **`Show(Soul)`** — `FadeGoal=1` → `Grab` → `PlaceSoul` → `PlaceDraw`.
- **`Grab`** — encuentra el [[BP_SoulArchive_SC]], le pide **`CollectOnly()`** y se copia los tres CSV.
  🔴 **El retrato no recolecta nada por su cuenta**: el archivo es el único recolector, y así el mismo
  `bFakeData` que rellena el `.sav` rellena el panel — una sola puerta.
- **`PlaceSoul`** — `Soul.MoveTo(SoulTag)`.
- **`PlaceDraw`** — `Sensor.ShowSignature()`, sin tocar el sensor.
- **`StepFade`** — `FInterpToConstant` sobre `Opacity` → `SetTintColorAndOpacity` del componente
  (el fundido barato por material, no Widget Animation).
- **`Hide()`** — `FadeGoal=0`. Todavía no lo llama nadie (lo va a llamar F3 al enganchar el gesto).

## El enganche en el guión ([[BP_Director_Story]], `RunEnding` sub 6)
```
Say(VOEnd1=VO 31)  →  ShowPortrait()  →  WaitFor "timer"  →  ArmWait
```
- **`ShowPortrait()`** (nueva, en el director): arma el timer de **`PortraitHold`** segundos hacia
  `EndingWaitDone` y llama a `Portrait.Show(WinnerRef)`.
- 🎛️ **`PortraitHold` = 20 s** (instance-editable) — es "el rato de contemplación" del paso 4 del plan.
  ⚠ Se puso **en la instancia además del CDO**: las variables instance-editable **nacen en 0** en el
  actor ya colocado.
- La espera pasó de `"vo"` a `"timer"`: ahora el VO 31 suena **dentro** de los 20 s en vez de mandarlos.
- Cirugía mínima: **un nodo insertado y un valor de pin cambiado**. No se tocó nada más de `RunEnding`.

## 🧪 Para MIRAR el retrato sin jugar la obra (dos interruptores)
1. `BP_SoulArchive_SC_C_0` → **`bFakeData = true`** (rellena calma, ritmo, respiración, melodía y dibujo).
2. `BP_Portrait_SC_C_1` → **`bDebugShowOnPlay = true`** (y `DebugShowDelay`, 8 s por defecto).

Play, y a los 8 s aparece el retrato lleno. **Las dos quedan en `false`.**
⚠ `bFakeData` sólo reemplaza lo que está **vacío o demasiado corto**: para calma y ritmo el umbral es
**60 caracteres** (menos de eso = no hubo corrida de verdad, sólo los pocos bins del salto de debug).
Ese número es un literal dentro de `FillGaps`, no una variable.

## 📌 Insumos de Beltrán
- **Dónde va el panel**: mover `BP_Portrait_SC_C_1` en el viewport (ya lo subió a Z=157). La fila de
  esferas de la melodía **cuelga del actor** vía `MelodyOffset`, así que se mueve con él.
- **`TP_portrait_soul`** (tag `portrait_soul`, hoy en 7640, **+45 Y**, 206): a dónde se corre la ameba.
  +Y es la **izquierda** del usuario, que camina hacia +X.
- 🔴 **`TP_signature_spot` hay que MOVERLO**: hoy está al lado de `soul_pick_6` (8091, +92, 411), que es
  el sitio del flujo viejo. Ahora la firma aparece en el momento del retrato, así que el punto tiene que
  ir **a la derecha de la ameba** (o sea −Y respecto de `TP_portrait_soul`), a la altura del retrato.
  La **escala del TargetPoint es la escala de la firma**.
- La diagramación fina de adentro del panel, en el Designer.

---

# 🎵 La melodía — las esferas REALES (decisión 6 del plan)

No es un dibujo de UI: son **`BP_SoundOrb_SC` de verdad**, las mismas de Attracting, spawneadas en una
fila y pulsadas en bucle. El orbe ya sabía hacer todo esto — lo único nuevo es quién le marca el pulso.

## Cómo funciona
```
Show()  →  StartMelody()
             ├─ StopMelody()      (limpia lo anterior: timer + Vanish de las esferas viejas)
             ├─ BuildMelody()     (parsea el CSV y siembra una esfera por entrada)
             └─ ArmBeat()         (timer LOOPING cada MelodyStep → MelodyTick)
MelodyTick()  →  avanza el paso 0..7 con wrap  →  Beat(i)  →  Orbs[i].PulseOnBeat()
```
- **`PairOrb(Tok)`** parte `"slot:clipId"` con `Utilities|String|Split` y valida los dos índices antes de
  sembrar. Un token corrupto se ignora en silencio — no rompe la melodía.
- **`OneOrb(Slot, ClipId)`** calcula la posición **en el espacio local del actor** (`TransformLocation`),
  así que **la fila se mueve con el panel**; spawnea, hace `Setup(null, null, clip, clipId)`,
  `Placed = true` y `Reveal()`.
  🔴 **Sensor y secuenciador van en nulo a propósito**: el orbe sólo los toca dentro de guards
  (`RefreshHover` tiene su `IsValid`, `FollowBeam` sólo si `Grabbed`), así que como pieza pasiva
  **no produce ni un `Accessed None`**. Verificado.
- **`StopMelody()`** limpia el timer por nombre y le manda `Vanish()` a cada esfera (que se encoge y se
  autodestruye). Lo llama también `Hide()`.

## 🎛️ El tempo sale del PAD, no de un número inventado
`StartMelody` calcula **`MelodyStep = PadSound.Duration / MelodySteps`**, que es exactamente lo que hace
`BP_Sequencer_SC.Boot`. Con `PadM1` da **0,6667 s por paso** y un compás de 5,33 s — **la melodía del
retrato suena al mismo tempo al que el usuario la armó**. Si `PadSound` queda en nulo, cae al knob
`MelodyStep`.
⚠ `Class|SoundBase|GetDuration` — hay **16** `GetDuration` distintos y el DSL agarra el de GeometryCache
por defecto (y el `read` de `Boot` **imprime justamente ese**, mal). Ver gotchas.

## Variables de la melodía
| Variable | Default | Rol |
|---|---|---|
| `MelodySounds` | los 20 clips de `Module1` | 🔴 **Copia** de `BP_Sequencer_SC.ModuleSounds`. `ClipId` es un índice directo a este array. |
| `PadSound` | `PadM1` | De dónde sale el tempo. |
| `MelodySteps` | 8 | El tamaño de la grilla (igual que `NumSteps` del secuenciador). |
| `MelodySpacing` | 16 cm | Separación entre esferas. |
| `MelodyOffset` | (0, 0, −45) | Dónde nace la fila, **relativo al actor**. |
| `MelodyScale` | 0.45 | Tamaño de cada esfera. |
| `MelodyStep` | 0.45 s | Fallback si no hay `PadSound`; lo pisa el cálculo del pad. |
| `Orbs` / `MelIdx` / `OrbCount` / `bMelodyOn` | — | Estado. |

🔴 **`MelodySounds` es una copia, y eso es deuda consciente**: el secuenciador vive en el sublevel de
Attracting, que **ya está descargado** cuando aparece el retrato, así que no se le puede preguntar. Si
algún día se agrega el Módulo 2, hay que **actualizar las dos listas**. La fuente de verdad sigue siendo
`BP_Sequencer_SC.ModuleSounds`.

## 🔴 Lo que costó el primer intento: 0 esferas sembradas
`BuildMelody` logueaó `melodia 0:3,2:8,4:14,7:5 - esferas reales sembradas = 0`. El CSV estaba perfecto.
La causa: **las variables instance-editable nuevas nacen en CERO en el actor ya colocado** — `MelodySteps`
valía 0 (así que `Orbs` se redimensionó a 1 y sólo el slot 0 pasaba el `IsValidIndex`) y `MelodySounds`
estaba **vacío** (así que tampoco pasaba el slot 0). Compilaba, corría y no decía nada.
👉 El log que lo delató fue el **contador** (`sembradas = N`), no una hipótesis. Vale la pena que las
funciones que siembran cosas cuenten y lo digan.

---

## TODO
- [ ] Escalar el dibujo para que su alto máximo iguale al de la ameba+anillos (§F2 del plan).
- [ ] `Hide()` enganchado al gesto de F3 (ya apaga panel **y** melodía).
- [ ] **Crossfade corto** al cambiar de vecino (decisión 7) — es de F5: hoy `StopMelody` corta seco.
- [ ] Visor.

## Relacionados
[[BP_SoulArchive_SC]] (`CollectOnly`, `bFakeData`) · [[BP_SoulHUD_SC]] (el patrón `OnPaint` + marco) ·
[[BP_Director_Story]] (`ShowPortrait`, sub 6) · [[BP_ProtoSoul_SC]] (`MoveTo`) ·
[[BP_Sensor_Soul]] (`ShowSignature`) · [[BP_BreathRing_SC]] (los puntajes por ciclo) ·
[[BP_ResultsPanel]] (el panel del esqueleto viejo, con barras por etapa)


---

## 2026-08-27 — F5: el mismo panel muestra el retrato de OTRO usuario

`Show(Soul)` sirve para el retrato **propio**: pide los datos al archivo con `CollectOnly()` (lo que hay
en el mundo ahora). Para la constelación hace falta lo contrario: los datos de **una entrada guardada**.

| Función nueva | Qué hace |
|---|---|
| **`ShowIndex(Index, Soul)`** | `SoulRef = Soul` · `FadeGoal = 1` · `bShown = true` · `GrabIndex(Index)` · `StartMelody()`. 🔴 **No** llama a `PlaceSoul` ni a `PlaceDraw`: de mover la ameba y de reconstruir el dibujo se encarga [[BP_Constellation_SC]]. |
| `GrabIndex(Index)` | Busca el archivo y, si está, `FeedIndex`. |
| `FeedIndex(Index)` | Si `Index` es válido en `Calm`, copia **las cuatro series de esa entrada** (`Calm`/`Heart`/`Breath`/`Melody`) a `SCalm`/`SHeart`/`SBreath`/`SMelody`, marca `bFed` y llama a `Feed()` — la misma puerta que usa el retrato propio. |

Con eso, cambiar de vecino es **una llamada**: la curva se redibuja, los anillos se recolocan y la
melodía se rearma con las esferas reales del vecino.

✅ Verificado en PIE (12 vecinos seguidos): series `180/180/4`, `180/180/5`, `180/180/6`, `180/180/7`…
y melodías distintas (`0:4,2:9,4:15,7:7` → `0:5,2:10,4:16,7:8` → …), 4 esferas reales cada una.
**Sin fuga de audio**: `StartMelody` arranca con `StopMelody`, y `BP_SoundOrb_SC.UpdateVisual` destruye
la esfera cuando `bDying` y `RevealT < 0,05`.

⬜ **Falta el crossfade** al cambiar de vecino: hoy la melodía anterior corta y arranca la nueva.


---

## 2026-08-27 (2ª tanda) — el panel fijo deja de ser el del vecino

Con la tarjeta viviendo dentro de [[BP_ProtoSoul_SC]], este actor **ya no muestra el panel del vecino**.
Le queda: el **retrato propio** (`Show`/`ShowIndex`, sin cambios) y ser el **director de la melodía**.

| Función nueva | Qué hace |
|---|---|
| **`FeedMelody(Index)`** | Lo único que la constelación le pide ahora: toma `Melody[Index]` del archivo y llama a `SwapMelody`. **No** enciende el panel. |
| `MelodyFromIndex(Index)` | El cuerpo, con el `IsValidIndex`. |

### La melodía ya no corta al cambiar de vecino
El "crossfade corto" del plan se resolvió como **continuidad de compás**, que es su versión musical:

| Función | Qué hace |
|---|---|
| `VanishLoop` / **`VanishOrbs`** | Sólo hace desaparecer las esferas y limpia el array. **No toca el timer.** |
| **`SwapMelody`** | `VanishOrbs` → `BuildMelody` → `bMelodyOn` → y **arma el pulso sólo si no estaba armado** (`bBeatArmed`). Cambian las notas, **la grilla sigue corriendo**. |
| `ArmFromPad` | Saca el paso del `PadSound` (`Class|SoundBase|GetDuration`) y llama a `ArmBeat`. Deduplica lo que antes vivía dentro de `StartMelody`. |
| `StopMelody` | Limpia timer + `bMelodyOn` + **`bBeatArmed`** + `VanishOrbs`. |
| `StartMelody` | `StopMelody` → `BuildMelody` → `MelIdx = -1` → `ArmFromPad`. Arranque limpio, para el retrato propio. |

⚠ **Deuda**: las esferas siguen naciendo relativas al transform de **este** actor, o sea en el atril
viejo, mientras la ameba y su tarjeta están en otro lado. Es lo único del conjunto que no viaja.

### En el widget: `WBP_Portrait_SC.SetHeading(S)`
Un nodo: `Widget|SetText(Text)` sobre el `Title`. Lo llama `FeedCard` con el `CardTitle` de la
constelación (`SOMEONE WHO WAS HERE`), así el retrato propio conserva `YOUR TRACE`.

⚠ Dos ids que cuestan encontrar:
- **`Widget|SetText` es el de `RichTextBlock`**; el de un `TextBlock` es **`Widget|SetText(Text)`**.
- Las variables del árbol de un widget viven bajo **`Variables|<NombreDelWBP>|`**
  (`Variables|WBP_Portrait_SC|GetTitle`), **no** bajo `Variables|Default|`.


---

## 2026-08-28 — las esferas viajan con su ameba: `OneOrb` ahora ATTACHEA

**El reporte:** *"Las esferas del sequencer no se están moviendo con la ameba, no están ancladas todavía.
Se quedan pegadas en el mismo lugar del world"* — y en la constelación, *"se ven al medio del world,
todas en el mismo lugar"*.

**La causa:** `OneOrb` spawneaba cada `BP_SoundOrb_SC` en una posición de MUNDO calculada a partir de
`OrbBase` (una foto de dónde estaba el ancla en ese instante) y **no las attacheaba a nada**. Si después
la ameba se movía — el viaje al punto de retrato, o el acercamiento de la estrella enfocada — las esferas
se quedaban donde nacieron. Y como en la constelación **todas las estrellas enfocadas van al mismo
`const_anchor`**, todas las filas terminaban en el mismo lugar.

### ✅ Lo que hace ahora
```
spawn en la identidad  →  Setup / SetPlaced / Reveal
AttachActorToComponent( orbe, alma.OrbAnchor, SnapToTarget × 3 )
SetActorRelativeLocation( orbe, MelodyOffset + (0, (slot − (n−1)/2) × MelodySpacing, 0) )
SetActorRelativeScale3D ( orbe, MelodyScale )
```

🔑 **`MelodySpacing`, `MelodyScale` y `MelodyOffset` pasaron a ser LOCALES al `OrbAnchor` del alma.** Como
ese ancla lleva escala `Size / RingSizeRef`, los tres números son **constantes** y el tamaño real de la
fila sale solo. A `Size = 0,3` (el `RingSizeRef`) la escala del ancla es 1, así que **los valores de hoy
(16 / 0,45) producen exactamente lo que se veía antes** y escalan desde ahí.
⚠ `MelodyOffset` pasó a **(0,0,0)**: el descenso de la fila ahora lo controla `OrbGapRel` del alma, y
tener dos perillas para lo mismo confunde. Hubo que ponerlo en cero **también en la instancia del nivel**.

💡 **El `Reveal` del orbe no pelea con esto**: anima la escala del **componente `Body`**, no la del actor
(`UpdateVisual` escribe `Body.RelativeScale3D` a partir de `BaseScale`). La escala relativa del actor
queda intacta.

🗑 `OrbBaseLoc` / `OrbBase` quedaron sin uso — el ancla se lee en vivo del alma.

### ⚠ Dos trampas del DSL en esta función
- **`SetPlaced` de otro Blueprint es un SETTER de variable: el valor va PRIMERO y el target segundo.**
  `(Class|BPSoundOrbSC|SetPlaced _orb true)` falla con *"Could not connect pin AsBP Sound Orb SC to
  Placed"*; lo correcto es `(Class|BPSoundOrbSC|SetPlaced true _orb)`. Es lo contrario del orden de una
  función normal (`Setup`), donde el `self` va primero.
- El read etiquetaba ese nodo como **`Class|BPIntroSequence|SetPlaced`** (colisión de nombres). El id
  bueno lo dio `find_node_types` con filtro `Placed`: `Class|BPSoundOrbSC|SetPlaced`.

### ✅ Medido en PIE
```
RETRATO: base de esferas en (7976.0, -582.175, 74.7)
RETRATO: esfera 0 en Y=-675.508  …  esfera 7 en Y=-488.842
```
Centro de la fila = −582,175 → **coincide exactamente con la base**. Paso = 186,67/7 = **26,67 cm**
(= 16 local × 1,667 de escala del ancla). Y la base cambia con cada vecino.
