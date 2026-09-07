# BP_Ganzfeld_SC + M_Ganzfeld_SC — el cascaron sin borde (Core/Light/)

> Creado 2026-09-04. Efecto 1.1 del [plan de la galeria](../../../../docs/PLAN-GALERIA-EFECTOS.md).
> **Estado: 🟡 compilado y colocado en `/Game/TestMeshes` en dos estaciones (`GAL_3_Ganzfeld` en 90000/100000/0, autorado; `GAL_9_Ganzfeld` en 270000/100000/0). Juzgado en el viewport. Falta el visor.**
> **2026-09-07: solo se usa el MODO 2 (fluido)** — las perillas de los modos 0 y 1 estan ocultas; el codigo de los tres sigue entero. Ver la seccion al final.

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

Categorias: `A - Forma` (Mesh/ShellRadius/ShellHeight) · `B - Color` (ColorTop/ColorMid/ColorBottom/Brightness) · `C - Gradiente` (GradientBias/DitherAmount/VeilAmount/VeilScale) · `D - Horizonte` (HorizonPos/Width/Glow) · `E - Respiracion` (BreathAmount/BreathSpeed) · `F - Modo` (Mode) · `G - Fluido` (FlowScale/FlowSpeed/FlowMix).

🔴 **Desde 2026-09-07 varias de esas perillas estan OCULTAS** (solo queda el modo 2) — ver la seccion "SOLO QUEDA EL MODO 2" mas abajo.

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


## 🔴🔴🔴 El modo FLUIDO: por qué salían líneas, y la construcción correcta
Beltrán pasó una referencia (gradient-noise multicolor, tipo Freepik) y con eso se entendió el error de fondo.

**Lo que yo hacía mal:** elegir el color con un **umbral sobre un solo ruido** — un `Step`, una rampa de tres paradas, una tienda. Da igual la forma: **todo umbral sobre un campo suave dibuja una línea de contorno.** El color del medio queda atado al cruce, y donde el ruido cruza rápido, esa banda se ve como una línea fina. Probé rampa, tienda y tienda normalizada; las tres son la misma función y las tres dan línea. En la referencia **no hay ningún umbral**.

✅ **La construcción correcta: un campo de ruido INDEPENDIENTE por color, como PESO.**
```
w1 = Noise(p)            w2 = Noise(p + off2)        w3 = Noise(p + off3)
color = (C1·w1 + C2·w2 + C3·w3) / (w1 + w2 + w3)
```
Los tres colores están presentes **en todos lados** en distinta proporción, y no hay ningún punto de corte. Nunca aparece una línea, con ninguna combinación de perillas.

💡 **Y de regalo, resuelve el otro pedido: "que nunca se quemen a blanco".** Al dividir por la suma de los pesos, el resultado es una **combinación convexa** — matemáticamente no puede salirse del triángulo que forman los tres colores. **Es imposible que se vaya a blanco.**
⚠ **Lo único que sí puede quemarlo es `Brightness > 1`**, que multiplica después. Estaba en **2,65** y por eso todo tendía al blanco. Con la mezcla convexa, `Brightness` tiene que quedarse **en 1 o menos**: sirve para bajar, nunca para subir.
⚠ `outputMin` de los tres ruidos en **0,3** (no 0): si un peso se acerca a cero, la división lo amplifica y reaparecen filamentos.

## 🔢 `Mode` es un ENTERO
0 = Horizonte · 1 = Turrell · 2 = Fluido. La variable del BP es `int` y se convierte a float al empujarla al material (`* 1.0`, porque `Conv_IntToFloat` no existe como nodo del DSL).

## 🔴 SOLO QUEDA EL MODO 2 (2026-09-07) — decision autoral de Beltran
*"Ya no tendremos 3 opciones, solo dejaremos el mode 2. Dejar solo las perillas de variables que afectan al mode 2. No elimines del codigo los otros, simplemente quita las perillas de esos otros modos."*

🔴 **El CODIGO de los tres modos sigue INTACTO** — material y `ApplyGanzfeld` no se tocaron. Lo unico que cambio es la **superficie de autoria**: las perillas de los modos 0 y 1 se pasaron a **Instance Editable = false**, asi que desaparecen del panel del actor (y del de Class Defaults). Volver atras es un click por variable, sin reconstruir nada.

| Estado | Variables |
|---|---|
| **Ocultas** (modo 0) | `GradientBias` · `HorizonPos` · `HorizonWidth` · `HorizonGlow` |
| **Ocultas** (modo 1) | `CenterYaw` · `CenterPitch` · `InnerStop` · `OuterStop` · `Softness` |
| **Oculta** (ya no se elige) | `Mode` — el default del CDO paso a **2** |
| **Visibles** (afectan al fluido) | `Mesh` · `ShellRadius` · `ShellHeight` · `ColorTop` · `ColorMid` · `ColorBottom` · `Brightness` · `DitherAmount` · `VeilAmount` · `VeilScale` · `FlowScale` · `FlowSpeed` · `FlowMix` · `BreathAmount` · `BreathSpeed` |

