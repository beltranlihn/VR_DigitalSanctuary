# Soul Charger — documento maestro de la obra

> 🔴 **Esta es la fuente autoritativa de la obra completa.** Reemplaza a [`Soul-Charger-Design.md`](../Soul-Charger-Design.md) de la raíz, que es previo al pivote a Quest y quedó desactualizado en narrativa, mecánicas y arquitectura. Donde choquen, **gana este documento**.
> Lo técnico-operativo de Unreal vive en la skill `unreal-vr`. El detalle por etapa, en `docs/stages/`.
>
> Última revisión completa de guión: **2026-08-06**.

---

## 1. Qué es

Experiencia de **VR inmersiva de biofeedback y meditación** para **Meta Quest 3 standalone**. **Sentada, un solo usuario, ~15 minutos.** Un asistente ayuda a colocar el EEG y los mandos antes de empezar.

El usuario entra al **Soul Charger Center**, donde lo recibe **Alma** —una figura abstracta tipo ameba, audioreactiva— que lo guía por **cinco etapas**: *Entering, Recognizing, Loving, Attracting, Surrounding*. En cada una realiza un ejercicio distinto y **carga poco a poco su alma**, que al final queda representada en una escultura personalizada y se suma a una constelación de almas de usuarios anteriores.

Construida en colaboración con el departamento de **Bioética de Johns Hopkins University** y el **Instituto Berman**. Eso no es decorativo: obliga a que **la medición sea legible y consentida**, y a que ningún dato se presente como una afirmación clínica que no se puede sostener.

**Sensores:** EEG (Muse) enviando actividad neuronal y ritmo cardíaco por **OSC** desde un PC — probado y estable. Respiración detectada con el **motion controller** apoyado en el estómago.

---

## 2. 🔴 Reglas transversales — lo más importante del documento

Estas cinco reglas gobiernan todas las etapas. Si una decisión de diseño las contradice, la decisión está mal.

### 2.1 Capa autoral + capa viva
**Toda interacción de biofeedback tiene dos capas superpuestas:**
- **Capa A (autoral):** ocurre siempre, define el ritmo, garantiza que la etapa termine y que se vea bella. Es la que sostiene la obra.
- **Capa B (viva):** los datos del usuario modulan amplitud, suavidad, color, densidad **encima** de la capa A.

Si respiras con la obra, el anillo florece entero. Si no, se mueve igual pero pequeño y apagado. **Nadie falla, nadie se traba, y el que se entrega ve visiblemente más.**

Esto no es un parche: es lo que hace que un EEG desconectado, una respiración no detectada o un usuario que no entendió **degraden con elegancia en toda la obra**, con una sola arquitectura en vez de cinco soluciones ad hoc.

### 🔴 Tiempo autoral vs tiempo del usuario (dicho por Beltrán, 2026-08-12)
*"Hay tiempos que van a ser más rápidos o cortos dependiendo del usuario: tocar el timbre, seleccionar la proto ameba, avanzar por los menús de instrucciones."*

| Va por **timer** (tiempo autoral) | Va por **evento** (tiempo del usuario) |
|---|---|
| el negro inicial, los logos, los fundidos | el menú Start / About |
| la caminata entre salas | el timbre del Center |
| el cierre de una etapa por su mecánica | elegir el Proto Soul |
| | pasar las páginas de instrucciones |

🔴 **Nada que el usuario tenga que hacer se cierra con un timer.** Si se hace, o se le corta algo a mitad o se lo deja mirando algo que ya terminó. Y al revés: lo autoral **no** espera al usuario, porque entonces la obra pierde su pulso.

### 2.2 Nunca hay callejón sin salida
Ninguna etapa puede quedarse esperando. Cada momento de espera tiene: **tres variantes de línea de voz** que invitan sin repetirse y, pasadas esas, **el sistema baja la exigencia o avanza solo**. El anillo de carga aparece igual. *Nadie debería quedar fuera de su propia alma por respirar distinto.*

### 2.3 El gesto cuenta la historia
El orden de las etapas es un arco del gesto y hay que **nombrarlo**, no solo ejecutarlo:

| | Etapas | Gramática |
|---|---|---|
| **Hacia adentro** | Entering, Recognizing | el mando es una sonda contra tu cuerpo |
| **Bisagra** | Loving | no haces nada; el sensor se cierra y se aquieta |
| **Hacia afuera** | Attracting, Surrounding | el mando apunta y crea |

Alma lo articula: *primero vas a escucharte, después vas a soltar, después vas a alcanzar.*

### 🔴 El arco empieza ANTES de las etapas, en el menú (decidido 2026-08-12)
El arco del gesto arranca en la primera interacción de la obra y **el puntero llega tarde a propósito**:

| Momento | Gesto | Confirmación |
|---|---|---|
| **Menú** (Start / About) | **tocar** con la mano | **hover + gatillo** |
| **Timbre** del Center | **apoyar** la mano | **esperar** (sostener) |
| **Sensor**, y las 4 primeras etapas | **tomar** con la mano | contacto |
| **Attracting** | **apuntar** | el beam, que aparece **recién acá** |

**Por qué el menú no usa beam:** si la primera interacción fuera con puntero, se enseñaría una herramienta para abandonarla durante cuatro etapas y recuperarla al final. Tocando, el menú **rima con el timbre que viene tres segundos después** y con tomar el sensor, y el beam queda como **capacidad nueva** que se gana en *Attracting*. Además, tocar enseña *tus manos son reales acá*, que es la tesis de la obra.

💡 **El timbre es el único que se confirma esperando**, y por eso es el que enseña la paciencia del resto de la obra.

### 2.4 El ritual se repite, la intensidad crece
La estructura *instrucciones → ejercicio → carga* se repite cinco veces a propósito — el ritual **es** la meditación. Lo que **no** puede repetirse idéntico es la carga:

**Anillo 1:** ~4 s, casi silencioso, íntimo → **Anillo 5:** ~20 s, música completa, la escultura entrando.

Y **el patrón se rompe una sola vez, a propósito**: en *Loving* no hay widget de instrucciones. Esa desviación única resetea la atención.

### 2.5 Medir es parte de la obra, no un backend
La medición se muestra, se explica y se enmarca como relación, no como diagnóstico. El lenguaje siempre es **recorrido**, nunca **puntaje**:
- ❌ *"Tu nivel de calma: X"* · *"Tu calma subió un 20%"*
- ✅ *"Así se movió tu calma"* · *"Hiciste cinco respiraciones profundas"*

---

## 3. Estructura narrativa

| # | Escena | Duración aprox. |
|---|---|---|
| 0 | **Intro** — negro 2 s, tres logos de 1 s (*Made with Unreal*, Alma Digital, Johns Hopkins), luego el título **Soul Charger** con *An interactive VR Biofeedback Experience*, y dos botones: **Start** y **About Us**. Todo esto pasa **en el exterior** (ver 6.b) | ~10 s + lo que tarde el usuario |
| 1 | **Oscuridad** — voz femenina espacializada, preguntas que instalan el mood | ~45 s |
| 2 | **La caminata** — desde el botón Start el pawn ya avanza por spline. Pasos, silueta de puerta, *Soul Charger Center*. Timbre: apoyas la mano y te escanea | ~45 s |
| 3 | **Hall** — Alma te recibe, explica las 5 etapas, calibración, eliges tu Proto Soul | ~90 s |
| 4–8 | **Las cinco etapas** | 5 × ~2 min |
| 9 | **Sala final** — la arquitectura se transforma (no hay compuerta) y **se vuelve a estar en el exterior**: gráfico de datos, **la pregunta de Alma y la elección**, constelación, despedida | ~2 min |
| | **Total** | **≈ 14–15 min** |

> ⚠ **El presupuesto es real: la obra da ~15 min, no 10–12.** Para festival es una duración normal, pero hay que asumirlo. **Si hay que recortar, se recorta intro y final, no las etapas** — ahí están los ~3,5 min más pasivos.
>
> ⚠ *Attracting* y *Surrounding* son abiertas y se pasarán de 2 min casi siempre. Cierran con **invitación suave** (el pad crece, la luz se entibia, Alma habla), nunca con corte seco.

> 🔴 **La caminata de la intro tiene dos trabajos:** instala el mood **y es donde se toma el baseline** (§5). Conviene que sean **30–40 s de avance estable**, para que la medición tenga de dónde promediar.

### El giro final: la pregunta de Alma

🔴 **Es el único momento de la obra donde algo está en juego.** Sin él son cinco beats de "haz algo" y un certificado; con él, la obra deja una pregunta abierta que el usuario se lleva puesta. Y no hay que inventarlo: la obra trata sobre **qué significa medir un alma**, y la colaboración con Bioética deja de vivir solo en los créditos.

Justo antes de la constelación, **Alma cuestiona lo que ella misma acaba de hacer**:

> *"¿Esto eres tú? ¿O es solo lo que yo pude medir de ti?"*

Y **no la responde**. La deja abierta.

Lo que la hace funcionar es **quién la dice**: Alma es la que midió. Que dude de su propia medición es lo que le da peso — dicha por un narrador externo sería una moraleja; dicha por ella es una confesión.

**Reglas de la línea:** corta, la dice Alma, y **queda sin respuesta**.

