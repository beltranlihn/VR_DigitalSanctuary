# BP_SoundBubble — progress tracker

Burbuja sonora del stage Touch (Fase 2 del brief [`docs/stages/touch-attracting.md`](../../../../docs/stages/touch-attracting.md)). Al apuntarla con el beam suena su clip en **loop con fade-in 1s** (preview); al salir del hover, **fade-out 1s**.

- **refPath**: `/Game/SoulCharger/Stages/Touch/BP_SoundBubble.BP_SoundBubble`  ·  **parent**: Actor  ·  **in level**: **no se colocan a mano** — las spawnea `BP_AttractDirector` en `BeginPlay`, una por `TargetPoint` con tag **`BubbleSpawn`** (hoy `TP_Bubble_01..06` en `L_Touch`). Para recomponer: mover/duplicar TargetPoints, sin tocar BPs. (2026-08-03)
- **Status**: 🟢 Fases 2-7 + **R1 (movimiento unificado e interpolado) y R2 (sacar burbujas a mano) PROBADOS EN VISOR** (2026-08-04). Encima, sin probar todavía: **hover-scale + `GrabSpeed` bajado a 6**. Las secciones de R1+R2 y de "ajustes de tacto" son las que mandan sobre movimiento y escala.

## Componentes (CDO)
- `DefaultSceneRoot`.
- `Mesh` (StaticMesh esfera, radio 8 = placeholder de la burbuja). Su colisión bloquea el canal Visibility → el line-trace del beam la detecta.
- `PreviewAudio` (AudioComponent) — `bAutoActivate=false`. Reproduce `PreviewSound` con fade.

## Variables
- `PreviewSound` : SoundBase — el clip de la burbuja · **instance-editable** (cada burbuja el suyo). **Vacío** hasta que haya audio (import manual, no hay tool MCP de audio).
- `BeamRef` : BP_AimBeam ref — cacheado en BeginPlay.
- `bWasHovered` : bool — para edge-detection del hover en Tick.
- **Tag del actor: `Aimable`** (en el CDO) → el beam la reconoce como apuntable.

## 🔄 Modelo PUSH (reescritura para dos manos) — 2026-08-03
Con **dos beams** (uno por mano) el modelo viejo se rompía: `BeginPlay` hacía `GetActorOfClass(BP_AimBeam)` y cacheaba **un solo** beam, así que la otra mano era invisible. Ahora **el beam avisa** en vez de que la burbuja pregunte:

- **`BeginPlay` eliminado** (ya no cachea nada) y **el polling de hover en Tick eliminado**. `EventTick` quedó en una sola línea: `if bIsGrabbed → DoFollow(DeltaSeconds)`.
- **`HoverCount : int`** + funciones **`NotifyHoverStart()`** / **`NotifyHoverEnd()`** que llama el beam. Es un **contador, no un bool**, justamente porque **las dos manos pueden estar apuntando la misma burbuja**: entra el fade-in solo cuando pasa de 0→1 y el fade-out cuando vuelve a 0 (con clamp en 0 para que un aviso de más no lo deje negativo).
- **`SetGrabbed` tiene un parámetro nuevo `Beam : BP_AimBeam`** y lo primero que hace es `SetBeamRef(Beam)`. Así **`BeamRef` dejó de significar "el único beam del mundo" y pasa a ser "el beam que me está agarrando"** — con eso `DoFollow` (que lo usa 3 veces) **quedó intacto** y sigue la mano correcta sola. `TryRelease` lo llama con `Beam` nulo, que limpia la referencia.
- `bWasHovered` **borrada** (era del edge-detection del polling).

## Grafos
- **EventBeginPlay**: `GetActorOfClass(BP_AimBeam_C)` → `CastToBP_AimBeam` → `SetBeamRef`. (Cachea el beam para leer su `CurrentHovered`.)
- **EventTick**: `beam=GetBeamRef`; `IsValid(beam)` → `now = (beam.CurrentHovered == self)`; si `now != bWasHovered` → (`now` ? `DoFadeIn` : `DoFadeOut`) + `SetWasHovered(now)`. **Polling de `CurrentHovered`** (no se ata el dispatcher entre actores; el beam expone la var pública). Edge-detected → los fades disparan una sola vez por transición.
- **DoFadeIn() / DoFadeOut()**: funciones auxiliares. `PreviewAudio.FadeIn/FadeOut(1.0s)`. 🔴 **Los nodos FadeIn/FadeOut se crearon por cirugía con `declaring_class=/Script/Engine.AudioComponent`**: el DSL resolvía el overload de `SynthComponent` (mismo nombre) y no conectaba el AudioComponent. Ver gotcha en el session log.

