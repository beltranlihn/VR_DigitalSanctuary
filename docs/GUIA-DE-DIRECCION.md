# Guía de dirección · cómo se administra Soul Charger

> Para quien dirige y para quien ajusta: qué se cambia dónde, cómo se prueba y qué no hay que romper.
> Escrita el 2026-10-02, con el reordenamiento del proyecto (ver `docs/AUDITORIA-ESTRUCTURA-2026-10-02.md`).

---

## 1. La obra en una página

```
L_SoulCharger_Obra  (el nivel del APK)
 └─ BP_Obra_SC  ── el DIRECTOR: lleva el reloj y las fases (Hall → 5 etapas → final → créditos)
     ├─ lee  DA_Partitura_Obra ............ CUÁNDO pasa cada cosa (todos los tiempos narrativos)
     ├─ carga como celdas los 6 niveles de test (LoadLevelInstance):
     │     Test_Breath · Test_Heart · Test_Mind · Test_Sequencer · Test_Draw · Test_Hall
     │     → DÓNDE pasa cada cosa (TargetPoints) y CÓMO es cada mecánica (sus actores y perillas)
     └─ habla con cada etapa SOLO por el contrato (StageIntro / Begin / RequestEnd / Outro + bStageDone)
```

**Las celdas son los niveles de test.** Lo que se ajusta en `Test_Heart` es lo que se ve en la Obra. Al arrancar,
la Obra descarta los actores con tag `TestOnly` (el ensayo, el piso de prueba, los andamios).

**Cada nivel de test tiene su ensayo** (`BP_StageRunner_SC`, `TestOnly`): Play en el nivel y la etapa corre como en la
Obra (velo, título, Alma, instrucciones, mecánica, pedido de cierre, carga) con **los mismos tiempos de la Partitura**.

---

## 2. ¿Dónde se cambia cada cosa? (las cuatro preguntas)

| Pregunta | Dónde | Cómo |
|---|---|---|
| **¿Cuándo?** (cuánto dura algo, cuándo entra Alma, cuándo se corta una etapa) | `/Game/SoulCharger/Obra/Partitura/DA_Partitura_Obra` | Doble clic, cambiar el número, guardar. Lista completa: `docs/PARTITURA.md` |
| **¿Dónde?** (dónde aparece Alma, la carga, el título de cada etapa) | TargetPoints `sc<K>_alma_in`, `sc<K>_alma_side`, `sc<K>_charge`, `sc<K>_title` en el nivel de test de la etapa | Moverlos en el viewport y guardar el nivel |
| **¿Cómo se ve y se siente una mecánica?** (umbral de respiración, latidos, color, tinta...) | Las perillas de su Blueprint o de su instancia en el nivel de test | Lista por mecánica: `docs/PERILLAS.md`. Si la instancia tiene un valor puesto, **manda la instancia** |
| **¿De qué color es el velo de cada etapa?** | `CTop`/`CHor` del `BP_StageRunner_SC` del nivel de test de la etapa | La Obra los lee al arrancar (`ReadRunners`) |

🔴 **Lo que NO se toca para ajustar:** los grafos de `BP_Obra_SC`. Si para cambiar un tiempo hace falta abrir un grafo,
es un tiempo que todavía no está en la Partitura: se agrega a la Partitura (ver §7), no se cambia el número en el grafo.

---

## 3. Recetas

### Cambiar un tiempo de la obra
1. Abrir `DA_Partitura_Obra`, cambiar el valor, **guardar**.
2. `python tools/unreal/smoke_obra.py` (≈9 min, sin visor): tiene que decir **OK**.
3. Probar en el visor (VR Preview de `L_SoulCharger_Obra`, o el APK).

### Ajustar una mecánica
1. Abrir su nivel de test (`Test_Breath`, `Test_Heart`, `Test_Mind`, `Test_Sequencer`, `Test_Draw`, `Test_Hall`).
2. Seleccionar el actor y cambiar la perilla en el Details (o en el Blueprint si es un valor de clase).
3. Play en el nivel: el ensayo corre la etapa entera. Sin visor: `python tools/unreal/probar_nivel.py Test_Heart`.
4. Guardar el nivel. La Obra lo toma tal cual (es su celda).

