# BP_SoulPicker_SC — la pantalla de "Start experience": elegir el alma entre 5

> `/Game/SoulCharger/Core/ProtoSoul/` · creado 2026-08-19 · **una instancia colocada** en `MapsV2/L_SoulCharger` en `(-5185, 0, 130)`.
> **Estado: 🟡 verificado en PIE de punta a punta salvo la elección, que necesita manos. Primer visor pasado (ver abajo).**
>
> 🔴 **CAMBIO DE ARQUITECTURA 2026-08-19 (decisión de Beltrán): las almas YA NO SE SPAWNEAN.** Están **colocadas a mano en el persistente**, nacen **dormidas**, y el picker las despierta cuando corresponde. Ver "Por qué colocadas y no spawneadas".

---

## Qué es
El actor que **gobierna la elección del alma**: al arrancar **encuentra** las 5 candidatas de [[BP_ProtoSoul_SC]] y las **duerme**; cuando la obra llega al Hall (y Alma termina su diálogo) las **despierta**; y cuando el usuario aprieta el gatillo sobre la que tiene hovereada, la elegida viaja al ancla de cara y **las otras cuatro se desvanecen y se destruyen**.

Pedido de Beltrán (2026-08-19): *"las amebas serán interactivas y deben aparecer cuando estamos en el Hall, pero efectivamente deben vivir en el persistente; simplemente la interacción sucede cuando estamos en esa etapa"*.

## 🗺️ La composición se autora en el viewport — las almas SON los actores
Las 5 candidatas son **5 `BP_ProtoSoul_SC` colocados a mano en `L_SoulCharger` (el persistente)**, cada uno con el **actor tag `soul_pick`**. Están en `x = -5185 / -5285,49`, `y = -90 / -45 / 0 / 45 / 90`, `z = 130`, con `Size = 0,3` y un `CoreColor` distinto cada una.
👉 **Para cambiar la malla, el color, el tamaño o la posición de una opción se abre ESA ameba en el viewport y se edita ahí. No se toca ningún Blueprint ni ningún array.**
⚠ El tag es lo único que las hace candidatas: **quitarle `soul_pick` a una la saca de la elección; agregar una 6ª es duplicar un actor y ponerle el tag.** El orden no importa — ya no hay índices que apareen.
El ancla de cara sigue siendo el `TargetPoint` **`soul_face`**, hijo de `BP_FaceAnchor_SC`, y **tiene que quedar en el persistente**: la elegida acompaña el resto de la obra y su ancla no puede descargarse con una sala.
⚠ Los 5 `TargetPoint` viejos (`soul_pick_0..4`) **quedaron en el nivel y ya no los usa nadie** — se dejaron ahí a propósito (la regla del proyecto es que sacar actores se pregunta). Borrarlos es decisión de Beltrán.

## 🧭 Por qué colocadas y no spawneadas
La pregunta la abrió Beltrán el 2026-08-19: *"como quiero elegir mesh y color específico para cada una de las 5, ¿conviene spawnearlas desde 0, o que ya existan e inactivas?"*.

**El argumento que decide no es técnico, es de autoría.** Con spawn, la malla y el color de cada opción viven en arrays paralelos dentro del picker: se editan a ciegas y no se ven hasta darle Play. Colocadas, se abre cada ameba en el viewport y **se la ve ahí mismo** — el material de `M_ProtoSoul` anima en el editor sin Play, que es justamente la propiedad por la que toda la vida visual se metió en el shader. Es el mismo criterio por el que [[BP_Bell]] se coloca a mano en vez de spawnearse por TargetPoint.

**Lo que se fue con el spawn:** los arrays `Meshes` / `CoreColors` / `PickTags`, las funciones `SpawnAll` / `SpawnOne`, los 5 TargetPoints de pick, y la necesidad de `Configure` en el alma (que sigue existiendo, pero ya no la usa nadie acá). El picker quedó con **una sola responsabilidad**: escuchar el gatillo y resolver.
**El precio, conocido:** la malla y el color pasan a ser **datos de autor en el nivel** — reponer un actor los borra (`gotchas.md` §114-115).

