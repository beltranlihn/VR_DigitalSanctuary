# Cableado de `M_BreathValley_SC`: los tres Custom del valle (v2, revisada el 2026-09-28)

> **Fuente de verdad:** `docs/PLAN-VALLE-ENTERING-2026-09-27.md` (§7). Este archivo dice **qué expresión del material entra en cada pin** de cada Custom y **a qué salida del material va** cada uno. El código está en los `.hlsl` de esta carpeta: cada archivo es el **cuerpo** de un `MaterialExpressionCustom` (termina en `return`). Su cabecera lista las mismas entradas, en el mismo orden. Las tablas de las §4 y §5 salen de `valley_build.json` (lo genera `scripts/plan_valley_material.py`).
>
> **Estado (2026-09-28):** los HLSL de la **v2 revisada** están escritos y verificados **sin Unreal** (§9). El material que existe en Unreal es la **v1**: hay que rearmarlo (§8). La v1 de este archivo está en `VR_Test/Saved/ClaudeScripts/valle_v1_backup/Valley_CABLEADO.md`; la v2 antes de la revisión, en `valle_v2_backup_pre_correccion/`.
>
> **Qué cambió en la revisión:** `ValleyHeightVS` suma `SwellIn` (29 entradas) y `ValleyGradVS` suma además `SwellShade` y `SwellShadeFull` al final (31 entradas). El oleaje mueve la geometría solo en la capa lejana y en el llano queda solo en el sombreado (el gradiente de `ValleyGradVS` lleva ese término). `DitherAmt` pasa a 1,5. El grafo no cambia.

## 0. Qué cambió respecto de la v1

**El grafo no cambia:**
- Siguen los mismos 3 Custom, las mismas salidas, los mismos 2 interpoladores y el mismo preshader.
- Los ajustes del material son los mismos.

**Cambian las entradas y los parámetros:**

| | v1 | v2 |
|---|---|---|
| Entradas de `ValleyHeightVS` | 23 | **29** |
| Entradas de `ValleyGradVS` | 23 | **31** (las 29 de `ValleyHeightVS` + `SwellShade`, `SwellShadeFull`) |
| Entradas de `ValleyPS` | 42 | **44** |
| Parámetros | 61 (52 escalares + 9 vectores) | **71 (62 + 9)** |
| Expresiones del material | 95 | **105** |

- **Salen 17 parámetros:** `ValleyX`, `ValleyA`, `ValleyB`, `SeatIn`, `SeatOut`, `RimHeight`, `RimCrest`, `RimBack`, `DuneAmp`, `DuneRise`, `DuneScale`, `DuneSeed`, `DuneShiftX`, `DuneShiftY`, `MorphNear`, `MorphFar` y `SheenPow`. Sus nodos quedan **huérfanos**: se borran.
- **Entran 27 parámetros:** `HillAmp`, `HillScale`, `HillSeed`, `HillNear`, `HillFull`, `HillFade`, `HillEnd`, `FarBase`, `FarAmp`, `FarScale`, `FarSeed`, `FarIn`, `FarFull`, `FarCrest`, `FarBack`, `SwellAmp`, `SwellNear`, `SwellIn`, `SwellFar`, `SwellScale`, `SwellSpeed`, `SwellSeed`, `SwellShade`, `SwellShadeFull`, `SheenW`, `HFogDist` y `HFogFall`.
- **Cambian de default:** `MorphAmt` 0,45 → 0,15, `Sheen` 0,4 → 0,28, `FogStart` 1000 → 1500, `FogDist` 5000 → 45000, `FogMax` 0,6 → 0,9 y `DitherAmt` 1 → 1,5.
  - ⚠ El adelanto temporal del tracker había dejado en el material `MorphSpeed` 4, `MorphAmt` 0,9 y `FogMax` 0,85. El rearmado los pisa: hay que verificar que queden los defaults de la tabla.

## 1. El grafo de un vistazo

