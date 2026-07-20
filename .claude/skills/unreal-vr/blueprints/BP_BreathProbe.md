# BP_BreathProbe — `/Game/SoulCharger/Stages/Breath/`

## Propósito
**Probe descartable** para responder UNA pregunta: ¿el mando apoyado sobre el abdomen produce una señal de respiración que se despegue del ruido de tracking?
No es la etapa Breath. Si el modelo se valida, el pipeline se copia a `BP_BreathChannel` y este BP se tira.

## Estado
# ✅ EL MECANISMO DE RESPIRACIÓN ESTÁ VALIDADO Y SINTONIZADO (test 11; re-validado ~test 25 con la caja de objetivo A/B)
> *"Suuuuper bien. Muy estable."* — con las dos manos, con aguante, con salidas y reentradas al umbral.
**Ya no se toca el modelo.** El siguiente paso NO es afinar: es **extraer** a `BP_BreathSource` (componente) exponiendo `Level` (0-1), `Phase`, `bBreathing`, `Amplitude` + dispatchers, con actores consumidores tontos. Ese era el pedido original del usuario: *"variables bastante simples que me permitan después mapearlas y multiplicarlas a lo que yo quiera"*. Este BP es **descartable** — el pipeline se copia y este se tira.
Pendiente menor: cablear `HF_BreathBuzz` (`PlayHapticEffect` + `bLoop`) cuando el usuario cree el asset a mano — reemplaza el interino `SetHapticsByValue(Frequency=0.0)`.

**Test 1 (16:50) — el modelo VALIDA.** El cubo escaló con la respiración. Datos: amplitud de respiración **~0.02** en el eje ganador (≈1.1° de inclinación), ciclos de 6-8 s, `Lin` 0.6-3.4 cm/s y `Ang` 0.7-4.5 °/s mientras respiraba, vs. 35-42 cm/s y 50-121 °/s al mover el brazo. **Los umbrales de quietud (8 / 25) están bien puestos**: hay un factor ~10 de separación.

### Los 2 bugs que reveló el test 1
1. **El escalón es indistinguible de una respiración lenta.** Al apoyar el mando en la mesa, el cambio brusco de orientación entró al band-pass. `Fast` lo siguió en 0.4 s, `Slow` en 15 s → `breath = Fast − Slow` quedó en **0.49 (13× la respiración real) y tardó 45 s en decaer**. Eso es *exactamente* el cubo achicándose lento sobre la mesa que vio el usuario. **Un band-pass no puede rechazar un escalón: un escalón contiene todas las frecuencias, incluida la banda de respiración.**
   → **Fix: reseed.** Si no está quieto o no está trackeado, `SlowV = FastV = raw` y `BreathV = 0`. El transitorio nunca entra al filtro. Bonus: `AmpV` deja de contaminarse con escalones, lo que **estabiliza la selección de eje** (en el test flip-flopeó 0→1→2→1 porque el escalón fue mayormente en Y).
2. **La velocidad del runtime se CONGELA, no se va a cero.** Sobre la mesa, `Lin` quedó clavado en **0.899491** y `Ang` en **0.178033**, idénticos a 6 decimales durante 48 s. Un piso de ruido fluctuaría; eso es un valor congelado → el mando se durmió / perdió tracking y `GetLinearVelocity` devuelve el último valor. Y congelado **pasa el test de quietud** (¡congelado es lo más quieto que hay!).
   → **Fix:** usar los **bool de retorno** de `GetLinearVelocity`/`GetAngularVelocity` (los tenía bindeados y no los usaba). `bTracked = lok AND aok` entra al umbral.

⚠ **Los dos bugs se tapaban entre sí**: el umbral se quedó en `true` **48 segundos** con el mando en la mesa.

## El modelo de señal (lo importante)
1. **Rotación, no posición.** La respiración mueve el abdomen 5-15 mm; en posición eso está a factor ~5 del jitter del tracking (1-2 mm). Pero el mando apoyado se **inclina** varios grados → un orden de magnitud mejor de SNR. (Es la razón por la que Flowborne pide que la superficie plana descanse sobre el abdomen.)
2. **Señal cruda = las 3 componentes Z de los ejes del mando** — `(Forward.Z, Right.Z, Up.Z)`. Es la tercera fila de la matriz de rotación: describe la inclinación **respecto a la gravedad**, ignora el yaw (que la respiración no mueve), y no tiene wrap de ángulos.
3. **Band-pass = FastEMA − SlowEMA.** La respiración vive en 0.1-0.3 Hz. `Slow` (tau 15s) absorbe drift de tracking y deriva postural; `Fast` (tau 0.4s) mata el jitter. La resta deja solo la oscilación, **centrada en cero por construcción → no hace falta calibrar**. Bonus: el **cruce por cero es el cambio de fase** inhala/exhala, y el tiempo entre cruces da el período (para el 4/6 y las 10 respiraciones válidas).
4. **Selección automática de eje.** Cuál eje capta la respiración depende del agarre, y hay un caso degenerado: un eje casi vertical va como el coseno → derivada cero → insensible justo donde importa. Solución: `AmpV` = EMA de |breath| por eje, y gana el de mayor amplitud. Funciona **porque el band-pass va antes**: el movimiento voluntario del brazo (0.5-5 Hz) queda fuera de banda y no ensucia la comparación.
5. **Quietud con la velocidad del runtime**, no diferencia finita: `MotionControllerUpdate|GetLinearVelocity` / `GetAngularVelocity` vienen de la IMU vía OpenXR. Umbral **absoluto** (no se calibra — ver doc §2).
6. **Umbral = quieto AND amplitud ≥ MinAmplitude.** No premia respirar bien: avisa que el sensor te lee. Es literal lo que hace Flowborne (*"The controller vibrates softly when ready to detect your breathing"*).

### Test 2 (17:08) — el grab funciona; 3 síntomas, 1 causa
`Track` funcionó (atrapó al mando dormido: `Lin` congelado en 2.19645) y el reseed funcionó (`Val=0.0` con `Lin=24`). Pero:
- **El debounce parecía roto** (activaba en 0.2 s en vez de 2 s, salía en 0.8 s en vez de 1.5 s).
- **No se sentía el háptico.**
- Los ajustes de `Gain`/`MinAmplitude`/`TauAmp` no tenían efecto.
**Causa única: el actor colocado en el nivel tenía `ActivateDelay=0, DeactivateDelay=0, HapticInterval=0, HapticAmplitude=0`** y los valores viejos de Gain/MinAmplitude/TauAmp. Los defaults del CDO **no llegan a las instancias ya colocadas** → ver gotchas. Fix: `set_properties` sobre la instancia del nivel.
⚠ Método: el cubo escalaba con la respiración **aunque `bBreathing` fuese falso** (la escala no dependía de `bBreathing`), y eso ocultó que el estado confirmado nunca se activaba. **Un feedback visual que no depende del estado que querés verificar no sirve como test de ese estado.**

### Test 2 — otros 2 hallazgos
- **Glitch al agarrar** (el cubo crece y se achica de golpe): las EMA de `LinSpeed`/`AngSpeed` arrancan en 0 → durante el tau (0.3 s) de subida, `bStill` es **true por error** mientras la mano se mueve rápido → el band-pass corre sobre datos en movimiento y `breath` pega un pico. **Fix: ataque rápido / caída lenta** — `LinSpeed = max(instantáneo, EMA)`. Detecta el movimiento en 1 frame; la vuelta a "quieto" sigue costando su tiempo (que es lo que queremos).
- **La señal estaba invertida** (inhalar achicaba). El signo depende del agarre y del eje elegido → `bInvert`. **No es un parche permanente**: cuando el prop del sensor tenga geometría definida, el agarre queda estandarizado y el signo pasa a ser una constante conocida.

### Test 3 (18:21) — la señal es excelente + rediseño de la salida
`BP 7` disparó **cada 2.0 s exactos con amplitud 0.6** → el código corría bien y **`SetHapticsByValue` SÍ funciona con OpenXR**. (Pregunta cerrada: se puede usar vibración continua.)

**La señal, un ciclo completo medido:**
```
18:22:01.0  Val=-0.055 ← mínimo      18:22:07.2  Val=+0.081 ← máximo
18:22:04.2  Val=-0.008              18:22:10.7  Val=-0.011
```
Oscilación limpísima, **período ~11 s**, pico a pico 0.13, `Amp`(Y) ~0.044 y estable. `MinAmplitude`=0.006 tiene margen de sobra. La derivada es perfectamente usable.

📐 **DATO DE DISEÑO: la inhalación del usuario dura ~6.5 s y la exhalación ~4.7 s** — al revés del 4/6 que asume §4.1 del doc (4 inhala / 6 exhala). Relevante para la decisión abierta §13 (4/6 vs 5/5).

### Rediseño: la escala es un INTEGRADOR POR TIEMPO, no una función de la inclinación
**El problema conceptual:** mapear escala = f(inclinación) hace que el tamaño dependa de **cuánto se te mueve la panza**, que varía por persona, contextura y agarre. Ninguna constante de ganancia arregla eso.
**La solución:** usar **solo el SIGNO de la derivada** (inhalando / exhalando) e integrar contra el reloj:
```
si inhalando:  Level += DT / RiseTime     (llega a 1.0 en RiseTime segundos)
si exhalando:  Level -= DT / FallTime
Level = clamp(Level, 0, 1)  →  escala = lerp(ScaleMin, ScaleMax, Level)
```
**Es independiente de la amplitud → independiente de la persona.** La amplitud sigue usándose, pero solo para el umbral (¿hay respiración?) y para el threshold de fase, no para la escala.
- **Fase por Schmitt trigger** sobre la derivada suavizada: pasa a `inhalando` si `dV > +Amp*PhaseThreshFrac`, a `exhalando` si `dV < -Amp*PhaseThreshFrac`, y **entre medio mantiene el estado**. Sin zona muerta que tunear, y no parpadea en los puntos de retorno (donde dV≈0).
- ⚠ **La derivada se congela (`dV=0`) cuando no hay quietud/tracking.** Si no, el reseed (`Val` salta a 0.0 de golpe) daría `dV ≈ 4.0/s` → dispararía "inhalando" falsamente. `PrevBreathValue` **sí** se actualiza siempre, para que al volver no haya un salto acumulado.
- **Base = `ScaleMin`** (el mínimo de la exhalación), no el punto medio. Fuera del umbral, `Level` interpola a 0 con `ReturnTau` → vuelve suave al base. Un solo camino para todo: ya no hay `RestScale`/`CurrentScale`/`ScaleTau`/`Gain`.

💡 **Insight de diseño que sale gratis:** si `RiseTime`/`FallTime` = el ritmo guiado, **el cubo se convierte en el maestro del ritmo**: llegar al máximo justo al terminar de inhalar = vas en sincro; quedarte saturado = inhalaste de más; no llegar = de menos. Con 4/6 sería exacto. Hoy está en 5/5 por pedido del usuario.

