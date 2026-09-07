# BP_VoidField_SC + M_VoidDots_SC — profundidad sin geometria (Core/Light/)

> Creado 2026-09-04. Efecto 1.2 del [plan de la galeria](../../../../docs/PLAN-GALERIA-EFECTOS.md).
> **Estado: 🟡 compilado y colocado en `/Game/TestMeshes` (dos instancias; la autorada esta en 120000/100000/0). Juzgado en el viewport. Falta el visor — y el visor es el unico lugar donde se puede juzgar de verdad, ver abajo.**
> **2026-09-07: la deriva se reemplazo por GIRO por esfera** (`E - Giro`, 6 perillas) — ver esa seccion; la deriva vieja tenia un bug que hacia que las tres capas se movieran en la misma direccion.

## Que es
Dos o tres cascarones concentricos a radios distintos con puntos resueltos **en el material**, sin textura y sin particulas. Al mover la cabeza las capas se desplazan a distinta velocidad, y **ese paralaje es lo unico que vende una escala infinita**: un gradiente de fondo, por lindo que sea, se lee plano.

El documento maestro ya lo habia decidido — *"la profundidad la van a dar las PARTICULAS, no el fondo"* — y esto da el mismo efecto con **3 draw calls** en vez de un sistema Niagara. Ademas, como es el mismo actor al principio y al final de la obra, es tambien la firma que cierra el arco.

## 🔴 ESFERAS, y el patron sacado de la DIRECCION en 3D (no de la UV)
**Historia, porque el camino importa.** La v1 usaba **cubos** con el patron sobre la UV, para evitar que una esfera UV amontonara los puntos en los polos. Beltran lo probo y dijo lo obvio: *"se nota mucho la esquina"*. Y tenia razon — sobre un cubo la densidad angular no es pareja (hacia las esquinas la cara abarca mas angulo), asi que la esquina se dibuja sola aunque el material solo pinte puntos.

✅ **La salida no es elegir entre polos o esquinas: es no usar UV.** El patron ahora se calcula sobre **`normalize(LocalPosition)` × Tiling**, o sea una grilla de celdas **en 3D** muestreada por la superficie de la esfera:
- **Sin polos** (no hay lat/long), **sin costuras** (no hay caras), **sin esquinas** (no hay cubo).
- La distribucion es uniforme porque una esfera corta una grilla 3D de forma pareja.
- 💡 De regalo: el tamaño aparente de cada punto varia solo, segun que tan cerca del centro de su celda pasa la superficie. Es variacion organica que antes habia que fabricar.

⚠ **Dos consecuencias medidas al hacer el cambio:**
1. **Los puntos se achican**, porque ahora el punto es la interseccion de una bola 3D con la superficie, no un disco 2D. Hubo que compensar `DotSize` (0,098 → **0,16**) y `Density` (0,266 → **0,45**).
2. 🔴 **La malla tiene que ser DENSA.** Con el `Sphere` del motor se veian **facetas triangulares y anillos concentricos**: la grilla 3D revela la teselacion. Se usa **`SM_GanzShell`** (96×48, 9.024 tris, radio 50 — la misma del Ganzfeld). El `Sphere` del motor NO sirve para este material.

Escala del componente = `Radio / 50`, igual que antes.

## 🔴 El punto NUNCA puede salirse de su celda — el jitter se acota solo
Sintoma reportado por Beltran: *"los puntos cortan en los vertices de la geometria"*. **No eran los vertices**: eran los bordes de la **celda**. Un punto grande y muy jitereado se pasaba de su casilla, y el pedazo que asomaba pertenece a la celda vecina — que tiene otro hash y otro jitter — asi que no continua: **se corta con un borde recto**. Por eso se veian cuadrados y medias lunas, y solo en los puntos grandes.

La cuenta es simple: el punto llega hasta `DotSize × 1,8` de su centro, el centro puede estar a `JitterAmount / 2` del centro de celda, y la celda mide 1 → **`JitterAmount/2 + DotSize×1,8 ≤ 0,5`**. Con el pulso el radio crece hasta `×(1 + PulseAmount)`, asi que hay que contarlo tambien.

✅ El material lo resuelve solo: calcula el **radio maximo posible** (incluyendo el pico del pulso) y acota el jitter a lo que sobra:
```
Rmax = DotSize × 1,8 × (1 + PulseAmount)
jitterEfectivo = max(0, min(JitterAmount, (0,5 − Rmax) × 2))
```
Asi `JitterAmount` es un **maximo deseado**, no una promesa: si los puntos crecen, el jitter cede. Nunca hay cortes, con cualquier combinacion de perillas.

