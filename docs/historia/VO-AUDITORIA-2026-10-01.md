# Auditoría de VO — 2026-10-01 (sesión Breath, pedido de Beltrán vía Narrativa)

Síntoma reportado por Beltrán: *"en varias etapas faltaron muchos voiceovers; Alma nos recibe, dice algo y se queda callada mucho rato sin que pase nada"*.

Fuentes: mezcla final de Beltrán (Ableton → master → cortes por clip, `Escritorio/Soul Charger VO MEZCLA final/`, 60 wav), lista `docs/VO-SOUL-CHARGER-2026-10-01.md` (v3), assets en `Content/`, trackers.

## 1. Cortes de la mezcla

**Método:** para cada clip, envolvente RMS cada 10 ms (umbral −40 dB) → dónde empieza y termina la voz; comparación de la duración del habla contra la toma generada que usó Beltrán, y correlación del comienzo contra esa toma para detectar ataques recortados.

**Resultado:**
- La mezcla usa la **tanda de velocidad 0,95** (`Escritorio/Soul Charger VO 2026-10-01 - voz original Alma`): el habla de cada clip coincide con esa toma (±0,05 s).
- **Ningún final cortado, ninguna palabra faltante, ninguna frase pegada** (el habla nunca es más corta que la toma; los huecos entre clips del master están a −132 dB).
- Silencio inicial máximo 0,21 s (VO_18): ninguno largo.
- **VO_12f1 "Hold." y VO_12f2 "Exhale.": NO están recortadas.** La correlación de forma de onda marcó 62/97 ms de ataque faltante, pero es una falsa alarma: en clips tan cortos con efectos (reverb/EQ cambian la fase) esa medición falla. Con la envolvente (robusta a los efectos) el desfase contra la toma es **0 ms** y el habla dura lo mismo (0,51 / 0,78 s vs 0,51 / 0,76 s). Decisión sin escucha (Beltrán duerme): no se toca. Colas de reverb cortadas por el clip siguiente (el clip de Ableton estaba pegado al siguiente) en 4 clips: inaudible salvo VO_35a (−51 dB al corte).

