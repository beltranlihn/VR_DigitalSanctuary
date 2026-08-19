# BP_InstructionsPanel_SC + WBP_Instructions — instrucciones por etapa

> `/Game/SoulCharger/Core/UI/` · creado 2026-08-18 · una instancia en el hall (`BP_InstructionsPanel_SC_C_0`, persistente, `250,0,150`, yaw 180).
> **Estado: 🟡 widget + contenedor construidos y compilados, visibles en editor. Faltan los botones físicos.**

---

## La decisión que define todo: **`WidgetSwitcher`**, no un array
Beltrán lo planteó exactamente bien: *"más que hacer un array, me gustaría poder ver directo en el editor de widget el diseño de cada página, y mover los elementos a mi libertad. ¿Eso sería armar varios canvas?"*

**Sí, y UMG tiene el contenedor hecho para esto.** `WidgetSwitcher` = una página por hijo:
- Cada hijo es un **Canvas Panel** → posicionamiento libre, arrastrar donde quiera.
- Su propiedad **`activeWidgetIndex` es editable en el Designer** → escribe un número y el Designer **muestra esa página**. Diseña cada una viéndola.
- Agregar una página = agregar un Canvas al switcher (o duplicar uno existente con click derecho). **Cero código, cero array que mantener en paralelo.**
- En runtime `SetActiveWidgetIndex` cambia de página.

💡 **Y encima es la opción barata.** Epic advierte que los Canvas Panel son caros en CPU (*"Canvas Panels using multiple draw calls, thus making them highly CPU-intensive"*), pero **el switcher sólo renderiza el hijo activo** → se paga un canvas, no N. Así que la ergonomía y la performance apuntan al mismo lado.

## Árbol del widget
```
Root (Overlay)              ← barato, sin anchors
├─ Bg    (Image)            ← color de fondo, lo pisa el BP por nivel
└─ Pages (WidgetSwitcher)   ← 🔴 UNA PÁGINA POR HIJO
   ├─ Page_0 (CanvasPanel) → Img_0 + Txt_0
   ├─ Page_1 (CanvasPanel) → Img_1 + Txt_1
   └─ Page_2 (CanvasPanel) → Img_2 + Txt_2
```
Las 3 páginas son **semilla**: imagen arriba (anclas 0.10-0.90 × 0.07-0.55), texto abajo (0.08-0.92 × 0.62-0.95), fuente 34, centrado, auto-wrap. Están por anclas relativas, así que se acomodan solas si cambia el `DrawSize`.

**Una sola función en el widget:** `Setup(Index, Color)` — cambia de página y aplica el fondo. Nada más.

## El contenedor
| Grupo | Variables |
|---|---|
| **0 - Paginas** | `StartIndex` (0) · `EndIndex` (2) — el **rango de páginas de este nivel** |
| **1 - Aspecto** | `BgColor` · `PanelWidth` (90 cm) |
| **2 - Enlace** | `PanelTag` (`instr_hall`) — con esto lo van a encontrar los botones |
| **Z - Estado interno** | `PageIndex` |

**API pública: `Apply(Index)` y `Step(Delta)`.** Los botones llamarán `Step(+1)` / `Step(-1)`; un `Delta` en vez de dos funciones Next/Prev deja además saltar de a dos si algún día hace falta.

🔴 **`EndIndex` no estaba en el plan de Beltrán y hace falta.** Si un solo widget guarda las páginas de TODAS las etapas, el botón "siguiente" del Breath caminaría hasta las páginas del Heart. Con `StartIndex`/`EndIndex` cada nivel **es dueño de un rango** y `Apply` clampa contra él. Es la única adición a su diseño.

- **Construction Script**: escala el `WidgetComponent` (`PanelWidth / DrawSize.X`) y llama `Apply(StartIndex)` → **se ve la página correcta en el editor**, con su color de fondo. Si el widget todavía no existe, el cast falla en silencio y no rompe nada.
- **BeginPlay**: `Apply(StartIndex)`.

