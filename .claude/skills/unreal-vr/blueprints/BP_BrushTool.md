# BP_BrushTool — progress tracker

- **refPath**: `/Game/SoulCharger/Stages/Movement/BP_BrushTool.BP_BrushTool` · **parent**: Actor · **en nivel**: sí, `L_Test_Movement` en `(45, 0, 100)` (para el test; en la obra lo spawneará `BP_MovementInstructions`)
- **Propósito**: **la herramienta**. Prop que se auto-adjunta por proximidad a la mano que lo toca (esa mano queda como la hábil), lee el gatillo de **esa** mano y le pasa puntos a `BP_DrawCanvas`. No sabe nada de geometría. Plan: [`docs/stages/movement-surrounding.md`](../../../../docs/stages/movement-surrounding.md).
- **Estado**: 🟡 **Fases 1–3 construidas, compila limpio, guardado.** Fase 1 probada en visor ✅. Fases 2 (One-Euro) y 3 (presión + calma) **sin probar todavía**. Falta paleta, háptico, audio.

## 🎚️ Fase 3 — presión del gatillo → ancho · calma → luz (2026-07-30)
> 🔴 **La presión → ancho se DESCARTÓ (2026-07-30, mismo día):** en el test no respondió (el curl del índice no llega parejo en modo mandos) y el usuario decidió que el ancho lo elija desde la paleta (3 grosores discretos, Fase 4). **`ComputeWidth` quedó devolviendo el ancho fijo** (`return GetBrushWidth`). El cableado de abajo (eventos `IA_Hand_IndexCurl_*`, vars `TrigPressure/PressEMA/PressTau/WidthMinFrac`) quedó **inerte** — se limpia en la Fase 4.0. **La calma → material SÍ se mantiene.** Se deja el detalle documentado por si el enfoque de presión vuelve.
### Presión analógica SIN crear IMC (reusa una acción existente) — DESCARTADA, ver nota arriba
🔴 **El mapeo tecla→acción de un IMC NO se puede escribir por MCP** (el array `Mappings` de structs `FEnhancedActionKeyMapping` no serializa — `get_properties` devuelve `[]`). Solución: **reusar `IA_Hand_IndexCurl_Left/Right`** (del XRFramework, **Axis1D**, ya mapeadas en `IMC_Hands`, que el pawn `BP_VRPawn_SC` referencia). El XRFramework mapea el curl del índice al **gatillo analógico** también en modo mandos (para animar las manos) → es la presión del gatillo, gratis, ya activa.
- **Eventos en el EventGraph:** `IA_Hand_IndexCurl_Right.Triggered` → `Branch(bIsRightHand)` → **True** → `SetTrigPressure(ActionValue)`. El Left igual pero por la salida **False** del branch. Así sólo la mano hábil setea la presión. `ActionValue` (Axis1D) es un **float en el pin índice 5** del evento.
- 🔑 **`IA_Shoot_*` (Boolean) se mantiene para arrancar/parar el trazo** (probado). El curl es SÓLO para leer la presión → ancho. Dos acciones sobre el mismo gatillo conviven. **Si el curl no disparara en modo mandos, el trazo sale fino pero NO se rompe** (arranque/stop siguen por el booleano) → degradación elegante, no un fallo duro.
- **`ComputeWidth(DT) → float`:** EMA de la presión (`PressEMA`, tau `PressTau=0.08`) y `ancho = BrushWidth × (WidthMinFrac + (1−WidthMinFrac)×PressEMA)`. `WidthMinFrac=0.15` = piso no-cero (un toque suave deja trazo visible, §5.1). Se resetea `PressEMA=0` al empezar el trazo.

### Calma → luz (el biofeedback que se conserva)
- **`ComputeCalm(DT)`** (llamada en `UpdateStroke` cada frame de trazo): lee `GetLinearVelocity` (cm/s) y `GetAngularVelocity` (**Rotator**, deg/s — magnitud = `VectorLength(MakeVector(roll,pitch,yaw))`) del `AttachedController`. `speedEMA`/`turnEMA` (tau `SpeedTau=0.15`) → `calmRaw = clamp(1−speed/VMax) × clamp(1−turn/TurnMax)` (`VMax=120`, `TurnMax=200`, instance-editable) → `CalmVal = EMA` con **tau asimétrico**: `CalmTauDown=0.12` (ataque rápido cuando cae) vs `CalmTauUp=0.6` (recuperación lenta) — el tirón se nota enseguida, la calma vuelve con generosidad. `CalmVal` viaja a `AddPoint.Calm` (antes 1.0 fijo) → se hornea en vertex color alpha.
- **El material `M_Brush_Light` lo lee:** emissive × `lerp(CalmMin=0.22, CalmMax=1.0, VertexColor.A)`. Gesto brusco = tenue (pero **sobre el piso de 13/255**, no desaparece) · gesto suave = pleno. Ver tracker de `BP_DrawCanvas`.

