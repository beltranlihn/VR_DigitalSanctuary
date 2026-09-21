# BP_StageShell_SC — la esfera de color que reemplaza a las salas (Core/Flow/)

> `/Game/SoulCharger/Core/Flow/BP_StageShell_SC` · creado 2026-09-21 · **una instancia** (`Director_Shell`) en `MapsV3/L_SoulCharger_V3`.
> Pedido de Beltrán: *"Cada lugar, en vez del mesh cilíndrico actual que hace de espacio, tendrá una esfera de color… El cambio entre una etapa y otra ya no será avanzando con fade a negro, sino que la esfera contenedora tiene que transicionar del color actual al siguiente de manera gradual."*
> **Estado: 🟢 la máquina verificada en PIE** (ciclo de 5 etapas con los tiempos exactos, 23 estaciones recogidas, cero `Accessed None`). ⬜ **Sin visor** — el ritmo del viraje y los colores son juicio de autor.

## Qué es
El director de las 5 etapas **en el mismo sitio**. Hace tres cosas y nada más:
1. **Vira el color** de un único `BP_Ganzfeld_SC` (el cascarón que envuelve al usuario) del color de la etapa actual al de la siguiente.
2. **Prende solo la etapa activa**: todo actor tagueado `STAGESTATION` se oculta **y se le apaga el Tick**; los que además llevan `STAGE_<n>` se encienden en su turno.
3. **Avisa cuando terminó** (`OnStageReady` + el estado que poleé [[BP_Director_Story]]).

🔴 **No es dueño de la esfera**: la busca por el tag `stage_shell` y le empuja los parámetros al material de su `StaticMeshComponent`. Así Beltrán sigue autorando el cascarón seleccionándolo en el viewport (radio, gradiente, modo), y el director solo manda el **color por etapa**.

## 🔴 Por qué es la opción más barata en el APK
| Palanca | Por qué |
|---|---|
| **Un solo cascarón, con `M_GanzSolid_SC`** | el modo fluido cuesta ~12 ms de los 13,9 del presupuesto; el liso ~4 y deja lugar al efecto de adelante. Medido en visor el 2026-09-16: metaball + cascarón liso = **9,4–11,4 ms, 72–73 fps** |
| **Nunca dos cascarones a la vez** | un crossfade entre dos esferas pagaría el fill dos veces. Por eso se lerpean los **parámetros**, no se mezclan dos actores |
| **`SetActorTickEnabled(false)` además de ocultar** | ocultar no apaga el Tick: en la galería se midieron **101 actores tickeando escondidos** |
| **Cero `LoadStreamLevel` entre etapas** | las transiciones de sala costaban 604 ms repartidos en 42 frames. Acá no hay ninguna |

## Registro de variables
### A - Etapas (instance-editable)
| Variable | Default | Rol |
|---|---|---|
| `StageTags` | `STAGE_1` … `STAGE_5` | el tag de cada etapa. **Índice 0 = etapa 1.** |
| `TopColors` | 5 colores | color **de arriba** del gradiente, por etapa (azul · rojo · morado · naranja · verde) |
| `BotColors` | 5 colores | color **de abajo**. El `ColorMid` se calcula como el lerp 0,5 de los dos |
| `ShellTag` | `stage_shell` | cómo encuentra el cascarón |
| `StationTag` | `STAGESTATION` | qué actores administra |
| `ShellBright` | 1.0 | el `Brightness` al que llega el cascarón encendido |
| 🎨 `PreviewStage` | 0 | **vista previa en el editor**: 1-5 pinta la esfera con la fila de esa etapa; 0 = apagado. Solo editor (ver abajo) |

### B - Tiempos (instance-editable)
| `FadeTime` | 3.0 s | cuánto dura el viraje de color |
| `HoldAfter` | 0.6 s | sostén con el color ya puesto antes de avisar |
| `bAutoDemo` | false | 🧪 **recorre las 5 etapas solo**, sin el director del guión. Es como se verificó por log |
| `AutoDemoGap` | 12 s | la pausa del modo automático |

### Z - Estado (no tocar)
`Stage` (1-5; 0 = ninguna; −1 = final) · `Phase` (0 reposo · 1 virando · 2 sostén) · `Elapsed` · `IdleTime` · `From/To Top/Bot/Bright` · `bEnding` · `bReady` · `Stations` (recogidos en `Boot`) · `ShellRef` · `ShellMesh`.

## Estructura de grafos
- **`BeginPlay`** → timer 0,3 s → **`Boot`**. El retraso es el de siempre: `BeginPlay` corre antes del `Possess`.
- **`Tick`** → `TickPhase(DeltaSeconds)`.