| Clip | Dur. (s) | Silencio inicial (s) | Habla (s) | Habla toma 0,95 (s) | Nota |
|---|---|---|---|---|---|
| 01_VO_01a | 5.49 | 0.17 | 5.03 | 4.96 | 0.17 s de silencio al inicio |
| 02_VO_01b | 2.22 | 0.00 | 1.93 | 1.9 | OK |
| 03_VO_01c | 6.97 | 0.02 | 6.69 | 6.69 | OK |
| 04_VO_02 | 7.33 | 0.11 | 7.00 | 6.98 | OK |
| 05_VO_03 | 9.10 | 0.06 | 8.78 | 8.75 | OK |
| 06_VO_03h | 1.70 | 0.01 | 1.38 | 1.32 | OK |
| 07_VO_04 | 8.41 | 0.18 | 7.96 | 7.96 | 0.18 s de silencio al inicio |
| 08_VO_05 | 5.30 | 0.07 | 5.03 | 5.01 | OK |
| 09_VO_06b | 2.50 | 0.00 | 2.31 | 2.29 | OK |
| 10_VO_06c | 3.27 | 0.00 | 2.98 | 3.02 | OK |
| 11_VO_06d | 3.14 | 0.01 | 2.88 | 2.87 | OK |
| 12_VO_06e | 3.25 | 0.01 | 2.94 | 2.93 | OK |
| 13_VO_06f | 3.73 | 0.00 | 3.44 | 3.46 | OK |
| 14_VO_06g | 3.07 | 0.06 | 2.74 | 2.73 | OK |
| 15_VO_07 | 3.05 | 0.02 | 2.80 | 2.8 | OK |
| 16_VO_10 | 8.50 | 0.08 | 8.16 | 8.15 | OK |
| 17_VO_11 | 5.84 | 0.04 | 5.47 | 5.47 | OK |
| 18_VO_11h | 3.40 | 0.02 | 3.10 | 3.1 | OK |
| 19_VO_11b | 7.45 | 0.06 | 7.14 | 7.07 | OK |
| 20_VO_12 | 5.24 | 0.04 | 4.77 | 4.77 | OK |
| 21_VO_12c | 3.56 | 0.00 | 3.34 | 3.3 | OK |
| 22_VO_12f1 | 0.81 | 0.00 | 0.51 | 0.51 | OK (falsa alarma de la correlación; envolvente: 0 ms) |
| 23_VO_12f2 | 1.05 | 0.01 | 0.78 | 0.76 | OK (falsa alarma de la correlación; envolvente: 0 ms) |
| 24_VO_13 | 6.14 | 0.05 | 5.88 | 5.89 | OK |
| 25_VO_14 | 5.88 | 0.18 | 5.42 | 5.42 | 0.18 s de silencio al inicio |
| 26_VO_15 | 3.67 | 0.08 | 3.31 | 3.28 | OK |
| 27_VO_16 | 3.78 | 0.03 | 3.48 | 3.47 | OK |
| 28_VO_16h | 2.58 | 0.04 | 2.29 | 2.24 | OK |
| 29_VO_17a | 4.00 | 0.04 | 3.89 | 3.84 | cola de reverb cortada por el clip siguiente (-57 dB al corte) |
| 30_VO_17c | 2.75 | 0.07 | 2.41 | 2.4 | OK |
| 31_VO_18 | 5.15 | 0.21 | 4.69 | 4.71 | 0.21 s de silencio al inicio |
| 32_VO_19 | 4.99 | 0.17 | 4.48 | 4.48 | 0.17 s de silencio al inicio |
| 33_VO_20 | 7.77 | 0.00 | 7.44 | 7.42 | OK |
| 34_VO_22 | 7.07 | 0.01 | 6.82 | 6.82 | OK |
| 35_VO_23 | 2.59 | 0.07 | 2.22 | 2.2 | OK |
| 36_VO_23b | 5.43 | 0.04 | 5.15 | 5.13 | OK |
| 37_VO_25 | 5.35 | 0.05 | 5.01 | 5.0 | OK |
| 38_VO_26 | 4.27 | 0.17 | 3.86 | 3.78 | 0.17 s de silencio al inicio |
| 39_VO_27 | 6.00 | 0.08 | 5.70 | 5.7 | cola de reverb cortada por el clip siguiente (-57 dB al corte) |
| 40_VO_27d | 5.20 | 0.02 | 4.90 | 4.94 | OK |
| 41_VO_27h | 2.31 | 0.05 | 1.99 | 1.98 | OK |
| 42_VO_27b | 4.31 | 0.04 | 3.96 | 3.97 | OK |
| 43_VO_27c | 2.68 | 0.06 | 2.36 | 2.36 | OK |
| 44_VO_28 | 2.00 | 0.01 | 1.76 | 1.7 | OK |
| 45_VO_29 | 2.59 | 0.06 | 2.20 | 2.19 | OK |
| 46_VO_30 | 3.03 | 0.01 | 2.72 | 2.72 | OK |
| 47_VO_31 | 10.27 | 0.04 | 9.90 | 9.91 | OK |
| 48_VO_32 | 4.91 | 0.02 | 4.61 | 4.59 | OK |
| 49_VO_32d | 6.91 | 0.08 | 6.51 | 6.57 | OK |
| 50_VO_32h | 2.45 | 0.06 | 2.10 | 2.1 | OK |
| 51_VO_32b | 2.68 | 0.06 | 2.35 | 2.34 | OK |
| 52_VO_32c | 4.31 | 0.04 | 4.06 | 3.99 | OK |
| 53_VO_33 | 2.00 | 0.07 | 1.66 | 1.68 | OK |
| 54_VO_34a | 4.00 | 0.00 | 3.84 | 3.85 | OK |
| 55_VO_34b | 10.39 | 0.03 | 10.05 | 10.06 | OK |
| 56_VO_36b | 5.24 | 0.09 | 4.84 | 4.78 | OK |
| 57_VO_36p | 2.67 | 0.02 | 2.36 | 2.35 | OK |
| 58_VO_35b | 6.30 | 0.02 | 6.07 | 5.97 | OK |
| 59_VO_35a | 2.00 | 0.04 | 1.90 | 1.86 | cola de reverb cortada por el clip siguiente (-51 dB al corte) |
| 60_VO_37 | 9.13 | 0.20 | 8.62 | 8.61 | 0.20 s de silencio al inicio |

