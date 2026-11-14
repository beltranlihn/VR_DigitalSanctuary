# Auditoría de estructura · 2026-11-14

> ✅ **Cerrado el 2026-11-14** — lo hecho está en §0. Las secciones §1-§3 son la foto de la revisión, de antes de ordenar.

Revisión completa del proyecto después de cinco semanas de trabajo intenso: la demo de la BCN Design Week, experimentos de
Loving y Attracting, Inner Canvas para 8 PICO y el Quest 2. Pedido de Beltrán: entender el total primero, dejar la documentación
al día y recién después ordenar, limpiar huérfanos y archivar lo obsoleto, sin romper nada.

Método (reproducible):
- `python tools/unreal/deps.py --plugins` arma el grafo de dependencias de los 1270 paquetes de `Content/` y de los plugins,
  leyendo las rutas de cada `.uasset`, sin abrir Unreal.
- Con ese grafo se calcula qué alcanza cada grupo de niveles.
- Los candidatos a huérfano se buscan además por nombre corto (cargas armadas por texto) y se confirman con
  `AssetTools.get_referencers` en el editor.

## 0. Qué se hizo el 2026-11-14 (cerrado)

**Respaldo.** Commit `f84d512` + tag `respaldo-pre-orden-2026-11-14`, con la prueba de humo de la Obra en OK antes y después
(`smoke_20261114-174803` → `smoke_20261114-183722`, 0 errores de Blueprint).

**Unreal**
- **Archivados 65 assets huérfanos** (+11 fuentes `.wav`/`.png`) → `_Deprecated/Content-2026-11-14/`, con manifiesto. Volver:
  `python tools/unreal/archive_unused.py --restore Content-2026-11-14`.
- **51 nodos huérfanos borrados** en 9 BPs: `BP_ICTutor_IC`, `BP_ICWallHUD_IC`, `BP_Harp_SC`, `BP_StageRunner_SC`, `BPC_TBTool_NC`,
  `BP_TBDirector_NC`, `BP_TBPalette`, `BP_SoundOrb_SC`. Todos con el DSL idéntico antes y después, compilados y guardados.
  `BP_ProtoSoul_SC` no se tocó (H11).
- **Verificado sin visor:**
  - la Obra (smoke OK);
  - el menú de la demo e Inner Canvas visor (`probar_nivel`, 0 errores);
  - la pantalla del PC (los mismos 32 avisos de `BP_ICSpace_IC.SpaceBoot` que el build del evento: preexistentes, ver H12);
  - `verificar_plugins.py` OK.

**Documentación**
- `docs/MAPA-DEL-PROYECTO.md` y `docs/CATALOGO.md`, nuevos (generado con `tools/unreal/gen_catalogo.py`).
- `_INDEX.md` de BPs cuadrado con el disco; la historia pasó a `_HISTORIA.md`.
- `CLAUDE.md` (§3.b, §6, §8), `MECANICAS-PORTABLES.md` §0.a, `PICO-EMPAQUETADO.md`, `README.md` de la raíz, `docs/README.md`,
  `Recursos/LEEME.md`, `scripts/LEEME.md` de la skill y gotchas 636-643.

**Carpeta del proyecto**
- 48 documentos viejos → `docs/historia/` y `docs/investigacion/`; los 4 de diseño de julio de la raíz →
  `docs/historia/raiz-2026-07/`. Enlaces reescritos y verificados: queda 1 roto, y ya estaba así antes.
- `Recursos` reagrupado: `Marca e interfaz/`, `3D/Blender`, `Audio/…`.
- `perf/` → `_Deprecated/perf-2026-09`.
- **Fuentes DSL** → `tools/bp_fuentes/` (H10).

**Borrado (con permiso de Beltrán)**
- caché de Fab del launcher: 5,3 GB;
- 39 builds intermedios: 32,2 GB; queda el último de cada app;
- `Packaging/` (duplicado). La demo solo en inglés se movió a `Packagings/Digital Sanctuary V1.0/Solo ingles (2026-10-23)`;
- `Recursos/DrawingToolkit`, `GDXR`, `Test_3DDraw` salieron de git (siguen en el tag).

**H12 · ✅ Arreglado el mismo 11-14:** en `L_InnerCanvas_Wall`, las 8 copias de `BP_ICSpace_IC` daban 32 avisos en `SpaceBoot`.
- La guarda era un `select`, que es puro y evalúa las dos ramas, así que el `Get(0)` del arreglo vacío corría igual (gotcha 644).
- Ahora la elección es un `if` de ejecución.
- La pantalla da 0 avisos y el visor 0 errores, con los mismos valores que antes.

## 1. Qué hay hoy

