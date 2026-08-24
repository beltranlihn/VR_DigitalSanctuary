# Soul Charger — Brief de dirección de arte

> **Para quién es este documento:** para diseñar el moodboard y la dirección visual/arquitectónica de la obra, con o sin IA generativa. Reúne el guión completo, las mecánicas, los objetos que ya existen en el motor y las restricciones técnicas que condicionan el arte.
>
> **Qué NO es:** no es documentación técnica de Unreal. Todo lo que aparece acá está expresado en términos de lo que el usuario ve y hace.
>
> Fuentes: `docs/OBRA-SOUL-CHARGER.md` (documento maestro), `docs/PLAN-GUION-2026-08-14.md` (mapeo del guión), guión original de Beltrán (8 actos), e inventario real del proyecto Unreal al 2026-08-24.

---

## 1. Qué es la obra

Experiencia de **realidad virtual de biofeedback y meditación** para **Meta Quest 3**. Es **sentada**, para **un solo usuario**, y dura **unos 15 minutos**. Un asistente ayuda a colocar el sensor EEG y los mandos antes de empezar.

El usuario entra al **Soul Charger Center**, donde lo recibe **Alma** —una figura abstracta, tipo ameba, audioreactiva— que lo guía por **cinco etapas**: *Entering, Recognizing, Loving, Attracting, Surrounding*. En cada una hace un ejercicio distinto y **carga poco a poco su alma**, que al final queda representada en una escultura personalizada y se suma a una constelación de almas de usuarios anteriores.

La obra se construye en colaboración con el departamento de **Bioética de Johns Hopkins University** y el **Instituto Berman**. Eso no es un crédito decorativo: obliga a que la medición sea **legible y consentida**, y a que nada se presente como una afirmación clínica.

**Qué se mide:** actividad neuronal y ritmo cardíaco (sensor EEG Muse, por OSC) durante toda la experiencia; respiración (con el mando apoyado en el estómago) solo durante la primera etapa.

---

## 2. La tesis visual, en una frase

> **Luz imposible sobre casi nada de geometría.**

La referencia es **James Turrell** — pero conviene entender qué se toma de él: **Turrell es luz, no geometría**. Su tema es que **no encuentras el borde**: las superficies se disuelven, no sabes a qué distancia está la pared, el color parece estar en el aire y no sobre un objeto.

### Tres cosas que NO son la obra

| ❌ | Por qué no |
|---|---|
| **Low-poly estilizado** | Da aristas duras y facetas visibles. Pelea de frente contra la referencia. |
| **Realista tipo archviz** | Una versión anterior del hall tenía mobiliario (paneles, aros de techo, pedestal) y por eso se leía como render de arquitectura, no como espacio de Turrell. |
| **Detalle de textura, props, decorados** | Cualquier objeto reconocible ancla la escala y rompe la disolución. |

### Lo que sí

- Superficies **grandes y curvas**, sin esquinas visibles.
- Todo el trabajo en **gradientes emisivos**: el color vive en la superficie que emite, no en objetos iluminados.
- **Despojar hasta que quede lo esencial.** En el hall, Alma debería ser lo único que hay en esa sala.
- La profundidad y la escala se dan con **partículas y paralaje**, no con detalle.

💡 En Quest 3 esto también es lo más barato de renderizar. Cuando la restricción técnica y la dirección artística coinciden, la dirección es la correcta.

---

## 3. Restricciones técnicas que condicionan el arte

Estas no son sugerencias: son propiedades del motor tal como está configurado. Diseñar contra ellas genera trabajo que después hay que tirar.

### 3.1 Cero luces — todo es *unlit* + emisivo
La obra **no tiene ninguna luz**: ni direccional, ni de cielo, ni atmósfera, ni niebla. **Todo el color sale de materiales emisivos.**

Consecuencias para el arte:
- **No hay sombras proyectadas.** Nada de composiciones que dependan de una sombra para leerse.
- **No hay especular ni reflejos** de fuentes de luz. Los materiales metálicos o de vidrio "realistas" no funcionan; hay que resolverlos como degradados y transparencias.
- **El volumen se sugiere con degradado**, no con iluminación. Una esfera se lee como esfera porque su emisivo varía, no porque le pegue una luz.
- El **Fresnel** (borde que se enciende al mirarlo de canto) es la herramienta principal para dar cuerpo sin luz. Ya se usa en Alma, en el alma del usuario y en el haz de luz falso.