## TODO / next
1. **Asignar `PreviewSound`** a las burbujas (importar un .wav placeholder — p.ej. `Recursos/Audio/Heart/HeartBeat.wav` — como SoundWave y ponerlo en el campo, o setear el default en el CDO). Sin sonido, el hover funciona (láser verde) pero el preview es mudo.
2. **Test en visor:** apuntar una burbuja → suena en loop con fade-in; salir → fade-out. (El loop depende de que el SoundWave/Cue sea looping.)
3. Estética: material unlit emisivo para la esfera (Quest); reemplazar la esfera placeholder por la mini-ameba.
4. Fases siguientes: far-grab + follow (Fase 3), attach a slot (Fase 4), audioreactivo (Fase 6), swap (Fase 7). Agregar el estado `Floating/Grabbed/Placed` cuando entre el grab.

## Open questions / risks
- El preview "loop" requiere que el clip sea looping (SoundWave con bLooping o un SoundCue con Looping). Definir al proveer el audio.
- Polling en Tick por burbuja (~20 burbujas) = 20 comparaciones/frame — trivial. Si escala mucho, migrar a los dispatchers `OnHoverBegin/End` del beam.
- Espacialización en Quest: fuentes deben ser mono + ITD Panner si se quieren posicionadas (ver `audio-quest.md`) — pendiente para el pulido de audio.

## Fase 3-4 (far-grab + placement) — 2026-07-30
**Vars nuevas:** `bIsGrabbed`, `GrabSpeed`(12), `bIsPlaced`, `MySlot`(BP_SeqSlot ref), `PlaceRadius`(25).
**Tick (cirugía):** se insertó un Branch al inicio → si `bIsGrabbed` → `DoFollow(DeltaSeconds)`; si no → la lógica de hover de antes.
**`DoFollow(DeltaSeconds)`:** 🔴 **DESACTUALIZADO — la función fue ELIMINADA el 2026-08-04**; su lógica vive en `UpdateMove` (ver R1). Era: `target = beam aim + forward * GrabHoldDistance`; `SetActorLocation(VInterpTo(...GrabSpeed))`.
**`SetGrabbed(NewGrabbed)`:** setea `bIsGrabbed`; si grab → `bIsPlaced=false` (permite re-colocar); si release → `TryPlace()`.
**`TryPlace()`:** `GetAllActorsOfClass(BP_SeqSlot)` → for-each → primer slot con Occupant inválido Y `Distance < PlaceRadius` → snap (`SetActorLocation` al slot), `bIsPlaced=true`, `MySlot=slot`, `slot.SetOccupant(self)`. (⚠ el `SetOccupant` cross-class es `(:Occupant valor :self target)` — el positional mapea mal.)
**Quién dispara el grab:** el `BP_AimBeam` (input grip `IA_Grab_Right`) llama `SetGrabbed`. Ver su tracker.
✅ **Occupant stale ARREGLADO (2026-08-03).** `SetGrabbed` con `NewGrabbed=true` ahora hace `IsValid(MySlot)` → libera el slot viejo (`SetOccupant(null)`) → `MySlot = null` → `bIsPlaced = false`. Antes, re-agarrar una burbuja colocada dejaba el slot marcado como ocupado para siempre: el secuenciador lo seguía disparando y ninguna otra burbuja podía entrar ahí.
## ✅ Fase 7 — SWAP hecho (2026-08-03)
- **`HomeLocation : Vector`** capturada en un `EventBeginPlay` nuevo (`SetHomeLocation = GetActorLocation`). Como las burbujas las spawnea el Director en los TargetPoints, cada una guarda la posición de su punto.
- **`ReturnHome()`**: `SetActorLocation(HomeLocation)` + `bIsPlaced=false` + `MySlot=null`.
- **`EvictSlot(Slot)`**: si el slot tiene `Occupant` válido → le manda `ReturnHome`.
- **`PlaceInNearestSlot` ya NO filtra slots libres**: busca el más cercano entre TODOS, y antes de colocarse llama `EvictSlot(best)`. Soltar sobre un bloque ocupado intercambia: la nueva entra, la vieja vuelve flotando a su lugar.
- Combinado con el fix del `Occupant` stale, el ciclo agarrar → colocar → re-agarrar → mover a otro slot queda consistente.