> *Alternativas registradas por si se ajusta el tono:*
> *— "Medí tu respiración, tu pulso, tu atención. Pero no sé si eso es tu alma." (más tierna, Alma admitiendo su límite)*
> *— "Esto es lo que registré. Lo que eres, solo lo sabes tú." (la más segura y afirmativa)*

**Puesta en escena:**

1. El alma completa al frente, sonando.
2. El gráfico se dibuja solo. *Esto es lo que pude medir de ti.*
3. **Silencio de 5–10 s.** La obra viene densa de eventos y lo necesita.
4. Alma aparece y hace la pregunta.
5. Ofrece la elección: **quedarse el alma o darla a la constelación.**

🔴 **Las dos respuestas llevan a un final construido.** Si "no" fuera un callejón, la elección sería falsa y se nota.

| Elección | Gesto | Resultado |
|---|---|---|
| **Compartir** | empujar el alma hacia arriba con la mano | la constelación aparece y el alma se suma a ella |
| **Quedarse el alma** | traerla hacia el pecho | la constelación aparece igual, **sin ti**: se ve a los demás desde afuera |

El segundo final es **más barato de construir** — la misma escena menos un elemento — y probablemente el más conmovedor. Nadie sale sintiendo que eligió mal.

🔴 **El cierre es un gesto del usuario, no un fundido.** Es la misma interacción en dos direcciones, y resuelve el final pasivo que tenía el guión original.

### El timbre es el tutorial
Apoyar la mano para que te escanee **es la misma gramática que tomar el sensor**. Enseña el gesto en los primeros 60 segundos sin decir "tutorial". El timbre y los sensores deben **parecerse visualmente** para que la rima sea evidente.

---

## 4. Las cinco etapas

| Etapa | Color | Ejercicio | Señal | Movimiento |
|---|---|---|---|---|
| **Entering** | azul | Respiración con el mando en el estómago. **5 ciclos.** La sala entera respira contigo | respiración (mando) | estático |
| **Recognizing** | rojo | Mando en el pecho. Con cada latido emanan anillos y hay háptico. **Asciendes** | ritmo cardíaco | 🔴 **hacia arriba** |
| **Loving** | morado | Contemplativo, sin sensor. Alma hace **3 preguntas**; con cada una la figura **cambia de forma** | actividad neuronal | estático |
| **Attracting** | naranja | Atraes burbujas sonoras con el puntero y compones tu melodía en un secuenciador de 5 slots | — | estático |
| **Surrounding** | verde | Dibujas tu propia capa alrededor del alma. Mandala por simetría radial | — | estático |

### Entering
🔴 **Aquí el widget con video SÍ va.** El gesto de respirar con el mando en el estómago **no es intuitivo para nadie** — sin instrucción visual la gente falla en 10 segundos y abandona emocionalmente la obra entera.
La voz **no cuenta las respiraciones en voz alta** (convierte el ejercicio en tarea con marcador). El conteo vive solo en lo visual.

### Recognizing
🔴 **La subida es autoral: siempre subes, siempre llegas.** El latido modula los anillos y el háptico, no el avance.
**Continua y monótona, sin rebotes.** Los "saltos de trampolín" del guión original son exactamente lo que marea: cada aceleración es un evento vestibular. Y hay que dar una **referencia vertical fija** (columna de luz, anillos que pasan) para que el cerebro tenga un riel.
Si no se detecta pulso, el fallback **no es un ritmo inventado**: se maneja con la respiración, que sí controlamos.

### Loving
Sin widget (la ruptura deliberada del patrón). Tres preguntas, ~35–40 s cada una.
- **Capa A:** la forma cambia con cada pregunta. Discreta, fiable, es la narrativa.
- **Capa B:** dentro de cada forma, el EEG mueve amplitud, agitación y temperatura de color.

La última pregunta prepara la pregunta grande del final.

### Attracting
El botón **FINISH MELODY** se enciende con los 5 slots llenos, pero **el timeout guarda lo que haya**. Guardar con 3 está bien: *la melodía de tu alma dura lo que alcanzaste a componer.*

### Surrounding
Dibujas **alrededor**, no adentro — dentro de un volumen semitransparente tu propia mano te tapa el trazo y dibujas a ciegas.

**Cuatro restricciones que hacen imposible dibujar algo feo, sin decirle a nadie qué dibujar:**
1. **Simetría radial** (probar con **5 ejes**: impar, orgánico, y rima con las 5 etapas). Cualquier garabato se vuelve mandala.
2. **Cascarón entre dos radios**: límite interior (por fuera del último anillo) y exterior. Todo lo dibujado es, por geometría, una capa.
3. **Paleta bloqueada**, derivada del color del alma elegida.
4. **Presupuesto finito de trazos.** La escasez produce composición.

