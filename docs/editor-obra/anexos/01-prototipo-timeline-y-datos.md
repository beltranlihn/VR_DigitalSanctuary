> Anexo de la auditoría del 2026-10-01 (informe: editor y modelo de datos del prototipo). Lo que manda es [PLAN-EDITOR-OBRA-2026-10-01.md](../PLAN-EDITOR-OBRA-2026-10-01.md); donde este anexo lo contradiga, gana el plan.

# Auditoría del editor y del modelo de datos del prototipo narrativo web

Base: `web/prototipo-narrativo/` (timeline.js 1189 líneas, guion.js 650, world.js 1597, index.html 352, ensayo.js 293), más la base del artifact (`timeline/main` v78, 7 respaldos, 116 audios), leída solo en modo lectura. Las cifras de ejecución salen de evaluar guion.js en Node con stubs, con un script que dejé en el scratchpad y no en el repo.

---

## 1. Modelo de datos

### 1.1 Estructura: actos → momentos → clips

**No es un archivo de datos: es código que se ejecuta.** `guion.js` llama a funciones que van registrando objetos en arrays globales: `ACTS, BEATS, CLIPS, GATES, BYUID` (timeline.js:24).

- `act(name)` crea `{name, beats[]}` (timeline.js:26).
- `beatTL(uid, title, desc, at, body)` crea el momento `{uid, title, desc, act, atSpec, clips[], idx, isBeat}`. Ejecuta `body()` con ese momento como "actual" (timeline.js:27-30).
- `clip(o)` toma el objeto libre del guion y le agrega `key, beat, uid = beat.uid + '/' + key, idx, atSpec, endSpec, label, dur` (timeline.js:31-37). Si la key se repite dentro del momento, le pone el sufijo `#2`, `#3`… según el orden de declaración (timeline.js:33).

**Conteo en ejecución:**

| | Cantidad |
|---|---|
| Actos | 10 |
| Momentos | 73 (en el código hay solo 52 llamadas a `beatTL`; el resto sale de bucles) |
| Clips | **592** (147 llamadas literales a `clip({`; el resto lo generan los ayudantes y los bucles) |
| Esperas (gates) | 10 |
| Pistas | 9 |
| Duración total | 1029,2 s (≈17:09). La intro todavía dice "~14 min" (index.html:334) |

Clips por pista: fx 180, obj 135, world 84, vo 70, hap 59, int 34, ui 12, amb 11, pawn 7.

Clips por acto: Arranque 3 · Inicio 47 · Hall 92 · Llegada 6 · Entering 70 · Recognizing 69 · Loving 74 · Attracting 78 · Surrounding 42 · Final 111.

### 1.2 Tipos de clip

No existe un campo `type`. El "tipo" sale de la pista más de qué funciones trae el objeto:

| Ayudante | Qué crea | Fuente |
|---|---|---|
| `vo(key, text, at, o)` | track `vo`. `dur = voDur(text)` | timeline.js:38 |
| `fx(id…)`, `hap(id…)`, `amb(id…)` | marcas de sonido, háptica o música. `key = id` | timeline.js:39-41 |
| `walk(...)` | track `pawn` con `apply` que mueve el rig. **Agrega solo un `FX_WALK`** | timeline.js:42-49 |
| `gate(key, label, expected, fw, g, at)` | track `int` con `gate: {fw, tick, visual, onUser, onFire, sounds}` | timeline.js:50 |
| `ghostSpan(...)` | track `ui` (fantasma más instrucción). **Agrega `FX_GHOSTAPPEAR/OUT`** | timeline.js:51-55 |
| `teleport(...)`, `toHudClip(...)` | macros de guion.js: 4 clips `obj` más fx y hap | guion.js:44-80 |
| `veilBeat`, `almaBeat`, `closingBeats`, `chargeBeat` | plantillas que generan momentos enteros por etapa | guion.js:284-353 |

Campos que puede tener un clip (todos opcionales menos `key` y `track`):

