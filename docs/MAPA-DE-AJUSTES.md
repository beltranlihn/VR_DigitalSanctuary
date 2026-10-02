# Mapa de ajustes — Soul Charger

> Qué quieres cambiar → qué actor seleccionas → qué campo tocas. Actualizado 2026-10-01; **tiempos de la obra actualizados el 2026-10-02: ahora viven en `DA_Partitura_Obra`** (ver `docs/PARTITURA.md` y `docs/GUIA-DE-DIRECCION.md`).

## Reglas que valen para todo
- **Lo que ves es lo que se juega.** Cada cosa existe una sola vez, colocada donde aparece. En el juego, lo que no toca todavía está oculto; el código lo muestra en su momento y lo destruye cuando ya no se usa.
- **Altura:** lo que va a la altura de los ojos se autora para ojos a **120 cm sobre el piso del pawn**. En el visor se corrige solo con la altura real. En el PIE de escritorio, sin visor, esas cosas se ven 120 cm más abajo; es normal.
- **Ajustar un nivel de test es ajustar la Obra:** la Obra carga esos mismos niveles. Guarda el nivel después de cambiar algo.
- **Los actores con tag `TestOnly`** (`StageRunner`, `HallRunner`, `Alma_Ensayo`…) solo existen en los niveles de test: la Obra los destruye al arrancar, salvo lo que copia del `StageRunner`.
- **Colores en Details: son lineales** (el mismo número se ve más claro de lo que sugiere el selector).
- **Nada se aplica con el Play corriendo:** se ve en el siguiente Play.
- **Antes del APK:** `DebugStart` −1 en la Obra y en `HallRunner` · `bDebugEnding` false · `Speed` 1 · `bSimulated` según el destino.
## Cómo se prueba

| Quiero… | Dónde | Campo |
|---|---|---|
| Jugar una etapa sola, completa | su nivel de test (Test_Breath, Test_Heart, Test_Mind, Test_Sequencer, Test_Draw) | Play. Corre el ensayo `StageRunner`. |
| Jugar el Hall solo | Test_Hall | Play. `HallRunner` → `DebugStart` (−1 = desde el título; 2 portal · 3 timbre · 4 Alma · 5 sensor · 6 elección · 7 baldosas · 8 HUD · 9 salida) · `DebugSoul` = qué alma se asume |
| Jugar la Obra desde un punto | L_SoulCharger_Obra → `BP_Obra_SC` | `DebugStart`: 1 Hall desde el inicio (solo salta el aviso) · 2 portal · **3 timbre** · **4 justo dentro del Hall** (Alma aparece) · 5 sensor · 6 elección del alma · 7 baldosas · 8 nace el HUD · 9 Alma a la puerta de salida · 10-14 Entering (apertura · Alma · instrucciones · mecánica · salida y carga) · 20-24 Recognizing · 30-34 Loving · 40-44 Attracting · 50-54 Surrounding · 60 última carga · 61 regreso · 62 resultados · 63 SHARE · 64 constelación. `DebugSoul` = alma por defecto. **Dejar en −1 para el APK.** |
| Acelerar la Obra | `BP_Obra_SC` | `Speed` (1 = real; solo para probar) |

## Ver todo junto: la Obra con sus subniveles
- Abre `L_SoulCharger_Obra`. En el panel **Levels** están los 6 niveles de test como subniveles: Test_Breath, Test_Heart, Test_Mind, Test_Sequencer, Test_Draw y Test_Hall.
- Todos están en el mismo origen y se superponen, así que conviene ver **uno a la vez**: el ojo de cada fila lo muestra u oculta en el editor. Por defecto queda visible Test_Hall, que es donde ocurren el inicio y el final.
- Lo que mueves en un subnivel se guarda en ese nivel de test, y la Obra lo carga igual. Al guardar, Unreal pregunta qué niveles guardar: guarda los que tocaste.
- **Nivel actual:** el que está en negrita en Levels recibe lo que colocas nuevo. Déjalo en *Persistent Level* salvo que quieras agregar algo a una etapa (doble clic en su fila).
- En el juego nada de esto cambia: los subniveles son *Blueprint* y no se cargan solos; la Obra sigue cargando las etapas como siempre.
- **Por qué en el Outliner hay varios HUD, Almas, PlayerStart…** (revisado el 2026-10-01 con un censo del mundo de juego): cada nivel de test trae sus propias piezas para poder probarse solo. Las que solo sirven para eso están en la carpeta **`SoloPrueba`** (tag `TestOnly`; 19 en total: 7 en Test_Hall, 3 en Entering, 3 en Fluid y 2 en cada uno de Heart, Sequencer y TBTest). Al arrancar, la Obra las descarta y deja **una sola** de cada pieza que manda (Alma, HUD, FaceAnchor, BioHub, mando, pawn). Lo único que se repite en el juego son el PlayerStart y el Brush de cada nivel, que no pelean: el pawn nace en el PlayerStart de la Obra antes de que carguen las etapas. **No borres lo de `SoloPrueba`**: sin eso, los niveles de test dejan de andar solos.
- Carpetas de la Obra: `Obra` (director, HUD, Alma, FaceAnchor, mando, aviso, contenido del viaje) · `Obra/Puntos` (PlayerStart y puntos de Alma y de carga) · `Final` · `Credits`. Test_Hall: `Hall/Sistemas` · `Hall/Arquitectura` · `Hall/Almas` · `Hall/Puntos` · `Hall/Polvo` · `Ajustes`.

## La Obra (L_SoulCharger_Obra → `BP_Obra_SC`)
Lo que ajustas en un nivel de test llega solo a la Obra: la Obra carga esos mismos niveles.

| Quiero cambiar… | Actor | Campo | Nota / valor |
|---|---|---|---|
| Dónde entra Alma en cada etapa | en el nivel de test de la etapa | TargetPoint `TP_sc<K>_alma_in` | K = 0 Entering · 1 Recognizing · 2 Loving · 3 Attracting · 4 Surrounding |
| Dónde se hace a un lado Alma | nivel de test | `TP_sc<K>_alma_side` | |
| Dónde aparece el anillo de carga y su tamaño | nivel de test | `TP_sc<K>_charge` | la escala del TargetPoint = el tamaño del anillo |
| Dónde aparece el título de la etapa | nivel de test | `TP_sc<K>_title` | |
| Cuánto dura Alma / instrucciones / salida en cada etapa | `DA_Partitura_Obra` | `Alma_TrasVoz` (Alma = largo de su voz + esto) · `Instr_Dur[K]` · `Salida_Dur[K]` | la Obra y el ensayo leen la Partitura (desde 2026-10-02 el `StageRunner` ya no manda) |
| Color del velo de cada etapa (apertura y cierre) | `BP_Obra_SC` | `CTops` / `CHors` (arrays, uno por etapa) | lineales |
| Color de la carga de cada etapa | `BP_Obra_SC` | `StageCols` | |
| Duración de cada carga | `DA_Partitura_Obra` | `Carga_Dur` (4 / 4 / 4 / 4 / 6 s) | la última es la carga final; la rampa a negro la sigue sola (`Final_NegroRampa`) |
| Duración del aviso inicial | `DA_Partitura_Obra` · `BP_Obra_SC` | `Aviso_Dur` (19 s) · `bDisclaimer` (categoría Config; apagarlo lo salta) | el texto entra 0,5→2 s y sale 3,5→4,8 s (`BP_Disclaimer_SC.DiscStep`); si cambias `DiscTime`, mueve esos dos tramos |
| Tiempos del final | `DA_Partitura_Obra` (categoría 4 Final) | `Res_Tope` 150 · `Res_Explorar` 25 · `Res_Cortafuegos` 30 · `Comp_Nado` 4 · `Comp_Lejos` 3 · `Creditos_Dur` 60 · `Const_*` · `Regreso_*` | |
| Estrellas de la constelación | L_SoulCharger_Obra, carpeta Credits | 30 `StaticMeshActor` con tag `CreditStar` | se mueven a mano |
| Datos simulados (APK) | `BP_Obra_SC` (Config) · `DA_Partitura_Obra` | `bSimulated` · `Sim_EtapaMax` 90 | |
| Transición entre etapas | `DA_Partitura_Obra` (categoría 2 Cada etapa) | `Velo_CierreDur` 2,5 · `Etapa_TituloRevelaIni/Fin` 0,5→1,8 · `Etapa_TituloSaleIni/Fin` 4,6→5,6 · `Etapa_TituloOculto` 5,7 · `Alma_Entra` 5,5 · `Etapa_VeloAbreIni/Fin` 1→4 | valores medidos en el grafo el 2026-10-02 (la versión anterior de esta fila no coincidía con el código) |
| Música ambiente de cada escena | `BP_Obra_SC`, categoría **Ambientes** | `AmbClips` (9 clips, en orden: 1 Intro · 2 Start · 3 Hall · 4 Breath · 5 Heart · 6 Mind · 7 Surrounding · 8 Salida · 9 Credits) · `AmbVolumes` (uno por clip, 0,8) · `AmbFadeIn` / `AmbFadeOut` (3 s) | siempre en estéreo (2D). Qué clip suena en cada momento lo decide la obra por fase |

