# BP_RimShape_SC + M_RimOnly_SC — formas que solo existen como su resplandor (Core/Light/)

> Creado 2026-09-04 por Nico, brief [`docs/BRIEF-NICO-EFECTOS.md`](../../../../docs/BRIEF-NICO-EFECTOS.md) §5.2. **Segundo efecto de Nico.** Geometría invisible salvo por su silueta: relleno cero, borde encendido — presencia sin masa, lo contrario de la arista dura que la obra descarta. Dos momentos del guión lo piden: el **cascarón de Surrounding** ("el borde brilla suave al acercarse") y la **sala final que se abre** (esconde su muro para devolver el exterior).
> **Estado: 🟡 material + BP compilados sin errores, 3 instancias en `L_EffectTest_Nico` (cascarón normal, disolviéndose, y cubo) juzgadas en el viewport — se ven distintas y el rim/disolución/borde encendido funcionan. Falta juicio de Beltrán y visor.**

## El material `M_RimOnly_SC` — unlit · translúcido · **two-sided** · Full Precision
Two-sided **a propósito**: el cascarón se habita desde adentro (Surrounding, sala final) → hay que verlo desde dentro. El `abs` del dot hace que el rim funcione en ambas caras.

La cadena, término por término:
| Término | Cómo | Perillas |
|---|---|---|
| **rim** | `pow(1 − abs(dot(N,V)), RimPower) · RimWidth` — brilla en la silueta, transparente de frente. 🔴 el `abs` va ADENTRO del dot (trampa 4 del brief: el Fresnel satura el dot antes del 1−x) | `RimPower` (3) · `RimWidth` (1) |
| **reveal** | `lerp(1, SphereMask(WorldPosition, CameraPositionWS, RevealRadius, RevealHard), RevealAmount)` — con `RevealAmount>0` la forma solo aparece cerca de la cabeza (aparece desde la nada al acercarse). **Default 0 = siempre visible** (para autorar en el viewport) | `RevealAmount` (0) · `RevealRadius` (300 cm) · `RevealHard` (0.5) |
| **body / dissolve** | `body = saturate((noise − DissolveThreshold)·10000)` (paso duro); el ruido es `T_ShaftNoise` muestreado en **XY de mundo × DissolveScale**. Subir `DissolveThreshold` come la forma | `DissolveThreshold` (0) · `DissolveScale` (0.01) |
| **edge encendido** | `edgeGlow = (1 − saturate((noise−thr)/max(DissolveEdge,ε))) · body` — la banda que se está quemando, con `DissolveEdgeColor` | `DissolveEdge` (0.08) · `DissolveEdgeColor` (ámbar) |
| **contact** | `DepthFade(ContactFade)` — no corta duro contra el piso | `ContactFade` (90) |

- **Emissive** = `(RimColor · rim · reveal · body + DissolveEdgeColor · edgeGlow) · Brightness`
- **Opacity** = `saturate(rim · reveal · body + edgeGlow) · contact` — 🔴 el borde disuelto se suma también a la OPACIDAD (no solo al emisivo) para que el filo encendido se vea aunque el rim ahí sea bajo. Es una desviación deliberada de la fórmula literal del brief (`Opacity = rim·reveal·diss·contact`), fiel al intento "con el borde encendido".
- Construido por 2 `execute_tool_script` seguros: 47 expresiones, 50 conexiones, 0 errores. Salidas verificadas.

⚠ **El ruido en XY de mundo es proyección PLANAR** → en una esfera el frente y el fondo mapean a XY parecidos y el patrón sale algo simétrico/vertical. Se ve bien como disolución; si Beltrán quiere orgánico puro, pasar a triplanar o UV de objeto.

## El BP `BP_RimShape_SC`
Idéntico patrón al del [[BP_Orb_SC]]: componente `Orb` (esfera del motor, malla intercambiable), variable interna `MID`, Construction Script que crea el MID de `M_RimOnly_SC` y empuja todo. **Todos los parámetros son escalar/color** → van por `Set{Scalar,Color}ParameterValueOnMaterials` sobre el componente (sin ambigüedad de overload; ver trampa en [[BP_Orb_SC]]). No hay textura-parámetro (el ruido es fijo en el material).

