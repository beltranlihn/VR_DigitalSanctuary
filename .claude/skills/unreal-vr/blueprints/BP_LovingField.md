# BP_LovingField — el campo de luz de Loving (Core/VFX/)

## Purpose
Acto 6 del guión: *"3 Niagaras aditivos timeados: VO16+SMind1→N1 · VO17+SMind2→N2 (N1 sigue) · VO18+SMind3→N3 · al terminar VO18 desaparecen todos. **Intensidad modulada por la calma EEG**"*. Reemplaza las 3 preguntas en TextRender que había antes.

Este BP es **un** campo. Se colocan **tres en `L_Room_Loving`** y cada uno se distingue por su `FieldIndex` (0·1·2). [[BP_Stage_Loving]] los busca por clase y les pide aparecer en su beat.

🎛️ **Todo lo autorable vive en el nivel, no en el grafo**: posición, rotación y **escala** de cada campo, su color, su sistema Niagara, y el mínimo de intensidad. Agregar un 4º campo = arrastrar otro actor y ponerle `FieldIndex=3` (y sumar un beat a `BeatTimes`). No se toca un solo nodo.

## Status
🟢 Ciclo verificado por log (2026-08-15, `DebugStartStage=3`): 3 campos encontrados, aparecen en sus beats, se apagan juntos, la etapa cierra por el camino real y encadena la ceremonia (anillo morado, carga 0.6). Cero `Accessed None`.
🟡 **El arte es placeholder**: los tres usan `NS_VoidDust`, que **no expone ningún user parameter** → hoy la calma modula sólo por **escala del componente**. Ver abajo.

## Anatomía
```
BP_LovingField (actor colocado en L_Room_Loving)
└─ FX  NiagaraComponent · Asset = NS_VoidDust (placeholder) · bAutoActivate=FALSE · CastShadow=false
```
Colocados: `LovingField0` (3750,−120,130) rosa · `LovingField1` (3750,+120,130) violeta · `LovingField2` (3700,0,230) ámbar — los tres a escala 0.1 (la sala Loving está en X=3600, la puerta en 4060).

## API
| Función | Qué hace |
|---|---|
| **`FieldAppear(Duration)`** | `Activate` del componente + fade de `Intensity` hacia **1** en `Duration`. |
| **`FieldVanish(Duration)`** | Fade de `Intensity` hacia **0**; al llegar, `Deactivate` (lo hace `FadeFinish`). |
| **`SetFieldCalm(C)`** | Guarda la calma 0-1 clampeada. 🔴 **La etapa la bombea desde su TICK, o sea una vez por frame** — ver abajo. |
| `ApplyField` / `FieldStep` / `FadeGate` / `FadeAdvance` / `FadeApply` / `FadeFinish` | Interno. |
| `ProbeParams` | 🔬 Ver abajo — corre en `BeginPlay`. |

**La fórmula de la modulación** (`ApplyField`):
```
efectivo = Intensity × (MinFactor + (1 − MinFactor) × Calm)
escala   = BaseScale × (0.25 + 0.75 × efectivo)
```
`MinFactor` 0.35 es el piso: con calma 0 el campo **no desaparece**, sólo baja al 35 %. Es la regla de "un módulo ausente nunca se ve como error" — con el EEG desconectado el campo sigue vivo.

## 🔴 60 Hz: la calma va POR FRAME, no por timer (decisión de Beltrán, 2026-08-15)
> *"yo trabajaría con el OSC que nos va a estar llegando a sesenta hertz, porque si después yo quiero mapear esa data al curl noise o a distintos efectos dentro del Niagara, es mucho más notorio y suave cuando es a sesenta hertz que cuando es a diez o a treinta. Así que dejémoslo a sesenta, que es el tiempo en el que nos va a llegar."*

