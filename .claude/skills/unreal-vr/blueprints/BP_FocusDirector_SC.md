# BP_FocusDirector_SC — ejercicio de FOCO con la mirada (Mechanics/Mind/, nivel `Test_Focus`)

- **refPath**: `/Game/SoulCharger/Mechanics/Mind/Blueprints/BP_FocusDirector_SC.BP_FocusDirector_SC` · parent Actor · creado 2026-10-29.
- **Pedido de Beltrán (2026-10-29):** una variante de Mind donde, en vez del EEG del Muse, la ameba se activa **sosteniendo la mirada**.
  - 4 amebas repartidas que se mueven suave y un punto que marca hacia dónde se mira.
  - Al sostener la mirada ~4,5 s sobre una, esta se carga de luz y de movimiento, y queda activada.
  - Lo quiere *"hermoso, didáctico, fácil e interactivo"*.
  - Aprobó: 4 amebas · primero una y después las otras tres · la carga no se reinicia al apartar la vista · constelación al final.
  - **La música todavía no** (la pasa él).
- **Nivel `Test_Focus`** (`Mechanics/Mind/Maps/`): duplicado de `Test_Mind`.
  - Tiene 4 `BP_LovingCell_SC` (`FocusCell0..3`) y el director (`FocusDirector`) en el origen.
  - Lo demás quedó igual: fluido, Ganzfeld y los 4 TPs `sc2_*` (no se ven en el juego).
  - **Sin el ensayo `BP_StageRunner_SC`**, que Beltrán aprobó sacar porque toma una célula con la coreografía de Loving. `Test_Mind` no cambió.
  - **Sin Alma**: Beltrán la sacó el mismo día (*"en este level de test no es necesario que esté Alma"*).
  - Son 19 actores.
- **Fuente de los grafos:** `scripts/focus/focus_src.dsl`. `gen_focus_dsl.py` expande `(G X)`/`(S X v)` igual que el arpa. También están `build_director.py` (variables y funciones), `prep_v3.py` (vaciar grafos y sacar lo viejo) y `focus_dot_material.py`.
- **Partículas de carga:** `Mechanics/Mind/VFX/NS_FocusMotes_SC`, duplicado de `NS_OrbHalo_SC` (SC_Sequencer) sin cambios.

## 🔁 4.ª vuelta (2026-10-29, al final de la tarde)
- *"Las partículas mucho más pequeñas, como las que ya tiene la ameba en los brazos"*: `MoteSize` **1,4 → 0,35 cm** (el `DustSize` de la célula), en el CDO y en la instancia. El máximo sigue siendo el doble (0,35-0,7). Tasa, color y atracción, iguales.
- *"No hagamos la gradación de color entre las paletas, no se ve muy bien; mantén el color original todo el rato"*: **se sacó el color del lugar.**
  - Se borraron las funciones `FcEnv`, `FcEnvBase`, `FcEnvPaint` y `FcHue`, y las variables `EnvHue`, `EnvSat`, `EnvBright`, `EnvSpeed`, `EnvBase`, `EnvP`, `EnvShown`, `EnvH`, `EnvS` y `EnvB`. `FcStep` se reescribió sin la llamada.
  - El fluido y `MPC_Fluid_SC` quedan con los colores del autor todo el recorrido.
  - Si vuelve: la versión con el color está en `focus_src_v3_backup.dsl`, `gen_focus_dsl_v3_backup.py` y `build_director_v3_backup.py` (en `Saved/ClaudeScripts/Focus/`).
- ✅ Simulate con `bDebugAuto`: sin errores; la nube se ve como puntos finos alrededor del núcleo (`cap_g1.png`, de cerca, con un 38 % de carga); con la primera ameba activada, `FluidTop`, `FluidMid`, `FluidBottom`, `GlowColor` y `MoteColor` siguen iguales a los del arranque. 19 actores, flags apagados, guardado.