### Test 4 (19:0x) — 3 bugs, y el más importante es conceptual
1. **`Accessed None ... GetPlayerController` en `StopHaptics`.** En `EndPlay` el PlayerController **ya no existe**. Fix: `IsValid` antes de usarlo. (Regla: nada de `GetPlayerController` sin guarda en EndPlay/Destroyed.)
2. **El cubo saltaba de chico a grande al empezar.** El componente `Box` se creó con `dimensions: 30` → su `RelativeScale3D` autoral es **0.3** (el cubo base de UE mide 100 cm). El código lo mandaba a `lerp(ScaleMin=1.0, …)` → salto instantáneo de 0.3 a 1.0 = **3.3×**. Fix: capturar `BaseScale` = `Class|SceneComponent|GetRelativeScale3D(Box)` en BeginPlay y usar **`ScaleMin`/`ScaleMax` como MULTIPLICADORES** de esa escala. Ahora 1.0 = el tamaño con el que lo dibujaste. **Diagnóstico del usuario, correcto.**
3. **🔴 EL IMPORTANTE — aguantar la respiración hacía que el nivel se moviera solo.** Al quedarse inflado y quieto, el cubo empezaba a achicarse; al aguantar exhalado, a crecer.
   **Causa: un band-pass NO PUEDE representar un nivel sostenido.** Si mantenés la panza inflada, `Slow` alcanza a `Fast` con `TauSlow` y `Val` decae hacia 0 **por construcción del filtro**. Esa decadencia tiene derivada negativa → el detector lo leía como "exhalando". Es el mismo agujero del escalón (test 1), por el otro lado: el band-pass ve *cambios*, y un sostenido no es un cambio.
   **Números:** decadencia ≈ `Val_pico / TauSlow` = 0.08/15 = **0.0053/s**, contra un umbral de fase de `Amp*0.15` = **0.0066/s**. Estaba solo un 25% por debajo → cualquier ruido lo cruzaba. Por eso fallaba *a veces*.
   **Fix doble:**
   - **Fase de 3 estados** (`Phase` int: +1 inhalando / −1 exhalando / **0 = aguantando**). Entre los dos gatillos, `Level` **se congela** en vez de seguir integrando. Es lo que pidió el usuario: "si aguantamos se mantiene donde estamos".
   - **`TauSlow` 15 → 30**, que baja la decadencia a **0.0027/s** → 2.4× de margen contra el umbral. No cuesta nada: el corte del pasa-altos queda en 0.0053 Hz y la respiración vive en 0.09 Hz (17× arriba, sin atenuación), y la deriva postural es de escala de minutos.

### Test 5 (19:20) — 🔴 DERIVAR AMPLIFICA EL RUIDO
Síntoma: "se enreda entre inhalación y exhalación". El log lo confirma — la fase cambiaba **cada 1.5-2 s** con una respiración de 11 s:
```
19:20:45.9 Fase=-1 dV=-0.060 | 19:20:46.5 Fase=+1 dV=+0.022 | 19:20:49.0 Fase=-1 dV=-0.019 | 19:20:50.6 Fase=+1 dV=+0.0066
```
**Causa:** una derivada multiplica cada componente de frecuencia por su ω → el jitter del tracking a ~2 Hz sale amplificado **~20× más** que la respiración a 0.09 Hz. Con `DerivTau=0.25` casi no había suavizado: los cambios de fase ocurrían con `dV` de 0.0066 / 0.0046 / 0.0031 contra un `thr` de 0.0029. **Eso era ruido cruzando el umbral, no respiración.**
**Fix (3 partes que se refuerzan):**
1. **`DerivTau` 0.25 → 1.2.** A 2 Hz la ganancia baja de 0.30 a 0.066 (4.5× menos ruido) mientras la respiración a 0.09 Hz solo cae de 0.99 a 0.83. Costo: ~1 s de retraso en detectar el cambio de fase — aceptable contra un cuarto de ciclo de 2.75 s.
2. **`PhaseThreshFrac` 0.15 → 0.35.** `thr` pasa de ~7% a ~15% del pico de `dV` (que es 0.05). Rechaza los temblores sin perder la respiración real.
3. **Sticky de 2 estados (pedido del usuario, y además ayuda):** se elimina el estado 0. Para invertir hay que cruzar el umbral **contrario** → los temblores chicos no pueden dar vuelta la fase.

### El estado "aguantar": FREEZE ❌ → CONTINUAR ✅ (spec del usuario)
> "Si estoy inhalando y paso a aguantar, el cubo debe seguir creciendo. Si estoy exhalando y aguanto, debe seguir bajando. La exhalación continúa como su estado anterior. Si ya cambiamos totalmente de estado, se invierte."

Eso es **exactamente un Schmitt trigger de 2 estados**: `Phase` solo toma +1 / −1, y **si `dV` está entre los dos gatillos NO se escribe nada → conserva el estado anterior** y `Level` sigue integrando en la misma dirección.
⚠ Esto es lo que había en el test 3 y falló — pero falló **solo porque `TauSlow=15`** hacía que la decadencia del band-pass (0.0053/s) casi alcanzara el umbral (0.0066/s) y diera vuelta la fase sola. Con `TauSlow=30` la decadencia es 0.0027/s contra un `thr` de ~0.0077/s → **2.8× de margen**. El sticky ahora sí se sostiene. (`Phase` se inicializa en −1 en BeginPlay.)

### Test 6 (11:10, 178 muestras / 94 s) — el sticky FUNCIONÓ, y por eso apareció su costo
**Lo que se arregló:** la fase ya **no oscila**. Mantiene el signo 2-9 s, período ~8.6 s. El bug del test 5 está muerto.
**Las 4 quejas del usuario eran UN problema con cuatro caras**, y las tres primeras salen del mismo detector:

1. **Retardo al cambiar de fase.** `DerivTau=1.2` **es** ~1.2 s de retraso. Las inhalaciones medidas duraron **3.3 s de promedio** → el cambio llega cuando ya pasó **más de un tercio** de la inhalación. **No hay tuning que lo salve**: bajar `DerivTau` devuelve el flip-flopping. El detector no puede ser rápido y estable a la vez.
2. **🔴 "Se queda pegado en pequeño" = el detector se vuelve SORDO (lazo de realimentación).** Entre 62.3 s y 71.8 s la fase quedó clavada en −1 durante **9.5 s**. `Amp` había subido a 0.030 → `thr = 0.35×Amp = 0.0105` → **más alto que el `dV` que alcanza una inhalación real** → nada podía cruzarlo → y como es sticky, nada lo sacaba. Movimiento infla `Amp` → sube `thr` → sordo → pegado.
3. **Bug de unidades detrás de la sordera:** `thr = PhaseThreshFrac × Amp` compara **una fracción de amplitud de señal** contra `DBreath`, que es una **derivada** (1/s). **Dimensionalmente inconsistente.** Solo funcionaba por coincidencia numérica del período: para un seno, `dV_max = Aω`. Si el usuario **respira más lento, ω baja, `dV_max` baja, pero `thr` no** → sordera garantizada. El detector castigaba justo lo que la obra quiere inducir.
4. **El reset al reentrar NO existía, confirmado:** en el corte de 71.8 s → 76.0 s la fase se mantuvo en −1 y salió del otro lado con el estado viejo intacto.

📐 **Dato de diseño:** `RiseTime`=5 s pero las inhalaciones reales duran 3.3 s → los `Lvl` al cambiar de fase fueron 0.47 / 0.69 / 0.94 / 0.88 / 0.59 / 0.50 / 0.28 → **el cubo casi nunca llega a los extremos**. Eso es la obra funcionando como se pidió (llegar al máximo a los 5 s induce respiración lenta), no un bug. Bajar `RiseTime` a ~3.5 haría todo más "instantáneo" a costa de dejar de empujar. **Decisión abierta del usuario.**

### Rediseño 2: DERIVADA + UMBRAL ❌ → PUNTOS DE RETORNO (ZigZag) ✅
Se deja de derivar. Se detecta el **punto de retorno** sobre la señal filtrada directamente:
```
Delta = max(Excursion, MinExcursion) * TurnFrac
si Phase>0:  RunMax = max(RunMax, B)
             si B < RunMax - Delta:  Excursion += (RunMax-RunMin - Excursion)*0.3 ; Phase=-1 ; RunMin=B
si Phase<0:  RunMin = min(RunMin, B)
             si B > RunMin + Delta:  Excursion += (RunMax-RunMin - Excursion)*0.3 ; Phase=+1 ; RunMax=B
```
Por qué es mejor, punto por punto contra los 4 bugs de arriba:
- **Sin derivada → sin retardo de derivada.** Reacciona apenas revertiste `Delta`.
- **`Delta` está en unidades de SEÑAL comparado contra SEÑAL** → dimensionalmente consistente → **independiente del período**. Respirar lento ya no ensordece nada. Mata el bug 3, y con él el 2.
- **`Excursion` se mide entre puntos de retorno reales** (pico a pico de una respiración de verdad), no como EMA de `|BreathV|` que el movimiento contamina. Mata el lazo de realimentación.
- **Aguantar sigue funcionando**: sin punto de retorno no hay cambio de fase. (Límite: el band-pass decae con `TauSlow=30` a ~0.00067/s desde un pico de 0.02; con `Delta≈0.004` el aguante se lee bien hasta **~6.7 s**. Más que eso es físicamente indetectable con un pasa-altos — no es pereza.)
- **Reset al reentrar**: en el `else` del reseed (no quieto / no trackeado) ahora se hace `RunMax=RunMin=0`, `Phase=-1`. `Level` **no** se resetea de golpe — baja integrando y luego interpola con `ReturnTau`, que es el retorno suave que ya se pidió.

⚠ **Límite honesto:** cerca de un punto de retorno la señal casi no se mueve, así que **ningún** detector robusto es instantáneo. Estimado: de ~1.2-1.5 s a **~0.6-0.9 s**. Es el piso físico.
⚠ `DBreath`/`DerivTau`/`PhaseThreshFrac` **quedan calculándose pero ya NO deciden la fase** — se dejan por diagnóstico. Si el ZigZag convence, borrarlas.

### Test 6 — el háptico: la causa real (ver gotchas)
No era la intensidad ni la calibración. `SetHapticsByValue` **clampea la frecuencia a [0,1]** y OpenXR la pasa **cruda como Hz** → el rango completo alcanzable es **0-1 Hz**, y teníamos `1.0` = **un pulso por segundo**, el peor valor posible. Interino aplicado: **`Frequency = 0.0`** = `XR_FREQUENCY_UNSPECIFIED` → el runtime elige su zumbido nativo continuo.
**Fix definitivo (pendiente, idea del usuario y es mejor):** un `HapticFeedbackEffect_Curve` **escapa del clamp** (escribe `Values.Frequency` directo, sin pasar por el constructor) → frecuencia real en Hz + `bLoop` → una llamada al entrar y `StopHapticEffect` al salir, en vez de por tick. El asset hay que crearlo **a mano** (no hereda de `UDataAsset`).

