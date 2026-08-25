# BP_BreathRing_SC — el temporizador de respiración de Entering (Core/UI/)

## Purpose
El **marcapasos de respiración** de la versión limpia: dos anillos concéntricos que marcan un ciclo
completo de respiración, con divisores, un marcador que avanza y los nombres de cada tramo escritos
**sobre la curva** del círculo. Es un **reloj fijo, NO reactivo al usuario** — avanza solo, pase lo que
pase, igual que el pacer del esqueleto viejo ([[BP_BreathPacer]]).

🔴 **La idea es que sea CONFIGURABLE, no que haga una respiración concreta.** Cambiás `Divisions` o
`PhaseTimes` en el panel de detalles y **los divisores, los textos y los tiempos se reacomodan solos**,
en el viewport, sin Play. Soporta las 3 formas del PDF de Beltrán (`BreathRing.pdf`, 2026-08-25):

| `Divisions` | Tramos | Qué hace el anillo animado |
|---|---|---|
| 2 | Inhale · Exhale | crece · se achica |
| 3 | Inhale · Hold · Exhale | crece · queda quieto arriba · se achica |
| 4 | Inhale · Hold · Exhale · Hold | crece · quieto arriba · se achica · quieto abajo |

## Status
🟡 **Construido, compilando y verificado por MEDICIÓN en editor y PIE, más revisión visual de Beltrán
(dos correcciones suyas ya aplicadas: sentido horario y medios discos hacia el centro).** Anillos, divisores,
marcador **y palabras** se ven en el viewport sin Play. ⬜ Falta el visor (tamaño,
distancia, si el ritmo se siente natural, si el texto en arco se lee, `TextArc` y el cuerpo de la fuente).

## Geometría — sale MEDIDA del PDF, no a ojo
Se extrajeron los vectores del PDF y se midieron las proporciones reales; los defaults salen de ahí.

| Elemento | Medida (relativa al radio del anillo fijo `R`) | Variable |
|---|---|---|
| Anillo fijo | `R`, línea más gruesa | `Radius` 22 cm · `LineWidth` 0.25 |
| Anillo animado | **por fuera** del fijo, línea más fina, de **1.155·R** a **1.386·R** | `RingScaleMin/Max` · `LineWidthAnim` 0.12 |
| Textos | circunferencia de **1.142·R** — justo donde el animado descansa en su mínimo | `LabelRadiusMul` 1.142 |
| Divisores | medio disco de diámetro ≈ **0.12·R**, lado plano sobre el anillo, **panza hacia el centro** | `DotSize` 2.6 cm |
| Ángulos | arrancan a las **12 en punto**, sentido horario | `StartAngle` 0 |

## 🔴 La decisión de diseño: los arcos son PROPORCIONALES al tiempo
Elección explícita de Beltrán. El arco de cada división **mide lo que dura**: en un 4-7-8 el `Hold`
ocupa casi el doble que el `Inhale`. Consecuencia buena: el marcador avanza a **velocidad angular
constante** (`360·T/CycleDur`), así el anillo se lee literalmente como un reloj y el marcador **cae
exacto sobre el divisor** en cada cambio de fase — verificado por medición (ver abajo).
(Las tres láminas del PDF muestran arcos iguales, pero ahí todos los tramos duraban lo mismo.)

## Cómo corre — la máquina de fases (`RingPhase`)
```
0 oculto  →  1 entrando  →  2 listo  →  3 corriendo  →  4 saliendo  →  5 fin  →  6 terminado
              (se dibuja)   (espera)    (los ciclos)    (se borra)     (avisa y se destruye)
```
```
ConstructionScript ──► Layout()                    ← el anillo se ve ENTERO en el viewport, sin Play
EventBeginPlay     ──► Layout() · RingPhase = bAutoPlay ? 1 : 0 · BRingReveal()
EventTick          ──► BRingTick(Dt)   ← siempre; adentro decide segun la fase
```
🔴 **La API pública (eventos custom), toda con prefijo propio para no colisionar:**
| Evento | Qué hace |
|---|---|
| **`BRingShow`** | Aparece dibujándose. Resetea `T`/`CycleIndex`. **NO arranca los ciclos.** |
| **`BRingGo`** | Arrancan los ciclos (fase 3). |
| **`BRingHalt`** | Los frena y lo deja quieto y visible (fase 2). |
| **`BRingHide`** | Sale borrándose (fase 4) → al terminar avisa y se destruye. |

Al completar `Cycles`, `BRingStep` pasa **solo** a la fase 4; cuando `RevealT` llega a 0, `BRingEnd`:
dispara `OnRingFinished`, llama a **`BP_Director_Story.StepTimeDone()`** y **se destruye**.