**El límite:** al salir del cascarón **deja de emitir puntos nuevos**; el trazo se corta y se reanuda al volver a entrar. 🔴 **Nunca borrar lo ya dibujado.** El borde brilla suave al acercarse, para que la regla se aprenda con el cuerpo.

🔴 **Mientras dibujas, la ameba ya muestra sus cuatro anillos.** Compones encima de lo que construiste, ves exactamente lo que vas a ver al final (sin escalados ni sorpresas), y la última etapa se convierte en la culminación visible de las otras cuatro.

**Tu capa es el sexto anillo — el único hecho a mano.** En la carga final se contrae y entra en el alma.

---

## 5. Medición, HUD y resultados

### El HUD es la ameba
Ni pegado al casco (incómodo, borroso en los bordes, rompe el lugar) ni reloj (compite con el sensor que llevas en la mano).

**El Proto Soul es la lectura:** su **pulso** es tu ritmo, la **agitación de su superficie** es tu calma, sus **anillos** son la carga. Cero números, cero paneles, y es el objeto del que trata la obra.

**Ubicación:** en VR no hay esquinas, hay **grados**. Dentro de ~20° del eje de mirada, **ligeramente por debajo del horizonte** (la mirada en reposo cae abajo; mirar arriba cansa). **Lazy-follow** con zona muerta de ~10° y recuperación de ~1 s, sin rotación rígida.

**El punto de conexión del sensor va en el sensor**, no en el HUD.

### Qué se mide y cuándo
| Señal | Cobertura |
|---|---|
| Calma (EEG) | toda la experiencia |
| Ritmo cardíaco (EEG) | toda la experiencia |
| Respiración (mando) | solo durante *Entering* |

**Baseline: la caminata hacia la puerta.** Todos hacen lo mismo, el mismo tiempo, sin tarea ni decisiones, y sin la carga emocional de las preguntas en la oscuridad. **Se toma en silencio** — el usuario solo ve la calibración narrativa del hall, que es la que instala el concepto.

**Segunda medición corta al final**, en la sala etérea, misma postura y misma ausencia de tarea, para comparar peras con peras.

⚠ A los 90 s dentro de un visor eso no es reposo clínico: es una **referencia interna de la obra**. El gráfico debe decirlo así.

### El panel de resultados
- **Calma y ritmo**: dos líneas continuas sobre el mismo eje de tiempo, con **las cinco bandas de color de las salas** como fondo. Sin grilla, sin números, sin ejes — parece un dibujo, no un dashboard.
- **Respiración**: **cinco pétalos radiales**, no una onda. Amplitud = profundidad, ancho = duración. Un pétalo pequeño no es un error. Rima con el mandala y con los anillos.
- **Jerarquía:** lo más grande es la comparación **inicio → final** de la calma.
- **Se dibuja solo**, de izquierda a derecha, en 6–8 s con la música. Un gráfico que aparece de golpe es una pantalla de resultados; uno que se traza es un recuerdo que vuelve.

🔴 **Modular: cualquier módulo puede faltar y el panel nunca queda vacío ni muestra un error.** Sin EEG, quedan respiración, melodía y escultura. Los huecos dentro de una línea se ven **tenues**, no rotos: un hueco roto parece falla, uno callado parece un pasaje.

⚠ **Va a haber gente cuya calma baje. Eso no se maquilla** — menos en una obra revisada por bioética. Se resuelve con la metáfora: si el gráfico se lee como *altura = mejor*, toda bajada es una mala nota; si se lee como **un paisaje que recorriste**, no hay bueno ni malo. Y eso es literalmente lo que el dato es.

---

## 6. Estética

**Referencia: James Turrell — pero Turrell es luz, no geometría.** Su tema es que no encuentras el borde: las superficies se disuelven.

- ❌ **Low-poly estilizado**: da aristas duras y facetas visibles. Pelea contra la referencia.
- ❌ **Realista tipo archviz**: el hall de la versión anterior tiene *mobiliario* (paneles, aros de techo, pedestal) y por eso se lee como render de arquitectura, no como espacio de Turrell.
- ✅ **Luz imposible sobre casi nada de geometría.** Superficies grandes y curvas, sin esquinas visibles, sin props, sin detalle de textura. Todo el trabajo en **gradientes emisivos**.

**Despojar el hall:** Alma debería ser lo único que hay en esa sala.

Lo bueno: en Quest 3 eso es también **lo más barato de renderizar**. Cuando la restricción técnica y la dirección artística coinciden, la dirección es la correcta.