### 3.2 Presupuesto de render
- **Meta Quest 3 standalone**, renderer móvil, 72 Hz de refresco.
- El cuello de botella es el **fill-rate**: lo que cuesta es cubrir píxeles, sobre todo con **transparencias superpuestas**. Muchas capas translúcidas grandes una encima de otra es lo más caro que se puede hacer.
- **No hay Lumen, ni Nanite, ni sombras virtuales.** Todo es geometría clásica y ligera.
- Las mallas se cuentan en miles de triángulos, no en millones. Referencia: la esfera de Alma son **5.120 triángulos**; cada anillo de carga son **440**.

### 3.3 Legibilidad en VR
- **No hay esquinas de pantalla**: hay **grados**. Lo que el usuario debe ver sin buscar tiene que estar dentro de unos **20° del eje de mirada**, y **ligeramente por debajo del horizonte** (la mirada en reposo cae hacia abajo; mirar hacia arriba cansa).
- **Las líneas finas se ven feas.** El antialiasing del visor las come. Todo trazo tiene que tener grosor real.
- **El texto se lee mal**. Cuanto menos texto, mejor; y el que haya, grande, alto contraste y en el centro del campo visual.
- **El suelo necesita patrón.** Sin referencia visual el avance no se lee como avance, y la caminata se siente rara sin que se sepa por qué.

### 3.4 Un dato de escala útil
Los paneles de interfaz se autoran en píxeles con la equivalencia **1 píxel = 1 milímetro**. Un panel de 1000 px de ancho mide 1 metro. Sirve para dimensionar cualquier elemento gráfico.

---

## 4. La paleta

**Cada etapa tiene un color**, y ese color se usa en tres lugares a la vez: la sala, el anillo de carga que se gana al terminarla, y la banda correspondiente en el gráfico final.

| Etapa | Color | Ejercicio |
|---|---|---|
| **Entering** | **Azul** | Respiración |
| **Recognizing** | **Rojo** | Ritmo cardíaco |
| **Loving** | **Morado** | Contemplación |
| **Attracting** | **Naranja** | Componer una melodía |
| **Surrounding** | **Verde** | Dibujar |

**El exterior** (principio y final) es un **vacío negro azulado infinito**, con un degradado vertical suave. El degradado es lo que lo hace leer como **amplitud** y no como vacío plano.

🔴 **Que el cielo del final sea exactamente el mismo del comienzo es lo que hace legible el regreso.** Es la firma que cierra el arco.

⚠ **El exterior de las salas debe ser negro profundo.** El interior es el que está iluminado y tiene color. Entre sala y sala hay vacío: la puerta abre a negro absoluto.

---

## 5. El recorrido completo, escena por escena

La obra tiene **ocho actos** y un final. Duración total: ~14-15 minutos.

### Acto 1 — Intro App (~10 s + lo que tarde el usuario)
**Dónde:** el exterior, el vacío negro azulado con partículas.

Fundido desde negro. Tres logos de un segundo cada uno (*Made with Unreal*, Alma Digital Studio, Johns Hopkins). Después el título **Soul Charger** con el subtítulo *An interactive VR Biofeedback Experience*, y dos botones: **Start** y **About Us**.

*About Us* abre un panel de texto con un botón para volver.

**Interacción:** los botones se **tocan con la mano** (hover que agranda el botón + gatillo para confirmar). Deliberadamente **no hay puntero láser todavía** — ver §7.

### Acto 2 — Intro Soul (~45-50 s)
Al pulsar Start, el título y los botones se desvanecen y **el usuario empieza a avanzar** por el vacío. Una voz femenina hace preguntas que instalan el ánimo.

**Lo que pasa visualmente:** mientras se avanza, **el fondo azulado y las partículas se van apagando gradualmente** hasta la oscuridad. Empiezan a escucharse pasos. En la oscuridad aparece la **silueta de una puerta**: el *Soul Charger Center*.

El usuario se detiene a unos metros de la puerta. Aparece un **timbre**: un cilindro sobre el que hay que **apoyar la mano y esperar**. Un anillo alrededor se carga de 0 a 100 mientras se sostiene. Al completarse, la puerta se abre y se camina hacia adentro.

🔴 **Este tramo tiene dos trabajos:** instala el ánimo **y** es donde se toma la medición de referencia (baseline). Por eso son 30-40 segundos de avance estable, sin tarea ni decisiones.

