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


## 🌊 2026-09-08 — el VEIL como lugar bajo: desplazamiento (WPO) + malla densa
Pedido de Beltran: *"me gustaria lograr que el veil sean lugares bajos, y el resto olas. Si la esfera logra eso seria bien interesante, quizas hay que hacer el mesh mas detallado de poligonos?"*

### Que se construyo
**Un solo campo manda la forma y el color.** El nodo `OneMinus_0` de la cadena del Veil (`v = 1 − saturate(m·1,5 − 0,5)`, donde `m = max(w1,w2,w3)`) ya era el campo suave del contorno: **1 en la frontera entre colores, 0 en el centro de cada mancha pura**. Ese mismo nodo, SIN el `^VeilScale` que lo afila en linea, ahora alimenta tambien el WPO:

```
WPO = VertexNormalWS × ( BreathAmount·sin(t·BreathSpeed)  +  v · WaveAmount )
                          ^ Multiply_6 (lo que ya habia)     ^ Multiply_66 (nuevo)
                          ambos sumados en Add_39 → Multiply_7.B
```
💡 Consecuencia buscada: **la linea brillante del veil vive en el fondo del valle**, y `VeilScale` sigue controlando su ancho sin tocar la forma del relieve. Cero muestras de ruido nuevas: reusa lo que el simplex ya calculo.

| Nodo nuevo | Rol |
|---|---|
| `ScalarParameter_5` = **`WaveAmount`** (grupo *H - Olas*, default −150) | amplitud en **cm de mundo**; 🔴 **el signo es el sentido** |
| `Multiply_66` | `v × WaveAmount` |
| `Add_39` | respiracion + ola → `Multiply_7.B` |
| `Clamp_0` | reemplaza a `Saturate_16` en el `Alpha` de `LinearInterpolate_9`: **`VeilAmount` ahora va de −1 a 1** |

🔴 **`VeilAmount` negativo = el contorno OSCURECE en vez de aclarar.** Es lo que hace que el relieve se *lea* (un valle oscuro es la lectura de profundidad de toda la vida). Positivo se comporta igual que antes, asi que **no rompe nada de lo autorado**: la instancia tenia 3,827, que el `saturate` viejo clampeaba a 1 y el `clamp` nuevo tambien → pixel identico.

### La malla: `SM_GanzShell_HD` (nueva, misma carpeta)
192 × 96 → **36.480 tris**, radio **50** (se respeta la convencion `escala = tamaño/50`, bounds verificados ±50), sin colision, normales emitidas hacia adentro como la vieja. Es el nuevo default de `Mesh` en el CDO; **`SM_GanzShell` (9k tris) sigue en el dropdown** como fallback barato.

🔴 **Por que 192 y no 96:** vale la regla ya medida en la losa de niebla — **~16 segmentos por longitud de onda** o el borde sale dentado. Con `FlowScale ~1,5` las manchas miden ~35-40°, o sea ~10 segmentos con la malla vieja (facetea) y ~20 con la nueva (pasa). Si Beltran sube `FlowScale` y aparecen facetas, el siguiente escalon es 256×128 (131k tris, el mismo presupuesto que `SM_FogSlab`) — es re-emitir el OBJ y re-importar.

### 🔴🔴 LO QUE HAY QUE SABER ANTES DE AUTORAR ESTO: desde el centro NO SE VE. Medido.
Capturas A/B del viewport, `FlowSpeed` congelado en 0 para aislar la animacion, `WaveAmount −2500` (¡la MITAD del radio!) contra 0:

| Camara | dif maxima | dif media | pixeles cambiados |
|---|---|---|---|
| **Centro exacto del cascaron** | **2/255** (= el dither) | **0,000/255** | **0,00 %** |
| 50 % del radio descentrada | 24/255 | 4,05/255 | 78 % |
| Desde AFUERA | radio de silueta **178 → 268 px** | — | — |

**No es un bug: es geometria.** El color se calcula sobre `normalize(LocalPosition)`, o sea sobre la **direccion**; un desplazamiento **radial** no cambia la direccion de ningun punto (`normalize(k·d) = d`). Desde el centro exacto la deformacion es **matematicamente invisible**, con cualquier amplitud. Es la misma razon por la que `BreathAmount` "no hace nada" (ya estaba anotado arriba) — ahora esta medido.

👉 **Se ve cuando se rompe la simetria:**
- **Descentrado** — cuanto mas lejos del centro esta la cabeza respecto del radio, mas paralaje. Con `ShellRadius 5000` (50 m) y el usuario sentado cerca del centro, es despreciable.
- **Cascaron chico** — a 3-5 m de radio la misma amplitud relativa se vuelve evidente.
- **Estereo en el visor** — los dos ojos ven el relieve a profundidades distintas. A 50 m la disparidad esta al borde del umbral (~1,7 arcmin vs ~1 de agudeza); a 5 m es franca. **Sin verificar en gafas.**
- **Desde afuera** — ahi la silueta lo delata y se ve perfecto (esa fue la captura que fijo el signo).

### El signo, verificado por medicion (no por razonamiento)
Con **`WaveAmount` NEGATIVO** el radio **solo crece** donde `v = 1` (silueta medida: 178 px → 268 px, nunca por dentro del circulo de referencia) → **el contorno del veil se aleja del centro → desde adentro es el hueco.** Es el sentido que pidio Beltran. Positivo lo trae hacia el espectador (cresta).

