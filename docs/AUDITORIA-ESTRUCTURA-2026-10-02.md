# Auditoría de estructura · código, Blueprints y pipeline de ajustes · 2026-10-02

**Pregunta de Beltrán:** ¿estamos armando bien la estructura de código y Blueprints? ¿Las mecánicas son migrables? ¿Está claro el pipeline para hacer ajustes? *"Cada vez que hacemos un ajuste, se están rompiendo otras cosas."* El proyecto se va a trabajar con más personas: tiene que quedar ordenado y fácil de ajustar (timing, parámetros, perillas).

**Cómo se midió** (sin PIE y sin tocar el nivel):
- Grafo de dependencias de los **2383 assets** de `Content/`. Se sacó leyendo las rutas `/Game/...` de cada `.uasset` y `.umap` (`tools/unreal/deps.py`). A partir de ese grafo se calculó lo que de verdad usa `L_SoulCharger_Obra`.
- Conteo de funciones y variables de los 13 Blueprints centrales, con el MCP en modo lectura.
- Lectura de trackers, docs y git, más el análisis de literales de `docs/editor-obra/anexos/03-unreal-orquestacion.md`.

---

## 0. Qué se hizo (estado al cierre del 2026-10-02)
| Punto de la auditoría | Hecho | Dónde |
|---|---|---|
| Respaldo antes de tocar nada | ✅ commit `a25b6ad` + tag `respaldo-pre-reorden-2026-10-02` | git |
| Assets sin uso fuera del proyecto (V1/V2/V3, galería, calibración, Touch, StylizedKitchen, Fab, demos) | ✅ 1596 assets, Content de 2,2 GB a 402 MB | `_Deprecated/Content-2026-10-02/` (raíz, fuera de git), `tools/unreal/archive_unused.py` |
| Cortar los enlaces del código vivo al viejo | ✅ | commit `d6d91f1` |
| Una sola fuente de tiempos (C1) | ✅ `DA_Partitura_Obra` (60 perillas), la leen la Obra y los ensayos; 63 + 9 literales conectados | `docs/PARTITURA.md`, tracker `BP_Partitura_SC.md` |
| Cierre único de etapa (C2) | ✅ `StageRequestEnd` en las 5 etapas; la Obra y el ensayo cortan igual | trackers de cada etapa |
| Prueba de humo de la obra entera (C5) | ✅ `tools/unreal/smoke_obra.py` (marcas en orden + 0 errores; `--traza` para el editor web) | `docs/GUIA-DE-DIRECCION.md` §3 |
| Probar un nivel sin visor | ✅ `tools/unreal/probar_nivel.py` | |
| Empaquetar e instalar en un paso | ✅ `empaquetar_obra.py` + `instalar_quest.ps1` (APK de la Obra cocinado, sin instalar) | |
| Guía de dirección, reglas de oro, perillas | ✅ | `docs/GUIA-DE-DIRECCION.md`, `docs/REGLAS-DE-ORO.md`, `docs/PERILLAS.md` |
| **Carpetas ordenadas por mecánica y por tipo** (pedido del 2026-10-02 a la tarde) | ✅ 461 assets movidos, 60 archivados, 12 niveles en su carpeta nueva (3 con nombre nuevo: Test_Breath, Test_Mind, Test_Draw), CoreRedirects para las rutas viejas de los niveles | `tools/unreal/reorden_contenido_2026-10-02.json`, `CLAUDE.md` §6 |
| Mecánicas como plugins (portables a otro proyecto) | ⬜ propuesta, pendiente de decisión | §4 de este documento y el informe final |
| LFS + locks, llevar `core/esqueleto` a `main` | ⬜ decisiones de Beltrán | `docs/WORKFLOW-EQUIPO.md` |
| Títulos del ensayo del Hall con literales propios | ⬜ pendiente | tracker `BP_HallRunner_SC.md` |

## 1. Veredicto corto