⚠ **Dos trampas del DSL que costaron un intento cada una:**
- `(CallFunction|MiFuncion arg)` posicional se conecta al pin **`self`**, no al parámetro → usar **keyword** (`:Slot _best`). Igual que ya pasaba con `SetOccupant`.
- Llamar una función **sobre otra instancia de la misma clase** no es `Class|BPSoundBubble|ReturnHome` (no existe): es `(CallFunction|ReturnHome :self _otro)`.
- 🔴 Y la de siempre: **`remove_function_graph` sin `compile_blueprint` en el medio deja el nombre tomado** → el `add_function_graph` devuelve `PlaceInNearestSlot_0`. Además, borrar una función deja **colgado el nodo de llamada** en quien la usaba: hay que borrar ese nodo, compilar, recrear la función y recrear la llamada.

✅ **ARREGLADO 2026-08-03 — `TryPlace` fue reemplazada por `PlaceInNearestSlot`.** Ahora hace **mínimo corriente**: arranca con `BestDist = PlaceRadius` y `BestSlot = null`, recorre los slots libres quedándose con el de menor distancia, y recién al final coloca si `BestSlot` es válido. Vars nuevas `BestSlot` / `BestDist`. `SetGrabbed` llama a la función nueva; `TryPlace` fue borrada.
⚠ Se usó la receta de `gotchas.md` para rehacer un function graph sin dejar escombros: `remove_function_graph` → **`compile_blueprint`** → `add_function_graph` → `write_graph_dsl`. Un `write_graph_dsl` que falla a mitad **deja nodos sueltos**; ante un error, recrear el grafo en vez de parchear.
⚠ `Utilities|Array|Get` **no existe** como type_id: es `Utilities|Array|Get(acopy)` / `Get(aref)`. Y `SetActorLocation` necesita `:NewLocation` explícito, si no el DSL mapea el vector al pin `self`.

<details><summary>Bug original (histórico)</summary>

🔴 **BUG conocido en `TryPlace` (detectado 2026-08-03, sin arreglar):** se queda con el **PRIMER** slot que devuelve `GetAllActorsOfClass` dentro de `PlaceRadius`, **no con el más cercano**. Con los slots cada 30cm y `PlaceRadius=25` las zonas de captura se superponen, así que soltar una burbuja entre dos slots la manda al que el array liste primero, no al que apuntó el usuario — en VR se siente como que el objeto salta al lugar equivocado. **Fix:** recorrer todos los slots libres, quedarse con el de menor distancia y recién ahí comparar contra `PlaceRadius`. Con eso el espaciado de la fila deja de ser crítico.

</details>

## 🟡 Fase 6 — pulso audioreactivo (lado burbuja LISTO, falta 1 conexión)
> ⚠ **`UpdatePulse` fue reescrita el 2026-08-04** para ser la única dueña de la escala (pulso × hover). Lo de abajo describe el pulso; la fórmula vigente está en "Ajustes de tacto".
- **Vars:** `PulseT`(0), `PulseAmount`(0.35), `PulseDecay`(5.0), `BaseScale`(0.16 = la escala real del mesh esfera).
- **`PulseOnBeat()`** → `PulseT = 1.0`. Es el hook que llama el Director en el beat.
- **`UpdatePulse(DeltaSeconds)`** → si `PulseT > 0`: decae por `DeltaSeconds * PulseDecay` (con `Max(0,…)`) y escala el `Mesh` a `BaseScale * (1 + PulseT * PulseAmount)`. Cuando llega a 0 deja de tocar la escala, así no cuesta nada en reposo.
- **`EventTick`** llama `UpdatePulse` **siempre** (después de la rama de `DoFollow`), por eso el decay corre esté agarrada o no.

🔴 **FALTA UNA SOLA CONEXIÓN:** que `BP_AttractDirector.OnBeat` llame `PulseOnBeat` sobre el `Occupant`. **Bloqueado por el gotcha del registro de nodos** (ver `gotchas.md`): `Class|BPSoundBubble|PulseOnBeat` no resuelve desde el grafo del Director hasta reiniciar el editor. Probado sin éxito: recompilar ambos BPs, `save_assets`, `load_asset`. **Al reabrir el editor, agregar ese nodo en el branch "Is Valid" del `OnBeat` y listo.**

