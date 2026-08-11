# BP_Vignette — viñeta de comodidad (Core/UI/)

## Purpose
Oscurece la periferia de la visión mientras hay movimiento. Reduce el flujo óptico periférico, que es **el motor real del mareo** en VR (`docs/OBRA-SOUL-CHARGER.md` §9.2). La maneja `BP_Walker`; se apaga al detenerse.

Se coloca **una sola instancia en el nivel persistente**, igual que `BP_FadeSphere`.

## Status
🟡 Construido y compilando. Falta test en visor y **falta medirlo en device**.

## De dónde salió
Copia deliberada del patrón de **`BP_FadeSphere`**, que ya anda en visor: un actor que en `BeginPlay` se busca la cámara del pawn y se attachea. La receta exacta, que es la que funciona:
```
GetPlayerPawn(0) -> GetComponentByClass("/Script/Engine.CameraComponent")
AttachActorToComponent(self, cam, "None", "SnapToTarget", "SnapToTarget", "KeepWorld", false)
```
⚠ Vive en el **persistente**. Un actor de sublevel **nunca** debe attachearse al pawn: se desattachea solo al guardar (`references/streaming-arch.md` §7).

## Componentes
- **`Dome`** — `/Engine/BasicShapes/Sphere` a radio 25 cm, material `M_Vignette`. Sin sombras, `translucencySortPriority = 100` para que dibuje por encima de la escena.
- 🔴 **`SetCollisionEnabled(NoCollision)` en `BeginPlay`.** Una esfera alrededor de la cabeza **bloquearía todos los line traces** de los punteros de mano. Se apaga en el grafo, no por propiedad, para que sea verificable.

## Estructura de grafos
- **`BeginPlay`** — apaga la colisión, busca la cámara, se attachea, `SetAmount(0)`. Loguea si el pawn no tiene `CameraComponent`.
- **`SetAmount(Amount)`** — `SetScalarParameterValueOnMaterials(Dome, "Amount", Amount)`. Sin variable MID: la variante `...OnMaterials` crea y reusa el MID sola.

## M_Vignette
Unlit · **Translucent** · TwoSided · `bDisableDepthTest` · sin fog.

🔴 **La máscara es GEOMÉTRICA, no screen-space** — y esto es lo importante:
```
LocalPosition.x / 50  ->  SmoothStep(OuterCos, InnerCos)  ->  OneMinus  ->  * Amount  ->  Opacity
Emissive = negro
```
Como la esfera está attacheada con `SnapToTarget`, su **+X local es el frente de la cámara**, así que `LocalPosition.x / radio` es directamente el coseno del ángulo respecto de la mirada. Eso da una viñeta **correcta en estéreo**, que es justo lo que una viñeta de screen-space no garantiza (`references/widgets-vr.md`: en HMD estéreo el screen-space no existe como concepto). El divisor **50 es el radio del asset sin escalar** — `LocalPosition` es previo a la escala, así que no cambia si se reescala el componente.

| Parámetro | Default | Qué ajusta |
|---|---|---|
| `InnerCos` | **0.97** | Dónde **empieza** a oscurecer. Es un **coseno**: 0.97 → empieza a 14° de la mirada. Más alto = ventana central más chica. |
| `OuterCos` | **0.72** | Dónde llega a negro pleno. 0.72 → 44°, así queda una banda negra sólida en los ~11° exteriores del campo. |
| `Amount` | 0.0 | Opacidad global. Lo maneja `BP_Walker` (`VignetteMax`, hoy **1.0**). **Arranca en 0.** |

**Estado actual (validado en visor 2026-08-11):** ventana limpia dentro de 14°, degradado de 14° a 44°, negro pleno de 44° al borde. Las **tres** palancas suben la intensidad y hacen cosas distintas:
- `VignetteMax` (en `BP_Walker`) = **cuán negro** llega a ponerse.
- `InnerCos` = **cuánto se cierra la ventana** limpia.
- `OuterCos` = **cuán rápido** el degradado llega al negro (más alto = banda sólida más ancha).

### 🔴🔴 Los dos parámetros son COSENOS, y calibrarlos "a ojo" da una viñeta invisible
**Pasó el 2026-08-11: la primera versión no se sentía en visor y todo el plumbing estaba bien.** Los valores originales eran `InnerCos = 0.80` / `OuterCos = 0.35`, que suenan razonables y son **geométricamente inútiles en un HMD**:

| | Ángulo | Qué pasaba |
|---|---|---|
| `InnerCos` 0.80 | θ = 37° | opacidad **exactamente 0** en los 74° centrales de la visión |
| `OuterCos` 0.35 | θ = 70° | el negro pleno cae **detrás del borde de la pantalla** |

El Quest 3 muestra ~**±55°**. En la esquina extrema del display la opacidad efectiva era `(1 − smoothstep(0.35, 0.80, cos 55°)) × 0.55 ≈ 0.28`: un velo del 28% en el rincón y nada en el resto. **Imperceptible.**

🔴 **La regla:** los dos parámetros hay que elegirlos desde el **FOV real del visor**, no desde números que "se vean bien" en un material preview de escritorio. Referencia rápida: `cos 20° = 0.94` · `cos 30° = 0.87` · `cos 40° = 0.77` · `cos 50° = 0.64` · `cos 55° = 0.57`. **`InnerCos` tiene que estar bien por encima de `cos(FOV/2)`** o el degradado entero queda fuera de la pantalla.

⚠ **Cómo se diagnosticó, porque el método importa más que el número:** se verificaron una por una las tres declaraciones sin confirmar (`twoSided`/`blendMode` del material, el material asignado al componente, el `MP_Opacity` conectado) y las tres estaban **bien**. Con el plumbing descartado por lectura y no por fe, el único candidato que quedaba era la geometría del mask — y ahí la cuenta cerró sola. Si me hubiera puesto a "probar cosas" en el material, habría tardado horas.

## TODO
- [ ] 🔴 **Medir en device con OVR Metrics.** Es una superficie translúcida que cubre buena parte de la pantalla, y Meta mide que el translúcido cuesta **~80 % más de GPU por frame que el masked** (`references/materials-vr.md`). El proyecto es **fill-rate bound**, y con la calibración intensa de ahora cubre **más** pantalla que antes.
  **Dos optimizaciones identificadas, en orden de rendimiento:**
  1. 💡 **Partir la viñeta en dos mallas.** De 44° hacia afuera la opacidad es **1.0 constante** → esa banda no necesita translucencia en absoluto: puede ser un **anillo opaco negro**, que no paga blending. Sólo el degradado de 14° a 44° necesita translúcido. Sale directamente de haber subido la intensidad: cuanto más intensa la viñeta, más área se puede pasar a opaco.
  2. Y el centro transparente (dentro de 14°) hoy **se sombrea para nada** — con geometría de anillo/túnel se saltea entero.
  No se hizo todavía porque es un placeholder y no hay que preoptimizar sin medición, pero está flageado y el camino está claro.
- [ ] Test en visor: confirmar que el borde no "bleedea" con MSAA (Meta lo advierte para bordes translúcidos).

## Relacionados
- [[BP_Walker]] (el único consumidor) · `BP_FadeSphere` (el patrón del que salió)