## 🔁 3.ª vuelta (2026-10-29 tarde, Beltrán en el visor)
Pedidos y respuestas:
- *"Siempre con un poco de noise y movimiento en los tentáculos; ahora se veían totalmente quietas cuando no estaban activadas"*. Causa medida:
  - con `SleepState` 0,95 la célula está en calma total: brazos cortos, curl × 0,25, tempo 0,7, amplitud 0,55 y arrastre rígido (`Kappa` 1 desde S 0,95);
  - encima `Agitation` 0.
  - Ahora: `SleepState` **0,5** (brazos a medio desplegar, sin arrastre rígido) y `SleepAgit` **0,35**.
- *"Que se sienta que se están cargando: atrayendo partículas, o que el noise de los tentáculos se empiece a activar"*. Causa medida:
  - la célula **satura `Agitation` en 1**, en el BP (`Clamp(AgS, 0, 1)`) y en el shader (`saturate(LV1.z)`);
  - con `ActivityDrive` 1 las dormidas ya estaban cerca del tope, así que la carga casi no sumaba.
  - Ahora `ActivityDrive` **0** en las 4 instancias: la agitación la maneja solo el director.
  - **Excitación** `Excite[i]` = la carga mientras se la mira (sin activar), suavizada con `ExciteSpeed`; baja sola al activarse o al apartar la vista.
  - **Vida** de la célula = base de la instancia × multiplicador:
    - `NoiseAmount`, `OrganicMotion`, `FloatAmount` y `PulseSpeed` por 1 → `AwakeLife` con e, + `ChargeLife` × Excite;
    - `StrandCurl` (los tentáculos) por 1 → `AwakeCurl`, + `ChargeCurl` × Excite;
    - `NoiseAmount` y `StrandCurl` con tope 2, el rango certificado de la célula.
  - Lo que va al shader (`NoiseAmount`, `StrandCurl`, `OrganicMotion`) va en `LifeSteps` (24) escalones: la célula re-empuja sus materiales (`StaticDirty`) solo cuando cambia el escalón.
  - **Partículas atraídas:** `NS_FocusMotes_SC`, una por ameba, creada en `FcBoot` y apagada.
    - Mientras se carga, nacen en una cáscara de `MoteRadius` cm y `MotePull` las lleva al núcleo; la tasa sube con la carga.
    - Al apartar la vista se sueltan hacia afuera (`MoteRelease`) y se apagan en `MoteFade` s.
    - Al activarse terminan de entrar.
  - El latido de luz sigue a `Excite`: no corta de golpe al activarse.
- *"Cuando crecieron, un movimiento las mueve a la derecha y a la izquierda; todas tenían el mismo seed y se movían sincronizadas"*. Dos causas:
  1. el vaivén del final (`OrbitYaw`) era el mismo para las 4: se **sacó** (`FcFinale`, `OrbitAmp`, `OrbitPeriod`, `OrbitYaw`, `FinaleDelay`, `FinaleTime`);
  2. el movimiento interno de la célula corre con `Tau`, que arranca en `PreviewTime` × `Tempo`, y las 4 tenían `PreviewTime` 0: iban en sincronía exacta. El `ClockSeed` de la 2.ª vuelta desfasaba `Clock`, que en la célula solo mueve la señal falsa: **no hacía nada** (se sacó).
  - Ahora `PreviewTime` 13 / 97 / 211 / 343 en las instancias, y vida base distinta:
    - `NoiseAmount` 1 / 1,15 / 0,9 / 1,05;
    - `OrganicMotion` 1 / 0,9 / 1,15 / 1,05;
    - `FloatAmount` 1 / 1,2 / 0,9 / 1,1.
  - La deriva y el balanceo de cada ameba usan frecuencias y fases **sorteadas al arrancar** (`WF` en 0,6-1,5 × `DriftHz`, `WP` en 0-2π), con dos senos por eje a razón 1 : 2,236.
  - Dormidas derivan a `DriftSleep` × la amplitud de las despiertas.
  - ⚠ Queda en sincronía el **micro**movimiento del shader (curl de las hebras, pseudópodos, bolas), que usa `GameTime` e índice de grupo, iguales en las 4. Lo disimulan la forma, el giro y la amplitud distintos. Si se sigue notando: un desfase de tiempo por célula en `LovingLib.ush`, que toca el material de Mind.
