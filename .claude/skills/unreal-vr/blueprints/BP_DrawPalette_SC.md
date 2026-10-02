# BP_DrawPalette_SC — la paleta nueva de la etapa de dibujo (Mechanics/Draw/)

## Purpose
La paleta física que modeló la sesión Mesh 3D (plano de Beltrán, 2026-09-29; modelo: `blender-3d/assets/draw-palette.md`). **Solo arte + estado visual**: la interacción (puntero, gatillo, qué pincel/color se elige, undo/redo, grosor) la pone la sesión **Drawing**, que la reemplaza por la paleta vieja (`BP_TBPalette`, ProceduralMesh).

## Status
🟢 Compila; colocada en `Mechanics/Draw/Test_DrawPalette` (sin luz direccional, GameMode `BP_XRGameMode`). Capturas del editor OK. 🟢 **Integrada por Drawing** (2026-09-29, ver abajo): interacción verificada en PIE con punta virtual. ⬜ Visor.

## Componentes (StaticMesh, sin colisión, sin sombras; todas las mallas con el ORIGEN EN EL CENTRO de la paleta)
| Componente | Malla | Material | Yaw |
|---|---|---|---|
| `Base` | `SM_DrawPalette_Base_SC` (slot 0 cuerpo, slot 1 ranura) | `MI_DrawPalette_Body_SC` / `M_DrawPalette_Groove_SC` | 0 |
| `Swatch` | `_Swatch_SC` (casquete central) | **`MI_DrawPalette_SwatchTex_SC`** (`M_DrawPaletteSwatch_SC`, desde 2026-09-29; override de la plantilla): color elegido + textura/relieve del pincel elegido. `MI_DrawPalette_Swatch_SC` quedó sin uso | 0 |
| `Color0..3` | `_Key_SC` | `MI_DrawPalette_Color_0..3_SC` (terracota, ocre, salvia, azul) | −60, −20, 20, 60 |
| `Brush0..3` | `_Key_SC` | `MI_DrawPalette_Brush_{TaperedMarker,OilPaint,Light,WetPaint}_SC` (= BrushIds [0,5,3,6], iconos `T_Ico_0/5/3/6`) | −120, −160, −200, −240 |
| `Redo` (ARRIBA) / `Undo` (ABAJO) | `_SideKey_SC` | `MI_DrawPalette_Redo/Undo_SC` (texto `T_DrawPalette_Redo/Undo`) | 0 / −28 |
| `Slider` | `_Slider_SC` (banda plana) | `M_DrawPalette_Glass_SC` (translúcido, `Opacity` 0,35) | 0 |
| `Knob` | `_Knob_SC` (disco, origen en SU centro) | `MI_DrawPalette_Knob_SC` | 0 |
Yaw = −(ángulo en Blender): Unreal espeja la Y. Orientación de uso: la paleta mira a +Z; en `Test_DrawPalette` está a `Yaw 90, Roll 50` frente al PlayerStart (colores a la derecha, undo/redo a la izquierda, slider abajo — como el plano).

## Variables (cat. *Palette*, instance-editable, se previsualizan en el editor)
`SelectedColor` (0..3, def 1) · `SelectedBrush` (0..3, def 1) · `Thickness` (0..1, def 0,5) · `KeyLift` (0,66 cm = lo que sube la seleccionada) · `KnobScaleMin/Max` (0,5 / 1,6).

## Función `ApplyState` (la llama el Construction Script; la mecánica la vuelve a llamar después de cambiar las variables)
- Sube `KeyLift` la cuña de color y la de pincel seleccionadas (las demás a 0).
- Disco: sobre el arco del slider, `ángulo = 227° + 86°·Thickness` (plano; izquierda = fino), `pos = (21,73·cos a, −21,73·sin a, −1,705)` cm; escala `lerp(KnobScaleMin, KnobScaleMax, Thickness)` (izquierda chico, derecha grande).
- Casquete: `SetVectorParameterValueOnMaterials("BaseColor")` con el color elegido (4 literales = los de las MI de color).

