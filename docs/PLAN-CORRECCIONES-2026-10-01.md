# Plan de correcciones — prueba de Beltrán, 2026-10-01 (madrugada)

Fuente: `docs/NOTAS-BELTRAN-2026-10-01-correcciones.md` (7 notas de voz). Dirige Narrativa; el editor lo lleva Narrativa y da turnos.
Sesiones activadas por pedido de Beltrán: Breath (auditoría de VO + Entering), Heart, Mind, Mesh 3D (visual) y Fantasmas (dos arreglos chicos).
Criterio de Beltrán: pensar como el usuario. Nada puede dejarlo parado sin saber qué pasa; nada demasiado largo ni demasiado rápido.
Cierre: APK Development instalado en el Quest y probado ahí (logcat), con informe para la mañana.

Prioridad: **P1** rompe el flujo o se ve roto · **P2** se nota y molesta · **P3** pulido.

## A. Flujo, silencios y voz (P1)
| # | Corrección | Dueño | Estado |
|---|---|---|---|
| A1 | Ambientes en crossfade real, sin huecos de silencio entre clips | Narrativa (`BP_Obra_SC` AmbTo/AmbFade) | ✅ AmbTick: el clip vuelve a entrar en crossfade antes de terminar (escrito y compilado; falta oírlo en el visor) |
| A2 | VO faltantes: auditar cortes y qué VO creados no suenan; integrar los que encajan (instrucciones, frases entre medio) | Breath (auditoría) + dueño de cada etapa (disparo) | ✅ Auditoría (`docs/VO-AUDITORIA-2026-10-01.md`). PIE en la Obra: Entering (VO_11 a 1,8 s del intro → VO_11b al empezar → VO_12 → la cuenta espera) y Attracting (VO_27 a 0,8 s, VO_27d, VO_27h a 20 s sin esferas), sin voces encimadas. Drawing (CueDraw), mismo patrón, no corrido |
| A3 | Alma aparece primero y recién después habla (nunca voz antes de verla) | Narrativa (`AlmaIn`/`AlmaSpeak` + Hall) | ✅ PIE: Alma aparece a 5,8 s y habla 1,5 s después (Entering, Attracting) |
| A4 | Heart: Alma saluda y queda callada; poner sus frases entre medio | Heart | ✅ VO_16/16h/17a/17c (PIE) |
| A5 | Salida del Hall → título ENTERING apenas se cruza la puerta, fluido y visible el tiempo justo | Narrativa (Hall `HallEnterExit` + `RunObra`) | 🟡 HallExitEarly (x ≥ 760) + OutTime 8; título 0,5→5,6; falta PIE |
| A6 | Volúmenes: efectos más bajos (la carga queda), ambientes aún más bajos; manda la voz | Narrativa | ✅ 27 efectos ×0,6 (lista en `Saved/ClaudeScripts/Obra/dump/sfx_vol_out.json`); voces, ambientes, cargas, M1S y pacer sin tocar; ambientes 0,38 |
| A7 | Texto inicial en inglés (sensores; datos simulados en este build), en el negro del inicio; se va cuando empieza la obra | Narrativa (`BP_Disclaimer_SC`) | 🟡 PIE: la fase del aviso dura 9 s y el Hall entra después; el render del texto se mira en el visor |

## B. Manos y sensor (P1)
| # | Corrección | Dueño | Estado |
|---|---|---|---|
| B1 | Una sola fuente de manos: sin mallas duplicadas en Attracting ni en Drawing | Narrativa | ✅ La mano duplicada era `HandGhost` de `BP_UserTool_SC` (mano de referencia del editor) visible en juego; `GhostOff` en cada cuadro. PIE por etapas: Entering solo sensor · Loving 2 manos · Attracting solo el mando · Drawing solo el mando. Falta visor |
| B2 | Línea de tiempo: Hall con manos → al tomar el sensor se van las manos; sensor en Entering y Heart → al terminar Heart vuelven las manos (Loving) → al terminar Loving se van las manos y queda el sensor en Attracting y Drawing hasta el final | Narrativa (función única en la Obra) | 🟡 HandsTick implementa la línea de tiempo completa (Hall: manos hasta tomar el sensor · Entering/Recognizing: sensor · Loving: manos · Attracting/Drawing/final: sensor); falta PIE |
| B3 | Material translúcido de la mano más transparente | Mesh 3D | 🟡 Mesh 3D: `MI_Hand_SC` Opacity 0,35→0,22, EdgeBoost 0,65→0,5; no visto |
| B4 | Háptico pegado en el final | Narrativa | 🟡 ChargeFx.MuteFeel + háptico 0 en fases 10-15; falta PIE |
| B5 | Heart: la mano no sale nunca del umbral | Heart | ✅ respaldo a 30 s que se suelta con la mano real (PIE) |

