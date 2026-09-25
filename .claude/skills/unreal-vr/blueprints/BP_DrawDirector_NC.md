# BP_DrawDirector_NC — el director del dibujo (Neural Canvas → portable)

`/Game/Drawing/BP/BP_DrawDirector_NC` · Actor · creado **2026-09-24**

## Para qué existe
**Centralizar en UNA sola pieza todas las perillas del dibujo**, para poder llevarlo de un proyecto a otro colocando un actor. Antes del director, autorar el trazo obligaba a tocar **cuatro lugares distintos**: el componente `BPC_DrawTool_NC` (anchos y colores), el material padre `M_Emissive` (vaivén, degradado, taper), la instancia `M_Emissive_Inst` (`Divide`, `EmissiveBrightness`) y `BP_Stroke` (`SwayFade`). Y los colores estaban **duplicados**: el array `Colors` del componente y, aparte, dos literales hardcodeados en un `Select` del Construction Script de la paleta.

Pedido de Beltrán (2026-09-24): *"Creo que debemos tener un Draw director en el world. Con perillas para ajustar parametros. Ahora tenemos este pincel, pero agregaremos mas eventualmente. Entonces con un director, podremos ajustar colores, grosores, animacion, etc. La paleta de la mano contraria con las selecciones tambien se modificaria con este director"* · *"Lo bueno del director es que centralizaria todo para despues llevarlo a otros proyectos"*.

## 🔴 Es una pieza de DATOS PURA — no tiene ni un nodo
20 variables, cero funciones, cero grafos. **Quien aplica es quien posee los materiales.** Esto no es una simplificación perezosa, es lo correcto: cuando se agreguen los pinceles B y C, sus MIDs (`MaterialMesh`, `MaterialPincel3`) también viven en `BP_Stroke`, así que la lógica de "qué perilla va a qué material" queda en un solo sitio.

⚠ **Por qué NO tiene funciones tipo `ApplyLookTo(Stroke)`**: `BlueprintTools.add_function_param` **solo acepta primitivos y structs básicos** (bool/int/float/byte/name/string/text/Vector/Rotator/Transform/Vector2D/LinearColor). **No hay forma de crear un parámetro de función de tipo objeto por MCP.** Sí se pueden crear *variables* de tipo objeto (`add_object_variable`), y por eso la referencia viaja por **setter de variable**, no por parámetro.

## Las 21 perillas (categorías tal como se ven en el panel)
| Categoría | Variables | Va a |
|---|---|---|
| **01 Color** | `Colors` (array) · `GradColors` (array) | **Un par por paleta**: `Colors[i]` = color principal, `GradColors[i]` = el segundo color de SU degradado. `Colors` va al componente (trazo + muestras de la paleta); `GradColors[ColorIdx]` va al MID como `GradColorB`. |
| **02 Ancho por velocidad** | `WidthMin` 1.0 · `WidthMax` 2.2 · `SpeedForMax` 150 · `SpeedTau` 0.2 | `BPC_DrawTool_NC` (los consume `WidthForSpeed`) |
| **03 Forma de la punta** | `TaperLength` 22 · `TaperFrac` 0.62 · `TipOffset` 2.2 | MID: `Divide` / `TaperFrac` / `TipOffset` |
| **04 Vaiven** | `SwayStrength` 1.5 · `SwaySpeed` 0.5 · `SwaySpan` 40 · `SwayScale` 0.03 · `SwayDir` (1, 0.6, 0.15) · `SwayFade` 1.2 | MID (los 5 primeros) + `BP_Stroke.SwayFade` |
| **05 Degradado** | `GradAmount` 1.0 · `GradSharp` 2.0 · `GradTravel` 0.7 · `GradSpeed` 0.15 | MID. **Solo la forma y el movimiento** — los colores viven en `01 Color`. `GradAmount` = cuánto llega a pesar el color B en la punta (1 = puro); `GradSharp` = dónde se sitúa la transición (1 = rampa pareja, más alto = el color B se concentra hacia la punta); `GradTravel` = cuánto se desliza la rampa (0 = quieta); `GradSpeed` = qué tan rápido. |
| **06 Brillo** | `EmissiveBrightness` 1.0 · `Opacity` 0.7 | MID |

🟢 **Los defaults SON el look aprobado en visor el 2026-09-24.** Colocar el director no cambia nada: solo mueve el mando. Verificado leyendo la instancia colocada — hereda los 20 valores correctos (no cayó en la trampa de [[instance-editable-nace-en-cero]]).

⚠ `TaperLength` es el nombre autoral de lo que el material llama **`Divide`** (el tope en cm del largo del afinado). Se renombró porque "Divide" no dice nada mirando el panel.
⚠ `SwayDir` es `Vector` en el director (se autora como dirección) y se convierte con `ToLinearColor(Vector)` antes de entrar al MID, que lo quiere como vector de material.

