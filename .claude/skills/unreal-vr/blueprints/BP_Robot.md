# BP_Robot — el usuario falso, para testear interacciones sin visor (Core/Debug/)

## Purpose
Pedido de Beltrán (2026-08-15): *"un sistema de debug que puedas correr tú en el play editor, donde puedas testear todas las interacciones que haría un usuario"*. La idea es levantar el techo que teníamos hasta ahora — **nada gestual se podía verificar en PIE** —, para poder arreglar cosas solo.

## Status
🟢 **Primera etapa completada de punta a punta por un robot** (2026-08-15). Recognizing entera, sin humano y **sin cortafuego**:
```
HB: Latido 3/15 … 10/15            ← cada 1,7 s = los 68 bpm simulados
CEREMONIA: la ameba llego al ChargeSpot · distancia = 0.0
CEREMONIA: anillo y barra completos · terminada - carga = 0.4
DIR: la ceremonia aviso que termino · fin de sala - baja la luz
DIR: precarga invisible de L_Room_Loving · camina el tramo 4
```
👉 Esto valida **tres cosas a la vez**: el arreglo de Heart de esa mañana, la ceremonia de carga, y que **el director avanza por la interacción y no por el timeout**.

🔴 **`RobotOn` queda en 0 por defecto.** Si quedara en 1, en una sesión con visor el robot le llevaría las manos al pecho a Beltrán y le arruinaría la corrida. Se enciende para testear y se apaga al terminar — como `DebugStartStage`.

Lo demostrado antes:
- ✅ **Las manos falsas funcionan.** `SetWorldLocation` sobre el `MotionControllerComponent` del pawn **se queda pegado** en PIE (no lo pisa el tracking, porque no hay tracking). Control positivo:
  ```
  ROBOT: mano=X=2412.000 Y=0.000 Z=-32.000 | pecho=X=2412.000 Y=0.000 Z=-32.000 | dist=0.0
  ```
- ✅ **Las mecánicas ven esa mano**: el sensor de latido se enganchó solo (`enMano=true | derecha=true`) sin que nadie tocara nada.
- ✅ **El gatillo se puede sintetizar**: existe el nodo **`Input|InjectInputforAction`** — se puede inyectar `IA_Shoot_Right` por el mismo camino que lo entrega un usuario. (Construido: no. Disponible: sí.)
- ⬜ Ninguna rutina completa una interacción de punta a punta todavía.

## 🔑 Por qué mover DOS componentes alcanza para todo
Toda la obra lee las manos por los mismos dos accesores del pawn — `GetMotionControllerLeftGrip` / `GetMotionControllerRightGrip`. El sensor de latido, el pincel, la elección de ameba y los botones **preguntan siempre ahí**. Entonces mover esos dos componentes **es** mover las manos para el juego entero: no hay que falsear cada mecánica por separado.

## Anatomía
```
BP_Robot (actor en L_Persistent)
  BeginPlay → timer RobotTick (TickTime 0,05 s) + timer RobotReport (3 s)
  RobotTick  → si RobotOn>0, despacha por Routine
  RunHeart   → las dos manos al pecho (Routine 2)
  ChestLoc() → camara + adelante*ChestFwd − arriba*ChestDrop
  SetHandR/L(Loc) → SetWorldLocation del grip correspondiente
  RobotReport → loguea mano / objetivo / distancia
```

| Variable | Default | Rol |
|---|---|---|
| `RobotOn` | 1 | Apaga el robot sin tocar el grafo. |
| `Routine` | 2 | Qué rutina corre. Hoy sólo la 2 (Heart). |
| `TickTime` | 0,05 s | Cada cuánto se reposicionan las manos. |
| `ChestDrop` / `ChestFwd` | 32 / 12 cm | Dónde está "el pecho" respecto de la cámara. |

## 🔴 Dos hallazgos de la primera corrida — los dos importan
**1. En PIE la cámara está en el SUELO (Z=0).** Sin HMD el pawn no recibe altura de tracking, así que la cabeza queda a la altura del piso y "el pecho" cae en Z=−32. Las lógicas **relativas a la cabeza** siguen siendo correctas, pero cualquier cosa colocada en el mundo a altura real queda lejísimos de las manos falsas. 👉 **Próximo paso obligatorio del robot: falsear también la cabeza** (subir la cámara a ~120 cm) o PIE nunca va a ser representativo.

**2. El salto por `DebugStartStage` se saltea la calibración del sensor.** El pulso lo cantó:
```
PULSE|Heart| latidos=0/15 | enMano=true | derecha=true | umbral=false | calibrado=false | cuenta=true
```
La calibración **no es un paso aparte**: ocurre dentro de `Step`, sola, cuando el sensor pasa `CalHold` = **4,5 s** quieto y en posición. Con `calibrado=false` el umbral no puede abrir, y sin umbral no hay latido. En la corrida real de Beltrán sí se calibró (`UMBRAL IN` en el log), así que **por ahora es un artefacto del atajo de debug, no un bug de la obra** — pero conviene tenerlo escrito: *si un usuario llegara a Heart sin haber calibrado, la etapa es inentrable*.

