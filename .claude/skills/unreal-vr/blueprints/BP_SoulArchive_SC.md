# BP_SoulArchive_SC + SG_Portrait_SC — el retrato persistido (Core/Flow/)

> Versión limpia (`_SC`) del viejo [[BP_SoulArchive]]. Nace del plan
> [`docs/PLAN-CIERRE-2026-08-27.md`](../../../../docs/PLAN-CIERRE-2026-08-27.md), **fase F1**.
> El viejo queda como referencia; **este es el que se usa en `L_SoulCharger`**.

- **refPath**: `/Game/SoulCharger/Core/Flow/BP_SoulArchive_SC.BP_SoulArchive_SC` · **parent**: Actor
- **En el nivel**: sí, colocado en `L_SoulCharger` (persistente) como `BP_SoulArchive_SC_C_0`, en el origen.
- **SaveGame**: `/Game/SoulCharger/Core/Flow/SG_Portrait_SC` · slot en disco `SoulPortraits`
  (`VR_Test/Saved/SaveGames/SoulPortraits.sav`).

## Status
🟢 **F1 verificada en PIE (2026-08-27)**, tres corridas:
1. Con `bDebugClearOnPlay` + `bDebugSeedFakes` + `DebugFakeCount=21`: se escriben 21 entradas,
   el FIFO deja **20** y **se va la más vieja** (el `stamp` 1 desaparece; la última es `stamp 21`).
   Los 9 arrays quedan alineados en cada paso (`20/20/20/20/20/20/20/20/20`).
2. Sin flags: **lee el `.sav` del disco** con las 20 y loguea la última entrada con contenido real
   (calmLen 1067 · heartLen 899 · respiración `0.76,0.31,0.34,0.85,0.81` · melodía `0:1,2:6,4:12,7:4` · dibujoLen 1923).
3. Con `bDebugAppendOnPlay` + `bFakeData`: **`AppendMeFromWorld` corre contra el mundo vivo** y mezcla
   real + ficticio (calma y ritmo REALES del BioHub — 3 casillas a los 12 s —, el resto relleno).
   Cero `Accessed None` en las tres.

⬜ Nadie de la obra lo llama todavía: el disparo real es **F3** (al compartir la ameba en el corazón).

---

# SG_Portrait_SC — el modelo de datos

**9 arrays paralelos**, una entrada por usuario. Paralelos y no un struct porque el MCP
**no puede agregar miembros a un `UserDefinedStruct`** (`F_SoulPortrait` sigue vacío).

| Campo | Tipo | Contenido |
|---|---|---|
| `Variants` | int[] | Índice del alma elegida dentro de `BP_SoulPicker_SC.Souls` |
| `Colors` | LinearColor[] | `CoreColor` de esa ameba |
| `Rings` | int[] | `RingsShown` (0..5) |
| `Calm` | String[] | CSV de hasta 180 valores 0..1 (una casilla de 5 s cada uno) |
| `Heart` | String[] | CSV de hasta 180 BPM |
| `Breath` | String[] | CSV de N puntajes 0..1, uno por ciclo de Entering |
| `Melody` | String[] | CSV `slot:clipId` |
| `Draw` | String[] | Trazos separados por `;`, puntos por `\|`, `x,y,z` con 1 decimal |
| `Stamp` | int[] | Contador de corrida (último + 1). Define quién es "el más viejo" |

## 🔴 El contrato de los CSV — leerlo antes de escribir el lector (F2/F5)
- **Separador de valores: la coma** en Calm/Heart/Breath/Melody.
- **`-1` = HUECO** en Calm y Heart (casilla sin muestras). Es inequívoco porque la calma es 0..1 y
  el ritmo siempre es mayor que 0. 🔴 **El lector TIENE que tratarlo como hueco, no como dato** — es la
  misma regla que el par `BinHas*`/`GetAvg` de [[BP_BioHub]] (§5 del guión: los huecos se dibujan
  *tenues*, no *rotos*).
