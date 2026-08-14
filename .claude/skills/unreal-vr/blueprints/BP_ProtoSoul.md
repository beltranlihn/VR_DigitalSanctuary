# BP_ProtoSoul — la ameba, que ES el HUD (Core/Amoeba/)

## Purpose
§5: **el Proto Soul es la lectura.** Su **pulso** es tu ritmo, la **agitación de su superficie** es tu calma, sus **anillos** son la carga. Cero números, cero paneles, y es el objeto del que trata la obra.

🔴 **No es un HUD pegado al casco ni un reloj.** §5 descarta las dos: pegado al casco es incómodo y borroso en los bordes y rompe el lugar; reloj compite con el sensor que llevás en la mano.

## Status
🟡 Pulso y agitación verificados en PIE. 🆕 **2026-08-14: el rol HUD ya NO es lazy-follow — la ameba se ANCLA al slot del HUD** (decisión de Beltrán, guión). 🆕 **2026-08-14 (tarde): los ANILLOS y el VIAJE de la ceremonia construidos y verificados por log.** ⬜ Falta el test en visor y el arte de los anillos.

## 🆕 2026-08-14 (tarde) — LOS ANILLOS Y EL VIAJE (la ceremonia de carga vive acá)
La ameba es dueña de **su movimiento** y de **sus anillos**; quién y cuándo lo pide es de [[BP_Ceremony]].

