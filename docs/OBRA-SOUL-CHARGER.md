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
| 0 | **Intro** — logos, título, Start / About | — |
| 1 | **Oscuridad** — voz femenina espacializada, preguntas que instalan el mood | ~45 s |
| 2 | **La caminata** — pasos en negro, silueta de puerta, *Soul Charger Center*. Timbre: apoyas la mano y te escanea | ~45 s |
| 3 | **Hall** — Alma te recibe, explica las 5 etapas, calibración, eliges tu Proto Soul | ~90 s |
| 4–8 | **Las cinco etapas** | 5 × ~2 min |
| 9 | **Sala final** — la arquitectura se transforma (no hay compuerta), gráfico de datos, constelación, despedida | ~2 min |
| | **Total** | **≈ 14–15 min** |

> ⚠ **El presupuesto es real: la obra da ~15 min, no 10–12.** Para festival es una duración normal, pero hay que asumirlo. **Si hay que recortar, se recorta intro y final, no las etapas** — ahí están los ~3,5 min más pasivos.
>
> ⚠ *Attracting* y *Surrounding* son abiertas y se pasarán de 2 min casi siempre. Cierran con **invitación suave** (el pad crece, la luz se entibia, Alma habla), nunca con corte seco.

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

### 9.2 Los cinco objetos persistentes

| Objeto | Responsabilidad |
|---|---|
| **`GI_SoulCharger`** (GameInstance) | Quién fue este usuario: malla, color, melodía, escultura, las 180 casillas de datos, el índice rotativo de bancos. Sobrevive a cualquier `OpenLevel`. |
| **`BP_BioHub`** | Ingesta OSC → binning → suavizado. **Única fuente de verdad** de calma y ritmo. Expone valor actual, promedio y flag de conexión. |
| **`BP_Sensor`** | Uno por mano, persistente. Enum de estado + malla que se reconfigura por etapa. |
| **`BP_ProtoSoul`** | La ameba: lazy-follow, anillos, reacción en vivo, animación de carga. Es también el HUD. |
| **`BP_NarrationDirector`** | Cola de VO: disparo por evento, por entrar a estado y por inactividad. Con variantes y **sin bloquear**. |

🔴 **El BioHub no sabe nada de etapas y las etapas no saben nada de OSC.** Si se cambia de dispositivo, se toca un solo Blueprint.

### 9.3 `BP_StageBase`
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

### 9.4 Captura de datos: casillas, no muestras
**180 casillas** para toda la experiencia (~5 s cada una). Cada una acumula **suma, cantidad de muestras, mínimo y máximo**, más **a qué etapa pertenece**.

Eso resuelve de una sola vez: el suavizado (promediar en ventanas de 5 s *es* el filtro), la memoria (180 en vez de 9.000), los huecos (cantidad de muestras en cero es un hueco *explícito*, no un cero que parece dato), el tamaño fijo de la geometría, y las bandas de color del gráfico.

### 9.5 Dibujar el gráfico
**Ribbon 3D reusando el generador de trazos de *Surrounding***. Cada casilla es un punto: `x = índice × separación`, `z = valor × altura`. Ventaja no solo técnica: **el gráfico queda hecho del mismo material que el dibujo del usuario.**
Los **cinco pétalos**: cinco meshes con la escala manejada por profundidad y duración.
Alternativa rápida si urge: UMG con `OnPaint` + `Draw Lines`, con líneas gruesas (en Quest las finas alias feo).

### 9.6 Refactor de lo ya construido
- **`BP_TouchSensor`** → `BP_Sensor` persistente. No se toma en cada etapa; **la etapa le dice en qué convertirse**.
- **`BP_AimBeam`** deja de depender de que un sensor lo equipe; el gate pasa al director.
- **`BP_AttractDirector`** pierde el reloj de Quartz y la orquestación general (suben a `BP_StageDirector`); se queda con el secuenciador.
- **La melodía guardada** sube al GameInstance.

---

## 10. Orden de construcción

**El esqueleto antes que los órganos.** Las mecánicas existen pero están sueltas; el riesgo es pulir órganos que no conectan. Y las preguntas abiertas —¿dura mucho?, ¿el ritual cansa?— **solo se responden caminando la obra completa**, cosa que se puede hacer sin una sola mecánica conectada.

1. **La caminata entre dos salas vacías.** Pawn sobre spline, compuerta, sublevel que carga y descarga. Es el mayor riesgo técnico. **Probar comodidad en visor antes de construir nada más.**
2. **El trío persistente**: `BP_BioHub`, `BP_Sensor`, `BP_ProtoSoul`. Que sobrevivan a la caminata y que la ameba lata con datos reales.
3. **`BP_StageBase` + cinco etapas vacías** (instrucciones → esperar N s → carga → puerta), con cajas grises como salas.
   👉 **Aquí ya se camina la obra completa de 15 minutos** y se responden las preguntas de ritmo.
4. **Enchufar las mecánicas reales**, una por una, como reemplazo de `RunStage()`.
5. **Panel de resultados y constelación** al final.

**Todos los assets son placeholders simples** hasta que la mecánica esté validada en visor.

---

## 11. Lo que falta decidir

- **La pregunta grande del final.** La obra tiene cinco beats de "haz algo" y **ningún giro dramático** — sin él es un menú de spa con certificado. El material ya está: trata sobre qué significa medir un alma. Antes de la constelación, Alma podría complicar lo que acaba de hacer: *"¿Esto eres tú? ¿O es solo lo que yo pude medir de ti?"* Y compartir tu alma deja de ser un botón para ser **una decisión con peso**.
- **El cierre debería ser un gesto del usuario**, no un fundido: que seas tú quien coloca su alma en la constelación, con la mano.
- **Silencio antes del final**: 5–10 s de nada después de *Surrounding*. La obra viene densa de eventos.
- Número de ejes de simetría del mandala (probar 5 en visor).
- Ancho y brillo del pincel: el primer trazo tiene que ser satisfactorio de inmediato.