- **Datos:** `label, text, id, note, dur, at, end, vfx, color, hint, ghost`.
- **Banderas:** `gate` (10), `help` (6), `simOnly` (2), `when` (16).
- **Funciones:** `apply(k, local)` (220), `during` (18), `fire` (1), `onStart` (12), `onEnd`, `reset` (2).

274 clips son instantáneos (dur 0, rombo en la UI). El comportamiento visible de 220 clips vive en closures `apply` que tocan el mundo directamente. **Ninguno de esos comportamientos es editable desde la UI.**

### 1.3 Anclas y cómo se resuelve el tiempo

`at` puede ser:

- un número: segundos desde el inicio del momento;
- `['KEY','end'|'start', off]`: un clip del mismo momento;
- `['1.4/WALK1']`: un clip de otro momento;
- `['1.4','start',19]`: otro momento.

Eso lo resuelven `refNode`/`parseAt` (timeline.js:58-66). `end` hace que un clip dure hasta un ancla; hay 22 clips así, con la bandera `crossSpan` si cruzan de momento (timeline.js:73-74). Un momento sin `at` va encadenado al fin del anterior (timeline.js:69); 23 de 73 tienen un `at` explícito. `resolveAll` arma el árbol de dependencias `kids` (timeline.js:78-80).

Cálculo de tiempos (timeline.js:89-146), memoizado y con detección de ciclos:

- `tStart(n) = tAnchor(effAt(n)) + EDITS[uid].d`. `effAt` prefiere el re-anclado que guardó el usuario (timeline.js:89).
- `tDur(c)` usa la primera fuente que exista, en este orden (timeline.js:101-110):
  1. `CUT` (voz cortada en vivo);
  2. ancla `end`;
  3. duración viva de la espera;
  4. `expectedDur`: duración del audio real (+0,3 s en VO), si no la editada, si no `voDur(texto editado)`, si no `c.dur`.
- `tEnd(beat)` es el máximo del fin de sus clips, **sin contar amb, fx, crossSpan ni help** (timeline.js:115).
- Después viene el **warp de locators**: tiempo base → tiempo final, lineal por tramos con escala `k` por parte (timeline.js:122-131). Los clips con audio real conservan su duración (`keepsDur`, timeline.js:132, 140).
- `ORDER` es CLIPS ordenado por `s`, y `TOTAL` es el máximo fin de momento (timeline.js:143-144).

Ejemplos literales:

```js
// guion.js:365 — dura hasta el inicio de otro momento
clip({ key: 'BIO', track: 'obj', label: '…', at: 0, end: ['2.R4', 'start'], during: () => W.sensorKind = 'bio' });
// guion.js:369-371 — espera (6 s esperados, cortafuegos 25) + ayuda condicional
gate('G_BREATH', 'Espera: sensor al estómago', 6, 25, { tick: () => S.down });
vo('VO_11h', 'Just below your ribs… flat side toward you.', ['G_BREATH', 'start', 12], { help: 'G_BREATH' });
// guion.js:589-590 — rama
vo('VO_36c', 'Thank you. Let it go…', .2, { when: yes });
vo('VO_36d', 'That\'s alright. What you lived here stays with you.', .2, { when: no });
```

### 1.4 Esperas, cortafuegos, ayudas y ramas

**Modo simulado.** La espera dura `expected` (o el `dur` editado).

**Modo en vivo.** `tickGates` mira `gate.tick()` en cada cuadro (timeline.js:314-326):

- si el usuario cumple, la espera se resuelve como `usuario`;
- si se pasa del cortafuegos `fw × k`, se resuelve como `cortafuegos`;
- si se pasa del tiempo esperado, la espera se alarga cuadro a cuadro (`g.dur = local/kk`) y **todo lo que sigue se corre en tiempo real**.

Además:

- Si el usuario actúa antes de que Alma termine, `cutPlayingVoices` corta la voz con un fundido de 0,5 s y adelanta lo que sigue (timeline.js:330-337).
- El botón "Resolver espera" llama a `resolveHeldGate` (timeline.js:338).
- `help` actúa solo si arranca antes de que termine su espera (`helpActive`, timeline.js:147).
- `simOnly` se salta en vivo (timeline.js:291).

