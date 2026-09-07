# BP_RimField_SC — el campo de siluetas que nace alrededor (Core/Light/)

> Creado 2026-09-04. Nace de una critica de Beltran a los tres efectos de Nico: *"los encuentro bastante fomes… la idea de estos materiales es armar entornos"*. `BP_RimShape_SC` es **una** forma; esto es **un campo** de N formas envolviendo al usuario, que es lo que lo convierte de prop en entorno.
> **Estado: 🟡 compila estricto, 48 instancias sembradas y verificadas en editor + PIE (visible/oculto por tags). Falta el juicio de Beltran y el visor.**

## Que es
Un `InstancedStaticMeshComponent` (**un solo draw call**) con N formas repartidas en un anillo alrededor del actor, todas con `M_RimOnly_SC` — el material de Nico, **sin tocarlo**. Como ese material ya trae el revelado por cercania de camara (`SphereMask` contra `CameraPositionWS`), **cada instancia aparece sola segun cuan cerca esta la cabeza**: se camina y las formas nacen adelante y se apagan atras. Eso sale gratis, es per-pixel y no cuesta ni un nodo de Blueprint.

## Registro de variables
| Variable | Default | Rol |
|---|---|---|
| `Count` | 48 | cuantas formas |
| `Seed` | 7 | semilla del hash — cambiarla re-baraja todo el campo |
| `AreaRadius` | 1400 | radio exterior del anillo (cm) |
| `InnerRadius` | 350 | **hueco central**: nada se siembra mas cerca que esto, asi el usuario no queda con una forma en la cara |
| `AreaHeight` | 500 | dispersion vertical (±250) |
| `SizeMin` / `SizeMax` | 80 / 320 | rango de tamaño en cm |
| `Mesh` | Sphere | malla intercambiable (el rim funciona en cualquiera) |
| `RimColor` · `RimPower` · `RimWidth` · `Brightness` | cian / 3 / 1 / 1.5 | el borde |
| `RevealAmount` · `RevealRadius` · `RevealHard` | 1 / 900 / 0.35 | 🔴 el revelado por cercania. **`RevealAmount` en 1 = solo se ve lo cercano** (es lo que hace el entorno) |
| `ContactFade` | 90 | DepthFade contra el piso |
| *(interna)* `MID` | — | material dinamico del ISM |

## Estructura del Construction Script
`SetStaticMesh` → `ClearInstances` → `CreateDynamicMaterialInstance` sobre el ISM → 7 escalares + 1 color por `Set{Scalar,Color}ParameterValueOnMaterials` → **`for` de `Count`**: cuatro llamadas a `FieldHash` (angulo, radio, altura, escala) y un `AddInstance` con el transform armado.

**`FieldHash(I, Salt) → float`** es el generador determinístico: `abs(frac(sin(I·Salt + Seed) · 43758.5453))`. Una sola funcion, cuatro usos con distinta sal — asi el campo es **reproducible** (misma seed = mismo campo) y cambiar una perilla no lo re-baraja.

🔴🔴 **La trampa que costo una pasada: `Math|Float|Fraction` de Unreal CONSERVA EL SIGNO** (`frac(-2.3) = -0.3`). Como `sin()` es negativo la mitad del tiempo, el hash devolvia negativos y **las instancias salian con escala negativa** (malla invertida) y radios menores que `InnerRadius`. Se detecto **leyendo `perInstanceSMData` y mirando los numeros**, no mirando el viewport. Fix: envolver en `Math|Float|Absolute(Float)`. **Regla general: cualquier hash `frac(sin(x)*k)` portado de shaders necesita `abs` en Blueprint.**

## Como se usa
Se coloca donde deba estar el centro del campo y se ajusta `AreaRadius`/`Count`. Para la obra:
- **Surrounding**: el cascaron que se insinua al acercarse.
- **La sala final que se abre**: animar `DissolveThreshold` del material (hoy no expuesto en este BP; se agrega si hace falta).
⚠ El revelado **solo se juzga moviendose**: en una captura estatica se ve un anillo de formas cercanas y nada mas.

## Session log
- **2026-09-04**: creado. ISM + 17 variables + `FieldHash`. CS por DSL a la primera (el DSL inserto solo las conversiones int→float del indice). Compila con `warnings_as_errors`. Colocado en la estacion 8 de la galeria con `GALSTATION` + `GAL_8`, envuelto en un `BP_Ganzfeld_SC` verde-azul. Bug del `Fraction` con signo encontrado y corregido por cirugia. Verificado en PIE: el pawn cae en su anchor, campo y cascaron visibles, la estacion vecina oculta.

## TODO
- [ ] Juicio de Beltran + visor (el paralaje y el revelado son de visor).
- [ ] Exponer `DissolveThreshold`/`DissolveEdge` si se quiere el campo que se quema.
- [ ] Medir fill en APK: son N siluetas translucidas; el ISM ahorra draw calls, no fill.
