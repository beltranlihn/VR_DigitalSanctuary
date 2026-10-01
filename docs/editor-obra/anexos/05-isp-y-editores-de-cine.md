> Anexo de la auditoría del 2026-10-01 (investigación: Immersive Studio Pro y convenciones de editores de cine). Lo que manda es [PLAN-EDITOR-OBRA-2026-10-01.md](../PLAN-EDITOR-OBRA-2026-10-01.md); donde este anexo lo contradiga, gana el plan.

# Investigación web: la referencia de UI/UX y las convenciones de edición de cine

## A. Qué es "Immersive Studio Pro"

### Lo más probable: es tu propio software, que ahora se llama VEATION

Lo que lo indica:
- Al buscar el nombre exacto, el primer resultado es el repositorio **`github.com/beltranlihn/Immersive-Studio-Pro`**. El buscador lo describe como un editor de video inmersivo de escritorio para fulldome, pantalla 2D y sala 360°, hecho en Electron con WebGL2. Al pedirlo sin autenticación hoy devuelve 404, así que lo más probable es que sea privado o que haya cambiado de nombre.
- En el disco está `C:/Users/beltr/Desktop/Alma Digital Studio/Projects/Immersive Studio Pro/` (en adelante `ISP/`):
  - `ISP/README.md:1-4` dice "VEATION. Editor de vídeo inmersivo de escritorio: domo fulldome, pantalla plana 2D y sala 360°".
  - En la raíz está `Immersive Studio Pro - User Manual.pdf`.
  - El último commit, `2aa181e`, dice "el nombre del paquete seguía siendo immersive-studio-pro".
  - El cambio de marca se explica en `docs/adr/adr-0011-marca-veation-formato-vea.md`.

Otros candidatos y por qué los descarto:

| Candidato | Qué es | ¿Encaja? |
|---|---|---|
| [Overloud Immersive Studio](https://www.overloud.com/products/immersive-studio) | Biblioteca de respuestas al impulso para reverb | No |
| [Immersive Interactive – Immersive Studio](https://immersive.co.uk/immersive-studio/) | Editor web de 360° con hotspots, orientado a educación | Solo como idea de "hotspots" |
| [Embody Immerse Virtual Studio Pro](https://embody.co/pages/ivs-apple-music) | Plugin de mezcla Atmos | No |
| [Reality Composer Pro (WWDC24 10102)](https://developer.apple.com/videos/play/wwdc2024/10102/) | Timelines de acciones que se disparan desde un componente Behaviors (OnTap, OnAddedToScene, OnCollision, OnNotification) y que pueden enviar notificaciones al código ([ejemplo](https://stepinto.vision/example-code/timelines-working-with-notifications/)) | No es "el" producto, pero es **el mejor patrón para mezclar timeline e interacción** (ver C) |
| [Apple Immersive Video Utility](https://support.apple.com/guide/immersive-video-utility/welcome/web) | Biblioteca, playlists y revisión sincronizada en varios Vision Pro ([MacRumors](https://www.macrumors.com/2025/04/07/apple-immersive-video-utility-app/)) | No edita. Lo útil es la revisión multi-dispositivo sincronizada |
| [DaVinci Resolve 20.1 immersive](https://petapixel.com/2025/08/07/davinci-resolve-is-first-macos-video-editor-to-fully-support-apple-immersive-video/) | Visor inmersivo con pan/tilt/roll en monitor 2D o en streaming al Vision Pro | Patrón de visor; no es "Studio Pro" |

**Consecuencia:** la referencia "elegante" no tiene que adivinarse en internet. Ya existe tokenizada, especificada y verificada en tu repositorio. El editor web debería **heredar el sistema de diseño de VEATION**, no imitar uno de afuera.

### Cómo es la UI/UX de VEATION

**Disposición** (`ISP/docs/manual/img/02-workspace-dome.png`; especificación en `ISP/docs/historial/REDISEÑO-UI.md` §1-7):
- **Barra superior de 28 px:** a la izquierda File · Edit · Window; a la derecha, el nombre del proyecto y un chip de formato ("4096² · 60p").
- **Columna izquierda, Media:** cambio Lista/Grilla, filtros All/Video/Image/Audio, orden, y una fila de creación (Import, Text, Shape, Compose, Adjust) cuyas etiquetas se ocultan a menos de ~340 px.
- **Visor al centro**, con barra propia:
  - 2D/3D;
  - superposiciones con etiqueta (Grid/Safe/Outline/Horizon/Alpha);
  - calidad Full/½/¼;
  - Clip/Comp, zoom en % y un menú **Output** (Full performance · Viewer window · NDI · Spout).
- **Inspector a la derecha:**
  - pestañas Inspector / Reactive FX;
  - una franja de 4 px con el color del clip, que se puede tocar para cambiarlo;
  - una cabecera de ítem (miniatura de 44×28, nombre en 13 px/600 y metadatos en 10 px);
  - secciones plegables (Transform, Clip, Source, Color, Motion).
- **Fila de parámetro del inspector:** etiqueta, fader de 3 px **relleno con el color del parámetro**, chip con el valor más su unidad, y un **diamante de keyframe** en ese mismo color.
- **Transporte de 28 px, el único en `#242424`:**
  - a la izquierda, **las secuencias como pestañas** y un `+`;
  - al centro: Mark In · inicio · Play (30×22) · fin · Mark Out · caja de timecode (TC y frames) · cambio TC/Frames;
  - a la derecha: Simple · Auto · Grid · Fit, y zoom −/＋.
- **Timeline** (REDISEÑO-UI §6):
  - Riel de herramientas de 34 px: V · selección de pista · H · T · B · Z.
  - Cabeceras de 168 px en **una sola columna para video y audio**. Cada una lleva franja de color, chevron, etiqueta V4/A1, nombre editable y botones M/S.
  - Clips: barra de título de 16 px, relleno con el color al 30 %, miniatura, y **fundidos como cuadraditos de 6×6 px en las esquinas superiores**.
  - Curvas de automatización en el color del parámetro.
  - Cabezal de reproducción de 2 px en `#E0E0E0` y una barra lateral de zoom vertical.
- **Barra de estado de 22 px:** muestra la ayuda de la herramienta activa ("Select (V) — click a clip…") y CPU/RAM/GPU.

**Estética** (`ISP/index.html:28-83`):
- Tres superficies: `#111` (fondos hundidos), `#1B1B1B` (paneles) y `#262626` (controles).
- Cuatro niveles de texto: `#E0E0E0`, `#B8B8B8`, `#8C8C8C` (solo unidades) y `#6D6D6D` (deshabilitado).
- Tres opacidades de línea (.05/.10/.16).
- **Solo dos acentos, por regla escrita**: cian `#4FC3E8` = "vivo/arrastrable" y ámbar `#E5B567` = "anulado".
- Interruptores en verde `#4A8D6F` y color de peligro `#E06C6C`.
- **Un color por parámetro** (Az `#E0954B`, El `#D8C24B`, Size `#E0645C`…), el mismo en el fader, el diamante y la curva.
- Tipografía Geist (más Inter y JetBrains Mono, según `ISP/licenses/`), base de 11 px y nada de MAYÚSCULAS.
- Alturas fijas de 28/22/16 px y una paleta de espaciado cerrada de 2 a 32 px.
- Bordes finos de .5 px y menús con ítems de 26 px y el atajo alineado a la derecha.
- Una paleta de comandos (`img/12-palette.png`) con la categoría a la izquierda y el atajo a la derecha.

**Interacción:**
- **Mover clips al estilo Ableton:** el original queda quieto y un fantasma muestra el destino (`ISP/COMPONENTS.md:768`).
- **Snapping siempre activo** a bordes, cabezal y marcadores; **Alt lo anula** (`COMPONENTS.md:77, 832`).
- Atajos (`ISP/docs/manual/data.js`):
  - transporte: J/K/L con 2×/4×/8×;
  - locators: M para crear, `.`/`,` para ir al siguiente o al anterior;
  - corte: ↑/↓ para saltar entre cortes, ⌘E para dividir, Alt+←/→ para mover un frame o un segundo;
  - edición: ⇧⌫ para ripple delete, "Nest selection";
  - "Detect beats → locators".
- **"Ventana solo-visor":** una ventana aparte con **la vista complementaria** a la del editor (2D ⇄ 3D) (`COMPONENTS.md:290`). Es el **precedente directo** de tu modo "dos pestañas".
- **Proceso de diseño:** ADR-0008 (recrear el diseño calcado y "lo que no está en el diseño se poda") y la verificación con sondas automáticas a 1920×1080.

## B. Lo que un editor de cine espera encontrar

| Convención | Dónde y cómo | Fuente |
|---|---|---|
| **Pistas libres** V1..n / A1..n, con lock, mute/solo, *track targeting* y *sync lock* | Premiere: el targeting define qué pistas afectan copiar, pegar y navegar; el sync lock define qué pistas se desplazan en un insert o ripple | [targeting](https://helpx.adobe.com/premiere/desktop/edit-projects/intro-to-editing/work-with-clips-on-the-timeline-using-track-targeting.html), [sync lock](https://helpx.adobe.com/premiere/desktop/edit-projects/change-clip-sequence/sync-lock-to-prevent-changes.html), [lock](https://helpx.adobe.com/premiere/desktop/edit-projects/change-clip-sequence/track-lock-to-prevent-changes.html) |
| **Timeline magnético** | FCP: *primary storyline*, *connected clips*, *storylines* que se mueven como unidad; los choques se resuelven empujando clips en vertical; *roles* y *audio lanes* por rol | [Apple](https://support.apple.com/guide/final-cut-pro/final-cut-pro-interface-ver92bd100a/mac), [Frame.io](https://blog.frame.io/2017/10/16/fcpx-magnetic-timeline/) |
| **Color = consecuencia** | Avid, modo segmento: **rojo** = Lift/Overwrite (no mueve a los demás, deja hueco); **amarillo** = Extract/Splice (hace ripple). En modo trim, los rodillos tienen los mismos colores | [ProVideo Coalition](https://www.provideocoalition.com/the_basics_of_avid_media_composer_for_a_final_cut_pro_editor/) |
| **Herramientas de trim** | Ripple (B), Roll (N), Slip (Y), Slide (U), Ripple delete | [ripple](https://helpx.adobe.com/premiere/desktop/edit-projects/trim-clips/perform-ripple-edits.html), [roll](https://helpx.adobe.com/premiere/desktop/edit-projects/trim-clips/perform-rolling-edits.html) |
| **Transporte** | J/K/L, I/O, ↑/↓ entre cortes, Home/End | ídem, y `data.js` de VEATION |
| **Marcadores con nota, duración y color**; anotar sobre el visor crea un marcador | Resolve | [Larry Jordan](https://larryjordan.com/articles/display-two-timelines-at-once-in-davinci-resolve-19/), [Blackmagic Forum](https://forum.blackmagicdesign.com/viewtopic.php?t=66922&p=376722) |
| **Comentarios exactos al frame**, con dibujo sobre la imagen y versiones apiladas | Frame.io | [Frame.io + FCP](https://blog.frame.io/2018/11/15/frameio-final-cut-x-extension/) |
| **Secuencias anidadas / compound** | FCP compound, Resolve compound, Premiere nest, VEATION Nest/Compose | [FCP](https://support.apple.com/guide/final-cut-pro/duplicate-projects-and-clips-verfd45ffa45/mac) |
| **Grupos plegables** | Logic *track stacks*: una carpeta que se pliega y se controla como unidad (folder) o que suma (summing) | [Apple](https://support.apple.com/guide/logicpro/track-stacks-overview-lgcp9bc4b63d/mac) |
| **Carriles paralelos dentro de una pista** | Ableton 12, *take lanes*: carril principal más N carriles, que se muestran y ocultan, y se reordenan con Ctrl+↑/↓ | [Ableton](https://www.ableton.com/en/live-manual/12/arrangement-view/), [Sound On Sound](https://www.soundonsound.com/techniques/ableton-live-getting-creative-take-lanes) |
| **Dos monitores / timelines apiladas** (vista general arriba, zoom abajo) | Resolve: Dual Screen y Stacked Timelines | [Larry Jordan](https://larryjordan.com/articles/display-two-timelines-at-once-in-davinci-resolve-19/), [Filmmaking Elements](https://filmmakingelements.com/how-to-use-dual-screens-in-davinci-resolve-17/) |
| **Versiones** | FCP Snapshot (⇧⌘D, nombre con fecha); VEATION "Save incremental _vNN" | [Apple](https://support.apple.com/guide/final-cut-pro/duplicate-projects-and-clips-verfd45ffa45/mac), [Ripple Training](https://www.rippletraining.com/blog/final-cut-pro-x/fast-project-versioning/) |

Referencias del lado del motor, que se reflejan en la UI:
- **Unreal Sequencer:** Event Track en modo Trigger o Repeater, con un Director Blueprint ([docs](https://dev.epicgames.com/documentation/en-us/unreal-engine/fire-blueprint-events-during-cinematics-in-unreal-engine)).
- **Unity Timeline:** Signal Track más un Signal Receiver, con marcadores como eventos puntuales ([docs](https://docs.unity3d.com/Packages/com.unity.timeline@1.8/manual/wf-signals.html)).
- **Notch:** combina timeline por capas, nodegraph y visor en un solo programa, y tiene un nodo "Jump to Time" que salta el cabezal ([manual](https://manual.notch.one/2026.1/en/docs/reference/user-interface/), [Jump to Time](http://manual.notch.one/0.9.23/en/topic/nodes-logic-jump-to-time)).
- **Theatre.js:** un editor de secuencias y keyframes sobre three.js en el navegador ([docs](https://www.theatrejs.com/docs/0.5/getting-started/with-three-js)). Sirve como referencia de editor de curvas; no conviene como dependencia, porque su modelo de datos no se corresponde con Unreal.

## C. Qué conviene adoptar y qué no

### Estado actual del prototipo (para ubicar las propuestas)

- **Nueve pistas fijas:** vo, fx, amb, hap, pawn, world, obj, ui, int (`timeline.js:11-21`).
- **Los carriles son automáticos:** `computeLanes()` vuelve a acomodar los clips en cada `layout()` (`timeline.js:590-606`). Solo se congelan mientras arrastras (`UI.lanesFrozen`, `timeline.js:731` y `:739`).
  - Por eso, **al soltar un clip, los demás pueden cambiar de carril**: es exactamente el problema de "se superponen o saltan" que describes.
- **La semántica interactiva ya existe:** `gate` (espera del usuario), `help` (solo si el usuario tarda) y `simOnly` (en vivo lo dispara el usuario) (`timeline.js:587`).
- También existen locators con factor de escala de tiempo, `WARP` (`timeline.js:122-130`).
- **Pocos atajos:** solo Space, ←/→, Home/End, Esc, Supr, M y T (`timeline.js:1141-1162`).

### Qué adoptar

1. **El sistema de diseño de VEATION, tal cual.** Copiar los tokens de `ISP/index.html:28-83` y la gramática de REDISEÑO-UI §0: alturas 28/22/16, wells, interruptores verdes, color por parámetro, menús de 26 px y paleta de comandos.
   - La disposición se calca: biblioteca de la obra a la izquierda, visor three.js al centro, inspector a la derecha, timeline abajo y barra de estado con la ayuda de la herramienta.
   - Tu socio y tú van a ver *la misma familia* de herramientas.
2. **Grupos con carriles explícitos (take lanes y folder stacks).**
   - Cada pista actual pasa a ser un **grupo plegable**, con franja de color, chevron, M/S/Lock y contador de carriles.
   - Dentro de cada grupo, **carriles creados por el usuario** (VO 1, VO 2…), con el índice guardado en el edit: un campo `lane` junto a `{uid,d,dur,fw,at,text}`.
   - El acomodo automático deja de correr solo y pasa a ser un **comando explícito** ("Ordenar carriles"), como las *audio lanes by role* de FCP.
   - Un clip solo cambia de carril si lo arrastras en vertical.
   - Si sueltas un clip encima de otro, la elección es **rechazarlo con el fantasma en rojo o crear un carril nuevo**, nunca superponerlo en silencio.
3. **Mover sin empujar por defecto (el rojo de Avid).**
   - Mover un clip no desplaza a los demás. En una obra donde la música, el attracting y la voz están sincronizados, el ripple automático rompe cosas lejos de donde miras.
   - **Ripple como herramienta o modificador explícito, en amarillo**, limitado al **acto actual** y a los grupos con *sync lock*.
   - La semántica de los colores, como en Avid, avisa la consecuencia antes de soltar.
4. **Atajos y movimiento de VEATION/NLE:**
   - transporte: J/K/L, I/O;
   - locators: M, `.`/`,`;
   - corte: ↑/↓ entre cortes, ⌘E para dividir, Alt+←/→ para mover un frame o un segundo;
   - edición: ⇧⌫ para ripple delete;
   - snapping siempre activo con **Alt para anularlo** y fantasma al arrastrar;
   - paleta de comandos con Ctrl+K.
5. **Disparadores como ciudadanos de la timeline**, no en un grafo aparte:
   - **Marcadores de evento** (como el Signal de Unity o el Trigger de Unreal) para lo instantáneo.
   - **Gates como clips elásticos** con duración esperada mínima/típica/máxima, un patrón visual propio (rayado y un ícono de mano) y un cabezal que "espera".
   - **Cables visibles "A dispara B"** entre clips: se dibujan solo al seleccionar, para no ensuciar.
   - El **grafo de nodos** se reserva para el *interior* de un bloque interactivo. Doble clic sobre el bloque lo abre como un nido o un compound, en una pestaña de secuencia como en VEATION. Es el modelo de Notch (capas en la timeline más un nodegraph) y de Reality Composer Pro (una timeline que lanza un trigger y avisa al terminar).
6. **Tiempo relativo además de absoluto.**
   - La caja de TC muestra el tiempo de la obra *y* el desfase respecto del ancla: "+00:04:12 desde Gate «respira»".
   - El absoluto en una pieza interactiva es una estimación: hay que decirlo en la UI.
7. **Dos modos de ventana:**
   - Todo en uno, con la disposición de VEATION.
   - **Visor en pestaña aparte**, como la ventana solo-visor de VEATION (`COMPONENTS.md:290`) o el Dual Screen de Resolve. Ambas pestañas comparten selección y cabezal.
   - Agregar arriba una **vista general apilada** (Stacked Timelines de Resolve): un mini-mapa de los ~15 min por actos, sobre la timeline con zoom.
8. **Inspector "en idioma de cine":**
   - Primero "qué hace" en lenguaje llano, con color por parámetro y diamante de keyframe.
   - Después, plegado, "En Unreal": el nombre del BP o variable, para ti.
   - Cada ítem muestra de dónde viene (Unreal, web o editado) y su estado de sincronización.
9. **Notas exactas al frame**, como Frame.io: marcadores con nota, duración, color y autor. Ese es el canal entre tu socio y tú.
10. **Snapshots con nombre** (Snapshot de FCP o "_vNN" de VEATION) y comparación entre versiones antes de publicar a Unreal.

### Qué no adoptar (choca con la interactividad o no aplica)

- **El timeline magnético global de FCP.** El ripple implícito lo mueve todo, y en una obra con gates eso desordena las sincronías. A lo sumo, dentro de un acto y como opción.
- **Slip y Slide en clips sin media** (eventos, actores, instrucciones): no tienen material de origen que deslizar. Sí sirven en clips de **audio**: VO, SFX, música.
- **Roll:** solo entre clips contiguos del mismo carril, por ejemplo el crossfade entre dos ambientes.
- **Visor de fuente/programa y edición de tres puntos con I/O de fuente:** no hay material de cámara. Basta con una vista previa en la biblioteca para escuchar un audio.
- **Numeración V1..Vn como identidad de pista:** acá las pistas tienen significado (Voz, Mundo…). Se usan nombres por grupo y números solo para los carriles.
- **Etalonaje, multicámara, mezclador completo y export de video:** fuera de alcance. El mezclador se reduce a ganancia y fundidos por clip, con los cuadraditos de VEATION.
- **Timecode absoluto como la verdad:** ver el punto 6.

## Fuentes
- [beltranlihn/Immersive-Studio-Pro (GitHub)](https://github.com/beltranlihn/Immersive-Studio-Pro)
- [Overloud Immersive Studio](https://www.overloud.com/products/immersive-studio) · [Immersive Interactive – Immersive Studio](https://immersive.co.uk/immersive-studio/) · [Embody Immerse Virtual Studio](https://embody.co/pages/ivs-apple-music)
- [Reality Composer Pro, WWDC24 10102](https://developer.apple.com/videos/play/wwdc2024/10102/) · [Timelines: Working with Notifications](https://stepinto.vision/example-code/timelines-working-with-notifications/)
- [Apple Immersive Video Utility](https://support.apple.com/guide/immersive-video-utility/welcome/web) · [MacRumors](https://www.macrumors.com/2025/04/07/apple-immersive-video-utility-app/)
- [Resolve 20.1 immersive (PetaPixel)](https://petapixel.com/2025/08/07/davinci-resolve-is-first-macos-video-editor-to-fully-support-apple-immersive-video/)
- [FCP interface](https://support.apple.com/guide/final-cut-pro/final-cut-pro-interface-ver92bd100a/mac) · [Magnetic timeline (Frame.io)](https://blog.frame.io/2017/10/16/fcpx-magnetic-timeline/) · [FCP duplicate/snapshot](https://support.apple.com/guide/final-cut-pro/duplicate-projects-and-clips-verfd45ffa45/mac) · [Ripple Training versioning](https://www.rippletraining.com/blog/final-cut-pro-x/fast-project-versioning/)
- [Premiere ripple](https://helpx.adobe.com/premiere/desktop/edit-projects/trim-clips/perform-ripple-edits.html) · [rolling](https://helpx.adobe.com/premiere/desktop/edit-projects/trim-clips/perform-rolling-edits.html) · [track targeting](https://helpx.adobe.com/premiere/desktop/edit-projects/intro-to-editing/work-with-clips-on-the-timeline-using-track-targeting.html) · [sync lock](https://helpx.adobe.com/premiere/desktop/edit-projects/change-clip-sequence/sync-lock-to-prevent-changes.html) · [track lock](https://helpx.adobe.com/premiere/desktop/edit-projects/change-clip-sequence/track-lock-to-prevent-changes.html) · [sync locks Avid/Premiere](https://blog.frame.io/2017/11/28/sync-locks-avid-premiere/)
- [Avid basics (ProVideo Coalition)](https://www.provideocoalition.com/the_basics_of_avid_media_composer_for_a_final_cut_pro_editor/)
- [Resolve dual timelines (Larry Jordan)](https://larryjordan.com/articles/display-two-timelines-at-once-in-davinci-resolve-19/) · [Resolve dual screen](https://filmmakingelements.com/how-to-use-dual-screens-in-davinci-resolve-17/)
- [Logic track stacks](https://support.apple.com/guide/logicpro/track-stacks-overview-lgcp9bc4b63d/mac) · [Ableton 12 Arrangement](https://www.ableton.com/en/live-manual/12/arrangement-view/) · [Ableton comping](https://www.ableton.com/en/live-manual/12/comping/)
- [Frame.io en FCP](https://blog.frame.io/2018/11/15/frameio-final-cut-x-extension/)
- [Unreal: Blueprint events desde Sequencer](https://dev.epicgames.com/documentation/en-us/unreal-engine/fire-blueprint-events-during-cinematics-in-unreal-engine) · [Event Track](https://docs.unrealengine.com/4.27/en-US/AnimatingObjects/Sequencer/Overview/Tracks/EventTrackOverview)
- [Unity signals](https://docs.unity3d.com/Packages/com.unity.timeline@1.8/manual/wf-signals.html)
- [Notch UI](https://manual.notch.one/2026.1/en/docs/reference/user-interface/) · [Notch Jump to Time](http://manual.notch.one/0.9.23/en/topic/nodes-logic-jump-to-time)
- [Theatre.js + three.js](https://www.theatrejs.com/docs/0.5/getting-started/with-three-js)

Archivos locales consultados (solo lectura):
- Prototipo web, en `C:/Users/beltr/Desktop/Alma Digital Studio/Projects/VR Unreal/web/prototipo-narrativo/`: `timeline.js`.
- VEATION, en `C:/Users/beltr/Desktop/Alma Digital Studio/Projects/Immersive Studio Pro/`: `README.md`, `index.html`, `COMPONENTS.md`, `docs/historial/REDISEÑO-UI.md`, `docs/adr/adr-0008-rediseno-rev1-regla-de-poda.md`, `docs/adr/adr-0009-arranque-en-dos-ventanas.md`, `docs/manual/data.js`, `docs/manual/img/` y `docs/MARCA.md`.