## C. Etapas (P1-P2)
| # | Corrección | Dueño | Estado |
|---|---|---|---|
| C1 | Heart: el pulso de agua y su sonido a la MITAD del latido; el simulado era rapidísimo | Heart | ✅ BeatDiv 2 (PIE) |
| C2 | Loving: la neurona aparece con Alma todavía al frente → que aparezca cuando Alma ya se hizo a un lado | Mind | ✅ Mind: la neurona espera 2 s y crece en 3 s con Alma ya a 2,4 m (PIE). Loving: VO_22/VO_23 por SayClip; dura 60 s |
| C3 | Attracting: todo muy blanco (el gusano se pierde con suelo y cielo) → paleta con contraste | Mesh 3D | 🟡 Mesh 3D: cielo con cenit malva, salar algo más bajo, gusano terracota→naranja, esferas oro/coral/perla/rosa viejo (visto en captura del editor, no en PIE) |
| C4 | Attracting: sacar el texto negro enorme "Save Game" del botón de la mano | Fantasmas | ✅ Fantasmas: `BP_SaveMelody_SC.Label` sin texto y oculto |
| C5 | Halo de color de la carga casi invisible | Mesh 3D (`BP_ChargeFx_SC`) | 🟡 Mesh 3D: `M_ChargeHaloTint_SC` translúcido (HaloSat 1,6 · HaloOpGain 2 · HaloMaxOpacity 0,6 · HaloGlow 1,1); no visto |
| C6 | TargetPoints de Alma al costado: más chica en TODAS las etapas (Beltrán cambió los primeros) y el TP define el transform completo | Narrativa | 🟡 TP laterales a 0,6 en las 4 etapas restantes; la Obra copia la escala del TP a Alma (AlmaSclIn/AlmaSclAside/AlmaSclTick, suave); en el Hall y el final, escala 1; falta PIE |

## D. Hall (P2)
| # | Corrección | Dueño | Estado |
|---|---|---|---|
| D1 | Fundido a negro del inicio más lento, sin tapar el nacimiento del Hall | Narrativa (`BP_HallDirector_SC`) | ⬜ |
| D2 | Título un par de segundos más antes de partir | Narrativa | ✅ HallIntro a PT 3 (antes 1); título se va 12→14,5 |
| D3 | Timbre: el anillo radial desaparece al instante al completar la carga | Narrativa | 🟡 SetVisibility(Slider,false) al completar; falta PIE |
| D4 | Timbre: el sonido parte al tocar; al soltar, fade out; al volver a tocar, parte de nuevo desde el inicio | Narrativa | 🟡 HallBellSnd: suena al tocar, fade out 0,5 s al soltar, vuelve a partir al retocar; el paso 7 ya no lo dispara; falta PIE |
| D5 | Sensor girando suave dentro del orb (moneda flotante); al tomarlo, pose correcta | Narrativa | 🟡 HallSensorSpin: 40°/s mientras espera; falta PIE |
| D6 | Protoameba: el TargetPoint define el transform completo (escala incluida) | Narrativa | ✅ TP_hall_soul_present escala 1 (guardado); el TP ya mandaba el transform |
| D7 | Protoameba: al llegar aparece su anillo, encajado a su tamaño (marca luces con las baldosas) | Narrativa | 🟡 `HallRing`: el anillo de carga nace alrededor de la protoameba cuando llega a su punto (pum de llegada ×1,5), con la escala ajustada a ella (`HallRingFit`); sus 5 luces siguen a las baldosas. PIE ok; falta visor |
| D8 | Al terminar la explicación de las etapas: animación corta (como el fin de carga), desaparece y reaparece en el HUD | Narrativa | 🟡 En el paso 24, la vuelta al nido de la carga, el doble de rápida (1,3 s): tiembla, pum y reaparece en el HUD. PIE ok; falta visor |
| D9 | EEG del HUD apenas más brillante o grueso | Mesh 3D | 🟡 Mesh 3D: EEG LineWidth 2→2,4 y alfa 0,64→0,77; no visto |
| D10 | Baldosas menos brillantes: bajar el brillo | Mesh 3D | 🟡 Mesh 3D: `M_Hall_Tile_SC` RestDim 0,7 (solo apaga el reposo); no visto |
| D11 | Alma: perillas en el BP para las partículas | Narrativa | ✅ Perillas `J - Aura` en BP_Alma_SC (AuraAlpha, AuraSize, AuraTwinkle, AuraCurl, AuraFlow, AuraGlow) → AuraApply al crear el aura |

