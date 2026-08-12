# BP_IntroSequence — el arranque de la obra (Core/Flow/)

## Purpose
§3 escena 0: **la obra arranca en negro con logos, título y menú.** Este actor lleva ese tiempo autoral: negro → 3 logos → título, y después le pasa la posta al [[BP_StageDirector]].

Pedido de Beltrán (2026-08-12): *"Negro 2 segundos, widget con imagen al centro un segundo, luego otra, luego otra… Made with Unreal, logo Alma Digital, logo Johns Hopkins. Luego, título de la obra."*

## Status
🟡 **La secuencia corre y está medida por log** (2026-08-12). ⬜ Faltan los **botones** (Start / About Us) y las **imágenes** de los logos.

## 🔴 Sin UMG: planos y TextRender
El "widget" es un **plano con material unlit** + `TextRenderComponent`, no un Widget Blueprint. Mismo criterio que el cartel de [[BP_Door]]: en Quest es mucho más barato (no hay render target ni árbol de Slate) y **esquiva todo `widgets-vr.md`** — world-space obligatorio, `TickMode` que no viene en `Automatic`, `bManuallyRedraw`, etc. Para tres logos y un título, alcanza y sobra.

| Componente | Qué es |
|---|---|
| `LogoPlane` | Plano de 100×100 cm (el `Plane` del motor), material `M_IntroLogo`, `pitch 90` para quedar vertical. **Oculto si no hay textura** para ese logo. |
| `Caption` | El texto del logo. Es el **placeholder** mientras no haya PNGs: dice `MADE WITH UNREAL`, etc. |
| `TitleText` | `Soul Charger` (worldSize 24) |
| `SubText` | `An interactive VR Biofeedback Experience` (worldSize 8) |

### 🔴 El fade es por EMISIVO, no por transparencia
`M_IntroLogo` es **unlit, opaco y TwoSided**: `Emissive = LogoTex.rgb × Brightness × Op`. Con `Op = 0` el plano queda **negro**, y contra el fondo negro de la obra **eso ya es invisible**. Lo mismo con los textos: `SetTextRenderColor(MakeColor(Op,Op,Op,1))` va de negro a blanco.
👉 **Cero translucidez**, que en Quest cuesta ~80 % más de GPU por frame, y cero problemas de orden de dibujado. Es la misma idea que hace funcionar el "sin techo" de `BP_Room`: en un mundo negro, apagar es desaparecer.

### ⚠ El panel va FUERA del fade sphere
`BP_FadeSphere` es una esfera de **60 cm de diámetro** pegada a la cámara (escala 0.6 sobre la esfera del motor): nada cabe adentro. Por eso el panel se coloca a `PanelDistance` (200 cm) y **el negro de los 2 s iniciales lo da el mundo vacío**, no el fade. Funciona porque en ese momento no hay ninguna sala visible todavía.

### Se coloca solo, frente a la mirada, una vez
`PlacePanel` → `PlaceStep(Cam)` corre en `BeginPlay`: toma **sólo el yaw** de la cámara, pone el actor a `PanelDistance` en esa dirección y lo rota `yaw + 180` para que los `TextRender` (que miran a +X) queden legibles.
💡 **Una vez, no cada frame**: así el panel es un objeto del mundo y no un HUD pegado a la cabeza (§5 descarta lo segundo). Y como el usuario arranca quieto, cae siempre en su campo de visión sin importar cómo agarró el visor.

## Registro de variables
| Variable | Default | Rol |
|---|---|---|
| `BlackTime` | 2.0 s | El negro inicial. |
| `LogoTime` | 1.0 s | Cuánto dura cada logo. |
| `FadeRate` | 3.0 /s | Velocidad de los fades (0→1 en ~0,33 s). |
| `PanelDistance` | 200 cm | A qué distancia se planta el panel. |
| `LogoCaptions` | 3 textos | Los placeholders. |
| `LogoTextures` | vacío | Las imágenes. **Vacío = se oculta el plano y queda sólo el texto**, que es el comportamiento correcto, no un bug. |
| `bAutoStartAfterTitle` | **true** | ⚠ **Andamio temporal:** 2,5 s después del título llama solo a `StartExperience()`. **Lo apaga el botón Start cuando exista.** |
| `LogoOp`/`LogoOpTarget` · `TitleOp`/`TitleOpTarget` | — | Estado de los dos fades. |

