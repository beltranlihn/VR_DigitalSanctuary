# Auditoría de pedidos de Beltrán · 28, 29 y 30 de septiembre de 2026

Fuente: los mensajes de Beltrán en las 8 sesiones del proyecto (Narrativa, Mesh 3D, Drawing, Breath, Mind, Secuencer, Heart y Hall), incluidos los que mandó a mitad de turno: **473 mensajes únicos** (`scratchpad/audit/extract.py`). Cada pedido se verificó contra el estado real: trackers de `blueprints/`, memoria de cada sesión, `docs/PLAN-NOCHE-2026-09-30.md`, logs de PIE y código de la web.

Estados:
- ✅ **aplicado y verificado** (PIE, log o lectura del asset/código);
- 👁 **aplicado, falta confirmarlo en el visor**;
- 🟡 **parcial o sin evidencia**;
- ❌ **no aplicado**.

Límite: las sesiones Remote Control que ya no están en esta máquina no se pudieron leer.

---

## Resumen

**Lo que falta de verdad** (❌ y 🟡):

| # | Pedido | Estado | Qué falta |
|---|---|---|---|
| 1 | Fantasmas de las instrucciones grabados contigo y metidos en la obra (09-29 09:07/09:14, 09-30 09:30) | ❌ | El sistema está construido (`L_GhostRec_SC`, reproductor, 10 DataAssets). **Falta la sesión de grabación contigo** y enchufar los fantasmas en el R4 de cada etapa. |
| 2 | Probar con el **robot** que simula un humano en todas las etapas (09-30 00:25) | ❌ | No se usó el robot. Las pruebas de punta a punta fueron PIE en autoplay, con los cortafuegos de cada etapa. |
| 3 | Si el usuario interactúa antes de que termine la voz, la voz se funde y seguimos (09-29 14:33) | ✅ | Web + Unreal. Heart: `Alma.FadeVoice(Time)`, y StopSpeaking funde en 0,3 s. Hall T5: HallSay por SayClip; si el timbre, el mando o el alma se resuelven con la VO sonando, la voz se funde y el paso sigue 0,3 s después (PIE con control negativo y positivo). 👁 oírlo con mano en el visor. |
| 4 | Que la experiencia no pase de **15 min** (09-29 09:03) | 🟡 | El timeline de la web suma **1018 s ≈ 17 min** (con el aviso de 20 s); en Unreal, estimado 17-19 min. Sobran ~2 min. Recortes que no tocan el diseño: créditos 60 → 40 s (−20), explorar resultados 25 → 15 s (−10), las 4 despedidas más cortas (~−15), el viaje del inicio 26 → 20 s (−6), los silencios de Loving 12 → 8 s ×3 (−12), el pacer de 5 → 4 ciclos (−14). **La decisión es tuya.** |
| 5 | "El entorno inicial y final es oscuro, acá están muy claros" (09-30 05:25) | 🟡 | La niebla del inicio y de la constelación es azul (tu guion dice "azulado suave"). No hay un cambio registrado después de ese comentario: **mirarlo tú**. |
| 6 | Carga: "la salida de la animación queda rara, se va el anillo y vuelve todo muy duro" (09-30 08:59, sobre la prueba de la carga final) | 👁 | Resuelto por el diseño nuevo del final, que pediste a las 09:07: la última carga ya **no vuelve al HUD**. El entorno funde a negro con el anillo y sus explosiones por delante (`FinalLook`), el HUD se disuelve y el alma sigue como pez hacia el Hall. Falta que lo veas en el visor. La vuelta al HUD de las cargas comunes es el "¡pum!" que aprobaste el 09-29. |
| 7 | "El botón de timbre quedó con la cara del botón abierta" (09-29 21:46, Mesh 3D) | ✅ | Estaba arreglado desde el 09-30 a las 02:48 (malla invertida por el sentido del perfil; `gen_bell.py` corregido y reimportado; registro en `BP_BellArt_SC.md`). Mesh 3D lo reconfirmó: 0 bordes abiertos y volumen positivo. |
| 8 | La experiencia arranca con un comando OSC desde el PC (guion 09-29) | 🟡 | Hoy arranca sola (necesario para el APK). El disparo por OSC no está implementado. |
| 9 | Error de carga en la web ("reading 'elements'") | ✅ | **No se reproduce.** 4 cargas con captura de errores activa, más un recorrido de los 1018 s del timeline cada 5 s: 0 errores, 0 matrices indefinidas, 0 shaders rotos. Los que se veían eran errores acumulados en la consola de la pestaña, de versiones viejas ya corregidas. |

