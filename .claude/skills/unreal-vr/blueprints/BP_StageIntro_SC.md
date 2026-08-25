# BP_StageIntro_SC + WBP_StageIntro_SC — la explicación de las etapas del Hall, versión LIMPIA (Core/UI/)

> `/Game/SoulCharger/Core/UI/` · creado 2026-08-25 · **una instancia** en `MapsV2/RoomsV2/L_Hall_SC` (`StageIntro (explicacion de etapas)`, en **230/0/140 yaw 180**, carpeta `3 Escena`).
> **Estado: 🟢 secuencia completa + entrada por VO 3 + salida verificadas en PIE** (título, 5 píldoras, 5 anillos, centrado exacto, salida **por opacidad** y aviso al director; cero `Accessed None`); ⬜ falta el visor (composición, tamaños, nitidez, si se lee espejada).

## Qué es
La animación del Hall donde el VO nombra las 5 etapas: **a la izquierda las píldoras con los nombres, a la derecha la proto ameba cargando un anillo por etapa**. Referencia: el PDF `UI Calibration copy` de Beltrán (5 láminas, una por etapa acumulada).
Sucede a [[BP_StageIntro]] (esqueleto viejo, usaba `BP_ProtoSoul`). Aquí la ameba es un **[[BP_ProtoSoul_SC]] REAL** spawneado en el mundo — el widget **no dibuja** ameba ni anillos (decisión de arquitectura que Beltrán ya había fijado: *"que sean reales, tal como las usamos en el world"*).

## La animación (lo que pidió Beltrán)
0. 🆕 **Lámina de título**: aparece **"Soul Charger"** (píldora gris, `PillTitle`) y **la ameba nace animada** junto con él (por eso el spawn ya NO la revela: `Reveal()` se llama en el paso 0). El título **no se desliza hacia arriba como las demás: desaparece, y Entering ocupa su lugar** (ambos viven en Y=0).
1. Cada píldora **nace con ancho 0 en su centro y se abre hacia los lados** — la misma gramática del marco del gráfico EEG del [[BP_SoulHUD_SC]].
2. **El grupo se mantiene siempre centrado**: al aparecer una nueva, las anteriores **se deslizan hacia arriba animadas**.
3. 🆕 **Nunca se superponen**: en cada cambio **primero pasa el slide y recién después aparece la nueva**.
4. Al aparecer cada píldora, la ameba **dibuja su anillo** (`DrawRing(i)`).
5. 🆕 **Salida**: tras el último anillo espera `ExitHold` y **desaparece todo de una** — las píldoras **se van por OPACIDAD, no achícandose** (la geometría queda clavada donde estaba y baja el alfa a 0; pedido explícito de Beltrán: *"con opacidad a 0, no con achicarse, que se ve medio raro como salida"*), y la ameba hace **`Disappear()` a secas** — 🆕 **los anillos se van con ella, achícándose**. Antes se llamaba también `HideRings()` y eso los **cortaba en duro** (Beltrán: *"se cortan de 0… no cortar en duro"*); ahora `RingRoot` escala por `AppearT` dentro de [[BP_ProtoSoul_SC]] y el corte desapareció.
6. 🆕 **Se libera**: `DestroyDelay` después de avisar, el actor **destruye la ameba que spawneó y se destruye a sí mismo**.

🔑 **Cómo se logra el centrado sin pelear con un VerticalBox**: los 5 `Border` viven en un `CanvasPanel` **anclados al centro (0.5, 0.5) con alignment (0.5, 0.5)** y su posición/tamaño los escribe el código. El alto total `HTotal = Occ × (PillH + PillGap) − PillGap` crece suave y todas las posiciones se recalculan alrededor del centro. Verificado en PIE: con las 5 abiertas `PosY = [−240, −120, 0, 120, 240]` (espaciado exacto 120 = 96 + 24) y `HTotal = 576`.