## Materiales (`M_DrawPalette_SC`, unlit, HLSL `unreal-vr/scripts/hlsl/DrawPaletteShadePS.hlsl`)
Nivel **sin luz direccional** → emisión propia + **sombreado falso**: luz principal fija en el mundo (`LightDir`, `Wrap`), relleno desde la vista (`Fill`), hemisferio (`Ambient`), `SelfGlow`; hormigón mate con manchado + grano. Máscara por UV1 (`IconUV` en la cuña / `LabelUV` en la lateral): `MaskTex`, `MaskRot` (grados), `MaskScale`, tinta `Ink` blanca + `InkGlow`. 🔴 El giro en Unreal es el **opuesto** al de Blender (V invertida al importar): íconos a lo largo de la cuña = `MaskRot 45`, `MaskScale 1,3`.

## Para Drawing (integración)
- Elegir: setear `SelectedColor` / `SelectedBrush` / `Thickness` y llamar `ApplyState`.
- Selección por puntero: los centros de las cuñas están a r ≈ 10,2 cm del centro, a los yaw de la tabla; undo/redo a r ≈ 23 cm (yaw 0 / −28 respecto del ángulo 166° del plano); el slider es el arco r 21,7 cm entre 227° y 313° del plano. Si hace falta colisión, las mallas no la tienen (`remove_collisions`): generarla o usar distancias.

## 🟢 INTEGRADA por Drawing (2026-09-29) — la usa `BP_TBPalette` (`/Game/SoulCharger/Mechanics/Draw/TB/`)
La lógica (qué se toca, qué se elige) vive en `BP_TBPalette`; este BP sigue siendo **solo arte + estado visual**, ahora animado. Detalle de la interacción: `BP_TBStroke.md` §5u.

**Cambios de Drawing en este BP y sus materiales** (Mesh 3D: no pisar sin avisar):
- **Casquete con la textura del pincel**: material nuevo **`M_DrawPaletteSwatch_SC`** (duplicado de `M_DrawPalette_SC`: mismo sombreado de hormigón; UV0; la máscara es el **alfa** de la textura del pincel `BrushTex`, una fila del atlas con `AtlasRows`; pintura = `BaseColor` con brillo `InkGlow`, lecho = `Ink`). Fuente: `scripts/hlsl/DrawPaletteSwatchPS.hlsl`. Instancia nueva **`MI_DrawPalette_SwatchTex_SC`** (SelfGlow 0,3, Ink 0,34/0,31/0,27) en `OverrideMaterials` de la plantilla `Swatch`. `MI_DrawPalette_Swatch_SC` quedó **sin uso** (no se reasignó su padre: eso crasheó el editor, gotcha 504).
- Variables nuevas: `Anim` (SelGlow 0,35 · HoverGlow 0,15 · BaseGlow 0,15 · HoverLift 0,3 · PressDepth 0,8 · PressGlow 0,7 · PulseTime 0,35 · AnimRate 14 · AnimHold 1 · BaseInk 0,55 · InkBoost 1,5) · `Estado` (HoverColor/HoverBrush −1, HoverUndo/HoverRedo/HoverSlider, UndoPulse/RedoPulse) · `Swatch` (KeyColors[4], SwatchTex[4] = T_TB_TaperedMarker/OilPaint_Base/Light/WetPaint_Base, SwatchRows [1,4,1,4]) · `Z-Interno`.
- Funciones nuevas: `InitArt` (BeginPlay → `ApplyColors`), `ApplyColors` (KeyColors → `BaseColor` de Color0..3), `FollowParent` + `ArtTick` + `Animate` + `KeyStep` + `SwatchStep` (Tick). El Construction Script (`ApplyState`) no se tocó.
- **Animación**: cada tecla va suave (FInterp manual, `AnimRate`) a su objetivo: seleccionada sube `KeyLift` y brilla `+SelGlow`; con la punta encima, `+HoverLift` y `+HoverGlow`; undo/redo al dispararse se **hunden** `PressDepth` y destellan `PressGlow` durante `PulseTime`. El brillo sube `SelfGlow` y también `InkGlow` (el ícono/texto se ilumina). El disco del slider sigue el grosor (posición y escala) y brilla con la punta encima. El casquete toma el color elegido y la textura del pincel elegido.
- **Costo**: solo anima durante `AnimHold` (1 s) después de un cambio de estado (firma `PrevSig`) o mientras hay pulso; en reposo el Tick no escribe nada.
- **Visibilidad**: `FollowParent` la esconde cuando el actor padre (la paleta lógica) **no tickea** — el director apaga el Tick de la paleta justo cuando la oculta (TourSleep y fin del sistema). `bHidden` de otro actor no se puede leer desde BP (el getter del DSL es solo de self).