**Lo que está aplicado pero solo se confirma en el visor** (👁):
- la línea del EEG en el HUD;
- el gatillo del mando que se aprieta (en la mano y en resultados);
- el láser, el hover y el hundido de SHARE a 1,9 m;
- el aura de Alma y el halo del alma en la constelación;
- el sensor azulado → rojizo;
- el dibujo creciendo en los resultados (probado sin dibujo real);
- **72 fps de la Obra en la Quest** (el APK nuevo todavía no corrió en el visor).

---

## Detalle por área

### Proceso, equipo y herramientas
- ✅ Guion de development + narrativa, con sonidos, VO, efectos y quién llama a quién → `docs/GUION-V5-2026-09-29.md`.
- ✅ Hall de entrada + un solo lugar para las etapas y el mismo punto de carga, sin level streaming: la Obra carga las celdas con `LoadLevelInstance`.
- ✅ Nada de flotas de agentes; turnos del editor; RAM vigilada (reglas en memoria). Esfuerzo de ultracode en "alto" en las 7 sesiones.
- ✅ Narrativa como director general (noches 28 y 29): cola, turnos y respuestas por ti. Registro en `docs/PLAN-NOCHE-2026-09-30.md`.
- ✅ Los valores de los niveles de test son los finales, la Obra coincide con ellos y la web sigue a Unreal: `ReadRunners` + `ensayo.js`, paletas v47.
- ✅ Créditos oficiales tal como los dictaste.
- ✅ "Después no apagues": el PC y Unreal siguen prendidos.
- ✅ Tiempos por timeline, no por sonido; solo la VO dura su audio (revisado en todas las sesiones; Attracting StepBPM 90).
- ✅ Toda interacción con botones tiene animación (ver cada sección).
- ✅ Ensayo de etapa: runner + TargetPoints movibles en los 5 niveles, y el Hall desde el timbre (`TestFromStep`). La Obra y la web leen esos puntos.

### Web (timeline editable)
- ✅ Toda la narrativa en la web, con timeline tipo Premiere: arrastrar con la rueda, FOV/distancia, barra espaciadora, guardado de tus ajustes, locators, pistas separadas y vinculadas.
- ✅ VO con texto editable, WAV, modo texto/audio/ambos, fades y crossfades; los ambient se extienden hasta el siguiente; los FX duran lo que dura su WAV; parámetros de estética por etapa; los pasos de la presentación de las etapas en clips separados (2.7a-e); WALK FX visible; sin instrucción de "mueve las manos".
- ✅ Colores y paletas de cada etapa (v47); sonidos provisorios reemplazables; ensayo (v48); latidos, timbre y viaje de Mind (v49); Hall T4 (v50); Alma durazno (v51); pacer de 5 ciclos (v52); aura (v53).
- ✅ Las esferas de Attracting no suenan al pasar el láser (solo visual).
- ✅ El error de carga no se reproduce (ver resumen).