🔴 **`bAutoPlay` cambió de significado**: ahora es *"no esperes a nadie"* — aparece y arranca los ciclos
solo, para probar el anillo suelto. **Para la obra tiene que estar en `false`**, así el director maneja
los tiempos.
🔴 **`T -= CycleDur`, nunca `T = 0`** — es la lección de [[BP_BreathPacer]]: poner a cero tira el sobrante
del frame y el anillo **deriva** contra un loop de audio. Medido acá: 3.001 s por ciclo con `CycleTime` 3.

## Registro de variables

### A - Ritmo (instance-editable)
| Variable | Default | Rol |
|---|---|---|
| `Divisions` | **4** | 2, 3 o 4. Se clampea a ese rango. Define la forma del ciclo **y** de qué fase crece/aguanta/achica. |
| `PhaseTimes` | **[4,4,4,4]** | Duración de cada división. Si `bScaleToCycleTime` está en true son **proporciones**; si no, segundos absolutos. Índices que falten se leen como 4.0 (`RawTime`). |
| `CycleTime` | **16** | Duración total del ciclo. Con `bScaleToCycleTime`, **cambia el tempo global sin tocar la proporción**. |
| `bScaleToCycleTime` | **true** | true = `PhaseTimes` se normalizan para sumar `CycleTime`. false = `CycleTime` se ignora y el ciclo dura la suma cruda. |
| `Cycles` | **5** | Cuántos ciclos completos antes de `OnRingFinished`. |
| `bAutoPlay` | **true** | 🔴 **Modo prueba**: aparece y arranca los ciclos solo, sin esperar al director. **En la obra va en `false`** — ahí manda `BRingShow`/`BRingGo`. |

### B - Textos (instance-editable)
🔴 **Las palabras NO son texto en runtime: son TEXTURAS horneadas** (ver "Las palabras" más abajo).

| Variable | Default | Rol |
|---|---|---|
| `MatInhale` / `MatHold` / `MatExhale` | `MI_Word_*` | Un material por palabra. **Acá se cambia la tipografía**: Beltrán reemplaza la textura de la instancia por la suya y listo. `Hold` se usa en las dos pausas. |
| `LabelRadiusMul` | **1.142** | Radio base del anillo de palabras, en múltiplos de `Radius`. Escala el plano, así que mueve **y** agranda — para eso están las dos de abajo, que lo desacoplan. |
| **`LabelSize`** | **1.0** | 🔴 **Tamaño del texto**, independiente del radio. 1 = como viene horneado. Lo aplica el material (`WordSize`) reescalando la UV alrededor del centro de la palabra, así que **no toca la posición**. ⚠ Si queda en **0** el código lo lee como 1 (guarda contra el "nace en cero" de las instancias ya colocadas). |
| **`bShowWords`** | **true** | 🆕 🔴 **Apaga los textos.** ⚠ Nació en `false` en la instancia vieja (el motor); inicializada a mano. |
| **`LabelPush`** | **0** cm | 🔴 **Acerca o aleja el texto del círculo**, en centímetros, sin cambiarle el tamaño. **Positivo = hacia afuera.** Lo aplica el material (`WordPush`) corriendo el punto de muestreo por el eje radial. |
| `TextColor` | blanco | Tinte de las palabras (`WordColor` del material). |
| `WordYawOffset` | **0** | Corrección de orientación si se hornea una textura con otro criterio. Con las texturas actuales va en 0. |

