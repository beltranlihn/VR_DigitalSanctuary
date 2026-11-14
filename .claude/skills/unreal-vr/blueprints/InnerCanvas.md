# Inner Canvas — los Blueprints de `/Game/InnerCanvas/Blueprints` (tracker conjunto)

Experiencia de dibujo de pie para 8 visores PICO + una pantalla de PC con los 8 dibujos. Plan y guion:
[`docs/innercanvas/PLAN-INNER-CANVAS.md`](../../../../docs/innercanvas/PLAN-INNER-CANVAS.md). Creada el 2026-11-11.
Todo se arma por DSL desde `VR_Test/Saved/ClaudeScripts/InnerCanvas/` (fuente de verdad de los grafos): `ic_*_dsl.py` →
`dump_ic.py` → `codes_<bp>.json` → escritor dentro de Unreal (`execute_tool_script`: borra los nodos de la función salvo la
entrada y escribe). Estructura (variables, funciones, componentes): `ic_spec.py` / `ic_spec_wall.py` → `build_ic.py`.

| BP | Nivel | Qué hace | Estado |
|---|---|---|---|
| `BP_ICFlow_IC` | `L_InnerCanvas` | Director. **Desde el 2026-11-12 se escribe con `ic_flow2_dsl.py`** (toma `ic_flow_dsl.py` y reemplaza): fases 0-13 = idioma tocando, mando a la mano tocándolo, teclado, tutorial (`FlowTut`/`TutAct` con `TutAt`), herramientas en las manos (`StageIntro`), espacio, HUD + 5 min, dibujo, presentación (2 vueltas y se va), cierre (`FEndShow`: el plano `Title` toma `MI_TourTitle_ENDES/ENDEN` y se pone a 3 m al frente; `FVeil` fase 11 = niebla 2-5 s, mensaje 1-2,6 s, se va 15-17 s; `ICReset` le devuelve `TitleMI`), orden del PC (`FlowTick` lee `Link.Cmd` → `RemoteCmd(Mode)`: 1 = `ResetOrientationAndPosition` + `ICReset`, 2 = `ICReset`). `FResetPick` y el botón RESET del visor ya no se usan. Pistas: una vez al entrar y otra cuando termina la voz (`Clk1` = ya mostrada) | 🟢 `-game` (2026-11-12 tarde: orden del PC por 9301 → recentra y reinicia; cierre ES y EN con capturas; 0 errores) · ⬜ visor |
| `BP_ICTutor_IC` | `L_InnerCanvas` | Tutorial visual (nuevo 2026-11-12): paleta de muestra (`BP_DrawPalette_SC` creada en runtime con los colores del dibujo) + el `BP_QuestCtrl_SC` del pedestal; etiquetas `L0-5` y líneas `K0-5` (`MI_ICLabel_IC`, atlas `T_ICLabels` de `tools/innercanvas/gen_tutor_tex_ic.py`) en dos columnas (`LabOff` relativo al centro de la paleta); la línea termina en el borde de la etiqueta. `TutDemo` (etiquetas fuera, toca color, pincel y dibuja) · `TutOut` (se desarma) · `TutHide` | 🟢 `-game` con capturas · ⬜ visor |
| `BP_ICHudKit_IC` | `L_InnerCanvas` | HUD de la Obra: nombre al centro, reloj a la derecha, círculo de tinta verde a la izquierda | 🟢 `-game` |
| `BP_ICKeyboard_IC` | `L_InnerCanvas` | Teclado A-Z (+Ñ en español), ESPACIO, BORRAR, OK; 32 teclas planas con `M_ICKey_IC` y el atlas `T_ICKeyAtlas`; el nombre en un RT | 🟢 `-game` |
| `BP_ICVoice_IC` / `BP_ICAmb_IC` | `L_InnerCanvas` | Voces IC_01..IC_12 (EN/ES) con subtítulos; música | 🟢 |
| `BP_ICSpace_IC` | los dos | Espacio 3 × 3 m: piso y 4 paredes (`M_ICSpace_IC`); aparece con la voz y queda tenue; cada pared se enciende al acercarse cabeza o mano. `AutoPlace` lo lleva al PlayerStart (en el PC va en false) | 🟢 |
| `BP_ICLink_IC` | `L_InnerCanvas` | Visor → PC por OSC/UDP: estado, nombre, trazos nudo por nudo (≤ 24 por cuadro), presentación. `-ICSlot= -ICWall= -ICPort=`. **Órdenes del PC**: servidor OSC en `CmdPort` 9301 (`-ICCmdPort=`), `OnCmd` lee `/ic/cmd` [visor, modo, id] (acepta su número o 0, ignora un id repetido: el PC lo manda 3 veces) y deja `Cmd`; el Assign se cableó a mano (gotcha 4) | 🟢 red real (visor → PC, 11-12) · 🟢 orden PC → visor en `-game` |
| `BP_ICWall_IC` | `L_InnerCanvas_Wall` | PC: servidor OSC 9300, reconstruye los trazos con `BP_TBStroke` en la celda de cada visor (x = k × 1 km), presentación (`OnPresent` → `PresStep`: `RevealCell` 1→0, `Relocate` centra a escala ≤ 1, `RevealCell` 0→1, giro), limpia la celda con una sesión nueva. Las 8 `SceneCapture2D` frontales (−751, 0, 180, pitch −2,5, FOV 30) dibujan en RT 960 × 1080 (`AssignCaps`, por cercanía). Perillas `PresFit` 290, `PresHideT` 2, `PresShowT` 2,5 | 🟢 `-game` + `.exe` con 8 visores falsos (2026-11-12) |
| `BP_ICWallHUD_IC` / `BP_ICWallGM_IC` | `L_InnerCanvas_Wall` | HUD (Canvas) 4 × 2 con número, nombre, tiempo y tinta / GameMode con ese HUD y pawn espectador. **Botones por cuadro** RESET / REINICIAR (`AddHitBox` R0-7 / S0-7; `OnBtn`: el primer clic arma "¿SEGURO?", el segundo antes de 3 s llama `BP_ICWall_IC.SendCmd`), y "ESPERANDO RESET" en fase 11. `SendCmd` manda `/ic/cmd` a la IP de la que llegó ese visor (`IPs`, `SetRxIP` antes de `OnMsg`), puerto 9301, 3 veces. Prueba sin mouse: `-ICTestCmd=N` manda RESET al visor N a los 25 s | 🟢 `-game` (orden real a un visor `-game`) · ⬜ clic en el `.exe` |

