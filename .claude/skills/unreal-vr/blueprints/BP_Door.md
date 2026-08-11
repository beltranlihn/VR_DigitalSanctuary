# BP_Door — la puerta entre salas (Core/Doors/)

## Purpose
El umbral entre etapas, según `docs/OBRA-SOUL-CHARGER.md` §9.8. **Un solo Blueprint para las cinco puertas**: el nombre de la etapa y el color de acento son variables que setea el director, así que cambiar el look de una puerta es cambiar datos, no editar el BP.

🔴 **La puerta NO existe durante la etapa.** Se revela al terminar: una línea de luz traza el marco sobre el muro, se enciende el cartel, y recién ahí abre. Dos motivos del doc: que la sala esté sellada comunica *"esto es lo único que tienes que hacer ahora"*, y evita que un elemento arquitectónico compita con el objeto reactivo en una sala que es casi vacío.

## Status
🟡 **Construido y compilando. Falta el test en visor.** Creado 2026-08-11 (rama `core/esqueleto`).
Colocada una instancia en `L_Room_Placeholder` en **(460, 0, 0)**, con los flags de prueba encendidos (ver "Ganchos de prueba").

## Componentes
Ejes locales: **+X = la dirección en la que se atraviesa** · Y = ancho · Z = alto. El origen del actor está en el piso, al centro del vano.

| Componente | Medidas | Posición local | Material |
|---|---|---|---|
| `PanelL` / `PanelR` | 10 × 150 × 400 cm cada uno → vano de **3 m × 4 m con 10 cm de espesor** (§9.8) | Y = ∓75, Z = 200 | `MI_DoorPanel` (muy oscuro, 0.04) |
| `Backdrop` | 10 × 460 × 560 cm | X = +45, Z = 225 | `MI_DoorBlack` (negro puro) |
| `BarL` / `BarR` | barras verticales del marco, 4 × 6 cm de sección | X = −8, Y = ∓153 | `MI_DoorGlow` (brillo 3) |
| `BarTop` | el dintel | X = −8, Z = 413 | `MI_DoorGlow` |
| `Sign` | `TextRenderComponent`, `worldSize` 40, centrado | X = −10, Z = 440, **yaw 180** para mirar hacia la sala | el suyo |

🔴 **El `Backdrop` es "el plano negro detrás" del §9.8 — es lo que hace funcionar el vacío.** Sin él, al abrirse la puerta se vería lo que haya más allá del muro en vez de negro absoluto.

ℹ️ **Por qué `TextRenderComponent` y no un widget UMG:** es mucho más barato en Quest y no arrastra el mundo de trampas de `widgets-vr.md` (world-space obligatorio, `TickMode` que no viene en `Automatic`, etc.). Para un cartel de una línea, alcanza.

## Registro de variables

### Autoral — las setea el director (§9.8: "desde el DataAsset de la etapa")
| Variable | Tipo | Rol |
|---|---|---|
| `StageName` | Text | **El nombre de la sala A LA QUE VAS**, no la que dejás. Por eso revelarlo al final es el momento correcto. |
| `AccentColor` | LinearColor | Color del marco, del cartel y del tinte de los paneles. §9.8: la luz que se cuela y el cartel **son de la sala que viene** — ya es rojo si vas a Recognizing, verde si vas a Surrounding. |

### Tiempos y geometría (instance-editable)
| Variable | Default | Rol |
|---|---|---|
| `RevealTime` | 2.5 s | Cuánto tarda el trazado del marco + el encendido del cartel. |
| `OpenTime` | 2.0 s | Cuánto tarda la apertura. |
| `PanelSlide` | 155 cm | Cuánto se corre cada panel. |
| `BarHeight` | 420 cm | Largo final de las barras verticales. |
| `BarSpan` | 312 cm | Largo final del dintel. |

### Estado
| Variable | Rol |
|---|---|
| `RevealProgress` / `RevealTarget` | Progreso 0..1 y su destino (0 o 1). `Reveal()` pone el target en 1. |
| `OpenProgress` / `OpenTarget` | Igual para la apertura. `Open()`→1, `Close()`→0. |
| `bPassed` | Se puso una sola vez, para que `OnPawnPassed` no se dispare cada frame. |
| `PawnRef` | El pawn. Se cachea en `BeginPlay` y **se re-busca si queda inválido**. |

### Dispatcher
- **`OnPawnPassed`** — lo consume el director para saber que el umbral quedó atrás.

## Estructura de grafos

**Interfaz pública (§9.8):** `Reveal()` · `Open()` · `Close()` · `Configure(NewStageName, NewAccent)`.

**`Reveal()`** — escribe el `StageName` en el cartel y pone `RevealTarget = 1`.
**`Open()` / `Close()`** — mueven `OpenTarget` a 1 / 0. La animación la hace el Tick.

**`Configure(NewStageName, NewAccent)`** — setea las dos variables, el texto del cartel, y aplica el acento a las 5 mallas con `SetVectorParameterValueOnMaterials`.

