> Anexo de la auditoría del 2026-10-01 (crítica adversaria de las dos propuestas). Lo que manda es [PLAN-EDITOR-OBRA-2026-10-01.md](../PLAN-EDITOR-OBRA-2026-10-01.md); donde este anexo lo contradiga, gana el plan.

# Crítica adversaria: editor de gameplay y narrativa (arquitectura y UX)

Rutas: `VR/` = `C:/Users/beltr/Desktop/Alma Digital Studio/Projects/VR Unreal/`; `ISP/` = `C:/Users/beltr/Desktop/Alma Digital Studio/Projects/Immersive Studio Pro/`; `WEB/` = `VR/web/prototipo-narrativo/`.

Verifiqué en el código las citas de ISP que usan las propuestas, y están bien: tokens en `ISP/index.html:28-83`, `.prow .lab` de 60 px en `:327`, `.trackhdr` de 168 px en `:419`, `#mediaPane` de 292 px en `:1227`, `#inspPane` de 300 px en `:1338`, `LANE_DEF_H`/`LANE_MIN_H`/`LANE_COLLAPSED_H` = 57/26/24 en `app.js:188`, `CLIP_HUE` en `:100`, `renderTimeline` en `:5452`, `cutOverlapsOnDrop` en `:7409` y `c.lane===li` en `:5479`. Los problemas son de fondo.

---

## 1. Errores de hecho

1. **"AndroidFileServer está activo en el `.uproject`".** Es falso: `VR/VR_Test/VR_Test.uproject:33-34` tiene `"Enabled": false`. El override en caliente de F6 depende de activar un plugin en configuración compartida, y la ruta escribible en el Quest sigue sin verificar.

2. **"El patrón de ISP es un solo realm: el `WebGLRenderer` se crea sobre un canvas de la emergente".** ISP no hace eso:
   - La emergente tiene un canvas **2D** (`ISP/app.js:2517`, `getContext('2d')`).
   - `viewerPaint` redimensiona el canvas GL principal al tamaño de la emergente, renderiza, copia con `drawImage(glc)` (`:2612-2616`), lo devuelve a su tamaño y vuelve a renderizar el editor.
   - Está pensado para repintar video solo cuando algo cambia. Con una escena three que anima a 60 fps serían 2 renders y 2 realocaciones del drawing buffer por cuadro.
   - Lo que propone la arquitectura es un patrón nuevo y sin probar, que además correría dentro de un iframe con sandbox.
   - Aparte, `ISP/docs/adr/adr-0009` trata del splash y no del visor, así que no sirve de precedente.

3. **"Escribir con condición de versión (hay que verificar qué ofrece el db)".** Ya está verificado y no lo ofrece. El contrato `db` 0.2.66 dice literalmente "Writes are last-writer-wins; there are no transactions". Lo que sí existe:
   - `acquire` (un lease de 1 a 600 s, sin verbo para soltarlo);
   - un máximo de **256 KiB por documento**;
   - un máximo de **64 suscripciones por vista**.

   Consecuencias para el diseño:
   - Las "versiones con nombre como snapshot completo" no caben en un documento: tienen que guardarse como asset JSON.
   - La presencia por latido en `db` gasta la cuota de llamadas. La capacidad `room` resuelve presencia y transporte, y trata dos pestañas de la misma persona como dos peers (`isMe && !sameTab`). Ninguna de las dos propuestas la considera.
   - El bloqueo suave se resuelve con `acquire`.

4. **"Beltrán reimporta solo, sin Claude y sin cola".** Esto contradice la misma regla de la arquitectura: "Unreal importa desde `obra/score/` en el repo, nunca desde la base". Pasar de la base al repo y correr `compile.mjs` requiere una sesión o Node. La frase solo es cierta si el editor compila en el navegador y entrega `score_unreal.json` con la capacidad `downloads`.

5. **Prueba dorada "±1 ms contra `computeSchedule`".** El horario depende de la duración real de cada audio + 0,3 s y de `S.voMode` (`WEB/timeline.js:101-103`, `:132`). En Node, sin audios, sale otro horario. El fixture tiene que leer `audio/*.dur` de la base. Y aun así compara contra los audios de la base, no contra la mezcla final (`VR/VR_Test/Saved/ClaudeScripts/vo_final/duraciones_mezcla.txt`).

6. **La UX dice agrupar "por sujeto, no por tipo de medio"**, pero su tabla agrupa casi todo por medio (Narrativa = VO, Sonido, Música, Háptica, FX visuales). Solo Objetos va por sujeto.