## Gotchas que costaron tiempo (2026-11-11)
1. **`(and (Utilities|IsValid x) ...)` se come la función.** Hay tres nodos `Utilities|IsValid`; en un `and` el DSL agarra el MACRO
   (con exec) y la función queda vacía, sin error. Leer de vuelta (`read_graph_dsl`) mostró `StrokeKnot` con un solo nodo. Usar la
   forma con ramas `(Utilities|IsValid x (:"Is Valid" ...))` como última sentencia del bloque.
2. **OSC: `GetOSCMessageStringAtIndex` cuenta TODOS los argumentos** (los floats también) y sus salidas van (valor, éxito).
3. **OSC de Unreal: un byte por letra y extiende el signo al leer.** La Ñ (0xD1) llega como U+FFD1 (`OSCStream.cpp`: `ReadChar`).
   `OnName` la devuelve. Un emisor que mande UTF-8 (Python) llega peor: el simulador manda Latin-1, como Unreal.
4. **`AssignOnOscMessageReceived` escrito por DSL crea un evento SIN parámetros.** Se crea el nodo Assign con `create_node`
   (genera el evento con la firma), se cablea a mano y se conecta su `Message` a `OnMsg`. Antes de recompilar varias veces, guardar.
5. **Celdas del PC a 1 km**: a 30 m las cámaras veían los dibujos de las celdas vecinas. A 1 km el cielo de 300 m de cada
   `BP_DrawSea_SC` las tapa. La cercanía de las paredes (`NearOf`) corta a 5 m afuera: si no, desde 1 km todas las paredes se encendían.
6. **Captura `-game` a 960 × 540**: líneas al 20 % de opacidad desaparecen al reducir 768 × 864 → 240 × 270. En el PC `BaseAlpha` 0,35.
7. `save_assets([])` guarda TODO lo sucio, también BPs de los plugins marcados como sucios por lecturas (pasó con `BP_TBDirector_NC`,
   `BPC_TBTool_NC`, `BP_TBStroke`: mismo tamaño que en git, ruido de guardado). Pasar siempre la lista explícita.

8. **`GetAttachedActors` es PURO** (función `const` de C++ = nodo puro). Un `for` sobre él lo re-evalúa en cada vuelta: al soltar o
   destruir dentro del bucle se saltea la mitad. Síntoma (2026-11-12): en la presentación del PC la mitad de los trazos subía con el
   pivote (~127 cm) y la otra quedaba invisible; `ClearCell` dejaba la mitad del dibujo anterior. Se copia a la variable `Tmp` antes
   del bucle. Mismo cuidado con cualquier getter puro que devuelva un array que el bucle modifica.
9. **4K en el PC**: el HUD dibuja en píxeles de 1080 × `_u = H / 1080`; `pantalla.ps1` llama `SetProcessDPIAware` antes de leer el
   monitor (sin eso un 4K al 150 % da 2560 × 1440).

10. **`HUD|DrawText` con una fuente Runtime rasteriza a su `LegacyFontSize` y estira con `Scale`**: Quicksand de la obra es 9 →
    ×3 a ×6 en 4K = pixelado. Copia `/Game/InnerCanvas/UI/F_ICWall_IC` a 64 y escala `_f = _u × 9/64` (achicar queda nítido).
11. **Oscurecer un cielo brillante**: el cielo del mar está en el hombro del tonemapper; × 0,55 lo bajó solo 8 % en pantalla (el agua,
    25 %). Medir el píxel antes y después (`PIL getpixel`) en vez de confiar en el factor.

## Ajustes 2026-11-12 (Beltrán)
- Visor: `PresentK` 1 (no crece), `BP_TBDirector_NC.HoldTime` 26 en la instancia de `L_InnerCanvas` (≈ 2 vueltas a 24°/s) y
  `DrawTick` fase 14 pasa al cierre cuando el dibujo terminó de irse (`SketchT` > 0 y `SketchPhase` 0; tope `SpinShow` + 40 s).
  Medido en `-game`: presentación → cierre 32,9 s.
- Sin mesa: `BP_TBTable.Disc` con `bHiddenInGame` en la instancia (el sistema de dibujo solo hace `SetActorHiddenInGame`).
- PC: los 8 `BP_DrawSea_SC` con los 27 valores verdes del mar de `L_InnerCanvas`; franjas oscuras detrás del texto.
- PC: banner arriba con la señal de cada visor (`DrawCells`, edad de `LastRx`: < 3 s OK, < 15 s débil, si no sin señal); RT 960 × 988;
  el espacio no se muestra (sin `SpaceReveal` en `WallBoot`).
- Visor: paredes solo con la cercanía (`SpaceTick` sin `_intro` en las paredes, `BaseAlpha` 0 en la instancia); HUD subido 4 cm
  y pitch −23 (actor `BP_SoulHUD3D_SC` del nivel). 🔴 `set_actor_transform` por MCP NO corre el Construction Script: el offset
  horneado (`HeadOffsetLoc/Rot`) se actualizó recién al recargar el nivel; verificar leyendo la propiedad después de recargar.

## Recorrido nuevo del inicio (2026-11-12 noche, acordado con Beltrán)
Bloque `RECORRIDO = True` al final de `ic_flow2_dsl.py`: pisa `FPlaceBtns`, `PickLang`, `IntroTick`, `KbWait`, `TutAct`, `GuideTick`,
`Grab` y el reparto de `FlowTick`. Copia previa: `ic_flow2_dsl.py.bak_recorrido`.

**Fases:**
- **0** Título. El piso del espacio ya está marcado: `SpaceReveal` + `RevealT` = 10, sin la subida. Los botones de idioma van en
  un panel a 1,5 m, 55 cm bajo los ojos, inclinados 15°, y los láseres de los dos rigs están prendidos.
- **1** Idioma con láser y gatillo (`PickLang` del 11-11).
- **2** Bienvenida (IC_01) y teclado.
- **3** Nombre con láser. IC_13 cuando termina la bienvenida.
- **4** HUD con nombre, 5:00 y tinta llena + IC_23 (tiempo y tinta). El reloj no corre.
- **5** `SpaceReveal` otra vez: el piso sube y las 4 paredes se encienden (`_intro × 0,55` en `SpaceTick`) + IC_24.
- **6** Tutorial (`FlowTut`/`TutAct`, `TutAt` = 0,8 · 4,2 · 6,2 · 8,5 · 11 · 13,6 · 15,6 · 19 · 26,6 · 28).
- **7** Al terminar la demo, el MISMO mando del tutorial se suelta del tutor y flota hacia `PedBase` (`VInterpTo`/`RInterpTo`
  1,6 s), después gira con `GrabStep` + IC_04 + pista de tocar.
