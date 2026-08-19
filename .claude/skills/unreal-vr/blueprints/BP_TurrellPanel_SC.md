# BP_TurrellPanel_SC + M_TurrellGradient — luz de Turrell sin luces

> `/Game/SoulCharger/Core/Light/` · creado 2026-08-18 · **una instancia colocada en el centro del hall** (`BP_TurrellPanel_SC_C_0`, en el **persistente**, en `0,0,230` con pitch 90).
> **Qué es:** un plano con un degradado radial de tres colores, animado, emisivo, pensado como banco de pruebas del vocabulario visual de James Turrell. El material es genérico: sirve en cualquier malla con UV0 sanas.

---

## Por qué existe
Pedido de Beltrán: *"lograr efectos como los espacios de james turrell, donde la luz transforma la arquitectura"*, sabiendo que **las luces en tiempo real son caras en VR** — que es exactamente lo que dice la doc de Meta (*"Using real-time lights sparingly… Bake lighting whenever possible"*, ver `references/materials-vr.md`). La salida es un shader: **cero luces, cero samplers, cero post**.

Y traía dos quejas concretas de intentos anteriores, que resultaron ser **dos problemas distintos con la misma pinta**. Ese fue el trabajo real de esta pieza.

## 🔴🔴 Los dos problemas del degradado animado en VR (y sus dos curas)

