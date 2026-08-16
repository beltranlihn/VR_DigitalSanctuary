# 🤖 Lo que encontró el robot — noche del 2026-08-15

> Campaña de pasadas automáticas mientras Beltrán dormía. Todo lo de acá está **medido en el log**, no deducido. Los números son literales.
> Estado del proyecto al cerrar: **`RobotOn = 0`**, **`DebugStartStage = -1`**, todo guardado y commiteado. Listo para ponerse las gafas.

---

## ❌ RETRACTADO — "el jugador nunca se mueve" era MI robot, no la obra

> 🔴 **Este hallazgo era falso.** Lo dejo escrito con su corrección porque el error de método vale más que la conclusión.
>
> **El recorrido por spline funciona perfecto.** Medido con el robot sin interferir:
> ```
> pawn=X=1200 | camara=X=1200
> pawn=X=2400 | camara=X=2400
> pawn=X=3000 | camara=X=2925   ← en pleno tramo, la cámara sigue al pawn
> pawn=X=3600 | camara=X=3600
> ```
> **La causa era mi propio robot**: `SetHead` reescribía la *posición completa* del `VROrigin` sesenta veces por segundo para simular la cabeza a 115 cm — y el `VROrigin` es justamente lo que el recorrido desplaza. Yo pisaba el movimiento y después medía el resultado de mi interferencia.
>
> **Arreglado**: `SetHead` ahora conserva X e Y y **sólo corrige la altura** (`_cur + up * (HeadHeight − _cur.z)`), más un interruptor `HeadOn` para poder aislarlo.
>
> 🔑 **La lección, que es la importante:** un instrumento que *modifica* el mundo puede fabricar el bug que después reporta. Beltrán tenía la evidencia en contra desde el principio — *"en gafas íbamos pasando de sala en sala sin problema"* — y **el dato del visor le gana a mi medición en PIE**. Cuando las dos cosas chocan, sospechar primero del instrumento.
> ⚠ Consecuencia: **todo lo que concluí sobre Attracting a partir de las distancias hay que volver a medirlo** con el robot arreglado. Que las burbujas estuvieran a 48 m era, casi seguro, el mismo artefacto.

## ~~EL GRANDE: el jugador nunca se mueve del origen~~ (ver retractación arriba)

```
sala Entering     X=1200
sala Recognizing  X=2400
sala Loving       X=3600
sala Attracting   X=4800
cámara del jugador   X=0     ← constante durante toda la obra
```

Medido dentro de Attracting, en la pasada completa (no en un atajo):
```
PULSE|Sitio| camara=X=0  | burbuja=X=4829.5 | slot=X=4855 | director=X=4800
```

**Cada sala se coloca en su parada del spline y el pawn se queda en el origen.** El director loguea `camina el tramo 4` mientras la cámara no se mueve un centímetro.

### Por qué esto explica exactamente lo que funciona y lo que no
| Anda | No anda |
|---|---|
| Todo lo **relativo al cuerpo**: respiración, latido, dibujar alrededor de la ameba, los botones y el timbre (nacen frente al usuario) | Todo lo que vive **en la sala**: las burbujas y slots de Attracting (a 48 m), las columnas de Recognizing, los campos de Loving |

Y explica la contradicción con las pruebas anteriores: **la mecánica de Attracting funciona en su propio nivel** (`L_Test_Touch`, donde todo está donde fue autorado) y **se rompe en el recorrido armado**.

### La decisión es de Beltrán, porque son dos diseños distintos
1. **El pawn debía caminar por el spline** y esa caminata no está moviendo la cámara → hay que arreglar el movimiento del pawn.
2. **Las salas debían venir hacia el jugador** → hay que colocarlas en el origen en vez de en la parada absoluta.

⚠ El síntoma en visor sería: ver la sala siguiente a lo lejos y no poder tocar nada de ella.

---

## 🟢 Tres bugs encontrados Y arreglados