```
                          ┌──────────────────────────────┐
 LocalPosition (XYZ) ─────┤ Custom ValleyHeightVS  (F3)  ├── Transform (vector, Local→World) ──► World Position Offset
   │  + 28 parámetros ────┤                              │
   │                      └──────────────────────────────┘
   │                      ┌──────────────────────────────┐
   ├──────────────────────┤ Custom ValleyGradVS    (F4)  ├── VertexInterpolator_0 (VS→PS) ──┐  VI1
   │  (los 28 + 2) ───────┤                              │                                  │
   │                      └──────────────────────────────┘                                  │
   └── VertexInterpolator_1 (VS→PS) ─────────────────────────────────────────────────────┐  │  LPi
                                                                                         ▼  ▼
 CameraVector ── Transform (vector, World→Local) ───────────────────── CamL ──► ┌───────────────────────┐
 Distance(AbsoluteWorldPosition, CameraPositionWS) ─────────────────── Dist ──► │ Custom ValleyPS  (F3) ├──► Emissive Color
 preshader D(LightAz,LightEl) · D(GlowAz,GlowEl) · D(MoonAz,MoonEl) ── dirs ──► │                       │
 preshader Cosine(MoonRadius, Period 360) ──────────────────────── MoonCosR ──► │                       │
 36 parámetros (25 escalares del PS, 9 vectores, Part, PerfMode) ─────────────► └───────────────────────┘
```

**Un Custom por salida** (gotcha 454): Unreal compila el WPO y cada `VertexInterpolator` en funciones separadas. Un Custom conectado a dos salidas **se ejecuta dos veces**. Por eso la altura (WPO) y el gradiente (interpolador) son dos nodos distintos que repiten la misma cuenta de `h`. Si se toca la cuenta en uno, hay que tocarla igual en el otro: `Valley_check.py` lo verifica.

## 2. Ajustes del material (§7 del plan; sin cambios)

| Propiedad | Valor |
|---|---|
| `MaterialDomain` | Surface |
| `BlendMode` | Opaque |
| `ShadingModel` | Unlit (la única salida con color es Emissive) |
| `TwoSided` | true |
| `FloatPrecisionMode` | **`MFPM_Full_MaterialExpressionOnly`** (el borde de la luna, el dither y las distancias de hasta 1000 m (la esfera del cielo) lo necesitan; gotchas 185 y 382) |
| Salidas usadas | **Emissive Color** ← `ValleyPS` · **World Position Offset** ← `Transform(ValleyHeightVS)` |

## 3. Nodos que no son parámetros (sin cambios)

| Rol | Clase | Configuración | Pin de salida usado (`outputIndex`, máscara) | Va a |
|---|---|---|---|---|
| `LP` | `MaterialExpressionLocalPosition` | Defaults: `IncludedOffsets = IncludeOffsets`, `LocalOrigin = Instance` (la misma config que `M_HeartScape_SC`). El código solo lee `LP.xy`/`LPi.xy` y el WPO es vertical puro | `XYZ` (0; máscara 1,1,1,0) | `LP` de los dos Custom VS y entrada `VS` de `VertexInterpolator_1` |
| `ValleyHeightVS` | `MaterialExpressionCustom` | `OutputType CMOT_Float3`, `Description "ValleyHeightVS"`, sin `additionalOutputs`, `code` = `ValleyHeightVS.hlsl` | salida principal (0) | entrada de `Transform_WPO` |
| `Transform_WPO` | `MaterialExpressionTransform` | `TransformSourceType = TRANSFORMSOURCE_Local`, `TransformType = TRANSFORM_World` (vector) | (0) | **World Position Offset** |
| `ValleyGradVS` | `MaterialExpressionCustom` | `OutputType CMOT_Float4`, `Description "ValleyGradVS"`, `code` = `ValleyGradVS.hlsl` | (0) | entrada `VS` de `VertexInterpolator_0` |
| `VertexInterpolator_0` | `MaterialExpressionVertexInterpolator` | — | `PS` (0; sin máscara) | `VI1` de `ValleyPS` (float4) |
| `VertexInterpolator_1` | `MaterialExpressionVertexInterpolator` | — | `PS` (0; sin máscara) | `LPi` de `ValleyPS` (float3) |
| `CamVec` | `MaterialExpressionCameraVectorWS` | — | (0) | entrada de `Transform_Cam` |
| `Transform_Cam` | `MaterialExpressionTransform` | `TransformSourceType = TRANSFORMSOURCE_World`, `TransformType = TRANSFORM_Local` (vector) | (0) | `CamL` de `ValleyPS` |
| `WorldPos` | `MaterialExpressionWorldPosition` | Default `WPT_Default` (absoluta, **con** el WPO: la distancia es al suelo desplazado) | (0) | `A` de `Distance` |
| `CamPos` | `MaterialExpressionCameraPositionWS` | — | (0) | `B` de `Distance` |
| `Distance` | `MaterialExpressionDistance` | — | (0) | `Dist` de `ValleyPS` |
| `ValleyPS` | `MaterialExpressionCustom` | `OutputType CMOT_Float3`, `Description "ValleyPS"`, `code` = `ValleyPS.hlsl` | salida principal | **Emissive Color** (`connect_to_output` con `output_name: ""`; gotcha 447) |
| Preshader | ver §6 | 22 nodos (`Sine`/`Cosine`/`AppendVector`/`Multiply`) | (0) | `LightDir`, `GlowDir`, `MoonDir` y `MoonCosR` de `ValleyPS` |