### Test 7 (3 pruebas, la última con mano IZQUIERDA) — ✅ el ZigZag funciona
> *"Funciona muuuy bien ahora."* La mano izquierda funciona → **cierra la pregunta de las dos manos**.
Único defecto: **al confirmar el umbral empezaba a subir instantáneamente aunque el usuario estuviera aguantando** (pruebas 1 y 3).

**Dos causas, ambas de la activación:**
1. **`MinExcursion` estaba ~10× bajo.** Se puso 0.012 confundiendo **amplitud** (`AmpV` ≈ 0.044 = promedio de |B|) con **pico a pico** (medido **0.13** en el test 3). Con `Excursion`=0 al activar, `Delta` cae a su piso = `0.012 × 0.15` = **0.0018** → eso es **ruido de tracking**, y el primer "punto de retorno" detectado era basura. → **`MinExcursion` 0.012 → 0.05** (`Delta` piso = 0.0075).
2. **🔴 Conceptual: al activar, el sistema NO SABE si inhalas o exhalas, y lo obligábamos a apostar.** `Phase=-1` en el reset es una apuesta, no un dato.

**Fix: `Phase = 0` = "todavía no lo sé" (≠ el estado 0 "aguantando" del test 4, que se descartó).**
- Reset (no quieto / no trackeado) → `Phase = 0`, `RunMax = RunMin = 0`.
- Con `Phase = 0` el nivel **no integra** — el bloque de nivel ya lo soportaba sin tocarlo: `(if (> Phase 0)) (elif (< Phase 0))` sin `else` → 0 no entra a ninguna rama y `Level` se congela. **El estado neutro salió gratis.**
- Con `Phase = 0` se rastrean **ambos** extremos (`>= 0` para RunMax, `<= 0` para RunMin) y **el primer punto de retorno real decide la dirección**. Después vuelve a ser sticky de 2 estados.
- ⚠ El sticky de 2 estados **sigue vigente durante la respiración** (spec del usuario: aguantar continúa el estado anterior). `Phase=0` **solo** existe entre el reset y el primer retorno detectado.

### Test 8 — el aguante al MÁXIMO (el pasa-altos otra vez) + vuelta al base
> *"Super bien, mejora."* Dos detalles, ambos resueltos **sin tocar el grafo** — solo valores.

**1. Aguantar inflado al máximo empezaba a bajar (a veces).** Es **el mismo agujero físico del test 4**, no una regresión: un pasa-altos **no puede representar un nivel sostenido**; con `raw` constante, `B` decae hacia 0 con `TauSlow`. Volvió porque ahora el usuario aguanta **más rato** (llegar al máximo toma `RiseTime`=5 s + la inhalación previa).
Números: pico ≈ 0.065, decaimiento = pico/`TauSlow` = 0.065/30 = **0.0022/s**; umbral de retorno = `TurnFrac × Excursion` = 0.15 × 0.13 = **0.0195** → aguante máximo = `−TauSlow·ln(1 − 0.0195/0.065)` = **10.7 s**. Quedaba **justo en el borde** → por eso fallaba *a veces*.
→ **`TauSlow` 30 → 90** = **~32 s de aguante**. Costo real: **ninguno**. La esquina del pasa-altos queda en 0.0018 Hz contra una respiración de ~0.11 Hz (**60× arriba**, sin atenuación), y la deriva postural es de escala de minutos. El reseed re-centra el filtro en cada movimiento, así que no se acumula nada.
💡 **Si 32 s no bastara**, el fix exacto (no probado) es **decaer `RunMax` con la misma ley que el filtro** (`RunMax -= RunMax*DT/TauSlow` mientras `Phase>0`): cancela el decaimiento analíticamente, y una exhalación real —que es mucho más rápida— igual dispara. Se descartó por ahora: 32 s ya excede cualquier aguante en una obra contemplativa, y `TauSlow` es una palanca de un solo número ya probada.

**2. La vuelta al tamaño base era muy brusca.** `ReturnTau` = 0.6 → ~63% en 0.6 s, prácticamente terminado en 1.8 s. → **`ReturnTau` 0.6 → 2.0** (~63% en 2 s, ~95% en 6 s).

### Test 9 — ❌ REVERTIDO: `bPhaseConfirmed` (exigir una reversión completa) fue PEOR
Intento: separar dirección provisional de fase confirmada, exigiendo una reversión real de `Delta` contra un extremo observado antes de mover el nivel. Razonamiento: `RunMax=RunMin=0` en el reset son extremos **inventados**, y `B > RunMin + Delta` los trataba como un valle real → "una rampa no es un punto de retorno".
**Veredicto del usuario: *"funciona mucho peor, le costó mucho tomar mi respiración y se equivocó en las direcciones."* Revertido.**

**Por qué falló (el razonamiento era correcto y la solución igual estaba mal):**
- **Sordera de medio ciclo.** Si entrabas a media inhalación, confirmar exigía **esperar el pico** → se perdía la inhalación **entera** (nivel congelado todo ese rato). Cambié un arranque falso por medio ciclo de sordera: peor negocio.
- **Direcciones al azar.** Con `RunMax`/`RunMin` sembrados en 0 y ruido alrededor, el primer extremo lo fijaba el ruido → la reversión "confirmada" salía en la dirección equivocada.

📌 **Lección de método:** un diagnóstico correcto no valida el fix. El diagnóstico ("el valle es falso") era cierto; la conclusión ("hay que exigir una reversión") no se seguía. **El problema real era otro: en el instante de entrar, `B` no es respiración — es el transitorio del reseed.** No había que endurecer el detector, había que **no darle datos sucios**.

### Test 10 — VENTANA DE ARMADO (idea del usuario) ✅
> *"Quizás la forma de arreglarlo es que cada vez que entremos al umbral, se tome medio segundo antes de reconocer si el usuario está inhalando o exhalando."*

Detector = **el del test 8, sin cambios** (el que funcionaba). Se agrega solo una ventana de armado antes de dejarlo mirar:
```
Reset (no quieto / no trackeado):  RunMax = RunMin = 0 ; Phase = 0 ; ArmTimer = 0
Cada frame quieto:
  si ArmTimer < ArmDelay:   ArmTimer += DT ; RunMax = RunMin = B ; Phase = 0   ; ← ventana: nivel congelado, extremos PEGADOS a B
  si no:                    ...detector ZigZag normal del test 8...
```
**Por qué funciona, y por qué NO es lo mismo que el test 9:** al fijar `RunMax = RunMin = B` en cada frame de la ventana, **no se acumula ningún extremo falso** y el filtro se asienta. Al terminar los 0.5 s, `RunMax=RunMin=B` es el **nivel real** de la señal, no el 0 artificial del reseed. Desde ahí, que `B` suba `Delta` **sí significa que estás inhalando** — la lógica simple da la respuesta correcta porque por fin recibe datos limpios.
**La ventana no reemplaza al detector: le entrega datos limpios.** `Phase=0` durante la ventana congela el nivel gratis (el bloque de nivel no tiene `else` para el 0).
Debug: `Cf=` → **`Arm=`** (el timer de armado) en el `BP 6`. `bPhaseConfirmed` **eliminada** del BP.

### Test 11 (558 muestras) — 🔴 LA ESPIRAL DE LA MUERTE DE `Excursion` (la causa de "a veces bien, a veces mal")
Datos: **`Exc` va de 0.0023 a 0.1304 (factor 57)**, `Dlt` de 0.0075 (piso) a 0.0196. Tramo delator, segundos 451-454:
```
451,19  1->-1  Lvl=0,95  Exc=0,0471  Dlt=0,0075
452,20  -1->1  Lvl=0,79  Exc=0,0370  Dlt=0,0075
452,70  1->-1  Lvl=0,77  Exc=0,0321  Dlt=0,0075
453,70  -1->1  Lvl=0,73  Exc=0,0322  Dlt=0,0075
```
**4 cambios de fase en 2.5 s con `Dlt` clavado en el piso** = flip-flopping de vuelta.

**Mecanismo — lazo de realimentación positiva:** giro espurio → mide una excursión chica → `Excursion` baja → `Delta` baja → **más sensible** → más giros espurios → `Excursion` baja más. **No puede salir sola**: cada giro falso "confirma" que las respiraciones son chiquitas.
📌 Es **la misma clase de bug que la sordera de `Amp` del test 6** —un lazo a través del umbral adaptativo— pero **al revés**: en vez de sordo, histérico. **Todo umbral adaptativo alimentado por su propia salida es sospechoso por defecto.**

**Fix: `Excursion` con ATAQUE RÁPIDO / CAÍDA LENTA** (el mismo truco que ya se usa para `LinSpeed` en este BP):
```
alpha = (medido > Excursion) ? ExcRiseAlpha(0.4) : ExcFallAlpha(0.05)
Excursion += (medido - Excursion) * alpha
```
Un giro espurio chico **apenas la mueve** (0.05); una respiración real grande **la restablece de inmediato** (0.4). Rompe la espiral. Además **`MinExcursion` 0.05 → 0.07** (piso de `Delta` 0.0075 → 0.0105).

### Test 11 — el delay al exhalar desde el máximo (pregunta del usuario) — DIAGNOSTICADO, no arreglado
> *"cuando llega al máximo inhalando y aguantando, si exhalo, hay un delay antes de que empiece a bajar"* + *"funciona mejor con mi respiración natural que con la de 5 segundos"*.

**Las dos observaciones son el mismo hecho.** El giro se detecta cuando `B` cae `Delta` bajo `RunMax`. Cerca de un pico la señal es **plana**, así que eso toma **~1.1 s** (con pico 0.065, `Delta` 0.0195, ω≈0.67: `0.065(1−cos(ωt))=0.0195` → t=1.1 s).
**Ese ~1 s existe SIEMPRE. Solo se VE cuando `Level` está saturado en 1.0**, porque ahí no se mueve nada. Con respiración natural nunca satura (inhalación ~3.3 s vs `RiseTime` 5 → llega a ~66%), así que durante el retardo el cubo **sigue creciendo** y se lee como la cola de la inhalación, no como delay. En el log: los `Lvl` al girar incluyen varios **1.00** exactos.
⚠ **El aguante y el giro rápido están en CONFLICTO DIRECTO, ambos vía `Delta`**: aguantar quiere `Delta` grande (para que el decaimiento del pasa-altos no dispare), girar rápido lo quiere chico. Y `t ∝ √Delta` → bajar `Delta` rinde poco (−20% de `Delta` = −11% de tiempo).
💡 **El fix que DISUELVE el conflicto (pendiente):** decaer `RunMax`/`RunMin` con la misma ley del filtro (`RunMax -= RunMax*DT/TauSlow`). Durante un aguante, `B` y `RunMax` decaen **igual** → su diferencia no cambia → **nunca dispara, para cualquier duración**. Una exhalación real cae ~65× más rápido que el decaimiento (0.047/s vs 0.0007/s) → dispara igual. Con eso `Delta` se elige **solo por ruido** (~0.005-0.008) → detección en ~0.6-0.7 s **sin perder aguante**. No se aplicó aún para no cambiar dos cosas a la vez.

