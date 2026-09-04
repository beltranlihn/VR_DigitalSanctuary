# BP_ControllerRig — progress tracker

- **refPath**: `/Game/BP_ControllerRig.BP_ControllerRig` · **parent**: Actor · **en nivel**: sí, **2 instancias** en `/Game/XRFramework/Levels/L_XRTemplate` — `ControllerRig_R` en (−40, 25, 120) y `ControllerRig_L` en (−40, −25, 120).
- **Propósito**: el **banco de pruebas de los mandos** (2026-09-03). Beltrán importó meshes propios de mando (`/Game/ControllerL|R`) y sensores (`/Game/BreathL|R`) y los había colgado del `BP_XRPawn`; al hacerlo **desaparecía todo** en Play. Este BP los saca del pawn: los tiene en el mundo, donde se autoran mirándolos, y **se los engancha a la mano en `BeginPlay`**.
- **Y es el examen de portabilidad del sistema de dibujo** (pedido de Beltrán: las mecánicas tienen que poder montarse en cualquier pawn). Ver `docs/` y la memoria del mandato.
- **Estado**: 🟢 **DIBUJA EN VISOR** (Beltrán, 2026-09-03 tarde: "Funciona") — anclaje + trazo desde el Marker con el gatillo, ambas manos. 🟡 Háptica continua agregada el mismo día (clon de `DrawHaptic` del sensor), **sin probar en visor todavía**.
- 🐛 **Bug encontrado y corregido (2026-09-03, la revisión pedida por Beltrán)**: `BeginStroke` tiene un 5º parámetro **`Mat`** desde el port de Neural Canvas (2026-08-31) — en la obra lo entrega la paleta (`Palette.CurBrushMat`). El rig lo llamaba **sin material** → `OpenSection` hacía `SetMaterial(None)` y el trazo habría salido con el material gris por defecto (o invisible). Fix: perilla **`DrawMat`** (ver abajo) cableada al pin `Mat`.

## Componentes
| Componente | Qué es |
|---|---|
| `HandRef` | `SkeletalMeshComponent` con `SKM_MannyXR_right|left`, **`Hidden in Game`**, `NoCollision`, sin sombra. 🔴 **Es SOLO una referencia visual**: no viaja a ningún lado, existe para que Beltrán calce el mando contra la mano **en el viewport, sin Play**. En juego no se dibuja. |
| `Controller` | El mesh del mando (`/Game/ControllerR|L`). |
| `Breath` | El mesh del sensor (`/Game/BreathR|L`). |
| `Marker` | Esfera del motor a escala **0,02 = 2 cm de diámetro**. 🔴 **Es el origen del trazo de dibujo**, no la mano. |

`bRightHand` (instance-editable) manda: el **Construction Script** elige el trío correcto de meshes según su valor, así que tirar el actor al mundo y marcar el check ya muestra la mano correcta en el viewport.

## Cómo se autora (la parte que importa para Beltrán)
Se selecciona el actor, se abre el árbol de componentes en el Details y se mueve **el componente** (`Controller`, `Breath` o `Marker`) con el gizmo contra la mano fantasma. **La transform relativa que quede ES el offset respecto de la mano real** — el `AttachComponentToComponent` usa `KeepRelative`, y `HandRef` está en el origen del actor, que es el mismo espacio que el componente de la mano del pawn. **La posición del actor en el mundo no importa**: se pone donde sea cómodo mirarlo.

### 🆕 2026-09-03 — los offsets autorados están HORNEADOS como default (pedido de Beltrán al pasar a TestMeshes)
- **Mano derecha = los templates de componentes del BP** (escritos vía `<Comp>_GEN_VARIABLE`): Controller (2.791, 9.5, −4.296)/(P−90, Y−10) · Breath (2.791, 9.5, −3.5)/ídem · Marker (4.167, 14.4, −5.615) escala **0.015**. Un rig nuevo con `bRightHand=true` **nace perfecto**, y el gizmo sigue funcionando para ajustar instancias.
- **Mano izquierda = espejo en el Construction Script** (rama else, literales): x, pitch y yaw invertidos — el espejo exacto que Beltrán autoró. Un rig con `bRightHand=false` también nace perfecto; ⚠ el gizmo NO manda en sus componentes (el CS lo pisa en cada reconstrucción) — para ajustar la izquierda se editan los literales del CS (o se ajusta la derecha, que es la master del espejo).
- **Uso en un nivel nuevo**: arrastrar 2 rigs, marcar `bRightHand=false` en uno. Listo — perillas y offsets vienen solos. Colocados así en **`/Game/TestMeshes`** (2026-09-03).
- 🔴 **Tres trampas MCP pagadas en esta pasada**: (1) `set_properties` multi-campo sobre el componente de una INSTANCIA registra el delta a medias (quedó solo la x; el rerun del CS se comió el resto) — para offsets de instancia, mejor gizmo o template; (2) una instancia **captura los valores del template AL COLOCARSE**: cambiar el template después no la actualiza, y (3) `reset_properties` vuelve a lo capturado en el spawn, no al template nuevo → la vía para "re-capturar" es **reemplazar el actor** (borrar el propio y re-colocarlo).