### Valores puestos (punto de partida mio, no decision autoral)
| | `Mesh` | `WaveAmount` | notas |
|---|---|---|---|
| CDO | `SM_GanzShell_HD` | −150 | |
| `GAL_3_Ganzfeld` (r=5000) | `SM_GanzShell_HD` | **−400** (8 % del radio) | tenia override de `Mesh` a la malla vieja |
| `GAL_9_Ganzfeld` (r=4000) | `SM_GanzShell_HD` | **−300** (7,5 %) | idem |

⚠ **Los dos actores tenian `Mesh` overrideado en la instancia** → no heredaban el default nuevo; hubo que escribirlo actor por actor. Volver atras es un dropdown.
⚠ **`WaveAmount` nacio en 0 en las dos instancias**, no en el default del CDO — el caso clasico de *"lo de la instancia le gana al Blueprint"*. Si se agrega otra estacion, revisar.
⚠ No se toco ningun otro valor autorado. `FlowSpeed` de GAL_3 se congelo para medir y se restauro a `0,146069` (verificado leyendo la instancia).
⚠ **El nivel `/Game/TestMeshes` quedo SIN GUARDAR a proposito** (los valores de instancia viven en el editor). Guardan `M_Ganzfeld_SC`, `BP_Ganzfeld_SC` y `SM_GanzShell_HD`.

### TODO de la primera pasada
- [x] Que el oleaje SE VEA desde adentro → resuelto con `WaveShade`, seccion siguiente.
- [ ] Visor: confirmar si el relieve estereo se percibe a `ShellRadius 5000`, y probar un cascaron chico (3-5 m).
- [ ] Costo: el simplex 4D ahora compila TAMBIEN en el vertex shader (18.721 vertices). No medido en device.


## 🌗 2026-09-08 (2a) — `WaveShade`: el sombreado por PENDIENTE, que es lo que hace que se vea
Beltran, mirandolo: *"se deforma pero no se nota tanto desde adentro, yo creo que si agregas una sombra, como en el oceano, funcionara"*. Tenia razon, y la receta ya estaba escrita en el proyecto.

### 🔴 La nota del oceano que evito inventar de nuevo
De `BP_LightShaft_SC.md` (v3 de la nube, 2026-09-04), sobre `M_CloudPlane_SC`:
> *"**sombreado por PENDIENTE** (2 muestras offset del heightfield → luz fija baña crestas, `SlopeShade`) — **el tinte por altura solo no esculpe**"*

Yo iba a oscurecer el hueco por ALTURA (`shade = 1 − v·k`), que es exactamente lo que esa nota ya declara insuficiente. **Leer el tracker del efecto que el usuario nombra como referencia costo una llamada y ahorro la pasada equivocada entera.** (El material del oceano tambien tiene `ValleyColor` y `SlopeShade` como parametros — se ven de una con `MaterialInstanceTools.list_parameters`, que es la forma barata de espiar como resolvio algo otro material.)

### Como se implemento: dentro del MISMO nodo `Custom`
La pendiente necesita el campo `v` evaluado en dos puntos. `v` sale de `max(w1,w2,w3)`, o sea de las **tres** muestras → hacen falta tres mas. Se hizo **adentro de `MaterialExpressionCustom_0`**, sin plomeria nueva:
- El bucle paso de `k < 3` a **`k < 6`**: las vueltas 0-2 muestrean en `P` (los tres pesos de color, salida sin tocar) y las 3-5 en **`P + SCLV`**, con `const float3 SCLV = float3(0, 0, 0.15)` = **la luz fija, desde el +Z local del cascaron ("desde arriba")**.
- Salida adicional **`Shade`** (`additionalOutputs`, `CMOT_Float1`) = `saturate(1,5·m1 − 0,5) − saturate(1,5·m0 − 0,5)`, es decir `v(P) − v(P+L)`: **positivo donde la superficie sube hacia la luz**.
- La salida `return` (los tres pesos) quedo **identica**. El color no cambio ni un bit con `WaveShade = 0`.

💡 **Por que la diferencia finita y no el gradiente del ganador.** Se evaluo usar solo el peso que gana el `max` (1 muestra extra en vez de 3, 33% en vez de 100%): **descartado**. El gradiente de un `max` es discontinuo justo en el empate entre dos pesos — o sea justo en la linea del veil — y eso dibuja **una linea de contorno**, que es el modo de falla nº1 documentado de este material. La diferencia finita sobre un offset real suaviza ese empate.

### En el grafo
`Custom.Shade → Multiply_67 (× WaveShade) → Add_40 (+1) → Max_3 (con 0) → Multiply_68 (× el color ya velado) → Multiply_4.A (Brightness)`.
El `Max` con 0 es la red de seguridad: sin el, un `WaveShade` grande manda el multiplicador a negativo y clipea a negro.

| Perilla | Rol | Rango util |
|---|---|---|
| **`WaveShade`** (cat. *H - Olas*, default **2,0**) | cuanto esculpe la luz. **0 = apagado, y el material vuelve a ser pixel por pixel el de antes.** El signo invierte de donde viene la luz | 0–5 |