⚠ **El precio, y el criterio para elegir:** cuanto mas grandes los puntos, menos jitter les queda y **mas se nota la retícula**. Medido: `DotSize` 0,16 → jitter efectivo 0,16 (se insinua la grilla); `DotSize` **0,11 → jitter efectivo 0,43** (se lee como estrellas). El default quedo en **0,11** con `Density` 0,5.

## 🔴🔴 El corte de los puntos: era MI cableado, no la malla
Beltran reporto puntos cortados y lo atribuyo a los vertices de la esfera (*"en el cubo no pasaba"*). **La malla era inocente.** Lo que lo probo en una corrida: con `JitterAmount = 0` y puntos GRANDES no se cortaba **ninguno** — si fuera la teselacion, se cortarian igual.

La causa fue un error mio al pasar el jitter a 3D: conecte el `AppendVector` de tres hashes **directo al multiplicador, salteando el `− 0,5`**. Sin esa resta el desplazamiento era siempre **positivo y del doble del rango** (`[0, amt]` en vez de `[−amt/2, +amt/2]`), asi que la cuenta del margen que hace el recorte quedaba corta y los puntos se pasaban de su celda.

💡 **La pista que lo desatasco fue de Beltran:** *"sucede claramente cuando pasa de un lugar a otro moviendose"*. Un corte que aparece **con el movimiento** apunta al borde de la CELDA (el patron se desliza y los puntos cruzan casillas), no a un vertice, que estaria quieto. Los sintomas que dependen del movimiento acusan al sistema de coordenadas, no a la geometria.

## 🔴 TRANSLUCIDO, no aditivo — para que el color sea el que elegis
Nacio aditivo, que es lo comodo sobre negro: suma y no hay que ordenar nada. Pero al encender el fondo, Beltran vio lo inevitable: *"el material de los puntos se suma con el brillo del fondo y los colores se ven muy blancos"*. **Aditivo sobre un fondo claro siempre tiende al blanco** — el color elegido se pierde.

✅ Pasado a **`BLEND_Translucent`**, con la cadena partida en dos:
- **Emisivo** = `color × Brightness` — el color puro, sin la mascara.
- **Opacidad** = `dotm × centelleo × FarDim × alive` — la mascara, sin el brillo.

Asi, donde la mascara vale 1 se ve **exactamente el color elegido**; el fondo no se suma. Verificado sobre fondo beige: el azul se ve azul, el rojo rojo y el naranja naranja.

⚠ **Tres consecuencias del cambio, para no sorprenderse:**
- `Brightness` por encima de 1 ya **no ilumina de mas**: en translucido el color se mezcla, no se suma (y sin MobileHDR no hay rango para pasarse). Sirve para bajar, no para brillar.
- `FarDim` ahora **desvanece** las capas lejanas en vez de oscurecerlas. Es lo mismo sobre negro y mejor sobre un fondo claro.
- Los tres cascarones son translucidos entre si, asi que se ordenan por componente. Con puntos ralos no se nota; si alguna vez molesta, la perilla es `TranslucencySortPriority`.

## 🎨 Tres colores repartidos al azar
`DotColor`, `DotColor2` y `DotColor3` (cat. *C - Color*). El reparto usa un **hash propio e independiente** de los que ya existian (el del tamaño, el del jitter y el de la densidad) — reusar uno hubiera correlacionado color con tamaño y **se verian patrones**, que es justo lo que Beltran pidio evitar. Dos `Step` a 1/3 y 2/3 parten el azar en tres tercios iguales.

## 🌑 Fondo solido opcional
Un cuarto cascaron `Back` (mismo `SM_GanzShell`) con **`M_VoidBack_SC`** — unlit, two-sided, emisivo plano. Cat. *F - Fondo*: **`bBackground`** (on/off), `BackColor`, `BackBrightness` y `BackRadius` (9.000 por default, o sea por fuera de las tres capas de puntos). Es opaco, asi que dibuja primero y los puntos aditivos se suman encima.
⚠ Al agregar el componente a un BP que ya tenia una instancia colocada, la instancia lo recibio con los **defaults de fabrica** (§164): hubo que escribirle malla y material tambien a la instancia.

## El material `M_VoidDots_SC` — unlit · **aditivo** · two-sided
Aditivo a proposito: sobre negro suma sin problemas de orden, y las tres capas se acumulan solas.