### Los 5 anillos — componentes, no spawns
`Ring0..Ring4`: `StaticMeshComponent` con `/Engine/BasicShapes/Plane` + **`M_SoulRing`**, tag `SoulRing`, `bVisible=false`, sin sombra, `NoCollision`, `relativeRotation` **pitch 90** (el plano mira al usuario cuando la ameba está anclada con rotación cero a la cámara).
🔴 **Cuelgan de `Body`, NO del root**: así heredan `BaseScale` **y el pulso** — los anillos laten con la ameba y escalan con ella sin una sola línea extra. Su escala relativa se aplica en `ApplyRing` como `RingBaseScale + Index × RingScaleStep` (**2.0 / 0.35** → 30…51 cm de plano ≈ 23…39 cm de anillo dibujado, con la ameba en 15 cm).
- **`CollectRings`** (al final de `BeginPlay`) llena `RingComps` con los 5 getters de componente **explícitos** — a propósito, en vez de `GetComponentsByTag`, que pierde sus args en silencio (gotcha #2 de la cosecha 08-14). Verificado: `SOUL: anillos registrados = 5`.
- **`ShowRingAt(Index, Progress)`** — guard de rango contra AMBOS arrays (`RingComps` y `RingColors`) → `ApplyRing`.
- **`DrawRing(Index, Duration)`** — arranca el dibujado animado; `RingAdvance`→`RingStep`→`RingApply` avanzan `Progress` **0 → 1.05** en `RingDur` y `RingFinish` deja `RingsShown = Index+1`.
  ⚠ **El 1.05 no es un error**: con `Progress` exactamente 1.0 el último gajo del barrido angular nunca se enciende (el `saturate(Progress − angle01)` da 0 en la costura). El 5 % de más cierra el anillo.
- **`SeedRings(Count)`** — muestra los primeros `Count` anillos ya completos. La llama el salto debug del director (`SeedSoulRings`, con `DebugStartStage − 1`) para que una etapa saltada tenga los anillos de las etapas "ya vividas". Verificado: `SOUL: anillos sembrados = 2` al saltar a la etapa 3.
- **`HideAllRings`** — los apaga todos y pone `RingsShown = 0`.

### El viaje — la ameba se mueve sola, la ceremonia sólo la manda
- **`LeaveHud()`** — `DetachFromActor` con **los TRES rules en `KeepWorld`** (sin eso la ameba salta al desprenderse). ⚠ El tercero (`ScaleRule`) hubo que ponerlo por `set_pin_value`: el DSL se comió el 3er posicional.
- **`TravelToPoint(Target, Duration)`** / **`ReturnToHud(Duration)`** — cachean `TravelFrom` = posición actual y arrancan `bTraveling`. La vuelta pone `bReturnMode`.
- **`TravelGate(Δ)` → `TravelAdvance` → `TravelApply(A)` → `TravelFinish`** (colgados de `HudStep`, o sea del Tick gateado por `bIsHUD`):
  - suavizado **smoothstep** `A²(3−2A)` — arranca y frena suave, que es lo que pide "viaje suave".
  - **en modo vuelta el destino se RECALCULA cada tick** (`RefreshSlotTarget` → `SetSlotTarget`: `CamTransform.TransformLocation(AmebaOffset)`), así la ameba persigue el slot aunque el usuario mueva la cabeza durante el regreso.
  - al terminar, si es vuelta → **`BecomeHud()`**, que re-attachea. La aserción `VerifySoulPose` vuelve a dar **32,76 cm** — el ciclo cierra en el mismo punto donde empezó.
- 🔴🔴 **BUG PAGADO (y cazado por la aserción espacial): `TravelAdvance` sin gate corría desde `BeginPlay`** y hacía `SetActorLocation(Lerp(0,0,0 → 0,0,0))` cada frame → la ameba clavada en el origen del mundo. **`SOUL POSE: distancia a la camara cm = 3600.0`** (= la X exacta de la sala Loving) lo delató; el log de flujo decía "anclada al slot" y era verdad… por un frame. **De ahí sale `TravelGate`.** Es exactamente la trampa #13/#14 de la cosecha 08-14 otra vez: el attach informa éxito y otra cosa lo pisa.

### Variables nuevas
| Variable | Default | Rol |
|---|---|---|
| `RingComps` | [] | Los 5 componentes, en orden Ring0..4. |
| `RingColors` | 5 colores | 🎨 **azul (0.10,0.35,1) · rojo (1,0.12,0.12) · morado (0.55,0.15,1) · naranja (1,0.42,0.06) · verde (0.15,1,0.45)** — la lámina del guión. El anillo n usa `RingColors[n]`. **Cambiar el color de una etapa = tocar este array.** |
| `RingBaseScale` / `RingScaleStep` | 2.0 / 0.35 | Radio del primer anillo y cuánto crece cada uno (en espacio local de `Body`). |
| `RingIdx` / `RingElapsed` / `RingDur` / `bRingDrawing` | — | Estado del anillo que se está dibujando. |
| `RingsShown` | 0 | Cuántos anillos hay encendidos. Es la carga leída en la ameba. |
| `bTraveling` / `bReturnMode` | false | Si se está moviendo, y hacia dónde (punto fijo vs slot vivo). |
| `TravelFrom` / `TravelTarget` / `TravelDur` / `TravelElapsed` | — | Estado del viaje. |

### `M_SoulRing` (Core/Amoeba/Materials/)
Unlit · **Additive** · TwoSided · sin una sola textura. Anillo procedural sobre el plano:
`mask = saturate(1 − |dist(UV, centro) − Radius| / Thickness)` (caída triangular = borde blando gratis) × `sweep = saturate((Progress − angle01) × 40)` con `angle01 = atan2(dy,dx)/2π + 0.5`.
`Emissive = RingColor × Brightness`, `Opacity = mask × sweep` → **el anillo se DIBUJA girando**, no aparece de golpe.
Parámetros: `Radius` (0.38) · `Thickness` (0.055) · `Progress` (1.0) · `RingColor` · `Brightness` (3.0). Se escriben por componente con `SetColorParameterValueOnMaterials` / `SetScalarParameterValueOnMaterials` (crean el MID solos, cero variables MID).

## 🆕 2026-08-14 — ANCLADA AL SLOT DEL HUD (reemplaza el lazy-follow)
- **API: `BecomeHud()`** — `bIsHUD=true` → `ReadAmebaAnchor` → `AttachHudMode` (attach **DIRECTO al CameraComponent del pawn** — nunca a padres escalados, gotcha #13 — con `AmebaOffset` + rotación cero). La llaman `SpawnHudSoul` del Hall y `SeedSoul` del salto debug.
- **El offset se autora con `TP_AmebaAnchor`** (tag `AmebaAnchor`, en el persistente junto al cubo, hoy (−2205, 13, 162) = cubo + (30, 13, 2) ≈ el círculo del slot del WBP). Arrastrarlo mueve dónde vive la ameba en el HUD.
- 🔴 **`AmebaOffset` = TP − `HeadRefLoc` DEL BP_SoulHUD (valor cacheado), NUNCA el cubo vivo**: cuando la ameba lee, el cubo ya está pegado a la cámara (gotcha #14 — así salió a 184 cm). Fallback sin HUD: (0,0,185).
- **`HudStep` quedó VACÍO** (el attach reemplaza a `UpdateFollow`+`ApplyPlacement`, que quedaron como funciones muertas — borrarlas cuando se confirme en visor). `UpdateReadout` (pulso/agitación) sigue corriendo para todas.
- **Aserción espacial permanente: `VerifySoulPose`** (1 s tras el attach) — verificado **32,76 cm = |(30,13,2)| exacto**.
- ✅ **La ceremonia de carga ya existe** (2026-08-14 tarde): TargetPoints `ChargeSpot` dentro de cada `L_Room_*` y la secuencia detach → viaje → anillo+carga → `BecomeHud()`. La orquesta [[BP_Ceremony]]; la ameba pone `LeaveHud`/`TravelToPoint`/`ReturnToHud`/`DrawRing`/`SeedRings`.

## 🆕 Lo que se agregó el 2026-08-11 (para la elección del Hall)
| Función | Rol |
|---|---|
| `ConfigureVariant(Id, Mesh, Mat, Color)` | 🔴 **La API pública de la variante.** El Construction Script sirve para autorar en el editor, pero una candidata **spawneada** necesita configurarse en runtime, y el CS no vuelve a correr. Setea las 4 variables y aplica las tres cosas. |
| `ApplyVariantColor()` | Aplica `SoulColorOverride` al parámetro `SoulColor` del material, **gateado por `bUseColorOverride`**. Ese bool es el flag que distingue "color negro" de "sin override": sin él, el default (0,0,0) apagaría la ameba. |
| `AdoptFromState()` / `AdoptStep(St)` | Lee [[BP_SoulState]] (el GameInstance) y, **si `bHasChosen`**, se configura con la elección. Corre en `BeginPlay`, así que **la identidad elegida sobrevive a los cambios de nivel** sin que nadie la reenvíe. |
| `TickStep(Delta)` / `HudStep(Delta)` | 🔴🔴 **El Tick ahora está gateado por `bIsHUD`.** `UpdateReadout` (pulso y agitación) corre en **todas** — las candidatas del Hall también laten, y eso es deseable: se ven vivas. Pero `UpdateFollow` + `ApplyPlacement` corren **sólo en el HUD**. Sin ese gate, cada candidata se pegaría a la cámara y se apilarían todas encima. |

⚠ **`SoulColorOverride` era dato muerto hasta hoy**: existía la variable y el parámetro del material, pero nada las conectaba. Es el caso típico de "declarado ≠ aplicado".

## 🐛 2026-08-12 — dos bugs que sólo aparecieron con el visor puesto
Beltrán probó y reportó: *"hay una esfera enorme pulsando al frente, y hay otra enorme pulsando al medio de cada sala"*. Eran **dos causas distintas** que se veían como una:

1. **`BaseScale` estaba en 1.0** → esferas de **1 metro**. Ver la tabla de variables. Ahora 0.15.
2. 🔴🔴 **`bIsHUD` estaba en `false` en la INSTANCIA de `L_Persistent`** (el CDO decía `true`). Como el Tick está gateado por ese bool, **la ameba HUD no seguía la mirada**: se quedaba clavada en el origen, o sea en el centro de la sala. Es el mismo caso de siempre — **las variables instance-editable se serializan como override y no heredan el default del CDO** — y acá fue especialmente insidioso porque el bool se agregó *después* de colocar el actor, así que quedó fijado en false.
   💡 **Cómo se verificó el arreglo sin visor:** con PIE corriendo, `find_actors` + `get_actor_transform` sobre la ameba. Antes daba `(0,0,0)` (clavada); ahora da `(80, 0, −23)`, o sea 92 cm delante de la cámara y 23 cm debajo de su altura → `ApplyPlacement` **corre**. Medirlo es mejor que mirarlo.
3. Lo que se veía "al medio de cada sala" eran **las 3 candidatas de [[BP_SoulChoice]]**, de 1 m cada una y separadas 30 cm → superpuestas parecen **una sola** esfera enorme. Y como viven en el nivel **persistente** y todas las salas están en el origen, aparecían en **todas** las salas. Se apagaron con el gate `bSpawnOnBeginPlay`.

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
| `BaseScale` | **0.15** | 🔴 **El tamaño real de la ameba, y NO se autora en el componente.** `ApplyReadout` hace `SetRelativeScale3D(Body, BaseScale·(1+PulseAmp·sin))` **cada frame**, así que la escala que se ponga a mano en el componente se pisa. La esfera básica del motor mide **100 cm**, por lo tanto `BaseScale` es directamente el diámetro en metros: 0.15 = **15 cm**. Estaba en **1.0** = una pelota de 1 m a 95 cm de la cara (reportado en visor el 2026-08-12 como *"una esfera enorme pulsando al frente"*). |
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
- [x] ~~**Los anillos de carga**~~ (§5: *"sus anillos son la carga"*) → construidos 2026-08-14: `Ring0..4` + `M_SoulRing` + `DrawRing`/`SeedRings`. Falta el **arte** (hoy es un anillo procedural liso) y verlos en visor.
- [x] ~~**El flujo de elección**~~ → construido en [[BP_SoulChoice]] + [[BP_SoulState]] (2026-08-11). Falta cerrar su bug y probarlo en visor.
- [ ] Higiene de nodos de los 6 grafos nuevos: **están encimados en el origen**, nunca se les corrió `auto_layout.py`.
- [ ] La **agitación** hoy es un seno de brillo. §5 pide *"agitación de su superficie"*, o sea deformación real. Cuando haya mesh definitivo, evaluar World Position Offset (barato en vértices) antes que Niagara.
- [ ] Medir en device: es un objeto chico, debería ser gratis, pero el Fresnel + el seno corren por píxel.

## Relacionados
- [[BP_BioHub]] (de donde lee) · `BP_AttractDirector` (el patrón de spawn por TargetPoint) · `F_SoulPortrait` (**UserDefinedStruct**, el retrato de datos del usuario) · `BP_StageBase` (sin construir, va a pedir los anillos)