### Medido, no estimado (mismo encuadre, desde el CENTRO EXACTO, `FlowSpeed` congelado en 0)
| Que se compara | dif maxima | dif media | pixeles cambiados |
|---|---|---|---|
| Geometria sola (`WaveAmount` −2500 vs 0) | 2/255 (dither) | 0,00 | **0,00 %** |
| **Sombra (`WaveShade` 2 vs 0)** | **64/255** | **7,04/255** | **83,6 %** |

👉 **La conclusion, en una linea: en un cascaron mirado desde adentro el relieve lo hace el SOMBREADO, no el WPO.** El desplazamiento sigue teniendo sentido (silueta desde afuera, estereo en el visor, cascarones chicos), pero no es lo que se ve.

### Costo — el numero que hay que vigilar
El material paso de **3 a 6 muestras de simplex 4D por pixel**, en una superficie opaca a pantalla completa. Es exactamente el riesgo que este tracker ya venia marcando. 🔴 **Sin medir en device.** Si aprieta, las salidas en orden de conveniencia: (1) `WaveShade = 0` no ahorra nada (el shader igual las calcula) → para ahorrar de verdad hay que **volver el bucle a `k < 3`** y quitar la conexion de `Shade`, que es una edicion de una propiedad; (2) bajar la malla a `SM_GanzShell`.

### Estado de las instancias al cierre
`GAL_3_Ganzfeld`: `WaveShade` 2 · `WaveAmount` **−1132,6** (⚠ **lo movio Beltran en vivo mientras se trabajaba** — no pisarlo) · `Mesh` HD · resto de sus valores intacto (`FlowSpeed` 0,146069 restaurado y verificado tras congelarlo para medir).
`GAL_9_Ganzfeld`: `WaveShade` 2 · `WaveAmount` −300 · `Mesh` HD.
CDO: `WaveShade` 2 · `WaveAmount` −150 · `Mesh` HD.
⚠ `WaveShade` tambien **nacio en 0 en las dos instancias** (igual que `WaveAmount`) y hubo que escribirlo actor por actor.

### TODO
- [ ] 🔴 **Visor + medicion de fill.** Es lo unico serio que queda: 6 simplex 4D a pantalla completa en Quest.
- [ ] Juicio de Beltran sobre `WaveShade` (2,0 es punto de partida mio) y sobre si la luz desde +Z local es la direccion que quiere — hoy esta **hardcodeada** en el HLSL (`SCLV`); volverla perilla es agregarle un input al `Custom`.
- [ ] Los nodos huerfanos viejos siguen sin limpiar (a proposito, hasta despues del visor).


## 📏 2026-09-08 (3a) — `WaveAmount` inflaba la esfera en vez de hacer olas. La causa exacta
Beltran: *"el wave amount, en vez de exagerar la deformacion, simplemente agranda la esfera. Deberia hacer mas intenso la altura de las olas respecto a la parte baja."* Tenia razon, y la causa sale del **propio codigo del shader**, no de una estimacion.

### La cuenta
En el nodo `Custom`, cada peso crudo es `R[k] = 0.3 + 0.7 * saturate(...)` → **`R ∈ [0,3 , 1,0]`, nunca baja de 0,3**. Los tres se normalizan (`Divide_8/9/10 = R[i]/sum`), asi que el maximo normalizado queda **acotado**:
```
m = max(w) ∈ [1/3 , 1,0/(1,0+0,3+0,3)] = [0,3333 , 0,625]
s = saturate(1,5·m − 0,5)              ∈ [0 , 0,4375]      ← nunca llega a 1
v = 1 − s   (= OneMinus_0, lo que iba al WPO)  ∈ [0,5625 , 1]   ← 🔴 NUNCA se acerca a 0
```
🔴 **Ese piso de 0,5625 es todo el problema.** Con `WaveAmount = −2000` el empuje hacia afuera era `2000·v ∈ [1125 , 2000]`: **1125 cm de inflado constante y solo 875 cm de ola**. Literalmente "agranda la esfera con un poco de textura encima".

✅ **Verificado contra las mediciones** (modelo de camara pinhole, `f ≈ 478,7 px` a partir del FOV 90 del viewport, validado con la esfera sin deformar: predicho 4001 cm, real 4000):
| Caso | prediccion del modelo | medido |
|---|---|---|
| GAL_3, R=5000, sin sesgo, A=−2000 | radio max **7000** | **6987** |
| GAL_9, R=4000, sesgo 0,5, A=−2000 | radio max **5000** | **4945** |

Y de paso queda establecido que **`VertexNormalWS` apunta HACIA ADENTRO** en estas mallas (un `WaveAmount` negativo empuja hacia AFUERA), coherente con que los dos OBJ se emitieron con normales hacia adentro.

### El arreglo: recentrar y normalizar el campo a su rango REAL
```
hw = (v − 0,78125) × 2,2857        ← 0,78125 = punto medio de [0,5625 , 1] ; 2,2857 = 1/0,4375
```
`hw ∈ [−0,5 , +0,5]` → media ≈ 0 (**deja de inflar**) y amplitud pico-a-pico = 1,0.
👉 **`WaveAmount` pasa a leerse como la ALTURA DE LA OLA en cm, de cresta a valle.** El veil (v=1) sigue siendo el punto mas bajo (se aleja del centro) y el centro de cada mancha pura pasa a ser cresta **hacia el espectador**, que antes no existia: antes toda la esfera se iba hacia afuera junta.

