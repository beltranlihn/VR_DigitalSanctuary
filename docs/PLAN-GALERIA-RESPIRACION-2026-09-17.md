# Plan — la respiración controla la galería (2026-09-17)

> **Estado (cierre 2026-09-17): 🟢 CONSTRUIDO y verificado en PIE · ⬜ falta el visor.** El diseño de abajo se escribió leyendo los trackers, con el MCP caído. Después se verificó contra el nivel y se construyó; donde los datos reales cambiaron la decisión, está anotado en **"Lo que cambió al construir"**.

## ✅ Lo construido (2026-09-17)
- **Commit previo `04d3b32`** (punto de retorno) + **snapshot** de las 82 instancias en `docs/snapshots/galeria_snapshot_2026-09-17.json`.
- **`Mechanics/Breath/BP_BreathManager_SC` + `MPC_Breath`** — tracker: `.claude/skills/unreal-vr/blueprints/BP_BreathManager_SC.md`. Colocado como `GAL_BreathManager` en `Galeria/_Sistema`.
- **7 BPs + 6 materiales** con perillas `R - Respiracion` (0 = idéntico a hoy). Cada tracker tiene su sección 2026-09-17.

| Estación | Instancias | Valores escritos (2ª pasada) | Verificado |
|---|---|---|---|
| 1 Haces | 20 | **Intensidad 0 → autorada** (`BreathIntensity 1`) · Spread In 0,8 / Out −0,7 | ✅ PIE: Intensity 0,02 ↔ 1,08, Spread 0 ↔ 126, curvas redondeadas |
| 5 VoidField | `GAL_4_VoidField` | **Giro** Spin In −0,9 / Out 3,0 · Density In 0,22 / Out −0,65 / Soft 0,06 | ✅ MID (las otras 10 VoidFields en 0) |
| 6 LineField | 1 | Wave In 1,0 / Out −0,9 | ✅ MID |
| 7 Sombra | 1 | Length In −0,65 / Out 2,0 · Sweep In −0,9 / Out 0,7 | compila estricto |
| 8 Metaball | 1 | BreathAttract 1 · **Spread** In 0,6 / Out −0,97 · **Curl** In 0,5 / Out −0,95 | ✅ MID |
| 9 Burbujas | 1 | Reveal In 0,5 / Out −0,65 · Size In 0,35 / Out −0,3 | ✅ MID |
| 10-11 Túneles | 8 + 3 | Size In 0,35 / Out −0,25 · Speed In −0,9 / Out 1,5 | ✅ MID (anillos y marco; el fondo en 0) |

**4ª pasada (vigente):** *"todo llega demasiado rápido a sus destinos"* → la causa era la **amplitud**: la escala fija en cm hacía que una respiración de ~3 cm cruzara el codo en el primer tercio. El manager ahora tiene **ganancia automática por usuario** (aprende la amplitud en ~8 s: una respiración normal de cualquiera llega a ~0,8 justo al final), `HorizTau 8`, resorte `SmoothFreq 4`, y la respiración de prueba genera cm que pasan por ese mismo camino (`FakeAmpCm`). Haces: intensidad lineal. Medido en PIE con 3 cm / 10 s: pico ±0,79 exactamente al final de cada media onda.

**3ª pasada (valores de estaciones, siguen vigentes):** haces `Spread 1,2 / −0,85` + intensidad · puntos (04 y 05) **crecen al inhalar** con `SizeIn 0,6 / SizeOut −0,35`, capas a distinto ritmo (0,36 / 0,6 / 0,84), giro igual al inhalar y ×5 al exhalar · líneas `1,6 / −0,95` · sombra largo `−0,8 / 3,0`, barrido `−0,5 / 1,2` · metaball **sin cambios** · burbujas revelado `0,8 / −0,8`, tamaño `0,6 / −0,45` · túneles tamaño `0,55 / −0,35`, velocidad `−0,85 / 2,5`, **espiral al exhalar** (circulares: estiramiento 0,35 + giro 1,2 rad/s; rectangulares: torsión 3 rad). Manager: `HorizTau 6`, `S` del band-pass crudo con codo suave y resorte (`SmoothFreq 6`), `SignedGain 1`/cm.