### Test 11 — sospecha del usuario: el HÁPTICO CONTAMINA LA IMU
> *"Probé nuevamente Flowborne, y la amplitud del háptico es super baja. Y nosotros la tenemos super alta. Esa vibración quizás interfiere."*

**Hipótesis fuerte y nunca verificada** (está en las preguntas abiertas desde el test 2). Lo grave: el háptico **solo vibra cuando `bBreathing` es true** — o sea, exactamente cuando medimos la respiración con la IMU **de ese mismo mando**. Si contamina, **se contamina a sí mismo**, y solo dentro del umbral → explicaría por qué se degrada *después* de activarse.
→ **`HapticAmplitude` 0.5 → 0.25.** Flowborne usa amplitud baja; puede no ser estética sino necesidad. **Pendiente de verificar de verdad:** comparar `Amp`/`Exc`/flips con `HapticAmplitude=0` vs 0.25.

### Test 12 (886 muestras @ 0.1 s) — 🔴 LA INVERSIÓN: el eje activo salta y `bInvert` es un signo GLOBAL
> *"En la última tanda se desincronizó e invirtió. Empezó a achicarse cuando inhalo y a agrandarse cuando exhalo."*

**Confirmado con datos. El eje activo saltaba en plena respiración, con señal buena:**
```
t=441,21  eje 1 -> 2   B=-0.0257  Amp=0.0268  Exc=0.1068  Lvl=0.15
t=445,20  eje 2 -> 1   B=+0.0254  Amp=0.0195  Exc=0.1055  Lvl=0.25
t=449,40  eje 1 -> 0   B=+0.0210  Amp=0.0171  Exc=0.0993  Lvl=0.54
t=462,20  eje 0 -> 1   B=+0.0214  Amp=0.0239  Exc=0.0902  Lvl=0.66
```
En t=449 se quedó en el **eje 0 durante 13 s** → esa es la "última tanda" invertida. (Los saltos de t=374-379 son inofensivos: `Amp`≈0, es el asentamiento.)

**Mecanismo: `bInvert` es UN SOLO SIGNO GLOBAL, pero el signo correcto DEPENDE DEL EJE ACTIVO.** `Forward.Z`, `Right.Z` y `Up.Z` tienen convenciones distintas respecto del abdomen. Con el eje 1 el signo es correcto; con el eje 0 queda al revés → **inhalar achica**. Y como el eje se queda ahí, **la inversión PERSISTE** (no es un glitch de un frame). Además, cada cambio de eje hace que `B` **salte discontinuamente** → giros espurios.
📌 Esto estaba en el TODO **desde el test 1** (*"si el eje sigue flip-flopeando, agregar histéresis ~25%"*) y se pateó 11 tests porque nunca lo habíamos visto morder. **Un TODO de "por si acaso" que resultó ser la causa raíz.**

**Fix (2 partes):**
1. **Histéresis `AxisHystFrac`(0.3):** un eje retador necesita superar al **titular** por 30%, no por un pelo. Sin esto, dos ejes con amplitud parecida se turnan el trono cada pocos segundos.
2. **Re-armado al cambiar de eje:** si el eje cambia, `ArmTimer=0`, `Phase=0`, `RunMax=RunMin=0` + `BP 7: CAMBIO DE EJE`. Un cambio de eje **es una recalibración**, y el salto de `B` no debe leerse como respiración. Reusa la ventana de armado del test 10.
Variable nueva `PrevAxis` para detectar el cambio (⚠ no se puede comparar contra un `bind` del getter: los nodos puros **se reevalúan por consumidor** y devolverían el valor YA actualizado).

⚠ **La histéresis NO arregla el signo, solo la estabilidad.** Si el eje cambia legítimamente (otro agarre), el signo puede seguir mal. **La solución de fondo es el prop del sensor con geometría definida**: estandariza el agarre → el eje ganador y su signo pasan a ser **constantes conocidas**, y toda esta maquinaria (selección automática + histéresis + `bInvert`) desaparece. Ver "señal 3× más débil" abajo — apunta al mismo lugar.

### Test 12 — 📐 la señal varía 3× entre sesiones (problema mayor, sin resolver)
`Exc` máximo: **0.0395** en este test vs **0.13** en el test 11 vs **pico a pico 0.13** en el test 3. **La fuerza de la señal cambia por un factor ~3 entre sesiones**, presumiblemente por agarre/posición del sensor.
🔴 **Esto es más grave que cualquier ajuste fino**: significa que una calibración que sirve hoy puede no servir mañana, y que todos los pisos absolutos (`MinExcursion`, `MinAmplitude`) son apuestas. Refuerza que **el prop con geometría definida es parte del mecanismo, no decoración**.

### Test 12 — el rebote al final de la exhalación (diagnosticado, NO arreglado)
> *"La aguantada al final de exhalación no la reconoce. Apenas llega al mínimo empieza a subir."* (El aguante al final de la INHALACIÓN sí funciona.)

**El decaimiento del filtro predice lo CONTRARIO a lo observado** → no es el filtro. En ese test `B` era **siempre positiva** (0.045 a 0.10, nunca cruza cero, por el offset que deja `TauSlow=90`), así que el decaimiento la empuja **hacia abajo en ambos extremos**: en el pico eso va *hacia* el disparo de exhalación (~9.5 s), en el valle va *en contra* del disparo de inhalación. O sea que el decaimiento haría fallar el aguante **arriba**, no abajo.
**Hipótesis viva: es FISIOLÓGICO.** Al terminar de exhalar y aguantar, dejas de apretar y **la panza rebota hacia afuera** — movimiento real en dirección de inhalación. Al final de la inhalación no hay rebote (aguantar ahí es esfuerzo muscular sostenido). **La asimetría está en el cuerpo, no en el código.** Con `Delta` en el piso (0.0105) un rebote de ~0.01 queda **justo en el borde**.
Candidatos, **opuestos entre sí — hay que medir la forma del rebote antes de elegir**: (a) si el rebote es **grande pero breve**, exigir que el giro se **sostenga ~0.3 s** (una inhalación real sigue subiendo, un rebote se detiene) → no cuesta velocidad; (b) si es **lento y sostenido**, subir el piso de `Delta` → cuesta velocidad. `DebugInterval` bajado a **0.1** para poder verlo.

### Test 13 — 🔴🔴 EL PEOR HASTA AHORA: `Amp` medía la DERIVA, no la respiración (hallado con Fable)
> *"Funcionó bastante bien un rato, luego ya dejó de tomármelo correctamente y no logré volver a hacerlo funcionar."*

**La aritmética, que no tiene vuelta:** `AmpV = EMA(|BreathV|)`. Si `B` tiene un **offset DC mayor que la oscilación**, el valor absoluto **no cancela nada** y el promedio **ES el offset**. La respiración ni participa.

**Verificado en el log, por bloques de 8 s (`Amp_esperado` = 0.32 × pico-a-pico):**
```
i=1280  picoapico=0.1082  centroDC=0.0065  Amp_real=0.0397  esperado=0.0346  ratio= 1.15x  ← control: sin offset, Amp mide bien
i=1440  picoapico=0.0214  centroDC=0.0528  Amp_real=0.0523  esperado=0.0069  ratio= 7.63x
i=1520  picoapico=0.0173  centroDC=0.0462  Amp_real=0.0462  esperado=0.0055  ratio= 8.34x  ← Amp == centroDC a 4 decimales
```
**`Amp_real` = `centroDC` exacto.** El bloque i=1280 (offset≈0 → ratio 1.15) es el **control que prueba el mecanismo**.

**Las 3 consecuencias encadenan TODO el síntoma:**
1. **🔴 Sordo, y te dice que te lee.** `Amplitude`(0.046, puro offset) ≫ `MinAmplitude`(0.003) → `RESP=true` + háptico vibrando, mientras la oscilación real colapsaba de 0.108 a **0.017** pico a pico. **El usuario nunca recibió la señal de reacomodar el mando** → *"no logré volver a hacerlo funcionar"*. **Un umbral que no puede bajar nunca es un umbral roto**, aunque el detector esté perfecto.
2. **Ciego, literalmente.** `Dlt` clavado en 0.0105 (piso `MinExcursion` 0.07×0.15) contra una semi-amplitud real de **0.0086** → **el umbral de giro era MAYOR que media respiración entera**. Ningún giro podía dispararse. No es que costara: era **imposible**.
3. **La selección de eje comparaba offsets, no oscilaciones** → elegía el eje que más deriva, no el que mejor lee.

**🔴 Causa de la causa: `TauSlow` 30 → 90 (test 8) lo creó.** Con tau 90 el `SlowEMA` casi no se mueve → cualquier deriva postural deja un offset DC que **persiste 3× más**. Se arregló el aguante y se creó esta ceguera. **Lección: subir un tau nunca es gratis — mueve el problema, no lo borra.**

**Fix: centrar SOLO el camino de amplitud/eje, NO el ZigZag.**
```
MidV += (BreathV - MidV) * clamp(DT/TauMid)     ; TauMid=10, solo quieto+trackeado; reseed → 0
centered = BreathV - MidV
AmpV += (|centered| - AmpV) * clamp(DT/TauAmp)  ; ahora mide OSCILACIÓN
BreathValue = centered[ActiveAxis] * sign        ; el ZigZag también usa la centrada
```
⚠ **`TauSlow`=90 NO se toca** — es lo que sostiene el aguante de 32 s (test 8). El problema no era el pasa-altos, era **medir amplitud sobre una señal descentrada**.
También: **`MinAmplitude` 0.003 → 0.006** (para que `RESP` pueda apagarse de verdad cuando la señal muere) y **`MinExcursion` 0.07 → 0.03** (el piso estaba calibrado para una señal de 0.13 pp y cegaba a las débiles).
💡 **La recuperación es el punto:** con `Amp` centrada, cuando la señal muere `RESP` se apaga → el háptico se corta → **el usuario sabe que tiene que reacomodar el mando**. Ese lazo de recuperación existía y estaba cegado.

**Descartado con evidencia (por Fable):** la espiral de `Excursion` (ya no decide nada: `Dlt` en el piso todo el tramo); eje trabado por histéresis (los `BP 7` dispararon bien); fase atascada (21 transiciones −1→+1 en el log).

### Test 14 — ❌ ROMPÍ EL AGUANTE al centrar TAMBIÉN el ZigZag (error de ejecución, no de diseño)
Fable dijo **explícitamente**: *"Centrar SOLO el camino de amplitud/eje. **No tocar `B` del ZigZag** — tau 90 es lo que sostiene el aguante de 32 s."* Y se centraron **las dos cosas**: `BreathValue` (la entrada del detector) pasó a usar `_centered`.