- **Grab → 8:**
  - `FHoldPed` (el mando a la mano hábil).
  - `TutOut`: la paleta de ejemplo se desarma. `OutStep` solo achica el mando si sigue colgado del tutor, y `TutHide` lo esconde
    a 1,3 s.
  - `StageIntro`: paleta y pincel a las manos.
  - IC_25 "El lienzo es tuyo".
- **9** A 1,2 s: `StageBegin` + `TimerT` 0: se dibuja y corre el reloj (`DrawTick` igual que antes).

**Detalles:**
- `IntroTick` hasta la fase 3. `GuideTick` de 4 a 8 (`Clk2` = "ya se dijo / instaló" en cada fase). El gatillo del mando en la
  mano corre desde la 8.
- **Voces:** valores de `BP_ICFlow_IC`: `VoGo` = IC_23, `VoSpace` = IC_24, `VoInvite` = IC_25 (los nombres de variable quedaron
  viejos). IC_02, IC_03, IC_06 e IC_22 ya no suenan.
- `BP_ICVoice_IC`: `VoEN`/`VoES` 25 pares y subtítulos de `subs_ic_ue.json`.
  - 🔴 `set_properties` no deja cambiar el largo y el contenido de un arreglo a la vez ("ArrayAdd… ambiguous"): primero `[]` y
    después la lista.
  - En la instancia no se pueden escribir (no son editables): toman el CDO al recompilar.
- **Pista HINT_LANG:** "Point and press the trigger · Apunta y aprieta el gatillo".

## Recorrido v2 con MARCO de instrucciones (2026-11-12 noche, PDF + nota de voz de Beltrán; memoria ic-recorrido-v2-marco)
Reemplaza al recorrido de la tarde (que sigue en `ic_flow2_dsl.py` como bloque `RECORRIDO`; el v2 es el bloque `RECORRIDO2`, que pisa
sus funciones). Todo con mano + láser hasta el final; nadie toma nada.
- **Fases:** 0 título + ENGLISH/ESPAÑOL + pista bilingüe debajo (`HintShow` modo 1) · 1 idioma · 2 bienvenida + teclado + pista
  "Apunta y presiona el gatillo para escribir tu nombre" debajo (modo 2) · 3 nombre · 4 HUD + IC_23 · 5 marco (`FlowTut`/`TutAct`,
  `TutAt` = 0,8 4,2 6,2 8,5 11 13,6 15,6 19 27) · 6 cartas de la mano (`PickHand`: `CardHov` por rig, gatillo) · 7 `HandChosen`:
  herramientas en las manos (`StageIntro`), manos del pawn ocultas, borde del piso (`SpaceReveal`), IC_27 · 9 a 0,6 s dibujo y reloj.
  Final (`FEndShow`): niebla + título y logo EN SU LUGAR (`FPlaceTitle`, `TitleMI`), se quedan (`FVeil` ya no los saca a 15-17 s).
- **`BP_ICTutor_IC` v2** (`ic_tutor2_dsl.py`, `ic_spec_tutor.py`): `Frame` (`M_ICPanel_IC`, 137 × 75 cm a 110 cm, `FrameW/H/X/Z`),
  `Logo` (`MI_TourTitle_INNERCANVAS`), `Hdr`; paleta a `PalScale` 0,91 (sin la espera de 3 s: `SetAppearDelay 0`) y mando a
  `PedScale` 1,8, entran juntos en 0,5 s. Etiquetas = texto liso (`M_ICText_IC` + atlas `T_ICTexts`, `tools/innercanvas/gen_texts_ic.py`
  → `texts_rects.json`), punto en el ancla (`DA`) y en la punta (`DB`), punta = ancla + `LabB[k]`. Mantos `M0..M4`
  (`M_ICMantle_IC`, sector de anillo) colgados de la `Base` de la paleta (medidas de la malla: plato −0,886, teclas 5,66-14,84,
  laterales −2,44, slider r 21,7 a z −1,7); ángulo de slider/undo/redo por su caja real × `MSign`. Cartas `CardL/CardR` + `CardHit`
  (colisión solo con las cartas a la vista), paletas chicas (la zurda espejada en X) y `BP_QuestCtrl_SC` chicos. `Warn` = aviso de
  borde colgado de la cámara del pawn (`WarnSet`). `Kill(A)` = destruir si es válido (gotcha 1: IsValid como última sentencia).
- **`BP_ICSpace_IC`**: en el visor (`AutoPlace`) el piso se ve siempre con el círculo, el punto y una muesca hacia el título
  (`RingA` 0,6, `Front` = dirección al TargetPoint `sc4_title` × `FlipX/FlipY`); el borde con `SpaceReveal`; paredes solo por cercanía.
  `WarnOn` = cabeza a < `WarnIn` 30 cm de un borde (sale a > `WarnOut` 45). `SpaceReset` apaga Alpha (si no, el borde quedaba).
- **Materiales nuevos** (`build_ic_mats2.py`, HLSL en `mat/`): `M_ICText_IC`, `M_ICPanel_IC`, `M_ICMantle_IC`; `M_ICSpace_IC` + `RingA`, `Front`.
- **Voces:** IC_26 "¿Con qué mano vas a dibujar? Apunta y elige." (`VoTut[8]`) · IC_27 "Este es tu espacio de dibujo. El lienzo es
  tuyo." (`VoInvite`). Arreglos de `BP_ICVoice_IC` desde `voice_vals2.json` (62 ids, 27 pares).
- **Probado en PIE sin visor (perillas de prueba):** del inicio al dibujo 58 s sin errores; del nombre al dibujo 48 s.
- ⚠ **Componentes agregados al CDO con el BP ya colocado en el nivel: la INSTANCIA los recibe vacíos** (StaticMesh None, rotación 0,
  sin material), aunque la plantilla quedó bien. Por eso `TutBoot` les pone malla, rotación y material en runtime. Verificar siempre el
  componente de la instancia (`...PersistentLevel.BP_X_C_0.Comp`), no el de la plantilla.
- ⚠ **Paleta zurda de las cartas = la misma receta del sistema de dibujo** (`PlaceArt`: escala (s, −s, s)) + giro de 180° en su plano
  para que el espejo quede izquierda-derecha. Con la X negativa, `ApplySideScale` (SideSize / escala) agrandaba undo/redo enormes.
  Mando zurdo = `BP_QuestCtrl_SC` con `SetLeft` + `ApplyHand` + `ApplyTrigger`.
- **Ajustes de Beltrán (11-12 noche):** nada sale del marco → `PalY` 13 (paleta 8 cm hacia el centro), `PedY` 52, Draw `LabB[5]` y −6,5;
  medido en PIE: el texto más a la izquierda termina a 10 cm del borde. Mantos más transparentes (`Fade` × 0,6 en `LabTick`).
  Undo/Redo más grandes en la paleta del marco (`SetSideSize` 1,25 + `ApplySideScale`; mantos 19-27,6 cm, ±17°). Cartas 52 × 30 cm,
  `MiniPal` 0,5, `MiniCtl` 1,25, mando a ∓15,5 y +5 cm de alto, inclinado ±20° (zurdo: mallas L sin el giro de 180°); rótulos debajo.