| Función | Responsabilidad |
|---|---|
| `Boot` | recoge `Stations` por tag, `HideAll`, cachea el cascarón y su mesh, lo deja **apagado** (`Brightness` 0 y oculto) con los colores de la etapa 1 cargados en `To*`. Si no hay cascarón, lo dice por log en vez de fallar en silencio |
| `HideAll` | oculta **y apaga el Tick** de todas las estaciones |
| `ShowStage(Idx)` | enciende las que tienen `StageTags[Idx−1]` |
| `ShellVis(On)` | prende/apaga el cascarón, con guarda de validez |
| `PushLook(Top, Bot, Bright)` | 🔴 el corazón: 3 `SetColorParameterValueOnMaterials` + 1 escalar sobre el mesh del cascarón. Crea y reusa el MID solo, sin variable MID |
| `GoToStage(Idx)` | **la API pública.** `From* = To*`, `To*` = la fila de la tabla, oculta la etapa vieja y arranca la fase 1. Con `Idx ≤ 0` es el **final**: mantiene el color y lleva el brillo a 0 |
| `Smoother(T)` | smootherstep `6t⁵−15t⁴+10t³`, la misma curva del resto del proyecto |
| `TickPhase(DT)` | reparte por fase (una función por fase, como [[BP_Director_Rooms]]) |
| `PhaseFade(DT)` | lerpea los 3 parámetros por `Smoother(Elapsed/FadeTime)`; al llegar, `FadeDone` |
| `FadeDone` | si es el final: apaga el cascarón y avisa. Si no: `ShowStage(Stage)` y pasa a la fase 2 |
| `PhaseHold(DT)` | espera `HoldAfter` y dispara **`OnStageReady`** |
| `PhaseIdle(DT)` | solo el modo automático de test |

## Contrato con el resto
- **Entrada:** `GoToStage(Idx)` — lo llama `NextRoom()` de [[BP_Director_Story]] con el número de sala (1-5), y `EndShell()` con −1 para el final.
- **Salida:** el dispatcher `OnStageReady`, y el estado (`Phase == 0` y `Stage == Room`) que **poleé** `CheckShell` del director del guión. Se poleé y no se bindea por la misma razón que los botones de la galería: se auto-recupera y no depende del orden de `BeginPlay`.

## Cómo se agrega un elemento a una etapa
**Una sola cosa:** ponerle al actor los tags **`STAGESTATION` + `STAGE_<n>`**. Nada más — ni arrays, ni código. Es el mismo diseño por tags que pidió Beltrán para la galería.
⚠ **No taguear los `BP_Anchor`/TargetPoint**: al encenderlos aparece su marcador (una esfera gris). Se dejan sin `STAGESTATION` y con su tag funcional solamente.

## 🔩 Trampas pagadas al construirlo (las generales van a gotchas.md)
1. 🔴 **Llamar a una función PROPIA con args posicionales choca con `self`**: `(CallFunction|ShowStage x)` falla con *"Could not connect pin Stage to self"*. **Siempre keywords**: `(CallFunction|ShowStage :Idx x)`.
2. 🔴 **El `elif` no admite un `else` hermano**: `(if a … (elif b …) (else …))` es un error de parseo. El `else` va **DENTRO** del `elif`: `(if a … (elif b … (else …)))`. Y **tampoco** se puede poner un `if` anidado antes de un `elif` → por eso las fases se partieron en `PhaseFade`/`PhaseHold`/`PhaseIdle`.
3. **`Utilities|Name|Equal(Name)` no existe** como `type_id` escribible (el `read` lo muestra pero no se puede escribir). Se compara con `==` y el literal envuelto: `(== (GetWaitFor) (Utilities|Name|MakeLiteralName "shell"))`.
4. **Los arrays de `LinearColor` SÍ se escriben con JSON** (`{"r":..,"g":..,"b":..,"a":..}`) en el CDO — la trampa del "solo la primera componente" es específica de los **transforms de SceneComponent**, no de todo.
5. `CastShadow` **no es propiedad del actor**: va en el componente `Volume` del metaball (`castShadow` en minúscula).

## TODO
- [ ] 🔴 **Visor**: el ritmo del viraje (`FadeTime`) y los 5 pares de color son decisión de autor.
- [ ] Medir en device la etapa 4 (metaball + 20 esferas + 8 slots juntos) y el modo GROUP de la 3.
- [ ] Decidir si el cascarón debe seguir a la cabeza o quedarse fijo (hoy fijo, centrado en la parada del pawn).

## Relacionados
- [[BP_Ganzfeld_SC]] — el cascarón que maneja · [[BP_Director_Story]] — quien le pide las etapas · [[BP_Director_Rooms]] — ahora solo carga el Hall · [[BP_GalleryDirector_SC]] — de donde salió el diseño por tags


