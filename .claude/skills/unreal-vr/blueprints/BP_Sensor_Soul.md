# BP_Sensor_Soul — el sensor que se toma con la mano hábil y CONTIENE las mecánicas (Core/Sensor/)

> `/Game/SoulCharger/Core/Sensor/BP_Sensor_Soul` · creado 2026-08-19 · **una instancia** en `MapsV2/L_SoulCharger` (`Sensor_Soul`, en **50/0/100**).
> **Estado: 🟡 modos + cableado con el director + fase de práctica verificados en PIE por log (2026-08-24, cero `Accessed None`); las mecánicas reales (respirar, latir, apuntar) necesitan visor.**

## Qué es
El sensor único de la versión limpia: **se toma UNA vez en el Hall** (esfera de 10 cm, **la mano con la que se toma define la mano hábil** — `bTookRight`; el salto de debug siembra la derecha) y **contiene TODAS las mecánicas de interacción de las etapas**, activadas por sala (decisión de Beltrán: *"contener todo el código de interacción en BP_Sensor_Soul y corregir desde ahí"*).

## 🔴 DECISIÓN 2026-08-24 (pivote de Beltrán): SIN sistema de calibración
> *"No vamos a hacer ningún sistema de calibración… ya tenemos unos valores bases. El usuario lee las instrucciones y parte a controlar la esfera con su respiración, siempre que esté dentro del umbral."*

- El **levantamiento de datos** vive aparte (el packaging de `Calibration/`); cuando haya datos suficientes, Beltrán los trae y **ahí** se afinan los valores del umbral.
- El umbral usa la **zona BASE** (`bZonePre`), **sin** `CalDist` por usuario. 🔬 **2026-08-24 (tarde): la zona salió del ANÁLISIS DE LOS 14 USUARIOS de la Quest** (`docs/ANALISIS-CALIBRACION-2026-08-24.md`): **`SafeHorizMax` 23 · `SafeVDropMin` 33 · `SafeVDropMax` 63 · `ActivateDelay` 1.5 s** (entrada al umbral más lenta — el reclamo de "reconoció demasiado rápido con la mano al aire"). Cobertura del estómago ≥99.7% y rechazo de la pierna 100% en los 11 usuarios válidos; `StillLin` 8 / `StillAng` 25 / `MinAmplitude` 0.003 confirmados por los datos. Escritos en CDO **y** en la instancia.
- La maquinaria de calibración quedó **DORMIDA, no borrada** (`BreathCalib`, `bCalibrated`, `CalDist/CalTimer/CalHold/CalGap/CalCooldown`, `bZonePost`, y la barra `CalibBar` del widget con su cadena `SetCalibProgress`): `BreathGate` la puentea llamando directo a `BreathThreshold`. Cuando vuelva la calibración con datos, se reconecta ahí.
- **El cierre de etapa es SOLO por tiempo** (*"la etapa tiene una duración definida"*): `CountBreaths` y `HeartBeatStep` **ya no llaman `MechDone`** — cuentan y loguean, nada más. `MechDone`/`OnMechDone`/`bMechDone` quedan dormidos (el gancho para cuando un cierre por mecánica vuelva a existir).

## 🎛️ El sistema de MODOS
- **`SetStage(StageIndex)`** (lo llama [[BP_Director_Story]]): guarda `Mode`, resetea el estado por-modo **y `bPractice`**, y prende/apaga el beam (`BeamMesh` visible sólo en modo 4).
- **`bPractice`** (lo escribe el director): la fase de **práctica** de Entering — el umbral corre durante las instrucciones y mueve el **círculo del widget**, pero la esfera del mundo ([[BP_BreathOrb_SC]]) espera. `StartStepTime` re-llama `SetStage(1)` → práctica off → la esfera aparece.
- **`TickMech(DT)`** (Tick): corre con `bTaken` && `!bMechDone` && pawn válido; despacha 1→`TickBreath` · 2→`TickHeart` · 4→`TickBeam` (if/elif — el `switch int` del DSL no acepta el case 4, §211).

| Mode | Sala | Mecánica |
|---|---|---|
| −1 / 0 | reposo / Hall | nada |
| **1** | Entering | **respiración por umbral** (base, sin calibración). Se arma **al mostrarse las instrucciones** (`ArmPractice`, con `bPractice=true`) y sigue toda la etapa. |
| **2** | Recognizing | **latido** al BPM del BioHub en zona de pecho (base). |
| 3 | Loving | nada (pasiva) |
| **4** | Attracting | **beam** desde el Aim de la mano hábil. |
| **5** | Surrounding | **dibujo 3D libre desde la mano hábil** (2026-08-26, ver §Modo 5). |

## 🌬️ Modo 1 — respiración (los valores efectivos del CDO afinado de `BP_BreathSensor_V2`)
`TickBreath(DT)` → `BreathGate` (puente) → `BreathThreshold` → `BreathHaptic` → `DetectDir` → `CountBreaths`:
1. **Quietud**: velocidades del grip de la **mano hábil** (EMA ataque-rápido/caída-lenta, `StillTau` 0.3) → `bQuiet` = LinSpeed<`StillLin` 14 && AngSpeed<`StillAng` 45 && trackeado (eran 8/25 — ver la 4ª pasada del 2026-09-01).
2. **Geometría** (`HeadGeom`): cámara del pawn vs `Body` → `GeomHoriz`/`GeomVDrop`/`SensDist`.
3. **Señal**: `Right.Z` del grip (LockedAxis=1 de V2). Band-pass `FastV`(τ 0.4) − `SlowV`(τ 20, el valor EFECTIVO del CDO — no el 90 del tracker viejo). Sin quietud → reseed.
4. **Umbral** (`BreathThreshold`, **v4 — ver la 3ª pasada del 2026-09-01**): `_in = bZonePre && bQuiet && (bBreathing || HAmp ≥ MinHAmp)`, con debounce **1.5 s de entrada / 0.2 s de salida** → `bBreathing` + logs `UMBRAL IN/OUT` + **`Pulse()` en el flanco IN**.
5. **Háptico del umbral** (`BreathHaptic`): zumbido continuo (`SetHapticsbyValue`, `HapticAmp` 0.25 — el valor de V2, knob de CDO **no** instance-editable) en la mano hábil mientras `bBreathing`; apagado limpio en el flanco de salida. 🔴 Reescrito tras §213: el estado `bWasBreathing` se actualiza **dentro del flanco**, no antes (un `bind` de getter puro no es snapshot).
6. **ZigZag** (`DetectDir`): señal = `BreathV × (derecha ? +1 : −1)`, delta = `Amplitude × DirFrac 0.3` → `bInhaling`.
7. **Conteo** (`CountBreaths`): sostenidas de `InhaleHold` 4 s → `BreathCount` + pulso + log. **No cierra nada.**

