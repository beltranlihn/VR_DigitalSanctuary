# Plan — modos de deformación del metaball + estación de pulso (2026-09-18)

> Pedido de Beltrán con dos dibujos (CURL · SIMETRIC · ROUND · GROUP, y las ondas concéntricas del corazón).
> Objetivo suyo: **un solo efecto que sirva para Breath, Mind y Heart**, con un switch en el BP para explorar entre formas.

## 0. Lo que manda el shader (leído antes de diseñar)
`M_MetaBlob_SC` → `Custom_0`, entradas `RayOrigin`, `RayDir`, `ParA`, `ParB`, `ParC`.

```hlsl
float3 C[16] = { ...tabla fija de direcciones... };
float  SF[16] = { ...variación de tamaño por gota... };
for (j = 0; j < N; j++) {
  float3 curl = float3(sin(T*CurlSpd + f*1.7), cos(...), sin(...));
  P[j] = C[j] * Spread * (1.0 - Attract) + curl * CurlAmt;   // ← AQUÍ entra todo
  R[j] = max(Rad * (1.0 + SizeVar*SF[j]), 0.5);
}
// después: sphere tracing con smooth-min, NSteps × N
```

🔑 **Las posiciones se calculan UNA VEZ POR PÍXEL, fuera del march.** Cambiar la ley de `P[j]` cuesta ~nada.
🔴 **Lo caro es `N` (BlobCount).** El march es `NSteps × N` = 64 × 6 = **384** evaluaciones por píxel, más `4 × N` de la normal. El metaball ya aporta **~6-12 ms** contra un presupuesto de 13,9 ms (medido en visor el 2026-09-15). **Duplicar las gotas duplica el efecto más caro de la galería.**

| Gotas | Evaluaciones | Contra las 6 de hoy |
|---|---|---|
| 6 (hoy) | 384 | ×1,0 |
| 9 (SIMETRIC del dibujo: centro + 8) | 576 | ×1,5 |
| 12 | 768 | ×2,0 |
| 16 (GROUP con 4 grupos de 4) | 1024 | ×2,7 |

👉 Los 4 modos salen casi gratis. **GROUP es el único con problema real de rendimiento**, y no por el modo sino por la cantidad de gotas que pide para leerse como grupos. Se construye igual y se **mide en visor** antes de decidir con cuántas se queda.

## 1. Los 4 modos — una sola ley, cuatro patrones
Se reescribe el bucle de posiciones con esta forma única:

```hlsl
P[j] = base*Spread + D*Spread*(1.0 - Attract) + curl*CurlAmt*curlG;
```
- **`base`** = lo que NO colapsa con `Attract` (solo lo usa GROUP: el centro de cada grupo).
- **`D`** = lo que SÍ colapsa: al subir `Attract` las gotas se van a la masa única.
- **`curlG`** = cuánto ruido curl se suma en ese modo.

| # | Modo | `base` | `D` | Lectura |
|---|---|---|---|---|
| **0** | **CURL** | 0 | `C[j]` (tabla de hoy) | 🔴 **Idéntico byte a byte a lo actual.** Es el default: quien no toque el switch no ve ningún cambio |
| **1** | **SIMETRIC** | 0 | gota 0 al centro; las demás en anillo `(cos a, sin a, 0)` con `a = 2π(j−1)/(N−1)` | Nacen unidas en el centro y se abren **radialmente**, como la flor del dibujo |
| **2** | **ROUND** | 0 | igual que 1 pero `a += Twist·(1−Attract)` y radio `1 + 0,35·SF[j]` | **Se abren girando**: la flecha del dibujo. Al cerrarse vuelven desenroscándose |
| **3** | **GROUP** | centro del grupo `g = j mod G`, en anillo, × `GrpSpread` | `C[j] · LocalScale` | **G grupitos separados.** `Attract` junta cada gota a SU grupo, no al centro del mundo: quedan 4-5 racimos |

**Por qué esta forma y no cuatro shaders:** el branch es por **uniforme** (todos los píxeles toman la misma rama), que en Adreno es barato. Un `StaticSwitchParameter` sería aún más barato pero **no se puede cambiar en un MID en runtime** — y el pedido es justamente poder explorar desde el panel.

