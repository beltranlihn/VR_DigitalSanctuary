# BP_BubbleField_SC — el ESPACIO de esferas flotantes (Core/Light/)

> Creado 2026-09-04. Nace de una critica de Beltran a los tres efectos de Nico: *"los encuentro bastante fomes… la idea de estos materiales es armar entornos"*. `BP_RimShape_SC` es **una** forma; esto es **un campo** de N formas envolviendo al usuario, que es lo que lo convierte de prop en entorno.
> **Estado: 🟡 compila estricto, 48 instancias sembradas y verificadas en editor + PIE (visible/oculto por tags). Falta el juicio de Beltran y el visor.**

## Que es
Un `InstancedStaticMeshComponent` (**un solo draw call**) con N formas repartidas en un anillo alrededor del actor, todas con `M_RimOnly_SC` — el material de Nico, **sin tocarlo**. Como ese material ya trae el revelado por cercania de camara (`SphereMask` contra `CameraPositionWS`), **cada instancia aparece sola segun cuan cerca esta la cabeza**: se camina y las formas nacen adelante y se apagan atras. Eso sale gratis, es per-pixel y no cuesta ni un nodo de Blueprint.

## Registro de variables
| Variable | Default | Rol |
|---|---|---|
| `Count` | 48 | cuantas formas |
| `Seed` | 7 | semilla del hash — cambiarla re-baraja todo el campo |
| `AreaRadius` | 1400 | radio exterior del anillo (cm) |
| `InnerRadius` | 350 | **hueco central**: nada se siembra mas cerca que esto, asi el usuario no queda con una forma en la cara |
| `AreaHeight` | 500 | dispersion vertical (±250) |
| `SizeMin` / `SizeMax` | 80 / 320 | rango de tamaño en cm |
| `Mesh` | Sphere | malla intercambiable (el rim funciona en cualquiera) |
| `RimColor` · `RimPower` · `RimWidth` · `Brightness` | cian / 3 / 1 / 1.5 | el borde |
| `RevealAmount` · `RevealRadius` · `RevealHard` | 1 / 900 / 0.35 | 🔴 el revelado por cercania. **`RevealAmount` en 1 = solo se ve lo cercano** (es lo que hace el entorno) |
| `ContactFade` | 90 | DepthFade contra el piso |
| *(interna)* `MID` | — | material dinamico del ISM |

## Estructura del Construction Script
`SetStaticMesh` → `ClearInstances` → `CreateDynamicMaterialInstance` sobre el ISM → 7 escalares + 1 color por `Set{Scalar,Color}ParameterValueOnMaterials` → **`for` de `Count`**: cuatro llamadas a `FieldHash` (angulo, radio, altura, escala) y un `AddInstance` con el transform armado.

**`FieldHash(I, Salt) → float`** es el generador determinístico: `abs(frac(sin(I·Salt + Seed) · 43758.5453))`. Una sola funcion, cuatro usos con distinta sal — asi el campo es **reproducible** (misma seed = mismo campo) y cambiar una perilla no lo re-baraja.

🔴🔴 **La trampa que costo una pasada: `Math|Float|Fraction` de Unreal CONSERVA EL SIGNO** (`frac(-2.3) = -0.3`). Como `sin()` es negativo la mitad del tiempo, el hash devolvia negativos y **las instancias salian con escala negativa** (malla invertida) y radios menores que `InnerRadius`. Se detecto **leyendo `perInstanceSMData` y mirando los numeros**, no mirando el viewport. Fix: envolver en `Math|Float|Absolute(Float)`. **Regla general: cualquier hash `frac(sin(x)*k)` portado de shaders necesita `abs` en Blueprint.**

## 🆕 2026-09-04 (tarde) — las burbujas, tras el juicio de Beltran
Vio el campo y dijo: ***"las bubbles estan lindas"*** — es lo unico de los tres efectos que le gusto. Pidio tres cosas, y las tres se resolvieron **en el material**, sin custom data ni logica de Blueprint:

**Un hash POR INSTANCIA**, sacado de `ObjectPositionWS` (en un ISM devuelve la posicion de cada instancia): `frac(sin(dot(pos, (12.9898, 78.233, 37.719))) · 43758.5453)`. Un solo valor 0-1 distinto por burbuja, que alimenta las dos cosas de abajo.
💡 A diferencia del hash de Blueprint, **aca NO hace falta `abs`**: el `frac` de HLSL ya devuelve positivo.