🔴 **DOS FASES separadas — es lo que evita que se superpongan** (pedido de Beltrán): hay **dos arrays distintos**, y ahí está todo el truco.
| Array | Qué maneja | Velocidad |
|---|---|---|
| **`Occupy[i]`** | el **hueco vertical** (la ocupación en el layout) → es lo que empuja a las de arriba | `SlideTime` |
| **`Reveal[i]`** | el **ancho** de la píldora | `GrowTime` |
El `Reveal` de la píldora *i* **sólo arranca cuando `Occupy[i] ≥ 0.999` Y el título ya cerró (`TitleR ≤ 0.01`)**. Así: primero se abre el hueco y las anteriores se corren, y recién cuando terminó empieza a dibujarse la nueva. La secuencia se **auto-ordena dentro del widget**, sin timers en el actor.

## WBP_StageIntro_SC — el widget (SÓLO las píldoras)
`Root` (CanvasPanel) → `PillTitle` + `Pill0..4` (Border, brush **RoundedBox `FixedRadius` 48**, padding 46/20) → `TxtTitle` + `Txt0..4` (TextBlock).
`PillTitle` es la lámina 0 (**"Soul Charger"**, gris `0.62/0.62/0.66`), clavada en **Y = 0** y fuera de la pila.
🎨 **Todo lo estético se edita en el Designer, el código no lo pisa**: el **color de cada píldora** vive en su `background.tintColor` (la paleta de la lámina: azul `0.29/0.42/0.94` · rojo `0.93/0.35/0.33` · morado `0.77/0.36/0.93` · ámbar `0.94/0.76/0.36` · verde `0.30/0.69/0.31`), y la **tipografía** en cada `Txt` (Roboto 40, letterSpacing 120, blanco). El código sólo escribe **posición, ancho y opacidad del texto**.

| Variable (widget) | Default | Rol |
|---|---|---|
| `PillW` / `PillH` / `PillGap` | 480 / 96 / 24 | **La diagramación**: ancho, alto y separación de las píldoras |
| `GrowTime` | 0.6 s | cuánto tarda una píldora en abrirse de 0 a su ancho |
| `SlideTime` | 0.5 s | constante del deslizamiento hacia arriba |
| `TextFadeStart` | 0.45 | a qué fracción de apertura empieza a aparecer el texto |
| `Reveal` / `Occupy` / `PosY` / `Target` | float[5] | estado de la animación (ancho / hueco / posición / pedido) |
| `TitleR` / `TitleT` | float | apertura del título y su objetivo |
| **`ExitFade`** | float | 🆕 **opacidad global de la salida** (1 → 0 en `ExitTime`). `LayoutPills` se la escribe como `SetRenderOpacity` a `PillTitle` y a las 5 píldoras; los `Txt` la heredan multiplicativamente, así que su propio fade de texto no se toca |
| `Occ` / `Acc` / `HTotal` | — | acumuladores del layout |

**API:** `InitPills()` · `SetTimings(Grow, Slide)` · **`ShowTitle()` / `HideTitle()`** · `ShowPill(Index)` · **`HideAll()`** (la salida: `bExiting = true` + `TitleT = 0`. 🔴 **NO toca los `Target`** — si los pusiera en 0 el grupo colapsaría al centro, que es justo lo que se descartó; el ancho y el hueco quedan congelados y lo único que se mueve es `ExitFade`) · `ResetPills()` · `StepPills(DT)` (la llama el actor desde su Tick).
🔴 **Una función por bucle** (`StepReveal` · `CalcOcc` · `StepSlide` · `LayoutPills`): en el DSL un `for` cierra la lista de statements, así que encadenar varios bucles en una sola función no compila. `StepPills` sólo orquesta las cuatro llamadas.