Interpoladores: `VI1` (4) + `LPi` (3) = **7 escalares de 16**, más los que el motor usa para `WorldPosition` y `CameraVector`.

**Forma de cada entrada** al cargarla ya cableada (gotcha 458):
- `ScalarParameter`: `"outputIndex": 0, "mask": 0`.
- `VectorParameter` por **`RGB`** (float3): `"outputIndex": 0, "mask": 1, "maskR": 1, "maskG": 1, "maskB": 1, "maskA": 0` (gotcha 453).
- `LocalPosition` `XYZ`: `"outputIndex": 0, "mask": 1, "maskR": 1, "maskG": 1, "maskB": 1, "maskA": 0`.
- `VertexInterpolator` `PS`, `Transform`, `Distance`, `AppendVector` y `Cosine`: `"outputIndex": 0, "mask": 0`.

## 4. `ValleyHeightVS` (29 entradas) y `ValleyGradVS` (31 entradas)

Las 29 primeras son **idénticas** en los dos, en el mismo orden. `ValleyGradVS` agrega dos al final (30 y 31), que `ValleyHeightVS` no tiene. Los dos Custom se conectan a **los mismos nodos** de parámetro: no hay que duplicar parámetros.

| # | Entrada | Tipo | Expresión | Grupo | Default |
|---|---|---|---|---|---|
| 1 | `LP` | float3 | `LocalPosition` → `XYZ` | — | — |
| 2 | `Part` | float | ScalarParameter `Part` | `9 - Interno` | 0 |
| 3 | `PerfMode` | float | ScalarParameter `PerfMode` | `9 - Interno` | 0 |
| 4 | `HillAmp` | float | ScalarParameter `HillAmp` | `1 - Colinas` | 2200 |
| 5 | `HillScale` | float | ScalarParameter `HillScale` | `1 - Colinas` | 8 |
| 6 | `HillSeed` | float | ScalarParameter `HillSeed` | `1 - Colinas` | 63 |
| 7 | `HillNear` | float | ScalarParameter `HillNear` | `1 - Colinas` | 4500 |
| 8 | `HillFull` | float | ScalarParameter `HillFull` | `1 - Colinas` | 12000 |
| 9 | `HillFade` | float | ScalarParameter `HillFade` | `1 - Colinas` | 19000 |
| 10 | `HillEnd` | float | ScalarParameter `HillEnd` | `1 - Colinas` | 26000 |
| 11 | `DuneLow` | float | ScalarParameter `DuneLow` | `1 - Colinas` | −0,35 |
| 12 | `DuneHigh` | float | ScalarParameter `DuneHigh` | `1 - Colinas` | 1,2 |
| 13 | `FarBase` | float | ScalarParameter `FarBase` | `2 - Lejos` | 2600 |
| 14 | `FarAmp` | float | ScalarParameter `FarAmp` | `2 - Lejos` | 5500 |
| 15 | `FarScale` | float | ScalarParameter `FarScale` | `2 - Lejos` | 22 |
| 16 | `FarSeed` | float | ScalarParameter `FarSeed` | `2 - Lejos` | 151 |
| 17 | `FarIn` | float | ScalarParameter `FarIn` | `2 - Lejos` | 28000 |
| 18 | `FarFull` | float | ScalarParameter `FarFull` | `2 - Lejos` | 40000 |
| 19 | `FarCrest` | float | ScalarParameter `FarCrest` | `2 - Lejos` | 47000 |
| 20 | `FarBack` | float | ScalarParameter `FarBack` | `2 - Lejos` | 59000 |
| 21 | `SwellAmp` | float | ScalarParameter `SwellAmp` | `3 - Movimiento` | 1880 |
| 22 | `SwellNear` | float | ScalarParameter `SwellNear` | `3 - Movimiento` | 1500 |
| 23 | `SwellIn` | float | ScalarParameter `SwellIn` | `3 - Movimiento` | 28000 |
| 24 | `SwellFar` | float | ScalarParameter `SwellFar` | `3 - Movimiento` | 40000 |
| 25 | `SwellScale` | float | ScalarParameter `SwellScale` | `3 - Movimiento` | 2,5 |
| 26 | `SwellSpeed` | float | ScalarParameter `SwellSpeed` | `3 - Movimiento` | 1 |
| 27 | `SwellSeed` | float | ScalarParameter `SwellSeed` | `3 - Movimiento` | 0 |
| 28 | `MorphAmt` | float | ScalarParameter `MorphAmt` | `3 - Movimiento` | 0,15 |
| 29 | `MorphSpeed` | float | ScalarParameter `MorphSpeed` | `3 - Movimiento` | 1 |
| 30 | `SwellShade` | float | ScalarParameter `SwellShade` (**solo `ValleyGradVS`**) | `3 - Movimiento` | 1000 |
| 31 | `SwellShadeFull` | float | ScalarParameter `SwellShadeFull` (**solo `ValleyGradVS`**) | `3 - Movimiento` | 5000 |