## 🔴🔴 2026-09-21 (noche) — UNA ESTACIÓN SE APAGA EN TRES CANALES, NO EN DOS
Lo cazó la primera pasada completa, con el log dando el nombre del culpable:
```
BEAM R corto contra: PulseField_Heart
BEAM L corto contra: PulseField_Heart
```
El plano de las ondas del latido (etapa 2) seguía **bloqueando el line-trace del beam** durante Attracting, **invisible y sin Tick**. `SetActorHiddenInGame` saca el dibujo y `SetActorTickEnabled` saca la lógica, pero **la colisión queda viva**.

🚩 **La forma general, y por qué es nueva:** en V2 cada sala era un sublevel y lo de la otra sala **no estaba en el mundo**. Al juntar las 5 etapas en el mismo sitio, **lo oculto de una estorba a la otra**. Es la misma familia que la saga de colisionadores fantasma (viñeta → proto ameba → HUD), por una puerta nueva.

✅ `HideAll` y `ShowStage` hacen ahora **`Collision|SetActorEnableCollision`** además de la visibilidad y el Tick. Verificado en PIE: el beam se arma y no queda ni una línea de choque.
👉 **La regla de este BP: visibilidad · Tick · colisión.** Si algún día se suma un cuarto canal (audio de un componente, por ejemplo), va en las mismas dos funciones.

## 🔗 2026-09-21 — el nivel V2 sigue funcionando (repliegue automático)
`BP_Director_Story` y `BP_Director_Rooms` son **compartidos**: la cirugía de V3 habría dejado `MapsV2/L_SoulCharger` trabado esperando una esfera que ahí no existe.
✅ **`ExitHall()` y `GoShell()` ramifican por `IsValid(ShellRef)`**: con esfera → V3 (viraje de color); sin esfera → el camino viejo (`Rooms.EndStage()` + espera `"door"`). `NextRoom` pone `WaitFor = "shell"` **antes** de llamar a `GoShell`, justo para que el repliegue pueda pisarlo con `"door"`.
👉 Un solo código sirve a los dos niveles, y V2 queda utilizable como referencia (que es lo que pide `CLAUDE.md`).

## 🎨 2026-09-21 (tarde) — LA HERRAMIENTA PARA AJUSTAR LOS COLORES (sin Play)
Pedido de Beltrán: *"Dame las herramientas para poder ajustar esos colores"*.

**Cómo se usa** — todo en la instancia **`Director_Shell`**, categoría **A-Etapas**:
1. **`PreviewStage`** = el número de la etapa que querés mirar (**1 Entering · 2 Recognizing · 3 Loving · 4 Attracting · 5 Surrounding**). La esfera toma ese color **en el viewport, al instante**.
2. Con la vista previa puesta, editá **`TopColors[n−1]`** (arriba) y **`BotColors[n−1]`** (abajo): se repinta **en vivo**. El color del medio se calcula solo (lerp 0,5), y es también el fondo del que nace el título de etapa.
3. **`ShellBright`** = el brillo al que llega la esfera. **`FadeTime`** (B-Tiempos) = cuánto tarda el viraje de una etapa a la otra.
4. **`PreviewStage = 0`** apaga la vista previa.
👉 **Para verlo en gafas**, `DebugStartRoom` de `Director_Story` arranca directo en cualquier etapa con su color (0 Hall · 1-5 · −1 obra entera — los 6 probados en PIE el 2026-09-21).

**Cómo está hecho** (mínimo): el Construction Script, si `1 ≤ PreviewStage ≤ Length(TopColors)`, llama **`PreviewPaint(Idx)`**, que busca el cascarón por `ShellTag`, cachea su mesh en `ShellMesh` y llama al **mismo `PushLook`** que usa el viraje en juego — una sola fuente para los nombres de los parámetros.
- **Es solo de editor, sin conflicto con el juego**: al arrancar, `Boot` deja el cascarón apagado y oculto, y desde ahí manda el director.
- ⚠ Si se edita el **propio cascarón** (`Shell_Stages`: radio, modo), su Construction Script le vuelve a poner sus colores. Se recupera tocando `PreviewStage` de nuevo.
- ✅ Verificado leyendo el MID del cascarón (`vectorParameterValues`): `PreviewStage 3` → `ColorTop (0,42 · 0,10 · 0,80)` morado; `4` → `(0,95 · 0,35 · 0,05)` naranja.
- Diseñada con **0 = apagado** a propósito: la variable nace en 0 en la instancia ya colocada, que es el valor neutro (gotcha 352).