## BP_StageIntro_SC — el actor
```
Panel      WidgetComponent · WBP_StageIntro_SC · Space=World · DrawSize 640×640 · TickMode Automatic
             scale 0.1 (640 px → 64 cm) · relativeLocation (0, +40, 0)   ← las píldoras
SoulAnchor SceneComponent · relativeLocation (0, −75, 0)                  ← ahí nace la proto ameba
```
- `BeginPlay → CacheW` (con reintento cada 0.2 s hasta 40 veces, porque el `WidgetComponent` crea su widget tarde) → `InitPills` + `SetTimings` + `SpawnSoul` + `AutoStart`.
- `SpawnSoul`: spawnea `BP_ProtoSoul_SC` en el **`GetWorldTransform` del `SoulAnchor`** (o sea posición, rotación **y escala** se autoran moviendo el anchor) y le escribe `RingDrawTime = RingTime`. 🔴 **No la revela**: nace dormida (`bStartAsleep`) y aparece animada en el paso 0, junto con el título.
- **`IntroPlay()`** es **la API pública** (la llama el director en el VO 3): resetea el estado, **limpia la lámina en el acto** y agenda **`IntroBegin`** a los `StartDelay` segundos. `IntroBegin` es el que arranca de verdad el timer looping. `IntroNext` avanza en **6 pasos**:
  - **Idx 0** → `StepZero` = `ShowTitle()` + `Soul.Reveal()` (la lámina "Soul Charger" y la ameba naciendo)
  - **Idx 1..5** → `RevealOne` = `HideTitle()` + `ShowPill(Idx−1)` + `DrawRing(Idx−1)`
  - **Idx 6** → `IntroStop` (corta el timer) + timer de `ExitHold` → **`IntroOutro`** = `widget.HideAll()` + `Soul.HideRings()` + `Soul.Disappear()` + timer de `OutroTime` → **`IntroDone`** = `bIntroDone = true` (el aviso) + timer de `DestroyDelay` → **`IntroDestroy`** = destruye la ameba spawneada y se destruye a sí mismo.
- `Tick → TickIntro(DT) → widget.StepPills(DT)`. 🔑 **La animación la corre el actor, no el Tick del widget** — evita la trampa del `TickMode` de los `WidgetComponent`.

| Variable (actor, instance-editable) | Default | Rol |
|---|---|---|
| **`StartDelay`** | 1.5 s | 🆕 **cuánto espera desde el disparo del VO 3 hasta empezar la animación**. `IntroPlay()` limpia la lámina al instante y agenda el arranque, así que durante la espera no se ve nada |
| `StepTime` | 4.0 s | **el ritmo**: cada cuánto aparece la etapa siguiente (se ajusta al VO) |
| `GrowTime` | 0.6 s | apertura de la píldora (se empuja al widget) |
| `SlideTime` | 0.5 s | deslizamiento vertical (se empuja al widget) |
| `RingTime` | 2.5 s | cuánto tarda el anillo de la ameba |
| `ExitHold` | 2.0 s | cuánto se queda la lámina completa antes de la salida (el total con lo anterior es `StepTime + ExitHold`) |
| `OutroTime` | 1.2 s | cuánto dura la salida antes de avisar que terminó (`bIntroDone`) |
| **`IntroInTime`** | 1.2 s | 🆕 **cuánto tarda la ENTRADA de la ameba + el título "Soul Charger"** (una sola perilla para los dos). `SpawnSoul` se la empuja a la ameba como su `AppearTime`, y `StepZero` sigue leyéndola **de la ameba** para el `TitleInTime` del widget — así quedan sincronizados por construcción sin tocar nada más |
| **`IntroOutTime`** | 0.6 s | 🆕 cuánto tarda la ameba (y con ella los anillos) en irse; se empuja como su `DisappearTime`. Es la salida del MESH — la de los cuadros de texto es `ExitTime` |
| **`ExitTime`** | 0.6 s | 🆕 **velocidad de la animación de SALIDA** (cuánto tardan las píldoras en cerrarse y colapsar). Independiente de `GrowTime`/`SlideTime`, que son la entrada. ⚠ Conviene que `OutroTime` ≥ `ExitTime`, o el director avanza antes de que la lámina termine de irse visualmente |
| **`DestroyDelay`** | 1.0 s | 🆕 margen entre el aviso y la autodestrucción — **es lo que le da tiempo al director a consumir `bIntroDone`** antes de que el actor deje de existir |
| `bAutoPlay` / `AutoPlayDelay` | true / 2.0 s | arranca solo (para probar). **Poner en false cuando el Hall dispare `IntroPlay`** |
| `Idx` / `WTries` / `IntroW` / `SoulRef` | — | estado interno |