La v1 bombeaba con un **timer de 0,1 s (10 Hz)**. Ahora `PumpCalm` cuelga del **`EventTick` de [[BP_Stage_Loving]]** (cirugía de nodo, enganchado después de `Parent:Tick`), y `ApplyField` ya corría por frame en el Tick del campo. La cadena entera quedó a **una actualización por frame**.
- **Por qué Tick y no un timer de 1/60**: en el target (Quest 3, 60 fps de render) un frame **es** 1/60 s, así que el Tick da exactamente el ritmo del OSC — y nunca queda desfasado contra el frame, que es lo que produce el escalonado que se nota en el shader. Un timer de 0,0167 s se alinea mal con el frame y puede disparar dos veces en uno.
- **Contrapartida honesta**: si baja el frame rate, baja el muestreo con él. Es correcto — no se puede pintar más rápido de lo que se dibuja.
- **`CalmParam` (default `"Calm"`)** es el hook para el mapeo de Beltrán: se escribe la **calma cruda 0-1 sin la curva de intensidad**, para poder colgarle curl noise o lo que sea dentro del Niagara. `IntensityParam` sigue llevando el valor ya modulado.
- **`bUseRawCalm`** en la etapa (instance-editable, default `false`) elige entre `BioHub.CalmSmooth` (EMA, suave pero con retardo) y `BioHub.Calm` (crudo a 60 Hz). Con el EEG real puede convenir el crudo, porque el suavizado que importa lo va a hacer el propio efecto.
- **Verificado (2026-08-15)**: con PIE corriendo, 18 lecturas seguidas de `Calm` sobre los 3 campos dieron una **rampa continua sin mesetas** (0,3400 → 0,3760), o sea que el valor cambia entre lectura y lectura. A 10 Hz habrían salido bloques de valores repetidos.

## 🔬 `ProbeParams` — el patrón que hay que copiar para cualquier Niagara data-driven
El sistema Niagara **es un dato** (`FX.Asset`), y los nombres de sus parámetros también (`IntensityParam` = "Intensity", `ColorParam` = "FieldColor", los dos instance-editable). En `BeginPlay` el actor **pregunta** si esos parámetros existen, con el pin `bIsValid` de `GetNiagaraVariable`, y guarda `bHasIntensity`/`bHasColor`. `WriteIntensity`/`WriteColor` escriben **sólo si existen**.

👉 Consecuencia práctica: **el día que Beltrán ponga un sistema que exponga `Intensity` y `FieldColor`, la modulación empieza a funcionar sola, sin tocar un nodo.** Y mientras tanto el log lo dice en la cara en vez de fingir:
```
LOVING FX: parametro de intensidad valido tal cual = false | con prefijo User. = false
LOVING FX: parametro de color valido = false
```
🔴 **Medido en `NS_VoidDust`: `userVariables` está VACÍO** (`GetSystemSummary`). No es que el nombre esté mal — el sistema no tiene ni un parámetro. Por eso la única palanca real hoy es la **escala del componente**, que funciona con cualquier sistema.

⚖️ **Lo que este probe NO resolvió todavía**: `assets-existentes.md` se contradice sobre si `SetNiagaraVariable(...)` lleva o no el prefijo `User.` (un bloque dice que sí, otro que es un no-op silencioso). Acá los dos dieron `false` **porque el parámetro no existe con ningún nombre**, así que la pregunta sigue abierta. **En cuanto haya un sistema con parámetros reales, esta misma línea de log la contesta** — es el motivo de que el probe pruebe las dos escrituras.

## Registro de variables (instance-editable las 6 primeras)
| Variable | Default | Rol |
|---|---|---|
| `FieldIndex` | 0 | En qué beat aparece este campo. **Es el único vínculo con la etapa.** |
| `FieldColor` | morado | Color que se escribe en `ColorParam` si el sistema lo expone. |
| `IntensityParam` / `ColorParam` / `CalmParam` | "Intensity" / "FieldColor" / **"Calm"** | Los nombres a buscar en el sistema. `CalmParam` recibe la **calma cruda** por frame — es el hook para mapear curl noise y demás dentro del Niagara. |
| `BaseScale` | (1,1,1) | Escala base del componente. La escala **del actor** se multiplica encima — eso es lo que se autora en el nivel. |
| `MinFactor` | 0.35 | Piso de intensidad con calma 0. |
| `Intensity` / `Calm` / `bFieldOn` / `bFading` / `Fade*` | — | Estado interno. |

## TODO
- [ ] 🔴 **Arte real**: un Niagara aditivo por campo, que exponga **`Intensity` (float), `FieldColor` (LinearColor) y `Calm` (float)**. En cuanto existan, `ProbeParams` los detecta solos y empiezan a escribirse por frame. `Calm` es el que Beltrán quiere mapear a curl noise.
- [ ] ⚠ `niagara-quest.md`: verificar en APK que la **Scalability** del emitter no lo apague (`fx.Niagara.QualityLevel` está clampeado en Android) y que el aditivo no dispare el overdraw.
- [ ] Visor: los tres campos son dust boxes de 10×10 m escalados a 0.1 — hay que ver cómo leen desde la silla.

## Relacionados
- [[BP_Stage_Subclases]] (§Loving v2) · [[BP_BioHub]] (de donde sale `CalmSmooth`) · [[BP_Ceremony]] (lo que corre después) · `NS_VoidDust` (el placeholder)
