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
| **`SetFieldCalm(C)`** | Guarda la calma 0-1 clampeada. La etapa la bombea a 10 Hz. |
| `ApplyField` / `FieldStep` / `FadeGate` / `FadeAdvance` / `FadeApply` / `FadeFinish` | Interno. |
| `ProbeParams` | 🔬 Ver abajo — corre en `BeginPlay`. |

**La fórmula de la modulación** (`ApplyField`):
```
efectivo = Intensity × (MinFactor + (1 − MinFactor) × Calm)
escala   = BaseScale × (0.25 + 0.75 × efectivo)
```
`MinFactor` 0.35 es el piso: con calma 0 el campo **no desaparece**, sólo baja al 35 %. Es la regla de "un módulo ausente nunca se ve como error" — con el EEG desconectado el campo sigue vivo.

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
| `IntensityParam` / `ColorParam` | "Intensity" / "FieldColor" | Los nombres a buscar en el sistema. |
| `BaseScale` | (1,1,1) | Escala base del componente. La escala **del actor** se multiplica encima — eso es lo que se autora en el nivel. |
| `MinFactor` | 0.35 | Piso de intensidad con calma 0. |
| `Intensity` / `Calm` / `bFieldOn` / `bFading` / `Fade*` | — | Estado interno. |

## TODO
- [ ] 🔴 **Arte real**: un Niagara aditivo por campo, que exponga `Intensity` (float) y `FieldColor` (LinearColor). En cuanto exista, `ProbeParams` lo detecta solo.
- [ ] ⚠ `niagara-quest.md`: verificar en APK que la **Scalability** del emitter no lo apague (`fx.Niagara.QualityLevel` está clampeado en Android) y que el aditivo no dispare el overdraw.
- [ ] Visor: los tres campos son dust boxes de 10×10 m escalados a 0.1 — hay que ver cómo leen desde la silla.

## Relacionados
- [[BP_Stage_Subclases]] (§Loving v2) · [[BP_BioHub]] (de donde sale `CalmSmooth`) · [[BP_Ceremony]] (lo que corre después) · `NS_VoidDust` (el placeholder)
