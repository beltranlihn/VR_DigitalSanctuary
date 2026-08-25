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

## 🎬 2026-08-19 — los paneles de sala nacen OCULTOS y los muestra el guión
- **Panel `bStartHidden`** (cat. *0 - Paginas*, instance-editable; **true en las 4 instancias de sala**, false en el de la partida): `BeginPlay` → `InitVisible()` pone `bVisible=!bStartHidden` y, si oculto, `AppearT=0` + `Panel` a escala 0. **`Show()`** (API pública) prende `bVisible` y `bEntering`; `TickShow → StepShow` lo hace crecer a `1/ExitTime` hasta `AppearT=1` (la misma curva de salida, al revés). El `Tick` quedó `TickShow → TickLeave`.
- **Botón**: dos `AND` por cirugía. En `ApplyVisible`, `bShown = (OnlyOnPage<0 || PageIndex==OnlyOnPage) AND PanelRef.bVisible` → oculto y sin detección mientras el panel esté oculto. En `AppearStep`, el target del crecimiento pasa a `(cerca AND bShown)` → cuando el panel se muestra el botón **crece** en vez de aparecer de golpe.
- Quién llama `Show()`: [[BP_Director_Story]] (`ShowPanel`, busca por tag `instr_<sala>` y se bindea a `OnFinished`). **Ya no es cierto que "OnFinished no lo escucha nadie".**

## 🔊 2026-08-20 — el sonido del botón suena al hacerse VISIBLE, no al entrar a la sala
El `PlayAppear` (y el crecimiento) estaban gateados solo por **cercanía** — al entrar a la sala ya estabas a <7 m y sonaba con el botón aún invisible. Cirugía en `AppearStep`: la condición del flanco pasó de `cerca` a **`cerca AND bShown`** (el mismo AND que ya alimentaba el crecimiento). Ahora el "aparece" suena en el momento en que el panel se muestra (o al acercarse, si ya estaba visible).

## 🎨 2026-08-20 — los colores de instancia POR FIN llegan al widget (+ alfa)
Beltrán: *"por más que cambie los colores de los menús, no cambiaban en el juego"*. **Causa**: `Apply` corre en el BeginPlay, cuando `GetUserWidgetObject` del WidgetComponent todavía devuelve null → el cast fallaba en silencio y el `BgColor` de la instancia nunca se aplicaba (el widget quedaba con su color de Designer). **Fix**: `ReApply()` (Apply con el `PageIndex` vigente) se llama (1) por **timer a 0,5 s del BeginPlay** (cubre el panel de la partida) y (2) dentro de **`Show()`** (cubre los paneles de sala, que aparecen tarde). Además el **alfa del `BgColor` ahora es la opacidad del fondo** (el `Setup` del widget usa `SetColorAndOpacity`, que siempre la respetó): las 5 instancias quedaron con **A = 0,55** conservando los RGB de Beltrán (Recognizing rojizo y Surrounding ámbar ya estaban autorados y por fin se ven). El texto no se toca.

## 🌬️ 2026-08-24 — las páginas de ENTERING son la 2 y la 3, con el círculo de práctica
🔴 **La instancia de `L_Entering_SC` define el rango: `StartIndex 2` / `EndIndex 3`** (las "dos páginas" de Beltrán — la tabla vieja de abajo que decía 0-2 está superada; la instancia manda). Sin sistema de calibración (pivote del día): el usuario lee, practica y parte.

| Página | Contenido (EN) | Extra |
|---|---|---|
| 2 | *"In this room, your breath takes the lead. / Rest the sensor gently on your belly, stay still, and breathe slowly - the circle follows your breath."* | **`BreathCircle`** — Image circular (brush `RoundedBox` + `HalfHeightRadius`, blanco tibio, anclas 0.44-0.56 × 0.36-0.54) que **respira con el usuario** vía `SetRenderScale` |
| 3 | *"When you feel ready, hold the button. / A sphere of light will appear and follow your breath."* | el botón (sin candado, original) → `Finish()` → la esfera del mundo |

