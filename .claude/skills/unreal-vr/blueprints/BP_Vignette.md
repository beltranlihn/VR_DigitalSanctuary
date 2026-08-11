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
| `InnerCos` | 0.80 | Dónde **empieza** a oscurecer. Más alto = agujero central más chico. |
| `OuterCos` | 0.35 | Dónde llega a negro pleno. La distancia entre los dos define lo suave del borde. |
| `Amount` | 0.0 | Opacidad global. Lo maneja `BP_Walker`. **Arranca en 0.** |

## TODO
- [ ] 🔴 **Medir en device con OVR Metrics.** Es una superficie translúcida que cubre buena parte de la pantalla, y Meta mide que el translúcido cuesta **~80 % más de GPU por frame que el masked** (`references/materials-vr.md`). El proyecto es **fill-rate bound**.
  **Optimización identificada si hace falta:** cambiar la esfera por un mesh de **anillo/túnel**, que no tenga geometría en el centro transparente. Hoy el centro se sombrea para nada. No se hizo todavía porque es un placeholder y no hay que preoptimizar sin medición — pero está flageado.
- [ ] Test en visor: confirmar que el borde no "bleedea" con MSAA (Meta lo advierte para bordes translúcidos).

## Relacionados
- [[BP_Walker]] (el único consumidor) · `BP_FadeSphere` (el patrón del que salió)