- **Salidas:** `ValleyHeightVS` → float3 `(0, 0, h)` → `Transform_WPO` → **WPO**. `ValleyGradVS` → float4 `(gx, gy, h, hf)` → `VertexInterpolator_0` → `VI1`. El gradiente `(gx, gy)` es el de h **más** el sombreado del oleaje (`Av·∇s`): con `SwellShade` 0 es exactamente ∇h.
- **Tiempo:** los dos leen `View.GameTime` adentro. **No se cablea ningún nodo `Time`**.
- `Part` 1 (cielo) o `PerfMode` 1/3 → los dos devuelven 0 (disco plano, gradiente nulo).

## 5. `ValleyPS`: entradas (44)

| # | Entrada | Tipo | Expresión | Grupo | Default |
|---|---|---|---|---|---|
| 1 | `VI1` | float4 | `VertexInterpolator_0` → `PS` | — | — |
| 2 | `LPi` | float3 | `VertexInterpolator_1` → `PS` | — | — |
| 3 | `CamL` | float3 | `CameraVector` → `Transform` (vector, World → Local) | — | — |
| 4 | `Dist` | float | `Distance(AbsoluteWorldPosition, CameraPositionWS)` | — | — |
| 5 | `Part` | float | ScalarParameter `Part` | `9 - Interno` | 0 |
| 6 | `PerfMode` | float | ScalarParameter `PerfMode` | `9 - Interno` | 0 |
| 7 | `LightDir` | float3 | preshader `D(LightAz, LightEl)` (§6) | — | — |
| 8 | `Wrap` | float | ScalarParameter `Wrap` | `4 - Luz y superficie` | 0,3 |
| 9 | `ShadeFloor` | float | ScalarParameter `ShadeFloor` | `4 - Luz y superficie` | 0 |
| 10 | `SlopeDark` | float | ScalarParameter `SlopeDark` | `4 - Luz y superficie` | 1,2 |
| 11 | `ColLit` | float3 | VectorParameter `ColLit` → `RGB` | `4 - Luz y superficie` | (0,434, 0,527, 0,855) |
| 12 | `ColShadow` | float3 | VectorParameter `ColShadow` → `RGB` | `4 - Luz y superficie` | (0,061, 0,117, 0,352) |
| 13 | `ColSheen` | float3 | VectorParameter `ColSheen` → `RGB` | `4 - Luz y superficie` | (0,855, 0,761, 0,913) |
| 14 | `Sheen` | float | ScalarParameter `Sheen` | `4 - Luz y superficie` | 0,28 |
| 15 | `SheenW` | float | ScalarParameter `SheenW` | `4 - Luz y superficie` | 0,3 |
| 16 | `SheenBack` | float | ScalarParameter `SheenBack` | `4 - Luz y superficie` | 0,35 |
| 17 | `CrestLight` | float | ScalarParameter `CrestLight` | `4 - Luz y superficie` | 0,2 |
| 18 | `ShadowCenter` | float3 | VectorParameter `ShadowCenter` → `RGB` | `9 - Interno` | (380, 0, 125) |
| 19 | `ShadowRadius` | float | ScalarParameter `ShadowRadius` | `9 - Interno` | 85 |
| 20 | `ShadowStrength` | float | ScalarParameter `ShadowStrength` | `9 - Interno` | 1,5 |
| 21 | `ShadowSoft` | float | ScalarParameter `ShadowSoft` | `5 - Sombra` | 0,8 |
| 22 | `ShadowTint` | float3 | VectorParameter `ShadowTint` → `RGB` | `5 - Sombra` | (0,305, 0,352, 0,68) |
| 23 | `ShadowMax` | float | ScalarParameter `ShadowMax` | `5 - Sombra` | 0,8 |
| 24 | `SkyZenith` | float3 | VectorParameter `SkyZenith` → `RGB` | `6 - Cielo` | (0,216, 0,328, 0,597) |
| 25 | `SkyHorizon` | float3 | VectorParameter `SkyHorizon` → `RGB` | `6 - Cielo` | (0,597, 0,624, 0,839) |
| 26 | `SkyGlow` | float3 | VectorParameter `SkyGlow` → `RGB` | `6 - Cielo` | (0,831, 0,68, 0,855) |
| 27 | `SkyGradTop` | float | ScalarParameter `SkyGradTop` | `6 - Cielo` | 0,7 |
| 28 | `GlowDir` | float3 | preshader `D(GlowAz, GlowEl)` (§6) | — | — |
| 29 | `GlowPow` | float | ScalarParameter `GlowPow` | `6 - Cielo` | 2 |
| 30 | `GlowHeight` | float | ScalarParameter `GlowHeight` | `6 - Cielo` | 0,45 |
| 31 | `GlowAmt` | float | ScalarParameter `GlowAmt` | `6 - Cielo` | 0,8 |
| 32 | `MoonDir` | float3 | preshader `D(MoonAz, MoonEl)` (§6) | — | — |
| 33 | `MoonCosR` | float | preshader `Cosine(MoonRadius)`, `Period 360` (§6) | — | — |
| 34 | `MoonEdge` | float | ScalarParameter `MoonEdge` | `7 - Luna` | 0,03 |
| 35 | `MoonColor` | float3 | VectorParameter `MoonColor` → `RGB` | `7 - Luna` | (0,73, 0,644, 0,839) |
| 36 | `MoonOpacity` | float | ScalarParameter `MoonOpacity` | `7 - Luna` | 0,55 |
| 37 | `MoonFill` | float | ScalarParameter `MoonFill` | `7 - Luna` | 0,2 |
| 38 | `MoonRim` | float | ScalarParameter `MoonRim` | `7 - Luna` | 1 |
| 39 | `FogStart` | float | ScalarParameter `FogStart` | `8 - Niebla` | 1500 |
| 40 | `FogDist` | float | ScalarParameter `FogDist` | `8 - Niebla` | 45000 |
| 41 | `FogMax` | float | ScalarParameter `FogMax` | `8 - Niebla` | 0,9 |
| 42 | `HFogDist` | float | ScalarParameter `HFogDist` | `8 - Niebla` | 60000 |
| 43 | `HFogFall` | float | ScalarParameter `HFogFall` | `8 - Niebla` | 1500 |
| 44 | `DitherAmt` | float | ScalarParameter `DitherAmt` | `8 - Niebla` | 1,5 |