7. **"Ctrl+T = nueva sub-pista (el ⌘T de `addLane`)".** Funciona en ISP porque es Electron (`ISP/app.js:16552`). En Chrome, Ctrl+T, Ctrl+W y Ctrl+N no se pueden interceptar. Ctrl+R, Ctrl+D y Ctrl+Shift+S chocan con el navegador y con claude.ai, así que hay que probarlos en el iframe real.

8. **Voseo en la UX** ("lo que movés se queda…"). Va contra la regla de la casa.

---

## 2. Choques con restricciones

1. **`ScoreApply()` pisa la instancia en tiempo de ejecución.** Es el choque más grave. Contradice "manda la instancia" (memorias `no-pisar-valores-del-editor`, `valores-de-test-son-finales` y `beltran-autora-mirando`: "un solo lugar donde autorar cada cosa").
   - Caso concreto: Beltrán cambia en Detalles una perilla de la categoría "Partitura", da Play y no pasa nada. La tabla manda hasta la próxima cosecha.
   - **Mitigación:** una reconciliación de tres vías por perilla. `ScoreApply` escribe solo si el valor de la instancia es igual al de la última importación. Si no coincide, gana la instancia y se registra `SCORE|diverge|<perilla>`.

2. **"Probar desde aquí" escribe `DebugStart` y "lo pone en la cola".**
   - `DebugStart` es una palanca de Beltrán (memoria `no-tocar-flags-debug`; la Obra quedó en 3 por pedido suyo, `TRK/BP_Obra_SC.md:347`).
   - "La cola" es un protocolo entre sesiones por SendMessage a Narrativa: la web no tiene ese canal.
   - **Mitigación:** una variable aparte, `ProbeStart`, que gana si es ≥ 0 y nunca se guarda en el nivel. La web solo copia la orden; no "encola".

3. **La acción "Mostrar u ocultar un rol"** choca con la regla del 10-01: "cargar por etapa, no cargar y esconder". El vocabulario tiene que ser Spawn/Destroy o carga de subnivel, respetando "nada arranca en el cuadro en que se enciende una celda".

4. **"Una aparición por cuadro, encolando las demás"** cambia tiempos. Entonces la traza no puede ser idéntica, y el criterio "una traza que difiere detiene la fase" se rompe solo. Hace falta una tolerancia explícita, por ejemplo ±1 cuadro.

5. **U5 (los runners leen las mismas perillas)** cambia a propósito uno de los dos títulos aprobados: el del runner (1→5,5 s) o el de la Obra (0,5→1,8 s). Es una decisión de autor, no una fase técnica.

6. **Observar con `Tick` pierde flancos.** `FinalFlow` corre unas 1,5 veces por cuadro (`TRK/BP_Obra_SC.md:207`), así que hay fases que duran 0 cuadros. Además, `GATE.late` y `VO.end` no existen como estado en Unreal.
   - **Mitigación:** que la Obra emita sus marcas por un dispatcher `OnMark(Name)`, con cirugía de un nodo por transición. El director sigue sin conocer al player.

7. **Binarios y editor ocupado.** U2 agrega unas 30 variables a `BP_Obra_SC` (gotcha 402), y ese binario es justo el que Narrativa edita a diario (fantasmas y manos el 10-01). Hace falta una ventana acordada con Narrativa y una sola tanda.

8. **Sostenible por una sesión: no lo es.** Cada comportamiento del catálogo exige seis cosas: implementación web, acción en `BP_ScorePlayer_SC`, mapeo en la cosecha, validador, migración y shim. A eso se suma el fork de ISP, que se mueve rápido:
   - 84 commits desde el 15-09;
   - `app.js` tiene hoy 19 504 líneas, mientras `ESTRUCTURA-DEL-CODIGO.md:31` todavía dice 14 499.

   Narrativa ya integra a mano cada mesh e interacción ("el prototipo sigue a Unreal", `WEB/README.md`).

9. **Usuario editor de cine.** El P0 de la UX le muestra de entrada: esperado, ayuda, cortafuegos, persona, ramas, anclas, origen del valor y candado. Primero necesita mover, recortar, escuchar y anotar.

---

## 3. Incoherencias entre arquitectura y UX