### 🎚️🔴 `BreathLevel` v6 — LA SEÑAL ES EL DESPLAZAMIENTO, NO LA INCLINACIÓN (2026-08-24, cierre)
Beltrán, tras 3 iteraciones fallidas: *"no siento nada conectado el sensor con la esfera"*. Se midió con **label de verdad-terreno**: él apretaba el gatillo al inhalar y lo soltaba al exhalar, 51 s a 72 Hz. Veredicto: **la inclinación del mando (`bv`) NO discrimina** (AUC 0.587 = azar) — el problema nunca fue el mapeo, era la **entrada**. Detalle completo: Parte 3 de `docs/ANALISIS-CALIBRACION-2026-08-24.md`.

- **La señal buena es `GeomHoriz`** (distancia horizontal cabeza→sensor): al inhalar la panza **empuja el sensor hacia afuera**. AUC **0.837** en la corrida de Beltrán y **0.990 mediana en los 11 usuarios** de calibración, con **el mismo signo en 10/11** → **señal universal, sin calibración ni seed de signo**. La inclinación funcionaba en el prop de calibración (agarre fijo) pero no en la esfera pegada al grip (agarre arbitrario).
- **`UpdateLevel` v6**: `S = EMA(GeomHoriz,0.4) − EMA(GeomHoriz,HorizTau 3)` (reseed si no hay quietud) → `nivel = 0.5 + 0.5·x/(1+|x|)`, `x = S/GainK 0.5` (centímetros) → `FInterpTo(LevelFollow 5)`. El band-pass de 3 s **elimina la deriva postural por construcción**.
- Parámetros elegidos con los datos: `HorizTau` 3 s (barrido 2-8, AUC 0.997) · `GainK` 0.5 cm (recorrido 0.18↔0.81 en el usuario mediano, 0.70 en el más suave, nadie clavado).
- **Dormidas** (no borradas): `SeedTheSign`/`SeedSign`/`bSignSeeded` · `Baseline`/`PinT`/`PinTau`/`PinThr`/`PinDwell` · `EnvHi`/`EnvLo`/`EnvTau`/`MinSpan` · `NormK` · `SigTau` · `SignAcc`. `bFlipSign` queda como escape manual. `bv`/ZigZag: solo conteo por log.
- 🧪 **Instrumentación** (apagar al validar, ambas en el CDO): `bDebugBreath` → `BLOG,t,lb,bv,ss,bl,lvl,sg,zn,qt,br,h,v,ls,as` cada frame, con **`lb` = gatillo como label** (eventos `IA_Shoot_*` + `IMC_MenuTrigger` con la receta del picker, en `EnsureInput`/`MaybeInput`); `bDebugOrb` → `OLOG,t,sc,rv`. Analizadores en `scratchpad/quest/analyze_{label,transform,geom,gain}.py`.
- ✅ **Validado en visor por Beltrán** (*"ahora sí, mucho mejor"*). Ajustes de cierre de esa pasada:
  - **El UMBRAL también pasó a la señal buena**: la compuerta de amplitud usaba `Amplitude` (EMA de la inclinación = ruido). Ahora es `HAmp` = EMA(|HorizBP|, `TauAmp` 4) contra **`MinHAmp` 0.02 cm**.
  - 🐛 **`MinHAmp` nació en 0.12 y bloqueó el umbral POR COMPLETO** (Beltrán: *"nunca entró"*). Error de extrapolación: 0.12 salió de las amplitudes de la calibración (0.5-4 cm de recorrido pico a pico), pero `HAmp` es **el EMA del valor absoluto**, un estadístico mucho menor — medido en vivo: mediana 0.09-0.38. ✅ **El valor final se eligió SIMULANDO la máquina del umbral sobre las 3 corridas reales del log** (`scratchpad/quest/sim_threshold.py`): con 0.12 → *nunca abre*; con 0.02 → abre y queda abierto 50-78 % del tiempo. 👉 Regla: **un umbral sobre un estadístico derivado se fija midiendo ESE estadístico en vivo, nunca extrapolando del crudo.**
  - 🔴 **Estructura final del umbral (v3, elegida por simulación):** `_in = zonePre && (bBreathing || (quiet && HAmp ≥ MinHAmp))` — **entrar** exige zona + quietud + respiración real; **quedarse** exige sólo zona. Así moverse o mirar alrededor ya no desconecta (sólo sacar la mano de la panza), y un sostén largo tampoco tira el umbral. Medido sobre las corridas reales: sube el tiempo conectado de 64 %→78 % (corrida buena) y de 23 %→50 % (corrida con mucho movimiento). Mientras no hay quietud el band-pass se resetea, así que el nivel vuelve suave al neutro sin perder la conexión.
  - **Los visuales volvieron a gatear por `bBreathing`** (no por `bZonePre`): Beltrán reportó que reaccionaban *antes* del pulso háptico. Ahora visual y háptica entran juntos, y el freeze que motivó el cambio anterior ya no aplica porque el umbral es estable con la señal nueva.
- 🔴 **Lección**: tres iteraciones afinando el mapeo de una señal que no contenía la información. **Ante "no se siente conectado", medir primero si la ENTRADA discrimina** — con un label del usuario real, en su contexto real.

### 🫁 2026-09-01 — el sostenido no se desinfla, y la sensibilidad se conserva (`HoldSlow` + `HoldMovK`)
**Reporte de Beltran en visor:** *"funciona super el control de la esfera. Lo unico, es que cuando estoy
arriba, sosteniendo el aire, la esfera se empieza a achicar sola."*

