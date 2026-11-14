# BP_Harp_SC — arpa que se toca con las manos, con sinte propio en MetaSounds

**Ruta:** `/Game/SoulCharger/Mechanics/Harp/Blueprints/BP_Harp_SC`
**Colocado en:** `/Game/SoulCharger/Mechanics/Harp/Maps/Test_Harp` como `BP_Harp_SC_C_0` (38, 0, 78), frente al PlayerStart (0, 0, 92)
**Y en `/Game/SoulCharger/Mechanics/Harp/Maps/Test_AttractingHang`** (2026-11-04, arranque de la reconstrucción de Attracting con el hang): copia de `Test_Sequencer` con su entorno (salar de Chladni `GAL_12_ChladniFloor`, Ganzfeld oculto, PlayerStart en (362700, 100000, 0), los 4 TargetPoints `sc3_*` para cuando vuelva Alma). Sin secuenciador, sin Alma, sin ensayo. El hang es `BP_Harp_SC_C_0` con etiqueta `Hang` en (362733, 100000, 76): la misma posición relativa al PlayerStart que en Test_Harp (+33, 0, +76). Tiene los 7 valores de instancia de Test_Harp: `InstrumentType` 1, `SoundIndex` 3, `NumStrings` 17, `Spacing` 7,253561, `StringLen` 283,697749, `LenTaper` 0, `StringRadius` 0,640025. Fuera de esos, la instancia es igual al CDO, igual que en Test_Harp. PIE: `fails=0`, encuentra los dos mandos de `BP_VRPawn_SC`, 0 `Accessed None`. El salar queda quieto: busca `BP_Sequencer_SC` y no lo encuentra.
**2026-11-04: segunda instancia, `AmoebaVoice` (`BP_Harp_SC_C_1`), en `Test_AttractingHang`.** Es la voz de la ameba de `BP_AttractCall_SC`:
- en (362733, 100000, −2000), con `bHidden`;
- los mismos 7 valores que el hang, salvo `SoundIndex` 0 y `RootNote` 62;
- **no tickea**: la apaga el director con un prerrequisito más el apagado en cada cuadro (gotcha 635), porque su `CtrlTick` montaría otro par de mandos;
- el director le llama `Pluck(I, Speed, Right)` desde afuera, y funciona sin Tick.

**2026-11-04: haces apagados.** Beltrán: *"No quiero ver salir los espermatozoides del hang. No elimines ese código, pero que esté apagado"*. `bShowOrbs` → **false** en el CDO y en la instancia de `Test_AttractingHang`. La perilla corta en `OrbCheck` (`if bShowOrbs and LP > PadSeen[I]` → `OrbLaunch`), así que no sale ningún haz. El código de las esferas y los haces queda entero: para volver a verlos, `bShowOrbs` ✅. **Apagado no cuesta nada.** `OrbEnsure` solo lo llama `OrbLaunch` (reserva perezosa, al primer lanzamiento), y `OrbTick` recorre `OrbComps`, que queda vacío. Verificado en PIE: `OrbComps` [] y `OrbBeams` [], con `fails=0`. Beltrán: *"No las usaré"*. En `Test_Harp` no se tocó la instancia: no tenía la perilla sobrescrita, así que debería tomar el false del CDO al abrir el nivel. Verificarlo al abrirlo.
**Nació:** 2026-10-27, pedido de Beltrán tras probar el *wHarp* de Virtuoso: *"un instrumento tipo arpa que se toque con las manos; las cuerdas vibran cuando se tocan y emiten sonido, además un par de efectos"*. Con háptica, las dos manos, polifónica, y estética elegante de Soul Charger (*"no un arpa neón fea como la de Virtuoso"*).
**Investigación previa:** [`docs/investigacion/INVESTIGACION-SINTE-ARPA-ARPEGIADOR-2026-10-27.md`](../../../../docs/investigacion/INVESTIGACION-SINTE-ARPA-ARPEGIADOR-2026-10-27.md)
**Estado:** 🟢 PIE: el sinte se arma con `fails=0`; con la mano de prueba se detectan los toques en orden, sin saltarse cuerdas; el `.wav` grabado suena y está afinado (cuerdas 0 y 8-13 a ±2 cents; la 14 a +18, dentro del error de medición). En PIE normal encuentra los dos mandos del pawn. ⬜ **visor** (tacto, latencia, volumen, timbre) · ⬜ APK (CPU de MetaSounds en Quest sin medir) · ⬜ sin commit.

---

## Qué hace (cuatro responsabilidades)
1. **Cuerdas:** las arma el script de construcción (`BuildStrings`), así se ven en el editor. Son N `StaticMeshComponent` de `SM_HarpString_SC` (cilindro de 100 cm × 48 anillos, Z hacia arriba, radio 1 → escala XY = `StringRadius`). Abajo están alineadas; la parte superior baja hacia los agudos (`LenTaper`). Sin marco: silueta Turrell.
2. **Sinte:** en `BeginPlay`, `BuildSynth` arma **un solo MetaSound en memoria** con la *Builder API*. Tiene una voz por cuerda (cuerda pulsada Karplus-Strong), las suma, y pasa por ganancia → Stereo Delay → Plate Reverb → Limiter L/R. Lo hace sonar con `Audition` en el componente `Synth`. **No hay asset de MetaSound**: el grafo se describe como DATOS (categoría `9-Sinte`).
3. **Toque:** en cada `Tick`, para cada mano (`HandR`/`HandL` = los MotionController Grip del pawn, encontrados por `MotionSource`), la punta es la posición del grip + forward × `TipFwd`, en espacio local del arpa. Hay dos detectores sobre el **segmento recorrido entre dos cuadros**, así un barrido rápido no se salta cuerdas:
   - `DetectStrum`: la mano cerca del plano (|x| < `PlaneTol`) que cruza la Y de cada cuerda. Calcula el rango de índices cruzados (no recorre todas).
   - `DetectPoke`: la mano atraviesa el plano x=0 cerca de una cuerda (`HitHalfWidth`).
4. **Respuesta (`Pluck`):** tiene un enfriamiento por cuerda (`Cooldown`). Velocidad 0-1 = rapidez / `VelFull`. Manda `Vel_i` (0,5 + 0,5·v), `Cut_i` (2000 + 7000·v²) y dispara `Pluck_i` al MetaSound. La cuerda se ilumina con el color de la mano (`HandColor`) y vibra (`Energy`, que se apaga en `DecayStrings` con `VibDecay`). Háptica con la receta de la Obra: `PlayHapticEffect(GrabHapticEffect)` en el PlayerController, mano derecha o izquierda, escala según la velocidad.

**Polifonía:** cada cuerda tiene su propia voz y su propio retardo, así que suenan a la vez y las dos manos tocan en paralelo.

## Registro de variables
**0-Arpa:** `NumStrings` 15 · `Spacing` 3,4 cm · `StringLen` 56 cm · `LenTaper` 0,4 (la más aguda mide el 60 %) · `StringRadius` 0,11 cm · `bDebugStrum` (mano de prueba que barre sola: para PIE sin visor) · `bRecordWav` (agrega un Wave Writer a la mezcla seca → `Saved/AudioCaptures/Output_N.wav`).
**1-Sonido:** `RootNote` 50 (Re3) · `ScaleSteps` [0,2,4,7,9] (pentatónica mayor; cuerda i = raíz + escala[i mod n] + 12·(i div n)) · `Decay` 3,2 s (T60 de la cuerda → feedback por voz) · `PanWidth` 0,7 · `DelayTime` 0,42 · `DelayFeedback` 0,3 · `DelayWet` 0,2 · `ReverbWet` 0,4 · `ReverbDecay` 0,6 · `Volume` 0,8 (ganancia antes del delay) · `MasterGainDb` 9 (entrada de los limitadores, umbral −3 dB).
**2-Luz:** `BaseColor` (0,30; 0,285; 0,27) blanco tibio tenue · `RightColor` (1; 0,74; 0,52) durazno · `LeftColor` (0,74; 0,70; 1) lavanda · `Glow` 1,4 · `VibAmp` 0,3 cm · `VibDecay` 1,4 s · `WobbleHz` 9 · `StringMat` `M_HarpString_SC` · `StringMesh` `SM_HarpString_SC`.
**3-Toque:** `TipFwd` 7 cm · `PlaneTol` 3 cm · `HitHalfWidth` 1,3 cm · `VelFull` 140 cm/s · `Cooldown` 0,07 s · `HapticScale` 0,7 · `HapticEffect` `/Game/XRFramework/Haptics/GrabHapticEffect`.
**9-Sinte (la receta de UNA voz, como datos):**
- Nodos (`VNS`/`VName`/`VVar`): 0 Noise · 1 AD Envelope (ojo: namespace `AD Envelope`, no `UE`) · 2 Multiply (Audio) · 3 One-Pole Low Pass Filter · 4 Delay · 5 Multiply (Audio by Float) · 6 Stereo Panner (variante vacía).
- Enlaces (`LFrom`/`LOut`/`LTo`/`LIn`): from −1/−2/−3 = entradas de la voz `Pluck_i`/`Vel_i`/`Cut_i`; to −10/−11 = salida L/R de la voz.
- Valores (`DNode`/`DIn`/`DVal`): fichas −1001 = periodo (1/f, menos 1 muestra en `VoiceDef`), −1002 = feedback = e^(−6,9078/(f·Decay)), −1003 = pan. Ráfaga AD: ataque 0,5 ms, caída **6 ms fija** (con 1 periodo, las agudas sonaban 10 veces más bajo).
- 👉 **Para cambiar el timbre se cambian estos arreglos en la instancia o el CDO, sin tocar grafos.**

