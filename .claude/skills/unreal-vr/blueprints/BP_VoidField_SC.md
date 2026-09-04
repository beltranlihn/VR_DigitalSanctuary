# BP_VoidField_SC + M_VoidDots_SC — profundidad sin geometria (Core/Light/)

> Creado 2026-09-04. Efecto 1.2 del [plan de la galeria](../../../../docs/PLAN-GALERIA-EFECTOS.md).
> **Estado: 🟡 compilado y colocado en `/Game/TestMeshes` (`VoidField_Test`, en 0/20000/200). Juzgado en el viewport. Falta el visor — y el visor es el unico lugar donde se puede juzgar de verdad, ver abajo.**

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

Categorias: `A - Capas` (Radius0/1/2, bLayer1, bLayer2) · `B - Puntos` (Tiling 20, DotSize 0,09, Density 0,25, JitterAmount 0,7, Brightness 2,2) · `C - Color` (DotColor, FarDim 0,35) · `D - Vida` (TwinkleAmount 0,3, TwinkleSpeed 0,4).

## 🌊 Deriva animada — cada capa a su velocidad y en su direccion
Pedido de Beltran (2026-09-04): *"siento que no funciona si no esta animado y cada capa se mueve en una direccion o una velocidad distinta; lo interesante de ese efecto es cuando las cosas se mueven"*. Y es correcto: sin animacion el paralaje **solo existe si movés la cabeza**, asi que quieto se lee como una textura.

En el material, la UV tileada se desplaza antes de partirse en celdas:
```
dir = (cos(DriftAngle), sin(DriftAngle))
uv  = TexCoord × Tiling + dir × Time × DriftSpeed        // y RECIEN AHI floor/frac
```
Va **antes** del `floor`/`frac` a proposito: asi se mueve el campo entero (celdas incluidas) y no solo el punto dentro de su celda — si fuera despues, los puntos rebotarian dentro de su casilla en vez de viajar.

**Los multiplicadores por capa** (en `ApplyVoidDrift`) usan razones y angulos **no enteros** para que las tres nunca se sincronicen:

| Capa | Velocidad | Angulo |
|---|---|---|
| 0 (cerca) | `DriftSpeed` × 1,00 | `DriftAngle` + 0° |
| 1 | × 0,62 | + 137° |
| 2 (lejos) | × 0,38 | + 251° |

La capa cercana se mueve **mas rapido** que las lejanas, que es como se comporta el paralaje real. Perillas en *E - Deriva*: **`DriftSpeed` (0,12 = una celda cada ~8 s)** y `DriftAngle` (orientacion global del conjunto).

⚠ **El default arranco en 0,03 y hubo que subirlo: era una celda cada 33 segundos, o sea invisible.** Medido: a 0,03 el material SI animaba (dos capturas seguidas del editor ya salian distintas), pero el movimiento no se percibe. Para un campo procedural lento, **"se mueve" y "se ve que se mueve" son dos cosas distintas** — el numero hay que elegirlo mirando, no razonando.

✅ **Verificado con control positivo** (2026-09-04): apagando el centelleo, dos capturas con `DriftSpeed = 0` salen **byte a byte identicas**, y con `DriftSpeed = 4` salen distintas. Sin apagar el centelleo el test no probaba nada, porque el centelleo ya animaba solo.

🔴 **Se anima en el EDITOR, no hace falta Play** — el nodo `Time` corre en el viewport. Si se ve congelado, lo que esta apagado es **Realtime** del viewport (el reloj de la barra, o `Ctrl+R`): con Realtime off no se anima ningun material de la obra, ni este ni los haces ni la nube.
⚠ El campo del nivel tenia `TwinkleAmount = 0,58` autorado por Beltran: se leyo y se restauro despues del test, no se piso con el default.

## 🔴 Lo que NO se puede juzgar en una captura
**El paralaje.** Una imagen fija muestra puntos; el efecto entero esta en que al mover la cabeza las capas se desplazan a distinta velocidad. En el editor se intuye moviendo la camara, pero **el veredicto real es el visor**. Si al probarlo no se siente profundidad, la palanca es separar mas los radios (por ejemplo 1000 / 3500 / 9000), no agregar puntos.

## TODO
- [ ] Juicio de Beltran y prueba en visor, sobre todo el paralaje.
- [ ] **Medir el fill**: son tres capas aditivas que ocupan la pantalla entera. Es el riesgo real de este efecto. Si aprieta, `bLayer2` off es lo primero.
- [ ] Rangos de slider a mano: Radius 300–20000 · Tiling 8–80 · DotSize 0,01–0,3 · Density 0–1 · JitterAmount 0–1 · Brightness 0–6 · FarDim 0–1 · Twinkle* 0–2.
