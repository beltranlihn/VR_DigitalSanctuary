# Soul Charger — Guía del proyecto

> **Documento vivo.** Es la fuente de verdad de diseño, arquitectura y convenciones.
> **Cada vez que cambiemos algo de narrativa, arquitectura o estructura, se modifica aquí primero.**
> Obra VR de biofeedback · ~15 min · **Meta Quest 3 STANDALONE (APK Android, sin PC)** · single user · **SEATED** · Alma Digital.

> 🔴 **CORRECCIÓN 16/07 — esto decía "tethered a PC" y era FALSO.** Confirmado por el usuario y por el config (`bPackageForMetaQuest=True`, `vr.MobileMultiView=True`, `r.Mobile.ShadingPath=0`). **No es un detalle: cambia el motor entero.** Corremos el **renderer MÓVIL**, no el de escritorio. Consecuencias que atraviesan todo el documento:
> - El presupuesto por frame no es el de un PC. Todo lo dinámico (luces, mallas, translucidez) se paga carísimo.
> - Varias conclusiones de [materials-vr.md](.claude/skills/unreal-vr/references/materials-vr.md) fueron escritas asumiendo PC VR y **están marcadas para revisión**.
> - `r.Substrate=True`, `r.RayTracing=True` y `r.ForwardShading=True` (que es el ajuste del renderer de **escritorio**) hay que revisarlos: en Android no aplican o son dudosos.
> - ✅ **El OSC NO es problema.** Va por WiFi y el Quest lo recibe sin drama — **testeado por el usuario**. El servidor OSC corre en el Quest y escucha `0.0.0.0`; el software del sensor emite desde otra máquina de la red. No hace falta cambiar nada de la arquitectura de señales por ser standalone.
> Socio: Johns Hopkins Berman Institute of Bioethics. **Marco: obra artística abstracta, NO dispositivo clínico** — es lo que al instituto le interesa.
> **[ABIERTO]** = decisión pendiente. Ver §13.

---
# 0. Estado actual y próximo paso
*(Actualizar al final de cada sesión.)*

### Decisión sobre el OSC
**`BP_OSCReceiver` (`/Game/OSC`) se queda intacto por ahora.** Es nuestra única referencia funcionando del cableado del delegate OSC. Se migra su lógica al GameInstance, se prueba, **y recién entonces se borra `/Game/OSC`**. No moverlo (redirector sin sentido).

### Hito actual: PROBAR LA TRANSICIÓN
Nada de arte, biofeedback, tags ni Data Assets todavía. **Qué valida:** que el streaming no hitchee, que **el fade cubra los dos ojos completos en estéreo**, y que el pawn aterrice bien **sentado**. Los tres riesgos que no se pueden descubrir tarde.

**Base**
- [x] Diseño, arquitectura y convenciones cerrados (este documento)
- [x] Árbol de carpetas creado en `/Game/SoulCharger/` (§10)
- [x] `Ball` borrada
- [ ] Borrar `/Game/Asset` (carpeta vacía)

**Niveles**
- [x] `L_Persistent` creado (duplicado de `Template_Default`) y **vaciado** — solo WorldSettings + PlayerStart
- [x] `L_Test_Stage` creado en `Maps/Tests/` — floor + skylight + directional, **sin fog ni nubes**
- [x] Referencia de escala en `L_Test_Stage`: cubo a **120 cm**, **hidden in game**
- [x] **Streaming funcionando** — `LoadStreamLevel` NO servía (exige registro previo como sublevel); **`LevelStreaming|LoadLevelInstance(byName)` sí**, sin registro, con ruta completa
- [x] `BP_SoulChargerGameMode` (parent GameModeBase, sin tocar el del template) → `Core/Flow/`, con `DefaultPawnClass = BP_VRPawn_SC`
- [x] `BP_VRPawn_SC` — duplicado de `BP_XRPawn` → `Core/Pawn/`
- [ ] PlayerStart de `L_Persistent` a altura coherente con seated