## Audio placeholder — 2026-08-03
`PreviewSound` tiene default en el CDO: **`Stages/Touch/Audio/MS_Synth`** (MetaSound **procedural**, no depende de ningún `.wav` → suena tal cual). Así las burbujas spawneadas dejan de ser mudas sin esperar al sound designer.
**Pendiente:** que cada burbuja tome un clip distinto de `DA_SoundBank` (hoy todas comparten el default). Requiere una ref al DataAsset en `BP_AttractDirector` y usar el `Array Index` del ForEach del spawn para hacer `SetPreviewSound(Clips[i % Length])`.

## ✅ R1 + R2 CONSTRUIDOS Y COMPILANDO — 2026-08-04 (falta test en visor)
Ver [`docs/stages/touch-attracting.md`](../../../../docs/stages/touch-attracting.md) §2.a y §4.b.

### El movimiento pasó a ser UNO SOLO: `UpdateMove(DeltaSeconds)`
Antes había **tres caminos** de movimiento y solo uno interpolaba: `DoFollow` con `VInterpTo`, y `PlaceInNearestSlot` / `ReturnHome` con `SetActorLocation` **instantáneo** (se veían como teleports). Ahora hay **un único `VInterpTo`** y los otros dos solo **setean un destino**.

**Vars nuevas:** `TargetLocation : Vector` (a dónde va) · `bMoving : bool` (¿viajando a un destino fijo?) · `TravelSpeed : float = 6` (velocidad de viaje a slot/casa; **`GrabSpeed`=12 sigue siendo la del follow** — dos palancas distintas a propósito).

**`UpdateMove(DeltaSeconds)`** (función nueva, llamada **incondicionalmente** desde el Tick):
1. Si `bIsGrabbed` → `bMoving = false` y `TargetLocation` = pose del beam (`GetAimSource` + forward × `GrabHoldDistance`). O sea: **agarrar cancela cualquier viaje en curso** — si no, al soltarla salía volando hacia un destino viejo.
2. Si `bIsGrabbed OR bMoving` → **un solo** `VInterpTo(GetActorLocation → TargetLocation, DeltaSeconds, Select(bIsGrabbed ? GrabSpeed : TravelSpeed))` → `SetActorLocation`.
3. Llegada: si **no** está agarrada y `VectorLengthSquared(Target − New) < 1.0` (=1 cm) → `SetActorLocation(TargetLocation)` exacto + `bMoving = false`. El snap final evita quedar a fracción de cm del slot.

**`PlaceInNearestSlot`** — el `SetActorLocation` fue reemplazado por `SetTargetLocation(slot.Location)` + `bMoving=true`. **La ocupación del slot se sigue marcando al instante** (`SetOccupant`/`MySlot`/`bIsPlaced`): el secuenciador la toma en el beat siguiente y el visual llega interpolando. Es deliberado.
**`ReturnHome`** — igual: `SetTargetLocation(HomeLocation)` + `bMoving=true` en vez del `SetActorLocation`.
**`DoFollow` ELIMINADA** (su lógica vive en `UpdateMove`). El `EventTick` quedó en dos líneas: `UpdateMove(DeltaSeconds)` → `UpdatePulse(DeltaSeconds)`; se fueron el Branch y el getter de `bIsGrabbed`.

### R2 — sacar burbujas a mano ✅
La rama **"Is Not Valid"** del `IsValid(BestSlot)` de `PlaceInNearestSlot` estaba **vacía** → soltar una burbuja lejos de la mesa la dejaba flotando donde cayera (y sentado se podía perder de alcance). Ahora llama **`ReturnHome()`** → vuelve interpolando a su `HomeLocation`. Liberar el slot ya funcionaba (se hace al agarrar).

🔴 **`TravelSpeed` NO puede quedar en 0:** `VInterpTo` con `InterpSpeed <= 0` **salta directo al target** — el teleport que veníamos a arreglar, de vuelta y en silencio. Default puesto en el CDO y **verificado leyendo el valor efectivo** (`get_properties` → `TravelSpeed:6, GrabSpeed:12, bMoving:false`).