## Grafos
```
BeginPlay: SetActorEnableCollision(false) → Delay 0.2 → _hand = FindHand(bRightHand)
           → AttachComponentToComponent × 3 (Controller · Breath · Marker) a _hand, KeepRelative
           → InitDraw()
EventTick: DrawTick()
IA_Shoot_Right / IA_Shoot_Left  (Started → DrawPress(bRight) · Completed → DrawRelease(bRight))
```
### 🆕 2026-09-03 — `FindHand(bRight)`: el anclaje es AGNÓSTICO DEL PAWN (pedido de Beltrán: "deben sumarse a cualquier pawn")
El `CastToBP_XRPawn` se eliminó. `FindHand` recorre `GetComponentsByClass(GetPlayerPawn, SceneComponent)` y devuelve el componente cuyo **`GetObjectName` == "HandRight"/"HandLeft"**; si no encuentra, print `RIGDRAW NOHAND` y devuelve null. **El contrato del Controller: cualquier pawn cuyo componente de mano se llame `HandRight`/`HandLeft`** — lo cumplen `BP_XRPawn` (template) y `BP_VRPawn_SC` (verificado por log con el SC en TestMeshes, 15:31).
🔴 **Trampa pagada: `GetDisplayName` de un componente devuelve el nombre DECORADO** (`BP_VRPawn_SC0.HandRight SKM_MannyXR_right`) — una comparación exacta contra "HandRight" jamás matchea. Para nombre pelado de componente: **`Utilities|GetObjectName`**.
🔴 **Trampa MCP: `add_function_graph` tras `remove_function_graph` sin compilar en el medio devuelve `<Nombre>_0`** (el nombre sigue ocupado). Orden: remove → compile (fallará por el call colgante, no importa) → add.
🔴 **2026-09-03 (tarde): los eventos eran `IA_Attract_*` (IMC_Touch) y EN VISOR NUNCA DISPARARON** (pasada de Beltrán: `INIT` ×2, `PRESS` ×0 en todo el log). Se reemplazaron por **`IA_Shoot_Right/Left`** — el camino PROBADO del proyecto: es el que usa `BP_Sensor_Soul` para `DrawPress`/`DrawRelease` en el Persistent y `BP_Instructions` en Breath, y funciona en cualquier nivel porque `IMC_Weapon_L/R` (que mapean `IA_Shoot_*` al gatillo por mano) están en `DefaultMappingContexts` de `Config/DefaultInput.ini` = se registran solos. Nota en negativo con la pieza exacta: **`IA_Attract_*` como evento de un ACTOR jamás fue probado en visor; lo probado por mano es `IA_Shoot_*`** (assets-existentes §ZANJADO).
- **`InitDraw()`** — `EnableInput(self, pc)` (pin `self` vacío = el actor, PC en su pin — verificado con `get_node_infos`) + `AddMappingContext(IMC_MenuTrigger, 1000, bIgnoreAllPressedKeysUntilRelease=False, bForceImmediately=True)` (cambiado de IMC_Touch a IMC_MenuTrigger para clonar el combo exacto del sensor; para el gatillo es vestigial — lo operativo son los IMC_Weapon automáticos) + spawnea **su propio `BP_DrawCanvas` en identidad** → `CanvasRef`. Print `RIGDRAW INIT`.
  🔴 **Va DESPUÉS del Delay a propósito**: el `BeginPlay` de un actor del nivel corre ~20 ms **antes** de que exista el PlayerController, y ahí `EnableInput` es un no-op silencioso.
- **`DrawPress(bRight)`** — compuerta `bRight == bRightHand && bCanDraw` → `BeginStroke(0, Marker.WorldLocation, Marker.UpVector, DrawColor)` + `bDrawHeld = true`. Print `RIGDRAW PRESS`.
- **`DrawRelease(bRight)`** — `EndStroke()` + `bDrawHeld = false`.
- **`DrawTick()`** — `DrawHaptic()` (siempre, así el flanco de apagado corre) → si `bDrawHeld`: `AddPoint(Marker.WorldLocation, Marker.UpVector, DrawWidth, Calm=1.0)`.
- **`DrawHaptic()` / `DrawHapOff()`** (2026-09-03) — **clones textuales de las del sensor** (leídas por DSL y copiadas, `bTookRight`→`bRightHand`, sin la compuerta `bStroking`): zumbido continuo `SetHapticsByValue(1.0, HapticAmp)` en la mano que dibuja mientras `bDrawHeld`; `bWasDrawHap` marca el flanco y `DrawHapOff` apaga limpio (`SetHapticsByValue(0,0)`). ⚠ DSL: los setters/getters de bools pierden la `b` SOLO en forma completa (`Variables|Default|SetWasDrawHap`); y el read etiqueta la llamada local como `Class|BPSensorSoul|DrawHaptic` — falso, verificado `|DrawHaptic` con self propio.
- ⚠ **`DrawEdge` / `DrawMaybeRelease` quedaron HUÉRFANAS**: eran el intento de disparar por poll de tecla, descartado con dato (las teclas XR no llegan al PlayerController). Borrarlas cuando el dibujo funcione.

