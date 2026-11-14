# Demo Soul Charger — Barcelona Design Week (2026-10-21)

Versión corta de la obra: un **menú** y **tres experiencias de ~3 min** (ENTERING = respiración, RECOGNIZING = latido, SURROUNDING = dibujo; Heart agregada el 20-10). App aparte en el visor (`com.almadigital.soulchargerdemo`, "Soul Charger Demo"); la Obra completa sigue instalada intacta. Guion v2 de Beltrán (19-10): [`GUION-DEMO-V2.md`](GUION-DEMO-V2.md).

## El recorrido
1. **Menú** (`L_Demo_Menu`, la niebla azul del Hall, `BP_HallFog_SC` con `bStartOn` en el nivel): Ambient 1 · título SOUL CHARGER + **START** · las instrucciones de botón van como **subtítulo** (`BP_DemoVoice_SC.ShowHint`, sin audio: "Point the button and press trigger" desde que aparece el menú hasta apretar) · se ven **las dos manos, cada una con su láser** (un `BP_SeqRig_SC` por mano: `DemoRig` y `DemoRigL`); cualquiera de los dos gatillos elige.
2. START → se van título y START → **BACK** + los tres cuadros verticales (30 × 42 cm, `SM_DemoCard3_*`: ícono, título, subtítulo y una explicación corta; dos tamaños de letra): ENTERING (derecha), RECOGNIZING (centro), SURROUNDING (izquierda) (subtítulo "Point the experience of your choice and press trigger"). Hover = el botón crece un poco y se enciende.
3. Al elegir: se van los botones y los láseres (quedan las manos) · Ambient 2 · **viaje** con partículas que **no frena nunca** (sigue mientras todo se va a negro y cambia el nivel) mientras la niebla azul **degrada a negro** (`FogOff`, 18 s) · a los 3 s (`VoDelay`) la voz de bienvenida; entre voz y voz `VoGap` 1,2 s con subtítulos · el **HUD** se instala con una onda de luz · **`VO_D03`**: qué se mide (actividad neuronal, cardíaca e índice de calma) · "You're ready" · **negro** (el velo cierra en 3,5 s, sin su piso de brillo: antes quedaba gris) → la experiencia. El HUD **no se vuelve a instalar** en la experiencia: aparece ya puesto (`HudKit.bShowNow`).
4. **Breath** (`L_Demo_Breath`): velo y título ENTERING · panel de instrucciones (16:9, curvo, imagen + texto): 1 tomar el sensor que flota al frente (con la mano que lo tome) → 2 sensor en la panza (avanza al entrar al umbral) → 3 el círculo sigue la respiración (avanza con 2 respiraciones) → 4 tipo de respiración (solo instrucción y voz, **sin START**: al terminar la voz se va el panel) · recién ahí aparecen el metaball y la guía · voz · pacer · al terminar: voz, el HUD tiembla y se va ("plop"), **cuadro de resultados** 35 s · negro → menú.
5. **Draw** (`L_Demo_Draw`): velo y título SURROUNDING · se ven las manos hasta que se toma el pincel (el mando que flota al frente): ahí el mando queda en esa mano, las manos se van y aparece la paleta en la otra (el director del dibujo duerme hasta ese momento: `bForceTour`) · 2 un **trazo de práctica**: al llegar a 1 m el trazo se va, voz, arranca el **reloj del HUD** (2:30) · termina por tinta o por tiempo · el dibujo se presenta girando, se corre a la derecha · voz, "plop", resultados 35 s · negro → menú.
5b. El sensor / el mando que flota **gira e inclina en dos ejes y sube y baja** mientras espera (`SpinDeg` 40, `TiltDeg` 28, `BobCm` 2,5; el mando de Draw se inclina menos). Al tomarlo desaparece en el mismo cuadro y aparece el de la mano. Al tomarlo y al apretar un botón del menú **vibra esa mano**, 0,12 s después del agarre (en el mismo cuadro la etapa apaga la háptica de las dos manos y se comía el pulso): `BP_SeqRig_SC.Pulse`, el háptico de la Obra (`PlayHapticEffect` + `GrabHapticEffect`). Los botones suenan con `ProtoSelect` (antes `ChargeFinal`, 15 s).
5c. **Cada página del panel tiene su voz** (`DemoFlow.PageVo`: Breath `VO_IB1-4`, Draw `VO_ID1-2`, el mismo texto de la página). En Breath las páginas que avanzan solas esperan a que termine su voz (los tiempos límite no esperan).
5d. **Final de Draw**: cuando los mandos se terminan de ir, vuelven las manos. Cuando el dibujo se corre a la derecha (con su mesa), **en el mismo momento** se va el HUD, aparecen los resultados y suena `VO_DD2`.
5e. **Heart** — 20-10 noche: **dos páginas** (1 tomar el sensor; 2 al pecho, con un anillo que late dentro del panel: `M_DemoInstrHeart_SC`, `Pulse` = `BeatEnv`, `Zone` = umbral) · a los `HeartPulses` (3) pulsos se va el panel y **recién ahí sube la esfera**. Lo de abajo es la versión anterior. (`L_Demo_Heart`, copia de Breath con el entorno de `Test_Heart`: la membrana `BP_HeartScape_SC` con los valores de Beltrán y `BP_HeartManager_SC`): velo rosado y título RECOGNIZING · panel: 1 tomar el sensor que flota (gira) → el sensor rojizo en la mano y la esfera sale del agua (`StageIntro`) · 2 "Place the sensor on your heart… stay still" (`StageBegin`; avanza con 1,5 s en el umbral del pecho) · 3 "Each heartbeat becomes a pulse of light…" → se va el panel · un pulso de luz, sonido y vibración cada 2 latidos; `VO_DH1` al primer pulso, `VO_DH2` cuando empieza la vuelta del mar · cierra sola (19 pulsos + la vuelta, ~100 s) o al tope `TopeS` 150 · `VO_DH3`, "plop", resultados (tercera ventana: YOUR HEARTBEAT, "N heartbeats felt") · negro → menú. Sin mano en el pecho 30 s, el manager pone el latido de respaldo. HUD: el disco del lado derecho se enciende en el umbral y destella con cada pulso (`Mode` 3).
6. **Nadie se queda trabado**: cada espera tiene un tiempo límite y la demo sigue sola (tabla de abajo). Al final siempre vuelve al menú.
7. **Salida del operador**: **cinco toques rápidos** del botón Menú (☰) **o Y** del mando izquierdo (menos de 0,7 s entre toques; los dos botones son la misma acción del framework) → vuelve al menú desde cualquier punto (en el menú lo reinicia). Cinco, para que un visitante no lo haga por accidente. En escritorio: mantener la tecla **M** 2 s. Plan B si el visor no la toma: botón Meta → salir de la app → abrirla de nuevo (10-15 s).