## 2. Cobertura (dónde se dispara cada VO hoy)

**Método:** `AssetTools.get_referencers` sobre los 71 SoundWave `VO_*` (editor, solo lectura, 2026-10-01 ~07:45). El grep de los `.uasset` **no sirve** para los nombres que terminan en número (FName guarda `VO_13` como `VO` + 13); los nombres con letra sí coinciden con el grep. ⚠ *Referenciado* = algún BP lo tiene cableado; que suene en la Obra además depende de que esa rama corra (el flujo de Narrativa ya está probado en PIE para Hall/Obra).

**Resumen:** de las 60 VO de la lista v3, **39 están cableadas** y **21 NO las dispara nada**: son justamente las de **adentro de cada mecánica** (instrucciones, exploración, ayudas y frases durante la etapa). Eso explica el síntoma de Beltrán: la Obra hace hablar a Alma al recibir (VO_10/15/20/26/31, `AlmaSpeak`) y al cerrar (carga y despedida), pero entre medio la etapa no dice nada. Además el **Hall sigue disparando 4 VO eliminadas** en la v3.

| VO | Texto (corto) | Etapa | Disparada por | Estado |
|---|---|---|---|---|
| VO_01a · 01b · 01c | viaje (preguntas, sonidos, el portal) | Inicio | BP_HallDirector_SC | ✅ suena |
| VO_02 | bienvenida de Alma | Inicio | BP_HallDirector_SC | ✅ |
| VO_03 · VO_03h | tomar el sensor · ayuda | Hall | BP_HallDirector_SC | ✅ (⚠ VO_03h: la v3 pide que suene solo tras MUCHO tiempo sin actuar — revisar el umbral en HallDirector) |
| VO_04 | elegir el alma (une 04 + 04b) | Hall | BP_HallDirector_SC | ✅ |
| VO_05 · 06b-06g · 07 | tu alma, las 5 baldosas, sígueme | Hall | BP_HallDirector_SC | ✅ |
| VO_10 · VO_15 · VO_20 · VO_26 · VO_31 | "This is …" (entrada de cada etapa) | Etapas | BP_Obra_SC (`AlmaSpeak`) + BP_StageRunner_SC | ✅ |
| **VO_11 · VO_11h · VO_11b · VO_12** | sensor en la panza · ayuda · explora · ejercicio | Entering | — | ❌ **no suena** |
| VO_12c · VO_12f1 · VO_12f2 | cuenta + Hold/Exhale del 1.er ciclo | Entering | BP_BreathStage_SC (copia `Breath/Audio`) | ✅ (la copia `Obra/Audio/VO_12c` no la usa nadie: duplicada) |
| VO_13 · VO_18 · VO_23b · VO_29 | felicita e invita a cargar | Etapas | BP_Obra_SC (`AlmaCharge`) | ✅ |
| VO_14 · VO_19 · VO_25 · VO_30 | sigamos a la etapa siguiente | Etapas | BP_Obra_SC (`FlowBye`) | ✅ |
| **VO_16 · VO_16h · VO_17a · VO_17c** | sensor en el pecho · ayuda · ¿oyes tu latido? · gratitud | Recognizing | — | ❌ **no suena** |
| **VO_22 · VO_23** | constelaciones · ¿qué pensamiento? | Loving | — | ❌ **no suena** |
| **VO_27 · 27d · 27h · 27b · 27c · 28** | alcanza el espacio · apunta y coloca · ayuda · magnetismo · SAVE · tu melodía | Attracting | — | ❌ **no suena** |
| **VO_32 · 32d · 32h · 32b · 32c** | una pintura de amor · el pincel · ayuda · texturas · SAVE | Surrounding | — | ❌ **no suena** |
| VO_33 | alma cargada | Final | BP_Obra_SC (`FinalStart`) | ✅ |
| VO_34a | regreso | Final | BP_HallDirector_SC | ✅ |
| VO_34b · 36b · 36p · 35b | carta · compartir · botones · constelación | Final | BP_Obra_SC (`FlowShare`/`FlowConst`) | ✅ |
| VO_35a | tu alma guía el camino | Final | BP_HallDirector_SC + BP_Obra_SC | ✅ |
| VO_37 | el regalo / gracias | Final | BP_Obra_SC | ✅ |