| Pregunta | Respuesta |
|---|---|
| ¿Las **mecánicas** están bien armadas? | **Sí, en general.** Ninguna mecánica conoce a la Obra. Respiración, dibujo (NeuralCanvas), aparición, fantasmas, resultados y el mando están limpios o casi. |
| ¿Son **migrables**? | **La mayoría sí.** Las excepciones son tres: Heart (arrastra el sensor viejo), el alma (`BP_ProtoSoul_SC`) y el HUD (arrastra el director de V2). Ver §4. |
| ¿La **orquestación** está bien? | **No. Ahí está el problema.** `BP_Obra_SC` es un director monolítico: 11 MB, ~130 funciones, 175 variables, 536 literales de tiempo y geometría, y conoce por clase a 30 Blueprints, incluidas piezas internas de las etapas. |
| ¿Está claro el **pipeline de ajustes**? | **No.** Un mismo tiempo puede vivir en cuatro lugares: instancia, CDO, TargetPoint o literal en un grafo. Los tiempos están acoplados entre sí sin que se vea, y no hay una prueba automática que avise cuando algo se rompe. |
| ¿Está listo para **más personas**? | **Todavía no.** Los docs se contradicen sobre cuál es el nivel actual, y `main` va 311 commits atrás. El código que genera los grafos está fuera de git, y tampoco hay bloqueo de binarios. |

**Por qué se rompe lo que no tocamos**, en una frase: las etapas están bien separadas entre sí, pero todas pasan por un solo Blueprint gigante. Ahí los tiempos son números sueltos que dependen unos de otros y hay dos sistemas que escriben lo mismo en el mismo cuadro. Además, cada etapa tiene dos copias de su flujo, la de la Obra y la del ensayo, y esas copias ya divergieron.

---

## 2. Lo que está bien (no tocar)

1. **El contrato de etapa** (`StageIntro / StageBegin / StageOutro + bStageDone`). Lo llama el director y las etapas nunca llaman al director. Está medido: `BP_Obra_SC` solo lo referencian los dos runners y su nivel.
2. **Las celdas son los niveles de test.** La Obra carga `Test_Entering`, `Test_Heart`, `Test_Fluid`, `Test_Sequencer`, `L_TBTest_SC` y `Test_Hall` con `LoadLevelInstance`. Cada mecánica se coloca y se afina en un solo lugar, y el tag `TestOnly` limpia los andamios al arrancar.
3. **NeuralCanvas (el dibujo) es el modelo de mecánica portable.** Tiene carpeta raíz propia, cero dependencias fuera de ella y un solo actor de entrada.
4. **Los managers extraídos.** `BP_BreathManager_SC`, `BP_BreathRig_SC` y `BPC_AppearLuz_SC` no dependen de ningún Blueprint. `BP_UserTool_SC` y `BP_ResultsArt_SC` solo dependen de la aparición.
5. **La cultura de registro.** Hay un tracker por Blueprint y gotchas numeradas, y las mediciones se hacen antes de opinar. El problema no es la falta de documentación (§5), es otro.

---

## 3. Las causas de que "un ajuste rompe otra cosa" (con evidencia)

### C1 · Un director monolítico que mete la mano en las etapas
- `BP_Obra_SC` tiene ~130 grafos y 175 variables, y depende de forma directa de **40 assets de tipo Blueprint o nivel**. Entre ellos hay piezas internas de las mecánicas: `BPC_TBTool_NC`, `BP_TBStroke`, `BP_SeqSlot_SC`, `BP_SoundOrb_SC`, `BP_BlobChain_SC` y `BP_SeqRig_SC`. Por ejemplo, la elección SHARE usa el láser del rig de Attracting.
- **El bug del dibujo de hoy es un caso de libro.** Para cerrar la etapa, el director forzaba `PT = 1000` en vez de pedirle a la etapa que cerrara. Así se salteaba el guardado propio del dibujo: no había presentación y los resultados salían vacíos. Cuando el director decide *por* la mecánica, cualquier cambio en la mecánica rompe el atajo, y al revés.
- El contrato se despacha con un **switch por clase** (`CallIntro/CallBegin/CallOutro/ReadDone`). Para agregar o cambiar una etapa hay que tocar el director en cuatro lugares.