### C - Geometría (instance-editable)
| Variable | Default | Rol |
|---|---|---|
| `Radius` | **22** cm | Radio del anillo fijo. **Todo lo demás escala con él** (escala de los planos, tamaño del widget, radio del texto). |
| `LineWidth` / `LineWidthAnim` | 0.25 / 0.12 | Grosor de cada anillo, en cm. El animado más fino, como en el PDF. Se convierten a UV: `Thickness = LineWidth / (100·ps)`. |
| `RingScaleMin` / `RingScaleMax` | 1.155 / 1.386 | Dónde descansa y hasta dónde llega el **1er** anillo animado, en múltiplos del radio fijo. |
| `RingScaleMin2` / `RingScaleMax2` | 1.45 / 1.75 | 🆕 El **2º** anillo animado. |
| `RingScaleMin3` / `RingScaleMax3` | 1.75 / 2.15 | 🆕 El **3er** anillo animado. 🔴 Los tres respiran con **la misma curva normalizada** (`RingK` 0→1) pero cada uno con su recorrido, así que se mueven con amplitudes distintas y el conjunto se lee en capas. ⚠ **`Max` ≤ 0 oculta ese anillo** — es la guarda que deja apagados los nuevos en una instancia vieja hasta que se les den valores. |
| `PulseGain` | **0.5** | 🆕 🔴 **Cuánto crece un divisor cuando el marcador lo pisa.** 0.5 = 50 % más grande en el pico. 0 = sin pulso. |
| `PulseTime` | **0.4** s | 🆕 Cuánto dura ese pulso hasta volver al tamaño normal. |
| `DotSize` | **2.6** cm | Diámetro del medio disco (divisores y marcador). |
| **`bShowDots`** | **true** | 🆕 🔴 **Apaga los divisores** (los medios discos fijos). No toca el marcador. |
| **`bShowMark`** | **true** | 🆕 🔴 **Apaga el marcador que avanza.** No toca los divisores. ⚠ Igual que el de arriba: nació en `false` en la instancia vieja. |
| `StartAngle` | 0 | Dónde arranca el ciclo. 0 = 12 en punto. |
| `RevealTime` | **1.2** s | 🆕 Cuánto tarda en dibujarse al entrar y en borrarse al salir. ⚠ Nació en 0 en la instancia vieja (el motor); inicializada a mano. |
| `EasePower` | **2.0** | 🔴 El easing del crecimiento con un solo número: `s = tᵖ/(tᵖ+(1−t)ᵖ)`. **1 = lineal · 2 = suave · 3+ = arranque y llegada marcados.** Misma fórmula que [[BP_Door_SC]]. |
| `DotYawOffset` | **0** | Corrección de a cuánto apunta la panza del medio disco. Quedó en 0 porque la orientación se arregló **en el material**; está por si alguna vez hay que rotarlos. |

### D - Color (instance-editable)
`RingColor` (blanco) · `DotColor` (blanco) · `Brightness` (2.0, compartido por anillos y puntos).
Decisión de Beltrán: **todo blanco**, como el PDF — los nombres y los divisores ya dicen en qué tramo
estás, y sumar tres colores más pelearía con una obra que es luz de color.

### E - Estado
| Variable | Rol |
|---|---|
| `Times` (float[4]) | Duración **efectiva** de cada fase, ya normalizada. Las posiciones que sobran se rellenan para que nunca haya índice inválido. |
| `Ends` (float[4]) | Tiempo de **fin acumulado** de cada fase. Es lo que hace que `BRingApply` encuentre la fase **sin bucle**: `i = (T≥Ends[0]) + (T≥Ends[1]) + (T≥Ends[2])`. Las posiciones sobrantes valen `CycleDur`, así la cuenta da lo correcto con 2 y 3 divisiones. |
| `CycleDur` | Duración efectiva del ciclo. |
| `NDiv` | `Divisions` ya clampeado a 2-4. |
| `CycleIndex` · `bRunning` | Ciclo actual / corriendo. |
| **`T`** | 🔴 El tiempo dentro del ciclo. **Es instance-editable a propósito**: escribís un número y el viewport muestra el anillo **en ese instante exacto**, sin Play. Es la forma de autorar mirando. |

## Estructura de funciones (11, una por responsabilidad)
| Función | Qué resuelve |
|---|---|
| **`Layout()`** | 🔴 El corazón. Normaliza los tiempos, llena `Times`/`Ends`/`CycleDur`/`NDiv`, escala y parametriza los dos anillos, coloca los 4 divisores y el marcador, dimensiona el widget y manda a construir los textos. **Sin un solo bucle** (ver trampa 2). |
| `RawTime(I)` | El `PhaseTimes[I]` con guarda: si el índice no existe devuelve 4.0. Un solo `if`, así nunca hay acceso inválido. |
| `RingK(I, A)` | 🔴 **La regla de cómo respira**, sin ramas de ejecución (todo con `select`): devuelve un **0→1 normalizado** — fase 0 sube · fase `sh` baja · las demás quedan en 1 o en 0 según estén antes o después de `sh`, con `sh = (Divisions==2 ? 1 : 2)`. Por eso **no hace falta un array de acciones**: la forma sale de la cantidad de divisiones. 🔴 Devuelve el valor **normalizado, no la escala**, justamente para que cada anillo aplique su propio `Min`/`Max`. |
| `EaseCurve(A)` | El suavizado. 🔴 Se llama `EaseCurve` y **no `Ease`** porque `Ease` choca con el nodo del motor (trampa que ya pagó [[BP_Door_SC]]). |
| **`BRingAnim(Rg, Mn, Mx, Bv)`** | 🆕 Un anillo animado: lo oculta si `Mx ≤ 0`, y si no le pone escala `ps · lerp(Mn, Mx, Bv)`. Llamada 3 veces desde `BRingApply` — agregar un cuarto anillo es un componente más, dos variables y una línea. |
| **`BRingLook(Rg, Width)`** | 🆕 Los parámetros de material de **un** anillo (radio, barrido, grosor, brillo, color). Llamada 4 veces desde `Layout`; existe para no repetir 5 nodos por anillo. |
| **`BRingPulse(Dot, I, Time)`** | 🆕 🔴 **El pulso del divisor.** Sin estado: calcula el tiempo transcurrido desde que el marcador pasó por él (`Time − (Ends[I] − Times[I])`, envuelto en el ciclo) y de ahí una caída lineal `a = clamp(1 − dt/PulseTime)`. Escala = base · `(1 + a·PulseGain)`. Al no guardar estado, **funciona igual scrubbeando `T` a mano en el editor** que corriendo. |
| `PlaceDot(Dot, I)` | Coloca **un** medio disco: visibilidad (`bShowDots && I < NDiv`), escala, posición en el ángulo de inicio de la fase I, yaw tangente y color. Llamada 5 veces (Div0-3 + Mark) en vez de 25 nodos repetidos. |
| `PlaceWord(W, I)` | Coloca **una** palabra: visibilidad (`bShowWords && I < NDiv`), escala, **yaw al ángulo medio de su tramo**, y el material que le toca (Inhale en la fase 0, Exhale en `sh`, Hold en el resto — la misma regla que `RingK`). Llamada 4 veces desde `Layout`. |
| **`BRingApply(Time)`** | Lo de cada frame: encuentra la fase, calcula el alpha, pide `RingK` y escala `RingAnim`; y mueve/rota `Mark` al ángulo `StartAngle + 360·Time/CycleDur`. |
| **`BRingStep(Dt)`** | Avanza `T`, detecta fin de ciclo (arrastrando el resto), cuenta ciclos y dispara `OnRingFinished`. |

