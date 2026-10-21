# BP_DemoHudKit_SC (+ BP_DemoVoice_SC) — el HUD y la voz de la demo (guion v2, 2026-10-19)

## BP_DemoHudKit_SC — adapta el HUD de la Obra
- **refPath**: `/Game/SoulCharger/Demo/Blueprints/BP_DemoHudKit_SC` · componentes propios `Disc`, `Wave`, `Pop` (Plane + `M_ChargeHalo_SC`, el material de los "pop" de la carga) y `Timer` (TextRender + `M_TextUnlit`).
- **Colocado en**: los 3 niveles de la demo, junto a `BP_SoulHUD3D_SC` (HudScale 0,44, HudCurve 56, los valores de `Test_Hall`), `BP_FaceAnchor_SC` (el HUD queda a (+32,9; 0; −11,0) del ancla, pitch −29,6) y `BP_BioHub` (Muse: puerto 10000, `/muse/calm`, `/muse/heart_rate`, `/muse/sensor_active`; **`bFakeSignal` false**).
- **Fuente**: `VR_Test/Saved/ClaudeScripts/Demo2/kit_dsl.py`.
- Qué hace:
  - esconde el HUD al arrancar (`HUDHideNow` a los 0,15 s) y lo muestra con `HudShow` (`HUDAppear` + `Birth` del EEG 1 s después) o con `HudInstall` (lo mismo + una onda de luz que se abre frente a los ojos, 1,6 s, con háptico);
  - la hermana late con el BPM del BioHub (`Sister.BPM = HUD.BPM`, que el HUD toma de `HeartSmooth`);
  - esconde el anillo y el alma del nido derecho (escala 0,0001) y pone ahí, colgados del `Art` del HUD: **`Mode` 1** = disco que se enciende con `BreathRig.BreathOn` (Breath) · **`Mode` 2** = `Timer` "m:ss" con `TimeLeft` (Draw);
  - `HudPlop`: 0,9 s de temblor (el `Art` vibra, `Flash` del borde sube, háptico creciente) → `HUDVanish` + el EEG se apaga + "pop" de luz + `SBubbleHoverOut`.
- Perillas: `Mode` · `bHideOnStart` · `AutoShow` (s; −1 = lo pide el director) · `DiscColor` · `WaveColor` · `TimerColor` · `TimerCm` · `TimeLeft` · `PlopSound` · `ShowSound`.
- Menú: `Mode` 0 y `AutoShow` −1 (lo instala el menú; al elegir pone `Mode` = elección y `TimeLeft` 150). Breath: `Mode` 1, `AutoShow` 1. Draw: `Mode` 2, `AutoShow` 1.

## BP_DemoVoice_SC — las VO de la demo con subtítulos
- **refPath**: `/Game/SoulCharger/Demo/Blueprints/BP_DemoVoice_SC` · componentes `Voice` (AudioComponent) y `Sub` (WidgetComponent con `WBP_SubLine_SC`, `M_HudWidget_SC`, escala 0,016).
- **Fuente**: `Demo2/voice_dsl.py`. Datos de subtítulos en el CDO (`VoIds`, `VoC0`, `VoCN`, `CS`, `CE`, `CW0`, `CWN`, `Words`, `WS`) = `tools/demo/subs_demo_ue.json`.
- API: `Say(Clip)` toca el clip y arranca sus tarjetas; `bSpeaking` (getter `GetSpeaking`) dura el clip + 0,2 s. Se cuelga del HUD (`AttachActorToActor` Snap) con `Offset` (0, 0, −3,5): los subtítulos van bajo el HUD, palabra por palabra (`Dim` 0,32, `Rise` 9, `WordFade` 0,16, `LineFade` 0,22).
- 🔴 El `BP_Subtitles_SC` de la Obra tiene TODAS sus funciones vacías: no se usa. Los widgets `WBP_SubLine_SC`/`WBP_SubWord_SC` sí funcionan.
- Voces: `tools/demo/vo_demo.json` → `python tools/demo/gen_vo_demo.py [ids]` (Soul Charger Woman, S2, 0,925, −21 LUFS, 48 kHz, tiempos por carácter de `/with-timestamps`: la clave no tiene permiso de alineación forzada). Después de regenerar, copiar los arreglos nuevos de `subs_demo_ue.json` al CDO de `BP_DemoVoice_SC`.

## 2026-10-19 (noche): costo en el visor
- `Wave` y `Pop` (planos de 100×100 cm aditivos a ~35 cm de los ojos) quedaban **visibles toda la demo** con `Amount` 0: dos capas a pantalla casi completa por cuadro. Ahora `KitSetup` los esconde y `KitWave`/`KitPlop` los muestran solo mientras animan. `Disc` visible solo en `Mode` 1, en `KitSlot` (cada cuadro: en el menú el `Mode` pasa de 0 a 1 al elegir ENTERING, después de `KitSetup`).
- El reloj (`Timer`, TextRender) llamaba `SetText` cada cuadro (recrea el proxy de render): ahora solo cuando cambia el segundo (`LastSec`, CDO −1).
- **`BP_DemoVoice_SC`**: el widget de subtítulos se redibuja a mano (`SetManuallyRedraw` al colgarse del HUD + `RequestRenderUpdate` mientras hay voz y 0,4 s después, `RedrawT`). Ojo: los subtítulos quedan **encima** de la píldora (Offset z −3,5), no debajo.
- `VO_DD2` nuevo: "Well done. This is what you created, and what your body was saying while you drew." (el guion pide felicitar).

## 2026-10-20 — el HUD no se reinstala en la experiencia
- Perilla nueva **`bShowNow`** (true en `L_Demo_Breath` y `L_Demo_Draw`): apenas el HUD está colgado de la cara (`KitSetup`), **`HudShowNow`**: `HUDHideNow` + `AppearT` 1 + `ApplyT(1)` + `Birth` con `BirthT` 1 → el HUD aparece ya puesto, sin animación, sin sonido, con el EEG nacido. El que vio el HUD instalarse en el menú lo encuentra igual al entrar (queda el ~1 s de carga en negro entre niveles).
- `VO_D03` agregada al CDO de `BP_DemoVoice_SC` (9 voces).
- (tarde) **`Mode` 3 = Heart**: `KitFindRig` busca `BP_HeartManager_SC` (var `Heart`); `KitDisc` lleva `DiscK` a `max(bHeartZone ? 0,55 : 0, BeatEnv)` (se enciende en el umbral, destella en cada pulso). El disco se ve en `Mode` 1 y 3. En `L_Demo_Heart`: `DiscColor` (1; 0,4; 0,35).

## 2026-10-20 (noche, 2.ª tanda) — "TEXT" en Heart
- `KitSlot`: el bloque del modo 3 (punto rojo) terminaba en `IsValid(Heart)` y el writer colgó de su `else` la línea `SetVisibility(Timer)` y el bloque del modo 2 (gotcha 590). En Heart el reloj nunca se escondía y mostraba "Text" sobre el disco. Ahora el reloj va ANTES y el bloque del modo 3 es lo último de la función.
- `Timer`: `Text` vacío en el CDO y `TextMaterial` = `M_DemoTextAA_SC` (alpha to coverage: borde suave en el Quest).