**Causa (por construccion, no un bug):** `BreathLevel` sale de un **band-pass**, y la linea de base
`HSlow` persigue a `GeomHoriz` con `HorizTau` 3 s. Al sostener el aire, `GeomHoriz` se queda arriba y la
base **lo alcanza en ~3 s** → `HorizBP` cae a 0 → el nivel vuelve al neutro → la esfera se desinfla sola.
Es el mismo mecanismo que elimina la deriva postural: no se apaga, solo se **modula**.

**La forma del arreglo:** el alfa del EMA lento se multiplica por un factor `lerp(1, HoldSlow, still)`.
El EMA rapido **no se toca nunca** — de ahi sale la sensibilidad.

#### 🔴 El primer intento fue un LAZO — la leccion del dia
La v1 definia `still` a partir de **`|HorizBP| / GainK`**: "frenar la base cuando la senal esta lejos del
centro". Compilaba, arreglaba el sostenido, y Beltran reporto: *"ya no se achica, pero perdio sensibilidad
a mi respiracion... quedo un poco mas terco."*

**Por que:** `HorizBP` **es** la salida del band-pass, y el band-pass depende de la base. Gatear la base con
`HorizBP` cierra un lazo de realimentacion positiva: senal lejos del centro → base lenta → la senal se queda
lejos del centro → la base sigue lenta. Una vez desplazado, el sistema **se traba** en el regimen lento y
deja de seguir la intensidad de la respiracion.

👉 **Regla general: nunca gatear un filtro con su propia salida.** La condicion tiene que salir de una
cantidad **aguas arriba** del filtro que se modula.

#### ✅ v2 — el gate es el MOVIMIENTO, y el umbral es relativo al propio usuario
```
mov     = |GeomHoriz − HFast|              ; ≈ TauFast × velocidad. Solo depende del EMA RAPIDO → sin lazo
MovAvg += (mov − MovAvg) × clamp(DT/HorizTau)   ; el movimiento tipico de ESTE usuario (se setea al final)
still   = 1 − clamp(mov / max(MovAvg × HoldMovK, 1e-4), 0, 1)
factor  = lerp(1.0, HoldSlow, still)
alpha_HSlow = clamp(DT / HorizTau) × factor
```
- **Respirando** (medio recorrido) `mov ≈ 1.5 × MovAvg` → `still = 0` → factor 1 → **`HorizTau` 3 s intacto**:
  la sensibilidad a rapido/lento vuelve entera.
- **Sosteniendo** `mov` cae al piso de tremor mientras `MovAvg` todavia recuerda los ultimos ~3 s de
  respiracion → `still ≈ 0.7-0.9` → factor ≈ 0.3-0.4 → tau efectivo **8-10 s**.
- **Simetrico** (tambien sostiene el vacio abajo) y **auto-escalado**: el umbral es el propio movimiento del
  usuario, no un numero en cm → sirve igual para quien respira profundo y para quien respira suave.
  🔴 Eso fue deliberado: un umbral en cm habria repetido el error de `MinHAmp` (extrapolar de la escala
  equivocada), y la obra la respiran visitantes distintos, no solo Beltran.
- **Arranque seguro**: `MovAvg` nace en 0 → denominador 1e-4 → `still = 0` → comportamiento clasico hasta
  que el promedio se puebla (~3 s).
- **Sostenido muy largo** (>10 s): `MovAvg` decae al piso, `still` baja y la base retoma. Acotado a proposito.

**Knobs** (los dos instance-editable, en CDO **y** en la instancia, §212, verificados con `get_properties`
sobre `BP_Sensor_Soul_C_0`: `HoldSlow 0.25 · HoldMovK 1 · HorizTau 3 · TauFast 0.4 · GainK 0.5`):
| Knob | Def | Sube = |
|---|---|---|
| `HoldSlow` | 0.25 | **cuanto** frena la base en el sostenido. Bajar = sostiene mas (0.15 → tau 20 s). **1.0 = apagado**, comportamiento anterior exacto |
| `HoldMovK` | 1.0 | **cuando** se considera "quieto". Subir = detecta sostenido antes (mas pegajoso); bajar = solo sostenidos muy quietos |

**Cirugia:** `UpdateLevel` quedo con 15 nodos nuevos y **un solo cable viejo reconectado** (el delta de
`HSlow`); la rama rapida quedo intacta. `MovAvg` (`Z - Estadointerno`) se setea al final del exec, despues de
`SetBreathLevel` → los lectores del mismo frame usan el valor del frame anterior (1 frame de lag, buscado y
sin efecto). Verificado por `read_graph_dsl` post-compile.

⏳ **Falta visor**: es tacto, no log. Si vuelve a desinflarse → subir `HoldMovK` a 1.5; si vuelve a sentirse
terco → bajarlo a 0.7. Si hace falta afinar con datos en vez de a ojo, una pasada con `bDebugBreath` alcanza
para medir la distribucion real de `mov`.

### 🚪 2026-09-01 (2ª pasada) — la salida del umbral: `DeactivateDelay` 0.5 → 0.2
**Reporte:** *"cuando saco mi mano del estomago, se demora demasiado en salir del umbral."*

**Lo que dice el grafo** (leido antes de tocar): con `bBreathing` ya en true, `_in = bZonePre && (bBreathing || …)`
colapsa a **`_in = bZonePre`** — la permanencia depende SOLO de la zona. Y `bZonePre` se recalcula cada frame
sin suavizado (`HeadGeom` es instantanea). Entonces **el unico retardo de salida es `DeactivateDelay`**.

Bajado **0.5 → 0.2 s** (CDO + instancia, verificado). La asimetria queda `ActivateDelay` 1.5 s de entrada /
0.2 s de salida — que es la forma correcta de una compuerta (ataque lento, release rapido): entrar sigue
exigiendo respiracion real y no parpadea, y salir es inmediato al retirar la mano.

⚠ **Si en visor SIGUE demorando, la causa ya no es el delay sino la GEOMETRIA de la zona**: querria decir que
donde Beltran apoya la mano al sacarla de la panza todavia cae dentro de `GeomHoriz ≤ SafeHorizMax 23` y
`SafeVDropMin 33 ≤ GeomVDrop ≤ SafeVDropMax 63`. En ese caso se ajusta la zona (bajar `SafeVDropMax`), no el
tiempo. 🔴 Ojo: esos tres numeros salieron del analisis de los 14 usuarios — tocarlos afecta la cobertura del
estomago, no solo la comodidad de una pasada.