Nodos: `OneMinus_0 → Subtract_3 (−0,78125) → Multiply_69 (×2,2857) → Multiply_66 (×WaveAmount) → Add_39 (+respiracion) → Multiply_7.B`.

⚠ **El significado del numero cambio.** Los valores que estaban puestos ya no quieren decir lo mismo: `WaveAmount −1132` (el que autoro Beltran en vivo) antes era "entre 637 y 1132 cm hacia afuera, todo junto"; ahora es "**1132 cm de cresta a valle repartidos alrededor del radio nominal**". Hay que re-autorarlo mirando.

### 🔴 Lo que NO se pudo verificar y por que
La captura del viewport empezo a devolver **el mismo frame negro tres veces seguidas** (bytes identicos) despues de haber funcionado toda la sesion en ese mismo encuadre. Coincide con que Beltran estaba usando el editor en paralelo (se lo vio mover `WaveAmount` a mano). **La normalizacion esta compilada y guardada pero NO la vi con mis ojos** — el juicio queda en Beltran, que tiene el editor delante.
🚩 Regla que sale de aca: `CaptureViewport` puede devolver un frame viejo sin avisar. **Si dos capturas consecutivas dan bytes identicos, la captura esta stale — no es un resultado, es una falla.** Comparar el hash antes de sacar conclusiones.

### Estado al cierre
| | `Mesh` | `WaveAmount` | `WaveShade` |
|---|---|---|---|
| CDO | `SM_GanzShell_HD` | −150 | 2,0 |
| `GAL_3_Ganzfeld` (R=5000) | HD | **−1132,6** (valor de Beltran, no tocado) | 2,0 |
| `GAL_9_Ganzfeld` (R=4000) | HD | −600 | 2,0 |
Guardados: `M_Ganzfeld_SC`, `BP_Ganzfeld_SC`, `SM_GanzShell_HD`. **El nivel `/Game/TestMeshes` sigue sin guardar** (los valores de instancia viven en el editor hasta que Beltran haga Save).


## 🎛️ 2026-09-08 (4a) — las perillas: se fueron TODAS las constantes hardcodeadas
Pedido de Beltran: *"dame las perillas para jugar con eso"*. Ya no queda ningun numero magico en el sistema de olas: las cuatro constantes que yo habia dejado en el shader ahora son parametros.

### Categoria `H - Olas` completa (6 perillas)
| Perilla | Que hace | Default | Rango util |
|---|---|---|---|
| **`WaveAmount`** | **altura de la ola en cm, de cresta a valle**. Signo = sentido (negativo = el veil es el hueco). 0 = esfera perfecta | −150 | ±100 a ±1500 segun `ShellRadius` |
| **`WaveLevel`** | **el nivel del mar**. Donde cae el corte entre cresta y valle dentro del campo. **0,78125 = equilibrado** (no infla ni encoge). Mas bajo → mas superficie es cresta y la esfera se agranda; mas alto → mas hueco y se achica | 0,78125 | 0,56 – 1,0 |
| **`WaveShade`** | **cuanto esculpe la luz rasante.** Es la perilla que hace que el relieve SE VEA desde adentro (la geometria sola no se ve). 0 = apagada | 2,0 | 0 – 5 |
| **`ShadeYaw`** | **de que lado viene la luz**, en grados alrededor del eje del cascaron | 0 | 0 – 360 |
| **`ShadeHeight`** | **altura de la luz**: 1 = cenital (desde el +Z local), 0 = rasante desde el costado, −1 = desde abajo | 1,0 | −1 – 1 |
| **`ShadeWidth`** | **que tan lejos se toma la segunda muestra** = dureza del relieve. Chico → relieve fino y contrastado; grande → lomas anchas y blandas. 🔴 **En 0 la sombra desaparece** (las dos muestras coinciden) | 0,15 | 0,04 – 0,5 |

💡 **Como se autora:** `WaveAmount` + `WaveLevel` definen la FORMA (y se ven desde afuera / en estereo); `WaveShade` + `ShadeYaw/Height/Width` definen COMO SE LEE desde adentro, que es lo que el usuario percibe. Son independientes: se puede tener sombra sin deformar (`WaveAmount = 0`) y sale igual de bien — y es mas barato en vertices.

### Lo que cambio por dentro
- `Subtract_3.B` dejo de ser la constante 0,78125 → ahora lo alimenta el parametro **`WaveLevel`**.
- 🔴 **El nodo `Custom` gano una QUINTA entrada, `L`** (la direccion+distancia de la luz), y el `const float3 SCLV` desaparecio del HLSL. La entrada se agrego reescribiendo la propiedad `inputs` completa **preservando las cuatro conexiones existentes** (`P`/`W`/`O1`/`O2`) y verificando con `get_expression_inputs` que las cinco quedaran cableadas. Funciono a la primera; es la via para agregarle inputs a un `Custom` sin rehacerlo.
- `L` se arma en el grafo: `ShadeYaw ×(1/360) → Cos/Sin` (⚠ los nodos `Sine`/`Cosine` de UE tienen `Period = 1`, o sea la entrada va en **VUELTAS, no en radianes**) `× (1 − |ShadeHeight|)` para el plano horizontal, `Append` con `ShadeHeight` en Z, y todo `× ShadeWidth`.
- Con los defaults (`ShadeYaw 0`, `ShadeHeight 1`, `ShadeWidth 0,15`) el vector da exactamente `(0, 0, 0.15)` — **identico al comportamiento hardcodeado anterior**, asi que nada cambio de aspecto al exponer las perillas.

