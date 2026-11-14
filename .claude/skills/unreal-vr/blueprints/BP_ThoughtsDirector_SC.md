# BP_ThoughtsDirector_SC — observar los pensamientos (Mechanics/Mind/, nivel `Test_Thoughts`)

- **refPath**: `/Game/SoulCharger/Mechanics/Mind/Blueprints/BP_ThoughtsDirector_SC.BP_ThoughtsDirector_SC` · parent Actor · creado 2026-10-30.
- **Pedido de Beltrán (2026-10-29/30).** Quiere que Soul Charger sea igual de linda y narrativa con y sin el EEG; Mind es la etapa que falta resolver.
  - Le gusta *"observar para activar cosas"*: *"esas frases y que hacia donde uno mire genere interacción lo encuentro muy lindo. Etéreo."*
  - La señal de quietud de la cabeza (la calma sin sensor) queda **para después**: *"me interesa primero la interactividad"*.
  - *"En un level nuevo, no pisemos las cosas ya armadas."*
- **La idea, atada a las voces de Alma del guion (§7.3):**
  - VO_22: *"Observe your thoughts like distant constellations… each one quietly forming, then fading."*
  - VO_23: *"Which thought carries a quiet wisdom today?"*
  - **No hay tarea ni lista:** los pensamientos se forman y se desvanecen solos. Mirarlo lo aclara; soltarlo lo deja ir. Al final eliges uno y queda como tu palabra.
  - No se puede fallar y la etapa termina por reloj.

## 🔁 2.ª vuelta (2026-10-30, Beltrán lo probó: *"está interesante"*)
- **Partículas** (*"no son tan lindas; algunas con opacidad; las del entorno funcionan porque hay variedad"*):
  - Copia propia `Mind/VFX/NS_ThoughtMotes_SC`; `NS_FocusMotes_SC` queda para Focus y Feed.
  - Su sprite usa el material nuevo **`Mind/Materials/M_ThoughtMote_SC`** (Unlit, Translucent, sprites de Niagara). Cada partícula toma de su `Particle Random`:
    - cuán difusa es: nítida y brillante (núcleo de 0,3 del sprite) o bokeh tenue (todo el sprite, alfa 0,18);
    - un tinte hacia blanco (hasta 35 %);
    - un titileo con frecuencia y fase propias.
  - Perillas del material: `Glow`, `Opacity`, `Twinkle` 0,35. Generador: `scripts/thoughts/thought_mote_material.py`. Gotcha 633.
  - `MoteSize` 0,6: sprite más grande; las nítidas se ven chicas y las difusas como manchas suaves.
- **Salida de la amebita** (*"que sea más linda la animación de salida"*). Nuevo `TdFly` en estados:
  - 0: espera su hora;
  - 1: **respira** `Burst` 0,7 s: crece `BurstGrow` 0,3 y enciende el borde `BurstGlow` 3, con smoothstep. Ya suelta polvo desde su superficie (`BurstRadius` 8) que la ameba atrae;
  - 2: se disuelve (`Disappear` en `ShrinkTime` 0,9 s) y el emisor viaja a la ameba;
  - 3 llega, 4 se apaga.
  - **Su palabra emerge** al soltarse (0,4 s), aunque no se la hubiera mirado. Se va con el barrido (`TitleOutTime` 1,4 s) y **sube** `TitleRise` 10 cm mientras se disuelve.
  - **El elegido se suelta primero;** los demás lo siguen escalonados (`GatherDelay` 0,6 + k × `GatherGap` 0,35 s). `TdConsume(I, At)` solo marca la hora.
- **La ameba se alimenta sin saltos** (*"se agrandó durísimo cada vez que le llegaron… es una carga que alimenta"*). Las dos causas:
  1. **El destello se reiniciaba:** cada llegada ponía la cuenta en cero (subía en 0,15 s) y, con seis llegadas seguidas, saltaba una y otra vez. Ahora cada llegada suma `FeedKick` 0,45 a una carga (`BloomE`, tope 1,5) que se descarga en `BloomTime` 2,2 s, y el destello (`BloomV`) la sigue suave (`BloomRise` 1,5). `BloomScale` 0,06 y `BloomLight` 0,45.
  2. **El crecimiento arrancaba de golpe:** un solo `FInterpTo` empieza a toda velocidad. Ahora son dos en cascada (`CellV` → `CellE`, `FeedSpeed` 0,9): arranca y frena suave.
  - Medido cuadro a cuadro: la escala va de 0,54 a 0,73 en unos 3 s sin saltos (máximo 0,13 por segundo) y se asienta en 0,70 en los 7 s siguientes.