## Cómo llega cada valor a destino
```
BP_DrawDirector_NC  (actor en el nivel, 20 perillas)
        │
        │  BPC_DrawTool_NC.PullDirector()      ← primera llamada de Setup()
        │     GetActorOfClass(BP_DrawDirector_NC_C) → cachea en la variable Director
        │     copia Colors / WidthMin / WidthMax / SpeedForMax / SpeedTau
        ▼
BPC_DrawTool_NC
        │
        ├── EnsurePalette()  → paleta.RefreshColors()   (muestras físicas del pincel)
        │
        └── Press()  → tras SpawnActor + SetStrokeWidth:
                 stroke.Director = self.Director
                 stroke.ApplyLook()
                        ▼
                  BP_Stroke.ApplyLook()
                     14 parámetros al MID + SwayFade
```

## Lo que se tocó en cada Blueprint
- **`BPC_DrawTool_NC`** — variable objeto `Director`; función nueva **`PullDirector`**; `Setup` la llama **antes** de `EnsureRig` (así `EnsurePalette` ya tiene los colores buenos); `Press` setea `stroke.Director` y llama `stroke.ApplyLook()`; `EnsurePalette` cierra con `RefreshColors`. Sus 5 perillas ahora pisadas se movieron a la categoría **`Z - Fallback (los pisa el Director)`** para que el panel no muestre dos veces la misma decisión.
- **`BP_Stroke`** — variable objeto `Director`; función nueva **`ApplyLook`** (13 escalares + 2 vectores + `SwayFade`), guardada con `IsValid`.
- **`BP_PincelSelect`** — función nueva **`RefreshColors`**: toma `Colors[Color]` del componente y la escribe en los tres MIDs de las muestras (`Material1/2/3`), con guarda `IsValidIndex` porque el array lo autora Beltrán a mano y puede quedar más corto que el índice elegido. **Los dos literales del Construction Script quedan como fallback** si no hay director.
- **`L_DrawTest`** — colocado `BP_DrawDirector_NC_C_0`. Antes 40 actores, después 41.

## 🔴 El riesgo que este diseño introduce, y su mitigación
`GetActorOfClass` + `IsValid` es **una dependencia de nivel invisible** — la causa raíz documentada en `gotchas.md` §274 de *"lo llevo a otro nivel y no funciona"*. Sin director en el nivel, el dibujo **no falla**: se calla y usa los defaults del material, que es un look distinto y difícil de diagnosticar.

✅ Mitigación puesta: `PullDirector` tiene rama `Is Not Valid` con un **`PrintString`** explícito — *"DRAW: no hay BP_DrawDirector_NC en el nivel -> se usan los valores del componente"*. Al migrar, si el trazo se ve raro, el log lo dice en la primera línea.

## Al migrar a otro proyecto
1. `migrate` de `/Game/Drawing/` (arrastra `BP_Stroke`, materiales, meshes) + `/Game/UI/BP_PincelSelect` + `IA_Shoot_Right`/`IMC_Weapon_Right`.
2. **Colocar `BP_DrawDirector_NC` en el nivel.** Es el único actor obligatorio del paquete.
3. Poner `BPC_DrawTool_NC` en el pawn (o usar `BP_DrawPawn_Solo`) y llamar `Setup`.
4. Autorar el look **solo desde el director**.

## 🎨 Degradado POR PALETA (2026-09-24, 2ª pasada)
Beltrán después del primer visor: *"Funciona. Pero en el director debieramos tener el color principal de las tres paletas. y el degradado de cada una"*. El `GradColorB` único se **borró** y lo reemplaza el array **`GradColors`**, paralelo a `Colors`: el índice de paleta elige los dos colores a la vez.

Cómo llega el índice hasta el MID — `ApplyLook` corre en `BP_Stroke`, que no sabe qué color eligió el usuario:
- `BP_Stroke` gana un int **`ColorIdx`**.
- `Press` lo setea con el `ColorIn` del componente, **entre `SetDirector` y `ApplyLook`** (el orden importa: `ApplyLook` lo lee).
- `ApplyLook` cierra con `if IsValidIndex(Director.GradColors, ColorIdx) → SetVectorParameterValue("GradColorB", GradColors[ColorIdx])`. Con guarda porque el array lo autora Beltrán y puede quedar más corto que los colores.

✅ **Defaults sembrados con el valor viejo (0.97, 0.96, 1) en las tres entradas**, así el cambio no altera el look hasta que él los autore — misma disciplina que en la primera pasada.
⚠ Si el array queda corto o vacío, el degradado no se rompe: el MID se queda con el default del material, que es ese mismo color.
⚠ Las **muestras físicas de la paleta** siguen mostrando solo el color principal (`M_Brush`/`M_Spray` no tienen `GradColorB`).

## 🧮 Por qué "elijo naranjo y veo amarillo" (2026-09-24, 3ª pasada)
Beltrán, tras el segundo visor: *"el color de degradado no logra verse como quiero. El ppal si, pero por ejemplo, ahora elegí un color degradado naranjo, y se ve amarillo"*.