## Verificado en PIE (2026-08-25, `DebugStartRoom=0`, medición del estado vivo a ~1 Hz)
| Momento | Medido |
|---|---|
| **Idx=0** | `TitleR=1`, todas las píldoras en 0, y la ameba naciendo (`AppearT` 0.81 → 1) ✓ |
| **Idx=1 (la transición clave)** | `TitleR=0.58` bajando · `Occupy=[1,0,0,0,0]` (el hueco YA abierto) · **`Reveal=[0,…]` — Entering todavía NO aparece**. Al frame siguiente `TitleR=0` y recién ahí `Reveal[0]` 0.48 → 1. **Las dos fases separadas, sin superposición** ✓ |
| Idx=2 y 3 | `Occupy` llega a 1 y `Reveal` va detrás (0.56 · 0.85) → **el slide ocurre antes de la aparición** ✓ |
| Idx=6 (fin) | `PosY=[−240,−120,0,120,240]` — **centrado y espaciado exactos**; los 5 anillos completos; el timer se detuvo |
| **Salida (opacidad)** | 210 muestras logueadas durante la salida: **`ExitFade` 0,97 → 0,94 → 0,92 → … → 0,0** mientras **`Reveal[0]` y `Occupy[0]` se quedan clavados en 1,0**. Es decir **se desvanece sin achicarse ni moverse**, exactamente lo pedido ✓ (la ameba, en paralelo, a `AppearT = 0`) |
- Widget cacheado al primer intento (`WTries=0`), 1 sola ameba spawneada, **cero `Accessed None`**.

### 🪒 El diente de sierra de los bordes — era el BLEND MODE (2026-08-25)
Beltrán, ya con la resolución subida: *"los bordes de cada cuadro se siguen viendo con mucho diente de sierra, como si tuvieran línea negra delgada. Pero en verdad no tienen"*.
🔴 **Causa: el `WidgetComponent` venía en `BlendMode = Masked`** (el default de fábrica) = **alfa de 1 bit**. Sin medios tonos no hay antialiasing: el borde redondeado se recorta en escalones y por el corte asoma el fondo oscuro del render target, que se lee como una línea negra finita. **Por eso subir `DrawSize` no lo arreglaba.**
✅ **Fix: `BlendMode = Transparent`**, escrito en el CDO **y en la instancia** del Hall. Ver `gotchas.md` §214 — es la 2ª vez que `Masked` muerde en esta obra.
⚠ **Al aplicarlo apareció que la instancia tiene diagramación propia**: `DrawSize 1920×1920` y `relativeScale3D 0.06` (autorados por Beltrán → panel de ~115 cm a **16,7 px/cm**), distintos del CDO (1040×1240 · 0,05). **Se respetaron**: manda la instancia. Si se quiere cambiar la nitidez, hay que tocarla ahí, no en el CDO.

## 🎬 Cuándo entra y cuándo devuelve el control (2026-08-25)
🔴 **Arranca en el VO 3 del Hall** — el momento en que Alma se mueve hacia un costado (pedido de Beltrán). Es el **sub 3 de `RunHallA`** en [[BP_Director_Story]]: la llamada a **`PlayStageIntro()`** se insertó **por cirugía entre `Alma.MoveTo` y el `Say(VO 3)`**, así que la lámina empieza justo cuando Alma se corre y arranca la voz.
⚠ `RunHallA` **no se puede reescribir desde el `read`**: el lector renderiza `BP_Sensor_Soul.Appear` como `Class|BPAlmaSC|Appear` (colisión de nombres, gotcha conocido) y reescribir rompería la aparición del sensor. **Sólo cirugía.**