- *(Mensaje aparte)* **El lugar se activa con las amebas:** *"de morados a azules, después de azules a verdes oscuros, luego la otra, etc."*. ❌ **Sacado en la 4.ª vuelta** (no se veía bien); queda como registro.
  - Progreso = `LightSum` (la suma de e de las 4, de 0 a 4), suavizado con `EnvSpeed`. Cargar una ameba ya empieza a virar el color; si se aparta la vista, vuelve un poco.
  - Las paradas giran el tono de la paleta del fluido que dejó el autor (`EnvHue` en grados), con saturación `EnvSat` y brillo `EnvBright`, interpoladas con smoothstep:

    | Parada | Tono | `EnvHue` | `EnvSat` | `EnvBright` |
    |---|---|---|---|---|
    | 0 | morado | 0 | 1 | 1 |
    | 1 | azul | −55 | 1,35 | 1 |
    | 2 | verde oscuro | −120 | 1,3 | 0,85 |
    | 3 | ámbar | −225 | 1,25 | 1,1 |
    | 4 | rosa aurora | −300 | 1,15 | 1,25 |

  - Qué se pinta y por dónde:
    - `FluidTop`, `FluidMid`, `FluidBottom`, `GlowColor` y `MoteColor` como variables del fluido, que las publica en su Tick;
    - `CellHigh`, `CellLow` y `CellFill` directo a `MPC_Fluid_SC`, porque el fluido solo las publica al arrancar.
  - Solo repinta si el progreso cambió más de 0,002.
- ✅ Simulate con `bDebugAuto`:
  - 2 activas (`NoiseAmount` 1,35 / 1,55 · `StrandCurl` 1,5 / 1,95);
  - una cargándose con la nube encendida;
  - una dormida (`AgS` 0,35, S 0,5);
  - `Tau` 76 / 160 / 371 / 528;
  - el entorno en azul con 1 y en verde con 2; el final en rosa.
- ✅ Prueba lenta (`DebugTarget` 0, `HoldTime` 12 temporal): al 12 % las partículas llegan a la ameba chica; al 82 % hay una nube en el núcleo y la célula está en su pico (`NoiseAmount` 1,875, `StrandCurl` 2, `OrganicMotion` 1,875). Capturas `cap_e1/e2/e3.png` y `cap_f1/f2.png` en `Saved/ClaudeScripts/Focus/`.
- ✅ Sin warnings ni errores en las dos corridas. Compila con `warnings_as_errors`. Flags revertidos (`bDebugAuto` false, `DebugTarget` −1, `HoldTime` 4,5). 19 actores. Guardado.
- ⬜ Visor y costo. Ahora hay 4 nubes de partículas (solo una prendida a la vez) y re-empujes por escalón en la ameba que se carga.

## 🔁 2.ª vuelta (2026-10-29, Beltrán probó en el visor: *"no me gustó nada"*)
- 5 brazos (`GroupCount` 5, la de Soul Charger); arrancan chicas (`SleepScale` 0,45; escala colocada 0,7) y crecen.
- Giro propio en el plano (roll 0 / 50 / −35 / 110; `HomeRot`) y forma propia por instancia (estáticos):
  - `FigureTilt` 15/9/21/12 · `GroupSpread` 1,08/0,96/1,14/1,02 · `CentreRadius` 16/14,5/17,5/15,2;
  - `PulseSpeed` 1/0,86/1,12/0,94 · `SizeVariation` 0,5/0,75/0,35/0,6 · `StrandCurl` 1/1,3/0,8/1,15.
- Se sacaron los haces del final (*"horrorosos"*) y el sonido de carga (`ChargeSound` None; la lógica queda para el sonido nuevo).
- La ameba de arriba subió a z 245.