### Variables nuevas (Fase 3)
`TrigPressure` `PressEMA` `WidthMinFrac`(0.15) `PressTau`(0.08) · `SpeedEMA` `TurnEMA` `CalmVal` `VMax`(120) `TurnMax`(200) `SpeedTau`(0.15) `CalmTauDown`(0.12) `CalmTauUp`(0.6). `BrushWidth` subido a **1.6** (ahora es el techo, no el ancho fijo).

## Estado anterior (Fases 1–2)
Ancho fijo, calma fija — superado por Fase 3.

## Componentes
- `DefaultSceneRoot`
- **`Body`** — cilindro (radio 0.7, alto 14) en `(7,0,0)` con `Pitch=-90` para que el eje Z de la primitiva apunte al **+X del actor** (adelante). Es placeholder: la malla real del pincel está en la lista de assets a proveer.

## Registro de variables
### Agarre (patrón calcado de `BP_BreathSensor_V2` / `BP_CalibProbe`)
- `LeftGrip` / `RightGrip` (MotionControllerComponent) — grips del pawn, cacheados en `AcquireControllers`.
- `AttachedController` (MotionControllerComponent) — al que se pegó.
- `bAttached` (bool) — ya se pegó.
- `bIsRightHand` (bool) — **la mano hábil**. Decide qué `IA_Shoot_*` consume, y más adelante de qué lado sale el háptico y en qué grip aparece la paleta.
- `TouchRadius` (float, **12** cm, instance-editable) — proximidad para auto-adjuntarse.

### Trazo
- `Canvas` (BP_DrawCanvas, **instance-editable**) — el lienzo. Si está vacío al BeginPlay, `EnsureCanvas` **spawnea uno** en el origen.
- `bTrigHeld` (bool) — gatillo de la mano hábil apretado. Lo setean los 4 custom events de input.
- `bStroking` (bool) — hay un trazo abierto en el canvas (evita llamar `BeginStroke` en cada frame).
- `BrushWidth` (float, **1.2** cm, instance-editable) — ancho fijo de la Fase 1. En la Fase 3 lo reemplaza la presión del gatillo.
- `TipOffset` (float, **16** cm, instance-editable) — a qué distancia del origen del actor, sobre su **forward**, está la punta que dibuja.
- `BrushColor` (LinearColor, **(0.15, 0.9, 0.45)**, instance-editable) — verde de la etapa. ⚠ Por encima del piso de 13/255 del panel del Quest (`materials-vr.md`).

### Filtro One-Euro de la punta
- `FiltPos` (Vector) · `FiltVel` (Vector) · `bFiltInit` (bool) — estado del filtro. Se resetea al empezar cada trazo.
- `MinCutoff` (float, **1.0** Hz) — bajarlo quita más temblor.
- `Beta` (float, **0.007**) — subirlo quita lag en los trazos rápidos.
- `DCutoff` (float, **1.0** Hz) — corte del filtro de la derivada.

`AutoReceiveInput = Player0` en el CDO. 🔴 **Sin esto un actor spawneado/colocado no recibe eventos de Enhanced Input** — lección ya pagada en `BP_CalibProbe`.

## Estructura de grafos

```
EventBeginPlay → reset de flags → AcquireControllers → EnsureCanvas
EventTick      → bAttached ? UpdateStroke : TryAttach
IA_Shoot_Left  → Triggered→TrigOnL  · Completed→TrigOffL
IA_Shoot_Right → Triggered→TrigOnR  · Completed→TrigOffR
```

- **`AcquireControllers()`** — castea el pawn a `BP_VRPawn_SC` y cachea `MotionControllerLeftGrip` / `MotionControllerRightGrip`.
- **`EnsureCanvas()`** — si `Canvas` no es válido, `SpawnActorFromClass(BP_DrawCanvas)` con **transform identidad** y lo guarda. 🔴 **La identidad no es cosmética** (ver abajo).
- **`TryAttach()`** — si `RightGrip` no es válido, reintenta `AcquireControllers`. Si lo es: mide la distancia del actor a cada grip; se queda con el más cercano que esté dentro de `TouchRadius`, setea `bIsRightHand` y llama `DoAttach`.
- **`DoAttach()`** — `bAttached=true`, `AttachActorToComponent(self, AttachedController, SnapToTarget loc+rot, KeepWorld scale)` y un `PrintString` que dice qué mano tomó el pincel.
- **`UpdateStroke()`** — punta cruda = `GetActorLocation + GetActorForwardVector × TipOffset`; up = `GetActorUpVector`. Si el gatillo está apretado: el primer frame `BeginStroke` (con la punta **cruda**, y `bFiltInit=false` para rearrancar el filtro), los siguientes `AddPoint` con la punta **filtrada** por `FilterTip`. Al soltar: `EndStroke`.
- **`FilterTip(Raw, DT) → Vector`** — **One-Euro Filter** (Casiez et al., CHI 2012). Saca el temblor de la mano cuando está casi quieta y no mete lag cuando el trazo es rápido a propósito:
  ```
  dx     = (Raw − FiltPos) / DT
  FiltVel = FiltVel + α(DCutoff, DT) · (dx − FiltVel)
  cutoff  = MinCutoff + Beta · |FiltVel|
  FiltPos = FiltPos + α(cutoff, DT) · (Raw − FiltPos)
  α(c,DT) = 1 / (1 + (1/(2π·c))/DT)
  ```
  Guarda contra `DT <= 0` y contra el primer frame (`bFiltInit`) devolviendo `Raw`. `DT` sale de `GetWorldDeltaSeconds` adentro de la función, así el `EventTick` no hubo que tocarlo.
  🔴 En el detector de **respiración** descartamos One-Euro porque su diseño (seguir más rápido cuanto más rápido se mueve) era lo contrario de lo que hacía falta. **Acá es exactamente su caso de uso original** (un puntero).