### 🔴 Estado del nivel al cierre — CAMBIO MIENTRAS TRABAJABAMOS
Beltran estuvo autorando en paralelo. Verificado por log (`LogEditorActor`), **no por suposicion**:
- **`GAL_9_Ganzfeld` lo BORRO EL (`Deleted Actor: BP_Ganzfeld_SC_C`, 11:18:59), no el MCP.** No se repuso. (Tambien borro dos `BP_LineField_SC_C` a las 11:34.)
- Coloco **dos estaciones nuevas**: `GAL_7_Shell_Violeta` (`ShellRadius` 10000) y `GAL_8_Shell_Verdeazul` (`ShellRadius` 3000), ambas con `SM_GanzShell` (la malla vieja de 9k tris).
- Movio `WaveAmount` de `GAL_3` dos veces durante la sesion (−1132,6 → −537,3). **Su valor manda.**

| Actor | `Mesh` | `WaveAmount` | `WaveShade` | estructurales |
|---|---|---|---|---|
| `GAL_3_Ganzfeld` (R 5000) | **HD** | −537,3 *(suyo)* | 2,0 | puestos |
| `GAL_7_Shell_Violeta` (R 10000) | vieja | **0** | **0** | puestos |
| `GAL_8_Shell_Verdeazul` (R 3000) | vieja | **0** | **0** | puestos |
| CDO | HD | −150 | 2,0 | puestos |

⚠ En GAL_7 y GAL_8 se escribieron **solo** `WaveLevel`/`ShadeYaw`/`ShadeHeight`/`ShadeWidth` (los estructurales) y se dejaron `WaveAmount` y `WaveShade` en **0 a proposito**: asi esas dos estaciones **se ven exactamente igual que antes**, pero las perillas ya responden cuando Beltran las mueva. Si les quiere poner olas, ademas conviene pasarlas a `SM_GanzShell_HD` (la vieja de 96×48 facetea el desplazamiento).
⚠ **Las 4 variables nuevas nacieron en 0 en las tres instancias** — cuarta vez en esta sesion que muerde lo mismo. `ShadeWidth = 0` es el caso peligroso: apaga la sombra entera sin error.

Guardados: `M_Ganzfeld_SC`, `BP_Ganzfeld_SC`. **`/Game/TestMeshes` sigue sin guardar** (lo guarda Beltran).

## 🔴 2026-09-15 — MEDIDO EN VISOR: el Ganzfeld es el efecto mas caro de la galeria, y por que

Primera medicion real en device (Quest 3, build del 8-sep, telemetria `VrApi` por segundo cruzada con los
`BOTON apretado: NEXT` del log). Presupuesto 72 Hz = **13,9 ms**. La columna `App` es el tiempo de GPU de la app.

| Estacion | Actores | App (ms) | FPS | GPU% |
|---|---|---|---|---|
| 3 · Ganzfeld | **`BP_Ganzfeld_SC_C_0` SOLO** | **24,1 – 27,2** | 37–39 | 0,92–0,97 |
| 7 · MetaBlob | `BP_MetaBlob_SC` + Ganzfeld | 30,3 – 38,9 | 28–30 | 0,79–0,97 |
| 8 · Burbujas | RimField + VoidField + Ganzfeld + 3 LightShaft | 22,6 – 26,3 | 31–35 | 0,97–0,98 |
| 9/10 · Ring Tunnel | `BP_RingTunnel_SC` | 4,9 – 5,9 | 67–72 | 0,51–0,74 |
| resto (Shaft/Ocean/Fog) | — | 7,8 – 11,0 | 59–73 | 0,43–0,84 |

🔴 **La estacion 3 tiene UN SOLO actor**, asi que esos 24–27 ms son el Ganzfeld puro: **casi el doble del
presupuesto del frame, el solo**. Restando, el metaball aporta ~6–12 ms encima del cascaron. Y la estacion 8,
con SEIS actores, cuesta lo mismo que el cascaron solo → los otros cinco no se notan. **El cascaron es el costo
de la galeria; todo lo demas es ruido alrededor.**

### La causa: `Mode` es un Scalar de RUNTIME, asi que se calculaban LOS TRES MODOS por pixel
`Mode` esta en la lista de parametros como **`Scalar`**, no como `StaticSwitchParameter`. El selector es una
pareja de `Step` anidados sobre `LinearInterpolate`:

```
Step_2 = (Mode >= 0.5)   Lerp_10( A = Multiply_1 [modo 0] , B = Add_20 [modo 1] , Alpha = Step_2 )
Step_3 = (Mode >= 1.5)   Lerp_11( A = Lerp_10            , B = Add_24 [modo 2] , Alpha = Step_3 )
                         Multiply_23.A <- Lerp_11   ->   ... -> Multiply_4 (xBrightness) -> Add_1 -> Emissive
```
Un `lerp` **no es una rama**: el GPU evalua las dos entradas y despues mezcla. Con los tres modos colgando de
ahi, y **10 nodos `Noise`** repartidos entre ellos, cada pixel del cascaron pagaba los modos 0 y 1 aunque desde
el 2026-09-07 la obra **solo usa el modo 2**.