## Registro de variables
| Cat | Variable | Rol |
|---|---|---|
| **A - Opciones** | `PickTag` (Name) | `"soul_pick"` — el actor tag que marca a una ameba como candidata. **Es lo único que define el reparto.** |
| | `FaceTag` (Name) | `"soul_face"` — a dónde viaja la elegida. |
| | `IMCRef` (InputMappingContext) | `IMC_MenuTrigger`. El contexto que hay que registrar para que llegue el gatillo. |
| | `bAwakeOnStart` (bool) | **Andamio, hoy en `true`.** Despierta solo tras `AwakeDelay`. Cuando el Hall llame a `Awake()`, se apaga. |
| | `AwakeDelay` (float) | 3 s. El tiempo que tardan en despertar con `bAwakeOnStart` — hace las veces del diálogo de Alma mientras no exista. |
| **Z - Estado interno** | `Souls` (BP_ProtoSoul_SC[]) | Las candidatas encontradas por tag. |
| | `Winner` | La elegida; sólo la usa `HideOne` para saber a quién NO esconder. |
| | `bChosen` | Cierra la elección: una sola vez. |
| | `bInputReady` | El bool que gatea el reintento de input desde el Tick. |

## Estructura de grafos
- **`BeginPlay`** → `FindSouls` → si `bAwakeOnStart`, timer de `AwakeDelay` → `Awake`.
- **`Tick`** → `MaybeInput` (reintenta hasta que el contexto quede puesto).
- **`IA_Shoot_Right` / `IA_Shoot_Left`, pin `Started`** → `Choose`.

| Función | Qué hace |
|---|---|
| **`FindSouls()`** | `GetAllActorsOfClassWithTag(BP_ProtoSoul_SC, PickTag)` → `Souls`, loguea cuántas encontró, y recorre durmiéndolas (`Sleep()`). **Dos nodos y un bucle** — lo que antes eran dos funciones y tres arrays. |
| **🔴 `Awake()`** | **El punto de entrada público de la etapa.** Recorre `Souls` → `Reveal()`: entran con su animación y recién ahí son hovereables. **Esto es lo que tiene que llamar el Hall cuando Alma termina su diálogo.** |
| **`EnsureInput()` / `MaybeInput()`** | La receta de input, copiada **literal** de `BP_MenuButton` (ver abajo). |
| **`Choose()`** | 🔴 **Guardada por `if (not bChosen)`** y recién ahí `for` sobre `Souls` → `Judge(s)`. Es el único punto de entrada de los dos eventos de gatillo. |
| **`Judge(S)`** | Si **no hay elección hecha Y `S.bHovering`**: cierra `bChosen`, guarda `Winner`, llama `S.Select(FaceTag)` y recorre `Souls` → `HideOne`. |
| **`HideOne(S)`** | Si `S != Winner`: **apaga su hover** → `S.Disappear()` → **`SetLifeSpan(S, S.DisappearTime + 0,25)`**. Las cuatro perdedoras se desvanecen y **se destruyen**; sólo la elegida sobrevive. |

🔴 **Por qué la guarda de `Choose` es obligatoria y no cosmética.** Las perdedoras se destruyen, así que `Souls` queda con referencias muertas. `Judge` tiene su propio `and (not bChosen) (S.bHovering)`, **pero el `AND` de Blueprint es una llamada a función y NO hace corto-circuito**: evalúa las dos ramas siempre, o sea que leería `bHovering` sobre actores destruidos en cada gatillazo posterior → `Accessed None` en loop. La guarda en `Choose` corta el recorrido entero antes de tocar el array. **La regla: en Blueprint, un `AND` no protege a su segundo operando.**

⚠ **El hover de las perdedoras se apaga ANTES del `Disappear`**, no por prolijidad: sin eso la mano que pasa por donde estaba una ameba invisible **dispara su sonido de hover y su háptica**. Se oiría un objeto que ya no está.

🔴 **Apretar el gatillo sin nada hovereado no hace NADA** — no es un callejón sin salida, es un no-op. Fue una decisión: la alternativa (elegir "la más cercana") desaparecería las 5 ante un gatillazo accidental.

💡 **Por qué tantas funciones chicas:** el parser del DSL sólo admite **un nodo multi-exec y al final de la lista** (`dsl.md`, trampa 1). Cada `if` y cada `for` fuerza un corte. `Judge` / `HideOne` no son diseño, son la forma que impone la herramienta.