## E. Final (P1)
| # | Corrección | Dueño | Estado |
|---|---|---|---|
| E1 | Última carga: terminar de cargar, luego negro del ENTORNO (no de todo); protoameba se desprende, anillo desaparece, protoameba avanza | Narrativa | 🟡 La carga llena a 8,5 s, 1 s de anillo lleno, el entorno se va a negro de 9,5 a 11,5 s y el anillo y el alma quedan visibles encima (materiales "siempre al frente" del HUD; el `FinalLook` tenía los materiales vacíos). En el Hall el alma se desprende como el pez y el anillo se va. PIE ok; falta visor |
| E2 | Compartir: desaparece TODO el sistema del cuadro (gráficos y dibujos), no solo el marco | Narrativa | 🟡 ResultsOutK funde las K en 0,8 s; falta PIE |
| E3 | Salida: sin pasos; menos espera | Narrativa | 🟡 HallWalk sin pasos en modo 3; ExitTime 12→7; falta PIE |
| E4 | Constelación: estrellas que crecen animadas (no de 0 a 1) | Fantasmas | 🟡 Fantasmas: StarsGrow (0→escala en 1,2 s, salida suave); escrito, no visto crecer |

## F. Cierre
| # | Paso | Estado |
|---|---|---|
| F1 | Corrida completa en PIE, 0 errores, cronometrando cada silencio | ✅ PIE por tramos, 0 errores en los 4: inicio −1 (aviso → Hall hasta el paso 12), 10 (Entering), 40 (Attracting), 60 (carga final → negro → Hall → resultados → compartir → salida 8,5 s → créditos) |
| F2 | APK Development (DebugStart −1, bSimulated true) | ✅ APK Development (DebugStart −1, bSimulated true, aviso on), última versión 10:01; copia en `Escritorio/Soul Charger Obra APK` |
| F3 | Instalar en el Quest; correr la obra entera; logcat sin errores; registrar tiempos | ✅ Instalado; obra entera en el visor 09:19-09:37 sin errores, con reinicio solo después de los créditos. Hall a 42 fps → arreglado a 62,5 (materiales del Hall); falta ~1 ms (haz del óculo) |
| F4 | Informe para Beltrán: hecho, probado, pendiente | ✅ `docs/INFORME-NOCHE-2026-10-01.md` |