| Pedido | Como se hizo | Perillas |
|---|---|---|
| *"distintos colores dentro de paletas de azulados"* | `lerp(RimColor, RimColorB, hash · ColorVariation)` — cada burbuja cae en un punto distinto entre los dos azules | `RimColorB` (azul claro) · `ColorVariation` (1 = variacion total, **0 = todas iguales**, que es el default del material para no cambiarle nada a `BP_RimShape_SC`) |
| *"hazlas pulsar suavemente"* | **WPO**: `VertexNormalWS · PulseAmount · sin(Time·PulseSpeed + hash·2π)` — la esfera se infla y desinfla de verdad, y **la fase sale del hash**, asi que cada una respira a su tiempo | `PulseAmount` (4 cm) · `PulseSpeed` (0.22 Hz) |
| *"aleatorio de tamaño"* | rango ampliado | `SizeMin` 60 → `SizeMax` 420 |

⚠ **El material es de Nico y lo usa tambien `BP_RimShape_SC`.** Los tres parametros nuevos tienen **default 0** (o sea: sin variacion y sin pulso), asi que sus tres formas sueltas siguen viendose exactamente igual. Solo el campo los enciende.

## Como se usa
Se coloca donde deba estar el centro del campo y se ajusta `AreaRadius`/`Count`. Para la obra:
- **Surrounding**: el cascaron que se insinua al acercarse.
- **La sala final que se abre**: animar `DissolveThreshold` del material (hoy no expuesto en este BP; se agrega si hace falta).
⚠ El revelado **solo se juzga moviendose**: en una captura estatica se ve un anillo de formas cercanas y nada mas.

## Session log
- **2026-09-04**: creado. ISM + 17 variables + `FieldHash`. CS por DSL a la primera (el DSL inserto solo las conversiones int→float del indice). Compila con `warnings_as_errors`. Colocado en la estacion 8 de la galeria con `GALSTATION` + `GAL_8`, envuelto en un `BP_Ganzfeld_SC` verde-azul. Bug del `Fraction` con signo encontrado y corregido por cirugia. Verificado en PIE: el pawn cae en su anchor, campo y cascaron visibles, la estacion vecina oculta.

## TODO
- [ ] Juicio de Beltran + visor (el paralaje y el revelado son de visor).
- [ ] Exponer `DissolveThreshold`/`DissolveEdge` si se quiere el campo que se quema.
- [ ] Medir fill en APK: son N siluetas translucidas; el ISM ahorra draw calls, no fill.


## 🫧 2026-09-04 (noche) — pasa a ser EL BP de los espacios de esferas
Beltran, mirando el campo: ***"lo que me gusto es armar espacios de esferas aleatorias, asi que ese es el BP que queremos lograr, no solo el material"***. El BP ya existia (yo lo habia presentado desde el material, que confundio); lo que faltaba era que se **llamara** y se **autoreara** como lo que es. Tres cambios:

1. **Renombrado** `BP_RimField_SC` → **`BP_BubbleField_SC`** (`AssetTools.move`, la instancia de la galeria siguio enganchada sola).
2. **Las 20 perillas quedaron en categorias y todas instance-editable**, que es lo que hace autorable el BP desde el panel: *A - Campo* (Count · Seed · AreaRadius · InnerRadius · VerticalScale) · *B - Esferas* (Mesh · SizeMin · SizeMax) · *C - Color* (RimColor · RimColorB · ColorVariation · Brightness) · *D - Borde* · *E - Pulso* · *F - Revelado* · *G - Contacto*.
3. 🔴 **La distribucion pasa de ANILLO a ESFERA COMPLETA**, a pedido suyo: *"quiero ver esferas por arriba, lados, delante, atras, dejando un espacio al centro que es donde va el pawn"*. El CS ahora siembra en una **cascara esferica**: azimut `u·2π`, y **`cosPhi = 2v−1` uniforme** (que es lo que reparte parejo sobre la esfera; usar el angulo directo amontona en los polos), `sinPhi = sqrt(1−cosPhi²)`, radio entre `InnerRadius` y `AreaRadius`. `VerticalScale` achata el campo (1 = esfera, <1 = lenteja).
   `AreaHeight` quedo sin uso y se reemplazo por `VerticalScale`.
   ✅ **Medido por bounds**: 32 m en X, 32 m en Y y **27 m en Z** (antes Z era 4 m: un disco).