| Tema | Arquitectura | UX |
|---|---|---|
| Dos vistas | Emergente, un solo realm, un solo audio (§4.1) | "Canal entre pestañas en lugar de `window.open`": dos realms, `world.js` y 3,9 MB de GLB cargados dos veces |
| Deshacer | "No se copia `pushUndo`/`snapshot`": deshacer por comandos | Atajos y tabla: "`pushUndo`/`snapshot` ampliados" |
| Solape al soltar | Se **rechaza** | Va a la primera sub-pista libre o a una nueva. Beltrán pidió que "se quede en su sub-pista" |
| Sub-pista | Solo dice "dónde se dibuja"; nunca cambia el comportamiento | Sub-pistas con significado: Omnipresente, Mano dominante/La otra, AMB A/B, Estado de Alma "en mosaico" (restricción sin huecos) |
| Fases | Persona en F5; diff de Unreal, candado y origen del valor en F3 | Todo eso en **P0** |
| Cian | "Vivo, arrastrable **o enlazado a Unreal**" | "Lo decide el usuario o llega en vivo" |
| Color de grupo | `LANE_COL` gris/verde/rojo (`app.js:88`) | 11 tonos de `CLIP_HUE` más el tinte de audio |

Además, la UX pone las Notas en dos lugares a la vez: una pestaña de la Biblioteca y otra del Inspector.

Ninguna de las dos define qué pasa cuando, al arrastrar una familia (el comportamiento por defecto en la UX), un hijo choca en su propia sub-pista de otro grupo.

---

## 4. Sobreingeniería y MVP

**Se puede posponer:**
- cajón Lógica y nodos;
- lista de cues;
- linter;
- ramas en pestañas;
- OSC, puente local, override JSON y Remote Control;
- JSON Schema compartido con Python y `tsc`;
- versiones con diff visual;
- presencia y bloqueo;
- dos ventanas y monitor flotante;
- gizmo, cámaras Planta/Libre y Rayos X;
- el refactor `world.apply(W)` de las 51 mutaciones.

**F1 no debe esperar a `world.apply(W)`.** El shim `legacy` puede ejecutar los 592 closures tal como están.

**La versión más chica que ya le sirve al socio:**
1. F0 tal como está propuesto: extracción a partitura con IDs estables, shim `legacy` y prueba dorada con fixture de audio. Vale la pena porque Narrativa toca `guion.js` a diario y los uid `#n` ya son frágiles.
2. **CSS y chrome de ISP copiados enteros:** tokens, `.top`, `.seg`/`.well`, menús, diálogos, paleta y barra de estado.
3. **Un timeline propio y chico escrito sobre las clases de ISP**, no el `renderTimeline` trasplantado (ver R3):
   - grupos y sub-pistas persistentes;
   - mover y recortar con imán;
   - rechazo de solape;
   - zoom y regla.
4. **Inspector de ISP** con solo Tiempo, Voz y Espera, que es lo que el socio edita hoy.
5. **Columna Unreal de solo lectura.** No necesita el editor compartido: sale de `duraciones_mezcla.txt` más un snapshot de instancias. Las divergencias van en ámbar, y cada elemento lleva una insignia "llega a Unreal / solo previs".
6. **Notas** en `notes/*`, guardando `user.id()`.
7. **La vista 3D actual**, sin cambios, en el panel central.

Nada se compila a Unreal todavía, y eso es honesto: no promete lo que no cumple.

---

## 5. Huecos

1. **Cuánto llega de verdad a Unreal.**
   - U2-U4 cubren unas 30 perillas, 11 clips de ambiente y las VO de etapa.
   - Siguen cableados en grafos: obj 135, world 84, fx 180, hap 59, pawn 7 y ui 12. Viven en el Hall (31 pasos), en ChargeFx y en cada BP de etapa.
   - Además, si `ScorePlayer` dispara SFX mientras los grafos viejos los siguen disparando, suenan **dos veces**. `bLegacy*` solo se prevé para AMB y VO.

2. **Audio real contra provisorio.**
   - La mezcla final está en `~/Desktop/Soul Charger VO MEZCLA final` (`importar_mezcla.py:7`), fuera del repo. Sus duraciones están en `Saved/`, que está en `.gitignore:10`.
   - La base del artifact tiene sus propios 116 audios.
   - Resultado: el clip dibuja un largo y suena otro.
   - Falta también el camino inverso: un FX que suba el socio no tiene cómo llegar a `Content/` como `.uasset`.

3. **Texto de VO en inglés editable.** Si el socio cambia el texto, no cambia la grabación. Hace falta un estado "texto ≠ grabación" y que los créditos queden bloqueados.