### Registro de variables (por categoría, con rol)
| Categoría | Variable | Tipo | Default | Rol |
|---|---|---|---|---|
| **A - Forma** | `Mesh` | StaticMesh | Sphere | malla intercambiable (esfera/cubo/cilindro) — el rim funciona en cualquiera |
| | `SizeCM` | float | 100 | tamaño en cm → escala `SizeCM/100` |
| **B - Borde** | `RimColor` | LinearColor | cian-blanco | color del resplandor de silueta |
| | `RimPower` | float | 3 | dureza del rim (0.5–8): más alto = franja más fina en la silueta |
| | `RimWidth` | float | 1 | fuerza del rim (0–3) |
| | `Brightness` | float | 1.5 | brillo global (0–4) |
| **C - Revelado** | `RevealAmount` | float | 0 | 0 = siempre visible; 1 = solo cerca de la cámara (aparece al acercarse) |
| | `RevealRadius` | float | 300 | radio de revelado en cm (50–800) |
| | `RevealHard` | float | 0.5 | dureza del borde del revelado (0–1) |
| **D - Disolucion** | `DissolveThreshold` | float | 0 | 0 = entero; subir = se come la forma (0–1) |
| | `DissolveEdge` | float | 0.08 | ancho del filo encendido (0–0.3) |
| | `DissolveEdgeColor` | LinearColor | ámbar | color del borde que se quema |
| | `DissolveScale` | float | 0.01 | escala del ruido de disolución (perilla extra, no en el brief) |
| **E - Contacto** | `ContactFade` | float | 90 | distancia del DepthFade contra geometría (0–400) |
| *(interna)* | `MID` | MaterialInstanceDynamic | — | material dinámico del CS |

### Estructura del Construction Script
`SetStaticMesh(Orb, Mesh)` → escala `SizeCM·0.01` → `CreateDynamicMaterialInstance(Orb, 0, M_RimOnly_SC)` → `SetMID` → 10 escalares por `SetScalarParameterValueOnMaterials` + 2 colores por `SetColorParameterValueOnMaterials`. Sin ramas. Verificado por `read_graph_dsl`, limpio.

## Session log
- **2026-09-04 (Nico):** creado tras `BP_Orb_SC`. Material por 2 scripts (47 nodos, 50 conexiones, 0 errores). BP con 15 variables. CS por DSL a la primera (ya conocía los getters con categoría y `Math|Vector|MakeVector`). 3 instancias colocadas (cascarón, disuelto a 0.5, cubo), nivel recargado. **Verificado en editor:** el rim brilla en la silueta con relleno cero, la disolución come la forma con el filo ámbar encendido, y funciona en cubo. Capturas en `docs/efectos-nico/rim_los_tres.png` y `rim_disuelto.png`.

## TODO
- [ ] Juicio de Beltrán (editor + visor). El **revelado por cámara** (`RevealAmount>0`) solo se juzga moviéndose en PIE/visor.
- [ ] Ruido de disolución PLANAR → simetría vertical en esferas. Si molesta, triplanar/UV de objeto.
- [ ] Rangos UIMin/UIMax a mano en el editor (MCP no expone la metadata). Sugeridos en la tabla.
- [ ] Two-sided = ×2 fill: medir en visor si se usa grande (el cascarón de Surrounding es a pantalla completa).
- [ ] Para la "sala final que se abre": animar `DissolveThreshold` 0→1 por el director (o `RevealAmount`) — es un consumidor externo, no de este BP.

## Open questions
- ¿La disolución debería ir por UV de la malla (más controlable por-forma) en vez de mundo? Depende de si Beltrán quiere que varias formas disuelvan coherentes en el espacio (mundo) o cada una a su modo (UV).
