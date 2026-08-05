# BP_TouchInstrPanel — progress tracker

Panel de instrucciones del stage Touch (fase **R7** del brief [`docs/stages/touch-attracting.md`](../../../../docs/stages/touch-attracting.md)). Muestra las páginas de bienvenida/instrucciones en world-space y **bloquea la interacción hasta terminarlas**.

- **refPath**: `/Game/SoulCharger/Stages/Touch/BP_TouchInstrPanel.BP_TouchInstrPanel` · **parent**: Actor
- **widget**: `/Game/SoulCharger/Stages/Touch/Widget/WBP_TouchInstr`
- **in level**: `TouchInstructions` (`BP_TouchInstrPanel_C_0`) en `L_Touch`, en **(120, 0, 135)** con yaw 180 (mirando al usuario sentado en el origen).
- **Status**: 🟡 **Compila y guardado. FALTA TEST EN VISOR.**

## 🔴 Regla de organización: todo lo del stage vive en el stage
Se copió de `Calibration` (`WBP_CalibInstructions` + `BP_CalibInstrPanel`) pero **se cortaron TODAS las dependencias a `Calibration/`** — la copia las arrastraba y eso ata un stage a otro.
- `M_RingTicks` + su textura → duplicados a `Stages/Touch/Widget/` (`M_RingTicks`, `T_RingTicks`).
- Las brushes de `Icon` y `WelcomeImage` se **limpiaron**: traían arte de calibración horneado. El arte de cada página entra por `SetIconMaterial` en runtime.
- ✅ Verificado con `get_dependencies`: el widget solo depende de sí mismo y de `Core/Font/Quicksand-Bold_Font` (compartida a propósito).
- ⚠ Queda un cabo del mismo tipo fuera de este BP: **`BP_SoundBubble.PreviewSound` apunta a `Calibration/Audio/Pad`**. Se resuelve en R8 junto con los clips reales.

## Componentes
- `DefaultSceneRoot` · `Panel` (WidgetComponent, **World space**, `GeometryMode = Cylinder`, DrawSize 1920×1080, escala 0.064 → ~123×69 cm). Heredado de la copia; ver `widgets-vr.md`.

## Variables
- `InstrWidget : WBP_TouchInstr` — el widget vivo, sacado con `GetUserWidgetObject(Panel)` en BeginPlay.
- `Beams : BP_AimBeam[]` — los dos beams, cacheados en BeginPlay.
- `PageTexts : Text[]` · **instance-editable** — 🔴 **el número de páginas lo define el LARGO de este array**, no una constante. Agregar o quitar páginas es editar el array en el nivel, sin tocar Blueprints. Vienen 4 de arranque.
- `PageIcons : MaterialInterface[]` · **instance-editable** — el arte por página. Hoy vacío; falta el arte de Touch.
- `PageIndex : int` · `HoldT : float` · `HoldDuration : float = 1.5` (instance-editable) · `bFinished : bool`
- `bSensorTaken` / `bAnyTrigger` — resultados de los dos polls. Son **variables miembro, no valores de retorno**: el DSL no expone cómo escribir un output param de función.

## 🆕 Apertura del nivel: negro → fade → widget
Mismo patrón que los otros stages, usando el **`BP_FadeSphere` compartido de `Core/UI/`** (no una copia: es infraestructura común, no contenido del stage).
- **`CacheRefs()` (BeginPlay)** termina con `GetActorOfClass(BP_FadeSphere)` → **`StartFade(NewTarget=1.0, Duration=0.01, negro)`** = **negro instantáneo**. El widget ya se armó detrás.
- **`TickOpening(Delta)`** acumula `OpenT`; al pasar `OpenDelay` (0.6 s) llama **`StartFade(0.0, FadeInDuration=2 s, negro)`** y marca `bOpened`. La escena y el panel aparecen juntos.
- 🔴 **Las páginas no corren hasta `bOpened`**: `UpdatePages` gatea todo detrás de la apertura, así el gatillo no puede saltarse la primera página durante el fundido.
- ⚠ Requiere un **`BP_FadeSphere` colocado en el nivel** — `L_Touch` no tenía; se agregó (`FadeSphere`, en el origen). Sin él, el cast falla y loguea `TCH|no hay BP_FadeSphere en el nivel` (no rompe, solo no hay fundido).
- `OpenDelay` y `FadeInDuration` son **instance-editable**.

## Grafos
- **EventBeginPlay**: `CacheRefs()` → cachea widget + beams, `PageIndex = 0`, `ShowPage()`, y arranca en negro.
- **EventTick**: `UpdatePages(Delta)`.
- **`UpdatePages(Delta)`**: si aún no está `bOpened` → `TickOpening(Delta)`. Si ya abrió y no está `bFinished`: página **0** → `TickWelcome()`; el resto → `TickHoldPage(Delta)`.
- **`TickWelcome()`**: `AnySensorTaken()` → si algún beam tiene `bEquipped`, `NextPage()`. **La página 1 avanza sola al tomar un sensor**, no con el gatillo.
- **`TickHoldPage(Delta)`**: `AnyTriggerHeld()` → si **no** hay gatillo, resetea `HoldT` y el radial a 0; si lo hay, acumula, actualiza `SetTriggerProgress(HoldT/HoldDuration)` y al pasar el umbral llama `NextPage()`. Mismo gesto que Calibration.
- **`ShowPage()`**: 🔴 **guardado con `IsValidIndex`** — si el índice se sale del array, llama `Finish()` en vez de indexar fuera de rango. Así un `PageTexts` vacío no rompe: simplemente no hay instrucciones.
- **`NextPage()`** / **`Finish()`**: `Finish` habilita **`bGrabEnabled = true` en los dos beams** y después **`DestroyActor(self)`**.