4. **Borrar con dependientes.** No está definido qué pasa con los clips anclados a uno borrado, ni con una `help` cuya espera desaparece.

5. **"Nunca se monta" depende de la persona.**
   - Un clip anclado al fin de una espera y otro con hora fija en la misma sub-pista no se tocan en Típico, pero chocan en Ausente.
   - Lo mismo pasa cuando la cosecha cambia la duración de una VO.
   - Hace falta definir la persona de referencia (Típico) y mostrar los demás choques como aviso, no como bloqueo.

6. **Grupo plegado.** No está definido dónde cae un clip que se suelta sobre la fila de resumen.

7. **El alto no alcanza.**
   - Las sub-pistas iniciales son unas 35, a 34 px, más 11 filas de grupo: unos 1450 px.
   - En los 402 px del timeline quedan unos 330 útiles.
   - Además, el artifact corre dentro de claude.ai y no tiene 1920×1080.

8. **Cuando Unreal cambia una mecánica** (Recognizing pasó de 18 a 38 latidos; Loving, de 80 a 60 s):
   - Falta un contrato por etapa, versionado en el repo y escrito por la sesión de esa etapa.
   - El aviso a Narrativa del README tendría que incluir "contrato cambiado".

9. **Permisos.**
   - En `db` escribe el nivel Contributor (`interact`).
   - `assets`, que hace falta para subir audio, es solo para Editor u Owner.
   - Un Editor externo invitado por email pierde ese nivel si el artifact también se comparte por link.

10. **`editor.html` dentro de `files`.** No está verificado que reciba `claude.use` ni que comparta la base. Plan B: un artifact nuevo, copiando los assets en el servidor (`from_url` + `asset_ids`, 10 por llamada: unas 12 llamadas para los 116 audios).

11. **Pruebas.** ISP se prueba con sondas CDP en Electron. En local, `claude.use` devuelve null, así que hace falta un shim de `window.claude` en memoria para correr el editor con Playwright y probar `db` y `room`.

12. **Rendimiento en vivo.** Hoy `computeSchedule` corre en cada cuadro de una espera retenida. Con el `renderTimeline` completo (unos 100 ms con 300 clips, `ISP/COMPONENTS.md:660`) se traba. Hay que usar solo `positionClips`. La virtualización horizontal es código nuevo, no de ISP.

13. **Comentarios nativos.** Nadie evaluó la capacidad `comments`: Claude recibe esos hilos con ArtifactComments. Tiene una restricción: la página no puede listar los hilos.

14. **El índice `plan`** (`timeline.js:899-903`), que leen las sesiones, tiene que sobrevivir al esquema 2.

15. **El `index.html` viejo** tiene que quedar en solo lectura **por código**, no por acuerdo.

---

## 6. Riesgos, de más a menos grave

1. **Ilusión de control.** El socio monta una obra que el APK no reproduce. *Mitigación:* insignia por elemento, alcance escrito en la barra de estado ("142 de 592 llegan a Unreal") y prioridad a las familias que pida el socio.
2. **`ScoreApply` pisa a Beltrán.** *Mitigación:* reconciliación de tres vías por perilla (§2.1).
3. **El trasplante de ISP choca con el modelo de datos.** ISP mueve clips sobre `c.start` absoluto (`nudgeSel`, `app.js:16483`; `snapTargets`, `:7048`), mientras que la partitura trabaja con anclas y desfases. `renderTimeline` llama a unos 80 ayudantes de medios, proxys y automatización. "Tal cual" es falso para los gestos. *Mitigación:*
   - copiar el CSS y el chrome sin tocar;
   - escribir un timeline propio sobre las clases de ISP;
   - copiar solo funciones puras: `fmtTime`, la matemática de imán y zoom, `inlineEdit`, menús y paleta;
   - un script que compare las líneas de origen en cada release de ISP.
4. **Doble runtime mantenido por una sola sesión.** *Mitigación:* catálogo de 10 acciones como máximo al principio; las mecánicas entran como "caja" con duración simulada.
5. **El observador pierde marcas.** *Mitigación:* dispatcher `OnMark`.
6. **Sandbox del artifact** (emergentes, canal entre pestañas, `editor.html`). *Mitigación:* una prueba de 30 minutos en el host real antes de F2, con `room` como transporte.
7. **Base sin transacciones y con 256 KiB por documento.** *Mitigación:* documentos granulares, versiones como asset y suscripciones por colección.
8. **Gotcha 402 con la Obra en edición activa.** *Mitigación:* U2 en una sola tanda, en el turno de la cola, con la Obra cerrada.
9. **Audio provisorio.** *Mitigación:* la cosecha sube la mezcla final a assets y marca "provisorio" por ID.
10. **Atajos del navegador.** *Mitigación:* remapear Ctrl+T y probar el resto en el iframe.