## Componentes y por qué están así
- **`Ring`** (SceneComponent, `relativeRotation` **Pitch +90**) — el marco del reloj, y **el único lugar
  donde se decide el sentido de giro**. Con Pitch **+90**: local +X → **arriba del mundo**, local +Y →
  **derecha del usuario**, local +Z → −X (mira al usuario). 🔴 Gracias a esa base toda la matemática es
  de una línea y **una sola rotación**: `P = R·(cos θ, sin θ, 0)` y `Yaw = θ`, con θ **horario** desde las 12.
  ⚠⚠ **Con Pitch −90 el anillo gira al revés** (local +X apunta ABAJO) — fue el primer bug que vio Beltrán.
  Recordar el convenio de UE: **pitch positivo levanta el +X**, o sea `Ry(+90): X→+Z, Z→−X`. Si alguna vez hay
  que invertir el sentido de giro, el cambio es **ese solo número**, no la fórmula.
- **`RingFixed` / `RingAnim` / `RingAnim2` / `RingAnim3`** — cuatro `Plane` con **`M_SoulRing` reusado** (el anillo de carga de la
  ceremonia: unlit, aditivo, TwoSided, anillo procedural sin textura). El animado **no se regenera**:
  se le cambia la **escala uniforme** del componente, que es una sola llamada por frame.
  Escala del plano: `ps = Radius/40` (porque el `Radius` del material queda en 0.4).
- **`Div0..Div3`** y **`Mark`** — cinco `Plane` con **`M_BreathDot_SC`** (nuevo, ver abajo). Los que
  sobran se ocultan según `NDiv`.
- **`Labels`** — un `WidgetComponent` con `WBP_BreathRing_SC`. `Yaw 180` (así mira al usuario que
  avanza en +X — la convención confirmada en `BP_SoulHUD_SC`), `DrawSize` 1024×1024, `Space` World,
  **`TickMode` Enabled** (la config probada de [[BP_Door_SC]]). Su escala la calcula `Layout`:
  `Radius·3.2 / DrawSize.X`, así el widget siempre encuadra el anillo sea cual sea el radio.

## Las palabras — texturas horneadas, idea de Beltrán
🔴 **El vocabulario es cerrado: Inhale / Hold / Exhale.** Por eso cada palabra vive **horneada y ya curvada**
dentro de una textura cuadrada, y el BP sólo tiene que **rotar un plano** al ángulo de su tramo. Literalmente lo
que propuso Beltrán: *"sería tener 3 materiales cada uno con su palabra, y girarlos dependiendo la división"*.

**Por qué esto NO rompe la adaptabilidad** (yo lo descarté mal la primera vez y me corrigió): la **curvatura de
la palabra depende sólo del radio del anillo, no de los tiempos**. Cambiar de 4 a 3 divisiones, o pasar a 4-7-8,
mueve *dónde* va la palabra, no *cómo* está curvada. Una palabra horneada sobrevive cualquier cambio de ritmo.