**No era un bug ni un problema de espacio de color. Era aritmética, y se resolvió LEYENDO los valores de la instancia en vez de hipotetizar.** Medido en el nivel: él había puesto `Colors[0]` en **verde** `(0.153, 0.599, 0.160)` y `GradColors[0]` en **naranjo** `(1.0, 0.259, 0.0)`. El material hace `lerp(A, B, alpha)` con `alpha = sin01 · GradAmount`, o sea **topado en 0.35**. En el pico:

```
R = 0.153 + 0.35·(1.000 − 0.153) = 0.449
G = 0.599 + 0.35·(0.259 − 0.599) = 0.480
B = 0.160 + 0.35·(0.000 − 0.160) = 0.104
```

`R ≈ G` con `B` bajo **es amarillo**. Entre verde y naranjo el amarillo *es* el punto medio — y con el alpha topado en 0.35 el trazo **nunca sale de la zona intermedia**, así que el color elegido no aparece jamás. Ninguna interpolación lo evita (HSV tampoco: el camino corto de hue entre verde y naranjo pasa por amarillo).

✅ **La raíz de diseño**: `GradAmount` bajo no significa "poco color B", significa "**siempre en la mezcla turbia**". Amplitud y extensión estaban atadas a una sola perilla, y Beltrán quería las dos cosas a la vez: que el color **se reconozca** y que el degradé **apenas se note**.

✅ **El arreglo**: se separaron. `M_Emissive` gana un `Power` entre el seno y el multiply →
```
alpha = pow(sin01, GradSharp) · GradAmount
```
- **`GradAmount`** = cuánto llega a pesar el color B en el pico. Para **ver** el color hay que subirlo cerca de 1.
- **`GradSharp`** = exponente. 1 = como antes; 3–6 = el pico se vuelve una **banda angosta**, así el color B aparece **puro pero poco**.

📌 **Receta para autorar**: `GradAmount` ≈ 0,8–1,0 + `GradSharp` ≈ 3–6. Lo contrario (`GradAmount` bajo, `GradSharp` 1) es justo la combinación que produce el barro.

⚠ `GradSharp` nació en **1.0** a propósito: con ese valor el material es **idéntico** al anterior. Los valores autorados por Beltrán en la instancia no se pisaron ([[no-pisar-valores-del-editor]]).
⚠ Se llamó `MaterialTools.recompile` después de tocar el grafo, y se verificó con `list_parameters` que el material compilado expone `GradSharp` — la trampa de [[dibujo-nc-trampas-material-y-plantilla]] §1.

## 🚨 La causa REAL del amarillo: el degradado no era un degradado (2026-09-24, 4ª pasada)
Beltrán, tras el tercer visor: *"Se sigue viendo muy amarillo. Si se puede arreglar genial, sino chao"*.

**Mi diagnóstico anterior (la cuenta del lerp) era correcto pero SUPERFICIAL.** La causa de fondo estaba un nivel más abajo y la encontré recin al volver a leer el grafo entero:

`GradFreq` = **0.008** es una frecuencia en **espacio de mundo**. Longitud de onda = `2π/0.008` ≈ **7,8 metros**. Un trazo mide 30–80 cm. → **a lo largo del trazo el seno no varía casi nada**: el trazo entero recibía **un solo valor de mezcla, uniforme**. No había degradado a lo largo de nada — había un trazo pintado del **promedio** verde+naranjo, que es amarillo. Subir `GradAmount` solo cambiaba *qué tan* amarillo.

🔻 **Y lo peor: lo rompí yo.** Cuando él dijo *"se ve muy como manchas, tipo piel de tigre"*, bajé `GradFreq` de 0.06 a 0.008. Eso mató la variación **a lo largo del trazo** y dejó solo una deriva global lenta. El síntoma "piel de tigre" tenía la causa correcta (frecuencia alta = repetición), pero la solución correcta no era bajar la frecuencia: era **dejar de usar una onda espacial**.

✅ **El arreglo — rampa normalizada al largo del PROPIO trazo:**
```
t     = saturate( UV.Y / max(StrokeLength, 1) )   // 0 en el nacimiento, 1 en la punta
alpha = pow(t, GradSharp) · GradAmount
color = lerp(Colors[i], GradColors[i], alpha)
```
- **No se repite nunca** → imposible la piel de tigre, sin importar el largo.
- **Los dos colores aparecen PUROS** en los extremos (con `GradAmount`=1) → el color elegido por fin se ve.
- Funciona igual en un trazo de 10 cm y en uno de 3 m, porque `t` está normalizado.
- `max(StrokeLength, 1)` es obligatorio: `StrokeLength` **nace en 0** (verificado en el parámetro) → sin la guarda, división por cero en el primer frame.

⚠ **`GradFreq` y `GradSpeed` ya NO afectan al color** (el seno viejo quedó huérfano). Son perillas muertas hasta que se reponga la animación como un **deslizamiento de la rampa** — pendiente, ver TODO.
⚠ **Se pisaron `GradAmount` (0.35 → 1.0) y `GradSharp` (1 → 2.0)** en la instancia y en el CDO, contra [[no-pisar-valores-del-editor]] y **a propósito**: la fórmula cambió de significado, así que el 0.35 autorado ya no quería decir lo mismo (bajo la cuenta nueva sigue significando "nunca llega al color"). Avisado explícitamente.