## El Hall (Test_Hall; la Obra lo carga igual)
| Quiero cambiar… | Actor | Campo | Nota / valor |
|---|---|---|---|
| Dónde parte el pawn y dónde se detiene | `HallDirector` | flechas `StopStart` · `StopDoor` · `StopInside` · `StopFar` · `StopReturn` · `StopCard` · `StopExit` | seleccionar el director y arrastrar la flecha; el pawn mira hacia la flecha |
| Cuánto duran las caminatas | `HallDirector` | `JourneyTime` 26 · `EnterTime` 7 · `OutTime` 11 · `ReturnTime` 8 · `ExitTime` 12 · `AccelTime` · `BrakeTime` | |
| Pausas y ritmo entre pasos | `HallDirector` | `IntroHold` 12 · `VOAir` 0,5 · todas las `Pace…` | |
| Cuánto esperan los cortafuegos | `HallDirector` | `FW_Bell` 25 · `FW_Tool` 20 · `FW_Choose` 25 · `BellHold` 3 | |
| Puertas | `HallDirector` | `DoorOpenDeg` · `DoorTime` · `DoorWarm` / `DoorCold` (color del vidrio) | |
| Baldosas | `HallDirector` | `TileLiftCm` · `TileGlowMax` · `TileTime` | |
| Nombres de etapa sobre las baldosas | `HallDirector` | componentes `Title0…Title4` (seleccionar en el panel de componentes y mover/escalar) | se ven en el editor |
| SOUL CHARGER / CENTER de las puertas | `HallTitle` (dos actores) | transform del actor · `RevealTime` · `OutTime` | se ven en el editor |
| Título SOUL CHARGER del inicio | `TituloInicio` (`BP_IntroTitle_SC`) | transform del actor · componentes `TitleP` (título) y `SubP` (bajada): mover, girar, escalar | es el título real; aparece a los 2,5 s y se va a los 13 s |
| Logos del título del inicio | `TituloInicio` → componentes `LogoADS` (Alma Digital) · `LogoJHU` (Johns Hopkins) · `LogoIDEAS` (Ideas Lab) | mover, escalar cada uno | aparecen de 6 a 8,6 s, escalonados, y se van con el título (10 a 12,5 s). Material `Obra/Titles/MI_Logo_*` (padre `M_TourLogo_SC`): `C0` = tinte, `U0`/`U1` = ancho del barrido |
| Sensor que invita a tomarlo: giro y orbe | `HallSensorOrb` (`BP_SensorOrb_SC`) | `SpinDeg` 15 (giro sobre su propio eje) · `OrbSize` 0,5 · `OrbOpacityCore` 0,02 · `OrbOpacityRim` 0,18 · `AppearTime` 1,6 · `BurstGrow` 0,3 · `BurstTime` 0,7 | el temblor del orbe: `MI_SensorOrb_SC` → `WobbleAmount` 0,01 · `WobbleSpeed` 0,3 · `RotAmount` 0 |
| Sensor en la mano (pose) | `HallDirector` → función `HallGrab` | derecha (4,325; −1,685; −2,335) roll 90 · izquierda (4,325; 1,685; −2,335) roll −90, relativo al grip | la misma pose que `UserTool` (`SensorXfR/L`) |
| Timbre: dónde, giro y tamaño | `Timbre` (`BP_BellArt_SC`) | transform del actor | el timbre real; oculto en el juego hasta el paso 6 |
| Sensor: dónde, giro y tamaño | `Sensor` (`BP_BioSensorArt_SC`) | transform del actor | el sensor real; oculto hasta el paso 12 |
| Almas candidatas: dónde | `HallSoul_0…4` | transform del actor | se quedan donde las dejes |
| Almas candidatas: color y tamaño | `HallSoul_0…4` | `CoreColor` · `EdgeColor` · `GradColorA/B` · `Size` 0,15 | 0 = la del centro, la que elige el cortafuegos |
| Dónde se presenta el alma elegida | `TP_hall_soul_present` | transform (la escala = el tamaño del alma) | |
| Dónde aparece Alma | `TP_hall_alma_center` · `TP_hall_alma_side` · `TP_hall_alma_exit` | transform | |
| Niebla del inicio | `HallFog` | `CTopFog` (arriba) · `CHorFog` (horizonte) · `FadeIn` · `FadeOut` | |
| Luz de afuera por la puerta de salida | `HallGlow` | | |

## El final (L_SoulCharger_Obra, carpeta `Final`; se ve con Test_Hall visible)
Todo está colocado donde aparece. Se prueba con `DebugStart` 62 (resultados), 63 (SHARE) y 64 (constelación): el pawn salta a `StopCard` / `StopExit`.

| Quiero cambiar… | Actor | Campo | Nota |
|---|---|---|---|
| Dónde está el cuadro de resultados y su tamaño | `Final_Cuadro` | transform del actor | oculto en el juego hasta los resultados. El contenido y la ventana de la melodía (gusano) lo siguen solos |
| Botones SHARE / DON'T SHARE | `Final_BotonShare` · `Final_BotonDontShare` | transform del actor | aparecen cuando Alma invita a compartir |
| Dónde se enciende el anillo junto al cuadro y su tamaño | `AnilloCarga` | transform del actor (la escala = el tamaño) | es el mismo anillo de las cargas de cada etapa; su posición en el editor solo cuenta para el final |
| Dónde aparece tu dibujo y su tamaño | TargetPoint `final_sketch` | transform (escala X × 55 cm = lado mayor del dibujo) | el dibujo lo hace el usuario en vivo; esto es su lugar |
| Dónde se pone Alma en los resultados y su tamaño | TargetPoint `final_alma` | transform (la escala = el tamaño de Alma) | |
| Por dónde nada el alma-pez al compartir | TargetPoints `final_fish_door` (la puerta) → `final_fish_away` (se aleja) | transform | sale del anillo, pasa por la puerta y se va. Tiempos: `SwimTime` 4 · `AwayTime` 3 en `BP_Obra_SC` |
| Dónde queda tu alma en la constelación y su tamaño | `Final_AlmaPez` | transform del actor (la escala = el tamaño) | solo si compartiste. Nunca va con el anillo: el anillo se apaga cuando nace el pez |
| Logos de los créditos | `Final_Creditos` → `LogoADS` · `LogoJHU` · `LogoIDEAS` | mover, escalar | pie bajo las tarjetas; aparecen de 15 a 17,6 s y se van con el título |
| Créditos: dónde y tamaño | `Final_Creditos` (carpeta Credits) | transform del actor · componentes `TitleP`, `SubP`, `Card0…5` | el actor está en los ojos de `StopExit` y los planos 4,5 m al frente. En el editor se ven el título, la bajada y la primera tarjeta (las 6 tarjetas van en el mismo lugar) |
| Estrellas | `CreditStar_00…29` (carpeta Credits) | transform | aparecen de a una en los primeros 5 s de la constelación |

