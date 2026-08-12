# BP_MenuButton — botón por CONTACTO + trigger (Core/UI/)

## Purpose
Los botones del menú de la intro (**START** / **ABOUT US**) y, más adelante, el **timbre** del Center. Se acercan con la mano y se confirman con el gatillo.

## Status
🟡 **Construido y compilando** (2026-08-12), con la cadena de input verificada nodo por nodo. ⬜ **Falta colocarlo, armarlo desde la intro y suscribirse a `OnPressed`** (ver TODO).

## 🔴 Por qué por CONTACTO y no por beam — decisión de Beltrán
Se lo consultó explícitamente y la respuesta fue **tocando + trigger**, y la razón es el **arco de gestos de la obra**:
```
menú (tocar)  →  timbre (apoyar la mano)  →  sensor (tomar)  →  beam (recién en Attracting)
```
El menú es la **primera** interacción. Si arrancara con beam, se enseñaría el puntero para abandonarlo durante cuatro etapas y recuperarlo al final. Tocando, **rima con el timbre que viene tres segundos después** y con tomar el sensor, y el beam queda como **capacidad nueva** que aparece en *Attracting*. Además enseña "tus manos son reales acá", que es la tesis de la obra.

💡 **`HoldTime` hace que el mismo Blueprint sirva para el timbre.** En **0** confirma al apretar el gatillo (los botones del menú). En **> 0** hay que sostener — que es lo que Beltrán definió para el timbre: *"el timbre que sea con esperar, los otros botones con hover más trigger"*.

## Componentes
| Componente | Qué es |
|---|---|
| `Plate` | Cubo escalado a **3 × 28 × 10 cm**, material `M_IntroLogo` (unlit emisivo). Es lo que crece con el hover. |
| `Label` | `TextRenderComponent`, `yaw 180`, worldSize 6. 🔴 Con **`M_TextUnlit`** desde el día uno: el material de fábrica es *lit* y en esta obra **no hay luces**, así que se vería negro (ver `materials-vr.md`). |

## Registro de variables
| Variable | Default | Rol |
|---|---|---|
| `LabelText` | "START" | El texto. Instance-editable: dos instancias, dos textos, un solo BP. |
| `HoverRadius` | 18 cm | Qué tan cerca tiene que estar la mano. |
| `HoldTime` | **0** | 0 = confirma al apretar. > 0 = hay que sostener (el timbre). |
| `HoverScale` / `HoverSpeed` | 1.18 / 8 | Cuánto crece al hover y qué tan rápido. |
| `bArmed` | false | 🔴 **Nace desarmado**: el botón no existe para el usuario hasta que la intro lo arma. Sin esto, apretar el gatillo en cualquier momento de la obra dispararía el menú. |
| `bDone` | false | Ya se apretó; no vuelve a disparar. |
| `BaseScale` | — | 🔴 **Vector, capturado en BeginPlay.** Ver la trampa de abajo. |
| `HandL` / `HandR` | — | Los motion controllers (pose **Grip**), del pawn. |
| `bTrigHeld` · `HoverT` · `HoldT` | — | Estado. |
| **`OnPressed`** | dispatcher | Lo que consume la intro. |

## Estructura de grafos
- **`BeginPlay`** — captura `BaseScale` · `CacheHands` · `ApplyLabel`.
- **`Tick`** — **sólo si `bArmed`** → `TickStep(Δ)`.
- **`TickStep`** — `RefreshHover` · `UpdateVisual` · y sólo si hay hover, `UpdateHold`.
- **`RefreshHover`** — pone `bHovered = false` y llama `CheckHand` **una vez por mano**. Setear-false-y-desmentir es más corto que contar.
- **`CheckHand(H)`** — **distancia al cuadrado contra radio al cuadrado** (receta de [[BP_Sensor]]: evita la raíz y esquiva `Math|Vector|Distance`).
- **`UpdateHold`** — si el gatillo está sostenido acumula, si no resetea a 0. **Soltar cancela siempre.**
- **`TickHold`** — al pasar `HoldTime` llama `Fire()`. Con `HoldTime = 0` eso es el primer frame con gatillo + mano cerca.
- **`Fire`** — `bDone = true`, se desarma, loguea y **hace el broadcast al final**, con el estado ya consistente.
- **`UpdateVisual`** — move-toward de `HoverT` y `escala = BaseScale × (1 + HoverT×(HoverScale−1))`.
- **`Arm` / `Disarm`** — la API que usa la intro.

### El input, por cirugía
El DSL **no puede crear eventos de input**. Van con `create_node` + `connect_pins`:
- type_id **`Input|EnhancedActionEvents|IA_Shoot_{Right,Left}`** (⚠ **no** `AddEvent|Input|EnhancedInputAction|…`, que no existe).
- **`Triggered` = pin 0 → `bTrigHeld = true`** · **`Completed` = pin 4 → false**.
- `IA_Shoot_L/R` del XRFramework es **la única acción de trigger que se entrega de verdad** en este proyecto, y **un actor suelto del nivel la recibe** (validado en visor con el pincel de Movement).
- ⚠ El `read_graph_dsl` muestra estos eventos **vacíos** aunque estén bien cableados. Verificado con `get_node_infos`: los 4 cables están.

## ⚠ Trampas heredadas (ya pagadas en otros BP)
- 🔴🔴 **`SetRelativeScale3D` con un escalar uniforme PISA la escala autoral.** En `BP_SaveButton` apareció un cilindro de 1 m tapando la vista. La escala **parte de `BaseScale`** (Vector, capturado en BeginPlay), nunca de 1.
- 🔴 **`bArmed` genera `GetArmed`/`SetArmed`, sin la `b`.** Ídem `bHovered`, `bTrigHeld`, `bDone`.
- ⚠ Llamar una función propia con parámetros desde el DSL: el primer pin posicional es **`self`** → usar keyword (`:H`, `:Delta`).

## TODO
- [ ] 🔴 **Colocar las dos instancias y ubicarlas al alcance del brazo.** Van **a ~45 cm**, no en el panel del título (que está a 200 cm): sentado, el brazo llega a 50-60 cm. Lo más limpio es que la intro las reposicione en runtime con la misma receta de `PlaceStep` (cámara + forward por yaw), a ±15 cm del centro.
- [ ] 🔴 **Que la intro las arme al mostrar el título** (`Arm()`) y se suscriba a `OnPressed`: START → `HideTitleAndGo()` (que ya existe y hace el fundido); ABOUT US → el panel de texto.
- [ ] **Desarmar el que no se apretó** cuando se elige uno.
- [ ] Aserciones en [[BP_SelfTest]]: que haya exactamente 2, con textos distintos, y que **nazcan desarmados**.
- [ ] Material propio con acento de color (hoy usa `M_IntroLogo`, que es el del logo).
- [ ] Test en visor: si 18 cm es cómodo o si conviene más grande, y si el crecimiento se lee.

## Relacionados
- [[BP_IntroSequence]] (quien los arma y los consume) · [[BP_Sensor]] (la receta de proximidad por mano) · `BP_SaveButton` (hover + hold + la trampa de la escala) · `references/assets-existentes.md` (por qué `IA_Shoot_*`)