**2ª pasada (feedback de Beltrán tras probar):** *"llegó muy duro a los máximos y mínimos"* → el manager publica `S` con techo suave (`k·y/(1+(k−1)|y|)`, `SignedGain` 2) en vez de `clamp`, y cada consumidor usa `1 + S·lerp(−Out, In, smoothstep)` en vez de tramos con quiebre. *"Más exagerados"* → todas las ganancias subieron. Haces: se sumó la **intensidad**. Metaball: exhalar baja **spread y curl** a casi 0 (antes el curl seguía separando las gotas). Puntos: la densidad no se notaba → **giro** integrado por fase (la escala de los cascarones se descartó: vista desde el centro no cambia nada en pantalla).

## 🔀 Lo que cambió al construir (los datos mandaron)
- **Metaball**: no fue `Spread` directo. El material ya hacía `Attract = lerp(Min, Max, sin(Time·Speed))`: el metaball **ya respiraba por reloj**. La respiración **reemplaza ese seno** cuando hay umbral (`On`) y vuelve al reloj al salir. Mismo rango autorado, cero riesgo de recorte.
- **Haces**: la ganancia escala el **radio del extremo** (`50 + Spread`), no `Spread`. Los haces tienen `Spread` 5 o 54,8; así se abren todos y el pozo acompaña con la misma cuenta. Cerrar termina en tubo.
- **Túneles**: hay **8 en la estación 10 y 3 en la 11** → el tamaño va **en el shader** (escalar actores costaría 144 transformadas por frame). La velocidad se integra por fase desde `FlowIn`/`FlowOut`.
- **VoidField**: está autorado denso (0,73) → rango asimétrico. Se agregó el borde suave, con `Soft 0` idéntico.
- **Sombra**: barrido al exhalar +50 % (con +70 % llegaba a 34°/s).

## 🎛️ Cómo probarlo
- **Editor, sin Play**: seleccionar `GAL_BreathManager` y mover **`PreviewBreath`** (−1 exhala … +1 inhala). Responden en el viewport las estaciones por material: 5, 6, 8, 9, 10, 11.
- **PIE sin gafas**: `bFakeBreath` en `GAL_BreathManager` (respira sola, período `FakePeriod`). Ahí se ven también las de CPU (1 y 7).
- **Visor**: mando en la panza, quieto 1,5 s → zumbido + pulso = conectado. Cualquier mano.
- **Quitar la interactividad**: poner en 0 las perillas `R - Respiracion` de la instancia (o borrar `GAL_BreathManager`: sin él `Signed` = 0 y todo queda como antes). Los valores originales de todo el nivel están en el snapshot.

## El pedido (Beltrán, textual y resumido)
Traer la mecánica de respiración a `/Game/TestMeshes` (la galería) y probar cómo se siente controlar parámetros en cada estación:
- 1ª (GAL_0, haces): **apertura del cono**.
- 2ª, 3ª, 4ª (océano, niebla, Ganzfeld): **nada**.
- 5ª, 6ª (VoidField, LineField) y 7ª (sombra): **decido yo**.
- 8ª metaball: **spread o curl**. 9ª burbujas: **tamaños y aparición**.
- 10ª y 11ª (túneles): **tamaño y velocidad baja al inhalar; velocidad y tamaño al exhalar**.
- La mecánica tiene que traer **umbral, háptica, etc.**: lo acordado para que sea **portable** entre proyectos.
- **Guardar los valores actuales de los BP del nivel**, para volver atrás si se quita la interactividad.
- Referencia de calidad: **la esfera de Entering** (`BP_BreathOrb_SC` + modo 1 de `BP_Sensor_Soul`), que "funciona excelente".