## 🔴 El Designer MIENTE si su preview no coincide con el `DrawSize`
Síntoma real (2026-08-18): *"en el editor se ve bien de proporción pero en el BP se ve apretado"*. El Designer arrancaba en **1280×720 con DPI Scale 0,67** (se lee abajo a la derecha del canvas) mientras el `WidgetComponent` renderiza a **1920×1200 sin ese escalado**. Dos discrepancias sumadas: **aspecto** (16:9 vs 16:10) y **tamaño de fuente** (~1,5× por el DPI) — el texto entraba en una línea en el preview y en dos en el mundo.

✅ **Una sola vez por asset:** el dropdown **`Fill Screen`** (NO el de `Screen Size`, que sólo lista dispositivos y no ofrece Custom) → **`Custom`** → **1920 × 1200**, y guardar (queda en el asset).
🔴 **Tiene que ser `Custom`, no `Custom on Screen`:** `Custom` **no aplica DPI scaling** y el `WidgetComponent` tampoco → correspondencia 1:1. `Custom on Screen` sí lo aplica y vuelve a mentir. El **DPI Scale pasa a 1,0 solo** al elegir bien.
💡 La regla mental correcta, y es la simple: **widget a NxM + `DrawSize` a NxM = se ve idéntico.** Si no coincide, es el modo de preview, no el widget.
⚠ **No se puede setear por MCP**: `designSizeMode` / `designTimeSize` son *editor-only data* del WidgetBlueprint y `set_properties` responde *"could not be set"* (la ruta resuelve al CDO). Hay que tocarlo a mano.
💡 Las anclas son **relativas**, así que el layout no se rompe con la resolución; **lo único que no escala solo es la fuente en píxeles**.

## Config del WidgetComponent
`space = World` (obligatorio en VR) · `drawSize = 900×600` · escala 0.1 → **90 × 60 cm** (1 px de DrawSize = 1 cm, ver `references/widgets-vr.md`) · **colisión apagada en los dos campos** (`collisionEnabled` **y** `collisionProfileName`): el perfil `UI` bloquea el canal Visibility y se comería el rayo del puntero.

## 🔘 El botón: `BP_InstrButton_SC` — **duplicado de `BP_Bell`, no reconstruido**
**Uno solo por nivel**, hold de **2 s**, el anillo se llena y avanza de página. Se hizo **duplicando `BP_Bell`** (`AssetTools.duplicate`) en vez de rehacerlo: así llegan gratis y ya probados la aparición por cercanía, el hold, el anillo `WBP_BellRing` (RadialSlider real), la háptica con detección de mano, los sonidos y el hundido del cuerpo.

Sólo se cambiaron **tres cosas**:
| Qué | Antes (Bell) | Ahora |
|---|---|---|
| `Fire()` | anillo a 1, feedback, y **prendía `bLeaving`** (se iba) | anillo a 1, feedback, **`HoldT`→0 y anillo→0** (queda listo para otra vez) y avisa al panel |
| `TickLeave()` | encoge → `OpenDoors` → `Advance` (caminata) → destroy | encoge → destroy. **Las dos funciones del Bell se borraron** |
| `Leave()` | no existía | **API pública**: prende `bLeaving`. La llama el panel al terminar |

`HoldDuration` = 2 s · `PanelTag` = `instr_hall`.

## 🔗 El enlace: UN actor tag, dos búsquedas
Panel y botón llevan **el mismo actor tag** (`instr_hall`); lo que los distingue es la **clase** que cada uno busca:
- Botón → `GetAllActorsOfClassWithTag(BP_InstructionsPanel_SC, PanelTag)` → `Advance()`
- Panel → `GetAllActorsOfClassWithTag(BP_InstrButton_SC, PanelTag)` → `Leave()`

Así no hay dos tags que mantener sincronizados, y varios paneles/botones en niveles distintos no se pisan.

## 🏁 El final de la etapa
`Advance()` decide: si `PageIndex < EndIndex` → `Step(1)`; **si ya está en `EndIndex` → `Finish()`**.