**Z-Estado:** `Strings`, `MIDs` (sin uso: se usa `Set*ParameterValueOnMaterials`), `Energy`, `LastPluck`, `PluckN/VelN/CutN` (nombres de parámetro precalculados), `Builder`, `Handles`, `VoiceL/R`, `SumL/R`, `AudioOuts`, `HandR/L`, `PrevR/L`, `bHasR/L`, `bReady`, `BuildFails`.

## Grafos (orden)
- **ConstructionScript** → `BuildStrings`.
- **BeginPlay** → `EnsureStrings` (si el arreglo no coincide con `NumStrings`, reconstruye) → `InitLook` (SideDir = vector derecho del actor, colores, brillo; reinicia `Energy`/`LastPluck`) → `MakeNames` → `BuildSynth`.
- **BuildSynth** → `CreateSourceBuilder("HarpSynth", Stereo, no OneShot)` → `BuildBody`: por cuerda, frecuencia/periodo/feedback/pan → `BuildVoice` (3 entradas de grafo + nodos + enlaces + valores, interpretando los datos) → `MixVoice` (cadena de `Add (Audio)`) → **`BuildFX_0`** → `DebugRecord` (si `bRecordWav`) → `Audition` → log `HARP synth ready, fails=N`.
- **Tick** → `HarpTick` → `FindHands` (si falta `HandR`) → `DecayStrings` → `TickR` (o la mano de prueba) → `TickL` → `HandStep` → `DetectStrum` + `DetectPoke` → `Pluck`.
- **Biblioteca del constructor:** `MSNode`, `MSOut`, `MSConnect`, `MSConnectH`, `MSSet`, `MSInput`, `Fail` (cuenta en `BuildFails` y loguea `HARP build fail: <pin>`).
- ⚠ La función de efectos se llama **`BuildFX_0`** (nodo `CallFunction|BuildFX0`): la `BuildFX` original se borró y el nombre quedó reservado (gotcha 603).

## Fuente del DSL
`.claude/skills/unreal-vr/scripts/harp/harp_src.dsl` (copia de trabajo en `VR_Test/Saved/ClaudeScripts/harp/`) (con `(G Var)`/`(S Var v)`) → `gen_harp_dsl.py` lo expande con la categoría de cada variable → `harp_dsl.json`. Se escribió grafo por grafo en funciones vacías. **No re-escribir un grafo existente con `write_graph_dsl`** (lo duplica).

## Cómo probar
- **Sin visor:** `bDebugStrum` + `bRecordWav` en la instancia → PIE 14 s → log `HARP pluck i` + `Saved/AudioCaptures/Output_N.wav` (float32, formato 3). El análisis está en el log de la sesión 2026-10-27: altura por DFT alrededor de la nota esperada.
- **En visor:** abrir `Test_Harp` → VR Preview (Link). El arpa está a 38 cm al frente, con la base a 78 cm del piso.

## Session log
- **2026-10-27:** construido entero por MCP.
  - Material `M_HarpString_SC`: Unlit; WPO de modo 1 + 0,35·modo 2 × `Energy` × `Amp` sobre `SideDir`; emisivo = Base + Hand·Energy·Glow.
  - Malla generada por OBJ.
  - Correcciones medidas con el `.wav`: (1) el lazo del nodo Delay es D+1 muestras → `VoiceDef` resta 1/48000 al periodo (`MapRangeUnclamped`), y la cuerda 0 pasó de −5 a +0,1 cents; (2) ráfaga fija de 6 ms, porque las agudas sonaban 10 veces más bajo; (3) velocidad mínima más alta + `Volume` 0,8 + limitadores con +9 dB.

- **2026-10-27 (2.ª vuelta, tras la primera prueba de Beltrán en visor: *"funciona, pero es difícil tocarlo con las manos"*):**
  - **Mandos de la Obra en vez de manos:** `BP_QuestCtrl_SC` (SC_Base) montado en cada Grip con la receta exacta de `BP_SeqRig_SC.MountQCtrl`: `SpawnActorfromClass` → `SetLeft` + `ApplyHand` → `AttachActorToComponent` KeepRelative → `SetActorRelativeTransform` con `QCtrlLocR` (5,686; 0,54; −1,678) / `QCtrlRotR` (P −13,566, Y −83,539, R 64,231), `QCtrlLocL` (5,877; −1,567; −2,05) / `QCtrlRotL` (0, −95, 65) y escala `QCtrlScale` 1,0875. Las manos se esconden con `SetHiddenInGame` (`ConcealHands`; perilla `bHideHands`).
  - **Lo que toca la cuerda es la cabeza del mando:** `HeadLocal` (0,68; 1,5; −1,5) en el marco del mando derecho; el izquierdo espeja X. Sale del bounds de `SM_QuestCtrl_Body_R_SC`: X −2,68…4,04, Y −7,24…3,26 con el mango hacia −Y, Z −7,34…0,81. Si no hay mando, cae a la punta vieja del grip (`TickR`/`TickL`).
  - **Tolerancias más amplias:** `PlaneTol` 3 → 4,5 cm · `HitHalfWidth` 1,3 → 1,7 (la mitad del espaciado).
  - **Ondulación más notoria:** `VibAmp` 0,3 → 1,4 cm · `VibDecay` 1,4 → 1,8 s · `WobbleHz` 9 → 8.
  - **Grafos nuevos:** `HarpTick2` (el Tick ahora llama a este: `FindHands` → `CtrlTick` → `DecayStrings` → `HandTickR` → `HandTickL`), `CtrlTick` (`CtrlEnsure` R/L + `ConcealHands` una vez), `MountQCtrl`, `CtrlEnsure`. `HarpTick` queda sin uso.
  - **Verificado en PIE:** `QCtrlR` hijo de `MotionControllerRightGrip` con `bLeft` false, `QCtrlL` hijo de `LeftGrip` con `bLeft` true, los dos a escala 1,0875; `HandLeft`/`HandRight` con `bHiddenInGame` true; `fails=0`; sin errores.
  - El gatillo del mando no se anima: el arpa no usa input. Si hace falta, copiar la parte `IA_Hand_IndexCurl` de `QCtrlHand`, que necesita input habilitado.

- **2026-10-28: VARIOS SONIDOS POR ÍNDICE** (pedido de Beltrán: *"los vas agregando como index en el BP, con una variable y perilla"*).
  - **Perilla `SoundIndex`** (1-Sonido, int): **0 = arpa** (Karplus-Strong) · **1 = pluck de sinte tipo Juno**. Se arma en `BeginPlay`: para cambiar de sonido, cambiar la perilla y volver a darle Play.
  - **Cómo se guardan las recetas:** todas en los mismos arreglos de `9-Sinte`, con una columna que dice a qué sonido pertenece cada fila: `VSnd` (nodos), `LSnd` (enlaces) y `DSnd` (valores). Los índices de nodo son **locales a cada receta** (0…n−1). `BuildVoice2` arma solo las filas cuyo sonido es `SoundIndex`.
  - **Fichas de valores** (`VoiceDef2`): −1001 periodo (−1 muestra) · −1002 feedback · −1003 pan · **−1004 frecuencia** · **−1005 frecuencia/2 (sub-octava)** · **−1006 frecuencia × 1,004 (desafinación +7 cents)**.
  - **Efectos por sonido:** `SndChorus` [0; 0,5] (un valor por sonido). `BuildFX2` agrega un chorus de dos `Flanger` (L 0,5 Hz / R 0,62 Hz, profundidad 0,5, retardo central 12 ms, mezcla = `SndChorus[SoundIndex]`) entre la ganancia y el Stereo Delay.
  - **Para agregar un sonido N:** agregar sus filas al final de los arreglos con `VSnd`/`LSnd`/`DSnd` = N, numerar sus nodos desde 0, y sumar un valor a `SndChorus`. Los arreglos con nombres vacíos se cargan en dos pasos (vaciar y cargar, gotcha 453).
  - **Receta del Juno (sonido 1, 16 nodos):** Saw(f) + Square(f×1,004, PW 0,38) → Add · Square(f/2) × 0,45 → Add → × 0,35 (**pre-ganancia**: el ladder satura con tanh) → Ladder (res 2,4, corte = 260 + env × `Cut_i`; env AD Float 2 ms / 0,30 s / curva 0,25) → × env AD Audio (3 ms / 1,2 s / curva 0,35) → × `Vel_i` → × 0,26 → Stereo Panner.
  - **Verificado:** `fails=0`. Con una cuerda sola y la mano de prueba: ataque inmediato, 0,027 → 0,012 a los 200 ms → 0,004 a los 800 ms, el brillo baja mientras cierra el filtro, afinado. El nivel se emparejó con el arpa midiendo los `.wav`.
  - **Grafos nuevos:** `BuildVoice2`, `VoiceDef2`, `BuildFX2`. `BuildBody` ahora llama a esos (los viejos `BuildVoice`/`VoiceDef`/`BuildFX_0` quedan sin uso).
  - ⚠ La primera receta del Juno usaba *Decay Curve* 2,5/3 y sonaba "sostenida". En MetaSounds, >1 es caída LOGARÍTMICA (gotcha 606).

