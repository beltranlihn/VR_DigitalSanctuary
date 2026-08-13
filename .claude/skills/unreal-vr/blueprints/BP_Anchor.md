# BP_Anchor — el punto de spawn que SÍ se ve en el editor (Core/Debug/)

## Purpose
Pedido de Beltrán (2026-08-13): *"para poder tener una visión de cómo irá quedando todo esto, debemos cargar en el mundo los objetos, que luego en el play no existan... a modo de debug, ya que desaparecen al poner play o están hidden in game. Así puedo tener control del diseño de arquitectura."*

Un `TargetPoint` que además **se ve**: esfera fantasma + el nombre de su tag flotando encima, ambos con **`Hidden in Game`**. En el editor ves dónde va a nacer cada cosa y lo mueves con el gizmo; en juego no existe visualmente pero **sigue siendo el punto de spawn real**.

## 🔴 La decisión que hizo esto barato: hereda de `TargetPoint`
`BP_Anchor` tiene como **padre `/Script/Engine.TargetPoint`**, así que **todas las búsquedas que ya existían siguen funcionando sin tocar una línea**: `GetAllActorsOfClassWithTag(TargetPoint, "SoulSpawn")` encuentra los anchors porque el filtro de clase es por `IsA`. Cero cambios en `BP_SoulChoice`, `BP_Stage_Hall`, `BP_IntroSequence`, `BP_StageDirector` ni `BP_Stage_Entering`.
👉 **Regla general:** cuando quieras enriquecer un actor "marcador" que ya está cableado por clase, **heredá de esa clase** en vez de cambiar los buscadores.

## Componentes
| Componente | Qué es |
|---|---|
| `Preview` | Esfera de 9 cm con **`MI_Ghost`** (Core/Debug/, instancia de `M_ProtoSoul`: verde agua, Brightness 0.8, Agitation 0). `bHiddenInGame=true`, **sin colisión** (o taparía los line traces de los punteros). |
| `TagLabel` | `TextRenderComponent` con `M_TextUnlit`, WorldSize 8, yaw 180, 14 cm arriba. `bHiddenInGame=true`. |

**`UserConstructionScript`**: si el actor tiene tags, escribe **`Tags[0]` en el TextRender**. O sea, el anchor **se rotula solo** con su propio tag en el viewport — no hay que mantener nombres a mano (y de hecho **no se puede**: no existe tool MCP para el label del outliner, `ActorLabel` no es seteable por `set_properties`).

## Los 14 anchors de `L_Persistent` (2026-08-13)
Reemplazaron uno a uno a los TargetPoints, con la misma posición, rotación y tag:
`MenuRoot` · `MenuSpawnStart` · `MenuSpawnAbout` · `MenuSpawnBack` · `BellSpawn` · `SensorSpawn` · **`SoulSpawn` ×5** · `AlmaSpawn` · `WidgetSpawn` · `BoxSpawn`.

## ⚠ Trampa pagada: los componentes nuevos NO llegan a las instancias ya colocadas
Los 14 anchors se crearon **antes** de que el BP tuviera el `TagLabel`. Al agregarlo, las instancias recibieron el componente **con los defaults de Unreal** (`bHiddenInGame=false`, `WorldSize=26`), **no** con los valores del CDO — o sea, los rótulos se habrían visto EN JUEGO. Es la familia de [[instance-editable-nace-en-cero]] aplicada a componentes.
👉 **Después de agregar un componente a un BP que ya tiene instancias colocadas, setear sus propiedades EN CADA INSTANCIA y verificarlas.** Se hizo con un script de `ProgrammaticToolset` (14 instancias × 2 componentes) y se verificó el valor efectivo de las 14.
⚠ Además: `WorldSize` sólo aceptó **`8.0`** (float); con `8` (entero) la llamada devolvía éxito y el valor seguía en 26. **Escribir los floats con decimal.**

## Verificado en PIE (2026-08-13)
Corrida completa con los anchors: menú spawneado en sus puntos, Alma presente, sensor en su lugar, salas moviéndose a sus paradas (X=0 y X=1200), y **las 5 candidatas nacidas en los 5 anchors y todavía ahí 3 s después** (`AUDIT`). Cero errores, cero avisos de `FALTA`.

## TODO
- Mallas de previsualización por tipo (plano para el widget, caja para la puerta) en vez de la esfera para todos: se cambia el `StaticMesh` del `Preview` **por instancia**, sin tocar el BP.
- Ver las 6 salas a la vez en el editor: eso no es cosa del anchor, va por los sublevels (`RoomMaps`) con su transform y el ojo del panel Levels.

## Relacionados
- [[BP_Journey]] (las paradas del recorrido) · [[BP_StageDirector]] · [[BP_SoulChoice]] · [[BP_Stage_Hall]]