### Tiempos límite (si la persona no hace nada)
| Espera | Perilla de `DemoFlow` | Valor | Qué pasa al vencer |
|---|---|---|---|
| Tomar el sensor / el pincel | `GrabWait` | 25 s | se toma solo con la mano derecha |
| Breath pág. 2: sensor en la panza | `ZoneWait` | 30 s | pasa a la página 3 |
| Breath pág. 3: el círculo | `BreathWait` | 30 s | pasa a la página 4 |
| Breath pág. 4 | (fijo) | 25 s | se va el panel aunque la voz no haya terminado |
| Draw: trazo de práctica | `PracticeWait` | 45 s | se corta con lo que haya (también sin trazo) |
| Cierre pedido que no llega | (fijo) | 30 s | Breath: tras `TopeS`; Draw: tras `DrawTime`. Se pasa a los resultados |
| Presentación del dibujo | `SpinTurnsT` × 2 | 24 s | se corre a la derecha aunque el giro no avance |

## HUD
El de la Obra (`BP_SoulHUD3D_SC`): izquierda la hermana azul latiendo con el pulso del **Muse** · centro el EEG · derecha: Breath = un disco que se enciende en el umbral, Draw = el reloj (se ve en 2:30 desde que aparece el HUD y empieza a correr con el dibujo). Los subtítulos van **encima** de la píldora (~24° bajo la vista), pegados a la cabeza como el HUD. El Muse llega por el `BioHub` de cada nivel (OSC, puerto 10000, `/muse/calm`, `/muse/heart_rate`, `/muse/sensor_active`). **Sin Muse**: el HUD no inventa datos (gráfico plano) y los resultados dicen "no signal".

