# BP_Orb_SC + M_Orb_SC — el objeto que se ve HECHO DE ALGO (Core/Light/)

> Creado 2026-09-04 por Nico, brief [`docs/BRIEF-NICO-EFECTOS.md`](../../../../docs/BRIEF-NICO-EFECTOS.md) §5.3 (galería de efectos, look-dev). Es el **primero de los tres efectos de Nico**. Un selector de *look* para orbes sólidos — lo que faltaba: todo lo del proyecto era superficie plana y la obra está llena de orbes (respiración, sonido, la ameba, las burbujas de Attracting).
> **Estado: 🟡 material + BP compilados sin errores, 3 instancias colocadas en `L_EffectTest_Nico` y juzgadas en el viewport del editor (los 3 looks se ven distintos y el material lee todos sus parámetros). Falta el juicio de Beltrán y el visor.**

## Qué es
Un `M_Orb_SC` **unlit · translúcido · Full Precision (expresiones)** con un selector `Look` (0/1/2) resuelto **por píxel** (dos `lerp` encadenados sobre un escalar), y un `BP_Orb_SC` con el patrón del proyecto: componente `Orb` (esfera del motor) + variables instance-editable por categoría + Construction Script que crea el MID y empuja todo → se ve en el viewport **sin Play**. Las 3 texturas matcap las genera un script Python (PNG puro, sin PIL).

🔴 **Por qué `Look` es un escalar por-píxel y NO un static switch:** el patrón del proyecto (componente + MID + Construction Script) usa un **MID dinámico**, y **un MID no puede cambiar static switches** (son compile-time, se heredan del padre). Con static switch el autor no podría girar `Look` en el panel y ver el cambio en el viewport. El costo (las 3 ramas se evalúan por píxel) es barato para un orbe chico; si en la obra hiciera falta congelarlo, se hace con 3 Material Instance Constants (una por look) y `static switch` — decisión de fill-rate para más adelante. **La misma tensión va a aparecer en `BP_LightPanel_SC` §5.1, donde el brief pide static switch: hay que resolverla con Beltrán (MIC por modo vs escalar por-píxel).**

## Los 3 looks (todos terminan en el mismo selector)
`emFinal = lerp( lerp(em0, em1, saturate(Look)) , em2, saturate(Look−1) )` · lo mismo para la opacidad. En `Look=0/1/2` entero cae exacto en em0/em1/em2.

| Look | Emissive | Opacity |
|---|---|---|
| **0 · Volumen falso** | `ColorA` | `pow(v, VolumePower) · Density`, con `v = abs(N·V)` (centro=1, borde=0) → bola de luz densa al centro, se disuelve al borde |
| **1 · Iridiscente** | `lerp(ColorA, ColorB, frac(f·HueCycles + HueOffset))`, con `f = 1−abs(N·V)` (el tono se corre con el ángulo de vista, como una pompa) | `lerp(0.2, 1.0, f)` — cuerpo tenue, borde sólido (cáscara de burbuja) |
| **2 · Matcap** | `TextureSample(Matcap, uvm) · Tint · MatcapStrength`, con `uvm = normalize(Transform(N, World→View)).xy · 0.5 + 0.5` | `1.0` (sólido) |

Al final: `Emissive = emFinal · Brightness · pulse` donde `pulse = 1 + PulseAmount·sin(phase)` (vida por reloj). `Opacity = opFinal`.

🔴 **`N·V` a mano, no el nodo `Fresnel`** (trampa 4 del brief): el Fresnel satura el dot antes del `1−x`; construí `DotProduct(VertexNormalWS, CameraVectorWS)` → `Abs` para que funcione desde cualquier cara.

🔴 **El pulso (trampa 1):** `Sine` con `Period = 6.283185` (radianes) y `phase = Time · PulseSpeed · 2π`; `Time` con `bOverride_Period = true, Period = 600` (anti-drift de fp16 en Quest, lección de `M_TurrellPanel`). En el editor quieto `Time=0` → pulse=1 (no se ve latir en una captura estática; sí en PIE/visor).

