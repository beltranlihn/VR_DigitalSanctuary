# BP_StageIntro + WBP_StageIntro — la explicación de las etapas del Hall (Core/UI/)

## Purpose
La animación del Hall en la que **se nombran las 5 etapas** mientras la proto ameba abre un anillo por cada una. Pedido de Beltrán (2026-08-14): *"un widget que tenga unos contenedores con los nombres de cada etapa, con los colores, y le ponemos una protoameba con los anillos alrededor abriéndose cuando se nombra cada etapa"*, con la lámina de la página 2 del PDF del guión como referencia de diseño.

🔴 **Corrección del mismo día, y es la decisión de arquitectura del asset:** *"la protoameba y los anillos que sean REALES, tal como las usamos en el world y en la experiencia. Simplemente, el widget va a tener los nombres con los contenedores y deja un espacio a la derecha donde ponemos una protoameba real con sus anillos reales."*
👉 El widget **NO dibuja** ameba ni anillos. Es sólo la columna de píldoras. La ameba de la explicación es un **[[BP_ProtoSoul]] de verdad**, spawneado en el mundo, con los mismos `Ring0..4` y el mismo `M_SoulRing` de la obra. Una versión anterior tenía 5 `Image` + un `M_SoulRingUI` (dominio UI) dentro del widget: **se borraron**. `M_SoulRingUI` quedó en `Core/UI/Materials/` sin uso — borrable.

## Status
🟢 **Ciclo completo verificado por log** (2026-08-15, `DebugStartStage=0`): las 5 píldoras se registran, la ameba nace en su anchor a **0.0 cm**, y las etapas se revelan 0·1·2·3·4 cada 4 s y cierra. **Cero `Accessed None`.** ⬜ Falta el visor (composición, tamaños, si el widget lee espejado) y el arte/VO.