- El pez y el anillo se turnan, nunca se ven juntos: en el regreso el pez nace donde estaba el anillo y el anillo se apaga; en los resultados el pez llega al anillo, se apaga y recién entonces se enciende el anillo (cruce de ~0,1 s); en SHARE se apagan los dos y nace solo el pez.
- Altura: todo esto va autorado para ojos a 120 cm sobre el piso. El cuadro hoy está 5 cm sobre los ojos de autor.

## Sonido
- **Ambientes:** estéreo, sin posición; se ajustan en `BP_Obra_SC` → categoría Ambientes (tabla de la Obra).
- **Sonidos de objetos:** suenan en el lugar del objeto con la atenuación compartida `/Game/SoulCharger/Core/Audio/ATT_Objeto_SC`. Por defecto suena pleno hasta 4 m y se apaga hacia los 36 m; si cambias ese asset, cambian todos. Tienen esa atenuación: timbre (`Bell`), puertas (`DoorOpen`), aparición y desaparición de luz (`SBubbleHoverOn`/`Out`), clic y apretar botón (`VR_click1`, `ChargeFinal`), cargas (`Charge1`, `ProtoHover`, `ProtoSelect`), mando (`Tomado`, `VR_shep_scale_down_02`) y los efectos del final (`FX_SOULSWIM`, `FX_SOULVANISH`, `FX_RINGVANISH`, `FX_SHAREAPPEAR`, `FX_SHARESELECT`).
- **Siguen en 2D a propósito:** las voces de Alma (VO), tus pasos (`Pasos`), los ambientes y el aviso inicial.
- Para que un sonido nuevo de objeto suene en el mundo: asígnale `ATT_Objeto_SC` en *Attenuation Settings* y tócalo con *Play Sound at Location* (o desde un componente del objeto).

## Aura de Alma (partículas)
Es un actor aparte (`BP_AlmaAura_SC`) que Alma crea al arrancar y lleva pegado. No hay actor en el nivel: se ajusta en el material **`Core/Alma/MI_AlmaAura_SC`** (marcar el casillero de cada parámetro):
- **1 - Nube:** `AuraAlpha` 0,35 (opacidad) · `SizeDeg` 0,16 · `SizeMinDeg` 0,10 · `SizeVar` 0,35 · `Twinkle` 0,45 · `ShellScale` 1 (radio del cascarón) · `Breath` 0,03 · `ColA`/`ColB` · `AuraGlow` 1.
- **2 - Curl:** `CurlAmp` 5,5 · `CurlFreq` 1,6 · `FlowSpeed` 0,35 · `SwirlSpeed` 0,08.
- **3 - Voz:** `SpeakCurl` 0,6 · `SpeakExpand` 0,05 · `SpeakGlow` 0,6.
- En `BP_AlmaAura_SC` (Class Defaults): `AuraSpeakRate` 1,2 · `bPreviewOnly` (true apaga todas las auras). En `BP_Alma_SC`, categoría I - Voz: `VOReact`, `VOAttack`, `VORelease`, `VOGain`. Apagar el aura sin tocar grafos: `AuraAlpha` 0.
- Para verla sin Play: arrastrar un `BP_AlmaAura_SC` al nivel con `bPreviewOnly` true (se destruye al dar Play) y sacarlo después.

## No ajustable hoy
- La pose del HUD (va pegado al pawn; es de Mesh 3D).

---

# Las 5 etapas

**Cómo leer este mapa**
- La Obra (`L_SoulCharger_Obra`) carga los 5 niveles de test tal como están guardados en disco: **ajustar la instancia en el nivel de test es ajustar la Obra**. Después de cambiar algo: **guardar el nivel** (la Obra lee el `.umap`, no el editor).
- **Excepción: los actores con tag `TestOnly` se destruyen al arrancar la Obra** (`StageRunner`, `Alma_Ensayo`, `Entering_UserTool`, `Loving_Ganzfeld`). Lo que se ajuste en ellos no llega a la Obra, salvo lo que la Obra copia del `StageRunner` (ver §0).
- Las etiquetas de actor salen de los trackers y de los `.umap`. Si dice "(etiqueta por confirmar)", buscar por la clase en el Outliner.
- Si una perilla aparece en 0 o vacía en la instancia cuando el tracker dice otro valor, es la trampa "instance-editable nace en cero": escribirla a mano.
- Los valores "actuales" son los documentados en los trackers al 2026-10-01. Puede que Beltrán los haya cambiado después en el editor: **lo que diga el panel Details manda**.

---

### 0. Común a las 5 etapas: el ensayo y sus marcas (`BP_StageRunner_SC`)

Cada nivel de test tiene un `StageRunner` (TestOnly + TOUR) y 4 TargetPoints **sin** TestOnly: `TP_sc<K>_alma_in`, `TP_sc<K>_alma_side`, `TP_sc<K>_charge` y `TP_sc<K>_title`. K = 0 Entering · 1 Recognizing · 2 Loving · 3 Attracting · 4 Surrounding. **La Obra lee los 4 TP**, así que moverlos en el nivel de test mueve la Obra.

**Alturas:** todo TP se lee relativo a los ojos: z en juego = z del TP + (z de la cámara − (z del PlayerStart + 120)). Si subes un TP 20 cm en el editor, en el visor sube 20 cm, sea cual sea la altura de la cabeza.

| Quiero cambiar… | Nivel | Actor (Outliner) | Campo (categoría) | Nota / valor actual |
|---|---|---|---|---|
| Dónde aparece Alma al recibir | test de la etapa | `TP_sc<K>_alma_in` | Transform (posición) | Base de referencia: 220 / 0 / +5 respecto del PlayerStart |
| Dónde se hace a un lado Alma (instrucciones) | test de la etapa | `TP_sc<K>_alma_side` | Transform (posición) | Base: 140 / −300 / +20 |
| Dónde aparece el anillo de carga y **de qué tamaño** | test de la etapa | `TP_sc<K>_charge` | Transform (posición **y escala**) | Base: 253 / 0 / +37, escala 2,115 (la pose aprobada en Test_Hall). El anillo mira a la cámara |
| Dónde aparece el título de la etapa | test de la etapa | `TP_sc<K>_title` | Transform (posición) | Base: 300 / 0 / 0. En la Obra el título queda exactamente en el TP |
| Cuánto dura la bienvenida de Alma | — | `DA_Partitura_Obra` | `Alma_TrasVoz` 3 | Alma = largo de su voz + `Alma_TrasVoz`, en la Obra y en el ensayo |
| Cuánto duran las instrucciones y la salida | — | `DA_Partitura_Obra` | `Instr_Dur[K]` (8,5 / 6 / 6 / 6 / 0,6) · `Salida_Dur[K]` 2,5 | la Obra y el ensayo |
| Color del velo que abre la etapa | test de la etapa | `StageRunner` | `CTop` / `CHor` (Ensayo) | **La Obra los copia** (= el cielo real de cada etapa) |
| Imagen del título | asset `MI_TourTitle_<ETAPA>` | — | parámetros del MI | El runner lo referencia en `TitleMI`; la Obra usa el mismo asset |
| Velocidad del ensayo / bucle | test de la etapa | `StageRunner` | `Speed` 1 · `Loop` true (Ensayo) | Solo el ensayo; no afecta a la Obra |
| Cuándo se le pide a la etapa que cierre | — | `DA_Partitura_Obra` | `Etapa_Tope[K]` (240 / 180 / 120 / 240 / 205) · `Corte_Espera` 30 | la Obra y el ensayo le piden `StageRequestEnd()`: la etapa cierra por su propio camino (Attracting guarda, Surrounding presenta) |

