# BP_StageTitle_SC + WBP_StageTitle_SC — el título de etapa (Core/UI/)

> Creado 2026-09-21. Pedido de Beltrán: *"Como ya no pasamos por puerta entre una etapa y otra, vamos a agregar un widget con un texto grande con el nombre de cada etapa. Va a partir del color del fondo, y luego transiciona a un degradado, cosa de que se revela. Solo aparecen en la entrada a cada etapa, antes de que aparezcan las instrucciones o Alma. La idea es que sea la presentación de etapa, elegante. Con texto en widget para que sea en alta calidad. No Text render."*
> **Estado: 🟢 verificado en PIE** (el título nace, revela y se disuelve; `BgColor` sigue en vivo al viraje de la esfera). ⬜ **Sin visor** y ⬜ **sin una pasada completa de la obra con el título puesto** (el editor crasheó antes de poder correrla — ver abajo).

## Qué es
La presentación de cada etapa, ahora que la puerta ya no la da. Aparece **durante el viraje de color** de [[BP_StageShell_SC]], antes de que entren Alma y las instrucciones, y se va solo.

**El gesto:** el texto está ahí desde el primer instante, pero **pintado exactamente del color del fondo**, así que no se ve. Después el color de cada letra viaja hacia el **degradado**, y el nombre *emerge del espacio*. Al terminar hace el camino inverso: **se disuelve de vuelta en el fondo**, no se apaga.

## 🔴 Por qué NO se hizo con un material sobre el widget
El plan original era un material (`SlateUI` + degradado + un `Reveal`) sobre el `WidgetComponent`. **Se descartó por dos motivos medidos:**
1. 🔴 **`TranslucentMaterial` del `WidgetComponent` NO es escribible por MCP** — no aparece en `list_properties` (sí están `space`, `drawSize`, `tickMode`, `bManuallyRedraw`, `bIsTwoSided`, `blendMode`). Sin eso el material nunca llega al componente.
2. La alternativa (un `Retainer Box` con `EffectMaterial`) **agrega un render target más** por encima del que el `WidgetComponent` ya usa. En Quest eso es fill que no hace falta.

✅ **La versión por letra no usa ningún render target extra ni ningún material**, y da el mismo efecto. Es la opción más barata de las tres.

## Cómo está hecho
### `WBP_StageTitle_SC` (duplicado de `WBP_DoorTitle`)
Se duplicó para heredar su `Arc` (el Canvas Panel) — **crear la jerarquía UMG desde cero no se puede por MCP**, pero **construirla en runtime sí**, que es lo que ya hacía `BuildArc`.

| Función | Qué hace |
|---|---|
| `BuildTitle(Texto, Size)` | limpia el canvas, crea un **`HorizontalBox`** centrado y le mete **una `TextBlock` POR LETRA**, guardándolas en `Letters`. 🔑 El HorizontalBox es lo que da **kerning real** — posicionar letra por letra (como hace `BuildArc`) sale monoespaciado y una "I" ocupa lo mismo que una "M" |
| `PaintLetters(Bg, GradA, GradB, Reveal, Stagger)` | por cada letra `i`: `u = i/(n−1)` · `col = lerp(GradA, GradB, u)` · `r = clamp(Reveal·(1+Stagger) − u·Stagger)` · `SetColorAndOpacity(lerp(Bg, col, r))` |

🔑 **El `Stagger` es lo que hace que “se revele”**: con 0 todas las letras aparecen juntas; con 0,6 la primera va adelantada y el revelado **barre la palabra de izquierda a derecha**.

### `BP_StageTitle_SC` (el actor)
**Componente:** `Title` (`WidgetComponent`) — `Space = World` (regla de oro de VR), `DrawSize` 1400×400, `TickMode Automatic`, `bIsTwoSided`, **`bManuallyRedraw = false`** (el revelado cambia colores por frame: con redraw manual no se actualizaría).