- **Salida:** float3, color **lineal** final → **Emissive Color**.
- Usa además `Parameters.SvPosition` (hash del dither, el mismo de `HeartScapePS`). No se cablea.
- `SheenW` **reemplaza** a `SheenPow` en el mismo lugar de la lista (entrada 15). No es un renombre: cambia el significado (un ancho, no un exponente) y el default (0,3). No hay que heredar el 4.
- `HFogDist` y `HFogFall` entran entre `FogMax` y `DitherAmt` (entradas 42 y 43).

## 6. Las cadenas de preshader (cero costo por píxel; sin cambios)

Dependen solo de parámetros, así que Unreal las pliega a **expresiones uniformes**: se calculan una vez por cuadro en la CPU.

`D(az, el) = (cos el · cos az, cos el · sin az, sin el)`, con los ángulos en **grados**:

```
az ──► Cosine (Period 360) ──► AppendVector.A ─┐
az ──► Sine   (Period 360) ──► AppendVector.B ─┴► (cos az, sin az) ──► Multiply.A ─┐
el ──► Cosine (Period 360) ───────────────────────────────────────► Multiply.B ─┴► AppendVector.A ─┐
el ──► Sine   (Period 360) ─────────────────────────────────────────────────────► AppendVector.B ─┴► float3 ──► ValleyPS.<Dir>
```