**No ajustable hoy (común)**
- Del `StageRunner` solo llegan a la Obra `CTop`/`CHor`. Sus tiempos vienen de la Partitura (los campos `AlmaTime`/`InstrTime`/`OutroTime`/`TimeoutS`/`ChargeTime` ya no se editan en el nivel).
- `EyeRef` 120: supuesto compartido con la Obra, no cambiar.
- La web del prototipo no se actualiza sola: después de mover TPs hay que re-exportar (`ensayo_export.py` → `gen_ensayo_js.py`).
- Visor: el ensayo solo se probó en PIE en Test_Breath y Test_Sequencer; Test_Heart, Test_Mind y Test_Draw están colocados sin correr.

---

### 1. Entering (respiración) — `/Game/SoulCharger/Mechanics/Breath/Maps/Test_Breath`, K = 0

#### Posición y tamaño
| Quiero cambiar… | Nivel | Actor (Outliner) | Campo (categoría) | Nota / valor actual |
|---|---|---|---|---|
| Dónde flota el metaball | Test_Breath | `Entering_Blob` | Transform (posición) | (380, 0, 125). ⚠ A menos de ~2,5 m del usuario la cámara entra en su proxy y deja de verse. No escalar el actor |
| Tamaño del metaball | Test_Breath | `Entering_Blob` | `SizeCM` (categoría por confirmar) | 220. El Construction Script pisa la escala del actor: el tamaño se ajusta acá |
| Dónde está el pacer y su tamaño | Test_Breath | `Entering_Pacer` | Transform + `SizeCm`, `LineWidth`, `ClearCenter` (B - Forma) | (200, 0, 70), Pitch 90, centrado en el metaball · `SizeCm` 350 · `LineWidth` 0,008 · `ClearCenter` 0,62 |
| Colinas más cerca o más altas | Test_Breath | `Entering_Valle` | `HillNear` 4500 · `HillAmp` 2200 (1-Colinas); `FarBase`/`FarAmp` (2-Lejos) | Escala del actor = 1 siempre (se puede girar en yaw). El actor está en z −90,4 (puesto a mano) |
| Sombra del metaball en el piso | Test_Breath | `Entering_Valle` | `bShadow` · `ShadowRadius` 85 · `ShadowStrength` 1,5 (8-Sombra) | Sigue sola al metaball (nace y se va con él) |
| Forma del aliento (cono y pluma) | asset `MI_BreathAir_SC` | (lo usa `Entering_Aire`) | `InSpreadH` 18 · `InSpreadV` 8 · `OutStart` 40 · `PlumeLen` 95 · `OutSizeCm` 0,22 · `OutAlpha` 0,45 | Boca: `MouthFwd` 6 / `MouthDown` 9 (A-Aliento) en `Entering_Aire` |

#### Color y luz
| Quiero cambiar… | Nivel | Actor (Outliner) | Campo (categoría) | Nota / valor actual |
|---|---|---|---|---|
| Color y brillo del metaball | Test_Breath | `Entering_Blob` | `ColorLight` (0,92, 0,945, 1) · `ColorShadow` (0,026, 0,013, 0,12) · `Brightness` 1,546 (categoría por confirmar) | Manchas de color: `FlowAmt` 0,6 · `FlowScale` 0,12 (G - Movimiento) |
| Color del pacer | Test_Breath | `Entering_Pacer` | `PacerColor` / `AccentColor` (1, 1, 1) · `Brightness` 1,43 · `Opacity` 0,85 · `EmissiveAlpha` 0 (C - Color) | `EmissiveAlpha` 0 = velo blanco correcto sobre el valle; en 1 se ve gris |
| Luz y colores del valle | Test_Breath | `Entering_Valle` | `ColLit` · `ColShadow` · `ColSheen` · `Sheen` 0,28 · `LightAz` 20 · `LightEl` 25 (4-LuzColor) | Se ve en vivo en el viewport |
| Cielo, luna y niebla | Test_Breath | `Entering_Valle` | `SkyZenith` / `SkyHorizon` / `SkyGlow` · `GlowAmt` 0,8 (5-Cielo) · `MoonAz` −40 · `MoonEl` 7 · `MoonRadius` 9 · `MoonOpacity` 0,55 · `MoonColor` (6-Luna) · `FogStart` 800 · `FogDist` 20000 · `FogMax` 0,93 (7-Niebla) | |
| Color del sensor en esta etapa | Test_Breath | `Entering_Stage` | `SensorColor` (0,35, 0,7, 1) (0-Contrato) | Azulado; lo manda al mando/sensor de la Obra |
| Intensidad del aliento y del polvo | Test_Breath | `Entering_Aire` / `Entering_Vida` | `AirAmount` 1 (A-Aliento) · `VidaAmount` 1 (A-Vida) · `GustLight` 2,8 (B-Rafagas) | 0 = apagado. Brillo del polvo: `DustAlpha` / `SunBase` en `MI_ValleyDust_SC` |

#### Tiempos y ritmo
| Quiero cambiar… | Nivel | Actor (Outliner) | Campo (categoría) | Nota / valor actual |
|---|---|---|---|---|
| Tiempos de la respiración guiada | Test_Breath | `Entering_Pacer` | `InhaleTime` / `Hold1Time` / `ExhaleTime` / `Hold2Time` = 4-3-4-3 · `Cycles` 5 (A - Ritmo) | `Preset` tiene que quedar en 0 (si no, pisa los tiempos). ⚠ Los sonidos del pacer están hechos para 4-3-4-3 |
| Pausas y halo del pacer | Test_Breath | `Entering_Pacer` | `LeadIn` / `LeadOut` 3 s (A - Ritmo) · `HaloStrength` 0,55 · `HaloFadeOut` 1,5 (F - Halo) | Progreso: `bShowProgress` · `ProgRadius` −0,035 (G - Progreso) |
| Exploración libre y cuenta regresiva | Test_Breath | `Entering_Stage` | `ExploreTime` 12 · `CountTime` 3 · `ToolDelay` 0,8 (0-Contrato) | De `StageBegin` al fin ≈ 88 s |
| Entrada y salida del metaball | Test_Breath | `Entering_Blob` | `IntroTime` 2,5 · `OutroTime` 2,5 · `MorphRadius` 0,08 · `MorphSpread` 1,9 · `MorphScale` 0,5 (F - Entrada Salida) | Nace por morfeo (gotas chicas que crecen y se funden) |
| Ondulación de las lomas | Test_Breath | `Entering_Valle` | `MorphAmt` 0,45 · `MorphSpeed` 2 · `SwellAmp` 2800 · `SwellSpeed` 2 · `ExhaleSwell` 3 · `SwellFollow` 0,6 (3-Movimiento) | ⚠ Por encima de los topes de confort (decisión de Beltrán). Si marea: bajar primero `SwellSpeed`. No cambiar los `*Speed` con el visor puesto (la fase salta) |
| Ráfagas de viento | Test_Breath | `Entering_Vida` | `FirstGap` 14 · `GapMin` / `GapMax` 20 / 40 s · `GustAmount` 1 (B-Rafagas) · `BreathEvery` 2 (C-Soplo) · `GustVolume` 0,8 (D-Sonido) | |