| Cat | Variable | Default | Rol |
|---|---|---|---|
| A - Titulo | `FontSize` | 130 | tamaño de la fuente, en px del widget |
| | `GradTop` / `GradBot` | blanco cálido / azul frío | los dos extremos del degradado |
| | `Stagger` | 0,6 | cuánto se escalona el revelado entre la primera y la última letra |
| B - Tiempos | `RevealTime` | 1,4 s | lo que tarda en emerger |
| | `HoldTime` | 1,0 s | cuánto se queda |
| | `FadeOutTime` | 0,9 s | lo que tarda en disolverse |
| Z - Estado | `Phase` (0 quieto · 1 entra · 2 sostiene · 3 sale) · `Elapsed` · `Reveal` · `BgColor` | | |

**API:** `Show(Texto)` (arma el texto y arranca) · `SetBg(Color)` (el color del fondo, en vivo).
**Grafos:** `BeginPlay` → timer 0,3 s → `Boot` (apagado) · `Tick` → `TickTitle` → `PhaseIn`/`PhaseHold`/`PhaseOut`, una función por fase (mismo patrón que [[BP_StageShell_SC]], por el límite del `elif` en el DSL).

## Contrato con la esfera
En [[BP_StageShell_SC]]:
- **`GoToStage(Idx)`** → `ShowTitle(Idx)` → `Title.Show(StageNames[Idx−1])`. Solo para etapas reales: con `Idx ≤ 0` (el final) **no hay título**.
- **`PushLook(Top, Bot, Bright)`** → `PushBg(lerp(Top,Bot,0.5))` → `Title.SetBg(...)` **cada tick del viraje**. Por eso el texto es siempre *exactamente* el color del fondo hasta que el revelado lo levanta.
- `StageNames` (Text[], instance-editable): `Entering · Recognizing · Loving · Attracting · Surrounding`. 🔴 **En inglés**, como todo lo que ve el usuario dentro del visor.

## ✅ Verificado en PIE
```
[WBP_StageTitle_SC_C_0] TITULO: Entering
titulo: Phase 0 · Reveal 0 · oculto                      <- en reposo
titulo: Phase 1 · Reveal 0,35 · BgColor (0,49 0,05 0,08) <- emergiendo, el fondo a mitad del viraje rojo->morado
titulo: Phase 2 · Reveal 1,00 · BgColor (0,34 0,05 0,34) <- sostén, el fondo ya morado
```
Cero `Accessed None`.

## ⬜ Lo que falta
- [ ] 🔴 **La pasada completa de la obra con el título puesto** — quedó sin correr (ver abajo).
- [ ] 🔴 **Visor**: el tamaño (hoy escala 0,15 → ~2,1 m de ancho a 3,5 m del usuario), la altura (`z = 190`), los dos colores del degradado y si 1,4/1,0/0,9 s es el ritmo correcto.
- [ ] Decidir si el título debe estar **más cerca o más lejos** que la ameba y el panel (hoy `x = 1500`, o sea detrás del metaball de Entering).
- [ ] Fuente: hoy usa la de fábrica. Si Beltrán trae una, se cambia en `BuildTitle` (`SetFont`).

## 💥 Por qué no hay pasada completa: el incidente del 2026-09-21
Al recrear `GoToStage`/`PushLook` en la esfera, **`BP_Director_Story` quedó sin compilar** (sus nodos de llamada quedaron huérfanos). El `StartPIE` siguiente abrió el modal *"Blueprint Asset Compilation Error"*, que **bloquea el hilo de juego y con él al MCP**. Se destrabó cerrando el modal por `WM_CLOSE`, pero eso dejó la sesión de PIE a medio construir y **el `StopPIE` siguiente crasheó el editor** (`PlayLevel.cpp:553`).
✅ **No se perdió nada**: había un `save_assets` inmediatamente antes del `StartPIE`.
📌 La regla completa quedó en `references/gotchas.md`.

## Relacionados
- [[BP_StageShell_SC]] — quien lo dispara y le pasa el color · [[BP_Door_SC]] / `WBP_DoorTitle` — de donde salió el widget