**Ramas.** `when` es un predicado que se evalúa por cuadro: el clip existe en la línea, pero no actúa (timeline.js:293). No hay líneas de tiempo alternativas: **las dos ramas ocupan el mismo horario** y el fin del momento es el de la rama más larga (timeline.js:115 no excluye `when`). Con DON'T SHARE, 9.6 igual espera los 8,2 s de FISH_DOOR/FISH_AWAY de la rama SHARE.

### 1.5 Locators, estética y audio

- **Locators.** Cada uno es `{id, name, ref: uid de momento, off, k}`. Por defecto hay uno por acto (timeline.js:123). Arrastrarlo cambia `k`, la escala de la parte anterior (timeline.js:669-670).
- **Estética (`LOOK`).** Es `{intro|hall|st0..st4: {param: valor}}`, con un esquema declarativo `LOOK_PARAMS` (timeline.js:218-223). Es estática por parte, no se puede animar en el tiempo. **Pisa los colores de velo que trae `ensayo.js` desde Unreal** (timeline.js:241 contra ensayo.js:287).
- **Audio por ID.** `soundIdOf` da `key` sin `#n` para VO y `id` para FX/AMB (timeline.js:353). El archivo va empaquetado como JSON `sc-audio-v1` en base64, convertido a WAV mono si pasa de 14,5 MB (timeline.js:433-437), y se guarda en `audio/<ID>` (timeline.js:450). `audioFor` cae al ID sin sufijo `_\d+`: así `FX_CHARGE` sirve para `FX_CHARGE_1..5` (timeline.js:354). Un mismo archivo vale para todos los clips de ese ID.

---

## 2. Pistas

Hay **9 pistas fijas, por tipo de medio**, hardcodeadas en `TRACKS` (timeline.js:11-21): Voz de Alma, Sonido, Música, Háptica, Pawn, Mundo, Objetos, Instrucción, Interacción. Cada una tiene su color CSS (index.html:18-26). La pista viene del campo `track` en el código y **no se puede cambiar desde la UI**.

Encima de las pistas hay tres filas fijas: Locators, Actos y Momentos (timeline.js:562-569).

**Sub-carriles: hoy son automáticos y no persisten.** `computeLanes` reparte los clips de cada pista con un algoritmo voraz por extensión en píxeles. Para los instantáneos esa extensión incluye **el ancho de la etiqueta** (timeline.js:591-607). Tres consecuencias:

1. El carril depende del zoom: cambiar `pxs` cambia el reparto.
2. Durante un arrastre los carriles se congelan (`lanesFrozen`, timeline.js:731), pero al soltar se recalculan (timeline.js:739-740 → `layout`). **El clip que moviste salta de carril.**
3. No hay superposición visual, pero tampoco hay control: no se puede crear, nombrar, fijar, bloquear ni silenciar un carril.

**Agrupación.** Se agrupa por tipo de medio, no por sujeto. "Objetos" mezcla 135 clips de Alma, anillo, sensor, timbre, HUD, alma-pez y resultados. "Mundo" mezcla 84 de niebla, velos, títulos, puertas y créditos. **Un editor de cine espera pistas por sujeto o capa, por ejemplo "Alma", "Anillo", "Puerta Este" o "Velo", con sub-pistas propias.** Eso es justo lo que pediste ("crear pistas en cada grupo").

---

## 3. Funciones que el editor ya tiene

**Mover y recortar**
- Arrastrar un clip o un momento: se mueve con su **familia** (todo lo anclado a él), con imán de 8 px al cabezal y a los bordes de los clips de momentos anteriores (timeline.js:710-742).
- Recortar solo el borde derecho (`.rz`). No existe para amb ni para spans, y queda oculto en VO/FX con audio (timeline.js:574; index.html:145). **No hay recorte del borde izquierdo, ni slip, ni ripple explícito.**
- Flechas: mueven el clip seleccionado 0,1 s (o 1 s con Shift); sin selección, mueven el cabezal (timeline.js:1153-1156).