### v2 (2026-09-29, primera vuelta de Beltrán en visor): mate, casquete entero y 60 %
- **Mate** (overrides en las MI, sin tocar el maestro): Ambient 0,14 · Diffuse 0,38 · Fill 0,06 · SelfGlow 0 en Body, Brush×4,
  Undo, Redo y Color×4 (antes, por defecto: 0,35 / 0,75 / 0,25 / 0,15 → el cuerpo llegaba casi a blanco). Pinceles, Undo y
  Redo con `BaseColor` más oscuro (0,40/0,37/0,33) para que los íconos y textos blancos se lean. Color×4 con Grain 0,14 y
  Mottle 0,2. Knob SelfGlow 0,1. La ranura (`M_DrawPalette_Groove_SC`) sigue emisiva (GrooveGlow 1).
- En el BP: `BaseGlow` 0 (lo no elegido no brilla), `SelGlow` 0,28, `HoverGlow` 0,12, `InkBoost` 1,2, `PressGlow` 0,6,
  `KeyLift` 0,9, `HoverLift` 0,35 y **`KeyColorGain` 0,7**: las teclas y el casquete muestran el color del dibujo × 0,7 (el
  trazo sigue con el color completo).
- **Casquete v2** (`DrawPaletteSwatchPS` v2 + `DrawPaletteSwatchUV` v2): se pinta **entero** con el color; la textura solo da el
  carácter. UV = el INTERIOR del trazo (U 0,12–0,62, V 0,22–0,78 de la fila). Sampler nuevo **`BrushBump`** (Normal) + `BumpAmt`:
  relieve de las cerdas en OilPaint/WetPaint (su `_N`, canal R, ×0,4 — el mismo relieve falso que `M_TB_Paint`); Light usa el
  alfa del interior (veladura); el marcador queda liso. Por pincel en el BP: `SwatchBump[4]`, `SwatchBumpAmt` [0; 0,4; 0; 0,4].
  (Medido en las PNG: el alfa del interior de OilPaint/WetPaint es casi plano, 0,94 ± 0,02; el carácter está en el `_N`.)
- **Deshacer/Rehacer conservan su tamaño** cuando la paleta se achica: `SideCheck` (en `FollowParent`, cada cuadro, barato)
  lee la escala RELATIVA del actor (la que pone `BP_TBPalette` con `ArtScale`) y, si cambió, `ApplySideScale`: escala
  Undo/Redo × 1/escala y los corre hacia el centro 19,6·(S−1) por su dirección (±166°) para que sigan pegados al borde
  (`KeyBase[8..9]`, que `KeyStep` suma a la elevación). La escala del padre (el encogido del cierre) no la dispara.
- **`SideSize`** (Anim, 0,8; pedido de Beltrán: *"achica los undo redo al 80 %"*): tamaño REAL de deshacer/rehacer respecto del
  modelado. `SideCheck` usa escala = `SideSize` / escala relativa de la paleta (hoy 0,8 / 0,6 = 1,333) y los mantiene pegados
  al borde. La zona de toque de `BP_TBPalette.ArtSense` se calcula cada cuadro con la escala real del componente `Undo`
  (radio 19,6 + 5,8·S, ±atan2(5·S, 19,6 + 2,7·S)) → cambiar `SideSize` basta, no hay que tocar la lógica.

### v3 (2026-09-30): teclas de color más claras y aro con los colores del mundo
Beltrán, con la paleta de trazos "A · niebla y agua" cargada: *"en la paleta física debieran verse más brillantes, quedan muy oscuros"* y *"la luz del aro, que sea más de los colores del mundo"*.