## 1. Por qué la esfera se siente tan bien (lo que hay que copiar)
- **La señal es una POSICIÓN**: `BreathLevel` sale del desplazamiento de la panza (`GeomHoriz` con band-pass 0,4 s / 3 s). La esfera la sigue 1 a 1: el tamaño **es** la respiración. Rango típico del usuario mediano: nivel 0,18 ↔ 0,81.
- **Rango enorme**: 15 ↔ 130 cm (≈3× en una respiración normal). Un ±10 % no se siente.
- **Suavizado corto**: `FInterpTo` 4 sobre un nivel que ya trae `LevelFollow` 5 → ~0,45 s de retraso total.
- **Reposo neutro y entrada sin salto**: fuera del umbral el objetivo es 0,5; en el flanco IN el sensor resiembra la señal y fija el nivel en 0,5.
- **La háptica confirma la conexión**: zumbido continuo (`HapticAmp` 0,25) mientras `bBreathing` + pulso en el flanco IN.

## 2. Principios de mapeo para la galería
1. **Una lectura principal por estación, en la dirección del cuerpo.** Inhalar = expandir, abrir, revelar, suspender. Exhalar = contraer, cerrar, retirar, fluir. Igual en todas las estaciones: el usuario aprende un solo idioma.
2. **Mapeos de POSICIÓN primero** (tamaño, apertura, altura, cantidad): siguen la respiración 1 a 1, como la esfera. Los de **VELOCIDAD** integran la señal (se sienten como "flujo", no como espejo). Por eso, cuando hay velocidad, va acompañada de uno de posición (túneles, sombra).
3. **Reposo = lo autorado.** Sin respirar (o con la interactividad apagada), cada perilla vale exactamente lo que Beltrán dejó. La respiración oscila **alrededor** de ese valor: `valor × (1 + max(S,0)·In + max(−S,0)·Out)`, con `S` en −1..+1 y dos perillas por mapeo: **cuánto cambia (±%) a inhalación plena** y **a exhalación plena**.
4. 🔴 **Nunca modular una velocidad que el shader calcula como `Time × Speed`**: cambiar `Speed` en caliente hace saltar la fase entera (con `Time` = 600 s, un Δ de 0,02 son 12 ciclos). La velocidad se integra: fase extra = `Speed · (In·∫max(S,0)dt + Out·∫max(−S,0)dt)`.
5. **Costo cero nuevo**: solo parámetros escalares en materiales que ya existen. Las estaciones ocultas no tickean (el director ya lo hace).
6. **Confort**: nada de girar con la respiración un espacio que envuelve al usuario (vección).

## 3. Arquitectura portable
### `BP_BreathManager_SC` — el Manager (Actor, uno por nivel)
Propuesta de carpeta-paquete: `/Game/SoulCharger/Mechanics/Breath/` (manager + `MPC_Breath` + página en `docs/MECANICAS-PORTABLES.md` §4.7).
- **Motor de señal**: `HeadGeom` + quietud + `UpdateLevel` v6 (con `HoldSlow`/`HoldMovK`) + `BreathThreshold` v4 (zona + quietud + amplitud; debounce 1,5 / 0,2 s; resiembra en el flanco IN), **con los valores del CDO vivo de `BP_Sensor_Soul`** (no de un doc).
- **Háptica**: `BreathHaptic` + `Pulse` tal cual (a PlayerController directo, sin hubs). Perillas `bHaptics`, `HapticAmp`. Opcional para probar en visor: que el zumbido suba con la inhalación (apagado por defecto).
- **Sin pawn por clase**: cámara = `GetComponentByClass(CameraComponent)` del pawn poseído; mano = `HandRight`/`HandLeft` por nombre → `GetAttachParent` → `MotionControllerComponent` (el `FindHandMC` probado del rig). La punta es la posición del grip (el sensor de la obra va pegado al grip; la zona salió de esa geometría).
- **Mano**: `HandMode` 0 = auto (la primera que entra a la zona; cambia solo fuera del umbral, resembrando filtros) · 1 derecha · 2 izquierda.
- **Inicialización tardía**: reintenta en el Tick hasta tener pawn, cámara y manos.
- **No es dueño del input** (no usa gatillo; no choca con los botones de la galería).
- **Publica**: variables `BreathLevel`, `bBreathing`, `BreathDrive` (0..1 suavizado, 0,5 en reposo), `BreathSigned` (−1..+1), `bRightActive`, `bZone`, `bQuiet`; y el **`MPC_Breath`** con `Signed`, `FlowIn`, `FlowOut`.
- **Autoría sin visor**: `PreviewBreath` (−1..+1) escribe el MPC desde el Construction Script → **un solo slider hace respirar todas las estaciones en el viewport**. `bFakeBreath` + período, para PIE sin gafas (patrón `bFakeSignal` del BioHub). En `BeginPlay` el MPC vuelve a 0 y manda la respiración real.
- `SignedGain` (≈1,5, con clamp): con una sola perilla se ajusta cuánto mueve una respiración normal a toda la galería.
- **No viaja** (capa de obra): toma del sensor, práctica, modos por sala, conteo por inclinación (`DetectDir`/`CountBreaths` usan la señal que el análisis descartó), calibración dormida.