| Pieza | Qué es |
|---|---|
| `Core/UI/Textures/T_Word_{Inhale,Hold,Exhale}` | 1024², blanco sobre negro. La palabra curvada sobre una circunferencia de radio **0,40** del ancho (la misma convención de `M_SoulRing`). **Espaciado por ancho real de cada glifo**, no por paso angular fijo — es text-on-path de verdad. Generadas con Quicksand-SemiBold a 48 px, que da el mismo arco que la referencia de Beltrán (~20° "Inhale"). |
| `Core/UI/Materials/M_BreathWord_SC` | Unlit · **aditivo** · TwoSided. `Emissive = WordTex.RGB × WordColor × Brightness`. Fondo negro = invisible en aditivo, así que **no depende del alpha**. 🔴 Además **remapea la UV** antes de muestrear: `uv' = 0.5 + WC + (uv − 0.5 − WC − WordPush·ũ) / WordSize`, con `WC = (0.4, 0)` = donde está horneada la palabra. Es un escalado **cartesiano alrededor del centro de la palabra**, no polar: sin `atan2` y sin discontinuidad. 🔴 La UV pasa por un **`Saturate` antes de muestrear**, y las texturas están en **`TA_Clamp`**: al achicar el texto (`LabelSize` < 1) el muestreo se sale de [0,1] y, con el `TA_Wrap` de fábrica, **la palabra reaparecía rotada 180° del otro lado del anillo** (lo vio Beltrán apenas ajustó el tamaño). Con el clamp, lo que se sale cae al borde, que es negro. La curva de la palabra se aparta unos milímetros del arco ideal en los extremos — imperceptible en el rango útil. |
| `MI_Word_{Inhale,Hold,Exhale}` | Una instancia por palabra, con su `WordTex`. Es lo que apunta cada variable `Mat*`. |
| `Word0..Word3` | Cuatro `Plane` **concéntricos con el anillo**, hijos de `Ring`. Sólo cambian de **yaw**. Los que sobran se ocultan. |

🔴 **La textura entra ROTADA 90°.** El eje **U** del `Plane` es el **radial** (el `Yaw = θ` del componente alinea su
+X con el radio) y el **V** es el tangencial. Como la palabra se dibuja "arriba y leyendo hacia la derecha" en la
imagen, hay que **rotarla 90° horario** al hornear para que caiga arriba del reloj leyendo en sentido del reloj.
El generador ya lo hace. ⚠ Si Beltrán hornea las suyas con otro criterio, `WordYawOffset` corrige giros de 90°,
pero **un espejo no se arregla con yaw**: hay que rehornear.

🛠️ **Cómo se regeneran**: el script vive en el historial de la sesión (PIL + Quicksand). Lo esencial: lienzo
1024² negro, radio 0,40·ancho, cuerpo 48 px, cada glifo posicionado por **longitud de arco acumulada** y rotado
su propio ángulo, y al final `transpose(ROTATE_270)`.

⚠ **Lo que se pierde con horneado:** nombres arbitrarios. Se fueron `PhaseNames`, `bAutoNames` y `TextArc`, que
prometerían una flexibilidad que ya no existe. Es la contra honesta del cambio, y es barata: el vocabulario de
una respiración guiada son esas tres palabras.

### 🗑️ Dos caminos descartados antes de llegar acá
1. **Widget UMG** (`WBP_BreathRing_SC`, copia de `WBP_DoorTitle`): funcionaba — 20 letras verificadas por log —
   pero **no se previsualiza en el viewport**, porque el `WidgetComponent` recrea su widget en cada reconstrucción
   del actor y se lleva puestas las letras. Beltrán necesita ver mientras autora, así que no servía.
2. **Un `TextRenderComponent` por letra**, creados con `AddComponentByClass`: los 20 componentes se creaban bien y
   en la posición exacta calculada, pero peleó con la convención de ejes del TextRender y con el churn de
   componentes de construction script. Se abandonó cuando Beltrán propuso las texturas, que además bajan de
   ~20 draw calls a **4** y permiten tipografía tratada a mano.

## `M_BreathDot_SC` (Core/UI/Materials/) — el medio disco
Material propio, 19 expresiones, **unlit · aditivo · TwoSided**, igual de barato que `M_SoulRing`.
Dibuja un disco recortado por la mitad: `mask = saturate((Radius − dist)/Soft) · saturate(dot(uv, CutDir)/Soft)`.

| Parámetro | Default | Rol |
|---|---|---|
| `Radius` | 0.45 | Radio del disco en UV. Con la escala del componente da `DotSize`. |
| `Soft` | 0.03 | Suavizado del borde (antialias analítico; un borde duro aliasea feo en Quest). |
| `CutDir` | **(−1, 0, 0)** | 🔴 **Hacia dónde queda la panza**, en espacio UV del plano. **El eje U del `Plane` es el RADIAL** (porque el punto lleva `Yaw = θ`, que alinea su +X con el radio) y el V es el tangencial. Por eso `(±1, 0, 0)` da radial — hacia adentro o hacia afuera — y `(0, ±1, 0)` da **tangencial**, que es lo que se veía mal. |
| `DotColor` / `Brightness` | blanco / 2.0 | Los pisa `PlaceDot` desde las variables del BP. |

