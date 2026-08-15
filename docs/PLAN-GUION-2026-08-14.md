# Plan vigente: el guión → construcción (2026-08-14)

> **Fuente autoritativa del QUÉ:** [`Soul-Charger-Script-2026-08-14.pdf`](Soul-Charger-Script-2026-08-14.pdf) — el guión segundo-a-segundo de Beltrán (8 actos, audio, haptics, simultaneidades). Este plan lo mapea contra lo construido y fija el orden. Reemplaza como plan activo a [`PLAN-2026-08-13.md`](PLAN-2026-08-13.md) (cuyas 11 decisiones siguen vigentes salvo lo que acá se supersede).
> **La palanca de iteración ya existe:** `DebugStartStage` en el director (−1 obra completa · 0..5 salto directo a la etapa por el flujo real, ~2,6 s). Cada pieza de este plan se testea con ella.

---

## 0. 🔴 Las 9 decisiones del guión (cerradas con Beltrán, 2026-08-14) — no se re-discuten sin él

| # | Tema | Decisión |
|---|---|---|
| 1 | **Señal de calma** | **EEG por OSC, normalizada 0–1** (dispositivo externo; Beltrán define la dirección OSC). Alimenta el gráfico del HUD, los Niagaras de Loving y la data del gráfico final. **También llega ritmo cardíaco por OSC** (ya probado: test 75.5). |
| 2 | **Loving "sin sensor"** | Significa **sin sensores de mano**: es pura observación. Los 3 Niagaras aditivos (timeados por VO 16/17/18 + SMind 1-3) se **intensifican/calman con la señal de calma EEG**. |
| 3 | **Selección de proto ameba** | **Hover + trigger.** El hover **agranda** la candidata para observarla (tienen geometrías y colores distintos); se puede hovear varias antes de decidir. Sonidos SProtoHover/SProtoselect + haptic sutil/fuerte. |
| 4 | **El timbre NO lleva trigger** | Solo posar la mano: se agranda al hover, vibración háptica continua durante el hold, y un **ring slider** alrededor del cilindro se carga 0→100 (SBell durante la carga, STrigger + pulso fuerte al completar). |
| 5 | **Cierre de Surrounding** | Por **metros acumulados de trazo** (no número de trazos). |
| 6 | **Límite de dibujo** | **Esfera traslúcida** (no círculo punteado): se dibuja en 3D alrededor de la proto ameba y sus anillos (se puede hacer un cascarón). **Al invadir el interior de la esfera, la línea se afina en punta y desaparece.** |
| 7 | **Pool de Attracting** | El clip base (+ pack de sonidos de objetos) **cambia aleatoriamente con cada jugador**, y está **sincronizado con el secuenciador desde la entrada** a la sala (Quartz, mismo BPM desde el primer fade in). |
| 8 | **Audio** | Beltrán pasa los archivos **después**. Se construye TODA la maquinaria ya (crossfades, triggers, haptics) con **placeholders data-driven**: entrada vacía = silencio + log `AUDIO: falta clip X` (patrón `ModeMeshes`: el dato faltante no rompe nada). Reemplazar sonidos = llenar arrays, cero código. |
| 9 | **El HUD es un actor NUEVO** + **gráficos finales por promedio de etapa** | `BP_SoulHUD`: sigue la cabeza (hereda ese trabajo del `BP_ProtoSoul` actual) y lleva 5 elementos propios + **slot** donde se ancla la proto ameba. Los gráficos del final muestran **promedios por etapa** de las señales OSC (calma EEG, ritmo; registrados durante toda la obra). |

---

## 1. Los sistemas transversales nuevos (atraviesan toda la obra — se construyen primero)

### 1.a 🆕 `BP_SoulHUD` — el HUD con gráficos en tiempo real
Actor nuevo (Core/), sigue la cabeza. Nace **animado, elemento por elemento, durante la calibración del Hall** (acto 3) y muere animado en la carga final de Surrounding ("nos hemos desprendido de él").
| Elemento | Dato | Nota |
|---|---|---|
| Gráfico de calma en tiempo real | EEG OSC 0–1 | La misma señal que Loving y el gráfico final |
| Círculo pulsando al ritmo cardíaco | BPM OSC | |
| Barra de carga del Soul | +20% por etapa (la ceremonia la sube) | |
| Círculo/slot transparente de la proto ameba | — | Ahí se ancla la elegida; de ahí se desprende en cada ceremonia |
| Punto de sensor conectado | ¿llegan paquetes OSC? | Verde/rojo por timeout de recepción |

El `BP_ProtoSoul` deja de seguir la cabeza por su cuenta: **la ameba se monta en el slot del HUD**.

### 1.b 🆕 La ceremonia de carga — UN sistema, corre 5 veces + el final
Secuencia reusable (función/actor invocado por el cierre de cada etapa, antes de la puerta):
```
proto ameba se desprende del HUD → se posiciona al frente → VO de felicitación
+ (SCharger) + anillo de color de la etapa se dibuja alrededor + barra del HUD sube a n×20%
→ al terminar, vuelve suave al slot del HUD con sus anillos acumulados
```
Colores de anillo por etapa (de la lámina del guión): Entering **azul** · Recognizing **rojo** · Loving **morado** · Attracting **naranja** · Surrounding cierra con la **carga final** (100%, HUD se disuelve). Datos: color, % objetivo, VO — todo por etapa, la secuencia es la misma.

### 1.c 🆕 `BP_BioHub` ampliado — las señales OSC y el registro
- Entradas: **EEG calma 0–1** (dirección OSC a definir por Beltrán) + **BPM** (ya existe). Punto de conexión = timeout de paquetes.
- **Registro de promedios por etapa**: acumulador (suma/conteo) que el director resetea en cada `EnterRoom` y vuelca al cerrar la etapa → GameInstance → SaveGame al final. Es la data del gráfico de resultados.

### 1.d 🆕 Audio + haptics framework (placeholders desde el día 1)
- **Ambients**: 8 clips en loop, uno por tramo (mapa data-driven sala→clip), **crossfade en cada transición de puerta** (fade out del actual + fade in del siguiente, disparado junto al `WalkOut`/`EnterRoom`). Attracting usa su pool aleatorio vía Quartz.
- **SFX**: catálogo por nombre (STitle, SBubble, SSelect, SPasos, SBell, STrigger, SDoor, SDoorReveal, SExplicación, SCalibration, SProtoHover, SProtoselect, SCountBreath, SCharger, SPulse, SMind 1-3, SDraw, SChargerFinal, SProtoHeart, SCredits). Entrada vacía = silencio + log.
- **VOs**: 30 archivos; los tiempos del guión se cuelgan de la **duración del clip** (variable), nunca hardcodeados (regla ya vigente para la intro).
- **Haptics**: 3 patrones reusables — **hover** (pulso muy suave, entrada y salida) · **selección** (pulso fuerte) · **hold** (vibración continua, la del umbral). Pasos con SPasos acoplado a la cadencia del walker.
- ⚠ `audio-quest.md` antes de tocar config: el bloque de audio del ini está bajo `WindowsTargetSettings` (el APK no lo lee); Quartz corre en Android por construcción; codecs ADPCM/Bink.