**Método de construcción**: mover el código probado, no reescribirlo. Opción preferida: `duplicate` de `BP_Sensor_Soul` y podar todo lo que no es respiración (nodos exactos, sin pasar por el DSL, que pierde pines), cambiar el acople al pawn por cirugía y **auditar que no quede ni una variable muerta** (Beltrán autora mirando el panel). La otra opción (leer DSL → escribir) solo si la poda resulta inviable, verificando cada AND de 3 pines con `get_node_infos`. `BP_Sensor_Soul` **no se toca**: la obra sigue igual; migrarla a consumidora del manager es un paso posterior, después del visor.

### Los Controls — las estaciones
- Cada material recibe un bloque chico: lee `MPC_Breath.Signed` y multiplica su parámetro por `1 + max(S,0)·In + max(−S,0)·Out` (un `Custom` de 3 entradas). `In`/`Out` son parámetros del MID, en 0 por defecto → **el material queda idéntico para todo el que no los prenda** (la obra, las otras estaciones y las otras instancias del mismo BP).
- Cada BP gana la categoría **`R - Respiración`** con esas perillas (0 en el CDO) y las empuja en su Construction Script. **No conoce al manager**: el único contrato es el MPC.
- Solo lo que es geometría de CPU (el barrido de la sombra y, si hace falta, el pozo de luz o la escala del túnel) lee el MPC desde el Tick del propio BP.

## 4. Estación por estación
| # | Estación | Inhala | Exhala | Parámetro · dónde | Cuidado |
|---|---|---|---|---|---|
| **GAL_0** | Haces (20) | el cono **se abre** | se cierra | `Spread` en `M_LightShaft` (WPO). Punto de partida: In +60 % / Out −50 % | 🔴 el **pozo del piso** depende de `Spread` en `ApplyFloorGlow` (CPU): tiene que acompañar o se despega. Leer esa función antes de elegir material vs Tick. Un haz con `Spread` 0 no se abre con un multiplicador: ver los valores reales. Más ancho = más fill aditivo |
| GAL_1..3 | Océano · Niebla · Ganzfeld | — | — | nada | — |
| **GAL_4** | VoidField | **el cielo se puebla**: se encienden estrellas | se apagan hasta quedar un cielo ralo | `Density` en `M_VoidDots_SC`. In +60 % / Out −60 %, con piso y techo absolutos (por encima de ~0,8 empieza a leerse como ruido) | 🔴 hoy es `step(n3, Density)`: cambiarla en caliente hace **parpadear** las estrellas. Pasa a un borde suave con ancho de parámetro (0 = el `step` de hoy, idéntico). Se descartaron: tamaño (mueve todos los puntos porque el jitter depende del tamaño), giro (vección y salto por `Time×Speed`), radios (casi invisibles sentado) |
| **GAL_5** | LineField | **sube el oleaje** | la superficie **se aquieta** | `WaveAmount` en `M_LineGlow_SC`. In +50 % / Out −70 % | más amplitud = más escorzo = más titileo; es la estación más justa (61-62 fps), pero esto no suma costo |
| **GAL_6** | Sombra (eclipse) | la sombra **se alarga** y **el giro se suspende** | se **recoge** hacia la esfera y **el giro fluye** | `LengthFade` (exponente, en `M_ShaftDark_SC`): In −50 % / Out +120 %. Barrido: `SweepPhase += SweepSpeed·DT·mult` en `StepSweep` (ya se integra en el BP → sin saltos): In −70 % / Out +70 % | el exponente no es lineal: ajustar mirando con el slider |
| **GAL_7** | Metaball | las gotas **se separan** | **se funden** en una sola masa | `Spread` (dentro del `Custom` de `M_MetaBlob_SC`: entrada nueva con la receta de 3 pasos). In +12 % / Out −60 % | 🔴 **asimétrico a propósito**: el cubo proxy ya recorta cerca de la extensión actual (~53 contra 50). Exhalar además abarata el march. Curl queda como alternativa si el spread no convence |
| **GAL_8** | Burbujas | **aparecen** más lejos y **se inflan** | **se retiran** a lo cercano y se achican | `RevealRadius` (In +60 % / Out −50 %) + inflado nuevo en `M_RimOnly_SC`: `TransformVector(LocalPosition)·k` (proporcional a cada burbuja, In +25 % / Out −20 %) | el revelado **es la gracia** del entorno (Beltrán): la respiración pasa a manejarlo. Inflar suma fill en la estación más cargada. `BP_RimShape_SC` usa el mismo material: queda igual con 0 |
| **GAL_9 / GAL_10** | Túneles | el portal **crece** y el viaje **frena** | el viaje **fluye** y el portal **se achica** | Velocidad: `Time` + offset integrado desde el MPC, que entra a todos los `Custom` que calculan `t` (In −75 % / Out +80 %). Tamaño: In +20 % / Out −15 % | 🔴 **`Speed` NO se puede tocar en caliente** (salta la fase). Tamaño: escalar el actor es exacto pero cuesta ~18 actualizaciones de transform por túnel por frame; **contar cuántos túneles hay en cada estación** antes de elegir CPU vs shader |