`Finish()` hace, en este orden:
1. Prende `bLeaving` (arranca la animación de salida del panel).
2. 🔴 **`OnFinished` — event dispatcher.** Es el "llamado de fin": **cualquier BP se bindea y sigue con lo suyo**. Se avisa **al principio de la salida**, no al final, para que lo que venga después pueda arrancar mientras el panel se desvanece.
3. Busca el botón por tag y le llama `Leave()`.

Panel y botón se **encogen en paralelo, cada uno con su tiempo** (`ExitTime` 0,5 s en el panel; `LeaveTime` en el botón) y **cada uno se autodestruye** al llegar a escala ~0. No hay un orquestador: cada actor se apaga solo.

## 📍 Dónde están colocados (2026-08-18)
🔴 **Uno por sala, y cada par vive en SU sublevel** (no en el persistente): así aparecen y desaparecen con la sala. **En el Hall no va ninguno** (decisión de Beltrán).

| Sala (sublevel) | Panel / Botón (x) | Tag | Páginas |
|---|---|---|---|
| `L_Entering_SC` | 1269 / 1219 | `instr_entering` | 0-2 |
| `L_Recognizing_SC` | 2769 / 2719 | `instr_recognizing` | 3-5 |
| `L_Attracting_SC` | 5769 / 5719 | `instr_attracting` | 6-8 |
| `L_Surrounding_SC` | 7269 / 7219 | `instr_surrounding` | 9-11 |

Offsets respecto del centro de sala: **panel −231, botón −281**, z 150 / 90 (los eligió Beltrán probando en el Hall). `Loving` quedó sin instrucciones. El reparto de páginas de a 3 es una propuesta: se cambia con `StartIndex`/`EndIndex` en cada instancia, **sin tocar el widget**.
💡 **Para colocar en un sublevel por MCP**: `SceneTools.load_level(<sublevel>)` lo abre como mapa propio, se colocan los actores, se guarda, y al final se vuelve con `load_level` al persistente. No hace falta "current level" de la panel de Levels.

## 🔒 El latch del botón: una página por apretada
Sin esto, con la mano apoyada el hold se reinicia solo y **pasa todas las páginas de corrido**. La solución son dos líneas en `UpdateHold`, con una única bool `bArmed`:
```
(SetbArmed (or (not bTouching) bArmed))          ; se re-arma SOLO al soltar
(SetHoldT  (select (and bTouching bArmed) (+ HoldT DT) 0.0))
```
y `Fire()` arranca con `SetbArmed false`. Con la mano quieta adentro, `HoldT` queda clavado en 0 y el anillo vacío; hay que **salir y volver a entrar** para cargar de nuevo. Sin ramas extra ni estado redundante.

## ⚠️ `BgColor` no se ve en el editor (limitación real)
El Construction Script llama `Apply`, pero **`GetUserWidgetObject` devuelve null en el editor** y el cast falla en silencio → el color por instancia **sólo se ve en Play**. No hay salida por Blueprint: **`InitWidget` y `RequestRedraw` NO están expuestos** (verificado con `find_node_types`).
👉 Lo que sí se ve en vivo en el editor es el color propio del widget (`Bg → Color and Opacity`), que es el que conviene usar para tunear. Beltrán lo dejó así a propósito: *"cambiará de color entre sala, pero si no se puede está bien, hago testeos y lo defino"*.

## ✅ El panel de la PARTIDA (2 páginas, 2 botones) — CONSTRUIDO 2026-08-18
Spec de Beltrán:

| Página | Botón IZQUIERDO ("Start experience") | Botón DERECHO ("Next / Previous page") |
|---|---|---|
| **1** — sólo imagen | visible → dispara **`OnFinished`** | avanza a la 2 |
| **2** — imagen + texto | **oculto** | vuelve a la 1 |