### 🚫 2026-09-01 (3ª pasada) — v4 del umbral: la QUIETUD tambien manda para quedarse
**Decision de Beltran, probando en visor:** *"si muevo muy rapido y saco un poco de la panza, ya debiera
salir. Ahora la movi rapido y me quede como a 20 cm de la panza y salio. El umbral debe estar determinado por
una mezcla de POSICION + QUIETUD. Si salgo de cualquiera de las dos, sale del umbral."*

**Antes (v3):** `_in = bZonePre && (bBreathing || (bQuiet && HAmp ≥ MinHAmp))`. Con `bBreathing` ya en true, el
`||` se satisfacia solo → **quedarse dependia UNICAMENTE de la zona**. Salir rapido de la panza sin salir de
los 23 cm de `SafeHorizMax` no desconectaba.

**Ahora (v4):** `_in = bZonePre && bQuiet && (bBreathing || HAmp ≥ MinHAmp)`
- **Entrar** exige las tres cosas (zona + quietud + amplitud real) sostenidas `ActivateDelay` 1.5 s. Sin cambios.
- **Quedarse** exige **zona Y quietud**. La amplitud deja de pedirse (para eso esta el `bBreathing ||`), asi un
  sostenido largo no tira el umbral.
- **Salir** por cualquiera de las dos, con `DeactivateDelay` 0.2 s.

**Cirugia (3 pasos):** el `>=` de `HAmp` pasa a alimentar directo el OR, se **borra** el AND viejo
`(bQuiet && HAmp≥Min)`, y `bQuiet` entra como **pin C** del AND exterior via `add_node_pin`.
🔴 **El `read_graph_dsl` MIENTE aca**: imprime el AND con dos entradas y deja `_bquiet` binde­ado y aparentemente
sin usar. Verificado con `get_node_infos`: pines A=`bZonePre`, B=`OR`, **C=`bQuiet`**. (Misma trampa que en
`DrawPress`/`DrawHaptic`, 2026-08-27.)

⚠ **Lo que esto revierte a proposito.** La v3 se habia elegido **simulando el umbral sobre 3 corridas reales**
(`scratchpad/quest/sim_threshold.py`) justamente porque exigir quietud para quedarse bajaba el tiempo conectado
a 64 % y 23 %. Beltran probo la v3 en visor y **prefiere el corte**: la desconexion al mover es ahora la
respuesta buscada, no un defecto. Si en visor el zumbido empieza a cortarse con micro-ajustes de la mano, las
palancas son `StillLin` 8 cm/s y `StillAng` 25 °/s (subirlas = mas tolerante) o `StillTau` 0.3 (bajarlo =
recupera la quietud mas rapido) — y ojo con la asimetria: salir cuesta 0.2 s pero **volver a entrar cuesta 1.5 s
mas lo que tarde `HAmp` en reconstruirse** (el band-pass se resiembra al perder la quietud).

### 🎚️ 2026-09-01 (4ª pasada) — bajarle la sensibilidad a la velocidad: `StillLin` 8→14 · `StillAng` 25→45
**Reporte:** *"ahora quedo demasiado sensible a la velocidad. Un poco menos."*

Consecuencia directa de la v4: al pasar `bQuiet` a gobernar tambien la **permanencia**, los umbrales de quietud
dejaron de usarse solo para *entrar* y empezaron a decidir *cortar*. Ahi quedaron cortos.

| Knob | Antes | Ahora | Por que |
|---|---|---|---|
| `StillAng` | 25 °/s | **45** | el sospechoso principal: la mano apoyada en la panza **cabecea con la respiracion** a ~5-15 °/s, demasiado cerca de 25. A 45 hay aire, y un gesto de retirar la mano pasa de 100 °/s |
| `StillLin` | 8 cm/s | **14** | respirar mueve la mano a 1-3 cm/s; retirarla, a 30-80. 14 cae comodo en el medio |

`StillTau` 0.3 y `DeactivateDelay` 0.2 **sin tocar**. Escritos en CDO **y** en la instancia, verificados.

