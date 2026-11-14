# 📚 Catálogo: qué hace cada asset

Generado por `python tools/unreal/gen_catalogo.py` (no editar a mano: las frases están en `tools/unreal/catalogo_desc.json`).
Una fila por Blueprint, material maestro, función de material, MPC, Niagara y data asset del proyecto y de los plugins `SC_*`.
**Usado por** = qué proyecto lo alcanza desde sus niveles (Obra, Demo, Inner Canvas, experimentos, niveles de prueba).
Las instancias de material (`MI_*`), texturas, mallas y sonidos no van: se entienden por su material o su BP.
Mapa general: [`MAPA-DEL-PROYECTO.md`](MAPA-DEL-PROYECTO.md) · detalle de cada BP: `.claude/skills/unreal-vr/blueprints/`.

Índice: [SoulCharger/Obra](#soulchargerobra) · [InnerCanvas](#innercanvas) · [SoulCharger/Core](#soulchargercore) · [SoulCharger/Demo](#soulchargerdemo) · [SoulCharger/Hall](#soulchargerhall) · [SoulCharger/Mechanics](#soulchargermechanics) · [SoulCharger/Shared](#soulchargershared) · [XRFramework](#xrframework) · [XRMannequins](#xrmannequins) · [Plugin SC_Base](#plugin-scbase) · [Plugin SC_Breath](#plugin-scbreath) · [Plugin SC_Draw](#plugin-scdraw) · [Plugin SC_Sequencer](#plugin-scsequencer)

## SoulCharger/Obra

| Asset | Tipo | Usado por | Qué hace |
|---|---|---|---|
| `BP_ChargeFx_SC` <br><sub>/Game/SoulCharger/Obra/Blueprints</sub> | Blueprint | Obra | Carga de la Obra: el anillo del HUD hace pum y renace grande en el punto de carga; duplicado de BP_ChargeTest_SC. El del ensayo del Hall es BP_ChargeTest_SC (no es duplicado: otro cliente). |
| `BP_Credits_SC` <br><sub>/Game/SoulCharger/Obra/Blueprints</sub> | Blueprint | Obra | Créditos del final de la Obra, frente a los ojos. |
| `BP_Disclaimer_SC` <br><sub>/Game/SoulCharger/Obra/Blueprints</sub> | Blueprint | Obra | Aviso de inicio de la Obra antes del Hall (DiscShow, tiempo DiscTime). |
| `BP_HallRunner_SC` <br><sub>/Game/SoulCharger/Obra/Blueprints</sub> | Blueprint | Obra | Ensayo del Hall (tag TestOnly): Play en Test_Hall corre el Hall como en la Obra; en la Obra se destruye. |
| `BP_IntroTitle_SC` <br><sub>/Game/SoulCharger/Obra/Blueprints</sub> | Blueprint | Obra, Demo | Título del inicio como objeto real que se mueve y escala en el editor, con los logos. |
| `BP_Obra_SC` <br><sub>/Game/SoulCharger/Obra/Blueprints</sub> | Blueprint | Obra | Director de la Obra: lleva el reloj y las fases (Hall → 5 etapas → final → créditos) y lee la Partitura. |
| `BP_SoulFish_SC` <br><sub>/Game/SoulCharger/Obra/Blueprints</sub> | Blueprint | Obra | Al regreso, el alma sale del anillo nadando como pez-cometa con chispas. |
| `BP_StageRunner_SC` <br><sub>/Game/SoulCharger/Obra/Blueprints</sub> | Blueprint | Obra | Ensayo de etapa en cada nivel de test: corre la etapa con los tiempos de la Partitura (tag TestOnly). |
| `M_TourVeil_SC` <br><sub>/Game/SoulCharger/Obra/Materials</sub> | material | Obra, Demo, Inner Canvas | Velo esférico pegado a la cámara que funde a negro o al color de la etapa; translúcido sin depth test. |
| `BP_Partitura_SC` <br><sub>/Game/SoulCharger/Obra/Partitura</sub> | Blueprint | Obra | Clase de datos (PrimaryDataAsset) con las ~60 perillas de tiempo de la obra. |
| `DA_Partitura_Obra` <br><sub>/Game/SoulCharger/Obra/Partitura</sub> | data asset | Obra | Todos los tiempos narrativos de la Obra; los leen BP_Obra_SC y BP_StageRunner_SC. |
| `M_TourLogo_SC` <br><sub>/Game/SoulCharger/Obra/Titles</sub> | material | Obra, Demo, Inner Canvas | Logos del inicio (MI_Logo_ADS/JHU/IDEAS): copia de M_TourTitle_SC con color y alfa de la textura y tinte C0. |
| `M_TourTitle_SC` <br><sub>/Game/SoulCharger/Obra/Titles</sub> | material | Obra, Demo, Inner Canvas, experimentos | Títulos de etapa y de la Obra: fuente horneada con barrido líquido (Reveal, Out). |

## InnerCanvas

| Asset | Tipo | Usado por | Qué hace |
|---|---|---|---|
| `BP_ICAmb_IC` <br><sub>/Game/InnerCanvas/Blueprints</sub> | Blueprint | Inner Canvas | Música/sonido ambiente de Inner Canvas en L_InnerCanvas. |
| `BP_ICFlow_IC` <br><sub>/Game/InnerCanvas/Blueprints</sub> | Blueprint | Inner Canvas | Director de Inner Canvas: idioma, nombre con teclado, HUD, tutorial, dibujo libre y final; se escribe desde ic_flow2_dsl.py. |
| `BP_ICHudKit_IC` <br><sub>/Game/InnerCanvas/Blueprints</sub> | Blueprint | Inner Canvas | HUD de Inner Canvas: nombre al centro, reloj a la derecha y círculo de tinta verde a la izquierda. |
| `BP_ICKeyboard_IC` <br><sub>/Game/InnerCanvas/Blueprints</sub> | Blueprint | Inner Canvas | Teclado virtual con láser (A-Z, Ñ en español, espacio, borrar, OK) para escribir el nombre; lo pinta en un render target. |
| `BP_ICLink_IC` <br><sub>/Game/InnerCanvas/Blueprints</sub> | Blueprint | Inner Canvas | Envía del visor al PC por OSC/UDP 9300 estado, nombre y trazos nudo a nudo; se configura con -ICSlot/-ICWall/-ICPort. |
| `BP_ICSpace_IC` <br><sub>/Game/InnerCanvas/Blueprints</sub> | Blueprint | Inner Canvas | Espacio de 3 × 3 m (piso y 4 paredes) que aparece con la voz y queda tenue; cada pared se enciende al acercarse cabeza o mano. |
| `BP_ICTutor_IC` <br><sub>/Game/InnerCanvas/Blueprints</sub> | Blueprint | Inner Canvas | Marco de instrucciones de Inner Canvas con paleta y mando grandes, mantos, etiquetas y cartas de mano dominante. |
| `BP_ICVoice_IC` <br><sub>/Game/InnerCanvas/Blueprints</sub> | Blueprint | Inner Canvas | Reproduce las voces IC_01..IC_12 en inglés o español con subtítulos. |
| `BP_ICWallGM_IC` <br><sub>/Game/InnerCanvas/Blueprints</sub> | Blueprint | Inner Canvas | GameMode de la pantalla del PC (L_InnerCanvas_Wall): usa BP_ICWallHUD_IC y un pawn espectador. |
| `BP_ICWallHUD_IC` <br><sub>/Game/InnerCanvas/Blueprints</sub> | Blueprint | Inner Canvas | HUD Canvas de la pantalla del PC: rejilla con número, nombre, tiempo y tinta de cada visor. |
| `BP_ICWall_IC` <br><sub>/Game/InnerCanvas/Blueprints</sub> | Blueprint | Inner Canvas | PC: servidor OSC 9300 que reconstruye con BP_TBStroke los trazos de cada visor en su celda (x = k × 1 km) y hace la presentación. |
| `M_ICHand_IC` <br><sub>/Game/InnerCanvas/Hands</sub> | material | Inner Canvas | Material de las manos de Inner Canvas (SKM_ICHand_R/L); copia de M_QuestCtrl_SC. |
| `M_ICKey_IC` <br><sub>/Game/InnerCanvas/Materials</sub> | material | Inner Canvas | Teclas planas del teclado de Inner Canvas con el atlas T_ICKeyAtlas (Custom HLSL). |
| `M_ICLogo_IC` <br><sub>/Game/InnerCanvas/Materials</sub> | material | Inner Canvas | Logo de Inner Canvas: copia de M_TourLogo_SC que toma el color de C0 en vez del de la textura. |
| `M_ICMantle_IC` <br><sub>/Game/InnerCanvas/Materials</sub> | material | Inner Canvas | Mantos blancos en forma de sector de anillo que se cuelgan de la paleta en el tutorial. |
| `M_ICPanel_IC` <br><sub>/Game/InnerCanvas/Materials</sub> | material | Inner Canvas | Panel del marco de instrucciones (Frame) del tutorial de Inner Canvas. |
| `M_ICSpace_IC` <br><sub>/Game/InnerCanvas/Materials</sub> | material | Inner Canvas | Piso y paredes del espacio 3 × 3 de Inner Canvas, con el anillo que marca el centro (Custom HLSL). |
| `M_ICText_IC` <br><sub>/Game/InnerCanvas/Materials</sub> | material | Inner Canvas | Etiquetas de texto liso del tutorial, leídas del atlas T_ICTexts. |

## SoulCharger/Core

| Asset | Tipo | Usado por | Qué hace |
|---|---|---|---|
| `BP_AlmaAura_SC` <br><sub>/Game/SoulCharger/Core/Alma</sub> | Blueprint | Obra, Demo, Inner Canvas, experimentos | Esfera de partículas diminutas y translúcidas con curl noise que envuelve a Alma; la spawnea BP_Alma_SC al arrancar. |
| `BP_Alma_SC` <br><sub>/Game/SoulCharger/Core/Alma</sub> | Blueprint | Obra, Demo, Inner Canvas, experimentos | Alma, la guía: esfera-ameba translúcida que flota, aparece y desaparece y habla por voice over en cada etapa. |
| `M_Alma` <br><sub>/Game/SoulCharger/Core/Alma</sub> | material | Obra, Demo, Inner Canvas, experimentos | Material de Alma: unlit, translúcido, de una cara, sin reflejos ni refracción. |
| `M_AlmaAura_SC` <br><sub>/Game/SoulCharger/Core/Alma</sub> | material | Obra, Demo, Inner Canvas, experimentos | Partículas del aura de Alma, todo en el vertex shader; unlit, AlphaComposite, dos caras, precisión Full. |
| `BP_PerfEntering_SC` <br><sub>/Game/SoulCharger/Core/Debug</sub> | Blueprint | Obra | Herramienta de medición (no es obra): en Test_Breath apaga piezas de Entering según PerfStartMode para medir costo. |
| `BP_PerfSwitch_SC` <br><sub>/Game/SoulCharger/Core/Debug</sub> | Blueprint | Obra | Herramienta de medición: recibe comandos de consola Perf0..3 y escribe PerfMode en MPC_Perf_SC. |
| `BP_SoulState` <br><sub>/Game/SoulCharger/Core/Flow</sub> | Blueprint | — nadie | GameInstance del proyecto (declarada en DefaultEngine.ini): guarda malla y color del alma del usuario entre niveles. |
| `BP_Ganzfeld_SC` <br><sub>/Game/SoulCharger/Core/Light</sub> | Blueprint | Obra, Demo, experimentos | Cascarón esférico sin borde que llena la vista de color (campo Ganzfeld); hoy solo se usa el modo fluido o el fondo liso. |
| `BP_LightShaft_SC` <br><sub>/Game/SoulCharger/Core/Light</sub> | Blueprint | Obra | Haz de luz falso tipo Turrell: geometría con material unlit aditivo, sin luces ni niebla; puede publicar su haz en MPC_LightShaft. |
| `MPC_LightShaft` <br><sub>/Game/SoulCharger/Core/Light</sub> | parámetros de material | Obra | Colección donde BP_LightShaft_SC publica posición, dirección, color y radio del haz para que otros materiales se iluminen. |
| `M_ApertureGlow_SC` <br><sub>/Game/SoulCharger/Core/Light</sub> | material | Obra | Disco fuente con halo radial procedural (plano unlit aditivo de dos caras): el óculo de donde sale el haz. |
| `M_GanzSolid_SC` <br><sub>/Game/SoulCharger/Core/Light</sub> | material | Obra, Demo, experimentos | Fondo liso para el cascarón Ganzfeld; mucho más barato que el modo fluido (~4 ms contra ~12). |
| `M_Ganzfeld_SC` <br><sub>/Game/SoulCharger/Core/Light</sub> | material | Obra, Demo, experimentos | Material del cascarón Ganzfeld: campo de color sin horizonte con modo fluido. |
| `M_LightShaft` <br><sub>/Game/SoulCharger/Core/Light</sub> | material | Obra | Material del haz de BP_LightShaft_SC: aditivo de dos caras; el BP siempre crea su MID desde aquí. |
| `BP_VRPawn_SC` <br><sub>/Game/SoulCharger/Core/Pawn</sub> | Blueprint | Obra, Demo, Inner Canvas, experimentos, pruebas | El pawn VR de todos los proyectos: cámara, mandos, manos y recentrado; compartido, coordinar antes de tocarlo. |
| `M_Hand_SC` <br><sub>/Game/SoulCharger/Core/Pawn/Materials</sub> | material | Obra, Demo, Inner Canvas, experimentos, pruebas | Manos del pawn en blanco emisivo translúcido (unlit, Fresnel en la opacidad); la demo usa su hija MI_Hand_Demo_SC. |
| `BP_FaceAnchor_SC` <br><sub>/Game/SoulCharger/Core/ProtoSoul</sub> | Blueprint | Obra, Demo, Inner Canvas | Ancla de cara: punto de referencia contra el que se hornea el pegado del HUD a la cabeza. |
| `BP_ProtoSoul_SC` <br><sub>/Game/SoulCharger/Core/ProtoSoul</sub> | Blueprint | Obra, experimentos | El alma del usuario: ameba elegible en el Hall que lo acompaña; sus anillos flotantes están apagados desde el 2026-09-30. |
| `BP_SoulPicker_SC` <br><sub>/Game/SoulCharger/Core/ProtoSoul</sub> | Blueprint | Obra | Gobierna la elección del alma: duerme las 5 candidatas, las despierta en el Hall y lleva la elegida con el gatillo. |
| `M_ProtoSoul` <br><sub>/Game/SoulCharger/Core/ProtoSoul</sub> | material | Obra, experimentos | Material de la ameba del alma del usuario (una cara); también es padre de MI_Ghost. |
| `M_ProtoSoul_HUD` <br><sub>/Game/SoulCharger/Core/ProtoSoul</sub> | material | Obra, Demo, Inner Canvas, experimentos | Duplicado de M_ProtoSoul con Disable Depth Test para que manos y escena no tapen al alma (HUD, carga). |
| `M_SoulRibbon_SC` <br><sub>/Game/SoulCharger/Core/ProtoSoul</sub> | material | Obra, experimentos | Cinta de los anillos del alma como trazo dibujado, siempre sin depth test; los anillos hoy están apagados. |
| `BP_BioHub` <br><sub>/Game/SoulCharger/Core/Signals</sub> | Blueprint | Obra, Demo, Inner Canvas, pruebas | Ingesta OSC de biosensores, suavizado y flag de conexión; las etapas leen de aquí sin saber de OSC (bFakeSignal simula). |
| `BP_OSCReceiver` <br><sub>/Game/SoulCharger/Core/Signals</sub> | Blueprint | Obra, Demo, Inner Canvas, pruebas | Servidor OSC que recibe floats por la red local y los expone como variables para otros BP. |
| `WBP_Portrait_SC` <br><sub>/Game/SoulCharger/Core/UI</sub> | widget | Obra, experimentos | Widget del retrato (1600 × 900) que la obra le devuelve al usuario con sus resultados. |

## SoulCharger/Demo

| Asset | Tipo | Usado por | Qué hace |
|---|---|---|---|
| `BP_DemoAmb_SC` <br><sub>/Game/SoulCharger/Demo/Blueprints</sub> | Blueprint | Demo, Inner Canvas | Sonido ambiente de la demo en bucle con crossfade consigo mismo (Clip, Volume, FadeIn, FadeOut). |
| `BP_DemoCard_SC` <br><sub>/Game/SoulCharger/Demo/Blueprints</sub> | Blueprint | Demo | Carta del menú de la demo, hija de BP_ShareButton_SC, que aplica mallas y materiales desde variables. |
| `BP_DemoExit_SC` <br><sub>/Game/SoulCharger/Demo/Blueprints</sub> | Blueprint | Demo, Inner Canvas | Salida del operador: cinco toques de Menú/Y (o mantener M) vuelven a L_Demo_Menu. |
| `BP_DemoFlow_SC` <br><sub>/Game/SoulCharger/Demo/Blueprints</sub> | Blueprint | Demo, Inner Canvas | Director de L_Demo_Breath y L_Demo_Draw: velo, título, panel de instrucciones, etapa y resultados. |
| `BP_DemoHudKit_SC` <br><sub>/Game/SoulCharger/Demo/Blueprints</sub> | Blueprint | Demo, Inner Canvas | HUD de la demo: disco, onda, pops de carga y reloj, junto a BP_SoulHUD3D_SC. |
| `BP_DemoMenu_SC` <br><sub>/Game/SoulCharger/Demo/Blueprints</sub> | Blueprint | Demo, Inner Canvas | Menú de la demo (L_Demo_Menu): título, ENGLISH/ESPAÑOL y 3 cartas que llevan a cada experiencia. |
| `BP_DemoResults_SC` <br><sub>/Game/SoulCharger/Demo/Blueprints</sub> | Blueprint | Demo, Inner Canvas | Cuadro curvo de resultados de la demo con ventanas EEG, pulso, respiración y calma; lo llama BP_DemoFlow_SC. |
| `BP_DemoShots_SC` <br><sub>/Game/SoulCharger/Demo/Blueprints</sub> | Blueprint | Demo | Capturas de prueba de la demo; hay que sacarlo de un nivel antes de cocinar. |
| `BP_DemoVoice_SC` <br><sub>/Game/SoulCharger/Demo/Blueprints</sub> | Blueprint | Demo, Inner Canvas | Voz de la demo con subtítulos y elección de idioma (SetLangES). |
| `BP_MirrorLink_SC` <br><sub>/Game/SoulCharger/Demo/Blueprints</sub> | Blueprint | Demo, Inner Canvas | Envía el estado del visor al robot de Windows por OSC (espejo para el público) y tiene la SpecCam. |
| `WBP_MirrorStatus_SC` <br><sub>/Game/SoulCharger/Demo/Blueprints</sub> | widget | Demo, Inner Canvas | Indicador en pantalla del robot de Windows: LINK OK con IP y mensajes/s, o recuadro rojo si no hay enlace. |
| `M_DemoInstrImage_SC` <br><sub>/Game/SoulCharger/Demo/Materials</sub> | material | Demo | Imagen de las páginas de instrucciones de la demo; con BreathMix muestra el anillo que sigue la respiración. |
| `M_DemoPanelPage_SC` <br><sub>/Game/SoulCharger/Demo/Materials</sub> | material | Demo | Páginas de instrucciones de la demo, translúcidas (BgOpacity 0,86) y del color de su carta. |
| `M_DemoResPane_SC` <br><sub>/Game/SoulCharger/Demo/Materials</sub> | material | Demo, Inner Canvas | Vidrio translúcido de las ventanas de resultados con contenido emisivo (Card) desde un render target. |
| `M_DemoTextAA_SC` <br><sub>/Game/SoulCharger/Demo/Materials</sub> | material | Demo, Inner Canvas | Texto de la demo con alpha to coverage (borde suave en Quest); copia de M_TextUnlit. |

## SoulCharger/Hall

| Asset | Tipo | Usado por | Qué hace |
|---|---|---|---|
| `BP_BellArt_SC` <br><sub>/Game/SoulCharger/Hall/Blueprints</sub> | Blueprint | Obra, pruebas | Arte y aparición del timbre del Hall (solo visual; la lógica vive en otro BP). |
| `BP_HallAmbience_SC` <br><sub>/Game/SoulCharger/Hall/Blueprints</sub> | Blueprint | Obra | Ambiente del Hall: oculta la arquitectura hasta el negro y mueve la onda de las líneas de luz (GrooveFront); lee al director. |
| `BP_HallDirector_SC` <br><sub>/Game/SoulCharger/Hall/Blueprints</sub> | Blueprint | Obra | Director del Hall (inicio, regreso y salida): timbre, sensor, elección del alma, niebla, luces y puertas. |
| `BP_HallFog_SC` <br><sub>/Game/SoulCharger/Hall/Blueprints</sub> | Blueprint | Obra, Demo | Niebla del inicio y del final: esfera pegada a la cámara, azul noche; FogOn/FogOff la funden. |
| `BP_HallGlow_SC` <br><sub>/Game/SoulCharger/Hall/Blueprints</sub> | Blueprint | Obra | Lo que se ve por la puerta de salida: esfera afuera de la puerta Este, blanco azulado. |
| `BP_HallLights_SC` <br><sub>/Game/SoulCharger/Hall/Blueprints</sub> | Blueprint | Obra | Enciende el interior del Hall (LightsOn/LightsOff funden HallLight y el haz con curva smoothstep). |
| `BP_HallTitle_SC` <br><sub>/Game/SoulCharger/Hall/Blueprints</sub> | Blueprint | Obra | Título SOUL CHARGER / CENTER al costado derecho de la puerta del Hall. |
| `BP_SensorOrb_SC` <br><sub>/Game/SoulCharger/Hall/Blueprints</sub> | Blueprint | Obra | Orbe burbuja que gira e invita a tomar el sensor en el Hall (SpinDeg, OrbSize, OrbOpacity). |
| `MPC_Hall_SC` <br><sub>/Game/SoulCharger/Hall/Materials</sub> | parámetros de material | Obra, Demo | Perillas globales del Hall: HallLight, DoorColor, GrooveFront y similares que leen sus materiales. |
| `M_HallDust_SC` <br><sub>/Game/SoulCharger/Hall/Materials</sub> | material | Obra | Polvo del Hall; brilla con max(HallLight, DustLight) para verse también en el viaje a oscuras. |
| `M_HallFog_SC` <br><sub>/Game/SoulCharger/Hall/Materials</sub> | material | Obra, Demo | Esfera de niebla del Hall pegada a la cámara; duplicado de M_TourVeil_SC con depth test. |
| `M_Hall_Exterior_SC` <br><sub>/Game/SoulCharger/Hall/Materials</sub> | material | Obra | Exterior del edificio del Hall; la línea del marco se enciende con FrameLight. |
| `M_Hall_Glass_SC` <br><sub>/Game/SoulCharger/Hall/Materials</sub> | material | Obra | Vidrio de la puerta del Hall; su color desde adentro es DoorColor y se enciende desde atrás. |
| `M_Hall_Interior_SC` <br><sub>/Game/SoulCharger/Hall/Materials</sub> | material | Obra | Interior del Hall con líneas de luz que ondulan con GrooveFront; se enciende con HallLight. |
| `M_Hall_Sky_SC` <br><sub>/Game/SoulCharger/Hall/Materials</sub> | material | Obra | Cielo del Hall; su emisivo escala con HallLight. |
| `M_Hall_Tile_SC` <br><sub>/Game/SoulCharger/Hall/Materials</sub> | material | Obra | Baldosas del Hall: se elevan (Lift) y brillan (TileGlow) además de seguir HallLight. |
| `M_SpaceDust_SC` <br><sub>/Game/SoulCharger/Hall/Materials</sub> | material | Obra, Demo | Polvo del viaje y la salida: duplicado de M_HallDust_SC que solo responde a DustLight. Distinto de M_HallDust_SC: también en el menú de la demo. |
| `NS_HallDust_SC` <br><sub>/Game/SoulCharger/Hall/VFX</sub> | Niagara | Obra | Partículas de polvo del Hall (Niagara) con M_HallDust_SC. |
| `NS_SpaceDust_SC` <br><sub>/Game/SoulCharger/Hall/VFX</sub> | Niagara | Obra, Demo | Polvo del viaje a oscuras (Niagara), duplicado de NS_HallDust_SC con M_SpaceDust_SC; también en el menú de la demo. |

## SoulCharger/Mechanics

| Asset | Tipo | Usado por | Qué hace |
|---|---|---|---|
| `BP_BreathAir_SC` <br><sub>/Game/SoulCharger/Mechanics/Breath/Blueprints</sub> | Blueprint | Obra, Demo | Aliento visible de Entering: aire que reacciona a la velocidad de la respiración leyendo MPC_Breath. |
| `BP_BreathStage_SC` <br><sub>/Game/SoulCharger/Mechanics/Breath/Blueprints</sub> | Blueprint | Obra, Demo, Inner Canvas | Orquestador de Entering: conoce a BP_BreathRig_SC, BP_BreathBlob_SC y BP_Pacer_SC, y las voces de Alma; implementa el contrato de etapa. |
| `BP_BreathValley_SC` <br><sub>/Game/SoulCharger/Mechanics/Breath/Blueprints</sub> | Blueprint | Obra, Demo, Inner Canvas | Valle de colinas de Entering con oleaje, niebla y cielo (71 parámetros); la sombra sigue al metaball. |
| `BP_ValleyLife_SC` <br><sub>/Game/SoulCharger/Mechanics/Breath/Blueprints</sub> | Blueprint | Obra, Demo, Inner Canvas | Capa de vida del valle: polvo y ráfagas de viento sobre las colinas. |
| `M_BreathAir_SC` <br><sub>/Game/SoulCharger/Mechanics/Breath/Materials</sub> | material | Obra, Demo | Material del aliento visible de Entering. |
| `M_BreathValley_SC` <br><sub>/Game/SoulCharger/Mechanics/Breath/Materials</sub> | material | Obra, Demo, Inner Canvas | Valle de Entering: unlit opaco de dos caras, precisión Full, con ráfagas (Gust*) por WPO. |
| `M_ValleyDust_SC` <br><sub>/Game/SoulCharger/Mechanics/Breath/Materials</sub> | material | Obra, Demo, Inner Canvas | Polvo de la capa de vida del valle. |
| `BP_DrawSea_SC` <br><sub>/Game/SoulCharger/Mechanics/Draw/Blueprints</sub> | Blueprint | Obra, Demo, Inner Canvas | Océano de Surrounding: mar oscuro y mate que avanza hacia el usuario, con niebla y polvo; todo en shader, sin Tick. |
| `M_DrawDust_SC` <br><sub>/Game/SoulCharger/Mechanics/Draw/Materials</sub> | material | Obra, Demo, Inner Canvas | Polvo fino del océano de dibujo; unlit translúcido aditivo, movimiento por WPO. |
| `M_DrawSea_SC` <br><sub>/Game/SoulCharger/Mechanics/Draw/Materials</sub> | material | Obra, Demo, Inner Canvas | Mar y cielo del océano de dibujo: unlit opaco de dos caras, oleaje por WPO. |
| `BP_AttractCall_SC` <br><sub>/Game/SoulCharger/Mechanics/Harp/Blueprints</sub> | Blueprint | experimentos | Llamada y respuesta con el hang: cada golpe lanza una onda a la ameba lejana, que brilla, se acerca y contesta. |
| `BP_AttractStreams_SC` <br><sub>/Game/SoulCharger/Mechanics/Harp/Blueprints</sub> | Blueprint | experimentos | Chorros de partículas desde una ameba lejana con cada nota del hang; apagado (MaxStreams 0), a Beltrán le pareció sucio. |
| `BP_Harp_SC` <br><sub>/Game/SoulCharger/Mechanics/Harp/Blueprints</sub> | Blueprint | experimentos | Arpa (o hang, InstrumentType 1) que se toca con las manos, con sinte propio por MetaSounds y hápticos. |
| `M_AttractMote_SC` <br><sub>/Game/SoulCharger/Mechanics/Harp/Materials</sub> | material | experimentos | Partículas de los chorros de Attracting movidas en el material (Custom Primitive Data, sin Niagara). |
| `M_AttractRing_SC` <br><sub>/Game/SoulCharger/Mechanics/Harp/Materials</sub> | material | experimentos | Onda en anillo de la llamada y respuesta; translúcido y sin luz. |
| `M_AttractShell_SC` <br><sub>/Game/SoulCharger/Mechanics/Harp/Materials</sub> | material | experimentos | Membrana ámbar de dos caras que se enciende cuando el ojo queda dentro de la ameba. |
| `M_HangRing_SC` <br><sub>/Game/SoulCharger/Mechanics/Harp/Materials</sub> | material | experimentos | Aro aditivo del hang que vibra con la nota (Rad, W, Int, Vib, Lobes). |
| `M_HarpSpark_SC` <br><sub>/Game/SoulCharger/Mechanics/Harp/Materials</sub> | material | experimentos | Chispas del arpa: esferas aditivas sin luz con núcleo brillante del color de la nota. |
| `M_HarpString_SC` <br><sub>/Game/SoulCharger/Mechanics/Harp/Materials</sub> | material | experimentos | Cuerdas del arpa que brillan y vibran al tocarlas. |
| `BP_HeartDust_SC` <br><sub>/Game/SoulCharger/Mechanics/Heart/Blueprints</sub> | Blueprint | Obra, Demo, Inner Canvas | Motas fijas al mar del latido que, con paralaje, ayudan a sentir el giro; lo spawnea el scape. |
| `BP_HeartManager_SC` <br><sub>/Game/SoulCharger/Mechanics/Heart/Blueprints</sub> | Blueprint | Obra, Demo, Inner Canvas | Mecánica del latido: detecta la mano en el pecho y marca el ritmo con el BPM de BP_BioHub; contrato de etapa. |
| `BP_HeartScape_SC` <br><sub>/Game/SoulCharger/Mechanics/Heart/Blueprints</sub> | Blueprint | Obra, Demo, Inner Canvas | Paisaje del latido: membrana mate enorme donde cada latido hace latir la esfera y nace una onda. |
| `M_HeartDust_SC` <br><sub>/Game/SoulCharger/Mechanics/Heart/Materials</sub> | material | Obra, Demo, Inner Canvas | Polvo del latido: unlit, AlphaComposite, dos caras, precisión Full, todo en el vertex shader. |
| `BP_FeedDirector_SC` <br><sub>/Game/SoulCharger/Mechanics/Mind/Blueprints</sub> | Blueprint | experimentos | Experimento Test_Feed: 6 protoamebas con nombre se cargan con la mirada, se vuelven polvo y alimentan a la principal. |
| `BP_FluidMedium_SC` <br><sub>/Game/SoulCharger/Mechanics/Mind/Blueprints</sub> | Blueprint | Obra, Demo, experimentos | Fluido cerebral de Loving: medio líquido 3D con fondo, células, motas, haces y velos; empuja colores a MPC_Fluid_SC. |
| `BP_FocusDirector_SC` <br><sub>/Game/SoulCharger/Mechanics/Mind/Blueprints</sub> | Blueprint | experimentos | Experimento Test_Focus: 4 amebas que se activan sosteniendo la mirada, sin EEG. |
| `BP_LovingCell_SC` <br><sub>/Game/SoulCharger/Mechanics/Mind/Blueprints</sub> | Blueprint | Obra, experimentos | Célula de Loving: núcleo ameba, grupos de bolas y membranas que crecen con State 0→1; contrato de etapa. |
| `BP_ThoughtsDirector_SC` <br><sub>/Game/SoulCharger/Mechanics/Mind/Blueprints</sub> | Blueprint | experimentos | Experimento Test_Thoughts (Loving sin sensor): pensamientos que, al mirarlos, revelan su palabra; en pausa. |
| `MPC_Fluid_SC` <br><sub>/Game/SoulCharger/Mechanics/Mind/Materials</sub> | parámetros de material | Obra, Demo, experimentos | Colores y parámetros globales del fluido cerebral que leen los materiales del fluido y de la célula. |
| `M_FluidBackground_SC` <br><sub>/Game/SoulCharger/Mechanics/Mind/Materials</sub> | material | Obra, Demo, experimentos | Fondo del fluido cerebral: esfera invertida opaca unlit de dos caras con luz desde arriba. |
| `M_FluidFarCells_SC` <br><sub>/Game/SoulCharger/Mechanics/Mind/Materials</sub> | material | Obra, Demo, experimentos | Células lejanas del fluido: masked con alpha to coverage, dos caras. |
| `M_FluidMidCells_SC` <br><sub>/Game/SoulCharger/Mechanics/Mind/Materials</sub> | material | Obra, Demo, experimentos | Células medias del fluido: opaco unlit. |
| `M_FluidMotes_SC` <br><sub>/Game/SoulCharger/Mechanics/Mind/Materials</sub> | material | Obra, Demo, experimentos | Motas en suspensión del fluido: translúcido unlit de dos caras. |
| `M_FluidShafts_SC` <br><sub>/Game/SoulCharger/Mechanics/Mind/Materials</sub> | material | Obra, Demo, experimentos | Haces de luz del fluido: aditivo de dos caras. |
| `M_FluidVeils_SC` <br><sub>/Game/SoulCharger/Mechanics/Mind/Materials</sub> | material | Obra, Demo, experimentos | Velos translúcidos del fluido, la capa de más relleno. |
| `M_FocusDot_SC` <br><sub>/Game/SoulCharger/Mechanics/Mind/Materials</sub> | material | experimentos | Punto con anillo que marca hacia dónde se mira en los experimentos de foco. |
| `M_LovingArm_SC` <br><sub>/Game/SoulCharger/Mechanics/Mind/Materials</sub> | material | Obra, experimentos | Brazo de la célula: tubo con hebra, cuello y tapa; AlphaComposite. |
| `M_LovingBalls_SC` <br><sub>/Game/SoulCharger/Mechanics/Mind/Materials</sub> | material | Obra, experimentos | Racimos de 2-3 bolas fundidas de la célula, con sombreado tipo arcilla. |
| `M_LovingBridge_SC` <br><sub>/Game/SoulCharger/Mechanics/Mind/Materials</sub> | material | Obra, experimentos | Puente de tensión superficial entre cuerpos de la célula (reloj de arena); AlphaComposite. |
| `M_LovingCentreFilm_SC` <br><sub>/Game/SoulCharger/Mechanics/Mind/Materials</sub> | material | Obra, experimentos | Membrana que envuelve el núcleo de la célula. |
| `M_LovingCentre_SC` <br><sub>/Game/SoulCharger/Mechanics/Mind/Materials</sub> | material | Obra, experimentos | Núcleo ameba cerrado de la célula, con normal analítica. |
| `M_LovingDust_SC` <br><sub>/Game/SoulCharger/Mechanics/Mind/Materials</sub> | material | Obra, experimentos | Segunda membrana de partículas de la célula (sprites en el vertex shader). |
| `M_LovingOuter_SC` <br><sub>/Game/SoulCharger/Mechanics/Mind/Materials</sub> | material | Obra, experimentos | Ameba translúcida exterior que encierra toda la célula; sus defaults afectan a todos los niveles. |
| `M_ThoughtMote_SC` <br><sub>/Game/SoulCharger/Mechanics/Mind/Materials</sub> | material | experimentos | Sprite del polvo de Test_Thoughts (unlit translúcido, para Niagara). |
| `NS_FocusMotes_SC` <br><sub>/Game/SoulCharger/Mechanics/Mind/VFX</sub> | Niagara | experimentos | Nube de partículas de carga de Focus y Feed; duplicado de NS_OrbHalo_SC. Copia a propósito de NS_OrbHalo_SC (plugin) para Feed/Focus. |
| `NS_ThoughtMotes_SC` <br><sub>/Game/SoulCharger/Mechanics/Mind/VFX</sub> | Niagara | experimentos | Polvo de los pensamientos de Test_Thoughts (copia propia de NS_FocusMotes_SC). |

## SoulCharger/Shared

| Asset | Tipo | Usado por | Qué hace |
|---|---|---|---|
| `BP_BioSensorArt_SC` <br><sub>/Game/SoulCharger/Shared/BioSensor/Blueprints</sub> | Blueprint | Obra, Demo, Inner Canvas, pruebas | Arte y aparición del sensor biométrico, con ondas; también es el sensor que flota en la demo. |
| `M_BioSensorWaves_SC` <br><sub>/Game/SoulCharger/Shared/BioSensor/Materials</sub> | material | Obra, Demo, Inner Canvas, pruebas | Aros de onda del sensor (Active para el juego, AppearGlow para la aparición). |
| `M_ChargeRing_Frame_SC` <br><sub>/Game/SoulCharger/Shared/ChargeRing</sub> | material | Obra, Demo, Inner Canvas | Anillo de carga de hormigón en el mundo; opaco. |
| `M_ChargeRing_Light_SC` <br><sub>/Game/SoulCharger/Shared/ChargeRing</sub> | material | Obra, Demo, Inner Canvas | Luz del anillo de carga en el mundo; opaco. |
| `BP_GhostPlayer_SC` <br><sub>/Game/SoulCharger/Shared/Ghost/Blueprints</sub> | Blueprint | Obra, Demo, pruebas | Reproduce en bucle un fantasma translúcido de dos manos que hace el gesto de instrucción hasta que el usuario lo hace. |
| `BP_GhostRecorder_SC` <br><sub>/Game/SoulCharger/Shared/Ghost/Blueprints</sub> | Blueprint | pruebas | Graba con los mandos los gestos de instrucción en L_GhostRec_SC y los escribe en un DA_Ghost_*. |
| `BP_GhostTake_SC` <br><sub>/Game/SoulCharger/Shared/Ghost/Blueprints</sub> | Blueprint | Obra, Demo, pruebas | Clase de datos de una toma de fantasma (los DA_Ghost_* son instancias). |
| `DA_Ghost_Attract` <br><sub>/Game/SoulCharger/Shared/Ghost/Data</sub> | data asset | Obra, pruebas | Toma del fantasma de Attracting: apunta a la esfera, la lleva a un slot y suelta. |
| `DA_Ghost_Bell` <br><sub>/Game/SoulCharger/Shared/Ghost/Data</sub> | data asset | Obra, pruebas | Toma del fantasma que toca el timbre del Hall. |
| `DA_Ghost_Breath` <br><sub>/Game/SoulCharger/Shared/Ghost/Data</sub> | data asset | Obra, Demo, pruebas | Toma del fantasma de Entering (respiración). |
| `DA_Ghost_Draw` <br><sub>/Game/SoulCharger/Shared/Ghost/Data</sub> | data asset | Obra, Demo, pruebas | Toma del fantasma de Surrounding: toca la paleta y dibuja una curva con el gatillo. |
| `DA_Ghost_Heart` <br><sub>/Game/SoulCharger/Shared/Ghost/Data</sub> | data asset | Obra, pruebas | Toma del fantasma de Recognizing (mano al pecho). |
| `DA_Ghost_Pick` <br><sub>/Game/SoulCharger/Shared/Ghost/Data</sub> | data asset | Obra, pruebas | Toma del fantasma que elige el alma en el Hall. |
| `DA_Ghost_Take` <br><sub>/Game/SoulCharger/Shared/Ghost/Data</sub> | data asset | Obra, pruebas | Toma del fantasma que toma el sensor en el Hall. |
| `M_Ghost_SC` <br><sub>/Game/SoulCharger/Shared/Ghost/Materials</sub> | material | Obra, Demo, pruebas | Manos fantasma: unlit aditivo con borde Fresnel (Color, Opacity, Pressed). |
| `BP_ChargeSoul_SC` <br><sub>/Game/SoulCharger/Shared/HUD/Blueprints</sub> | Blueprint | Obra | La ameba de 15 cm dentro del anillo de carga; también es la base del pez-cometa. |
| `BP_ChargeTest_SC` <br><sub>/Game/SoulCharger/Shared/HUD/Blueprints</sub> | Blueprint | Obra | Prueba de la coreografía de carga (teletransporte del anillo del HUD); la Obra usa su duplicado BP_ChargeFx_SC. Lo usa el ensayo del Hall (BP_HallRunner_SC); la Obra usa BP_ChargeFx_SC. |
| `BP_HUDArt_SC` <br><sub>/Game/SoulCharger/Shared/HUD/Blueprints</sub> | Blueprint | Obra, Demo, Inner Canvas | Arte 3D del HUD: la píldora (borde, bisel, copas y vidrio) donde va el EEG. |
| `BP_HUDRingSoul_SC` <br><sub>/Game/SoulCharger/Shared/HUD/Blueprints</sub> | Blueprint | Obra, Demo, Inner Canvas | El alma pequeña (1,5 cm) dentro del anillo del HUD, sin latido. |
| `BP_HUDSister_SC` <br><sub>/Game/SoulCharger/Shared/HUD/Blueprints</sub> | Blueprint | Obra, Demo, Inner Canvas | La hermana del HUD: ameba de 3 cm que late a la mitad del ritmo. |
| `BP_SoulHUD3D_SC` <br><sub>/Game/SoulCharger/Shared/HUD/Blueprints</sub> | Blueprint | Obra, Demo, Inner Canvas | HUD como objeto 3D pegado a la cabeza (hijo de BP_SoulHUD_SC): píldora, EEG vivo, alma y hermana; perillas HudScale y HudCurve. |
| `BP_SoulHUD_SC` <br><sub>/Game/SoulCharger/Shared/HUD/Blueprints</sub> | Blueprint | Obra, Demo, Inner Canvas | HUD base pegado a la cabeza: barra de carga, gráfico EEG y punto del latido. |
| `M_AppearTraceHUD_SC` <br><sub>/Game/SoulCharger/Shared/HUD/Materials</sub> | material | Obra, Demo, Inner Canvas | Trazo de aparición del HUD: variante de M_AppearTrace_SC sin depth test y con el doblez del HUD. |
| `M_ChargeHaloTint_SC` <br><sub>/Game/SoulCharger/Shared/HUD/Materials</sub> | material | Obra | Halo de carga translúcido y teñido del color de la etapa; copia de M_ChargeHalo_SC. |
| `M_ChargeHaloTop_SC` <br><sub>/Game/SoulCharger/Shared/HUD/Materials</sub> | material | Obra | Halo de carga sin depth test para que el anillo y sus explosiones queden delante del negro final. |
| `M_ChargeHalo_SC` <br><sub>/Game/SoulCharger/Shared/HUD/Materials</sub> | material | Obra, Demo, Inner Canvas | Halo aditivo de la carga: anillo gaussiano y relleno (los pops de carga). |
| `M_ChargeRing_FrameHUD_SC` <br><sub>/Game/SoulCharger/Shared/HUD/Materials</sub> | material | Obra, Demo, Inner Canvas | Anillo de carga de hormigón del HUD: translúcido sin depth test. |
| `M_ChargeRing_LightHUD_SC` <br><sub>/Game/SoulCharger/Shared/HUD/Materials</sub> | material | Obra, Demo, Inner Canvas | Luz del anillo de carga del HUD: translúcido sin depth test. |
| `M_HudWidget_SC` <br><sub>/Game/SoulCharger/Shared/HUD/Materials</sub> | material | Obra, Demo, Inner Canvas | Material por encima de todo para widgets del HUD y subtítulos (sin depth test). |
| `WBP_SoulHUD_SC` <br><sub>/Game/SoulCharger/Shared/HUD/UI</sub> | widget | Obra, Demo, Inner Canvas | Widget del HUD con barra de carga, gráfico EEG y punto del latido, con datos de BP_BioHub. |
| `BP_JourneyContent_SC` <br><sub>/Game/SoulCharger/Shared/Results/Blueprints</sub> | Blueprint | Obra, pruebas | Contenido de los resultados del viaje (puntajes por etapa en render targets) dentro del marco de BP_ResultsArt_SC. |
| `BP_ResultsArt_SC` <br><sub>/Game/SoulCharger/Shared/Results/Blueprints</sub> | Blueprint | Obra, pruebas | Marco 3D del cuadro de resultados: vidrio, ventanas, título y cajita del tip que se abre al apuntar. |
| `BP_ShareButton_SC` <br><sub>/Game/SoulCharger/Shared/Results/Blueprints</sub> | Blueprint | Obra, Demo, Inner Canvas, pruebas | Botón SHARE de los resultados con aparición, hover y press; también es padre de las cartas de la demo. |
| `M_JourneyCard_SC` <br><sub>/Game/SoulCharger/Shared/Results/Materials</sub> | material | Obra, pruebas | Tarjetas de los resultados: unlit aditivo de dos caras (Gain). |
| `WBP_SubLine_SC` <br><sub>/Game/SoulCharger/Shared/Subtitles</sub> | widget | Demo, Inner Canvas | Línea de subtítulo con cápsula oscura translúcida detrás; la usan la demo e Inner Canvas. |
| `WBP_SubWord_SC` <br><sub>/Game/SoulCharger/Shared/Subtitles</sub> | widget | Demo, Inner Canvas | Palabra de subtítulo, sin contorno ni sombra; la usan la demo e Inner Canvas. |
| `BP_UserTool_SC` <br><sub>/Game/SoulCharger/Shared/UserTool</sub> | Blueprint | Obra, Demo, Inner Canvas | El mando/sensor del usuario, un solo actor persistente que cambia de color y rol por etapa (PushColor). |

## XRFramework

| Asset | Tipo | Usado por | Qué hace |
|---|---|---|---|
| `BPI_PawnAnim` <br><sub>/Game/XRFramework/Blueprints</sub> | interfaz | Obra, Demo, Inner Canvas, experimentos, pruebas | Interfaz de la plantilla VR de Epic para animar u ocultar las manos del pawn (HideUnhideHand). |
| `BP_AssetGuideline` <br><sub>/Game/XRFramework/Blueprints</sub> | Blueprint | Obra, Demo, Inner Canvas, experimentos, pruebas | (inferido) Actor de la plantilla VR de Epic con guías de escala y referencia para assets. |
| `BP_GrabComponent` <br><sub>/Game/XRFramework/Blueprints</sub> | Blueprint | Obra, Demo, Inner Canvas, experimentos, pruebas | Componente de la plantilla VR de Epic que hace agarrable un objeto; el pawn agarra el más cercano al grip. |
| `BP_Menu` <br><sub>/Game/XRFramework/Blueprints</sub> | Blueprint | Obra, Demo, Inner Canvas, experimentos, pruebas | Menú láser de la plantilla VR de Epic (con NS_MenuLaser y cursor M_VRCursor). |
| `BP_Passthrough` <br><sub>/Game/XRFramework/Blueprints</sub> | Blueprint | Obra, Demo, Inner Canvas, experimentos, pruebas | (inferido) Actor de la plantilla VR de Epic que activa el passthrough de cámaras. |
| `BP_TeleportVisualizer` <br><sub>/Game/XRFramework/Blueprints</sub> | Blueprint | Obra, Demo, Inner Canvas, experimentos, pruebas | Visualizador del teleport de la plantilla VR de Epic (arco y anillo). |
| `BP_XRGameMode` <br><sub>/Game/XRFramework/Blueprints</sub> | Blueprint | Obra, Demo, Inner Canvas, experimentos, pruebas | GameMode por defecto de la plantilla VR de Epic que usa todo el proyecto. |
| `WBP_Menu` <br><sub>/Game/XRFramework/Blueprints</sub> | widget | Obra, Demo, Inner Canvas, experimentos, pruebas | Widget del menú de la plantilla VR de Epic (incluye el botón de reset de orientación). |
| `BP_InputModifier_XAxisPositiveOnly` <br><sub>/Game/XRFramework/Input</sub> | Blueprint | Obra, Demo, Inner Canvas, experimentos, pruebas | (inferido) Modificador de Enhanced Input de la plantilla que deja pasar solo el eje X positivo. |
| `MF_OccludedPixels` <br><sub>/Game/XRFramework/Materials/Functions</sub> | función de material | Obra, Demo, Inner Canvas, experimentos, pruebas | (inferido) Función de material de la plantilla VR que detecta píxeles ocultos (usada en los materiales de teleport). |
| `M_TeleportCylinder` <br><sub>/Game/XRFramework/Materials</sub> | material | Obra, Demo, Inner Canvas, experimentos, pruebas | (inferido) Cilindro del destino de teleport de la plantilla VR de Epic. |
| `M_TeleportNoise` <br><sub>/Game/XRFramework/Materials</sub> | material | Obra, Demo, Inner Canvas, experimentos, pruebas | (inferido) Ruido animado del visualizador de teleport de la plantilla VR de Epic. |
| `M_VRCursor` <br><sub>/Game/XRFramework/Materials</sub> | material | Obra, Demo, Inner Canvas, experimentos, pruebas | Cursor esférico de impacto del láser del menú de la plantilla VR. |
| `NS_MenuLaser` <br><sub>/Game/XRFramework/VFX</sub> | Niagara | Obra, Demo, Inner Canvas, experimentos, pruebas | Láser del menú de la plantilla VR (Niagara); base de duplicados del proyecto. |
| `NS_PlayAreaBounds` <br><sub>/Game/XRFramework/VFX</sub> | Niagara | Obra, Demo, Inner Canvas, experimentos, pruebas | Límites del área de juego de la plantilla VR (Niagara). |
| `NS_TeleportRing` <br><sub>/Game/XRFramework/VFX</sub> | Niagara | Obra, Demo, Inner Canvas, experimentos, pruebas | Anillo de destino del teleport de la plantilla VR (Niagara). |
| `NS_TeleportTrace` <br><sub>/Game/XRFramework/VFX</sub> | Niagara | Obra, Demo, Inner Canvas, experimentos, pruebas | Arco del teleport de la plantilla VR (Niagara). |

## XRMannequins

| Asset | Tipo | Usado por | Qué hace |
|---|---|---|---|
| `BP_MannequinsXR` <br><sub>/Game/XRMannequins</sub> | Blueprint | Obra, Demo, Inner Canvas, experimentos, pruebas | Manos del maniquí de la plantilla VR de Epic que usa el pawn. |
| `MF_Diffraction` <br><sub>/Game/XRMannequins/Materials/Functions</sub> | función de material | Obra, Demo, Inner Canvas, experimentos, pruebas | (inferido) Función de material de la plantilla con brillo de difracción para el maniquí. |
| `MF_logo3layers` <br><sub>/Game/XRMannequins/Materials/Functions</sub> | función de material | Obra, Demo, Inner Canvas, experimentos, pruebas | (inferido) Función de material de la plantilla que compone el logo del maniquí en tres capas. |
| `ML_BaseColorFallOff` <br><sub>/Game/XRMannequins/Materials/Functions</sub> | capa de material | Obra, Demo, Inner Canvas, experimentos, pruebas | (inferido) Capa de material de la plantilla con degradado del color base del maniquí. |
| `M_Mannequin` <br><sub>/Game/XRMannequins/Materials</sub> | material | Obra, Demo, Inner Canvas, experimentos, pruebas | (inferido) Material original del maniquí de la plantilla VR de Epic. |
| `ABP_MannequinsXR` <br><sub>/Game/XRMannequins/Meshes</sub> | anim BP | Obra, Demo, Inner Canvas, experimentos, pruebas | Animation Blueprint de las manos del maniquí: anima los dedos con el input. |

## Plugin SC_Base

| Asset | Tipo | Usado por | Qué hace |
|---|---|---|---|
| `BPC_AppearLuz_SC` <br><sub>/SC_Base/Blueprints</sub> | componente | Obra, Demo, Inner Canvas, experimentos, pruebas | Componente de aparición luz primero: Appear() de 1,5 s con trazo de luz y Vanish() con la misma curva al revés. |
| `BP_Anchor` <br><sub>/SC_Base/Blueprints</sub> | Blueprint | Obra, Demo, Inner Canvas, experimentos | TargetPoint visible solo en el editor (esfera fantasma y nombre del tag) que marca dónde nace algo. |
| `BP_QuestCtrl_SC` <br><sub>/SC_Base/Blueprints</sub> | Blueprint | Obra, Demo, Inner Canvas, experimentos, pruebas | El mando visible para el usuario: forma de Quest sin botones, cuerpo negro y tapa gris-blanca. |
| `MPC_HUD_SC` <br><sub>/SC_Base/Materials</sub> | parámetros de material | Obra, Demo, Inner Canvas | Doblez del HUD (CurveR) que aplican por WPO los materiales del HUD; lo escribe BP_SoulHUD3D_SC. |
| `MPC_Perf_SC` <br><sub>/SC_Base/Materials</sub> | parámetros de material | Obra, Demo, Inner Canvas, experimentos | PerfMode del banco de medición: los shaders lo leen para cambiar de modo; lo escribe BP_PerfSwitch_SC. |
| `M_AnchorGhost_SC` <br><sub>/SC_Base/Materials</sub> | material | Obra, Demo, Inner Canvas, experimentos | Material de ameba que viene de Core/Amoeba (antes también se llamaba M_ProtoSoul); en SC_Base. Solo lo usa MI_Ghost; no confundir con M_ProtoSoul (el alma). |
| `M_AppearTrace_SC` <br><sub>/SC_Base/Materials</sub> | material | Obra, Demo, Inner Canvas, experimentos, pruebas | Trazo de luz de la aparición: aditivo de dos caras (Sweep, Head, Glow). |
| `M_Beam_SC` <br><sub>/SC_Base/Materials</sub> | material | Obra, Demo, Inner Canvas, experimentos | Haz unlit emisivo para punteros y rayos. |
| `M_ControllerMain_SC` <br><sub>/SC_Base/Materials</sub> | material | Obra, Demo, Inner Canvas, experimentos | (inferido) Segundo material viejo importado con la malla del mando (antes /Game/Material_002). En uso: mallas ControllerL/R y BreathL/R (nombre heredado). |
| `M_ControllerSecond_SC` <br><sub>/SC_Base/Materials</sub> | material | Obra, Demo, Inner Canvas, experimentos | (inferido) Material viejo importado con la malla del mando (antes /Game/Material_001). En uso: mallas ControllerL/R (nombre heredado). |
| `M_DrawPalette_Groove_SC` <br><sub>/SC_Base/Materials</sub> | material | Obra, Demo, Inner Canvas, experimentos, pruebas | Ranura de la paleta de dibujo con el color activo; también la usa la ranura del hang. |
| `M_DrawPalette_SC` <br><sub>/SC_Base/Materials</sub> | material | Obra, Demo, Inner Canvas, experimentos, pruebas | Cuerpo de la paleta de dibujo: unlit con sombreado HLSL; también padre de los materiales del hang. |
| `M_HeartScape_SC` <br><sub>/SC_Base/Materials</sub> | material | Obra, Demo, Inner Canvas, experimentos | Membrana mate del latido, con la esfera central y sus ondas. |
| `M_PointerDot_SC` <br><sub>/SC_Base/Materials</sub> | material | Obra, Demo, Inner Canvas, experimentos | Punto de impacto del puntero: unlit translúcido de dos caras sin depth test. |
| `M_Pointer_SC` <br><sub>/SC_Base/Materials</sub> | material | Obra, Demo, Inner Canvas, experimentos | Láser del puntero: unlit translúcido de dos caras que se desvanece hacia la punta. |
| `M_QuestCtrl_SC` <br><sub>/SC_Base/Materials</sub> | material | Obra, Demo, Inner Canvas, experimentos, pruebas | Mando de Quest: unlit con sombreado falso y borde de luz. |
| `M_SCChargeSlider_SC` <br><sub>/SC_Base/Materials</sub> | material | Obra, Demo, Inner Canvas, experimentos, pruebas | Slider transparente aditivo que se llena con Progress 0..1 (timbre, SAVE). |
| `M_SCGlass_SC` <br><sub>/SC_Base/Materials</sub> | material | Obra, Demo, Inner Canvas | Vidrio de la familia SC con el doblez del HUD. |
| `M_SCLight_SC` <br><sub>/SC_Base/Materials</sub> | material | Obra, Demo, Inner Canvas, experimentos, pruebas | Cintas de luz de la familia SC (Color × Glow × AppearGlow). |
| `M_SCObjectTrans_SC` <br><sub>/SC_Base/Materials</sub> | material | Obra, Demo, Inner Canvas | Hormigón translúcido de la familia SC (Flash, Opacity). |
| `M_SCObject_SC` <br><sub>/SC_Base/Materials</sub> | material | Obra, Demo, Inner Canvas, experimentos, pruebas | Hormigón de la familia SC para timbre, sensor, SAVE y HUD; no se tiñe. |
| `M_SCPanelGlass_SC` <br><sub>/SC_Base/Materials</sub> | material | Obra, Demo, Inner Canvas, pruebas | Vidrio de paneles en el mundo: como M_SCGlass_SC, pero sin doblez y con depth test. |
| `M_SCPanel_SC` <br><sub>/SC_Base/Materials</sub> | material | Obra, Demo, Inner Canvas, pruebas | Hormigón translúcido de paneles en el mundo: sin doblez y con depth test. |
| `M_TextUnlit` <br><sub>/SC_Base/Materials</sub> | material | Obra, Demo, Inner Canvas, experimentos, pruebas | Texto unlit para TextRender (el de fábrica es Lit y sale negro sin luces). |

## Plugin SC_Breath

| Asset | Tipo | Usado por | Qué hace |
|---|---|---|---|
| `BP_BreathBlob_SC` <br><sub>/SC_Breath/Blueprints</sub> | Blueprint | Obra, Demo, Inner Canvas | Metaball de respiración que crece y se mueve con el aliento (lee MPC_Breath). |
| `BP_BreathRig_SC` <br><sub>/SC_Breath/Blueprints</sub> | Blueprint | Obra, Demo, Inner Canvas | Mando-sensor solo para la respiración, activo solo en Entering; publica la señal en MPC_Breath. |
| `BP_Pacer_SC` <br><sub>/SC_Breath/Blueprints</sub> | Blueprint | Obra, Demo, Inner Canvas | Reloj guía de respiración en 3 modos (Aros, Órbita, Arco) que indica cuándo inhalar; no es sensor. |
| `MPC_Breath` <br><sub>/SC_Breath/Materials</sub> | parámetros de material | Obra, Demo, Inner Canvas | La señal de respiración (Signed, On) que leen aire, valle y metaball. |
| `M_BreathBlob_SC` <br><sub>/SC_Breath/Materials</sub> | material | Obra, Demo, Inner Canvas | Metaball de respiración por raymarch (solo modo 0). |
| `M_BreathCtrl_SC` <br><sub>/SC_Breath/Materials</sub> | material | Obra, Demo, Inner Canvas | Mando de respiración emisivo (CtrlColor × CtrlBrightness); duplicado de M_SeqCtrl_SC. |
| `M_Pacer_SC` <br><sub>/SC_Breath/Materials</sub> | material | Obra, Demo, Inner Canvas | Dibujo del pacer de respiración; el BP le empuja Lung, Cycle y Phase. |

## Plugin SC_Draw

| Asset | Tipo | Usado por | Qué hace |
|---|---|---|---|
| `BPC_TBTool_NC` <br><sub>/SC_Draw/Blueprints</sub> | componente | Obra, Demo, Inner Canvas | Herramienta de dibujo: presión, comenzar y alimentar trazos, historial y undo/redo. |
| `BP_DrawPalette_SC` <br><sub>/SC_Draw/Blueprints</sub> | Blueprint | Obra, Demo, Inner Canvas, pruebas | Paleta física 3D de dibujo: arte y estado visual (colores, pinceles, grosor). |
| `BP_TBDirector_NC` <br><sub>/SC_Draw/Blueprints</sub> | Blueprint | Obra, Demo, Inner Canvas | Director de Surrounding: maneja el dibujo, el bloqueo, guardar y el cierre por TimeUp; contrato de etapa. |
| `BP_TBPalette` <br><sub>/SC_Draw/Blueprints</sub> | Blueprint | Obra, Demo, Inner Canvas | Paleta vieja de pinceles y botones (undo, redo, clear, save, color) en un ProceduralMesh; aún da el ancla del arte. |
| `BP_TBStroke` <br><sub>/SC_Draw/Blueprints</sub> | Blueprint | Obra, Demo, Inner Canvas | Trazo estilo Tilt Brush: cinta generada con pinceles, presión y vaivén. |
| `BP_TBTable` <br><sub>/SC_Draw/Blueprints</sub> | Blueprint | Obra, Demo, Inner Canvas | Mesa de dibujo: disco de 40 cm que ancla el dibujo y se desvanece al borde. |
| `BP_TBTrail_NC` <br><sub>/SC_Draw/Blueprints</sub> | Blueprint | Obra, Demo, Inner Canvas | Estela/trazo en vivo, hijo de BP_TBStroke, con sus mismos pinceles. |
| `MF_TB_Grad` <br><sub>/SC_Draw/Materials</sub> | función de material | Obra, Demo, Inner Canvas | Función de material: degradado de tinte al final del emisivo en los maestros de trazo. |
| `MF_TB_StrokeU` <br><sub>/SC_Draw/Materials</sub> | función de material | Obra, Demo, Inner Canvas | Función de material: coordenada U del trazo con punta fija de 4 cm. |
| `MF_TB_Sway` <br><sub>/SC_Draw/Materials</sub> | función de material | Obra, Demo, Inner Canvas | Función de material: vaivén suave de los trazos y colapso al guardar (Reveal). |
| `MPC_TB_Table` <br><sub>/SC_Draw/Materials</sub> | parámetros de material | Obra, Demo, Inner Canvas | (inferido) Parámetros globales de la mesa de dibujo que leen los materiales del trazo. |
| `M_DrawPaletteSwatch_SC` <br><sub>/SC_Draw/Materials</sub> | material | Obra, Demo, Inner Canvas, pruebas | Casquete central de la paleta que muestra el color elegido. |
| `M_DrawPalette_Glass_SC` <br><sub>/SC_Draw/Materials</sub> | material | Obra, Demo, Inner Canvas, pruebas | Banda del slider de la paleta: translúcido (Opacity 0,35). |
| `M_DrawPalette_Ink_SC` <br><sub>/SC_Draw/Materials</sub> | material | Obra, Demo, Inner Canvas, pruebas | Arco de tinta restante de la paleta: unlit translúcido de dos caras. |
| `M_TBHand_NC` <br><sub>/SC_Draw/Materials</sub> | material | Obra, Demo, Inner Canvas | Mano de dibujo: unlit opaco con Tint gris. |
| `M_TBRibbon_NC` <br><sub>/SC_Draw/Materials</sub> | material | Obra, Demo, Inner Canvas | Cinta base del trazo: unlit translúcido de dos caras. |
| `M_TB_Additive` <br><sub>/SC_Draw/Materials</sub> | material | Obra, Demo, Inner Canvas | Maestro de trazos aditivos (unlit, dos caras), como luz o resaltador. |
| `M_TB_Clear` <br><sub>/SC_Draw/Materials</sub> | material | Obra, Demo, Inner Canvas | Botón de borrar todo de la paleta (glifo X rojiza). |
| `M_TB_ColorWheel` <br><sub>/SC_Draw/Materials</sub> | material | Obra, Demo, Inner Canvas | Rueda de color de la paleta. |
| `M_TB_Icon` <br><sub>/SC_Draw/Materials</sub> | material | Obra, Demo, Inner Canvas | Icono de cada pincel en la rejilla de la paleta. |
| `M_TB_Masked` <br><sub>/SC_Draw/Materials</sub> | material | Obra, Demo, Inner Canvas | Maestro de trazos enmascarados (unlit, dos caras), como vinilo o marcador. |
| `M_TB_Paint` <br><sub>/SC_Draw/Materials</sub> | material | Obra, Demo, Inner Canvas | Maestro de trazos de pintura con relieve falso (óleo, pintura húmeda). |
| `M_TB_Redo` <br><sub>/SC_Draw/Materials</sub> | material | Obra, Demo, Inner Canvas | Botón rehacer de la paleta (flecha espejada de M_TB_Undo). |
| `M_TB_Save` <br><sub>/SC_Draw/Materials</sub> | material | Obra, Demo, Inner Canvas | Botón guardar de la paleta (marco con rombo dorado y progreso radial al sostener). |
| `M_TB_Slider` <br><sub>/SC_Draw/Materials</sub> | material | Obra, Demo, Inner Canvas | Barra de slider de la paleta (Fill). |
| `M_TB_Solid` <br><sub>/SC_Draw/Materials</sub> | material | Obra, Demo, Inner Canvas | Maestro de trazos sólidos opacos con color de vértice. |
| `M_TB_Swatch` <br><sub>/SC_Draw/Materials</sub> | material | Obra, Demo, Inner Canvas | Muestra del color actual en la paleta (Col). |
| `M_TB_Table` <br><sub>/SC_Draw/Materials</sub> | material | Obra, Demo, Inner Canvas | Disco azulado de la mesa de dibujo que se desvanece al borde (TableOpacity, TableFade). |
| `M_TB_TipHalo` <br><sub>/SC_Draw/Materials</sub> | material | Obra, Demo, Inner Canvas | Halo aditivo en la punta del pincel con anillos. |
| `M_TB_UIColor` <br><sub>/SC_Draw/Materials</sub> | material | Obra, Demo, Inner Canvas | Elementos de interfaz de la paleta con emisivo = color de vértice. |
| `M_TB_Undo` <br><sub>/SC_Draw/Materials</sub> | material | Obra, Demo, Inner Canvas | Botón deshacer de la paleta (flecha curva). |

## Plugin SC_Sequencer

| Asset | Tipo | Usado por | Qué hace |
|---|---|---|---|
| `BP_BlobChain_SC` <br><sub>/SC_Sequencer/Blueprints</sub> | Blueprint | Obra, Demo, Inner Canvas, experimentos | Gusano de metaballs por malla que une las esferas de los slots del secuenciador. |
| `BP_ChladniFloor_SC` <br><sub>/SC_Sequencer/Blueprints</sub> | Blueprint | Obra, experimentos | Piso y cielo de Attracting: salar pastel al ocaso cuyo mandala de Chladni responde a la música. |
| `BP_OrbDirector_SC` <br><sub>/SC_Sequencer/Blueprints</sub> | Blueprint | Obra, Demo, Inner Canvas, experimentos | Director de las esferas de sonido: aparición, regreso a su sitio y cono de partículas al sostenerlas. |
| `BP_SaveMelodyArt_SC` <br><sub>/SC_Sequencer/Blueprints</sub> | Blueprint | Obra, Demo, Inner Canvas, experimentos, pruebas | Arte y aparición del botón SAVE MELODY. |
| `BP_SaveMelody_SC` <br><sub>/SC_Sequencer/Blueprints</sub> | Blueprint | Obra, Demo, Inner Canvas, experimentos | Botón SAVE MELODY: se sostiene para guardar la melodía. |
| `BP_SeqRig_SC` <br><sub>/SC_Sequencer/Blueprints</sub> | Blueprint | Obra, Demo, Inner Canvas, experimentos | Rig de mandos del secuenciador: láser, agarrar esferas, botón y hápticos (Pulse); también lo usa Inner Canvas. |
| `BP_SeqSlot_SC` <br><sub>/SC_Sequencer/Blueprints</sub> | Blueprint | Obra, Demo, Inner Canvas, experimentos | Slot del secuenciador donde se deja una esfera de sonido. |
| `BP_Sequencer_SC` <br><sub>/SC_Sequencer/Blueprints</sub> | Blueprint | Obra, Demo, Inner Canvas, experimentos | Secuenciador musical de Attracting: cabezal, slots y melodía; contrato de etapa (guarda o cierra). |
| `BP_SoundOrb_SC` <br><sub>/SC_Sequencer/Blueprints</sub> | Blueprint | Obra, Demo, Inner Canvas, experimentos | Esfera flotante con sonido que se agarra y se coloca en un slot. |
| `M_BlobCore_SC` <br><sub>/SC_Sequencer/Materials</sub> | material | Obra, Demo, Inner Canvas, experimentos | Núcleos blancos translúcidos de las esferas del secuenciador. |
| `M_BlobMesh_SC` <br><sub>/SC_Sequencer/Materials</sub> | material | Obra, Demo, Inner Canvas, experimentos | Gusano del secuenciador por desplazamiento de vértices. |
| `M_BlobOrb_SC` <br><sub>/SC_Sequencer/Materials</sub> | material | Obra | Esferas del secuenciador con sombreado half-lambert bicolor. |
| `M_ChladniFloor_SC` <br><sub>/SC_Sequencer/Materials</sub> | material | Obra, experimentos | Salar de Chladni de Attracting: polígonos de sal, grano de granito y mandala que responde a la música. |
| `M_SeqCtrl_SC` <br><sub>/SC_Sequencer/Materials</sub> | material | Obra, Demo, Inner Canvas, experimentos | Mando emisivo del secuenciador (CtrlColor × CtrlBrightness). |
| `M_SlotChain_SC` <br><sub>/SC_Sequencer/Materials</sub> | material | Obra, Demo, Inner Canvas, experimentos | Metaball por raymarch de la cadena del secuenciador (versión anterior al gusano por malla). |
| `NS_OrbAttract_SC` <br><sub>/SC_Sequencer/VFX</sub> | Niagara | Obra, Demo, Inner Canvas, experimentos | Partículas que van de la esfera agarrada a la mano (AttractRate). |
| `NS_OrbHalo_SC` <br><sub>/SC_Sequencer/VFX</sub> | Niagara | Obra, Demo, Inner Canvas, experimentos | Halo de partículas mínimas alrededor de cada esfera flotante. |