- Los floats se redondean con `SnapToGrid` **antes** de `ToString(Float)`: calma 0.001, ritmo 0.1,
  respiración 0.01, dibujo 0.1. `SanitizeFloat` recorta los ceros de cola, así que salen cortos
  (`0.412`, `68.3`) — de ahí que 20 entradas ficticias pesen **82 KB** de `.sav`.
- **Dibujo**: `x,y,z|x,y,z;x,y,z|…` — el punto y coma abre trazo nuevo, la barra continúa el trazo.

## Registro de variables

### Config (instance-editable)
| Variable | Default | Rol |
|---|---|---|
| `SlotName` | `SoulPortraits` | Slot en disco. |
| `MaxEntries` | 20 | Tope del anillo FIFO. Al entrar la 21, sale la más vieja por el frente. |

### Estado
`Data` (el `SG_Portrait_SC` vivo) · `MyIndex` (dónde quedó mi ameba; −1 si todavía no compartí) ·
`Tmp` (String[] de andamio, se limpia al principio de cada serializador) ·
`SCalm/SHeart/SBreath/SMelody/SDraw/SVariant/SRings/SCol` (lo que junta `AppendMeFromWorld`) ·
`BioRef/RingRef/SeqRef/CanvasRef/PickRef` (las fuentes, cacheadas por `CacheSources`).

### 🧪 Flags de debug — **todas quedan en `false`**
| Flag | Qué hace |
|---|---|
| `bDebugClearOnPlay` | Borra el slot y arranca de cero. |
| `bDebugSeedFakes` + `DebugFakeCount` (6) | Siembra N entradas falsas **completas y distintas** vía `MakeFake`. |
| `bDebugAppendOnPlay` + `DebugAppendDelay` (8 s) | Timer que llama a `AppendMeFromWorld` sin jugar la obra. |
| `bFakeData` | **§6.b del plan**: rellena con ficción *sólo los campos que quedaron vacíos*. |

🔴 **`bFakeData` no escribe las variables finales de nadie**: genera CSVs y los mete por
**la misma puerta que el dato real** (`AppendMe` → el mismo `.sav`). Mismo criterio que
`bFakeSignal` del BioHub. Un modo debug que escribiera el widget directo no probaría nada.

## API
| Función | Qué hace |
|---|---|
| `LoadArchive()` | Si el slot existe lo carga y castea; si no, `EnsureData`. Después `ReportArchive`. |
| **`AppendMe(Variant, RingsN, Col, CalmCSV, HeartCSV, BreathCSV, MelodyCSV, DrawCSV)`** | Escribe los 9 campos **en una sola función** (mitigación del desalineado), calcula `Stamp` = último+1, fija `MyIndex`, `TrimArchive`, `SaveArchive`, `ReportArchive`. |
| **`AppendMeFromWorld()`** | 🔴 **La puerta de entrada de F3.** Resetea, `CacheSources`, los cinco `Take*`, `FillGaps`, y llama a `AppendMe`. |
| `CacheSources()` | `GetActorOfClass` + cast de BioHub, BreathRing, Sequencer, DrawCanvas y SoulPicker. |
| `TakeBio/TakeRing/TakeSeq/TakeCanvas/TakeSoul()` | Una fuente cada una, con su `IsValid`. Si la fuente no está, el campo queda vacío (**sin `Accessed None`**). |
| `FillGaps()` | Si `bFakeData`: reemplaza **sólo lo vacío** con ficción (`SelectString`). |
| `TrimArchive()` | FIFO: mientras haya más de `MaxEntries`, saca el índice 0 **de los 9** y baja `MyIndex`. |
| `Count()` | Cuántas entradas hay (0 si no hay `Data`). |
| `ReportArchive()` / `ReportLast()` | Log de los 9 largos / de la última entrada con su contenido. |
| `MakeFake(Seed)` · `FakeSeries(Seed,bHeart)` · `FakeBreath(Seed)` · `FakeDraw(Seed)` | Generadores deterministas por semilla (senos de dos frecuencias: nunca una recta ni valores todos iguales). |
| `MaybeClearArchive()` · `DebugSeedFakes()` · `MaybeAppendOnPlay()` | Los tres gates de debug, llamados desde `BeginPlay`. |