- **Segunda pasada:** mantos de undo/redo COLGADOS DE CADA TECLA (`GetUndo`/`GetRedo`, espacio de la malla SideKey: centro −165,7°, r 19,6-26,
  ±14,5°, z −2,6): siguen su tamaño (SideSize), su corrimiento y su despliegue. Calcularlos desde la Base fallaba al agrandar las teclas.
  "Dibujar" 6 cm por delante del mando (el mando lo tapaba), `LabB[5]` y −8; `PedY` 43, `PalY` 15.
- 🔴 **El láser no llegaba a los botones de idioma** (VR Preview de Beltrán): los planos del tutor (en la instancia, con la colisión por
  defecto BlockAllDynamic) viajan con la pista bajo los botones y el `Frame` invisible de 137 × 75 cm los tapaba. `TutBoot` apaga la
  colisión de TODOS sus componentes; `CardHit` se enciende solo con las cartas. Verificado en PIE: todo `NoCollision`.
- 🔴 **Segundo bloqueo del láser: el plano `Board` del teclado** (QueryOnly, oculto, en (−245, 0, 190): delante, a la altura de las manos).
  Ahora solo tiene colisión con el teclado a la vista (`IntroTick :2` lo enciende, `GuideTick :0` e `ICReset` lo apagan; `FBoot` lo
  apaga). `FBoot` también apaga la colisión del mando del pedestal y de `BP_TBTable` (ocultos, BlockAllDynamic); el tutor apaga la de
  sus paletas y mandos (`SetActorEnableCollision`). Regla: **lo oculto sigue chocando** — antes de un láser, revisar qué hay delante.
- 🔴 **Cartas sin hover ni gatillo:** el láser en modo resultados (`TickBeamRes`) es `LineTraceForObjects` con tipo **Destructible**; `CardHit`
  tenía el tipo por defecto. `CardsSpawn` le pone `SetCollisionObjectType ECC_Destructible` + QueryOnly (como el `Board` del teclado).
- **Tercera pasada (11-12 noche):** botones de idioma a escala 1,5 (la del editor; `FPlaceBtns` los dejaba en 1). Logo de Alma BLANCO:
  `M_ICLogo_IC` (copia de `M_TourLogo_SC` con color = C0, no el de la textura; `FBoot` se lo pone al componente `Logo`, la Obra no se toca).
  **Teclado dentro del marco:** `BP_ICTutor_IC.FrameShow` pone el actor donde van las instrucciones con marco + logo (`FrameOn`), el
  director pone el teclado delante (−1,5; 0; −6) a escala 0,9 con teclas claras (`Accent` 0,85/0,9/0,88); la pista del nombre va dentro
  del marco, abajo; el marco sigue sin cortes hasta las instrucciones (`TutBegin` no mueve el actor si `FrameOn`). Subtítulos apagados
  mientras se ve el marco (se encimaban) y de vuelta en `HandChosen`. **HUD nítido:** nombre (`NameWork` 2048 × 512 → `NameRT`
  1024 × 256) y reloj (512 → 256) con la fuente de 64 `F_ICWall_IC` (la Quicksand de 9 estirada se pixelaba); `HudShow` alinea nombre y
  reloj a la cabeza (antes al "arriba" del mundo del arranque: quedaban girados).
- **Cuarta pasada (11-13):** paneles 1 m más lejos (`Dist` 210; después Beltrán: 60 cm más cerca → `Dist` 150, instancia y CDO); teclado a x 5 (2 cm delante del panel, antes −1,5);
  logo INNER CANVAS centrado en el panel del teclado (`FrameShow`); al elegir el nombre el panel se va (`SetFrameOn false` en
  `GuideTick :0`; `TutTick` lo funde con `FrameK`) y las instrucciones entran después con paleta y mando. Campo del nombre 56 × 14 cm
  (4:1 como `NameRT`; a 81 × 12 el texto se veía achatado) en z 24,5, texto 2,5 / 1,85. HUD: nombre y reloj pegados al vidrio
  (z 0,3 local del arte, rotación relativa 0; antes 1,97 ≈ 1 cm adelante) con prioridad de orden 12. Final: `SpaceReset` en `FEndShow`
  (se va el borde, queda el círculo) y el piso con prioridad 32650 (sobre el velo de 32600): el círculo se ve en la niebla blanca.