## Qué se cambia dónde
| Qué | Dónde |
|---|---|
| **Imágenes de las instrucciones** (cuadradas) | `Demo/Textures/InstrImg/T_DemoInstrImg_<Breath_1..4 \| Draw_1..2>`: clic derecho → **Reimport With New File** → tu imagen cuadrada (la página 3 de Breath le superpone el círculo que respira). O cambiar el material de esa página en `DemoFlow` → `Images` |
| Textos de las instrucciones | `blender-3d/scripts/gen_instr_card2.py` (`PAGES`) → regenerar `T_Instr2_*` → reimportar |
| Voces de las instrucciones | `DemoFlow` de cada nivel → `PageVo` (una por página, en orden) |
| Imágenes / textos del panel de Heart | `T_DemoInstrImg_Heart_1..3` (Reimport With New File) · textos: `gen_instr_card2.py --text <dir> --only Heart` (`--only` evita pisar las imágenes que reemplazaste en Breath/Draw) |
| Voces | `tools/demo/vo_demo.json` → `python tools/demo/gen_vo_demo.py VO_xx` (regenera solo esa) → copiar los arreglos de `tools/demo/subs_demo_ue.json` al CDO de `BP_DemoVoice_SC` |
| Viaje del menú | `DemoMenu` (instancia) → `TravelCm` 1400 · `TravelTime` 32 · `AccelTime`/`BrakeTime` 4 · `VoDelay` 3 (espera de la bienvenida) · `VoGap` 1,2 · la niebla: `BP_HallFog_SC` → `FadeOut` 18 |
| Sonido de los botones | cada `BP_ShareButton_SC` de los niveles → `PressSound` (`ProtoSelect`) |
| Tiempos de cada experiencia | `DemoFlow` → `PanelAt` · `TopeS` (Breath 170) · `DrawTime` (Draw 150) · `PracticeM` (1 m) · `ResultsHold` 35 · `SpinTurnsT` 12 (= 2 vueltas a `SpinSpeed` 60) · `ShiftCm` · tiempos límite (arriba) |
| Largo de Breath | `Entering_Pacer` → `Cycles` (7: 5 de la parte 1 a 5-3-8-0 + los 2 de la parte final ≈ 114 s; 21-10, breathwork) |
| Tinta de Draw | `TBDirector` → `InkMeters` (75: 2,5 min de dibujo continuo a ~50 cm/s; 22-10) · presentación: `HoldTime` 999 (el dibujo queda girando) y `SpinSpeed` 60 |
| HUD | `HudKit` de cada nivel (`Mode`, colores) · `SoulHUD` (tamaño, curva) |
| Música | `DemoMusic` → `Clip`; Ambient 2 del menú = `DemoMenu.Amb2` |

## 🔴 Antes del APK: perillas de prueba en APAGADO
**Lo revisa solo** `python tools/demo/verificar_perillas.py` (lee los `.umap`): `empaquetar_obra.py --variante demo` y `empaquetar_robot.py` lo corren antes de cocinar y **no cocinan** si algo no está en el valor de público. Si cambia un valor de público, cambiarlo en `PUBLICO` del script y en esta tabla.

| Actor | Perilla | Valor de público |
|---|---|---|
| `L_Demo_Menu` → `DemoMenu` | `DebugPick` · `DrawShowTime` (el reloj del HUD al elegir Draw = `DrawTime`) | **−1 · 150** |
| `L_Demo_Breath` / `L_Demo_Draw` → `DemoFlow` | `AutoHand` · `AutoGo` · `bTestSynth` · `DrawTime` | **0 · 0 · false · 150** |
| `L_Demo_Breath` / `L_Demo_Draw` → `DemoFlow` | `GrabWait` · `ZoneWait` · `BreathWait` · `GoWait` · `PracticeWait` | **> 0** (25 · 30 · 30 · 60 · 45) |
| `L_Demo_Breath` → `Entering_Pacer` | `Cycles` | **7** |
| `L_Demo_Breath` → `DemoFlow` | `TopeS` | **170** |
| `L_Demo_Heart` → `DemoFlow` | `AutoHand` · `AutoGo` · `TopeS` · `GrabWait`/`ZoneWait` | **0 · 0 · 150 · > 0** |
| `L_Demo_Heart` → `HeartManager` | `bContractTest` · `bFakeBeat` · `bIgnoreTracking` · `HeartVDropMin` | **false · false · false · 10** (las tres últimas son las recetas de PIE de escritorio) |
| `L_Demo_Breath` → etapa (`BP_BreathStage_SC`) | `bAutoStart` · `bContractTest` | **false · false** (`bAutoStart` viene en true en el Blueprint: el nivel tiene que decir false) |
| `L_Demo_Draw` → `TBDirector` | `bForceTour` | **true** (duerme hasta que se toma el mando; sin esto la paleta aparece al cargar el nivel) |
| `L_Demo_Draw` → `TBDirector` / herramienta | `bContractTest` · `bSynth` · `bSynthDry` | **false** |
| los 4 niveles → `BioHub` | `bFakeSignal` | **true** (20-10 noche, pedido de Beltrán: la demo va con la señal simulada del Muse; la guardia lo exige) |
| `DemoShots` (los 2 niveles) | `Every` | **0** |

