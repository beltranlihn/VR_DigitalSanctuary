# 🗺️ Mapa del proyecto (al 2026-11-14)

Dónde está cada cosa del proyecto Unreal `VR_Test`, qué hace y cómo se prueba. Al proponer una idea, se empieza por acá.
- El detalle de cada Blueprint está en `.claude/skills/unreal-vr/blueprints/_INDEX.md` y en su tracker.
- Los materiales, los Niagara y los BPs uno por uno están en [`CATALOGO.md`](CATALOGO.md).
- Cómo se llegó a este orden: [`AUDITORIA-ESTRUCTURA-2026-11-14.md`](AUDITORIA-ESTRUCTURA-2026-11-14.md).

## 1. Tres proyectos en un mismo Content

| Proyecto | Qué es | Niveles | Estado | Entregado |
|---|---|---|---|---|
| **Soul Charger · la Obra** | VR de sanación sentada, ~15 min: Hall + 5 etapas + final. Quest 3 | `SoulCharger/Obra/L_SoulCharger_Obra` (director `BP_Obra_SC`) + sus celdas `Test_Hall`, `Test_Breath`, `Test_Heart`, `Test_Mind`, `Test_Sequencer`, `Test_Draw` | 🟢 entera; Loving y Attracting en rediseño | — |
| **Digital Sanctuary · la demo** | demo corta para ferias: menú bilingüe + Breath, Heart y Draw, con el sensor Muse y el robot de Windows | `SoulCharger/Demo/Maps/L_Demo_Menu`, `L_Demo_Breath`, `L_Demo_Heart`, `L_Demo_Draw` | 🟢 | `Projects/Packagings/Digital Sanctuary V1.0` (BCN Design Week, 10-2026) |
| **Inner Canvas** | dibujo de pie (3 × 3 m, 5 min) para varios visores + un PC que muestra los dibujos en vivo | `InnerCanvas/Maps/L_InnerCanvas` (visor), `L_InnerCanvas_Wall` (PC) | 🟢 | `Projects/Packagings/Inner Canvas v1.0` (evento corporativo, 2026-11-13) |

🔴 **Dependen entre sí:**
- Inner Canvas usa 116 assets de `SoulCharger/Demo/` (HUD, voz, flujo).
- La demo usa 49 de `Mechanics/`.
- Los tres usan los cuatro plugins `SC_*`.

Antes de mover o borrar algo de `Demo/` o de un plugin, hay que mirar quién lo usa:
`python tools/unreal/deps.py --plugins` + `docs/auditoria-2026-11-14/alcance.py`, o `AssetTools.get_referencers`.

## 2. Todos los niveles y cómo se prueban

| Nivel | Para qué | Cómo probarlo |
|---|---|---|
| `Obra/L_SoulCharger_Obra` | la Obra entera; el editor arranca acá | `python tools/unreal/smoke_obra.py` (≈9 min, sin visor). Tiene que dar OK antes de un commit grande o un APK |
| `Hall/Maps/Test_Hall` y `Mechanics/<X>/Maps/Test_<X>` | cada etapa sola, con su ensayo (`BP_StageRunner_SC` / `BP_HallRunner_SC`). Lo que se ajusta acá es lo que se ve en la Obra | Play en el nivel |
| `Demo/Maps/L_Demo_*` | la demo | `python tools/unreal/probar_nivel.py ... --extra="-MirrorRole=-1"`; con valores de público recorre todo sola |
| `InnerCanvas/Maps/L_InnerCanvas` / `_Wall` | Inner Canvas visor / PC | `-game`; el PC con `tools/innercanvas/simular_visores.py` |
| `Mechanics/Mind/Maps/Test_Thoughts`, `Test_Feed`, `Test_Focus` | ⏸️ Loving sin EEG: tres variantes en pausa desde 11-04 (falta elegir camino) | Play / Simulate |
| `Mechanics/Harp/Maps/Test_AttractingHang` + `Test_Harp` | 🟡 Attracting reconstruido con un instrumento (hang, llamada y respuesta) + el arpa | Play (notas automáticas) |
| `Shared/QuestController/Test_QuestCtrl` | 🔴 **el nivel neutro**: abrir este para cambiar variables o funciones de un BP (regla de oro 3) | — |
| `Shared/Appear/Test_Appear`, `Shared/Results/Maps/Test_Results`, `Shared/Ghost/Maps/L_GhostRec_SC`, `Mechanics/Draw/Maps/Test_DrawPalette` | probar una pieza sola: aparición, cuadro de resultados, grabar fantasmas, paleta de dibujo | Play |

