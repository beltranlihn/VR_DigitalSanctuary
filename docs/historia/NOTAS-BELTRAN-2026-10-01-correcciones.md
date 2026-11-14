# Notas de voz de Beltrán — correcciones tras ver la Obra (2026-10-01, madrugada)
Transcritas tal cual llegaron; el plan se arma cuando Beltrán diga "listos".

## Nota 1
- Inicio / Hall: el fundido a negro fue demasiado rápido. Debe demorarse un poco más, sin chocar con que alcance a verse el nacimiento del mesh del Hall; atrasarlo un poco.
- Timbre: al terminar la carga, el anillo de alrededor (radial slider) tiene que desaparecer al instante cuando llega al final; si no, se queda pegado.
- Al principio: dejar el título un par de segundos más antes de partir.
- Timbre, sonido: debe empezar apenas empezamos a tocar el timbre. Si sacamos la mano, se va con un fade out. Si lo volvemos a tocar, vuelve a empezar desde el principio, apenas lo tocamos.
- Sensor: al tomarlo deben desaparecer las manos (el sensor pasa a ser nuestra mano). Ahora quedaban las manos y el sensor: muy incómodo.
- Sensor: debe girar animado dentro del orb, suave, como la moneda flotante de un videojuego. Al agarrarlo, debe quedar en la posición correcta.
- Alma (BP): dejar perillas y variables para ajustar las partículas.
- Protoameba: al seleccionarla se mueve a un TargetPoint; ese TargetPoint debe definir el transform COMPLETO (no solo la ubicación). Beltrán agrandó el TargetPoint y la protoameba no se agrandó.
- Protoameba: al llegar al TargetPoint debe aparecer el anillo que la contiene, encajado a ella aunque la hayamos agrandado con el TargetPoint (el anillo marca sus luces junto con la animación de las baldosas).
- Gráfico del EEG: se ve muy poco; subirle el brillo o engrosarlo, pero muy, muy poquito.
- Baldosas menos brillantes: se pasaron de brillo.
- Al terminar la explicación de las etapas (la protoameba con su anillo): una pequeña animación, como al final de la carga, para que desaparezca y vuelva a aparecer en nuestro HUD.

## Nota 2
- Ambient clips: desorden. Deben fundirse uno con otro (crossfade). Ahora se acaba uno, pasan muchísimos segundos de silencio y recién parte el otro.
- Salida del Hall: el texto de ENTERING casi no existió. Pasó mucho rato desde que empezamos a caminar para salir hasta que llegamos afuera y apareció el texto, que duró un segundo. El texto de Entering debe aparecer apenas cruzamos la puerta de salida del Hall; tiene que ser muy fluido.
- VO faltantes en varias etapas: revisar los últimos VO (¿Breath los recortó mal?). Había muchos (instrucciones, otros entre medio de la experiencia) que no sonaron; Alma recibe, dice algo y se queda callada mucho rato sin que pase nada, sin saber qué hacer. Si los VO de instrucciones aún no existen, OK; pero si ya estaban creados y encajan en la narrativa, agregarlos.
- Alma empieza a hablar antes de aparecer. Alma tiene que aparecer y recién ahí hablar.
- TargetPoints de Alma: igual que con la protoameba, deben definir su transform completo (si achico el TargetPoint, Alma se achica).
- Volúmenes: todos los sonidos de efectos más bajos (el de carga queda como está); los ambient clips todavía más bajos. Tiene que prevalecer la voz.
- Ritmo cardíaco (Heart): pasó lo mismo, Alma apareció, dijo hola y se quedó callada mucho rato sin que pase nada. Se suponía que había frases entre medio; ver si existen y se olvidaron.
- Heart: el pulso va rapidísimo. El sonido y el pulso del agua deben ir a la MITAD del pulso cardíaco que llega (EEG/BioHub). El simulado actual, visual y sonoramente, era rapidísimo: incómodo, poco wellness.
- Cargas de la ameba (cuando se va al frente y se carga): en casi todas no se notaba el halo de color.
- Heart: la mano nunca salió del umbral. Aunque sacara la mano del cuerpo, quedaba pegada en el umbral. ¿Algo replicado? Hay que arreglarlo.

