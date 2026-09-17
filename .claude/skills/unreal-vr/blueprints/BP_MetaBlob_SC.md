# BP_MetaBlob_SC + M_MetaBlob_SC — los metaballs (Core/Light/)

> Creado 2026-09-07 (estacion 7 de la galeria, reemplaza los 3 orbes de Nico). Veredicto de Beltran: **"Super. Se ve bien"**.
> Tracker escrito el **2026-09-15** al medirlo en visor por primera vez.
> **Estado: 🟢 aprobado de aspecto · 🔴 es el efecto mas caro de la galeria.**

## Que es
Raymarch de un SDF de esferas con smooth-min, en un `MaterialExpressionCustom`. **Unlit, translucido, one-sided**,
sobre un proxy que es el **cubo de engine** (`/Engine/BasicShapes/Cube`) en el componente `Volume`
(`RelativeScale3D` 1,1,1 · `BoundsScale` 1 · ⚠ `CastShadow = true`, que en un raymarch translucido no sirve de nada).

El march arranca en la **camara** (`RayOrigin` = `CameraPositionWS` transformado a espacio local), no en la
superficie del proxy: **el proxy solo funciona como mascara de pixeles**, no acota el recorrido del rayo.

## 🔬 Medido en visor (Quest 3, 2026-09-15)
Estacion 7 = `BP_MetaBlob_SC` + `BP_Ganzfeld_SC_C_1`, **App = 30,3–38,9 ms** contra un presupuesto de 13,9 ms,
FPS 28–30, `GPU% = 0,97`. Restandole el cascaron (medido solo en la estacion 3: 24–27 ms),
**el metaball aporta ~6–12 ms**. Es el segundo efecto mas caro, no el primero.

## 🔴 Los valores REALES de la instancia (no los del CDO) y lo que implican
| | instancia `BP_MetaBlob_SC_C_0` | CDO |
|---|---|---|
| `Spread` | 19,46 | 26 |
| `BlobRadius` | 13,58 | 13 |
| `SizeVariation` | 0,45 | 0,45 |
| `CurlAmount` | 19,37 | 7 |
| `BlobCount` | 6,03 → el shader usa **6** | 7 |
| `Steps` | 86,68 → el shader usa **64** | 28 |

🔴 **`Steps` esta CLAMPEADO a 64 en el shader** (`clamp(ParB.z, 4.0, 64.0)`): todo lo que Beltran ponga por
encima de 64 **no hace nada**. La perilla miente en ese rango.

**Costo por pixel:** el march es `Steps x BlobCount` = **64 x 6 = 384** evaluaciones en el peor caso, mas
`4 x BlobCount = 24` de la normal por diferencias finitas. El march domina por completo.

## ❌ Dos optimizaciones propuestas que NO sobrevivieron a los numeros (2026-09-15)
### 1. Cambiar el proxy de cubo a esfera — **esta AL REVES**
Extension de la nube en unidades locales: `P[j] = C[j]*Spread*(1-Attract) + curl*CurlAmount`, con `|C[j]| <= 1`
y `|curl| <= sqrt(3)*CurlAmount = 33,5` (tipico ~23,7), mas `rmax = BlobRadius*(1+SizeVariation) = 19,69`.
→ **extension tipica ~53, peor caso ~73** unidades locales.
- El **cubo de engine** a escala 1 llega a **50** en las caras (86,6 en las diagonales).
- La **esfera de engine** a escala 1 llega a **50 en todas las direcciones** → recortaria MAS que el cubo.
- Una esfera que si contenga la nube necesita radio ~73, o sea escala 1,46 — pero **escalar el componente
  escala el espacio local y por lo tanto el SDF entero** (el blob se veria 1,46x mas grande), asi que habria
  que compensar dentro del shader.
- Y aun compensando: esa esfera proyecta `pi*73^2 ~ 16.700` contra los ~10.000 del cubo de frente.
  **La esfera que entra cubre ~1,7x MAS pantalla que el cubo.** La idea es contraproducente.

🚩 **Corolario que SI importa:** con extension tipica ~53 contra 50 de media-arista, **el cubo probablemente
ya esta recortando los blobs** cuando el curl los lleva lejos. Es un defecto de aspecto, no de rendimiento.
**Falta que Beltran lo mire.**

### 2. Normal analitica en vez de las 4 muestras — **marginal**
Se estimo "un tercio del costo" suponiendo `BlobCount = 16`. Con el valor real (**6**) la normal cuesta
`4 x 6 = 24` evaluaciones contra las hasta `384` del march: **~6%**. No justifica tocar el shader.