- **Teclas de color, solo `MI_DrawPalette_Color_0..3_SC`:** Ambient 0,30 · Diffuse 0,60 · Fill 0,12. Antes 0,14 / 0,38 / 0,06, de la v2.
- **`KeyColorGain` 1,0**, antes 0,7, en el CDO **y en la plantilla del actor hijo** `BP_TBPalette:ArtAnchor_GEN_VARIABLE.ArtAnchor_GEN_VARIABLE_BP_DrawPalette_SC_C_CAT`.
  - 🔴 La plantilla NO sigue al CDO: seguía en 0,7. Hay que tocar las dos.
- Una tecla mostraba ~25 % de su color en la cara iluminada; ahora ~65 %. La v1 "brillantísima" estaba en ~100 %.
- El casquete también sube, porque usa el mismo `KeyColorGain`. Pinceles, cuerpo y undo/redo quedan igual.
- **Aro (ranura):** `M_DrawPalette_Groove_SC.GrooveColor` pasa de (1; 0,72; 0,42), ámbar, a **(0,36; 0,76; 0,66)**, un aguamarina de la familia del nivel (tono ~160°). `GrooveGlow` sigue en 1.
- Verificado en PIE: el arte usa `KeyColorGain` 1 y los `KeyColors` de la paleta A.
- **v3b (mismo día):** Beltrán: *"el aro quedó muy celeste, un poco más verdoso agua y menos saturado"*. `GrooveColor` = (0,342; 0,571; 0,456) lineal = #9EC7B4 (tono 152°, saturación 0,27). Antes #A2E2D4 (167° / 0,52).

### v4 (2026-09-30): deshacer y rehacer se abren según su tamaño
Beltrán: *"los botones undo y redo se están superponiendo; rotar cada uno respecto del centro de la paleta para que queden justo separados"*.
- **Causa:** con la paleta chica, `SideScale` = `SideSize` / escala de la paleta (0,65 / 0,464 = 1,40) agranda las teclas, pero la separación seguía fija en ±14°.
  - Modelado (`draw-palette.md`): cada tecla ocupa ±12° y quedan 2° de aire a cada lado de la línea media.
  - Agrandadas y corridas al borde, cada una ocupa ±16,7° → se tapaban.
- **`ApplySideScale` reescrita.** Calcula
  `SideHalf = atan2d(0,2079·S, 1 − 0,0219·S) + SideGap`
  = el medio ancho angular real del borde interno (r 19,6) de la tecla escalada y corrida, más el aire.
  - Undo: yaw `−14 − SideHalf`. Redo: yaw `−14 + SideHalf`. Los dos giran alrededor del centro de la paleta.
  - Corrimiento `KeyBase[8/9]` = 19,6·(S−1)·(cos, ∓sin) de `SideHalf`.
  - Con S = 1 da exactamente lo modelado: 14°, yaw −28 / 0.
- Perilla **`SideGap`** (Anim, 2°: el aire del modelado) y **`SideHalf`** (Z-Interno, calculada).
  - 🔴 En la plantilla del actor hijo también (`BP_TBPalette:ArtAnchor_GEN_VARIABLE…_CAT`): la plantilla nació en 0.
- **`BP_TBPalette.ArtSense`:** la zona de toque de undo/redo usa `180 − Art.SideHalf` en vez de la variable fija `SideAng` (166), que queda sin uso.
- Verificado en PIE: S 1,40 → `SideHalf` 18,72; Undo yaw −32,72; Redo +4,72; toque ±16,7° alrededor de ±161,3°. Sin errores. ⬜ Visto por Beltrán.
- 🔴 Al cablear `ArtSense` rompí el slider de grosor (gotcha 510): un `connect_pins` con el id equivocado reemplazó su `SliderRMax` por `SideHalfAng`. Beltrán lo vio ("dejó de funcionar el selector de tamaño"). Se reconectó, y se verificó con la punta de depuración: slider, deshacer y rehacer responden cada uno en su zona.