## Valores de público (20-10 noche, para el APK `Demo_BDW`)
`bFakeSignal` **true** en los 4 niveles desde la segunda tanda de la noche (antes false = Muse real; si se conecta un Muse real con esto en true, las dos señales entran por el mismo `Ingest` y se mezclan), Breath `TopeS` 170, Heart `TopeS` 150, Draw `DrawTime` 150, menú `DrawShowTime` 150. **Resolución del visor** (21-10 noche): `RenderPct` por nivel, aplicado 1 s después del pawn (que pone 100): menú **120**, Draw **115**, Breath y Heart **100**. Para probar otro valor sin recompilar: `-DemoRenderPct=N` en `UECommandLine.txt` (pisa los 4 niveles). Para volver a probar en Unreal con experiencias cortas y Muse simulado: `bFakeSignal` true y 30 s (y devolverlos antes del próximo APK; la guardia lo exige).

## Probar sin visor
```
python tools/unreal/probar_nivel.py /Game/SoulCharger/Demo/Maps/L_Demo_Breath --segundos 250 --extra="-MirrorRole=-1" --filtro "DEMOFLOW|VOZ|HUDKIT|RESULT"
```
`--extra="-MirrorRole=-1"` apaga el espejo (sin visor el enlace arranca como receptor y el menú espera la pose). **Con los valores de público** la experiencia también recorre todo sola, por los tiempos límite (Breath ≈ 6 min, Draw ≈ 5 min): es la prueba de "nadie hace nada". Para ir rápido: `AutoHand` 1, `AutoGo` 3 y (Draw) `bTestSynth` — y después devolverlos (la guardia del empaquetado lo recuerda). `DemoShots.Every` N saca una captura cada N s (`Saved/Screenshots/WindowsEditor`). Tiene que dar `errores de Blueprint: 0`.

## Probado sin visor (2026-10-19, noche)
- "Nadie hace nada" con valores de público: Breath completo (≈6 min) y Draw completo (≈5 min) vuelven solos al menú. 0 errores.
- Menú → Draw con trazo sintético: viaje, voces con subtítulos (redibujo manual), HUD, dibujo presentado y corrido 160 cm (pivote registrado), resultados, menú.
- Draw con **gatillo inyectado** (robot / Quest falso): después del trazo de práctica se puede dibujar (bug del candado arreglado; antes no se podía), mano izquierda incluida.
- APK final: `Recursos/.../APK/Soul Charger Demo APK 2026-10-19 1901` (OBB 101 MB, antes 128). Las copias intermedias de esta noche quedaron en `_superados`.

## Empaquetar e instalar
```
python tools/unreal/empaquetar_obra.py --variante demo
powershell -File tools/unreal/instalar_quest.ps1 -Variante demo
```

## Piezas (fichas en `.claude/skills/unreal-vr/blueprints/`)
`BP_DemoMenu_SC` (menú, viaje, bienvenida) · `BP_DemoFlow_SC` (director de Breath y Draw) · `BP_DemoHudKit_SC` + `BP_DemoVoice_SC` (HUD y voz con subtítulos) · `BP_DemoResults_SC` (cuadro de resultados) · `BP_DemoCard_SC` (cuadros y panel, con mallas por variable) · `BP_DemoAmb_SC` (música) · `BP_DemoExit_SC` · `BP_MirrorLink_SC` (robot). Modelos: `blender-3d/assets/instr-card2.md`, `demo-results.md`.