**Fade (el riesgo #1)**
- [x] `M_FadeSphere` creado → `Core/UI/`
- [x] `M_FadeSphere`: **two-sided** + unlit + translucent — *verificado leyendo las propiedades de vuelta*
- [x] `M_FadeSphere`: parámetros `Opacity` (scalar) y `FadeColor` (vector) cableados a MP_Opacity / MP_EmissiveColor
- [x] `BP_FadeSphere` creado → `Core/UI/`
- [x] `BP_FadeSphere`: esfera de 30 cm de radio en el CDO + material asignado + sombras off
- [x] `BP_FadeSphere`: se engancha a la cámara del pawn en BeginPlay (`GetComponentByClass CameraComponent` → `AttachActorToComponent` SnapToTarget) + crea el MID
- [x] `BP_FadeSphere`: función `StartFade(NewTarget, Duration, Color)` + Tick que interpola la opacidad. **Compila.**
- [ ] **Probar en el casco** que la esfera cubre ambos ojos (radio 30 cm: > near clip, < campo visual)

**Flujo**
- [x] `BP_FlowDirector` creado → `Core/Flow/`
- [ ] `BP_FlowDirector`: precarga async → fade → visible + teleport → descarga diferida
- [ ] Colocar FlowDirector + FadeSphere en `L_Persistent`

**Prueba final del hito**
- [ ] Con el casco: el fade cubre **ambos ojos completos**
- [ ] Sin hitch perceptible al streamear
- [ ] La escala se siente bien sentado

### A verificar en el editor (no dar por hecho)
1. **Enum exacto del tracking origin** para seated (eye level, no floor level).
2. Que el nodo **`Assign`** del delegate OSC funcione en el grafo de un **GameInstance**.
3. Si el MCP puede crear **Structs** y **Enums** (no se vio toolset; probablemente manual).

### Capacidades del MCP — verificado
- **Sí:** carpetas, Blueprints, Data Assets, materiales, escribir grafos, colocar/borrar actores, compilar, guardar.
- **Sí, vía duplicado:** **crear niveles** — duplicar `/Engine/Maps/Templates/Template_Default` y luego vaciarlo/poblarlo con SceneTools.
- **No:** instalar plugins (el Message Router lo instala el humano), Project Settings.

---
# PARTE 1 — LA OBRA
---

## 1. Narrativa y flujo

Llegas a un **centro** —arquitectura serena, curva, crema y latón— donde vienes a cargar tu alma.

- **Alma** — amoeba blanca translúcida sobre una base de cobre. Te recibe, te guía, te da el contexto. Es la voz de la obra.
- **Soul Amoeba** — la que tú eliges. **No reacciona al biofeedback**: es tu trofeo. Empieza pequeña; termina con un anillo por etapa.

**Flujo y niveles:**

| # | Nivel | Contenido | Color |
|---|---|---|---|
| — | `L_Persistent` | Master casi vacío: FlowDirector, FadeSphere, pawn | — |
| 1 | `L_Inicio` | Título / menú | azul profundo |
| 2 | `L_Centro` | Alma te recibe · eliges tu ameba · Alma muestra cómo se rellenan los anillos · **calibración EEG** | crema / latón |
| 3 | `L_Breath` | **Entering** — Respiración | azul |
| 4 | `L_Heart` | **Recognizing** — Corazón | rojo / coral |
| 5 | `L_Mind` | **Loving** — Mente | morado |
| 6 | `L_Touch` | **Attracting** — Tacto | amarillo / naranja |
| 7 | `L_Movement` | **Surrounding** — Movimiento | verde |
| 8 | `L_Salida` | Ameba cargada → compartir → constelación | azul profundo |

Los 8 son **sub-niveles que se cargan y descargan** sobre el persistente. **El Centro también streamea** — se descarga mientras estás en una etapa, y todo queda simétrico.

Cada etapa vive detrás de un **portal circular dorado** que se abre a un espacio de color saturado.

> **[ABIERTO]** Nombres por sentido (Breath, Heart…) vs. por etapa (Entering, Recognizing…). Adoptado por ahora: **sentido**. No mezclar.

## 2. Principios de diseño

- **No hay fracaso, ni puntaje, ni tiempo.**
- **El esfuerzo es contraproducente y debe sentirse así.**
- **La tarea es indirecta.** Respirar mueve el mundo. Nunca "mira tu métrica y bájala".
- **Umbrales:**
  - **Quietud** → umbral **absoluto** bien elegido. **No se calibra.** (Verificado por ingeniería inversa de Flowborne: no calibra nada; el mando sobre la mesa cae dentro del umbral.) El umbral **es la instrucción**: no adapta el juego al usuario, le enseña al usuario qué es moverse suave.
  - **EEG** → sí se calibra. **Única calibración de la obra.**
- **Tutorial:** Alma da el contexto → **menú con gráfica y texto simple que pide una ACCIÓN**, no que explica un concepto → **la puerta para avanzar es hacerla.** El lenguaje de UI ya existe en la obra: retícula circular con texto curvado en el anillo ("TOUCH TO ACTIVATE").
- **Ajusta la mecánica a la señal.** Mando (rápido, limpio) → interacción ajustada. EEG (lento, ruidoso) → modulación ambiental, **nunca eventos discretos ni sonidos abruptos**.
- **Biometría como color / brillo / movimiento. Nunca como número.** Un número se lee como calificación.
- **Supresión contextual del biosignal:** en las cargas de ameba y momentos de asombro se **ignora la señal a propósito** (ahí el pico de activación es deseable; leerlo como "no estás en calma" castigaría al usuario por disfrutar).
- **Re-baseline al inicio de cada etapa.**

## 3. Estructura común de cada etapa

Cuatro fases, iguales para las cinco. **`BP_StageBase` implementa este esqueleto; cada etapa solo rellena los huecos.**

1. **Inicio** — Alma te recibe y da contexto.
2. **Instrucciones** — gráfica + texto que pide la acción. Gate: no avanzas hasta hacerla.
3. **Experiencia** — el bucle.
4. **Término y Carga** — cierre sin fracaso + recompensa frente al usuario. *Biosignal suprimido aquí.*

## 4. Las etapas

### 4.1 Entering — Respiración — azul
- **Objetivo:** 10 respiraciones válidas.
- **Input:** mando sobre el abdomen. Se toma un **"sensor" ficticio** (prop diegético que justifica el gesto). Umbral de quietud absoluto + fase inhala/exhala.
- **Mecánica:** ritmo guiado **4s inhala / 6s exhala** (exhalación larga = respuesta parasimpática más fuerte). Movimiento brusco → sales del umbral.
- **Visualización:** el usuario **controla los anillos**. Figura que crece y decrece. Niagara: partículas entran a la boca al inhalar, salen al exhalar. Widget de validez **cromático y de grano grueso**, nunca numérico.
- **Término:** 10 válidas. Sin límite de tiempo.
- **Aporta a la ameba:** **regularidad** → intensidad del halo.
- **[ABIERTO]** 4/6 vs 5/5 (5/5 ≈ 6 resp/min = punto de máxima coherencia cardíaca).

### 4.2 Recognizing — Corazón — rojo/coral
- **Objetivo:** llegar al final de un recorrido ascendente. *Es simplemente reconocer.*
- **Input:** mando sobre el pecho (umbral de quietud) + ritmo cardíaco por OSC.
- **Mecánica:** el háptico **late con tu pulso**: lo sientes. Cada latido dentro del umbral = **impulso hacia arriba** que parte rápido y se frena. Pulso rápido = muchos impulsos cortos. Pulso lento = pocos largos. **Compensados: todos llegan.**
- **Lo que decide el avance es la quietud, no el pulso.** Nunca se premia el pulso lento (no es controlable; castigarlo sería cruel e inútil).
- **El pulso define la *textura* del ascenso, no el puntaje:** rápido = staccato, brillante. Lento = planeos largos, serenos.
- **Visualización:** las líneas horizontales que cruzan la sala son los niveles que superas con cada latido.
- **Término:** llegar arriba.
- **Aporta a la ameba:** **pulso promedio** → ritmo de pulsación.

### 4.3 Loving — Mente — morado
**Marco honesto:** el EEG **no puede medir amor**. Sí puede medir el **estado receptivo** que lo permite. Entonces: **Alma aporta el contenido** (la invitación, traer a alguien a la mente — eso hace que la etapa sea *Loving*), y **el EEG mide la apertura**, que es la precondición.

- **Objetivo:** acumular X tiempo total dentro del umbral. Indulgente, no instantáneo.
- **Input:** **potencia alfa frontal (AF7 + AF8 sumados, NO asimetría)**, filtrada por el software externo y enviada por OSC.
  - Alfa es el fenómeno más robusto y replicado del EEG. La asimetría frontal (FAA) es tentadora pero está en crisis de replicación e indexa "aproximación" en general (incluye ira), no calidez.
  - **Gamma descartado.** El paper de loving-kindness (Lutz 2004) era con monjes de +10.000 horas, y el gamma del cuero cabelludo está dominado por músculo (comprobado paralizando sujetos: la potencia >20 Hz cae 10-200x). En Muse sería un **detector de mandíbula disfrazado de compasión**.
- **Mecánica — invertida respecto al prototipo:** el **bloqueo alfa** es el hallazgo más clásico del EEG: el alfa **cae** con el esfuerzo cognitivo y **sube** al soltar.
  - **Te esfuerzas → alfa cae → el toroide se agita, turbulento.**
  - **Sueltas → alfa sube → se asienta, laminar y luminoso.**
  - **La fisiología hace cumplir la regla sola.** La obra no dice que el esfuerzo es contraproducente: el cuerpo lo demuestra.
- **Visualización:** el **toroide morado** entre el anillo del techo y el del suelo. Turbulencia y brillo del Niagara. Ya existe y es el visual ideal.
- **Calibración:** en el Centro, narrativa. **El baseline debe capturarse en la misma condición que la etapa** — ojos abiertos, en VR. El efecto grande de alfa (2-3x) es con ojos cerrados; en VR el rango es menor, así que importa el **cambio relativo al baseline propio**, no el valor absoluto.
- **Nunca afirmar que la obra "mide amor" o "mide compasión".** Lo defendible: *proxy de apertura y receptividad*.
- **[ABIERTO]** 10-15s puede quedar corto para un baseline estable (la literatura sugiere 60-90s). Se puede estirar mientras Alma habla.

### 4.4 Attracting — Tacto — amarillo/naranja
> 🔄 **ACTUALIZADO 22/07 (narrativa vigente).** La versión anterior planteaba atraer por *calidad del gesto* (suave = viene / tirón = dispersa) y capas pre-armonizadas generadas. La mecánica vigente es un **secuenciador de 5 pasos con clips** y **agarre a distancia por trigger**. Plan de construcción paso a paso: [`docs/stages/touch-attracting.md`](docs/stages/touch-attracting.md).
- **Objetivo:** componer **tu** melodía en un pequeño **secuenciador de 5 pasos**. No existe nota equivocada — todo cuantizado y en key.
- **Escena:** una **mesa/secuenciador con 5 bloques** frente al usuario (en alcance de brazos, sentado) y **~20 burbujas sonoras** (mini-amebas translúcidas) flotando alrededor. De fondo, un **pad** suave en loop, ya sonando.
- **Input:** un **beam/láser sutil** desde el mando (estilo el puntero default de Meta) + **trigger**.
- **Mecánica:**
  - **Hover** sobre una burbuja → reacción visual sutil + su sonido entra en **loop con fade** (preview). Sacás el hover → fade out. Así descubrís los timbres.
  - **Trigger** → la **atraés a distancia** (far-grab): la burbuja te sigue con movimiento suave, como una varita mágica.
  - La posás en uno de los **5 bloques** → queda fija y **entra al secuenciador**: suena **cuantizada** cuando el playhead pasa por su paso, con una **animación audioreactiva** en cada golpe.
  - Posar sobre un bloque **ya ocupado** → **intercambio** (el anterior vuelve a su posición flotante). Iterás y probás armonías hasta que te guste tu patrón.
- **Baranda invisible:** todo cuantizado y en key por defecto; nunca se expone el interruptor para apagarla. **El usuario no puede sonar mal.**
- **Finish:** con los **5 bloques llenos** se habilita **"Guardar melodía"** (botón apuntable con el beam). Guardar cierra la etapa; la melodía queda persistida como tu **firma sonora** (para reusarla en las mecánicas siguientes).
- **Sonido:** **solo clips** (one-shots rítmicos + pad), reproducidos con timing sample-accurate por **Quartz**. **Nada sintetizado en runtime** (ver [audio-quest.md](.claude/skills/unreal-vr/references/audio-quest.md)).
- **Descartado:** repetir una melodía dada (tipo Simón). Es un test de memoria: carga cognitiva, estado de fracaso, y mata el "creando mi propia melodía". Ninguno de los grandes juguetes musicales en VR pide recordar ni repetir.

### 4.5 Surrounding — Movimiento — verde
- **Objetivo:** dibujo 3D libre. **Sin consigna, sin figura a copiar.**
  - *Descartado "dibuja a tu alrededor / cobertura":* dato real de usuarios — unos dibujan ruido, otros plantas, otros objetos. Es impredecible y ninguna condición de forma funciona.
- **Input:** dibujo 3D tipo Tilt Brush + **suavidad del movimiento**.
- **Mecánica:** el pincel responde a la calma del gesto — brusco = fino, apagado; suave = grueso, luminoso. **La calma se vuelve bella, no puntuada.** La herramienta no permite trazo feo.
- **Duración: ~2 minutos** (verificado: más allá hay demasiados trazos).
- **Aporta a la ameba — la clave:** al cargar, **el dibujo colapsa y se miniaturiza hacia adentro de la ameba**: queda como una **escultura dentro de tu ameba translúcida**. Dibujaste alrededor tuyo; ahora vive dentro tuyo. Funciona con *cualquier cosa* que dibujen y resuelve la unicidad con **contenido**, no con un parámetro.

## 5. La Soul Amoeba

**Dos sistemas, dos trabajos. No mezclarlos:**
- **Anillos = progreso.** Un color por etapa, iguales para todos, legibles.
- **El resto = identidad.** Único por persona.

**Elección:** al inicio se muestran **5 opciones** de un **banco rotativo** (20-30 mallas base). El usuario **elige** — elegir crea propiedad, y esa propiedad es lo que hace que compartirla al final signifique algo.

| Fuente | Dato | Parámetro visual |
|---|---|---|
| Banco | elección del usuario | **malla base** |
| Recognizing | pulso promedio | **ritmo de pulsación** |
| Entering | **regularidad** al seguir el 4/6 | **intensidad del halo** |
| Loving | promedio de actividad | **partículas alrededor** — turbulencia y brillo |
| Attracting | tu melodía | **firma sonora** (los 5 clips de tu secuencia + su orden) |
| Surrounding | tu dibujo | **escultura interior** |
| — | animación | **rotación de los anillos** |

**Halo:** late al **ritmo guiado 4/6** (el que la obra te enseñó — igual para todos), y la **regularidad del usuario define su intensidad**: a quien le fluyó → halo intenso y limpio; a quien le costó → halo débil e irregular.

**Rotación de anillos:** al cargarse cada etapa, el anillo **hace una rotación antes de quedar fijo**. En la constelación, esas rotaciones se activan **en órdenes distintos** por ameba — da dinamismo y variedad sin lógica extra.

## 6. UI

- **Nada anclado al casco.** La UI fijada a la cabeza no respeta la profundidad, persigue la mirada y cuesta presencia.
- **Display en muñeca/antebrazo**, consultable al mirar. **Debe hablar el lenguaje visual de la obra** —anillo, texto curvado, latón/luz—, **no el lenguaje clínico**. Nada de "pulsera de paciente".
- Todo lo consultable dentro de **~30°** de la mirada al frente (~55° es el techo antes de fatiga cervical).
- **Biometría como color/brillo/movimiento. Nunca un número ni una etiqueta.**
- **Barra de carga:** 20% por etapa, avanza con los logros. Consultable y de **grano grueso**, no un velocímetro. *(Una barra que avanza con tu calma es literalmente "¿ya estás en calma?" hecho visible, e invita al monitoreo que sube la activación. Mantenerla discreta.)*
- **[ABIERTO]** dónde vive la proto-ameba en la UI.

## 7. Cierre y constelación

- Revelación de tu ameba cargada.
- **Invitación explícita a compartir** (el consentimiento = "privacy as design", el ángulo del Berman).
- Al aceptar, **tu ameba se une al resto**: queda **al centro**, y alrededor aparecen las de usuarios anteriores en **target points fijos**.
- **Se guardan las últimas 30**, reescribiéndose. *El usuario no sabe que la suya desaparecerá algún día — eso lo sabe solo el autor. No tienen nombre.*
- **Hover:** apuntar una ameba la **agranda**, sus partículas se mueven, **suena su melodía**. Al quitar el hover vuelve a su tamaño.
- Como cada partida cambia de key, conviene que suene **una a la vez** — que es lo que el hover ya garantiza.

## 8. Dirección de arte

- Templo minimalista tipo James Turrell: arquitectura curva, crema y latón, anillos de luz, círculos concéntricos, portales dorados a espacios de color saturado. **Abstracto, no fotorrealista** (TRIPP descubrió en testing que los entornos naturales fotorrealistas se leen como estresantes/uncanny; la abstracción fue decisión deliberada).
- **La fragilidad técnica es desproporcionadamente dañina** en una obra de wellness: un glitch inyecta el estrés que la obra intenta quitar. Por eso: **primero que funcione (grey-box), después que sea lindo.**

---
# PARTE 2 — CÓMO SE CONSTRUYE
---

## 9. Arquitectura de gameplay

### Diagnóstico del setup anterior
El bus de eventos no era el problema. El problema era el **alcance**: un enum global con el guion completo del juego, y un `Switch on e_GameEvent` de 20+ casos (casi todos vacíos) en cada BP.
- **"¿Quién escucha el evento 14?" solo se responde abriendo todos los BP.** Es estructural: los Event Dispatchers de UE no tienen vista de "quién está suscrito"; el método recomendado por la comunidad es buscar el nombre con Find-in-Blueprints a mano.
- Insertar un beat en el medio **renumera todo**.
- **No existe ningún lugar donde leer el flujo.**
- Y peleaba contra el objetivo de **"cada etapa standalone"**: un enum global hace que cada etapa dependa del guion global.

> **Matiz: el patrón no estaba mal, estaba mal *escalado*.** Un enum + switch **local** dentro de una etapa (5-10 beats, un solo dueño) es perfectamente legible y sigue siendo la recomendación. Lo que no escala es el enum **global** con switches repartidos.

### Niveles: streaming aditivo
- **Level Streaming aditivo controlado por Blueprint** (`Load Stream Level` / `Unload Stream Level`).
- **Cada nivel de etapa** tiene su **World Settings → GameMode override + PlayerStart** → **se abre y se juega directo en PIE**. Es la mayor palanca de iteración: probar Mind no requiere jugar 10 minutos primero.
- El pawn vive en el persistente y **se teletransporta** al sub-nivel visible. El PlayerStart de cada etapa **solo se usa en standalone** (esa es la función del boot check).
- **Descartado: Streaming Volumes.** Son para mundos grandes con streaming por posición. Con topología fija hub→portal→etapa, una llamada explícita es más clara y debuggeable.
- **Descartado: World Partition.** Hecho para mundos abiertos de 5 km²+. Bajo 1 km² agrega complejidad, overhead de One-File-Per-Actor en control de versiones, HLOD, y **streaming por distancia que pelea contra el gating narrativo explícito**.
- **Descartado: Level Instances.** Tentadores para anidar etapas en el hub, pero **no están garantizados cargados en BeginPlay en builds standalone/empaquetados** (funciona en PIE y falla silencioso al empaquetar). Trampa real.
- **`Open Level` nunca como transición del jugador**: destruye el mundo de forma síncrona, pantalla negra, y puede **stallear el pipeline del HMD** — en el casco eso no se lee como un corte, se lee como pérdida de tracking. Sí sirve para abrir una etapa sola en el editor.

### La transición entre etapas (VR)
1. **Precargar** la etapa siguiente **async** mientras el usuario aún está en el hub (`Should Block on Load = false`, `Make Visible After Load = false`).
2. **Fade** al color de la etapa destino.
3. Hacer visible + teletransportar el pawn.
4. Fade de vuelta.
5. **Descargar la etapa anterior unos segundos después**, fuera del camino crítico.

- ⚠ **El fade de cámara 2D de UE no sirve en VR**: por el render estéreo deja **una región en el centro de ambos ojos sin cubrir**. Solución: **esfera/domo translúcido pegado a la cámara**, animando opacidad 0→1→0.
- ⚠ **El hitching no viene del streaming (que es async), viene del garbage collector al DESCARGAR.** Por eso el paso 5 va fuera del camino crítico. Diagnóstico: `stat dumphitches`, `stat memgc`.
- Meta recomienda explícitamente el fade al cambiar de entorno, para no desorientar.

### El flujo
- **Authority: el GameInstance (Blueprint)**, no un actor manager en el nivel. Sobrevive los cambios de nivel, no se puede olvidar de colocar ni duplicar. Lleva `CurrentStage`, las flags globales, **el retrato de datos** y **el servidor OSC**.
  - *(Los Subsystems serían el lugar "correcto" en UE moderno, pero **requieren C++**: se pueden usar desde BP, no crear. El GameInstance es el sustituto pragmático sin C++ ni plugins.)*
- **Enum global → Gameplay Tags.** `Flow.Breath.SensorGrabbed`. Nunca más renumerar; se eligen de un dropdown; y **coincidencia parcial**: un listener puede suscribirse a `Flow.Breath` y recibir todos los beats de esa etapa.
- **God switch → Gameplay Message Router.** Cada listener registra **solo el tag que le importa**; el filtrado lo hace el sistema. Accesible desde BP, sin C++.
  > ⚠ **[REVISAR — dato nuevo del 16/07]** El **Gameplay Message Subsystem / GameplayMessageRouter NO tiene NINGUNA página de documentación oficial de Epic.** Existe en el código de Lyra, pero Epic **no lo documenta ni lo recomienda**: todo lo que circula presentándolo como "el patrón bendecido de Epic" es interpretación de la comunidad sobre código de ejemplo. Además, toda la maquinaria modular de Epic (Game Features, Component Manager) está apuntada a **proyectos multiplayer grandes con fronteras de plugins** — problemas que esta obra no tiene. Lo que Epic **sí** documenta para "uno avisa, N escuchan" son los **Event Dispatchers**.
  > **No invalida la decisión** (los tags con coincidencia parcial siguen siendo una ventaja real, y los Gameplay Tags sí son oficiales), pero hay que tomarla sabiendo que **construimos sobre código de ejemplo sin documentar ni garantías de API**, no sobre una feature soportada. Alternativa proporcionada: dispatchers + tags, sin el router. Decidir antes de cablear el flujo. Ver [bp-practices.md](.claude/skills/unreal-vr/references/bp-practices.md).
- **El flujo se declara en `DA_FlowSequence`**: lista ordenada de beats, legible de corrido **en una sola tabla**. Es el "lugar donde leer el flujo" que antes no existía — **la mayor ganancia al menor costo**.
- **Cada etapa:** un controller que hereda de `BP_StageBase`, con interfaz mínima (`Activate` / `Deactivate` / `IsComplete`), sus beats locales (aquí un enum+switch local está bien), y **emite un solo tag al terminar** (`Flow.Breath.Complete`). No sabe nada del hub ni de las otras etapas.
- **Boot check por etapa:** si el estado del GameInstance está sin setear → modo standalone, arranca con defaults sensatos.

> **Honestidad:** "¿quién escucha este tag?" **no queda 100% resuelto ni con tags** — Reference Viewer y Find-in-Blueprints ayudan pero no dan un grafo de listeners. Se mitiga con **convención** (documentar listeners por tag), no con herramientas.
> **Lo que sí desaparece:** los switches con casos vacíos, el renumerado al insertar beats, y el "no sé dónde se activa esto".

### Los beats: Sequencer
- **Un Level Sequence corto por beat** (Alma habla, la puerta abre, aparece el objeto), con **Event Track** llamando funciones en el **Director Blueprint** de la secuencia. Es BP-friendly de verdad (Quick Bind).
- **Esperar input del jugador:** `Pause` desde un Event Track, y `Play` cuando el jugador hace la acción. Patrón soportado, no un hack.
- ⚠ **Nunca uses Camera Cut tracks.** Toman control de la cámara del viewport — en VR eso pelea con el head tracking. **Sequencer es titiritero del mundo, no de los ojos.** *(Inferencia a partir de cómo funciona el Camera Cut + principios de confort VR; no hay doc de Epic que lo diga con esas palabras.)*
- **No hagas una sola secuencia gigante de 15 minutos**: imposible de reordenar, lenta de navegar, y obliga a reproducir todo para probar el final.

### Descartados
- **GAS**: para habilidades/atributos de RPG. No aplica.
- **StateTree**: production-ready desde 5.7 y **el framework por defecto para lógica nueva en 5.8**; conceptualmente calza perfecto. Pero se autora en **un editor propio, no en un grafo de BP** — herramienta y paradigma nuevos para un equipo BP-only. **Aplazado**, no descartado.

## 10. Convenciones de proyecto

### Estructura de carpetas
**Regla base: organizar por contexto (feature), no por tipo.** Los prefijos ya dan el filtrado por tipo en el Content Browser; una carpeta `Materials/` con 2 materiales adentro es fricción, no orden.

> **El hábito anterior (carpeta por nivel + subcarpetas BP/Materials/FX) era medio correcto.** La capa **externa** (carpeta por etapa) está bien y es justo lo que hace que cada etapa sea un módulo autocontenido. **La capa interna por tipo es la que sobra.**
> **Excepción:** si UNA etapa junta ~15-20+ assets del mismo tipo, esa sola se subdivide. Nunca preventivamente ni pareja.

```
Content/
├── XRFramework/                  ← contenido del template. No tocar, no mezclar.
└── SoulCharger/                  ← todo lo nuestro. Nada suelto en Content/.
    ├── Core/                     ← SOLO lo que usan 2+ etapas
    │   ├── Flow/                 BP_SoulChargerGI, DA_FlowSequence, F_Beat
    │   ├── Signals/              F_Signal, BP_SignalProvider*, BI_Signal
    │   ├── Amoeba/               BP_SoulAmoeba + sus materiales/FX
    │   ├── Alma/                 BP_Alma
    │   ├── Pawn/                 pawn VR compartido
    │   ├── UI/                   BP_WristUI, WBP_Instruction, BP_FadeSphere
    │   └── FX/                   solo FX reusados por 2+ etapas
    ├── Stages/                   ← cada una plana, ordenada por prefijo
    │   ├── Inicio/  Centro/  Breath/  Heart/  Mind/  Touch/  Movement/  Salida/
    ├── Maps/
    │   ├── L_Persistent
    │   ├── Stages/               L_Inicio, L_Centro, L_Breath, L_Heart, L_Mind, L_Touch, L_Movement, L_Salida
    │   └── Tests/                L_Test_Breath, L_Test_Heart… (nunca referenciados por el flujo real)
    └── Developers/Beltran/       scratch. Oculta por defecto en el Content Browser.
```

### La regla que evita que `Core/` se vuelva un cajón de sastre
- Un asset **entra a `Core/` solo cuando una SEGUNDA etapa lo necesita.** Nada especulativo.
- `Core/` se subdivide **por sub-feature, no por tipo**.
- **Auditoría:** si algo en `Core/` lo referencia una sola etapa → no es core, vuelve a su etapa.
- **Desde el día 1 en `Core/UI/`:** el fade sphere y la UI de muñeca. Duplicarlos por etapa es el error más común en arquitecturas hub-and-spoke.

### Prefijos
Epic documenta **solo prefijos, no jerarquía de carpetas** (la jerarquía es convención comunitaria). **Epic y la guía de Allar se contradicen** en varios. Regla: **tabla oficial de Epic donde exista; comunidad donde Epic calla.**

| Tipo | Usamos | Nota |
|---|---|---|
| Blueprint | `BP_` | ambos coinciden |
| Blueprint Interface | `BI_` | Epic. (Allar dice `BPI_`, también muy común) |
| Struct | `F_` | Epic. (Allar dice `S_`) |
| Enum | `E_` | Epic |
| Static Mesh | `SM_` | Epic. (Allar dice `S_`, obsoleto) |
| Skeletal Mesh | `SK_` | |
| Material / Instance | `M_` / `MI_` | |
| Texture | `T_` | |
| Widget | `WBP_` | |
| Niagara System / Emitter | `FXS_` / `FXE_` | set específico de Niagara |
| Data Asset | `DA_` | Epic no lo cubre; estándar de facto |
| Data Table | `DT_` | |
| Level Sequence | `LS_` | |
| Level | `L_` | convención muy extendida |

**Gameplay Tags** no llevan prefijo: dot-strings en PascalCase → `Flow.Breath.SensorGrabbed`.

⚠ **Lyra usa sus propias letras** (`B_`, `W_`, `L_`). Es coherencia interna de Epic para ese proyecto, **no** una recomendación. No copiar.

### Reglas que evitan dolor
- **Nada suelto en `Content/`.** Todo bajo `SoulCharger/`.
- **Sin espacios ni caracteres especiales** en nombres ni carpetas (rompe rutas de cook/packaging).
- **Mover assets después cuesta:** Unreal deja *redirectors*. Click derecho → **Fix Up Redirectors in Folder** antes de cada commit. Por eso el árbol se fija **antes** de crear contenido.
- **`Developers/<nombre>/`** para experimentos; oculta por defecto (View Options → Show Developers Folder).
- **Migrate** copia un asset + dependencias a otro proyecto. Tener Alma / Ameba / Signals limpios en `Core/` hará indoloro reusarlos en otra obra.

### No copiar la estructura de Lyra
Lyra mete cada modo en un **plugin GameFeature** con su propio Content y Config. Resuelve problemas que no tenemos: modos hot-swappable, muchos equipos, live-service, límites de módulos C++. **Sobreingeniería para 8 etapas fijas y un dev.** Se copia el *principio* (etapa autocontenida + core mínimo), no el mecanismo.

## 11. Inventario: qué creamos

### Lo que ya existe
| Existe | Destino |
|---|---|
| **BP_XRPawn** (XRFramework) | Se queda. Es el hub de interacción. |
| **BP_OSCReceiver** | **Se refactoriza** → su lógica se muda al GameInstance / `Core/Signals`. |
| **Ball** | Fue el test. Se borra. |

> **El problema con el OSC:** hoy el servidor vive en un actor del nivel. Con streaming, si está en un sub-nivel **muere cuando la etapa se descarga**; y en standalone no existiría. **El `OSCServer` es un UObject, no un actor → se muda al GameInstance.** Sobrevive todo, cada etapa lo tiene gratis, no hay que colocar nada. *(A verificar: que el nodo `Assign` funcione en el grafo de un GameInstance.)*

### Tier 0 — Prerrequisitos (no son Blueprints)
1. **Instalar el Gameplay Message Router.** Preferir la **reimplementación MIT independiente** en GitHub antes que descargar Lyra entero solo por una carpeta. Hacerlo **ahora**: retrofitearlo significa recablear todos los listeners.
2. **Configurar los Gameplay Tags** del proyecto (`Flow.*`, `Signal.*`).
3. **Project Settings → Maps & Modes → Game Instance Class** → el nuestro.
4. **Fijar el árbol de carpetas** (§10) antes de crear nada.

### Tier 1 — La espina
| Archivo | Tipo | Para qué |
|---|---|---|
| **BP_SoulChargerGI** | GameInstance | El authority: `CurrentStage`, flags, retrato de datos, servidor OSC. |
| **F_Beat** | Struct | `BeatId` (GameplayTag) + nombre + etapa dueña. |
| **DA_FlowSequence** | Primary Data Asset | La lista ordenada de beats. **El único lugar donde se lee el flujo.** |
| **BI_Stage** | Blueprint Interface | `Activate` / `Deactivate` / `IsComplete`. |
| **BP_StageBase** | Actor (padre) | El esqueleto de 4 fases (§3) + boot check + emite el tag de completado. |
| **BP_FadeSphere** | Actor/Component | Esfera translúcida pegada a la cámara. **Sin esto no hay transición válida en VR.** |
| **BP_FlowDirector** | Actor (persistente) | Ejecuta las transiciones: precarga async → fade → visible + teleport → descarga diferida. |
| **L_Persistent** + **L_Test_Stage** | Niveles | Uno real y uno falso, solo para probar el streaming. |

### Tier 2 — Runtime compartido
| Archivo | Tipo | Para qué |
|---|---|---|
| **F_Signal** | Struct | `Value` (0-1) + `Confidence` + `Quality`. **La abstracción.** |
| **BP_SignalProvider** | Actor/Component (padre) | Base de toda fuente. |
| **BP_SignalProvider_Fake** | Hija | **Sliders y ondas seno. Permite construir las 5 etapas sin casco ni EEG.** |
| **BP_SignalProvider_OSC** | Hija | Heart y Mind desde el GameInstance. |
| **BP_SignalProvider_Breath** | Hija | Derivada del mando (quietud + fase). |
| **F_SoulPortrait** | Struct | El retrato acumulado. Vive en el GI. |
| **BP_SoulAmoeba** | Actor | Renderiza el retrato. Se reusa en hub, cargas y constelación. |
| **BP_Alma** | Actor | La guía. |
| **WBP_Instruction** | Widget | Gráfica + texto que pide una acción. |
| **BP_WristUI** | Actor/Component | El display de muñeca. |

### Deferido a propósito
Los 5 controllers de etapa, `BP_Portal`, la constelación, los bancos de sonido, `DA_AmoebaBank` — cuando haya algo que conectar.

## 12. Plan de construcción

### Grey-box
Cada nivel arranca **tonto a propósito**: **floor + skylight + PlayerStart. Sin fog, sin nada.** Toda la lógica vive en `BP_StageBase` por herencia — así duplicar niveles es seguro: un cambio de lógica se hace una vez, no ocho.
- **Una referencia de escala humana en cada nivel**, a **altura de ojos sentado**. Los errores de escala en VR son **invisibles en el monitor y brutales con el casco puesto**. Es lo que más caro sale descubrir tarde.
- **No estampar los 8 niveles todavía.** Primero el persistente + uno; probar el patrón; **después** duplicar.

### La experiencia es SEATED — implicaciones
- **Tracking origin a nivel de ojos, NO floor level.** El PlayerStart se posiciona a altura de ojos sentado. *(Confirmar el enum exacto en el editor.)*
- **La locomoción del XRFramework es peso muerto.** Teleport y snap turn no aplican sentado, y las etapas son estacionarias (el ascenso de Heart es la obra moviéndote, no locomoción del usuario). **Se elimina el NavMesh, `NavModifier_NoTeleport`, `IA_Move`, `IA_Turn` y `BP_TeleportVisualizer`.** Menos superficie que mantener.
- **Hace falta un recenter**: sentado, la orientación de la silla varía por usuario.
- **Envelope de alcance reducido:** los pedestales de Attracting y el dibujo de Movement deben caber en el alcance de brazos **sentado**. Afecta colocación y escala.

### Orden
1. **Tier 1 con una etapa falsa** (un cubo y un botón "listo"). Prueba la arquitectura completa sin arte, sin biofeedback, sin nada que confunda el diagnóstico. **Si el streaming hitchea o el fade deja el hueco estéreo, hay que saberlo ahora.**
2. **Tier 2**, empezando por `F_Signal` + `BP_SignalProvider_Fake` → construir y probar las 5 etapas en el editor, sin casco.
3. **Parámetros de umbral expuestos y editables en vivo + visualización de debug de la señal.** El threshold de respiración no se resuelve con arquitectura, se resuelve **testeando**; iterar debe costar minutos, no recompilaciones.
4. **Primera etapa real: Breath.** Mecánica clara, concepto ya validado, y obliga a resolver el threshold (la deuda técnica más vieja).
5. Las 4 etapas restantes, duplicando el template probado.
6. Recién entonces: materiales, iluminación, arte.

### Notas para el pipeline EEG (software externo)
- **TP9/TP10 son los canales malos** — un estudio de 2024 encontró señal no fisiológica en ellos **aunque el indicador de calidad del propio Muse decía que estaban bien**. AF7/AF8 son los buenos.
- **No confiar en el flag de calidad del Muse**: verificar forma espectral plausible (pendiente 1/f, bump de alfa en reposo).
- **Usar gamma/beta-alto como detector de artefacto (EMG), no como señal.** Si sube → rechazar la ventana.
- **Suavizado exponencial ~10s** + z-score contra el baseline personal.
- **Degradación elegante:** si TP9/TP10 vienen mal, caer a solo AF7/AF8 en vez de meter basura al Niagara.

---
# PARTE 3
---

## 13. Decisiones abiertas

1. **Entering:** 4/6 vs 5/5. → **Ahora hay datos.** Medido en el probe (16/07): la respiración natural del usuario da **inhalación ~6.5 s / exhalación ~4.7 s** (período ~11 s) — o sea, **más larga la inhalación**, al revés de lo que asume el 4/6. Dos consecuencias: (a) el 4/6 no describe cómo respira la gente relajada por defecto, hay que *enseñarlo*; (b) la mecánica ya construida convierte esto en decisión de diseño concreta: **`RiseTime`/`FallTime` del integrador SON el ritmo guiado**. Si se ponen en 4/6, llegar al máximo justo al terminar de inhalar significa ir en sincro, saturar = inhalaste de más, no llegar = de menos. **El cubo (después, la figura) pasa a ser el maestro del ritmo, sin UI ni números** — coherente con §2 ("la tarea es indirecta"). Hoy en 5/5 para testear.
2. **Calibración EEG:** 10-15s vs. estirarla a 60-90s mientras Alma habla.
3. **Proto-ameba en la UI:** dónde vive.
4. **Nombres de niveles:** por sentido (adoptado) vs. por etapa.
5. **Verificar:** que el nodo `Assign` del delegate OSC funcione en el grafo de un GameInstance.
