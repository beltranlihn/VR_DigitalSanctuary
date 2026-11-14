# BP_AttractCall_SC: llamada y respuesta (Attracting con el hang)

**Ruta:** `/Game/SoulCharger/Mechanics/Harp/Blueprints/BP_AttractCall_SC`
**Colocado en:** `/Game/SoulCharger/Mechanics/Harp/Maps/Test_AttractingHang` como `AttractCall` (`BP_AttractCall_SC_C_0`), en el PlayerStart (362700, 100000, 0), con yaw 0.
**Nació:** 2026-11-04, después de la investigación de mecánicas VR (Ragnarock: el ritmo mueve el mundo; SPHERES: escuchar con el gesto). Beltrán había descartado los chorros de partículas (*"se ve muy sucio"*), las órbitas y el amanecer, y pidió algo *"muy simple, evocativo, minimal, que dé cuenta de cómo se transforma nuestro entorno a medida que tocamos, ya que cierta cantidad de toque es lo que termina la etapa"*. A la propuesta de llamada y respuesta contestó: *"Haz la prueba"*.

**Estado:**
- 🟢 Compila.
- 🟢 PIE con `bDebugNotes` (una nota cada 1,5 s): 51 respuestas en unos 75 s. La ameba fue de 24 m a 2,3 m, y al llegar se marcó `bStageDone`. La voz suena: `HARP pluck i` sale del actor `BP_Harp_SC_C_1`. Solo hay 2 `BP_QuestCtrl_SC`, o sea sin mandos duplicados. 0 `Accessed None`.
- ⬜ Visor: legibilidad de las ondas, si la respuesta se entiende como respuesta, la voz, la háptica y el ritmo del acercamiento.
- ⬜ Notas reales del hang (en PIE solo hubo notas automáticas).
- ⬜ Costo en el Quest, con 2 sintes de MetaSounds.
- ⬜ Sin commit.

## La mecánica
1. **La llamada.** Cada golpe del hang lanza una **onda**: un anillo fino del color de la nota sobre el espejo del salar, que nace al pie del hang. Crece a `WaveSpeed` (11 m/s).
2. **La respuesta.** Cuando la onda llega a la ameba (en el plano, contra donde está **ahora**):
   - la ameba **brilla** (`EdgeIntensity` sube a `GlowPeak` y baja en `GlowDecay`);
   - se acerca un paso (`StepPerCall` × (1 − `StepVelGain` + `StepVelGain` · fuerza del golpe));
   - **devuelve una onda** del mismo color, más tenue (`ReturnAlpha`).
3. **Lo que te alcanza.** Cuando la onda de vuelta llega a ti, **suena la voz de la ameba**: la misma nota una octava más arriba, con timbre de arpa, que llega más fuerte cuanto más cerca está. **Vibra el mando derecho** (lo hace el `Pluck` del hang; `bVoiceRight`).
4. **El arco.** La distancia es el retardo. Al principio la respuesta tarda unos 4,4 s (24 m de ida y vuelta) y suena como un eco lejano. Cerca, la respuesta llega en 0,4 s y se vuelve un dúo.
5. **El final, el abrazo (2026-11-05).** Beltrán: *"arma el final que me envuelve"*.
   - Cuando `Shown` llega a 1 (la ameba en `NearPoint`), empieza el abrazo (`AcEmbrace`): en `EmbraceTime` (6 s, smoothstep) la ameba sigue hasta el ojo (`EmbraceEye`, la cámara en ese momento) y crece de `AmoebaSize` 1,2 a `EmbraceSize` 3,6 (radio 50·Size cm: de 60 a 180 cm).
   - `M_ProtoSoul` es de una cara, así que desde adentro no se ve. Por eso se enciende **la membrana**, `Shell`: la `/Engine/BasicShapes/Sphere` con `M_AttractShell_SC` (translúcido de dos caras), de radio `ShellRadius` 160 cm y centrada en el ojo. Ondula por su normal (`ShellWobble` 4 cm) y tiene **venas** lentas que derivan (`ShellVeins` 0,6). Es de color `ShellColor` ámbar, brilla con `ShellGlow` 1,2 y **late con cada respuesta** (`Pulse`).
   - Su alfa sube según cuánto está el ojo **dentro** de la ameba (radio − distancia: de −20 a +40 cm, de 0 a `ShellAlpha` 0,55), así se enciende justo cuando la cámara cruza el borde.
   - Al completarse el abrazo se marca `bStageDone` (log `ATTRACT stage done (embraced)`).
   - Adentro el dúo sigue: la ameba está en el ojo, así que las respuestas llegan al instante.
   - **Vista previa en el editor:** `bPreviewEmbrace` (4-Prueba) muestra la membrana en `PreviewEye` (0, 0, 115), para ajustar color y alfa mirando.
   - Verificado: en PIE, el abrazo arranca al llegar y termina 6,5 s después, con la ameba en el ojo y `Size` 3,6, la membrana visible a escala 3,2 y 0 `Accessed None`. En el editor, con las capturas `emb_prev_in/out`, desde adentro el salar queda velado de crema-ámbar con manchas lentas; desde afuera es una burbuja ondulada alrededor del hang.
   - ⚠ La membrana corta el piso: su centro está a 115 cm y su radio es de 160.
   - **Cortafuegos:** `Drift` la acerca sola, muy lento (500 s sin tocar).
   - El acercamiento usa una frenada física: v = max(`BrakeFloor`, `Brake`·√resto), según [[movimiento-frenada-fisica-no-exponencial]].