```
uv    = TexCoord × Tiling
cell  = floor(uv)              f = frac(uv) − 0.5
n1    = frac(sin(dot(cell, (12.9898, 78.233))) × 43758.5453)     // hash por celda, sin textura
n2    = frac(sin(dot(cell, (93.9898, 67.345))) × 24634.6345)
n3    = frac(n1×7.31 + n2×3.17)                                   // tercer valor, barato
jit   = (append(n1,n2) − 0.5) × JitterAmount
d     = length(f − jit)
size  = DotSize × lerp(0.35, 1, n1)                               // tamaños variados
dotm  = saturate((size×1.8 − d) / (size×0.8))
alive = step(n3, Density)                                          // 🔴 celdas VACIAS
twk   = lerp(1, 0.5 + 0.5·sin(t·TwinkleSpeed + n2·2π), TwinkleAmount)
Emissive = DotColor × dotm × twk × lerp(FarDim, 1, n2) × Brightness × alive
```

🔴 **El `jitter` por celda y el `Density` son los dos que hacen el efecto**, y los dos se descubrieron mirando:
- **Sin jitter se ve la grilla** y el paralaje deja de leerse como estrellas.
- **Sin `Density` TODAS las celdas tienen punto**, y el resultado parece ruido de television, no un vacio. Poner celdas vacias fue lo que lo convirtio en un campo de estrellas.

**Medido** (cobertura de pantalla con puntos, camara en el centro): `Density` 1.0 → 6,0 % · 0,5 → 3,1 % · 0,25 → **1,45 %** (el default) · 0 → apagado. La relacion es lineal y 1,5 % es donde deja de leerse como ruido.

## El BP
Tres `StaticMeshComponent` (`Shell0/1/2`) con el `Cube` del motor. `ApplyVoid` pone escala y perillas; `ApplyVoidDensity` empuja la densidad.

🔴 **Las tres capas NO pueden compartir los mismos valores.** Con UV identicas los puntos caen en las mismas posiciones angulares y las tres capas **coinciden exactamente** — se ven como una sola, tres veces mas brillante, y el paralaje desaparece. Por eso el BP aplica multiplicadores **no enteros** por capa:

| Capa | Radio | Tiling × | DotSize × | Brillo × | Density × |
|---|---|---|---|---|---|
| 0 | `Radius0` (1200) | 1,0 | 1,0 | 1,0 | 1,0 |
| 1 | `Radius1` (2600) | **1,73** | 0,75 | 0,60 | 0,8 |
| 2 | `Radius2` (5200) | **2,91** | 0,55 | 0,35 | 0,6 |

Escala del componente = `Radio / 50` (el cubo del motor mide 100). `bLayer1` / `bLayer2` apagan las capas de atras.

Categorias: `A - Capas` (Radius0/1/2, bLayer1, bLayer2) · `B - Puntos` (Tiling 20, DotSize 0,09, Density 0,25, JitterAmount 0,7, Brightness 2,2) · `C - Color` (DotColor/2/3, FarDim 0,35) · `D - Vida` (TwinkleAmount 0,3, TwinkleSpeed 0,4) · **`E - Giro` (SpinSpeed0/1/2 + SpinAxis0/1/2)** · `F - Fondo` (bBackground, BackColor, BackBrightness, BackRadius).

Funciones, en el orden en que las llama el Construction Script: `ApplyVoid` → `ApplyVoidDensity` → **`ApplyVoidSpin`** → `ApplyVoidPulse` → `ApplyVoidColors` → `ApplyVoidBack`.

## 🌀 GIRO por esfera — cada cascaron rota en su sentido, a su velocidad y sobre su eje
Pedido de Beltran (2026-09-07): *"debemos tener control para animar las esferas con los puntitos; cada esfera debe poder animarse para girar en sentidos y velocidades distintas para lograr el efecto parallax"*. Reemplaza a la **deriva** anterior, que se borro entera.

🔴 **Por que la deriva vieja no servia, con dos causas medidas:**
1. **Era una TRASLACION, no una rotacion.** Sumaba `dir2D × Time × DriftSpeed` a la direccion 3D antes del `floor`/`frac`. El campo entero se corria en una sola direccion — se lee como "avanzar entre la nieve", no como un cielo que gira. Ademas el offset **crece sin cota** con `Time`, asi que a sesiones largas la precision float se degrada.
2. 🔴 **Las tres capas derivaban en la MISMA direccion.** El BP sumaba `+137` y `+251` al `DriftAngle` "en grados", pero el nodo `Cosine`/`Sine` del material toma su entrada en **vueltas** (`Period = 1`), no en grados: 137 y 251 son **enteros**, o sea vuelta completa → `frac = 0` → el mismo angulo que la capa 0. La unica diferencia real entre capas era la velocidad. **El paralaje direccional nunca existio.**