| Salida | `az` | `el` | Valor con defaults |
|---|---|---|---|
| `LightDir` | ScalarParameter `LightAz` (`4 - Luz y superficie`, 20) | `LightEl` (`4 - Luz y superficie`, 25) | (0,851651, 0,309976, 0,422618) |
| `GlowDir` | `GlowAz` (`6 - Cielo`, 20) | `GlowEl` (`6 - Cielo`, 2) | (0,939120, 0,341812, 0,034899) |
| `MoonDir` | `MoonAz` (`7 - Luna`, −40) | `MoonEl` (`7 - Luna`, 7) | (0,760334, −0,637996, 0,121869) |
| `MoonCosR` | `Cosine(MoonRadius)` con `Period 360` (`MoonRadius`: `7 - Luna`, 9) | — | 0,987688 |

Son 7 nodos por dirección (×3) más 1 para `MoonCosR`: **22 nodos**. Pines: los unarios (`Sine`, `Cosine`) entran por `"None"`; `AppendVector` y `Multiply` por `A`/`B`.

🔴 **`Period = 360` en TODOS los `Sine`/`Cosine`.** El default es `Period = 1` (la entrada en vueltas) y `Period ≤ 0` no calcula `cos(x)`. Si falta el 360, la luz y la luna apuntan a cualquier lado sin ningún error. **Control:** en el editor, `LightAz` 20 → 200 tiene que dar vuelta la iluminación de las lomas.

## 7. Parámetros: el conteo

| Destino | Escalares | Vectores |
|---|---|---|
| Los dos Custom VS (`Part`, `PerfMode` y los 26 de forma y movimiento) | 28 | — |
| Solo `ValleyGradVS` (`SwellShade`, `SwellShadeFull`) | 2 | — |
| Solo `ValleyPS` | 25 | 9 (los 8 colores y `ShadowCenter`) |
| Solo preshader (`LightAz`, `LightEl`, `GlowAz`, `GlowEl`, `MoonAz`, `MoonEl`, `MoonRadius`) | 7 | — |
| **Total** | **62** | **9** → **71**, como en la §7.1 del plan |

`Part` y `PerfMode` son **un solo nodo cada uno** y alimentan los tres Custom.

**Nodos del material:** 71 parámetros + 22 de preshader + 3 Custom + `LocalPosition` + 2 `VertexInterpolator` + 2 `Transform` + `CameraVector` + `WorldPosition` + `CameraPositionWS` + `Distance` = **105 expresiones**.

**Enlaces:**
- 60 entradas de los VS (29 + 31) y 44 del PS.
- 30 dentro de las cadenas de dirección y 1 en `MoonCosR`.
- 6 del resto: `LocalPosition` → VI_1, GradVS → VI_0, HeightVS → Transform, CameraVector → Transform, y 2 a `Distance`.
- 2 salidas del material: Emissive y WPO.

## 8. Receta de carga (v1 → v2; resumen de las gotchas 446, 447, 453 y 458)

0. **Antes:** contar los actores del nivel. Guardar con rutas explícitas (reglas de la etapa).
1. **Parámetros:**
   - Crear los 27 nuevos con grupo, default y rango de la §7.1 del plan. `valley_build.json` trae nombre, tipo, default y grupo.
   - **Borrar los 17 nodos de parámetro que salieron** (§0). Quedan desconectados cuando se recargan las entradas, pero hay que sacarlos del grafo y de la MI.