## 🔴🔴 El techo real de PIE: el detector depende del TRACKING, no de la posición
Falsear la mano no alcanzaba para que el sensor de latido detectara. La autopsia, leyendo `Step`:
```
_rv44 = quietud   AND  _rv43
_rv43 = (and  GetLinearVelocity.ReturnValue  GetAngularVelocity.ReturnValue)   ← los bValid del tracking
```
`MotionControllerUpdate|GetLinearVelocity` devuelve **el vector y un bool de validez**, y el detector exige **los dos válidos**. En PIE no hay runtime XR: ese bool es `false` y **ninguna cantidad de posición falsa lo cambia**. Medido: geometría perfecta (`horiz=12 ≤ 20`, `vdrop=32 ≥ 5`, `vel=0`) y aun así `calT=0.0`, es decir el temporizador de calibración **nunca arrancaba**.

👉 **La frontera del robot queda así:**
- ✅ Todo lo **posicional** (hover por distancia, agarre por cercanía, dibujo, elección por ángulo) → el robot lo maneja.
- ❌ Todo lo que sale del **tracking** (`BP_HeartSensor`, `BP_BreathSensor_V2` — el mismo detector) → no corre en PIE.

**La salida, sin tocar el Blueprint frágil:** el robot **saltea sólo el detector** desde afuera, con los setters públicos (§67):
`SetCalibrated(true)` + `SetBreathing(true)` — y, la pieza clave, **`SetDeactivateDelay(99999)`**.
Sin ese último, había una **carrera perdida**: yo escribía `bBreathing=true` 20 veces por segundo y `Step` lo apagaba ~60 (y `UpdateHeartbeat` corre justo después de `Step` en el mismo tick, así que leía `false` siempre). Subiendo el retardo de desactivación, `Step` **nunca llega a apagarlo** y una sola escritura alcanza. 💡 Regla general: **para ganarle a una lógica por tick no hay que escribir más rápido, hay que desarmar su condición de apagado.**
⚠ Con esto **el detector no queda probado** — queda probado todo lo que viene después de él, que es la cadena larga (intervalo, pulso, conteo, háptico, audio, cierre, ceremonia, transición).

## 🟢 El gatillo inyectado FUNCIONA — y con eso cayó el primer diagnóstico real
`Input|InjectInputForAction` entrega la acción por el mismo camino que un usuario. Verificado dos veces en la misma corrida:
```
BOTON armado: START      →  1 s después  →  BOTON apretado: START      (sin ningún atajo)
ROBOT: hover conseguido, inyecto el gatillo   21:43:37.095
SOULCHOICE: elegida la variante 0             21:43:37.427   ← 330 ms después
```
🔴 **Conclusión que importa: el hover+trigger sobre las proto amebas del Hall NO está roto.** Beltrán reportó en visor *"sigue sin funcionar el trigger con las protoamebas"*, y acá funciona por el camino real del input — ni llamada directa, ni cortafuego.

👉 **La hipótesis que queda es de ALCANCE, no de lógica**, y la sostiene el propio log del juego:
```
AUDIT: camara en           X=0    Y=0     Z=115
AUDIT: candidata sigue en  X=70   Y=0     Z=172      (y las otras cuatro, todas en Z=172)
```
Las candidatas están **57 cm por encima de los ojos** y a **65-70 cm al frente**. El robot consigue el hover porque **teletransporta la mano exactamente al actor**; una persona sentada tiene que llegar de verdad. Encaja con la intuición de Beltrán (*"me acuerdo que las amebas estaban altas"*).
⬜ **Próxima prueba en visor:** bajar los `TargetPoint` de las candidatas a la altura del pecho/hombros y ver si el trigger "empieza a andar" — sería la confirmación.

## 🔬 Autopsia del instrumento: por qué la inyección "no llegaba" al principio
Los primeros intentos no disparaban nada, y estuve a punto de reportar el bug de Beltrán como reproducido. **Lo salvó el control positivo**: probé la inyección contra el botón START —que ya sabía que funciona— y tampoco lo apretaba. Eso movió la sospecha de la obra a mi herramienta. El log lo confirmó al cerrar PIE:
```
Accessed None trying to read (real) property CallFunc_GetLocalPlayerSubsystem_ReturnValue
```
**`LocalPlayerSubsystems|GetEnhancedInputLocalPlayerSubsystem` sin argumentos devuelve None.** Hay dos nodos con el mismo nombre y sólo uno sirve: **`PlayerController|LocalPlayerSubsystems|GetEnhancedInputLocalPlayerSubsystem`**, que recibe el PlayerController (`Game|GetPlayerController 0`). Con ese, todo anduvo a la primera.
💡 La lección, otra vez: **un instrumento sin validar produce diagnósticos falsos con toda confianza.** El control positivo costó una corrida y evitó acusar al juego de un bug que no tiene.

