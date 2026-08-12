# BP_Room — la sala placeholder (Core/Rooms/)

## Purpose
La sala vacía de la obra: piso + muro, sin techo. Es lo que se carga y descarga como **streaming sublevel** alrededor del pawn. Una sola instancia por sublevel, **siempre en el origen** — todas las salas se construyen en el mismo origen (`docs/OBRA-SOUL-CHARGER.md` §9.2), y el negro tapa el intercambio.

No es un `BP_StageBase`: no sabe nada de etapas ni de mecánicas. Solo es el espacio y su luz.

## Status
🟡 **Construido y compilando. Falta el test en visor.** Creado 2026-08-11 (rama `core/esqueleto`).

## Componentes
| Componente | Qué es | Transform |
|---|---|---|
| `Floor` | `/Engine/BasicShapes/Cylinder` escalado (10, 10, 0.1) = disco de **10 m de diámetro** y 10 cm de espesor. Material `MI_RoomFloor`. | `relativeLocation Z = -5` para que **la cara superior quede en Z=0**. |
| `Wall` | El mismo cilindro escalado (10, 10, 4.5) = muro de **4,5 m**. Material `MI_RoomWall` (two-sided, se ve desde adentro). | `relativeLocation Z = +225` para que abarque **0..450**. |

🔴 **`PrimitiveTools.add_cylinder` IGNORA el `local_transform`** — aplica la escala derivada de `radius`/`height` pero deja `relativeLocation` en (0,0,0). Hay que setear la posición después con `ObjectTools.set_properties` y **verificarla con `get_properties`**. El cilindro del motor está centrado en su origen (bounds −50..+50), de ahí los offsets de arriba.

✅ **No hace falta recortar el techo.** La tapa superior del cilindro cae por encima de `WallHeight`, donde el gradiente del material ya vale 0 → **renderiza negra** y se confunde con el vacío. Cero geometría extra, y además ocluye el exterior, que es lo que §9.2 pide ("el exterior de los espacios debe ser negro profundo").

## Registro de variables

### Autoral — las setea el director o se editan por instancia
| Variable | Tipo | Rol |
|---|---|---|
| `RoomName` | Text | Nombre de la sala. Hoy no se muestra en ningún lado; existe para que el cartel de `BP_Door` y el HUD de debug lo lean. |
| `AccentColor` | LinearColor | **El color de la luz de la sala.** Se aplica a `LineColor` del piso y a `WallColor` del muro. Es lo que hace que la sala A y la sala B se vean distintas siendo el mismo asset. Default (0.55, 0.70, 0.85). |
| `MaxBrightness` | float | Brillo cuando `LightAlpha` = 1. Default 1.0. La palanca para subir o bajar toda la sala sin tocar materiales. |
| `InitialLight` | float | Con cuánta luz **nace** la sala. Default **0.0** → la sala aparece negra y el director la sube. Es lo que hace que el usuario nunca vea la sala nueva "encendida de golpe". |

### Estado
| Variable | Tipo | Rol |
|---|---|---|
| `LightAlpha` | float | Luz actual 0..1. La escribe `SetLight`. Existe para que el director pueda leerla y hacer rampas. |

## Estructura de grafos

**`InitRoom()`** — aplica el color de acento a los dos materiales y pone la luz en `InitialLight`.
```
AccentColor -> SetVectorParameterValueOnMaterials(Floor, "LineColor")
            -> SetVectorParameterValueOnMaterials(Wall,  "WallColor")
SetLight(InitialLight)
```

**`SetLight(Alpha)`** — la única palanca de luz.
```
LightAlpha = Alpha
b = Alpha * MaxBrightness
SetScalarParameterValueOnMaterials(Floor, "Brightness", b)
SetScalarParameterValueOnMaterials(Wall,  "Brightness", b)
```
🔴 Los dos materiales exponen el parámetro con **el mismo nombre `Brightness`** a propósito: una sola llamada modula la sala entera.

**`Configure(NewRoomName, NewAccent)`** — setea las dos variables y llama `InitRoom`. Es la puerta de entrada del director: §9.8 quiere que el look salga de un DataAsset de la etapa, no de editar el BP.