- **`TrigOnL/TrigOffL/TrigOnR/TrigOffR`** — cuatro custom events de 2 nodos que setean `bTrigHeld` **sólo si la mano coincide** con `bIsRightHand`. Así el gatillo de la mano libre no dibuja.

## 🔴 Restricciones que no se pueden romper

1. **El `BP_DrawCanvas` tiene que estar en transform IDENTIDAD.** El pincel le pasa la punta en **coordenadas de mundo**, y el `ProceduralMeshComponent` interpreta sus vértices en **espacio local**. Si el lienzo se mueve o se rota, el dibujo aparece desplazado. Por eso `EnsureCanvas` lo spawnea con `MakeTransform` vacío. *(Cuando llegue la miniaturización dentro de la ameba habrá que resolver esto: o el canvas convierte world→local al escribir, o la escala se aplica a un actor padre.)*
2. **Input por EVENTOS, nunca por value-getters.** Los getters de OpenXR devuelven 0 fuera de su IMC — lección de Calibration.
3. **Fase 1 usa `IA_Shoot_Left`/`IA_Shoot_Right` del XRFramework**, que son **Boolean**, no Axis1D. Es deliberado: ya están mapeadas en un IMC activo y son el camino probado (las usan `BP_Instructions` y `BP_CalibProbe`). La **Fase 3** las reemplaza por `IA_Draw_*` **Axis1D** propias del stage para tener presión analógica; hasta entonces el ancho es fijo.

## Cómo testearlo (PIE o visor, `L_Test_Movement`)
1. El pincel aparece flotando a 45 cm adelante, a 1 m de altura. Acercar cualquiera de las dos manos → se pega y se imprime `MV: pincel tomado - mano DERECHA/IZQUIERDA`.
2. Apretar el gatillo **de esa mano** y mover → tiene que salir una cinta verde continua que **se retuerce siguiendo la curva, sin flips**.
3. **Primer chequeo si no se ve nada / se ve sólo desde atrás:** el winding de `BuildTriangles` en `BP_DrawCanvas` está derivado, no verificado — invertir el orden de los índices ahí.
4. Chequeo del frame: dibujar un espiral. La cara de la cinta tiene que girar suave, sin saltos bruscos de 180°.

## TODO
- [x] ~~Probar en visor~~ — ✅ funciona (2026-07-29): el pincel se toma y dibuja.
- [x] ~~**Fase 2**: One-Euro sobre la punta~~ — ✅ hecho (`FilterTip`). **Falta afinarlo con el casco puesto.**
- [ ] **Fase 3**: `IA_Draw_*` Axis1D propias + EMA de presión + rate-limit → `Width`; métrica de calma (`GetLinearVelocity` + giro de la dirección) → `Calm`.
- [ ] **Fase 4.5**: avisar a `BP_BrushPalette` qué mano quedó libre; suprimir el dibujo mientras la punta está en el volumen de la paleta.
- [ ] **Fase 5**: háptico por punto emitido + sonido continuo modulado.
- [ ] Malla real del pincel (hoy es un cilindro placeholder) y el `SceneComponent` de punta si se prefiere a calcularla por offset.
- [ ] Caso borde del plan §5.0: soltar el pincel a mitad de etapa y volver a tomarlo con la otra mano (hoy `bAttached` nunca vuelve a false).

## Session log
- **2026-07-29 (Fase 2)** — Agregado el **One-Euro** (`FilterTip` + 6 variables). `UpdateStroke` **recreado** (`remove_function_graph` → `compile` → `add`) para meter la llamada al filtro sin dejar huérfanos; `DT` se toma con `GetWorldDeltaSeconds` adentro para no tener que tocar el `EventTick`. Compila limpio con `warnings_as_errors`. Sin afinar en visor.
- **2026-07-29 (1er test en visor)** — 🎉 **Funciona**: el pincel aparece, se toma y dibuja. El trazo se veía "feo y geométrico" → era el material faltante del canvas, no este BP.
- **2026-07-29** — Creado desde el stub vacío. 12 variables, 5 funciones, 4 custom events de input, componente `Body`, CDO con `AutoReceiveInput=Player0` y defaults. Colocado en `L_Test_Movement` junto con un `BP_DrawCanvas` en el origen (y el `Canvas` del instance apuntando a él). Se sacó del nivel el `BP_BreathStageManager` que venía de la duplicación de `L_Test_Breath` (habría intentado cerrar una etapa que no existe acá). Compila limpio.
