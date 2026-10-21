# BP_DemoMenu_SC — el menú de la demo (Barcelona Design Week)

- **refPath**: `/Game/SoulCharger/Demo/Blueprints/BP_DemoMenu_SC` · parent Actor · creado 2026-10-16 (sesión Director, pedido de Beltrán).
- **Nivel**: `/Game/SoulCharger/Demo/Maps/L_Demo_Menu` (copia de `Test_Hall` sin la lógica ni la geometría del Hall: queda la niebla azul `BP_HallFog_SC` con `bStartOn`, el título `BP_IntroTitle_SC` y `BP_HallAmbience_SC`). PlayerStart en (−3600, 0, 76,97), el punto de arranque del título de la Obra.
- **Estado**: 🟡 compila; ⬜ PIE del recorrido completo; ⬜ visor.

## El orden (pedido de Beltrán, 2026-10-16)
Título SOUL CHARGER sobre el fondo azul → botón **START** (láser + gatillo, un clic) → se va el título, aparecen los **dos cuadros** (ENTERING / SURROUNDING) y START se convierte en **BACK** → al elegir, los botones se van animados → **velo degradado** con los colores de la etapa → `OpenLevel` → en la etapa, Alma y después el panel de instrucciones.

## Piezas que encuentra (por tag / clase, en `Boot`)
| Variable | Qué | Cómo |
|---|---|---|
| `BtnStart` | START/BACK (un solo actor) | `BP_ShareButton_SC` con tag `demo_start` (escala 1,5) |
| `BtnA` / `BtnB` | cuadros ENTERING / SURROUNDING | `BP_ShareButton_SC` con tag `demo_a` / `demo_b`, mallas `SM_DemoCard_*` por instancia, `TopShare` = `MI_DemoCard_PlateTop{Entering,Surrounding}_SC`, `Hit` (0,95; 15,2; 9,7) en (0,9; 0; 0) |
| `Rig` | el láser | `BP_SeqRig_SC` en modo resultados (`ResultsBeam`), `bMountButton` false |
| `Title` | título | tag `hall_intro_title` |

## Variables
- **Menu** (por instancia): `LevelA` `L_Demo_Breath` · `LevelB` `L_Demo_Draw` · `TopA/HorA`, `TopB/HorB` = colores del velo de cada etapa (= `CTop/CHor` del ensayo de su nivel) · `TopMenu/HorMenu` = colores de la niebla (el velo abre "de niebla a niebla") · `EyeRef` 120 · `MIStart` / `MIBack` (las etiquetas del botón).
- **Debug**: `DebugPick` (−1 apagado; 1 o 2 = elige solo esa experiencia a los 2,5 s, START incluido). 🔴 Tiene que quedar en −1 en el APK.
- **Z-Estado**: `Phase`, `RT` (reloj del menú), `PT` (reloj de la fase), `LastPressN`, `Choice`, `DZ`, refs.

## Fases (EventTick, `Dt ≤ 1/30`)
| Phase | Qué | Sale con |
|---|---|---|
| 0 | espera la cámara | PT ≥ 0,2 → `Place` (sube/baja título y botones `cam.z − (PlayerStart.z + EyeRef)`, muestra el título) |
| 1 | velo abre RT 0,5→3 · título revela RT 1,5→5 | RT ≥ 4,5 → `ResultsBeam(true)`, START `Appear` |
| 2 | espera START (`Pick`) | clic → `Choose` → START `Press` |
| 3 | título sale (Out 0→1 en 2 s) | PT ≥ 2,2 → etiqueta BACK, `Appear` de BACK + los dos cuadros |
| 4 | elige (`Pick`) | BACK → fase 5 · cuadro → `Press` del elegido, `Vanish` del otro y de BACK → fase 6 |
| 5 | vuelve el título (Out 1→0) | PT ≥ 2,2 → etiqueta START, `Appear` → fase 2 |
| 6 | botones saliendo | PT ≥ 1,5 → `ResultsBeam(false)`, colores del velo = los de la etapa |
| 7 | velo cierra 0→1 en 2,5 s | PT ≥ 3 → fase 8 + `OpenLevel(LevelA/B)` |