#### Mecánica
| Quiero cambiar… | Nivel | Actor (Outliner) | Campo (categoría) | Nota / valor actual |
|---|---|---|---|---|
| Qué tan fácil entra el umbral (panza) | Test_Breath | `Entering_BreathRig` | `SafeHorizMax` 23 · `SafeVDropMin/Max` 33 / 63 · `StillLin` / `StillAng` 14 / 45 · `ActivateDelay` 1,5 · `FacingMin` 0,34 (A - Umbral) | Valores del manager, validados en visor; confirmar en la instancia |
| Qué tan rápido sigue el metaball a la respiración | Test_Breath | `Entering_BreathRig` | `BreathFollowTime` 3,0 · `BreathFollowAttack` 0,12 · `RangeTau` 6 · `SignedGain` 1 (D - Salida) | `BreathFollowTime` = segundos para llegar al extremo |
| Cuánto reacciona el metaball | Test_Breath | `Entering_Blob` | `BreathSpreadIn` −0,85 · `BreathSpreadOut` 0,6 · `BreathCurlIn` −0,7 · `BreathRadiusOut` −0,15 · `BreathBrightOut` 0 (R - Respiracion) | Más negativo al inhalar = más redondo y quieto |
| Vibración | Test_Breath | `Entering_BreathRig` | `HapticAmp` 0,25 · `bHaptics` (C - Haptica) | |

**No ajustable hoy (Entering)**
- **Mando y sensor en la mano:** `Entering_UserTool` es TestOnly. En la Obra manda `UserTool_Obra` del persistente `L_SoulCharger_Obra` (`SensorXfR/L`, `LightColor`, `MorphTime`, categoría A-Herramienta). La pose del sensor en la mano está sin validar en visor.
- **Sonidos del pacer** hechos para 4-3-4-3: si cambian los tiempos hay que regenerarlos (`make_pacer_sounds.py`).
- **Capa viva del valle** (`FogBreath`, `GlowBreath`, `ShadowBreath`, `WarmBreath`, `LiveTau`, `L-Respira`): no es instance-editable, solo en Class Defaults de `BP_BreathValley_SC`.
- `MI_BreathValley_SC` no tiene overrides a propósito: el look se ajusta en las perillas del actor (que pisan el MI).
- Escala del valle y del aliento = 1 (los shaders asumen cm locales). El metaball no se escala por el actor.
- `EdgeAA` (1,5, borde del metaball) vive en el material maestro `M_BreathBlob_SC` (E - Calidad), no en el actor. Los bordes internos entre lóbulos no tienen perilla.
- No colocar `BP_BreathManager_SC` en el mismo nivel que el rig (los dos escriben `MPC_Breath`).
- Mano izquierda solo probada en PIE. `bContractTest` y `bShowMandoOnBegin` en false al guardar; `PreviewBreath` en 0 antes de empaquetar.

---

### 2. Recognizing (latido) — `/Game/SoulCharger/Mechanics/Heart/Maps/Test_Heart`, K = 1

#### Posición y tamaño
| Quiero cambiar… | Nivel | Actor (Outliner) | Campo (categoría) | Nota / valor actual |
|---|---|---|---|---|
| Dónde están la esfera y el mar | Test_Heart | `HeartScape` | Transform (posición, yaw) | (600, 0, −20): esfera 6 m al frente. Escala del actor = 1 siempre. ⚠ Durante la vuelta el actor se mueve y gira solo desde esa base |
| Tamaño y altura de la esfera central | Test_Heart | `HeartScape` | `HeartSize` 68,1 · `HeartHeight` 113 (3 - Esfera central) | Valores de Beltrán |
| Cuánto se hunde con cada latido | Test_Heart | `HeartScape` | `HeartPush` 24,4 · `HeartSquash` 0,06 · `WellRest` 3 · `WellPush` 10 · `HeartGrow` · `HeartAmoeba` (3 - Esfera central) | `HeartPush` es de Beltrán |
| La ola | Test_Heart | `HeartScape` | `WaveSpeed` · `WaveHeight` / `WaveHeightFar` · `WaveWidth` · `WaveReach` · `WaveHills` (2 - Ola) | |
| Las lunas que emergen | Test_Heart | `HeartScape` | `SizeMin` / `SizeMax` 8 / 60 · `SpawnMin` / `SpawnMax` 300 / 1500 · `OrbClearance` 500 · `OrbRise` 700 · `OrbAmoeba` 0,08 · `AmebaMix` (4 - Esferas que emergen) | `OrbAmoeba` es de Beltrán |
| Altura y sentido de la vuelta | Test_Heart | `HeartScape` | `OrbitRise` 400 cm · `OrbitSpin` 1 (+1 antihoraria, −1 horaria) (5 - Vuelta) | ⬜ Sin PIE ni visor |

#### Color y luz
| Quiero cambiar… | Nivel | Actor (Outliner) | Campo (categoría) | Nota / valor actual |
|---|---|---|---|---|
| Colores de la membrana | Test_Heart | `HeartScape` | `ColorLight` (0,96/0,84/0,80) · `ColorShadow` (0,34/0,07/0,09) · `ColorSheen` · `ColorGlow` (1/0,34/0,28) (5 - Colores de la membrana) | Paleta blanca-rojiza del 09-30 |
| Línea de cresta | Test_Heart | `HeartScape` | `ColorCrest` (1/0,78/0,72) · `CrestLine` · `CrestLineWidth` · `CrestGlow` (5 - Colores de la membrana) | |
| Colores de la esfera (y de las lunas) | Test_Heart | `HeartScape` | `HeartColor` · `HeartColorShadow` · `HeartColorCore` (1/0,62/0,56) · `HeartColorRim` (1/0,52/0,48) (6 - Colores de la esfera) | |
| Cielo y niebla | Test_Heart | `HeartScape` | `SkyColorTop` · `SkyColorHorizon` (0,95/0,85/0,83) · `SkyColorGlow` · `HorizonGlow` · `FogStart` · `FogDistance` (7 - Horizonte y niebla) | |
| Color del sensor en esta etapa | Test_Heart | `HeartManager` | `SensorColor` (1, 0,34, 0,28) (categoría por confirmar) | Rojizo. ⬜ Sin ver en la Obra |
| Forma fina (pozo, oleaje, luz rasante) | asset `MI_HeartScape_SC` | (vía `LookMI` de `HeartScape`) | grupos `1` a `8` | Lo que es perilla del actor pisa al MI |

#### Tiempos y ritmo
| Quiero cambiar… | Nivel | Actor (Outliner) | Campo (categoría) | Nota / valor actual |
|---|---|---|---|---|
| Largo de la etapa | Test_Heart | `HeartManager` | `StageBeats` 38 (categoría por confirmar) | ~38 s a 60 lpm; ~76 s con el respaldo a 30 lpm; más lo que dure la vuelta |
| En qué latido empieza la vuelta | Test_Heart | `HeartManager` | `OrbitAtBeat` 19 (0 = sin vuelta) | La etapa espera a que termine la vuelta para cerrar |
| Duración de la vuelta | Test_Heart | `HeartScape` | `OrbitTime` 60 s (5 - Vuelta) | Con 60 s: giro medio 6°/s, pico 11,2°/s; subida pico 12,5 cm/s |
| Suavidad del pulso | Test_Heart | `HeartScape` | `PulseRise` 0,45 s (1 - Latido) · `PushSpeed` 1 (3 - Esfera central) | |
| Cuánto tarda la esfera en brotar y hundirse | Test_Heart | `HeartScape` | `EntryTime` 2,5 s (3 - Esfera central) | |
| Latido de respaldo sin sensor | Test_Heart | `HeartManager` | `BackupAfter` 8 s (categoría por confirmar) | Si no hay latidos en 8 s fuerza la zona |

#### Mecánica
| Quiero cambiar… | Nivel | Actor (Outliner) | Campo (categoría) | Nota / valor actual |
|---|---|---|---|---|
| Zona del pecho | Test_Heart | `HeartManager` | `HeartHorizMax` 25 · `HeartVDropMin/Max` 10 / 45 · `StillLin` / `StillAng` 14 / 45 · `ActivateDelay` 1,5 (A - Zona) | `VDrop` puestos a ojo, sin datos de calibración |
| Vibración y sonido del latido | Test_Heart | `HeartManager` | `bHaptics` · `HapticAmp` 0,25 · `bSound` · `HeartBeatSound` (C - Feedback) | |