### Inicio y transiciones
- ✅ Arranca en **negro**, con el título quieto; después se desvanece y avanzamos entre motas del espacio. El azul pasa a negro a mitad del trayecto y recién ahí se carga el Hall. Los pasos suenan al final. Todo parte apagado en BeginPlay, sin tirones. Los ambient suenan.
- ✅ Aviso de 20 s en negro (prototipo simulado) y datos simulados (`bSimulated`).
- ✅ Velo lejano de 50 m, sin dither de ruido y sin bandas. Nada aparece antes de que termine el fundido. Sin el cuadro negro al cambiar de etapa. Títulos fijos en el mundo, al frente, con borde fwidth (sin dientes de sierra). Color de cada título = paleta de la etapa que viene.
- ✅ Cada etapa abre ágil (velo 1→5 s, Alma a los 5,5 s); despedida e invitación de Alma después de cada carga; Alma bien al costado mientras dejas libre la mecánica.
- 👁 72 fps en todas las transiciones: medido en el visor el 09-29 (recorrido v6, Attracting luego a 72). La Obra nueva no se midió en la Quest.

### Hall de acceso
- ✅ Arquitectura:
  - pabellón circular con óculo, dos puertas circulares completas, vidrio cálido esmerilado y hormigón fino;
  - afuera negro con piel negra que tapa las hojas;
  - hendiduras en placas, marco de luz exterior, haz en cono que se abre hacia abajo, polvo interior;
  - 5 baldosas biseladas de hormigón con su color;
  - encendido tipo portal y emisión hacia abajo.
- ✅ Baldosas v3: más rugosas, línea más clara y de grosor parejo. Suben unos cm, se iluminan con su color y muestran su nombre mientras Alma presenta cada etapa.
- ✅ Título SOUL CHARGER / CENTER a la derecha de la puerta, alineado a la izquierda, con desvanecimiento líquido, en las dos llegadas al Hall.
- ✅ La salida pasa a blanco azulado (color de Breath) cuando Alma dice "Follow me".
- ✅ Las líneas del domo se encienden en onda al entrar (las dos veces) y se apagan al salir (control positivo aprobado).
- ✅ Orbe transparente alrededor del mando, que estalla al tomarlo; motas del exterior distintas a las del interior.
- ✅ Tu alma elegida queda al centro del Hall, más chica y sin anillo; los anillos flotantes viejos están apagados (el código se conserva); con el cortafuegos se elige la del centro.
- ✅ Timbre que se hunde 1 cm en 0,12 s mientras lo aprietas; timbre, almas y mando al alcance de la mano.
- ✅ Agilidad (VOAir 0,5, caminatas más cortas) y 25 perillas de ritmo en el panel.
- ✅ Las puertas se abren solas cuando pasa el alma (regreso, SHARE y salida con el pez como LeadActor); la salida ya no dice "Your soul will lead the way".
- ✅ La cara del botón del timbre (arreglada el 09-30 a las 02:48).

### HUD y cargas
- ✅ HUD píldora alargada:
  - anillo y ameba a la derecha, EEG al centro y pulso a la izquierda (la hermana de tu alma, que late);
  - base translúcida con marco fino y transparente;
  - perillas de curvatura, escala y opacidad;
  - el EEG nace de derecha a izquierda y queda dentro del marco;
  - se ve por delante de todo; el HUD viejo se quitó.
- ✅ La hermana visible en la Obra (el template estaba en 0; arreglado y guardado).
- 👁 La línea del EEG en la Obra: todo vivo en PIE, pero el visor no la confirmó.
- ✅ Carga:
  - aviso con temblor + háptico → ¡pum! → el alma reaparece al frente girando;
  - el borde del HUD se ilumina y da la vuelta;
  - sin la "pelota";
  - halo detrás, del color de la etapa y sin competir;
  - 2 s quieta y la luz queda encendida (grande y en el HUD);
  - sin el destello de un cuadro al nacer;
  - el TargetPoint mueve y escala la carga.
- ✅ Carga final de 6 s: gira, vibra, háptico, cinco explosiones y un anillo de color por etapa. El entorno se va a negro mientras carga.
- 🟡 La vuelta de la carga común (ver resumen).