- **2026-10-28 (3.ª vuelta, tras probar el Juno en visor: *"va súper"*):**
  - **Ondulación más corta, chica y rápida:** `VibAmp` 1,4 → 0,5 cm · `VibDecay` 1,8 → 0,6 s · `WobbleHz` 8 → 18. Cargado en el CDO **y en la instancia de `Test_Harp`**, porque el CDO no se propaga (gotcha 608).
  - **Gatillo del mando izquierdo corrido:** `BP_QuestCtrl_SC.ApplyHand` solo cambia las mallas; la bisagra la pone `ApplyTrigger`, que se había llamado en el CS cuando el mando todavía era derecho. Arreglo en `MountQCtrl`: `ApplyTrigger` justo después de `ApplyHand`. Verificado en PIE: L en (−1,565; 2,432; −0,145), R en (1,565; …).
  - **Destello en el toque:** `Spark(I, Right)` se llama desde `Pluck`. La posición es la cuerda i a la altura de la cabeza del mando (`SparkTipZ`, recortada al largo de la cuerda). Usa una reserva de `SparkPool` esferas (`SparkSlot2`, `/Engine/BasicShapes/Sphere` + `M_HarpSpark_SC`, aditivo sin luz, núcleo `dot(N,V)³` × `Color` × `Glow` 6 × `Fade`). `SparkTick` (desde `HarpTick2`): escala `SparkSize`·(0,6 + `SparkGrow`·t), Fade = (1−t)², se apaga a `SparkLife`. Perillas en 2-Luz: `bShowSparks` ✅ · `SparkSize` 2,5 cm · `SparkGrow` 1,6 · `SparkLife` 0,4 s · `SparkPool` 10.
  - 🔴 La primera versión (`SparkSlot`) devolvía `n` = largo, y el `bind` se volvió a evaluar DESPUÉS del `Add` (un índice de más → *Accessed None*). Reemplazada por `SparkSlot2`, que devuelve `LastIndex`. `SparkSlot` queda sin uso.
  - Verificado en PIE con la mano de prueba: 10 destellos rotando, edades y visibilidad correctas, 0 errores.

- **2026-10-28 (4.ª vuelta): PAD con nota sostenida, sonido 2** (Beltrán: *"un pad cálido muy rico, attack lento, que sostenga si mantengo la mano, release suave al sacarla; full ambient"*).
  - **Modo sostenido por sonido:** `SndHold` [0, 0, 1]. En `HandStep` las llamadas son ahora `DetectAll` y `DetectPoke2`: con `SndHold[SoundIndex]` = 1 corre `HoldStep` en vez de los detectores de cruce.
  - **Cómo funciona `HoldStep`:** `HoldIndex(P)` da la cuerda bajo la punta: |x| < `PlaneTol`, |y − y_i| < `HoldWidth` (1,6 cm) y z dentro de la cuerda; si no hay, −1. Si cambia respecto de `HeldR1`/`HeldL1` (índice+1, 0 = ninguna, así no hace falta inicializar), `HoldChange` → `NoteOffIf` (dispara `Rel_i`, salvo que la otra mano tenga la misma cuerda) + `NoteOnIf` (→ `Pluck`: ataque, destello y háptica). Mientras sigue en la misma cuerda, `HoldSustain` la mantiene encendida (`Energy` ≥ `HoldGlow` 0,45).
  - **Cada voz tiene 4 entradas:** `BuildVoice3` suma `Rel_i` (trigger); en los enlaces es la ficha −4 (`VoiceLink2`). `VoiceDef3` suma las fichas −1007 = f × 0,9965 y −1008 = f × 1,0035.
  - **Receta del pad (14 nodos):** Saw(f−6c) + Saw(f+6c) + Triangle(f/2) × 0,6 → × 0,3 → Ladder (res 1,3; corte = LFO 0,13 Hz entre 600 y 1500 Hz, desfase = pan, así cada cuerda respira distinto) → × ADSR (ataque 1,4 s curva 1,6 · decay 1,5 s · sustain 0,75 · release 3 s curva 0,7; Trigger Attack = `Pluck_i`, Trigger Release = `Rel_i`) → × `Vel_i` → × 0,25 → Stereo Panner. `SndChorus[2]` = 0,65.
  - **Verificado en PIE** (una cuerda, mano de prueba): pluck → release cada ~0,63 s; `.wav`: sube lento (0 → 0,007 RMS en 0,63 s) y el release suave sigue sonando más de 1,8 s después; `fails=0`, sin errores.
  - Caso borde: en el primer cuadro el cooldown de `Pluck` puede saltear el ataque (`LastPluck` = 0). Sin efecto audible.
  - ⚠ Costo: un pad tiene 3 osciladores + LFO + ladder por voz, siempre corriendo (17 voces). Medir en el Quest.

- **2026-10-28 (5.ª vuelta): pad expresivo** (Beltrán: *"que la pelotita se mantenga visible mientras toca; si sube la mano, más brillo o cutoff, si la baja, más opaco, como un sinte real; el umbral, relativo a donde tocó"*).
  - `DetectAll` → **`HoldStep2`** → `HoldChange2` (NoteOff + NoteOn + **`HoldBegin`**: guarda la altura del toque `HoldZ0R/L`, el destello del ataque `HoldSparkR/L` = `LastSpark` y pone `Cut_i` = `PadCutBase`) o **`HoldSustain3`** (brillo de la cuerda + `Cut_i` = clamp(`PadCutBase` × 2^(Δz · `PadOctPerCm`), `PadCutMin`, `PadCutMax`) + **`KeepSpark`**: mueve el destello a la cuerda a la altura de la mano y fija su edad en `HoldSparkAge` 0,1, guardado por `IsValidIndex`).
  - `Spark` ahora anota `LastSpark` (cirugía: `SetLastSpark` después del último `SetArrayElem`).
  - **Receta del pad:** el LFO pasó a ser un factor (0,8–1,25) y un nodo nuevo, el 14 (`Multiply Float`), hace LFO × `Cut_i` → corte del ladder. El brillo lo controla la mano; el LFO respira alrededor.
  - **Perillas** (1-Sonido): `PadCutBase` 1100 Hz · `PadOctPerCm` 0,125 (8 cm por octava) · `PadCutMin` 250 · `PadCutMax` 8000. 2-Luz: `HoldSparkAge` 0,1.
  - **Verificado en PIE:** mientras se sostiene, la edad del destello queda en 0,1 (encendido); al soltar envejece hasta 0,4 y se apaga; 0 errores. ⬜ El cambio de brillo por altura no se pudo probar en PIE (la mano de prueba solo se mueve de lado): falta el visor.
  - Arreglado: `HoldSustain2` movía un destello inexistente en el primer toque de la sesión (el cooldown de `Pluck` a t≈0 salteaba el ataque). `HoldSustain2` y `HoldStep` quedan sin uso.