2. **Código:**
   - Cargar el `code` de cada Custom desde `valley_build.json` (`read_file` + `set_properties({"code": ..., "outputType": ..., "description": ...})`).
   - Los comentarios de la cabecera viajan con el código. No cuestan nada: el compilador los descarta.
3. **Entradas:**
   - Vaciar primero: `set_properties({"inputs": []})`.
   - Después cargarlas **ya cableadas** en una sola llamada, en el orden de las tablas de las §4 y §5 y con la forma de la §3.
   - Releer con `get_properties` y comparar nombres y orden contra la cabecera del `.hlsl`.
4. **Salidas:** no cambian. Verificar que siguen `ValleyPS` → Emissive (`output_name: ""`) y `Transform_WPO` → WPO.
5. **Compilar:** `recompile` y buscar `Failed to compile` en el log (PC y ES31).
6. **MI:** revisar `MI_BreathValley_SC`. Sin overrides de parámetros que ya no existen, ni de `MorphAmt`, `MorphSpeed`, `Sheen`, `FogStart`, `FogDist`, `FogMax` o `DitherAmt` con valores viejos.
7. **Controles en el editor:**
   - Control positivo del WPO: `PerfMode` 1 (disco plano) contra 0.
   - `PerfMode` 2: suelo `ColLit` plano y cielo `SkyHorizon` plano.
   - `CaptureAssetImage` después de tocar el asset (gotcha 452).
   - **Movimiento: con Realtime encendido** (Ctrl+R) o en PIE. Control positivo: `SwellSpeed` 5 durante 20 s y después volver a 1, **solo en el viewport del editor, nunca con el visor puesto** (al volver, la fase salta).
8. **BP (no es del material, pero va en la misma tanda):** `Sky` con escala 2000 y **`Treat as Background for Occlusion`** (el cielo se dibuja después del suelo; plan §6 y §9).

## 9. Verificación hecha (sin Unreal) y cómo repetirla

`python Valley_check.py` (en esta carpeta; no escribe nada en el repo) verifica (84 chequeos, `RESULTADO: TODO OK`):

1. **Estático:**
   - Las entradas de la cabecera coinciden con el código: cada una se usa y los tipos cierran en la compilación.
   - Sin bucles, arreglos ni `half`.
   - La lista de `ValleyHeightVS` es el comienzo de la de `ValleyGradVS`, en el mismo orden.
   - `OutputType` coincide con el `return`.
   - **El default escrito en la cabecera de cada `ScalarParameter` es el de la tabla 7.1 del plan** (la cabecera viaja dentro del Custom).
2. **Compilación** de un wrapper que imita la función que genera Unreal:
   - **`dxc` SM6 con `-WX`**: los tres, limpios.
   - **`fxc` SM5**: los tres, limpios.
   - **`glslc` HLSL → SPIR-V Vulkan 1.1 con `-Werror` + `spirv-val`** (el camino de la Quest): los tres, limpios.
   - Las 9 ramas `[branch]` llegan al SPIR-V como `SelectionControl DontFlatten` (`spirv-dis`).
3. **Números:** traduce **mecánicamente los `.hlsl`** a Python.
   - **Sección 12 del plan:** reproduce 13 alturas con su gradiente y `hf`, 6 colores del suelo con su `O` y 7 del cielo.
   - **Contra el modelo numpy** (`scripts/valley_model.py`), en 3000 puntos con los defaults, 2000 con perillas no default (capas encimadas, semillas, escalas) y 2000 con rampas invertidas (`HillEnd < HillFade`, `FarBack < FarCrest`, `SwellIn < SwellNear`):
     - Altura: ±6·10⁻⁴ cm (constantes de 8 cifras).
     - Gradiente: ±4·10⁻⁷.
     - Color: ±5·10⁻⁹ (incluye 300 puntos junto al metaball, donde se calcula la sombra).
   - **Controles cruzados:**
     - `h` es idéntica en las dos VS.
     - Gradiente contra diferencias finitas, con `SwellShade` 0: 1,5·10⁻⁹. El término de sombreado es exactamente `back·Av·∇s` y no toca `h` ni `hf`.
     - **Piso = 0 exacto** a ≤ 10 m del usuario y del metaball durante 1 h; la geometría del oleaje vale 0 exacto a menos de `SwellIn`.
     - Sin acantilado con `HillEnd < HillFade` (el caso de la revisión).
     - **Velocidad vertical:** la cota rigurosa (oleaje + respiración) ≤ 0,5°/s y el máximo **buscado** (200.000 muestras + optimización local, confirmado en el HLSL) por debajo de la cota.
     - Rotación de las direcciones de las tres capas.
     - `PerfMode` 1/2/3 y `Part` 1.
     - Dither (`DitherAmt` 1,5).
     - Ramas: el piso cercano no calcula ni la niebla ni el cielo; la sombra solo se calcula cerca del metaball; cada capa del VS se evalúa solo en su banda (y `ValleyHeightVS` no evalúa el oleaje en el llano).
