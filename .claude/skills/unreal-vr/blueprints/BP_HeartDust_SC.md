# BP_HeartDust_SC — polvo y partículas del mar del latido (Mechanics/Heart/Scape/)

## Purpose
Pedido de Beltrán (2026-10-01): *"partículas y polvo que ayuden a entender el giro"* de la vuelta del mar. Motas fijas al mar con paralaje: al girar, las cercanas pasan de costado y las lejanas despacio → se lee el giro y la subida.
Ruta: `/Game/SoulCharger/Mechanics/Heart/Scape/BP_HeartDust_SC`. Actor SEPARADO (no un componente nuevo del scape: gotchas 402/478); lo spawnea y destruye `BP_HeartScape_SC` (`BootDust` / `DustEnd`, con `Owner = scape`, pegado al `DefaultSceneRoot`).

## Status
🟢 Construido y spawneado/pegado en PIE. ⬜ Look y **72 fps en visor/APK** (OVR Metrics) sin ver.

## Assets
| Asset | Qué es |
|---|---|
| `SM_HeartDust_SC` | 4400 quads = **17.600 vértices**: 3900 de polvo + 500 partículas, en el espacio LOCAL del mar. 80 % en un anillo r 400-1400 cm, z 60-620 (donde pasa el espectador); el resto r 150-2800, z 10-950. Generador `scripts/gen_heart_dust.py`; modelo `scripts/heart_dust_model.py` con chequeo numérico (~165 motas a menos de 4 m del espectador). |
| `M_HeartDust_SC` / `MI_HeartDust_SC` | Unlit · AlphaComposite · dos caras · sin niebla · precisión Full. `scripts/hlsl/HeartDustVS.hlsl` (17 entradas) + `HeartDustPS.hlsl` (4). Plan `scripts/plan_heart_dust.py`, armado `scripts/apply_heart_dust_material.py`. **1 draw call.** |

## Cómo se mueve (VS)
Motas FIJAS al mar con deriva de 6 cm. Tamaño angular con piso; se apagan cerca de la cara (`NearFade`) y lejos (`FarFade`). Al estar pegado al mar, hereda su giro, subida y regreso sin lógica propia.

## Perillas (MI_HeartDust_SC)
| Grupo | Perillas |
|---|---|
| 1 - Polvo | `DustAlpha` 0,22 · `DustSizeDeg` 0,10 · `DustColor` (1, 0,88, 0,84) |
| 2 - Particulas | `SparkAlpha` 0,55 · `SparkSizeDeg` 0,20 · `SparkColor` (1, 0,72, 0,66) · `Twinkle` 0,6 |
| 3 - Comun | `SizeMinDeg` 0,07 · `SizeVar` 0,35 · `DriftAmp` 6 · `DriftSpeed` 0,18 · `NearFade` 60 · `FarFade` 2600 · `Glow` 1 |
| 9 - Interno | `DustReveal` (lo escribe el BP) |

## Variables
- `Dust` (StaticMeshComponent): sin sombra, `translucencySortPriority` 2.
- `ScapeRef` (Z - Interno).
- `bPreviewOnly` (editable): una copia colocada a mano para mirar en el editor se destruye al dar Play.

## Grafos
- `BeginPlay`: `bPreviewOnly` → `DestroyActor`; si no, `CastToBP_HeartScape_SC(GetOwner)` → `ScapeRef`.
- `Tick` → `DustDrive()`: `DustReveal` = `ScapeRef.EntryT` (el polvo aparece y se va con la esfera central).
- 🔑 El polvo LEE al scape: el scape no tiene variables del polvo más allá de `DustRef`.