- **2026-10-28 (6.ª vuelta): LATCH con el gatillo en el pad** (Beltrán: *"si tengo una cuerda tocada y aprieto el trigger, se queda sonando mientras mantenga el trigger, y puedo mover la mano y tocar otras cuerdas; así podría tocar un acorde de 4 notas"*).
  - **Cómo se toca:** el gatillo de una mano toma la cuerda que esa mano sostiene. También si el gatillo se aprieta antes y después se toca: la primera cuerda que toque queda tomada. La mano queda libre para tocar otras en modo sostenido normal. Al soltar el gatillo, la nota hace su release, salvo que una mano la esté tocando (entonces sigue como un toque normal) o que la otra mano también la tenga tomada. Dos manos = 2 tomadas + 2 tocadas = acorde de 4.
  - **Input:** copia de `BP_SeqRig_SC.EnsureInput` (`EnableInput` + `AddMappingContext(IMC_Weapon_R/L, 1000, …ForceImmediately)` + `HasMappingContext` → `bInputReady`), reintentada desde `LatchTick` hasta que quede lista. Eventos `IA_Shoot_Right/Left` (cirugía en el EventGraph): `Started` → `TrigDown(Right)`, `Completed` y `Canceled` → `TrigUp(Right)`, que solo escriben `bTrigR/L`.
  - **Lógica por cuadro:** `HarpTick2` termina en **`LatchTick`** → `LatchHand(R)`, `LatchHand(L)`, `EnsureInput` si falta. `LatchHand`: sin latch, gatillo + `HeldX1` > 0 → **`LatchSet`** (anota `LatchR1/L1`, `LatchShow`, háptico 0,6 × `HapticScale`). Con latch → **`LatchHold`**: gatillo apretado = la cuerda queda encendida (`Energy` ≥ `HoldGlow`); suelto = **`LatchFree`** → `LatchFade` + `LatchRel` + `LatchClear`.
  - **No soltar lo tomado:** `HoldChange2` ahora llama a **`NoteOffIf2`** (cirugía, reemplaza a `NoteOffIf`): no dispara `Rel_i` si la cuerda está en `LatchR1` o `LatchL1`. El corte queda donde estaba cuando la mano salió.
  - **Destello fijo:** dos esferas propias (`LatchComps`, `LatchEnsure`), fuera de la reserva para que un toque nuevo no se las lleve. `LatchShow` la pone donde estaba el destello sostenido de esa mano, con la escala y el `Fade` de `HoldSparkAge`. Al soltar, `LatchFade` pasa el destello a la reserva (`SparkSlot2`, edad `HoldSparkAge`) y `SparkTick` lo apaga como a cualquier otro.
  - **Perilla:** `bTriggerLatch` ✅ (3-Toque). `IMCRight/IMCLeft` = `IMC_Weapon_*`.
  - **Verificado en PIE** (una cuerda, mano de prueba, `bTrigR` escrito en el actor de PIE, gotcha 609): `HARP input ready` en el primer cuadro; con el gatillo, `HARP latch 0`, 20 s sin ningún `release` (8 retoques), `Energy` 0,45 con la mano lejos y destello fijo visible (escala 0,025). Al soltar con la mano lejos: `HARP latch release 0`, destello oculto y pasado a la reserva, y vuelve el ciclo normal. `.wav`: los toques sueltos llegan a ~0,008 RMS; tomada, la nota completa el ataque y sostiene 0,022–0,037 durante los 20 s; al soltar, release suave. 0 errores de script.
  - ⚠ Retocar una cuerda tomada vuelve a disparar el ataque (como dos manos en la misma cuerda). Con el ADSR de MetaSounds sube desde el nivel actual, sin corte.
  - Grafos nuevos: `EnsureInput`, `TrigDown`, `TrigUp`, `NoteOffIf2`, `LatchEnsure`, `LatchShow`, `LatchFade`, `LatchRel`, `LatchClear`, `LatchFree`, `LatchSet`, `LatchHold`, `LatchHand`, `LatchTick`. `NoteOffIf` queda sin uso.

- **2026-10-28 (7.ª vuelta): SNAP en el pad + LUZ de la cuerda tocada** (Beltrán: *"que en el pad haya un poco de snap cuando estamos tocando la cuerda o cerca, porque no es un toque one shot sino un continuo"* · *"las cuerdas que se tocan, en cualquiera de los instrumentos, deben ponerse de color y notarse bien"*).
  - **Snap:** `DetectAll` llama ahora a **`HoldStep3`** → **`HoldIndex2(P, Held)`**. Captura la cuerda más cercana con `SnapCatch` (1 cm) de más que `HoldWidth`/`PlaneTol` y también pasadas las puntas. La sostenida se mantiene con `SnapHold` (2,5 cm) más de profundidad y de puntas, y hacia el costado `SnapSide` (0,6 cm) más que la captura, sin pasar la mitad del espaciado + `SnapSide`. Esa histéresis evita que la nota titile entre dos cuerdas. Con el arpa de `Test_Harp` (espaciado 7,25 cm), la captura pasa de 1,6 a 2,6 cm a cada lado y suelta a 3,2. El destello ya quedaba sobre la cuerda (`KeepSpark` recorta la altura), así que se ve pegado a ella aunque el mando esté corrido. `HoldStep2` queda sin uso.
  - **Por qué no se notaba el color:** el emisivo era `Base + Hand·Energy·Glow` y `Energy` es la vibración, que en la 3.ª vuelta pasó a apagarse en 0,6 s. Además el color de la mano sumado sobre el blanco se lavaba hacia el blanco.
  - **Luz propia por cuerda:** arreglo `Light` (+ `LightSeen`). **`LightTick`** va al final de `HarpTick2`: un toque nuevo (`LastPluck` > `LightSeen`) = 1; si no, baja linealmente en `LightDecay` (2 s); sostenida o con latch, al menos `HoldLight` (1). No hizo falta tocar `Pluck`. `LightOne` calcula y le pasa el valor a `LightSet` como parámetro (así el `bind` no se re-evalúa después de escribir). `LightEnsure` dimensiona los arreglos y carga las perillas en cada cuerda (`LightLook`) una vez.
  - **Material `M_HarpString_SC`:** parámetros `Light`, `LitGlow` 1, `LitSat` 1,6, `LitThick` 0,1 cm, `NoteColor`, `NoteMix`. Emisivo = `lerp(Base, pow(color, LitSat)·LitGlow, l) + color·Energy·Glow·0,3`, con `l` = ease-out de `Light` y color = `lerp(HandColor, NoteColor, NoteMix)`. WPO: además de la vibración, la cuerda encendida engorda `LitThick` por la normal (radio 0,11 → 0,21 cm).

- **2026-10-28 (8.ª vuelta): la ESFERA, más grande, vibrando según la nota y con su color** (Beltrán: *"la esfera que aparece, hagámosla un poco más grande, y que vibre según la frecuencia de cada nota y con su color respectivo"*).
  - **Color por nota:** `NoteMidi(I)` (igual que `BuildBody`: raíz + escala[i mod k] + 12·(i div k)) → **`NoteColor(I)`** = HSV con tono `NoteHueStart` 35° + `NoteHueRange` −150° × (nota mod 12)/12 y saturación `NoteSat` 0,55. Las octavas comparten color. Con Re pentatónica: coral, rosa, rosa-magenta, lila, lavanda. `NoteColorMix` 1 = color de la nota; 0 = color de la mano, como antes. Vale para la esfera y para la cuerda encendida.
  - **Vibración:** material `M_HarpSpark_SC` con WPO nuevo (`SparkVib`): una gota que oscila. Modo P2 sobre z a `VibHz` + modo P3 sobre x a 1,5×, amplitud `VibAmp` × radio del objeto × `saturate(Fade·1,8)`; usa `View.GameTime` (gotcha 382). Así la esfera sostenida vibra todo el rato y la de un toque se calma mientras se apaga. **`NoteVibHz(I)`** = `SparkVibHz` 4 Hz en la raíz × 2^(octavas · `SparkVibOct` 0,5), o sea que las agudas tiemblan más rápido (≈4 → 13 Hz en tres octavas y media; una nota de 150 Hz real no se puede ver a 72 cuadros).
  - **`SparkTone(C, I, Right)`** carga `Color`, `VibHz` y `VibAmp` en una esfera. Lo llaman `Spark` (cirugía: reemplaza el nodo que ponía el color de la mano), `LatchShow` y `LatchFade` (reescritas vaciando el cuerpo; las llamadas quedan).
  - **Tamaño:** `SparkSize` 2,5 → 3,5 (CDO e instancia).
  - **Verificado en PIE** (mano de prueba sobre las 17 cuerdas, `SoundIndex` 2): pluck/release 0→16 en orden y sin titileo. Estela de `Light` 1 → 0,08 a lo largo de las cuerdas ya tocadas. Cada esfera con su `Color` de nota y su `VibHz` (6,3 / 6,9 / 7,3 / 8 Hz en las agudas), `VibAmp` 0,22 y escala final 0,077. Cada cuerda con su `NoteColor`, `Light` y perillas. 0 errores de script, los dos materiales compilan. ⬜ El aspecto (vibración, grosor, colores) se juzga en el visor.