### Entering (respiración)
- ✅ Partículas que entran por la boca al inhalar y salen al exhalar, pegadas a la cabeza: cono más cerrado, mismo tamaño, salida instantánea, no se cortan al mover la cabeza.
- ✅ Más niebla, polvo, ráfagas y vida; más partículas de ambiente y más lejos; perillas del valle.
- ✅ Las lomas ondulan siempre y más rápido al exhalar.
- ✅ Pacer blanco (no gris, `EmissiveAlpha`); el metaball ya no se pone gris al respirar.
- ✅ Metaball que nace por morfeo y se va con animación.
- ✅ Exploración libre (12 s) → cuenta 3, 2, 1 → pacer 3 s después; 5 ciclos 4-3-4-3; un punto por ciclo + arco de avance.
- ✅ El mando se convierte en el sensor azulado; el bug del sensor que a veces no aparecía está arreglado.
- ✅ Ensayo probado de punta a punta en Test_Entering.

### Recognizing (latido)
- ✅ Al llegar, el mar ondula suave, sin pulsos; la esfera aparece con las instrucciones.
- ✅ Un pulso visual por cada latido que suena (no uno por medio); paleta blanca-rojiza; la esfera se hunde con animación al final.
- ✅ Termina con **38 latidos** (antes 75, la mitad).
- ✅ Lunas: nacen con cada latido; hay latido de respaldo si no llega señal (1 s con datos simulados); probado en el PIE completo.
- ✅ El sensor se tiñe rojizo en StageIntro y se suelta en StageOutro (en el log de la Obra; 👁 el color, en el visor).

### Loving / Mind
- ✅ Líquido del cerebro con curl y sin pulso; partículas de cara a la cámara; rayos cáusticos animados; células lejanas en la niebla; ameba central con sombreado y membrana más redonda y más translúcida; menos sci-fi.
- ✅ Paleta morada poco saturada; célula centrada al frente y un poco más lejos; reactividad a la actividad más marcada; el mundo se acelera con la actividad; partículas de los brazos arregladas; células medias con membrana translúcida y núcleo perla (ya no "globos").
- ✅ Solo manos (sin sensor), que mueven las partículas.
- ✅ Sensación de avanzar: las partículas fluyen hacia ti a 25 cm/s desde Begin y frenan en el outro; el pawn y la neurona quedan quietos (perilla TravelSpeed).

### Attracting (secuenciador)
- ✅ Salar de Uyuni pastel, esferas y gusano con la paleta. El piso con patrón quedó **apagado y blanco**, como pediste; el código se conserva para volver a trabajarlo.
- ✅ Botón SAVE: hover + gatillo, se hunde y se carga.
- ✅ Animaciones de entrada y salida; Alma primero, después el gusano y después las esferas.
- ✅ Halo de partículas curl en cada esfera, que se deshace al agarrarla y vuelve al soltarla.
- ✅ Hover sin sonido ni háptico; reloj de 90 BPM de autor.
- ✅ Mando de la obra con gatillo animado (`bQuestCtrl`; 👁 visor).
- ✅ Con datos simulados cierra a los 90 s si nadie juega (`SimStageMax`).

### Surrounding (dibujo), etapa cerrada por ti el 09-29
- ✅ Océano oscuro y mate, avance lento, niebla y polvo; Ambient Clip 7.
- ✅ Paleta 3D completa:
  - selección elevada e iluminada; círculo central pintado con la textura; slider de tamaño; undo/redo al 65 %, sin superponerse y legibles con la mano izquierda;
  - rotación desde el centro con perillas que funcionan; offset; spin en su plano;
  - menos emisivo, con grano;
  - colores "A" con degradé, aro verde agua;
  - estela tipo Tilt Brush fina y corta, que funciona desde el inicio; halo en la punta, más brillante que su color;
  - tinta en arco verde pastel = largo de la etapa;
  - animación de aparición con sonido;
  - color de la mesa y tamaño mínimo/máximo del pincel en el director.
