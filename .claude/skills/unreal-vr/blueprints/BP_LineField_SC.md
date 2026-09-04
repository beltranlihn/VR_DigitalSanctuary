# BP_LineField_SC + M_LineGlow_SC — la luz dibujada con lineas (Core/Light/)

> Creado 2026-09-04. Efecto 1.6 del [plan de la galeria](../../../../docs/PLAN-GALERIA-EFECTOS.md).
> **Estado: 🟡 compilado, colocado en `/Game/TestMeshes` (`LineField_Test`, en 0/40000/150) y juzgado en el viewport. Falta el visor — y aca el visor importa mas que en los otros, ver "el riesgo" abajo.**

## Que es
Una superficie que **solo existe como lineas**: 120 tiras paralelas que ondulan por WPO. No hay plano, no hay relleno — la forma se lee entera por la deformacion de las lineas, como una topografia dibujada. Es la version "grafica" de la luz: en vez de un volumen luminoso, un trazo.

Sirve para un horizonte, un piso que respira, un techo, o una pared que se curva. Y como todo lo demas de la obra, es unlit + aditivo sobre negro.

## La malla `SM_LineGrid` — 120 tiras, 15.360 tris
Generada por script (Python → OBJ → `import_file`). Huella **100 × 100 uu** como el resto, asi que la cuenta de `FieldSize ÷ 100` es la misma que en `BP_FogSlab_SC`.

Cada tira es un quad largo de **64 segmentos** (para que la ola tenga donde curvarse) y ocupa el **55 % de su carril** — el 45 % restante es el hueco negro entre lineas. La UV esta pensada para el material: **`u` corre a lo largo de la tira** (0→1) y **`v` cruza su ancho** (0→1).

🔴 **Los 15.360 triangulos son baratos** (unlit, sin sombras) — el costo de este efecto no es la geometria.

## El material `M_LineGlow_SC` — unlit · **aditivo** · two-sided · Full Precision
```
prof  = (1 - |2v - 1|) ^ LineSharp            // perfil suave a lo ancho de la tira
tip   = saturate(min(u, 1-u) / TipFade)       // las puntas se disuelven
depth = DepthFade(ContactFade)                 // no corta duro contra la geometria
far   = saturate((FarFade - PixelDepth) / FarFadeRange)
idx   = floor((localY/100 + 0.5) * LineCount)  // 🔴 el INDICE de la linea, sin UV extra
vary  = lerp(1 - LineVary, 1, hash(idx))       // cada linea con su propio brillo
Emissive = LineColor * prof * tip * depth * vary * far * Brightness
WPO   = VertexNormalWS * (0.6·sin(px·WaveScale + t·WaveSpeed) + 0.4·sin(0.73·py·WaveScale - 1.37·t·WaveSpeed)) * WaveAmount
donde px, py = LocalPosition.XY / 100 * (FieldSizeX, FieldSizeY)   // centimetros reales
```

💡 **El truco que evita una malla mas complicada:** la UV es *por tira*, asi que `v` no dice donde esta la linea dentro del campo — y OBJ no soporta un segundo canal de UV ni color por vertice. La salida fue **sacar el indice de linea de `LocalPosition.Y`**: `floor((y/100 + 0.5) · LineCount)`. Con eso hay un hash por linea sin tocar la malla. ⚠ Por eso **`LineCount` tiene que coincidir con la malla** (120): si no, el hash agrupa o parte lineas.

⚠ Las coordenadas de la ola van en **centimetros reales** (`LocalPosition × FieldSize`), no en UV — la misma correccion que hubo que hacerle a `BP_FogSlab_SC`: asi un campo grande y uno chico ondulan igual y `WaveScale` significa lo mismo siempre.

⚠ `Sine` con `period = 6.283185`, o la entrada se multiplica por 2π (trampa ya conocida del proyecto).

## 🔴 El riesgo real: esto es contenido de alta frecuencia y el visor lo va a hacer titilar
Lineas finas sobre negro es **el peor caso de aliasing que existe**. En el viewport ya se ve moire donde la superficie se escorza; en el visor, con la cabeza en movimiento, eso **hormiguea**. MSAA 4x ayuda pero no lo resuelve solo.

Por eso el material trae **`FarFade` / `FarFadeRange`**, y no es un adorno: **apagar la lejania es la mitigacion principal**. Con el campo en 20 m, `FarFade` 2400 / `FarFadeRange` 1500 deja limpio lo cercano y disuelve en negro justo donde empezaria el hormigueo. Se ve mejor Y cuesta menos fill.

Si en el visor sigue molestando, en orden:
1. **Bajar `LineSharp`** (linea mas gorda y difusa, cubre mas de un pixel).
2. **Acercar `FarFade`**.
3. **Regenerar la malla con menos tiras** (48-64 en vez de 120) — es cambiar dos numeros en el generador.

## El BP
Un componente `Lines` (`SM_LineGrid`, sin sombras, `boundsScale` 2 porque el WPO saca vertices de los bounds). El Construction Script encadena **`ApplyLines`** (escala + todas las perillas) y **`ApplyLineFade`** (las dos de distancia). El tamaño se autora en centimetros: `FieldSizeX/Y` → escala del componente ÷ 100.

Categorias: `A - Forma` (FieldSizeX/Y 2000, LineCount 120) · `B - Color` (LineColor, Brightness 2.5) · `C - Linea` (LineSharp 1.6, LineVary 0.5, TipFade 0.12) · `D - Contacto` (ContactFade 60) · `E - Ola` (WaveAmount 180, WaveScale 0.0035, WaveSpeed 0.35) · `F - Distancia` (FarFade 2400, FarFadeRange 1500).

💡 **Como se usa la densidad:** las 120 lineas estan fijas en la malla, asi que **`FieldSize` es la perilla de densidad** — campo grande = lineas separadas, campo chico = lineas juntas. A 2000 cm quedan cada 16,7 cm.

## TODO
- [ ] Juicio de Beltran y **prueba en visor, mirando el titileo con la cabeza en movimiento** (es el punto flojo de este efecto).
- [ ] Rangos de slider a mano: FieldSizeX/Y 200-20000 · LineSharp 0,3-6 · LineVary 0-1 · TipFade 0,01-0,5 · ContactFade 0-400 · WaveAmount 0-600 · WaveScale 0,0005-0,02 · WaveSpeed 0-2 · FarFade 300-20000 · FarFadeRange 100-8000.
- [ ] Si gusta, una variante con las tiras cruzadas (rejilla) — es otra malla, el mismo material.