### Probar la obra entera desde un punto
- En el editor: en la instancia de `BP_Obra_SC` (nivel `L_SoulCharger_Obra`), categoría **Debug**, `DebugStart`:
  `1` Hall · `2-9` pasos del Hall · `10-14` Entering (apertura, Alma, instrucciones, mecánica, salida) · `20-24` Recognizing ·
  `30-34` Loving · `40-44` Attracting · `50-54` Surrounding · `60` última carga · `61` regreso · `62` resultados · `63` SHARE · `64` créditos.
  🔴 Volver a **−1** antes de empaquetar (la Obra lo avisa en el log: `OBRA CONFIG: ATENCION`).
- Sin editor: `smoke_obra.py` acepta lo mismo por línea de comandos (`-ObraStart=N`), y `-ObraSpeed=N` acelera el reloj.

### Antes de un APK
1. **Guardar todo** (Ctrl+Shift+S).
2. `python tools/unreal/smoke_obra.py` → **OK**.
3. Checklist de §6.
4. `python tools/unreal/empaquetar_obra.py` (o `--variante v2` para instalarlo al lado del otro). ≈15 min.
5. Con el visor conectado: `powershell -File tools/unreal/instalar_quest.ps1` (o `-Variante v2`).

---

## 4. El contrato de etapa (cómo habla el director con las etapas)

| Llamada | Quién la hace | Qué hace la etapa |
|---|---|---|
| `StageIntro()` | el director, después de que Alma presenta | aparece (sin mecánica todavía) |
| `StageBegin()` | el director, después de las instrucciones | arranca la mecánica |
| **`StageRequestEnd()`** | el director, a los `Etapa_Tope[K]` s de mecánica (o `Sim_EtapaMax` con `bSimulated` en Attracting y Surrounding) | **cierra por su propio camino**: Breath/Heart/Loving quedan listas · Attracting guarda la melodía (SAVE) si hay · Surrounding guarda y presenta el dibujo |
| `bStageDone` | la etapa lo pone en true | el director lo lee cada cuadro; cuando está, sigue |
| `StageOutro()` | el director, con `bStageDone` (o a `Corte_Espera` s del pedido, tope de seguridad) | se va (animación de salida, suelta los mandos) |

**Reglas del contrato:**
- La etapa **nunca** llama al director ni conoce `BP_Obra_SC`. El director **nunca** fuerza el final de una etapa: lo pide.
- El ensayo (`BP_StageRunner_SC`) llama exactamente lo mismo: lo que funciona en el ensayo funciona en la Obra.
- Una etapa nueva implementa las 4 funciones + `bStageDone` y se agrega a los `switch` de `CallIntro/CallBegin/CallOutro/ReadDone/RequestEnd` (Obra) y `RIntro/RBegin/ROutro/RRead/RRequestEnd` (ensayo).

---

## 5. Mapa de fases de la Obra (y qué perilla de la Partitura manda en cada una)