## 3. Content, carpeta por carpeta

Convención (orden del 2026-10-02): dentro de cada mecánica, del Hall, de la Obra, de la Demo y de Inner Canvas, los assets van
**por tipo**: `Blueprints/ Materials/ Meshes/ Textures/ Audio/ Input/ VFX/ UI/ Data/ Maps/`. Sufijos: `_SC` = Soul Charger,
`_IC` = Inner Canvas, `_NC` = el dibujo heredado de Neural Canvas.

| Carpeta | Qué hay |
|---|---|
| `SoulCharger/Core/` | la base: `BP_VRPawn_SC` (pawn liviano), `BP_Alma_SC` (Alma, toda su vida en el material), `BP_ProtoSoul_SC` (el alma del usuario), `BP_BioHub` + `BP_OSCReceiver` (señales: Muse/OSC puerto 10000), luz, audio, `Flow/BP_SoulState` (la GameInstance), Debug |
| `SoulCharger/Obra/` | el director `BP_Obra_SC`, `DA_Partitura_Obra` (todos los tiempos, ver `docs/PARTITURA.md`), ensayos, títulos, créditos, voces `VO_*` |
| `SoulCharger/Hall/` | inicio, hall y regreso: director, niebla, luz, timbre, orbe del sensor |
| `SoulCharger/Mechanics/Breath/` | Entering (la etapa): orquestador con voces y el valle. El sistema de respiración está en el plugin `SC_Breath` |
| `SoulCharger/Mechanics/Heart/` | Recognizing: latido, membrana, polvo |
| `SoulCharger/Mechanics/Mind/` | Loving: la célula `BP_LovingCell_SC`, el fluido `BP_FluidMedium_SC` (también lo usa el menú de la demo) y los 3 experimentos en pausa |
| `SoulCharger/Mechanics/Sequencer/` | solo `Test_Sequencer`: el secuenciador está en el plugin `SC_Sequencer` |
| `SoulCharger/Mechanics/Draw/` | Surrounding: el océano `BP_DrawSea_SC` y `Test_Draw`. El dibujo está en el plugin `SC_Draw` |
| `SoulCharger/Mechanics/Harp/` | el arpa/hang `BP_Harp_SC` (sinte propio con MetaSounds) y el Attracting nuevo (`BP_AttractCall_SC`, `BP_AttractStreams_SC` apagado) |
| `SoulCharger/Shared/` | piezas de varias etapas: HUD, resultados y SHARE, fantasmas de instrucciones, `BP_UserTool_SC` (el objeto de la mano), subtítulos (widgets), anillo de carga, mandos |
| `SoulCharger/Demo/` | la demo: menú, flujo, HUD, voz bilingüe, resultados, cartas, ambiente, enlace al robot (`BP_MirrorLink_SC`), mezcla de audio de Beltrán (`Audio/Mix`) |
| `InnerCanvas/` | Inner Canvas: 12 BPs `*_IC`, audio (voces `IC_*` ES/EN y sonidos `SND_IC_*` de Beltrán), mano de PolyOne (CC-BY: el crédito va en el cartel físico), UI (fuentes por tamaño `F_ICW*`), mapas |
| `XRFramework/`, `XRMannequins/` | plantilla VR de Epic: GameMode, input (IMC/IA), manos. 🔴 No se tocan |
| `Collections/`, `Developers/` | vacías, del editor |

## 4. Plugins (`VR_Test/Plugins/`)

| Plugin | Qué | Notas |
|---|---|---|
| `SC_Base` | el mando (`BP_QuestCtrl_SC`), la aparición "luz primero" (`BPC_AppearLuz_SC`), el ancla, materiales `M_SC*`, láser, sonidos de interfaz | lo comparten todas las mecánicas portables |
| `SC_Breath` | respiración: sensor, metaball, guía (`MPC_Breath`) | portable |
| `SC_Draw` | dibujo estilo Tilt Brush: director, herramienta, trazo, paleta | portable; Inner Canvas lo modificó (11-12/13) |
| `SC_Sequencer` | el secuenciador de Attracting + `BP_SeqRig_SC` (rig de mandos con láser, también lo usan la demo e Inner Canvas) | portable |
| `Marketplace/PICOOpenXR` 1.6.1 | plugin oficial PICO (Fab): pide 72 Hz en PICO, entre otras cosas | 🔴 reescribe `DefaultEngine.ini` en cada arranque del editor; ver `docs/PICO-EMPAQUETADO.md` |