- **Voces v3 (11-13, guion aprobado por Beltrán):** idioma y nombre SIN voz (`IntroTick :2/:3`). Con el HUD suena la bienvenida
  narrativa `VoGo` = IC_28 (24,7 s ES: "Te damos la bienvenida a Inner Canvas… Tienes cinco minutos para dibujar y expresarte
  libremente. Antes de empezar, conoce tus herramientas."); al terminar entran juntos marco + paleta + mando. Al irse a blanco suena la
  reflexión `VoThanks` = IC_29 (20,8 s ES: "Cada trazo que dejaste es una parte de ti que encontró su forma. Todos podemos crear; todos
  somos artistas. Llévate este lienzo contigo. Gracias por participar en Inner Canvas. Ya puedes quitarte las gafas."). Ya no se usan
  IC_01, IC_13 ni IC_23. Arreglos de `BP_ICVoice_IC` desde `voice_vals3.json` (66 ids, 29 pares). La música (`BP_ICAmb_IC`) ya arranca
  con el nivel y hace loop.
- **Cierre partido (11-13):** mientras el dibujo gira, `VoLook` = IC_30 (22,9 s ES: "Vuelve al centro y mira a tu alrededor. Este es tu
  lienzo interior. Cada trazo que dejaste es una parte de ti que encontró su forma. Todos podemos crear; todos somos artistas. Llévate este
  lienzo contigo."); cuando el dibujo ya se fue, `VoThanks` = IC_31 (6,2 s: "Gracias por participar en Inner Canvas. Ya puedes quitarte
  las gafas."). IC_29 queda sin uso. Arreglos de voz desde `voice_vals4.json` (70 ids, 31 pares). Nombre del HUD al 75 % (`HudShow`).
- **Reinicio desde el visor (11-13):** mantener los DOS grips 5 s (`GripHoldT` en `FlowTick`, cualquier fase) = `RemoteCmd 1`, lo mismo
  que RESET del PC: recentra donde está parada la persona y reinicia. Lee `IA_Hand_Grasp_L/R` (el grip analógico de la animación de la
  mano, que llega en el visor) con `IA_Grab_*_Pressed` de respaldo (máximo de los dos > 0,7). Tras disparar, `GripHoldT` = −30 (no se
  repite aunque sigan apretando). ⬜ Probado solo que compila: falta el visor.
- **Quinta pasada (11-13):** (1) la bolita del láser solo va al punto si el actor golpeado tiene el tag **`Aimable`**
  (`BP_SeqRig_SC.PlaceDotHitR`): el tutor lo lleva (CDO e instancia) → la bolita llega a las cartas. (2) "Dibujar" a la profundidad de
  las otras etiquetas (`Anch[5]` x = `_ax`) y `LabB[5]` y −14 (el mando lo tapaba). (3) HUD plano: `HudCurve` 0 en la instancia de
  `L_InnerCanvas` (era 56: los nidos se doblaban 0,9 cm hacia adelante y tapaban el círculo de tinta → titilaba); el círculo pegado al
  vidrio (z 0,3, rotación 0, prioridad 12). (4) Nombre largo: `KbDraw` mide el texto (`Canvas|ClippedTextSize`) y lo achica para no pasar
  de 1126 px de 2048 (el ancho de la caja del HUD). (5) Fondo del marco 15 % más transparente (`Rim.y` 0,272 en `TutBoot`).
- **Sexta pasada (11-13):** subtítulos de las voces siempre encendidos (el teclado y `FlowTut` ya no los apagan). Música: `FadeIn`
  de `BP_ICAmb_IC` 3 → 0,3 s (con 3 s se oía recién con los botones). Logo de Alma: `M_ICLogo_IC` usa el alfa de `T_Logo_ADS` tal cual
  (2048 × 512); el corte en 0,5 de la receta de la Obra (para campos de distancia) se comía los trazos finos y se veía en baja.
  Unreal se colgó una vez al detener PIE con una consulta en curso: después del reinicio todo estaba guardado (38 actores, perillas OK).
- Botones de idioma y su pista centrados bajo el TÍTULO: el yaw sale de la dirección al TargetPoint `TagTitle`, no de la mirada inicial
  (`FPlaceBtns` y la pista en `IntroTick :0`, `TY_EXPR` en el bloque `RECORRIDO2`).
- ⚠ `codes_tutor2.json` pasó los 80 KB que lee `AssetTools.read_file`: se escribe en dos partes (`codes_tutor2_0/1.json`).
- Mantos de colores y pinceles a z −0,30 de la malla (a −0,83 el plato de la paleta los tapaba); undo y redo ±12° (a ±15 se juntaban).
- ⚠ Escritor: un error de PARSEO del DSL (p. ej. `bind` repetido en la misma función) aborta el script entero aunque esté en try. Antes de
  escribir, escanear binds duplicados por función (los `for` con la misma variable sí se pueden repetir).

## Sonidos de Beltrán (2026-11-13, mezclados en Ableton: NO tocar volúmenes en Unreal)
Fuente: `Desktop/Sonidos/*.wav` (24 bit 48 kHz) → `Content/InnerCanvas/Audio/SFX/SND_IC_<nombre>` (pasados a 16 bit con dither, mismo
pico; el pad de 7:12 pesa 79 MB en wav y 43 MB el asset). Todo se reproduce a volumen 1 (`BP_ICAmb_IC.Volume` 1, `SfxVol` 1).
| Momento | Dónde | Sonido |
|---|---|---|
| Aparecen los botones de idioma (UNA vez para los dos) | `BP_ShareButton_SC_C_0.AppearLuz.AppearSound`; el `_C_1` en None | `SND_IC_SpawnButtonIdioma` |
| Gatillo sobre un botón de idioma | `PressSound` de `_C_0` y `_C_1` | `SND_IC_SelectButtonIdioma` |
| Hover de los botones | sin cambio (`SND_Demo_HoverOn/Out`). La salida de los botones sigue con `SBubbleHoverOut` | — |
| Hover de una tecla | `BP_ICKeyboard_IC.HoverSound` (nuevo; `KbTick`: suena cuando `H1`/`H2` cambia a otra tecla ≥ 0, `PH1`/`PH2` = la anterior) | `SND_IC_HoverTecla` |
| Gatillo sobre una tecla | `BP_ICKeyboard_IC.ClickSound` | `SND_IC_SelectTecla` |
| Aparece el HUD | `BP_ICHudKit_IC.ShowSound` (la salida `PlopSound` sigue `SND_Demo_HudOut`) | `SND_IC_SpawnHUD` |
| Entra una paleta (la del marco y la de la mano) | `BP_ICTutor_IC.PalSndAll(false)` | `PalInSound` = `SND_IC_PaletteIn` |
| Se va una paleta / entran las chicas de las cartas | `PalSndAll` pone `VanishSound` None siempre y `AppearSound` None con `Mute` | — |
| Aparece / se va el dibujo completo (cierre) | `BP_TBDirector_NC_C_0.ShowSound` / `HideSound` (`SketchAppear`/`SketchVanish`) | `SND_IC_DrawIn` / `SND_IC_DrawOut` |
| Pad de fondo | `BP_ICAmb_IC_C_0.Clip` (asset con `bLooping` true, como el anterior) | `SND_IC_PadFondo` |
- `PalSndAll(Mute)`: recorre las `BP_DrawPalette_SC` vivas y escribe `AppearSound`/`VanishSound` en la paleta (la copia a su
  `BPC_AppearLuz_SC` al crearlo en `AppearEnsure`) y, si el componente ya existe, también en él. La llaman `TutBegin`, `CardsSpawn`
  (`Mute`), `HandChosen` (después de `StageIntro`) y `GuideTick :3` (después de `StageBegin`). ✅ PIE: la paleta de la mano
  (`ArtAnchor` de `BP_TBPalette`) quedó con PaletteIn / None en la paleta y en su componente. Sin errores hasta el dibujo.
- **Ajustes de Beltrán (11-13, después de oír; segunda pasada):** pad `BP_ICAmb_IC_C_0.Volume` **0,5**; hover de teclas
  `BP_ICKeyboard_IC.HoverVol` **0,2** (va al `VolumeMultiplier` de los dos `PlaySound2D` de `KbTick`); trigger de teclas
  `BP_ICKeyboard_IC.ClickVol` **0,5** (perilla nueva, `PlaySound2D` de `KbPress`); **hover de las cartas de mano** (faltaba):
  `TutTick` (con `CardsOn`, antes de elegir: `PickT` < 0) compara `Hov` con `PrevHov` → sale de una carta = `CardOutSound`, entra =
  `CardHovSound` (los mismos de los botones de idioma: `SND_Demo_HoverOn/Out`, a volumen 1); `CardsSpawn` pone `PrevHov` −1. PIE sin
  errores hasta el dibujo; el hover en sí solo se oye con láser (visor).
- **APK 2026-11-13 02:28 + pantalla 02:29** (`Recursos/Inner Canvas/APK|Pantalla/...`). Gafa 1 (`PA94Y0MGJ9240807G`): desinstalados
  `soulchargerdemobi` e `innercanvas` viejos, instalado el nuevo con `-Slot 1 -Wall 192.168.0.190` (router de Alma; Beltrán: dejarla
  para ese router aunque el PC esté en otra red). Arranca: LINK visor 1 → 192.168.0.190:9300, corrección PICO ON, título.
- ⚠ `instalar_pico_ic.ps1 -Lanzar` daba "arranco: False" en falso: el runtime PICO llena logcat con
  `XR_ERROR_EYEGAZY_PERMISION_NOT_ENABLE_BD` (~70 líneas/s) y las líneas UE se pierden. Ahora borra y lee el log de la app en el visor
  (`.../files/UnrealGame/VR_Test/VR_Test/Saved/Logs/VR_Test.log`). Probado en la gafa 1: `arranco: True`.
- Gafas 2-8 instaladas igual (`visores_ic.json` con las 8 series; las 8 arrancan con `LINK: visor N -> 192.168.0.190:9300`). En la
  gafa 8 saltó la guardia nueva del instalador ("la app todavia no creo su carpeta") y quedó bien a la primera. ⚠ **Gafa 7: Unreal sin log ni `Saved/`** aunque corría a 72 FPS:
  su primera apertura tardó más que los 4 s del instalador, y el `mkdir -p` de adb creó `files/UnrealGame/VR_Test` (dueño `shell`) y
  `/sdcard/UnrealGame/VR_Test` antes que la app → Unreal no podía escribir ahí. Arreglo: borrar las dos, abrir la app (crea la suya en
  ~5 s), cerrar y recién ahí escribir la línea. El instalador ahora espera a que exista la carpeta de la app antes de escribir.
- **Pantalla del PC en el TV 4K (11-13, foto de Beltrán: "todo pixelado"):**
  - Causa: `pantalla.ps1` leía `Screen.Bounds`, que aun con `SetProcessDPIAware` da 1280 × 720 para un TV 4K al 300 % (la escala
    del sistema es la de la principal) → el juego salía en 720p y el TV lo agrandaba ×3. Ahora usa `EnumDisplaySettings` (DEVMODE:
    posición y tamaño en píxeles reales) → `-WinX=1920 -ResX=3840 -ResY=2160 -fullscreen`, ventana medida 1920,0 → 5760,2160.
  - Textos chicos rotos aun en 4K: salían de la fuente de 64 px reducida ×4 (el Canvas no tiene mips). Fuentes por tamaño, ~1:1 en
    4K: `F_ICWall_IC` 64 (título), `F_ICWallM_IC` 32 (número, nombre, reloj; escala `_fm` = `_u`·0,28125), `F_ICWallS_IC` 18 (el
    resto; `_fs` = `_u`·0,5).
  - **Sin botones RESET / REINICIAR** (Beltrán: el reinicio desde las gafas anda perfecto): fuera las 16 `AddHitBox` y los botones;
    franja de arriba de cada celda 40 px de 1080 (era 52); cursor y clics apagados (pines de `EventGraph`, sin reescribirlo).
  - Medido en el exe a 4K con 8 visores simulados: 37 FPS, GPU 24 ms (las 8 capturas de 960 × 988; bajar la vista principal con
    `r.ScreenPercentage 10` no cambia nada). Capturar al doble para suavizar los trazos finos bajaría a ~10-15 FPS: no se hizo.
  - 🔴🔴 **LA causa real del pixelado (11-13 10:30): el juego NO reconocía la escala de Windows.** Unreal en modo juego solo se
    declara DPI-aware con `[/Script/Engine.UserInterfaceSettings] bAllowHighDPIInGameMode=True` (`SlateApplication.cpp` ~1023);
    sin eso, en el TV 4K al 300 % Windows le daba 1280 × 720 y lo ESTIRABA ×3 (bordes rectos nítidos, letras y trazos en bloques
    de 3 × 3; `GetWindowDpiAwarenessContext` = 0, DPI 96). `-ini:Engine:[...]:bAllowHighDPIInGameMode=True` por línea de comandos NO
    alcanzó. Arreglo: los `.bat` hacen `set __COMPAT_LAYER=HighDpiAware` antes de `start` → awareness 2, DPI 288, 4K real (columnas
    vecinas idénticas en los dibujos: 69 % → 2 %). **Abrir SIEMPRE con los `.bat`, no con el `.exe`.** ⚠ Una captura de pantalla
    (`CopyFromScreen`) muestra lo mismo estirado: de lejos parece bien; hay que ampliar sin filtro o medir píxeles repetidos.
    Las fuentes 4K se recalibraron para el tamaño que se veía (= 3 × las de 1080): título 54, ALMA 21, VISOR 24, OK 21,
    ESPERANDO 24, número 30, nombre/reloj 33. Cámaras: `FOVAngle` 30 (Beltrán: más zoom, puede cortar arriba y abajo).
  - Dibujos con dientes en 4K real (la captura no tiene antialiasing y se mostraba 1:1; "ayer se veía mejor" porque en 720p se
    achicaba ×2): RT de cada celda **3840 × 1976** (el doble de la celda) y el HUD la reduce a la mitad = antialiasing 2×.
    Medido: 44 FPS, GPU 21,8 ms (4 capturas).
  - 🔴 **Texto del Canvas = SIN filtrar** (copia el texel más cercano): con `:Scale` ≠ 1 salen dientes. Cada texto va a `:Scale 1.0`
    con su fuente `F_ICW<n>_IC` (LegacyFontSize n) y en posición entera; juego 4K (H ≥ 1600) y juego 1080. El raster de
    LegacyFontSize n sale ~1,45× lo estimado: tamaños MEDIDOS contra la captura vieja (4K: título 36, ALMA 11, VISOR 15, OK 12,
    ESPERANDO 15, número 19, nombre/reloj 22; 1080: la mitad, mínimo 7). `FS`/`FS2` del HUD ya no se usan.
  - **4 visores (11-13 10:20, Beltrán):** HUD en 2 × 2 (celdas 1920 × 988 en 4K, apaisadas), RT = 1920 × 988, señal de 4 visores
    arriba. En `L_InnerCanvas_Wall`: cámaras `FOVAngle` 45 (era 30; ~3,2 m de alto a 7,5 m) y las 5-8 sin capturar
    (`bCaptureEveryFrame`/`bCaptureOnMovement` false). Los visores 5-8 se siguen recibiendo pero no se dibujan.
  - Carpeta lista en `Desktop/Inner Canvas Pantalla` (build 03:20, `InnerCanvas_Pantalla.bat` / `_Ventana.bat` en la pantalla 2;
    `Configurar_IP_Picos.bat` pide confirmación).
- **Versión del evento archivada (11-14):** `Projects/Packagings/Inner Canvas v1.0/` (fuera del repo), con `APK PICO/` (02:28 +
  `visores_ic.json`), `APK Quest/` (variante `innercanvasquest`, 11-13 16:33), `Windows Pantalla/` (build 10:37, la que estaba en el
  escritorio) y un `LEEME.txt`. Ya no hay copia en el escritorio.
- ⚠ `PH1`/`PH2` no son instance-editable: `set_properties` en la instancia falla; toman el −1 del CDO.
- ⚠ `read_graph_dsl` rotula los setters de la paleta como `BPCAppearLuzSC|SetAppearSound` (mismo nombre de variable en las dos
  clases): el `self` real se ve con `get_node_infos` (0-2 = BP Draw Palette SC, 3-5 = BPC Appear Luz SC).
- La auto-elección de mano de prueba (`AutoHand`) espera 3 s (antes 2), pedido para el video de diseño sonoro.
- 🔴 **Voces = DIRECTO de ElevenLabs, SIN NINGÚN PROCESO (regla de Beltrán 11-13).** Ni normalizar, ni filtrar, ni remuestrear: el
  `loudnorm` + soxr de `gen_vo_demo.py` agregaba una banda espuria de 12-14 kHz y él las oyó "sin antipop". `gen_vo_ic.py` usa ahora
  `tts_raw`: `pcm_24000` de `/with-timestamps` escrito tal cual en un wav de 24 kHz mono 16 bit (la cuenta no permite `pcm_44100` ni
  `mp3_44100_192`: 403). El nivel se ajusta SOLO en Unreal: `BP_ICVoice_IC_C_0.Voice.VolumeMultiplier` (la variable `Volume` del BP
  no está cableada). Regeneradas las 17 que se usan × 2 idiomas (respaldo de las anteriores en
  `Saved/ClaudeScripts/InnerCanvas/vo_backup_1113/`); subtítulos nuevos en `voice_vals5.json` (CDO, la instancia los sigue).
  Copias tal cual en `Desktop/InnerCanvas_VoiceOver_ElevenLabs/{ES,EN}` (orden de aparición).
- Niveles medidos: voces crudas −15 a −19 LUFS (mediana −16,9), picos hasta −0,4 dBTP; pad nuevo −15,7 LUFS (el viejo −25,7). La voz
  queda ~1 LU bajo el pad (en el video estaba 4,7 LU sobre el pad viejo). No se puede subir sin saturar: `VolumeMultiplier` 1. Suma
  voz + pad en el peor punto (poema sobre el final del pad): −0,35 dBFS. Decisión pendiente de Beltrán: bajar el pad en su mezcla.

## Gatillo animado del mando en la mano (2026-11-12, pedido de Beltrán)
- `FlowTick` lee el gatillo con el nodo de valor **`IA_Shoot_Right/Left`** (`IMC_Weapon_*`: Trigger_Click de OculusTouch y PICO;
  es lo que escribe en el teclado y dibuja, probado en los dos visores). `FBoot` hace `EnableInput`. Es 0/1: el mando lo suaviza
  con su `FInterpTo`. Fases 4 y ≥ 6: `SetTrigger` al mando del pedestal (en la 5 lo mueve el tutorial). El mando de dibujo de la
  mano hábil recibe el `Value` ya suavizado del pedestal (`TrigApply`). Log `IC: gatillo 1/0` en cada cambio.
- 🔴 **`IA_Hand_IndexCurl` da 0 en cuanto alguien agrega `IMC_Weapon_*` con prioridad 1000** (el rig y el dibujo lo hacen):
  OpenXR arma un action set por cada contexto de `DefaultMappingContexts` y con `XR_EXT_active_action_set_priority` el de mayor
  prioridad se queda con el gatillo (`OpenXRInput.cpp` `SyncActions`). `IMC_TB_Draw_R` no está en esa lista → `IA_TB_Pressure_R`
  no recibe nada de OpenXR (el `TrigStep` del director de dibujo nunca animó). Segundo intento (`IndexCurl`): no se movía.
- 🔴 **`GetInputAnalogKeyState` con teclas XR da SIEMPRE 0**: con Enhanced Input, OpenXR inyecta el valor en la acción
  (`InjectInputForAction`, `OpenXRInput.cpp` ~1198) y no emite la tecla. Solo las `LegacyActions` emiten teclas. Primer intento
  (por tecla) probado por Beltrán en VR Preview con Quest: no se movía. El respaldo por tecla de `TrigStep` también está muerto.
  - Fase 4 (teclado, mando del pedestal en la mano): `BP_QuestCtrl_SC.SetTrigger` con la mano hábil.
  - Siempre: `BP_TBDirector_NC.TrigApply` sobre `TrigR/TrigL` (los gatillos que crea `InstallCtrl`).
- 🔴 El `TrigStep` propio del director de dibujo lee `IA_TB_Pressure_*` + la tecla OculusTouch, y **`IMC_TB_Draw_R/L` no tiene
  teclas PICO**: en Pico, su gatillo quedaba quieto. Por eso `FBoot` hace `AddTickPrerequisiteActor(TB)`: el director de IC
  tickea DESPUÉS del de dibujo y su valor gana. No se tocó el plugin.
- `FHoldPed` e `ICReset` llaman `ApplyTrigger` después de `ApplyHand`, para la trampa del zurdo de `BP_QuestCtrl_SC`.
- `read_graph_dsl` muestra mal `SetTrigger` como `MetaSoundParameterPack|SetTrigger` y `GetTrigR` como `BPMirrorLinkSC`. Por los
  pines (`get_node_infos`) son los correctos.
- 🟢 Compila; PIE sin errores · ⬜ gatillo real en visor (Quest Link y Pico) con la versión de `IndexCurl`.

## Mano nueva de Inner Canvas (2026-11-12 noche, pedido de Beltrán: "la mano de VR template es horrible")
- Fuente: **"Free Pack – VR Hands (Rigged)" de PolyOne Studio, CC-BY 4.0** (uso comercial OK, **hay que darle crédito**).
  Original y licencia en `C:\Users\beltr\Desktop\vr-hand\`. Unos 1.660 triángulos por mano.
- `tools/innercanvas/mano_ic_encaje.py` (Blender en segundo plano) la lleva al esqueleto `SK_MannequinsXR` sin tocarlo: marco
  completo por hueso (segmento + normal de la palma, que controla el GIRO, lo que falló el 09-03), estira sin trasladar, skinning
  a mano con los pesos originales. Continuidad 0,0 mm en las 10 articulaciones. La izquierda es el espejo en X. `--render` = prueba
  de flexión (`flex_hoja.png`): se dobla igual que la de Manny.
- Assets en `/Game/InnerCanvas/Hands/`: `SKM_ICHand_R/L` (esqueleto `SK_MannequinsXR`) + `M_ICHand_IC` (copia de `M_QuestCtrl_SC`,
  unlit con sombreado propio, `bUsedWithSkeletalMesh`) + `MI_ICHand_IC` (`BodyColor`/`CapColor` 0,80/0,82/0,81).
- `BP_ICFlow_IC.FHands` (en `ic_flow2_dsl.py`) cambia la malla y el material en los componentes `HandRight/HandLeft` del pawn
  **en tiempo de ejecución**: el pawn de la Obra no se toca. El material va al componente porque el pawn trae `MI_Hand_SC`.
  Volver atrás = `FHands` del base.
- 🟢 PIE: los dos componentes con la malla nueva, el material y `ABP_MannequinsXR`, sin errores · ⬜ VR Preview / visor.
- **v6 (mismo día, después del VR Preview de Beltrán):** él vio el índice "corrido", un pliegue en la membrana pulgar-índice y el
  índice que no se doblaba con el gatillo; además pidió achicarla un poco.
  - **Encaje:** pasa a un **thin-plate spline** (40 referencias: las 21 articulaciones exactas + puntos hacia el dorso de cada
    falange para el giro + antebrazo) en vez de matrices por hueso. Esas mezclaban mal donde la palma y el dedo no coincidían, y
    el afín de la palma arrugaba el antebrazo.
  - **Pesos:** se copian de la mano de Manny por cara más cercana (`DATA_TRANSFER`), con metacarpianos incluidos. Los originales
    estaban pensados para otro pivote del pulgar.
  - **Normales:** las personalizadas del modelo NO se pasan (`--normales` lo intenta, pero deja manchas). Unreal las calcula.
  - **Assets:** se reimportó como `SKM_ICMano_R/L`: `import_file` no sobrescribe un asset existente. Las `SKM_ICHand_*` se borraron.
  - **Índice:** `IA_Hand_IndexCurl` nunca llega (OpenXR: `IMC_Weapon` a 1000 le gana), así que `FlowTick` escribe
    `ABP_MannequinsXR.PoseAlphaIndexCurl` en cada componente "Hand*" con `FInterpTo` (16) hacia `IA_Shoot_Right/Left`.
    Con la mano vieja tampoco se doblaba.
  - **Tamaño:** `FHands` pone escala 0,9 en el componente.
- 🟢 PIE: malla v6 y escala 0,9 en las dos, sin errores. Beltrán en VR Preview: el índice anda; el pulgar se ve aplastado y en
  punta, y las yemas angulosas.
- **v7** (`SKM_ICMano7_R/L`, 3.618 vértices y unos 6.700 triángulos por mano):
  - La base del pulgar (CMC) queda libre: forzarla a la de Manny estiraba el pulgar 48 %.
  - Cada punta conserva el largo propio de la yema.
  - 4 puntos de sección por falange (6 mm) mantienen el dedo redondo.
  - 1 nivel de subdivisión sobre la malla original (yemas redondas).
  - Script v6 guardado como `mano_ic_encaje_v6.py`. ⬜ VR Preview.
- **MODO COMPARAR (activo, pedido de Beltrán):** `COMPARAR = True` en `ic_flow2_dsl.py`.
  - La mano de Manny queda en el pawn, con su `MI_Hand_SC` blanco translúcido y escala 1.
  - `FHands` agrega a `BP_ICFlow_IC` un `SkeletalMeshComponent` por mano (`AddComponentbyClass :Class …`, con el pin por NOMBRE:
    en posición cae en `self` y el compilado dice "must have a class specified"). Lo cuelga del componente de la mano, con la v7,
    `MI_ICHandCmp_IC` (copia de `MI_Hand_SC` en verde), escala 0,9 y `SetLeaderPoseComponent` hacia la mano de Manny.
  - PIE verificado. Para volver a una sola mano: `COMPARAR = False` y reescribir `FHands`.
- **v8** (`SKM_ICMano8_R/L`): con las dos manos superpuestas Beltrán vio el pulgar más delgado y aplastado.
  - `section_extent` mide el grosor de cada falange del pulgar en las dos mallas (vértices a ±3 mm del medio, marco de la falange).
  - La sección destino del pulgar se agranda en esa proporción: ×1,18/1,00 en la falange proximal y ×1,32/1,19 en la distal
    (palma-dorso / ancho).
  - Script v7 guardado como `mano_ic_encaje_v7.py`. Beltrán: "Perfecto".
- **FINAL (2026-11-12 noche): una sola mano.**
  - `COMPARAR = False`: la v8 va en el componente del pawn, **blanca translúcida** (`MI_Hand_SC` de la Obra, con su fundido hacia
    la muñeca, que tapa el antebrazo del modelo) y escala 0,9.
  - `MI_ICHandCmp_IC` se borró.
  - `M_ICHand_IC`/`MI_ICHand_IC` (gris opaco) quedan sin uso, como alternativa.
  - 🟢 PIE: `SKM_ICMano8_R/L`, `MI_Hand_SC` y 0,9 en las dos manos, sin errores · ⬜ visor Pico.
  - **Crédito CC-BY:** "Hands: PolyOne Studio (Sketchfab), CC-BY 4.0" va en el **cartel físico** del evento, que pone Beltrán.
    No va dentro del VR.

## Corrección de poses del PICO (en `BP_ICFlow_IC`)
`PicoBoot` / `PicoAim` / `PicoTB` / `PoseTick` + componentes `AimFixR/L` (MotionController sin fuente: `MotionSource` ICFixR/L,
`bAutoActivate` false, `bDisableLowLatencyUpdate` true). Perillas `PicoAimPitch` −15, `PicoAimFwd` 5, `PicoGripUp` 2 (CDO), y por
línea de comandos `-PicoFix=0/1 -PicoAimPitch= -PicoAimFwd= -PicoGripUp= -PoseDump`. No toca `BP_SeqRig_SC` ni
`BP_TBDirector_NC`: les cambia las referencias (`AimR/L`, `RightAim`) y reinstala la punta. Detalle: PLAN §5.
Probado con `-PicoFix=1` en `-game`: 2 sesiones completas, 0 errores. ⬜ valores en el visor.
