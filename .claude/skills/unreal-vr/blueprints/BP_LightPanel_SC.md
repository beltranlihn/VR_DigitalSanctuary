# BP_LightPanel_SC + M_LightPanel_SC — la superficie que hace cosas (Core/Light/)

> Creado 2026-09-04 por Nico, brief [`docs/BRIEF-NICO-EFECTOS.md`](../../../../docs/BRIEF-NICO-EFECTOS.md) §5.1. **Tercer efecto de Nico** (el más grande). Un panel plano con un selector de modo que agrupa cuatro efectos que comparten toda la cañería, en vez de cuatro Blueprints casi idénticos. Es el vocabulario de una obra de luz mínima: una franja que recorre un muro, un halo que respira, un rosetón que gira, una pared que se enciende cuando te acercás.
> **Estado: 🟡 material (107 expr) + BP compilados sin errores, 4 instancias (una por modo) en `L_EffectTest_Nico` juzgadas en el viewport — los 4 modos se ven claramente distintos. Falta juicio de Beltrán y visor.**

## 🔴 La decisión del selector: escalar por-píxel, NO static switch (diverge del brief §5.1)
El brief pide resolver los 4 modos con un **static switch** ("cada instancia compila solo su rama"). **No lo hice, y es a propósito** — con el patrón obligatorio del proyecto (componente + **MID dinámico** + Construction Script, §3) **es imposible**: un `UMaterialInstanceDynamic` **no puede cambiar static switches** (son compile-time, se heredan del padre). Con static switch, girar `Mode` en el panel de detalles NO actualizaría el viewport, y el brief §6.2 exige "se ve bien en el viewport sin darle Play" + §6.3 "todas las perillas hacen algo visible".

Entonces `Mode` es un **escalar** y los 4 modos se seleccionan **por píxel** (dos `lerp` encadenados sobre `saturate(Mode−k)`). Se editan vivo en el viewport. Costo: las 4 ramas se evalúan por píxel (lo que el brief quería evitar). **Es la misma decisión que tomé en [[BP_Orb_SC]] y quedó pendiente de charlar con Beltrán.**
👉 **Si Beltrán quiere la optimización de permutación** (que cada instancia pague solo su modo), la vía es: `M_LightPanel_SC` con un static switch `Mode`, **4 Material Instance Constants** (`MI_LightPanel_Sweep/Rings/Mandala/Proximity`) con el switch fijado, y el BP elige el MIC según `Mode` y crea el MID **desde ese MIC**. Sigue viéndose en el viewport (el CS re-elige el MIC). Es más assets y más trabajo; se decide con él. **Es una decisión de fill para la obra, no un cambio visual.**

## El material `M_LightPanel_SC` — unlit · translúcido · one-sided · Full Precision (107 expresiones)
Todos los modos terminan igual: `Emissive = PanelColor · mask · Brightness` · `Opacity = mask · EdgeMask`.

| Modo | mask | Perillas |
|---|---|---|
| **0 · BARRIDO** | `exp(−(frac(p − t·SweepSpeed) − 0.5)² / SweepWidth)`, con `p = dot(uv−0.5, dir(SweepAngle))` — una franja de claridad recorre el panel en la dirección `SweepAngle` | `SweepAngle` (0°) · `SweepSpeed` (0.25) · `SweepWidth` (0.04) |
| **1 · ANILLOS** | suma de `1 − smoothstep(0, RingSoft, |r − RingPos_i|)` para 3 anillos, con `r = dist(uv, centro)·2`; `RingCount` (1–3) apaga anillos con `saturate(RingCount−i)` | `RingCount` (3) · `RingPos1/2/3` (0.3/0.55/0.8) · `RingSoft` (0.02) |
| **2 · MANDALA** | `saturate(ringMask(r) + spoke)`, con `spoke = 1 − smoothstep(0, RingSoft, |frac(atan2(y,x)/2π·Segments + t·SpinSpeed) − 0.5|)` — anillos + radios girando | `Segments` (8) · `SpinSpeed` (0.05) |
| **3 · CERCANÍA** | `SphereMask(WorldPosition, CameraPositionWS, TouchRadius, TouchHardness)` — el panel se enciende donde está la cámara | `TouchRadius` (180 cm) · `TouchHardness` (0.5) |

