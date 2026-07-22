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

## ⚪ Stages sin empezar (carpetas vacías o mínimas)
- **Movement** — sistema de **dibujo 3D** (el usuario dibuja "el interior de la ameba"). Decisión de arquitectura ya tomada: **procedural mesh (ribbon), NO Niagara** (tiene que ser bakeable + persistible por usuario). Receta en `skills/unreal-vr/references/movement-3d-drawing.md` (algoritmo `PincelA_AddPoint` + color picker HSV + grab + persistencia SaveGame). Se revisaron 4 proyectos VR de referencia (en `Recursos/`).
- **Mind** — stage mental. Sin empezar.
- **Touch** — interacción táctil. Sin empezar (mecánicas de VR interesantes en el proyecto GDXR de `Recursos/`: botones, agarrar, mover cosas).
- **Inicio** — entrada/onboarding de la obra. Sin empezar.
- **Centro / Salida** — núcleo y cierre de la obra. Sin empezar.

**Al arrancar cualquiera:** usar **Breath como plantilla**, crear su tracker en `blueprints/` desde el día 1, y actualizar este archivo.

---

## Cómo mantener este archivo
Al terminar de trabajar un stage: actualizá su fila (estado, qué se hizo, qué falta) y la fecha de arriba. El detalle por-Blueprint va en los trackers de la skill, no acá — esto es el mapa de alto nivel.
