# BP_FeedDirector_SC — alimentar la ameba con conceptos (Mechanics/Mind/, nivel `Test_Feed`)

- **refPath**: `/Game/SoulCharger/Mechanics/Mind/Blueprints/BP_FeedDirector_SC.BP_FeedDirector_SC` · parent Actor · creado 2026-10-29.
- **Pedido de Beltrán (2026-10-29), otro formato del foco**, con boceto en papel:
  - *"Hagámoslo en un nuevo level para no perder este"*: `Test_Focus` no se tocó.
  - Queda **solo la ameba principal**, al frente.
  - Alrededor flota una **constelación de amebitas de colores**, *"más de la onda de las protoamebas"*, cada una con su nombre.
  - El ejercicio es cargar las amebitas con la mirada: *"atraer e incorporar a nuestra mente distintos conceptos"*.
  - *"Cada amebita que carguemos desaparece, se convierte en partículas y se va atraída hacia la ameba principal"*, que se va cargando: crece, activa su movimiento y se ilumina, *"como si la estuviéramos alimentando"*.
- **Los nombres, del boceto:** AWARENESS · LOVE · ATTRACTION · LIVE · DEEP · MIND (en inglés, como todo lo que se ve en el visor). "LIVE" se leyó del boceto: confirmar.

## El nivel `Test_Feed` (`Mechanics/Mind/Maps/`)
- Es un duplicado de `Test_Focus`.
- De la copia se sacaron las amebas 1 a 3 y `BP_FocusDirector_SC`, con el OK implícito del pedido ("mantenemos la principal").
- Queda `BP_LovingCell_SC_C_0`, la principal, en (265, 0, 100), con los valores de instancia de `Test_Focus` (`PreviewTime` 13, `ActivityDrive` 0…).
- **6 `BP_ProtoSoul_SC`** (`Concept_<NOMBRE>`), a 200 cm de los ojos (0, 0, 120), como el boceto:

  | Concepto | Posición | Yaw / pitch |
  |---|---|---|
  | AWARENESS | (157, −98, 195) | −32° / +22° |
  | LOVE | (158, 106, 182) | +34° / +18° |
  | ATTRACTION | (112, −166, 127) | −56° / +2° |
  | LIVE | (109, 167, 106) | +57° / −4° |
  | DEEP | (166, −88, 52) | −28° / −20° |
  | MIND | (169, 68, 39) | +22° / −24° |

  - Cada instancia lleva su `Size` (0,15-0,17), `PhaseSeed` (0,11 a 0,95, para que no floten en fase) y 5 colores propios (`CoreColor`, `RimColor`, `EdgeColor`, `GradColorA/B`): celeste, rosa, ámbar, verde, azul profundo y violeta.
  - Son datos de autor en la instancia, como las candidatas del alma.
- `BP_FeedDirector_SC_C_0` en el origen. Lo demás quedó igual (fluido, Ganzfeld, los 4 TPs `sc2_*`). **22 actores.**

## Lo que reusa (no se construyó nada que ya existiera)
- **La protoameba** (`BP_ProtoSoul_SC`, Core): su aparición y desaparición animadas (`Appear` / `Disappear`) y su material (borde, fresnel, flotar).
  - El director solo le escribe `Size`, `EdgeIntensity` y `SpinSpeed`; su propio Tick los aplica (`ApplyHoverScale`, `PushHoverLook`, `StepSpin`).
  - `bHoverEnabled` queda en false (`Sleep()` al arrancar; `Appear` no lo prende): sin hover de manos ni su sonido.
- **El título de la Obra**: `M_TourTitle_SC`, Michroma horneada (R nítida, G resplandor), barrido líquido con `Reveal` / `Out` / `LT`.
  - `T_Concept_<NOMBRE>` (`Mind/Textures/`), del generador `scripts/feed/gen_concept_titles.py`: mismo tamaño y espaciado que `T_Title_SOULCHARGER`.
  - `MI_ConceptTitle_SC` (paleta lila de LOVING) y una hija por nombre, `MI_ConceptTitle_<NOMBRE>`, con su `Tex` y `U0/U1`.
- **De `BP_FocusDirector_SC`:** la mirada (cono con histéresis), la carga y la pista, el punto con anillo (`M_FocusDot_SC`), la ameba principal (vida, brazos, deriva propia, colores dormida/despierta) y la nube de carga (`NS_FocusMotes_SC`).

## Cómo corre
1. A los `StartDelay` s aparece la ameba principal, chica (`SleepScale` 0,45) y dormida.
2. `ConceptDelay` s después aparecen las amebitas, una cada `ConceptGap` s. Su nombre emerge debajo (`TitleDelay` + `TitleTime`).
3. **Al mirar una amebita:**
   - se carga en `HoldTime` s;
   - crece (`ConceptGrow`), enciende el borde con un latido (`ConceptGlow`, `ChargePulse`) y gira más rápido (`ConceptSpin`);
   - polvo de su color se junta en ella (la nube de carga de `Test_Focus`, `MoteRadius` 30).
   - Si se aparta la vista, la carga baja despacio (`FadeBack`).