**VO eliminadas en la v3 que TODAVÍA están cableadas** (hay que sacarlas):
| VO | Dónde | Efecto hoy | Dueño |
|---|---|---|---|
| VO_01d "Rest your hand on the bell…" | BP_HallDirector_SC | la v3 la eliminó (el timbre va solo con la animación) | Inicio y Hall |
| VO_01h "Rest your hand on it." | BP_HallDirector_SC | ayuda eliminada | Inicio y Hall |
| VO_04b "Point at the one that calls you…" | BP_HallDirector_SC | **duplica** el final de la nueva VO_04 (que ya lo dice) | Inicio y Hall |
| VO_06a "Your journey has five stages." | BP_HallDirector_SC | eliminada en la v3 | Inicio y Hall |
| VO_24 "Your calm has lit the third light." | BP_StageRunner_SC (solo el ensayo de test) | no suena en la Obra; limpiar el runner | Narrativa |
Sin referencias (se pueden borrar cuando Narrativa decida): VO_34c, VO_35c, VO_36, VO_36c, VO_36d y la copia `Obra/Audio/VO_12c`.

## 3. VO que existen y no suenan: dónde engancharlas y dueño

Regla común (Narrativa): hablar con `Alma.SayClip(Clip)` si Alma está visible y no está hablando; si no, 2D. Ninguna espera debe salir del largo de un sonido salvo la VO misma.

### Entering — dueño: Breath (BP_BreathStage_SC) — **lo hago yo** (script preparado, pido turno)
| VO | Cuándo (guion v3) | Enganche |
|---|---|---|
| VO_11 "Rest the sensor on your belly…" | instrucciones, con el fantasma: cuando el mando ya es sensor | fase 10 (StageIntro), a `ToolDelay` + ~1 s (el sensor ya se formó) |
| VO_11b "Take a moment to explore…" | al empezar la exploración libre | fase 11 (StageBegin), apenas termina VO_11 + 0,5 s |
| VO_11h "Just below your ribs… flat side toward you." | ayuda: solo si el sensor no está en la panza | fase 11, si el rig no detecta zona (`bZone` false) ~4 s después de VO_11b |
| VO_12 "Now, let's do a simple breathing exercise…" | fin de la exploración, justo antes de la cuenta | fase 11, a `ExploreTime − dur(VO_12) − 0,4`, nunca antes de que termine la anterior; **la cuenta espera** a que VO_12 termine (+0,3 s) |
⚠ Con `ExploreTime` 12, VO_11b (7,45 s) + VO_12 (5,24 s) no entran: la exploración se estira sola a ~13,5 s (la cuenta espera a VO_12). Si se prefiere más silencio libre, subir `ExploreTime` a ~15.
⚠ La Obra da `InstrTime` 6 entre StageIntro y StageBegin; VO_11 empieza a ~1,8 s y dura 5,84 → termina a ~7,6: StageBegin no la corta (VO_11b espera a que termine), pero conviene `InstrTime` ≥ 8,5 para Entering (Narrativa).