### 🔴 Y el bug del color que reporto ("estas orbes deben ser de distintos colores")
Las burbujas salian **todas del mismo color** y pulsando al unisono. Causa: **`ObjectPositionWS` en un InstancedStaticMesh devuelve la posicion del COMPONENTE, no la de cada instancia** — asi que el hash daba el mismo numero para las 48. Fix: **`PerInstanceRandom`**, el nodo del motor hecho exactamente para esto (un aleatorio por instancia de ISM/foliage). Se borro toda la cadena del hash de posicion.
💡 En un mesh NO instanciado `PerInstanceRandom` devuelve 0 → `BP_RimShape_SC` sigue viendose igual, sin variacion ni pulso. El default se mantiene sano solo.
⚠ **Regla general: para variar POR INSTANCIA en un ISM, `PerInstanceRandom`. `ObjectPositionWS` NO sirve.**


## 🌊 Wobble y esfera densa (2026-09-04, cierre)
Beltran: ***"el entorno de esferas ya esta hermoso y me gusta asi como esta"***, con dos pedidos y una definicion de que es lo importante: *"agreguemosle un poco de wobble suave como ya lo tenia el material de alma, y le dejamos una esfera con mas poligonos. Pero **la gracia de este entorno es el develado. Eso es lo rico**"*.

**El wobble** es la receta de [[BP_Alma_SC]] portada al `M_RimOnly_SC`: **suma de dos senos con frecuencias no enteras** sobre la posicion local del vertice, desplazando por la normal. Nada de `Noise` (la leccion de Alma: 16-80 instrucciones por octava).
```
d  = dot(LocalPosition, (1, 0.73, 1.37)) · WobbleScale
t  = Time · WobbleSpeed
w  = ( sin(d + t) + sin(d·1.9 − t·0.7) ) · WobbleAmount
WPO = VertexNormalWS · ( pulso + w )        ← el pulso y el wobble SUMAN sobre la misma normal
```
💡 Se suman los dos **escalares** y se multiplica **una sola vez** por la normal: un multiply vectorial menos.
Perillas (cat. *E - Pulso*): `WobbleAmount` 3 cm · `WobbleScale` 0.045 (tamaño de la onda sobre la superficie) · `WobbleSpeed` 0.6.

**La malla**: pasa del `Sphere` del motor a **`SM_AlmaSphere`** (la icoesfera de Alma, **5.120 tris, sin polos pinchados**) — el wobble necesita densidad y esa malla ya existia en el proyecto, no se creo nada.

🔴 **Presupuesto a vigilar**: con `Count` 110 son **~563.000 triangulos** en un solo draw call, y cada vertice corre el WPO. Es un numero alto para Quest aunque el proyecto sea fill-rate bound. Si en visor pesa, las palancas en orden: bajar `Count`, o hacer una copia de la esfera con LODs (**no tocar `SM_AlmaSphere`, que es de Alma**).

## Lo que hay que preservar
🔴 **La gracia del efecto es el REVELADO** (dicho por Beltran). Cualquier ajuste futuro — colores, pulso, wobble, cantidad — no debe competir con eso: las esferas tienen que seguir naciendo al acercarse y apagandose al alejarse. `RevealAmount` en 1 y `RevealRadius` acorde al tamaño del campo.


## 🪼 Deriva y estiramiento: el espacio surreal (2026-09-04, cierre)
La intencion que fijo Beltran: ***"armar un entorno como si estuvieramos bajo el agua en un entorno de medusas, que es un ambiente muy agradable"***, y despues: *"que las esferas tengan deriva, alguna deformacion distinta, algo que lo haga sentir que estamos en un espacio muy surreal"*.

🔑 **La idea que lo resuelve: lo surreal no es el movimiento, es que CADA ESFERA OBEDEZCA UNA LEY DISTINTA.** Las dos cosas nuevas sacan su direccion del **mismo `PerInstanceRandom`**, asi que ninguna se mueve ni se deforma como su vecina, y no hace falta ni un dato extra por instancia.

