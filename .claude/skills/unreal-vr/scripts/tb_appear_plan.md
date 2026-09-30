# Aparición "luz primero" en la paleta: plan de integración (Drawing, 2026-09-30)

Fuente: `blender-3d/scripts/anim_palette_luz.py` (tabla `T`, `pose()`) + componente `BPC_AppearLuz_SC` de Mesh 3D (`/Game/SoulCharger/Mechanics/Appear/`).
Reloj = `AppearT` del componente (0..1, 1,5 s; `Vanish` = misma curva al revés). Mis piezas se posan leyendo `AppearT`: **no** llevan tag.

## Reparto
| Pieza | Quién | Cómo |
|---|---|---|
| `Base` (+ ranura, slot 1) | componente | tag `AppearBody`: párpado + `Flash` + `AppearGlow` |
| Trazo `SM_DrawPalette_Trace_SC` | componente | creado en runtime (hijo de la raíz, escala 1), tag `AppearTrace` |
| Cuñas ×8, `Swatch`, `Undo`/`Redo`, `Knob` | Drawing | `AppearPose(T)` en el Tick del arte |
| `Slider` (vidrio) y arco de tinta | Drawing | parámetro `Sweep` en sus materiales |

## Mapeo Blender → Unreal (el espejo de la Y)
- Ángulo de Unreal = −ángulo de Blender. Las cuñas, pares `(Color_k, Brush_k)`, brotan con t0 = 0,52 + 0,018·k y duran 0,24.
- Deshacer/rehacer: la pieza de Unreal **`Redo`** está donde el `Undo` de Blender (166°) → t0 = **0,5934**. `Undo` de Unreal (Blender 194°) → t0 = **0,6094**. Los dos duran 0,24. Calculado invirtiendo H2Pos.
- Giro de pétalo: Blender `R_y(−β)` en el marco de la pieza (X radial, Z arriba) = **pitch +β** en UE (la punta sube). Ala: `R_y(+φ)` = **pitch −φ** (la punta baja).
- La bisagra de la cuña va en el canto interior, sobre la cara: H = (5,67; 0; z_top) en el marco de la malla (cuña a 0°). z_top sale de los bounds de `SM_DrawPalette_Key_SC`.
- Bisagra de deshacer/rehacer: la malla está a 194° de Unreal. H = 21,4·(cos194, sin194) + z_top. El giro va alrededor de la tangente: `Yaw(−194)·Pitch(−φ)·Yaw(194)`. El movimiento radial va por (cos194, sin194).

## Transform por pieza (M en el marco de la malla, antes del Rest)
- `M = T(−H) · [Yaw(−a)·]Pitch(θ)[·Yaw(a)] · Scale(s) · T(H) · T(move)`
- `Rel = Compose(M, Rest)`
- Rest de la cuña: loc `KeyBase[I] + (0,0,CurLift[I]·Lf)`, yaw de tabla (Color −60,−20,20,60; Brush −120,−160,−200,−240), escala 1.
- Rest de deshacer/rehacer: loc `KeyBase[8/9] + (0,0,CurLift)`, yaw `−14 ∓ SideHalf`, escala `SideScale`. Es lo mismo que `ApplySideScale` + `KeyStep`.
- Con t = 1 queda M = identidad y Rel = Rest exacto. Ahí se reactiva `Animate`: `AnimLeft = AnimHold`, y `KeyStep` sigue sin salto.

## Curvas (iguales a Blender)
- **Cuña:**
  - u = seg(t, t0, t0 + 0,24); s = eoc(seg(u, 0, 0,45)); β = 55·(1 − eio(seg(u, 0,2, 1)));
  - Flash = 0,6·(1 − sm(seg(u, 0,15, 0,85)));
  - Lf = eob(seg(t, 0,84, 0,96), 1,2) solo en las elegidas (CurLift > 0).
- **Ala:**
  - u = seg(t, t0, t0 + 0,24); out = eio(seg(u, 0, 0,45)); up = eob(seg(u, 0,35, 1), 0,9); φ = 20·(1 − eio(seg(u, 0,35, 1)));
  - move = radial·(−2,4·(1 − out)) + z·(−3·(1 − up));
  - Flash = 0,6·(1 − sm(seg(u, 0,3, 0,9))).
- **Casquete:** f = eoc(seg(t, 0,50, 0,68)); z = −Sink·(1 − f), con Sink sacado de los bounds; Flash = 1,2·(1 − sm(seg(t, 0,56, 0,78))).
- **Slider:** Sweep = eio(seg(t, 0,68, 0,92)); Head = 2,4·sm(seg(ss, 0, 0,08))·(1 − sm(seg(ss, 0,75, 1))).
  - Máscara por ángulo local (LocalPosition): frac = (133 − atan2d(y, x))/86.