## 🎮🔴 El input: la receta probada, no los defaults
Copiada de `BP_MenuButton.EnsureInput`, que **anda en visor**:
```
EnableInput(self, PlayerController)
AddMappingContext(subsystem, IMC_MenuTrigger, Priority = 1000,
                  bIgnoreAllPressedKeysUntilRelease = False,   <- el default True SUPRIME el input
                  bForceImmediately = True)                    <- el default es False
bInputReady = HasMappingContext(...)
```
🔴 **Va en el TICK (`MaybeInput`), no en BeginPlay**: ahí el PlayerController puede no existir todavía y `AddMappingContext` **falla en silencio**.

🔴🔴 **Aclaración sobre "reusar `IA_Continue` + `IMC_Continue`":** lo que se reusa de esa receta es **la configuración del `AddMappingContext`** (los tres flags), que es la parte que importa. **La acción que se escucha es `IA_Shoot_Right` / `IA_Shoot_Left` del XRFramework**, porque **ningún Blueprint del proyecto tiene el evento `IA_Continue` y ninguno dispara por ahí** — verificado el 2026-08-19 barriendo los `.uasset`: `BP_Instructions` (Breath), `BP_MenuButton`, `BP_CalibProbe`, `BP_AimBeam`, `BP_BrushTool` y `BP_SoulChoice` **todos** escuchan `IA_Shoot_*`; `IA_Continue` sólo aparece como asset, sin evento. El `IMC` es el que trae el gatillo; la `IA` es la que se escucha. Son dos cosas distintas y conviene no mezclarlas.
- Eventos creados con **`create_node`** (`Input|EnhancedActionEvents|IA_Shoot_{Right,Left}`) — **el DSL no puede crearlos**. Cableados desde **`Started` (pin 1)**, no `Triggered` (que dispara cada frame).
- ⚠ El `read_graph_dsl` del EventGraph los muestra **vacíos**: es el gotcha conocido, no es código muerto. Se confirman con `get_node_infos`.

## ✅ Lo verificado en PIE (2026-08-19, después del cambio a colocadas)
Medido en el **estado estable**, no en el frame del arranque (regla de [[BP_SoulChoice]]):

| Aserción | Resultado |
|---|---|
| Encuentra las candidatas por tag | ✅ `PICKER: almas encontradas = 5` |
| Nacen dormidas y **se quedan** dormidas | ✅ el `Reveal` llegó **2,87 s después** del arranque — si el sueño no aguantara, habrían aparecido en el frame 1 |
| Despiertan por `Awake()` | ✅ `PICKER: las almas despiertan` |
| Estado después de despertar | ✅ `Size = 0,30` · escala real del `Body` = 0,30 · `bHoverEnabled = true` · `bLeaving = false` · `AppearT = 1` |
| Cada una con SU color | ✅ la del medio en violeta, y las 5 distintas |
| El input queda registrado | ✅ `PICKER: input listo` |
| `Accessed None` | ✅ ninguno |

### 🚨 La trampa que mordió en el camino: `almas encontradas = 0`
La primera corrida después del cambio encontró **cero almas** con los 5 actores tagueados correctamente. **No era el tag ni la búsqueda:** la instancia del picker ya estaba colocada en el nivel **desde antes de que existieran `PickTag`, `bAwakeOnStart` y `AwakeDelay`**, así que en la instancia nacieron en `None` / `false` / `0` mientras el CDO tenía los valores correctos. Es [[instance-editable-nace-en-cero]] (`gotchas.md` §146) por enésima vez.
👉 **Regla operativa: agregar una variable a un BP YA COLOCADO obliga a escribirla también en cada instancia** — con la **lista explícita de nombres nuevos**, nunca un diff genérico contra el CDO (eso pisaría los datos de autor).
💡 Y lo que la cazó en una corrida fue el `PrintString` con **el conteo**: "encontradas = 0" es un síntoma que señala solo. Un log que dice "arranqué" no habría dicho nada.

## 🔬 El control positivo que resolvió la duda del MID
El riesgo real del sembrado era: **cambiar la malla después del Construction Script se lleva puesto el `MID`** (lo advierte el tracker de [[BP_ProtoSoul_SC]]) y con él los ~20 parámetros del material. En vez de teorizar se **midió**: `Configure` loguea el material del slot 0 después de cambiar la malla.
```
PROTO: material slot 0 tras Configure = MID_M_ProtoSoul_0   x5
```
👉 **El MID SOBREVIVE.** `SetStaticMesh` sólo **recorta** los override materials cuando la malla nueva tiene MENOS slots; con una malla de un solo material el slot 0 queda intacto (y en el CDO `M_ProtoSoul` ya está como override del `Body`). Por eso alcanza con re-empujar `CoreColor` y no hace falta rehacer el Construction Script — que además es intocable por el §142 de `gotchas.md`.
⚠ **El límite conocido:** una malla con **0 slots de material** sí borraría el override. Si Beltrán mete una malla rara y el alma sale gris, ese log lo dice de una.