### Acto 3 — Recepción / Hall (~90 s)
**Dónde:** la primera sala. La más despojada de todas.

Al cruzar la puerta aparece **Alma** y da la bienvenida. Después:

1. **Explica las cinco etapas**: aparecen los cinco nombres en gris junto a una ameba, y cada nombre **se colorea** y **su anillo aparece** a medida que Alma lo nombra.
2. **Pide tomar el sensor.** Al tomarlo se ejecuta una **calibración**: anillos que se expanden alrededor, y **el HUD nace animado, elemento por elemento**.
3. **Pide elegir el Proto Soul**: aparecen **cinco amebas candidatas**, cada una con **geometría y color distintos**. El usuario las mira (el *hover* las agranda para observarlas) y elige una con el gatillo.
4. Las otras cuatro desaparecen. La elegida viaja al frente y **se ancla al HUD** del usuario.
5. Alma **desaparece achicándose**. Se revela la puerta hacia *Entering*.

### Actos 4-8 — Las cinco etapas (~2 min cada una)

Todas siguen el mismo ritual: **Alma habla → instrucciones → ejercicio → ceremonia de carga → puerta**.

🔴 **El ritual se repite a propósito — el ritual *es* la meditación.** Lo que no puede repetirse idéntico es la carga: la primera dura unos 4 segundos y es casi silenciosa; la última dura unos 20 con música completa.

Y **el patrón se rompe una sola vez**: en *Loving* no hay panel de instrucciones. Esa desviación única resetea la atención.

---

#### Acto 4 — Entering (azul) · Respiración
El usuario se apoya el mando **en el estómago** y respira. Un objeto frente a él responde a su respiración en tiempo real, mientras un **indicador radial** marca el ritmo guiado: **4 segundos inhalar, 4 sostener, 4 exhalar**, cinco veces.

**Visualmente: la sala entera respira con el usuario** — muros, luz, volumen del ambiente. No solo un objeto.

🔴 **El usuario está quieto y el espacio se expande.** Si avanzara, leería su respiración como propulsión; quieto, la lee como **aquello que crea el mundo**. Eso es la tesis de la obra.

#### Acto 5 — Recognizing (rojo) · Ritmo cardíaco
El usuario se apoya el mando **en el pecho**. Con cada latido: un **pulso háptico**, un sonido, y un **anillo que emana desde el corazón**.

**Visualmente: el usuario asciende.** Pero es una ilusión: el usuario no se mueve, **el entorno desciende** a su alrededor. La subida ocurre en **diez saltos** de igual extensión, con una curva de trampolín (rápido y después lento).

🔴 **Hace falta una referencia vertical fija** —una columna de luz, anillos que pasan al lado— porque ascender en un espacio liso y curvo, sin nada con qué medir el movimiento, es de las cosas peor toleradas en VR.

#### Acto 6 — Loving (morado) · Contemplación
**Sin sensores en las manos y sin panel de instrucciones.** Es pura observación.

Alma hace **tres preguntas**. Con cada una aparece un **campo de luz** distinto (partículas, volumétrico) que se **suma** al anterior: primero uno, después dos, después tres. Al terminar la tercera pregunta desaparecen todos.

**La intensidad y la agitación de esos campos las modula la calma medida del usuario en vivo.**

#### Acto 7 — Attracting (naranja) · Componer
**Acá aparece el puntero láser por primera vez en toda la obra.**

Alrededor flotan **burbujas sonoras**. El usuario las **atrae con el haz** y las coloca en un **secuenciador de cinco espacios**, componiendo una melodía sobre una base rítmica que ya venía sonando desde que entró.

Un botón **FINISH MELODY** se enciende cuando los cinco espacios están llenos, pero se puede cerrar con menos: *la melodía de tu alma dura lo que alcanzaste a componer*.

**Coda:** desaparecen los haces y los espacios; **las burbujas elegidas se alinean al frente y suenan dos o tres vueltas**, y después se van.

#### Acto 8 — Surrounding (verde) · Dibujar
La ameba del usuario **se desprende del HUD** y se coloca al frente, a distancia de brazo y algo más grande que un balón, **ya mostrando sus cuatro anillos ganados**.

El usuario **dibuja alrededor de ella** —no adentro—, con la punta del sensor convertida en pincel.

**Cuatro restricciones hacen imposible dibujar algo feo, sin decirle a nadie qué dibujar:**

