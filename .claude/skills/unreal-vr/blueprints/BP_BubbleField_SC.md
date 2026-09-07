# BP_BubbleField_SC — el ESPACIO de esferas flotantes (Core/Light/)

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

## 🆕 2026-09-04 (tarde) — las burbujas, tras el juicio de Beltran
Vio el campo y dijo: ***"las bubbles estan lindas"*** — es lo unico de los tres efectos que le gusto. Pidio tres cosas, y las tres se resolvieron **en el material**, sin custom data ni logica de Blueprint:

**Un hash POR INSTANCIA**, sacado de `ObjectPositionWS` (en un ISM devuelve la posicion de cada instancia): `frac(sin(dot(pos, (12.9898, 78.233, 37.719))) · 43758.5453)`. Un solo valor 0-1 distinto por burbuja, que alimenta las dos cosas de abajo.
💡 A diferencia del hash de Blueprint, **aca NO hace falta `abs`**: el `frac` de HLSL ya devuelve positivo.

| Pedido | Como se hizo | Perillas |
|---|---|---|
| *"distintos colores dentro de paletas de azulados"* | `lerp(RimColor, RimColorB, hash · ColorVariation)` — cada burbuja cae en un punto distinto entre los dos azules | `RimColorB` (azul claro) · `ColorVariation` (1 = variacion total, **0 = todas iguales**, que es el default del material para no cambiarle nada a `BP_RimShape_SC`) |
| *"hazlas pulsar suavemente"* | **WPO**: `VertexNormalWS · PulseAmount · sin(Time·PulseSpeed + hash·2π)` — la esfera se infla y desinfla de verdad, y **la fase sale del hash**, asi que cada una respira a su tiempo | `PulseAmount` (4 cm) · `PulseSpeed` (0.22 Hz) |
| *"aleatorio de tamaño"* | rango ampliado | `SizeMin` 60 → `SizeMax` 420 |

⚠ **El material es de Nico y lo usa tambien `BP_RimShape_SC`.** Los tres parametros nuevos tienen **default 0** (o sea: sin variacion y sin pulso), asi que sus tres formas sueltas siguen viendose exactamente igual. Solo el campo los enciende.

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


## 🫧 2026-09-04 (noche) — pasa a ser EL BP de los espacios de esferas
Beltran, mirando el campo: ***"lo que me gusto es armar espacios de esferas aleatorias, asi que ese es el BP que queremos lograr, no solo el material"***. El BP ya existia (yo lo habia presentado desde el material, que confundio); lo que faltaba era que se **llamara** y se **autoreara** como lo que es. Tres cambios:

1. **Renombrado** `BP_RimField_SC` → **`BP_BubbleField_SC`** (`AssetTools.move`, la instancia de la galeria siguio enganchada sola).
2. **Las 20 perillas quedaron en categorias y todas instance-editable**, que es lo que hace autorable el BP desde el panel: *A - Campo* (Count · Seed · AreaRadius · InnerRadius · VerticalScale) · *B - Esferas* (Mesh · SizeMin · SizeMax) · *C - Color* (RimColor · RimColorB · ColorVariation · Brightness) · *D - Borde* · *E - Pulso* · *F - Revelado* · *G - Contacto*.
3. 🔴 **La distribucion pasa de ANILLO a ESFERA COMPLETA**, a pedido suyo: *"quiero ver esferas por arriba, lados, delante, atras, dejando un espacio al centro que es donde va el pawn"*. El CS ahora siembra en una **cascara esferica**: azimut `u·2π`, y **`cosPhi = 2v−1` uniforme** (que es lo que reparte parejo sobre la esfera; usar el angulo directo amontona en los polos), `sinPhi = sqrt(1−cosPhi²)`, radio entre `InnerRadius` y `AreaRadius`. `VerticalScale` achata el campo (1 = esfera, <1 = lenteja).
   `AreaHeight` quedo sin uso y se reemplazo por `VerticalScale`.
   ✅ **Medido por bounds**: 32 m en X, 32 m en Y y **27 m en Z** (antes Z era 4 m: un disco).

### 🔴 Y el bug del color que reporto ("estas orbes deben ser de distintos colores")
Las burbujas salian **todas del mismo color** y pulsando al unisono. Causa: **`ObjectPositionWS` en un InstancedStaticMesh devuelve la posicion del COMPONENTE, no la de cada instancia** — asi que el hash daba el mismo numero para las 48. Fix: **`PerInstanceRandom`**, el nodo del motor hecho exactamente para esto (un aleatorio por instancia de ISM/foliage). Se borro toda la cadena del hash de posicion.
💡 En un mesh NO instanciado `PerInstanceRandom` devuelve 0 → `BP_RimShape_SC` sigue viendose igual, sin variacion ni pulso. El default se mantiene sano solo.
⚠ **Regla general: para variar POR INSTANCIA en un ISM, `PerInstanceRandom`. `ObjectPositionWS` NO sirve.**