## El material `M_Orb_SC` — 51 expresiones
- **Propiedades:** `shadingModel=MSM_Unlit`, `blendMode=BLEND_Translucent`, `twoSided=false` (one-sided para ahorrar fill; la opacidad ya hace el volumen), `floatPrecisionMode=MFPM_Full_MaterialExpressionOnly`.
- **Parámetros (13, todos empujados por el BP vía el MID):** escalares `Look · Brightness · VolumePower · Density · HueCycles · HueOffset · MatcapStrength · PulseAmount · PulseSpeed`; vectores `ColorA · ColorB · Tint`; textura `Matcap`.
- Salidas: `Emissive ← em_out (Multiply_9)`, `Opacity ← opFinal (LinearInterpolate_5)` — verificado con `get_property_input`.
- Construido por **`execute_tool_script`** (patrón `safe_script`, cero excepciones sueltas): script 1 crea las 51 expresiones + fija propiedades + descubre nombres de pines; script 2 hace las 60 conexiones + 2 salidas. Cero errores en ambos.

## El BP `BP_Orb_SC`
Componente **`Orb`** (StaticMeshComponent, esfera del motor por `PrimitiveTools.add_sphere`). Variable interna **`MID`** (MaterialInstanceDynamic, no editable). El actor va en escala 1; el tamaño sale de `SizeCM`.

### Registro de variables (por categoría, con rol)
| Categoría | Variable | Tipo | Default | Rol |
|---|---|---|---|---|
| **A - Forma** | `Look` | float | 0 | selector de look 0/1/2 (float para empujarse directo al escalar del material sin cast) |
| | `Mesh` | StaticMesh | `/Engine/BasicShapes/Sphere` | malla intercambiable (esfera/cubo/lo que sea) |
| | `SizeCM` | float | 30 | tamaño en cm → el CS pone escala `SizeCM/100` en el componente |
| **B - Color** | `ColorA` | LinearColor | ámbar (1, 0.6, 0.25) | color del volumen; extremo A de la iridiscencia |
| | `ColorB` | LinearColor | azul frío (0.3, 0.55, 1) | extremo B de la iridiscencia |
| | `Tint` | LinearColor | blanco | tinte del matcap |
| | `Brightness` | float | 1 | brillo global del emisivo (0–4) |
| **C - Volumen** | `VolumePower` | float | 2 | curva del falso volumen (0.5–6): más alto = núcleo más chico y denso |
| | `Density` | float | 0.7 | opacidad máxima del volumen (0–1) |
| **D - Iridiscencia** | `HueCycles` | float | 2 | cuántos ciclos de tono a lo ancho del ángulo (0.5–4) |
| | `HueOffset` | float | 0 | corre el tono (0–1) |
| **E - Matcap** | `Matcap` | Texture2D | `T_Matcap_01` | la textura de sombreado esférico |
| | `MatcapStrength` | float | 1 | fuerza del matcap sobre el emisivo (0–2) |
| **F - Vida** | `PulseAmount` | float | 0.12 | amplitud del latido de brillo (0–1) |
| | `PulseSpeed` | float | 1 | frecuencia del latido en Hz (0–3) — por reloj |
| *(interna)* | `MID` | MaterialInstanceDynamic | — | el material dinámico creado en el CS |

### Estructura del Construction Script (orden del pipeline)
1. `SetStaticMesh(Orb, Mesh)` — swap de malla (sin `IsValid`: el default siempre es válido; si el autor lo pone en None, la esfera se vacía y es obvio).
2. `SetRelativeScale3D(Orb, (SizeCM·0.01)³)` — cm → escala.
3. `mid = CreateDynamicMaterialInstance(Orb, 0, M_Orb_SC)` → `SetMID(mid)`.
4. **9 escalares** vía `SetScalarParameterValueOnMaterials(Orb, …)` y **3 colores** vía `SetColorParameterValueOnMaterials(Orb, …)` — variantes **sobre el componente** (no ambiguas; ver trampa abajo).
5. La **textura** vía `SetTextureParameterValue(mid, "Matcap", Matcap)` — esta va sobre el MID (no hay variante `onMaterials` para texturas, pero `SetTextureParameterValue` es inequívoco: las colecciones no tienen texturas).