4. **Al 100 %:**
   - la amebita se disuelve (su `Disappear`), su nombre se va con el barrido líquido (`TitleOutTime`) y vibran los dos mandos;
   - el emisor de partículas **viaja** de la amebita a la ameba principal, en arco (`FlyArc`) y a `FlySpeed` cm/s, dejando una estela de polvo de su color que la ameba atrae (`FlyPush`).
5. **Cuando el emisor llega:**
   - la ameba principal come: `Fed` + 1, suena `FeedSound` y destella (luz, escala, agitación y vida extra por `BloomTime` s);
   - crece hacia su tamaño completo: lo comido se suaviza con `FeedSpeed`.
   - La vida y los brazos van de dormida a despierta (`AwakeLife`, `AwakeCurl`) y el fluido sigue su luz.
6. Con las 6 comidas y absorbidas: suena `FinaleSound`, se va el punto y, tras `FinaleHold` s, `bStageDone`.

## Variables (categorías)
**1-Conceptos**
- `Concepts` (ProtoSoul[]) · `TitleMats` (MI[], mismo orden).
- `HoldTime` 3 · `FadeBack` 0,35 · `GazeDeg` 7 / `GazeOut` 11.
- `StartDelay` 2 · `ConceptDelay` 3,5 · `ConceptGap` 0,7 · `ConceptAppear` 1,2 (= `AppearTime` de la protoameba).
- `HintDelay` 6 · `HintLight` 0,35 · `HintHz` 0,4.
- `ConceptGrow` 0,35 · `ConceptGlow` 3 · `ConceptSpin` 120 · `ChargePulse` 0,5 · `ChargePulseHz` 1,1 · `ExciteSpeed` 2,5.

**2-Ameba** (la principal)
- `Main` · `RevealTime` 2,5 · `SleepState` 0,5 → `AwakeState` 0 · `SleepScale` 0,45.
- `SleepDim` / `SleepMix` / `SleepTint`.
- `BloomTime` 1,6 · `BloomScale` 0,14 · `BloomLight` 0,7.
- `DriftAmp` 12 · `DriftHz` 0,045 · `DriftSleep` 0,5 · `WanderRot` 7.
- `SleepAgit` 0,35 → `AwakeAgit` 1 · `FeedAgit` 0,8.
- `AwakeLife` 1,35 · `AwakeCurl` 1,5 · `FeedLife` 0,6 · `FeedCurl` 0,8 · `LifeSteps` 24 · `FeedSpeed` 1,2.

**3-Punto:** las de `Test_Focus`. **4-Final:** `FinaleHold` 14.

**5-Sonido:** `FeedSound` = `ChargeFinal` · `FinaleSound` = `SND_MindAppear` · `SfxVol` 0,8 · `HapticEffect` = `GrabHapticEffect`. Sin sonido de carga.

**6-Mundo:** `Fluid` · `FluidCalm` 0,95 · `FluidActive` 0,15. Los colores del fluido no se tocan.

**7-Particulas**
- Nube de carga: `MoteSystem` = `NS_FocusMotes_SC` · `MoteRate` 70 · `MoteLife` 1,2 · `MoteSize` 0,35 (el polvo de los brazos) · `MoteRadius` 30 · `MoteNoise` 15 · `MotePull` 80 · `MoteRelease` 40 · `MoteAlpha` 0,9 · `MoteFade` 0,5.
- Vuelo: `FlySpeed` 120 cm/s · `FlyRate` 220 /s · `FlyTime` 0,9 s (vida de la estela) · `FlyRadius` 5 · `FlyNoise` 12 · `FlyPush` 60 · `FlyArc` 25 cm.

**8-Titulos:** `TitleMesh` = plano del motor · `EyePos` (0, 0, 120) (hacia dónde miran) · `TitleScale` 0,17 (letra de ~4 cm) · `TitleDrop` 16 cm · `TitleDelay` 0,4 · `TitleTime` 1,6 · `TitleOutTime` 0,8.

**9-Prueba:** `DebugTarget` −1 · `bDebugAuto` false (mira la de la pista 6 s de cada 8). 🔴 Se encienden **antes** del Play y se apagan después (gotcha 628).

**Z-Estado:**
- Por concepto: `Charge` `Consumed` `Reveal` `RevealAt` `ConsumeAt` `FeedAt` `FlyState` `Excite` `MoteF` `MoteOn` `Motes` `BaseSize` `BaseEdge` `BaseSpin` `CCol` (= `CoreColor`) `TitleComps`.
- De la principal: `OrigCol` `MainHome` `MainRot` `MainSc` `BaseLife` `BasePulse` `WF` `WP` `MainRevealAt` `Fed` `FedShown` `LastFeedAt` `LightP`.
- Generales: `Target` `GBest` `GBestDot` `Clock` `PhaseT` `Phase` `NoLook` `DotD` `DotRing` `DotComp` `HintI` `LightSum` `bStageDone`.