### v5 (2026-09-30): el MEDIDOR DE TINTA en el arco libre
Beltrán: *"en la circunferencia exterior entre el slider de tamaño y el botón redo, un radial slider que marque cuánta tinta nos queda; una variable de metros lineales que disminuye al dibujar; al llegar al final activa save drawing. Con eso marcamos el largo de la etapa"* y *"verde pastel, medio translúcido"*.
- **Arco:** `ProceduralMeshComponent` creado en runtime por `InkEnsure` (como el halo; no pasa por la plantilla).
  - `InkGeom` arma una banda de `InkSegs` (64) segmentos, con el mismo radio que el slider de grosor (r 21,4–22,06) y z −1,6.
  - Va desde el slider (46,1° − `InkGap`) hasta rehacer (−180 + 2·`SideHalf` − `SideGap` + `InkGap`), así se adapta a la apertura de deshacer/rehacer. Hoy son ≈ 40° → −138,6°.
  - `InitArt` → `InkBuild`. `ApplySideScale` → `InkGeom` al final.
  - `InkSet(L)` guarda `InkLevel` y escribe `Fill` con `SetScalarParameterValueOnMaterials`.
- **Material `M_DrawPalette_Ink_SC`** (Unlit, Translucent, TwoSided; HLSL `scripts/hlsl/InkArcPS.hlsl`):
  - UV.x 0 = junto al slider → 1 = junto a rehacer. Se llena desde 0 hasta `Fill`.
  - `Color` = `TrackColor` (0,39; 0,79; 0,48), verde pastel. `FillAlpha` 0,55 · `TrackAlpha` 0,15 (el tramo gastado queda como vidrio tenue) · `HeadGlow` 0,5 (la cabeza del nivel brilla) · `Soft` 0,012.
  - El aspecto se ajusta en los defaults del material.
- Perillas (cat. *Tinta*): `InkGap` 6° · `InkSegs` 64 · `InkLevel` (lo escribe el director). También en la plantilla del actor hijo de `BP_TBPalette`.
- La lógica vive en el director (`BP_TBStroke.md` §5ad).
### v6 (2026-09-30): APARICIÓN "luz primero" + textos legibles para zurdo
Beltrán: *"aplica la animación"* (la aprobada en Blender, `blender-3d/assets/aparicion-luz.md`), *"que la tinta aparezca con el barrido del slider"* y *"al pasar a la mano izquierda, la inversión debería cambiar los textos para que se lean undo y redo"*. Plan y números: `scripts/tb_appear_plan.md`.
- **Reloj = `BPC_AppearLuz_SC`** (Mesh 3D), creado en runtime por `AppearEnsure`.
  - Parámetros: FaceAxis (0,0,1), PivotDepth −1,64, `AppearSound`/`VanishSound` del arte, que en el prototipo web son `FX_PALETTEAPPEAR`/`FX_PALETTEVANISH`. De relleno: `VR_shep_scale_up_02`/`down_02`.
  - Anima lo que tiene tag: `Base` (`AppearBody`: párpado, `Flash`, `AppearGlow` de la ranura) y el trazo `SM_DrawPalette_Trace_SC` (`AppearTrace`, hijo de `DefaultSceneRoot`, escala 1). Los tags se ponen en runtime con `AddUnique(GetComponentTags)`.
- **Mis piezas se posan leyendo `AppearT`** (`AppearPoseStep` después de `ArtTick`: solo cuando `AppearT` cambia) → `AppearPose(T)`:
  - `PetalPose`: 4 pares Color/Brush, t0 = 0,52 + 0,018·k, duración 0,24. Brotan escalando desde la bisagra interior (5,6557; 0; 0) y bajan de pitch 55° a 0. Las elegidas suben con `ease_out_back(1,2)` a 0,84–0,96. Además `CurLift[I]` = pose, así `KeyStep` sigue sin salto.
  - `WingPose`: Redo t0 = 0,5934, Undo t0 = 0,6094 (**el espejo de la Y: el Redo de Unreal está donde el Undo de Blender**). Cajón −2,4 cm radial y −3 cm en z; despliegue de 20° alrededor de la tangente de la malla (a 194°); bisagra (−19,018; −4,742; −0,975). El reposo = `ApplySideScale` (yaw −14 ∓ SideHalf, escala SideScale).
  - `SwatchPose`: sube 1,1 cm desde el pozo con `Flash`.
  - `LatePose`: el vidrio del slider con `Sweep`/`Head` (0,68–0,92); el disco viaja en la cabeza del barrido y se suelta en su grosor; la tinta aparece con `InkSweep` (0,80–1,00).
  - En T = 1 todo cae EXACTO en su reposo. Medido: Color0 yaw −60 y z 0,9; Undo/Redo −32,72/+4,72 a escala 1,40; disco en (−5,48; 21,02) a escala 0,863. En ese momento `AnimLeft` = `AnimHold`.