## Arquitectura: el director manda, la célula no se toca
- Las amebas son `BP_LovingCell_SC` en **fase 0** (sin contrato). **No se tocó ningún grafo de la célula**, que usa la Obra.
- El director escribe en cada célula, cada cuadro:
  - `GlobalState`, `Agitation`, y la vida (`NoiseAmount`, `StrandCurl`, `OrganicMotion`, `FloatAmount`, `PulseSpeed`);
  - posición, giro y escala; oculto (`StageVisual` no corre en fase 0);
  - los 6 colores con su `PushLook`, solo si la luz cambió.
- Lo que va al shader cambia por escalones; `FloatAmount` y `PulseSpeed` son solo del BP y van continuos.
- Instancias de las células:
  - copian los overrides de la célula de `Test_Mind`, menos `RMin` (la célula lo calcula sola);
  - `Fluid` = None (el fluido lo maneja el director) y `ActivityDrive` 0;
  - paletas por giro de tono con la misma luminancia: 0 violeta (la original) · 1 orquídea (+35°) · 2 pervinca (−30°) · 3 azul lavanda (−60°).
- **Dónde está cada ameba** (escala 0,7; el usuario en el origen mirando +X; ojos ≈ z 120):

| Ameba | Lugar | Posición | Yaw / Roll | Aparece |
|---|---|---|---|---|
| 0 | frente, abajo | (265, 0, 100) | 180 / 0 | primera |
| 1 | derecha | (151, 242, 140) | 238 / 50 | segunda |
| 2 | arriba, al centro | (300, 0, 245) | 180 / −35 | tercera |
| 3 | izquierda | (151, −242, 125) | 122 / 110 | cuarta |

## Registro de variables (instance-editable salvo Z-Estado)
**1-Foco**
- `Cells` (BP_LovingCell_SC[]): las amebas en el **orden de aparición**.
- `HoldTime` 4,5: segundos de mirada sostenida para activar.
- `FadeBack` 0,35: al apartar la vista la carga baja a 0,35× la velocidad de subida; **no se reinicia**.
- `GazeDeg` 8 / `GazeOut` 12: cono para entrar y para seguir en la misma ameba (histéresis contra el temblor de la cabeza).
- `StartDelay` 2: cuándo aparece la primera.
- `RevealDelay` 1,5 / `RevealGap` 0,9: las otras aparecen tras activar la primera, escalonadas.
- `RevealTime` 2,5: aparición con ease-out-back, la misma curva que `StageIntro` de la célula.
- `HintDelay` 6: sin mirar una ameba sin activar durante ese tiempo, la primera que falta late suave.

**2-Ameba**
- `SleepState` 0,5 / `AwakeState` 0: el estado que recibe la célula.
- `SleepScale` 0,45: tamaño dormida, relativo a la escala colocada.
- `SleepDim` 0,3 · `SleepMix` 0,8 · `SleepTint` gris lila: color dormido = lerp(original, tinte, mix) × dim; conserva el alfa.
- `SleepAgit` 0,35 · `AwakeAgit` 1 · `ChargeAgit` 1: `Agitation` = lerp(Sleep, Awake, e) + ChargeAgit × Excite. La célula la satura en 1.
- `AwakeLife` 1,35 · `ChargeLife` 0,7: multiplicador de `NoiseAmount`, `OrganicMotion`, `FloatAmount` y `PulseSpeed`.
- `AwakeCurl` 1,5 · `ChargeCurl` 0,9: multiplicador de `StrandCurl`, los tentáculos.
- `LifeSteps` 24: escalones de lo que va al shader. Menos escalones = menos re-empujes.
- `ExciteSpeed` 2,5: qué tan rápido sube y baja la excitación.
- `ChargePulse` 0,35 · `ChargePulseHz` 1,4: el latido de luz mientras se carga.
- `BloomTime` 1,6 · `BloomScale` 0,14 · `BloomLight` 0,7: el destello al activarse.
- `DriftAmp` 12 cm · `DriftHz` 0,045 · `DriftSleep` 0,5 · `WanderRot` 7°: deriva y balanceo propios de cada ameba.
- `HintLight` 0,35 · `HintHz` 0,4: el latido de la pista.