## Estructura de grafos
```
BeginPlay → CacheCamera · PlacePanel · HideAll → timer "Logo1" a BlackTime
Logo1 → SetLogo(0) → timer "Logo2" a LogoTime
Logo2 → SetLogo(1) → timer "Logo3"
Logo3 → SetLogo(2) → timer "TitleStep"
TitleStep → ShowTitle() · MaybeStart()
Tick → UpdateFades(Δ)
```
- **`SetLogo(i)`** — 🔴 **pone `LogoOp` en 0 de golpe** y el target en 1, así **cada logo entra con su propio fade** en vez de ser un cambio de texto sobre algo ya visible. Es la diferencia entre "aparecen tres logos" y "se cambia un cartel".
- **`UpdateFades`** — move-toward sin ramas: `Op += clamp(Target−Op, −rate·Δt, +rate·Δt)`. Mismo patrón que `BP_Room.UpdateLight`.
- **`ApplyLogoOp` / `ApplyTitleOp`** — el emisivo del plano + el color de los textos. El `Caption` sigue al **logo**; `TitleText` y `SubText` siguen al **título**.
- **`StartWalk` → `StartStep(Dir)`** — castea el `BP_StageDirector` y llama `StartExperience()`.
  ⚠ **El timer apunta a la FUNCIÓN `StartWalk`, no a un custom event.** Al escribir el DSL, un `(event Custom|StartWalk)` **colisiona con la función del mismo nombre** y el parser lo renombra a `CustomEvent` (quedó un huérfano que hubo que borrar). `SetTimerByFunctionName` llama funciones igual que eventos, así que la función sola alcanza.

## Verificado por log (2026-08-12)
```
10:32:17.19  INTRO: negro, arranca la secuencia
10:32:19.22  INTRO: logo 1        (+2,03 s)
10:32:20.22  INTRO: logo 2        (+1,00 s)
10:32:21.22  INTRO: logo 3        (+1,00 s)
10:32:22.22  INTRO: titulo en pantalla
…luego DIR: entra a la sala      (la cadena intro → caminata → hall corre completa)
```
Cero errores. Y **`bAutoStart` del director quedó en `false`**: ahora el arranque lo manda la intro.

## TODO
- [ ] 🔴 **Los botones Start / About Us** — por **contacto de la mano + trigger**, no por beam (decisión de Beltrán, 2026-08-12: el arco de gestos va *tocar → sensor → beam sólo en Attracting*). Receta de mano en [[BP_Sensor]], receta de hover/escala en `BP_SaveButton`.
- [ ] **About Us**: panel de texto + volver.
- [ ] **Start**: esconde suavemente título y botones (ya está el fade: `TitleOpTarget = 0`) y llama `StartExperience()`. Al hacerlo, **apagar `bAutoStartAfterTitle`**.
- [ ] 🔴 **Las 3 imágenes.** Cuando existan los PNGs: cargarlos en `LogoTextures` y hacer que la textura llegue al material. ⚠ Para eso hace falta un **MID** (`SetTextureParameterValue` no tiene variante `onMaterials`), y `SetScalarParameterValue` está **duplicado** en el DSL → el nodo del MID va por **cirugía con `declaring_class`** (ver la trampa en `BP_SaveButton.md`).
- [ ] La tipografía de la obra (`Core/Font/Quicksand`) en los `TextRender` — hoy usan la del motor.
- [ ] `M_IntroLogo` quedó con **5 expresiones huérfanas** de un script que falló a mitad (ver abajo). No afectan el material compilado; conviene limpiarlas a mano.
- [ ] Test en visor: tamaño del título y distancia del panel sentado.

## ⚠ Trampas mordidas al construirlo (2026-08-12)
- 🔴🔴 **Un `execute_tool_script` que falla ROLLBACKEA lo que hizo… pero NO todo.** `add_variable`, `set_properties` y `write_graph_dsl` se revierten; **`add_expression` de materiales y `add_component` NO**. Dos intentos fallidos dejaron **5 expresiones huérfanas** en `M_IntroLogo` y **4 componentes basura** en el BP (que sí se borraron con `remove_component`). 👉 Después de un script que falló, **verificar qué quedó** en vez de asumir que no pasó nada.
- 🔴 **`try/except` alrededor de `execute_tool` NO salva el script**: la excepción aborta la corrida igual. Lo que puede fallar va en su **propia llamada MCP**, no dentro de un script largo.
- 🔴 **`collisionEnabled` no se puede setear en la misma llamada que el resto de las propiedades** de un StaticMeshComponent (falla toda la llamada). Va aparte.
- 🔴 **`Math|Rotator|MakeRotator` es `(Roll, Pitch, Yaw)`** posicional — poner el yaw en el segundo lugar lo mete en el **pitch** y el panel queda tumbado. Usar **argumentos con nombre** (`:Yaw`) o el acceso a campo `(.yaw rot)`.
- ⚠ **`(bind (_a _b _c) (BreakRotator ...))`** no salió como esperaba; el acceso por campo **`(.yaw x)`** es más claro y más corto.
- ⚠ `add_component` vive en **`ActorTools`**, no en `BlueprintTools`. Y `MaterialTools` usa **`connect_to_output`** (no `connect_to_material_property`), y **`delete_unused_expressions` pide `material`**, no `material_or_function`.

## Relacionados
- [[BP_StageDirector]] (a quien le pasa la posta con `StartExperience`) · [[BP_Door]] (el mismo criterio de TextRender sobre UMG) · `BP_FadeSphere` · `BP_SaveButton` (la receta de hover y escala para los botones que vienen)