- ✅ Optimización del trazo largo (sin caída de cuadros, sin desplazamiento del inicio, trazos cortos suaves); gatillo animado; mando nuevo espejado.
- ✅ Con datos simulados cierra a los 90 s si nadie dibuja.

### Final (regreso, resultados, compartir, constelación)
- ✅ A negro durante la última carga → el alma sale como pez-cometa sutil (partículas chicas del color del alma) → las puertas se abren solas → el Hall.
- ✅ Cuadro de resultados:
  - estética del HUD con bisel; "Your Journey Through Soul Charger";
  - EEG resumen, curva del latido, un anillo por ciclo de respiración, el gusano con tu melodía;
  - explicación con el láser y sonido de la paleta; el cuadro más alto (sin chocar con el piso);
  - el anillo grande a la izquierda, casi del alto del cuadro, que vuelve animado; el dibujo a la derecha, con su animación de crecimiento (👁 con un dibujo real).
- ✅ El gusano suena cuando el pawn ya se detuvo (el pad arranca 0,5 s después).
- ✅ Láser y puntero en resultados (fuera del modo solo-captura; 👁 visor).
- ✅ **Compartir**:
  - 25 s para explorar → Alma invita → SHARE / DON'T SHARE con hover + gatillo (se hunden) → respuesta;
  - SHARE: se va lo del frente, tu alma se desprende y nada con campanitas hasta la puerta, que se abre sola; en la constelación aparece **sin anillo y con halo**;
  - DON'T SHARE: se desvanece y no está en la constelación.
  - **Probado en PIE en las dos ramas, 0 errores.**
- ✅ Alma se va para siempre después de los resultados; las VO siguientes son omnipresentes; su reacción a la voz es suave; tiene su aura curl; look de la maqueta en las 7 Almas.
- ✅ Constelación: título SOUL CHARGER + créditos, 1 min, fundido y el nivel se reinicia.
- ✅ Sonidos provisorios para todas las animaciones nuevas.

### Mesh 3D (modelos)
- ✅ Investigación de frosted glass; paleta (40 cm, sin reflejos, íconos y textos blancos, undo abajo).
- ✅ Mando de la obra modelado desde cero: forma orgánica tipo Quest, solo gatillo, cuerpo negro y tapa gris-blanca, espejado.
- ✅ Sensor de Breath: cara plana, hendidura de luz, aros constantes hacia afuera, media esfera atrás con otro material, 5 cm de espesor.
- ✅ Timbre (base, aro, slider transparente abajo, botón ancho que se mueve) y botón SAVE (15 cm, aro que da toda la vuelta, más luz al apretar).
- ✅ Aparición "luz primero" (1,5 s, con sonido) en paleta, timbre, SAVE, sensor, anillo y HUD.
- ✅ HUD y cuadro de resultados modelados; material del anillo más claro y con aro de luz cálido; botones SHARE / DON'T SHARE.
- ✅ La cara del timbre (arreglada el 09-30 a las 02:48).

### APK
- ✅ APK de la Obra en el Escritorio, en dos versiones (un solo archivo de 268 MB, o APK + OBB), **rehecho a las 23:03 con el fundido de voz y el Hall T5**. Antes, un PIE de la Obra hasta la primera etapa: 0 errores.
  - Development, con aviso y datos simulados, autoplay y paquete propio `com.almadigital.soulcharger`.
  - El cortafuegos de compartir elige SHARE en este modo.
- ✅ Calidad máxima en la Quest: `r.MSAACount=4`, render al 125 % (`xr.SecondaryScreenPercentage.HMDRenderTarget`), FFR apagado (`xr.OpenXRFBFoveationLevel=0`), en `Config/Android/AndroidEngine.ini`.
- 👁 Sin correr todavía en la Quest.
