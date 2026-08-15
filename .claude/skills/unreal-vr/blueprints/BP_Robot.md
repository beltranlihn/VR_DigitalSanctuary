# BP_Robot — el usuario falso, para testear interacciones sin visor (Core/Debug/)

## Purpose
Pedido de Beltrán (2026-08-15): *"un sistema de debug que puedas correr tú en el play editor, donde puedas testear todas las interacciones que haría un usuario"*. La idea es levantar el techo que teníamos hasta ahora — **nada gestual se podía verificar en PIE** —, para poder arreglar cosas solo.

## Status
🟡 **El concepto está PROBADO, las rutinas no.** Lo que ya está demostrado en PIE:
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