### C2 · Los tiempos son literales acoplados, no perillas
- En el volcado hay **536 literales de punto flotante en 122 grafos** (anexo 03 del editor). Los grafos que más concentran son RunObra 57, ResultsFade 56, IntroTitle 50, FlowVeil 42, ResultsShow 23 y HallRingStep 20.
- **Hay acoplamientos invisibles.** La última carga de 6 s se asume en tres literales distintos (`FlowVeil` 9,5→11,5, `ReadCharge` 5,6 + C y el golpe de `ChargeFinal` a 10,5 s). Si se cambia `ChargeTimes[4]` sin mover los otros, el final se desfasa. Lo mismo pasa con `DiscTime` y `DiscStep`, el cierre del velo (69→71,5) y `AdvanceStage`, y los topes 180/120/240 de cada etapa.
- **Una perilla puede vivir en cuatro lugares:** I (instancia en el nivel), CDO (default de la clase), TP (TargetPoint) y L (literal en un grafo). No hay una tabla que diga cuál manda. Las trampas pagadas lo muestran: *"lo de la instancia le gana al Blueprint"*, *"instance-editable nace en cero"* y *"`set_properties` en PIE reconstruye el actor"*.

### C3 · Dos escritores del mismo estado en el mismo cuadro
- `RunObra` (switch 0-15) maneja las fases. Encima, `FinalFlow`, `FlowVeil`, `FlowShare`, `FlowConst`, `SimCut` e `IntroTitle` **reescriben lo mismo después**. El tracker lo dice tal cual: *"lo que escribe gana en ese cuadro"*.
- Cada arreglo se apiló como una capa nueva para no tocar `RunObra`, y eso tuvo sentido en su momento. Pero ahora, para saber qué valor tiene el velo en la fase 9, hay que leer varios grafos y saber en qué orden corren.

### C4 · Dos copias del flujo de cada etapa
- La Obra corre la etapa con `RunObra`. El ensayo corre en cada nivel de test con `BP_StageRunner_SC` (y el Hall con `BP_HallRunner_SC`). **Cada uno lleva sus propios literales y ya divergieron.** El título del runner aparece entre 1 y 5,5 s y se va entre 9 y 12,5 s; en la Obra aparece entre 0,5 y 1,8 s y se va entre 4,6 y 5,6 s. Una etapa que se ve bien en el ensayo puede verse distinta en la Obra.
- Hay más duplicados del mismo tipo: `BP_Obra_SC` nació duplicado de `BP_StageTour_SC`, con islas huérfanas heredadas; `BP_ChargeFx_SC` es duplicado de `BP_ChargeTest_SC`; y `BP_UserTool_SC` lleva una copia de `BP_BioSensorArt_SC`.

### C5 · El pasado sigue enchufado
- De los **212 Blueprints** de `SoulCharger/` y `NeuralCanvas/`, la Obra usa de verdad **83**. Los otros 129 son la historia del proyecto (esqueleto V1, V2, V3, galería, calibración, Touch).
- Igual se cocinan, por dos enlaces:
  - **el pawn** (`BP_VRPawn_SC` → `BP_TestKit` → `BP_StageDirector` → los `L_Room_*` de V1, más `BP_HeartSensor`, `BP_BreathSensor_V2`, etc.);
  - **el HUD** (`BP_SoulHUD_SC` → `BP_Director_Story` de V2 → `BP_Sensor_Soul`, `BP_Director_Rooms`, `BP_Director_Movement`…).
- Eso no es solo peso muerto. **Los Blueprints viejos ensucian la resolución de nombres del DSL**: `CallFunction|Step` se cableó a `BP_HeartSensor.Step`, una clase de V1 (trampa 5 de `BP_Obra_SC.md`). Mientras existan, cada función nueva corre el riesgo de engancharse a la equivocada.