**El eje propio de cada esfera** (se calcula una vez y sirve para las dos):
```
ang = PerInstanceRandom · 2π                      ← ya existia, es la fase del pulso
dir = ( cos(ang), sin(ang), cos(ang·2.7) )        ← un vector distinto por instancia
```

| Efecto | Formula | Perillas (cat. *E - Pulso*) |
|---|---|---|
| **Deriva** — la esfera viaja despacio en SU direccion y vuelve | `WPO += dir · sin(Time·DriftSpeed + ang) · DriftAmount` | `DriftAmount` 90 cm · `DriftSpeed` 0.09 |
| **Estiramiento** — se alarga a lo largo de SU eje, oscilando entre gota y esfera | `WPO += dir · dot(Normal, dir) · sin(Time·StretchSpeed + ang) · StretchAmount` | `StretchAmount` 0.35 · `StretchSpeed` 0.13 |

El `dot(Normal, dir)` es lo que convierte una traslacion en una **deformacion**: los vertices del lado del eje se van hacia afuera y los del lado opuesto hacia adentro. Con el signo oscilando, la esfera pasa de estirada a achatada por el mismo eje.

**El WPO completo del material queda:**
```
WPO = Normal · (pulso + wobble)   +   dir · deriva   +   dir · estiramiento
```
Las tres capas tienen periodos distintos y sin relacion entera (0.35 / 0.6 / 0.09 / 0.13 Hz), asi que **el conjunto no repite** — es la misma idea de las frecuencias no enteras de Alma, llevada al campo entero.

⚠ **Costo**: son 4 senos/cosenos mas **por vertice**, sobre ~123 instancias × 5.120 tris. Los defaults son suaves a proposito. Si en visor pesa: bajar `Count` antes que apagar efectos, porque el numero de vertices es el multiplicador de todo esto.


## 🌊 El medio submarino de la estacion 8 (2026-09-04)
Las tres capas que faltaban para que se lea **agua** y no vacio. **Ninguna necesito codigo nuevo**: son actores que ya existian, colocados con `GALSTATION` + `GAL_8` y configurados desde sus propias perillas — que es justo lo que pidio Beltran (*"que tengan perillas para yo jugar con ellos"*).

| Capa | Que se uso | Perillas para jugar |
|---|---|---|
| **Motas suspendidas** (marine snow) | **`BP_VoidField_SC`** — 3 cascarones de puntos procedurales, 3 draw calls, **sin Niagara**. Tiene deriva propia | `density` 0.45 · `dotSize` 0.13 · `driftSpeed` 0.05 · `driftAngle` · `twinkleAmount` 0.35 · `brightness` 0.7 · `farDim` 0.55 · los **3 dotColor** · `radius0/1/2` (700/1500/2600) |
| **Luz desde la superficie** | **3 × `BP_LightShaft_SC`** verticales, muy anchos (`Spread` 11-17) y tenues (`Intensity` 0.22-0.35), a distinta altura y grosor | `Intensity` · `Spread` · `SmokeAmount` (0.5-0.6, es lo que da el polvo en el haz) · `SmokeSpeed` · `BeamColor` · `EdgeSoft` · `LengthFade` |
| **Gradiente de profundidad** | el `BP_Ganzfeld_SC` de la estacion | `colorTop` (celeste de superficie) → `colorMid` → `colorBottom` (casi negro), `gradientBias` 1.15, `horizonPos` 0.72 |

🔴 **`bBackground = false` en las motas**: el VoidField trae su propio fondo esferico y taparia al Ganzfeld. Se apaga y manda el cascaron de la estacion.
🔴 Los haces van con **`bShowFloorGlow` y `bShowSourceGlow` en false**: no hay piso ni ventana que justifique el pozo de luz ni el disco fuente; aca el haz es solo el volumen de luz en el agua.
✅ **Verificado en PIE**: motas y haces de la 8 visibles, y el `BP_VoidField_SC` de la estacion 4 (el de Beltran) **oculto** — las dos instancias del mismo BP no se contaminan porque la pertenencia es por tag.

⚠ **Fill-rate**: se sumaron 3 haces translucidos + 3 cascarones de puntos a un campo que ya tiene ~123 esferas translucidas. **Es la combinacion mas cara de la galeria y solo se juzga en el visor.** Si hay que recortar, el orden sugerido: primero un haz, despues `Count` de las esferas, y las motas al final (son las mas baratas y las que mas "agua" aportan).