- 💡 **`SphereMask` es un nodo del motor** (A, B, Radius, Hardness) — caída esférica en un solo nodo, reemplaza `Distance→Subtract→Divide→Saturate`. Descubierto en Content Examples.
- **Máscara de borde** (`G - Borde`, copiada de `M_FogSlab_SC`): `d = lerp(max(|u|,|v|), length(uv·2), EdgeRound)` (0 = rectángulo, 1 = círculo); `m = saturate((1−d)·EdgeSoft)`; `EdgeMask = lerp(1, m, EdgeAmount)`.
- 🔴 **`Sine`/`Cosine` con `Period = 6.283185`** (radianes; `SweepAngle` se pasa por `deg2rad`), `Time` con `Period = 600` (anti-drift fp16 en Quest). `atan2` = `Arctangent2` (Y, X). `exp` = `Exponential`.
- Construido por 2 `execute_tool_script` seguros: 107 expresiones, 135 conexiones, 0 errores. Salidas verificadas por `list_parameters` (18 params) — compiló.

## El BP `BP_LightPanel_SC`
Componente **`Panel`** (StaticMeshComponent; la malla la asigna el CS, default `/Engine/BasicShapes/Plane`). Variable interna `MID`. **Todos los params del material son escalar/color** → van por `Set{Scalar,Color}ParameterValueOnMaterials` (sin ambigüedad de overload).

### Registro de variables (por categoría, con rol)
| Categoría | Variable | Default | Rol |
|---|---|---|---|
| **A - Forma** | `Mode` (float) | 0 | selector 0/1/2/3 (por-píxel) |
| | `PanelSizeX` / `PanelSizeY` (float, cm) | 2000 | tamaño → escala `Size/100` del componente (Z=1); **NO son params del material** |
| | `Mesh` (StaticMesh) | Plane | malla del panel |
| **B - Color** | `PanelColor` (LinearColor) · `Brightness` (0–4) | ámbar · 1 | color y brillo del emisivo |
| **C - Barrido** | `SweepAngle` (0–360) · `SweepSpeed` (0–2) · `SweepWidth` (0.005–0.3) | 0 · 0.25 · 0.04 | dirección, velocidad y ancho de la franja |
| **D - Anillos** | `RingCount` (1–3) · `RingPos1/2/3` (0–1) · `RingSoft` (0.002–0.2) | 3 · 0.3/0.55/0.8 · 0.02 | cantidad, radios y suavidad de los anillos |
| **E - Mandala** | `Segments` (3–24) · `SpinSpeed` (−1–1) | 8 · 0.05 | radios y giro |
| **F - Cercania** | `TouchRadius` (cm, 20–600) · `TouchHardness` (0–1) | 180 · 0.5 | radio y dureza del encendido por proximidad |
| **G - Borde** | `EdgeRound` (0–1) · `EdgeSoft` (0.5–16) · `EdgeAmount` (0–1) | 0 · 2.5 · 1 | forma (rect/círculo), dureza y fuerza del borde |
| *(interna)* | `MID` | — | material dinámico del CS |

### Construction Script
`SetStaticMesh(Panel, Mesh)` → escala `(PanelSizeX·0.01, PanelSizeY·0.01, 1)` → `CreateDynamicMaterialInstance(Panel, 0, M_LightPanel_SC)` → `SetMID` → 17 escalares por `SetScalarParameterValueOnMaterials` + 1 color. Sin ramas. Verificado por `read_graph_dsl`, limpio.

## Session log
- **2026-09-04 (Nico):** tercero de los tres. Material por 2 scripts (107 nodos, 135 conexiones, 0 errores). BP con 21 variables + componente StaticMesh. CS por DSL a la primera. 4 instancias colocadas (una por modo, 3 m, grid 2×2, planas mirando arriba), nivel recargado, capturado en cenital. **Verificado en editor:** los 4 modos se ven distintos (barrido/anillos/mandala/cercanía), la máscara de borde suaviza los cantos, `SphereMask` enciende el panel de cercanía. Capturas en `docs/efectos-nico/panel_4modos.png`.

## TODO
- [ ] 🔴 **Charlar con Beltrán la decisión static-switch vs escalar por-píxel** (arriba). Si quiere la optimización → 4 MICs.
- [ ] Modo 3 (cercanía): el "encenderse al acercarte en PIE" solo se juzga moviéndose en visor. En la captura se forzó `TouchRadius` alto para que la cámara cenital lo prenda.
- [ ] Rangos UIMin/UIMax a mano en el editor (MCP no expone la metadata). Sugeridos en la tabla.
- [ ] Visor: 4 ramas por píxel + translúcido a pantalla parcial. Barato para un panel, medir si se llenan varios. El barrido/mandala se juzgan en movimiento.
- [ ] La malla default es el `Plane` del motor (normal +Z). Para un muro, rotar el actor. `PanelSizeX/Y` en cm, actor escala 1.

## Open questions
- ¿El mandala debería tener el patrón de anillos *también* en la coordenada angular (petals cerrados) en vez de anillos(r) + radios? La lectura actual (rejilla radial) es limpia; si Beltrán quiere pétalos, se cambia la composición de `mask2`.
- ¿One-sided alcanza, o algún panel se mira desde atrás? (two-sided duplica fill).