### C6 · Nada avisa cuando algo se rompe
- La verificación es un PIE mirado a mano y un log filtrado. El "robot" que simula un usuario nunca se usó (auditoría del 09-30).
- No hay una lista de marcas esperadas en orden ("entra la fase 4 de la etapa 0", "StageOutro por fin propio = true", etc.) que un script compare contra el log. Por eso las roturas aparecen recién en el visor o en el APK, como pasó con el dibujo.
- **El reloj se frena bajo carga extrema:** el director limita el paso a 0,1 s (corrección del 2026-10-02: no es 1/30 s como decía la primera versión de este documento). Por debajo de 10 fps, el timeline avanza más lento que el tiempo real, mientras que la VO y el audio siguen al tiempo real. En la Quest a 72 fps no pasa; solo afecta a un PIE de fondo muy cargado o a un enganche largo (una carga), donde el reloj pierde lo que excede 0,1 s por cuadro.

---

## 4. Migrabilidad, medida hoy

Dependencias de Blueprint de cada pieza (del grafo de assets, 2026-10-02):

| Pieza | Depende de | Veredicto |
|---|---|---|
| `BP_BreathManager_SC` · `BP_BreathRig_SC` · `BPC_AppearLuz_SC` | — | 🟢 puras |
| `BP_UserTool_SC` · `BP_ResultsArt_SC` · `BP_GhostPlayer_SC` · `BP_Alma_SC` | solo su pieza hermana (aparición, take, aura) | 🟢 |
| `BP_TBDirector_NC` + `BPC_TBTool_NC` (dibujo) | todo dentro de NeuralCanvas + `BP_DrawPalette_SC` | 🟢 (la paleta vive fuera de la carpeta raíz: moverla) |
| `BP_BreathStage_SC` | Alma, blob, rig, pacer, UserTool, ValleyLife | 🟡 capa ETAPA: está bien que conozca a Alma |
| `BP_LovingCell_SC` | Alma, fluido | 🟡 ídem |
| `BP_Sequencer_SC` + `BP_SeqRig_SC` | su cluster de Attracting + `BP_QuestCtrl_SC` | 🟢 el beam ya no vive en el sensor viejo |
| `BP_JourneyContent_SC` | `BP_BioHub`, resultados | 🟢 |
| `BP_FluidMedium_SC` | **el pawn** | 🟡 cambiar por el resolvedor de manos o cámara |
| `BP_HallDirector_SC` | **el pawn**, Alma, ProtoSoul, SoulPicker, arte del Hall | 🟡 es el director del Hall: aceptable, salvo el pawn |
| `BP_HeartManager_SC` | Alma, BioHub, HeartScape, UserTool, **`BP_Sensor_Soul`** | 🔴 el "manager limpio" de 09-19 volvió a enganchar el sensor viejo |
| `BP_ProtoSoul_SC` (el alma) | **`BP_Sensor_Soul`**, **el pawn** | 🔴 |
| `BP_SoulHUD_SC` | **`BP_Director_Story`** (V2) | 🔴 arrastra media obra vieja al cook |
| `BP_VRPawn_SC` | **`BP_TestKit`** → esqueleto V1 | 🔴 el pawn es la raíz de casi todo el peso muerto |

**Conclusión:** las mecánicas se pueden migrar. Lo que no se puede migrar es la Obra, y no hace falta que se pueda, porque es la capa ETAPA y obra. Para que el proyecto sea fácil de trabajar, hay que cortar **cuatro enlaces** (pawn → TestKit, HUD → Director_Story, HeartManager → Sensor_Soul, ProtoSoul → Sensor_Soul) y **sacar los tiempos de la Obra a datos**.

---

## 5. Pipeline de ajustes y trabajo en equipo