⚠ **Ojo con la convencion del nodo `Step` de UE**: sus pines se llaman `X` e `Y` y calcula **`X >= Y`**
(el umbral es `Y`), al reves de lo que sugiere el `step(edge, x)` de HLSL. Lo verifique por la estructura
anidada, no por la firma.

### ✅ Lo que se hizo (2026-09-15) — reversible en UNA conexion
**`Multiply_23.A` se reconecto de `Lerp_11` a `Add_24`** (la salida del modo 2), se recompilo y se guardo.
No se borro ni un nodo: los modos 0 y 1 quedan enteros en el grafo, solo sin referencias, y el compilador de
shaders los elimina. **Sin cambio de aspecto: el modo 2 era lo unico que se veia.**

🔁 **Para revertir:** `connect_expressions(from=LinearInterpolate_11, to=Multiply_23, to_input="A")` + `recompile`.
🔬 **Falta medir en device** cuanto bajo. Se mide repitiendo la pasada y mirando `App` en la estacion 3.

### Lo que NO es el problema (dos teorias descartadas)
- ❌ **`TwoSided` no cuesta el doble.** Desde el centro de una esfera cada rayo corta el cascaron **una sola vez**
  (el hemisferio cercano queda detras de la camara, fuera del frustum). No hay doble capa. Y como desde adentro
  la cara visible **es** la backface, ponerlo one-sided lo dejaria negro. Two-sided aca es lo que lo hace visible.
- ❌ **La foveacion no es una palanca libre.** Ya esta deliberadamente clavada en Low con el dinamico apagado
  (`Config/Android/AndroidEngine.ini`), porque los niveles 2–3 degradan visiblemente y el dinamico causaba el
  aliasing intermitente que Beltran reporto el 2026-08-21. Subirla desharia una decision suya con motivo escrito.

### Lo que queda sobre la mesa, en orden
1. 🔬 **Medir esta mejora** antes de tocar nada mas.
2. **`xr.SecondaryScreenPercentage.HMDRenderTarget = 135`** multiplica el fill de TODO: 1,17x contra 125 y
   **1,82x contra 100**. El propio comentario del ini dice *"Si OVR Metrics muestra caida de fps, ESTA es la
   primera linea a revertir a 125"* — la condicion ya se cumplio. **Es decision de Beltran** (lo subio para
   pelear el aliasing).
3. **`FloatPrecisionMode = MFPM_Full_MaterialExpressionOnly`** → `MFPM_Default` seria ~2x de ALU, pero
   ⚠ **rompe el dither R2**: `frac(dot(px, k))` con `px` en pixeles (~2000) pierde toda la precision en fp16.
   Habria que reescribir el dither primero.
4. Recien despues el metaball (proxy esfera en vez del cubo de engine, normal analitica).

### 🔴 2026-09-15 (2a) — RESULTADO NEGATIVO MEDIDO: podar los modos 0 y 1 NO bajo nada
Se empaqueto (FULL COOK, exit 0), se instalo y se repitio la pasada. Estacion 3, mismo recorrido:

| | GPU MHz | Temp | App (ms) en la estacion 3 |
|---|---|---|---|
| **Antes** (los 3 modos) | **545** | 35 °C | 24,1 · 27,2 · 24,3 · 24,1 · 27,1 · 26,7 |
| **Despues** (solo modo 2) | **640** | 38 °C | 25,8 · 23,8 · 23,1 · 23,4 · 26,3 · 26,7 · 20,3 · 22,9 |

🔴 **El control mata la mejora aparente:** la segunda corrida tuvo el GPU **17% mas rapido** (640 vs 545 MHz).
Normalizando por reloj, el "antes" equivale a ~24 ms y el "despues" a ~28 ms. **La poda no movio la aguja.**
Ninguna otra estacion cambio tampoco (VoidField 4,5–6,3 → 5,4–6,9; LineField ~15 → ~16; base 7,8–11,0 → 8,2–11,4).

**Lo que eso PRUEBA:** los modos 0 y 1 eran **baratos** (mascaras y gradientes, sin ruido). **Todo el costo esta
dentro del modo 2.** La poda queda igual (es codigo muerto de verdad, no cuesta nada tenerla) pero ⚠ **deja el
parametro `Mode` inerte**. Revertir: `connect_expressions(from=LinearInterpolate_11, to=Multiply_23, to_input="A")`.

### 🔴 DONDE ESTA EL COSTO DE VERDAD: `MaterialExpressionCustom_0` = **SEIS** simplex 4D por pixel
Leido el codigo (`Description = "Simplex4D_Fluid"`): es un `[unroll] for (k = 0; k < 6; k++)` donde **cada
vuelta es un simplex 4D COMPLETO** (5 gradientes, 4 cadenas anidadas de `SCPERM`). En el 100% de la pantalla,
por dos ojos.

| k | muestra | para que |
|---|---|---|
| 0,1,2 | `P + {0, O1, O2}` | los **tres canales de color** (R, G, B decorrelacionados por offset) |
| 3,4,5 | `P + L + {0, O1, O2}` | **solo** para `Shade = max(R6[3..5]) − max(R6[0..2])`, **UN escalar** |