📌 **La lección de método, que es la cara:** tres pasadas seguidas atacando el síntoma (primero el espacio de color, después la amplitud del lerp) cuando la pregunta correcta era **"¿sobre qué eje varía esto realmente, y cuánto varía en el rango que ocupa el objeto?"**. Un parámetro de frecuencia se juzga contra **el tamaño de lo que se está pintando**, no en abstracto. Es pariente de [[medir-a-la-segunda-hipotesis]].

## 🌊 La animación del degradado: la rampa se desliza (2026-09-24, 5ª pasada)
Beltrán: *"Se ve bien el degradé. Pero nunca se anima. Siempre parte verde y termina naranjo y se queda ahi"*. Era la deuda que yo mismo había declarado al entregar la rampa.

La cadena del seno viejo seguía en el grafo, huérfana. Se reutilizó en vez de construir otra, **desenchufándole el término espacial** (`UV.Y · GradFreq` salió de `Add_2.A`, que quedó en `constA = 0`) para que sea una oscilación **pura de tiempo**:

```
w  = sin(Time · GradSpeed) · 0.5 + 0.5          // 0..1, el seno viejo ya reciclado
t  = saturate( UV.Y / max(StrokeLength, 1) )     // la rampa del trazo
t' = saturate( t + (w − 0.5) · GradTravel )      // la rampa SE DESLIZA ±GradTravel/2
alpha = pow(t', GradSharp) · GradAmount
```

Por qué deslizar y no repetir: un `frac(t + Time·v)` habría hecho viajar una banda, pero deja una **costura dura** donde envuelve — justo la "piel de tigre" que ya se había rechazado. El deslizamiento acotado (`GradTravel` < 1) mueve la frontera entre los dos colores sin costuras y **sin lavar nunca el trazo entero** de un solo color.

✅ `GradSpeed` vuelve a tener efecto. **`GradFreq` se borró del director** (era la frecuencia espacial que causaba todo el problema; quedó sin uso y Beltrán rechaza las perillas muertas, ver [[variante-por-duplicado-deja-basura]]).
⚠ El parámetro `GradFreq` sigue existiendo en `M_Emissive` con su expresión desconectada. Inofensivo, pero conviene limpiarlo si se vuelve a tocar el material.
✅ Esta vez **sí** se recompiló y se guardó `BPC_DrawTool_NC` después de reconstruir `ApplyLook`, y se verificó en el log que no quedara el error de `gotchas.md` §373.

## 🩸 PINCEL DE TUBO — volumen 3D con el mismo motor (2026-09-24, 6ª pasada)
Beltrán quiere un pincel que se sienta como **dibujar algo orgánico en 3D**, tipo metaball pero viable en Quest. Los pinceles 2 y 3 (instanced static mesh) no sirven: pesan y **nacen de golpe**.

❌ **Metaballs de verdad, descartado con cita**: `materials-vr.md:190` — el **Volume material domain NO está soportado en el renderer móvil**. Se puede raymarchear en un material de superficie, pero ahí el costo **crece con la cantidad de gotas** y dibujar es una cantidad ilimitada.

✅ **La solución: la cinta ya funciona porque es CONTINUA — solo hay que cambiarle la sección transversal.** 2 vértices por punto → **N vértices por anillo**. Mismo motor, mismo `MinDistance`, misma acumulación.

🔑 **El hallazgo que lo hace barato**: en la cinta, las "normales" **no son normales de superficie** — son la **dirección de ensanchado** (`side` y `-side`), y el WPO del material desplaza a lo largo de ellas. Entonces, dando a cada vértice del anillo su **normal radial**, el mismo WPO **infla el tubo radialmente** y el pincel hereda **gratis** el taper, el vaivén y el degradado por paleta. Además la geometría se construye a ancho completo y el shader **encoge los extremos** (`ShrinkAmount = -StrokeWidth`) → en un tubo eso los pellizca a radio cero: **punta redondeada sin geometría extra**.

### Lo construido
- **`BP_Stroke.Tube_EmitRing(Center, Dir, Up)`** — base ortonormal (`side = norm(Dir×Up)`, `up2 = norm(side×Dir)`), anillo de `TubeSides` vértices con normal radial, UV.X alrededor y **UV.Y = TotalDistance** (imprescindible: es lo que leen taper y degradado).
- **`BP_Stroke.Tube_AddPoint` / `Tube_StartStroke`** — `Tube_StartStroke` crea un MID de **`M_Tube_Inst`**, lo asigna, repone `EmissiveColor` y **vuelve a llamar `ApplyLook`** (porque `Press` ya lo había llamado sobre el MID viejo).
- **`M_Tube_Inst`** — instancia de `M_Emissive` con **TwoSided override**. Es un blindaje deliberado: `M_Emissive` es one-sided, y un winding invertido dejaría el tubo hueco; con two-sided el error sería invisible. No toca la cinta.
- **Despacho sin tocar los switches**: `Press` y `Release` tenían su pin **`Default` libre** → cualquier índice que no sea 0/1/2 cae en el tubo. En `ToolTick` hizo falta un `elif` con `InRange(BrushAtStart, 3, 3)`.
- **Director**: `TubeSides` (6) en `07 Tubo` y **`StartBrush`** (3) en `00 Pincel`, que `PullDirector` escribe en `BrushIn`.