## 🥽 Primer visor (2026-08-19) — reporte de Beltrán
> *"Funciona. Se spawnearon. Todas lograban el hover. Hice trigger y se vino a mi cara la seleccionada. Las otras se desvanecieron, **pero volvieron a aparecer nuevamente en sus target point**."*

✅ Sembrado, hover en las 5, gatillo, y el viaje a la cara: **todo anduvo a la primera**.
🐛 El único fallo era el "vuelven a aparecer" → resultó ser un bug **de `BP_ProtoSoul_SC`, no del picker**: `Disappear()` nunca había sido un estado terminal (ver su tracker, "dos dueños de la escala del `Body`"). Arreglado.
🆕 Y una decisión de Beltrán a partir de ahí: *"las que se van deberían desaparecer y luego destroy. Ya no deben existir en el mundo, sólo la seleccionada prevalece"* → `SetLifeSpan` en `HideOne`.

## Falta
- [ ] 🔴 **Segundo visor**: que despierten con su animación, que la elegida viaje a la cara, y que las 4 perdedoras se vayan **y no vuelvan** (y a los ~0,85 s ya no existan).
- [ ] 🔴 **Engancharlo al Hall**: hoy despierta solo por `bAwakeOnStart` + `AwakeDelay` (3 s), que es un **andamio**. Cuando exista el diálogo de Alma, ese callback llama a **`Awake()`** y `bAwakeOnStart` se apaga.
- [ ] Las 5 mallas reales (hoy las 5 heredan `SM_ChamferCube` del CDO y sólo se distinguen por color) — se ponen **por instancia, en el viewport**.
- [ ] `SelectSound` sigue en `None` en el CDO de `BP_ProtoSoul_SC` → la elección es **muda**.
- [ ] Persistir la elección para el resto de la obra.
- [ ] Decidir si se borran los 5 `TargetPoint` `soul_pick_0..4`, que quedaron sin uso.

## Relacionados
- [[BP_ProtoSoul_SC]] — las candidatas, y de dónde salen `Configure` / `Select` · [[BP_SoulChoice]] — la versión VIEJA de esta misma pantalla (esqueleto), de donde salen las lecciones · [[BP_MenuButton]] — la receta de input · [[BP_Alma_SC]] — el sistema de puntos por tag

## 🎬 2026-08-19 — enganchado al guión: `ChosenTag`, `OnChosen`, `Rearm`, `ForceChoose`
- **`FaceTag` se eliminó → `ChosenTag`** (`soul_pick_0`): la elegida ya **no viaja a la cara** al elegirla sino a **`TP soul_pick_0`** (pedido de Beltrán: *"se mueve hacia TP_Pick_0, simultáneamente VO 8; cuando termina VO 8, se mueve hacia el target point de nuestro hud"*). El viaje a la cara lo ordena el director después.
- **`OnChosen`** (dispatcher): se dispara al final de `Judge`, después de esconder a las perdedoras. El director lee `Winner` ahí.
- **`Rearm(NewTag)`**: para el final de la obra (VO 32): `Souls = [Winner]`, `bChosen=false`, `ChosenTag=NewTag`, `Winner.EnableHover(true)` → el mismo gatillo vuelve a funcionar y `Select` la manda a `soul_pick_6`. Con guarda `IsValid(Winner)`.
- **`ForceChoose()`** (test): marca `bHovering=true` en `Souls[0]` y llama `Judge` → elige sin manos. Lo usa `bAutoTest` del director.
- La instancia quedó con **`bAwakeOnStart=false`**: ahora despierta por `Awake()` desde el director (al arrancar el VO 7). El andamio de `AwakeDelay` queda por si se prueba el picker solo.