**Anclas**
- El inspector tiene un select "Anclado a", **limitado a los clips del mismo momento** más el ancla actual (timeline.js:772-780). Re-anclar recalcula `off` para que el clip no se mueva (timeline.js:878-882).
- Curvas SVG muestran el padre y los hijos del clip seleccionado (timeline.js:698-705).

**Transporte**
- Play/pausa con Espacio, que se captura antes que nadie (timeline.js:1141).
- Velocidad 1/2/4/8×, sin reversa (timeline.js:1094).
- Scrub sobre la regla (timeline.js:758-760), doble clic para ir al inicio de un clip (timeline.js:744), Home/End.
- Mini-pista de actos para saltar (timeline.js:682-685).

**Vista**
- Zoom con Ctrl o Alt más rueda, centrado en el mouse; botones +, − y Ver todo (timeline.js:762-769).
- Paneo con el botón del medio (timeline.js:749-755). Seguir el cabezal. Alto del panel arrastrable (timeline.js:1134-1136).

**Inspector**
- Inicio, duración (o tiempo esperado en las esperas) y cortafuegos.
- Texto de Alma (textarea; Ctrl+Enter guarda).
- Bloque de audio: cargar, reemplazar, quitar, escuchar, fundidos de entrada y salida.
- "Sonidos de esta interacción" (`gate.sounds`).
- Volver al original.
- Panel de locator: nombre, %, borrar (timeline.js:813-887).

**Locators**
- Agregar con M o con "+", arrastrar para estirar, doble clic para renombrar, Supr para borrar (timeline.js:655-676, 1160-1161).

**Audio**
- Soltar archivos en la ventana: se asignan por nombre, con limpieza de sufijos como `_V2`, `_FINAL` o `(1)` (timeline.js:481-486).
- Soltar un archivo sobre un clip lo asigna a ese clip.
- Botón "Audios" para cargar varios.
- Crossfade automático entre VO que se pisan y entre ambientes (timeline.js:369-377, 404-408).
- Modos de voz texto, audio o ambos, y voz sintética.

**Estética**
- Panel por parte que sigue al cabezal (timeline.js:246-273).
- Sliders de "Animaciones" (`S.tw`, timeline.js:1165-1168). **Estos no se guardan.**

**Exportar e importar**
- JSON de edits más tabla de momentos (timeline.js:953-963).

**Persistencia**
- Las ediciones se guardan como capa sobre el guion: `EDITS[uid] = {d, dur, fw, at:{ref,edge,off}, text, fin, fout}` (timeline.js:84).
- localStorage `sc-timeline-v1` al instante, más `timeline/main` con debounce de 1,2 s y flush al ocultar o cerrar la pestaña (timeline.js:905-950).
- Respaldo `timeline/bk-AAAAMMDDhhmm` antes del primer cambio de cada sesión (timeline.js:914-917).
- Huérfanos: ajustes de uids que ya no existen, que se conservan y se vuelven a guardar (timeline.js:897-898).
- `plan` resumido para que lo lea Claude (timeline.js:899-903).
- Al cargar, gana el más nuevo entre local y base, por `savedAt` (timeline.js:939).
- Deshacer: 120 snapshots completos de `{EDITS, LOCS}`. **No cubre `LOOK` ni audio** (timeline.js:543-549).

**Lo que Beltrán ajustó de verdad** (`timeline/main` v78):

- **17 edits** (10 `d`, 11 `dur`), **todos en los actos 0 y 1** (los primeros ~2 min).
- 0 textos, 0 re-anclados, 0 cortafuegos, 0 fundidos.
- 9 locators, todos en k = 1.
- Estética: solo `intro.fogTop/fogHor`.
- 116 audios (32,7 MB, ~33 min).

**4 de esos 17 edits no tienen efecto:**