- **Cadena del círculo**: widget `SetCircleSize(S)` (`Widget|Transform|SetRenderScale` — 🐛 fix 2026-08-24: el DSL había SOLTADO el getter del target y el pin `self` quedó libre → **escalaba el widget entero** (texto+imagen+círculo, lo vio Beltrán en visor); el pin se conectó por cirugía a `BreathCircle` y verificado con `get_node_infos`) ← panel **`SetPractice(S)`** (con caché `WidgetRef`/`bWidgetOk` vía `EnsureWidget`) ← `BP_Director_Story.TickPractice` (empuja la escala interpolada cada tick mientras se espera el panel de la sala 1).
- 🗃️ **Dormido para cuando vuelva la calibración con datos**: `CalibBar` (ProgressBar en `Page_1`, `visibility=Collapsed`) + widget `SetCalibBar(P)` + panel `SetCalibProgress(P)`. Nadie los llama.
- ⚠ `Txt_0` (agregado por error a la Page_0 cuando se asumió el rango 0-2) fue **eliminado**; `Txt_1` restaurado a su valor previo ("Start experience"). Page_0/Page_1 quedaron como estaban.
- ⚠ Trampas UMG: `AddWidget` exige **`widgetDisplayName`** · `ToggleWidgetAsVariable` exige **`bIsVariable`** · los `
` de los textos entran bien por `set_properties` (JSON), la trampa del `
` literal es solo del DSL.

## ❤️ 2026-08-25 — la página de RECOGNIZING es la 4, con el círculo del latido
🔴 **La instancia de `L_Recognizing_SC` define el rango: `StartIndex 4` / `EndIndex 4`** — UNA sola página (decisión de Beltrán; la tabla vieja 3-5 está superada, la instancia manda).

- **`HeartCircle`** — Image en `Page_4` (brush `RoundedBox` + `HalfHeightRadius`, tono rosado cálido 0.9/0.62/0.58, anclas 0.44-0.56 × 0.36-0.54, **`RenderOpacity` 0 de fábrica**): el círculo que **late a 1/2 del pulso** y **solo se ve dentro del umbral de pecho**. Falta el texto en inglés de la página (Beltrán) y su posición fina en el Designer.
- **Cadena**: widget `SetHeartCircle(S, O)` (SetRenderScale + SetRenderOpacity sobre `HeartCircle`, pines `self` verificados con `get_node_infos`) ← panel **`SetHeartFx(S, O)`** (mismo caché `EnsureWidget`/`WidgetOk` de `SetPractice`) ← `BP_Director_Story.TickHeartFx` (S = 1 + 0.6·`BeatEnv` del sensor; O = fade por `bHeartZone`).

## 🪟 2026-08-21 — el fondo deja el widget y pasa a ser GEOMETRÍA: `Glass` + `M_InstrGlass`
Pedido de Beltrán: *"en vez del color genérico del widget, un material translúcido como el de las ventanas, y yo poder configurar el emisivo y la transparencia"*.

🔴 **La causa real de que no le gustara**: el `WidgetComponent` está en **`blendMode = Masked`** → alfa de **1 bit**. El `BgColor` con alfa 0,55 se dibujaba **opaco**; ninguna transparencia hecha dentro del widget iba a funcionar.

**Arquitectura nueva**: el widget se queda **sólo con texto e imagen** (el `Bg` quedó en `visibility = Hidden`), y el fondo es un **`ProceduralMeshComponent` `Glass`** — un plano **curvado igual que el widget** — con material de mundo propio.
- **`Glass` cuelga del `Panel`**, así hereda su escala y **la animación de aparición/salida funciona gratis** (`StepShow`/`TickLeave` escalan el Panel).
- La malla se genera en el **Construction Script** (`BuildGlass`): grid de `GNx`×`GNy` (32×6 = 231 verts / 384 tris) curvado con la fórmula del modo Cylinder de UE — `R = DrawSize.X / arcRad`, `Apothem = R·cos(arc/2)`, y por vértice `X = Apo − R·cos(ang)`, `Y = R·sin(ang)`. Verificado: con arco 30° da `R = 3666,9` y `Apo = 3541,98`; con 52,552° (el de la partida) `R = 2093,3`.
- 🔴 **`ArcAngle` es ahora una VARIABLE DEL ACTOR** y el CS se la **empuja al widget** (`SetCylinderArcAngle`) — una sola fuente de verdad, imposible que vidrio y widget se desincronicen. Ver el gotcha §183 (por qué no se puede leer del componente).
- **Esquinas redondeadas por SDF en el material**, no por geometría: bordes suaves y antialiaseados en vez de recorte poligonal. `CornerRadius` se escribe en **píxeles del widget** (48, el mismo valor que el `RoundedBox` del brush) y el BP lo convierte a fracción de altura.
- Colisión apagada **por código** en el CS (`SetCollisionEnabled(NoCollision)`): en la instancia no se deja escribir (§58), y una colisión ahí bloquearía los punteros.