- **Disparo:** `FollowParent` → `AppearGate(tick del padre)`. Al encenderse la paleta → `Appear()`; al apagarse (cierre, `TourSleep`) → `Vanish()`, y se oculta recién cuando `AppearT` llega a 0. Director: `OutroStep` ya NO encoge la paleta por escala (`Select_5` opción 1 = escala actual).
  - ✅ PIE: la entrada termina en reposo. La salida (tinta 1 m + sintético): `AppearT` 0,68 bajando en pleno cierre, después 0 y el arte oculto. Paleta sin encogerse. Sin errores nuevos.
- **Materiales** (neutros por defecto):
  - `M_DrawPalette_SC` y `M_DrawPaletteSwatch_SC`: emisión += `FlashColor`·`Flash`.
  - `M_DrawPalette_Groove_SC`: × `AppearGlow` (1).
  - `M_DrawPalette_Glass_SC`: Custom `GlassSweepPS` con frac = (133 − ángulo local)/86 → opacidad × máscara + cabeza cálida.
  - `M_DrawPalette_Ink_SC`: Custom `InkRevealPS` → opacidad × revelado.
- **Zurdo:**
  - `M_DrawPalette_SC` ganó `MaskFlip` (Custom `MaskFlipUV` antes de `DrawPaletteMaskUV`): U → 1 − U. En `LabelUV` e `IconUV`, U es el sentido de lectura (tangencial); el espejo lo invierte y deja el radial.
  - `MirrorCheck` (en `FollowParent`): espejado = el producto de las escalas del actor es < 0. El signo de Y solo no alcanza: Unreal puede pasar el negativo a otro eje al componer. Cuando cambia, pone `MaskFlip` en Brush0..3, Undo y Redo.
  - ✅ Diestro: `bMirror` false. ⬜ Zurdo en el visor.
- ⬜ Visor: el aspecto de la aparición (el párpado de canto a la cámara, el sentido de giro de pétalos y alas), el sonido y los textos para zurdo.
- **v6b — espera antes de aparecer.** Beltrán: *"puse play y no sucedió ninguna animación; dale una espera de 3 segundos antes de que suceda"*.
  - Causa: corría en el primer instante del Play, cuando la paleta se enciende, antes de que él mirara.
  - `AppearGate` ahora acumula `WantT` (con `GetWorldDeltaSeconds`) mientras el padre tickea. Aparece recién cuando `WantT ≥ AppearDelay`.
  - Mientras espera, el arte queda OCULTO: hidden = no deseado Y el componente sin `Playing`.
  - La espera vale cada vez que la paleta se enciende (también al despertar en el recorrido).
  - Perillas (Aparicion, en la plantilla de `BP_TBPalette` y en el CDO): `AppearDelay` 3 s · `bAppearDemo` false (lo pasa a `Demo` del componente: aparece y desaparece en bucle, para evaluar).
  - ✅ PIE: a los 2,29 s oculta y sin empezar; a los 3,15 s `AppearT` 0,11 corriendo; después reposo exacto.
- **v5b (mismo día):** Beltrán: *"se debe notar más el contraste entre la cantidad de carga de tinta"*. Nuevos defaults del material: `FillAlpha` 0,55 → 0,85 · `TrackAlpha` 0,15 → 0,06 · `TrackColor` → (0,20; 0,32; 0,25), apagado · `Glow` 1,0 → 1,4 · `HeadGlow` 0,5 → 0,9. ⬜ Visor.
- ✅ **Validada por Beltrán en VR Preview (2026-09-30):** *"Funciona. Todo correcto. Damos por guardado esta etapa."* ⬜ Zurdo (`MaskFlip`) y APK.