| Tema | Hoy | Problema para un equipo |
|---|---|---|
| **¿Cuál es el nivel actual?** | `CLAUDE.md` dice MapsV2 y `_INDEX.md` tiene dos "ETAPA ACTUAL" (V3 y V2). La realidad es `Obra/L_SoulCharger_Obra`. La tabla de estado de `CLAUDE.md` §3 es de agosto. | Alguien nuevo empieza en el nivel equivocado. |
| **Conocimiento** | `gotchas.md` tiene 2955 líneas y 582 entradas; la skill pesa 7,6 MB; hay 47 docs y 173 notas de memoria local. | Es imposible de leer entero, y las reglas clave están mezcladas con la historia. Las notas de memoria no las ve nadie más. |
| **Fuente de los grafos** | Los generadores DSL, los HLSL y las fuentes de mallas están en `VR_Test/Saved/ClaudeScripts/` (3816 archivos), y **`Saved/` está en `.gitignore`**. También hay parte en el scratchpad de cada sesión. | El "código fuente" de la Obra no tiene historia, no se revisa y otra persona no lo ve. |
| **Git** | La rama de trabajo es `core/esqueleto`, que va **311 commits por delante de `main`**. Hay cambios sin commitear en `BP_Obra_SC`, `BP_TBDirector_NC`, `BPC_TBTool_NC` y el nivel (el arreglo del dibujo de hoy). No se usa LFS y `.git` pesa 5 GB. | Clonar es pesado y `main` no sirve de base. Sin `git lfs lock`, dos personas pueden pisarse un `.uasset` sin aviso. |
| **Dónde se cambia un tiempo** | En cuatro lugares posibles (I/CDO/TP/L), sin tabla. | Quien ajusta no sabe si su cambio llega al APK ni qué más mueve. |
| **Debug dentro de la obra** | `DebugStart`, `DbgDrawSynth`, `bPhotos`, `DebugShare`, `ObraDbgFF`, `Speed` y `bSimulated` viven en el director de producción. | Riesgo de salir al festival con un modo de prueba. Por ejemplo, con `bSimulated` el cortafuegos elige SHARE y las etapas cortan a 90 s. |

---

## 6. Qué hacer: tres fases, de menor a mayor riesgo

### Fase 0 · Antes del festival (sin tocar la arquitectura)
1. **Commit + tag** del estado que funciona (`festival-2026-10`). Decidir si `core/esqueleto` pasa a ser la base o se mergea a `main`.
2. **Checklist de build de festival**, como sección fija de `WORKFLOW-EQUIPO.md`. Antes de cada APK de público, chequear estas perillas: `bSimulated`, `bDisclaimer`, `DebugStart −1`, `DbgDrawSynth false`, `bPhotos false`, `DebugShare −1` y `Speed 1`.
3. **Prueba de humo con un solo comando** (`tools/unreal/smoke_obra.py`):
   - corre un PIE de la Obra en autoplay con `Speed` alto;
   - compara el log contra una lista de marcas esperadas en orden (las 5 etapas con "por fin propio", la carga, los resultados con el dibujo, SHARE, los créditos, el reinicio);
   - falla si aparece un `Accessed None`.

   Se corre antes de cada APK y después de cada cambio en la Obra. Es lo que más rápido reduce el "se rompió otra cosa".
4. **Arreglar los docs de entrada.** `CLAUDE.md` §2.b y §3 tienen que decir que el nivel es `L_SoulCharger_Obra`, con su tabla de estado real. En `_INDEX.md`, la sección de la Obra va primero y V2/V3 bajan a "Histórico".

### Fase 1 · Después del festival: un solo lugar para los tiempos y un contrato de verdad
5. **La partitura como datos.** Un `DA_ObraScore` (DataAsset o DataTable) con todos los tiempos narrativos por etapa y por momento. La primera tanda son los ~30 literales del anexo 03: título, velo, entrada de Alma, topes, cierre, última carga, `FlowShare`/`FlowConst` y aviso.
   - Se promueven **por cirugía** (literal → getter), sin reescribir `RunObra`.
   - Los acoplados se expresan relativos entre sí. Por ejemplo, `VeilClose = ChargeEnd − 1,5`, no tres números sueltos.
   - El editor web (`obra/score/score.json` + `contract.json`) ya apunta a esto: el score podría **exportar** ese DataAsset.
6. **`BPI_Stage` en vez del switch por clase.** Una interfaz con `StageIntro`, `StageBegin`, `StageOutro`, `StageRequestEnd(Reason)`, `IsStageDone` y `GetStageInfo`.
   - **`StageRequestEnd`** es la pieza que faltaba: el director *pide* el cierre y la etapa cierra por su propio camino (guardar, presentar, soltar). Nunca más forzar `PT = 1000`.
   - Así una etapa nueva no toca el director.