- `1.1/AMB_01`, `1.4/AMB_02` y `1.10/AMB_03` tienen `dur`, pero el ancho del ambiente lo da `ambEnd` (timeline.js:556, 628) y el loop de audio lo ignora (timeline.js:404-408).
- `1.4/VO_01c` tiene `dur`, pero el audio real manda (timeline.js:101).

El inspector deja editar esos campos sin avisar.

---

## 4. Acoplamiento con world.js

- **Un solo ámbito global.** Los scripts clásicos se cargan en este orden: world → ensayo → timeline → guion (index.html:349-352). Comparten un único ámbito global: world.js declara ~200 nombres de primer nivel y `S` es el estado global mutable (world.js:32-40).
- **Contrato principal: `W`, "el estado deseado del mundo".**
  - `resetW()` deja ~70 campos en cero (timeline.js:151-158) y `baseWorld()` reinicia a mano una parte de los objetos three.js (timeline.js:159-170).
  - `evaluate(t)` recorre `ORDER` y llama `apply(k, local)` en cada clip que ya empezó. Los clips terminados siguen aplicando con k = 1 (timeline.js:286-311).
  - `applyW()` traduce `W` a three.js (timeline.js:171-209).
- **El estado solo es función de t a medias.** Muchos `apply` mutan la escena directamente: `bell.visible`, `container.position`, `hallU.uLight`, `rigTo()` en TELEPORT (guion.js:538), uniforms de niebla (guion.js:612). Lo que `baseWorld` no reinicia, más el estado de interacción (`S.share`, `S.carry`, `S.data.strokes`, `S.melody`), **no se rebobina** al hacer seek hacia atrás. Solo dos clips tienen `reset`.
- **Disparos de una vez.** `fireStart` corre al cruzar el inicio de un clip en play: llama `cue()`, `startVoice` y `setAmbient` (timeline.js:277-285). `fire` y `onEnd` cuelgan del mismo cruce (timeline.js:303-307).
- **Dependencia circular.** world.js llama de vuelta a timeline.js con `typeof playSoundId === 'function'` (world.js:148) y `audioFor` (world.js:826).
- **timeline.js también hospeda la simulación del mundo.** `frame()` incluye respiración, EEG, calma, HUD, pacer, SAVE, cámara y mano del mouse (timeline.js:983-1081). Además, cada `apply` de guion.js referencia directamente posiciones y objetos de world.js.
- **No hay API ni eventos.** El único "API" es `window.SC`, que solo existe con `?debug` (timeline.js:1188).

---

## 5. Problemas

### 5.1 UX, pensando en un editor de cine

1. **No se puede crear, borrar, duplicar ni cambiar de pista un elemento.** Todo nuevo FX, sonido o aparición exige editar guion.js. Para tu socio, el editor solo **re-temporiza** lo que ya existe.
2. **Los carriles saltan** después de cada arrastre y con el zoom (§2). Las pistas no se pueden crear, nombrar, bloquear, ocultar, silenciar ni aislar (solo).
3. **La familia es implícita.** Mover un clip arrastra a todos sus anclados sin que se vea hasta seleccionarlo. No hay un "link/unlink" explícito ni un modo ripple, insert u overwrite con nombre.
4. **El anclado solo se ofrece dentro del mismo momento** (timeline.js:772-780).
5. **Tiempo en m:ss.s.** No hay timecode ni cuadros, ni rango In/Out, ni loop, ni shuttle JKL, ni reversa. Las flechas cambian de significado según haya selección o no (timeline.js:1153-1156), lo que facilita mover un clip sin querer.
6. **No se ve la forma de onda.** Un audio es solo una línea de cola (`.tail`, index.html:146). Tampoco hay miniaturas ni marcadores con comentarios.
7. **Las ramas no se distinguen.** No existe la clase `when` (timeline.js:573), así que SHARE y DON'T SHARE se dibujan mezcladas.
8. **Campos que no hacen nada** (dur de amb, dur de VO con audio) y duraciones que no escalan el comportamiento interno. El `apply` lleva tiempos fijos:
   - DISCLAIMER usa `k*20` (guion.js:87);
   - PACER usa `local % 14` y 70 s (guion.js:381-384);
   - FISH_IDLE usa `dur: 26` adentro (guion.js:554);
   - teleport usa fracciones fijas.
   
   Al estirar el clip, la animación no lo sigue.