💡 **Por que ocultar y no borrar es lo correcto aca:** la mezcla entre modos son dos `Step` sobre `Mode`, o sea que las tres ramas se **calculan igual** y se pesan; con `Mode = 2` las ramas 0 y 1 pesan 0 y sus perillas no pueden afectar nada. No hay riesgo de que una perilla oculta este haciendo algo por atras. (Costo de shader: las tres ramas siguen compilando — si algun dia aprieta el fill en el visor, ahi si conviene podar el material de verdad.)

⚠ **Las dos instancias colocadas quedaron en `Mode = 2`.** `GAL_3_Ganzfeld` ya estaba autorado en 2; **`GAL_9_Ganzfeld` estaba en 0 con todos los demas valores en default** y paso a 2 al recompilar (no tenia override propio, heredaba del CDO). O sea: **el aspecto de la estacion 9 cambio** — si ahi se queria el degradado por horizonte, hay que decidirlo de nuevo.
⚠ Consecuencia tecnica: una variable con Instance Editable en false **tampoco se puede escribir por `ObjectTools.set_properties`** sobre la instancia (falla con *"could not be set"*). Es el modo barato de VERIFICAR que quedo oculta — y el aviso de que para cambiarla hay que volver a habilitarla.

## ⚠ Cicatriz de proceso, para no repetirla
Este material se enredó por **reusar nodos identificándolos por nombre** (`LinearInterpolate_5`, `_6`…) en vez de mapear la cadena antes de tocar. Reescribí sin querer los nodos del modo Turrell, y por eso `Softness` dejó de responder. **Antes de cirugía sobre un material grande: recorrer la cadena desde `MP_EmissiveColor` hacia atrás y anotar los nombres.** Cuesta una llamada.


## 🔴🔴 2026-09-07 — las perillas `Flow*` no hacian NADA, y por que
Beltran: *"las perillas de flow no hacen nada"*. Tenia razon, y la causa es exactamente la **cicatriz** que este tracker ya avisaba: al reconstruir el modo fluido con los tres ruidos como peso, la cadena NUEVA (`Noise_4/5/6`) se enchufo a los nodos equivocados y quedo asi:

| Entrada del fluido | Estaba conectada a | Deberia ser |
|---|---|---|
| escala del ruido (`Multiply_46`) | **`VeilScale`** | `FlowScale` |
| deriva temporal (`Multiply_47`) | **una `Constant` = 0,25** | `FlowSpeed` |
| separacion de los 3 campos | nada (offsets fijos) | `FlowMix` |

`FlowScale` y `FlowSpeed` seguian alimentando la cadena VIEJA (`Noise_3`), que ya no llega a la salida. Por eso los tres parametros **existian, compilaban y el BP los empujaba bien** — y no pasaba nada. 💡 Y explica el sintoma raro que se venia arrastrando: lo que hacia mover el fluido era **`VeilScale`**, o sea se estaba autorando el efecto con la perilla equivocada.

✅ **Arreglado:** `Multiply_46.B` ← `FlowScale`, `Multiply_47.B` ← `FlowSpeed`, y `FlowMix` ahora **escala los dos vectores de offset** entre los tres campos de ruido (`FlowMix = 0` → los tres ruidos coinciden → color plano; `= 1` → separacion completa, marmolado). Es el rol que le faltaba desde la reconstruccion.

⚠ **Los valores que estaban en la instancia (`FlowScale` 626,7 · `FlowSpeed` 15,7 · `FlowMix` 1,46) eran de arrastrar sliders a ciegas** — con las perillas ya conectadas hubieran dado ruido puro. Se reemplazaron por los que **reproducen lo que se venia viendo**: `FlowScale` 1,537 (el `VeilScale` que lo estaba manejando), `FlowSpeed` 0,25 (la constante), `FlowMix` 1,0 (los offsets estaban a full). Defaults del CDO: 1,6 / 0,25 / 1,0.

🔴🔴 **La leccion de proceso, que es mas cara que el bug:** Beltran reporto el sintoma en cuatro palabras y yo gaste una tanda entera de capturas y ~130k tokens **demostrando que tenia razon** antes de ir a arreglarlo. El A/B solo confirmo lo que el ya sabia; lo que resolvio el caso fueron **seis `get_expression_inputs`** recorriendo la cadena hacia atras desde `MP_EmissiveColor`. Ver `gotchas.md` §316.


## 🔴🔴 2026-09-07 (cierre) — el modo fluido REESCRITO: simplex 4D + el Veil como contorno
Jornada larga y cara. Queda esto, y conviene leerlo antes de tocar nada del modo 2.