## Fases (`Phase`)
| Fase | Qué pasa | Pasa a la siguiente cuando |
|---|---|---|
| 0 | espera | `StartDelay`: aparece la principal |
| 1 | la principal sola | `ConceptDelay`: se programan las amebitas |
| 2 | se alimenta | `Fed` = 6 y `FedShown` ≥ 5,97 (`FinaleSound`) |
| 3 | llena | `FinaleHold` |
| 4 | fin | `bStageDone` = true |

## Grafos (16 funciones, más EventGraph y UCS; compila con warnings_as_errors)
- **EventGraph:** `BeginPlay → FdBoot` · `Tick → FdStep(min(dt, 0,05))`.
- **`FdBoot`** (+ **`FdBootMain`**):
  - la principal (lugar, giro, escala, vida, colores, deriva sorteada; oculta y dormida);
  - por concepto: el estado, su nube (`SpawnSystemAtLocation`, apagada) y su título (StaticMesh absoluto con su MI, debajo de la amebita, girado hacia `EyePos` con `CombineRotators((0,90,90), MakeRotFromX)`, sort 110, oculto);
  - el punto.
- **`FdStep(Dt)`:** reloj → `FdGaze` → `FdCharge` → `FdConcept` por concepto → `FdMain` → `FdDot` → EEG del fluido.
- **`FdGaze`:** como `FcGaze`, sobre los conceptos visibles y sin consumir.
- **`FdCharge(Dt)`:** la carga, `Excite`, `FdConsume` al 100 %, la pista, `NoLook` y las fases. **`FdRevealConcepts`:** programa las apariciones.
- **`FdConsume(I)`:** `Disappear`; `FeedAt` = ahora + distancia / `FlySpeed`; la nube pasa a vuelo (Target = la principal, `Push` `FlyPush`, `Pull` 0); los hápticos.
- **`FdConcept(I, Dt)`:**
  - el título (visibilidad, `Reveal`, `Out`, `LT`) y `FdMote`;
  - `Appear` en el primer cuadro con `Clock ≥ RevealAt` (gotcha 632);
  - si no se consumió: tamaño en escalones, borde y giro.
- **`FdMote(I, Dt)`** / **`FdMoteEdge(I, Want)`:** la nube de carga (la de `FcMote`). Si el concepto se consumió, pasa a **`FdFly(I)`**: estados 1 → 3 → 4:
  - 1: el emisor viaja en smoothstep y arco; al llegar, `Fed` + 1, `FeedSound` y destello;
  - 3: espera a que mueran las últimas;
  - 4: se apaga.
- **`FdMain(Dt)`:** la principal se alimenta (adaptación de `FcCell`). **`FdLook(L)`** / **`FdMix(C, L)`:** sus colores. **`FdDot(Dt)`** · **`FdSound(Snd)`**.

## ✅ Verificado (2026-10-29, Simulate con `bDebugAuto`)
- Recorrido completo hasta `bStageDone` (≈ 52 s). Sin `Accessed None`, errores ni warnings de script.
  - En Simulate el log se llena de `PROTO: sin pawn VR`: es el `CachePawn` de cada protoameba, que no encuentra pawn. Con pawn no pasa.
- Capturas en `Saved/ClaudeScripts/Feed/`:
  - `cap_t1`: LOVE cargándose con polvo adentro; DEEP y MIND con sus nombres.
  - `cap_fly0`: la estela celeste de AWARENESS entrando en la principal y su nombre disolviéndose.
  - `cap_fly2`: DEEP llegando, la principal ya crecida.
  - `cap_full`: el final, la principal llena.
- La principal llena: `GlobalState` 0, `Agitation` 1, `NoiseAmount` 1,35, `StrandCurl` 1,5.
- `bDebugAuto` apagado y guardado. 22 actores.

## 🐛 Dos arreglos en la primera prueba
1. Las amebitas no aparecían: el flanco de `Appear` leía `Reveal` con un `bind` que se relee después de escribirlo (gotcha 632). Ahora el flanco es el del reloj.
2. Las partículas no viajaban (quedaba una esfera expandiéndose en el lugar): `Pull` del halo es radial desde el emisor, no hacia `Target` (gotcha 631). Ahora viaja el emisor.

## Pendiente
- ⬜ **Visor:**
  - si se lee el nombre a 2 m (`TitleScale`);
  - el tamaño de las amebitas;
  - los 120° de ancho, porque ATTRACTION y LIVE obligan a girar la cabeza;
  - la estela (`FlyRate`, `FlyArc`);
  - si "LIVE" es la palabra.
- ⬜ **Costo en el Quest:** 6 protoamebas (traslúcidas, con su Tick) + la principal de 5 grupos + 6 títulos traslúcidos + 6 nubes (una prendida por vez).
- ⬜ La música (la de Beltrán) y la VO de Alma.
- ⬜ Sin commit.
- 💡 Si se quiere que la constelación quede: en vez de `Disappear`, dejar la amebita como un punto apagado.