## Perillas (instance-editable) — 🔴 escritas a mano en las DOS instancias
`DrawWidth` **1.8** cm (la paleta de la obra usa 1,5 / 3 / 5,5 tras Neural Canvas) · `DrawColor` (0.35, 0.7, 1, 1) · `bCanDraw` true · `bRightHand` · **`DrawMat`** (nueva 2026-09-03): el material del pincel, default **`/Game/Drawing/Material/M_Emissive_Inst`** (pincel 1 de la paleta de la obra; el otro es `M_Spray`) · **`HapticAmp`** (nueva 2026-09-03): amplitud del zumbido al dibujar, **0.25** (el valor afinado de V2/sensor) · **`bShowController` / `bShowBreath` / `bShowMarker` / `bShowHand`** (nuevas 2026-09-03, default true): visibilidad por mesh. Las 3 primeras aplican en el **Construction Script** (se ven en viewport sin Play); `bShowHand` apaga la mano fantasma (`HandRef`, CS) **y la mano real del pawn** (`SetVisibility(_hand)` en BeginPlay tras el attach — con `false` la oculta; con `true` NO fuerza a mostrar una mano que el pawn tenga en Hidden-in-Game, como las del XRPawn del template). **Todas escritas en el CDO Y en las dos instancias, releídas y verificadas** (las bShow* nacieron en false en las instancias — la trampa de siempre — y se corrigieron a mano).
🔴 Nacieron en **0 / false / (0,0,0,0)** en las instancias colocadas porque las variables se agregaron después (`gotchas.md`, regla de la instancia). Con `bCanDraw=false` no dibuja, con `DrawWidth=0` el trazo es invisible, con el color en negro transparente tampoco se ve. **Si se agrega una perilla nueva, escribirla en las dos instancias y releerla.**

## Decisiones y por qué (no re-derivar)
- **`BP_DrawCanvas` se reusa INTACTO** como motor de geometría; el rig solo le manda puntos. Es la misma decisión que tomó Surrounding V2.
- **Un canvas POR RIG** (no compartido): el canvas tiene un solo trazo activo (`bDrawing`/`PointCount`), así que dos manos sobre el mismo canvas se pisarían.
- **`Breath` y `Marker` son hermanos de `Controller`**, no hijos: así cada uno tiene su offset propio contra la mano y moverlos no arrastra a los otros. Si se quiere el sensor pegado al mando, reparentar `Breath` bajo `Controller`.
- **Las manos del pawn están `Hidden in Game`** (pedido de Beltrán: ver solo el mando). Son de clase **`BP_MannequinsXR`**, no `SkeletalMeshComponent` puro.
- **El input NO se resolvió con `IMC_MenuTrigger`**: ese contexto mapea `IA_Continue`, que no distingue mano. `IMC_Touch` (`IA_Attract_Left/Right`) sí. Mapa completo medido en `references/assets-existentes.md` §ZANJADO 2026-09-03.

## Diagnóstico sembrado (limpiar al validar)
`RIGDRAW INIT` (una vez por rig; si se repite, hay un bucle de exec) · `RIGDRAW PRESS` (llega el gatillo). ✅ El `RIGDRAW AX` por frame **ya se borró** (2026-09-03, con sus 4 alimentadores puros; `DrawTick` quedó solo `if bDrawHeld → AddPoint`).

## TODO
- [x] ~~Una pasada de visor mirando `RIGDRAW PRESS`~~ → ✅ **DIBUJA** (Beltrán en gafas, 2026-09-03).
- [x] ~~Háptica~~ → ✅ **validada por Beltrán en gafas** ("Funcioan").
- [ ] ⚠ Al reabrir **L_XRTemplate**: sus 2 rigs tendrán las `bShow*` en false (variables nuevas, trampa de la instancia) → escribirlas en true, o los meshes no se verán.
- [ ] Cambiar el pawn a `BP_VRPawn_SC` (ofrecido por Beltrán 2026-09-03): su BeginPlay es autocontenido (tracking origin + IMCs + recentrado, sin director). Toca: GameMode del nivel + el cast y los getters `HandLeft/HandRight` del BeginPlay del rig. Hacerlo DESPUÉS de la primera tinta, una variable por vez.
- [ ] **Paleta en la mano contraria + háptica en la mano que dibuja** — la definición completa de la mecánica según Beltrán. Reusar `BP_BrushPalette` (entrega color+ancho+material) y la háptica ya afinada de Surrounding V2.
- [ ] Borrar el print PRESS y las dos funciones huérfanas al validar.
- [ ] Si el trazo sale tembloroso: portar el **One-Euro** que ya está afinado en `BP_Sensor_Soul` (`DrawFilter`).
- [ ] **El paso grande**: extraer `BPC_DrawTool` del modo 5 del sensor y que este rig sea su primer consumidor. El componente **no** debe llamar `EnableInput` ni agregar contextos: recibe `Press()`/`Release()`/`SetTip()` del que lo hospeda.