**No ajustable hoy (Recognizing)**
- `BeatDivider` (HeartScape) y `BeatDiv` (HeartManager): dejar en **1** (un pulso visual por cada latido que suena, nunca doble).
- `bDemo` en false en `HeartScape` (en true mete latidos propios sin sonido). `bFakeBeat` false, `HeartVDropMin` 10 y `bIgnoreTracking` false (los valores de escritorio no se guardan).
- Grupo `9 - Interno` de `MI_HeartScape_SC`: lo escribe el actor. `PreviewIntensity`, `DemoVariation`, `WellRadius` y `OrbMax` se leen del MI, no son perillas.
- Sin sensor real el BioHub publica 0 y el ritmo queda en 30 lpm. En la Obra, `bSimulated` prende la señal falsa de todos los BioHub.
- La vuelta (`5 - Vuelta` + `OrbitAtBeat`) está construida pero sin PIE ni visor.
- No hay rangos de slider en el panel (usar la tabla del MI).

---

### 3. Loving (mente) — `/Game/SoulCharger/Mechanics/Mind/Maps/Test_Mind`, K = 2

#### Posición y tamaño
| Quiero cambiar… | Nivel | Actor (Outliner) | Campo (categoría) | Nota / valor actual |
|---|---|---|---|---|
| Dónde está la célula | Test_Mind | `LovingCell` | Transform | (200, 0, 115), yaw 180 (su +X mira al usuario). Sube 10 cm al entrar y 15 al salir |
| Tamaño del núcleo y de las bolas | Test_Mind | `LovingCell` | `CentreRadius` 16 cm · `GroupSize` 1 (bola = 3,4 cm × GroupSize) · `SizeVariation` 0,5 (2-Forma) | |
| Cuántos grupos y a qué distancia | Test_Mind | `LovingCell` | `GroupCount` 5 (hasta 10) · `DistSeparated` 82 · `DistConnected` 38 · `GroupSpread` 1 · `FigureTilt` 15° (2-Forma) | |
| Envoltura exterior | Test_Mind | `LovingCell` | `OuterOpacity` 0,01 · `OuterBody` 60 · `OuterSoftness` 1 · `OuterWobble` 0,2 · `OuterMargin` 3 (6-Envoltura) | `OuterOpacity` 0 = oculta, costo cero |
| Amebas del fondo (cantidad y tamaño) | Test_Mind | `Fluid` (etiqueta por confirmar; clase `BP_FluidMedium_SC`) | `MidCellCount` 5 · `MidCellScale` 1,1 · `MidCellRange` 1800 · `FarCellCount` 20 · `FarCellSize` 80 (4-Celulas) | |
| Partículas del agua | Test_Mind | ídem | `NearSize` / `MidSize` / `FarSize` 0,45 / 1,3 / 6 · alfas 0,45 / 0,45 / 0,35 · `Bokeh` 3 (3-Particulas) | |

#### Color y luz
| Quiero cambiar… | Nivel | Actor (Outliner) | Campo (categoría) | Nota / valor actual |
|---|---|---|---|---|
| Colores de la ameba | Test_Mind | `LovingCell` | `AmoebaColor1` #F7ECFB · `AmoebaColor2` #B095D5 · `ShadowColor` #4B3C5D (7-Color) | Paleta morada del 09-30 |
| Membranas y partículas de la célula | Test_Mind | `LovingCell` | `MembraneColor` #E8D8F0 · `MembraneRim` #BFA2D5 (7-Color) · `OuterColor` #C6B0D7 (6-Envoltura) · `DustColor` #DECBE7 · `DustOpacity` (5-Particulas) | |
| Cáusticas del agua sobre la célula | Test_Mind | `LovingCell` | `WaterLight` (0,5) · `WaterLightShell` (8-Agua) | 0 = apagada; 2-3 = se lee fuerte |
| Color del agua | Test_Mind | `Fluid` (por confirmar) | `FluidTop` #362E3E · `FluidMid` #241E2A · `FluidBottom` #131115 (2-Liquido) | |
| Luz desde arriba, haces y cáusticas | Test_Mind | ídem | `GlowColor` #D3C3D9 · `GlowAmount` 0,32 · `GlowPower` 4 (2-Liquido) · `ShaftAmount` 0,14 · `VeilAmount` 0 · `CausticAmount` 0,22 · `CausticScale` 38 (5-Luz) | |
| Color de las amebas del fondo y motas | Test_Mind | ídem | `CellHigh` #C0ACCC · `CellLow` #342A3E · `CellFill` #3B3047 · `CellContrast` 0,7 (4-Celulas) · `MoteColor` #DDCAE6 · `MoteBright` 0,75 (3-Particulas) | |
| Profundidad y bruma | Test_Mind | ídem | `AbsorbDist` 650 · `AbsorbMax` 0,95 (2-Liquido) | |

#### Tiempos y ritmo
| Quiero cambiar… | Nivel | Actor (Outliner) | Campo (categoría) | Nota / valor actual |
|---|---|---|---|---|
| Largo de la mecánica | Test_Mind | `LovingCell` | `StageDuration` (9-Etapa; la instancia tiene 60) | La Obra le pide cerrar a `Etapa_Tope[2]` 120 s |
| Entrada y salida de la célula | Test_Mind | `LovingCell` | `IntroTime` 3 · `OutroTime` 3 · `SndVolume` 0,8 (9-Etapa) | |
| Viaje hacia adelante | Test_Mind | `Fluid` (por confirmar) | `TravelSpeed` 25 cm/s · `TravelEase` 4 · `TravelEaseOut` 2 · `TravelYaw` −180 (7-Viaje) | En el viewport se ve siempre, para ajustar mirando |
| Corriente y remolinos | Test_Mind | ídem | `CurrentSpeed` 2,5 · `FlowSpeed` 0,1 · `Turbulence` 0,45 (1-Movimiento) · `ActiveBoost` 2 (0-EEG) | `ActiveBoost` = cuánto se acelera el mundo cuando la ameba está activa |
| Qué tan viva o agitada | Test_Mind | `LovingCell` | `ActivityDrive` 1 · `StateSmoothing` 1,2 (1-Estado) · `NoiseAmount` · `OrganicMotion` · `PulseSpeed` · `StrandCurl` (4-Vida) | |

#### Mecánica
| Quiero cambiar… | Nivel | Actor (Outliner) | Campo (categoría) | Nota / valor actual |
|---|---|---|---|---|
| Manos que revuelven el agua | Test_Mind | `Fluid` (por confirmar) | `bHandStir` true · `StirStrength` · `StirRadius` · `StirSwirl` · `HandMaxSpeed` 300 (6-Manos) | ⬜ Sin visor con mandos |
| Contraste activo/calma del agua | Test_Mind | ídem | `EEGFlow` 1,0 · `EEGClarity` · `EEGSmoothing` 1,5 (0-EEG) | |

**No ajustable hoy (Loving)**
- La actividad no viene de un sensor: la célula la genera sola en `StageBegin` y la copia al fluido (`StageCouple`). `EEG` / `bFakeEEG` del fluido y `GlobalState` de la célula los pisa el código: no tocarlos.
- El fluido va en el origen con rotación identidad (todo en espacio local).
- `Loving_Ganzfeld` es TestOnly y está oculto: no existe en la Obra.
- `LightDir` de los materiales de la célula y `OuterLook` / `OuterSh` de `M_LovingOuter_SC` son defaults de material (afectan a todos los niveles), no perillas de la instancia. El orden de dibujo de la envoltura (40) está en código.
- Las motas cercanas se dibujan por delante de manos y HUD: arreglarlo pide tocar `Core/` (coordinar).
- `WaterLight` tiene que quedar en 0 en cualquier nivel sin fluido. Todo sin visor.

---

### 4. Attracting (secuenciador) — `/Game/SoulCharger/Mechanics/Sequencer/Maps/Test_Sequencer`, K = 3