**Consecuencia aritmética:** centrar con `TauMid`=10 **es** un pasa-altos de tau 10 sobre el detector. El aguante dependía de tau **90**. Aguantando: la señal centrada decae a **0.003/s** contra `Delta`=0.0067 → **giro falso a los 2.5 s de aguantar**. El aguante bajó de **32 s a 2.5 s**. Por eso *"no logré sincronizarlo bien"*: el detector se daba vuelta solo apenas se sostenía.
Evidencia: fases de **0.76 / 1.10 / 1.43 / 1.67 s** mezcladas con las reales (media 3.84 s).

**Fix: `BreathValue` (ZigZag) usa `_breathv` SIN centrar; `AmpV` usa `_centered`.** Dos caminos, dos filtros, a propósito:
| Camino | Señal | Por qué |
|---|---|---|
| **ZigZag / `BreathValue`** | `BreathV` **sin centrar** (tau 90) | el aguante necesita que la señal NO decaiga → tau largo |
| **`AmpV` / selección de eje / umbral** | `BreathV − MidV` (tau 10) | medir amplitud exige quitar el DC → tau corto |

📌 **La lección:** el centrado y el aguante quieren **taus opuestos**. Un solo filtro no puede servir a los dos. Intentar centrar todo con un tau destruye el otro requisito **en silencio** — compila igual, se ve igual, y falla en el visor.
📌 **Lección de método:** el subagente dio la advertencia exacta y se ignoró al implementar. **Cuando un diagnóstico viene con un "no toques X", ese "no toques" es parte del fix, no un comentario al margen.**

Lo que SÍ quedó bien del test 13 (verificado en el log): **`B` ahora cruza cero** (−0.045 a +0.064) y `Amp` centrada promedia 0.024 → `MinAmplitude`=0.006 **no** es lo que frena la entrada.

### Test 14 — la barrera de dwell propuesta por el usuario (PENDIENTE, no aplicada)
> *"A veces reconoce un mínimo de inhalación involuntaria que duró muy poco, y se queda pegado agrandándose. El hold que sucede al aguantar viniendo de una inhalación o exhalación, que solo se active si venimos de estar 1 segundo dentro de ese estado."*

**Diagnóstico del usuario: correcto y estructural.** Con la fase pegajosa, **un giro espurio de medio segundo se convierte en integración sostenida indefinida** — el nivel se va a tope como si aguantaras. El sticky es lo que hace posible el aguante (spec del usuario, test 5) y **este es su costo**: no distingue "aguanto tras inhalar de verdad" de "un tic me cambió la fase y nada me la saca".
**No aplicada todavía a propósito:** el test 14 tenía una causa introducida por nosotros (arriba) que produce exactamente ese síntoma. **Primero sacar la causa propia, después medir si la barrera sigue haciendo falta.** Si persisten fases <1 s con el ZigZag sin centrar, implementar: `PhaseTimer` (tiempo desde el último cambio de fase) y que la integración sostenida exija `PhaseTimer >= HoldQualifyTime`(1.0).

### Test 15 — 🔴 EL EJE VIVÍA CAMBIANDO: la histéresis del 30% no alcanza con Amps centradas chicas y parecidas
> *"Me tomó mucho rato hasta que reconoció que tenía el control en el estómago, y luego fue muy difícil sincronizarlo."*

**Datos del log (13:28-13:30):** **10× `BP 7: CAMBIO DE EJE` en ~105 s**, varios DURANTE `RESP=true` y en plena respiración (13:28:17: eje 1→2 con Fase=-1 activa, `B` saltó de +0.0197 a −0.0279). RESP entró/salió en ciclos de 1-7 s. Causa doble, ambas del centrado del test 13/14:
1. **Las 3 Amp centradas son chicas y parecidas** (titular 0.0095 vs retador 0.0124 = solo +32%, apenas sobre el 30% de histéresis) → el trono se disputa cada pocos segundos. Cada cambio = rearme (fase/extremos/ventana) → el detector vivía reseteándose. En la era buena la Amp inflada por el DC hacía dominar un eje establemente (por la razón equivocada).
2. **`MinAmplitude`=0.006 quedó DENTRO de la banda de trabajo de la Amp centrada** (0.005-0.014 respirando bien): a las 13:29:36 `RESP` cayó con Amp pasando de 0.0064 a 0.0058. Con `DeactivateDelay`=0.5 cada roce apagaba RESP.

**Fix (grafo + valores):**
- **El eje se CONGELA mientras `bBreathing` es true** — el eje es una decisión de calibración, no de frame. Si el eje es incorrecto, la Amp baja → RESP cae → se re-permite la selección: el failsafe existe solo.
- **Dwell mínimo entre cambios de eje:** `AxisDwell`(4.0, editable) / `AxisDwellTimer` (estado; **default 999** en CDO e instancia para que la PRIMERA selección sea inmediata). El timer suma DT siempre y se resetea a 0 en cada cambio. 4.0 ≈ `TauAmp`: no tiene sentido re-decidir más rápido de lo que converge la medida que decide.
- **`MinAmplitude` 0.006 → 0.003** (banda de trabajo 0.005-0.014 queda 2-5× arriba; la señal muerta decae bajo 0.003 con `TauAmp`=4 → el lazo de recuperación del test 13 sigue vivo, solo ~2.8 s más lento).
- **`DeactivateDelay` 0.5 → 1.5** (el valor de diseño documentado de las dos capas; los microdips ya no apagan RESP).
- **`MinExcursion` 0.03 → 0.05** = el valor de la era buena (tests 7-10). El piso de `Dlt` 0.0045 permitía flips de fase de ~1.5 s (13:28:15-16); vuelve a 0.0075.
⚠ La reescritura de `Step` dejó huérfanos nuevos — **limpieza pendiente** (método en gotchas §limpieza).

### Test 16 — 🔴 EL CONGELAMIENTO DEL EJE LE DIO PERMANENCIA A UNA ELECCIÓN NO CONFIABLE
> *"En la mitad del testeo se invierten los papeles, agrandar y achicar suceden al revés."*

**La secuencia exacta del log (14:08-14:10):**
```
14.09.02  BP 4: RESPIRANDO       <- eje congelado en 1, funcionaba
14.09.52  BP 5: SALISTE          <- bajon momentaneo del umbral (~1 s)
14.09.52  BP 7: CAMBIO DE EJE    <- al descongelarse eligio el eje 2
14.09.54  BP 4: RESPIRANDO       <- congelado en el eje 2 = signo invertido, PERMANENTE
```
Antes del bajón: **426/426 muestras en eje 1**, fase vs. pendiente de `B` **166 aciertos / 9 fallos**. Después: eje 2 e inversión.

**Mecanismo:** al caer el umbral, el reseed pone `BreathV=0` → las 3 `AmpV` decaen a ~0 → **al reconstruirse, el ganador se decide por RUIDO (cara o cruz)**. El congelamiento del test 15 no arregló la elección: le dio **permanencia a una elección no confiable**. Antes flip-flopeaba y volvía sola; ahora se clava en el error.
📌 **Lección:** estabilizar una decisión no la vuelve correcta. **Si el mecanismo de elección no es confiable, congelarlo empeora el fallo** — cambia un parpadeo por un error permanente.

**Fix: MATAR la auto-selección. `bLockAxis`(true) + `LockedAxis`(1).** Con lock, `ActiveAxis = LockedAxis` sin histéresis, sin dwell, sin rearmado; `PrevAxis` se escribe con `LockedAxis` cada frame → la rama `BP 7` (que vive en el `else`) no puede disparar. Con `bLockAxis=false` vuelve la lógica anterior intacta.
**Justificación con datos:** el **eje 1 gana siempre que la señal es real** (426/426 en el test 16; 699/886 en el test 12). La auto-selección **no compraba nada y costaba inversiones**.
⚠ **`bInvert=true` queda calibrado PARA EL EJE 1.** Si algún día se cambia `LockedAxis`, hay que revisar el signo.
⚠ **Sin failsafe automático:** si el agarre cambia y el eje 1 deja de captar, `Amp` cae y `RESP` no entra (hay que reacomodar el mando, o poner `bLockAxis=false`). Es el comportamiento correcto: **avisa en vez de inventar**.
💡 **El fix de fondo sigue siendo el prop del sensor con geometría definida** — estandariza el agarre → el eje y su signo pasan a ser **constantes conocidas** y toda esta maquinaria (auto-selección + histéresis + dwell + `bInvert`) se borra. Esto ya se decía en el test 12; el lock es el atajo que lo aproxima.

### Test 18 — 🔴 CONGELADO EN EL MÁXIMO tras reentrar: Fase=0 congelaba en vez de soltar
> *"Funcionó bien hasta que salí y volví a entrar. Se quedó pegado en grande y no volvió más."*

**Secuencia exacta del log (reentrada 16:46:42):** el cubo funcionó y **fue subiendo** con cada respiración (deriva del integrador) hasta saturar en **Lvl=1.00** durante una inhalación real (s03). En s06.8 el usuario movió la mano (`Lin`=8.3 > `StillLinThreshold`=8) → **reseed** → `Phase=0`. La señal post-reseed quedó débil y casi plana (`B` entre −0.017 y −0.013, rango 0.004 **< `Dlt`=0.0089**) → **ningún giro pudo dispararse** → `Phase` se quedó en **0** → y **Fase=0 CONGELABA el nivel** → **16 segundos clavado en 1.00** hasta que una exhalación real lo destrabó.

**Causa raíz:** el bloque de integración de `Level` tenía `if Phase>0 sube / elif Phase<0 baja / (Phase==0: nada)`. **`Phase=0` = "no sé tu dirección" (post-reseed/arming), y congelar en ese estado significa quedar atascado en el último valor** — que aquí era la saturación 1.0. Un movimiento de mano borra la fase; si la señal reaparecida es débil, nunca se recupera.

**Fix: `Phase==0` DENTRO de `bBreathing` vuelve a la base con `ReturnTau`** (la misma expresión que la rama no-breathing), en vez de congelar. Si se pierde la lectura, el cubo se relaja hacia abajo y retoma en la próxima respiración detectada.
⚠ **NO afecta el aguante real:** aguantar mantiene `Phase=+1`/`−1` (sticky), nunca 0. `Phase=0` sólo ocurre post-reseed/arming. Cambio de una sola rama; todo lo demás intacto (verificado por Fable).
💡 **De fondo sigue siendo el talón de Aquiles del integrador:** (a) deriva hacia la saturación en varias respiraciones, (b) una vez saturado necesita `FallTime` s de `−1` sostenido para bajar. El fix cura el atasco; la deriva-a-saturación es inherente. **Si reaparece, el mapeo directo-normalizado (que el usuario descartó en el test 17) lo eliminaría estructuralmente.**