9. **En vivo, toda la línea se desliza cuadro a cuadro** mientras una espera está retenida.
10. **Estética fuera del tiempo.** Es un panel flotante aparte (index.html:254), sin keyframes. "Animaciones" (`S.tw`) se pierde al recargar.
11. **Diálogos nativos** `prompt`, `confirm` y `alert` (timeline.js:674, 810, 962, 1111). El inspector desaparece por debajo de 860 px (index.html:234).
12. **Las dos pestañas hoy no son posibles.** No hay sincronización del transporte entre pestañas ni `onSnapshot` de `timeline/main` (solo de `audio`, timeline.js:515). Dos pestañas serían dos reproductores independientes que se pisan al guardar (§5.3).

### 5.2 Arquitectura y código

- **timeline.js tiene al menos 8 responsabilidades:** registro, scheduler, evaluador, simulación por cuadro del mundo, audio (WebAudio, assets, DB), editor DOM, inspector, persistencia y controles. Líneas de cientos de caracteres; no hay módulos, tipos ni tests.
- **La lógica de la obra es código con closures** sobre variables internas de world.js. No se puede serializar, ni editar desde la UI, ni pasar a Unreal. El comentario de world.js:2 menciona un `engine.js` que no existe.
- **Rendimiento.** Hoy alcanza; con el doble o el triple de clips empezará a trabarse (y el modo nodos los multiplicará):
  - `evaluate` es O(n) por cuadro sobre 592 clips.
  - `computeSchedule` más `place()` reescriben 592 divs en cada `pointermove`.
  - `placeLocs` y `buildRuler` reconstruyen el DOM con `innerHTML` en cada layout.
  - Durante una espera retenida, `computeSchedule` corre en cada cuadro.
- **No se puede separar en dos procesos:** el horario solo se calcula dentro de la página con three.js. Igual, que mi script haya contado todo en Node con stubs prueba que el registro sí se puede extraer.

### 5.3 Datos

- **Las keys son frágiles.** `uid = momento/key`, y 45 uids llevan `#n` según el orden de declaración (por ejemplo `1.R6/HAP_PULSE_STRONG#3`). Si insertas un clip igual antes, los ajustes guardados pasan al clip equivocado sin aviso. Renombrar una key o un momento deja huérfanos. El README lo advierte (README.md:11), pero no lo resuelve.
- **IDs generados en código** (`'FX_CHARGE_' + (n+1)`, `'VO_06' + 'bcdef'[i]`, `FX_ORB_*`). Un grep no los encuentra. Hay audios huérfanos reales en la base: `VO_35a` y `FX_ORBHOVEROUT`.
- **Varias fuentes de verdad para lo mismo:**
  - la estructura y los comportamientos (guion.js);
  - la capa EDITS (base y localStorage);
  - las constantes de world.js (`STAGES`, `CHARGE_T`);
  - ensayo.js, generado desde Unreal, que pisa `STAGES.top/hor` y `CHARGE_T` (ensayo.js:287);
  - `LOOK`, que a su vez pisa el velo de ensayo (timeline.js:241).
  
  **El timing editado nunca vuelve a Unreal.** Solo existe `plan` como resumen de lectura. La dirección Unreal → web cubre posiciones y unos pocos tiempos por etapa, como deltas.
- **Las unidades dependen de los locators.** `d` se guarda en tiempo base dividido por `k` (timeline.js:736, 864): el mismo número significa otra cosa si cambias un locator. Los nombres de los locators se copian a la base y no siguen al acto.
- **La concurrencia es último-gana.** `db.doc('timeline/main').set(...)` reemplaza el documento entero sin `if_version` (timeline.js:920), y al cargar se elige por `savedAt` (timeline.js:939). Si Beltrán y su socio editan a la vez, uno borra el trabajo del otro.
- **Deshacer no cubre la estética.** "Restablecer" tampoco toca `LOOK` (timeline.js:1111).