## Piezas
- **La voz = `AmoebaVoice` (`BP_Harp_SC_C_1`)**, una segunda instancia del hang:
  - en (362733, 100000, −2000), bajo el piso;
  - con `bHidden`;
  - con los mismos 7 valores que el hang, salvo `SoundIndex` 0 (arpa pulsada) y `RootNote` 62 (una octava arriba).
  - Con `InstrumentType` 1 sus 9 voces son las mismas notas que las del hang (`HangSteps`, Re Kurd).
  - Su sonido no es espacial: el `Synth` no tiene atenuación, así que la posición no importa.
  - 🔴 **No puede tickear:** su `CtrlTick` montaría otro par de mandos en los grips.
    - `PrimaryActorTick` no se puede escribir en la instancia por MCP: *"could not be set"*.
    - Su `BeginPlay` vuelve a encender el Tick, porque `bStartWithTickEnabled` está en true.
    - **Arreglo:** en `AcBootVoice`, `AddTickPrerequisiteActor(Voice, self)`, así la voz tickea después del director, y `SetActorTickEnabled(false)` en **cada** `AcTick`. Se apaga antes de su primer Tick (gotcha 635).
  - `Pluck` funciona sin Tick: dispara la voz, guarda `LastPluck`, `Energy`, `Spark` y la háptica.
- **La ameba = `Amoeba` (`BP_ProtoSoul_SC_C_0`):**
  - `Size` 1,2, `bStartAsleep` false y `bHoverEnabled` false en la instancia;
  - en el editor queda en `FarPoint`: (365100, 100000, 280);
  - el director solo la mueve (`SetActorLocation`) y le escribe `Size`/`EdgeIntensity`; su Tick los aplica.
  - ⚠ Su material es translúcido y de **una sola cara**: desde adentro no se ve. Por eso el final queda a 2,3 m y no "adentro".
- **Las ondas:** una reserva de `RingPool` (24) componentes de `SM_AttractRing_SC`:
  - una corona plana de 160 segmentos (UV.x = ángulo, UV.y = 0 adentro y 1 afuera), con límites ampliados ±40 m;
  - con `M_AttractRing_SC`, translúcido y sin luz.
  - Por Custom Primitive Data: `RA` 0 = (radio cm, ancho cm, alfa, suavidad) y `RC` 4 = (color, brillo).
  - El WPO pone cada vértice en radio R ± W/2, así el ancho queda en cm de mundo. Solo se dibujan los píxeles del anillo, sin un quad grande translúcido encima: eso cuida el fill del Quest.