🔴 **Y el sub 3 ya no espera al VO: espera a que la EXPLICACIÓN termine.** Antes el VO 4 + `Sensor.Appear()` salían al terminar el VO 3; ahora salen **cuando la animación de salida del widget se completa** (pedido de Beltrán). Implementación:
- El sub 3 del Hall pasó a `WaitFor = "intro"` (cambio de **un literal** en el `SetWaitFor`, sin tocar la estructura).
- El actor levanta **`bIntroDone`** cuando termina la salida, y el director lo **poll-ea** en `TickIntroDone` (dependencia invertida, el patrón de la ceremonia — evita las trampas de los nodos `Assign`). Al verlo: log + `Next()` → sub 4 = VO 4 + sensor.
- `PlayStageIntro` cachea la referencia en `IntroRef` al buscar el actor por clase (vive en el sublevel del Hall, así que no existe hasta que la sala streamea).
- `IntroPlay()` resetea `bIntroDone` al arrancar, así el ciclo es repetible.

✅ **Verificado en PIE, la cadena entera** (`DebugStartRoom=0`): `arranca la explicacion de las etapas (VO 3)` → … → `INTRO: termino la animacion de salida` → `STORY: la explicacion termino - sigue el sensor` → `SENSOR: aparece`. Los pasos del Hall quedaron `paso 3 espera: intro` → `paso 4 espera: taken`. **Cero `Accessed None`.**

⏱ **Duración total de la lámina** = `StepTime × 6 + ExitHold + OutroTime` ≈ **27 s** con los valores actuales. Como ahora el sensor espera a que termine, **`StepTime` es la palanca para calzarla con el largo real del VO 3** (y con lo que dure la explicación hablada).

### 🎚️ Entrada y salida tienen velocidades separadas (2026-08-25)
- **Salida**: el widget lleva un flag **`bExiting`** que levanta `HideAll()` y baja `ResetPills()`. Mientras está en true, **`ExitFade` cae de 1 a 0 en `ExitTime`** (y el título cierra con esa misma constante). Así la salida se regula sola con una única perilla, sin tocar el ritmo de la entrada.
- 🆕 **La salida de las píldoras es OPACIDAD, no escala** (2026-08-25, corrección de Beltrán): la primera versión cerraba `Target` → 0 y el grupo se desarmaba coleando hacia el centro; se veía raro. Ahora **la geometría no se mueve** y baja el alfa. La ameba **sí** sigue saliendo por escala (`Disappear()`), que ahí sí queda bien.
- **El título entra al mismo tiempo que la ameba, y ahora los dos se manejan con UNA perilla del actor**: `SpawnSoul` → **`PushSoulTimes()`** escribe `IntroInTime`/`IntroOutTime` en el `AppearTime`/`DisappearTime` de la ameba recién spawneada, y `StepZero` **lee el `AppearTime` de esa ameba y se lo empuja al widget** (`SetTitleInTime`), así que la píldora "Soul Charger" y el mesh **crecen sincronizados por construcción** — si Beltrán cambia el `AppearTime` de la ameba, el título lo sigue solo, sin re-sincronizar a mano. La velocidad del título es entonces: **abriendo** → `TitleInTime` (= el de la ameba) · **cerrando para dar paso a Entering** → `GrowTime` · **en la salida final** → `ExitTime`.
- ✅ **Verificado en PIE muestreando los dos a la vez** (`AppearTime` de la ameba = 1,2 s): `TitleR` y `AppearT` suben en paralelo exacto — `0,125/0,125 · 0,25/0,25 · 0,375/0,375 · 0,5/0,514 · 0,764/0,778 · 1/1`, y `TitleInTime` llegó en 1,2 empujado desde la ameba. Cero `Accessed None`.
⚠ **Trampa del MCP pagada acá**: una variable de widget **no expuesta** (sin *Instance Editable*) **no existe como setter cross-clase**, y `find_node_types` tampoco indexa los miembros recién creados. El camino que funcionó: **`create_node` con el `type_id` a mano + `declaring_class`**, y después cablear por cirugía (ver `gotchas.md` sobre el índice que no refresca).