**`ApplyReveal(P)`** — el trazado del marco, en dos fases sobre un solo progreso:
- `P` 0 → 0.55: las **barras verticales crecen desde el piso** (escala en Z **y** posición en Z/2, porque escalar un cubo lo agranda desde su centro).
- `P` 0.45 → 0.85: el **dintel crece desde el centro hacia afuera** (solo escala en Y).
- `P` > 0.85: aparece el cartel.
Las fases **se solapan a propósito** (0.45 < 0.55): el dintel arranca antes de que las verticales terminen, así el trazo se lee como un gesto continuo y no como tres pasos.

**`ApplyOpen(P)`** — los paneles se separan en Y: `∓(75 + PanelSlide·P)`.

**`UpdateDoor(Delta)`** — 🔴 **deliberadamente SIN ramas.** Avanza los dos progresos y aplica los dos siempre:
```
step = (Target·2 − 1) · Delta / Time      ; Target sólo vale 0 o 1 → +step o −step
Progress = Clamp01(Progress + step)
```
Es la forma sin branches de un "mover hacia el objetivo", y existe así porque **el parser del DSL sólo admite un nodo multi-exec y va al final** (ver `references/dsl.md`). Cuesta dos `SetRelativeLocation` por frame de más cuando la puerta está quieta; a cambio el grafo es trivial y no puede quedar a medio camino.

**`CheckPawn()`** — el único `IsValid` del pawn. Adentro llama a `CheckPassed` y `TryApproach`; si el pawn es inválido, lo vuelve a buscar. Existe para que las otras dos no tengan que revalidar.

**`CheckPassed()`** — cruce por **producto punto**, no por volumen de colisión:
```
dot(pawnLoc − doorLoc, doorForward) > 0  →  bPassed = true, OnPawnPassed
```
🔴 **Por qué no un trigger de overlap:** el pawn se mueve con `SetActorLocation` desde `BP_Walker` y no está garantizado que tenga una primitiva de colisión que genere overlaps. El producto punto es determinista, funciona con la puerta rotada en cualquier ángulo, y no depende de cómo esté armado el pawn.

**`TryApproach()`** — si `bAutoOpenOnApproach` y el pawn está más cerca que `AutoOpenDistance` y la puerta todavía no abrió → `Open()`.

**`EventGraph`**
- `BeginPlay`: cachea el pawn, esconde el cartel, `Configure` con los valores de la instancia, `ApplyReveal(0)` + `ApplyOpen(0)` (para que **nazca cerrada y sin marco** aunque el editor la haya dejado a medias), y si `bRevealOnBeginPlay`, revela.
- `Tick`: `UpdateDoor(Δt)` y `CheckPawn()`. Dos llamadas a función, cero ramas.

## Ganchos de prueba (se sacan cuando exista `BP_StageDirector`)
| Variable | En la clase | En la instancia de `L_Room_Placeholder` |
|---|---|---|
| `bRevealOnBeginPlay` | **false** | **true** — así la puerta ya está trazada y sirve de **referencia de avance** mientras caminás. |
| `bAutoOpenOnApproach` | **false** | **true** |
| `AutoOpenDistance` | 260 cm | **300 cm** |

⚠ **Esto NO es la secuencia autoral.** En la obra el orden del §9.2 es: la luz de la sala baja → se traza el marco → se enciende el cartel → negro → swap → **y la puerta abre del otro lado**, revelando la sala nueva. El auto-open por proximidad existe sólo para que la caminata sea testeable sin el director.

## Session log
- **2026-08-11** — creado. Verificado que el `Configure` del `BeginPlay` es **el propio de la puerta** y no el homónimo de `BP_Room`: el `read_graph_dsl` lo mostraba como `Class|BPRoom|Configure`, pero `get_node_infos` confirma `type_id = "|Configure"` con `self` de tipo *Self Object Reference* y los parámetros `NewStageName`/`NewAccent`. Es el caso de mislabel por colisión de nombres que ya avisa `gotchas.md` — **con dos clases que tienen un método del mismo nombre, hay que verificar el nodo, no el read.**
- La puerta quedó en X=460 y no en 500 (el muro) para que el pawn, que termina la caminata en X=500, **efectivamente la cruce** y `OnPawnPassed` dispare. Contra un muro oscuro los 40 cm no se notan.

## TODO
- [ ] **Test en visor.**
- [ ] Los paneles hoy están visibles desde el principio (son muy oscuros, así que contra el muro apenas se leen). La versión autoral debería **fundirlos** durante el `Reveal` en vez de tenerlos ahí: §9.8 quiere que la sala esté *sellada*.
- [ ] Que `BP_StageDirector` llame `Configure` + `Reveal` + `Open` en el orden del §9.2, y que se saquen los dos flags de prueba.
- [ ] La luz que se cuela por la rendija (§9.8) no está: hoy detrás sólo hay negro. Va cuando la sala siguiente ya se precargue de verdad.

## Open questions
- ¿El trazado de 2,5 s es el tiempo correcto? Tiene que leerse como un gesto, no como una animación de UI.
- El cartel en `TextRenderComponent` no tiene la tipografía de la obra (`Core/Font/Quicksand`). Se puede asignar por `SetTextMaterial`/font, pero conviene decidirlo con el look final.

## Relacionados
- [[BP_Room]] (dueña del muro donde vive el marco) · [[BP_Walker]] · `BP_StageDirector` (sin construir)