🔴 **La mitad del nodo (3 de 6 evaluaciones) existe para producir un unico escalar de relieve.** Y es una
diferencia finita a lo largo de `L`, que no necesita tres muestras nuevas: alcanza con **una sola** (−33%), o
con `ddx`/`ddy` de `sm0`, que en GPU es gratis (−50%).

🔴🔴 **Y hoy se computa aunque se multiplique por CERO.** Verificado en las tres instancias del nivel:

| instancia | `ShellRadius` | `WaveAmount` | `WaveShade` |
|---|---|---|---|
| `BP_Ganzfeld_SC_C_0` (GAL_3) | 5000 | −537,3 | **2,0** ← lo usa |
| `BP_Ganzfeld_SC_C_1` (GAL_7) | 10000 | 0 | **0** ← 3 simplex 4D al tacho |
| `BP_Ganzfeld_SC_C_2` (GAL_8) | 3000 | 0 | **0** ← idem |

**Dos de las tres instancias pagan la mitad del nodo y tiran el resultado.** Un `StaticSwitchParameter`
("usar relieve") las sacaria de esas 3 evaluaciones sin tocar como se ve GAL_3. Es la proxima medicion.

### ✅ 2026-09-15 (3a) — el relieve detras de una RAMA UNIFORME (no un static switch)
🔴 **Por que NO se uso `StaticSwitchParameter`, que era el plan:** los parametros estaticos solo existen en
instancias-**asset** (`UMaterialInstanceConstant`). `BP_Ganzfeld_SC` arma su material con
`CreateDynamicMaterialInstance`, y **un MID no puede setear un static switch**. Habrian hecho falta dos
materiales padre y logica en el BP para elegir. Se descarto.

✅ **Lo que se hizo, que da lo mismo y es gratis:** `WaveShade` entra al nodo `Custom` como un input nuevo
(**`UseShade`**, sexto; los cinco originales quedaron intactos, verificado por lectura) y el cuerpo del loop
arranca con:

```hlsl
if ((k >= 3) && (UseShade == 0.0)) { R6[k] = 0.0; continue; }
```

Con `[unroll]`, `k` es constante de compilacion: para `k < 3` la condicion se pliega a nada, y para `k >= 3`
queda **una rama uniforme** — `WaveShade` vale lo mismo en todos los pixeles del draw, asi que es 100% coherente
y el GPU **se saltea tres simplex 4D enteros**. Cierra con
`Shade = (UseShade == 0.0) ? 0.0 : (sm1 - sm0);`.

**Efecto esperado:** GAL_7 y GAL_8 (`WaveShade = 0`) pasan de 6 a 3 evaluaciones. **GAL_3 (`WaveShade = 2`) no
cambia en nada** — ni el costo ni el aspecto.
✅ Recompilo sin errores; `list_parameters` sigue devolviendo los 28 parametros (o sea compilo de verdad). Guardado.
🔬 **Sin medir.** Va al mismo build que el resto de los cambios pendientes.
⚠ **Supuesto a confirmar a ojo:** que con `WaveShade = 0` el termino `Shade` no alimente nada mas aguas abajo.
Si GAL_7 y GAL_8 se ven igual que antes, queda confirmado.

### 🔬 2026-09-15 (4a) — MEDIDO: cuanto valio cada cambio, y el relieve fuera de GAL_3
Tercera pasada en visor, con **resolucion 125** (era 135), **modo 2 podado** y **relieve tras rama uniforme**.
Comparado **al mismo reloj de GPU**, que es la unica forma honesta:

| estacion | antes | despues | reloj | cambio | FPS |
|---|---|---|---|---|---|
| **7 · MetaBlob + Ganzfeld** | 32,7 ms | **18,2 ms** | 640 MHz las dos | **−44%** | 28–30 → **48–56** |
| **8 · Burbujas** | ~25 ms | **~16,6 ms** | 640 MHz las dos | **−34%** | 31–35 → **51–53** |
| **3 · Ganzfeld solo** | 25,6 ms | **23,3 ms** | 545 MHz las dos | **−9%** | 37–39 → **43–45** |

✅ **La rama uniforme del relieve FUNCIONA y esta medida.** La estacion 3 es la unica con `WaveShade = 2`, o sea
**la unica donde la rama no saltea nada** — solo se llevo el −14% teorico de la resolucion (dio −9%; el resto
del frame no escala con resolucion). Las otras dos se llevaron resolucion **mas** los tres simplex 4D salteados.
🔬 **Eso mide el relieve indirectamente: saltearlo vale ~10 ms** en un cascaron a pantalla completa.
Beltran lo noto sin ver los numeros: *"donde mas glitcheo fue en la etapa donde solo esta el ganzfield"*.

✅ **2026-09-15: `WaveShade` de `GAL_3_Ganzfeld` puesto en 0** a pedido suyo (*"quita el relieve"*), para que la
estacion 3 se lleve tambien esos ~10 ms y quede cerca del presupuesto (~23 → ~13 ms esperado).
⚠ **`WaveAmount` queda en −1161,6** (valor suyo, lo movio desde el −537,3 que estaba anotado): eso es la **onda
geometrica por WPO**, que es vertex shader y no cuesta fill. O sea que la 3 queda en una combinacion que
**todavia no se vio**: onda geometrica SIN sombreado de relieve. Falta el juicio de Beltran.