---

## 6. Qué se reusa y qué conviene reescribir

| Pieza | Decisión | Por qué |
|---|---|---|
| Semántica de anclas (ref/edge/off, `end`, encadenado de momentos) y resolución memoizada con detección de ciclos (timeline.js:89-118) | **Reusar el concepto, reescribir como módulo puro** sobre datos tipados | Es lo más valioso: "lo que se dispara junto se mueve junto". Encaja con el modo nodos (un ancla es una arista). Hay que sacarla del DOM y de las globales. |
| Esperas (expected + cortafuegos + en vivo/simulada), ayudas, `simOnly`, corte de voz | **Reusar la semántica** | Ya modelan "cero callejones sin salida" y el tiempo del usuario. `tick/visual/onUser` pasan a ser **tipos de interacción con ID y parámetros**, sin closures. |
| Ramas `when` | **Rediseñar** | Hoy son máscaras sobre un horario único. Necesitan ser ramas reales, con su propia duración, en la capa de nodos. |
| Warp de locators (timeline.js:122-131) | **Reusar** | "Estirar o comprimir una parte" es una operación natural de montaje. Conviene guardar los tiempos ya resueltos, no en base/k. |
| Pipeline de audio (asignar por nombre, empaquetar, `audio/<ID>`, onSnapshot, envolventes y crossfades) | **Reusar casi tal cual**, aislado como módulo | Funciona y ya tiene 116 audios cargados. Falta agregar forma de onda. |
| Seguridad de persistencia (local primero, debounce, respaldos, huérfanos, `plan`) | **Reusar las ideas; reescribir la escritura** | Hace falta pasar a documentos por entidad o parches con `if_version`, `onSnapshot` de la obra y un canal entre pestañas (BroadcastChannel) para cabezal y selección. Es la condición para las dos pestañas y los dos editores. |
| Inspector por esquema (el patrón de `LOOK_PARAMS`) | **Reusar el patrón** y generalizarlo a todos los tipos | Los parámetros de cada comportamiento quedan editables y legibles. |
| Vocabulario visual (rayado de espera, marca roja de cortafuegos, ayuda punteada, rombo instantáneo, triángulos de fundido, curvas de familia) | **Reusar** | Ya es legible y elegante. Se lleva al nuevo componente. |
| Editor DOM (`buildEditor/place/computeLanes`, inspector con innerHTML, teclado) | **Reescribir** | Carriles no persistentes, sin crear/borrar/cambiar de pista, sin recorte izquierdo ni multiselección, rendimiento O(n) en DOM. Hace falta un componente de pistas con **grupos por sujeto → sub-pistas fijas creadas por el usuario**, canvas o DOM virtualizado. |
| Contenido de guion.js (73 momentos, 592 clips, labels, textos, anclas) | **Migrar, no reescribir a mano** | Se puede extraer con un evaluador con stubs (ya funciona) a un JSON con IDs estables (ULID) separados de la key visible. Los `apply` se catalogan en ~25-30 comportamientos con parámetros (aparecer/desaparecer, mover entre puntos, velo, título, teleport, carga…). Los tiempos internos fijos (`k*20`, `%14`, `dur 26`) pasan a ser parámetros. |
| Evaluador `W`/`applyW` y `frame()` | **Reescribir separando** | El horario y la evaluación van en un núcleo sin render (sirve para la pestaña de timeline y para exportar a Unreal). La simulación por cuadro y `applyW` vuelven a world.js, detrás de una interfaz `world.apply(state)`. Eso además resuelve la dependencia circular. |
| Capa EDITS sobre código | **Eliminar** | Con el guion como datos, el documento es la obra. Desaparecen las keys `#n`, los huérfanos y las tres fuentes de verdad. Es el requisito para que web y Unreal lean el mismo archivo. |