🔴 **Dos correcciones de Beltrán mirando el visor/editor (2026-08-25), en dos rondas:**
1. *"la parte circular de las medias esferas debe apuntar hacia el centro"* → estaba **hacia afuera**.
2. *"están perpendiculares a su línea"* → el primer intento (`CutDir` de (0,1,0) a (0,−1,0)) seguía mal
   porque **los dos son el eje tangencial**: cambió de un tangente al otro, no de tangencial a radial.
   El bueno es **`(−1, 0, 0)`** — el eje U, que es el radial.
⚠ **La lección:** entre dos valores de un eje equivocado, ninguno es el correcto, y en una captura chica
los dos "parecen casi bien". La orientación de una forma en UV **no se adivina probando signos**: se razona
cuál eje del mesh es el que interesa (acá, el que el `Yaw` alinea con el radio) y después se elige el signo.
Se arregló **en el material**, no en el Blueprint, para que **nazca bien en toda instancia** y `DotYawOffset`
quede en 0 como corrección neutra.

## ✅ Verificación por medición (2026-08-25)
No se dio nada por bueno "porque compila". Lo medido:

**Layout** — con `CycleTime` 3 y `PhaseTimes` [4,4,4,4]: `Times=[0.75×4]`, `Ends=[0.75, 1.5, 2.25, 3]`,
`CycleDur=3`, `NDiv=4`. Con `CycleTime` 16: `Times=[4,4,4,4]`, `Ends=[4,8,12,16]`. ✓

**El ciclo, en PIE** — `ciclo 1` y `ciclo 2` separados por **3.001 s** exactos, y `terminado` al llegar
a `Cycles`. Cero `Accessed None`. ✓

**La animación, forzando `T` y leyendo los componentes** (esto es lo que prueba que `RingK` está bien):

| `T` | fase | escala de `RingAnim` | ángulo del marcador |
|---|---|---|---|
| 0 | arranca inhale | 0.63525 = **mínimo** | 0° (12 en punto) |
| 2 | mitad inhale | 0.69878 | 45° |
| 4 | fin inhale | 0.76230 = **máximo** | 90° |
| 6 | mitad hold | 0.76230 (**quieto**) | 135° |
| 10 | mitad exhale | 0.69878 (bajando) | 225° |
| 14 | mitad hold final | 0.63525 (quieto abajo) | 315° |

Todos coinciden con el cálculo a mano. El marcador cae **exacto** sobre cada divisor al cambiar de fase. ✓

**Los textos** — `BREATHRING: letras creadas = 20` = Inhale(6) + Hold(4) + Exhale(6) + Hold(4). ✓

## 🔗 Cómo se engancha a la obra (2026-08-25)
El anillo pasó de juguete suelto a **el reloj de la etapa Entering**: la duración de la etapa la manda él.

```
Terminan las instrucciones
  └ Director.StartStepTime  → Sensor.SetStage(1)      (el orbe aparece solo, ya existía)
                             → BreathRingCue(1) → BRingShow()   ← entra, SIN ciclos
                             → arranca el VO del paso
Termina el VO
  └ Director.OnVOFinished_Event → BreathRingCue(2) → BRingGo()  ← arrancan los ciclos
Terminan los ciclos
  └ BRingStep → fase 4 (sale) → BRingEnd → Director.StepTimeDone()
                                            → SetStage(-1): muere el umbral, el orbe se va solo
                                            → Next(): sigue el cierre (VO, ameba, carga)
                                            → el anillo se destruye
El orbe, al quedar invisible con la etapa cerrada → OrbRetire → se destruye
```

**Lo que se agregó afuera, mínimo y sin reescribir nada ajeno:**
- **`BP_Director_Story.BreathRingCue(Mode)`** — una función nueva. Busca el anillo, y con `Mode 1` lo hace
  entrar, con `Mode 2` le arranca los ciclos. Guardada por `Room == 1`, y el modo 2 además por `WaitFor == "time"`,
  así que **un VO que termina en otro momento no la dispara**. Enganchada por **cirugía** en dos puntos:
  al final de `StartStepTime` y **antes** del branch de `OnVOFinished_Event`.
- **`BP_BreathOrb_SC.OrbRetire()`** — colgada del Tick después de `TickOrb`. Se destruye cuando ya se mostró
  (`bEverShown`), la etapa cerró (`Mode == -1`) y `RevealT < 0.02`.