### Niveles (23)
| Grupo | Niveles | Estado | Alcanza |
|---|---|---|---|
| **Obra** | `Obra/L_SoulCharger_Obra` + sus celdas `Test_Hall`, `Test_Breath`, `Test_Heart`, `Test_Mind`, `Test_Sequencer`, `Test_Draw` | 🟢 la obra entera; smoke `tools/unreal/smoke_obra.py` | 703 paquetes |
| **Demo BDW** (Digital Sanctuary V1.0) | `Demo/Maps/L_Demo_Menu`, `L_Demo_Breath`, `L_Demo_Draw`, `L_Demo_Heart` | 🟢 entregada (BDW, 10-24); bilingüe | 708 |
| **Inner Canvas** | `InnerCanvas/Maps/L_InnerCanvas` (visor), `L_InnerCanvas_Wall` (pantalla del PC) | 🟢 evento 11-13; variante Quest 2 (11-13) | 687 |
| Experimentos Loving (sin EEG) | `Mechanics/Mind/Maps/Test_Thoughts`, `Test_Feed`, `Test_Focus` | ⏸️ en pausa desde 11-04 (Mind sin sensor: 3 caminos sin elegir) | 18 / 12 / 2 assets propios |
| Experimento Attracting | `Mechanics/Harp/Maps/Test_AttractingHang` (+ `Test_Harp`, el arpa) | 🟡 en curso (11-04); falta visor | 8 propios + el hang |
| Niveles de prueba de piezas | `Shared/QuestController/Test_QuestCtrl` (el nivel neutro para cambiar estructura de BPs), `Shared/Appear/Test_Appear`, `Shared/Results/Maps/Test_Results`, `Shared/Ghost/Maps/L_GhostRec_SC`, `Mechanics/Draw/Maps/Test_DrawPalette` | 🟢 útiles | 1-2 propios cada uno |

### Carpetas
| Carpeta | Archivos | MB | Qué es |
|---|---|---|---|
| `Content/SoulCharger/Core` | 84 | 147 | base de la obra: pawn, Alma, alma del usuario, señales, luz, audio |
| `Content/SoulCharger/Demo` | 342 | 494 | la demo BDW. **Inner Canvas usa 116 de sus assets** (HUD, voz, flujo): no se puede archivar |
| `Content/SoulCharger/Hall` | 88 | 24 | inicio, hall, regreso |
| `Content/SoulCharger/Mechanics` | 138 | 63 | Breath, Heart, Mind (+ Thoughts/Feed/Focus), Sequencer, Draw, Harp (arpa + hang de Attracting) |
| `Content/SoulCharger/Obra` | 178 | 59 | director, partitura, títulos, voces |
| `Content/SoulCharger/Shared` | 99 | 19 | HUD, resultados, fantasma, mandos, aparición, subtítulos |
| `Content/InnerCanvas` | 207 | 190 | la experiencia de dibujo de pie (142 son audio) |
| `Content/XRFramework`, `XRMannequins` | 83 | 17 | plantilla VR de Epic (GameMode, input, manos) |
| `Content/Fab` | 2 | 0,3 | una mano importada el 11-13 que no usa nadie |
| `Plugins/SC_Base`, `SC_Draw`, `SC_Breath`, `SC_Sequencer` | 238 | 67 | las mecánicas portables |
| `Plugins/Marketplace/PICOOpenXR` | 1336 | 1013 | plugin PICO (19 MB de fuente + 994 MB de binarios ignorados por git) |

Por tipo: ~114 Blueprints, 124 materiales maestros, ~190 instancias de material, 10 Niagara, 100 texturas, 88 mallas,
~250 audios.

## 2. Hallazgos

**H1 · Nada commiteado desde el 21-10** (`98e99ba`): 1465 cambios en el árbol, entre ellos todo Inner Canvas, los experimentos y
el plugin PICO. Y hay **~3 GB sin ignorar**, que un `git add` subiría:
- `Packaging/` en la raíz: dos builds de Windows de la BDW, 1 GB cada uno.
- `Recursos/Inner Canvas`: APK, OBB y builds de la pantalla.

**H2 · 68 assets huérfanos confirmados** (ni el grafo ni el registro del editor les encuentran quien los use):
| Dónde | Cuántos | Qué son |
|---|---|---|
| `Demo/` | 31 | cartas e instrucciones viejas de la demo (`SM_DemoCard2_*`, `SM_InstrCard_*`, `T_Instr_*_P2/P3`), `BP_DemoInstr_SC` (reemplazado por `BP_DemoFlow_SC`), `DA_Partitura_Demo` |
| `InnerCanvas/` | 17 | 13 fuentes `F_ICW*` de tamaños descartados al calibrar el TV 4K, 2 títulos `ENDEN/ENDES` del final viejo |
| `Obra/` | 11 | 4 sonidos placeholder, 5 voces `VO_*c/d` (tomas alternativas), `BP_AuthorMark_SC`, `T_Title_DISCLAIMER` |
| `Shared/` | 4 | `BP_Subtitles_SC` (su tracker: "todas sus funciones vacías, no se usa"), 3 `DA_Ghost_*` sin etapa |
| `SC_Breath` | 3 | `SND_PacerInhale/Hold/Exhale` |
| `Fab/Hand` | 2 | la mano de Fab del 11-13 |

