# BP_DemoAmb_SC — la música de cada nivel de la demo, en bucle

- **refPath**: `/Game/SoulCharger/Demo/Blueprints/BP_DemoAmb_SC` · parent Actor · creado 2026-10-16.
- **Por qué**: los `Ambient_Clip_*` no hacen loop (la Obra los encadena con `AmbTick`: crossfade consigo mismo). Un `AmbientSound` se queda en silencio cuando el clip termina (Surrounding dura 144 s; la experiencia, ~3 min). Copia la lógica de `BP_Obra_SC.AmbTo/AmbTick`.

## Variables
- **Amb** (por instancia): `Clip` · `Volume` 0,8 · `FadeIn` 3 · `FadeOut` 3.
- **Z-Estado**: `Cur` (AudioComponent), `Age`, `Len`, `bOut`, `Mode` (1 = hay ensayo, 2 = hay menú), `Runner`, `Menu`.

## Grafos
- `BeginPlay`: busca `BP_StageRunner_SC` / `BP_DemoMenu_SC` → `Mode`; `Play`.
- `Play`: `CreateSound2D(Clip, Volume)` → `Cur`, `Len` = duración del clip, `FadeIn`.
- `LoopStep` (Tick): a `Len − FadeOut` → `FadeOut` del actual + `Play` otra vez (crossfade).
- `CloseStep` (Tick): cuando el ensayo llega a `RPhase` 7 o el menú a `Phase` 7 (el velo cierra) → `FadeOut` 3 s, una vez.
- 🔴 `Audio|Components|Audio|FadeIn/FadeOut` están **duplicados** en el catálogo (trampa 3 del DSL): el DSL toma el que no es y falla con *"Could not connect … to self"*. Se crearon con `create_node` + `declaring_class` `/Script/Engine.AudioComponent`.

## Instancias
`L_Demo_Menu` Clip 1 (Intro) · `L_Demo_Breath` Clip 4 (Breath) · `L_Demo_Draw` Clip 7 (Surrounding; reemplaza el `AmbientSound` TestOnly de la copia).


## 2026-10-19 — Switch y FadeAll (guion v2)
- `Switch(NewClip)`: `FadeOut` 2,5 s del clip actual + `Play` del nuevo (el menú pasa de Ambient 1 a Ambient 2 al elegir).
- `FadeAll()`: `bOut` + `FadeOut` 3 s (lo llaman el menú y `BP_DemoFlow_SC` al ir a negro).
- `CloseStep` ya no se llama (dependía del ensayo y del menú viejo): EventGraph = BeginPlay → `Play`; Tick → `Age` + `LoopStep`. Los `FadeOut` se crearon por nodo con `declaring_class` AudioComponent.

## 2026-10-19 (noche)
- `CloseStep` vacío y variable `Runner` fuera: era del guion v1 y arrastraba `BP_StageRunner_SC` (y con él la Obra) a cada nivel de la demo.
