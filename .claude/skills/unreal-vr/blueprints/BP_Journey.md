# BP_Journey — el recorrido completo de la obra (Core/Movement/)

## Purpose
**Un solo spline que cubre TODO el viaje**, dividido en paradas que Beltrán arrastra en el viewport. Reemplaza el modelo anterior, donde cada sala se recorría con un segmento recto de 10 m reconstruido en el origen y las 6 salas se apilaban en el mismo lugar.

Pedido de Beltrán (2026-08-13): *"un spline largo que toma todo el recorrido, dividido en puntos. Así yo puedo mover esos puntos como me parezca. Y el pawn avanza de punto 1 a punto 2, punto 2 a punto 3... y definimos el tiempo que toma recorrer entre uno y otro."*

## Status
🟢 **Recorrido y caminata verificados en PIE** (2026-08-13): el director lo usa para TODO (corredor de la intro incluido). Paradas re-escritas por la revisión de narrativa (2026-08-13 tarde): aparición lejos en el vacío + llegada frente a la puerta del Center + Hall calzando con su preview.

## Cómo se autora (sin tocar Blueprints)
- El actor (`BP_Journey_C_2` tras la renovación del 2026-08-13) vive en `L_Persistent` en el origen. Su componente **`Route` (SplineComponent) se edita en el viewport**: arrastrar puntos, agregar/quitar, cambiar tangentes.
- **Paradas actuales (8)**, todas a Z=0 — el walker coloca el pawn en la Z del spline, y el pawn a Z=0 es lo que da la altura de cámara medida (~185):
  | Índice | X | Qué es |
  |---|---|---|
  | 0 | −2300 | aparición en el vacío / menú (= `PlayerStart` y `MenuRoot`) |
  | 1 | −650 | llegada frente a la puerta del Center, a 1,5 m (la puerta se deriva sola: parada1.X + `DoorAhead` 150 = −500, el borde del Hall; el timbre = anchor `BellSpawn` en −615, z130) |
  | 2 | 0 | Hall (= su preview) |
  | 3 | 1200 | Entering |
  | 4 | 2400 | Recognizing |
  | 5 | 3600 | Loving |
  | 6 | 4800 | Attracting |
  | 7 | 6000 | Surrounding |
- ⚠ **Si se arrastra la parada 1, mover también el anchor `BellSpawn`** (la puerta la sigue sola; el timbre no).
- 🔴🔴 **Contrato con los mapas (decisión de Beltrán 2026-08-13): el MAPA es la autoridad de posición de cada sala.** Cada `L_Room_*` guarda su sala en su posición mundial real; las paradas 2..7 **deben coincidir** con esas posiciones (y con los previews). El director ya no mueve salas: si se muda una sala, se muda **su mapa + su parada + su preview**, los tres juntos.
- **`LegTimes`** (array de float, instance-editable): segundos del tramo *i* (de la parada *i* a la *i+1*). Hoy `[10, 5, 8, 8, 8, 8, 8]` (tramo 0 = corredor de la intro, 10 s placeholder hasta la voz real de ~45 s; 🆕 **tramo 1 = la entrada CAMINANDO al Hall tras el timbre, 5 s** — ya no es teleport). **`DefaultLegTime`** (8 s) se usa si el array es más corto que la cantidad de tramos → **agregar un punto nunca rompe nada**.
- Los puntos están en **`CIM_Linear`**: tramos rectos, exactamente "de punto a punto". Cambiar un punto a *Curve* en el viewport lo vuelve curvo sin tocar código.

## API
| Función | Devuelve |
|---|---|
| `GetStopCount()` | cantidad de paradas del spline |
| `GetStopLocation(Index)` | posición **mundial** de la parada |
| `GetLocAtKey(Key)` | posición mundial en la clave de spline (float): la clave *i+0.5* es la mitad del tramo *i* |
| `GetLegTime(Index)` | `LegTimes[Index]` o `DefaultLegTime` |

🔴 **Todo usa `GetLocationAtSplineInputKey`, NUNCA distancia-a-lo-largo-del-spline.** Los puntos se escribieron por `set_properties` sobre `SplineCurves`, y eso **no recalcula el `reparamTable`** (queda con el rango viejo hasta que Beltrán mueva un punto en el editor). Las funciones por *input key* no lo usan; las de distancia darían basura.

## 🔴🔴 NO repetir la escritura de puntos por propiedad sobre la instancia — tira el editor
Al intentar pasar de 7 a 8 paradas escribiendo `SplineCurves` sobre **la instancia del nivel**, el editor **crasheó** con `Assertion failed: Rotation.Points.Num() == NumPoints` (SplineComponent.cpp:738). La escritura necesita dos pasos (vaciar → llenar) y en la ventana intermedia las tres curvas quedan descoordinadas; si el engine redibuja el spline ahí, revienta. Detalle completo en `gotchas.md`.
👉 **Para cambiar las paradas: arrastrarlas en el viewport** (para eso está), o migrar a que el Construction Script arme el spline desde un array `Stops` editable.

### 🆕 2026-08-13 (tarde) — y con la MISMA cantidad de puntos, sobre la instancia NO APLICA (en silencio)
Con la instancia ya arrastrada en el viewport, `set_properties(SplineCurves)` (mismo conteo, una sola llamada, struct completo) **devuelve `true` y no cambia nada**: el *component instance data* del spline restaura las curvas arrastradas tras cada PostEditChange. **La vía que SÍ funcionó** (usada para re-escribir las 8 paradas):
1. Escribir `SplineCurves` en el **template del CDO** (`BP_Journey.BP_Journey_C:Route_GEN_VARIABLE`) — mismo conteo → una sola llamada, sin ventana de crash. Compilar.
2. `remove_from_scene` de la instancia vieja + `add_to_scene_from_asset` → la nueva hereda del CDO (se pierden los overrides de instancia: re-setear `LegTimes` y verificar).
3. Verificar las paradas **en la instancia nueva** con `get_properties` del componente.

## Cómo se escribieron los puntos por MCP la primera vez (sobre el CDO, con el BP recién creado)
`ObjectTools.set_properties` sobre el componente con la propiedad **`SplineCurves`**, en **DOS pasos**: primero `points: []` en las 3 curvas (position/rotation/scale), después el array completo. Un solo paso falla con *"ArrayAdd: elements changed alongside the size change"* — es la misma trampa de arrays del CDO. Las 3 curvas deben tener **la misma cantidad de puntos**.

## Relacionados
- [[BP_Walker]] (`WalkLeg`/`UpdateLeg`, el consumidor) · [[BP_StageDirector]] (entrega 2: las salas se posicionan en las paradas)