**Entering: estático, y respira la sala entera** — muros, luz, volumen del ambiente, no solo un anillo. Nada de túnel tipo Flowborne: si avanzas, el usuario lee su respiración como propulsión; si te quedas quieto y el espacio se expande, la lee como **aquello que crea el mundo**. Lo segundo es la tesis de la obra.

### 6.b El exterior, y que la obra vuelve a él
La obra **empieza y termina afuera**: se arranca en un exterior, se entra al Center, se recorre entero, y al final —para la constelación— **se vuelve a estar en el exterior**. Los interiores (Hall y etapas) son salas que aparecen *dentro* de ese afuera.

- El exterior es un **vacío negro azulado infinito**, con un degradado vertical suave: el degradado es lo que lo hace leer como **amplitud** y no como vacío plano.
- 🔴 **La profundidad la van a dar las PARTÍCULAS, no el fondo.** Lo que vende escala es el **paralaje**: un campo disperso de puntos a distintas distancias hace más que cualquier gradiente.
- 🔴 **Que el cielo del final sea EL MISMO del comienzo es lo que hace legible el regreso.** Conviene que sea el mismo sistema de partículas en los dos momentos: es la firma que cierra el arco.
- **Consecuencia para la sala final:** para devolver el exterior, la sala final tiene que **abrirse** —esconder su muro—, no sólo bajar la luz. Es la única metamorfosis de la obra, y ahora se sabe *hacia qué* se transforma.

### 6.c 🔴 Cero luces: todo es unlit + emisivo (decidido 2026-08-12)
La obra **no tiene ninguna luz**: ni direccional, ni sky, ni atmósfera, ni niebla. Todo el color sale de **materiales emisivos**. Si algún día hace falta un punto de luz concreto, es una **excepción deliberada y local**, no el modo de trabajo.

Encaja por tres lados a la vez: es Turrell (luz en el aire, no objetos iluminados), es lo más barato en el renderer móvil, y evita depender de horneado.

⚠ **La consecuencia práctica, que ya costó una sesión:** sin luces, **cualquier material *lit* renderiza negro sobre negro**. Al traer un asset nuevo —del template, del motor, de donde sea— lo primero es mirarle el *shading model*.

**Transiciones:** salas y compuertas, no arquitectura que se transforma — la metamorfosis es espectáculo y compite con la contemplación; la puerta dice *estás entrando a un lugar*, y da el título de cada sala. **La única transformación se guarda para la sala final**, donde ya no hay compuerta.

---

## 7. El sensor

**Se toma una vez, se conserva siempre.** Recupera ~1 min de instrucciones repetidas y elimina el beat que se volvería monótono a la tercera.

La puntuación de inicio de etapa **la da la transformación de la herramienta**, no volver a tomarla: entras a la sala, el instrumento se reconfigura solo, y eso *es* el aviso.

| Etapa | Estado del sensor |
|---|---|
| Entering | cono suave desde una cara → te dice qué lado va contra el estómago |
| Recognizing | el mismo cono, más corto y pulsando → pecho |
| Loving | **se cierra y se aquieta** → sin decir nada, comunica "no me necesitas" |
| Attracting | el extremo se abre en emisor → de ahí sale el haz |
| Surrounding | la punta se afina en pincel |

**Versión barata:** cuerpo idéntico siempre, se intercambia solo la punta.

### Mano hábil
1. *"Toma el sensor con la mano que te resulte más cómoda"* → **esa mano queda registrada como hábil**. Se descubre haciendo, no se pregunta en un menú.
2. Aparece de inmediato el **segundo sensor, cerrado y dormido**. Si apareciera recién en *Attracting* sería un objeto nuevo a mitad de obra.
3. Widget con video: *"apóyalo contra tu estómago así"* → aquí ocurre la calibración de posición de reposo.

🔴 **La mano hábil tiene que ser una variable en todo el pipeline de respiración, no un supuesto.** Si alguien toma con la izquierda y el detector sigue leyendo el mando derecho, la etapa falla en silencio y parece problema del usuario.
**Si nadie toma nada** en N segundos: se asigna la derecha y se sigue.
**Solo una mano activa por defecto.** *Attracting* es la única etapa que enciende ambas; en *Surrounding* la mano que descansa no debe poder rayar.

---

## 8. Variabilidad entre sesiones

```
DA_SoulBank    → 20 mallas + colores. Se muestran 5 por sesión.
DA_SoundBank   → 5 bancos, cada uno con 1 pad + 20 sonidos. Se elige 1 por sesión.
```

🔴 **Rotación, no azar.** Con random puro, dos personas seguidas en la fila de un festival pueden recibir lo mismo. Un **índice que avanza en cada sesión**, guardado en un SaveGame de la instalación, garantiza variedad entre visitantes consecutivos, que es donde de verdad se nota.