🔴 **El cierre reusa `StepTimeDone` del director, no un camino nuevo.** Esa función ya trae la guarda
`WaitFor == "time"`, así que: **el cortafuegos de `StepTimes[1]` sigue vivo** y el que llegue primero cierra;
el segundo se ignora solo. Cero callejones sin salida sin escribir una línea de más.

## 👁️ Qué existe y qué no
Tres interruptores para componer la interfaz, **cada uno junto a lo que controla** en el panel (no en una
categoría aparte): `bShowWords` con los textos, `bShowDots` y `bShowMark` con la geometría.

Se aplican con **`SetVisibility` real** dentro de `PlaceWord`/`PlaceDot` — o sea **en el layout, no por frame**:
lo apagado no se dibuja ni cuesta fill-rate. El marcador lleva su propia línea al final de `Layout`, después
del `PlaceDot(Mark, 0)`, porque comparte función con los divisores pero **no** su interruptor.

✅ Verificado por medición, uno por uno: apagar cada interruptor deja invisible **sólo** lo suyo.

⚠ **Los tres nacen en `false` en una instancia que ya existía** (el motor estrena toda variable nueva en cero,
y para un bool eso es "apagado" = todo invisible). En instancias nuevas el CDO manda y arrancan en `true`.

## ⚠ Trampas pagadas (todas nuevas, todas caras)
1. 🔴🔴 **Los nombres de función chocan entre Blueprints y el DSL resuelve al equivocado — EN SILENCIO Y
   COMPILANDO.** `CallFunction|Apply` se cableó a `Class|BPInstructionsPanelSC|Apply`, `Advance` a
   `Class|BPBell|Advance`, y después `RingApply`/`RingAdvance` a `BP_ProtoSoul`. Lo mismo pasó con el
   **event dispatcher** `OnFinished`, que resolvió al de `BP_InstructionsPanel_SC` y ahí sí falló la
   compilación. **Sólo se detecta leyendo el grafo después de escribirlo**: si aparece `Class|OtroBP|MiFuncion`
   en vez de `CallFunction|MiFuncion`, es esto. Se resolvió con prefijos únicos (`BRingApply`, `BRingStep`,
   `OnRingFinished`) **verificados con `find_node_types` ANTES de escribir**.
2. **`for`, `if`, `switch`, `CastTo*` e `IsValid` terminan la lista de statements.** `Layout` se escribió
   **completamente desenrollado** (sin un solo bucle, con `select` en vez de ramas) justamente para no
   necesitar tres bucles seguidos. Con `Divisions ≤ 4` sale gratis y el grafo queda plano.
3. **Las variables se referencian por su CATEGORÍA, no por `Default`.** Al ponerles categoría, el id pasa
   a ser `Variables|A-Ritmo|GetDivisions` (espacios eliminados). `Variables|Default|` queda sólo para los
   **componentes**. Y ojo con la normalización: `bScaleToCycleTime` → **`GetScaletoCycleTime`** (la "to"
   en minúscula, y sin la `b`).
4. **`add_variable` quiere los tipos en minúscula**: `bool`, `int`, `float`, `string` — no `Boolean`/`Integer`.
5. **`get_actor_bounds` devuelve un cubo fijo de 256 cm** para estos actores (lo mismo para `BP_BreathOrb_SC`
   y `BP_InstructionsPanel_SC`). **No sirve para medir tamaños** — casi me manda a perseguir un bug que no existía.
6. 🔴🔴 **`set_properties` con varias propiedades juntas puede aplicar unas y otras no, devolviendo éxito.**
   Al crear los `Word0..3` mandé `staticMesh` + `overrideMaterials` + flags de sombra en **una sola llamada**:
   entró todo menos **`staticMesh`, que quedó en `None`**. Resultado: planos sin malla, invisibles, con material,
   escala, rotación y visibilidad **todos correctos al leerlos** — el síntoma perfecto para diagnosticar cualquier
   cosa menos la verdadera. Me costó varias rondas persiguiendo el material y la textura.
   👉 **Setear el mesh en su PROPIA llamada y verificarlo**, componente por componente. Yo verifiqué `RingFixed`
   y `Mark` en la primera tanda, y **no verifiqué los `Word*`** — la regla del proyecto aplicada a medias no sirve.
   ⚠ Y hay una segunda capa: la **instancia ya colocada guarda su propio override**, así que arreglar el CDO **no
   la cura**. Hubo que reponer el actor. Un `SetStaticMesh` por código con la ruta **entre comillas tampoco resuelve**
   (el literal no se convierte en referencia de asset): si hace falta por código, va por variable de objeto.