## ✅ R1 + R2 PROBADOS EN VISOR — 2026-08-04
Funcionan: el viaje al slot y la vuelta a casa interpolan (se acabaron los teleports), el swap muestra a la vieja volando, y sacar burbujas del slot y soltarlas lejos las devuelve a su lugar liberando el slot. **Feedback del usuario: "todo iba super bien"**, con dos ajustes de tacto (abajo).

## 🎚️ Ajustes de tacto pedidos tras el test — 2026-08-04
### 1. Hover = la burbuja se agranda un poco
🔴 **El hover y el pulso del beat escriben LA MISMA escala del mesh** → no se puede agregar el hover por afuera, se pisan (la burbuja late y el latido borra el agrandado, o al revés). Por eso **`UpdatePulse` pasó a ser el ÚNICO dueño de la escala** y combina los dos efectos **multiplicándolos**:

`Mesh.Scale = BaseScale × (1 + PulseT × PulseAmount) × (1 + HoverT × (HoverScale − 1))`

- **Vars nuevas:** `HoverScale : float = 1.15` (cuánto crece; 1.0 = no crece) · `HoverT : float` (0→1 suavizado, **estado interno, no tocar a mano**) · `HoverSpeed : float = 8` (qué tan rápido entra/sale el agrandado).
- `HoverT` persigue con `FInterpTo` el objetivo `HoverCount > 0 ? 1 : 0` → **el agrandado entra y sale suave**, y como se apoya en `HoverCount` (no en un bool) **las dos manos sobre la misma burbuja no lo duplican**, igual que el audio.
- **Qué palanca mover:** ¿crece poco/mucho? → `HoverScale`. ¿El crecimiento se siente brusco o lento? → `HoverSpeed`. ¿El latido del beat? → `PulseAmount`/`PulseDecay`, que quedaron intactos.

⚠ **Se quitó el early-out `if PulseT > 0`** que evitaba escribir la escala en reposo. Con el hover metido adentro, ese guard pasaba a ser un **bug**: en el frame en que `HoverT` llega a 0 el guard corta y el mesh queda con la última escala agrandada. Ahora la escala se escribe siempre: son ~20 `SetRelativeScale3D` por frame, ruido frente a los line-traces en un target **fill-rate bound**. Si algún día el profiling lo señala, la solución es un flag "dirty", no volver al guard.

✅ De paso se **colapsó la expresión de escala que estaba inlineada 3 veces** (una por eje del `MakeVector`) a un solo `bind` → un subárbol en vez de tres (`bp-lean-construction.md`). ⚠ El `read_graph_dsl` la sigue **mostrando** 3 veces: es el inlineado de nodos puros del read, no una duplicación real.

### 2. La burbuja llegaba demasiado rápido a la mano
**`GrabSpeed` 12 → 6**, y tras un segundo test **6 → 3**.
⚠ **`GrabSpeed` gobierna DOS cosas a la vez** porque `VInterpTo` es proporcional a la distancia: el **tirón inicial** (la burbuja está lejos → se mueve rápido en términos absolutos, que es lo que se sentía violento) **y** el **retraso del seguimiento** mientras la sostenés. Bajarla suaviza el tirón pero también hace el follow más flotante. Si el tirón sigue molestando pero el follow queda mushy, la separación correcta es **`FInterpToConstant`** (velocidad uniforme en cm/s, el acercamiento nunca es violento) — no está construido.

### 3. Ir al slot y volver a casa dejaron de compartir velocidad — 2026-08-04 (2º test)
El usuario pidió **la mitad de velocidad para volver al punto original** (venga de la mano o de un slot) **sin tocar** la velocidad de ir al slot, que ya se sentía bien. Pero `TravelSpeed` gobernaba **las dos**. Se separaron:

- **`MoveSpeed : float`** — 🔴 **estado, no configuración**: la velocidad del viaje **en curso**. `UpdateMove` la usa cuando la burbuja NO está agarrada. **No tocar a mano.**
- **`ReturnSpeed : float = 3`** — configuración: la velocidad de **volver a `HomeLocation`**. La setea `ReturnHome()` en `MoveSpeed`.
- **`TravelSpeed : float = 6`** — configuración: la velocidad de **ir a un slot**. La setea `PlaceInNearestSlot` en `MoveSpeed`.
- El `Select` de `UpdateMove` quedó `bIsGrabbed ? GrabSpeed : MoveSpeed`. **Cada origen de movimiento declara su propia velocidad** al arrancar el viaje — agregar un tercer tipo de viaje es una línea más, no otro `Select` anidado.