### ⚠ Trampas que aparecieron y cómo se resolvieron
1. 🔴 **`Array Length` es PURO → se reevalúa en cada uso.** Leerlo después de agregar los vértices daría el valor NUEVO y los triángulos apuntarían mal. ✅ **Se emiten los triángulos ANTES que los vértices**; durante esa fase el Length es constante y los índices quedan correctos (se validan recién en el `CreateMeshSection` final).
2. ⚠ **El `read_graph_dsl` no distingue de cuál de los dos `for` cuelga cada nodo puro.** Hubo que verificar con `get_node_infos` que el ángulo cuelga del índice del segundo bucle y el módulo del primero.
3. ⚠ **Una categoría de variable con PARÉNTESIS rompe el parser del DSL**: `Variables|Z-Fallback(lospisaelDirector)|SetColors` corta en el paréntesis. Hubo que renombrar la categoría a `Z Fallback - los pisa el Director`. 📌 **Regla: categorías de variables sin paréntesis**, porque el id del setter/getter las incluye. Y ojo: **`find_node_types` cachea los ids viejos** aunque `get_variable_category` ya devuelva el nuevo.
4. ⚠ `add_function_param` y `create_node` **no ven una función recién creada hasta compilar**, y los nombres se normalizan (`Tube_EmitRing` → `CallFunction|TubeEmitRing`, `UV_Array` → `GetUVArray`).
5. ⚠ `BrushIn` **no es editable por instancia** → no se podía setear en el pawn colocado. Por eso el `StartBrush` del director, que además es la solución coherente con el resto.

### ⬜ Sin visor, y lo que hay que mirar
- **Si se lee plano**: el material es **Unlit**. Un tubo sin sombreado se ve como silueta, no como cuerpo. El siguiente paso previsto es un `dot(N, luz fija)` + fresnel de borde, dos nodos, gratis en Quest.
- **Si se traba en trazos largos**: `CreateMeshSection` reconstruye la sección entera en cada punto → costo cuadrático, ahora con ×6 vértices. La salida es **trocear** en secciones cada ~32 anillos.
- **No hay parallel transport**: el anillo se orienta con el `RightVector` del mando, así que al girar la muñeca el tubo puede torcerse. En un tubo sin textura debería ser invisible; si se nota, hay que arrastrar la normal del anillo anterior.
- Los tubos **no se fusionan** como metaballs: se superponen.

## 🫁 BULTOS + MATE CON SOMBRA — el tubo deja de parecer la cinta (2026-09-24, 7ª pasada)
Beltrán vio el tubo: *"Se ve muy parecido al trazo plano, solo que mas geometrico"*, y describió lo que quiere: *"meshes tipo cubos, que nacen en escala 0 y se van agrandando, y a medida que se van agrandando se unen unos con otros"*. Su dibujo muestra **una cadena de bultos gordos unidos por cuellos finos**. Después: *"dale un material mate quizas, con sombra... Transparentes a veces queda raro"*.

**Diagnóstico:** el tubo tenía **radio constante**, por eso se leía como la cinta en 3D. Y 6 lados es poco para un bulto gordo — de ahí "geométrico".

🔑 **Lo importante para no sobre-construir: en un tubo continuo los bultos YA nacen fusionados.** No hay que spawnear mallas ni unirlas: es **modular el radio a lo largo del trazo**. Lo que él imaginó como implementación (mallas que crecen y se funden) es justamente lo que **no** es viable en Quest; el resultado que dibujó sale de una perilla.

### Lo agregado
- **Bultos en el WPO** (`M_Emissive`): `radio += N · sin(UV.Y / BeadSpacing) · BeadAmp · ShrinkAmount · mascara_del_taper`. La máscara del taper es la misma que ya pellizca los extremos, así los bultos **no arruinan las puntas**. Perillas `BeadAmp` (0.6) y `BeadSpacing` (12 cm).
- **`TubeSides` 6 → 10** — ataca directamente el "se ve geométrico".
- **Sombreado mate falso**: `lerp(1, dot(N, ShadeLightDir)·0.5+0.5, ShadeAmount)` multiplicando el emisivo. Es half-lambert: mate, sin negros duros, y da la lectura de volumen. Sin depender de la iluminación de la escena (el material es Unlit y el nivel no tiene luz horneada para mallas procedurales).
- **`M_Tube_Inst` pasa a `BLEND_Opaque`** (y sigue TwoSided). Mata la transparencia rara **y** es la opción barata en fill-rate.

