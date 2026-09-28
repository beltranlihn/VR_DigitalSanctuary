# SM_ChargeRing_SC — el anillo contenedor de la proto ameba

## Propósito
Reemplaza los anillos animados que hoy rodean a la ameba (se veían desordenados) por un **objeto físico**: un anillo de metal mate oscuro con **5 cavidades de luz**, una por etapa, que se cargan y marcan el avance; en el **vacío central** flota la proto ameba. Pedido de Beltrán (2026-09-27), con referencia visual (render de anillo con 5 paneles pastel + dos vistas SketchUp).
- 🔴 **Simétrico: se ve IGUAL por ambas caras** (pedido explícito). Todo el perfil está espejado en X.
- Bisel en **todos** los bordes, "muy 3D".

## Estado
✅ **Modelado, exportado e importado en Unreal con sus materiales** (2026-09-27). Verificado por render en Blender (5 vistas) y por captura del asset en Unreal (con un control de la cuenta de las paredes, ver abajo). ⬜ **Falta:** veredicto de Beltrán sobre la forma, colocarlo con la ameba (Blueprint que empuje la carga), y verlo en visor.

## Assets
| Asset | Dónde | Qué |
|---|---|---|
| `SM_ChargeRing_SC` | `/Game/SoulCharger/Mechanics/ChargeRing/` | La malla: 19.023 tris, 10.330 vértices de render, 2 slots, **sin colisión** (a propósito: una caja taparía el trazado del puntero hacia la ameba), sin Nanite |
| `M_ChargeRing_Frame_SC` + `MI_ChargeRing_Frame_SC` | ídem | El metal (slot `M_ChargeRing_Frame`) |
| `M_ChargeRing_Light_SC` + `MI_ChargeRing_Light_SC` | ídem | Los pisos de luz (slot `M_ChargeRing_Light`) |
| Script de construcción | `blender-3d/scripts/gen_charge_ring.py` | Paramétrico, headless. Escribe `.fbx` y `.blend` en `VR_Test/Saved/ClaudeScripts/` |
| Render de presentación | `blender-3d/scripts/render_charge_ring.py` | Cycles/OptiX, materiales de preview + ameba provisoria de vidrio. Con `-- <salida>.blend` arma la **escena para abrir en el GUI** (EEVEE, propiedad `Carga` 0-5 en el anillo conectada al material): `VR_Test/Saved/ClaudeScripts/SM_ChargeRing_SC_presentacion.blend` |
| HLSL de los materiales | `unreal-vr/scripts/hlsl/ChargeRing{Frame,Light}PS.hlsl` | Fuente de los nodos Custom |

## Forma y parámetros (las perillas, arriba del script; todo en fracciones de R)
| Perilla | Valor | Nota |
|---|---|---|
| `R` | 0,23 m | Radio del núcleo → **46 cm de diámetro**. Se escala en Unreal |
| Planta | vacío 0,445 (núcleo) / 0,49 (caras) · cavidades 0,644–0,837 · placas 0,955 · núcleo 1,0 | **Medida en px sobre la vista frontal de la referencia** |
| `SEP_WIDTH` | 0,12 | Barras separadoras de **lados paralelos**, una arriba al centro |
| `THICK` / `CORE_FRAC` | 0,22 / 0,34 | Espesor total (5,06 cm); el núcleo central es el 34 % |
| `POCKET` | 0,04 | Profundidad de cada cavidad (9 mm) |
| Redondeos del perfil | cara 0,028 · rincón 0,012 · núcleo 0,016 | Los cantos grandes de la silueta van **en el perfil** (arcos tangentes), no en el bisel |
| `BEVEL` | 0,012 (2,8 mm), 3 segmentos | Solo el borde de las cavidades |
| `SEGMENTS` | 96 | A 1 m el facetado de la silueta es 0,1 mm |
| `DIRECTION` | +1 | Sentido de avance de las etapas: **antihorario** (el de la referencia). −1 = horario |

**Lenguaje de forma:** un **núcleo** central más ancho que sobresale por fuera y por dentro, entre dos **placas** de cara → el canto escalonado de la referencia, repetido en las dos caras. En cada cara, 5 cavidades (sectores de corona) cuyo piso es la superficie de luz.

## 🔴 El contrato de la UV (lo que lee el material de luz)
Pisos de las cavidades, UV0: **`U = etapa + t`** (0..5), **`V = 1 − radial`** (Unreal invierte la V al importar, gotcha 302 de unreal-vr).
- Etapas en el **orden de la obra, antihorario desde arriba a la izquierda**: 0 Entering (azul, arriba-izq) · 1 Recognizing (rojo, izq) · 2 Loving (violeta, abajo) · 3 Attracting (ámbar, der) · 4 Surrounding (verde, arriba-der). 💡 **La referencia de Beltrán ya tenía exactamente ese orden de colores.**
- `t` va de 0 a 1 en el sentido de avance, **normalizado por radio**: t=0 y t=1 caen justo sobre el borde de las barras (así la carga arranca y termina al ras de la barra, no a mitad de camino).
- Las dos caras comparten `U` para el mismo punto físico (es un solo contenedor): vista de atrás, el sentido se invierte.

