# BP_Journey — el recorrido completo de la obra (Core/Movement/)

## Purpose
**Un solo spline que cubre TODO el viaje**, dividido en paradas que Beltrán arrastra en el viewport. Reemplaza el modelo anterior, donde cada sala se recorría con un segmento recto de 10 m reconstruido en el origen y las 6 salas se apilaban en el mismo lugar.

Pedido de Beltrán (2026-08-13): *"un spline largo que toma todo el recorrido, dividido en puntos. Así yo puedo mover esos puntos como me parezca. Y el pawn avanza de punto 1 a punto 2, punto 2 a punto 3... y definimos el tiempo que toma recorrer entre uno y otro."*

## Status
🟢 **Recorrido y caminata verificados en PIE** (2026-08-13): 6 tramos seguidos, llegada exacta a cada parada, cámara de X=−500 a X=6000. ⬜ El director todavía NO lo usa (sigue con el modelo viejo) — esa es la entrega 2.

## Cómo se autora (sin tocar Blueprints)
- El actor `BP_Journey_C_0` vive en `L_Persistent` en el origen. Su componente **`Route` (SplineComponent) se edita en el viewport**: arrastrar puntos, agregar/quitar, cambiar tangentes.
- **Paradas actuales (7)**, todas a Z=0 — el walker coloca el pawn en la Z del spline, y el pawn a Z=0 es lo que da la altura de cámara medida (~185):
  | Índice | X | Qué es |
  |---|---|---|
  | 0 | −500 | arranque / menú (coincide con el PlayerStart) |
  | 1 | 0 | Hall |
  | 2 | 1200 | Entering |
  | 3 | 2400 | Recognizing |
  | 4 | 3600 | Loving |
  | 5 | 4800 | Attracting |
  | 6 | 6000 | Surrounding |
- **`LegTimes`** (array de float, instance-editable): segundos del tramo *i* (de la parada *i* a la *i+1*). Hoy `[6, 8, 8, 8, 8, 8]`. **`DefaultLegTime`** (8 s) se usa si el array es más corto que la cantidad de tramos → **agregar un punto nunca rompe nada**.
- Los puntos están en **`CIM_Linear`**: tramos rectos, exactamente "de punto a punto". Cambiar un punto a *Curve* en el viewport lo vuelve curvo sin tocar código.

## API
| Función | Devuelve |
|---|---|
| `GetStopCount()` | cantidad de paradas del spline |
| `GetStopLocation(Index)` | posición **mundial** de la parada |
| `GetLocAtKey(Key)` | posición mundial en la clave de spline (float): la clave *i+0.5* es la mitad del tramo *i* |
| `GetLegTime(Index)` | `LegTimes[Index]` o `DefaultLegTime` |

🔴 **Todo usa `GetLocationAtSplineInputKey`, NUNCA distancia-a-lo-largo-del-spline.** Los puntos se escribieron por `set_properties` sobre `SplineCurves`, y eso **no recalcula el `reparamTable`** (queda con el rango viejo hasta que Beltrán mueva un punto en el editor). Las funciones por *input key* no lo usan; las de distancia darían basura.

## Cómo se escribieron los puntos por MCP (para repetirlo)
`ObjectTools.set_properties` sobre el componente con la propiedad **`SplineCurves`**, en **DOS pasos**: primero `points: []` en las 3 curvas (position/rotation/scale), después el array completo. Un solo paso falla con *"ArrayAdd: elements changed alongside the size change"* — es la misma trampa de arrays del CDO. Las 3 curvas deben tener **la misma cantidad de puntos**.

## Relacionados
- [[BP_Walker]] (`WalkLeg`/`UpdateLeg`, el consumidor) · [[BP_StageDirector]] (entrega 2: las salas se posicionan en las paradas)