## Pendiente de visor
- Alturas y distancias: el panel a 1,5 m (centro de su curva en los ojos), los resultados a 1,6 m; que se lean el texto y los rótulos.
- Tomar el sensor y el mando que flotan al frente (radio 14 cm) con cualquiera de las dos manos.
- El círculo de la página 3 y el umbral (página 2) con el sensor real en la panza.
- Draw: el trazo de práctica (1 m) y que el clic del panel no deje rastro; el dibujo corrido a la derecha detrás del cuadro.
- El "plop" del HUD, la onda de luz de la instalación y los subtítulos sobre la píldora.
- El Muse llegando al Quest (IP del Quest en el servidor del Muse, puerto 10000).
- **La salida del operador (Menú/Y ×5)**: va por Enhanced Input (`IA_Menu_Toggle_Left` de `IMC_Default`, que está en los contextos por defecto de `DefaultInput.ini`); sin visor no se puede probar.
- Rótulos de resultados (`WorldSize` 2,4 / 2,6) y ayuda del menú (`HintCm` 2,8): que se lean a 1,5-1,6 m.
- (20-10 noche, 2.ª tanda) Sin "TEXT" en el disco de Heart · sin click al volver al menú ni al entrar a la experiencia · subtítulos con cápsula en fondo claro y oscuro · texto de los cuadros a 1,20 m · bordes de los rótulos de resultados · el tiempo menú → experiencia (~38 s estimado).

## Cambios 2026-10-20 (noche), tras la prueba de Beltrán en Unreal
- Título de cada etapa más largo: se va entre 8 y 9,3 s (`TitleO0/O1`, `TitleHide` 9,4) y el panel aparece a los 9,8 s (`PanelAt`), en los tres niveles.
- Figuras reactivas **dentro del panel** (esquema de cómo funciona): Breath pág. 3 muestra solo el anillo que sigue la respiración (`M_DemoInstrImage_SC`: con `BreathMix` 1 ya no se ve la imagen debajo); Heart pág. 2, el anillo que late.
- Textos nítidos: las texturas de texto (cuadros, panel, START/BACK) no tenían mipmaps y titilaban en el visor; ahora `TMGS_Sharpen2` + `NeverStream`.
- **Heart**: al tercer pulso se va el panel y el latido se **pausa** (`TourSleep`); 1 s después sube la esfera (2,5 s) y recién arriba vuelve a latir (`StageBegin`). Fases de `HeartTick` 0-7.
- **Blanco en Unreal**: es una regresión de UE 5.8 en PIE (gotcha 589): al cambiar de nivel jugando, el nivel nuevo se dibuja con el render de PC. No pasa en el Quest. Para probar en el editor: después de cada cambio de nivel, apretar **dos veces** el botón de vista previa (Preview Mode) de la barra.
- **Marcos negros** de cuadros y panel al aparecer/desaparecer: las mallas nuevas (`SM_DemoCard3_*`, `SM_InstrCard2_*`) no tenían material en el trazo de luz (`WorldGridMaterial` = negro sin luz). Ahora tienen los de la familia SHARE (trazo `M_AppearTrace_SC`).
- **Título del menú: DIGITAL SANCTUARY** (pedido de Beltrán): `T_Title_DIGITALSANCTUARY` (Michroma, mismo estilo y ancho que `T_Title_SOULCHARGER`: R nítida / G resplandor, 2048 × 512) en `MI_Demo_TitleDS_SC`; `DemoMenu.Boot` se lo pone al `TitleP` del título (su Construction Script rehace el material desde `MI_Credit_Title`, por eso no sirve cambiarlo en la instancia). La Obra sigue diciendo SOUL CHARGER.
- **APK `Demo_BDW`**: `python tools/unreal/empaquetar_obra.py --variante demo --nombre Demo_BDW` (mismo paquete `com.almadigital.soulchargerdemo`: reemplaza la demo instalada; en el visor se llama Demo_BDW).
- **El menú nunca pasa a negro** (Beltrán): ya no se llama `HallFog.FogOff`; la niebla queda azul todo el viaje y el velo se cierra en **6 s** del azul al color de la experiencia (el nivel se abre a los 6,5 s).
- **HUD de Heart**: el disco derecho es un **punto rojo** (`DiscColor` 1/0,16/0,12 en `L_Demo_Heart`) que crece con cada pulso: `BeatCount / StageBeats` (los pulsos que cierran la etapa) → se llena de 0 a 100; destella con cada latido. (`KitDisc`/`KitSlot` modo 3: `Inner` −0,1, `Radius` 0, `Width` 0,06→0,56.)
- **Trazo de luz del color de cada experiencia**: cuadros del menú (azul / verde / rojo, `DemoMenu.Boot`) y panel de instrucciones (`DemoFlow.TraceColor`: Breath azul, Heart rojo, Draw verde) — antes salía dorado (el color del SHARE).
- **Cuadros legibles sin hover**: placa oscura en el tono de cada experiencia (`MI_DemoCard_PlateTop*` `Base` 0,16/0,19/0,27 · 0,13/0,22/0,16 · 0,26/0,13/0,13; antes gris claro con letra blanca).
- **Empalme menú → experiencia por color, no por negro** (pedido de Beltrán): el menú cierra el velo al color con que arranca la experiencia elegida (`TopA/HorA` Breath celeste, `TopC/HorC` Heart rosado claro, `TopB/HorB` Draw azul noche = `CTop/CHor` del `DemoFlow` de ese nivel). UE 5.8 no muestra pantalla de carga en VR (ni el proyecto la configura): durante el `OpenLevel` el visor sostiene el último cuadro, así que el color empalma. La experiencia arranca con el velo quieto en ese color, el título entra a 1,2-2,5 s (`TitleR0/R1`) y el velo se abre a la escena a 3-6 s (`VeilA0/A1`). ⬜ Confirmar en el Quest que no aparece negro durante la carga.
- **Línea negra en el canal de luz** al aparecer/desaparecer botones y cuadros: el canal (`/SC_Base/M_SCLight_SC`, opaco) vale `Color·Glow·AppearGlow` y durante la aparición `AppearGlow` es 0. Nuevo parámetro `AppearFloor` (default 0: la Obra queda igual), 0,4 en `MI_Demo_Ring_*`, `MI_ShareButton_Ring_SC` (START/BACK; ⚠ también el SHARE de la Obra) y `MI_BioSensor_{Ring,BackRing,TipLight}_SC` (el sensor que flota; también en la Obra). La ranura de la paleta de Draw (`M_DrawPalette_Groove_SC`, sin instancia) tiene el mismo piso con default 0,4.