**3-Punto**
- `DotAngle` 3°: tamaño angular fijo.
- `DotIdle` 260 cm: distancia sin objetivo. Con objetivo va a la distancia de la ameba −25 cm, para no verse doble.
- `DotColor` · `DotOpacity` 0,9 · `DotIdleOpacity` 0,55.
- `DotMat` = `M_FocusDot_SC` · `DotMesh` = `/Engine/BasicShapes/Plane`.

**4-Final**
- `FinaleHold` 14: tras activar las 4, ese tiempo hasta `bStageDone`.

**5-Sonido** (todos de la Obra)
- `RevealSound` = `SBubbleHoverOn` · `ChargeSound` = None (pendiente del sonido nuevo).
- `LockSound` = `ChargeFinal` · `FinaleSound` = `SND_MindAppear` · `SfxVol` 0,8.
- `HapticEffect` = `GrabHapticEffect`: `PlayHapticEffect` en las dos manos al activar.

**6-Mundo**
- `Fluid`, `FluidCalm` 0,95, `FluidActive` 0,15: el EEG del fluido sigue la luz promedio de las amebas. Sus colores no se tocan.

**7-Particulas**
- `MoteSystem` = `NS_FocusMotes_SC`.
- `MoteRate` 90 /s (× 0,3-1 según la carga) · `MoteLife` 1,8 s · `MoteSize` 0,35 cm, como el polvo de los brazos (el máximo es el doble) · `MoteAlpha` 0,9: color A1 de la ameba.
- `MoteRadius` 75 cm · `MoteNoise` 25 · `MotePull` 110 (atracción, cm/s²) · `MoteRelease` 60 (al soltar) · `MoteFade` 0,6 s.

**9-Prueba**
- `DebugTarget` (−1): ≥ 0 fuerza la mirada a esa ameba.
- `bDebugAuto` (false): mira la ameba de la pista 6 s de cada 8. Es la prueba sin visor.
- 🔴 Las dos van **apagadas** en la instancia. Se ponen **antes** del Play (gotcha 628).

**Z-Estado:** `Charge[]` `Locked[]` `Reveal[]` `RevealAt[]` (−1 = no programada) `LockAt[]` `LightP[]` `Excite[]` `MoteF[]` `MoteOn[]` `Motes[]` `Home[]` `HomeRot[]` `BaseSc[]` `BaseLife[]` (NoiseAmount, StrandCurl, OrganicMotion, FloatAmount de la instancia) `BasePulse[]` `WF[]` `WP[]` `OrigCol[]` (6 por ameba) `DotComp` `ChargeAC` `Target` `GBest` `GBestDot` `Clock` `PhaseT` `Phase` `NoLook` `DotD` `DotRing` `LockedN` `HintI` `ChargeOn` `LightSum` `RevSnd` `bStageDone`.

## Fases (`Phase`)
| Fase | Qué pasa | Pasa a la siguiente cuando |
|---|---|---|
| 0 | espera | `StartDelay`, y aparece la ameba 0 |
| 1 | solo la ameba 0 | se activa la 0 (`FcRevealRest`) |
| 2 | las 4 | `LockedN` = 4 (`FinaleSound`) |
| 3 | las 4 activas, cada una con su movimiento | `FinaleHold` |
| 4 | fin | `bStageDone` = true |

## Grafos (15 funciones, más EventGraph y UCS; compila con warnings_as_errors)
- **EventGraph:** `BeginPlay → FcBoot` · `Tick → FcStep(min(dt, 0,05))`.
- **`FcBoot`:**
  - por ameba: inicializa los arreglos; guarda lugar, giro, escala, vida base y colores; sortea `WF`/`WP`; crea su nube (`SpawnSystemAtLocation`, sin auto-activar); la esconde y la pinta dormida;
  - crea el punto (StaticMesh absoluto, sort 300).