**`BeginPlay`** = `MaybeClearArchive` → `LoadArchive` → `DebugSeedFakes` → `ReportLast` → `MaybeAppendOnPlay`.

## 🔴 Trampas pagadas acá
1. **`Array|Add` / `Array|RemoveIndex` sobre el array de OTRO objeto opera sobre una COPIA.**
   El patrón correcto es **leer → modificar → volver a escribir**, con `bind` de por medio
   (el compilador crea **un solo temp** para el getter, y ése es el que se muta y se re-escribe):
   ```
   (bind _v (Class|SGPortraitSC|GetVariants _d))
   (Utilities|Array|Add _v Variant)
   (Class|SGPortraitSC|SetVariants :self _d :Variants _v)
   ```
   ⚠ El `TrimArchive` **del BP viejo está roto por esto**: hace `RemoveIndex` sobre el getter sin
   `bind` ni re-escritura, así que nunca recortó nada (no se notó porque `MaxEntries` era 60).
2. **`select` evalúa las DOS ramas** → dividir por `Count` dentro de un `select` **divide por cero**
   en las casillas vacías y ensucia el log. Se arregla con `Max(Integer) Count 1` en el divisor
   (está así en `BP_BioHub.Series`).
3. **`add_function_graph` con un nombre recién borrado devuelve `Nombre_0`**: para rehacer una función
   hay que `remove_function_graph` → **`compile_blueprint`** → `add_function_graph`.
4. El `read_graph_dsl` **rotula mal la clase** de los getters homónimos (muestra `Class|BPBioHub|GetCalm`
   sobre el SaveGame, y `Class|BPSoulArchive|EnsureData` sobre una llamada a sí mismo). Se confirma con
   `get_node_infos`: el `type_id` real era `|EnsureData` con el pin `self` sin conectar = auto-llamada.

## Relacionados
[[BP_BioHub]] (`Series`) · [[BP_BreathRing_SC]] (`SerializeBreath`) · [[BP_Sequencer_SC]] (`SerializeMelody`) ·
[[BP_DrawCanvas]] (`SerializeDraw`) · [[BP_SoulPicker_SC]] (`Winner`/`Souls`) · [[BP_ProtoSoul_SC]] ·
[[BP_SoulArchive]] (el viejo) · [[BP_Constellation]] / [[BP_ConstExplorer]] (F4/F5)

---

## 🤖 2026-08-27 (noche) — campaña de pasadas completas con el robot

**Qué se pidió**: pasadas completas de la obra con el robot simulando la interacción, sin cortafuegos
salvo donde sean inevitables, y 2-3 repeticiones para ver si el SaveGame acumula gente nueva.

### 🔴 El límite que apareció primero
**`RunAuto` (rutina 0) del robot está atado a `BP_StageDirector`** — el director del esqueleto VIEJO,
que no existe en `L_SoulCharger`. En el nivel V2 `StageIdx` devuelve −1 y la rutina no hace nada.
👉 **Lo único que el robot sabe hacer hoy en V2 es dibujar en Surrounding (rutina 3).**
Las rutinas de Entering, Recognizing, Loving y Attracting hay que **construirlas para V2**.

### Veredicto de la pasada completa (obra entera, `DebugStartRoom = -1`, `bAutoTest = true`)
| Etapa | Cómo cerró |
|---|---|
| Hall | 🟢 interacción (autotest fuerza el hover+gatillo, que es el camino real) |
| **Entering** | 🔴 cortafuego — 90 s. El robot no respira. |
| **Recognizing** | 🔴 cortafuego — **240 s exactos**. El robot no hace latido. |
| Loving | 🟢 sin cortafuego (`StepTimes[3]` = 0) |
| **Attracting** | 🔴 cortafuego — 300 s. El robot no coloca esferas. |
| **Surrounding** | 🟢 **interacción: 29 s** — el robot dibujó los 10 m con `StepTimes[5]` en 300 |
| Final | 🟢 entero por el camino real |