- **2026-10-28 (9.ª vuelta): GRIP para tomar más notas (acorde de 6), release más corto, esfera más arriba y más grande, escala para ambient** (Beltrán: *"el release está muy largo · las esferas un poco más arriba respecto al controller y más grandes · agreguemos el botón de grab para sostener nuevas notas, así tocamos un acorde de 6 · pon una escala más linda para ambient"*).
  - **El latch pasó a 4 ranuras** `K`: 0 gatillo R · 1 gatillo L · 2 grip R · 3 grip L. Arreglo `Latch1[K]` = cuerda + 1 (0 = libre; CDO [0,0,0,0], y `LatchEnsure`/`LatchAny` lo dimensionan a 4 por si llega vacío). `LatchTick` (reescrita) → `LatchEnsure` (4 esferas fijas) → **`SlotHand(K)`** × 4 → `EnsureInput`. `SlotHand`: con la ranura libre, botón apretado (`bTrigX`·`bTriggerLatch` o `bGripX`·`bGripLatch`) y una cuerda sostenida que **ninguna otra ranura tiene** (`LatchAny(I, K)`) → **`SlotSet`** (esfera fija `SlotShow`, `Latch1[K]`, háptico). Con latch → **`SlotHold`**: apretado = la cuerda queda encendida; suelto = **`SlotFree`** → `SlotFade` + `SlotRel` (no suelta si una mano la toca u otra ranura la tiene) + `Latch1[K]` = 0.
  - **`LatchAny(I, K)`**: true si alguna ranura distinta de K (K = −1: cualquiera) tiene la cuerda I. `NoteOffIf2` y `LightOne` (reescritas) la usan con −1. Las funciones viejas por mano (`LatchHand`, `LatchSet`, `LatchHold`, `LatchFree`, `LatchRel`, `LatchClear`, `LatchShow`, `LatchFade`) y las variables `LatchR1/LatchL1` quedan sin uso.
  - **Grip:** eventos `IA_Grab_{Right,Left}_Pressed` / `_Released` del XRFramework (los mapea `IMC_Default` sobre `OculusTouch_*_Grip_Axis`, contexto por defecto, el mismo que usa el pawn para agarrar), `Triggered` → `GripDown(Right)` / `GripUp(Right)` → `bGripR/L`. Perilla `bGripLatch` ✅ (3-Toque).
  - **Release del pad:** fila 37 de la receta (`ADSR Release Time`, sonido 2) 3 → **1,2 s** (CDO e instancia).
  - **Esfera:** `SparkLift` 4 cm (2-Luz) más arriba que la cabeza del mando: **`SparkTipZ2`** (= `SparkTipZ` + `SparkLift`, cirugía en `Spark`) y `KeepSpark` reescrita. `SparkSize` 3,5 → 4,5.
  - **Escala:** `ScaleSteps` [0,2,4,7,9] → **[0,2,4,7,9,11]**, el hexatónico mayor (pentatónica + 7.ª mayor): Re, Mi, Fa#, La, Si, Do#, un color de Re maj9/6. Con 17 cuerdas va de Re3 a Si5. Vale para los tres sonidos.
  - **Verificado en PIE** (17 cuerdas, `SoundIndex` 2, mano de prueba; `bTrigR`/`bGripR` escritos en el actor de PIE): `fails=0`, `HARP input ready`. Con el gatillo, `latch k=0 i=11`; con el grip, `latch k=2 i=0`; la mano tocando la 14 → 3 notas en la mano derecha, las tres con `Light` 1. Después del latch no hubo `release 11` ni `release 0`. Esferas fijas a z 117,48 (la mano a 113,48), escala 0,045, color y `VibHz` de su nota (coral 4 Hz, naranja 7,8 Hz). Al soltar el grip con la mano sobre la 0, la nota siguió como toque normal y se soltó al salir. Al soltar el gatillo: `latch release k=0 i=11`. 0 errores de script.

- **2026-10-28 (10.ª vuelta): CHORUS de verdad** (Beltrán: *"agrega un efecto chorus"*).
  - **Por qué no se oía el de antes:** `BuildFX2` usaba un `Flanger` por canal con `Modulation Depth` 0,5, pero esa profundidad está en ms (gotcha 614). Así el retardo iba de 11,5 a 12,5 ms a 0,5 Hz, unos 3 cents: casi nada.
  - **`BuildFX3`** (copia de `BuildFX2` con el chorus cambiado; `BuildBody` la llama por cirugía y `BuildFX2` queda sin uso): por lado, dos `Flanger` al 100 % húmedo → `Add` → × `SndChorus·0,5`, más la seca × (1 − 0,35·`SndChorus`) → `Add` → Stereo Delay. Voces: L1 (`ChorusRate`, `ChorusDelay`, `ChorusDepth`), L2 (rate × 1,55, retardo × 1,4, profundidad × 0,6), R1 (rate × 1,09, retardo + 1,3 ms), R2 (rate × 1,42, retardo × 1,25, profundidad × 0,6). Los ritmos distintos abren el estéreo. Con los valores por defecto modula unos 12 cents por voz, como un chorus clásico tipo Juno.
  - **Perillas** (1-Sonido): `ChorusRate` 0,45 Hz · `ChorusDelay` 9 ms (máx. 20) · `ChorusDepth` 2,6 ms (no puede pasar el retardo) · mezcla por sonido `SndChorus` [0,3 arpa · 0,6 Juno · 0,8 pad] (antes [0; 0,5; 0,65]).
  - **Verificado en PIE:** `fails=0` (los 18 nodos de efectos creados y conectados), 0 errores de script. ⚠ No medido en `.wav`: `DebugRecord` graba la mezcla seca (`SumL`), antes de los efectos. Para medir el chorus haría falta colgar el Wave Writer después de `BuildFX3`.

- **2026-10-28 (11.ª vuelta):** Beltrán, tras probarlo: *"está muy fuerte, bájalo un poco, y el attack un poco más rápido para sentir cuando cambia de nota"*.
  - **Chorus más suave:** `SndChorus` [0,3; 0,6; 0,8] → **[0,2; 0,4; 0,5]**, `ChorusDepth` 2,6 → **2,0 ms** (≈10 cents).
  - **Ataque del pad:** fila 34 `Attack Time` 1,4 → **0,45 s**, fila 38 `Attack Curve` 1,6 → **1,1**. CDO e instancia.
  - **Medido en `.wav`** (una cuerda, mano de prueba, toques de 1,25 s por el snap): cada toque llega a su nivel pleno en ~0,3-0,5 s (0,037 RMS a los 0,3 s del primero). Antes, un toque de 0,6 s llegaba apenas a 0,007.

- **2026-10-28 (12.ª vuelta): HALO que sube por la cuerda desde la esfera** (Beltrán: *"que desde la esfera salga un halo hacia arriba de la cuerda; si es un solo toque sale uno, si es sostenido se mantiene un halo que se note que va constantemente enviando energía hacia arriba"*).
  - **Lo dibuja el material** `M_HarpString_SC`, sin componentes nuevos. Custom `HarpHalo` (float) → intensidad `H` en cada punto de la cuerda. La WPO engorda la cuerda `H·HaloSwell` por la normal (una perla) y el emisivo suma `color·H·HaloGlow`. Pulsos con forma gaussiana de largo `HaloWidth` que suben a `HaloSpeed` desde `HaloZ`, uno cada `HaloGap` cm mientras se emite, y se apagan al llegar a `HaloReach` cm y con la `Light` de la cuerda.
  - **Edades relativas, no tiempos absolutos:** en el Quest las entradas de un Custom van en media precisión (gotcha 382), así que el BP manda `HaloA` = segundos desde que empezó a emitir (envuelta por período cuando pasa de `HaloReach/HaloSpeed + 1`) y `HaloB` = segundos desde que dejó de emitir (0 mientras sostiene). Un toque suelto: A = B → un solo pulso.
  - **BP:** `Spark` → **`HaloStart(I, Z)`** (cirugía; Z = salida de `SparkTipZ2`, la altura de la esfera): si la cuerda no estaba emitiendo, anota `HaloT0`/`HaloT1` = ahora. `LightOne` (reescrita) → **`LightSet2(I, L, Seen, Held)`** → **`HaloFlip`** (anota en `HaloT1` el cambio de sostenida a suelta; la primera versión se llamaba `HaloEdge` y chocaba con `BP_SoundOrb_SC.HaloEdge`) + **`HaloSend`** (A y B al material). `KeepSpark` (reescrita) mueve `HaloZ` con la esfera sostenida. `LightLook` (reescrita) carga `HaloLen` (largo de cada cuerda) y las perillas. `LightEnsure` (reescrita) dimensiona `HaloT0/T1/On`.
  - **Perillas** (2-Luz): `HaloGlow` 3 · `HaloSwell` 0,9 cm · `HaloWidth` 3 cm · `HaloGap` 14 cm (≈5 pulsos/s a 70 cm/s) · `HaloSpeed` 70 cm/s · `HaloReach` 80 cm. Con `StringRadius` 0,64 de Beltrán, el ensanche de 0,35 no se veía; con 0,9 queda una perla de ~3 cm.
  - **Verificado con capturas en Simulate** (gotcha 616): barrido por las 17 cuerdas → cada cuerda recién tocada lleva una perla que sube, más alta cuanto más viejo el toque. Una cuerda sostenida → tren continuo de perlas desde la esfera hacia arriba, que se achican y apagan. Parámetros: sostenida `HaloB` 0, `HaloZ` = altura de la esfera (117,5). Recién soltada: A 0,42 / B 0,20.
  - ⚠ Caso borde conocido: si la mano ya está sobre una cuerda en el cuadro 0, `Pluck` no dispara por el enfriamiento y no hay esfera ni `HaloZ` (el halo sale del pie de la cuerda). En el visor no pasa.