### Recognizing — dueño: Heart (BP_HeartManager_SC) — en curso
| VO | Cuándo | Enganche sugerido |
|---|---|---|
| VO_16 "Place the sensor on your chest…" | instrucciones, con el fantasma | `StageIntro`, cuando el sensor ya está rojizo (SetSensorColor) |
| VO_16h "A little higher… and very still." | ayuda si no hay latido en zona tras 2 bucles del fantasma | timer desde StageBegin sin latido en zona |
| VO_17a "Can you hear your heartbeat?…" | primer latido en zona, ANTES de que la membrana reaccione | evento del primer latido válido |
| VO_17c "Does gratitude flow through your heartbeat?" | a mitad de los latidos | contador de latidos = mitad del objetivo (o mitad del tiempo de la etapa) |

### Loving — dueño: Mind (BP_LovingCell_SC) — en curso
| VO | Cuándo | Enganche sugerido |
|---|---|---|
| VO_22 "Observe your thoughts like distant constellations…" | forma 2 (+ FX_MIND_2) | el cambio a la forma 2 de la célula |
| VO_23 "Which thought carries a quiet wisdom today?" | forma 3 (+ FX_MIND_3) | el cambio a la forma 3 |
(VO_20 ya cubre la entrada; VO_23b la dispara la Obra antes de la carga.)

### Attracting — dueño: Narrativa (BP_Sequencer_SC)
| VO | Cuándo (guion) | Evento de la mecánica que conviene usar |
|---|---|---|
| VO_27 "Reach into the space…" | instrucciones, con el fantasma | `StageIntro` / `SeqIntroGo` (cuando aparecen esferas y slots), tras `IntroDelay` |
| VO_27d "Point at a sphere and pull the trigger… place it on the shape." | con el fantasma, después de VO_27 | encadenada a VO_27 (+0,5 s), antes de `StageBegin` (`ArmBeamNow`) |
| VO_27h "Point at a sphere and pull the trigger." | ayuda: sin agarre tras 2 bucles del fantasma | timer desde `StageBegin` sin ninguna esfera agarrada |
| VO_27b "Can you feel your magnetism?…" | **tercera esfera colocada** | `NotifyPlaced` (contador de colocadas = 3) |
| VO_27c "When it sounds like you, hold SAVE." | ~75 s de juego | tiempo desde `StageBegin` ≥ 75 s y SAVE disponible (≥ 1 slot ocupado) |
| VO_28 "Listen… this is your melody." | coda (las 2 pasadas después de SAVE) | confirmación del SAVE (`ResultsPlay`/coda), al empezar la primera pasada |

### Surrounding — dueño: Narrativa (BP_TBDirector_NC)
| VO | Cuándo (guion) | Evento sugerido |
|---|---|---|
| VO_32 "A painting of love, a dance of life, an image of the soul." | instrucciones, con el fantasma | `StageIntro` (la paleta aparece) |
| VO_32d "Bring your brush close to a color…" | con el fantasma, después de VO_32 | encadenada a VO_32 (+0,5 s) |
| VO_32h "Press the trigger and move your hand." | ayuda: sin trazo tras 2 bucles del fantasma | timer desde `StageBegin` sin ningún trazo |
| VO_32b "Can your emotions become visible textures?" | ~40 s de dibujo | tiempo dibujando (o desde el primer trazo) ≥ 40 s |
| VO_32c "Take your time… hold SAVE." | ~60 s de dibujo | tiempo dibujando ≥ 60 s (y SAVE visible) |

## 4. Resumen para Beltrán
- Tu mezcla está bien cortada: 60/60 clips completos, sin palabras cortadas ni frases pegadas.
- El silencio largo en las etapas es porque **21 VO de adentro de las mecánicas no están conectadas** (Entering 4, Recognizing 4, Loving 2, Attracting 6, Surrounding 5). Reparto: Entering = Breath, Recognizing = Heart, Loving = Mind, Attracting y Surrounding = Narrativa.
- El Hall todavía dice 4 frases que eliminaste (VO_01d, 01h, 04b, 06a): VO_04b repite lo que ahora dice VO_04.