**Valores vigentes verificados en el CDO:** `GrabSpeed 3` · `ReturnSpeed 3` · `TravelSpeed 6` · `MoveSpeed 6` (default de arranque, se pisa en cada viaje).

### Pendiente de este BP
1. 🔴 **Test en visor del hover-scale y de las velocidades nuevas.**
2. **R4 — Doble hover: verificar, no construir.** `HoverCount` ya está bien resuelto (contador con clamp en 0, fade-in solo en 0→1). **Falta el test en visor** apuntando la misma burbuja con las dos manos: el preview tiene que sonar **una sola vez**.
3. **R8 — Audio.** Migrar `PreviewSound` a la arquitectura del §3.b del brief: **un solo `MS_BubbleVoice`** parametrizado (pin `Wave` de **constructor**, seteado con `SetObjectParameter` **antes** del Play) en vez de un SoundBase por burbuja. Salida **mono** + `ITD Panner` + Plate Reverb dentro del grafo. **Recién cuando lleguen los clips reales** — hoy `MS_Synth` alcanza.

## Session log
- **2026-08-04 (tacto):** R1+R2 **probados en visor y aprobados**. Vars `HoverScale`/`HoverT`/`HoverSpeed`; `UpdatePulse` recreada (borrar nodo de llamada → compile → `remove_function_graph` → compile → `add_function_graph` → `write_graph_dsl` → recrear la llamada) para que combine pulso × hover en una sola escritura de escala; `GrabSpeed` 12→6 en el CDO. Compila y guardado.
  - ⚠ **`Math|Float|Max(Float)` NO se usó** por la trampa de los paréntesis en el type_id → el clamp a 0 se hizo con `(select (> x 0.0) x 0.0)`, solo operadores.
  - ⚠ **`Transformation|SetRelativeScale3D`** lleva `:self` (componente) + **`:NewScale3D`** explícitos, igual que `SetActorLocation` con `:NewLocation`.
- **2026-08-04 (R1+R2):** vars `TargetLocation`/`bMoving`/`TravelSpeed`; función nueva `UpdateMove` por `write_graph_dsl` (grafo vacío = seguro); cirugía en `EventGraph` (fuera Branch + getter `bIsGrabbed` + llamada a `DoFollow`, entra `UpdateMove` incondicional), en `ReturnHome` y en `PlaceInNearestSlot` (fuera los `SetActorLocation`, entran `SetTargetLocation` + `SetMoving`), y `ReturnHome()` en la rama "Is Not Valid". `DoFollow` borrada (primero el nodo de llamada → compile → `remove_function_graph` → compile). Default de `TravelSpeed` en el CDO. Compila y guardado.
  - ⚠ **`Math|Vector|Distance(Vector)` que emite el `read` es riesgoso de escribir** (los paréntesis en el type_id chocan con el parser del S-expr). Se usó **`Math|Vector|VectorLengthSquared`** del delta, que además evita la raíz cuadrada.
  - ⚠ **`AssetTools.save_assets` toma `asset_paths: ["/Game/..."]` (strings, sin `.Nombre`), NO `assets:[{refPath}]`** como el resto de las tools.
  - ⚠ **`find_node_types` con filtro genérico ("Distance") devuelve ~300 entradas.** El filtro tiene que ser el prefijo completo (`Math|Vector|VectorLength`).
- 2026-07-29: Fase 2 construida. Componentes Mesh+PreviewAudio, vars PreviewSound/BeamRef/bWasHovered, tag "Aimable". EventGraph (BeginPlay cachea beam; Tick polling+edge-detection). Fades en funciones `DoFadeIn/DoFadeOut`. **Gotcha:** `Audio|Components|Audio|FadeIn/Out` tiene overload AudioComponent Y SynthComponent con el mismo type_id → el DSL elegía SynthComponent ("Could not connect PreviewAudio to self"). Solución: crear los nodos por `create_node` con `declaring_class=/Script/Engine.AudioComponent` en funciones aparte. Compila. 3 burbujas en `L_Touch`. `PreviewSound` vacío (falta audio). Guardado.