| Fase | Momento | Perillas |
|---|---|---|
| 16 | aviso de prototipo (si `bDisclaimer`) | `Aviso_Dur` |
| 9 | Hall: velo, título SOUL CHARGER, recorrido, timbre, sensor, elección del alma, HUD | `Hall_VeloAbre*`, `Titulo_*`, `Bajada_*`, `Logos_*`, `Hall_IntroA`, `HUD_EEGRetardo` (el resto del Hall: perillas de `BP_HallDirector_SC`) |
| 0 | apertura de cada etapa: velo de color + título | `Etapa_VeloAbre*`, `Etapa_Titulo*`, `Alma_Entra` |
| 4 | Alma presenta la etapa | `Alma_VozRetardo`, `Alma_TrasVoz` |
| 5 | instrucciones | `Instr_Dur[K]`, `Instr_EsperaMax` (Attracting) |
| 6 | la mecánica | `Etapa_Tope[K]` (pedido de cierre), `Corte_Espera`, `Sim_EtapaMax` |
| 7 | salida de la etapa + felicitación de Alma | `Salida_Dur[K]`, `Salida_TrasVoz` |
| 8 | carga del anillo | `Carga_Dur[K]`, `Carga_Minima`; la última = la carga final, con `Final_NegroRampa` |
| 2 | Alma invita a la siguiente, el velo cierra | `Despedida_Retardo`, `Despedida_TrasVoz`, `Velo_CierreDur` |
| 10-11 | a negro, regreso al Hall | `Regreso_HallA`, `Regreso_VeloIni/Fin`, `Regreso_PezA` |
| 12 | resultados y SHARE / DON'T SHARE | `Res_*`, `Comp_Nado`, `Comp_Lejos` |
| 13 | salida del Hall | `Salida_HallA` |
| 14 | constelación y créditos | `Const_*`, `Creditos_Dur` |
| 15 | fundido y reinicio | `Fundido_Dur` |

---

## 6. Checklist de build de público (antes de cada APK que va a ver gente)

En la instancia de `BP_Obra_SC` (`L_SoulCharger_Obra`):
- [ ] **Config → `bSimulated`**: `false` para el festival (con `true` los datos son simulados, las etapas cortan a `Sim_EtapaMax` y el cortafuegos de compartir elige SHARE). `true` solo para el APK de postulación.
- [ ] **Config → `bDisclaimer`**: `true` solo si va el aviso de prototipo.
- [ ] **Debug → `DebugStart`** `−1` · `Speed` `1` · `bPhotos` `false` · `bDebugEnding` `false` · `DebugShare` `−1` · `DbgDrawSynth` `false`.
- [ ] Prueba de humo **OK** con el estado guardado.

La Obra imprime al arrancar una línea `OBRA CONFIG: ...` con todo eso, y `OBRA CONFIG: ATENCION` si hay algo de prueba
encendido: es lo primero que hay que mirar en el logcat del visor.

---

## 7. Cuando hace falta tocar Blueprints (para quien programa)

1. **Leer antes**: el tracker del BP en `.claude/skills/unreal-vr/blueprints/` y `docs/REGLAS-DE-ORO.md`.
2. **Cambios de estructura** (variables, funciones nuevas) **con un nivel neutro abierto** (`Test_QuestCtrl`), nunca con el nivel
   donde el BP está colocado: el reinstanciado puede llevarse el actor (gotcha 402).
3. **Un tiempo nuevo** → a la Partitura: variable en `BP_Partitura_SC` (categoría por momento, instance-editable) + valor en
   `DA_Partitura_Obra` + copia en `BP_Obra_SC` (categoría Partitura) + línea en `LoadPartitura` + el getter en el grafo.
   Y la entrada en `tools/unreal/partitura_def.py` → `python tools/unreal/gen_partitura_doc.py`.
4. **Un escritor por estado**: si dos funciones escriben lo mismo en el mismo cuadro (el velo, el reloj `T`), gana la última y
   el ajuste "no hace nada". Antes de agregar una capa, buscar quién más escribe esa variable.
5. **Después de cada cambio**: compilar sin errores → guardar → `smoke_obra.py` OK → commit.

---

## 8. Mapa de carpetas

