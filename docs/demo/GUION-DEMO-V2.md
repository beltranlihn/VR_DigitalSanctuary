# Demo BDW — guion v2 (Beltrán, 2026-10-19)

Guion original: Google Doc de Beltrán (19-10). Decisiones del 19-10: pulso y EEG vienen del **Muse** (por el BioHub, OSC); el gráfico central del HUD es **siempre la actividad neuronal**; voz **Soul Charger Woman** (receta S2, 0,925); modelos nuevos solo para el **panel de instrucciones** (16:9, curvo hacia el usuario como el HUD) y el **cuadro de resultados**; el sensor de Breath y el mando/paleta de Draw son los que ya existen; las imágenes de las instrucciones son **cuadradas y se cambian fácil**; todo para el miércoles 21.

## Recorrido
### Menú (`L_Demo_Menu`)
1. Ambient 1 · título + START · subtítulo "Point the button and press trigger" · hover = un poco más grande y con luz · se ven los mandos con el láser, no las manos.
2. START → se van título y START animados → BACK en el mismo lugar + los dos cuadros · subtítulo "Point the experience of your choice and press trigger".
3. Elegir → se van animados · Ambient 2 · los mandos desaparecen y aparecen las manos suavemente.
4. Avanzamos por el espacio azul con partículas (como el inicio de la Obra) · VO de bienvenida (`VO_D01b` Breath / `VO_D01d` Draw) con subtítulos bajo el HUD.
5. Termina la VO → el HUD aparece animado + un efecto de luz frente a los ojos → VO `VO_D02` ("You're ready").
6. Negro → nivel de la experiencia.

### Breath (`L_Demo_Breath`)
1. Ambient de la etapa · niebla y título animado de la etapa · el marco de instrucciones aparece animado.
2. P1 "Pick up the sensor…": el sensor flota al frente; al tocarlo se pega a esa mano (mano hábil = la que lo toma) y las manos desaparecen → sigue sola.
3. P2 sensor en la panza: entra al umbral → sigue sola.
4. P3 círculo que sigue la respiración: un par de respiraciones → sigue sola.
5. P4 tipo de respiración + botón START (láser desde el sensor, sin mando de Quest).
6. Se va el panel → metaball + `VO_DB1` → unos segundos de exploración → pacer (cuenta "three, two, one") + `VO_DB2` → la sesión.
7. Fin: se va el pacer, se va el metaball, `VO_DB3`, el HUD vibra y se va con un "plop", aparece el cuadro de resultados: actividad (EEG), pulso, círculos por ciclo, índice de calma grande a la derecha.
8. 30-40 s → negro → menú.

### Draw (`L_Demo_Draw`)
1. P1 "Pick up the brush…": el mando flota al frente; al tocarlo queda en esa mano y aparece la paleta en la otra.
2. P2 paleta + invitación a dibujar: el usuario hace un trazo; al llegar a cierta distancia el trazo se va animado → `VO_DD1` → la mecánica con **timer en el HUD**.
3. Termina por tinta o por tiempo → el dibujo va al frente girando → dos vueltas → se corre a la derecha → `VO_DD2` → HUD "plop" → cuadro de resultados: actividad neuronal, pulso, índice de calma.
4. 30-40 s → negro → menú.

## HUD
Píldora v4 de la Obra (`BP_SoulHUD3D_SC`): izquierda la hermana azul latiendo con el pulso del Muse · centro el EEG · derecha: Breath = disco que se enciende en el umbral, Draw = timer.

## Piezas (Unreal, `/Game/SoulCharger/Demo/`)
| Pieza | Qué |
|---|---|
| `BP_DemoVoice_SC` | toca las VO de la demo y las subtitula palabra por palabra bajo el HUD (widget `WBP_SubLine_SC`; datos de `tools/demo/subs_demo_ue.json`) |
| `BP_DemoHudKit_SC` | adapta el HUD de la Obra a la demo: hermana con el BPM, slot derecho (disco / timer), entrada con efecto de luz, salida con temblor y "plop" |
| `BP_DemoMenu_SC` | + subtítulos de ayuda, hover con escala, mandos/manos, viaje, VO, HUD, negro |
| `BP_DemoFlow_SC` | director de cada experiencia (reemplaza a `BP_StageRunner_SC` + `BP_DemoInstr_SC` en los niveles de la demo): velo y título, páginas que avanzan solas, contrato de la etapa, VO, timer, resultados, negro, menú |
| `BP_DemoResults_SC` | el cuadro de resultados (modelo nuevo + contenido dibujado como el de la Obra) |

## Voces
`tools/demo/vo_demo.json` → `python tools/demo/gen_vo_demo.py` → `Demo/Audio/VO/VO_*.wav` (+ `tools/demo/subs_demo*.json`).

## Estado (2026-10-19, 17:00)
- 🟢 Todo armado y probado en `-game` sin visor (0 errores de Blueprint): menú → viaje → bienvenida → HUD → negro → Breath / Draw → resultados → negro → menú. Capturas en `VR_Test/Saved/ClaudeScripts/Demo2/shots_*.png` y `res_crop2.png`.
- 🟢 Robot: sigue al director nuevo (probado con el Quest falso `flujo_breath` / `flujo_draw`).
- 🟢 APK `Recursos/Soul Charger - Escritorio 2026-10/APK/Soul Charger Demo APK 2026-10-19 1651`.
- ⬜ Visor: alturas, lectura del panel y de los resultados, tomar el sensor/mando, umbral, trazo de práctica, Muse real.
- ⬜ Imágenes reales de las instrucciones (hoy van las de muestra de Blender).