### Parámetros nuevos del material
- `ParC` pasa de float2 a **float4**: `(SizeVariation, BlobCount, Mode, GroupCount)`.
- Entrada nueva **`ParD`** = `(Twist, GrpSpread, LocalScale, 0)`.
- Total: **6 entradas** en el `Custom`. ⚠ Tope conocido: con 13 entradas un `Custom` falló a compilar sin decir por qué; con 6 compila (gotcha 1304).

### Perillas nuevas del BP (cat. **`B - Modo`**)
`BlobMode` (int 0-3) · `Twist` · `GroupCount` · `GroupSpread` · `LocalScale`.
⚠ **El MCP no crea enums.** Va como **entero** con los valores documentados. Si Beltrán crea a mano el enum `E_BlobMode`, se migra la variable y queda el desplegable con nombres (mismo trato que `F_SoulPortrait`).

## 2. Estación de pulso (Heart) — las ondas concéntricas
Del segundo dibujo: **anillos que nacen en un centro y se expanden**, y de perfil un tren de ondas que levanta la superficie.

- **BP nuevo `BP_PulseField_SC` + `M_PulseField_SC`.** 🔴 **No se duplica `BP_CloudPlane_SC`**: duplicar arrastra decenas de perillas muertas (regla del proyecto) y el océano sigue intacto en su estación. Este nace con sus ~8 perillas y nada más.
- **Sin buffer de eventos.** Se copia el patrón **ya probado del túnel**: una fase continua y K anillos separados una unidad de fase:
  ```
  edad_k = frac(PulsePhase) + k          k = 0..K-1
  r_k    = c · edad_k
  h      = Σ A · exp(−((r − r_k)/w)²) · exp(−edad_k/decay)
  ```
  Con K = 4-5 anillos vivos, son 5 evaluaciones por vértice/píxel. Barato.
- **La fase se INTEGRA en el BP** (`PulsePhase += Rate·DT`), nunca `Time × Rate`: cambiar el ritmo en caliente saltaría la onda entera (gotcha ya pagado en los túneles).
- **De dónde sale el ritmo:** variable `Rate` con tres fuentes posibles, en este orden de construcción:
  1. **fija** (para autorar mirando),
  2. **respiración** (el tracking que ya anda, que es lo que Beltrán quiere probar ahora),
  3. **BPM por OSC** (`BP_BioHub`/`BP_HeartSensor`), que es el destino final.
  En un latido se hace **resync suave** de la fase al entero más cercano: se engancha al latido real sin saltos.

## 3. Orden de construcción
1. 🟢 **Modos del metaball** (modo 0 idéntico → riesgo cero) → verificar en el viewport con `PreviewBreath`, modo por modo.
2. **Medir GROUP en visor** subiendo `BlobCount` hasta que se lea como racimos, y decidir con el número en la mano.
3. **`BP_PulseField_SC`** + su material, colocado como estación nueva de la galería.
4. Engancharlo a la respiración para probar el ritmo; OSC después.
5. Trackers + `MECANICAS-PORTABLES.md` (el metaball con modos pasa a ser ficha portable para Breath/Mind/Heart).

## 4. Riesgos anotados
- 🔴 **Rendimiento de GROUP** (arriba). Se mide, no se promete.
- ⚠ **SIMETRIC del dibujo son 9 gotas** (centro + 8); con las 6 de hoy salen centro + 5. Subir `BlobCount` es una perilla, y cuesta ×1,5.
- ⚠ El anillo de SIMETRIC/ROUND vive en el **plano XY local del actor**: rotando el actor se elige desde dónde se ve la flor. Si hace falta que se lea igual desde cualquier lado, la variante es distribución de Fibonacci sobre la esfera — es cambiar 2 líneas.
- ⚠ La estación nueva hay que **agregarla a los arrays del `GAL_DIRECTOR`** (`Anchors`, `Stations`, `Names`, `StationTags`). Es agregar, no sacar.