**Lo personalizado es:** malla base, color, melodía, escultura y el gráfico.
**Los cinco anillos son iguales para todos.** Eso hace que la constelación signifique algo —mismo ritual, interior propio— y además es mucho más barato que anillos personalizados que nadie puede comparar contra nada.

---

## 9. Arquitectura técnica

### 9.1 Un nivel persistente, salas como sublevels
No se puede caminar por un spline hacia una pantalla de carga, y el sensor, la ameba y los datos tienen que sobrevivir a las transiciones.

**Nivel persistente** con el pawn y todo lo que perdura + **salas como streaming sublevels** que cargan y descargan alrededor del jugador. Con eso: caminata continua, solo dos salas en memoria a la vez, y nada se destruye.

⚠ **Los niveles de test NO se tiran.** Se siguen usando para iterar cada mecánica aislada; el nivel persistente es de **ensamblaje**.

### 9.1.b 🔴 Spawnear, matar, y ubicar con TargetPoints (regla de Beltrán, 2026-08-12)
*"Ojalá tooodo hagamos que se spawnee y después que se elimine. Siempre usando target points para que sean fáciles de ubicar. Por lo menos todo lo que se pueda y valga la pena. VR se trata de optimizar."*

1. **Nada existe antes de su momento.** Si el usuario todavía no lo tiene que ver, **no está spawneado** (no "escondido").
2. **Nada sobrevive a su momento.** Lo que ya no se usa se **destruye**. Cero residuos.
3. **La posición se autora con `TargetPoint` + tag**, nunca con coordenadas en Blueprint. Se mueve en el viewport, sin tocar código, y las cosas quedan **simétricas por construcción**.

Tags en uso: `MenuSpawn` (los botones del menú) · `SoulSpawn` (las Proto Souls elegibles) · `BubbleSpawn` (las burbujas de *Attracting*).

💡 **Beneficio no obvio:** el bug de "un botón más arriba que el otro" **desaparece** cuando los dos salen de puntos autorados. Y agregar un tercero es un punto más, no código.

### 9.2 Movimiento y transiciones

**El efecto de caminata — validado en visor (2026-08-06).** Traslación vertical + giro suave de cámara de lado a lado + viñeta. Probado y cómodo.
- Vertical **1,5–2 cm**, angular **1–2 grados**.
- 🔴 **Acoplado a la cadencia de las pisadas**, nunca una oscilación independiente. Lo que marea es el roll rápido o desincronizado; a ritmo de paso el cerebro lo lee como locomoción y lo acepta.
- La amplitud entra y sale con la rampa de velocidad. Aceleración suave (~1 s) y velocidad constante en el medio: **la aceleración es lo que marea, no la velocidad**.
- **Viñeta dinámica** mientras hay movimiento, fuera al detenerse. Reduce el flujo óptico periférico, que es el motor real del mareo.
- ⚠ La susceptibilidad varía muchísimo entre personas. Dejarlo como **parámetro ajustable, incluso a cero**, y probarlo con gente ajena al equipo antes de cerrarlo.
- 🔴 **El suelo necesita patrón.** Sin referencia visual, el avance no se lee como avance y la caminata se siente rara sin que se sepa por qué.

**Velocidad y distancias.** Salas de 10 m de diámetro → centro a centro ~10–12 m. A **1,5–2 m/s son 5–7 s**, que es el largo correcto de un beat de transición.

**Recognizing es el único cambio de movimiento: hacia arriba** — y con otra personalidad. La caminata es **rítmica**; la subida es **continua y lisa, sin bob ni pasos**: flotas. 🔴 Necesita una **referencia vertical fija** (columna de luz, anillos que pasan al lado): sin ella, ascender en un espacio liso y curvo es de las cosas peor toleradas, porque el ojo no tiene con qué medir el movimiento.

**El vacío negro entre salas.** La puerta abre a **negro absoluto**, igual que la entrada al Center en la intro. Nada de portales reales (scene capture es caro en Quest) ni de salas contiguas.

🔴 **Todas las salas se construyen en el MISMO origen.** El pawn avanza hacia el umbral, el negro tapa el intercambio, y vuelve al centro sin que se note. Eso elimina toda restricción de layout, hace trivial el streaming, y convierte el fundido en algo **narrativamente motivado**: entre sala y sala hay vacío. Y rima — cada transición repite el umbral de entrada a la obra.

⚠ Para que funcione, **el exterior de los espacios debe ser negro profundo**. El interior es el que está iluminado y tiene color.