- **Disco:** sigue la cabeza del barrido y se suelta en su grosor.
  - rest = Thickness; f = Sweep·1,06 − 0,03;
  - kf = f < rest − 0,1 ? f : rest − 0,1·exp(−(f − rest + 0,1)/0,1); kf = lerp(kf, rest, sm(seg(t, 0,90, 0,97)));
  - Posición: ángulo Blender 227 + 86·kf → (21,73·cos, −21,73·sin, −1,705).
  - Escala = rest·lerp(0,1; 1; eoc(seg(kf/max(rest; 0,01), 0, 0,5))).
- **Tinta** (aprobado por Beltrán: *"que la tinta aparezca con el barrido del slider"*):
  - `InkSweep` = eio(seg(t, 0,80, 1,00)) sigue al slider.
  - Máscara por UV.x en `InkArcPS`: a *= saturate((InkSweep·1,06 − x)/0,06), con la cabeza del barrido brillante.

## Materiales (parámetros neutros por defecto = idéntico a hoy)
- `M_DrawPalette_SC` (cuerpo, cuñas, alas, disco): `Flash` 0, `FlashColor` (1; 0,72; 0,45). Emisión += FlashColor·Flash.
- `M_DrawPaletteSwatch_SC`: lo mismo.
- `M_DrawPalette_Groove_SC`: `AppearGlow` 1, multiplica la emisión. Lo escribe el componente.
- `M_DrawPalette_Glass_SC`: `Sweep` 1, `Head` 0, `SweepSoft` 0,06.
- `M_DrawPalette_Ink_SC`: `InkSweep` 1.

## Disparo
- `InitArt`: crea el trazo (tag `AppearTrace`), pone el tag `AppearBody` en `Base`, crea `BPC_AppearLuz_SC` en runtime (FaceAxis (0,0,1), PivotDepth −1,64, sonidos) y lo deja OCULTO (AppearT 0).
- Cuando el arte pasa a visible (flanco de `FollowParent`, o el primer cuadro listo) → `Appear()`.
- Director `OutroStep`: en el flanco de `bSystemDone`, `Art.Vanish()`. La paleta ya NO se encoge por escala. Se oculta cuando `OutroT ≥ max(OutroTime, 1,5)`.
- Sonidos: variables del arte `AppearSound`/`VanishSound` (IDs `FX_PALETTEAPPEAR`/`FX_PALETTEVANISH`) → las del componente. Placeholder: `VR_shep_scale_up_02` / `VR_shep_scale_down_02`. El audio definitivo lo pone Beltrán.

## Mano izquierda: textos legibles (Beltrán, 2026-09-30)
*"Cuando vamos a pasar a la mano izquierda, la inversión debería también cambiar los textos para que se puedan leer los textos de undo y redo."*
- Para el zurdo, la paleta se espeja con escala negativa (`PlaceArt`: escala (s, ±s, s); ver `MirrorPalette`). Una malla espejada lleva su textura espejada: UNDO/REDO se leerían al revés, y los íconos de los pinceles también.
- Arreglo en el material, sin tocar mallas:
  - `M_DrawPalette_SC` gana `MaskFlip` (0 = hoy): voltea la UV de la máscara sobre el eje de lectura antes de `MaskRot`.
  - En el reflejo, el sentido tangencial (el de lectura) se invierte y el radial no, así que las cabezas de las letras siguen hacia afuera.
  - El eje exacto (U o V de `LabelUV`) se comprueba con una captura del editor, con la paleta espejada en `Test_DrawPalette`.
- Arte: `MirrorCheck` en `FollowParent` (barato, por flanco). Si el signo de la escala Y del actor en el mundo es < 0, pone `MaskFlip` = 1 en `Brush0..3`, `Undo` y `Redo` (`SetScalarParameterValueOnMaterials`); si no, 0.
- Leer primero `MirrorPalette` del director, por si ya hace algo con las máscaras.
- ⚠ Ojo también con la aparición espejada: mis poses son locales (se espejan solas). El párpado del componente usa `InverseTransformDirection` del dueño; con escala negativa, comprobar que la rendija sigue horizontal.

## A leer en el turno (antes de escribir)
- `BPC_AppearLuz_SC`: cómo se lo deja oculto al inicio, nombres exactos de `Appear`/`Vanish`/`AppearT`/`FaceAxis`/`PivotDepth`/`AppearSound`.
- `BP_DrawPalette_SC`: `ArtTick`, `Animate`, `FollowParent` (el flanco de visibilidad), índices de `CurLift`/`KeyBase` (0-3 Color, 4-7 Brush, 8 Undo, 9 Redo) y cómo se posa el disco.
- Bounds: `SM_DrawPalette_Key_SC`, `SM_DrawPalette_SideKey_SC`, `SM_DrawPalette_Swatch_SC`.
- La salida de emisión de los 4 materiales, para enchufar Flash / Sweep.