## Cambios 2026-10-20 (noche, 4.ª tanda): índice de calma, HUD y visor del robot
- **Índice de calma** (pedido de Beltrán): la app del sensor (Muse Integration 0.3, dirigida desde acá) calcula un % con signo respecto de la calibración de la persona (EEG α/β, ruido muscular, pulso, movimiento, parpadeo; con calidad 0-1) y lo manda en `/muse/calm_index`. El Quest lo guarda en el BioHub, lo reenvía al robot y el cuadro de resultados de los dos muestra **`CALM INDEX +N%`** (o `--`). Sin sensor, el simulado sube de 0 a ~+22 %.
- El gráfico del HUD es la **actividad neuronal**: la app ya no manda `/muse/calm`; los 4 niveles leen `/muse/alpha` (`AddrCalm`). La guardia lo exige.
- Robot: el HUD cuelga de la cámara de espectador (se salía de cuadro al mover el casco) y el mesh del visor del pawn queda oculto.
- ✅ **Probado (21-10, 0-1 h) con el APK y el robot nuevos y Muse Integration 0.3.1 (simulador, calibración demo-2)**: las tres experiencias de punta a punta en el Quest con el robot siguiéndolas, "BIO: Muse real" en cada nivel, CALM INDEX igual en el Quest (captura del visor) y en el robot (+27 % Heart, +22 % Draw, +32 % Breath), 0 errores de Blueprint.
- **Cuadro de resultados en altísima calidad** (pedido de Beltrán): textos y gráficos ahora son **textura** (Quicksand, la fuente de la obra), no `TextRender`: se dibujan a 2 px/mm y se reducen 2:1 a la textura de cada ventana. Siguen la curva del vidrio (antes se cortaban), no tienen escalones ni tramado. En Heart el conteo va en el título ("HEARTBEATS FELT - N"). Detalle en el tracker de `BP_DemoResults_SC`; regla nueva en `docs/REGLAS-DE-ORO.md` §11.
- 🔴 **Después de instalar un APK nuevo, correr cada experiencia una vez antes del público**: la primera vez que aparece el cuadro de resultados el visor compila su pipeline gráfico (~0,5 s de imagen congelada, medido con VrApi `Stale=33`); en las corridas siguientes ya está en la caché del visor. La pasada de prueba de esta noche dejó la caché caliente.