1. **Simetría radial de cinco ejes.** Cualquier garabato se vuelve mandala. (Impar, orgánico, y rima con las cinco etapas.)
2. **Un cascarón entre dos radios**: hay un límite interior y uno exterior. Todo lo dibujado es, por geometría, una capa.
3. **Paleta bloqueada**, derivada del color del alma elegida.
4. **Presupuesto finito de trazo.** La escasez produce composición.

**El límite es una esfera translúcida** alrededor de la ameba y sus anillos. Al invadirla, **la línea se afina en punta y se corta**; se reanuda al salir. **Nunca se borra lo ya dibujado.** El borde brilla suave al acercarse, para que la regla se aprenda con el cuerpo.

🔴 **La capa dibujada es el sexto anillo — el único hecho a mano.**

---

### El final (~2 min)

**La carga final.** Todo simultáneo, y tiene que ser impactante: la ameba crece y se aleja, vórtices y partículas de carga, los anillos girando, la barra llegando al 100%, **el HUD se disuelve** ("nos hemos desprendido de él")… y **la arquitectura se deshace en el lugar**, tipo transformer, hasta devolver el exterior.

🔴 **No hay última puerta y no hay avance.** El usuario se queda donde está y el espacio se desarma a su alrededor. Es la **única metamorfosis de toda la obra**, y por eso está guardada para acá. La sala tiene que **abrirse** —esconder su muro—, no solo bajar la luz.

**En el exterior**, con el mismo cielo del comienzo:

1. Suena **la melodía que el usuario compuso**.
2. Bajo la ameba **se dibuja solo el gráfico de resultados**.
3. **Silencio de 5 a 10 segundos.** La obra viene densa de eventos y lo necesita.
4. **Alma aparece y hace la pregunta.**

#### El giro final: la pregunta de Alma

🔴 **Es el único momento de la obra donde algo está en juego.** Justo antes de la constelación, Alma cuestiona lo que ella misma acaba de hacer:

> *"¿Esto eres tú? ¿O es solo lo que yo pude medir de ti?"*

Y **no la responde**. La deja abierta.

Lo que la hace funcionar es **quién la dice**: Alma es la que midió. Que dude de su propia medición es lo que le da peso — dicha por un narrador externo sería una moraleja; dicha por ella es una confesión.

#### La elección

Alma ofrece dos caminos. **El cierre es un gesto del usuario, no un fundido**: la ameba está frente a él, al alcance de la mano; la toma y la mueve.

| Elección | Gesto | Resultado |
|---|---|---|
| **Compartir** | empujar el alma hacia arriba | la constelación aparece y el alma se suma a ella |
| **Quedársela** | traerla hacia el pecho | la constelación aparece igual, **sin él**: se ve a los demás desde afuera |

🔴 **Las dos respuestas llevan a un final construido.** Si una fuera un callejón, la elección sería falsa y se nota. Nadie sale sintiendo que eligió mal.

**Después:** aparece la **constelación de almas de usuarios anteriores**. El usuario puede apuntar a cualquiera con el haz y **escuchar su melodía**. Tiempo de exploración, fundido a negro, agradecimiento, créditos.

---

## 6. Los personajes y objetos

Esta es la lista de todo lo que ocupa espacio en la obra. La columna **Estado** dice qué existe hoy en el motor y con qué nivel de acabado.

### 6.1 Los dos seres

#### **Alma** — la guía
Una **esfera-ameba translúcida** que flota, aparece y viaja entre puntos. Es abstracta: no tiene cara, ni ojos, ni nada antropomórfico. **Es audioreactiva**: se deforma con la voz.

Aparece en el Hall, al comienzo de cada etapa, y en el final.

Técnicamente **toda su vida está en el material**: la deformación, el gradiente, el doble Fresnel y el flotar son sumas de ondas. No tiene animación de esqueleto ni simulación. Malla: una **icoesfera de 5.120 triángulos**.

> **Estado:** existe y funciona. Falta arte definitivo — hoy es una esfera con un material propio.

#### **El Proto Soul** — el alma del usuario
La misma familia visual que Alma, pero **es del usuario**. Se elige entre **cinco candidatas** que difieren en **malla y color**.

Vive **anclada al HUD** durante toda la obra, y **se desprende** en cada ceremonia de carga y en el final.

🔴 **El Proto Soul es el HUD real de la obra:** su **pulso** es el ritmo cardíaco del usuario, la **agitación de su superficie** es su calma, sus **anillos** son la carga acumulada. Cero números, cero paneles.

