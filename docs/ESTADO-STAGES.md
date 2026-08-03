# Estado de los stages — Soul Charger

Índice de alto nivel de dónde está cada stage. **Detalle fino de cada Blueprint → su tracker en `.claude/skills/unreal-vr/blueprints/<BP>.md`.** Actualizá este archivo al terminar de trabajar un stage.

> Última actualización: **2026-08-03**.

Stages (carpetas en `VR_Test/Content/SoulCharger/Stages/`): **Breath · Heart · Mind · Movement · Touch · Inicio · Centro · Salida**. Además hay una herramienta de investigación en `Content/SoulCharger/Calibration/` (no es un stage de la obra).

---

## 🟢 BREATH — completo end-to-end · **plantilla de la obra**
El flujo entero corre en el visor sin errores. **Es el patrón arquitectónico a copiar en los demás stages.**

**Flujo:** negro → fade in → widget de instrucciones (5 páginas: relajación → tomar sensor → calibrar sobre el abdomen → círculo reactivo → inicio) → aparece la esfera y arranca el conteo → cada **inhalación sostenida 4s** suma 1 (con háptico) → al llegar a `MaxBreathCount` el sensor desaparece, la esfera va a escala 0, fade a negro, reinicia.

**BPs (todos con tracker en `blueprints/`):**
- **`BP_BreathSensor_V2`** — sensor agarrable + detector de respiración + calibración/zona segura + conteo + hápticos, fusionado. El corazón del stage. 🔴 Su función `Step` es un pipeline **frágil**: no reescribir desde el read, solo cirugía.
- **`Box_Breath`** — la esfera visual (consumidor tonto: lee `bBreathing`/`bInhaling`/`bStageComplete` y anima escala + material emisivo + Niagara).
- **`BP_Instructions`** + **`WBP_BreathInstructions`** — máquina de 5 páginas (UMG world-space), spawnea sensor y esfera.
- **`BP_BreathStageManager`** — orquesta el cierre (fin de conteo → esfera a 0 → fade → reinicio).
- **`BP_IntroFade`** / **`BP_FadeSphere`** (`Core/UI/`) — fade compartido.

**Patrón arquitectónico que deja:** sensor / consumidor visual / manager de cierre **separados** (cada uno un BP, pawn liviano); widget de instrucciones world-space event-driven; cierre por manager + fade + transición.

**Pendientes menores (no bloquean):** borrar prints de diagnóstico `IB:`; verificar en APK real que la calibración acotada (`SafeTol=9`) discrimina abdomen vs muslo; integrar al flujo maestro (hoy corre aislado en `Maps/Tests/L_Test_Breath`).

## 🟡 HEART — en progreso
Segundo stage temático (latido). Recibe el ritmo cardíaco por **OSC** (desde un sensor externo / Empatica-style) y lo visualiza.
- **`BP_OSCReceiver`** — recibe el heart rate por OSC.
- **`BP_HeartSensor`** — beat desde OSC + **visualizador de zona segura (debug)**: esfera traslúcida verde/rojo para calibrar el tamaño de la zona. 🟡 Construido y funcional **pero la esfera queda fija en el mundo** (la zona es relativa a la cabeza) → pendiente hacer que siga la cabeza.
- **`Ball_Heart`** — pulso de escala por latido.
- Widget de 5 páginas + manager + `L_Test_Heart` (duplicados del patrón Breath).

## 🟢 CALIBRATION (herramienta, no stage) — pipeline listo, falta test en visor
Nivel para **levantar datos de muchos usuarios** y tunear los umbrales de detección con evidencia. En `Content/SoulCharger/Calibration/`.
- **`BP_CalibProbe`** (duplicado del sensor), **`BP_CalibDirector`** (máquina de estados de 7 segmentos guiados por tiempo), **`L_Calibration`** (nivel VR).
- **Persistencia:** SaveGame por usuario (`SG_CalibSession` + `SG_CalibIndex`) → un `.sav` por persona que se acumula y persiste; `bUseExternalFilesDir=True` para sacarlo por USB. Empaquetar Development.
- Tracker completo: `blueprints/BP_CalibDirector.md`.
- **Hallazgos del análisis de datos** (guían el diseño de la obra): **reposo** se detecta robusto con `LinSpeed < 1` (generaliza entre personas); **posición del sensor** (en el cuerpo vs fuera) con `horiz < 17`; **inhala vs exhala NO se resuelve con un umbral global** — es sujeto-específico, hay que normalizar por usuario. Por eso el nivel de calibración captura un baseline por persona.
- **Próximo:** test en Link/PIE → después texto in-headset 3D + pacer del segmento de respiración → empaquetar y testear con gente.