## Cambios 2026-10-20 (noche, 3.ª tanda): señal simulada como respaldo, robot con estado de conexión
- **Señal simulada = respaldo** (`BP_BioHub`, Core): simula solo si no llega el sensor real por 2 s (`FakeHold`). Con la app del sensor mandando al Quest, el simulado se apaga solo ("BIO: Muse real"); si el sensor se corta, vuelve ("BIO: sin Muse, vuelve el simulado"). `bFakeSignal` sigue en true en los 4 niveles (ahora quiere decir "respaldo permitido"); la Obra (false) no cambia. Prueba sin sensor: `tools/demo/muse_falso.py`.
- **La app del sensor no se toca**: manda solo al Quest (UDP 10000). El robot recibe calma y BPM a través del Quest (`/sc/st`). El robot puede correr en el mismo PC que la app del sensor; esa app no tiene que escuchar en UDP 9000 ni 10000. Detalle en `docs/demo/ROBOT.md`.
- **Robot con estado de conexión en pantalla** (`WBP_MirrorStatus_SC`): línea verde "LINK OK" con la IP del Quest y mensajes/s; recuadro rojo con la IP del PC para el Quest si pasan 8 s sin datos; Tab para el detalle. Vigía: a los 3 s sin datos el robot suelta gatillos y grips. `Robot.bat` le pasa la IP del PC (`-MirrorMyIP`).
- Revisión adversaria de toda la tanda de esta noche (workflow `robot-link-and-review`, agentes de solo lectura): sin bloqueos. Quedan dos clicks posibles fuera del camino normal: la salida del operador (Menú ×5) abre el menú con la música sonando, y el robot puede cortar un nivel con música si quedó muy atrás del Quest.
- **Red**: la wifi de invitados del lab aísla a los equipos. ✅ **Solución probada (23 h): hotspot del laptop** con el Quest conectado a él (laptop `192.168.137.1`, Quest `192.168.137.165`): robot en verde siguiendo al visor y el sensor (simulado desde el laptop) llegando al Quest y de ahí al robot. Paso a paso en `docs/demo/ROBOT.md`.

## Cambios 2026-10-20 (noche, 2.ª tanda), tras probar el APK `Demo_BDW` en el Quest
- **"TEXT" sobre el disco del HUD en Heart**: en `KitSlot` el bloque del modo 3 terminaba en un `IsValid` y el DSL colgó de su `else` la línea que esconde el reloj (gotcha 590): en Heart el reloj de Draw quedaba visible con su texto por defecto. Reordenado (el reloj va antes) y el `Timer` nace con texto vacío.
- **Señal simulada en el APK**: `bFakeSignal` true en los 4 niveles; la guardia ahora la **exige**.
- **Click de audio al cambiar de nivel**: antes de cada `OpenLevel` el volumen **maestro** (`MasterMix` = `MasterSubmixDefault`) baja a 0 con margen, y cada nivel lo devuelve a 1 al arrancar (`FBoot` / `Boot`; la música entra con su `FadeIn` de 3 s). Experiencia → menú: rampa de 3 s en la fase 18 y el menú se abre a los **4 s** (antes 3, con la música todavía en cola). Menú → experiencia: la música **sigue** mientras el velo se cierra (ya no `FadeAll` al empezar el cierre) y el maestro baja de 3 a 6 s; el nivel se abre a los 6,5 s.
- **Menú → experiencia más corto** (antes ~50 s desde que se elige, con silencios): bienvenida a los `VoDelay` **3 s** (antes 6), `VoGap` **1,2 s** (antes 2,5), `VO_D03` a los 2,5 s de instalado el HUD (antes 4), "You're ready" a los 3 s (antes 5) y el cierre arranca 0,6 s después de que termina la voz. ⬜ Medir en el visor (estimado ~38 s, sin silencios largos).
- **Subtítulos** (borde negro en fondo claro, baja calidad): `WBP_SubWord_SC` sin contorno ni sombra (eran negros: en fondo claro se veía un borde dentado); `WBP_SubLine_SC` con una **cápsula oscura translúcida** detrás (`Back`, 50 %, se ajusta al largo de la línea y se funde con el subtítulo). El widget se dibujaba a 900 px en ~20° (2,2× la densidad del visor, sin mips = aliasing): ahora 560 × 100 a escala 0,0257 (mismo tamaño físico), fuente 16, `Rise` 5,6. Estos dos widgets solo los usa la demo (`BP_Subtitles_SC` de la Obra no está en ningún nivel).
- **Textos del cuadro de resultados** (y el reloj del HUD): `M_TextUnlit` es enmascarado y en móvil el borde queda sin antialiasing. Copia `Demo/Materials/M_DemoTextAA_SC` con **alpha to coverage** (con MSAA 4x el borde del campo de distancia queda suave).
- **Títulos** (DIGITAL SANCTUARY, ENTERING, RECOGNIZING, SURROUNDING): estaban en `TC_Masks` = ASTC 6×6 en el Quest (bloques en los bordes). Ahora `TC_EditorIcon` (sin compresión). Los logos ya estaban sin compresión.
- **Cuadros del menú**: más cerca (1,20 m, antes 1,50) y mips de su textura con `Sharpen4` (antes 2).
- **Por qué el APK se ve más blando que en Unreal por Link**: el pawn de la Obra fija la resolución del visor al 100 % en su BeginPlay (1680 × 1760 por ojo, gotcha 445); por Link el PC dibuja más. Subirla (120 % = ×1,44 de píxeles) es la mejora más grande para todo el texto, pero hay que medir fps en el visor antes: no se tocó.
- **Frame drops**: la primera corrida de un APK nuevo compila los PSO de Vulkan sobre la marcha (el caché se guardó al final de la sesión, 17:33). Después de instalar, **correr una vez las tres experiencias** antes de recibir público. Hubo además un `ensure` del motor (FAppTime desde un hilo de Java, 17:29:37) = un tirón; no es del proyecto.