## Registro de variables (Details)
- **0-Enlace:** `Harp` (el hang que se toca) · `Voice` (la voz de la ameba) · `Amoeba`.
- **1-Onda:**
  - `WaveSpeed` 1100 cm/s.
  - `RingWidth` 5 cm + `RingWidthGrow` 0,012 por cm de radio.
  - `RingAlpha` 0,85 (llamada) · `ReturnAlpha` 0,55 (respuesta).
  - `RingFade` 2500 cm (e-pliegue de la distancia) · `RingAfter` 1 s (fundido después de llegar).
  - `RingSoft` 1,5 (borde) · `RingGlow` 1,3.
  - `RingZ` 3 cm sobre el piso del actor.
  - `RingPool` 24 · `RingMesh` · `RingMat`.
- **2-Ameba:**
  - `FarPoint` (2400, 0, 280) · `NearPoint` (230, 0, 135), los dos locales.
  - `AmoebaSize` 1,2.
  - `StepPerCall` 0,025 · `StepVelGain` 0,5.
  - `Drift` 0,002 /s.
  - `Brake` 0,35 · `BrakeFloor` 0,01.
  - `GlowPeak` 4 · `GlowDecay` 1,2 s.
- **3-Voz:** `VoiceSpeedFar` 50 · `VoiceSpeedNear` 160 (cm/s que se le pasan a `Pluck`; × (0,6 + 0,4 · fuerza)) · `bVoiceRight` ✅.
- **4-Prueba:** `bDebugNotes`, una nota al azar (voz 0..8, fuerza 0,3..1) cada `DebugEvery` (1,5 s). Prenderla en la instancia antes del Play y apagarla después.
- **Z-Estado:**
  - `Rings`;
  - por anillo: `RAge`, `RRad`, `RHit` (radio al llegar), `RKind` (0 llamada, 1 respuesta), `RVoice`, `RVel`, `RFired`, `RAlive`;
  - `Seen` (último `LastPluck` por voz);
  - `Progress`/`Shown` (0..1), `Pulse`, `BaseEdge` (el `EdgeIntensity` de la ameba al arrancar), `NextRing`, `NextDebug`, `Calls`, `bStageDone`.

## Grafos
- **CS** → `AcBuild`: la reserva de anillos, ocultos.
- **BeginPlay** → `AcBoot`: los arreglos en cero, `AcBootVoice`, `AcBootHarp` (`Seen`) y `BaseEdge`.
- **Tick** → `AcTick(min(Dt, 0,05))`:
  - `AcBootVoice` (apaga la voz);
  - `AcDebug`;
  - `AcAmoeba` (Drift, frenada, posición, tamaño y brillo; `bStageDone`);
  - con cámara: `AcRingStep` de los anillos vivos y `AcSense`.
- `AcSense`: `LastPluck` > `Seen` → `AcCall(voz, Energy[voz])`.
- `AcCall` → `AcRing(0, …)` desde el pie del hang.
- `AcRing`: el próximo de la reserva (circular), con posición y CPD.
- `AcRingStep`: radio, alfa y llegada (→ `AcArrive`); fundido y apagado.
- `AcArrive`: si es una llamada, `AcAnswer`; si es una respuesta, `Voice.Pluck`.
- `AcAnswer`: `Pulse`, `Progress`, `Calls` y `AcRing(1, …)` desde el pie de la ameba.

**Fuente:** `scripts/attract/`.
- `call_src.dsl` + `gen_call_dsl.py` (→ `call_dsl.json`) + `build_call.py`.
- El anillo: `gen_ring_obj.py` y `gen_ring_material.py`, más `apply_attract_material.py`, que ahora es genérico por plan: cambiar `PLAN` arriba de todo.

## Session log
- **2026-11-04:** construido entero.
  - El `%` del DSL no existe (*"Utilities|Operators|Modulo does not exist"*): se usa `select` (gotcha 634).
  - La voz se apaga con un prerrequisito más el apagado en cada cuadro (gotcha 635).
  - Los chorros (`AttractStreams`) quedaron apagados con `MaxStreams` 0 en su instancia.

## TODO
- [ ] Visor con Beltrán.
- [x] El "te envuelve" del final (2026-11-05): el abrazo con la membrana `Shell`. ⬜ visor (¿demasiado opaca? ¿el color?).
- [ ] ¿La ameba contesta con OTRA nota (armonía) en lugar de la octava?
- [ ] ¿Las ondas con un poco de relieve sobre el salar? (la ola de `BP_ChladniFloor_SC`).
- [ ] Costo de 2 sintes en el Quest.