### Test 19 (fix aplicado, pendiente de probar) — SlowEMA con TAU ADAPTATIVO: mata el escalón fantasma de los micro-ajustes
**El problema (diagnosticado post test 18):** un ajuste de postura con `Lin`≈5 (bajo `StillLinThreshold`=8 → NO reseed) inyecta un escalón DC en `B` que `TauSlow`=90 tarda ~90 s en absorber → sordo/desincronizado el resto de la sesión.
**Fix:** el tau del **SlowV** (solo el SlowV) es ahora adaptativo:
`tau = (LinSpeed > ReCenterLinThreshold) ? TauSlowFast : TauSlow` → alpha = `clamp(DT / max(tau, 0.01))`.
Quieto de verdad (Lin ≤ 2.5) → tau 90 (el aguante de 32 s intacto). Movimiento moderado (2.5 < Lin < 8) → tau 0.5: el SlowEMA persigue la nueva línea base en ~1 s y el escalón no entra al band-pass.
Vars nuevas (instance-editable, seteadas en CDO + instancia): **`ReCenterLinThreshold`(2.5 cm/s)** · **`TauSlowFast`(0.5)**.
FastV/MidV/AmpV/ZigZag/armado/reseed/fix Phase==0/lock de eje/audio/debug: **sin tocar** (verificado por re-lectura tras compilar).
⚠ Riesgo a vigilar en el test: mientras `Lin` esté en (2.5, 8) el SlowEMA sigue a `B` con tau 0.5 → el band-pass se comprime hacia 0 durante ese tramo (señal atenuada, no falsa). Si la respiración misma llegara a empujar `Lin` sobre 2.5 se atenuaría de verdad — datos de tests: respirando `Lin`=0.6-3.4, así que 2.5 roza el rango medido; si atenúa, subir `ReCenterLinThreshold` a ~4.
⚠ Esta reescritura de `Step` dejó una generación más de huérfanos (limpieza pendiente, método en gotchas).

## 🎯 PLAN DE REDISEÑO — "umbral + cambio de dirección puro" (aprobado por el usuario, PENDIENTE de implementar)
El usuario, tras ingeniería inversa de Flowborne, confirmó: **solo importan umbral + cambio de dirección; la caja es solo visualización.** El core ZigZag+fase pegajosa YA es eso. Los 3 peores bugs (atasco en máx, deriva a saturación, "otro timing") vienen TODOS del **integrador**. → **Matar el integrador, mapeo directo.**

**Corrección de realidad (research):** el acelerómetro crudo NO es accesible en Quest/UE5.8 y físicamente es peor (a=Aω²≈0.0008g a 0.2Hz). La DIRECCIÓN se saca de la **inclinación** (Z de los ejes de orientación), no de aceleración. El "giroscopio/acelerómetro" del usuario para el umbral ≈ `GetAngularVelocity`/`GetLinearVelocity`, que YA se usan para la quietud.

**Cambio central:** reemplazar `Level += DT/RiseTime` / `-= DT/FallTime` por
`Level = clamp((B − RunMin) / max(RunMax − RunMin, MinExcursion), 0, 1)`
usando los MISMOS `RunMax`/`RunMin` del ZigZag (sin estado nuevo). Autocentrado, sin deriva, sin atasco, sincronía perfecta. Mientras `Phase==0` (arming) → `Level=0` explícito (evita dividir por Exc≈0).

**Destino de cada mecanismo:**
- **MUEREN:** `RiseTime`, `FallTime`, `ReturnTau`, el retorno-a-base de Phase==0 (test 18), y las ya-muertas `DBreath`/`DerivTau`/`PhaseThreshFrac`.
- **SE QUEDAN:** `RunMax`/`RunMin`/`Excursion` (ahora doble tarea: giros + escala); `TauSlow`/`TauSlowFast` adaptativo (protege el detector, no el integrador); `MidV`/`AmpV`/`TauAmp` (sostienen el umbral — el log confirma margen angosto Amp/MinAmplitude ~2×); `MinAmplitude`/`MinExcursion`; `bLockAxis`/`AxisDwell`; `ArmDelay`/`ArmTimer`.

**Conclusiones del log (sesión 17:39-17:41, señal floja Exc~0.029 = 4.5× más débil que las buenas):** `Fase=0` ocupó **24%** del tiempo; el integrador **ya saturó en 102 s** (6.3 s continuos clavado en 1.0) — prueba en miniatura del atasco a 25 min; `RESP` flipeó 6× (margen de umbral angosto).

**Robustez 25 min:** con mapeo directo, Level NO puede derivar a saturación (no integra tiempo). El `TauSlow` adaptativo sigue protegiendo `B` del escalón DC por ajuste de postura. Validar SOLO este cambio antes de tocar `TauSlow`.

**Riesgos:** se pierde el "maestro de ritmo" (RiseTime empujaba a un ritmo objetivo) — usuario lo acepta; el retardo en los extremos (~0.6-1.1 s, límite físico del ZigZag) no cambia; con Exc chico, `MinExcursion` como piso del denominador evita amplificar ruido.

### Test 20 — mapeo directo IMPLEMENTADO (el plan de arriba, aplicado)
Se reemplazó el integrador por tiempo (`Level += DT/RiseTime` / `-= DT/FallTime` / retorno con `ReturnTau`) por el mapeo directo posicional planeado:
```
si bBreathing Y Phase != 0:  Level = clamp( (BreathValue - RunMin) / max(RunMax - RunMin, MinExcursion), 0, 1 )
si no (bBreathing==false O Phase==0):  Level = 0
```
`BreathValue` es la señal **sin centrar** que ya alimenta el ZigZag (test 14: es la que sostiene el aguante con `TauSlow`=90), y `RunMin`/`RunMax`/`MinExcursion` son los mismos que el ZigZag ya mantenía — **cero estado nuevo**. Ya no hace falta animar la vuelta a la base: `Level` se recalcula cada frame directo desde la señal, no hay nada que "drenar".

**Trampas del DSL nuevas, no documentadas antes de hoy** (se suman a las de `gotchas.md`):
- `(bind _x (|GetbXxx))` con un booleano **en el preámbulo `bind`** falla (`does not exist`) aunque el mismo getter funcione bien **inline dentro del árbol exec** — hubo que eliminar esos binds y usar el getter inline en el punto de uso.
- El getter cross-clase de bool también pierde la palabra completa esperada: no es `(|GetIsRightHand ref)` sino `(Class|BPBreathSensor|GetIsRightHand ref)` (ya estaba en gotchas, confirmado de nuevo).
- `Math|Vector|Vector_Zero` y `Math|Vector|Vector_GetAbs` (nombres que `read_graph_dsl` imprime) **no existen como type_id**; son `Math|Vector|VectorZero` y `Math|Vector|VectorGetAbs` sin guión bajo.
- Una rama `(else _)` (no-op que el read imprime para "nada que hacer") **no es un statement válido** — hay que reemplazarla por una sentencia real inocua (se usó `(Variables|Default|SetPhase (Variables|Default|GetPhase))`, una reescritura de sí misma).

**Variables muertas borradas:** `RiseTime`, `FallTime`, `ReturnTau` — confirmado sin referencias en `Step` NI en `EventGraph`/`UpdateAudio`/`DoFadeIn`/`DoFadeOut` antes de borrar. `remove_variable` + `compile_blueprint` (limpio) + `save_assets`.

**Limpieza de huérfanos post-reescritura** (9 intentos de `write_graph_dsl` antes de dar con la sintaxis correcta dejaron cuerpos abandonados): método de vitalidad dirigida vía `ProgrammaticToolset` sobre los 5 grafos del BP → `Step` **903 → 451 nodos vivos (452 borrados)**; `EventGraph`/`UpdateAudio`/`DoFadeIn`/`DoFadeOut` ya estaban limpios (0 borrados cada uno). `compile_blueprint` + `save_assets` otra vez tras la limpieza.

**Verificado por relectura tras compilar:** el ZigZag (`RunMax`/`RunMin`/`Excursion`/`Phase`, ventana de armado, `TurnFrac`) intacto; el tau adaptativo del SlowV (test 19, `ReCenterLinThreshold`/`TauSlowFast`) intacto; `MidV`/`AmpV`/selección-lock de eje intactos; escala sigue `Lerp(ScaleMin, ScaleMax, Level)` sobre `BaseScale`; debug `BP 6`, audio (`CallFunction|UpdateAudio`) y háptico intactos.

⚠ **Pendiente de probar en el visor.** Riesgo a vigilar: sin integrador, `Level` ya no puede quedar "atascado" ni derivar a saturación (los bugs de los tests 18/11), pero el retardo físico cerca de los puntos de retorno (~0.6-1.1 s, el piso del ZigZag) sigue igual — no lo resuelve el mapeo directo, nunca fue su objetivo.

### Test 21 — comportamiento de la caja: objetivo + velocidad constante (detección NO se toca)
> Usuario, tras validar que la detección funciona instantánea: *"Si inhalando → tamaño objetivo A (máximo); si exhalando → objetivo B (mínimo). Interpolado desde su ubicación actual, a velocidad constante. De mínimo a máximo = 5 s si nunca cambio de dirección."*

El mapeo posicional del test 20 seguía la señal cruda directamente (podía verse "brusco"). Se reemplaza por **búsqueda de objetivo binario a velocidad constante**:
```
Target = (bBreathing Y Phase>0) ? 1.0 : 0.0
speed  = 1 / max( (Target>=Level ? RiseTime : FallTime), 0.1 )
Level  = FInterpToConstant(Level, Target, DT, speed)   // sin overshoot, velocidad constante
```
`RiseTime=FallTime=5` → 5 s de mínimo a máximo. Recreadas ambas variables (murieron en test 20).

🔴 **Método (importante): NO se reescribió `Step` — se hizo CIRUGÍA.** El detector (ZigZag) funciona y es frágil, y el `read_graph_dsl` lo representa CON PÉRDIDAS (ej: muestra `(and (GetLinearVelocity) (GetAngularVelocity))` inline, pero escribir eso FALLA — el original usa el pin booleano de retorno; y muestra `Vector_Zero` que como write es `VectorZero`). Reescribir desde el read habría roto la detección. En su lugar:
1. Función nueva **`UpdateLevel(DT)`** (grafo vacío → `write_graph_dsl` seguro) con la lógica de objetivo+FInterpToConstant.
2. En `Step`, cirugía de nodos: se insertó `(CallFunction|UpdateLevel DT)` en lugar del bloque de Level (branch + 3 SetLevel), redirigiendo las **4 fuentes de exec** del debounce al nuevo nodo y su salida a la escala. Detección verificada **idéntica byte por byte** por relectura.
Costo: solo 17 huérfanos (vs 400+ de una reescritura completa). `FInterpToConstant` = `Math|Interpolation|FInterptoConstant(Current, Target, DeltaTime, InterpSpeed)`.

💡 **Regla nueva para el futuro:** cuando el grafo tiene lógica frágil que funciona y solo hay que cambiar UN bloque → **extraer el bloque nuevo a una función aparte (write seguro en grafo vacío) + cirugía mínima de una llamada en el grafo grande.** No reescribir el grafo grande desde el read con pérdidas.