7. **Un escritor por estado.** Partir `BP_Obra_SC` en componentes con dueño único: fases y reloj · velo y título · Alma/VO · carga · final (resultados/share/créditos) · ambientes · debug.
   - `FinalFlow` deja de reescribir lo que escribió `RunObra`: cada cosa la escribe un solo componente.
8. **Runner = Obra.** `BP_StageRunner_SC` y `BP_HallRunner_SC` usan el mismo componente de fase que la Obra, con los mismos datos. Así el ensayo de una etapa reproduce exactamente lo que pasa en la Obra.
9. **Debug afuera.** Un `BP_ObraDebug_SC` con tag `TestOnly` es dueño de `DebugStart`, `DbgDrawSynth`, `bPhotos`, `DebugShare` y `Speed`. En el build de público no existe.

### Fase 2 · Orden para el equipo
10. **Cortar los cuatro enlaces** de §4 y **mover los 129 Blueprints sin uso a `/Game/_Archivo/`**, o borrarlos después del tag. Así se achica el cook y se terminan las colisiones de nombres del DSL. Se verifica con `deps.py`, buscando que la Obra quede en ~83 Blueprints.
11. **Estructura de carpetas** que se entienda sola:
    ```
    /Game/SoulCharger/Obra/          director, partitura, nivel final
    /Game/SoulCharger/Mechanics/<X>/ una carpeta por mecánica, con su nivel Test_<X> adentro
    /Game/SoulCharger/Shared/        pawn, hubs, Alma, HUD, aparición, resolvedor de manos
    /Game/NeuralCanvas/              (ya está bien)
    /Game/_Archivo/                  la historia
    ```
    Hoy los `Test_*` de las etapas están en la raíz de `/Game` y `Core/` mezcla vivos con muertos (27 de ~110 Blueprints en uso).
12. **Una ficha por mecánica** (`Mechanics/<X>/README.md` o la ficha de `MECANICAS-PORTABLES.md`) con **la tabla de perillas**: nombre · qué cambia · dónde vive (I/CDO/TP/DA) · rango · en qué nivel se ajusta. Es el documento que necesita una persona que entra a ajustar timing.
13. **Versionar la fuente.** Pasar los generadores DSL, los HLSL y los `.blend`/`.py` de mallas de `Saved/ClaudeScripts/` a `tools/unreal/` y `art/source/` dentro del repo.
14. **Git para varias personas.** LFS con `lockable` para `*.uasset`/`*.umap` hacia adelante (el plugin de control de versiones de Unreal muestra los locks). Un dueño por Blueprint grande, y PRs a `main` por hito.
15. **Gotchas en dos niveles.** Las ~30 reglas que muerden a cualquiera van a una página corta (`REGLAS-DE-ORO.md`); las otras 550 quedan como archivo histórico consultable.

---

## 7. Prioridad sugerida

| # | Qué | Esfuerzo | Riesgo | Impacto en "se rompe otra cosa" |
|---|---|---|---|---|
| 1 | Prueba de humo + checklist de festival | ½ día | nulo | **alto** (detecta antes del visor) |
| 2 | Commit/tag + docs de entrada | 1 h | nulo | medio (equipo) |
| 3 | Partitura `DA_ObraScore` (30 literales) | 1-2 días | bajo (cirugía) | **alto** (tiempos en un lugar) |
| 4 | `BPI_Stage` + `StageRequestEnd` | 1 día | medio | **alto** (cierres por su propio camino) |
| 5 | Runner = Obra | 1 día | medio | alto (el ensayo vuelve a ser fiel) |
| 6 | Cortar 4 enlaces + archivar 129 BPs | 1 día | medio (cook) | medio (DSL y cook) |
| 7 | Partir `BP_Obra_SC` en componentes | 3-5 días | **alto** | alto, pero solo después de 1, 3 y 4 |
| 8 | Carpetas, fichas, LFS, fuente versionada | 2 días | bajo | alto para el equipo |

**Regla para hacerlo sin romper:** primero la prueba de humo (1), después todo lo demás. Cada paso termina con la prueba en verde y un commit. El paso 7 no se hace antes del festival.