### 🧹 Liberación de memoria y la trampa de destruirse (2026-08-25)
Pedido de Beltrán: *"una vez que se acabó la animación y lanzó la siguiente acción, debemos hacer destroy del componente para liberar memoria"*.
- **`IntroDestroy()`**: `DestroyActor` sobre `SoulRef` (la ameba es un **actor aparte**, spawneado por este BP — destruir el actor de la lámina no se la lleva) y después `DestroyActor` sobre sí mismo.
- 🔴 **Por qué hay `DestroyDelay` y no se destruye en el acto**: el director espera el final **poll-eando `IntroRef.bIntroDone`**. Si el actor se destruyera en el mismo instante en que levanta la bandera, el poll encontraría la referencia inválida y **la obra quedaría colgada para siempre en `WaitFor = "intro"`**. El margen de 1 s garantiza que el director ya la consumió (medido: la consume a los **16 ms**).
- 🛡️ **Y además una red de seguridad en el director**: la rama `Is Not Valid` de `TickIntroDone` ahora **avanza igual** (`no hay explicacion viva - sigo igual`). Así, destruir el actor —o que ni siquiera exista en la sala— **nunca puede colgar la obra**.

✅ **Verificado por marcas de tiempo del log** (`DebugStartRoom = 0`, valores de la instancia):
```
10:26:46.152  STORY: arranca la explicacion de las etapas (VO 3)
10:26:48.152  INTRO: arranca la animacion            <- +2,000 s = StartDelay exacto
10:27:01.752  INTRO: termino la animacion de salida
10:27:01.768  STORY: la explicacion termino - sigue el sensor   <- +16 ms
10:27:01.768  SENSOR: aparece
10:27:02.752  INTRO: me destruyo y libero memoria    <- +1,000 s = DestroyDelay
```
Tras la corrida: **0 actores `StageIntro` y 0 amebas spawneadas vivas**, cero `Accessed None`.

### ⏱ Los tiempos vigentes los autora Beltrán EN LA INSTANCIA (2026-08-25)
🔴 **La instancia del Hall tiene valores propios y son los que corren** — el CDO no manda. Estado autorado al cierre de la jornada:
`StartDelay` **2,0** · `StepTime` **2,0** · `GrowTime` **0,2** · `SlideTime` **0,2** · `RingTime` **2,0** · `ExitHold` **3,0** · `OutroTime` **2,5** · `ExitTime` **0,6** · `DestroyDelay` **1,0** · `IntroInTime` **1,2** · `IntroOutTime` **0,6** · `bAutoPlay` **false**.
Y en el `Panel`: `DrawSize` **1920×1920** · `relativeScale3D` **0,06** (panel de ~115 cm, 16,7 px/cm) · `BlendMode` **Transparent**.
⚠ **No pisar estos valores desde el CDO.** Antes de escribir cualquier perilla en la instancia, **leerla primero**: varias veces en esta jornada el CDO y la instancia estaban distintos porque Beltrán ajustaba en vivo mientras se construía.
✅ **`StartDelay` verificado midiendo el log**: entre `arranca la explicacion de las etapas (VO 3)` y `INTRO: arranca la animacion` pasaron **exactamente 2,00 s**, el valor de la instancia. (La 1ª medición dio 3,37 s y era falsa: se comparaba contra una línea de una corrida ANTERIOR — el log es acumulativo. Se rehízo comparando **marcas de tiempo del propio log**, no reloj de pared.)

## 🔎 Nitidez del texto — por qué se veía mal y cómo se arregló (2026-08-25)
Beltrán: *"los cuadros de texto se ven en bajísima calidad"*. **No era la fuente ni el material: era la densidad de píxeles del render target.** Un `WidgetComponent` dibuja el widget en una textura de `DrawSize` px que después se estira al tamaño físico del quad, así que lo que manda es **px/cm**:

| Widget | DrawSize · escala | tamaño físico | **px/cm** |
|---|---|---|---|
| este panel (antes) | 640×640 · 0.10 | 64 × 64 cm | **10** ← borroso |
| [[BP_SoulHUD_SC]] (se ve bien) | 1000×400 · 0.04 | 40 × 16 cm | **25** |
| **este panel (ahora)** | **1040×1240 · 0.05** | **52 × 62 cm** | **20** |

