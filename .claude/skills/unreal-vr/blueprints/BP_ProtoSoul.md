# BP_ProtoSoul — la ameba, que ES el HUD (Core/Amoeba/)

## Purpose
§5: **el Proto Soul es la lectura.** Su **pulso** es tu ritmo, la **agitación de su superficie** es tu calma, sus **anillos** son la carga. Cero números, cero paneles, y es el objeto del que trata la obra.

🔴 **No es un HUD pegado al casco ni un reloj.** §5 descarta las dos: pegado al casco es incómodo y borroso en los bordes y rompe el lugar; reloj compite con el sensor que llevás en la mano.

## Status
🟡 **Lazy-follow, pulso y agitación construidos y verificados en PIE** (2026-08-11). 🆕 **Variantes configurables en runtime y adopción desde el GameInstance.** ⬜ Faltan los **anillos de carga** y el test en visor.

## 🆕 Lo que se agregó el 2026-08-11 (para la elección del Hall)
| Función | Rol |
|---|---|
| `ConfigureVariant(Id, Mesh, Mat, Color)` | 🔴 **La API pública de la variante.** El Construction Script sirve para autorar en el editor, pero una candidata **spawneada** necesita configurarse en runtime, y el CS no vuelve a correr. Setea las 4 variables y aplica las tres cosas. |
| `ApplyVariantColor()` | Aplica `SoulColorOverride` al parámetro `SoulColor` del material, **gateado por `bUseColorOverride`**. Ese bool es el flag que distingue "color negro" de "sin override": sin él, el default (0,0,0) apagaría la ameba. |
| `AdoptFromState()` / `AdoptStep(St)` | Lee [[BP_SoulState]] (el GameInstance) y, **si `bHasChosen`**, se configura con la elección. Corre en `BeginPlay`, así que **la identidad elegida sobrevive a los cambios de nivel** sin que nadie la reenvíe. |
| `TickStep(Delta)` / `HudStep(Delta)` | 🔴🔴 **El Tick ahora está gateado por `bIsHUD`.** `UpdateReadout` (pulso y agitación) corre en **todas** — las candidatas del Hall también laten, y eso es deseable: se ven vivas. Pero `UpdateFollow` + `ApplyPlacement` corren **sólo en el HUD**. Sin ese gate, cada candidata se pegaría a la cámara y se apilarían todas encima. |

⚠ **`SoulColorOverride` era dato muerto hasta hoy**: existía la variable y el parámetro del material, pero nada las conectaba. Es el caso típico de "declarado ≠ aplicado".

## 🔴 Dos roles en el mismo Blueprint: HUD y variante elegible
Aclarado por Beltrán el 2026-08-11: **las Proto Souls aparecen en TargetPoints frente al usuario, y la que elige el usuario es la que queda** (§3, escena 3 del Hall). Así que el mismo BP tiene que servir para dos cosas:

| Rol | `bIsHUD` | Comportamiento |
|---|---|---|
| **El HUD** | true | Sigue la mirada con lazy-follow y lee el BioHub. Es la instancia que acompaña toda la obra. |
| **Variante elegible** | false | Se queda quieta en su TargetPoint del Hall, con **su propio mesh y material**, esperando que la elijan. |

Por eso el mesh y el material **no están hardcodeados**:
| Variable | Tipo | Rol |
|---|---|---|
| `SoulMesh` | StaticMesh | El mesh de esta variante. **Si está vacío se queda la esfera por defecto**, así que un placeholder nunca desaparece. |
| `SoulMaterial` | MaterialInterface | El material de esta variante. Mismo criterio: vacío = queda `M_ProtoSoul`. |
| `VariantId` | int | Identidad de la variante, para persistirla en el GameInstance cuando el usuario elija. |
| `SoulColorOverride` | LinearColor | Color de esta variante. |
| `bIsHUD` | bool | Cuál de los dos roles cumple. |

🔴 **`ApplyVariant` y `ApplyVariantMat` corren en el CONSTRUCTION SCRIPT**, no en BeginPlay. Es a propósito: hay que **ver las variantes lado a lado en el editor** para diseñar la elección. Si se aplicaran en runtime, autorarlas sería a ciegas.

💡 **El spawn por TargetPoint ya está resuelto en el proyecto** — no inventarlo. `BP_AttractDirector` (Touch) hace `GetAllActorsOfClassWithTag(TargetPoint, "BubbleSpawn")` y spawnea uno por punto; su tracker dice: *"para cambiar cuántas/dónde flotan se agregan o mueven TargetPoints, no se toca ningún Blueprint"*. **Copiar ese patrón con un tag propio** (ej. `SoulSpawn`).