## Revisión de toda la demo (2026-10-20, tarde)
Arreglado y probado sin visor (0 errores de Blueprint):
- **Robot y Heart**: el robot no tiene tracking y el umbral del pecho no abría (solo arrancaba el latido de respaldo a los 30 s). `BP_MirrorLink_SC.RobotHeart` pone `bIgnoreTracking` en el manager, como `RobotBreath` con la respiración. Probado con el Quest falso (`mirror_test_send.py --guion flujo_heart`): `UMBRAL IN` con la mano recibida apenas empieza la etapa.
- **Manos al final**: `UserTool.Release` esconde el sensor pero no devuelve la mano. Breath (que dejaba el sensor puesto) y Heart terminan ahora como Draw: se va el sensor y vuelven las manos (`HandsBack`).
- **START de Breath**: el láser salía de la mano que tiene el sensor en la panza; ahora sale de la mano libre, con la mano visible (rig de `L_Demo_Breath`: `bHideHands`/`bShowControllers` false), y vibra esa mano.
- **Voces de Heart**: la segunda (`VO_DH2`) espera al menos 10 s después de que se va el panel (podían salir una pegada a la otra).
Para decidir: el orden de los cuadros del menú (ver abajo).

## Limitaciones conocidas (decisiones para después del miércoles)
- **Orden de los cuadros**: mirando el menú, de izquierda a derecha se lee SURROUNDING · RECOGNIZING · ENTERING (al revés que la Obra). Cambiarlo es mover dos actores (Y +35 ↔ −35).
- **Un solo nivel**: el menú y las experiencias son niveles separados; entre uno y otro hay ~1 s de carga en negro en que el HUD no está. Para continuidad total, después de BDW: un nivel persistente con las experiencias como subniveles (como la Obra).
- Las manos vuelven de golpe al elegir la experiencia (el guion dice "suavemente"); un fundido pide tocar el pawn.
- Las voces del pacer ("three, two, one, inhale", "hold", "exhale") son las de la Obra y no llevan subtítulo.
- En Draw los resultados tienen una tercera ventana ("YOUR DRAWING", cantidad de trazos) que el guion no pide: **decidir si queda**.
- El trazo de práctica se corta cuando la persona **suelta** el gatillo pasado el metro (no en mitad del trazo).
- Si alguien se saca el visor a mitad, la sesión sigue donde estaba: cortar con Menú ×5 al cambiar de persona.