### 1. Lo que estaba roto de verdad
| Sintoma que reporto Beltran | Causa real |
|---|---|
| *"las perillas de flow no hacen nada"* | La cadena NUEVA del fluido (`Noise_4/5/6`) estaba enchufada a **`VeilScale`** para la escala y a una **`Constant`** para el tiempo. `FlowScale`/`FlowSpeed` alimentaban la cadena VIEJA (`Noise_3`), que ya no llegaba a la salida. Los tres parametros existian, compilaban y el BP los empujaba bien — y no hacian nada. |
| *"se mueve para un lado"* | El patron se calcula sobre `normalize(LocalPosition)`, que gasta **las tres dimensiones** del ruido. Sin dimension libre, todo movimiento es tangencial → se desliza. Ver §2. |
| *"sigue como un pulso"* | Dos causas encadenadas: (a) un crossfade entre dos campos de ruido INDEPENDIENTES **disuelve, no deforma**; (b) despues, el **Veil** quedo muestreando una posicion que **saltaba de golpe** cada vez que `Floor(Time·FlowSpeed)` avanzaba, y con `VeilAmount = 3,13` ese termino tapaba todo lo demas. |

### 2. 🔴 La restriccion de fondo (no es un bug, es geometria)
TouchDesigner anima un Noise TOP moviendo `Translate Z` porque el plano usa `(u,v)` y **deja el eje Z libre**. Nuestro cascaron usa las tres coordenadas para describir la superficie: **no queda ninguna libre para el tiempo**. Y no se arregla reduciendo a una carta 2D — una esfera no admite una sin costura ni polos, es topologico (por eso el material abandono las UV en su dia).

Consecuencia, y explica por que fallaron CINCO intentos seguidos:
- Traslacion / vaiven / rotacion del dominio → **tangencial** → se ve ir hacia un lado.
- Marcha **radial** → es la unica no tangencial (es la normal de la superficie, el analogo real del Z del plano), pero el radio **es** la escala tangencial → las manchas se achican y no se puede sostener un flujo grande.

✅ **Con escala fija + evolucion en el lugar + sin direccion, las cuatro dimensiones NO son opcionales.**

### 3. La solucion: simplex 4D de Ashima/Gustavson en un nodo `Custom`
`MaterialExpressionCustom_0`, `OutputType = CMOT_Float3`, entradas `P` (= `dir × FlowScale`), `W` (= `Time × FlowSpeed`), `O1`/`O2` (los offsets × `FlowMix`). Devuelve los **tres pesos de color de una sola vez**.

🔴 **Por que simplex y no el value noise que escribi primero:** la literatura es explicita — *"gradient noise provides enhanced smoothness and **temporal stability**, making it preferable for animations"*, y del de valor: *"the **lattice is still quite obvious**"*. El ruido de VALOR pulsa por construccion. Ese fue el pulso que Beltran vio en la version 4D hecha a mano. Ademas simplex evalua **5 esquinas en vez de 16** → salio mas barato que el parche.

💡 De paso: bajo de **6 muestras de ruido a 3**.

### 4. 🔴 El Veil ahora es EL CONTORNO del propio degradado (pedido de Beltran)
*"El veil deberia ser el contorno animado de la misma gradiente."* Ya no hay ruido aparte: se derivan de los **pesos que el fluido ya calculo**.
```
m     = max(w1, w2, w3)          // 1/3 = frontera entre colores · 1 = color puro
borde = (1 − saturate(m·1,5 − 0,5)) ^ VeilScale
Veil  = lerp(1, 1 + borde, saturate(VeilAmount))
```
Se anima solo (los bordes se mueven con el simplex) y **no cuesta ninguna muestra de ruido nueva**.

| Perilla | Rol | Rango util |
|---|---|---|
| `VeilAmount` | cuanto se nota el contorno | **0–1** (ahora acotado con `saturate`) |
| `VeilScale` | ancho del borde: bajo = banda difusa, alto = linea fina | 1–12 |
| `FlowScale` | tamaño de mancha (independiente del tiempo) | — |
| `FlowSpeed` | velocidad del hervor (0 congela) | — |
| `FlowMix` | separacion entre los tres colores | 0–1,5 |

⚠ **`VeilAmount` era el ALPHA CRUDO de un lerp.** Un alpha solo tiene sentido en 0–1; el `3,13` que tenia la instancia **extrapolaba** muy afuera y dominaba la imagen. No era un valor mal elegido: era una perilla que no servia para lo que se le pedia. Leccion generalizable en `gotchas.md` §318.

⚠ **Valores que se pisaron** (los de la instancia se autoraron sobre un sistema roto): `FlowScale` 626,7 → 1,537 · `FlowSpeed` 15,7 → 0,06 · `FlowMix` 1,46 → 1,0 · `VeilAmount` 3,13 → 0,5 · `VeilScale` 1,537 → 4,0.

### 5. Nodos huerfanos que quedaron
Las seis `Noise` viejas, los `LinearInterpolate_12/13/14`, los `RotateAboutAxis_0/1/2` y la cadena Lissajous ya **no llegan a la salida** (no compilan al shader, no cuestan). Se pueden limpiar con `delete_unused_expressions`, pero **conviene hacerlo recien despues del visor**, por si hay que volver atras.

### 6. TODO
- [ ] 🔴 **Visor**, y sobre todo **medir el fill**: es una superficie opaca a pantalla completa con 3 muestras de simplex 4D. Es el riesgo real de este material.
- [ ] Beltran elige `VeilAmount`/`VeilScale`/`Flow*` mirando; los valores de arriba son punto de partida mio, no decision autoral.
