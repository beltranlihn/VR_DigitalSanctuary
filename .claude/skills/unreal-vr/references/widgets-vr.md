# Widgets (UMG) en VR — Quest 3 standalone

Fuentes: (A) doc oficial Epic/Meta con URL, (B) código UE 5.8 (`C:\Program Files\Epic Games\UE_5.8\Engine\Source\Runtime\UMG\...`, archivo:línea — **gana sobre la doc web si difieren**), (C) fuente técnica con URL, (D) folclore sin fuente (marcado explícito). Doc web de Epic sin versión o de 5.0–5.3 se trata como sospechosa; se verificó contra el código 5.8 en cada punto crítico.

---

## 🔴 Regla de oro + checklist de un widget VR barato

**Un widget de instrucciones o de carga en este proyecto SIEMPRE va en un `WidgetComponent` con `Space = World`, nunca screen-space.** Ver §1 para la cita y el motivo técnico (estereoscopía).

Checklist antes de dar por terminado cualquier widget nuevo:
- [ ] `Space = World` (nunca `Screen`) — (B) `WidgetComponent.h:25-31`.
- [ ] `TickMode` puesto **explícitamente** en `Automatic`. ⚠ **El default de fábrica en 5.8 NO es Automatic** — ver trampa en §4.
- [ ] `DrawSize` lo más chico posible para la legibilidad que necesitás (≥18px de fuente, no resolución de pantalla completa). Ver §3 y §9.
- [ ] `bManuallyRedraw = true` si el contenido es estático o cambia por evento discreto (texto de instrucciones, no la barra de progreso mientras progresa). Ver §4.
- [ ] Contenido actualizado por **evento**, nunca por Property Binding. Ver §3.
- [ ] Nada de `TickWhenOffscreen = true` salvo que lo necesites de verdad — con `false` (default) el widget deja de redibujarse cuando no fue renderizado recientemente (`WasRecentlyRendered`), lo cual ahorra costo cuando el panel queda fuera de vista.
- [ ] `BlendMode = Opaque` si el fondo del widget lo permite (Turrell = fondos oscuros sólidos detrás del texto pueden ser opacos). Si es translúcido, que sea el widget más chico y menos superpuesto posible — overdraw en Quest cuesta.
- [ ] Contar cuántos `WidgetComponent` están activos/visibles a la vez en la escena — cada uno es un render target + un pase de render aparte.

---

## (a) Por qué screen-space NO funciona en VR — World-space obligatorio