#### Posición y tamaño
| Quiero cambiar… | Nivel | Actor (Outliner) | Campo (categoría) | Nota / valor actual |
|---|---|---|---|---|
| Mover, girar o escalar el gusano y sus 8 slots | Test_Sequencer | `GAL_12_BlobChain` | Transform | Los slots son hijos del gusano: se mueven con él. No mover slots sueltos |
| Dónde reaparece la mesa después del SAVE | Test_Sequencer | `GAL_12_FinalTP` (TP `seq_final_attracting`) | Transform completo (posición, giro, escala) | La escala del TP escala el gusano (1,555). El pivote es `GAL_12_Sequencer` |
| Centro del domo de esferas | Test_Sequencer | `GAL_12_OrbDirector` | Transform del actor | (362700, 100000, 120). Moverlo o girarlo mueve todas las esferas (previa y juego). `GroupOffset` (z 43) suma encima |
| Forma del domo | Test_Sequencer | `GAL_12_OrbDirector` | `OrbCount` 68 · `DomeRadius` (~976 cm) · `DomeElevMin` / `DomeElevMax` 0 / 80° · `DomeArc` 360° · `Spread` / `SpreadSeed` (5-Constelacion) | `DomeRadius` + desorden < `TraceDistance` 2500 del rig. `Spread.z` sugerido 40-60 |
| Tamaño de las esferas | Test_Sequencer | `GAL_12_OrbDirector` | `ScaleMin` / `ScaleMax` (2-Esfera) · `AnchorScale` 0,13 (tamaño al anclar, igual para todas) | |
| Grosor y fusión del gusano | Test_Sequencer | `GAL_12_BlobChain` | `BlobRadius` 8,5 · `Smooth` 17,68 · `OrbFuse` 0,872 (0-Config) | Con `BlobRadius` < ~6,9 las gotas se separan |
| Botón SAVE en la mano de apoyo | Test_Sequencer | `GAL_12_SeqRig` | `BtnOffset` (0-Rig) | (5,57, 0,8, −2,08), escala 0,4. Mando: `QCtrlLocR` / `QCtrlRotR` / `QCtrlScale` 1,0875 |