## 🔴 ESTADO DE LA CAMPAÑA DE PASADAS (2026-08-15 noche) — leer esto primero al retomar
Beltrán se fue a dormir y autorizó seguir solo, pasada tras pasada, hasta que la obra corra fluida y sin errores. **Él prueba con visor mañana.**

### El protocolo de una pasada (acordado con él)
1. **Configurar** (`RobotOn=1`, `Routine=0`, `DebugStartStage=-1`, `Phase=0`) con PIE **detenido**.
2. `StartPIE` y **NO TOCAR NADA** — ni una consulta al log durante la corrida. Esperar con un `sleep` en background (fuera de Unreal).
3. Al terminar, revisar de una sola vez: cortafuegos, líneas `completa - aviso al director por el camino real`, `Accessed None`.
4. Arreglar **con PIE detenido**, y repetir.

🔴🔴 **NUNCA compilar con PIE corriendo.** Beltrán está fuera de la oficina y no puede reiniciar el editor: colgarlo nos deja parados a los dos.
🔴 **Al terminar cada sesión, dejar `RobotOn=0` y `DebugStartStage=-1`** — si no, su corrida con visor arranca con el robot llevándole las manos al pecho.

### Veredicto de la última pasada completa (22:41 → 22:54)
| Etapa | Cierre |
|---|---|
| Hall · Entering · Recognizing · Loving | 🟢 **por el camino real**, sin ningún cortafuego |
| **Attracting** | 🔴 por tiempo — el robot coloca **una sola burbuja** y la etapa espera la melodía terminada (falta repetir agarrar-soltar y apretar FINISH MELODY) |
| **Surrounding** | 🔴 por tiempo — `PULSE\|Surrounding\| metros=0.0 \| dibujando=false \| puntos=0`: **el pincel no dibuja**. Se le escribe `bTrigHeld` pero el lienzo no registra un solo punto → probablemente hay que **agarrar el pincel primero** |
| Final | ⬜ pendiente de confirmar con `RunFinale` |

✅ **Cero cortafuegos de instrucciones** en esa pasada: los tres arreglos (`InstrHeart`, `BreathBypass`, gatillo por frame) funcionaron.

### Lo que falta construir, en orden
1. **Attracting**: bucle de N burbujas (no una) + botón FINISH MELODY sostenido.
2. **Surrounding**: averiguar por qué el trazo no nace (¿el pincel necesita estar agarrado? ¿`BP_DrawCanvas` necesita `StartStroke`?) y dibujar de verdad hasta `TargetMeters`.
3. Confirmar el final por gesto.
4. Cuando las seis etapas cierren por interacción: **pasada limpia de punta a punta con cero cortafuegos** y revisar `Accessed None`.

### 📉 El misterio de los 3 fps (medido, no resuelto)
El editor renderiza a **~36 frames cada 12 s** durante PIE. Descartado por medición: `bThrottleCPUWhenNotForeground` ya estaba en `false`, `t.MaxFPS`=0, y **una ventana controlada de 10 minutos sin una sola llamada MCP dio exactamente el mismo ritmo** (la hipótesis de que lo causaban mis consultas es falsa).
💡 **No invalida los tests**: la simulación corre en tiempo real (12,000 s de juego por cada 12 s de reloj) y todo lo que mide la obra es por `DeltaSeconds`. El único cuidado es la granularidad de 0,33 s en lo que se evalúa por frame (sostenidos de gatillo).

## Cómo se usa (modelo por lotes, no en vivo)
No se puede llamar a una función de Blueprint desde el MCP con PIE corriendo. El ciclo es:
**configurar (`RobotOn`, `Routine`, `DebugStartStage`) → `StartPIE` → leer log y capturas → `StopPIE`.**
El pulso de [[BP_TestKit]] es el que reporta si la rutina consiguió su objetivo.

## TODO
- [ ] 🔴 Falsear la altura de la cabeza (cámara a ~120 cm) — sin eso, media geometría no se puede probar.
- [ ] Que la rutina de Heart llegue a calibrar: sostener quieto 4,5 s en zona y ver `UMBRAL IN` → `HB: Latido`.
- [ ] `PressTrigger` / `ReleaseTrigger` con `Input|InjectInputforAction` (`IA_Shoot_Right`).
- [ ] Rutinas: elegir ameba en el Hall · agarrar burbuja y soltarla en un slot · dibujar un trazo en Surrounding.
- [ ] Aserciones `ROBOT: PASS/FAIL` con el formato de [[BP_SelfTest]].

## Relacionados
- [[BP_TestKit]] (el pulso que dice si la rutina funcionó) · [[BP_SelfTest]] (las aserciones sin humano) · [[BP_HeartSensor]] · `references/vr-pawn.md` · `references/input.md`