**Los anillos de carga** son un elemento visual importante: son **trazos dibujados**, no aros geométricos. Una cinta plana con torsión, que recorre un **rollo de dos vueltas y media superpuestas** —de ahí el aspecto de trazos cruzados—, con una punta que ilumina, que nace y muere en punta, con respiración de grosor. Son **aditivos**: donde se cruzan, brillan.

🔴 **Los cinco anillos son iguales para todos los usuarios.** Eso hace que la constelación signifique algo: mismo ritual, interior propio.

> **Estado:** existe y funciona, con material propio y anillos generados proceduralmente. **Falta el arte definitivo de las cinco variantes de malla.** Está previsto un banco de **20 mallas + colores**, de las que se muestran 5 por sesión.

### 6.2 Los objetos que se tocan

| Objeto | Qué es | Tamaño | Estado |
|---|---|---|---|
| **El sensor** | El instrumento que se toma una vez y se conserva toda la obra. **Se reconfigura en cada etapa** y esa transformación *es* el aviso de que empieza algo nuevo. | de mano | ⚠ Existe una versión mínima (una esfera de 10 cm). **Falta todo el diseño.** |
| **El timbre** | Cilindro sobre el que se apoya la mano. Crece al acercarse, se hunde al presionarlo, y un **anillo alrededor** se carga mientras se sostiene. | 35 cm | Funciona. Placeholder visual. |
| **Los botones de menú** | Start / About Us / BACK / FINISH MELODY / avanzar instrucciones. Se **tocan**: crecen al hover, se confirman con el gatillo. | — | Funcionan. Placeholder visual. |
| **Las burbujas sonoras** | Objetos flotantes de *Attracting* que se atraen con el haz. Cada una tiene un sonido. | — | Funcionan. Placeholder visual. |
| **El secuenciador** | Cinco espacios donde se colocan las burbujas para componer. | — | Funciona. Placeholder visual. |

#### 🔴 El sensor, en detalle
Es el objeto más importante de la obra después de las dos amebas, y **es el que menos arte tiene hoy**.

**Se toma una vez y se conserva siempre.** Al tomarlo, la mano con la que se toma **queda registrada como la mano hábil** — no se pregunta en un menú, se descubre haciendo. Inmediatamente aparece el **segundo sensor, cerrado y dormido**, en la otra mano.

La transformación por etapa:

| Etapa | Estado del sensor |
|---|---|
| **Entering** | un cono suave sale de una cara → indica qué lado va contra el estómago |
| **Recognizing** | el mismo cono, más corto y **pulsando** → pecho |
| **Loving** | **se cierra y se aquieta** → sin decir nada, comunica *"no me necesitas"* |
| **Attracting** | el extremo **se abre en emisor** → de ahí sale el haz |
| **Surrounding** | la punta **se afina en pincel** |

💡 **Versión económica de producción:** el cuerpo es idéntico siempre y **solo se intercambia la punta**.

🔴 **El timbre y el sensor deben parecerse visualmente.** Apoyar la mano en el timbre para que te escanee es la misma gramática que tomar el sensor: el timbre es el tutorial, y la rima tiene que ser evidente.

### 6.3 La arquitectura

#### Las salas
**Seis salas** en total (Hall + cinco etapas). Hoy son un **placeholder deliberado**: un disco de piso de **10 metros de diámetro** con un patrón sutil, y un cilindro de muro de **4 a 5 metros** de alto, **sin techo**.

🔴 **Cada sala se diseña por separado y a mano.** El placeholder existe solo para poder caminar la obra completa antes de que exista el arte. **Todas se construyen en el mismo origen**: el usuario avanza hacia el umbral, el negro tapa el intercambio, y aparece en el centro de la siguiente sin notarlo. Eso elimina cualquier restricción de layout: **las salas no tienen que conectar entre sí físicamente.**

> **Estado:** placeholder funcional, con materiales de piso y muro por sala ya separados y listos para recibir el arte real.

#### Las puertas
**Dos hojas** que corren de lado a lado, con un **vidrio** que va de negro al color de la sala siguiente, y un **cartel sobre el dintel** con el nombre de la sala.