## 🟢🟡 TOUCH = "Attracting" (etapa de MÚSICA) — mecánica base PROBADA EN VISOR · falta que el secuenciador suene

> ✅ **2026-08-03 — corre end-to-end en el visor:** apuntás con las dos manos, la burbuja suena al hacer hover, la atraés sosteniendo el gatillo, la posás en un bloque y podés intercambiarla. Falta mucho fine tuning, pero la mecánica está.
> 🔴 **Lo que NO suena todavía: el secuenciador.** `OnBeat` detecta el bloque ocupado y hace pulsar la burbuja, pero **nunca dispara el clip** — falta la reproducción, y migrar el playhead de timer a Quartz.

Secuenciador de 5 pasos: apuntás burbujas sonoras con un beam, las atraés sosteniendo el gatillo, las posás en 5 slots y suenan por step. Brief: [`stages/touch-attracting.md`](stages/touch-attracting.md) · detalle por-BP en `blueprints/BP_*.md`.

**Traspaso:** lo arrancó Nico (Fases 0-5) y desde el **2026-08-03** lo sigue Beltrán en `stage/touch`. 🔴 Al retomarlo se encontró que **todos los actores de gameplay estaban apilados en (0,0,0)** y que los eventos de far-grab **estaban vacíos**: las fases figuraban como hechas porque *compilaban*, pero nunca habían corrido. **Lección para el equipo: que compile no dice nada; una fase no está hecha hasta que se ve corriendo.**

**Hecho y compilando:**
- `L_Touch` armado de verdad: 5 slots en fila (X=55, Z=75), 6 `TP_Bubble_*` y 2 beams.
- **Beam por mano** (`AimBeam_Right`/`Left`, `bIsRight` instance-editable), **attacheado al pawn** en BeginPlay → sobrevive al recentrado. Pose *Aim* (la de grip apunta casi hacia arriba en UE 5.x).
- **Input propio**: `IA_Attract_Left/Right` + `IMC_Touch`, **trigger sostenido**, registrado por el Director con prioridad 1.
- **Burbujas spawneadas por TargetPoint** con tag `BubbleSpawn` → la composición se arma moviendo puntos en el viewport, sin tocar Blueprints, y escala a las ~20 del brief.
- Hover **push** (el beam avisa; `HoverCount` soporta las dos manos), far-grab, colocación en el **slot más cercano**, **swap** con vuelta a `HomeLocation`, y **pulso audioreactivo** en el beat.
- Audio placeholder: `MS_Synth`/`MS_Perc` (MetaSounds procedurales, sin dependencias) en `Stages/Touch/Audio/`.
- Materiales **unlit emisivos** para láser, burbuja y slot (`Stages/Touch/Materials/`).
- Logs con prefijo **`TCH|`** para cruzar la prueba en visor con el Output Log.

**Pendiente:**
- 🔴 **Probar en visor** — nada de esto corrió nunca.
- **Quartz**: el playhead sigue por **timer**. Bloqueado por un paso manual en el editor (crear el custom event desde el pin del `Subscribe`) — ver tracker de `BP_AttractDirector`.
- Fase 8 (botón Guardar + `SG_Melody`), Fase 9 (instrucciones + cierre), Fase 10 (Android).
- Variedad de clip por burbuja desde `DA_SoundBank` (hoy todas comparten el default).
- `Stages/Touch/Ref/` tiene assets migrados con **4 referencias rotas** → riesgo de cook. Nadie los usa; decidir si se borran.
- `L_Touch` **no está en MapsToCook** (no bloquea PIE, sí el APK).
## 🟡 MOVEMENT = "Surrounding" (etapa de DIBUJO 3D) — en construcción