## ✅ La palanca que si queda, y es decision de aspecto
**`Steps`.** El march ya hace sphere tracing de verdad (`t += max(res, eps)`) y corta por impacto
(`res < eps`) y por distancia (`t > maxT`, con `maxT = Spread*4 + rmax*6 = 196`). Los rayos que queman los 64
pasos son los **rasantes de la silueta**. Bajarlo erosiona un poco el borde. **No tocar sin que Beltran lo juzgue.**

Otras, menores: **`CastShadow = false`** en el componente `Volume` (gratis), y los arrays locales `P[16]`/`R[16]`
con indexado dinamico, que en Adreno presionan registros aunque `BlobCount` sea 6.


## 🌬️ 2026-09-17 — la respiración REEMPLAZA el reloj de la atracción ([[BP_BreathManager_SC]])
Pedido de Beltrán: *"Metaball, puede ser el spread o curl"*.

🔑 **El hallazgo del cableado que decidió todo:** `Attract = lerp(AttractMin, AttractMax, sin(Time·AttractSpeed))` → `P = C·Spread·(1−Attract)`. **El metaball ya respiraba solo, por reloj**: se funde y se separa. La respiración no suma otra animación: **toma ese ciclo**.

- **Material `M_MetaBlob_SC`**: `Custom` **`BreathAttract`** (`Sin`=`Sine_0`, `S`=`Signed`, `On`=`On` del MPC, `G`=`BreathAttract`) → `LinearInterpolate_0.Alpha`: `lerp(Sin, −S, saturate(On·G))`.
  - Inhala (S = +1) → alpha −1 → **máxima separación** del rango que ya recorría el reloj · exhala → `AttractMax` → **se funde en una masa** · reposo (S = 0) → `AttractMin` → el spread autorado.
  - **Sin umbral (`On` = 0) sigue el reloj de siempre**; al entrar al umbral pasa al usuario con un fundido de ~1 s.
- **BP**: perilla `BreathAttract` (0..1, cat. *R - Respiracion*) + `ApplyBreath` (a `Volume`) al final del Construction Script. Instancia `GAL_7_MetaBlob`: **1**. Verificado en el MID.
- 💡 No agrega extensión ni costo al raymarch: el rango es el mismo que ya recorría el reloj.


### 🌬️ 2026-09-17 (2ª pasada) — curva SUAVE y rango exagerado
Beltrán tras probar: *"llegó muy duro a los valores máximos y mínimos, no suave como con la esfera"* y *"un poco más exagerados"*.
- **Causa (en el manager, no acá):** `BreathSigned` era `clamp(gain·y)` → con ganancia 1,5 una respiración normal chocaba contra ±1 y quedaba plana. Ahora es `k·y/(1+(k−1)|y|)` (techo suave, `SignedGain` 2).
- **Mapeo nuevo del consumidor** (sin quiebre en 0 aunque las ganancias sean asimétricas): `m = 1 + S·lerp(−Out, In, smoothstep((S+1)/2))`. `In` = fracción a inhalación plena, `Out` = a exhalación plena, igual que antes.
- **Pedido: "el spread y el curl muy bajos en la exhalación"**. Con la versión 1 al exhalar el attract llegaba a `AttractMax`, pero el **curl (19,4, tan grande como el spread) seguía separando las gotas**: nunca se fundían.
- `Custom` **`BreathAttractSpread`** (reemplaza a `BreathAttract` y al `LinearInterpolate_0` del reloj, borrados): `lerp(lerp(AttractMin, AttractMax, sin), 1 − mSpread, saturate(On·BreathAttract))` → `AppendVector_0.B`. Con umbral, la respiración maneja el spread directo: `mSpread = 1 + S·lerp(−SpreadOut, SpreadIn, smoothstep)`.
- `Custom` **`BreathCurl`** = `CurlAmount·lerp(1, mCurl, saturate(On·BreathAttract))` → `AppendVector_3.A`.
- Perillas nuevas **`BreathSpreadIn/Out`** · **`BreathCurlIn/Out`**; `BreathAttract` queda como "cuánto toma el control la respiración" (0..1).
- **Valores**: `SpreadIn 0,6` · `SpreadOut −0,97` (×0,03: una sola masa) · `CurlIn 0,5` · `CurlOut −0,95` (×0,05: quieta) · `BreathAttract 1`.