Reglas importantes:
- 🔴 **La puerta no existe durante la etapa.** Se revela al terminar: baja la luz de la sala, **una línea de luz traza el marco** sobre el muro, se enciende el cartel, y recién ahí abre. Que la sala esté sellada comunica *"esto es lo único que tienes que hacer ahora"*.
- **El marco pertenece a la sala donde estás** — es un hueco en *ese* muro.
- **La luz que se cuela por la rendija y el cartel pertenecen a la sala que viene.** El resplandor ya es rojo si vas a *Recognizing*, verde si vas a *Surrounding*.
- Se camina hacia la puerta **cerrada** y abre al llegar. Repite literalmente el gesto de la entrada al Center.

> **Estado:** ✅ **Es lo único que ya tiene arte real.** Marco, hojas, vidrio y cartel construidos, con las cinco puertas colocadas.

#### Los paneles de instrucciones
Un panel translúcido con páginas que el usuario pasa con un botón físico. Hay uno por etapa, con **un color de fondo por etapa**. Aparecen en cuatro de las cinco etapas (*Loving* no lleva).

> **Estado:** funciona, con cinco variantes de color. Falta el contenido real (los textos y los videos explicativos) y el arte.

#### El HUD
Un panel a unos 30-35 cm frente al usuario, **anclado a la cabeza**, con tres elementos: **una barra de carga vertical**, **un gráfico tipo EEG** que corre de derecha a izquierda con la señal de calma en vivo, y **un punto que late** al ritmo cardíaco.

Va **ligeramente por debajo del horizonte de la mirada**. Usa un material que **queda por encima de todo** — las manos nunca lo tapan, como el HUD de rendimiento de las gafas.

**Nace animado, elemento por elemento**, durante la calibración del Hall, y **se disuelve** en la carga final.

> **Estado:** construido y funcionando con datos en vivo. Sin arte: hoy son formas geométricas básicas sin fondo.

### 6.4 Los elementos del final

| Elemento | Qué es | Estado |
|---|---|---|
| **El gráfico de resultados** | Cinco filas, una por etapa, cada una en su color, con dos barras: **calma** (en el color de la etapa) y **ritmo** (blanca, más fina). Se revelan una por una. | Funciona, sin arte |
| **La constelación** | Una ameba por cada usuario anterior, flotando en el exterior, cada una con su color, su malla y sus anillos. Se pueden apuntar para escuchar su melodía. | Funciona, con posiciones colocables a mano |
| **Los créditos** | Panel de texto al final. | Funciona, textos pendientes |

#### 🔴 Cómo debería verse el gráfico de resultados
Esto está definido en el documento maestro y conviene respetarlo, porque es donde la colaboración con Bioética se hace visible:

- **Calma y ritmo:** dos líneas continuas sobre el mismo eje de tiempo, con **las cinco bandas de color de las salas** como fondo. **Sin grilla, sin números, sin ejes.** Tiene que parecer un dibujo, no un tablero de datos.
- **Respiración:** **cinco pétalos radiales**, no una onda. Amplitud = profundidad, ancho = duración. **Un pétalo pequeño no es un error.** Rima con el mandala y con los anillos.
- **Jerarquía:** lo más grande es la comparación **inicio → final** de la calma.
- **Se dibuja solo**, de izquierda a derecha, en 6 a 8 segundos, con la música. Un gráfico que aparece de golpe es una pantalla de resultados; uno que se traza es un recuerdo que vuelve.
- **Modular:** cualquier módulo puede faltar y el panel **nunca queda vacío ni muestra un error**. Los huecos dentro de una línea se ven **tenues, no rotos**: un hueco roto parece falla, uno callado parece un pasaje.

⚠ **Va a haber gente cuya calma baje, y eso no se maquilla.** Se resuelve con la metáfora: si el gráfico se lee como *altura = mejor*, toda bajada es una mala nota; si se lee como **un paisaje que recorriste**, no hay bueno ni malo. Y eso es literalmente lo que el dato es.

---

## 7. Cinco reglas que gobiernan todo

Si una decisión de diseño las contradice, la decisión está mal.

### 7.1 Capa autoral + capa viva
**Toda interacción de biofeedback tiene dos capas superpuestas:**

- **Capa A (autoral):** ocurre siempre, define el ritmo, garantiza que la etapa termine y que se vea bella.
- **Capa B (viva):** los datos del usuario modulan amplitud, suavidad, color y densidad **encima** de la capa A.

Si el usuario respira con la obra, el anillo florece entero. Si no, se mueve igual pero pequeño y apagado. **Nadie falla, nadie se traba, y el que se entrega ve visiblemente más.**