7. **El `WidgetComponent` recrea su widget en CADA reconstrucción del actor** (se vio con los nombres de
   instancia: `_90`, `_158`, `_92`, `_95`…). Por eso las letras que arma el Construction Script **se pierden**
   y el texto **no se previsualiza en el viewport del editor**, aunque sí se construye en Play (20 letras).
   Los anillos, divisores y marcador —que es lo que de verdad hay que autorar mirando— **sí se ven en vivo**.
8. 🔴 **`Appear` y `Play` como nombres de evento público: colisión instantánea.** Al llamarlos desde el
   director, `Appear` se cableó a **`Class|BPAlmaSC|Appear`** y `Play` a **`Components|Animation|Play`** — con el
   anillo como target, compilando. Renombrados a `BRingShow`/`BRingGo`/`BRingHalt`/`BRingHide`. Es la §219 otra
   vez, ahora en eventos custom: **cuanto más natural el nombre, más seguro que está tomado.**
9. 🔴 **Una condición de destrucción que se cumple al ARRANCAR.** `OrbRetire` borraba el orbe en el primer
   frame: la condición era `Mode == -1 && RevealT < 0.02`, y el sensor **ya está en −1 antes de que empiece la
   etapa**. Yo había identificado el riesgo ("hace falta un flag de *llegó a mostrarse*") y me convencí de que
   `Mode` no valdría −1 al inicio. Lo cachó el log de PIE, no yo. 👉 **Una condición de apagado se prueba con
   el caso de arranque antes que con el de cierre**, y un riesgo identificado se mitiga o se verifica — no se
   razona para descartarlo.
10. **`set_pin_value` sobre un `CallFunction`: el parámetro NO es el índice 1.** Los pines son 0=`execute`,
   1=`self` (oculto), 2=el primer argumento. Escribir en el 1 no da error y el argumento queda en su default —
   los dos `BreathRingCue` quedaron en `Mode = 0`. Leer los pines con `get_node_infos` antes de escribir.
11. **`ActorTools.set_actor_transform` SÍ funciona** en este build para un actor colocado, y en cambio
   `ObjectTools.set_properties` sobre su root component **se aplicó a medias** (tomó la X, ignoró la Z).
   Es al revés de lo que decía `toolsets.md`. Verificar siempre con `get_actor_transform`.

## Dónde está y cómo se prueba
Colocado en **`L_Entering_SC`** en **(1400, 0, 150)**, rotación identidad (el `Ring` ya trae el pitch).
Con `bAutoPlay` en true arranca solo al entrar a la sala. ⚠ En el editor el `BP_BreathOrb_SC` se ve a
escala 1 y lo tapa; en Play el orbe baja a 0.25 y deja de estorbar. **Arrastralo donde quieras** — no
depende de ningún TargetPoint.

## TODO
- [ ] 🔴 **Visor**: tamaño (44 cm de anillo a ~1 m), si las palabras se leen, si el cuerpo de 48 px es el correcto
      a esa distancia, y si el ritmo 4/4/4/4 se siente natural.
- [ ] Engancharlo a la obra: `bAutoPlay=false` + `Play()` desde [[BP_Director_Story]], y escuchar
      `OnRingFinished` para cerrar la etapa.
- [ ] Audio por fase / loop calzado al ciclo (el `LBreath` de [[BP_BreathPacer]] ya resolvió esto: loop de
      12 s contra un ciclo de 12 s; acá el ciclo es configurable, así que habría que estirar o cambiar el clip).
- [ ] Háptico suave al cambiar de tramo, cuando exista el framework 1.d.
- [ ] 🎨 **Arte**: reemplazar las tres texturas por las de Beltrán (letras tratadas, no una fuente). El pipeline
      ya es el definitivo — sólo cambia el PNG dentro de cada `MI_Word_*`.
- [ ] 🧹 **Barrer huérfanos**: una reescritura de `RingK` sobre el grafo existente dejó ~19 nodos sueltos. Correr `scripts/clean_orphans.py` — pero **commitear el `.uasset` antes**, como pide el propio script.
- [ ] Si alguna vez cambia mucho `Radius`, rehornear (la curvatura está atada al radio, no a los tiempos).

## Relacionados
[[BP_BreathPacer]] (el antecesor del esqueleto viejo — de ahí salen el arrastre del resto y el cierre por
reloj) · [[BP_Door_SC]] (la fórmula de `EaseCurve`; su `WBP_DoorTitle.BuildArc` fue el primer intento, descartado) ·
[[BP_BreathOrb_SC]] (comparte sala) · [[BP_Sensor_Soul]] (la respiración real; el anillo **no** la mide) ·
`M_SoulRing` · [[BP_SoulHUD_SC]] (de ahí la convención de Yaw 180 del `WidgetComponent`)