#### Color y luz
| Quiero cambiar… | Nivel | Actor (Outliner) | Campo (categoría) | Nota / valor actual |
|---|---|---|---|---|
| Paleta de las esferas | Test_Sequencer | `GAL_12_OrbDirector` | `Color1..4` (#f6e2b8 · #f3d0ac · #fbeedb · #eec6a0) · `ShadeColor` #e3c29f · `ShadowColor` #d7b699 · `OwnShade` 1 · `OwnShadeDepth` 0,7 · `ShadeFloor` 0,45 · `ShadowTint` 0,15 · `Brightness` 1,15 (1-Color) | Paleta Uyuni. `Seed` (0-General) resortea qué color le toca a cada esfera |
| Color del gusano | Test_Sequencer | `GAL_12_BlobChain` | `ColorLow` #e5c6a3 · `ColorHigh` #fff3e2 · `ChainBrightness` 1,25 · `ColorPulse` (0-Config) | El tinte al sonar sale del color de cada esfera |
| Cielo y sal | Test_Sequencer | `GAL_12_ChladniFloor` | `SkyTop` #efe0d0 · `SkyMid` #f6dcc2 · `SkyHorizon` #fce9c6 · `SunColor` #fff2d8 · `SunAzimuth` −24 · `SunElevation` 2,5 · `SunSize` 7 · `Haze` · `FogDistance` 2600 (5 - Cielo) · `SaltLit` #fffaf2 · `SaltShade` #efe3d4 · `FlatTone` 0,7 · `Wetness` 0,45 (3 - Salar) | Piso blanco liso: `FloorPattern` false (1 - Figura) |
| Halo de partículas de las esferas | Test_Sequencer | `GAL_12_OrbDirector` | `HaloOn` · `HaloAlpha` 0,45 · `HaloRate` 9 · `HaloSizeMin/Max` 1,6 / 2,8 · `HaloRadius` 1,3 · `HaloNoise` 6 (9-Halo) | En PIE se ve la próxima vez que un halo se prende |
| Color del mando y del láser | Test_Sequencer | `GAL_12_SeqRig` | `CtrlColor` #ffdcb4 (0-Rig) · `PtrColor` #ffdcb4 · `PtrLen` 40 · `PtrWidth` 0,45 · `PtrOpacity` 0,58 (1-Puntero) | |

#### Tiempos y ritmo
| Quiero cambiar… | Nivel | Actor (Outliner) | Campo (categoría) | Nota / valor actual |
|---|---|---|---|---|
| Cierre después del SAVE | Test_Sequencer | `GAL_12_Sequencer` | `FinalPasses` 2 · `ExitTime` 1,5 · `bReplayOnSave` true · `PadFadeIn` 1 · `PadFadeOut` 2 (0-Config) | |
| Aparición de la mesa en la intro | Test_Sequencer | `GAL_12_Sequencer` | `IntroOrbsAt` 1,2 s · `IntroToolsAt` 2,4 s · `OutroStep` 0,5 (categoría por confirmar) | |
| Sonidos del pad y de las esferas | Test_Sequencer | `GAL_12_OrbDirector` | `PadSound` (PadM1) · `OrbClips` (los 20 de Module1) (9-Sonido) | La esfera *i* suena `OrbClips[i % N]` |
| Giro y movimiento de las esferas | Test_Sequencer | `GAL_12_OrbDirector` | `SpinSlow` / `SpinFast` 22 / 150 °/s · `SpinAccel` 4 (4-Giro) · `GrabSpeed` 1,5 · `ReturnSpeed` 1,5 (7-Movimiento) · `WobbleAmp` / `WobbleFreq` / `WobbleSpeed` (3-Forma) | |
| Vida del gusano | Test_Sequencer | `GAL_12_BlobChain` | `FloatAmount` / `FloatSpeed` · `SwellAmount` / `SwellSpeed` · `PulseSmooth` · `PulseAmount` (0-Config) | |

#### Mecánica
| Quiero cambiar… | Nivel | Actor (Outliner) | Campo (categoría) | Nota / valor actual |
|---|---|---|---|---|
| Cono de partículas al agarrar | Test_Sequencer | `GAL_12_OrbDirector` | `AttractOn` · `AttractRate` ~120 · `AttractSpeed` 25 · `AttractStop` ~20 · `AttractAlpha` (6-Particulas) | Reentrar a PIE para ver el cambio |
| Alcance del láser y mano | Test_Sequencer | `GAL_12_SeqRig` | `TraceDistance` 2500 · `bRightHanded` (0-Rig) | |
| Encaje en slot y tamaño al volver | Class Defaults de `BP_SoundOrb_SC` | (las esferas se spawnean, no hay instancia) | `PlaceRadius` 25 · `GrowDist` 100 · `GrabDelay` 0,3 · `PulseAmount` 0,35 · `HoverScale` 1,15 | Afecta a todas las esferas del proyecto |
| Carga del botón SAVE | Test_Sequencer | `GAL_12_SaveMelody` | `HoldDuration` 3 s (categoría por confirmar) | Apuntar + sostener |

**No ajustable hoy (Attracting)**
- **Patrón de Chladni apagado** (`FloorPattern` false): `1 - Figura` (salvo el radio), `2 - Cambio` y `4 - Grano` no se ven hasta prenderlo. `Geometric` no tiene efecto (el camino recto salió del shader). La sombra y el reflejo del gusano en el piso están preparados pero no aplicados.
- `StepBPM` 90 (tempo), `ResultsSpacing` y `ResultsPadDelay` están en 0-Config pero **no son instance-editable** (solo Class Defaults). El tempo tiene que calzar con el loop del pad (8 pasos = 5,333 s).
- No mover solo `GAL_12_Sequencer`: es el pivote del teletransporte del cierre (cambia dónde cae la mesa respecto de `GAL_12_FinalTP`).
- `NS_OrbAttract_SC`: `Attraction Strength` en 0 y `Add Velocity` sin tocar; la vida de las partículas la calcula el BP. `OrbColors` del secuenciador es un respaldo sin uso.
- Grupo `9 - Interno` y `Dither` del material del piso los escribe el actor.
- Halo: 68 sistemas de partículas sin medir en la Quest; con la paleta Uyuni pueden leerse poco. Todo el tacto sin visor.

---

### 5. Surrounding (dibujo) — `/Game/SoulCharger/Mechanics/Draw/Maps/Test_Draw`, K = 4

⚠ Etapa **cerrada por Beltrán** el 2026-09-30 ("Funciona. Todo correcto."). Tocar solo si hace falta.

#### Posición y tamaño
| Quiero cambiar… | Nivel | Actor (Outliner) | Campo (categoría) | Nota / valor actual |
|---|---|---|---|---|
| Mesa de dibujo | Test_Draw | `DrawTable` (BP_TBTable) | Transform | (−265, 0, 180), Yaw 180; su +X apunta hacia quien dibuja. Moverla cambia el ancla; su escala no escala el dibujo |
| Dónde se exhibe el dibujo guardado | Test_Draw | `SketchTarget` (TargetPoint) | Transform (posición, giro, escala) | (235, 0, 80), Yaw 180, escala 4,89; +X hacia quien mira; la escala agranda el dibujo |
| Pose de la paleta en la mano | Test_Draw | `TBDirector` | `PaletteSide` / `PaletteUp` / `PaletteNear` (cm) · `PaletteTilt` / `PaletteBank` / `PaletteSpin` (°) · `PaletteScale` 0,464 (07 PALETA) | Se ajusta en vivo durante el PIE; al parar, copiar los valores a la instancia |
| Mar | Test_Draw | `DrawSea` | Transform · `SwellAmp` 22 · `SwellLenMax` / `SwellLenMin` 2600 / 420 (1-Oleaje) | z −120 = 226 cm bajo el usuario; escala 1; se puede girar en yaw |
| Grosor del trazo | Test_Draw | `TBDirector` | `StartSize` 0,45 · `SliderMinSize` / `SliderMaxSize` 0,5 / 1,5 (07 PALETA) | |
| Halo de la punta | Test_Draw | `TBDirector` | `bHalo` · `HaloScale` 3 · `HaloIntensity` 0,6 · `HaloBoost` 1 (06 PUNTA) | |

#### Color y luz
| Quiero cambiar… | Nivel | Actor (Outliner) | Campo (categoría) | Nota / valor actual |
|---|---|---|---|---|
| Los 4 colores de la paleta | Test_Draw | `TBDirector` | `SlotColorA[4]` · `SlotColorB[4]` (degradado) · `bColorGradient` · `ColorMode` 1 (01 COLOR) | Las teclas de la paleta se pintan con `SlotColorA` |
| Brillo de la punta | Test_Draw | `TBDirector` | `TipGain` 1,5 · `TipLift` 0,06 (06 PUNTA) | |
| Color de la mesa | Test_Draw | `TBDirector` | `TableColor` (0,25 / 0,55 / 1) (03 SKETCH) | Solo en juego. Opacidad: `TableOpacity` 0,35 en `M_TB_Table` |
| Mar y cielo | Test_Draw | `DrawSea` | `DeepColor` / `SurfColor` / `CrestColor` · `CrestAmt` · `LightAz` 40 · `LightEl` 22 (5-Superficie) · `ZenithColor` / `HorizonColor` · `GlowColor` · `FogStart` 500 · `FogDensity` 0,00017 (6-CieloNiebla) | |
| Polvo | Test_Draw | `DrawSea` | `bShowDust` · `DustColor` · `DustAmt` 0,45 · `DustSize` 0,9 · `DustRise` 0,6 (7-Polvo) | |
| Relieve del marcador | asset `MI_TB_TaperedMarker` | — | `ReliefAmt` 0,15 | El pincel 1, "sutil" a pedido de Beltrán |

#### Tiempos y ritmo
| Quiero cambiar… | Nivel | Actor (Outliner) | Campo (categoría) | Nota / valor actual |
|---|---|---|---|---|
| Largo de la etapa (la tinta) | Test_Draw | `TBDirector` | `InkMeters` 30 m · `bInk` (10 TINTA) | ~100 s de dibujo a 30 cm/s. Al agotarse, guarda solo |
| Exhibición del dibujo | Test_Draw | `TBDirector` | `HoldTime` 5 s · `SpinSpeed` 20 °/s · `ShowTime` / `HideTime` · `OutroTime` 1,2 (03 SKETCH) | |
| Entrada de mandos y paleta | Test_Draw | `TBDirector` | `IntroTime` 0,8 · `ContractPaletteDelay` 0,6 (11 CONTRATO) | |
| Vaivén de los trazos | Test_Draw | `TBDirector` | `bSwayEnabled` · `SwayStrength` 2,739 · `SwaySpeed` · `SwayWave` · `SwaySpan` · `SwayFade` (02 ANIMACION) | |
| Oleaje y avance del mar | Test_Draw | `DrawSea` | `Tempo` 0,28 (1-Oleaje) · `Advance` 5 (3-Avance) | |
| Estela del pincel | Class Defaults de `BP_TBTrail_NC` | (se crea en runtime) | `TrailLife` 0,12 · `TrailWidth` 0,7 · `TrailIdeal` 6 (10 ESTELA) | |

#### Mecánica
| Quiero cambiar… | Nivel | Actor (Outliner) | Campo (categoría) | Nota / valor actual |
|---|---|---|---|---|
| Vibración al dibujar | Test_Draw | `TBDirector` | `DrawHapAmp` · `DrawHapFreq` · `ClickHapAmp` · `DrawHapPulse` (05 HAPTICA) | |
| Sonidos y música | Test_Draw | `TBDirector` / `Ambient_Surrounding` | `BrushLoop[]` / `BrushLoopVol[]` · `ClickVol` · `SfxVol` · `ChargeVol` 0,6 · `SliderVol` 0,3 (04 AUDIO) · volumen del AmbientSound (Ambient_Clip_7) | La música es el AmbientSound del nivel |

**No ajustable hoy (Surrounding)**
- La paleta 3D no tiene teclas Save/Clear: el cierre es por tinta. `SaveHoldTime` no tiene efecto.
- Zurdo pendiente (`MirrorPalette` / `MaskFlip`): la paleta 3D no se espeja bien.
- La estela y la aparición de la paleta (`AppearDelay` 3 s, pose `ArtAnchor`) viven en Class Defaults / plantilla de `BP_TBTrail_NC` y `BP_TBPalette`, no en la instancia. En la Obra, `ContractPaletteDelay` 0,6 pisa `AppearDelay`.
- `PaletteOffset` está en el marco inclinado del grip: para ajustar a ojo, dejarlo como está y usar Side/Up/Near.
- El grosor por joystick está apagado a propósito (`bSizeByStick` false: choca con el stick del pawn).
- Flags de debug en false: `bSynth`, `bProfile`, `bForceTour`, `bContractTest`.
- En los resultados de la Obra el dibujo lo coloca `PlaceSketch` (55 cm): `SketchTarget` solo manda en la exhibición de la etapa. Mar y trazo incremental sin medir en la Quest.

---

### 6. Vive en la Obra, no en el nivel de test (`BP_Obra_SC_C_0` en `L_SoulCharger_Obra`)
- `ChargeTimes` (4 / 4 / 4 / 4 / 6 s) y `StageCols` (color del anillo de carga por etapa).
- Cortafuegos de cada mecánica: Recognizing 150 s, Loving 120 s, el resto 240 s. Con `bSimulated` (APK de postulación), Attracting y Surrounding cierran a `SimStageMax` 90 s.
- `UserTool_Obra` (mando y sensor de toda la obra, en el persistente).
- `DebugStart` en −1 antes de empaquetar el APK.