**Fase 1 del plan construida entera (2026-07-29) — falta el test en visor.** Los dos Blueprints compilan limpio y están colocados en `Maps/Tests/L_Test_Movement`:
- **`BP_DrawCanvas`** (motor de geometría): `BuildTriangles` / `BeginStroke` / `AddPoint` / `EndStroke` + `WriteRing` / `CollapseRing` / `PushMesh`, con pre-alocación de la sección, `UpdateMeshSection`, cinta plana con frame transportado y decimación por distancia + ángulo.
- **`BP_BrushTool`** (la herramienta): auto-attach por proximidad a la mano que lo toca, gatillo de esa mano → `BeginStroke`/`AddPoint`/`EndStroke` con ancho fijo.

✅ **Fase 1 probada en visor y funcionando** (2026-07-29): el pincel aparece, se toma con cualquier mano y dibuja. El trazo salía "feo y geométrico" porque **le faltaba el material** — se creó `Materials/M_Brush_Light` (unlit + Fresnel).

✅ **Fase 2 construida, sin probar todavía**: taper de tres tiempos en la geometría, One-Euro sobre la punta, continuación de sección al pasar los 128 puntos, decimación afinada (1 cm / 6°).

✅ **Cadena de widget propia**: `BP_MovementIntro` (sólo el fade) + `Widget/WBP_MovementInstructions` (verde) + su material. El nivel ya no arrastra nada de Breath.

Trackers con el detalle: `skills/unreal-vr/blueprints/BP_DrawCanvas.md` y `BP_BrushTool.md`.

✅ **Calma → luz** (Fase 3) y ✅ **paleta de configuración de 9 celdas** (Fase 4: color · grosor · pincel, selección tocando con la punta) construidas. **Color y grosor validados en visor.**

⏸️ **PAUSA 2026-08-03 (sin batería en el visor) — falta UN test.** Lo último, sin probar: el material pasó a **aditivo con borde suave** y la cinta de **4 vértices a 2 (plana)**, copiando lo que hace el proyecto de Tilt Brush propio. **Qué mirar al retomar:** si desaparecieron las esquirlas triangulares en las esquinas agudas. Plan de contingencia y detalle en `skills/unreal-vr/blueprints/BP_DrawCanvas.md` (sección "RETOMAR ACÁ").

🔴 **Aprendizaje de la sesión** (en `gotchas.md`): una **función impura usada inline como argumento de datos** deja el pin **desconectado en 0**, compilando limpio y sin warnings. Nos mordió dos veces (el ancho del pincel y la supresión de la paleta). Verificar siempre con `get_node_infos` que los pines tengan `connected_pins`.

Falta: presión analógica descartada (el ancho ahora es discreto desde la paleta), roll de muñeca, audio/háptico del pincel, el driver de páginas de instrucciones (bloqueado por textos+íconos), cierre por timer y persistencia.

Nivel de prueba: `Maps/Tests/L_Test_Movement`. Rama: `stage/movement`.

## ⚪ Stages sin empezar (carpetas vacías o mínimas)
- **Movement — contexto de diseño** (el estado vivo está arriba). El usuario dibuja luz en el aire a su alrededor; **el ancho lo da la presión del gatillo dentro del techo que fija la paleta, y la suavidad del gesto modula la luz** (brusco = apagado, suave = luminoso). **Brief + organigrama de construcción completo → [`stages/movement-surrounding.md`](stages/movement-surrounding.md)** (motor de geometría, métrica de calma, los 3 pinceles, persistencia y las 10 fases). Decisiones cerradas: **procedural mesh, NO Niagara**; **cinta plana cuya cara sigue el trazo** (frame por transporte paralelo) con taper de tres tiempos y textura animada, estilo Open Brush; cierre por timer de ~2 min; **paleta en la mano izquierda** (ancho máximo + 2-4 pinceles preset); persistencia SaveGame desde el día 1; `r.MobileHDR=True`. Research de los 4 proyectos VR de referencia (en `Recursos/`) + el algoritmo `PincelA_AddPoint`: `skills/unreal-vr/references/movement-3d-drawing.md`.
- **Mind** — stage mental. Sin empezar.
- **Inicio** — entrada/onboarding de la obra. Sin empezar.
- **Centro / Salida** — núcleo y cierre de la obra. Sin empezar.

**Al arrancar cualquiera:** usar **Breath como plantilla**, crear su tracker en `blueprints/` desde el día 1, y actualizar este archivo.

---

## Cómo mantener este archivo
Al terminar de trabajar un stage: actualizá su fila (estado, qué se hizo, qué falta) y la fecha de arriba. El detalle por-Blueprint va en los trackers de la skill, no acá — esto es el mapa de alto nivel.