### `M_InstrGlass` (Core/UI/) — unlit · translucent · **two-sided**
Parámetros: `GlassColor` · `Emissive` · `Opacity` · `CornerRadius` · `EdgeSoft` · `Aspect` (los tres últimos los calcula el BP). Two-sided a propósito: un plano abierto no paga fill extra y así no depende del winding.

### Las perillas del actor (cat. *2 - Vidrio*, todas por instancia)
| Perilla | Default | Qué hace |
|---|---|---|
| `GlassColor` | el `BgColor` que ya tenía cada instancia | color del vidrio |
| `GlassEmissive` | 1,0 | **cuánto brilla** |
| `GlassOpacity` | 0,55 | **transparencia real** (ahora sí) |
| `GlassCornerRadius` | 48 px | redondeo de esquinas |
| `GlassEdgeSoft` | 6 px | suavizado del borde |
| `GlassMargin` | 24 px | cuánto sobresale respecto del texto |
| `GlassOffset` | 2 px | cuánto se separa del widget (**invertir el signo si queda delante**) |
| `ArcAngle` | 30 (52,552 en la partida) | curvatura — la manda al widget |
| `GNx` / `GNy` | 32 / 6 | densidad de la malla |
⚠ Las 5 instancias quedaron escritas con sus valores (§146). El `BgColor` sigue existiendo pero ya no se ve: el color vive ahora en `GlassColor`.

### 🎨 2026-08-21 (2ª vuelta) — instancias de material por sala + interruptor del vidrio
- **5 instancias de `M_InstrGlass`** en `Core/UI/`: `MI_InstrGlass_{Blue,Red,Purple,Orange,Green}`, todas con **`Emissive 0,5` y `Opacity 0,25`, copiados de `MI_Vidrio`** (el vidrio de las ventanas de las puertas). **El color, el emisivo y la transparencia se editan EN LA INSTANCIA DE MATERIAL**, no en el BP.
- 🔴 Por eso `PushGlassMat` **ya no empuja color/emisivo/opacidad** (las variables `GlassColor`/`GlassEmissive`/`GlassOpacity` se eliminaron): sólo asigna **`GlassMaterial`** (variable nueva, por instancia) y los tres parámetros que dependen de la geometría (`Aspect`, `CornerRadius`, `EdgeSoft`). Así la MI manda y no hay dos fuentes peleando.
- **Reparto**: partida/título **morado** · Entering **azul** · Recognizing **rojo** · Attracting **naranja** · Surrounding **verde** (sigue el código de color de los anillos: entering azul, recognizing rojo, loving morado, attracting naranja).
- 🆕 **`bShowGlass` + `SetGlassVisible(On)`**: interruptor del fondo, por instancia y también en runtime. **El panel del título va con `bShowGlass = false`** (pedido de Beltrán: ahí sólo se ve la imagen).
- **`GlassOffset` = 1 cm de mundo por detrás** del widget, para no tapar texto ni imagen: en unidades de widget son **−9,6** en las salas (escala 200/1920) y **−7,68** en la partida (250/1920). Negativo = atrás; si en visor apareciera delante, invertir el signo.
- El `Bg` del `WBP_Instructions` quedó **`visibility = Hidden`**: afecta a los 5 paneles de una vez.