- **2026-10-28 (13.ª vuelta): EL HANG, otro formato del mismo instrumento** (Beltrán, con fotos de un handpan electrónico: *"cambiar el tipo de instrumento dentro del BP; mismos sintes, otro formato; cada botón como mesh independiente para hacerlo pulsar; en cada golpe un anillo que se expande y el botón se hunde en su eje; si el sinte es el pad, el anillo se mantiene vibrando mientras se sostenga"* · *"de la estética de los meshes de Soul Charger, como la paleta de Drawing"*).
  - **Perilla `InstrumentType`** (0-Arpa): 0 = arpa (como siempre) · 1 = hang. Mismos sonidos (`SoundIndex`), voces y latch del gatillo y del grip.
  - **Mallas** (Blender headless, ficha `blender-3d/assets/hang.md`): `SM_Hang_Body_SC` (hormigón, 9 bolsillos), `SM_Hang_Pad_SC`, `SM_Hang_Ding_SC` (origen sobre la cúpula, +Z por su eje). **Materiales** = familia de la paleta: `MI_Hang_Body/Pocket/PadTop_SC` (de `M_DrawPalette_SC`; `Flash`/`FlashColor` = el destello del golpe), `MI_Hang_Groove/PadSide_SC` (de `M_DrawPalette_Groove_SC`; la ranura con el color de la nota), `M_HangRing_SC` (aditivo: aro con `Rad`, `W`, `Int`, `Vib`, `Ph`, `Lobes`, `Col`).
  - **Construcción** (`BuildHang`, en el script de construcción después de `BuildStrings`, por cirugía): en modo 1 esconde las cuerdas (siguen existiendo: las voces se indexan igual) y crea el cuerpo en `HangLoc`/`HangRot` + 9 pads (`BuildPad`: colgados del cuerpo en `PadLoc`/`MakeRotFromZ(PadUp)`) + 9 anillos (plano de `/Engine/BasicShapes/Plane`, hijo del pad, a `PadTopH`+0,12, escala 4R/100, oculto). Se ve en el editor.
  - **Notas:** `PadNote` = voz de cada pad [0,7,5,3,1,2,4,6,8]: el ding es la más grave y las 8 suben en zigzag izquierda-derecha desde el pad más cercano al jugador (−X) hasta el más lejano, como un handpan.
  - **Detección** (`DetectAll` y `DetectPoke2` reescritas): en modo 1 → **`PadStep`**. Golpe (sonidos sin sostenido) = `PadHitOne`: la cabeza del mando cruza bajando el plano a `PadHitAbove` sobre la cara del pad (por su eje), dentro de `PadR + PadSlop` → `Pluck(voz, velocidad por el eje)`. Sostenido = **`PadHold`**: la misma máquina que las cuerdas (`HoldChange2` / `HoldSustain3`) con `PadIndex` (dentro de `PadHoldAbove` sobre la cara y `PadHoldBelow` debajo, con `PadKeep` de histéresis) y `PadPress` como "altura": hundir la mano en el pad abre el filtro.
  - **Dibujo** (`PadTick` al final de `HarpTick2`, por cirugía): el primer cuadro **`HangInit`** apaga las esferas de las cuerdas (`bShowSparks` = false en runtime), guarda centro/eje/radio de cada pad en el espacio del actor (`PadC`/`PadN`/`PadR`) y pinta cada pad, ranura y anillo con el color de su nota. Por cuadro, **`PadOne`** (con `LatchAny`, así el gatillo y el grip también lo sostienen): el pad se hunde por su eje (golpe `PadHitSink` que vuelve en `PadSinkTime`; sostenido `PadHoldSink`), destella (`Flash`) y la ranura sube (`GrooveGlow`). **`RingDraw`**: golpe = el aro sale del borde (0,5) y se abre a 0,95 apagándose en `RingLife`; sostenido = queda en `RingHoldR` **vibrando** (lóbulos que giran a `NoteVibHz` de la nota); al soltar se abre y se apaga. Un pad quieto se dibuja una vez y después se saltea (`PadQuiet`).
  - **Mano de prueba:** `TickR` (reescrita) → **`DebugHand`**: en modo 1 baja y sube por el eje de cada pad, uno cada 0,9 s; en el arpa barre las cuerdas como antes.
  - **Perillas** (4-Hang): `HangLoc` (12, 0, −12) · `HangRot` pitch 15 (la cara hacia el jugador) · `PadHitAbove` 0,8 · `PadSlop` 1 · `PadHoldAbove` 1,5 · `PadHoldBelow` 6 · `PadKeep` 1,5 · `PadTopH` 0,35 · `PadHitSink` 0,45 · `PadHoldSink` 0,3 · `PadSinkTime` 0,12 · `PadFlash` 0,6 · `PadIdleGlow` 0,35 · `PadHitGlow` 2,5 · `RingLife` 0,7 · `RingGlow` 2 · `RingHoldR` 0,56 · `RingHoldGlow` 1,3 · `RingVib` 0,03 · `RingW` 0,045 · `RingLobes` 4. Datos: `PadLoc`/`PadUp`/`PadRad` (de `hang_pads.json`), `PadNote`, mallas y materiales.
  - **Verificado en Simulate** (mano de prueba + capturas del viewport): con el pad sostenido (sonido 2) toca en orden 0→7→5→3 con release al levantar, el pad tomado queda con su anillo vibrando y el anterior abre el suyo. Con el sonido 0, `pluck` cada 0,9 s sin releases, el pad golpeado se hunde y vuelve, y el anillo se abre (radio 0,59, brillo 1,6 recién golpeado). 0 errores de script.
  - ⬜ Visor: la altura y la distancia (`HangLoc`/`HangRot`), el tacto (`PadHitAbove`, `PadSlop`) y el brillo del hormigón (en el viewport se ve muy claro).

- **2026-10-28 (14.ª vuelta):** Beltrán: *"baja el ataque del pad al mínimo, o agrega perilla y yo lo bajo"* · *"los botones del hang que tengan color"*.
  - **Perilla `PadAttack`** (1-Sonido, s; 0,005 = el mínimo): ficha nueva **−1009** en `VoiceDef3` (reescrita) y la fila 34 de la receta (`ADSR Attack Time` del sonido 2) vale −1009. Medido en `.wav`: la nota llega al 90 % en 10 ms (antes, 300-500 ms). `fails=0`.
  - **Pads con color:** `BuildPad` (reescrita) pinta cada pad con el color de su nota × **`PadColorV`** (4-Hang, 0,8), y `MI_Hang_PadTop_SC` pasó al sombreado de los botones de color de la paleta (`Ambient` 0,3 · `Diffuse` 0,6 · `Fill` 0,12 · `Grain` 0,14 · `Mottle` 0,2). Se ve en el editor (script de construcción).
  - Beltrán subió el actor a (33, 0, 168): el hang queda a ~1,56 m del piso del nivel. Es su posición; las capturas de prueba tienen que encuadrar desde ahí.

- **2026-10-28 (15.ª vuelta): SONIDO 3 = HANG por SÍNTESIS MODAL + escala Re Kurd** (Beltrán: *"¿se puede un hang que suene real con síntesis, no un Casio de 50 euros?"* → *"armalo con síntesis modal y escala Re Kurd; déjamelo puesto, con reverb y chorus; debe tener velocity"*).
  - **Receta (sonido 3, 39 nodos por voz):** 6 modos = Sine × AD Envelope (Audio; ataque 1,5 ms, caída con curva 0,45) × amplitud: **1** (amp 1, 4,2 s) · **1,0016** (0,45, 3,8 s: el batido lento de la fundamental) · **2** (0,55, 3,0 s) · **2,0035** (0,20, 2,6 s: batido de la octava) · **3** (0,32, 2,0 s: la quinta de la octava) · **4,37** (0,08, 0,5 s: el brillo metálico que se apaga rápido). + el golpe: Noise × AD (0,3 ms / 8 ms) × 0,25. Suma → One-Pole LPF con `Cut_i` (900 Hz suave → 9,9 kHz fuerte) → × `Vel_i` → **× `Vel_i` otra vez** (dinámica ~20 dB) → × 0,025 → Stereo Panner. `SndChorus[3]` 0,35 · `SndHold[3]` 0 · reverb = la plate general.
  - **Ficha genérica de frecuencia** en `VoiceDef3` (reescrita): v ≤ −10000 → f × ((−v − 10000)/1000). Ej.: 2,0035 → −12003,5.
  - **Escala propia del hang:** perilla **`HangSteps`** (4-Hang) [0, 7, 8, 10, 12, 14, 15, 17, 19] sobre `RootNote` 50 = **Re Kurd** (Re3 · La3 Si♭3 Do4 Re4 Mi4 Fa4 Sol4 La4). `NoteMidi` (reescrita) la usa en modo 1 (la del arpa sigue siendo `ScaleSteps`). **`BuildBody` (reescrita) arma las voces con `VoiceFor(I, N)`** (nota = `NoteMidi`) y en el hang arma **solo 9 voces** (una por pad), no 17.
  - **Medido en `.wav`:** ding fundamental 146,90 Hz (Re3 = 146,83), octava 293,75 (×1,9997), quinta de la octava 440,51 (×2,9988); a los 0,75 s la fundamental conserva 61 % y el modo de 4,37 el 0,7 %. Dinámica: misma nota suave (vel 0,14) contra fuerte (vel 0,95) = **18,9 y 19,3 dB** (cuenta: 19,4). `fails=0` en todas las corridas.
  - ⚠ En la prueba, el primer golpe del primer cuadro sale a velocidad máxima (la posición anterior de la mano es (0,0,0)). En el visor no pasa.
  - Test_Harp quedó en hang + sonido 3.

