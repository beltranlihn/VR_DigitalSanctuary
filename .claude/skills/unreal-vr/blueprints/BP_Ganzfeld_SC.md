# BP_Ganzfeld_SC + M_Ganzfeld_SC — el cascaron sin borde (Core/Light/)

> Creado 2026-09-04. Efecto 1.1 del [plan de la galeria](../../../../docs/PLAN-GALERIA-EFECTOS.md).
> **Estado: 🟡 compilado, colocado en `/Game/TestMeshes` (`Ganzfeld_Test`, en 0/12000/200) y juzgado en el viewport. Falta el visor.**

## Que es
Una superficie grande y curva con un gradiente emisivo continuo: **sin esquina, sin borde, sin textura que de escala**. El ojo se queda sin referencia de profundidad y el cuarto deja de leerse como cuarto. Es el *Ganzfeld* de Turrell, y se hace con un material, no con luces.

Es la seccion 6 del documento maestro escrita como material — *"su tema es que no encuentras el borde: las superficies se disuelven"* — y hasta ahora la obra no tenia nada que hiciera eso: el haz y la niebla ponen luz EN el aire, pero las salas seguian teniendo paredes que se leian como paredes.

## `SM_GanzShell` — la malla
Esfera invertida generada por script (96 x 48 = **9024 tris**, radio 50 asi que el diametro es 100 y vale la convencion `escala = tamaño/50`). Sin colision.

🔴 **Por que una malla propia y no la esfera del motor:** el gradiente se calcula por pixel desde `LocalPosition`, y esa posicion se interpola LINEALMENTE a lo largo de cada triangulo. Con triangulos grandes la superficie interpolada se aparta de la esfera real y aparece una **discontinuidad de pendiente** en cada arista — bandas de Mach, justo en un gradiente suave que es donde mas se ven. Con 9k tris el error es despreciable.

⚠ **El winding no quedo como se esperaba.** Se emitio el OBJ con winding invertido y normales hacia adentro para tener un cascaron de una cara, pero el importador **espeja la Y tambien en las POSICIONES**, lo que invierte la mano y deja las caras mirando hacia afuera otra vez: desde adentro se veia **todo negro**. La salida fue poner el material en **two-sided**, que en un material OPACO es casi gratis (no hay overdraw; el depth test se queda con la cara mas cercana). Si algun dia hace falta una cara sola, hay que emitir el OBJ con winding normal.

## El material `M_Ganzfeld_SC` — unlit · **OPACO** · two-sided · Full Precision
🔴 **Opaco a proposito.** Es la unica superficie grande del proyecto que no es translucida, y eso es una ventaja: escribe profundidad, mata el overdraw de todo lo que quede detras, y como es la sala no hay nada que ver a traves.

| Termino | Como | Perillas |
|---|---|---|
| **Gradiente** | `h = saturate(LocalPosition.Z/100 + 0.5)` elevado a `GradientBias`, y `lerp(ColorBottom, ColorTop, h)`. La altura sale de la posicion LOCAL, asi que el gradiente siempre recorre el cascaron entero por mas que se lo escale o se lo achate | `ColorTop` · `ColorBottom` · `GradientBias` (1) |
| **Banda de horizonte** | `lerp(1, HorizonGlow, saturate(1 − \|h − HorizonPos\|·HorizonWidth))` — una franja mas clara a una altura elegible. En `HorizonGlow = 1` esta apagada | `HorizonPos` (0,5) · `HorizonWidth` (8) · `HorizonGlow` (1) |
| **Dither** | 🔴 el termino que hace o rompe el efecto, ver abajo | `DitherAmount` (4) |
| **Respiracion** (WPO) | `VertexNormalWS × BreathAmount × sin(t · BreathSpeed)` — el cascaron entero se expande y contrae. **Por reloj**, no por sensor: atarlo a la respiracion real es etapa posterior | `BreathAmount` (60 cm) · `BreathSpeed` (0,15) |

### 🔴 El dither, que es lo unico dificil de este material
Un gradiente suave sobre una superficie enorme es **el peor caso posible para 8 bits**: se ve escalonado. Y `DitherTemporalAA` **no sirve** en este proyecto porque no hay TAA (usamos MSAA).

La solucion que quedo es un **dither R2**, sin textura y sin filtrado:
```
px = ScreenPosition × ViewSize          // coordenada en PIXELES, no en UV de viewport
d  = frac(dot(px, (0.7548776662, 0.5698402909)))   // secuencia de baja discrepancia
Emissive += (d − 0.5) × DitherAmount / 255
```
⚠ **El primer intento fue con una textura de ruido muestreada en pantalla y NO dithereaba nada**: la UV era `ScreenPosition × 900`, o sea la textura teselada 900 veces, y con filtrado bilineal + mips el motor la promedia a un gris plano. Para dithear hace falta **un valor distinto por pixel**, y con textura eso obliga a acertar la escala exacta (`ViewSize/256`) y a desactivar mips. La version R2 no tiene ese problema y son cinco instrucciones.