### Test 22 — 🔴 BUG LATENTE EXPUESTO: la fase se clavaba en −1 (la detección estaba a medias)
> *"La caja ya no hace nada."* Tras el test 21 (objetivo por fase).

**El log fue concluyente:** durante 246 muestras seguidas de respiración real (B oscilando de −0.06 a +0.017), **`Fase=-1` TODO el tiempo**. La detección **nunca disparaba el giro de exhalación→inhalación**. Como el test 21 usa `Target = (bBreathing Y Phase>0)`, y Phase nunca era >0, el objetivo era siempre 0 → caja clavada en el mínimo.

**Causa raíz (bug latente de la reescritura del test 20 por Sonnet):** toda la detección estaba envuelta en un gate `(if Phase>=0)`. La rama FALSA (Phase<0) iba a un no-op `SetPhase(Phase)`. Así, **al llegar a −1, el chequeo de giro-a-inhalación —que está DENTRO de ese gate— nunca se alcanzaba** → Phase clavada en −1 para siempre.
🔴 **Por qué no se detectó antes:** el mapeo POSICIONAL del test 20 leía `(B−RunMin)/(RunMax−RunMin)`, que **no depende del signo de Phase** (solo de que sea ≠0). Así que la caja se movía bien igual, y el bug quedó oculto por 2 tests. El test 21 (objetivo por signo de fase) lo expuso. **Lección: un feedback que no depende de la variable X no puede validar X** (ya lo sabíamos del test 2 — reaprendido).

**Fix quirúrgico:** el gate era `IfThenElse_95` (condición `Phase>=0`; TRUE→detección, FALSE→no-op `SetPhase_365`). Se reconectó la salida del arm-window (`IfThenElse_94.else`) **directo al cuerpo de detección** (`SetRunMax`), saltándose el gate; borrados el gate y el no-op. Ahora la detección corre **siempre que no está armando**, y los guardas internos (`RunMax=Max(...)` auto-protegido; `RunMin` bajo `Phase<=0`; giros con su propio guard) manejan cada dirección. El giro `(Phase<=0 Y B>RunMin+delta)→Phase=+1` por fin es alcanzable. Verificado por relectura: el `(elif Phase>=0 ... else noop)` ahora es `(else ...)` limpio.

⚠ **Este bug estaba en la detección desde el test 20** — o sea que "funciona instantáneo" (tests 20/21) era el mapeo posicional tapándolo. Con la fase ahora correcta, el objetivo+velocidad-constante del test 21 debería por fin alternar.

### Test 23 — freeze en Fase=0 (indeterminada): la caja se queda en su extremo
> *"Se agranda y se achica bien. Un detalle: si llega al mínimo o al máximo pero no se ha detectado un cambio de dirección, debe quedarse ahí."*

El objetivo binario del test 21 (`Phase>0 ? 1 : 0`) hacía que **Fase=0** (indeterminada — tras reseed por micro-movimiento, o al entrar) mandara el objetivo a 0 → la caja se iba al mínimo aunque estuviera arriba. Las fases ±1 ya se quedaban (sticky), pero la 0 no.

**Fix en `UpdateLevel`** — objetivo con 4 casos por prioridad:
```
Target = !bBreathing ? 0.0              // fuera del umbral → vuelve a base
       : Phase>0     ? 1.0              // inhalando → máximo
       : Phase<0     ? 0.0              // exhalando → mínimo
       :               Level            // indeterminado → CONGELA (se queda donde está)
```
Con `Target=Level`, `FInterpToConstant` no mueve nada → la caja se queda en el extremo alcanzado hasta que se detecte un giro real. `!bBreathing` tiene prioridad para que una `Phase` vieja no impida el retorno a base al salir del umbral.

### Test 24 — la PRIMERA activación tras Play tarda ~5 s (las reentradas no)
> *"El primer intento de reconocer el umbral tras Play tarda como 5 s. Si salgo y reentro, tarda menos."*

**Causa (confirmada en log):** `Amp = EMA(TauAmp)` de `|BreathV−MidV|`. Tras Play arranca en **0** y tarda ~4 s en cargarse hasta cruzar `MinAmplitude`(0.003); +1 s de `ActivateDelay` = ~5 s. En las **reentradas, `AmpV` NO se reinicia** (el reseed resetea MidV/RunMax/RunMin/Phase pero **no AmpV**), así que sigue cargada de antes → reactiva casi al instante. No es un paso extra en la primera: es que las demás parten con `AmpV` precargada.

**Fix (solo valor): `TauAmp` 4 → 2.** `TauAmp` estaba alto para estabilizar la selección de eje, pero **el eje ahora está fijo (`bLockAxis`)** → ese motivo desapareció. Bajarlo carga `Amp` ~2× más rápido. Sin riesgo de flicker del gate: la señal en régimen (Amp~0.012+) está muy por encima de MinAmplitude, y `DeactivateDelay`(0.5) absorbe caídas breves. Si aún se siente lento, bajar a ~1.5.

### Test 25 — arranque en 0.5: la caja responde de inmediato al entrar (Opción A)
> *"Toma más rápido la detección del umbral, pero hay delay largo entre entrar y que la caja se mueva."*

**Causa (log):** al entrar exhalando, `Target=0` (mínimo) y la caja **ya está en el piso** → no hay movimiento visible hasta la próxima inhalación. `TauAmp`=2 (test 24) activó RESP antes (a mitad de exhalación), ensanchando ese hueco. Comportamiento correcto (exhalado=chico) pero se siente como delay.

**Fix (Opción A, elegida por el usuario):** al confirmar el umbral (`SetBreathing true`, evento BP 4), **sembrar `Level=0.5`**. Así la caja parte del medio y el primer movimiento en CUALQUIER dirección (inhalar→sube a 1, exhalar→baja a 0) se ve al instante. Se autocorrige en el primer ciclo. `UpdateLevel` toma el control desde 0.5 el mismo frame (si Phase=0 → congela en 0.5; si ±1 → interpola desde 0.5).
**Cirugía:** nodo `SetLevel(0.5)` insertado en el exec entre `SetbBreathing(true)` (VariableSet_369) y el PrintString BP 4. Una sola inserción, 0 huérfanos.

### Test 26 — ❌ REVERTIDOS los tests 24 y 25 (semilla 0.5 + TauAmp 2): saltos y parpadeo
> *"Quedó rarísimo. Se pegó saltos de tamaño muy rápidos, le costó tomar el umbral."*

**Dos errores míos, confirmados en el log:**
1. **La semilla `Level=0.5` (test 25) es un SALTO instantáneo, no una transición.** Log: RESP se activa → `Lvl` salta 0.00→0.50 de golpe. Un `SetLevel(0.5)` popea; no interpola. Y como se dispara en CADA activación, con el umbral parpadeando saltaba una y otra vez.
2. **`TauAmp=2` (test 24) desestabilizó el umbral.** Señal débil esta sesión (`Amp` 0.0006–0.009, rozando `MinAmplitude`=0.003). Con menos suavizado, `Amp` sigue los bajones en los cruces/aguantes y cae bajo el umbral → RESP parpadea (`BP4`/`BP5` cada 1-2 s). Con `TauAmp=4`, `Amp` decae más lento y aguanta el umbral en los bajones breves.

**Revertido:** nodo semilla borrado (flujo directo `SetBreathing(true)`→PrintString restaurado); `TauAmp` 2→4. Vuelta al estado estable del test 23.

📌 **Quedan pendientes (NO tocar a la ligera):** (a) primera detección ~5 s tras Play (Amp carga desde 0); (b) "delay" al entrar exhalando (caja en mínimo hasta inhalar). **El fix correcto NO es una semilla instantánea.** Candidato real: **envolvente con ataque rápido / caída lenta para `AmpV`** (como ya se hace con LinSpeed) → sube rápido (primera detección veloz) Y no cae en los cruces (umbral estable) — resuelve (a) y el parpadeo de una. Requiere cambio de código medido, no un valor. La raíz de fondo sigue siendo la señal débil variable entre sesiones.

### Test 24 — VUELTA al mapeo directo del test 20 (pedido del usuario) + entrada más rápida
> *"Se nos está haciendo difícil. Volvamos a la versión de hace ~20 min que funcionaba bien (la 'muy instantánea'), y solo que se demore menos en tomar el primer umbral."*

Los tests 21-23 (objetivo+velocidad constante, freeze en Fase=0) se sintieron como sobre-ingeniería. Se revierte `UpdateLevel` al **mapeo directo posicional del test 20**:
```
si bBreathing Y Phase!=0:  Level = clamp( (BreathValue - RunMin) / max(RunMax - RunMin, MinExcursion), 0, 1 )
si no:                     Level = 0
```
La caja sigue la posición real de la respiración en tiempo real ("muy instantáneo"). **Se conserva el fix de fase del test 22** (el gate `Phase>=0` sigue eliminado — no afecta al posicional, y mejora la robustez).
**Entrada más rápida:** `ActivateDelay` 1.0 → **0.5** (CDO + instancia). El primer ingreso al umbral tarda la mitad.

### Test 24b — corrección: el usuario quería la de OBJETIVO (A/B interpolado), no la posicional
Aclaración del usuario: *"No, es la que interpolaba al máximo y mínimo de caja, la que tenía objetivo escala A y B."* → se restauró `UpdateLevel` a la versión **objetivo + velocidad constante con freeze en Fase=0** (test 23), NO la posicional. Se mantiene `ActivateDelay`=0.5 (entrada rápida). `RiseTime`=`FallTime`=5.

**ESTADO VIGENTE del comportamiento de la caja:** objetivo por fase (inhalando→máximo, exhalando→mínimo, Fase=0→congela, fuera de umbral→base) con `FInterpToConstant` a velocidad constante (5 s de extremo a extremo). Detección con el fix de fase del test 22. Entrada al umbral en 0.5 s.

📌 **Lección de proceso:** el "volvamos atrás" costó dos pasadas (posicional → objetivo) por no confirmar CUÁL comportamiento antes de tocar. Con dos diseños de caja plausibles ("directo/instantáneo" vs "objetivo/interpolado"), **preguntar cuál en UNA línea antes de revertir** habría ahorrado el rodeo.

### Limpieza de huérfanos (post-audio) — 8.88 MB → 1.20 MB
3683 nodos muertos borrados (`Step` 3665→405, EventGraph 466→43) con el método de **vitalidad dirigida** vía ProgrammaticToolset — ver gotchas §limpieza. Compila limpio, EventGraph verificado intacto. Los grafos escritos una sola vez dieron 0 borrados (control del criterio).