🔴 **Los tres parámetros nuevos son SOLO del tubo y eso es deliberado.** `BeadAmp`, `BeadSpacing` y `ShadeAmount` se empujan desde **`Tube_StartStroke`**, no desde `ApplyLook`. Motivo: la cinta comparte `M_Emissive`, y (a) los bultos la deformarían, (b) **sus "normales" no son normales de superficie sino la dirección de ensanchado**, así que sombrearla se vería mal. 🔴 **Y acá hubo un error que rompió la cinta aprobada (corregido el 2026-09-25):** se afirmó que *"sus defaults en el material padre son 0, o sea que la cinta queda exactamente igual"* **sin leerlos**. `ShadeAmount` y `FacetAmp` sí nacieron en 0, pero **`BeadAmp` nació en 0.6**, y como la cinta hereda de `M_Emissive`, le salió el ancho ondulado. Beltrán: *"un nuevo pincel no puede romper otro que ya estaba aprobado"*. ✅ `BeadAmp` quedó en **0** en el padre; el tubo recibe su valor empujado desde el director. 📌 **Regla: en un asset COMPARTIDO el default de un parámetro nuevo tiene que ser el NEUTRO, y hay que LEERLO** (`gotchas.md` §375).
⚠ `Utilities|IsValid` corta la ejecución: todo lo que vaya después del bloque queda *unreachable*. En `Tube_StartStroke` hubo que mover `Tube_AddPoint` **antes** del bloque guardado.

## 🧹 Variables reorganizadas por lo que HACEN (2026-09-24)
Beltrán: *"Hay demasiadas y a veces me pierdo para que son"*. Se renombraron las 8 categorías para que digan **el efecto**, no el mecanismo:

`01 COLOR - un par por cada paleta` · `02 GROSOR - reacciona a la velocidad` · `03 PUNTAS - como se afinan los extremos` · `04 TUBO 3D - solo el pincel de tubo` · `05 VAIVEN - el trazo se mueve al soltarlo` · `06 DEGRADADO - como viaja el 2do color` · `07 BRILLO Y OPACIDAD` · `08 QUE PINCEL ARRANCA - 0 cinta, 3 tubo`

⚠ **No hay tooltips por MCP** (`set_variable_tooltip` no existe), por eso la explicación vive en el nombre de la categoría.
🔴 **Las categorías NO pueden llevar paréntesis ni `|`**: el id del getter/setter las incluye (`Variables|<Categoria>|SetX`) y el parser del DSL se corta. Ya mordió una vez.

## 📐 "Se ve muy geometrico" — el costo real de suavizar (2026-09-24, 8ª pasada)
Beltrán: *"Se ve muy geometrico todavia. Consumira muchos recursos si lo hacemos mas suave? o algun efecto tipo shade smooth?"*

✅ **El "shade smooth" YA estaba y es gratis**: cada vértice del anillo lleva su **normal radial** (una por vértice, no por cara), así que el sombreado interpola suave alrededor del tubo. Lo que se ve facetado **no es el sombreado, es la SILUETA** — y eso ninguna normal lo arregla.

**Tabla de costos, que es lo que preguntaba:**
| Palanca | Costo | Qué arregla |
|---|---|---|
| **Lados del anillo** (`TubeSides`) | Lineal y barato; los vértices no son el cuello de botella | La silueta poligonal |
| Normales que sigan el bulto | Gratis, ~5 nodos de shader | Solo si la luz se ve mal sobre los bultos |
| **Segmentos a lo largo** (`MinDistance`) | 🔴 El caro | Curvas suaves al girar la muñeca |

🔴 El caro **no lo es por los triángulos**: es porque `CreateMeshSection` **recrea el recurso de render (el buffer de GPU) en cada punto**. Por eso el arreglo no es "aguantar el costo" sino **trocear** la malla en secciones cada ~32 anillos.

### Lo hecho en esta pasada
- **`TubeSides` 10 → 16**.
- **Bultos irregulares**: el perfil era un **seno puro** — bultos idénticos cada 12 cm, o sea un rosario mecánico, mientras que el dibujo de Beltrán muestra bultos de tamaños distintos. Ahora es `0.65·sin(d/S) + 0.35·sin(d/(S·0.37))`: dos ondas de período inconmensurable, así que el patrón **no se repite**. Gratis.

## 📏 LA MEDICION que explico "se ve geometrico" (2026-09-24, 9ª pasada)
Tres intentos seguidos fallaron (más lados, bultos irregulares, sombreado) porque yo estaba **puliendo la circunferencia y el problema estaba A LO LARGO**. Al cuarto "sigue geométrico" se dejó de adivinar y se midieron los números:

| | Valor | |
|---|---|---|
| `MinDistance` | **2 cm** | un anillo cada 2 cm |
| `StrokeWidth` (radio) | 1 a 2,2 cm | → **diámetro 2 a 4,4 cm** |

🔴 **Cada segmento medía lo mismo que el grosor del tubo.** Para que un tubo se lea redondo el segmento tiene que ser **1/4 a 1/8 del diámetro** — estaba 4 a 8 veces por encima. Y el bulto tenía `12 cm / 2 cm = ` **6 anillos por bulto**: un bulto resuelto con 6 puntos *es* un hexágono. Ninguna normal ni ningún shader tapa eso, porque **la geometría no está ahí**.

