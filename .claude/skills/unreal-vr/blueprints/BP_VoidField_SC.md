# BP_VoidField_SC + M_VoidDots_SC — profundidad sin geometria (Core/Light/)

> Creado 2026-09-04. Efecto 1.2 del [plan de la galeria](../../../../docs/PLAN-GALERIA-EFECTOS.md).
> **Estado: 🟡 compilado y colocado en `/Game/TestMeshes` (`VoidField_Test`, en 0/20000/200). Juzgado en el viewport. Falta el visor — y el visor es el unico lugar donde se puede juzgar de verdad, ver abajo.**

## Que es
Dos o tres cascarones concentricos a radios distintos con puntos resueltos **en el material**, sin textura y sin particulas. Al mover la cabeza las capas se desplazan a distinta velocidad, y **ese paralaje es lo unico que vende una escala infinita**: un gradiente de fondo, por lindo que sea, se lee plano.

El documento maestro ya lo habia decidido — *"la profundidad la van a dar las PARTICULAS, no el fondo"* — y esto da el mismo efecto con **3 draw calls** en vez de un sistema Niagara. Ademas, como es el mismo actor al principio y al final de la obra, es tambien la firma que cierra el arco.

## 🔴 Cascarones CUBICOS, no esfericos
Se usa el `Cube` del motor, no una esfera. Motivo: los puntos se distribuyen por **UV**, y una esfera UV **amontona todo en los polos** — justo donde mirás en un vacio. El cubo no tiene polos: cada cara lleva su UV 0..1 y la densidad queda pareja.

Y la forma del cubo es **invisible**: el material solo dibuja puntos sobre negro, no hay gradiente ni superficie que delate la geometria.

⚠ **La contra:** el patron es por cara, asi que en las 12 aristas del cubo el dibujo no continua. No se nota salvo que mires fijo una arista, y con tres cascarones a escalas distintas las costuras no coinciden. Si algun dia molesta, la salida es una proyeccion tipo cubemap desde `LocalPosition` (mas nodos, misma idea).

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

## 🔴 Lo que NO se puede juzgar en una captura
**El paralaje.** Una imagen fija muestra puntos; el efecto entero esta en que al mover la cabeza las capas se desplazan a distinta velocidad. En el editor se intuye moviendo la camara, pero **el veredicto real es el visor**. Si al probarlo no se siente profundidad, la palanca es separar mas los radios (por ejemplo 1000 / 3500 / 9000), no agregar puntos.

## TODO
- [ ] Juicio de Beltran y prueba en visor, sobre todo el paralaje.
- [ ] **Medir el fill**: son tres capas aditivas que ocupan la pantalla entera. Es el riesgo real de este efecto. Si aprieta, `bLayer2` off es lo primero.
- [ ] Rangos de slider a mano: Radius 300–20000 · Tiling 8–80 · DotSize 0,01–0,3 · Density 0–1 · JitterAmount 0–1 · Brightness 0–6 · FarDim 0–1 · Twinkle* 0–2.