Lista exacta: `docs/auditoria-2026-11-14/huerfanos.json`.

**H3 · Dependencias cruzadas que no estaban escritas:**
- Inner Canvas depende de `SoulCharger/Demo` (116 assets) y de `Mechanics` (30).
- La demo depende de `Mechanics` (49).
- Los plugins `SC_Base`, `SC_Draw` y `SC_Sequencer` se tocaron para Inner Canvas el 11-12 y 11-13 (`BP_QuestCtrl_SC`,
  `BP_SeqRig_SC`, `BP_TBDirector_NC`, `BP_DrawPalette_SC`, `BPC_TBTool_NC`, `BP_TBPalette`). **La Obra no se probó desde
  entonces**: hay que pasarle la prueba de humo.

**H4 · Documentación atrasada:**
- `blueprints/_INDEX.md` quedó en el 10-02: le faltan Inner Canvas (12 BPs), los experimentos y la demo. Arrastra unas 250 líneas
  de historia de estructuras que ya no existen (MapsV2, V3, Stages/).
- Sin tracker propio: `BP_DemoVoice_SC`, `BP_DemoShots_SC`, `BP_GhostRecorder_SC`, `BP_SoundOrb_SC`, `BP_TBDirector_NC`,
  `BPC_TBTool_NC`, `BP_TBPalette` y los 12 de Inner Canvas (documentados juntos en `InnerCanvas.md`).
- No hay un mapa de niveles ni un catálogo de qué hace cada material, cada Niagara y cada BP.
- `assets-existentes.md` está al 11-04 y `MECANICAS-PORTABLES.md` al 10-02.

**H5 · Plugin PICO OpenXR:**
- Reescribe el `DefaultEngine.ini` compartido en cada arranque del editor.
- Su `DisableRHIThread=True` apaga el hilo RHI también en los APK de Quest. Solo la variante `innercanvasquest` lo corrige; la
  Obra y la demo salen sin hilo RHI.
- ✅ Corregido el 11-14: `empaquetar_obra.py` pone `DisableRHIThread=False` en toda variante que no sea PICO, solo mientras cocina.
- Sigue pendiente aislar el plugin entero (apagado por defecto, encendido solo en la variante pico). Hace falta un PICO a mano para
  verificarlo.

**H6 · Caché de descargas de Epic/Fab** (fuera del proyecto, en `C:\ProgramData\Epic\EpicGamesLauncher\VaultCache`): 5,4 GB.
- Lyra 5.8: 5 GB, de julio.
- Tres proyectos de dibujo usados como referencia en julio: `Draw`, `DrawingToolkit` y `GDXR_UVRT_Lite` (0,44 GB).

**H7 · Nombres sin prefijo** (`Voice*`, `Ambient*`, `Bell`, `HeartBeat`, `M1S*` del secuenciador, `IC_*`):
- No se renombran. Varios se cargan por nombre o por índice, y renombrar rompe en silencio.
- Se documentan en el catálogo.

**H8 · `skills/unreal-vr/scripts/` tiene ~140 archivos:** generadores de una sola vez (septiembre) mezclados con los reusables
(`safe_script.py`, `clean_orphans.py`, `auto_layout.py`).

**H9 · Raíz del repo:**
- `Packaging/` está duplicado con `Projects/Packagings`.
- `perf/`: 201 MB de mediciones de septiembre, sin versionar.
- Los documentos de diseño anteriores al pivote a Quest (`Soul-Charger-*.md`) siguen en la raíz.

**H10 · Las fuentes de los BPs escritos por script no tenían respaldo.**
- `ic_flow2_dsl.py`, `ic_tutor2_dsl.py`, los de la demo (`Demo2/`), el Hall, el arpa, Focus, Thoughts…: 426 archivos `.py`/`.dsl`
  en `VR_Test/Saved/ClaudeScripts/`.
- Tienen que vivir ahí (el editor solo lee de `/Game`, del Content de un plugin o de `Saved/`), y `Saved/` está ignorado por git.
- ✅ Hecho el 11-14: `tools/unreal/respaldar_fuentes_bp.py` las espeja en `tools/bp_fuentes/`. La mini-skill `/commit` lo corre
  antes de cada commit.