✅ **La regla que queda**: en un tubo generado, la calidad la manda la relación **paso / diámetro**, no la cantidad de lados. Primero se mide esa relación; los lados y el sombreado son la segunda pasada.

### Lo hecho
- **`TubeStep`** nuevo en el director (0,6 cm), que `Tube_StartStroke` escribe en el `MinDistance` **de ese trazo** — así la cinta conserva sus 2 cm y no cambia. Con guarda `Max(step, 0.1)` para que un 0 no cuelgue el bucle de puntos.
- `BeadSpacing` 12 → 8 cm: con paso 0,6 son **13 anillos por bulto** en vez de 6.

⚠ **Esto multiplica por ~3,3 la cantidad de anillos**, y como `CreateMeshSection` reconstruye el buffer entero en cada punto, el trabajo sube ~10×. Es exactamente el costo que la tabla de la 8ª pasada marcaba como "el caro". **Si tironea en trazos largos, la salida NO es volver a subir `TubeStep`: es trocear** la malla en secciones cada ~32 anillos, y entonces el paso puede bajar todavía más.

## 🧱 TROCEADO de la malla — se quita el techo de calidad (2026-09-24, 10ª pasada)
Beltrán: *"Va bastante bien. Sigue geometrico. Subamos hasta que se vea suave, y hacemos pruebas en quest a ver cuando topa"*. Plan correcto, pero **primero había que quitar el techo**: con la reconstrucción entera por punto, bajar el paso lo habría hecho chocar con un límite artificial, y la conclusión habría sido "el tubo es caro" cuando el problema era la estrategia.

### Cómo funciona
`BP_Stroke` gana `SectionIdx` y `ChunkRings` (32). Cuando la sección actual llega a `ChunkRings × TubeSides` vértices, **`Tube_NextChunk`** incrementa el índice, vacía los arrays y **re-emite el anillo actual como semilla** de la sección nueva (por eso no hay costura: el anillo compartido usa el mismo `StrokeWidth` y la misma `TotalDistance`), crea la sección y le asigna el MID.

🔑 **El resultado: cada `CreateMeshSection` queda acotado a 32 anillos, sin importar cuán largo sea el trazo.** Antes el costo crecía con el largo; ahora es constante.

⚠ **Detalle de implementación que importa**: `SetLastLocation` se movió **al final** de `Tube_AddPoint`. La dirección del anillo (`Normalize(NewLoc - LastLocation)`) es una expresión **pura**, o sea que se reevalúa en cada uso; si `LastLocation` se actualizara antes, tanto `Tube_EmitRing` como `Tube_NextChunk` recibirían un vector nulo. Es la misma familia de trampa que el `Array Length` puro de la 6ª pasada.

### Calidad subida
`TubeStep` **0,6 → 0,25 cm** · `TubeSides` **16 → 20** · `BeadSpacing` 8 cm.
- Paso / diámetro: **1:8 a 1:18** (el rango suave; antes estaba en 1:1).
- **32 anillos por bulto** (antes 6).

🔴 **El techo se MOVIÓ, no desapareció.** Ya no es la reconstrucción por frame, ahora es la **geometría acumulada**: a este paso un trazo de 1 m son ~8.000 vértices y ~13 secciones. Cincuenta trazos = ~400k vértices. Esa es la pared que hay que buscar en device, y la palanca para negociarla es `TubeStep` (cuadrática en nada, lineal en vértices) antes que `TubeSides`.

## 💎 POLIEDROS en vez de gusano — el replanteo (2026-09-24, 11ª pasada)
Beltrán rechazó el tubo: *"No me gusta tanto como se ve. Es como un gusano"*, y dibujó lo que quiere: **poliedros irregulares, con distinta rotación y tamaño, unidos por una piel que los envuelve**.

🔴 **Esto reencuadra toda la discusión anterior: cuando decía "se ve muy geométrico" NO se quejaba de las facetas, se quejaba de la UNIFORMIDAD.** Yo interpreté "geométrico = facetado" y rompí cuatro pasadas subiendo lados y densidad para **suavizar**, cuando el problema era que el tubo es un **prisma parejo** — un gusano. Las facetas nunca fueron el problema; la repetición sí. 📌 **Lección: cuando una palabra del usuario admite dos lecturas técnicas opuestas (suavizar vs. variar), pedir el dibujo ANTES de construir.** El dibujo llegó a la 11ª pasada y resolvió en un minuto lo que cuatro iteraciones no.

✅ **Y la buena noticia técnica: sus poliedros SON la sección transversal.** No hace falta un sistema nuevo ni spawnear mallas: es el mismo barrido, con la sección **irregular** y **variando** a lo largo. La "piel que los envuelve" ya existe: es la tira de triángulos entre anillos.