**Para el arte esto significa:** cada efecto necesita diseñarse en **dos estados** —el mínimo garantizado y el máximo— y verse bien en los dos.

### 7.2 Nunca hay callejón sin salida
Ninguna etapa puede quedarse esperando. Cada momento de espera tiene tres variantes de línea de voz que invitan sin repetirse, y pasadas esas, el sistema baja la exigencia o avanza solo. *Nadie debería quedar fuera de su propia alma por respirar distinto.*

### 7.3 El gesto cuenta la historia
El orden de las etapas es un **arco del gesto**:

| | Etapas | Gramática |
|---|---|---|
| **Hacia adentro** | Entering, Recognizing | el mando es una sonda contra tu cuerpo |
| **Bisagra** | Loving | no haces nada; el sensor se cierra y se aquieta |
| **Hacia afuera** | Attracting, Surrounding | el mando apunta y crea |

Y el arco empieza **antes** de las etapas. **El puntero láser llega tarde a propósito:**

| Momento | Gesto | Confirmación |
|---|---|---|
| **Menú** | **tocar** con la mano | hover + gatillo |
| **Timbre** | **apoyar** la mano | **esperar** (sostener) |
| **Sensor** y las 4 primeras etapas | **tomar** con la mano | contacto |
| **Attracting** | **apuntar** | el haz, que aparece **recién acá** |

**Por qué el menú no usa puntero:** si la primera interacción fuera con láser, se enseñaría una herramienta para abandonarla durante cuatro etapas y recuperarla al final. Tocando, el menú **rima con el timbre que viene tres segundos después** y con tomar el sensor, y el haz queda como una **capacidad nueva que se gana** en *Attracting*. Además, tocar enseña *tus manos son reales acá*, que es la tesis de la obra.

💡 **El timbre es el único que se confirma esperando**, y por eso es el que enseña la paciencia del resto de la obra.

### 7.4 El ritual se repite, la intensidad crece
Cinco veces la misma estructura. Lo que crece es la carga: **anillo 1** ≈ 4 s casi en silencio, íntimo → **anillo 5** ≈ 20 s con música completa y la escultura entrando.

### 7.5 Medir es parte de la obra, no un backend
La medición se muestra, se explica y se enmarca como **relación**, no como diagnóstico. El lenguaje siempre es **recorrido**, nunca **puntaje**:

- ❌ *"Tu nivel de calma: X"* · *"Tu calma subió un 20%"*
- ✅ *"Así se movió tu calma"* · *"Hiciste cinco respiraciones profundas"*

---

## 8. Qué existe hoy y qué hay que diseñar

Inventario real del proyecto al **2026-08-24**.

### ✅ Ya tiene arte real
- **Las puertas** — marco, dos hojas, vidrio de color, cartel con el nombre de la sala.

### 🟡 Construido y funcionando, con arte placeholder
Estos elementos **ya se mueven, reaccionan y están integrados**. Lo que falta es reemplazar la forma, no rehacer la mecánica.

| Elemento | Placeholder actual |
|---|---|
| **Alma** | esfera con material propio (deformación por ondas, doble Fresnel) |
| **El Proto Soul** | esfera con material propio + anillos como cinta dibujada |
| **Las salas** (×6) | disco de 10 m + cilindro de muro de 4,5 m, materiales de piso y muro separados por sala |
| **El HUD** | tres formas geométricas sin fondo |
| **El timbre** | cilindro de 35 cm + anillo de carga |
| **Los botones** | formas simples con material propio |
| **Los paneles de instrucciones** | panel translúcido, cinco colores |
| **Los campos de luz de Loving** (×3) | sistemas de partículas esféricos, uno rosa, uno violeta, uno ámbar |
| **El haz de luz** | cono unlit aditivo que finge luz sobre humo, sin luces ni niebla |
| **El panel de luz tipo Turrell** | plano con degradado radial de tres colores, animado y emisivo |
| **El gráfico de resultados** | cinco filas con barras de color |
| **La constelación** | amebas colocadas en puntos movibles a mano |
| **Los créditos** | panel de texto |

### ❌ Lo que hay que diseñar desde cero

**Por orden de importancia para la obra:**