✅ **Ahora el material rota el campo con `RotateAboutAxis`**, que es el nodo del motor pensado justo para esto:
```
dir  = normalize(LocalPosition)
ang  = Time × SpinSpeed / 360        // SpinSpeed en GRADOS/seg; RotateAboutAxis toma vueltas (Period=1)
dir' = dir + RotateAboutAxis(normalize(SpinAxis), ang, pivot=(0,0,0), dir)
uv   = dir' × Tiling                 // y RECIEN AHI floor/frac
```
`RotateAboutAxis` devuelve el **desplazamiento** (`R·dir − dir`), por eso se le vuelve a sumar `dir`: la suma da `R·dir`, un vector unitario rotado. Al ser una rotacion pura no hay deriva acumulada ni perdida de precision: `Time` crece, el angulo da vueltas, y el campo nunca se aleja.

💡 **Por que la rotacion si da paralaje y la traslacion no:** con tres cascarones girando a velocidades distintas, mirando en cualquier direccion se ven tres capas de puntos cruzando el campo visual a ritmos distintos — exactamente la señal que el cerebro lee como distancia. Y con **ejes distintos** ninguna capa comparte polo con otra, asi que no hay una zona del cielo donde las tres se queden quietas juntas.

### Las perillas — cat. *E - Giro* (6 variables, instance-editable)
| Variable | Default | Rol |
|---|---|---|
| `SpinSpeed0` | **1,2** | Grados/seg de la capa CERCANA. **El signo es el sentido de giro.** |
| `SpinSpeed1` | **−0,7** | Idem capa media — negativa a proposito: gira al reves que la 0. |
| `SpinSpeed2` | **0,35** | Idem capa lejana. Mas lenta = se lee mas lejos. |
| `SpinAxis0` | (0, 0, 1) | Eje de giro de la capa cercana (se normaliza en el material). Z = gira como un cielo. |
| `SpinAxis1` | (0,25, 0,1, 1) | Eje inclinado — polo distinto al de la capa 0. |
| `SpinAxis2` | (−0,15, 0,3, 1) | Otro eje inclinado. |

🔴 **Ya NO hay multiplicadores hardcodeados por capa.** Antes el BP inventaba las razones (×0,62, ×0,38) y los angulos (+137°, +251°) adentro de `ApplyVoidDrift`. Ahora **cada esfera tiene su propia perilla**, que es lo que se pidio: se autora mirando, no se deduce de una tabla. La funcion es `ApplyVoidSpin` y solo empuja los seis valores a los tres cascarones.

**Ordenes de magnitud, para no perder tiempo:** una celda del patron subtiende ≈ `360/Tiling` grados (con `Tiling` 29 ≈ **2°**). O sea `SpinSpeed = 1,2` ≈ media celda por segundo — visible pero calmo. Por debajo de **0,2 °/s** deja de percibirse (es el mismo error que costo la deriva: *"se mueve" y "se ve que se mueve" son dos cosas distintas*). Arriba de ≈5 °/s empieza a parecer un protector de pantalla.

✅ **Verificado (2026-09-07)** con la camara dentro del campo, dos capturas del viewport a ~9 s: el patron esta **completamente reordenado** (25,2 % de los pixeles distintos, diferencia media 10,3/765), los puntos siguen dibujandose bien y una captura al cenit (pitch 89°) confirma que **no hay pinchazo de polo ni costura**. Falta el visor.

🔴 **Se anima en el EDITOR, no hace falta Play** — el nodo `Time` corre en el viewport. Si se ve congelado, lo que esta apagado es **Realtime** del viewport (el reloj de la barra, o `Ctrl+R`).

## 🔴 Lo que NO se puede juzgar en una captura
**El paralaje.** Una imagen fija muestra puntos; el efecto entero esta en que al mover la cabeza las capas se desplazan a distinta velocidad. En el editor se intuye moviendo la camara, pero **el veredicto real es el visor**. Si al probarlo no se siente profundidad, la palanca es separar mas los radios (por ejemplo 1000 / 3500 / 9000), no agregar puntos.

## TODO
- [ ] Juicio de Beltran y prueba en visor, sobre todo el paralaje (ahora por GIRO, no por deriva).
- [ ] Elegir mirando los seis valores de `E - Giro`: los defaults (1,2 / −0,7 / 0,35 °/s) son un punto de partida, no una decision autoral.
- [ ] **Medir el fill**: son tres capas aditivas que ocupan la pantalla entera. Es el riesgo real de este efecto. Si aprieta, `bLayer2` off es lo primero.
- [ ] Rangos de slider a mano: Radius 300–20000 · Tiling 8–80 · DotSize 0,01–0,3 · Density 0–1 · JitterAmount 0–1 · Brightness 0–6 · FarDim 0–1 · Twinkle* 0–2.