- **2026-10-28 (16.ª vuelta): ESFERAS CON HAZ en el hang** (Beltrán: *"con cada golpe, que salga una esfera con haz hacia el frente y se pierda en el infinito; las notas no salen todas del mismo punto"* → al probar: *"solo se veían puntos, sin esfera; se tiene que ver orgánico, con movimiento, no solo una línea recta"*).
  - **Disparo:** `PadOne` (reescrita) → **`OrbCheck(I, V, LP)`**: si `LastPluck` de la voz es más nuevo que `PadSeen[I]`, lanza con la fuerza del golpe (`Energy[V]`). `PadTickOn` (reescrita) → **`OrbTick`** → `OrbOne` (edad) → `OrbPlace`.
  - **`OrbLaunch(I, V, Vel)`:** sale de encima de SU pad (`PadC + PadN·(PadTopH + OrbLift)`), hacia el frente del instrumento, abriéndose según el lado del pad (`OrbSpread`) y subiendo (`OrbRise`). Semilla de fase al azar (`OrbSeed`). Color = **color de la nota AL CUADRADO** (satura el pastel de `NoteColor`; con el aditivo salía blanco).
  - **`OrbPath(Slot, Tm)` → Vector (función pura de la trayectoria):** avanza acelerando (`OrbSpeed·(0,7 + 0,6·vel)·t + ½·OrbAccel·t²`) y serpentea a los lados (`OrbWave` a `OrbWaveHz`) y arriba (0,6 de amplitud a 1,37× la frecuencia, fase 2,1×); la onda se abre en los primeros `OrbWaveIn` cm y crece hasta 2,5× lejos. Medido en Simulate: 9-57 cm de desvío lateral según la fase.
  - **`OrbPlace(Slot)`:** la esfera en `OrbPath(t)`, con pop de 0,12 s (ease-out) y apagado `1 − k²` en `OrbLife`. **El haz es un `SplineMeshComponent`** con `SM_HarpString_SC` (48 anillos, eje Z): Hermite entre `OrbPath(t − OrbTrail)` y `OrbPath(t)`, tangentes por diferencia de 0,04 s × el largo en tiempo, así **sigue la curva del vuelo**. Grosor `OrbBeamW` × radio de la esfera en la punta, 8 % en la cola.
  - **`OrbEnsure`:** reserva de `OrbPool` esferas (`SparkMesh` + `SparkMat`) y haces (spline, `bManualAttachment` true + `SetAbsolute` + `Movable`: espacio de mundo).
  - **Material `M_HarpSpark_SC`:** dos perillas nuevas en el Custom de emisivo, **`Core`** (exponente del núcleo `dot(N,V)^Core`, default 3 = el destello de siempre) y **`Rim`** (borde `(1−d)²·saturate(4d)`, default 0); `bUsedWithSplineMeshes` ✅. La esfera usa `Core` = `OrbCore` 0,8 y `Rim` = `OrbRim` 0,7 (se lee como esfera, no como punto); el haz, `Core` 1,5, sin borde y sin vibración.
  - **Perillas (4-Hang), valores de esta vuelta (la 18.ª cambió el vuelo y varios valores):** `bShowOrbs` ✅ · `OrbPool` 16 · `OrbSize` 9 cm · `OrbLift` 2,5 · `OrbSpeed` 18 · `OrbAccel` 45 · `OrbLife` 7 s · `OrbRise` 0,25 · `OrbSpread` 0,02 · `OrbTrail` 1,2 s · `OrbVib` 0,2 · `OrbGlow` 1,6 · `OrbWave` 22 cm · `OrbWaveHz` 0,5 · `OrbWaveIn` 30 cm · `OrbCore` 0,8 · `OrbRim` 0,7 · `OrbBeamW` 0,4. Estado: `OrbComps`, `OrbBeams` (spline), `OrbAge`, `OrbP0`, `OrbDir`, `OrbVel`, `OrbSeed`, `OrbNext`, `PadSeen`. (`OrbTrails`, la estela de esfera estirada, se borró.)
  - **Verificado en Simulate** (mano de prueba + capturas desde atrás y de costado): esferas de color, haces curvos que serpentean, se pierden a ~12 m. Gotchas 617-621.
  - En el camino el arpa desapareció del nivel (un script que falló deshizo y se llevó el actor, gotcha 617): se recuperó recargando `Test_Harp` desde disco con permiso de Beltrán.

- **2026-10-28 (17.ª vuelta): SONIDO 3 = HANG POR RESONADORES** (Beltrán: *"no sonaba ni por si acaso a hang pan, era un sinte más; el hang es metálico, con mucho rango dinámico"* → investigación en [`docs/investigacion/INVESTIGACION-SONIDO-HANG-2026-10-28.md`](../../../../docs/investigacion/INVESTIGACION-SONIDO-HANG-2026-10-28.md) → *"ármalo"*).
  - **Por qué sonaba a sinte:**
    - El batido iba a 0,2–1 Hz (suena a phaser). El medido en handpans reales es de 3–9 Hz.
    - El chorus estaba en 0,35.
    - Cada golpe reiniciaba la envolvente.
    - Había un solo modo inarmónico.
    - La caída era `1 − x^c` del AD Envelope y no exponencial: a los 0,75 s seguía al 61 %, cuando un handpan real ya cayó 15 dB.
  - **Receta nueva (48 nodos por voz; la arma `recipe_snd3_reson.py`):**
    - **El golpe es un clic seco:** `Count` del `Trigger Counter` → Int32→Time→Float → audio → paso alto de 4 kHz. Se le suma un 12 % de ruido de 5 ms, así ningún golpe es igual.
    - **Excitación:** el golpe pasa por el paso bajo `Cut_i` (la fuerza) y se multiplica por **`Vel³`** (bus principal, ~32 dB de rango) y **`Vel⁴`** (bus brillante, ~42 dB).
    - **Diez resonadores `Biquad Filter` pasa-banda** (caída exponencial real; el golpe nuevo suma energía; la cola no salta con la fuerza del golpe siguiente):
      | Modo | Frecuencia | T60 | A | Bus |
      |---|---|---|---|---|
      | Fundamental | ×1 | 3,2 s | 0,75 | Vel³ |
      | Gemela de la fundamental | ×1,0045 | 4,6 s | 0,20 | Vel⁴ |
      | Octava | ×1,997 | 2,7 s | 0,80 | Vel³ |
      | Gemela de la octava | ×2,016 | 3,4 s | 0,28 | Vel³ |
      | Quinta de la octava | ×2,985 | 1,9 s | 0,40 | Vel⁴ |
      | Gemela de la quinta | ×3,008 | 2,3 s | 0,16 | Vel⁴ |
      | Inarmónico | ×7,50 | 0,7 s | 0,50 | Vel⁴ |
      | Inarmónico | ×8,16 | 0,5 s | 0,40 | Vel⁴ |
      | Cuerpo (Helmholtz) | 73,4 Hz × peso del ding | 0,6 s | 0,45 | Vel³ |
      | Casco | 380 Hz | 0,04 s | 0,30 | Vel⁴ |
    - **Salida:** suma → × 0,025 → panner. `SndChorus[3]` = **0**.
  - **Código nuevo:**
    - **`VoiceFor` (reescrita) → `BuildVoice4`** (BuildVoice3 + la voz) **→ `VoiceDef4`.** Mismas fichas que `VoiceDef3`, más estas:
      | Ficha | Qué da |
      |---|---|
      | `-1100-k` | Literal entero k, por **`MSSetI`** (el enum `Type` del Biquad = 2) |
      | `-1010` | Peso del ding (1 en la voz 0; si no, `HangBodyOther`) |
      | `-300000-100·Hz` | Hz absolutos |
      | `-200000-1000·T60` | Ancho de banda en octavas = 3,174 / (T60 · Hz del modo anterior, `SynLastHz`) |
      | `-400000/-500000/-600000 - 10·g` | Ganancia g × `HangDecay`, × `HangMetal` o × `HangShimmer` |
    - **`MSNode` (reescrita):** el Biquad es versión mayor 2.
  - **Perillas (4-Hang):**
    - `HangDecay` 1: escala todas las caídas y compensa la ganancia.
    - `HangMetal` 1: nivel de los inarmónicos.
    - `HangShimmer` 1: nivel de las gemelas del batido.
    - `HangT60Tilt` 0,25: las agudas caen antes, × (220/f)^tilt.
    - `HangBodyOther` 0,25: cuánto cuerpo suenan las notas que no son el ding.
    - Todas se aplican al armar el sinte, así que hay que reiniciar el Play.
  - **Tres trampas que aparecieron en el camino** (gotchas 622-626):
    1. `Value` del `Trigger Counter` no se mueve en el primer disparo: el primer golpe de cada pad salía sin clic.
    2. **El parámetro float llega un bloque después del disparo:** cada golpe sonaba con la fuerza del ANTERIOR. Se arregló con un `Trigger Delay` de **25 ms** al frente, que cubre un bloque de 1024 a 44,1 kHz en Android.
    3. El AD Envelope de audio se suaviza ~2 ms y no sirve como clic.
  - **Medido en `.wav`** (Simulate, mano de prueba, `fails=0` en las 4 corridas finales):
    - Proporciones ×1,997 / ×2,985 / ×7,50 / ×8,16.
    - T60 de la fundamental **3,03 s** (handpans reales: 2,9 s). Con `HangDecay` 1,5 da 4,50 s.
    - Batido de la octava de 2,7 Hz (Re3) a 8,3 Hz (La4).
    - Del golpe suave al pleno: +16 dB de nivel, +18 dB de ataque, energía sobre 1 kHz ×4,5. La quinta pasa de −13 a −8 dB y el ×7,5 de −25 a −17 dB. Con `HangMetal` 2, el ×7,5 queda a −7 dB.
    - Los golpes de la primera vuelta ya igualan a los de la segunda.
    - Pico máximo 0,070, contra 0,046 del sonido anterior. Los golpes típicos quedan al mismo nivel.
    - El arpa (sonido 0) arma con `fails=0` por el camino nuevo.
  - Test_Harp quedó en hang + sonido 3, con la instancia como estaba (mano de prueba apagada, `VelFull` 140). Se guardaron el BP y el nivel; 10 actores.