## Anatomía
```
BP_StageIntro (actor colocado EN L_Room_Hall, no en el persistente)
├─ Panel      WidgetComponent · WBP_StageIntro · Space=World · DrawSize 620×560 · TickMode Automatic
│               relativeScale 0.1 (620 px → 62 cm) · relativeLocation (0, +40, 0)
└─ SoulAnchor SceneComponent · relativeLocation (0, −75, 0) ← acá nace la proto ameba
```
- Colocado en `L_Room_Hall` en **(230, 0, 140) yaw 180** (la sala mira a +X: su puerta está en X=460).
- 🎛️ **Todo se autora moviendo cosas, no tocando el grafo:** el actor (posición/rotación/**escala** de toda la composición), `Panel` (dónde y qué tamaño el texto), `SoulAnchor` (dónde y **de qué tamaño** la ameba — el spawn usa `GetWorldTransform`, o sea también su escala y rotación). Es la regla del transform completo que pidió Beltrán.
- ⚠ **Si en visor la composición se lee espejada** (píldoras a la derecha), invertir el signo de `Y` en `Panel` y `SoulAnchor`. El sentido de lectura de un `WidgetComponent` con yaw 180 no está confirmado en visor.

## WBP_StageIntro (el widget: SÓLO las píldoras)
`Root` (CanvasPanel, anclado full) → `Pills` (VerticalBox) → `Pill0..Pill4` (Border) → `Txt0..Txt4` (TextBlock).
- Píldora: brush **`RoundedBox` con `roundingType=FixedRadius` y `cornerRadii` 48** (la cápsula de la lámina), padding 46/20, 22 px de separación entre píldoras.
- Texto: 40 px, `letterSpacing` 120, centrado, blanco. **En inglés**: ENTERING · RECOGNIZING · LOVING · ATTRACTING · SURROUNDING.
- Variables: `PillComps` (array de Border) · `StageColors` (5 LinearColor, **la paleta de la lámina**: azul 0.29/0.42/0.94 · rojo 0.93/0.35/0.33 · morado 0.77/0.36/0.93 · ámbar 0.94/0.76/0.36 · verde 0.30/0.69/0.31) · `IdleColor` (0.09,0.09,0.11) · `IdleOpacity` 0.35.
- API: **`InitPills()`** (la llama su propio `Event Construct` → el widget se auto-inicializa aunque lo recreen) · **`ResetPills()`** (todas grises al 35 %) · **`RevealPill(Index)`** (color de la etapa + opacidad 1.0, con guard contra los dos arrays).
- 🔴 Los `Event Tick` y `Event PreConstruct` vacíos que deja el `write_graph_dsl` se **borraron**: un Tick vacío en un widget igual tickea.

## El actor: cómo corre
```
BeginPlay → WTries=0 → CacheIntroWidget
CacheIntroWidget:  GetUserWidgetObject(Panel) → IsValid ? BindIntroWidget : RetryIntroWidget (0.2 s, hasta 40 intentos)
BindIntroWidget:   cast a WBP_StageIntro → InitPills → SpawnIntroSoul → IntroAutoStart
SpawnIntroSoul:    SpawnActor BP_ProtoSoul en GetWorldTransform(SoulAnchor) → bIsHUD=false → HideAllRings
                   → timer 1.5 s a VerifyIntroPose (aserción espacial)
IntroAutoStart:    si bAutoPlay → timer AutoPlayDelay a IntroPlay   (si no, espera a que la etapa llame IntroPlay)
IntroPlay:         IntroReset → timer LOOP StepTime a IntroNext → IntroNext (el primero, ya)
IntroNext:         IntroIdx++ ; si < 5 → IntroReveal(IntroIdx) ; si no → IntroStop
IntroReveal(i):    IntroRevealW(i)  +  IntroRevealSoul(i)
IntroRevealW(i):   relee el widget VIVO del componente → ResetPills → RevealPill 0..i   (repinta TODO, idempotente)
IntroRevealSoul(i):DrawRing(i, RingTime) sobre la proto ameba
IntroStop:         ClearTimer("IntroNext")
```
- 🔴 **`IntroRevealW` NO usa la referencia cacheada `IntroWidget`: relee `GetUserWidgetObject(Panel)` cada vez.** Un `WidgetComponent` puede **recrear** su widget (se vio nacer dos veces en una corrida), y el nuevo arranca gris. Como además repinta `0..i` en vez de sólo `i`, el estado se **auto-repara** si el widget se recrea a mitad de la animación.
- **`IntroPlay` es la API pública** para cuando la etapa del Hall maneje el tiempo (y el VO). Con `bAutoPlay=false` el actor no hace nada hasta que se lo llamen.

## Registro de variables (instance-editable las 4 primeras)
| Variable | Default | Rol |
|---|---|---|
| `StepTime` | **4.0 s** | Cada cuánto se nombra la etapa siguiente. Es **la palanca del ritmo**; Beltrán la ajusta al VO. |
| `RingTime` | **1.6 s** | Cuánto tarda en dibujarse el anillo de la ameba (va a `DrawRing`). |
| `bAutoPlay` | **true** | Si arranca solo. Ponerlo en `false` cuando el Hall maneje el disparo. |
| `AutoPlayDelay` | **2.0 s** | Cuánto espera desde el BeginPlay de la sala. Se clampea a un mínimo de 0.05 (un timer de 0 no dispara). |
| `IntroIdx` | −1 | Qué etapa va. `IntroReset` lo devuelve a −1. |
| `SoulRef` / `IntroWidget` / `WTries` | — | Estado interno. |

## Verificado por log (2026-08-15, `DebugStartStage=0`)
```
EXPLICA: pastillas registradas = 5
EXPLICA: proto ameba de la explicacion creada
EXPLICA POSE: distancia ameba-anchor cm = 0.0      ← medida 1,5 s DESPUÉS del spawn
EXPLICA: IntroReset deja idx = -1
EXPLICA: IntroNext avanza a idx = 0 → etapa revelada = 0
                              1 → 1 · 2 → 2 · 3 → 3 · 4 → 4
EXPLICA: IntroNext avanza a idx = 5 → explicacion de etapas terminada
```
Cero `Accessed None` en la corrida.

## 🐛 El bug que costó dos corridas: el nodo puro re-evaluado (trampa YA documentada)
La primera versión de `IntroNext` era:
```
(bind _n (+ (GetIntroIdx) 1))
(SetIntroIdx _n)
(if (< _n 5) (IntroReveal _n) (else (IntroStop)))
```
Resultado medido: empezaba en la etapa **1** y cortaba una etapa **antes**. Las dos cosas a la vez.
**Causa:** el `+` es puro y se evalúa **una vez por consumidor** — y el primer consumidor (`SetIntroIdx`) **escribe la variable que el `+` lee**. Así que el `Branch` y el `IntroReveal` re-evaluaban el `+` sobre el valor ya incrementado → `_n+1` en los dos.
**Fix:** escribir primero y **releer la variable fresca** en cada consumidor:
```
(SetIntroIdx (+ (GetIntroIdx) 1))        ; el + tiene UN solo consumidor
(if (< (GetIntroIdx) 5) (IntroReveal (GetIntroIdx)) (else (IntroStop)))
```
🔴 Esto **ya estaba en `gotchas.md` §"Nodos PUROS: se re-evalúan en CADA consumidor"** — se pagó igual. La **firma para reconocerlo rápido**: un off-by-one que aparece en **dos lugares distintos al mismo tiempo** (el valor usado y la condición de corte). Si sólo estuviera mal el argumento sería otra cosa.

## Cosas que no hay que volver a descubrir
- **`AddWidget` informa `bIsVariable: true` pero NO lo aplica.** Hay que llamar **`UMGToolSet.ToggleWidgetAsVariable`** por cada hijo y después **`UMGToolSet.CompileWidgetBlueprint`**; recién ahí existen los getters `Variables|<WBP>|Get<Hijo>`.
- **`find_node_types` NO lista esos getters aunque existan** — `write_graph_dsl` los resuelve igual. No usar `find_node_types` como prueba de ausencia.
- **`ObjectTools` cambia el nombre del parámetro según la tool**: `get_properties` usa `instance` + **`properties`**; `set_properties` usa `instance` + **`values`**.
- **Llamando una función PROPIA desde el DSL, el primer posicional puede caer en el pin `self`** (`Could not connect pin ReturnValue to self`). Usar el keyword: `(CallFunction|BindIntroWidget :W _w)`.
- **Setter de variable de OTRO objeto**: `(Class|BPProtoSoul|SetIsHUD :self _soul :bIsHUD false)` — con posicionales el target se va al pin de valor.
- **`StartPIE` devuelve "Timed out waiting for PIE to start" y sin embargo PIE corrió**: los logs valen. Pero hay que **`StopPIE` antes del siguiente `StartPIE`** o tira "A play session is already running".
- 🔴 **El prefijo `INTRO:` ya lo usaba `BP_IntroSequence`** (el menú/logo del arranque). Por eso este BP loguea **`EXPLICA:`**. Antes de elegir un prefijo de log, buscarlo.

## TODO
- [ ] 🔴 **Visor**: composición (¿se lee espejado?), tamaño del texto a 2,3 m, tamaño de la ameba, si el ritmo de 4 s acompaña.
- [ ] Que el Hall dispare `IntroPlay` (y ponga `bAutoPlay=false`) en vez del autoplay por tiempo, cuando exista el VO.
- [ ] VO por etapa: array de `SoundBase` con el patrón placeholder de [[BP_Ceremony]] (vacío = silencio + log).
- [ ] Borrar `Core/UI/Materials/M_SoulRingUI` (quedó sin uso al pasar a la ameba real).

## Relacionados
- [[BP_ProtoSoul]] (la ameba y sus anillos reales) · [[BP_Ceremony]] (usa los mismos anillos, uno por etapa cerrada) · [[BP_SoulHUD]] · `BP_IntroSequence` (el otro "intro": logos y menú de arranque, no confundir)