- Los 2,3 GB restantes de `ClaudeScripts` son volcados y capturas regenerables.

**H11 · Revisado el 11-14 (registro del editor): ninguno sobra, no se borra nada.**
- `BP_ChargeTest_SC` (Shared/HUD) lo usa el ensayo del Hall (`BP_HallRunner_SC`, `Test_Hall`). `BP_ChargeFx_SC` lo usa la Obra
  (`BP_Obra_SC`). Son dos clientes distintos y validados: unificarlos obliga a re-probar el Hall en visor.
- `NS_FocusMotes_SC` es una copia de `NS_OrbHalo_SC` (plugin `SC_Sequencer`). La usan solo Feed y Focus, que están en pausa. Es una
  copia a propósito para no tocar el plugin; se decide cuando se elija el camino de Mind.
- `M_SpaceDust_SC`/`NS_SpaceDust_SC` y `M_HallDust_SC`/`NS_HallDust_SC` son dos polvos distintos colocados en `Test_Hall`. El
  primero también está en el menú de la demo: no son duplicados.
- `M_ProtoSoul` (Core) es el material del alma: lo usan el alma, los créditos, la carga y tres experimentos. `M_AnchorGhost_SC`
  (SC_Base) solo lo usa `MI_Ghost`. Son dos materiales distintos con nombre parecido.
- `M_ControllerSecond_SC/002` son los materiales de las mallas del mando (`ControllerL/R`) y del sensor (`BreathL/R`). Están en uso; el
  nombre es solo heredado.
- `M_SoulRibbon_SC` lo usa `BP_ProtoSoul_SC`: los anillos están apagados y se conservan por decisión de Beltrán.

Lista original del catálogo:
- **Casi gemelos:**
  - `BP_ChargeTest_SC` / `BP_ChargeFx_SC`: la Obra usa el segundo, pero el primero también llega a la Obra.
  - `NS_FocusMotes_SC` es `NS_OrbHalo_SC` sin cambios.
  - `M_SpaceDust_SC` / `NS_SpaceDust_SC` son copias del polvo del Hall.
- **Nombres confusos:** `M_ProtoSoul` (Core) y `M_AnchorGhost_SC` (SC_Base, el viejo `M_ProtoSoul` de Core/Amoeba).
- **Dudas de uso:**
  - `M_ControllerSecond_SC/002` (materiales viejos del mando, en SC_Base): los alcanzan todos los proyectos.
  - `M_SoulRibbon_SC` sigue referenciado aunque los anillos del alma están apagados.
- **Código apagado a propósito:** `BP_ProtoSoul_SC` tiene 61 nodos desenchufados (anillos y tarjeta del alma, apagados el 09-30 "sin
  borrar código", según su tracker). La limpieza de huérfanos los dejó.

## 3. Plan (de menor a mayor riesgo; cada fase se verifica antes de la siguiente)

| Fase | Qué | Riesgo | Vuelta atrás |
|---|---|---|---|
| **F0 · Respaldo** | prueba de humo de la Obra (línea de base) · `.gitignore` para lo pesado · commit + tag `respaldo-pre-orden-2026-11-14` | nulo | el tag |
| **F1 · Documentación** | `_INDEX.md` nuevo (lo vigente) + `_HISTORIA.md` · `docs/MAPA-DEL-PROYECTO.md` (niveles, carpetas, dependencias, cómo probar) · catálogo de BPs, materiales y Niagara (qué hace cada uno) · trackers que faltan · `assets-existentes`, `MECANICAS-PORTABLES` §0, `CLAUDE.md` §3/§6 | nulo | git |
| **F2 · Huérfanos dentro de los BPs** | nodos sueltos de los BPs de las últimas semanas (`scripts/clean_orphans.py`), BP por BP, leyendo antes y compilando después | bajo | tag + git |
| **F3 · Archivar assets huérfanos** | los 68 de H2 (y lo que Beltrán decida de los experimentos) → `_Deprecated/Content-2026-11-14/`, fuera del proyecto, con el editor cerrado (`archive_unused.py` + `limpiar_con_editor_cerrado.py`) | medio | `_Deprecated/` + tag |
| **F4 · Fuera de Unreal** | `Packaging/` → `Packagings` · caché de Fab · `scripts/` de la skill separados en reusables y archivo · docs de la raíz a `docs/historia/` · `DisableRHIThread=False` en todas las variantes de Quest | bajo | git |
| **F5 · Verificación final** | smoke de la Obra · `-game` de Inner Canvas y de la demo · `verificar_plugins.py` · commit | — | — |

No se renombra ni se mueve de carpeta ningún asset vivo: el orden de `Content/` del 10-02 se sostiene. Lo que falta es sacar lo que
sobra y escribir el mapa.