---

## 2. Mapeo por acto: beat → estado → dónde vive

Leyenda: ✅ construido (ajuste fino) · 🔧 rework de lo existente · 🆕 nuevo

### Acto 1 — Intro App
| Beat | Estado | Nota |
|---|---|---|
| Fade desde negro al vacío azulado con partículas + Ambient Clip 1 | ✅ | El fade inicial hoy es negro instantáneo → pasa a fade in |
| 3 logos → título (STitle) → Start/About | ✅ | `BP_IntroSequence`; faltan PNGs |
| About → ventana descripción + volver | ✅ | Texto real pendiente (inglés) |
| Hover de botones: SBubble + pulso suave + **agrandado** · trigger: SSelect + pulso fuerte | 🔧 | Receta de hover/escala en `BP_SaveButton`; sumar sonido+haptic |

### Acto 2 — Intro Soul
| Beat | Estado | Nota |
|---|---|---|
| Start → botones y título se desvanecen · crossfade Ambient 1→2 | ✅/🆕 | Kill del menú existe; crossfade nuevo (1.d) |
| Caminata lenta por el vacío + VO 1 (preguntas de mood) | ✅ | Tramo 0; duración = duración del VO |
| **Oscurecimiento gradual**: partículas y fondo azulado se van MIENTRAS avanzamos; empiezan los pasos (SPasos) | 🔧 | Hoy las partículas se apagan de golpe al llegar; pasa a rampa durante el tramo |
| Puerta visible en la oscuridad, nos detenemos a metros; timbre | ✅ | Paradas 1 + `BellSpawn` |
| Timbre: agrandado al hover + SBubble + pulso · hold = vibración continua + SBell + **ring slider 0→100** | 🔧 | El hold ya funciona; falta ring slider visual + audio + haptics (decisión #4) |
| Carga completa: STrigger + pulso fuerte, desaparece, puertas abren (SDoor), caminamos adentro · crossfade 2→3 | ✅ | Ya construido el flujo; sumar sonidos |

### Acto 3 — Recepción (Hall)
| Beat | Estado | Nota |
|---|---|---|
| Al traspasar la puerta aparece Alma + VO 2 bienvenida | ✅ | Alma viajera; afinar el timing "mientras cruzamos" |
| VO 3 explicación + 🆕 **animación de etapas**: 5 nombres en gris + ameba; cada nombre se colorea y su anillo aparece al nombrarse (SExplicación) | 🆕 | Lámina p.2 del guión: pills Entering/Recognizing/Loving/Attracting/Surrounding + ameba con anillos de colores |
| VO 4: tomar el sensor → calibración: Niagara de anillos alrededor (SCalibration) + **el HUD nace animado** | 🔧/🆕 | Toma del sensor ✅ (any-hand + STrigger/SBubble/haptic); anillos + HUD nuevos (1.a) |
| VO 5: elegir proto ameba — **hover (agranda + SProtoHover + pulso) / trigger (SProtoselect + pulso fuerte)** | 🔧 | Cambia de toque a hover+trigger (decisión #3); candidatas ✅ |
| Las demás desaparecen; la elegida al frente + VO 6 → se ancla al **slot del HUD** | 🔧 | La persistencia en GameInstance ✅; el anclaje pasa al HUD |
| VO 7: Alma "desaparece achicándose" · puerta a Entering (SDoorReveal/SPasos/SDoor) · crossfade 3→4 | ✅ | Ciclo de transición; sumar el achicado de Alma + sonidos |

### Acto 4 — Entering
| Beat | Estado | Nota |
|---|---|---|
| Alma en su posición + VO 8 · widget de instrucciones | ✅ | 🔧 sumar **auto-avance de página a los 20 s** (cortafuego) |
| 🔧🔧 **La mecánica ya NO cierra por conteo**: aparece el objeto + **radial slider** de timing (4 inhala / 4 aguanta / 4 exhala × 5; test con 2) + SCountBreath + VO 9. El usuario controla el objeto en tiempo real; el timing avanza solo | 🔧🔧 | Muere `MaxBreathCount`/auto-cierre del sensor. El radial slider ya existe en el widget de Calibration → reusar. El sensor de respiración sigue moviendo el objeto |
| Ceremonia de carga (anillo azul, 20%) + VO 10/11 · puerta · crossfade 4→5 | 🆕 | Sistema 1.b |

### Acto 5 — Recognizing
| Beat | Estado | Nota |
|---|---|---|
| Alma + VO 12 · widget instrucciones | ✅ | |
| 🔧🔧 **La subida por pulsos**: umbral (sensor al pecho) ✅; al entrar: pulso háptico al corazón + SPulse **a ½ del BPM real (OSC)**; **10 saltos de igual extensión** con curva trampolín (rápido→lento); anillo Niagara desde el corazón por pulso; fuera del umbral el avance sigue lento (no se detiene); reentrar re-activa | 🔧🔧 | Reemplaza `MaxBeatCount` y el descenso continuo actual de las columnas. El recorrido total es fijo: 10 saltos |
| Ceremonia (anillo rojo, 40%) + VO 13/14 · puerta · crossfade 5→6 | 🆕 | |

### Acto 6 — Loving
| Beat | Estado | Nota |
|---|---|---|
| Alma + VO 15 · **SIN widget de instrucciones** | 🔧 | |
| 🔧🔧 **3 Niagaras aditivos** timeados: VO16+SMind1→N1 · VO17+SMind2→N2 (N1 sigue) · VO18+SMind3→N3 · al terminar VO18 desaparecen todos. **Intensidad modulada por la calma EEG** | 🔧🔧 | Reemplaza las 3 preguntas en TextRender. Sin sensores de mano. ⚠ `niagara-quest.md`: QualityLevel clampeado en Android, parámetros por `SetNiagaraVariableFloat` (ojo nombre fantasma) |
| Ceremonia (anillo morado, 60%) + VO 19/20 · puerta · fade out 6 → **fade in Attracting Base (pool aleatorio)** | 🆕 | |

### Acto 7 — Attracting
| Beat | Estado | Nota |
|---|---|---|
| Attracting Base ya en loop al entrar, **sincronizado por Quartz con el secuenciador** · clip + pack por jugador (pool aleatorio) | 🆕 | Decisión #7 |
| Alma + VO 21 · widget instrucciones | ✅ | |
| Al terminar: beams + slots + botón + objetos flotantes aparecen uno a uno | ✅ | Todo probado en visor |
| Cierre: guardar melodía o cortafuego | ✅ | FINISH MELODY probado; falta el SaveGame (R6, ahora parte del final) |
| 🔧 **Coda**: desaparecen beams/slots/no-elegidos; **los elegidos se alinean al frente y suenan 2-3 vueltas** + VO 22; luego desaparecen, el pad sigue | 🔧 | Nuevo tramo entre el cierre y la ceremonia |
| Ceremonia (anillo naranja, 80%) + VO 23 · puerta · fade out pad → fade in Ambient 7 | 🆕 | |

### Acto 8 — Surrounding + Final
| Beat | Estado | Nota |
|---|---|---|
| Alma + VO 24 · widget instrucciones | ✅ | |
| 🔧 La proto ameba se desprende y se posiciona **a distancia/tamaño de dibujo** (algo más grande que un balón); mecánica de dibujo alrededor con **esfera traslúcida de límite** — invadirla afina la línea en punta y la corta; SDraw al dibujar; cierre por **metros acumulados** | 🔧 | `BP_BrushTool`/`BP_DrawCanvas` ✅; el lienzo pasa a ser alrededor de la ameba; decisiones #5/#6 |
| 🆕 **La carga final** (todo simultáneo, "totalmente impactante"): VO 25 · ameba crece y se aleja · Niagaras de carga (vortex, partículas) · anillos girando · barra a 100% · **HUD se disuelve animado** · SChargerFinal · la arquitectura se deshace tipo transformer → exterior | 🔧/🆕 | `Dissolve()` ✅ como base; el resto nuevo |
| 🆕 Exterior: fade out 7 → **suena NUESTRA melodía** · gráficos de resultados bajo la ameba (promedios por etapa: calma, ritmo, respiración) + VO 26 | 🆕 | Data del registro 1.c |
| 🆕 VO 28: decidir **incorporarla al corazón y compartirla**: tomarla y atraerla al pecho → SProtoHeart + explosión Niagara → **constelación de amebas de usuarios anteriores** aparece · melodía → Ambient 8 · la proto viaja como estrella fugaz a su lugar | 🟡 | ✅ **La persistencia y la constelación ya existen** (`BP_SoulArchive` + `BP_Constellation`, 2026-08-15, round-trip de disco verificado; posiciones por TargetPoints `ConstSpot` movibles a mano). ⬜ Falta el gesto — ver la fila de abajo. |
| 🔴 **CÓMO SE TOMA LA AMEBA (decisión de Beltrán, 2026-08-15)**: *"nuestra protoameba tiene que estar **frente a nosotros al alcance de la mano**, y tenemos que **tomarla con hover + trigger**, y ahí podemos moverla hasta nuestro corazón"* | 🆕 | **Hover = proximidad de la mano, NO láser** (está al alcance del brazo). Lo que hay para reusar: el **attach por cercanía de `BP_BrushTool`**, que está **probado en visor** (*"acercar cualquiera de las dos manos → se pega"*) — sirve como detector de hover; y el **gatillo con la config que SÍ funciona** (`IA_Continue` + `IMC_Continue`, `Priority=1000` + `bIgnoreAllPressedKeysUntilRelease=False` + `bForceImmediately=True`; los defaults suprimen el input). ⚠ `IA_Grab_*` del XRFramework **existen pero están sin mapear**, y `C_GrabComponent` es un patrón de `Recursos/` que **no está integrado**: no asumir que andan. Al soltar en el pecho → `SProtoHeart` + Niagara + `AppendMe` + viaje a su TargetPoint. |
| 🆕 VO 29 · **beams para explorar**: hover sobre una ameba = suena SU melodía · tiempo de exploración → fade a negro · VO 30 gracias · SCredits + créditos · reload del nivel y vuelve a empezar | 🆕 | El beam ✅ existe (Attracting); el hover-melodía es nuevo |

---

## 2.b Avance (2026-08-14, misma jornada)
- ✅ **BioHub**: las 3 señales OSC del server de Beltrán definidas (int 0/1 sensor · float calma 0–1 @60 Hz · float BPM numérico) + camino de enteros nuevo + **simulación LFO encendida** (`bFakeSignal` en la instancia; apagarla cuando llegue el server real). Direcciones como variables (`/calm`, `/hr`, `/sensor` — Beltrán confirma las finales).
- ✅ **`BP_SoulHUD` v2 FUNCIONANDO (confirmado por Beltrán en editor y Play)**: HUD físico **UMG** (`WBP_SoulHUD`, diagramación de la lámina del guión) con **onda EEG real** (OnPaint+DrawLines, corre de derecha a izquierda, buffer 48 muestras), pulso al BPM, barra de carga vertical (`SetCharge`), slot y punto de sensor. **Attach DIRECTO a la cámara del pawn** (nunca a padres escalados — gotcha #13) con offset autoral por `TP_HudAnchor` vs cubo de cabeza; preview `bEditorPreview` en el nivel; aserción espacial permanente `VerifyHudPose` (30 cm verificados). Integrado al salto debug (`SeedHud`) y al arranque (`bDebugHudAlways`, andamiaje hasta que la calibración del Hall lo haga nacer). Falta: visor con casco, nacimiento/muerte animados, anclar la proto ameba al slot, arte.

- ✅ **La proto ameba ANCLADA al slot del HUD (2026-08-14, cierre — validado por Beltrán)**: `BecomeHud()` en `BP_ProtoSoul` (fuera el lazy-follow), offset autoral por **`TP_AmebaAnchor`** (arrastrable, como el del HUD), attach directo a la cámara. La llaman el Hall (`SpawnHudSoul`) y el seed del salto debug. Verificado: 32,76 cm exactos.
- ✅ **LA CEREMONIA DE CARGA (1.b) CONSTRUIDA Y VERIFICADA POR LOG (2026-08-14, tarde)** — el sistema que cierra las 5 etapas:
  - **`ChargeSpot`**: un `BP_Anchor` (hereda de `TargetPoint`, invisible en juego) tagueado `ChargeSpot` **dentro de cada `L_Room_*`**, en `(salaX + 110, 0, 140)`. Moverlo = arrastrarlo en el mapa de la sala, cero código. Sin él no hay callejón sin salida: `FallbackSpot` usa un punto frente a la cámara y **loguea que falta**.
  - **`BP_Ceremony`** (Core/Flow/, actor colocado en `L_Persistent`): `LeaveHud` → viaje 2,2 s → anillo 2,6 s **+ barra subiendo en paralelo** → 1,2 s de contemplación → vuelta 2,0 s → `BecomeHud()`. **Total ≈ 8,3 s.**
  - **Los anillos viven en `BP_ProtoSoul`** (`Ring0..4` + material procedural `M_SoulRing` con barrido angular), colgados de `Body` para heredar escala y pulso. Colores por `RingColors` (azul/rojo/morado/naranja/verde). **Se acumulan**; el salto debug los siembra con `SeedRings(DebugStartStage−1)`.
  - 🔴 **El director NO conoce la ceremonia**: publica `CeremonyRequest` y ella avisa con `CeremonyDone`; cortafuegos de 25 s. Enganche: `EndStage → KillStage → MaybeCeremony → (ceremonia) → AfterCeremony → DimAndReveal…`
  - **Audio**: `VoClips` (array por etapa) y `ChargeSfx` vacíos = silencio + `AUDIO: falta clip ...`. Llenar el array = tener audio, cero código (decisión #8).
  - Verificado 3 corridas con `DebugStartStage=3`, aserción espacial ameba↔ChargeSpot = **0.0 cm** y vuelta al slot a **32,76 cm**, cero `Accessed None`. Detalle: [`blueprints/BP_Ceremony.md`](../.claude/skills/unreal-vr/blueprints/BP_Ceremony.md).
- ✅ **ACTO 4 — ENTERING REWORKEADO (2026-08-14, noche)**, verificado por log de punta a punta:
  - 🆕 **`BP_BreathPacer`** (Stages/Breath/): el **ritmo guiado**. Anillo world-space (reusa `M_SoulRing`) + `TextRender` INHALE/HOLD/EXHALE que marcan **4/4/4 × 5** y **avanzan solos**. Medido: **11,95 s por ciclo**, 5 ciclos. Posición autorable con `TP_PacerSpawn` dentro de `L_Room_Entering` (1310, 0, 165).
  - 🔧🔧 **Muere el cierre por conteo**: `CheckBreathHit` de la etapa pasó de preguntar `bStageComplete` a `bCountingEnabled` (= "arrancó el ejercicio") y el cierre lo pide el pacer (`PacerFinished` → `BreathComplete` → `StageDone`). En el sensor, `CompleteBreathStage` quedó detrás de **`MaybeCompleteBreath` + `bAutoComplete=false`**: el conteo y su háptico siguen vivos, pero **ya no cierran ni esconden el sensor**.
  - 🔧 **Cortafuegos de página a los 20 s** en `BP_Instructions` (`PageFirewall` + `ForcePage`, insertado por cirugía en el Tick). Verificado: página 0→2 a los 20 s exactos, 2→3 a los 40. ⚠ Forzar la **página 2** deja el sensor sin calibrar — es el precio de no tener callejones sin salida.
  - **Encadenado con la ceremonia**: al cerrar, `carga = 0.2` y **anillo 0 (azul)**, `anillos acumulados = 1`. Cero `Accessed None`.
- ✅ **ACTO 5 — RECOGNIZING REWORKEADO (2026-08-14, noche)**: la subida ahora es **UN valor `Progress` 0→1** en `BP_Descent`, con dos caminos que **los dos llegan**: en umbral, cada latido a ½ BPM dispara un **salto de 1/10 con curva trampolín** (ease-out `1−(1−a)²`, 1,1 s); fuera del umbral, **drift lento continuo** (0,012/s ≈ 83 s). Muere `MaxBeatCount` como cierre (el `FinishAfterDelay` del sensor —que **recargaba el nivel**— quedó tras `MaybeFinishHeart`+`bAutoFinish=false`). Verificado por log el camino del drift + ceremonia al 40 % con anillo rojo; **los 10 saltos necesitan casco**. 🧪 **`DriftRate` puesto en 0,1 = recorrido completo en 10 s** (pedido de Beltrán, para iterar rápido); **el valor de obra es 0,012 ≈ 83 s** y hay que restaurarlo antes de juzgar el ritmo: con 0,1 el drift es más rápido que los saltos y la mecánica se invierte. Detalle: `blueprints/BP_Stage_Subclases.md` §Recognizing v4.
  ⬜ Falta de este beat: el **anillo Niagara desde el corazón por pulso** (capa VFX, el hook es `PulseJump`), el clip **SPulse**, y el cortafuegos de página de 20 s en `BP_HeartInstructions` (Breath ya lo tiene).
- ✅ **ACTO 3 — LA EXPLICACIÓN DE ETAPAS DEL HALL (2026-08-15)**: el punto 1 del memo de visor. **`BP_StageIntro` + `WBP_StageIntro`** (`Core/UI/`), colocado en `L_Room_Hall` en (230,0,140) yaw 180.
  - El widget es **sólo la columna de 5 píldoras cápsula** con los nombres en inglés y la paleta de la lámina p.2 (azul·rojo·morado·ámbar·verde). 🔴 **La ameba y los anillos NO son dibujos de UI: son un `BP_ProtoSoul` REAL** spawneado al lado, con los mismos `Ring0..4` y el mismo `M_SoulRing` de la obra — decisión explícita de Beltrán (*"que sean reales, tal como las usamos en el world"*). La primera versión los tenía dentro del widget y se descartó.
  - Ritmo por `StepTime` (4 s) y `RingTime` (1,6 s), instance-editable: **la animación la termina de timear Beltrán**. `IntroPlay` es la API pública para cuando el Hall la dispare con el VO (`bAutoPlay=false`).
  - Todo se autora **moviendo transforms**: el actor (posición/rotación/escala de la composición), `Panel` (el texto), `SoulAnchor` (dónde y **de qué tamaño** la ameba — el spawn usa `GetWorldTransform` completo).
  - Verificado por log: 5 píldoras, ameba a **0,0 cm de su anchor** (medido 1,5 s DESPUÉS del spawn), etapas 0·1·2·3·4 y cierre. **Cero `Accessed None`.** ⬜ Falta visor. Detalle: `blueprints/BP_StageIntro.md`.
- ✅ **ACTO 6 — LOVING REWORKEADO (2026-08-15)**: mueren las 3 preguntas en TextRender; entran los **3 campos de luz**.
  - **`BP_LovingField`** (`Core/VFX/`) = UN campo. Se colocaron **tres en `L_Room_Loving`**, distinguidos por `FieldIndex` 0·1·2. `BP_Stage_Loving` los busca por clase (`GetAllActorsOfClass`) y enciende el que toca en cada beat; **los anteriores siguen encendidos**, como pide el guión, y al terminar el beat 3 se apagan todos juntos.
  - **La calma del EEG los modula POR FRAME (≈60 Hz)**: `efectivo = Intensity × (0,35 + 0,65 × Calm)`. El piso de 0,35 es deliberado — con el EEG desconectado el campo baja pero **no desaparece** (un módulo ausente nunca se ve como error).
  - 🔴 **Decisión de Beltrán (2026-08-15): el bombeo va a 60 Hz, no a 10.** *"el OSC nos va a estar llegando a sesenta hertz… si después yo quiero mapear esa data al curl noise o a distintos efectos dentro del Niagara, es mucho más notorio y suave a sesenta que a diez o treinta"*. Implementado colgando `PumpCalm` del **Tick** de la etapa (en el target un frame es 1/60 s, así que da el ritmo exacto del OSC sin desfasarse contra el frame; un timer de 0,0167 s sí se desfasa). Se agregó **`CalmParam`** al campo, que escribe la **calma cruda sin la curva de intensidad** — ése es el hook para el curl noise —, y **`bUseRawCalm`** en la etapa para elegir entre `Calm` crudo y `CalmSmooth`.
  - **El Niagara y los nombres de sus parámetros son DATOS.** `ProbeParams` pregunta en BeginPlay si el sistema expone `Intensity`/`FieldColor` (pin `bIsValid` de `GetNiagaraVariable`) y sólo escribe lo que existe → **el arte real entra sin tocar un nodo**. 🔴 Hoy el placeholder es `NS_VoidDust`, que **no expone ningún parámetro** (medido con `GetSystemSummary`: `userVariables` vacío), así que la única palanca viva es la escala del componente, y el log lo dice explícitamente en vez de fingir.
  - **Timing autorable**: `BeatTimes` [12, 12, 14] s y `FieldFade` 3 s, instance-editable — es la palanca para calzar con VO 16/17/18. VO y SMind son placeholders data-driven (vacío = silencio + log), como en la ceremonia.
  - Verificado por log (`DebugStartStage=3`): 3 campos, beats a 0/12/24 s, apagado a los 38 s, cierre a los 41,5 s y **ceremonia encadenada con anillo morado y carga 0.6**. Cero `Accessed None`. ⬜ Falta visor y el arte.
- ✅ **LA PERSISTENCIA MULTI-USUARIO Y LA CONSTELACIÓN (2026-08-15)** — arranca el camino al end-to-end que pidió Beltrán (*"llegar incluso a compartir mi ameba cargada con el resto de la constelación"*).
  - **`BP_SoulArchive` + `SG_Constellation`**: SaveGame con **6 arrays paralelos** (variante, color, anillos, promedio de calma, promedio de ritmo, melodía como string), **una entrada por usuario**, con tope y recorte por el frente. `AppendMe` agrega la mía y persiste. 🟢 **Round-trip de disco verificado**: la corrida 2 leyó lo que guardó la 1.
  - **`BP_Constellation`**: spawnea una `BP_ProtoSoul` por ameba guardada **en TargetPoints tagueados `ConstSpot`**, con el **transform completo** de cada punto — pedido explícito de Beltrán: *"así yo también puedo mover a mano dónde quiero que aparezcan"*. Verificado: nacieron con la escala 0.6 del punto. 12 puntos colocados de arranque; si faltan puntos lo **loguea** en vez de truncar en silencio.
  - ⚠ **`F_SoulPortrait` estaba vacío** (sólo un placeholder) y el MCP **no puede agregar miembros a un UserDefinedStruct** → de ahí los arrays paralelos.
- 🔜 **PRÓXIMO PASO — el tramo del medio del final** (lo único que separa el end-to-end de la constelación): **`BP_Finale`** = carga al 100 % + disolución del HUD → la ameba se desprende, crece y se aleja → exterior; y **la decisión del corazón** (llevarla al pecho → `AppendMe` → viaja como estrella fugaz a su TargetPoint). Hoy la obra **termina en `FinishObra`**, que disuelve la sala y enciende las partículas del exterior, y ahí se corta.
- 🔜 Después — **Acto 7, la CODA de Attracting**: al cerrar la melodía, desaparecen beams/slots/no-elegidos, **los elegidos se alinean al frente y suenan 2-3 vueltas** + VO 22, y recién ahí la ceremonia (anillo naranja, 80 %).
  ⚠ Pendiente que NO está en el orden de obra: **la carga final** (etapa 5 = 100 % + disolución animada del HUD), que hoy corre la ceremonia normal.
- ✅ **1.d — FRAMEWORK DE AUDIO + HAPTICS (2026-08-15)**: el punto que se había saltado del orden de construcción.
  - **`BP_AudioHub`** (`Core/Audio/`, colocado en `L_Persistent`): **el catálogo único**. `SfxMap` (Map String→SoundBase, para STitle/SBubble/SCharger/SMind…), `AmbientMap` (los 8 ambients) y `VoClips` (los 30 VOs por índice del guión). `PlaySfx`/`PlaySfxAt`/`PlayAmbient` (**crossfade real** alternando dos AudioComponents) y 🔴 **`PlayVo(i)` que DEVUELVE LA DURACIÓN del clip** (−1 si falta) — así se cumple la regla del guión de que *los tiempos cuelgan del clip, nunca hardcodeados*. Catálogo vacío = la obra corre igual y cada falta se loguea.
  - **`BP_HapticHub`**: los 3 patrones reusables sin ningún asset — `HapticHover` (suave), `HapticSelect` (fuerte), `HapticHold` (continuo, el del umbral), con `bEnabled` para apagar todo.
  - **Retrofiteados ya**: Loving (pide `SMind1-3` + VO 15/16/17, y **espera la duración del VO** si existe, si no `BeatTimes`) y la ceremonia (`VoIndexByStage` etapa→VO global + `SCharger` por nombre). Sus arrays locales se borraron. ⬜ Faltan Breath, Heart, Attracting, Intro y Hall — la migración es mecánica.
  - ⬜ 🔴 **Los haptics todavía no los llama nadie.** El primer candidato es el pulso de Heart (punto 3 del memo de visor: *"tampoco sentí el pulso haptic"*).
  - Verificado por log (`DebugStartStage=3`): el hub reporta el catálogo, Loving pide sus 3 SFX y sus 3 VOs, la ceremonia pide el VO 18 y `SCharger`. Cero `Accessed None`. Detalle: `blueprints/BP_AudioHub.md`.

## 2.c 🔴 FEEDBACK DE VISOR DE BELTRÁN (2026-08-14, noche) — pendientes abiertos

Probó el recorrido con `DebugStartStage`. **Lo que reportó, textual y sin interpretar:**

| # | Qué | Estado |
|---|---|---|
| 1 | **La animación de explicación de las etapas del Hall**: los nombres de cada etapa, lo que va a suceder, y una proto ameba con sus anillos. *"En algún minuto tenemos que hacerla."* | ✅ **CONSTRUIDA 2026-08-15** — `BP_StageIntro` + `WBP_StageIntro`, con la **proto ameba y los anillos REALES** (corrección de Beltrán a mitad de construcción). Verificada por log; falta visor y el VO. Ver §2.b y `blueprints/BP_StageIntro.md`. |
| 2 | 🔴 **El anillo de respiración: YA EXISTÍA.** *"Fíjate en el widget de la calibración, ahí ya habíamos creado un anillo que tiene marcado los distintos pasos de la respiración y que iba avanzando en infinito. No crees cosas desde cero si ya existen, y ya te había comentado que ahí estaba."* | 🔴 **Error de proceso, no descuido**: el plan decía "el radial slider ya existe en el widget de Calibration → reusar" y se construyó uno nuevo igual. **Reemplazar por el de Calibration.** |
| 3 | 🔴 **Heart avanzó solo**: *"esa experiencia avanza y los objetos empiezan a mover cuando estamos DENTRO del umbral… ahora avanzó completamente solo y no esperó a que yo estuviera en el umbral con el sensor en mi corazón."* Y **no sintió el pulso háptico**. | 🔴 Causa directa: el `DriftRate` de test (0,1 = 10 s) terminaba la etapa **antes** de que diera tiempo a calibrar (4,5 s) y entrar en zona. Es la inversión que estaba anotada. |
| 4 | **Attracting sin beam ni secuenciador**: aparecieron los objetos, pero **no apareció el beam** para interactuar y **no pulsaban los slots**. | 🟡 **Secuenciador ARREGLADO** (2026-08-14): `AttractRunBody` **nunca llamaba `StartExperience()`** del `BP_AttractDirector` — en el test aislado de Touch lo llamaba el `Finish()` del panel de instrucciones, que en la obra no corre. Cableado entre `EquipBeams` y `AttractIntro`, verificado por `get_node_infos` (el `read` lo etiqueta mal como `Class|BPStageDirector|StartExperience`). ✅ **BEAM ARREGLADO** (2026-08-14). No era el equipado ni el DrawDebugLine: eran **tres cosas encadenadas**, todas invisibles al compilador —
  1. 🔴 **El componente `BeamFX` de `BP_AimBeam` tenía `Asset: None`** — el sistema Niagara había quedado sin asignar porque **`NS_TouchBeam` estaba en la carpeta `Deprecated/`**. Movido de vuelta a `Stages/Touch/VFX/` y reasignado.
  2. 🔴 **`UpdateBeamPoints` escribía los parámetros con el NOMBRE equivocado**: `"Beam_Start"`/`"Beam_End"` cuando el sistema los expone como **`User.BeamStart`/`User.BeamEnd`**.
  3. 🔴 **Y con el TIPO equivocado**: `SetNiagaraVariable(**Position**)` cuando son **`Vector3f`**. Las dos trampas están documentadas en `assets-existentes.md` ("el tipo del setter tiene que coincidir EXACTO — si no, NO-OP silencioso") y aun así el código las tenía.
  **Verificado contra el asset con `GetUserVariables`, no contra la nota** — que es justo la lección que ese mismo documento dejaba escrita. ⬜ Falta confirmarlo en visor. |
| 5 | **Las instrucciones de Attracting son un TextRender pelado.** *"Tenemos que utilizar el mismo widget que hemos usado en los otros stages."* | ✅ **Corregido 2026-08-14**: `SpawnAttractPanel` ya no spawnea un `TextRenderActor` — spawnea **`BP_TouchInstrPanel`**, que es el panel world-space con el mismo widget de Calibration (páginas, radial de gatillo sostenido, arte por página). Se aprovechó para aplicar la regla del transform (`GetActorTransform` del anchor). `PanelRef` se retipó a `Actor` para poder sostenerlo. ⚠ Pendientes de este panel: sus `PageTexts` vienen con **4 placeholders en español** (los textos in-headset van en inglés) y `AttractText` quedó como **dato muerto** en la etapa. |

> 🔴🔴 **La regla que sale de acá, en sus palabras: *"replicar, replicar, replicar — ya tenemos mucho construido, tenemos que utilizarlo bien."*** El protocolo de arranque de la skill ya lo dice; lo que falló fue **no obedecerlo cuando el plan Y Beltrán ya habían señalado el asset**. Ante la duda entre "reuso lo que hay" y "construyo algo mejor": **se reusa**, y si el existente no alcanza, se propone el cambio antes de construir.

## 2.d 🔁 BUCLE DE TRABAJO AUTÓNOMO (2026-08-15 noche) — leer esto primero tras un reset de contexto

Beltrán dio permiso para avanzar toda la noche sin esperar confirmación: *"contúna etapa por etapa de la forma en que ya lo estás haciendo, testeando, confirmando, continuando, pero nunca esperes de mi confirmación personal para seguir"*. Y pidió apoyarse en las **skills ya construidas**, que existen justamente para no repetir errores.

**El ciclo, una tarea a la vez:**
1. **Protocolo de arranque de la skill `unreal-vr`** (no es opcional): `references/assets-existentes.md` → `blueprints/_INDEX.md` → `references/gotchas.md` → el **tracker del BP** que voy a tocar. Buscar por FUNCIÓN, no por nombre. **Si algo no anda a los 2 intentos, parar y buscar si ya existe una versión probada.**
2. **Construir** con el mínimo de nodos (`bp-lean-construction`), reusando lo que ya está probado en visor.
3. **Leer el grafo después de CADA write** (`read_graph_dsl`) y confirmar lo sospechoso con `get_node_infos` — el read miente por colisión de nombres y no muestra la cadena de exec.
4. **Barrer huérfanos** con `scripts/clean_orphans.py` **copiado tal cual**, exigiendo `identical: true`. ⚠ Borrar a mano los `FunctionResult` sobrantes de funciones con retorno: el barrido los toma como entrada y deja viva la isla muerta.
5. **Verificar por log**: `save_assets` → `StopPIE` → `compile` → `StartPIE` → `GetLogEntries` del patrón propio **y de `Accessed None`** → `StopPIE`. Nunca compilar con PIE corriendo.
6. **Restaurar el estado de prueba** (`DebugStartStage` vuelve a −1, flags de debug en `false`, slots de SaveGame de prueba borrados).
7. **Documentar**: tracker del BP + fila en `_INDEX.md` + cosecha en `gotchas.md` si apareció una trampa nueva + este plan.
8. **Commitear el hito** y pasar a la siguiente.

🔴 **Reglas que no se negocian, ya pagadas:** no se tocan los **IMC** (decisión de Beltrán) · lo que va al **pawn no se mata nunca**, así que los listeners van en los actores de etapa · los **nombres de función son únicos en TODO el proyecto** · **que compile no prueba nada**: se verifica el valor efectivo, no la declaración.

## 2.e 🔍 AUDITORÍA CONTRA EL GUIÓN COMPLETO (2026-08-15, relectura de las 8 páginas)

Beltrán pidió una vuelta de revisión con dos criterios suyos: **(1) ojo con las micro-interacciones** — dónde se agranda un botón y dónde no, dónde se interactúa de una manera y dónde de otra — y **(2) matar lo de la etapa anterior sin romper el resto**, por optimización.

Leyenda: ✅ hecho · 🟡 hecho a medias · ⬜ falta · 🔴 hallazgo/bug

### Acto 1 — Intro App
| Beat del guión | Estado |
|---|---|
| Fade desde negro a infinito azulado con partículas + Ambient 1 | 🟡 el fade inicial sigue siendo **negro instantáneo**, no fade in |
| 3 logos → título (STitle) → Start/About · About con descripción y volver | ✅ falta el arte (PNGs) y el texto en inglés |
| 🎯 **Hover de botón: SBubble + pulso suave + SE AGRANDA — en la ENTRADA y en la SALIDA del hover** | 🟡 `BP_MenuButton` ya agranda; **faltan el sonido y el háptico**, y el guión pide el pulso **también al salir** |
| 🎯 **Selección = hover + trigger → SSelect + pulso FUERTE** | 🟡 el trigger funciona; falta sonido y háptico |

### Acto 2 — Intro Soul
| Beat | Estado |
|---|---|
| Botones y título se desvanecen · crossfade Ambient 1→2 | 🟡 el kill existe; **el crossfade lo puede hacer `BP_AudioHub.PlayAmbient` pero NADIE lo llama todavía** |
| Caminata + VO 1 | ✅ |
| 🎯 **Oscurecimiento GRADUAL mientras avanzamos** (se van partículas y fondo azulado) | ⬜ hoy se apagan **de golpe** al llegar |
| SPasos acoplado a la cadencia del walker | ⬜ el walker ya tiene la cadencia; falta el clip |
| 🎯 **El timbre NO lleva trigger**: sólo posar la mano → se agranda + SBubble + pulso al hover/unhover → al mantener, **vibración continua** + SBell → **ring slider 0→100** → STrigger + pulso fuerte | 🟡 el hold funciona. **Faltan: el ring slider visual, los 3 sonidos y los hápticos.** Es la micro-interacción más distinta de todas y la que más fácil se aplana |

### Acto 3 — Recepción (Hall)
| Beat | Estado |
|---|---|
| Alma da la bienvenida (VO 2) | ✅ |
| **VO 3 + animación de las 5 etapas**: nombres y contenedores **en GRISES**, se colorean 1 a 1, y **cada anillo aparece cuando se nombra la etapa** + SExplicación | ✅ **construido hoy** (`BP_StageIntro`). Falta SExplicación y calzar con el VO |
| Tomar el sensor → STrigger + SBubble + pulso fuerte | 🟡 el sensor se toma; faltan sonidos y háptico |
| **Niagara de anillos subiendo y bajando con nosotros en el centro** + SCalibration | ⬜ no existe |
| 🎯 **Los 5 elementos del HUD aparecen UNO A UNO, animados** | 🟡 el HUD aparece **entero de una**; la aparición animada por elemento no está |
| Elección de proto ameba: hover → SProtoHover + pulso sutil + **se agranda** · trigger → SProtoselect + pulso fuerte | 🟡 el hover y el agrandado existen. **🔴 Ver el hallazgo de abajo** |
| Las demás desaparecen · la elegida se posiciona al frente · VO 6 · se ancla al HUD · VO 7 · Alma se achica y desaparece | ✅ |

> 🔴🔴 **HALLAZGO — la selección del Hall probablemente NO dispara.** `BP_SoulChoice` escucha los eventos **`IA_Shoot_Left/Right`**, pero el contexto que agrega (`IMCRef`) es **`IMC_MenuTrigger`, que sólo mapea `IA_Continue`**. Y los `IMC_Weapon_*` (los que mapearían `IA_Shoot`) están **vacíos**. O sea: el hover marca la candidata, pero el gatillo nunca llega. **Arreglo sin tocar IMC: cambiar los dos eventos a `IA_Continue`**, igual que hace `BP_Finale`. Verificar en visor.

### Acto 4 — Entering
| Beat | Estado |
|---|---|
| VO 8 · widget de instrucciones · **cortafuegos de página a los 20 s** | ✅ |
| Objeto + **radial slider de timing** · sin conteo · el timing avanza solo, el usuario controla el objeto en tiempo real | ✅ (`BP_BreathPacer`, reusando el anillo de Calibration) |
| SCountBreath + VO 9 **simultáneos** | ⬜ audio |
| ⚠ *"Son 5 respiraciones… **para testear usaremos 2 simplemente**"* | 🟡 hoy son **5**. Si querés iterar rápido, bajar los ciclos a 2 |
| Ceremonia: VO 10 + SCharger + anillo **azul** + barra a 20 % · vuelta al HUD · VO 11 | ✅ |

### Acto 5 — Recognizing
| Beat | Estado |
|---|---|
| VO 12 · instrucciones · objetos flotando alrededor | ✅ |
| Al entrar al umbral: **háptico de pulso fuerte en el corazón** + SPulse | ✅ **cableado hoy** (`FireJump` → `HapticSelect` + `PlaySfx`) |
| 10 saltos, curva trampolín, ½ del ritmo cardíaco, fuera del umbral sigue lento | ✅ |
| **Niagara que expulsa un anillo desde nuestro corazón con cada pulso** | ⬜ falta (arte). El hook es `FireJump` |
| Ceremonia: VO 13 + anillo **rojo** + 40 % · VO 14 | ✅ |

### Acto 6 — Loving
| Beat | Estado |
|---|---|
| VO 15 · **sin widget de instrucciones** | ✅ |
| 3 Niagaras timeados VO16/17/18 + SMind 1-3, **acumulativos**, modulados por la actividad | ✅ **construido hoy** (`BP_LovingField`, calma a 60 Hz). ⬜ el arte Niagara real |
| Ceremonia: VO 19 + anillo **morado** + 60 % · VO 20 | ✅ |

### Acto 7 — Attracting
| Beat | Estado |
|---|---|
| **Attracting Base ya sonando al entrar**, sincronizado con el secuenciador · **clip y pack cambian con cada jugador** | ⬜ ni el pool aleatorio ni la sync por Quartz |
| VO 21 · instrucciones · después aparecen beams, slots, botón y objetos uno a uno | ✅ (instrucciones ya en inglés) |
| **Coda**: se van beams, no elegidos y slots; **los elegidos se alinean al frente y suenan 2-3 vueltas** + VO 22; luego desaparecen y **el pad sigue** | ✅ **construido hoy**. ⚠ El "el pad sigue" depende del ambient, que aún no suena |
| Ceremonia: anillo **naranja** + 80 % · VO 23 | ✅ |

### Acto 8 — Surrounding + Final
| Beat | Estado |
|---|---|
| VO 24 · instrucciones | ✅ |
| 🎯 **La proto ameba se desprende y se posiciona al frente, a distancia y tamaño cómodos para dibujar** (*"un poco más grande que un balón"*) | ⬜ **no está**: hoy se dibuja donde esté el pincel, no alrededor de la ameba |
| 🎯 **Zona segura / esfera límite; al pasarla la línea se va en punta** | ⬜ no está |
| SDraw mientras se mantiene el gatillo | ⬜ audio |
| Cierre por **cantidad de trazo definida** | ✅ **construido hoy** (12 m, editable) |
| Última carga: VO 25 · la ameba **crece y se aleja** · barra a 100 % · **HUD se disuelve animado** · SChargerFinal | 🟡 **carga, disolución y desprendimiento hechos hoy**; ⬜ falta que **crezca** y los **Niagaras de carga (vortex, partículas)** y los **anillos girando** |
| 🎯 **La arquitectura se modifica "tipo transformer" y desaparece** revelando el exterior | 🟡 hoy es un `Dissolve` (fade), no una transformación |
| Ambient 7 fade out → **suena NUESTRA melodía** · gráficos de resultados bajo la ameba · VO 26 | 🟡 la melodía **se guarda** como string; ⬜ reproducirla y ⬜ los gráficos (tarea #9) |
| VO 28: decidir incorporarla al corazón · **tomarla y atraerla** → SProtoHeart + explosión Niagara · constelación aparece **poco a poco** · melodía→Ambient 8 · la proto viaja como **estrella fugaz** | ✅ el gesto (hover+gatillo), el guardado y el viaje. ⬜ la explosión Niagara y que la constelación aparezca **gradual** (hoy es de una) |
| VO 29 · **beam para explorar: hover sobre una ameba = suena SU melodía** | ⬜ tarea #9 |
| Las amebas **desaparecen poco a poco** · negro · VO 30 · SCredits · **créditos frente a nosotros** · reload | 🟡 negro, VO, SFX y **reload verificados hoy**; ⬜ la desaparición gradual y ⬜ la **UI de créditos** |

### 🧹 Sobre el criterio (2) de Beltrán: matar sin romper
El patrón **está sano**: cada etapa spawnea lo suyo y su `Cleanup<X>` lo destruye, y el director hace `KillStage`. Lo que la auditoría confirma es que **eso mismo es el árbitro del input** — por eso el listener del gatillo del final vive en el actor del final y no en el pawn. ⚠ **Lo único que NO se mata nunca es lo que esté en el pawn o en el persistente**: hoy son los hubs (Bio/Audio/Haptic/Archivo/Constelación), que deben ser permanentes, y está bien. **Regla a sostener: si algo nuevo necesita input, va en un actor de etapa.**

### 📌 Lo que sale de esta auditoría como pendiente REAL
1. 🔴 **El bug de la selección del Hall** (`IA_Shoot` vs `IA_Continue`) — lo más urgente, rompe un beat central.
2. **Las micro-interacciones de hover**: sonido + háptico en los botones del menú, el timbre (ring slider + 3 sonidos + vibración continua) y la elección del Hall. Todo el andamiaje ya existe (`BP_HapticHub`, `BP_AudioHub`); es cablearlo.
3. **El lienzo alrededor de la ameba + la esfera límite** de Surrounding.
4. **Los ambients**: nadie llama `PlayAmbient` todavía, y el guión pide crossfade en **cada** puerta.
5. **El arte Niagara**: calibración, anillo por pulso, campos de Loving, carga final, explosión del corazón.
6. **Aparición/desaparición gradual** de la constelación y del HUD por elemento.
7. **Pool aleatorio + Quartz** en Attracting.


## 2.f Higiene final de la jornada (2026-08-15, madrugada)

- **Barrido de huerfanos sobre los 23 Blueprints centrales**: solo **13 huerfanos** en todo el proyecto (BP_AudioHub 8, BP_Stage_Loving 5), los dos restos de reescrituras de esta misma noche. Borrados con **`identical: true`** en ambos. El resto salio limpio porque se barrio despues de cada escritura.
- **PIE de control final**: cero `Accessed None` en la corrida completa.
- **`DebugStartStage` restaurado a -1** y todos los flags de debug (`bDebugRunOnPlay`, `bDebugAppendOnPlay`, `bDebugClearOnPlay`, `bDebugBuildOnPlay`) en `false`. Slot de prueba `SoulConstellation.sav` borrado del disco.
- ⬜ **Pendiente: el layout automatico de los grafos nuevos.** `scripts/auto_layout.py` existe y esta validado, pero corre sobre **un grafo por invocacion** y hay que pasarle el script entero (6,5 KB) al `execute_tool_script`. Transcribirlo a mano viola la regla de no reimplementar scripts de la skill, asi que se dejo para una pasada dedicada. Los grafos nuevos **funcionan bien pero estan encimados en el origen**: al abrirlos en el editor hay que ordenarlos a ojo.

## 3. Orden de construcción propuesto

1. **`BP_SoulHUD` + señales OSC (EEG/BPM) + registro de promedios** (1.a + 1.c) — el HUD atraviesa todo; sin él no hay ceremonia ni Loving ni final.
2. **La ceremonia de carga** (1.b) — cierra las 5 etapas; testeable con `DebugStartStage` en cualquiera.
3. **Audio + haptics framework con placeholders** (1.d) — crossfades por sala + catálogo SFX + 3 patrones haptic. Se construye una vez y cada acto solo lo llena.
4. **Reworks de etapa en orden de obra**: Intro/menú (hover grow + sonidos) → oscurecimiento del corredor + ring slider del timbre → Hall (animación de etapas + calibración/HUD + selección hover+trigger) → Entering timeado → Recognizing 10 pulsos → Loving Niagaras EEG → Attracting (pool+Quartz+coda) → Surrounding (esfera límite + metros).
5. **El final completo** (gráficos, decisión del corazón, constelación multi-usuario, exploración, créditos, reload).
6. Fine-tuning con arte por etapa (1-2 jornadas c/u, con `DebugStartStage`).

## 4. Pendientes de Beltrán (insumos, no bloquean)
- **Archivos de audio**: 8 ambients + ~22 SFX + 30 VOs + pool de Attracting (clips base + packs de objetos). Con placeholders mientras.
- **Dirección/formato OSC de la señal EEG** (0–1) — y confirmar la del BPM.
- PNGs de los 3 logos · texto de About US (inglés) · meshes/materiales de las proto amebas (geometrías distintas) y de los modos del sensor.
- 🧬 **Llenar `Core/Amoeba/F_SoulPortrait` a mano** (hoy está vacío, sólo un placeholder `tBD`): variante int · color LinearColor · anillos int · calma float · ritmo float · melodía string. **El MCP no puede agregar miembros a un UserDefinedStruct**, por eso `SG_Constellation` persiste con **arrays paralelos**. Funciona y está verificado, pero si Beltrán llena el struct, se migra a un solo array de structs (más elegante y sin riesgo de desalineado). No bloquea nada.