- `ChosenDrop` 95: la palabra elegida queda bajo la ameba ya crecida.
- `FlyRate` 160.
- Se sacó `LastFeedAt`.
- ✅ Simulate completo, sin warnings ni `Accessed None`. Capturas `cap_v2_close`, `cap_v2_burst`, `cap_v2_gather`, `cap_v2_end`; serie `series_v2.json`.
- La fuente de la 1.ª vuelta está en `thoughts_src_v1_backup.dsl`.

## El nivel `Test_Thoughts` (`Mechanics/Mind/Maps/`)
- Es un duplicado de `Test_Feed`, sin su `BP_FeedDirector_SC`.
- Queda la ameba principal (`BP_LovingCell_SC_C_0`, en (265, 0, 100)).
- **8 protoamebas**, una por pensamiento: las 6 de Feed más 2 nuevas. Las palabras, cualidades en inglés:

  | Índice | Pensamiento | Color |
  |---|---|---|
  | 0 | CLARITY | celeste |
  | 1 | LOVE | rosa |
  | 2 | TRUST | ámbar |
  | 3 | GRATITUDE | verde |
  | 4 | CALM | azul profundo |
  | 5 | PRESENCE | violeta |
  | 6 | PATIENCE | turquesa |
  | 7 | JOY | dorado |

  - En las instancias: `AppearTime` 2,2 y `DisappearTime` 1,8 (se forman y se desvanecen despacio).
- **12 lugares** (`TargetPoint_4..15`): un campo de unos ±42° de ancho y −24° a +28° de alto, a 195-235 cm de los ojos.
  - Dejan libre el centro, donde está la ameba.
  - Son autorales: se mueven en el editor y el director toma su posición al arrancar.
- `BP_ThoughtsDirector_SC_C_0` en el origen. **36 actores.**
- Palabras: `T_Concept_<PALABRA>` + `MI_ConceptTitle_<PALABRA>`, del generador `scripts/feed/gen_concept_titles.py`. Es el título líquido de la Obra (Michroma).

## Cómo corre (≈ 70-90 s)
1. **0-2 s:** el fluido solo.
2. **A los 2 s** (`StartDelay`) la ameba se condensa (`RevealTime` 4) y Alma dice VO_20: *"This is Loving. There is nothing to do here… just let go."*
3. **Desde los 11 s** (`DustAt`), polvo fino sigue la mirada: donde miras, a 2,2 m, se junta. Sin VO_21 (no está grabada): lo cuenta la interacción.
4. **A los 17 s** (`T22`) llega VO_22 y, 2,5 s después, empiezan a formarse los pensamientos, uno cada 1,6 s, en lugares libres al azar.
   - Cada uno vive entre 10 y 16 s (`LifeMin`, `LifeMax`), se desvanece y vuelve a formarse en otro lugar 2,5-6 s después (`GapMin`, `GapMax`).
   - **Si lo miras:**
     - se aclara: crece (`ObsGrow`), enciende el borde (`ObsGlow`) y gira (`ObsSpin`);
     - junta polvo de su color y **emerge su palabra** con el barrido líquido, que vuelve atrás si apartas la vista;
     - **no envejece mientras lo miras.**
   - **Si lo sueltas:** le quedan 3,5 s (`ReleaseLife`).
   - Mirar pensamientos le da luz a la ameba (`AttnMax` 0,55 tras `AttnFull` 25 s de mirar en total).
5. **A los 52 s** (`T23`) llega VO_23: *"Which thought carries a quiet wisdom today?"*. 3 s después se abre la elección.
   - El pensamiento que sostengas `HoldTime` (3 s) se carga: crece, se enciende y late.
   - Al llenarse **es el tuyo**. Suena VO_23b (*"Let's gather all these thoughts…"*), vibran los mandos y **todos los pensamientos vivos se vuelven polvo y confluyen en la ameba**, el tuyo incluido.
   - Si nadie elige en 25 s (`ChoiceTimeout`), queda el más mirado.
6. **Cuando llega el tuyo:**
   - la ameba se llena (`CellE` 1), destella y toma un poco de su color (`ChosenTint` 0,35);
   - su palabra emerge bajo la ameba (`ChosenDrop` 75 cm, `ChosenScale` 0,26).
   - `FinaleHold` 10 s después, `bStageDone`.