🔴 **Estos dos numeros venian del analisis de los 14 usuarios** (*"StillLin 8 / StillAng 25 confirmados por los
datos"*). Retocarlos es legitimo porque **cambio su funcion**: alli se validaron como compuerta de ENTRADA
(separar "respirando quieto" de "manoteando"), y desde la v4 tambien son la compuerta de SALIDA, que pide mas
tolerancia. Si alguna vez vuelve la calibracion por usuario, revisar los dos usos por separado.

⏳ Si sigue cortando de mas, la proxima palanca es **`StillTau` 0.3 → 0.15** (recupera la quietud al doble de
velocidad, asi un pico corto no llega a acumular los 0.2 s de `DeactivateDelay`), antes que seguir subiendo los
umbrales — pasado cierto punto dejan de distinguir el gesto de sacar la mano.

### 🌱 2026-09-01 (5ª pasada) — reenganche sin salto: la senal se RESIEMBRA en el flanco IN
**Reporte:** *"cuando salgo rapido del umbral, al volver a entrar, vuelve demasiado rapido a otro tamano.
Deberia ser como la primera vez que entramos, que no hay un cambio rapido de la nada."*

**Causa:** `UpdateLevel` **nunca deja de correr** — el umbral solo decide quien MIRA el resultado. La esfera
usa `select(bBreathing, BreathLevel, 0.5)`: mientras esta afuera apunta al neutro, pero el nivel sigue
evolucionando por dentro. Entre que vuelve la quietud y que el umbral abre pasan **`ActivateDelay` 1.5 s**
de banda pasante desarrollandose **a ciegas**; en el flanco IN la esfera se engancha a un valor que ya
estaba lejos del neutro → salto. La primera entrada de la etapa no lo tiene porque la esfera nace con
`RevealT` en 0 y el crecimiento queda enmascarado por el fundido de aparicion.

**Arreglo — 3 setters al final de la rama IN de `BreathThreshold`:**
```
(|SetbBreathing true) (Pulse) (PrintString "UMBRAL IN")
(SetHFast  GeomHoriz)     ; resiembra el EMA rapido
(SetHSlow  GeomHoriz)     ; y el lento  → HorizBP = 0
(SetBreathLevel 0.5)      ; el nivel arranca en el neutro
```
`HFast = HSlow = GeomHoriz` deja el band-pass en cero, y el 0.5 es **exactamente** el valor que la esfera ya
estaba usando (`select(..., 0.5)` en `TickOrb`, verificado en el grafo del orbe). O sea: **en el instante del
IN el objetivo de la esfera no cambia en nada**; recien se mueve cuando la respiracion vuelve a desarrollar
la senal, igual que en la primera entrada.

💡 Se arregla en el SENSOR y no en la esfera a proposito: `BreathLevel` lo consumen tambien el circulo del
widget de practica y cualquier consumidor futuro. Un envelope de suavizado en `BP_BreathOrb_SC` habria tapado
el salto en un solo lugar.

⚠ Efecto lateral aceptado: se pierden los 1.5 s de historia de la senal al reenganchar, asi que el primer
medio segundo despues del IN la esfera se queda cerca del neutro. Es justamente lo pedido.

## ❤️ Modo 2 — latido (completado 2026-08-25 para la etapa Recognizing)
`TickHeart` → zona de pecho base (`HeartHorizMax` 25, `HeartVDrop` 10-45, a ojo — afinar en visor) con debounce (`ActivateDelay` 1.5 de entrada, salida instantánea) → **`HeartZoneFx(DT)`** (nueva, corre siempre en modo 2) → si en zona: `HeartBeatStep`: intervalo `60/(HeartSmooth/BeatDiv 2)` del [[BP_BioHub]] (fake LFO ya late) → `Pulse` + `OnBeatPulse` + **`BeatEnv=1`** + **audio `HeartBeatSound` (SpawnSoundAttached al `Body`)** + conteo. **No cierra nada** — el cierre de Recognizing lo hace [[BP_Elevator_SC]] por distancia.

**`HeartZoneFx`** (el feedback del umbral, patrón calcado de `BreathHaptic`):
1. `bHeartZone` = `bBioOk && ZoneTimer ≥ ActivateDelay` — **la bool pública del umbral** (la leen el director para el círculo del widget y quien haga falta).
2. `BeatEnv` decae con `FInterpTo(→0, BeatEnvDecay 2.5)` — el **envelope del latido** (salta a 1 en cada beat): el círculo de la página escala con esto.
3. Zumbido continuo en la mano hábil mientras `bHeartZone`, con apagado limpio en el flanco de salida (`bWasHeartZone` actualizado DENTRO del flanco, §213). 🆕 **2026-08-25: la amplitud LATE — `lerp(HapticAmp 0.25, 1.0, BeatEnv)`**: en cada latido la vibración salta a tope y decae con el envelope. Fue el fix del reporte de Beltrán *"falta el pulso fuerte"*: el `PlayHapticEffect` del `Pulse()` quedaba pisado porque `SetHapticsByValue` se re-aplica CADA TICK en zona (comparten canal) — en vez de pelear canales, el pulso viaja EN el zumbido.

⚠ La salida de zona es instantánea (sin `DeactivateDelay`): si en visor el zumbido parpadea al borde de la zona, agregar el debounce de salida como en breath.
⚠ Consumidores de `OnBeatPulse`: [[BP_Elevator_SC]] (el kick del ascensor).

## 🔦 Modo 4 — beam (extendido 2026-08-26 para la etapa Attracting limpia)
`TickBeam`: trace Visibility desde el Aim de la mano hábil (`TraceDistance` 800) → publica `bBeamHit`/`BeamHitLoc`/**`BeamStart`** (el origen del rayo)/**`BeamHitActor`** (el actor golpeado, null sin impacto — sale del `BreakHitResult` que ya existía; cirugía: 2 sets insertados tras `SetBeamHitLoc`) → estira `BeamMesh` (cilindro, `M_Beam_SC` unlit, NoCollision) del inicio al impacto. Visible sólo en modo 4.

**El gatillo del beam** (2026-08-26): los eventos `IA_Shoot_Right/Left` (que ya alimentaban los labels de debug) ganaron continuación — `LabelOn.then → BeamPress(Right)` y `LabelOff.then → BeamRelease(Right)`, con el literal del bool verificado por `get_pin_value`. Solo actúan con `Mode==4` y la **mano hábil** (`Right == bTookRight`):
- `BeamPress` → `BeamGrabTry`: cast de `BeamHitActor` a [[BP_SoundOrb_SC|BP_Sequencer_SC]] → `HeldOrb` + `GrabStart()` + `Pulse()` háptico; si no, `BeamBtnTry` → cast a `BP_SaveMelody_SC` → `HeldBtn` + `BeginHold()`.
- `BeamRelease` → `DropOrb` (`GrabEnd()` → la esfera se coloca o vuelve a casa) + `DropBtn` (`EndHold()`).
- El IMC lo arma el director en `ArmBeam` vía **`MaybeInput()`** (la receta probada de `EnsureInput`: `IMC_MenuTrigger`, Priority 1000, etc.).
Los consumidores del beam (esferas y botón) **poll-ean** `BeamHitActor == self` para el hover; la esfera agarrada sigue `BeamStart + dir × GrabHoldDist` leyendo `BeamStart`/`BeamHitLoc`.

## ✏️ Modo 5 — dibujo 3D libre (Surrounding V2, 2026-08-26)
Plan maestro: `docs/stages/surrounding-v2.md`. **Sin lápiz** (la punta es el propio sensor en la mano hábil), **sin botón** (1 m de práctica cierra las instrucciones), **cierre por 10 m lineales**, la firma reaparece junto al alma al final. 🔴 **El canvas (`BP_DrawCanvas`) NO se tocó**: el sensor lo spawnea en identidad, lee su `ArcLength` público, y el "borrar" es destruir + re-spawnear.

**Flujo:** `SetStage(5)` (nuevo último nodo: `DrawStage(StageIndex)`) → `DrawStage`: canvas nuevo (destruye el viejo = borra práctica) + paleta (`BP_BrushPalette`, `AttachToHand(bTookRight)` = mano contraria) + estado a cero + MPC `DrawFade=1`. `SetStage(≠5)` → `DrawOff`: suelta paleta, cierra trazo, **el canvas QUEDA** (la firma). El Tick despacha por el `else` del branch modo-4 de `TickMech` → **`DrawGate`** (guardas: Mode==5 → `CacheHandRef` → `IsValid(HandRef)` → `TickDraw`).

**`TickDraw(DT)`:** punta = `Body.GetWorldLocation` → `DrawFilter` (One-Euro clonado del pincel) → `DrawCalm` (calma clonada, lee `HandRef`) → `Palette.UpdateTouch` + supresión `bOver` → gatillo (`bDrawHeld`, seteado por `DrawPress/DrawRelease` colgados de los `then` libres de `BeamPress/BeamRelease`, gateados Mode==5 + mano hábil) → `BeginStroke`(color/mat de la paleta)/`AddPoint`(ancho de la paleta, `CalmVal`)/`EndStroke` → **`DrawCount`**: `DrawTotalNow = DrawMeters + arc del trazo vivo`; si `≥ TargetCm` y no práctica → **`DrawFinish`** = guarda total, print, `FadeTo(0)` (disolución por MPC) y **`StepTimeDone`** del director.

**Fade:** `FadeTo(Target)` + `FadeStep` (timer loop 0.04 s, `FInterptoConstant` a velocidad `1/DrawFadeTime`) escriben el escalar **`DrawFade` de `MPC_Draw`**, que multiplica el Opacity de `M_Brush_Light` (y hereda a las 2 MIs). **`ShowSignature()`** (la llama el director en el sub 9 del final): busca el TargetPoint tag **`signature_spot`**, mueve+escala el canvas (`loc = TP − s×centro_bounds`, **la escala del TP = la escala de la firma**) y `FadeTo(1)`.

🆕 **2026-08-27 (4ª tanda) — dos velocidades de fade**: `FadeStep` ya no lee `DrawFadeTime` sino una variable interna **`FadeTime`**, que se escribe al arrancar cada fade: `FadeTo` la pone en `DrawFadeTime` (2.5 — la disolución final y el fade-in de la firma) y la nueva **`FadeFast()`** en **`PracticeFadeTime`** (0.5, instance-editable, CDO+instancia). El director llama `FadeFast()` para el trazo de práctica, así se va a la misma velocidad que el panel de instrucciones (`ExitTime` 0.5). Verificado por robot: práctica 0.5 s, disolución final 2.9 s.

🆕 **2026-08-27 (3ª tanda):** **se eliminan los pulsos de entrada y salida del gatillo** (decisión de Beltrán tras probarlos en gafas: alcanza con el zumbido continuo). `DrawPress`/`DrawRelease` quedan solo con el `Set bDrawHeld`; borrados el nodo `Pulse` y su getter de `bTookRight` en ambos grafos. La háptica continua (`DrawHaptic`) y las compuertas `bDrawDone` **no se tocaron** (pin C verificado intacto post-borrado).

🆕 **2026-08-27 (2ª tanda):** (a) **`bDrawDone` también gatea gatillo y háptica**: pin C con `NOT bDrawDone` en los `AND` de `DrawPress`, `DrawRelease` y `DrawHaptic` (vía `add_node_pin` del AND conmutativo) — durante el bloqueo de la práctica (y la contemplación del final) el trigger no pulsa y el zumbido se apaga en el primer tick; todo revive cuando `PracticeGo` re-habilita. ⚠ El lector del DSL muestra el AND con 2 entradas aunque tenga 3 — verificar con `get_node_infos`. (b) 🐛 **El pulso salía en la mano contraria**: `Pulse(Right)` tiene PARÁMETRO de mano y las llamadas nuevas lo dejaban en el default `false` (= izquierda); cableado `bTookRight` en ambas.

🆕 **2026-08-27 (ajustes tras la validación en gafas):** (a) **contemplación**: `DrawFinish` ya no disuelve al toque — bloquea, espera **`AdmireTime`** (5 s, instance-editable) → `DrawDissolve` (fade) → `DrawClosed` (aviso al director con el fade completo). (b) **Háptica del dibujo**: `Pulse()` al apretar Y al soltar el gatillo (colgado en `DrawPress`/`DrawRelease`), y **zumbido continuo suave** mientras se dibuja — `DrawHaptic` (en la cadena de `DrawGate`, ANTES de la compuerta `bDrawDone`, así el flanco de apagado siempre corre), patrón calcado de `BreathHaptic` (`SetHapticsByValue` 1.0/`HapticAmp` por tick, apagado limpio en el flanco con `bWasDrawHap` §213); `DrawHapOff` también se llama desde `DrawOff` (salida de modo).

**Knobs** (instance-editable, ya escritos en la instancia): `PracticeCm` **300** · `TargetCm` 1000 · `DrawFadeTime` 2.5 · 🆕 `AdmireTime` 5. De CDO: One-Euro (`MinCutoff` 1 / `Beta` 0.007 / `DCutoff` 1), calma (`VMax` 120 / `TurnMax` 200 / `SpeedTau` 0.15 / `CalmTauDown` 0.12 / `CalmTauUp` 0.6).

✅ **Verificado por log (PIE autotest, `DebugStartRoom=5`, cortafuegos temporal 15 s):** ciclo completo sala 5 — SetStage 5 + canvas + paleta → práctica → panel cerrado → **re-SetStage 5 (borra práctica)** → cierre → 5º anillo → ending → `la firma aparece junto al alma` → `FIN del guion`, **cero `Accessed None` en la corrida completa**. ⚠ Lo que PIE no prueba: dibujar de verdad, el look del trazo (F0 pendiente), la paleta en mano — **visor**.
🐛 **Tres bugs cazados por el ROBOT** (rutina 3 de [[BP_Robot]], mismo día): (1) `DrawCalm` leía `HandRef` null → `CacheHandRef` + `IsValid` en `DrawGate`. (2) 🔴 **El paso 10 del final re-llama `StartStepTime` → `SetStage(5)` y `DrawStage` DESTRUÍA LA FIRMA recién aparecida** → guarda `bDrawDone` en `DrawStage`: con el dibujo completado, la re-entrada al modo 5 no toca nada (ni canvas ni paleta). (3) Ese mismo paso 10 dejaba `TickDraw` corriendo sin paleta (Accessed None en `PaletteRef`) → `DrawGate` también gatea por `(not bDrawDone)`.
✅ **Ciclo completo verificado 2× por el robot dibujando de VERDAD** (rutina 3: mano derecha en Lissajous ~70 cm/s): práctica 1 m cierra el panel POR MECÁNICA (una sola vez, candado del director), 10 m cierran la etapa a los ~20 s (cortafuegos 300 s intacto), la firma reaparece con el dibujo real y **sobrevive al paso 10**; cero `Accessed None` en la ventana completa.

## Registro de variables (además de las de la toma)
| Cat | Variables | Rol |
|---|---|---|
| C - Breath (knobs por instancia) | `TauSlow` 20 · `TauFast` 0.4 · `TauAmp` 4 · `MinAmplitude` 0.003 · **`StillLin` 14 · `StillAng` 45** (eran 8/25) · `StillTau` 0.3 · `SafeTol` 9 · **`SafeHorizMax` 23 · `SafeVDropMin` 33 · `SafeVDropMax` 63** · `CalHold` 4.5 · `CalGap` 2 · **`ActivateDelay` 1.5** · **`DeactivateDelay` 0.2** (era 0.5) · `DirFrac` 0.3 · `InhaleHold` 4 · `MaxBreaths` 5 · 🆕 **`HoldSlow` 0.25 · `HoldMovK` 1.0** | zona y delay del análisis 2026-08-24 (`docs/ANALISIS-CALIBRACION-2026-08-24.md`); los `Cal*`/`SafeTol` hoy dormidos. `HapticAmp` 0.25 = knob de CDO (no editable, §212) |
| D - Heart | `BeatDiv` 2 · `HeartHorizMax` 25 · `HeartVDropMin` 10 · `HeartVDropMax` 45 · `MaxBeats` 15 · 🆕 `BeatEnvDecay` 2.5 · 🆕 `HeartBeatSound` = `Core/Audio/Sounds/HeartBeat` | `MaxBeats` hoy sin efecto (no cierra). Los 2 nuevos son **knobs de CDO, no instance-editable** (a propósito, §212). 🧪 Truco de PIE sin visor: `HeartVDropMin=0` en la instancia abre la zona con la mano de escritorio (VDrop=0). |
| E - Beam | `TraceDistance` 800 · `BeamRadius` 0.6 | |
| Z - Estado | `Mode` −1 · `bPractice` · `bMechDone`(dormida) · `bQuiet` · `bZonePre/Post` · filtros (`SlowV/FastV/BreathV/Amplitude/RunExtreme`) · `bCalibrated`/`CalDist`/`CalTimer`/`CalCooldown` (dormidas) · `InTimer/OutTimer` · `bBreathing`/`bInhaling`/`bWasBreathing`/`InhaleTimer`/`bHoldCounted`/`BreathCount` · `ZoneTimer/BeatTimer/BeatCount/bBioOk/BioRef` · `bBeamHit/BeamHitLoc` · `GeomHoriz/GeomVDrop/SensDist` · 🆕 `MovAvg` · `HandRef/AimRef` · `bPendingRight` | |

🔴 **Los 25 knobs están escritos en la INSTANCIA del nivel** (§212: nacieron en 0 pese al CDO). Si se repone el actor, recargarlos.

## La toma (2026-08-19, intacta) + reintento
`Body`+`Twin` (`MI_Sensor`, NoCollision), detección por distancia², `Appear()`, `Take(Right)` → attach + sonido + háptica + `OnTaken`. `Take` sin pawn **se reintenta solo** cada 0.5 s (`RetryTake` + `bPendingRight`) — arregló la siembra de `DebugStartRoom` (pawn tardío).

## Verificado por log (2026-08-24, PIE `DebugStartRoom=1` + autotest)
- Práctica: `SetStage 1` + `bPractice=true` al mostrarse el panel (medido en la instancia PIE) → la esfera espera (`RevealT=0`).
- Paso: `SetStage 1` (práctica off) → **`ORB: true`** → 10 s → `SetStage -1` → **`ORB: false`**. Ciclo de salas intacto, **cero `Accessed None`**.
- ⚠ Lo que PIE no prueba: respirar de verdad (umbral/zona con el sensor en la panza), el zumbido, el círculo moviéndose — **visor**.

## Trampas pagadas acá
§210 (`get_node_type_pins` instancia un nodo sonda) · §211 (`Equal(Name)` no escribible → `==`; `switch int` sin case 4) · §212 (knobs instance-editable nacen en 0 en la instancia ya colocada) · **§213 (un `bind` de getter puro NO es snapshot — el patrón de flanco correcto actualiza el estado dentro del flanco)** · los literales bool/string a funciones propias se pierden (usar `:keyword` + variables) · el setter cross-class de una VARIABLE lleva el valor primero (`(Class|X|SetVar :self ref :pin valor)`) · `MotionControllerComponent` = `/Script/HeadMountedDisplay.` · en CDO de componentes: `bVisible` y `{"BodyInstance":{"CollisionEnabled":...}}`.

## TODO
- [ ] 🔴 **Visor**: umbral con el sensor en la panza (zona base, sin calibrar), zumbido + pulso del IN, círculo de práctica en la página 2, esfera al terminar instrucciones, y el beam en Attracting.
- [ ] Cuando lleguen los **datos del levantamiento**: definir los valores seguros del umbral (y decidir si vuelve la calibración por usuario — la maquinaria dormida está lista).
- [ ] Modo 5 (dibujo 3D) · visual real del beam · consumidores de `OnBeatPulse`.


---

## 2026-08-27 — modo exploración: el beam VISIBLE sin trace (F5 del cierre)

La constelación se apunta **por ángulo** (las amebas no tienen colisión), pero el guión pide un **láser
visible** como el de Attracting. Dos funciones nuevas, y **cero cirugía** sobre `SetStage` / `TickMech`:

| Función | Qué hace |
|---|---|
| **`ExploreOn(On)`** | `SetActive` + `SetVisibility` de `BeamFxR` y `BeamFxL`. Enciende y apaga los dos beams sin tocar `Mode`. |
| **`AimBeams()`** | Guarda `IsValid(PawnSC)` → `AimBeamsBody`. |
| `AimBeamsBody()` | Toma los dos `MotionController*Aim`, escribe `BeamStart`/`BeamEndR` y `BeamStartL`/`BeamEndL` como `origen + forward × TraceDistance` (**sin `LineTraceByChannel`**) y llama a `DrawBeamR`/`DrawBeamL`. |

🔑 **Por qué no se tocó `TickMech`**: su cadena de `if` anidados por `Mode` es delicada, y agregarle un
modo 6 obligaba a cirugía sobre nodos nesteados. En cambio **[[BP_Constellation_SC]] llama a `AimBeams()`
desde SU propio `EventTick`** mientras `bExploring`. El beam se actualiza igual por frame, y el sensor
queda con un `Mode` de -1 (inerte) durante toda la exploración.

⚠ Consecuencia buscada: con `Mode` en -1, `BeamPress`/`BeamGrabTry` **no** se activan → el usuario no
puede agarrar por accidente una de las esferas de la melodía del vecino con el gatillo.

`ShowSignature()` se reusa tal cual para el dibujo del vecino (lo llama `BP_Constellation_SC.DrawNow`
después de `Canvas.RebuildFrom`). 🔴 **Por eso hay que mover `TP_signature_spot`**: hoy sigue arriba, al
lado de `soul_pick_6`; ahora es el atril del dibujo y va junto al panel del retrato.


---

## 2026-08-28 — `DropSignature()`: al venir al corazón viaja sola la ameba

**Pedido de Beltrán:** *"Cuando atraigo la ameba a mi corazón, el dibujo ya no debe estar. Debe acercarse
solo la ameba."*

```
(fn DropSignature ()
  (IsValid CanvasRef
    :"Is Valid"
      (DetachFromActor CanvasRef)     ; se queda donde está — NO viaja con la ameba
      (FadeTo 0.0)))                  ; y se apaga con el fundido de siempre (DrawFadeTime = 2,5 s)
```
El **detach** es la mitad importante: sin él, el dibujo acompañaba a la ameba durante los 3 s del viaje,
que es justo lo contrario de *"debe acercarse sola"*.
`FadeTo` es el mismo verbo que ya usaba `FadeDrawOut` de la constelación, y **`ShowSignatureAt` lo revierte**
con `FadeTo(1)`, así que la exploración posterior vuelve a mostrarlo sin nada extra.

### 🔴 Quién lo llama, y por qué NO se llama desde el gesto
Lo dispara **`BP_ProtoSoul_SC.ArmCarry`** (que corre en cada `StartCarry`) a través de `DropMyDraw`, pero
**sólo si el alma tiene `HasDraw = true`** — bandera que enciende `SoulPlaceDrawing` y apaga el propio
`ArmCarry`.
👉 **La guarda no es un lujo: durante Surrounding el `CanvasRef` del sensor es el dibujo VIVO del usuario.**
Si `ArmCarry` apagara el canvas sin condición, agarrar la ameba con la mano en esa etapa **borraría de la
vista el dibujo que la persona está haciendo**. La bandera distingue exactamente el caso que importa: sólo
el alma que recibió una firma anclada la suelta.

### ✅ Verificado en PIE (cero `Accessed None`)
Con `bDebugShowOnPlay` del retrato en +14 s (después de que el modo dibujo cree el canvas) y
`bDebugShareOnPlay` del picker en +23 s, todo en el mismo frame:
```
PROTO: agarrada con la DERECHA
PROTO: soltada del ancla
SENSOR: el dibujo se queda atras y se apaga - viaja sola la ameba
PICKER: enganchada por gesto con la DERECHA
RETRATO: se apaga
...  6,0 s después  →  PROTO: compartida    (3 s de viaje + 3 s de ShareHold)
```
💡 Y una corrida previa comprobó la **rama negativa**: con el retrato mostrado **antes** de que existiera el
canvas (`SENSOR: no hay canvas para anclar`), el gesto **no** imprimió la línea del drop. La guarda funciona
en los dos sentidos.

💡 Las **esferas del secuenciador ya desaparecían solas**: `HidePortrait` → `Hide` → `StopMelody` →
`VanishOrbs`. Por eso Beltrán sólo vio quedarse el dibujo.


---

## 2026-09-02 — el beam de exploración ahora TRAZA, no sólo se ve

**El síntoma**: en la constelación el hover por beam no detectaba nada. El log lo decía sin ambigüedad —
`SENSOR: beams de exploracion encendidos` aparecía, pero `BeamHitActor` nunca cambiaba.

**La causa**: `ExploreOn(On)` **sólo encendía el VFX** (`SetActive` + `SetVisibility` de `BeamFxR/L`).
El `LineTraceByChannel` vive en `TickBeamR/L`, y a esos los llama `TickBeam` **sólo cuando `Mode == 4`**
(Attracting). En la constelación el sensor está en **`Mode = -1`** — a propósito, para que `BeamPress` /
`BeamGrabTry` no dejen agarrar por accidente las esferas del vecino. Resultado: **el beam se veía pero no
trazaba**.

✅ **Arreglo mínimo, sin tocar el modo:**
- Nueva `bExploring`, que **`ExploreOn` enciende y apaga** junto con el VFX.
- `TickMech` gana un `elif`: corre `TickBeam` **si `Mode == 4` O si `bExploring`**.

🔑 **El grab sigue apagado**: `BeamPress`/`BeamGrabTry` siguen gateados por `Mode == 4`, así que en la
constelación el beam **traza y da hover, pero no agarra**. Que es exactamente lo que se quería.

⚠ Al reescribir `TickMech` hay dos trampas: los parámetros de las funciones propias **van por keyword**
(`:DT DT`) porque el pin `self` se come el primer posicional, y los getters de bools son
`Variables|Z-Estadointerno|GetTaken` / `GetMechDone` (no `Variables|Default|`). Verificado después con
`get_node_infos` que las 5 llamadas siguen apuntando a `SELF`, y barridos 22 huérfanos con el DSL vivo
idéntico.