## Materiales (unlit, como toda la obra)
**Los dos comparten los nombres de parámetro de carga y color** → una sola llamada `SetScalarParameterValueOnMaterials(Charge_Loving, x)` sobre el componente actualiza metal y luz a la vez.

| Grupo | Parámetros | En |
|---|---|---|
| `1 - Carga` | `Charge_Entering` · `Charge_Recognizing` · `Charge_Loving` · `Charge_Attracting` · `Charge_Surrounding` (0..1; **default 1** para ver el anillo lleno en el editor — el Blueprint las pone en 0 al arrancar) | ambos |
| `2 - Colores` | `Color_<Etapa>` (los colores oficiales de `BP_ProtoSoul.RingColors`) · `Pastel` 0,3 (aclara hacia blanco, el pastel de la referencia) | ambos |
| `3 - Luz` | `EmptyLevel` 0,1 (cavidad vacía = vidrio tintado oscuro) · `FullLevel` 0,9 · `EdgeSoftness` 0,015 (ancho del frente de carga) | ambos |
| `3 - Luz` | `FrontGlow` 0,6 (brillo del frente mientras carga) | luz |
| `3 - Luz` | `WallGlow` 0,55 (cuánto tiñe la luz las paredes de su cavidad) | metal |
| `4 - Metal` | `MetalColor` · `LightDir` (dirección a la luz, **mundo**) · `Ambient` · `Diffuse` · `Spec` · `Gloss` · `SkyColor` · `GroundColor` · `Env` | metal |

- **Metal:** luz fingida en el shader (difuso + especular + reflejo cielo/suelo por la dirección reflejada + fresnel, que es lo que hace brillar los biseles) + **rebote**: calcula por `LocalPosition` en qué cavidad y a qué altura de la carga está cada pixel de pared, y la tiñe con el color de esa etapa si está cargada. 🔴 Esa cuenta tiene **constantes de la malla** (R 23 cm, cavidades, cara, piso, barras): si cambia la malla, se cambian en `ChargeRingFramePS.hlsl`.
- **Dither R2 de 1 LSB** en los dos (receta de `materials-vr.md` contra bandas de 8 bits).
- `floatPrecisionMode` por defecto (half): U llega a 5 → paso de 0,4 % en t, invisible. Sin `Time`.

## Verificación hecha
1. **Malla**: FBX reimportado en Blender: 0 aristas no-manifold, 0 degenerados, 0 duplicados. En Unreal 19.023 de 19.024 tris (descarta la única astilla < 0,01 mm²).
2. **Normales**: control en el script — desvío de las normales de esquina en las caras planas: máx. 1,05°, p95 0,12°; 0 caras invertidas.
3. **Cuenta del metal vs UV**: puerto de la cuenta HLSL contra `slot_uv` de Blender, 20.000 puntos: diferencia máx. 7e-6, 0 etapas cruzadas.
4. **El espejado en Y del FBX** (lo único que no se podía probar sin Unreal): control con `WallGlow` 6 y `Charge_Entering` 0 → **solo** la cavidad azul (arriba-izq) quedó con las paredes apagadas. Si el espejado estuviera mal, se apagaba la verde. Instancia restaurada después (`clear_parameters`).

## Trampas que costaron esta vez (detalle en `references/gotchas.md` 18-22)
Booleano + bisel: `clamp_overlap` achicó el bisel a micrones en casi todo el borde de las cavidades (las "astillas" que Unreal descartaba); soldar después del bisel aplastó esos tramos y torció las normales; triangular antes de ponderar normales dio dientes de sierra; sin clamp, el bisel plegó polígonos contra las tiras radiales de la revolución. **La receta que quedó:** booleano → aplicar → `remove_doubles` (0,46 mm) + disolver las aristas coplanares de la cara → bisel **sin** clamp → normales ponderadas → triangular n-gons (`CLIP`, conservando normales).

## Pendientes
- [ ] Veredicto de Beltrán sobre proporciones/espesor/tamaño (render en el chat del 2026-09-27).
- [ ] Blueprint (o función en `BP_ProtoSoul_SC`) que coloque el anillo alrededor de la ameba y empuje `Charge_<Etapa>` con la carga real (hoy la dueña de "los anillos" es la ameba: `SeedRings`/`DrawRing`).
- [ ] Ver en visor: legibilidad del metal oscuro contra el vacío, y si `LightDir` en mundo funciona cuando el anillo gira con el usuario.
- [ ] Costo: 19k tris + 2 secciones. Si hace falta, bajar `SEGMENTS`/`ARC_SAMPLES` (la silueta aguanta 64).

## Log
- **2026-09-27** — construido de cero en Blender headless (el GUI no estaba abierto; hay otro agente en el editor de Unreal, así que todo por llamadas sueltas y guardado con rutas explícitas). 10 iteraciones del bucle render→crítica: espesor (0,18→0,22), redondeos al perfil, colores oficiales de etapa, limpieza de la malla (ver trampas). Materiales creados en Unreal por MCP, ~95 llamadas sueltas y 2 scripts de solo captura.