### 🐛 Dos bugs que sólo aparecen en una corrida REAL
Las verificaciones anteriores usaban datos ficticios, así que estos dos nunca se habían visto.

**1. El dibujo del usuario NO se guardaba (`dibujoLen = 0`).**
`TakeCanvas` buscaba el canvas con `GetActorOfClass` **en el paso 8**, y para entonces ya no existe.
El instrumento lo cantó: `ARCHIVO: NO hay canvas al guardar - el dibujo se pierde`, y después
`ARCHIVO: no habia canvas al cerrar la sala` — o sea que **ni siquiera al empezar el final** estaba.
✅ **El arreglo no fue buscarlo más tarde sino capturarlo antes**: `BP_Sensor_Soul.KeepSign()` guarda el
CSV en `SignCSV` **dentro de `DrawFinish`** — el instante exacto en que el dibujo se completa y el canvas
con seguridad existe (la función hasta le llama `EndStroke`) — y `TakeCanvas` lo lee del sensor.
Verificado: `firma guardada al terminar el dibujo, largo = 6129` → `firma tomada del sensor, largo = 6129`.

**2. Los anillos se guardaban en 0.** Dos causas encadenadas:
- **`DrawRing` nunca tocaba `RingsShown`** — el único que lo incrementaba era `TickRingKey`, o sea el
  camino de **teclas de debug**. En una corrida real el contador se quedaba en 0 para siempre.
- **`TakeSoul` dependía de `PickRef`**, que llega en None al guardar. La versión original tenía un
  `IsValid(PickRef)` que **se tragaba el problema en silencio**; al reescribirla apareció el
  `Accessed None` y con él la causa.
✅ Arreglos: `DrawRing` hace `RingsShown = max(RingsShown, Index+1)`, y `TakeSoul` ya no depende del
picker: toma el alma del **`WinnerRef` del director** (`SoulFromDirector`), que es la fuente confiable en
ese momento; el picker sólo se usa para resolver el índice de variante (`VariantOf`).
Verificado: `ARCHIVO: alma ganadora - anillos = 5`.

### ✅ El SaveGame acumula
Los `Stamp` de las pasadas sucesivas: **25 → 26 → 27 → 28 → 29**, con el FIFO sacando la más vieja cada
vez (`ARCHIVO: se fue la mas vieja (FIFO)`, largos siempre `20/20/…`). La última entrada quedó completa:
```
stamp 29 | variante 0 | anillos 5 | calma 1052 | ritmo 899 | respiracion — | melodia — | dibujo 6129
```

### ⬜ Lo que sigue vacío, y por qué
`respiracion` y `melodia` quedan vacías **porque el robot no puede producirlas todavía** (Entering y
Attracting cierran por cortafuego). No es un bug del guardado: es la consecuencia directa del límite de
arriba. Se llenarán solas cuando existan las rutinas V2 — o en la primera corrida con gafas.

### ⚠ Otro hallazgo
**Con `DebugStartRoom = 5` la práctica de dibujo no se completa** y la etapa se queda trabada. Por el
flujo real (`DebugStartRoom = -1`) cierra en 29 s. Es un problema del atajo de debug, no de la obra.

### Estado en que quedó todo
`RobotOn = 0` · `HeadOn = 0` · `Routine = 3` · `DebugStartRoom = 5` (el de Beltrán) · `bAutoTest = false` ·
**`StepTimes` de vuelta en los valores de obra `[0, 90, 240, 0, 300, 300]`** · todas las flags de debug
del archivo, la constelación, el retrato y el picker en `false`.