**La secuencia de transición:**
```
carga del anillo  -> empieza a PRECARGAR el sublevel siguiente (Make Visible After Load = false)
la luz de la sala baja + se traza el marco de la puerta + se enciende el cartel
negro completo    -> swap: oculta A, muestra B, reposiciona el pawn
la puerta abre    -> la nueva sala sube de luz a tu alrededor
```

🔴 **La precarga es obligatoria.** El streaming en Quest no es instantáneo: si la carga ocurre en el momento del apagón, hay un tirón justo cuando el usuario está mirando. Cargando durante la animación del anillo, al llegar el negro solo hay que **hacerlo visible**, que sí es instantáneo.

Y aunque la luz de la sala haga el trabajo narrativo, **mantener un fundido a negro real por encima** que llegue a 1.0 en el instante del swap. Es el cinturón de seguridad: si algo hitchea, no se ve.

**Placeholder de sala:** disco de piso de **10 m** con patrón sutil + cilindro de muro de **4–5 m** de alto, sin techo. No hace falta recortar el hueco de la puerta: como el fundido ocurre antes de llegar, el clip no se ve.

### 9.3 Los cinco objetos persistentes

| Objeto | Responsabilidad |
|---|---|
| **`GI_SoulCharger`** (GameInstance) | Quién fue este usuario: malla, color, melodía, escultura, las 180 casillas de datos, el índice rotativo de bancos. Sobrevive a cualquier `OpenLevel`. |
| **`BP_BioHub`** | Ingesta OSC → binning → suavizado. **Única fuente de verdad** de calma y ritmo. Expone valor actual, promedio y flag de conexión. |
| **`BP_Sensor`** | Uno por mano, persistente. Enum de estado + malla que se reconfigura por etapa. |
| **`BP_ProtoSoul`** | La ameba: lazy-follow, anillos, reacción en vivo, animación de carga. Es también el HUD. |
| **`BP_NarrationDirector`** | Cola de VO: disparo por evento, por entrar a estado y por inactividad. Con variantes y **sin bloquear**. |

🔴 **El BioHub no sabe nada de etapas y las etapas no saben nada de OSC.** Si se cambia de dispositivo, se toca un solo Blueprint.

### 9.4 `BP_StageBase`
```
BeginStage()
  → instrucciones (o saltarlas)
  → configurar el sensor para esta etapa
  → RunStage()        ← lo único que cada etapa sobreescribe
  → ChargeAnimation(índiceAnillo, intensidad)
  → abrir compuerta / avisar al director
```
Duración, timeout, si lleva widget y la intensidad de la carga son **variables de instancia**. El crescendo de las cargas pasa a ser un número por etapa, y los cortafuegos de inactividad se implementan **una sola vez**.

**`BP_StageDirector`** en el nivel persistente lleva la lista ordenada, mueve el pawn por el spline y maneja las compuertas.

### 9.5 Captura de datos: casillas, no muestras
**180 casillas** para toda la experiencia (~5 s cada una). Cada una acumula **suma, cantidad de muestras, mínimo y máximo**, más **a qué etapa pertenece**.

Eso resuelve de una sola vez: el suavizado (promediar en ventanas de 5 s *es* el filtro), la memoria (180 en vez de 9.000), los huecos (cantidad de muestras en cero es un hueco *explícito*, no un cero que parece dato), el tamaño fijo de la geometría, y las bandas de color del gráfico.

### 9.6 Dibujar el gráfico
**Ribbon 3D reusando el generador de trazos de *Surrounding***. Cada casilla es un punto: `x = índice × separación`, `z = valor × altura`. Ventaja no solo técnica: **el gráfico queda hecho del mismo material que el dibujo del usuario.**
Los **cinco pétalos**: cinco meshes con la escala manejada por profundidad y duración.
Alternativa rápida si urge: UMG con `OnPaint` + `Draw Lines`, con líneas gruesas (en Quest las finas alias feo).

### 9.7 Refactor de lo ya construido
- **`BP_TouchSensor`** → `BP_Sensor` persistente. No se toma en cada etapa; **la etapa le dice en qué convertirse**.
- **`BP_AimBeam`** deja de depender de que un sensor lo equipe; el gate pasa al director.
- **`BP_AttractDirector`** pierde el reloj de Quartz y la orquestación general (suben a `BP_StageDirector`); se queda con el secuenciador.
- **La melodía guardada** sube al GameInstance.

### 9.8 `BP_Door`

**Un solo Blueprint.** El mesh del marco y el color de acento son **variables** que el `BP_StageDirector` setea desde el DataAsset de la etapa: cambiar el look de una puerta es cambiar un asset en una tabla, no editar un BP.