`Pick` = copia de `BP_Obra_SC.SharePickStep`: hover = `Rig.BeamHitActor == botón` **y** `AppearLuz.AppearT ≥ 0,999` (el `Hit` responde aunque el botón esté oculto); clic = cambió `Rig.ResPressN`. `VeilFx`/`TitleFx` calculan todo desde la fase, sin parámetros (el DSL pierde los literales numéricos pasados a funciones propias).

## Trampas de esta construcción
- `read_graph_dsl` muestra `(Class|BPAlmaSC|Boot)` y `(Class|BPCAppearLuzSC|Appear …)`: **es una etiqueta mal puesta del read**; `get_node_infos` confirma `self` = el propio BP y `BP Share Button SC`.
- `Utilities|Equal(Object)` no existe: se compara objetos con `==`.


## v2 (2026-10-19, guion de Beltrán) — viaje, bienvenida, HUD y negro
- Fuente nueva: `VR_Test/Saved/ClaudeScripts/Demo2/menu_dsl.py` (todos los grafos reescritos; `Boot`, `Place`, `Choose`, `VeilFx`, `TitleFx`, `Pick`, `HoverFx`, `TravelStep`, `MenuTick`; `WaitMirror` intacta).
- Componente nuevo `Hint` (TextRender): "Point the button and press trigger" (fase 2) / "Point the experience of your choice and press trigger" (fase 4), 24 cm bajo START. Hover = escala ×`HoverScale` 1,07 (además de la luz del botón).
- Fases nuevas: 6 botones saliendo → `ResultsBeam(false)` (se van los mandos, vuelven las manos) + `Amb.Switch(Amb2)` (Ambient_Clip_2) → **7 viaje** (`TravelStep`: el pawn avanza `TravelCm` 1400 en `TravelTime` 18 s, perfil trapecio con `AccelTime` 2,5 / `BrakeTime` 3, los del Hall) + `VO_D01b`/`VO_D01d` → al terminar la voz **8** `Kit.HudInstall` → 2,6 s → **9** `VO_D02` → al terminar **10** velo a negro (`Black`) + `Amb.FadeAll` → 3 s → `OpenLevel`.
- El velo sigue a la cámara desde la fase 7. `Choose` pone `Kit.Mode` = elección y `Kit.TimeLeft` 150.
- En el nivel: `SpaceDust_0..2` (NS_SpaceDust_SC de Test_Hall), `SoulHUD` + `FaceAnchor` + `BioHub` + `DemoVoice` + `HudKit`.
- Probado en `-game` (`--extra="-MirrorRole=-1"`, `DebugPick` 1): START → cuadros → Breath → viaje 16 s de voz → HUD → ready → negro → Breath, 0 errores.

## 2026-10-19 (noche)
- **Robot**: `MenuRobot` (enlace en modo 2 → `bRobotM`) en la fase 10; el robot NO abre la experiencia (la abre `LevelStep` cuando el Quest aterriza; antes había ida y vuelta de niveles). Fase 11: si el robot sigue ahí 30 s, vuelve a `L_Demo_Menu`.
- Ayuda (`Hint`): `HintCm` 2 → 2,8 (se leía en el límite).