✅ **El arreglo**: se duplicó la densidad **sin cambiar el tamaño físico de las píldoras** (siguen midiendo 48 cm de ancho). Como `DrawSize` es el lienzo en píxeles, hubo que **multiplicar por 2 TODOS los valores en px** para conservar la misma diagramación: `PillW` 960 · `PillH` 192 · `PillGap` 48 · `cornerRadii` 96 · padding 92/40 · **fuente 80**. El lienzo además se ajustó al contenido (no cuadrado) para no pagar píxeles vacíos.
⚠ **El costo**: el render target pasó de 0,41 a 1,29 MPx (×3,15) y **se redibuja cada frame mientras la animación corre** (no en las pausas). Si en Quest pesa, la perilla es bajar `DrawSize` y subir `relativeScale3D` en la misma proporción — el tamaño en el mundo no cambia, sólo la nitidez.
💡 Si aún así se lee delgado a esa distancia, los siguientes escalones son: **tipografía más gruesa** (`typefaceFontName` a `Bold` en los `Txt`) y subir el tamaño físico del actor.

## TODO
- [ ] 🔴 **Visor**: composición (posición del actor / `Panel` / `SoulAnchor`), tamaño de letra a esa distancia y si el widget se lee espejado con yaw 180 (si sí, invertir el signo de `Y` en los dos componentes).
- [x] ✅ Enganchado al **VO 3** del Hall y `bAutoPlay=false` en la instancia.
- [ ] Ajustar `StepTime` al largo real del VO 3 (hoy la lámina dura ~27 s y el sensor espera a que termine).

## Relacionados
[[BP_StageIntro]] (el ancestro del esqueleto viejo) · [[BP_ProtoSoul_SC]] (la ameba y sus anillos) · [[BP_SoulHUD_SC]] (de donde sale la gramática del nacimiento por ancho) · [[BP_Director_Story]] (quien lo disparará)

### 💍 Los anillos ya no se cortan, y una sola perilla para la entrada (2026-08-25)
Dos pedidos de Beltrán sobre la misma lámina:
1. *"agrega una variable que controle el tiempo de aparición de la ameba + el texto soul charger"* → **`IntroInTime`** (y de yapa **`IntroOutTime`** para la salida del mesh). `SpawnSoul` termina llamando a **`PushSoulTimes()`**, que se las escribe a la ameba recién spawneada. Como `StepZero` ya leía el `AppearTime` **de la ameba** para el título, con empujar la ameba alcanza: **los dos siguen la misma perilla sin lógica extra**.
2. *"desaparecer anillos: mal, se cortan de 0"* → se sacó la llamada a `HideRings()` de `IntroOutro` y **`ApplyRingScale` de [[BP_ProtoSoul_SC]] ahora multiplica la escala del `RingRoot` por `Ease(EaseInOut, AppearT)`**. Los anillos se achican con el cuerpo, con la curva del cuerpo.

✅ **Medido en PIE, 210 muestras a frame-rate durante la salida**: `AppearT` baja parejo **0,972 → 0,944 → 0,917 → … → 0** (≈0,0278 por frame = los 0,6 s de `IntroOutTime`) mientras **`RingReveal[0]` se queda en 1,05 todo el tiempo** — o sea el anillo **sigue dibujado y sólo se achíca**, ya no se apaga de golpe.
✅ **La perilla aterriza de verdad** (no sólo compila): con la instancia en `IntroInTime = 1,2`, el log de la ameba spawneada da `kIn=1,2 → sIn=1,2`.
✅ Corrida completa sin `Accessed None`: `INTRO: arranca la animacion` → `INTRO: termino la animacion de salida` → `INTRO: me destruyo y libero memoria` → `STORY: la explicacion termino - sigue el sensor`.

🚩 **Dos trampas que costó esta tanda** (ambas en `gotchas.md` §216-217): el valor de instancia de una variable nueva **se pierde en el siguiente recompilado del Blueprint** — hay que escribirlo **después** de la última compilación y ahí guardar el nivel; y borrar un nodo de diagnóstico que se había **intercalado** en una cadena la deja **cortada** (se dejó `ApplyRingScale` sin sucesor y `StepRings` colgando — los anillos no se habrían animado nunca).