## 🤲 2026-08-20 — el modo COMPARTIR reemplaza a la re-elección
`Rearm(NewTag)` ya **no** rehabilita `Judge`: prende **`bShareMode`** y el hover de la ganadora. Con `bShareMode`:
- **Gatillo `Started`** → `Choose` → `ShareGrab`: si la ganadora está hovereada, `StartCarry(bTouchRight)` — queda agarrada a ESA mano **mientras el gatillo esté apretado**.
- **Gatillo `Completed`** (los pines de soltar de `IA_Shoot_Right/Left`, cableados por cirugía) → `ReleaseGrab` → `EndCarry`: vuelve sola a su punto.
- **Compartir** = acercarla bajo el visor (lo detecta la propia ameba, ver su tracker) → `OnShared` → el guión la manda a `soul_pick_6`.
- `ForceShare()` (test) dispara `Shared()` directo. ⚠ `ChosenTag` quedó sin uso en este modo (el destino lo comanda el guión).


## 🆕 2026-08-27 — el gesto sin gatillo (F3 del plan de cierre)
Decisión 9 del plan: *"Atracción por gesto: **cualquier mano**, cono de ~10°, ~1 s de permanencia.
Sin gatillo."*

🔴 **NO se construyó de cero: se le cambió el DISPARADOR a un mecanismo que ya existía y andaba.**
El modo compartir ya estaba entero (`Rearm` → `bShareMode` → `ShareGrabBody` con hover + gatillo sostenido
→ `Winner.StartCarry`), cableado al `RunEnding` sub 7 del director. Lo único que cambia es **cómo se
engancha**.

⚠ **El plan decía "modo nuevo en `BP_Sensor_Soul`"** — se hizo **acá** en su lugar, y la razón es
concreta: `bShareMode`, `Winner` y el Tick ya viven en el picker, y el sensor no conoce a la ganadora.
Meterlo en el sensor habría sido reconstruir un camino probado. **Si Beltrán prefiere el sensor, se
mueve; pero conviene saber que esto ya funciona.**

### La cadena
```
Tick → AimStep(DT)
   si bShareMode y todavía no enganchó:
     AimScan(DT)   → AimTry(mano derecha) y AimTry(mano izquierda)   [o la cámara, ver debug]
     AimAccum      → AimT += DT si alguna acierta, 0 si no
                   → si AimT >= AimDwell → AimHook(cuál mano)
AimHook → Winner.StartCarry(mano) + HidePortrait()  (apaga panel Y melodía)
```
- **`AimTry(Comp)`** es el mismo criterio por **ÁNGULO** que ya usaba [[BP_ConstExplorer]]: producto punto
  entre la dirección al alma y el forward del componente, contra `cos(AimConeDeg)`.
  **Sin colisión, sin line trace, sin tocar la ameba.**
- El **gatillo sigue cableado** (`ShareGrabBody`) y no molesta: hace exactamente lo mismo. Se dejó como
  camino alternativo probado en vez de borrarlo.

| Variable | Default | Rol |
|---|---|---|
| `AimConeDeg` | 10° | Cuán fino hay que apuntar. **La palanca de comodidad.** |
| `AimDwell` | 1.0 s | Cuánto hay que sostener la mirada/el gesto. |
| `AimT` / `bAimHooked` / `AimRight` | — | Estado; `bAimHooked` hace que el enganche sea de una sola vez. |
| `PawnAim` | — | El pawn, cacheado por `CacheAim` (lo rearma `RearmBody`). |
| 🧪 `bAimFromCamera` | false | **Apunta con la CÁMARA en vez de las manos** — es lo que permite verificar el gesto en PIE sin visor. |
| 🧪 `bDebugShareOnPlay` + `DebugShareDelay` | false | Abre el modo compartir solo, sin recorrer la obra. |

### ✅ Verificado en PIE (2026-08-27), con los tiempos exactos
```
14:52:49.8  PICKER: DEBUG - abro modo compartir sin recorrer la obra
14:52:49.8  PICKER: modo compartir - apuntar la ameba con cualquier mano, sin gatillo
14:52:50.8  PICKER: enganchada por gesto con la DERECHA - viaja a la mano   ← +1,0 s = AimDwell
14:52:50.8  RETRATO: se apaga
14:52:53.9  PROTO: compartida - operacion lograda                          ← +3,05 s = ShareHold
```
Cero `Accessed None`. **Los dos tiempos caen clavados en sus knobs** — no es "parece que anda".

## Relacionados
[[BP_ProtoSoul_SC]] (`StartCarry` / `CarryBody` / `ShareZone`) · [[BP_Portrait_SC]] (lo que se apaga al
enganchar) · [[BP_Director_Story]] (`RunEnding` sub 7 abre el modo, sub 8 guarda) ·
[[BP_ConstExplorer]] (de dónde sale el criterio por ángulo)