🔴 **Trampa del DSL pagada acá (ya estaba en `dsl.md` §3):** `Rendering|Material|SetScalarParameterValue`/`SetVectorParameterValue` están DUPLICADOS (MID vs MaterialParameterCollection) y el DSL agarra el de Collection → falla. **Solución limpia:** `Set{Scalar,Color}ParameterValueonMaterials` sobre el componente (crean/reusan el MID internamente). Para escalares y colores es lo mejor; para la textura, como no existe esa variante, se usa el MID (que igual creamos para tenerlo).
🔴 **Otra trampa nueva (documentada en `dsl.md`): los getters de variables CON categoría llevan la categoría comprimida en el type_id** — `Variables|A-Forma|GetLook`, no `Variables|Default|GetLook` (los espacios del "A - Forma" se caen a "A-Forma"). `Variables|Default|` solo para las sin categoría (`Orb`, `MID`, `DefaultSceneRoot`). Confirmar siempre con `find_node_types(graph, "Variables|", [])`.

## Las texturas matcap
3 PNG 256×256 RGB generados por [`docs/efectos-nico/gen_matcaps.py`](../../../../docs/efectos-nico/gen_matcaps.py) (PNG puro con `zlib`+`struct`, sin PIL/numpy): color base + highlight gaussiano desplazado arriba + luz de borde (rim), muestreado por `r=|uv centrado|`. `T_Matcap_01` perla · `T_Matcap_02` vidrio frío (azul) · `T_Matcap_03` seda cálida. ⚠ Están **importadas con sRGB** (son color, no data).

## Cómo se usa / se autora
- Girás `Look` 0/1/2 en el panel de detalles y el look cambia en el viewport (el CS re-empuja). ⚠ **Si cambiás un valor y no reacciona, recargá el nivel** — un MID creado antes de que el material ganara un parámetro no lo honra (trampa 2 del brief), y también hay que recargar cuando se setean variables de instancia por MCP (el CS no se re-ejecuta solo).
- `Mesh` = cubo/cilindro para looks no esféricos (el matcap y el volumen funcionan en cualquier malla).

## Session log
- **2026-09-04 (Nico):** creado de cero. Nivel `L_EffectTest_Nico` (duplicado de `L_Test_Stage`, despejado de sky/luces/piso → vacío negro para look-dev). Material por 2 scripts seguros (51 nodos, 60 conexiones, 0 errores). BP con 16 variables + componente. CS por DSL (2 intentos fallidos por getters con categoría y por `MakeVector`→`Math|Vector|MakeVector`; el 3º limpio, verificado por `read_graph_dsl`, sin huérfanos). 3 instancias colocadas (Look 0/1/2), nivel recargado para re-correr el CS. **Verificado en editor:** los 3 looks se ven distintos (volumen ámbar, iridiscente pálido, matcap vidrio azul con rim), material lee todos los parámetros, escala 30 cm, MID aplicado. Capturas en `docs/efectos-nico/`.

## TODO
- [ ] Juicio de Beltrán (editor + visor). El **iridiscente es el que menos pega** — quizá subir `HueCycles` default o saturar `ColorB`; se decide mirándolo.
- [ ] Rangos UIMin/UIMax de sliders a mano en el editor (el MCP no expone esa metadata). Sugeridos en la tabla de variables.
- [ ] Los matcaps son degradados radiales simples; si se quiere más realismo (perla/seda), regenerar `gen_matcaps.py` con más luminancia (ojo al piso de 13/255 de Quest — autorar brillante).
- [ ] Visor: es translúcido a pantalla parcial → fill barato para un orbe, pero **medir si se apilan muchos** (respiración + sonido + burbujas). El pulso y el hue-shift solo se juzgan de verdad en movimiento/visor.
- [ ] Decidir con Beltrán el patrón del selector para `BP_LightPanel_SC` (§5.1 pide static switch, que choca con el MID dinámico — ver arriba).

## Open questions
- ¿El `Transform(World→View)` del matcap necesita flip de Y en Quest? En el editor se ve bien; confirmar en visor (los ejes de vista pueden diferir).
- ¿One-sided alcanza para el volumen o Beltrán va a querer verlo "lleno" desde adentro? (two-sided duplica fill).