**(A)** Foro/soporte Epic (consistente con el comportamiento verificado en código): en VR "no hay pantalla" en el sentido 2D del HUD — el `Space = Screen` de un `WidgetComponent` "renders the widget on the screen completely outside of the world and is never occluded" (doc oficial *Widget Components in Unreal Engine*, https://dev.epicgames.com/documentation/en-us/unreal-engine/widget-components-in-unreal-engine). Un HUD screen-space se dibuja en un plano 2D fijo del framebuffer del visor de escritorio; en un HMD estereoscópico no existe ese framebuffer único — hay dos vistas (una por ojo) con proyección y parallax distintos, así que un overlay 2D fijo no tiene ninguna posición 3D coherente que resolver para ambos ojos a la vez y **no se ve, o se ve mal (doble/plano pegado a la cara)**. La comunidad XR de Epic lo resume así: *"there is no 'screen', so the widget is invisible"* cuando se intenta usar un HUD 2D dentro de un HMD.

**(B) Confirmado en código 5.8** — `WidgetComponent.h:24-31`:
```cpp
UENUM(BlueprintType)
enum class EWidgetSpace : uint8
{
    /** The widget is rendered in the world as mesh, it can be occluded like any other mesh in the world. */
    World,
    /** The widget is rendered in the screen, completely outside of the world, never occluded. */
    Screen
};
```
`World` = el widget se renderiza como **malla en el mundo 3D** (occludable, con profundidad estéreo correcta porque es geometría real). `Screen` = fuera del mundo, pensado para HUD de escritorio con un único punto de vista — **no tiene noción de ojo izq/der**, por eso no sirve para HMD.

**Mecanismo del `WidgetComponent`** (comentario de clase, `WidgetComponent.h:84-93`):
> "The widget component provides a surface in the 3D environment on which to render widgets normally rendered to the screen. Widgets are first rendered to a render target, then that render target is displayed in the world."

Es decir: UMG dibuja el Widget Blueprint a un `UTextureRenderTarget2D` (offscreen, como una cámara de render-to-texture), y ese RT se aplica como textura sobre una malla plano/cilindro (`UMeshComponent`) que vive en el mundo con la profundidad estéreo correcta para ambos ojos.

**Doc oficial XR de Epic (5.8)**, *Design user interfaces for XR experiences*: la UI para experiencias XR "must be 3D so you can interact with it in the virtual environment" (https://dev.epicgames.com/documentation/unreal-engine/design-user-interfaces-for-xr-experiences-in-unreal-engine).

---

## (b) Crear el Widget Blueprint (UMG) y el Widget Component

### Widget Blueprint
Content Browser → Add → User Interface → **Widget Blueprint** (`WBP_*`). Se abre el UMG Designer: panel **Hierarchy** (árbol de contenedores/widgets), **Palette** (widgets disponibles), canvas de diseño, **Details**.

**Jerarquía recomendada** (root típicamente **no** debería ser Canvas Panel suelto si se puede evitar overdraw/costo — ver nota de performance abajo, pero Canvas Panel sigue siendo el root por defecto que crea UMG):
- **Canvas Panel** — root libre, posicionamiento por anchors/offsets. (B) `CanvasPanel.h` existe en 5.8. ⚠ Nota de performance (A, doc *Optimization Guidelines for UMG*): *"Canvas Panels increment their child widgets' IDs so they can render on top of one another if need be. This results in Canvas Panels using multiple draw calls, thus making them highly CPU-intensive."* → para un panel de instrucciones simple, considerar **Overlay** o **Vertical/Horizontal Box** como contenedor principal en vez de anidar todo en Canvas.
- **Vertical Box / Horizontal Box** (B) `VerticalBox.h` / `HorizontalBox.h` — layout en fila/columna, auto-tamaño según contenido. Bueno para apilar título + cuerpo de instrucciones.
- **Overlay** (B) `Overlay.h` — apila widgets uno sobre otro (fondo + texto encima), sin el costo de anchors de Canvas.
- **Size Box** (B) `SizeBox.h` — fuerza un tamaño mínimo/máximo/fijo a su hijo; útil para fijar el área de texto sin depender del Canvas.

### Widgets concretos que vas a usar (firma verificada en 5.8)

**Text Block** — (B) `TextBlock.h:30-54`
- `Text` (`FText`, `Category="Content"`) — el contenido.
- `Font` (`FSlateFontInfo`) — tamaño, tipografía, weight.
- Justificación vía `ETextJustify`. `AutoWrapText` disponible para envolver texto largo de instrucciones.

**Rich Text Block** — (B) `RichTextBlock.h` existe en 5.8 (permite markup inline `<Bold>...</>` con `Decorators`/`RichTextBlockDecorator.h`). Para instrucciones con énfasis parcial (ej. resaltar una palabra) en vez de tener que craftear varios Text Blocks.

**Image** — (B) `Image.h:39` — `Brush` (`FSlateBrush`) referencia una textura/material. Sirve para íconos o fondos con gradiente (coherente con la estética Turrell: se puede meter un Material Instance con gradiente radial en el Brush).

**Progress Bar** — (B) `ProgressBar.h:28-82`
- `WidgetStyle` (`FProgressBarStyle`).
- `Percent` (`float`, 0..1, `UIMin/UIMax = 0/1`) — **acceso directo deprecado desde 5.1**, usar getter/setter: `GetPercent()` / `SetPercent(float)` (`UFUNCTION(BlueprintCallable, Category="Progress")`, línea 81-82). En Blueprint esto es el nodo **Set Percent**, no escribir la variable directo.
- `FillColorAndOpacity` — color del relleno (útil para un progreso con gradiente de color Turrell en vez de barra genérica).
- Tiene modo `IsMarquee`/`bIsMarquee` (getter `UseMarquee`) para un indicador indeterminado (spinner) si no tenés progreso real.

**Border** — contenedor con `Background` (`FSlateBrush`) + padding; útil como panel de fondo detrás del texto de instrucciones (rectángulo o con material con blur/gradiente).

---

## (c) Widget Component en el mundo — propiedades clave (verificado 5.8)

Todas confirmadas en (B) `WidgetComponent.h` (líneas indicadas) salvo que se marque lo contrario.

| Propiedad | Tipo / valor | Qué hace | Línea |
|---|---|---|---|
| `Space` | `EWidgetSpace::World` / `Screen` | World = malla 3D occludable; Screen = HUD 2D fuera del mundo (no VR) | 447-448 |
| `WidgetClass` | `TSubclassOf<UUserWidget>` | Qué Widget Blueprint instanciar | 455-456 |
| `DrawSize` | `FIntPoint`, default `(500,500)` | Tamaño del widget **en píxeles** — resolución del render target | 459-460, .cpp:621 |
| `bManuallyRedraw` | `bool`, default `false` | Si `true`, sólo redibuja cuando llamás `RequestRenderUpdate()` (o queda pendiente `bRedrawRequested`) | 463-464, .cpp:622-623 |
| `RedrawTime` | `float`, default `0` | Intervalo mínimo entre redibujados; con `bManuallyRedraw` limita la tasa incluso de los redraws pedidos | 470-476 |
| `TickMode` | `ETickMode`: `Disabled` / `Enabled` / `Automatic` | Cuándo tickea el componente (ver trampa en §4) | 70-81, 642 |
| `GeometryMode` | `Plane` / `Cylinder` | Malla plana o curva (cilindro, con `CylinderArcAngle`) | 50-58, 638-640 |
| `bIsTwoSided` | `bool` | Visible desde atrás o no | 571-573 |
| `BlendMode` | `Opaque` / `Masked` / `Transparent` | Modo de blend del material del widget | 42-48, 559-561 |
| `bUseInvalidationInWorldSpace` | `bool` | Usa el sistema de invalidation de Slate para actualizar el widget world-space | 491-496 |
| `TickWhenOffscreen` | `bool` | Si sigue tickeando cuando no fue renderizado recientemente | 282-294, 575-577 |
| `Pivot` | `FVector2D` | Punto de anclaje del quad respecto al origen del componente | 307-313 |
| `bDrawAtDesiredSize` | `bool` | El RT se ajusta automático al tamaño deseado del widget en vez de `DrawSize` fijo — ⚠ comentario del propio motor: *"WARNING: If you change this every frame, it will be very expensive."* (línea 498-504) | 316-321, 498-506 |

### Mapeo DrawSize (píxeles) → tamaño físico en el mundo

**(B) Verificado en `WidgetComponent.cpp`:**
- `CalcBounds()` (línea 907-917): el bounding box del quad usa `CurrentDrawSize.X/Y` **directamente como unidades de Unreal (cm)**: `BoxExtent = FVector(1.f, CurrentDrawSize.X/2, CurrentDrawSize.Y/2)`.
- El collision box aplica además la escala del componente: `(FVector(0.01f, CurrentDrawSize.X*0.5f, CurrentDrawSize.Y*0.5f) * GetComponentTransform().GetScale3D())` (línea 941).

**Conclusión práctica:** con `Scale = (1,1,1)`, `DrawSize = (1000, 500)` px da un quad de **1000×500 cm** (10×5 m) en el mundo — 1 píxel de DrawSize = 1 cm por defecto. Para que un widget de `DrawSize` alto (buena resolución de texto) ocupe un tamaño físico razonable (ej. 1 m de ancho), hay que **escalar el `WidgetComponent`** hacia abajo: `Scale.X/Y/Z ≈ tamaño_físico_deseado_cm / DrawSize_px`. Ej.: `DrawSize=(1000,500)` + `Scale=(0.001,0.001,0.001)` en los ejes del plano ≈ 1 m × 0.5 m. Esto es la manera correcta de subir el DPI efectivo (más nitidez) sin agrandar el panel: **subís DrawSize y bajás la Scale en la misma proporción**.

---

## (d) Interacción en VR (opcional — la obra puede no necesitarla)

**Para el caso de instrucciones que el usuario "avanza"**, si hiciera falta: `WidgetInteractionComponent` (B) `WidgetInteractionComponent.h`, montado en el motion controller (o en su pivote de "aim").

Confirmado en código 5.8:
- Es un `USceneComponent` que simula un puntero láser: *"This is a component to allow interaction with the Widget Component. This class allows you to simulate a sort of laser pointer device, when it hovers over widgets it will send the basic signals to show as if the mouse were moving on top of it."* (línea 49-53).
- `InteractionSource` (`EWidgetInteractionSource`): `World` (traza desde la posición/orientación del propio componente — el caso VR), `Mouse`, `CenterScreen`, `Custom` (línea 23-37, 229-230).
- `InteractionDistance` (float) — distancia máxima de interacción (línea 218-222).
- `PointerIndex` (int32) — cada mano/controller necesita un índice distinto para no pisarse el foco (línea 204-208).
- Disparo de click: `PressPointerKey(FKey Key)` / `ReleasePointerKey(FKey Key)` — simula el botón (típicamente `EKeys::LeftMouseButton`) como si viniera del mouse (línea 78-92).
- `bShowDebug` + `DebugColor`/`DebugLineThickness` para visualizar el rayo en desarrollo (línea 246-265).

**Marcado como opcional**: si la obra es contemplativa de un solo usuario sentado, probablemente **no** necesites que el usuario "clickee" nada — un widget de instrucciones puede simplemente aparecer/desaparecer por temporizador o por evento del propio flujo de la obra (Sequencer/Blueprint), sin `WidgetInteractionComponent`. Usalo sólo si necesitás un botón real ("Continuar", "Saltar instrucciones").

---

## (e) 🔴 Actualizar contenido: Event-driven, NO Property Binding

**(A) Confirmado con doc oficial (5.8):**

*Property Binding for UMG* (https://dev.epicgames.com/documentation/en-us/unreal-engine/property-binding-for-umg-in-unreal-engine): un binding conecta una propiedad del widget a una función/variable que **se re-evalúa constantemente**: *"When you bind attributes to fields in your UI, they poll the attribute every frame."*

*Driving UI Updates with Events in Unreal Engine* (https://dev.epicgames.com/documentation/unreal-engine/driving-ui-updates-with-events-in-unreal-engine) — cita textual: *"if you are using a more complex system with multiple properties checking for updates every frame, this setup can lead to poor performance."* Y describe el patrón recomendado: *"The Custom Event inside the HUD Widget Blueprint now only checks and updates the display of player's Health when it changes, rather than always checking the value regardless of whether or not it changed."*

*Optimization Guidelines for UMG* (https://dev.epicgames.com/documentation/en-us/unreal-engine/optimization-guidelines-for-umg-in-unreal-engine) recomienda explícitamente evitar bindings cuando se puede optimizar.

**Patrón recomendado (Event-driven update):**
1. El widget expone una función `UFUNCTION(BlueprintCallable)` tipo `SetInstructionText(FText NewText)` o `SetLoadProgress(float Percent)`.
2. Quien posee la lógica (el `Actor`/`GameMode`/Manager) llama a esa función **sólo cuando el valor cambia** — ej. al empezar un capítulo de la obra, al cambiar el % de carga.
3. Dentro de la función: `TextBlock->SetText(NewText)` / `ProgressBar->SetPercent(Percent)` — **usar los setters** (`SetPercent`, no escribir `Percent` directo — (B) `ProgressBar.h:31` marca el acceso directo `UE_DEPRECATED(5.1, ...)`, hay que usar getter/setter también en 5.8).
4. Alternativa aún más desacoplada: `Event Dispatcher` en el actor de origen (ej. `OnLoadProgressChanged(float NewPercent)`) al que el widget se bindea una sola vez en `Construct`, no cada frame.

Esto reemplaza tanto los **Property Bindings de UMG** (el ícono de "bind" en Details, que crea una función invisible evaluada cada frame) como cualquier `Tick` del widget que "chequee" un valor — ambos cuestan CPU todos los frames aunque nada haya cambiado.

---

## (f) 🔴 Performance en Quest standalone — reglas concretas

Cada `WidgetComponent` en `World` space es: (1) un **render target** (textura offscreen) que UMG redibuja, más (2) **otro pase de render** (dibujar ese RT sobre una malla en la escena, con su propio material translúcido/opaco). En un móvil TBDR fill-rate-limited como el Snapdragon del Quest 3, esto no es gratis — cada widget visible suma trabajo de GPU aparte del resto de la escena.

### 🔴 La trampa más importante: `TickMode` por defecto en 5.8 NO es "Automatic"

**(B) Verificado en código**, `WidgetComponent.cpp:58-64` y `640-644`:
```cpp
static bool bUseAutomaticTickModeByDefault = false;
static FAutoConsoleVariableRef CVarbUseAutomaticTickModeByDefault(
    TEXT("WidgetComponent.UseAutomaticTickModeByDefault"),
    bUseAutomaticTickModeByDefault,
    TEXT("Sets to true to Disable Tick by default on Widget Components when set to false, the tick will enabled by default.")
);
...
, TickMode(bUseAutomaticTickModeByDefault ? ETickMode::Automatic : ETickMode::Enabled)
```
El CVar por defecto es `false` → **el `WidgetComponent` recién creado arranca con `TickMode = Enabled` (tickea siempre), no `Automatic`.** El comentario del enum dice que `Automatic` "is ticked only when needed. i.e. when visible" (`WidgetComponent.h:79-80`) — pero **hay que poner `TickMode = Automatic` a mano en cada `WidgetComponent`** (o cambiar el CVar a nivel proyecto) para obtener ese comportamiento; no viene así de fábrica en 5.8. Un widget con `TickMode=Enabled` sigue evaluando su lógica de redraw aunque esté fuera de cámara/oculto, salvo que además juegue `TickWhenOffscreen=false` combinado con `WasRecentlyRendered()` (ver abajo) — pero el tick del componente en sí no se apaga solo.

### Cómo decide el motor si redibuja (verificado, `WidgetComponent.cpp:1369-1385`, función `ShouldDrawWidget`)
```cpp
bool UWidgetComponent::ShouldDrawWidget() const
{
    const float RenderTimeThreshold = .5f;
    if (IsVisible())
    {
        if (TickWhenOffscreen || WasRecentlyRendered(RenderTimeThreshold) || LastWidgetRenderTime == 0.0)
        {
            if ((GetCurrentTime() - LastWidgetRenderTime) >= RedrawTime)
            {
                return bManuallyRedraw ? bRedrawRequested : true;
            }
        }
    }
    return false;
}
```
Es decir: si **no** ponés `bManuallyRedraw=true`, el widget se redibuja cada vez que pasa el `RedrawTime` (por defecto 0 → **cada frame que sea visible**), sin importar si el contenido cambió. `bManuallyRedraw=true` hace que sólo redibuje cuando vos llamás `RequestRenderUpdate()` (`SetManuallyRedraw`, línea 1788-1791) — esto es lo que hay que usar para un panel de instrucciones con texto estático: se dibuja una vez al aparecer y no vuelve a costar nada hasta el próximo cambio de texto.

### Reglas concretas para Quest 3 standalone

1. **`TickMode = Automatic`** explícito en todo `WidgetComponent` de la obra (no confiar en el default). Ojo: además hay que confirmarlo en runtime porque el default depende del CVar del proyecto.
2. **`bManuallyRedraw = true`** en cualquier widget cuyo contenido no cambie todos los frames (paneles de instrucciones fijos, título). Llamar `RequestRenderUpdate()` sólo al cambiar el texto/estado.
3. Para la **barra de carga**, que sí cambia seguido durante la carga: `bManuallyRedraw=true` + `RequestRenderUpdate()` llamado desde el mismo evento que actualiza `Percent` (no todos los frames — ver §(g), throttlear a ~10 Hz alcanza para que se vea fluido sin redibujar 72/90 veces por segundo).
4. **`DrawSize` chico**: no uses una resolución de escritorio (ej. 1920×1080) para un panel de texto — con las reglas de §9 (18px+ de fuente, ~qHD por metro), un `DrawSize` de 512×256 a 1024×512 alcanza y sobra para un panel de instrucciones a distancia de lectura VR.
5. **Property Bindings prohibidos** — ver §(e). Cada binding activo sí corre cada frame sin importar `TickMode`/`bManuallyRedraw` del componente, porque vive en la lógica de Slate del propio widget, no del `WidgetComponent`.
6. **`Invalidation Box`** (B) `InvalidationBox.h`, existe y es válido en 5.8 (`UInvalidationBox : public UContentWidget`, cachea la geometría de los hijos: *"Caching / Performance"*, comentario de clase). Envolver el contenido estático del panel de instrucciones (texto + fondo) en un `Invalidation Box` evita que Slate vuelva a hacer prepass/tick/paint de esos hijos si nada invalidó el layout — sumalo al `bManuallyRedraw` del `WidgetComponent` (son capas de optimización distintas y complementarias: una decide si el `WidgetComponent` pide un redraw del RT, la otra decide si Slate recalcula el árbol de widgets dentro de ese RT).
7. **`Retainer Box`** (B) `RetainerBox.h`, también existe en 5.8. Aplana los hijos a un render target propio con control de `Phase`/`PhaseCount` (ej. `PhaseCount=2` → redibuja la UI a la mitad del framerate). Doc oficial: úsalo sólo si `Invalidation Box` no alcanza, porque *"Retainer Panels have high overhead when they repaint and use more memory than individual widgets would with an Invalidation Box"* — para este proyecto (paneles simples de texto/barra), **Invalidation Box + `bManuallyRedraw` del `WidgetComponent` debería bastar**; no hace falta Retainer Box salvo que se necesite un post-proceso de material sobre el render target.
8. **Overdraw / translúcido = sí suma, y Quest es fill-rate bound.** Cada `WidgetComponent` con `BlendMode=Transparent` dibuja su quad con blending sobre lo que hay detrás — si superponés varios paneles translúcidos (fondo con gradiente + texto + borde, cada uno un `WidgetComponent` separado), estás multiplicando el overdraw en el mismo fragmento de pantalla. Preferí **un solo `WidgetComponent`** por panel (con el fondo, el texto y el borde como hijos *dentro* del mismo Widget Blueprint) en vez de varios `WidgetComponent` apilados — así el overdraw ocurre una vez dentro del render target (barato, es un RT chico) y sólo una vez al componer ese RT en el mundo, no N veces.
9. **Cantidad de widgets simultáneos**: para una obra de 15 min con paneles de instrucciones + una barra de carga, mantené **como mucho 1-2 `WidgetComponent` visibles a la vez**; ocultá/destruí (o al menos `SetVisibility(false)`, que además detiene el draw vía `ShouldDrawWidget→IsVisible()`) los que no estén en uso en ese momento del recorrido.
10. `bApplyGammaCorrection`, `bOverrideRenderTargetFormat`/`RenderTargetFormatOverride` (B) `WidgetComponent.h:537-569`: por defecto el RT usa el formato Slate estándar (RGBA8); no hace falta tocarlo salvo necesidad específica de precisión de color para gradientes finos — en cuyo caso hay costo extra de memoria/ancho de banda, evaluar caso a caso.

---

## (g) Fade in/out y transiciones

Dos caminos verificados en 5.8, con costo distinto:

### Opción A — `RenderOpacity` del Widget (animar dentro de UMG o desde Blueprint)
(B) `Widget.h:449-452` y `598-602`: `RenderOpacity` (`float`, 0-1) existe en la clase base `UWidget` — **acceso directo también deprecado desde 5.1**, usar `GetRenderOpacity()`/`SetRenderOpacity(float)`.

- **Widget Animation** (UMG Animations panel, `Animation/WidgetAnimation.h` existe en 5.8): crear una track de `Render Opacity` de 0→1, reproducir con `Play Animation`. (A) Doc oficial confirma el patrón: *"To fade something in or out, use Render Opacity rather than Visibility... because it's numeric, Unreal can interpolate between values over time."* (*Animating UMG Widgets in Unreal Engine*, https://dev.epicgames.com/documentation/en-us/unreal-engine/animating-umg-widgets-in-unreal-engine). **(D, no verificado con cita exacta en 5.8)**: la doc de *Optimization Guidelines for UMG* distingue animaciones "material-only" (costo cero de CPU, GPU-only) de animaciones de Sequencer que tocan layout (*"layout invalidation, which will in turn recalculate the layout each frame"*) — animar sólo `RenderOpacity` sin tocar tamaño/posición debería quedar del lado barato, pero confirmalo empíricamente en el profiler del proyecto si el fade se nota costoso.

### Opción B — Animar el material del `WidgetComponent` (o su `TintColorAndOpacity`)
(B) `WidgetComponent.h:300-306` y comentario de clase (líneas 88-93): el componente expone `TintColorAndOpacity` (`FLinearColor`) vía `SetTintColorAndOpacity()`, que es un parámetro del material dinámico (`MaterialInstanceDynamic`) que envuelve el render target — **no toca Slate ni recalcula el árbol de widgets**, sólo un scalar/vector de material.

### Cuál es más barato en Quest
**Opción B (Tint/Opacity del `WidgetComponent` vía material) es más barata** porque el fade ocurre íntegramente en la GPU sobre un material simple, sin re-evaluar layout de Slate ni re-renderizar el contenido del widget al render target (podés incluso tener `bManuallyRedraw=true` en el widget interior mientras el fade anima afuera, sin redibujar el texto en cada frame del fade). La Opción A (`RenderOpacity` vía Widget Animation) sigue estando bien para fades simples de opacity pura (según la doc, no invalida layout si no toca tamaño/posición), pero si ya estás manejando el `WidgetComponent` en Blueprint, animar `TintColorAndOpacity` con un Timeline es el camino de menor costo y evita depender del sistema de Animations de UMG. **Recomendación para este proyecto** (estética Turrell, fades lentos y suaves): Timeline en el actor dueño del `WidgetComponent` → `SetTintColorAndOpacity(Lerp(...))` cada tick del fade (el fade en sí es corto, unos segundos, así que el tick temporal del Timeline no es un problema de performance sostenido).

---

## (h) Barra de carga / progreso real

### El patrón general
1. `WBP` con un `ProgressBar` cuyo `Percent` se actualiza por función (`SetLoadProgress(float NewPercent)` → `ProgressBar->SetPercent(NewPercent)`), **nunca** por binding (§e).
2. La fuente del progreso llama a esa función sólo cuando el valor cambia de forma perceptible (ej. cada 1-5%, no en cada micro-tick de carga) — throttleado, no cada frame.
3. Marcar `bManuallyRedraw=true` en el `WidgetComponent` y llamar `RequestRenderUpdate()` en el mismo punto donde se llama `SetLoadProgress` — así el redraw del render target está sincronizado con el cambio real, no con el framerate.

### De dónde sacar el 0-1 real (verificado en código 5.8, con caveats)
- **Level Streaming**: `ULevelStreaming::GetLevelStreamingState()` (B) `LevelStreaming.h:371` da el estado (`Unloaded/Loading/LoadingWaitingForFinish/Loaded/...`), **no un porcentaje continuo** — sirve para un indicador binario/discreto o un `Marquee`/spinner (`ProgressBar::bIsMarquee`, ver §b), no para una barra 0-100% suave.
- **Async load de assets/paquetes**: existe `GetAsyncLoadPercentage(const FName& PackageName)` (B) `UObjectGlobals.h:938-943`, pero es **C++ puro, no `UFUNCTION`/`BlueprintCallable`** — no aparece como nodo en Blueprint sin un wrapper propio en C++. El propio comentario del motor advierte: *"@warning THIS IS SLOW. MAY BLOCK ASYNC LOADING."* — no llamarlo todos los frames aunque se exponga.
- **`FStreamableHandle::GetProgress()`** (B) `Engine/StreamableManager.h:405-414`, devuelve 0-1 (`GetLoadProgress()`, `GetRelativeDownloadProgress()`, `GetAbsoluteDownloadProgress()`) — también C++ puro (`ENGINE_API`, sin `UFUNCTION`); es el mecanismo correcto si están cargando `PrimaryAsset`s/soft references vía `Asset Manager`, pero requiere una función C++ o Blueprint Function Library propia para exponerlo como nodo.

**⚠ Conclusión honesta (no folclore, pero sí gap de la API pública de Blueprint):** UE 5.8 **no expone de fábrica un nodo Blueprint nativo de "porcentaje 0-1 de carga de nivel/asset"** — las dos fuentes de verdad reales (`GetAsyncLoadPercentage`, `FStreamableHandle::GetProgress`) son C++ sin `UFUNCTION`. Para una barra de progreso real en Blueprint puro hay dos caminos honestos:
1. **Progreso simulado/estimado**: animar `Percent` de 0→1 en un tiempo estimado (Timeline) sincronizado con el disparo de la carga y el evento de "carga completa" (`OnLevelLoaded` del streaming, o el `Completed` del nodo `Load Level Instance`) — es lo que hacen la mayoría de los tutoriales encontrados y **no es folclore, es la salida pragmática documentada por la comunidad ante el gap de la API** (C, ej. https://forums.unrealengine.com/t/how-to-create-loading-bar-progress-for-loading-level-in-blueprint/746364).
2. **Wrapper C++ mínimo**: una `UBlueprintFunctionLibrary` con un `UFUNCTION(BlueprintPure) static float GetLoadPercent(...)` que llame a `FStreamableHandle::GetProgress()` o `GetAsyncLoadPercentage()` — la opción "real" si el proyecto ya tiene módulo C++.

Para esta obra (15 min, carga entre "capítulos"), lo pragmático suele ser: nodo `Load Level Instance` (o `Level Streaming` con `Should Block On Load=false`) → mientras carga, animar la barra con progreso estimado (curva/Timeline calibrada al tiempo real de carga medido en el dispositivo) → al recibir `OnLevelLoaded`, `SetPercent(1.0)` y disparar el fade-out del panel (§g).

---

## (i) Legibilidad de texto en VR/Quest

**(A) Meta Horizon OS Developers — Typography** (https://developers.meta.com/horizon/design/styles_typography/):
- *"A font size no smaller than 14px is required for minimal legibility."*
- *"For a comfortable reading experience, use a font size of 18px or larger."*
- *"Choose a sans-serif font with a high x-height and large counters"* para legibilidad a distintas distancias.
- *"Larger weights such as Black, Bold, and Medium are more legible than lighter weights like Light and Thin."* — usar weight fuerte para títulos/labels, Regular para cuerpo.
- Evitar itálicas: *"do not render well in fully immersive experiences."*
- *"Type is rendered differently on Quest headsets compared to traditional monitors due to the display technology, lens properties, and unique viewing conditions"* — **hay que probar en hardware real**, no confiar en cómo se ve en el editor de escritorio.

**(A) Meta Horizon OS Developers — Panels** (https://developers.meta.com/horizon/design/panels/): tamaños de panel de referencia (para paneles 2D del sistema, no directamente `WidgetComponent` de UE, pero orientativo): panel por defecto 1024×640 dp, mínimo 384×500 dp. La guía de distancia/ergonomía específica de "Hands UI best practices" está linkeada desde esa página pero no se pudo extraer el texto completo en esta pasada — **si se necesita el número exacto de distancia recomendada, revisar esa sub-página directamente**.

**(C, otra fuente ya citada en la búsqueda, sin acceso al texto completo verificado, tratar con cautela)**: guías generales de UI en VR mencionan ~45 cm para interacción directa con manos y ~1 m para paneles de lectura/observación a distancia — **esto coincide con el sentido común de "obra sentada contemplativa" pero no se pudo confirmar el número exacto en la doc de Meta en esta pasada; verificar antes de fijar la distancia final del panel de instrucciones.**

### Traducción práctica a `DrawSize` + tamaño físico (usando la fórmula de §c)
Si el panel de instrucciones queda a ~1-1.5 m del usuario (lectura cómoda sentado) y querés que el texto de cuerpo se vea como "18px cómodos": no hay una conversión 1:1 automática entre "18px de Slate Font" y "tamaño angular en el HMD", porque depende de cuánto mundo-espacio ocupa cada píxel del `DrawSize` (ver mapeo §c). Regla práctica: **fijá primero el tamaño físico del panel en el mundo** (ej. 60×30 cm para un panel de instrucciones a 1.2 m), y ajustá el `DrawSize` de manera que la fuente en píxeles (18-24px Slate) ocupe una fracción razonable de esa resolución — ej. `DrawSize=(900,450)` con `Scale≈0.00067` (60cm/900px) es un punto de partida razonable; **siempre validar en el visor puesto**, no en el editor de escritorio, tal como pide la propia guía de Meta.

### Folclore / sin fuente confirmada (marcado)
- (D) "regla de oro de 1 metro mínimo de distancia de lectura en VR" — circula mucho en foros pero no se encontró como cita textual de Epic o Meta en esta pasada; tratar como heurística de partida, no como norma.
- (D) Cualquier cifra de "DPI ideal de render target para Quest 3" (ej. "usar tal densidad de píxeles por metro") no tiene fuente oficial verificada aquí — se deriva empíricamente probando en el dispositivo, como indica la propia guía de Meta.