**Se reusa este mismo panel y este mismo botón.** Sólo hacen falta **tres perillas**:
- **Panel · `bPingPong` (bool)** — hoy `Advance()` hace *"si `PageIndex >= EndIndex` → `Finish()`, si no → `Step(1)`"*. Con la bool, al llegar al final **vuelve a `StartIndex`** en vez de terminar. Con 2 páginas **eso ES el toggle**: el botón derecho no necesita saber si va o vuelve, hace siempre lo mismo.
- **Botón · `bFinishButton` (bool)** — llama `Finish()` directo en vez de `Advance()`. Es el botón izquierdo.
- **Botón · `OnlyOnPage` (int, −1 = siempre)** — se oculta cuando la página actual no es esa. Con `0`, el botón izquierdo desaparece en la página 2 y reaparece al volver. Necesita **cachear la referencia al panel** (mismo patrón auto-reparable que `PawnSC`, §151) en vez de buscar por tag cada frame.

💡 **"Next" y "Previous" no requieren nada**: el botón es físico y sin etiqueta, así que la misma acción sirve para los dos sentidos.

### 🔴 Por qué NO se creó un segundo widget
La idea inicial era un `WBP_StartInstructions` aparte, pero `Apply` hace un **cast duro a `WBP_Instructions`** y con otra clase falla. Se evaluaron tres salidas:
1. **Blueprint Interface** `Setup(Index, Color)` — la correcta en abstracto, pero **el MCP no tiene tools de interfaces** (`create_interface`/`add_interface`/`implement_interface` no existen). Descartada por imposible desde acá; se puede hacer a mano en el editor si algún día hay muchos tipos de widget.
2. `GetWidgetFromName` para buscar `Pages` y `Bg` por nombre y castear sólo a clases del motor — elegante, pero **el nodo no resuelve** en el contexto de un Actor.
3. ✅ **Las 2 páginas como 12 y 13 del widget que ya existe.** Cero arquitectura nueva, y **cada página es un Canvas independiente**, así que la estética de la partida puede ser totalmente distinta a la de las salas. El `BgColor` es por instancia. **Es además la más lean.**

### Cómo quedó colocado (persistente)
| Actor | Posición | Config |
|---|---|---|
| `InstrPanel_Start` | −1500, 0, 150 | `StartIndex` 12 · `EndIndex` 13 · **`bPingPong` ✔** |
| `InstrButton_Start` (izq.) | −1550, **−35**, 90 | **`bFinishButton` ✔** · `OnlyOnPage` **12** |
| `InstrButton_Next` (der.) | −1550, **+35**, 90 | `bFinishButton` ✘ · `OnlyOnPage` **−1** (siempre) |

Los tres con el actor tag **`instr_start`**. Están en el **persistente** porque la partida ocurre antes de que streamee ninguna sala.
⚠ La orientación (`yaw` 180) se copió de los paneles de sala y **no está validada en visor**; si se lee espejado, girar.

### El detalle que hace que el ocultar funcione
`OnlyOnPage` no sólo esconde el actor: **también apaga su detección de mano**. El engranaje está en `RunBell`, que es donde se calcula si el botón está siendo tocado —
```
bTouching = (AppearT > 0.9) AND bHandsNear AND bShown
```
— así que agregar `bShown` como un término más de esa condición alcanza para que un botón oculto no responda. Sin eso, el botón invisible seguiría cargándose con la mano encima, porque la detección es **por distancia**, no por colisión.
La referencia al panel se **cachea** en `PanelRef` con el mismo patrón auto-reparable de `PawnSC` (§151): `IsValid` → si no, `CachePanel()`. Nada de buscar por tag cada frame.

## Lo que falta
- **Bindearse a `OnFinished`** desde quien tenga que seguir (el director de etapa). Hoy el aviso sale y no lo escucha nadie.
- Test en visor: el hold de 2 s, la distancia de la mano, y si el panel se lee bien a esa distancia.
- Textos reales **en inglés** (regla del proyecto; sólo Calibration quedó en español).
- Duplicar panel + botón en los otros 5 niveles, con su `StartIndex`/`EndIndex` y su tag.

## Trampas pagadas acá
Ver `gotchas.md` **§147** (sólo se aplica el PRIMER campo de un struct en una instancia → poner adelante el que importa), **§148** (`AddWidget` devuelve `None`; las refs se piden con `GetWidgets`, y los slots cuelgan del PADRE) y **§149** (las continuaciones de un cast en el DSL son `(:then ...)` / `(:CastFailed)`, no statements sueltos).