## Nota 3
- Sensor: desde que lo tomamos en el Hall de entrada NO desaparece de la mano hasta que termina la etapa de ritmo cardíaco (Heart). Es el mismo sensor para Entering (respiración) y Heart. Desaparece al terminar Heart y ahí vuelven a aparecer las manos.
- Manos duplicadas: volvieron a aparecer muchísimos mesh de manos en varias etapas. En Attracting apareció otro mesh de mano, y en el dibujo otro encima: varios mesh de manos superpuestos.
- Material translúcido de la mano: tiene que ser más transparente.

## Nota 4
- Attracting: todo demasiado blanco; casi no se ve nada. El gusano se pierde con el suelo y con el cielo. Ajustar la paleta para que se distingan las cosas.
- Attracting: en el botón de la mano para SAVE hay un texto negro horripilante y enorme ("Save Game"). Sacarlo; basta con el botón.
- Última carga: se fue a negro antes de terminar la carga (el anillo empezó a desvanecerse a negro mientras se cargaba). Debe terminar la carga y recién ahí irse a negro el ENTORNO, no toda la visual. Secuencia: termina de cargar → la protoameba se desprende del anillo → el anillo desaparece → la protoameba empieza a moverse hacia adentro.

## Nota 5
- Parte final: se quedó pegado un háptico todo el rato en las manos. Muy extraño.
- Manos en las últimas etapas: la mano tiene que desaparecer al terminar la etapa de actividad neuronal (Loving / Mind). Al iniciar Attracting tenemos el sensor, en el dibujo también, y nos quedamos con el sensor hasta el final. (Aquí es donde aparecieron los mesh de manos uno encima de otro.)
- Actividad neuronal (Loving): la neurona aparece cuando Alma todavía está al frente; se superponen y queda súper raro.
- TargetPoints de Alma al costado: cada vez que Alma se va para el lado, esos TargetPoints deben hacer que Alma se vea más chica. Ese TargetPoint se repite nivel tras nivel; Beltrán alcanzó a cambiarlo en los primeros, falta en los últimos.
- Resultados (final): aparecen el dibujo, el anillo y el panel con instrucciones (OK). Pero al apretar compartir y correr la animación en que desaparece el cuadro, solo se fue el MARCO; siguieron ahí todos los dibujos de los gráficos. Debe desaparecer todo lo que compone ese sistema.
- Después nos demoramos mucho en salir, y ahí ya no deberían sonar los pasos (ya vamos saliendo hacia afuera).
- Constelación al llegar afuera: aparecieron todas de 0 a 1 de golpe. Deben crecer animadas.

## Nota 6 (general + mandato)
- Muy molesto que no haya fundido entre ambient clips: la obra se sintió parada a la mitad. Transiciones: el texto de etapa estuvo muy poco rato y Alma empezaba a hablar antes de aparecer.
- Revisar muy bien los VO con el agente que los pasó (Breath): ¿bien recortados? ¿faltó integrar? Se sintió que faltaban.
- MANDATO: preparar un plan, desarrollarlo entero, organizarlo bien. Hacer un APK, dejarlo instalado en las gafas (quedaron enchufadas) y testearlo en el APK. Beltrán no va a estar; mañana lo muestra: tiene que funcionar ("si no funciona sería un fraude"). Se sentía muy trabada; los glitches de manos que aparecen y desaparecen son muy raros.
- En los segundos negros del inicio: un texto al frente del usuario, en inglés, bien redactado: la experiencia usa sensores para medir actividad neuronal y ritmo cardíaco, que generan variaciones a lo largo de la experiencia, y en este build esos datos se simulan. Debe desaparecer cuando empieza el resto de la experiencia.

## Nota 7 (criterio)
- Pensar como un usuario viviendo la experiencia: que nada del gameplay lo deje parado preguntándose "¿qué está pasando? no entiendo". Pensar como developer pero también como usuario. Si una mecánica se demora demasiado o pasa muy rápido, el usuario se pierde y sale de la obra. Mucho cuidado con eso.