## Registro
- 08:05 Heart: C1, B5, A4 ✅ (PIE).
- 08:15 Narrativa: A1 (AmbTick + ambientes 0,6→0,38), VO de Attracting/Drawing (StageCues/CueAttract/CueDraw), fase 5 espera las instrucciones (bInstrReady), AlmaSpeak con 1,5 s, título de etapa 0,5→5,6 (Alma a 5,8), Recognizing 180 s, velo final 8,6→10,9, aviso (textura, sort, 9 s).
- Hallazgo: el texto del aviso tenía sort 110 bajo el velo negro (32600) → no podía verse nunca.
- 09:05 Narrativa: HandsTick con IsValid (los Accessed None que vio Fantasmas), escala de Alma desde la Obra, perillas del aura, timbre con sonido al tocar y sensor girando, efectos ×0,6. Final: el velo de la vuelta al Hall cierra 0,2→1,4 s y el salto al Hall espera a 1,6 s (antes saltaba a 0,5 s, con el velo todavía abierto).
- 09:40 Breath: VO de Entering cableadas en BP_BreathStage_SC (StageSay + StepStageVO; el cue del pacer espera la retención); runner InstrTime 8,5.
- 09:50 Narrativa: PIE −1/10/40/60 con 0 errores (los "Accessed None" de HandsTick ya no aparecen). DebugStart −1, todo guardado; APK en cocción.
- 09:19-09:37 APK en el Quest: obra completa sin errores. Hall 42 fps (App 21,8 ms).
- 09:45-10:03 Narrativa: rendimiento del Hall: HallGroovesPS v7 (51 fps) → ruido por textura `T_HallNoiseRG_SC` en HallInteriorPS v4 (61) y HallTilePS v2 (62,5). APK final 10:01 instalado. Con las transparencias apagadas llega a 72: queda el haz del óculo.
- 10:40 Narrativa (Beltrán despierto: "es hacer más rápida esa animación"): D7/D8 con `BP_ChargeFx_SC` manejado desde la Obra (`HallRing`). PIE desde el paso 14, sin errores. **En el APK de las 12:33.**
- 11:00 Narrativa (pedido de Beltrán): E1 completo. La carga termina, 1 s después el entorno se va a negro y el anillo con el alma quedan por encima. **En el APK de las 12:33.**
- 11:30 Narrativa: manos duplicadas resueltas (HandGhost), medido en PIE etapa por etapa. Pregunta abierta a Beltrán: en Attracting y Drawing se ve el mando de la etapa, no el sensor.
- 12:33 APK nuevo instalado (pedido de Beltrán), con el anillo del Hall, la última carga y el negro, y la mano fantasma apagada. Arranca y llega al Hall sin errores; la app quedó cerrada.

## Tanda de la tarde (13:00-13:35) — APK 13:32 instalado, arranque al Hall sin errores
- **Draw**: se dibuja cuando aparece la mesa. `StageCues`: el primer aviso entra en fase 5 o 6 y `bInstrReady` siempre verdadero en la etapa 4; `StageTimes`: `InstrTime 0,6` en K = 4.
- **Heart (y todas)**: Alma se mueve a la izquierda a los `VODur + 3 s` (se quitó el `StAlma` por etapa, que la dejaba callada demasiado).
- **Resultados**: Alma 45 cm más a la izquierda (`ResAlmaLeft`) y a 0,7 (`ResAlmaScale`); `AlmaSclTick` ya no la fuerza a 1 en la fase 12. Dibujo girando sobre su eje a 20°/s (`SketchSpeed`, función `SketchSpin`, llamada desde `AlmaSclTick`).
- **Final**: el panel no reaparece (`ResultsOutK` con fase ≥ 12); el anillo de carga del botón apretado se esconde con la placa (`BP_ShareButton_SC.PoseButton`: `SetVisibility(Slider)` con el mismo bool de la placa).
- **Hall**: ameba elegida al doble (`HallSoulBig` escala `TP_hall_soul_present` × `HallSoulScale` 2 al entrar a la fase 9; el anillo la sigue por su `Size`). Baldosas: brillo encendido × `GlowGain` 0,4 y con la textura (`GlowTexture` 0,8) en `M_Hall_Tile_SC`.
- **Alma audio-reactiva ×1,4** en la instancia de la Obra (`VOReactWobble` 1,19, `Bright` 0,49, `Size` 0,16, `Warm` 0,49).
- **Logos** en calidad alta (`TC_EditorIcon`, sin mips de streaming).
- Quest: desinstaladas las apps viejas (sequencer, recorrido, calibration, entering, TESTMESHES, heart) por pedido de Beltrán, sin respaldo. Queda solo `com.almadigital.soulcharger`.

## Después de la visita (14:40-15:30)
- La ameba del Hall desaparecía: `HallSoulScale` estaba en 0 en la instancia. Quitado (manda el TargetPoint que agrandó Beltrán). Las perillas de resultados también estaban en 0 (Alma invisible): corregidas.
- Zurdos: la Obra pasa la mano del Hall a Breath, Attracting y Drawing (ver `BP_Obra_SC.md`). El selector elige la ameba encendida más cercana a una mano (`BP_SoulPicker_SC.PickNearest`); antes ganaba la primera en orden si había dos encendidas, y por eso el color del HUD podía no ser el elegido.
- En paralelo: sesión del editor web con nodos (tarea aparte) y sesión de instrucciones con fantasmas (tarea aparte; pide el turno del editor a Narrativa).