Todos los porcentajes son **puntos de partida para el slider**, no decisiones cerradas.

## 5. Guardar lo que hay (antes de tocar nada)
1. **Snapshot**: todas las variables instance-editable + transform de cada actor `GALSTATION`, del director y de los hubs → `docs/snapshots/galeria-2026-09-17.json` (script con la plantilla `safe_script.py` + canario de actores).
2. **Script de restauración** que lee ese JSON y reescribe las instancias.
3. Proponer a Beltrán **commitear antes de construir** (hay borrados del fur y de `Hang` sin commitear).
4. Garantía de diseño: con las perillas `R - Respiración` en 0, cada estación queda exactamente como está hoy.

## 6. Qué se verifica con el MCP antes de construir
- `get_properties` de `Anchors`/`StationTags`/`Names` del director: confirmar el orden GAL_0..GAL_10 y la numeración que usó Beltrán.
- Valores reales de cada instancia: `Spread` de los 20 haces (¿hay ceros?), `Density` del VoidField de GAL_4, `WaveAmount`, `LengthFade`/`SweepSpeed`, `Spread` del metaball, `RevealRadius` de las burbujas, **cuántos túneles** hay en GAL_9 y GAL_10.
- Grafos: `ApplyFloorGlow` (cómo entra `Spread` al pozo), cómo llega `Time` a los `Custom` del túnel, cómo empaqueta el metaball sus parámetros, y en `BP_Sensor_Soul`: `TickBreath`, `HeadGeom`, `UpdateLevel`, `BreathThreshold`, `BreathHaptic`, `Pulse`, de dónde salen la cámara, el grip y las velocidades, y si `CountBreaths` hace vibrar.
- El pawn de `TestMeshes`: que tenga `HandRight`/`HandLeft` hijas de su grip.

## 7. Orden de construcción
0. Snapshot + commit (con OK de Beltrán).
1. `BP_BreathManager_SC` + `MPC_Breath` → PIE con `bFakeBreath`: el MPC se mueve, cero `Accessed None`, `BREATH: listo`.
2. GAL_0 (haces) → verificar con el slider en el viewport.
3. GAL_7 y GAL_8 (metaball, burbujas) → slider.
4. GAL_9 / GAL_10 (túneles) → slider + PIE con fake (la velocidad solo se ve corriendo).
5. GAL_4, GAL_5, GAL_6 → slider.
6. Visor con Beltrán, iterando en vivo con prints con nombre.
7. Trackers de cada BP tocado + `_INDEX.md` + `MECANICAS-PORTABLES.md` §4.7 + `assets-existentes.md`.