## 🌬️ 2026-09-17 — APARICIÓN y TAMAÑO con la respiración ([[BP_BreathManager_SC]])
Pedido de Beltrán: *"Bubbles, pueden ser tamaños y aparición"*. Y la regla de este BP: **la gracia es el develado** → la respiración pasa a manejarlo.

- **Material `M_RimOnly_SC`** (compartido con `BP_RimShape_SC`: todo nace en 0 → idéntico):
  1. `Custom` **`BreathReveal`** (`Val`=`RevealRadius`) → `SphereMask_0.Radius`.
  2. **Inflado proporcional a cada burbuja**: `LocalPosition.XYZ` → `Transform` (vector, Local→World: usa la escala de la instancia del ISM) → `Custom` **`BreathInflate`** = `LPW·(max(S,0)·In + max(−S,0)·Out)` → `Add_11(Add_10, inflado)` → WPO.
- **BP**: perillas `BreathRevealIn/Out` · `BreathSizeIn/Out` + `ApplyBreath` (a `Shapes`) colgado del **`Completed` del `ForLoop`**. No del cuerpo del bucle, que correría 123 veces.
- **Instancia `GAL_8_RimField`**: `RevealIn 0,35` (1192 → 1609 ≈ `AreaRadius` 1600: aparece todo el campo) · `RevealOut −0,5` (→ 596: solo lo más cercano) · `SizeIn 0,2` · `SizeOut −0,15`. Verificado en el MID.
- 👁️ Se ve en el editor con `PreviewBreath` del manager (el develado igual se juzga moviéndose).
- ⚠ Inflar suma fill en la estación más cargada de la galería.


### 🌬️ 2026-09-17 (2ª pasada) — curva SUAVE y rango exagerado
Beltrán tras probar: *"llegó muy duro a los valores máximos y mínimos, no suave como con la esfera"* y *"un poco más exagerados"*.
- **Causa (en el manager, no acá):** `BreathSigned` era `clamp(gain·y)` → con ganancia 1,5 una respiración normal chocaba contra ±1 y quedaba plana. Ahora es `k·y/(1+(k−1)|y|)` (techo suave, `SignedGain` 2).
- **Mapeo nuevo del consumidor** (sin quiebre en 0 aunque las ganancias sean asimétricas): `m = 1 + S·lerp(−Out, In, smoothstep((S+1)/2))`. `In` = fracción a inhalación plena, `Out` = a exhalación plena, igual que antes.
- `BreathReveal` y `BreathInflate` con la curva suave.
- **Valores**: `RevealIn 0,5` (1192 → 1788: aparece todo) · `RevealOut −0,65` (→ 417 ≈ `InnerRadius`: solo asoman las más cercanas) · `SizeIn 0,35` · `SizeOut −0,3`.


### 🌬️ 2026-09-17 (3ª pasada) — acompañar la respiración lenta, suavidad de resorte, más exagerado
Beltrán: *"si hago una respiración lenta deben demorarse más en llegar al máximo o mínimo, acompañando mi movimiento"* · *"sigo sintiendo que está un poco duro"* · *"los valores más exagerados, menos el metaball"*.
- **Causa (en el manager):** (1) `HorizTau` 3 s: la base del band-pass alcanzaba a una respiración lenta a mitad de la inhalación → el pico llegaba ANTES del final; (2) dos saturaciones encadenadas (`x/(1+|x|)` del nivel y el techo suave de `SignedGain`) = una sola muy comprimida: casi todo el recorrido quedaba pegado al máximo.
- **Arreglo (manager):** `HorizTau` **6**; `S` sale del band-pass CRUDO en cm (`x = (HFast−HSlow)·SignedGain`, `SignedGain` 1 = 1 cm) con codo suave `x/(1+|x|³)^(1/3)` (lineal hasta ~0,7) y pasa por un **resorte críticamente amortiguado** (`SmoothFreq` 6): velocidad continua, sin rebote.
- ✅ Medido en PIE con respiración de prueba de 10 s: el máximo llega al final de la media onda (no antes), la velocidad de `S` sube y baja suave.
- **Valores**: `RevealIn 0,8` · `RevealOut −0,8` · `SizeIn 0,6` · `SizeOut −0,45`.