1. 🔴 **El sensor** y sus cinco transformaciones. Es el objeto que el usuario tiene en la mano durante toda la obra y hoy es una esfera.
2. 🔴 **Las seis salas.** Cada una es un diseño propio, con su color y su comportamiento. Es el grueso del trabajo de arquitectura.
3. 🔴 **El exterior**: el vacío negro azulado, su degradado y su campo de partículas. Aparece dos veces —al principio y al final— y **tiene que ser el mismo**.
4. **Las cinco variantes del Proto Soul** (banco previsto de 20 mallas + colores).
5. **Alma** — forma definitiva.
6. **La transformación final**: cómo se deshace la arquitectura para devolver el exterior. Es la única metamorfosis de la obra.
7. **Los logos y el título** de la intro.
8. **Los contenidos de los paneles de instrucciones**: qué se ve en cada página (idealmente video corto o pictograma, no texto).
9. **El HUD**: los tres elementos gráficos.
10. **Las burbujas sonoras y el secuenciador** de *Attracting*.
11. **El pincel y el trazo** de *Surrounding*, y la esfera translúcida que marca el límite.
12. **El gráfico de resultados**: los pétalos de respiración y las bandas de color.

---

## 9. Notas para trabajar con IA generativa

Algunas cosas que conviene tener presentes al escribir prompts para moodboard, porque hay una brecha entre lo que sale bonito en una imagen y lo que funciona en un visor.

### Términos que ayudan
> *James Turrell, light installation, Skyspace, Ganzfeld, luminous gradient, volumetric color field, edgeless space, glow without a visible source, soft falloff, infinite void, deep blue-black, emissive surfaces, no visible geometry, seamless curved wall, translucent membrane, bioluminescent, abstract organism*

### Términos que llevan al lugar equivocado
> *low poly, stylized, cel shaded, sci-fi HUD, holographic interface, neon cyberpunk, futuristic laboratory, medical device, dashboard, archviz, interior design, furniture, props, detailed textures*

### Cuatro trampas concretas

1. **La IA pone luces.** Casi toda imagen generada tiene una fuente de luz implícita con sus sombras. Acá **no hay ninguna**. Al mirar una referencia, hay que preguntarse: *¿esto se sostiene si le quito toda la iluminación y el color solo puede salir de las superficies emisivas?* Si la respuesta es no, la imagen es bonita pero no es construible.

2. **La IA llena el espacio.** Va a agregar objetos, mobiliario, detalle. **El trabajo acá es sustractivo**: en el Hall, Alma debería ser lo único que hay.

3. **La escala se pierde en una imagen 2D.** Las salas son de **10 metros de diámetro** y el usuario está **sentado en el centro**. Conviene pensar cada imagen desde ese punto de vista concreto, no desde una cámara flotante.

4. **Las transparencias apiladas son caras.** Una imagen con siete capas de humo translúcido superpuestas es exactamente lo que no se puede renderizar en un visor autónomo. Una o dos capas grandes, sí.

### Qué es más útil entregar
- **Vistas desde el punto de vista del usuario sentado**, no plantas ni vistas aéreas.
- **La misma sala en dos estados**: en reposo y en su momento máximo (respirando, ascendiendo, cargando).
- **Paletas por sala**, con los degradados concretos.
- **Fichas de objeto** para el sensor y las amebas: varias vistas, y en el caso del sensor **las cinco puntas**.
- **La transición**: qué se ve durante el fundido a negro entre salas, y cómo se traza el marco de la puerta sobre el muro.

---

## 10. Resumen de una página

| | |
|---|---|
| **Qué** | VR de biofeedback y meditación, sentada, un usuario, ~15 min, Meta Quest 3 |
| **Quién guía** | **Alma**, una ameba abstracta audioreactiva |
| **Qué se lleva el usuario** | **su Proto Soul**: malla, color, cinco anillos, una melodía y una capa dibujada a mano |
| **Estructura** | exterior → caminata → timbre → Hall → 5 etapas → carga final → exterior → constelación |
| **Las 5 etapas** | Entering (azul, respirar) · Recognizing (rojo, latido) · Loving (morado, contemplar) · Attracting (naranja, componer) · Surrounding (verde, dibujar) |
| **Estética** | James Turrell: luz imposible sobre casi nada de geometría |
| **Regla técnica dura** | cero luces, todo unlit + emisivo, sin sombras, presupuesto de fill-rate ajustado |
| **Regla narrativa dura** | capa autoral + capa viva: nadie falla, y el que se entrega ve más |
| **El momento clave** | la pregunta de Alma: *"¿Esto eres tú? ¿O es solo lo que yo pude medir de ti?"* — y no la responde |
| **Lo más urgente de diseñar** | el sensor · las seis salas · el exterior |