- **`FcStep(Dt)`:** reloj → `FcGaze` → `FcCharge` → `FcCell` por ameba → `FcDot` → EEG del fluido.
- **`FcGaze`:** `DebugTarget` / `bDebugAuto`; si no, `GetPlayerCameraManager`: de las amebas con `Reveal` ≥ 0,9, la de mayor `dot(dir, forward)` dentro del cono.
- **`FcCharge(Dt)`:** carga y descarga, `Excite`, `FcMote` por ameba, `FcLock` al 100 %; `HintI`; `FcChargeSnd`, `NoLook` y las fases.
- **`FcMote(I, Dt)` / `FcMoteEdge(I, Want)`:** la nube de partículas. Solo trabaja la ameba con la nube prendida o apagándose. Al prenderse copia las perillas y activa; al apagarse corta el nacimiento y suelta o termina de absorber.
- **`FcChargeSnd(W)`** / **`FcACFade`** (`FadeOut` de `AudioComponent` puesto **por cirugía**, gotchas 40/102) · **`FcLock(I)`** · **`FcSound(Snd)`** · **`FcRevealRest`**.
- **`FcCell(I)`:**
  - aparición con ease-out-back · `e` = smoothstep(carga) · `x` = Excite · destello · pista;
  - escala = aparición × lerp(`SleepScale`, 1, e) × (1 + destello);
  - posición = hogar + deriva propia; giro = el del hogar + balanceo propio;
  - `GlobalState`, `Agitation` y la vida (escalonada para el shader);
  - `FcLook` **solo si la luz cambió > 0,004**.
- **`FcLook(I, L)`** / **`FcMix(C, L)`:** los colores dormido / despierto / destello.
- **`FcDot(Dt)`:** el punto frente a la cámara a `DotD` (suavizado), parámetros `Progress`, `Ring` y `Opacity`; se oculta en el final.

## `M_FocusDot_SC` (Mind/Materials)
- Configuración copiada de `M_PointerDot_SC`: Unlit, Translucent, TwoSided, sin depth test.
- Customs `FocusPS` (Color × Glow) y `FocusOP`: punto suave, halo y anillo de progreso que arranca arriba y gira en sentido horario; sin anillo se ve a 0,22.
- Parámetros: `Color`, `Glow`, `Opacity`, `Progress`, `Ring`, `DotR` 0,11, `RingR` 0,72, `RingW` 0,05.

## Pendiente
- ⬜ **Visor:** que se sienta; la altura real de los ojos; el tamaño del punto; el temblor de la cabeza contra `GazeDeg`; si las partículas de 0,35 cm se leen o hay que subir `MoteRate`.
- ⬜ **Costo:** 4 células de 5 grupos, más la nube y los re-empujes de la que se carga. Medir en el Quest antes de sumar nada.
- ⬜ **Música:** la de Beltrán, una capa por ameba, que sube con la carga. **Sonido de carga** nuevo.
- ⬜ VO de Alma con la instrucción, en inglés.
- ⬜ Sin commit.

## Trampas de esta construcción
- Escribir una perilla en el actor de **PIE** con `set_properties` re-corre su Construction Script: los componentes creados en runtime quedan `TRASH_` y los arreglos se vacían (gotcha 628).
- La célula satura `Agitation` en 1 y su reloj de vida es `Tau`, que nace de `PreviewTime` (gotcha 629).
- `set_properties` de un arreglo pide una lista JSON, no el texto de Unreal `(a,b)` (gotcha 630).
- Se volvieron a pagar gotchas ya anotadas: `elif` se anida (177) · `%` infijo no existe, pero el nodo `Math|Float|%(Float)` sí (450) · `bIsEditorOnlyActor` no saca un actor del PIE (608) · `StartPIE` con warmup alto da timeout pero arranca (98).