- **2026-10-28 (18.ª vuelta): ESFERAS COMO COMETAS con impulso** (Beltrán: *"es muy intenso que salgan del botón; debieran salir más adelante, más suave, y que se alejen más como un cometa, sin tanta curva, como si tuvieran un impulso desde el hang"*).
  - **`OrbLaunch` (reescrita):** la esfera nace **`OrbAhead` cm por delante de su pad**, sobre la misma línea de vuelo (`P0 = pad + dirección·OrbAhead`). La cola nunca llega al botón.
  - **`OrbPath` (reescrita), distancia con impulso:** `sp·t + ½·OrbAccel·t² + kk·τ·(1 − e^(−t/τ))`.
    - `sp = OrbSpeed·(0,7 + 0,6·vel)` es el planeo.
    - `kk = OrbKick·(0,4 + 0,6·vel) − sp` es el exceso inicial.
    - `τ = OrbDrag`.
    - Arranca rápido según la fuerza del golpe, frena y sigue planeando con una fuga suave hacia lo lejos (antes aceleraba desde lento).
    - La onda lateral quedó igual en el código; se bajó por perilla.
  - **`OrbPlace` (reescrita):** en vez del pop de 0,12 s, la esfera **se enciende suave en `OrbSoft` s**. Es un smoothstep en el brillo de la esfera y del haz, y el tamaño va del 35 % al 100 %.
  - **Perillas nuevas (4-Hang):** `OrbKick` 320 cm/s · `OrbDrag` 0,45 s · `OrbAhead` 18 cm · `OrbSoft` 0,4 s.
  - **Perillas cambiadas (CDO e instancia, que estaban iguales):** `OrbSpeed` 18 → 85 (ahora es el planeo) · `OrbAccel` 45 → 12 · `OrbWave` 22 → 4 cm · `OrbWaveHz` 0,5 → 0,2.
  - **Medido en Simulate** (mano de prueba, golpes suaves de vel 0,15):
    - A 0,4 s va a 60 cm de su punto de nacimiento; a 6,7 s, a 7,7 m.
    - Desvío lateral máximo de 12 cm (antes, 9-57 cm).
    - Por la cuenta, aparece a ~30-45 cm del pad y llega a brillo pleno a ~70 cm (golpe suave) o a ~1,2 m (golpe pleno).
    - Capturas de atrás, de costado y de cerca: cometas casi rectos, sin brillo sobre el botón.
    - `fails=0` y sin errores de runtime.
  - Grafo leído después de escribir: sin `(/ 0` (gotcha 618).
  - Test_Harp quedó con la mano de prueba apagada. Se guardaron el BP y el nivel; 10 actores.

- **2026-10-28 (19.ª vuelta): HAZ DE LUZ desde DEBAJO del hang** (Beltrán: *"está lindo, pero parecen espermatozoides; debe ser más un haz que un gusanito · que salgan desde abajo del hang, no desde arriba, así dejamos libre la zona donde se toca"*).
  - **`OrbLaunch` (reescrita):**
    - Nacen **debajo del hang, bajo su pad**: `PadLoc[I]` (espacio del cuerpo) con z = −`OrbBelow`, llevado por `MakeTransform(HangLoc, HangRot)` y la transformada del actor. Más `OrbAhead` por la línea de vuelo.
    - Ya no usa `PadN`.
    - Al haz le pone `Along` = `OrbAlong`.
    - Desde el lugar del jugador, el haz aparece por delante del borde del hang, no sobre los pads.
  - **`OrbPlace` (reescrita):** el ancho del haz en la cola es `OrbTailW` del de la punta (antes 0,08 fijo: la cola fina era el "gusanito"), y el brillo del haz es `OrbBeamI` (antes 0,6 fijo).
  - **Material `M_HarpSpark_SC`:**
    - Parámetro nuevo **`Along`** (default 0 = sin efecto: las esferas del arpa no cambian) + `TextureCoordinate` como entrada `UV` del Custom de emisivo: `al = pow(t, |Along|)`.
    - `t` es `UV.y` si `Along` > 0, o `1 − UV.y` si < 0.
    - La V de `SM_HarpString_SC` va al revés del spline (gotcha 627), así que el haz del hang usa −1,5: brilla en la punta y se apaga hacia la cola.
  - **Perillas nuevas (4-Hang):** `OrbBelow` 4 cm · `OrbTailW` 0,5 · `OrbAlong` −1,5 · `OrbBeamI` 0,9.
  - **Perillas cambiadas (CDO e instancia, que estaban iguales):** `OrbAhead` 18 → 0 · `OrbSize` 9 → 6 (la esfera queda como la punta del haz) · `OrbBeamW` 0,4 → 0,9 · `OrbTrail` 1,2 → 1,8 s · `OrbWave` 4 → 0 (recto).
  - **Verificado en Simulate** (capturas de costado, desde abajo y desde el lugar del jugador):
    - Haces rectos de color, brillantes en la punta y que se apagan hacia la cola.
    - Salen de debajo del cuerpo y aparecen por delante del borde.
    - `fails=0` y sin errores de runtime.
  - Grafos leídos después de escribir, sin `(/ 0`.
  - Se guardaron BP, nivel y material; 10 actores; mano de prueba apagada.

## TODO
- ⬜ Visor: el hang nuevo (¿suena a handpan? cuánto metal, batido y caída: `HangMetal`, `HangShimmer`, `HangDecay`; el golpe más suave a −32 dB, ¿se oye?). Costo de 9 voces × 10 Biquad en el Quest.
- ⬜ Visor: la demora de 25 ms del golpe del hang. Si en el Quest el bloque es más chico se puede bajar; el valor está en la fila `Delay Time` del nodo 0 del sonido 3.
- ⬜ Visor: los haces del hang (nacen bajo el hang `OrbBelow`; ancho `OrbBeamW`/`OrbTailW`, degradado `OrbAlong`, brillo `OrbBeamI`, largo `OrbTrail`; impulso `OrbKick`/`OrbDrag`, planeo `OrbSpeed`; costo de 16 esferas + 16 splines con 4 `OrbPath` por esfera por cuadro).
- ⬜ Visor: el hang (posición, tacto, anillo, brillo).
- ⬜ Visor: el halo (velocidad, tamaño, brillo; costo del Custom en el vertex shader con 17 cuerdas).
- ⬜ Oído/visor: el chorus nuevo (cantidad por sonido en `SndChorus`).
- ⬜ Visor: el grip real (los `IA_Grab_*` de `IMC_Default`) en un actor; el gatillo real ya está probado en otros actores.
- ⬜ Visor: color por nota, vibración de la esfera, grosor de la cuerda encendida y el snap (la mano de prueba solo se mueve de lado, así que no prueba la retención en profundidad).
- ⬜ Visor: probar el latch con el gatillo real (el input es el del secuenciador, probado en visor, pero en el arpa todavía no).
- ⬜ Visor: tacto (`TipFwd`, `PlaneTol`, `VelFull`), latencia, volumen y timbre con Beltrán.
- ⬜ 🔴 Latencia del APK: el bloque de audio de `DefaultEngine.ini` está en la sección de Windows → Android usa 44,1 kHz / 1024 / 4 buffers (~90 ms). Coordinar antes de tocar `Config/`.
- ⬜ Medir la CPU de 15 voces + FX en el Quest.
- ⬜ Arpegiador (un solo reloj con el gusano) — diseño en la investigación §4.
- ⬜ Borrar `MIDs` (variable sin uso) cuando se haga la próxima limpieza.