Regla: nada de un plugin `SC_*` apunta a `/Game/SoulCharger` → `python tools/unreal/verificar_plugins.py`. Cada uno tiene su
`LEEME.md`. Mecánicas que faltan pasar a plugin: Heart y Mind (`docs/MECANICAS-PORTABLES.md` §0).

## 5. Empaquetar e instalar

| Qué | Empaquetar | Instalar |
|---|---|---|
| Obra (Quest) | `python tools/unreal/empaquetar_obra.py` | `powershell -File tools/unreal/instalar_quest.ps1` |
| Demo bilingüe (Quest) | `empaquetar_obra.py --variante demobi --nombre Demo_BDW_Bilingual` | `instalar_quest.ps1 -Variante demobi` |
| Robot de la demo (Windows) | `python tools/unreal/empaquetar_robot.py` | — |
| Inner Canvas PICO | `empaquetar_obra.py --variante innercanvas` | `powershell -File tools/innercanvas/instalar_pico_ic.ps1 -Todos -Wall <IP del PC>` |
| Inner Canvas Quest | `empaquetar_obra.py --variante innercanvasquest` | `instalar_pico_ic.ps1 -Variante quest -Serial … -Slot N -Wall <IP>` |
| Inner Canvas pantalla (Windows) | `python tools/innercanvas/empaquetar_pantalla.py` | abrir con `InnerCanvas_Pantalla.bat` (corrige la escala de Windows) |

- Cada empaquetado deja su copia en `Recursos/…/APK` o `Recursos/Inner Canvas/Pantalla` (local, fuera de git).
- **Una versión entregada va a `Projects/Packagings/<Nombre vX.Y>/`**, con su LEEME. Nunca al escritorio.
- Siempre Development: Shipping recorta los logs y cambia las rutas de guardado.

## 6. Herramientas (`tools/`)

| Carpeta | Para qué |
|---|---|
| `tools/unreal/` | prueba de humo, probar un nivel, empaquetar, instalar, dependencias (`deps.py`), archivar sin borrar (`archive_unused.py`, `limpiar_con_editor_cerrado.py`), plugins, partitura, `respaldar_fuentes_bp.py` |
| `tools/bp_fuentes/` | copia de las fuentes `.py`/`.dsl` de los BPs escritos por script. El original vive en `VR_Test/Saved/ClaudeScripts/<tema>/`, porque el editor solo lee desde ahí. Se actualiza en cada `/commit` |
| `tools/innercanvas/` | Inner Canvas: voces, textos, títulos, atlas del teclado, mano, pantalla, instalador PICO/Quest, simulador de visores |
| `tools/demo/` | la demo: voces bilingües, subtítulos, robot, Muse falso, perillas de público |
| `tools/editor/`, `tools/score/` | Veation VR Studio, el editor web de los tiempos de la Obra (`web/editor-obra`) y sus pruebas |
| `tools/pieeg/` | PiEEG XR: sonda BLE y análisis de la señal |

## 7. Dónde está el conocimiento

| Qué | Dónde |
|---|---|
| Lo técnico de Unreal (MCP, DSL, Quest, materiales, luz) | skill `unreal-vr`: `SKILL.md` + `references/` |
| Cada Blueprint | `blueprints/_INDEX.md` + el tracker `<BP>.md` (Inner Canvas: `InnerCanvas.md`) |
| Lo que ya existe y se reusa (input, hápticos, Niagara, materiales) | `references/assets-existentes.md` |
| Las trampas pagadas (643) | `references/gotchas.md`; las cortas en `docs/REGLAS-DE-ORO.md` |
| La obra (guion, partitura, perillas, dirección) | `docs/OBRA-SOUL-CHARGER.md`, `docs/GUION-V5-2026-09-29.md`, `docs/PARTITURA.md`, `docs/PERILLAS.md`, `docs/GUIA-DE-DIRECCION.md` |
| La demo / Inner Canvas | `docs/demo/DEMO-BDW.md` / `docs/innercanvas/PLAN-INNER-CANVAS.md` |
| PICO | `docs/PICO-EMPAQUETADO.md` |
| Lo archivado | `_Deprecated/` (fuera del proyecto y de git; manifiestos adentro) y los tags `respaldo-pre-reorden-2026-10-02` y `respaldo-pre-orden-2026-11-14` |