4. **Control negativo automático:** 8 mutaciones (un peso de ola solo en Height, una derivada, una fase solo en Grad, el sombreado del oleaje, el acantilado de `HillEnd < HillFade`, la niebla de altura, el sheen sin niebla y la rama de la sombra) **tienen que fallar**, y fallan.
5. **Identidad con el plan:** el código de cada archivo es **idéntico línea a línea** al bloque de la §7.2 del plan.

**Lo que solo se puede verificar en Unreal/Quest:**
- Que el material compile en el editor (PC y ES31) y en el cook de Android.
- El control positivo `PerfMode` 1 contra 0.
- El orden de dibujo del cielo como fondo y el costo (banco `PerfValley0..3`; píxeles = m0 − m2).
- El juicio de Beltrán en el visor.

## 10. Capa viva (2026-09-28, rev. 2): 9 entradas de `ValleyPS` por preshader

Plan: `docs/PLAN-RESPIRACION-ENTORNO-2026-09-28.md` §6. El código de los tres Custom **no cambia**; cambia qué expresión entra en 9 pines de `ValleyPS` (la rev. 1 eran 11: `ShadowRadius` y `GlowHeight` volvieron a su parámetro, como en la v2):

| Entrada de `ValleyPS` | Antes (v2) | Capa viva | Helpers (`Desc`) |
|---|---|---|---|
| `FogDist`, `HFogDist`, `HFogFall`, `GlowAmt`, `GlowPow`, `ShadowSoft`, `ShadowStrength` | el parámetro | `Multiply(A = parámetro, B = Live<Nombre>)` | `M_<Entrada>` |
| `SkyHorizon` | `SkyHorizon` (RGB) | **Tint** (tinte relativo: sigue a la perilla `SkyHorizon` de `ApplyLook`): `Multiply(A = SkyHorizon.RGB, B = Add(Multiply(Subtract(BreathTint.RGB, ConstB 1), LiveWarm), ConstB 1))` = `SkyHorizon × (1 + (BreathTint − 1) × LiveWarm)` | `T_SkyHorizon_d`, `T_SkyHorizon_m`, `T_SkyHorizon_o`, `T_SkyHorizon` |
| `ShadowTint` | `ShadowTint` (RGB) | **Mix**: `Add(A = ShadowTint.RGB, B = Multiply(Subtract(ShadowWarm.RGB, ShadowTint.RGB), LiveShadowWarm))` | `X_ShadowTint_d`, `X_ShadowTint_m`, `X_ShadowTint` |

- Son todas cuentas de uniformes (parámetro × parámetro y constantes): Unreal las pliega en el **preshader** (se evalúan en la CPU al cambiar el MID). Verificación en el editor: las estadísticas del material (instrucciones del PS) tienen que quedar **iguales** antes y después (receta V3).
- Neutro exacto: `Mul` × 1, `Mix` + (B − A) × 0, `Tint` × (1 + (B − 1) × 0) = × 1: cada entrada vale lo mismo que en la v2 **bit a bit**.
- Expresiones: 108 → **133** (+11 parámetros, +7 `Multiply`, +3 del `Mix`, +4 del `Tint`). Lo arman `apply_valley_material_A.py` (helpers; lista `helpers_sobrantes` si quedan `M_*`/`X_*`/`T_*` que el plan ya no usa) y `_B.py` (cableado); `dryrun_material_script.py valle` los corre contra un editor simulado desde el material v2 y verifica: todas las entradas conectadas, idempotente, neutro = v2 exacto, respirando = `valley_model.efectivos()`. `dryrun_material_script.py rollback` prueba la vuelta a la v2 con `Saved/ClaudeScripts/aliento/rollback_valle_v2/`.