### 1. El pincel de Surrounding pedía que lo agarraran
Nacía con `bAttached=false` y su Tick llamaba `TryAttach` hasta que una mano lo tocara; el log decía *"pincel flotando - tomalo con cualquier mano"*. **Contradice la regla de la obra**: el sensor que se toma en el Hall es la herramienta de toda la experiencia.
**Arreglo**: `SpawnBrushAt` lee la mano hábil de `BP_SoulState` y engancha el pincel ahí, llamando al `DoAttach` propio del pincel (así se conserva la paleta de colores que se crea en ese paso). Reusa el patrón que ya existía en `BP_HeartSensor.ForceAttachToHand`.
✅ **Verificado**: 12 metros dibujados y `SURROUNDING: metros alcanzados - la etapa cierra por el camino real`.

### 2. El puntero de Attracting nacía APAGADO
`BP_Stage_Attracting.EquipOneBeam` llamaba `Equip(beam)` **sin pasar el argumento `NewEquipped`** → el pin quedaba en su default `false`. La función que enciende el puntero lo apagaba, y la etapa igual logueaba *"beams activados"*.
Cadena de consecuencias: sin cursor ni traza → sin hover → no se agarra ninguna burbuja → ningún slot se ocupa → **FINISH MELODY nunca se habilita** → la etapa sólo puede cerrar por cortafuego.
✅ **Verificado**: pasó de `equipado=false | inputListo=false | golpea=None` a `equipado=true | inputListo=true` y el rayo ya traza.
💡 **La lección**: una llamada sin un argumento **no es un error de compilación**, y `read_graph_dsl` la muestra corta, o sea que parece correcta. Se caza midiendo el estado del actor, no leyendo el grafo.

### 3. `BP_AttractDirector.OnBeat` pulsaba slots destruidos
El orden estaba invertido: leía el ítem del array, sacaba su ocupante y llamaba a `Pulse`, y **recién después** preguntaba `IsValidIndex`. Con un slot destruido reventaba en cada latido a 90 BPM:
```
Accessed None ... CallFunc_Array_Get_Item | Node: Pulse | Graph: OnBeat
```
✅ **Arreglado** con una guarda `IsValid` insertada por cirugía (el grafo no se puede reescribir: usa `bExperienceStarted`, un bool `b` que el DSL no lee desde su propia clase).
⬜ **Falta la causa de fondo**: el reloj Quartz **sigue latiendo después de que la etapa barre los slots**. La guarda evita el crash; lo correcto es parar el reloj en `CleanupAttract`.

---

## 📋 Estado de cierre por etapa (última pasada completa)
| Etapa | Cierre |
|---|---|
| Hall | 🟢 por gatillo — `SOULCHOICE: elegida la variante 0`, 1 s después de armarse |
| Entering | 🟢 por su mecánica — 5 ciclos del pacer, 12 s exactos por vuelta |
| Recognizing | 🟢 por el camino real — 15 latidos |
| Loving | 🟢 por el camino real |
| Surrounding | 🟢 por metros dibujados **(nuevo)** |
| **Attracting** | 🔴 por tiempo — bloqueado por el problema de las salas lejanas |
| **Final** | 🔴 `cortafuegos - nadie la tomo` — el robot no llega a tomar la ameba |

✅ **Cero cortafuegos de instrucciones** en toda la pasada.

---

## Deuda que queda anotada
- [ ] 🔴 Decidir y arreglar lo de las salas lejanas (arriba). **Bloquea Attracting y probablemente afecta la percepción de todas las salas en visor.**
- [ ] 🔴 Parar el reloj Quartz en `CleanupAttract`.
- [ ] El final por gesto: `RunFinale` apunta la mano a la ameba y dispara, pero sigue cerrando por cortafuego — falta diagnosticar con el mismo método (medir el estado de `BP_Finale`, no leer su grafo).
- [ ] `SpawnBrushAt` tiene **tres cadenas huérfanas** de escrituras viejas; pasar `clean_orphans.py` por `BP_Stage_Surrounding`.
- [ ] El editor renderiza a ~3 fps en PIE — **descartado** que sea el throttle de fondo, `t.MaxFPS` o mis consultas (10 min de silencio total dieron el mismo ritmo). Sin explicación todavía; **no invalida los tests** porque la simulación corre en tiempo real.