## 2026-10-20 — prueba de Beltrán en Unreal
- **Dos láseres**: segundo `BP_SeqRig_SC` en el nivel (`DemoRigL`, `bRightHanded` false); los dos con `bShowControllers` false y `bHideHands` false → se ven las manos, cada una con su láser. `Boot`: `Rig` = rig 0, `Rig2` = rig 1. `Pick` decide el clic por rig (cada uno cuenta solo su gatillo: `ResPressN`/`LastPressN`, `LastPressN2`) **antes** de actualizar los contadores (`_p1`/`_p2` son binds puros, gotcha 409). Fases 1 y 6: `ResultsBeam` de los dos.
- **Niebla azul**: `BP_HallFog_SC` del nivel con `bStartOn` true (nunca había estado: el menú se veía negro al abrir el velo) y `FadeOut` 18; la fase 6 llama `FogOff` → degrada a negro durante el viaje.
- **Viaje**: `TravelTime` 32, `AccelTime`/`BrakeTime` 4 (instancia). La bienvenida espera `VoDelay` (4 s, variable nueva).
- **Fase 8**: `HudInstall` → 2,6 s → `VoMeasure` (`VO_D03`: "During this experience, we'll be measuring your neural activity, your heart activity, and a calm index.") → al terminar, `VoReady` → 9. Sin renumerar fases (`Said` se reusa).
- `Choose` pone el reloj del HUD en `DrawShowTime` (antes 150 fijo).
- Botones: `PressSound` = `ProtoSelect` (era `ChargeFinal`, 15 s).
- Fuente `Demo2/menu_dsl.py` (respaldo `menu_dsl_backup_1020.py`). Probado en `-game` con `DebugPick` 2: dos rigs, viaje, VO_D01d → HUD → VO_D03 → VO_D02 → negro → Draw, 0 errores.
- (tarde) Al elegir un botón vibra la mano que apretó: `BP_SeqRig_SC.Pulse` del rig que contó el clic (`GetRightHanded`).
- (tarde) **Tercer cuadro RECOGNIZING** (`CardRecognizing`, tag `demo_c`, `MI_DemoCard_PlateTopRecognizing_SC` + colores `MI_Demo_*_Recognizing_SC`): cuadros en Y +35 (ENTERING) / 0 (RECOGNIZING) / −35 (SURROUNDING). Variables `BtnC`, `bHovC`, `KC`, `BaseC`, `VoHeart` (`VO_D01h`), `LevelC` (`L_Demo_Heart`). `Choice` 3 = Heart: voz `VoHeart`, `OpenLevel(LevelC)`, `Kit.Mode` 3. Probado en `-game` con `DebugPick` 3 (devuelto a −1): elige, viaja, VO_D01h → HUD → VO_D03 → VO_D02 → negro → `L_Demo_Heart`; 0 errores. Fuente `Demo2/edit_menu_heart_1020.py`.

## 2026-10-20 (noche) — tras la prueba de Beltrán (fuente `menu_dsl.py`, `edit_menu_1020t.py` + parches; respaldos `menu_dsl_backup_1020t/1020n.py`)
- Variables nuevas `QuietT` (s de silencio desde que calló la voz) y `VoGap` (2,5, editable). Cada paso del viaje espera `VoGap` de silencio; `VoMeasure` a los 4 s del HUD; el cierre a negro dura 3,5 s y el nivel se abre a los 4 s. Instancia: `VoDelay` 6.
- `TravelStep` ya no frena: acelera en `AccelTime` y sigue a la velocidad de antes (`TravelCm / (TravelTime − (Accel+Brake)/2)`) hasta el cambio de nivel.
- Pistas como subtítulo: `ShowHint :Id (GetHintStart)` en la fase 0 (desde que el menú se ubica) y al volver con BACK; `HintPick` con los cuadros; `Choose` → `HideHint`. `HintStart`/`HintPick` de la instancia = ids `HINT_START`/`HINT_PICK` (el literal string a función propia se pierde). El TextRender `Hint` queda oculto.
- `VeilFx`: `Floor` 0 en fase ≥ 9 (con el velo en negro el piso de 0,02 se veía gris).
- 2026-10-20 (noche, 2): ya no llama `HallFog.FogOff` (nunca pasa a negro); el velo cierra en 6 s (`VeilFx`) al color de la experiencia elegida (`TopA/HorA`, `TopC/HorC` nuevas para Heart, `TopB/HorB`) y el nivel se abre a los 6,5 s. `Boot`: trazo de cada cuadro del color de su experiencia (`GetTrace` → `Color`) y el título en `TitleMI` (`MI_Demo_TitleDS_SC`, DIGITAL SANCTUARY) sobre el `TitleP` del título de la Obra.


## 2026-10-20 (noche, 2.ª tanda) — menú → experiencia más corto y sin click
- Variable `MasterMix` (SoundSubmix, `MasterSubmixDefault`); `Boot` arranca con el maestro en 1.
- Fase 8: `VO_D03` a los 2,5 s del HUD (antes 4), "You're ready" a los 3 s (antes 5). Fase 9: el cierre arranca con `QuietT` ≥ 0,6 (antes `VoGap`) y **sin `FadeAll`** (la música seguía 3 s y después ~4 s de silencio). Fase 10: maestro 1 → 0 entre 3 y 6 s; `OpenLevel` a los 6,5 s.
- CDO `VoGap` 1,2 (antes 2,5); instancia de `L_Demo_Menu`: `VoDelay` 3 (antes 6).
- Cuadros (`BP_DemoCard_SC_C_0/1/2`) a X −3480 (1,20 m del PlayerStart; antes 1,50) para que el texto se lea más grande.