**`Dissolve(WaitTime)`** 🆕 (2026-08-12) — **el caso terminal de la obra** (plan §0 #7): al completarse la última carga no hay avance ni puerta — la arquitectura se deshace en el lugar y queda el exterior (`BP_Void`). Placeholder de la animación "transformer" futura:
```
RampLight(0, WaitTime)                      ← la sala se apaga (en un mundo sin luces, apagar es desaparecer)
timer "FinishDissolve" a max(WaitTime,0.01)
```
**`FinishDissolve()`** — `SetVisibility(false)` en `Floor` y `Wall` + log `ROOM: la sala se deshizo - queda el exterior`. 🔴 **Esconder los meshes es obligatorio, no cosmético:** un muro opaco en negro sigue siendo un **oclusor** — taparía el degradado del vacío y las partículas de la constelación (misma lección que el LogoPlane invisible de la intro). Lo llama `BP_StageDirector.FinishObra` con `LightFadeTime`.

**`EventGraph`** — solo `BeginPlay -> InitRoom()`.
⚠ `BeginPlay` de un actor de sublevel corre **durante `AddToWorld`**, es decir **antes** de que el nivel quede visible y antes de que dispare `OnLevelShown`. Por eso alcanza para que la sala nazca negra sin que se vea un flash. El fade sphere está igual por encima como red.

## Materiales (Core/Rooms/Materials/)

**`M_RoomFloor`** — Unlit · Opaque · una cara · `bFullyRough`.
Grilla construida sobre **posición de mundo**, no sobre UVs, así que la escala del mesh no la estira:
```
WorldPosition.XY / GridSize -> Frac -> |x - 0.5| -> max(dx, dy)
  -> SmoothStep(0.5 - LineWidth, 0.5)        = máscara de línea
  -> Lerp(BaseTone, LineColor) * Brightness  -> Emissive
```
🔴 **El suelo NECESITA este patrón** (§9.2): sin referencia visual el avance no se lee como avance y la caminata se siente rara sin que se sepa por qué. No es decoración.

| Parámetro | Default | Qué ajusta |
|---|---|---|
| `GridSize` | 50 | Lado de la celda en cm. Más chico = más referencia de movimiento, más aliasing. |
| `LineWidth` | 0.06 | Grosor de la línea como fracción de celda. |
| `LineColor` | (0.55,0.70,0.85) | Lo pisa `AccentColor`. |
| `BaseTone` | (0.015,0.02,0.03) | El piso entre líneas. Muy bajo pero **no negro**: es la diferencia entre "un piso" y "líneas flotando en el vacío". |
| `Brightness` | 1.0 | Lo maneja `SetLight`. |

**`M_RoomWall`** — Unlit · Opaque · **TwoSided** (verificado efectivo) · `bFullyRough`.
```
saturate(WorldPosition.Z / WallHeight) -> OneMinus -> Power(Falloff)
  -> * WallColor * Brightness -> Emissive
```
Brillante abajo, apagándose hacia arriba: luz en el aire, no una pared pintada.

| Parámetro | Default | Qué ajusta |
|---|---|---|
| `WallHeight` | 450 | Altura a la que el muro ya llegó a negro. **Es lo que hace invisible la tapa del cilindro** — si lo subís por encima de 450, aparece techo. |
| `Falloff` | 2.2 | Curva del degradado. Más alto = la luz se queda más pegada al piso. |
| `WallColor` | (0.20,0.28,0.42) | Lo pisa `AccentColor`. |
| `Brightness` | 1.0 | Lo maneja `SetLight`. |

Las instancias `MI_RoomFloor` / `MI_RoomWall` quedan con `Brightness` visible **a propósito**, para que la sala se pueda autorar en el viewport; en runtime `BeginPlay` la baja a `InitialLight`.

## Session log
- **2026-08-11** — creado. `L_Room_Placeholder.umap` duplicado de `L_Test_Stage` y vaciado (sin `SkyAtmosphere`, `SkyLight`, `DirectionalLight`, `PlayerStart` ni el piso del template). Una instancia `BP_Room` en el origen. Materiales verificados con `list_parameters` (los 5 y los 4 parámetros salen bien) y `get_properties` (`twoSided` efectivamente `true`).

## TODO
- [ ] **Test en visor** — es lo único que manda.
- [ ] Que el director llame `Configure` al recibir `OnLevelShown` (lo consume `BP_StageDirector`, todavía sin construir).
- [ ] Decidir si el piso lleva falloff radial. Hoy no: el muro tapa el borde del disco, así que el canto no se ve. Si en algún momento el muro se abre o baja, hay que agregarlo.
- [ ] Medir en device. Son 2 draws opacos unlit, debería ser gratis, pero el muro llena mucha pantalla y el proyecto es **fill-rate bound**.

## Open questions
- ¿La grilla de 50 cm es la escala correcta de referencia para caminar a 1,75 m/s, o conviene más grande para que no aliasee en Quest? Se decide en visor.
- `InitialLight = 0` deja la sala negra si el director no la sube nunca. Es deliberado (falla en oscuro, no en flash), pero conviene que el `BP_DebugDirector` avise cuando una sala lleva N segundos con luz 0.