## Variables (categorías)
**1-Pensamientos**
- `Thoughts` (ProtoSoul[]) · `TitleMats` (MI[], mismo orden) · `Slots` (Actor[]).
- `GazeDeg` 7 / `GazeOut` 11 · `ObsSpeed` 1,6 · `ObsGrow` 0,25 · `ObsGlow` 2,5 · `ObsSpin` 80.
- `LifeMin` 10 · `LifeMax` 16 · `ReleaseLife` 3,5 · `GapMin` 2,5 · `GapMax` 6 · `FormDelay` 2,5 · `FormGap` 1,6 · `LifeSteps` 24.

**2-Eleccion**
- `HoldTime` 3 · `FadeBack` 0,5 · `ChooseGrow` 0,25 · `ChooseGlow` 2,5 · `ChargePulse` 0,5 · `ChargePulseHz` 1,1 · `ExciteSpeed` 2,5.
- `ChoiceDelay` 3 · `ChoiceTimeout` 25 · `ChosenTint` 0,35 · `ChosenDrop` 75 · `ChosenScale` 0,26.

**3-Ameba:** las de `BP_FeedDirector_SC` (`RevealTime` 4, `FeedSpeed` 0,8) + `AttnMax` 0,55 · `AttnFull` 25.

**4-Tiempos:** `StartDelay` 2 · `DustAt` 11 · `T22` 17 · `T23` 52 · `FinaleHold` 10.

**5-Sonido:** `VoLines` = [VO_20, VO_22, VO_23, VO_23b] (`/Game/SoulCharger/Obra/Audio/`) · `VoVol` 1 · `FeedSound` = `ChargeFinal` (cuando llega el tuyo) · `SfxVol` 0,8 · `HapticEffect`.

**6-Mundo:** `Fluid` · `FluidCalm` / `FluidActive` (el EEG del fluido sigue la luz de la ameba).

**7-Particulas**
- Nube del pensamiento mirado: `MoteSystem` = `NS_FocusMotes_SC` · `MoteRate` 70 · `MoteLife` 1,4 · `MoteSize` 0,35 · `MoteRadius` 30 · `MoteNoise` 15 · `MotePull` 80 · `MoteRelease` 40 · `MoteAlpha` 0,9 · `MoteFade` 0,6.
- Vuelo: `Fly*` de Feed.
- Polvo de la mirada: `DustRate` 35 · `DustRadius` 40 · `DustDist` 220 · `DustSpeed` 3 · `DustColor` · `DustAlpha` 0,7.

**8-Titulos:** `TitleMesh` · `EyePos` (0, 0, 120) · `TitleScale` 0,15 · `TitleDrop` 16 · `TitleTime` 1,2 · `TitleOutTime` 0,8.

**9-Prueba:** `DebugTarget` · `bDebugAuto` (mira 6 s de cada 8 un pensamiento vivo, distinto en cada ventana). Se ponen **antes** del Play (gotcha 628).

**Z-Estado:**
- Por pensamiento: `TState` (0 dormido · 1 vivo · 3 hecho polvo) `Obs` `ObsTotal` `Charge` `Excite` `NextAt` `DieAt` `ConsumeAt` `FeedAt` `FlyState` `MoteF` `MoteOn` `Motes` `SlotOf` `BaseSize` `BaseEdge` `BaseSpin` `CCol` `TitleComps`.
- Lugares: `SlotLoc` `SlotBusy`.
- De la ameba: `OrigCol` `MainHome` `MainRot` `MainSc` `BaseLife` `BasePulse` `WF` `WP` `MainRevealAt` `CellE` `AttnSum` `LastFeedAt` `LightP` `TintNow`.
- Generales: `Target` `HintI` `GBest` `GBestDot` `Clock` `Phase` `Chosen` `ChosenAt` `bChosenIn` `ChosenInAt` `bFormOn` `bChoiceOn` `PickSlot` `PickStart` `DustComp` `DustPos` `ChosenComp` `LightSum` `bStageDone`.

## Fases (`Phase`)
| Fase | Qué pasa | Pasa a la siguiente cuando |
|---|---|---|
| 0 | espera | `StartDelay`: la ameba + VO_20 |
| 1 | la ameba; desde `DustAt`, el polvo sigue la mirada | `T22`: VO_22, se programan los pensamientos |
| 2 | los pensamientos se forman y se desvanecen | `T23`: VO_23 |
| 3 | la elección (se abre `ChoiceDelay` s después) | se llena uno (`TdChoose`) o `ChoiceTimeout` (`TdAutoChoose`) |
| 4 | todos confluyen en la ameba; llega el tuyo | `FinaleHold` s después de que llega |
| 5 | fin | `bStageDone` |