```
/Game/SoulCharger/Obra/                 L_SoulCharger_Obra (el nivel final, en la raíz de la carpeta para encontrarlo rápido)
                                        Blueprints/ (BP_Obra_SC, ensayos, créditos, aviso) · Partitura/ (DA_Partitura_Obra)
                                        Titles/ (títulos y créditos) · Audio/ (voces de Alma, Placeholder/) · Materials/
/Game/SoulCharger/Hall/                 inicio, hall y regreso, con el timbre · Maps/Test_Hall
/Game/SoulCharger/Mechanics/Breath/     Entering, la etapa: orquestador con voces, valle, aliento · Maps/Test_Breath
/Game/SoulCharger/Mechanics/Heart/      Recognizing: el latido               · Maps/Test_Heart
/Game/SoulCharger/Mechanics/Mind/       Loving: la célula y el fluido        · Maps/Test_Mind
/Game/SoulCharger/Mechanics/Sequencer/  Attracting, la etapa                 · Maps/Test_Sequencer
/Game/SoulCharger/Mechanics/Draw/       Surrounding: la etapa (el océano) · Maps/Test_Draw, Test_DrawPalette
/SC_Draw/  (VR_Test/Plugins/SC_Draw)    el SISTEMA de dibujo, portable: director, herramienta, trazo, paleta
/SC_Breath/ (VR_Test/Plugins/SC_Breath) el sistema de respiración: sensor, metaball, guía (la etapa queda en Mechanics/Breath)
/SC_Sequencer/ (VR_Test/Plugins/SC_Sequencer) el secuenciador entero (en Mechanics/Sequencer queda solo su nivel)
/SC_Base/  (VR_Test/Plugins/SC_Base)    lo que comparten las mecánicas portables: mandos, aparición, puntero, sonidos de interfaz, pedestal
/Game/SoulCharger/Shared/<Pieza>/       lo que usan varias etapas: HUD, Results, Ghost, UserTool, Appear, BioSensor,
                                        ChargeRing, QuestController, Subtitles (cada una con su Test_ si lo tiene)
/Game/SoulCharger/Core/<Pieza>/         la base: Alma, Pawn, ProtoSoul, Signals (BioHub/OSC), Light, Audio, Pointer, Input, UI, Debug
/Game/XRFramework, /Game/XRMannequins   la base VR de Epic (GameMode, input, manos)
/Game/_Deprecated/                      sin uso: se saca del proyecto con tools/unreal/limpiar_con_editor_cerrado.py
```
Dentro de cada mecánica, del Hall y de la Obra los assets van **por tipo**: `Blueprints/ Materials/ Meshes/ Textures/ Audio/
Input/ VFX/ UI/ Data/ Maps/`. Un asset nuevo va a la carpeta de su mecánica y a la subcarpeta de su tipo. Si lo usan dos
mecánicas o más, va a `Shared/`.

Lo que la obra no usa quedó **fuera del proyecto**, en `_Deprecated/Content-2026-10-02/` (1596 assets: V1/V2/V3, galería,
calibración, Touch, StylizedKitchen, Fab, EasyFog, demos del template). Para traer algo de vuelta:
`python tools/unreal/archive_unused.py --restore Content-2026-10-02 --only /Game/Ruta` con Unreal cerrado.
Git conserva todo en el tag `respaldo-pre-reorden-2026-10-02`.

## 9. Herramientas (`tools/unreal/`)

| Script | Para qué |
|---|---|
| `smoke_obra.py` | Prueba de humo de la Obra entera, sin visor (≈9 min). OK = todas las marcas en orden y 0 errores |
| `probar_nivel.py <Test_X>` | Corre un nivel de test un rato y resume su log |
| `empaquetar_obra.py [--variante v2]` | Arma el APK y lo copia a Recursos |
| `instalar_quest.ps1 [-Variante v2]` | Instala el APK en el visor y verifica que llega al Hall |
| `deps.py` | Grafo de dependencias de Content/ (qué usa qué), sin abrir Unreal |
| `archive_unused.py` | Saca assets sin uso del proyecto (y los devuelve) |
| `partitura_def.py` + `gen_partitura_doc.py` | La definición de la Partitura y su documento |
| `gen_perillas_doc.py` | Regenera `docs/PERILLAS.md` desde un volcado del editor |
| `partitura_export.py` (+ `mcp/partitura_export_job.py`) | Publica los valores vivos del DA y las perillas en `obra/unreal/` para el editor web (`obra/unreal/LEEME.md`) |
| `smoke_obra.py --speed 1 --traza` | Además escribe `obra/unreal/traza.json`: la secuencia real de fases con el reloj de la obra |