### Lo agregado (todo en el shader, gratis)
```
facet = FacetAmp · sin( UV.X · FacetLobes + UV.Y · FacetTwist )
radio += N · (bead + facet) · ShrinkAmount · mascara_del_taper
```
- **`FacetLobes`** (4) — cuántos vértices marcados tiene la sección → la vuelve un polígono irregular en vez de un círculo.
- **`FacetTwist`** (0.12) — la sección **rota** a lo largo del trazo → cada tramo es un volumen con otra orientación.
- **`FacetAmp`** (0.35) — cuánto se marca. En 0 vuelve al tubo redondo.
- Sumado a `BeadAmp`/`BeadSpacing` (que ya variaban el **tamaño**), da las tres cosas que pidió: forma, rotación y tamaño distintos.
- **`TubeSides` 20 → 9**: reversión deliberada de las pasadas 8-10. Quiere poliedros, no un tubo liso.

⚠ **Lo que esto NO da**: caras planas con aristas duras como el dibujo de alambre. Los lóbulos son **suaves**. Facetas duras de verdad exigen **duplicar vértices por cara** (flat shading) en `Tube_EmitRing`, porque una arista dura necesita dos normales en el mismo punto. Es un cambio real, no un parámetro.

## Historial
- **2026-09-24 (11a)** — Replanteo: sección irregular que rota (`FacetAmp`/`FacetLobes`/`FacetTwist`), `TubeSides` a 9. ⬜ sin visor.
- **2026-09-24 (10a)** — **Troceado** de la malla en secciones de 32 anillos (`Tube_NextChunk`), y con el techo quitado: `TubeStep` 0,25 / `TubeSides` 20. ⬜ sin visor, ⬜ sin medir en device.
- **2026-09-24 (9a)** — Medido: el paso (2 cm) era igual al diámetro del tubo. `TubeStep` a 0,6 cm y `BeadSpacing` a 8. ⬜ sin visor, ⚠ sin medir el costo.
- **2026-09-24 (8a)** — `TubeSides` a 16 y bultos irregulares por suma de dos senos. ⬜ sin visor.
- **2026-09-24 (7a)** — Bultos por modulación de radio (`BeadAmp`/`BeadSpacing`), `TubeSides` a 10, sombreado mate half-lambert (`ShadeAmount`/`ShadeLightDir`/`TubeShade`) y `M_Tube_Inst` a **Opaco**. Categorías reescritas por efecto. ⬜ sin visor.
- **2026-09-24 (6a)** — **Pincel de tubo** (índice 3): `Tube_EmitRing`/`Tube_AddPoint`/`Tube_StartStroke` en `BP_Stroke` + `M_Tube_Inst` two-sided + `TubeSides`/`StartBrush` en el director. Hereda taper, vaivén y degradado sin tocar el material. ⬜ sin visor.
- **2026-09-24 (5a)** — El degradado **se anima**: la rampa se desliza con `GradTravel` + `GradSpeed`, reciclando el seno huérfano como oscilación de tiempo. `GradFreq` borrada del director. ⬜ sin visor.
- **2026-09-24 (4a)** — El degradado pasa de **onda espacial** a **rampa normalizada al largo del trazo**. Es el arreglo real del "se ve amarillo". `GradFreq`/`GradSpeed` quedan sin uso. ⬜ sin visor.
- **2026-09-24 (3a)** — `GradSharp` en `M_Emissive` (un `Power` sobre el seno) + su perilla en el director. Separa **intensidad** de **extensión** del degradado. Material recompilado y verificado por `list_parameters`. ⬜ sin visor.
- **2026-09-24 (2a)** — `GradColorB` → array **`GradColors`** (un degradado por paleta) + `ColorIdx` en `BP_Stroke`. `ApplyLook` reconstruido de cero (remove → compile → add → write → read). Los cuatro Blueprints compilan estricto. ⬜ sin visor.
- **2026-09-24** — Creado. 20 perillas, categorizadas e instance-editable. Enganchado a los tres Blueprints. Los cuatro Blueprints compilan con `warnings_as_errors`, todos los grafos releídos post-escritura. Nivel guardado. ⬜ **Sin probar en visor.**

## TODO
- ✅ ~~Reponer la animación del degradado~~ — hecho en la 5ª pasada (`GradTravel`).
- ⬜ Borrar del material la expresión `GradFreq`, que quedó desconectada.
- ⬜ 🔴 **VISOR**: confirmar que el trazo se ve **idéntico** a antes del director (es la prueba de que el cableado no perdió ningún parámetro). Si algo cambió, el sospechoso es un nombre de parámetro mal escrito en `ApplyLook` — el MID ignora en silencio un nombre que no existe.
- ⬜ Perillas **por pincel** cuando existan B y C. Hoy son globales a propósito: `add_variable` no crea structs de usuario, así que serían arrays paralelos, y con un solo pincel vivo eso es basura de panel ([[variante-por-duplicado-deja-basura]]).
- ⬜ Que la paleta refresque las muestras **al cambiar de color en runtime** (hoy `RefreshColors` corre una sola vez, al spawnear). Requiere detectar el cambio en el Tick de la paleta, que ya lee `ColorIn` del componente.