## Registro de variables (comportamiento)
| Variable | Default | Rol |
|---|---|---|
| `DeadzoneDeg` | 10° | Zona muerta del lazy-follow. §5 pide ~10°. |
| `RecoverTime` | 1.0 s | Recuperación. §5 pide ~1 s. |
| `PitchDeg` | **−14°** | 🔴 **Negativo a propósito:** §5 dice *"ligeramente por debajo del horizonte (la mirada en reposo cae abajo; mirar arriba cansa)"*. |
| `Distance` | 95 cm | A qué distancia flota. |
| `PulseAmp` | 0.09 | Amplitud del pulso como fracción de escala. |
| `BaseScale` | 1.0 | Escala base. |
| `FallbackBPM` | 66 | Con qué late cuando no hay señal. |
| `FollowYaw` / `PulsePhase` | — | Estado interno. |
| `BioRef` / `CamRef` | — | Cacheadas en BeginPlay. |

## Estructura de grafos
- **`BeginPlay`** — `CacheRefs` (busca el BioHub) · `CacheCamera` (la cámara del pawn).
- **`Tick`** — `UpdateFollow(Δt)` · `ApplyPlacement()` · `UpdateReadout(Δt)`.
- **`UpdateFollow`** — 🔴 **sigue SOLO el yaw, nunca el pitch.** Si siguiera el pitch te la pondría siempre en la cara y dejaría de ser un objeto del mundo. Usa `Math|Rotator|NormalizeAxis` para tomar el camino corto (−180..180) y **solo se mueve si el error supera la zona muerta**.
- **`ApplyPlacement`** — posición = cámara + `forward(MakeRotator(PitchDeg, FollowYaw, 0)) × Distance`. El pitch es **fijo**, no interpolado: es lo que la mantiene debajo del horizonte sin importar dónde mires.
- **`UpdateReadout`** → `ReadFromBio` si hay BioHub, si no `ReadFallback`.
- **`ReadFromBio`** → 🔴 **si `bConnected` es false usa el fallback igual.** §5 pide que un módulo ausente **nunca se vea como error**: con el EEG desconectado `CalmSmooth` es 0, que significaría "agitación máxima" — una lectura alarmante y falsa. Mejor late tranquila.
- **`ApplyReadout(Calm, BPM, Δt)`** — la traducción de dato a forma:
  - `PulsePhase += Δt · (BPM/60) · 360` → **la fase avanza al ritmo real, no a un reloj fijo**.
  - escala = `BaseScale · (1 + PulseAmp·sin(fase))` → el pulso.
  - `Agitation = clamp01(1 − Calm)` → **invertido a propósito**: más calma, menos agitación.

## M_ProtoSoul (Core/Amoeba/Materials/)
Unlit · Opaque · `bFullyRough`. `emissive = SoulColor × Brightness × (0.35 + Fresnel + Agitation·sin(t·AgitationSpeed))`.
El **Fresnel** le da el borde encendido que la hace leer como algo vivo y no como una pelota. Opaco a propósito: la translucencia cuesta ~80 % más de GPU en Quest y acá no aporta.
Parámetros: `SoulColor` · `Brightness` · `Agitation` · `AgitationSpeed`.

## Verificado en PIE (2026-08-11)
- `BioRef` y `CamRef` resuelven a los actores correctos.
- `PulsePhase` avanzó a **372°/s ≈ 1,03 Hz ≈ 62 BPM**, que es exactamente el `HeartSmooth` que estaba dando el BioHub → **el pulso sigue la señal**, no un reloj.
- Posición (592, 0, **−22,4**) con la cámara en X≈500: **92 cm adelante y 23 cm por debajo** de la altura de la cámara. El "ligeramente por debajo del horizonte" es medible, no una impresión.
- `FollowYaw = 0` con la cámara a yaw 0 → la zona muerta no se dispara sola.

## TODO
- [ ] 🔴 **Test en visor.** El lazy-follow es de esas cosas que solo se juzgan con la cabeza puesta: la zona muerta y la recuperación se sienten, no se calculan.
- [ ] **Los anillos de carga** (§5: *"sus anillos son la carga"*). Uno por etapa completada, 5 en total. Va con `ChargeAnimation(índiceAnillo, intensidad)` del `BP_StageBase` (§9.4).
- [x] ~~**El flujo de elección**~~ → construido en [[BP_SoulChoice]] + [[BP_SoulState]] (2026-08-11). Falta cerrar su bug y probarlo en visor.
- [ ] Higiene de nodos de los 6 grafos nuevos: **están encimados en el origen**, nunca se les corrió `auto_layout.py`.
- [ ] La **agitación** hoy es un seno de brillo. §5 pide *"agitación de su superficie"*, o sea deformación real. Cuando haya mesh definitivo, evaluar World Position Offset (barato en vértices) antes que Niagara.
- [ ] Medir en device: es un objeto chico, debería ser gratis, pero el Fresnel + el seno corren por píxel.

## Relacionados
- [[BP_BioHub]] (de donde lee) · `BP_AttractDirector` (el patrón de spawn por TargetPoint) · `F_SoulPortrait` (**UserDefinedStruct**, el retrato de datos del usuario) · `BP_StageBase` (sin construir, va a pedir los anillos)