**Medido, no estimado** (columna central de una captura, contando tramos de pixeles con el mismo valor):

| `DitherAmount` | tramos planos | largo medio | **largo maximo** |
|---|---|---|---|
| 0 (apagado) | 80 | 10,8 px | **32 px** — bandas obvias |
| 1,5 | 727 | 1,2 px | 23 px — quedan bandas en la zona mas plana |
| **4,0** | 857 | 1,0 px | **2 px** — sin banding |

Por eso el default es **4**. Bajarlo trae las bandas de vuelta.

## El BP
Un componente `Shell` (StaticMeshComponent, `SM_GanzShell`, sin sombras, sin colision, `bUseAsOccluder` off, **`boundsScale` 2** por el WPO) y una funcion `ApplyGanzfeld` en el Construction Script que pone la malla, calcula la escala y empuja las 10 perillas.

**El tamaño se autora en centimetros:** `ShellRadius` y `ShellHeight` (cat. *A - Forma*, default 1500 = 15 m de radio, 30 m de lado a lado), traducidos a `escala = cm / 50`. Separar radio de altura permite achatarlo en domo o estirarlo en tubo.

Categorias: `A - Forma` (Mesh/ShellRadius/ShellHeight) · `B - Color` (ColorTop/ColorBottom/Brightness) · `C - Gradiente` (GradientBias/DitherAmount) · `D - Horizonte` (HorizonPos/Width/Glow) · `E - Respiracion` (BreathAmount/BreathSpeed).

## Rangos sugeridos para los sliders (a mano en el editor; el MCP no expone esa metadata)
ShellRadius/Height 300–8000 · Brightness 0–3 · GradientBias 0,2–4 · DitherAmount 0–8 · HorizonPos 0–1 · HorizonWidth 1–40 · HorizonGlow 1–3 · BreathAmount 0–200 · BreathSpeed 0–1.

## TODO
- [ ] Juicio de Beltran y prueba en visor. **El riesgo real es el fill**: es una superficie que ocupa la pantalla entera. Al ser opaca deberia ser barata, pero hay que medirlo.
- [ ] Ver si el banding aguanta en el visor. En el editor hay tonemapper y en el APK no (`r.MobileHDR=False`), asi que la cuantizacion final es distinta — puede hacer falta subir `DitherAmount`.
- [ ] Probar si la esfera es la forma correcta o conviene un domo con paredes mas rectas. La variable `Mesh` permite cambiarla sin tocar nada mas.


## 🎨 TRES MODOS (2026-09-04) — porque un degradado fijo se lee como "una esfera con textura"
Beltrán, mirándolo en la galería: *"se nota demasiado que estoy en una esfera con una textura; debe sentirse como un espacio etéreo"*. El degradado por altura, por limpio que sea, **delata la geometría**: el ojo encuentra el eje y el horizonte, y desde ahí lee la esfera.

La perilla **`Mode`** (cat. *F - Modo*) elige entre tres campos, todos calculados sobre `normalize(LocalPosition)` — o sea sobre la DIRECCIÓN, nunca sobre UV:

| `Mode` | Qué es | Perillas propias |
|---|---|---|
| **0 · Horizonte** | lo que había: degradado por altura + banda de horizonte | `GradientBias`, `HorizonPos/Width/Glow` |
| **1 · Turrell** | resplandor **radial** desde una dirección: centro brillante que se abre hacia afuera en 3 colores. Sin eje vertical y sin horizonte, que es lo que hacía obvia la esfera | `CenterYaw`, `CenterPitch`, `InnerStop`, `OuterStop`, `Softness` |
| **2 · Fluido** | dos ruidos analíticos que se mueven lento y **mezclan los tres colores** como una tinta en agua. Es el que más borra la geometría: no hay ninguna dirección privilegiada | `FlowScale`, `FlowSpeed`, `FlowMix` |

Los tres usan **`ColorTop`, `ColorBottom` y el nuevo `ColorMid`** (2 o 3 colores según el modo). La mezcla entre modos son dos `Step` sobre `Mode`, así que se puede animar el cambio si algún día hace falta.

💡 **`VeilAmount` / `VeilScale` (cat. *C - Gradiente*) actúan en LOS TRES modos**: un ruido muy suave y muy lento que rompe la uniformidad perfecta. Es lo que saca la sensación de "textura pegada a una esfera" incluso en el modo horizonte. En 0 se apaga.

⚠ **Ruido analítico (`GradientALU`), no de textura** — acá se puede porque no alimenta ningún WPO. En la nube, ese mismo ruido de textura era el que hacía terrazas al desplazar vértices (ver `gotchas` §287-288).

## ⚠ La variable que efectivamente no hace nada: `BreathAmount`
Está conectada y empuja al material, pero **desde adentro de un cascarón uniforme no se percibe**: mover el radio hacia afuera y hacia adentro no cambia lo que ve el usuario, porque no hay referencia contra la cual medir el cambio. Si se quiere una respiración perceptible, tiene que modular **el color o el gradiente**, no la geometría.
