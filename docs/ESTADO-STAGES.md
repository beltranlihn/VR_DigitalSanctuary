# Estado de los stages — Soul Charger

Índice de alto nivel de dónde está cada stage. **Detalle fino de cada Blueprint → su tracker en `.claude/skills/unreal-vr/blueprints/<BP>.md`.** Actualizá este archivo al terminar de trabajar un stage.

> Última actualización: **2026-07-22**.

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
- **Touch = "Attracting" (etapa de MÚSICA)** — 🟡 en diseño, a punto de arrancar (dev: Nico). NO es "interacción táctil genérica": es un **secuenciador de 5 pasos** donde apuntás burbujas sonoras con un beam, las atraés con trigger (far-grab con interp), las posás en los 5 bloques de una mesa y suenan cuantizadas (Quartz) sobre un pad; con los 5 llenos, "Guardar melodía" (SaveGame). **Brief + organigrama de construcción completo → [`stages/touch-attracting.md`](stages/touch-attracting.md)** (incluye el scaffold ya creado en `Stages/Touch/`: widget de instrucciones naranja + stubs de los BPs base + `SG_Melody`). Audio verificado en `skills/unreal-vr/references/audio-quest.md`. Las mecánicas de agarrar/apuntar de GDXR (`Recursos/`) sirven de referencia de interacción.
- **Inicio** — entrada/onboarding de la obra. Sin empezar.
- **Centro / Salida** — núcleo y cierre de la obra. Sin empezar.

**Al arrancar cualquiera:** usar **Breath como plantilla**, crear su tracker en `blueprints/` desde el día 1, y actualizar este archivo.

---

## Cómo mantener este archivo
Al terminar de trabajar un stage: actualizá su fila (estado, qué se hizo, qué falta) y la fecha de arriba. El detalle por-Blueprint va en los trackers de la skill, no acá — esto es el mapa de alto nivel.