## 🔴🔴 El panel BLOQUEABA el line-trace — dos arreglos (2026-08-05, reportado en visor)
**Síntoma:** con las instrucciones terminadas no se podían agarrar las esferas: el rayo chocaba contra el panel invisible.
1. **`Finish` DESTRUYE el actor, no lo esconde.** `SetActorHiddenInGame` deja la colisión viva y el trace sigue chocando — el mismo error que ya había mordido en `BP_SaveButton`. Como el panel no vuelve a usarse, `DestroyActor` es lo correcto. ⚠ El `SetGrabEnabled` a los beams va **ANTES** del destroy.
2. **La colisión del `Panel` se apaga en BeginPlay, por código.** El `WidgetComponent` viene con perfil **`UI`**, que **bloquea el canal Visibility** → el beam le hacía hover incluso durante las instrucciones.
   - 🔴 **No se puede arreglar desde las propiedades del editor:** setear `BodyInstance.collisionEnabled = NoCollision` funciona en el **CDO** pero **la instancia del nivel lo revierte a `QueryOnly`/perfil `UI`** — el WidgetComponent lo regenera. Verificado leyendo el valor efectivo después de setearlo.
   - **La solución que sí aplica** es `Collision|SetCollisionEnabled(Panel, NoCollision)` como primera línea de `CacheRefs`. Caso de manual de "declarado ≠ aplicado": ponerlo donde de verdad toma efecto.

## 🔴 Cómo se bloquea la interacción
En `BP_AimBeam`:
- **`bGrabEnabled`** (default **false**) — `TryGrab` muere si está en false. Durante las instrucciones se puede **apuntar** (hay beam y hover) pero **no agarrar nada**: ni burbujas ni el botón.
- **`bTriggerHeld`** — lo setea `TryGrab` **ANTES** del candado y lo baja `TryRelease`. Ese orden es lo que permite usar el gatillo para pasar de página mientras agarrar sigue bloqueado.

## ⚠ Trampas ya mordidas al construirlo
- 🔴 **`read_graph_dsl` etiqueta mal las llamadas a funciones propias cuando hay colisión de nombres.** `NextPage` mostraba `(Ability|Tasks|Finish)` — parecía que llamaba al `Finish` de Gameplay Abilities. **Era falso**: `get_node_infos` confirmó `type_id = |Finish`, la función propia. Lo mismo con `Class|WBPCalibInstructions|...` en `ShowPage`, que en realidad apunta al widget duplicado. **Verificar con `get_node_infos` antes de "arreglar" nada.**
- **`create_node` SÍ agarra la función equivocada** cuando hay colisión (le pasó a `CacheAimSource`) → pasar siempre `declaring_class`.
- **Una variable `bFoo` genera `GetFoo`/`SetFoo`**, sin la `b`. `|SetbFinished` no existe; es `Variables|Default|SetFinished`.
- **`Utilities|Array|Get` no existe** como type_id: son `Get(acopy)` y `Get(aref)`.
- **Llamar una función propia con parámetros**: el primer pin posicional es `self` → usar keyword (`:DeltaSeconds DeltaSeconds`).
- **Dangling `else`**: con ifs anidados, poner el caso de cancelación **primero** (`if (not cond) … (else …)`) y dejar el if interno como última sentencia del bloque `else`.
- 🔴 **Un `bind` con sublistas `:then`/`:CastFailed` CONSUME el resto de la función**: todo lo que va después queda como *"Unreachable code after branch/return"* y el DSL lo rechaza. Un cast con ramas explícitas tiene que ir **al final**, o hay que repetir la continuación dentro de cada rama. Por eso `CacheRefs` hace `ShowPage()` **antes** de buscar el `FadeSphere`.

## TODO / next
1. 🔴 **Test en visor**: arranca el panel con la página 1; al tomar un sensor pasa a la 2; gatillo sostenido ~1.5 s avanza cada página con el radial llenándose; al terminar el panel desaparece y **recién ahí** se puede agarrar. Antes de eso, apuntar y gatillar no agarra nada.
2. **Arte por página** → llenar `PageIcons` (hoy vacío) y volver a conectar el `Icon` en `ShowPage` cuando exista.
3. **Textos definitivos en INGLÉS** (regla del proyecto). Los 4 actuales son placeholder en español.
4. Ajustar posición/altura del panel sentado — hoy (120, 0, 135) a ojo.

## Session log
- **2026-08-05:** creado por duplicación desde Calibration, dependencias cortadas, 10 variables, 9 funciones, EventGraph por cirugía, candado `bGrabEnabled`/`bTriggerHeld` en `BP_AimBeam`. Instancia colocada en `L_Touch`. Compila y guardado.