### 1. El movimiento se corta con el tiempo → es **precisión de coma flotante**, no el diseño de la animación
*"el movimiento se empieza a ver cortado a medida que avanza la experiencia"*. Es un bug conocido y documentado en Android: el material corre en **fp16 (half)**, el `Time` acumula, y llega un punto en que el avance entre dos cuadros es **menor que el ulp** — la animación pasa a moverse a saltos. En el hilo de Epic lo reportan **a los 3 minutos**, con el juego a 60 fps estables: *"Turning on the Use Full Precision option helped me"*.
→ [Why does a material slow down after a short period of time?](https://forums.unrealengine.com/t/why-does-a-material-slow-down-after-a-short-period-of-time/466050)

**La cura, doble:**
- **`floatPrecisionMode = MFPM_Full_MaterialExpressionOnly`** en el material. Es la opción intermedia (*"Use Full-Precision For Material-Expressions Only"*): fuerza fp32 en la matemática del material sin pagarlo en todo el resto del shader.
- **El nodo `Time` con `bOverride_Period = true`, `period = 300`.** El valor nunca crece más allá de 300 s, así que la precisión no se degrada ni aunque el editor lleve días abierto. Es cinturón y tiradores: aunque `Full Precision` ya alcanza para una obra de 15 min, esto lo vuelve independiente del tiempo de sesión.

### 2. El degradado se ve en bandas → es **la cuantización a 8 bits**, y se cura con **dither**
Un degradado grande y suave es el peor caso para 8 bits por canal: los escalones se ven como anillos concéntricos. La cura estándar es **romper la cuantización con ruido de amplitud ~1 LSB**.

⚠ **`DitherTemporalAA` NO sirve acá**: necesita TAA, y en Quest el post está en MSAA (`references/materials-vr.md` — *"Disable antialiasing in GammaLDR mode"*, queda MSAA). Hay que usar un dither **estático en espacio de pantalla**, que con MSAA es estable y no titila.

Implementación, ~6 instrucciones: `frac(dot(PixelPosition, (0.7548776662, 0.5698402910)))` — la **secuencia R2** de baja discrepancia, que reparte como blue noise con dos multiplicaciones y **sin textura**. Se centra en 0 y se escala por `Dither` (default **0.004** ≈ 1/255).

💡 `ScreenPosition` ya trae una salida **`PixelPosition`**: no hace falta multiplicar `ViewportUV` por `ViewSize`.

### 3. Y el emisivo que se quema a blanco → **clamp que preserva el tono**
Pedido explícito: *"algo de emisivo pero sin quemarse a blanco"*. Dos medidas:
- 🔴 **Nunca sumar capas de color, sólo interpolar.** Sumar sobre una base clara satura a blanco — es la lección que ya costó tiempo en `M_Alma` (el borde blanco, `gotchas.md` §136).
- **Normalización por el canal máximo:** `col / max(max(r,g,b), 1)`. Si ningún canal pasa de 1 es la identidad; si alguno se pasa, baja **todo el color junto**, así que **el tono se conserva exacto** en vez de derivar a blanco. Coste: ~5 instrucciones.
  ⚠ **Consecuencia para el autor:** `Brightness` por encima del punto donde el canal más alto llega a 1 **deja de hacer efecto** (se re-normaliza). Es el comportamiento buscado, pero conviene saberlo: la intensidad se lleva con los **colores**, no con `Brightness`.

## 🎨 Cómo se construye el degradado (y por qué no hay ruido)
Igual que en [BP_Alma_SC](BP_Alma_SC.md), **cero nodo `Noise`**: cuesta de 16 a 80 instrucciones **por octava** más lecturas de textura. Acá ni siquiera hace falta ruido — el movimiento sale de **tres senos** cuyas frecuencias no comparten divisor.

🔴 **El truco que hace que el bucle no se note y aun así cierre perfecto:** las tres frecuencias se expresan como **número entero de ciclos dentro del período de 300 s** (`Cycles`, default **2 / 3 / 5**, pasados por `round()` en el material). Al ser coprimos, el patrón compuesto no se repite hasta los 300 s completos; y al ser enteros, **el salto de `Time` al reiniciar el período es exactamente invisible**. Por eso el knob es "ciclos" y no "velocidad": cualquier valor que se escriba se redondea a un entero y sigue cerrando sin costura.

Las tres ondas se reparten así, **reusando** en vez de generar nuevas:

| Onda | Mueve |
|---|---|
| `s1`, `s2` | la **deriva del centro** (X e Y) |
| `s3` | el **latido del radio** |
| `s1 · s2` | el **corrimiento de `MidStop`** — el producto de dos senos da un batido de ritmo distinto **gratis**, sin un cuarto seno |

El color es una cadena de dos `lerp` sobre el radio normalizado: `Inner → Mid` hasta `MidStop`, `Mid → Outer` de ahí al borde. Los `saturate` de cada alfa hacen que cada tramo ignore al otro **sin un solo `if`**.

## Registro de variables
Las 15 son instance-editable y **se empujan al material desde el Construction Script** → se ven en el viewport al instante, sin Play.

| Grupo | Variables |
|---|---|
| **0 - Panel** | `Size` (4 × 4 m). Cuadrado a propósito: con `Aspect = 1` da un **círculo exacto**. |
| **A - Colores** | `ColorInner` · `ColorMid` · `ColorOuter` · `Brightness` (1.0) |
| **B - Forma** | `Center` (0.5, 0.5 en UV) · `Radius` (1 = el degradado llega justo al borde) · `Softness` (1.4, potencia sobre el radio) · `Aspect` (1) · `MidStop` (0.45) · `OuterStop` (0.75) |
| **C - Animacion** | `Cycles` (2,3,5) · `DriftAmount` (0.05) · `PulseAmount` (0.08) · `MidDrift` (0.06) · `Repeats` (1) · `Flow` (20) |

## 🌊 El flujo continuo: por qué la rampa tiene que CERRAR el círculo
Pedido de Beltrán: *"que se vaya agrandando constantemente y apareciendo los 3 colores, así la vemos mutar todo el rato"*.

Se resuelve corriendo el patrón hacia afuera sin parar: `q = frac(rp · Repeats − t · Flow/300)`. El `frac` es lo que lo hace **infinito**, y de ahí sale la restricción que define el diseño:

🔴 **Un `frac` salta de 1 a 0, así que la rampa de color TIENE que volver al color inicial o se ve una costura dura.** Por eso la rampa dejó de ser `Inner → Mid → Outer` y pasó a ser **cíclica**: `Inner → Mid(MidStop) → Outer(OuterStop) → Inner(1)`. Tres `lerp` en vez de dos. Sin ese tercer tramo, cada anillo que llega al borde reaparecería en el centro con un corte visible.

- **`Flow`** = expansiones por período de 300 s. **Se redondea a entero** por la misma razón que `Cycles`: entero ⇒ el reinicio de `Time` cae en el cierre del ciclo y no se ve. Default 20 = una expansión cada 15 s.
- **`Repeats`** = cuántas veces entra la rampa completa en el radio. 1 = un anillo; 3 = tres anillos concéntricos viajando.
- **`Flow = 0`** congela el flujo y deja el disco quieto (con la deriva y el latido de siempre).
⚠ Fuera del radio `rp` está saturado a 1, así que las esquinas del plano quedan de **color plano que cambia con el tiempo** en vez de anillos. Con `Radius = 1` es un área chica; con `Radius` bajo se nota más.
| **D - Calidad** | `Dither` (0.004) |

**No hay variable `MID` ni estado interno.** Ver abajo.

## Estructura
**Un solo grafo: el Construction Script. Sin Tick, sin funciones, sin eventos.** Toda la animación vive en el material, así que el BP no hace nada por cuadro — sólo traduce sus perillas a parámetros del material.

🔴 **Sin `CreateDynamicMaterialInstance` y sin variable `MID`:** se usan las variantes **`Set{Scalar,Color,Vector}ParameterValueOnMaterials`**, cuyo pin `self` es el **componente de malla**. Crean y reusan el MID internamente. Eso borra de un saque la variable, el nodo de creación, el `IsValid` — y la ambigüedad de la que se habla abajo.

## ⚠️ Trampas que costaron un intento
- 🔴🔴 **El bug que se comió el "radial": una constante creada sin valor nace en CERO y compila en verde.** De las dos constantes de valor 2 que arman el vector de aspecto, **una quedó sin setear**. Resultado: `float2(Aspect*2, 0)` → el eje Y se anulaba antes del `length` → el gradiente salía **lineal sobre un eje**, no radial. Beltrán lo reportó como **dos** quejas distintas (*"¿puedes hacerla radial?"* y *"no entendí lo del ColorOuter"*) y era **un solo cero**: al colapsar el gradiente a un eje, el color exterior quedaba en dos franjas del borde. ✅ Barrido obligatorio tras construir un material por script: listar **toda constante en 0**. Ver `gotchas.md` §145.
- 🔴 **`Rendering|Material|SetVectorParameterValue` y `SetScalarParameterValue` existen DUPLICADOS** (uno para *Material Parameter Collection*, otro para *MaterialInstanceDynamic*) y **el DSL agarra el de Collection**. Síntoma exacto: *"Could not connect pin MID to Collection"*. Se ve en `find_node_types`, donde los dos nombres aparecen **dos veces cada uno**. La salida buena no es desambiguar con `declaring_class` sino **usar las variantes `OnMaterials`**, que además dejan el grafo más chico.
- ⚠ **El material es `TwoSided = true` pero `BLEND_Opaque`**, no translúcido. Opaco a dos caras no tiene el problema de orden de dibujo que dejó a `M_Alma` "cuadriculada" (`gotchas.md` §135), y además evita el aviso de Meta de que la translucidez cuesta **~80% más de GPU por cuadro** que el masked.
- ⚠ **El piso de 13/255 del panel de Quest** (`references/materials-vr.md`) le pega de lleno a este material: el extremo oscuro del degradado **se aplasta a negro plano** en el visor aunque en el monitor se vea. Autorar `ColorOuter` **más arriba** de lo que pide el ojo en el editor.

## Estado
🟡 **Construido, compilado y colocado. Verificado en el editor** — la instancia ya tiene `MID_M_TurrellGradient_0` en `overrideMaterials`, que prueba que el Construction Script corrió y empujó los parámetros. **Falta el test en visor**, que es el único que vale para color (ni Link ni el previewer sirven, ver `materials-vr.md`).

**Pendiente natural:** medir el coste real cuando el panel llene la pantalla, que es el caso Turrell de verdad (la obra es **fill-rate bound**, no geometry bound).