### Audio (3 WAV) — Umbral (loop), Inhale, Exhale con fades de 1 s
Spec del usuario: **Umbral** loop, fade-in/out 1 s con el flanco de `bBreathing`. **Inhale/Exhale** one-shot, fade-in al empezar la fase, **se mantienen al aguantar** (Phase pegajosa), fade-out al cambiar de estado.
Assets: `/Game/SoulCharger/Stages/Breath/Audio/{Umbral,Inhale,Exhale}` (importados a mano por el usuario — **no hay toolset de audio MCP**). Estéreo, 44.1 kHz, 24-bit (el importador convierte 24→16 solo, `SoundFactory.cpp:391`). Umbral `bLooping=true`. Componentes con `bAllowSpatialization=false` (2D, la respiración es la del usuario, no un objeto en el espacio).

**Arquitectura: 3 `AudioComponent` persistentes en el CDO** (`AudioUmbral/Inhale/Exhale`), no cargar-y-descartar. Razones verificadas en código:
- `FadeIn` internamente hace `PlayInternal(StartTime)` (`AudioComponent.cpp:970`) → **re-dispara desde cero**, un mismo componente sirve para siempre.
- `FadeOut` sobre algo que no suena **no hace nada** (`if (!IsActive()) return;`, línea 987) → seguro llamarlo siempre, sin guardas.

**🔴 Trampa del DSL: `FadeIn`/`FadeOut` tienen overload ambiguo Synth vs AudioComponent.** `write_graph_dsl` elige el de **SynthComponent** → el pin `self` no acepta un `AudioComponent` (*"Could not connect pin ... to self"*). Y NO existe la forma `Class|AudioComponent|FadeIn`.
**Solución:** dos funciones helper `DoFadeIn(Comp, Dur)` / `DoFadeOut(Comp, Dur)` con el nodo creado por **`create_node` + `declaring_class: /Script/Engine.AudioComponent`** (fuerza el `self` a AudioComponent, verificado: pin pasó de "Synth Component" a "Audio Component Object Reference"). La lógica de flancos va en `UpdateAudio` (DSL) llamando a los helpers con `CallFunction|DoFadeIn`. `UpdateAudio` se llama desde `Step` con `CallFunction|UpdateAudio` (la forma `(Variables|Default|UpdateAudio)` **no existe** para funciones propias).

**Lógica** (`UpdateAudio`, verificada por Fable los 7 puntos): `_aphase = bBreathing ? Phase : 0`. Umbral por flanco de `bBreathing`; Inhale/Exhale por flanco de `_aphase` (a +1: FadeIn Inhale + FadeOut Exhale; a −1: al revés; a 0: FadeOut ambos). `bLastAudioBreathing`/`LastAudioPhase` se guardan **después** de comparar. Aguantar → Phase pegajosa no cambia → `_aphase` no cambia → el sonido se mantiene. ✅ cumple la spec.
Vars nuevas: `LastAudioPhase`(int) `bLastAudioBreathing`(bool) `AudioFadeTime`(1.0, editable). Componentes: `AudioUmbral` `AudioInhale` `AudioExhale`.
Pendiente de test en visor.

## Estado de dos capas: umbral crudo vs. `bBreathing`
- `bInThreshold` (crudo, por frame) = `bStill AND bTracked AND Amplitude >= MinAmplitude`.
- **`bBreathing` (confirmado, con debounce)** = lo que consume el gameplay. Entra tras `ActivateDelay` (0.5 s, bajado en test 24) continuos en umbral; sale tras `DeactivateDelay` (0.5 s) continuos fuera. Evita el parpadeo y confirma "ya estás posicionado".

## Variables — valores VIGENTES (última actualización tras los tests 24b-26, verificados en la instancia del nivel)
**Config (instance-editable):** `bDebug` `DebugInterval`(0.5) `bInvert`(true) · **`bLockAxis`(true) `LockedAxis`(1)** — eje FIJO, sin auto-selección · **`TauSlow`(90)** `TauFast`(0.4) **`TauAmp`(4)** (test 26 revirtió el 2 del test 24) · **`ReCenterLinThreshold`(2.5) `TauSlowFast`(0.5)** — tau adaptativo del SlowV (test 19) · **`MinAmplitude`(0.003)** · **`TurnFrac`(0.25)** **`MinExcursion`(0.035)** (bajado desde 0.05 para señal débil) · `StillLinThreshold`(8 cm/s) `StillAngThreshold`(25 °/s) `StillTau`(0.3) · `ScaleMin`(1.0 = base) `ScaleMax`(2.5) · **`ActivateDelay`(0.5)** (test 24) **`DeactivateDelay`(0.5)** `HapticAmplitude`(0.25) · **`RiseTime`(5) `FallTime`(5)** — velocidad constante de `UpdateLevel` (recreadas en test 21) · **`AxisDwell`(4.0) `AxisDwellTimer`(default 999, estado)** — test 15: eje congelado con `bBreathing`, dwell entre cambios (superado por `bLockAxis`)
🔴 **`ReturnTau` YA NO EXISTE** (borrada en test 20). `RiseTime`/`FallTime` murieron en el test 20 pero fueron **recreadas en el test 21** para la caja de objetivo A/B (`FInterpToConstant`, 5 s de extremo a extremo — el estado vigente del test 24b).
**`Phase`: +1 = inhalando · −1 = exhalando · 0 = aún no determinado (durante la ventana de armado → nivel congelado).**
**`ArmDelay`(0.5) `ArmTimer`** — la ventana de armado del test 10. Impide que el transitorio del reseed se lea como respiración.
🔴 **`ArmDelay` NO es un gusto, tiene un piso físico: `ArmDelay` > `TauFast`.** Probado a 0.3 → *"funciona bastante mal"*, revertido a 0.5. **0.3 < `TauFast`(0.4)**: la ventana terminaba **antes de que el filtro rápido se asentara** (a 0.3 s va 53% convergido), así que entregaba justo la basura que la ventana existe para filtrar. A 0.5 s va 71%. **Ratio sano ≈ 1.25× `TauFast`.** Si algún día se toca `TauFast`, hay que mover `ArmDelay` con él.
Referencia de escala: **pico a pico real ≈ 0.13**, `AmpV` ≈ 0.044. No confundirlas otra vez — `MinExcursion` es **pico a pico**.
**Muertas pero presentes** (ya no deciden nada): `DerivTau`(1.2) `PhaseThreshFrac`(0.35) `DBreath` — solo diagnóstico.
**Estado:** `SlowV` `FastV` `AmpV` `BreathV` (Vector) · `LinSpeed` `AngSpeed` `BreathValue` `PrevBreathValue` `DBreath` `Level` `Amplitude` **`RunMax` `RunMin` `Excursion`** `DebugTimer` `InTimer` `OutTimer` · `bStill` `bInThreshold` `bTracked` `bBreathing` `bInhaling` `bInit` · `Phase` `ActiveAxis` (int) · `BaseScale` · `MCRef` · `SensorRef`
**Componente:** `Box` (cubo 30cm, `RelativeScale3D` autoral 0.3)

📌 `TauAmp` 6→4 y `MinAmplitude` 0.006→0.003 son **el arreglo del "se demoró 3-4 s en reconocer"**: `AmpV` decae a ~0 con el movimiento y tiene que reconstruirse hasta `MinAmplitude` antes de que `bInThreshold` sea true. Con 6/0.006 eso tomaba ~1.4 s **además** del `ActivateDelay`; con 4/0.003 baja a ~0.4 s. Se tocó `MinAmplitude` en vez de bajar más `TauAmp` porque `TauAmp` es lo que estabiliza la **selección de eje** — bajarlo mucho la haría flip-flopear.

⚠ **Todos los defaults hay que setearlos en la INSTANCIA del nivel además del CDO** — ver gotchas.

## Grafo
- `Custom|FindSensor` — `GetActorOfClass` BP_BreathSensor → `SensorRef`.
- `Custom|PulseHaptic` — pulso de 0.12 s en la mano que dice el sensor. Lo llama `Step` (una **función puede llamar a un custom event**; es el truco para usar `Delay`, que en una función está prohibido).
- `EventBeginPlay` → `FindSensor`.
- `EventTick` → IsValid(SensorRef) → si el sensor está tomado: `MCRef` = mando del sensor + `Step(DT)`. Si no: resetea y espera.
- **`Step` (función)** — todo el pipeline. Orden importante: velocidad+tracking → quietud → **band-pass SOLO si (still AND tracked), si no reseed** → amplitud → eje → umbral → debounce → háptico → escala → debug.

## Debug (prefijo `BP n:` / `SN n:` en el sensor)
`bDebug` enciende/apaga; `DebugInterval` limita la frecuencia (si no, spamea a 90 fps).
- `BP 1:` BeginPlay · `BP 2:` sensor encontrado / ERROR · `BP 3:` escala base del Box · `BP 4:` RESPIRANDO confirmado · `BP 5:` SALISTE
- `BP 6:` (test 6 en adelante) `Fase=n | Lvl=f | B=f | Exc=f | Dlt=f | Amp=f | RESP=b` — `B` es la señal filtrada, `Exc` la excursión pico-a-pico aprendida, `Dlt` el umbral de retorno. **Se sacaron `dV` y `thr`**: ya no deciden la fase.
- `SN 1:` mandos localizados · `SN 2:` sensor tomado (+ mano)

## Nivel de prueba
`/Game/SoulCharger/Maps/Tests/L_Test_Breath` — duplicado de L_Test_Stage. WorldSettings→DefaultGameMode = `BP_SoulChargerGameMode_C` (spawnea el pawn VR sin depender del FlowDirector ni del streaming). Probe en (200, 0, 130), sensor en (45, 0, 105).

## TODO
⚠ Lista de la fase inicial (pre-test 2), conservada como registro — los tests 2-26 ya ocurrieron; el estado real está en "Estado" y en "ESTADO VIGENTE" arriba.
- [x] Validar el modelo con casco → **valida** (test 1).
- [ ] **Test 2**: verificar que el reseed mata el transitorio (el cubo debe quedarse quieto al apoyar en la mesa, no decaer 45 s) y que `Track=false` aparece con el mando dormido.
- [ ] Confirmar que el háptico no contamina la IMU (¿sube `Lin`/`Ang` al pulsar?). Si no contamina → se puede pasar a vibración continua.
- [ ] Estabilidad del eje: en el test 1 los 3 ejes tenían amplitudes casi iguales (0.026/0.018/0.017). Si sigue flip-flopeando con el reseed, agregar histéresis (cambiar de eje solo si el retador supera al titular por ~25%).
- [ ] Si el test 2 pasa → extraer a `BP_BreathChannel` + `BP_SignalProvider_Breath`.
- [ ] Detección de fase por cruce por cero + período → las 10 respiraciones válidas y el 4/6.

## Preguntas abiertas
- ¿La amplitud de respiración decae si el usuario respira poco profundo? En el test 1 bajó de 0.026 a 0.013 en 10 s. Si roza `MinAmplitude` se va a caer el umbral respirando de verdad.
- Un `ReceiveActorBeginOverlap` vacío quedó de un write anterior. Inofensivo.