### Lo que queda para abaratar el cascaron (es el fondo de TODAS las etapas)
1. ⬜ **Los tres canales de color son tres simplex 4D independientes** (`R6[0..2]` con offsets `O1`/`O2`).
   Es **el costo base que pagan todas las estaciones**. Derivar G y B del mismo ruido llevaria el nodo de 3
   evaluaciones a 1 → **el fondo costaria un tercio**. 🔴 Cambia como se comporta el color: decision de Beltran.
2. ⬜ Si alguna vez vuelve el relieve: bajarlo de 3 muestras a 1 (usar un solo canal en `P + L`) → el nodo pasa
   a 4 evaluaciones en vez de 6.
3. ❌ **NO tocar el ruido 4D.** Esta elegido a proposito (gotchas §319): sobre una esfera cualquier ruido 3D se
   lee "yendo hacia un lado". Cambiarlo rompe justo lo que hace que funcione.

### ✅ 2026-09-16 — `ShellMaterial`: el cascaron puede ser FONDO LISO (`M_GanzSolid_SC`)
Pedido de Beltran tras medir: en las estaciones 7 y 8 el cascaron es solo fondo y costaba **~12 ms, el doble que el
metaball**. *"Podria reemplazarse por una esfera con color de fondo nomas, es lo unico que necesito."*

**`M_GanzSolid_SC`** = duplicado de `M_Ganzfeld_SC` con **`Multiply_4.A` ← `Multiply_1`** (modo 0: degradado ×
banda de horizonte). Saltea el fluido (3 simplex 4D), el Veil (`Noise`) y la onda. Emissive = degradado × Brightness
+ dither R2; la respiracion WPO sigue. **Mismos nombres de parametro** → el BP lo maneja sin cambios.

🔴 **Por que hizo falta tocar el BP:** `ApplyGanzfeld` **nunca asignaba material** — solo empuja parametros con
`Set*ParameterValueOnMaterials`, que crean un MID sobre lo que haya en el slot. Un `overrideMaterials` escrito en la
instancia **no sobrevive**: el Construction Script lo pisa con un MID hijo del material del template (verificado
leyendo el `Parent` del MID).

**Cambio en el BP (cirugia de nodos, no `write_graph_dsl`):**
- Variable **`ShellMaterial`** (`MaterialInterface`, instance-editable, cat. `A - Forma`, default CDO = `M_Ganzfeld_SC`).
- En `ApplyGanzfeld`: `SetStaticMesh` → **`SetMaterial(Shell, 0, ShellMaterial)`** → escala → parametros.
- ✅ Orden verificado: el Construction Script es `ApplyGanzfeld` → `ApplyGanzMode`, asi que el `SetMaterial` corre
  ANTES de que `ApplyGanzMode` empuje los parametros del fluido. Si se invierte, la estacion 3 pierde su fluido.

| instancia | `ShellMaterial` | MID resultante (verificado tras recargar nivel) |
|---|---|---|
| `GAL_3` (`_C_0`) | `M_Ganzfeld_SC` | `MID_M_Ganzfeld_SC_0` |
| `GAL_7` (`_C_1`) | **`M_GanzSolid_SC`** | `MID_M_GanzSolid_SC_0` — colores violeta llegaron intactos |
| `GAL_8` (`_C_2`) | **`M_GanzSolid_SC`** | `MID_M_GanzSolid_SC_0` |

⚠ **Si `ShellMaterial` queda vacio en una instancia, el cascaron se pinta con el material por defecto.** Toda
instancia NUEVA hereda el default del CDO, asi que no pasa; pero cualquier instancia vieja colocada antes de hoy
hay que escribirla a mano (la variable nace vacia en instancias existentes — gotcha repetido).
🔬 Falta medir en visor (build del 2026-09-16).

### 🟢 2026-09-16 — MEDIDO en visor: fondo liso en 7 y 8. Beltran: *"funciona super bien… perfe para seguir trabajando"*
| estacion | inicio (15-sep) | 15-sep noche | **16-sep (fondo liso)** | FPS |
|---|---|---|---|---|
| 3 · Ganzfeld (fluido) | 25,6 ms | ~12 ms | **12,3–13,2 ms** | 70–73 |
| 7 · MetaBlob | 32,7 ms | 18,2 ms | **9,4–11,4 ms** | **72–73** |
| 8 · Burbujas | ~25 ms | ~16,6 ms | **8,9–9,3 ms** | **73** |
| 5 · Line Field | ~15 ms | ~13,6 ms | **14,9–16,2 ms** | ⚠ **61–62** |

✅ El fondo liso vale **~7–8 ms** por cascaron frente al fluido sin relieve. El fluido de la 3 no se toco (mismo
costo que ayer, y Beltran no reporto cambios de aspecto) → el `SetMaterial` antes de `ApplyGanzMode` es seguro.
🔴 **Unica estacion que hoy no sostiene 72 fps: la 5 (Line Field)**, 61–62 fps a 456 MHz. Es la proxima si se optimiza.
La 3 (12–13 ms) es la mas justa contra el presupuesto de 13,9 ms. Todo lo demas corre a tasa completa.
Errores del log del device: solo los 76 conocidos de `LogIoDispatcher` (fallback de memory-map, no fatal).