## Grafos (21 funciones, más EventGraph y UCS; compila con warnings_as_errors)
- **`TdBoot`:** los lugares → por pensamiento (estado, base, nube, título) → **`TdBootMain`** (la ameba; va después, porque su `TdLook` lee `CCol`) → el título del elegido → el polvo de la mirada.
- **`TdStep(Dt)`:** reloj → `TdPhase` → `TdGaze` → atención → `TdThought` por pensamiento → `TdDust` → `TdMain` → `TdChosenTitle` → EEG del fluido.
- **`TdPhase`:** las fases y las voces. **`TdGaze`:** la pista (`HintI`) y la mirada (cono con histéresis, solo pensamientos vivos con `AppearT` ≥ 0,8).
- **`TdThought(I, Dt)`:**
  - `Obs`, `ObsTotal`, la carga (solo en la elección) y `DieAt` (en pausa mientras se lo mira; `ReleaseLife` al soltarlo);
  - el título y `TdMote`;
  - vivo: elige, se desvanece o se aclara; dormido: se forma a su hora.
- **`TdForm(I)`:** busca un lugar libre desde uno al azar (`PickStart`); mueve la protoameba, su título y su nube; le devuelve su base y llama `Appear`. **`TdFade(I)`:** `Disappear`, libera el lugar y programa la vuelta.
- **`TdChoose(I)`:** cierra la elección, prepara el título del elegido, VO_23b, `TdConsume` de todos los vivos y los hápticos. **`TdAutoChoose`:** el más mirado.
- **`TdConsume(I)`** / **`TdFly(I)`:** el vuelo en polvo de Feed (gotcha 631: viaja el emisor). Al llegar el elegido, `bChosenIn`.
- **`TdMote(I, Dt)`** / **`TdMoteEdge(I, Want)`:** la nube del pensamiento mirado.
- **`TdDust(Dt)`** / **`TdDustAt(Dt, P)`:** el polvo de la mirada; sin cámara (Simulate), un vaivén delante de `EyePos`.
- **`TdMain(Dt)`:** la ameba (de `FdMain`), con la atención y `TintNow`. **`TdLook(L)`** / **`TdMix(C, L)`** (+ tinte) · **`TdChosenTitle`** · **`TdSound(Snd, Vol)`**.

## ✅ Verificado (2026-10-30, Simulate con `bDebugAuto`)
- Recorrido completo hasta `bStageDone` (≈ 70 s).
- El ciclo de los pensamientos funciona: los estados pasan por `11110000` → `01111110` → `10101111` → `11111101` y se re-forman en otros lugares.
- Se eligió CLARITY a los 59 s; se juntaron los 6 vivos y la ameba llegó a 1.
- Capturas en `Saved/ClaudeScripts/Thoughts/`:
  - `cap_a`: GRATITUDE mirada, con su palabra y su polvo;
  - `cap_b`: JOY mirada, otra en formación;
  - `cap_b2`: CLARITY cargándose en la elección;
  - `cap_c`: todas confluyendo en polvo hacia la ameba;
  - `cap_d`: la ameba llena con CLARITY debajo.
- Sin `Accessed None`. Una advertencia de arranque (`CCol` vacío al pintar la ameba) se arregló moviendo `TdBootMain` después de los pensamientos; la corrida siguiente salió limpia.
- `bDebugAuto` apagado, guardado, 36 actores. Queda abierto `Test_Thoughts` para que Beltrán lo pruebe (lo pidió).

## Pendiente
- ⬜ **Visor:** el ritmo (cuántos pensamientos a la vez, cuánto viven); si la palabra al mirar se lee y se siente bien; el polvo de la mirada; el tiempo de la elección; el campo de ±42°; las palabras.
- ⬜ **Costo en el Quest:** 8 protoamebas traslúcidas con Tick, 8 títulos, 9 nubes (normalmente 1-2 activas) y la ameba.
- ⬜ VO_21 (*"What you see around you… is your own mind"*), si se quiere: hoy no existe el audio.
- ⬜ Guardar la palabra elegida para los resultados y lo que se comparte (hoy queda en `Chosen`).
- ⬜ La señal de quietud (la calma sin sensor), para después.
- ⬜ Sin commit.