- Dos paneles, **3 m de ancho × 4 de alto**, 10 cm de espesor, con Timeline de apertura.
- **Cartel sobre el dintel**, variable `StageName` (Text), que se enciende **por separado** de la apertura.
- **Plano negro detrás** — es lo que hace funcionar el vacío.
- Interfaz: `Reveal()` · `Open()` · `Close()` · evento `OnPawnPassed`.

🔴 **La puerta NO existe durante la etapa.** Se revela al terminar: baja la luz de la sala, una línea de luz **traza el marco** sobre el muro, se enciende el cartel, y recién ahí abre. Dos motivos: que la sala esté sellada comunica *"esto es lo único que tienes que hacer ahora"*, y evita que un elemento arquitectónico compita con el objeto reactivo en una sala que es casi vacío.

**A quién pertenece la puerta:**
- **El marco es de la sala donde estás** — es un hueco en *ese* muro, con *esa* arquitectura.
- **La luz que se cuela y el cartel son de la sala que viene.** El resplandor por la rendija ya es rojo si vas a Recognizing, verde si vas a Surrounding.

El cartel muestra el nombre de **la sala a la que vas**, por eso revelarlo al final es el momento correcto. Repite cinco veces el gesto de la entrada al Center: silueta oscura, y al abrirse aparece la luz del interior.

**Fase placeholder:** un solo marco genérico; varía únicamente el color de acento.

### 9.9 Sistema de debug

🔴 **El skip de debug y el cortafuegos por inactividad son la MISMA función.** `BP_StageBase` ya necesita una salida de emergencia (regla §2.2); esa es la que usa el debug. Cero arquitectura extra.

```
ForceComplete(bFastCharge)
```

Recorre **el mismo camino que una finalización real**: cierra los datos de la etapa, otorga el anillo, reconfigura el sensor, revela la puerta y avisa al director. Lo único distinto es que acelera la animación de carga.

🔴 **El skip nunca es "saltar a la etapa N", siempre es "completar esta ahora".** Teletransportar se salta efectos colaterales y deja estados inconsistentes que después se depuran como fantasmas. Completar deja el estado bien **por definición**, porque es el mismo código que corre en la experiencia real.

- **`BP_DebugDirector`**, suelto en el nivel persistente: se borra y listo. **Ningún código de debug esparcido por las etapas.**
- Bind a un botón poco usado (Y o menú) **con combinación**, para que no se dispare sin querer con el visor puesto.
- Gate por un bool del GameInstance que se apaga en el build.
- **HUD de debug**: etapa actual, tiempo transcurrido, conexión del sensor, calma y ritmo. Es lo que más tiempo ahorra de todo esto.
- **`JumpToResults`** que **sintetice datos plausibles** — si saltas directo, las 180 casillas están vacías y el panel no dibuja nada.

---

## 10. Orden de construcción

**El esqueleto antes que los órganos.** Las mecánicas existen pero están sueltas; el riesgo es pulir órganos que no conectan. Y las preguntas abiertas —¿dura mucho?, ¿el ritual cansa?— **solo se responden caminando la obra completa**, cosa que se puede hacer sin una sola mecánica conectada.

1. **La caminata entre dos salas vacías.** Es el mayor riesgo técnico y todo lo demás cuelga de ahí. **Probar comodidad en visor antes de construir nada más.** Cinco piezas:
   1. Nivel persistente + sublevel de sala (piso de 10 m con patrón + cilindro de 4–5 m).
   2. **Mover por spline** con rampa, bob (vertical + angular) y viñeta. Se usa desde el botón Start, antes que cualquier sala.
   3. **`BP_Door`** con revelado del marco, cartel y color de acento.
   4. El ciclo **precarga → apagón → swap → reposicionar → subir luz**.
   5. **`BP_DebugDirector`** con `ForceComplete`, desde el primer día.
2. **El trío persistente**: `BP_BioHub`, `BP_Sensor`, `BP_ProtoSoul`. Que sobrevivan a la caminata y que la ameba lata con datos reales.
3. **`BP_StageBase` + cinco etapas vacías** (instrucciones → esperar N s → carga → puerta), con cajas grises como salas.
   👉 **Aquí ya se camina la obra completa de 15 minutos** y se responden las preguntas de ritmo.
4. **Enchufar las mecánicas reales**, una por una, como reemplazo de `RunStage()`.
5. **Panel de resultados y constelación** al final.

**Todos los assets son placeholders simples** hasta que la mecánica esté validada en visor.

---

## 11. Lo que falta decidir

> ✅ **El giro final quedó resuelto** (2026-08-06): la pregunta de Alma, la elección con dos finales construidos y el cierre por gesto. Ver §3.
- Número de ejes de simetría del mandala (probar 5 en visor).
- Ancho y brillo del pincel: el primer trazo tiene que ser satisfactorio de inmediato.