---

## 7. Preguntas abiertas para Beltrán (solo las que cambian el diseño)

1. **¿Quién manda en las perillas que ya son de instancia** (`Pace*`, `FW_*`, `ChargeTimes`)? *Recomiendo:* la instancia de Unreal. La partitura propone, y solo los literales que se conviertan en perillas se leen de la tabla, con reconciliación de tres vías.
2. **¿Qué familias tienen que llegar a Unreal primero?** *Recomiendo:* ambientes, VO de etapa y título/velo. El resto queda como previs con insignia.
3. **Solape al soltar:** ¿rechazar o reubicar? *Recomiendo:* rechazar en el movimiento horizontal, crear sub-pista solo con la ranura, y que los choques que causen la persona o los audios sean aviso, no bloqueo.
4. **¿Una sub-pista puede significar algo** (Omnipresente, mano dominante)? *Recomiendo:* no. El significado va en el inspector.
5. **¿Agrupar por sujeto o por medio?** *Recomiendo:* el orden de ISP. Lo visual arriba y por sujeto (Alma, Timbre, Anillo); el sonido abajo y por bus (VO, SFX, AMB, HAP).
6. **¿Dos pestañas o emergente?** *Recomiendo:* el MVP todo en uno; después, dos pestañas con `room`, una vez probado en el host.
7. **¿Qué nivel de acceso tiene el socio y está en la organización?** *Recomiendo:* Editor, si va a subir audio.
8. **Título: ¿cuál es el final**, el del runner o el de la Obra? (Esto define U5.)
9. **ISP: ¿fork o módulo compartido?** *Recomiendo:* fork del CSS y del chrome con encabezado de procedencia; el timeline, propio.

---

## 8. Fidelidad a ISP

Medidas y tokens están bien citados. Estas son las desviaciones sin motivo suficiente:

1. **Inspector a 320 px con etiquetas de 84 px.** ISP ya traduce "Fundido de salida" (`T('Fade out','Fundido de salida')` en `app.js`) y vive con 60 px (`index.html:327`). Hay que arreglarlo en ISP mismo o acortar las etiquetas, no bifurcar la medida. "Cortafuegos" se puede decir "Tope", que es el vocabulario que la propia UX propone.
2. **Encabezado de 58 px con tres bandas (actos, regla, momentos).** En ISP es una sola regla de 24 px con los locators en la mitad de abajo (R223), y ADR-0008 dice "lo que no está en el diseño se poda". *Alternativa:* actos como regiones dentro de la regla, momentos como marcadores.
3. **Cabecera de grupo con +, L, M y S en 168 px.** ISP lleva solo M y S (`index.html:448`), y así el nombre queda en unos 60 px. Mejor `+` al pasar el mouse y L en el menú contextual.
4. **Cajón de 220 o 260 px** contra los 188 de `.curvedrawer` (`index.html:392`).
5. **Glifos Unicode en los esquemas** (⚓ ◉ ⧉ ◠ ♪ ⟳ ⚑). En ISP todo pasa por `ICO()`, y el comentario de `:root` dice "Sin bordes, sin iconos": la affordance la da el contraste. La captura `02-workspace-dome.png` muestra segmentados con texto (2D/3D, Full/½/¼, Clip/Comp).
6. **Cian con cinco significados.** En ISP el cian es "vivo/arrastrable" y nada más (`index.html:47`). "Enlazado a Unreal" tiene que ir sin color.
7. **Un transporte de 28 px recargado** con pestañas de secuencia, persona de 4 segmentos, timecode relativo, [Obra|Momento] y el grupo de edición. En la captura de 1600 px, el transporte de ISP ya está lleno. La persona va mejor en la barra superior, junto al total.
8. **Diseño a 1920×1080.** ISP se verificó a 1600×900, y el artifact corre dentro del marco de claude.ai. Hay que diseñar para unos 1600×860 útiles.
9. **Sub-pista de 34 px** contra `LANE_DEF_H` de 57. Se justifica por densidad, pero el cuerpo de 13 px pierde el contenido del clip. Conviene partir de `LANE_MIN_H` (26 px) y del alto global de ISP (R156), en lugar de inventar una medida.