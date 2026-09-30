# BPC_AppearLuz_SC — la aparición "luz primero", portable (Mechanics/Appear/)

- **Estado**: 🟢 compila y guardado (2026-09-30, Tick corregido) · 🟢 PIE dentro de la paleta (Drawing) · 🟢 **Simulate en `Mechanics/Appear/Test_Appear`** con timbre, SAVE y sensor en `Demo`. Las capturas (`ClaudeScripts/Appear/sim_sheet.png`) muestran trazo → rendija → párpado → enfriado → pieza que asoma → luces · ⬜ visor: el párpado de canto necesita la cámara del jugador; en Simulate toma la del editor.
- **Propósito**: reemplazar la "escala de 0 a 1" por la aparición aprobada por Beltrán (ver `blender-3d/assets/aparicion-luz.md` y los GIF). Cumple tres cosas:
  - **Entrada** `Appear()` de 1,5 s y **salida** `Vanish()`, que es la misma curva al revés.
  - Un solo componente sirve para cualquier actor de arte: timbre, SAVE MELODY, sensor, la base de la paleta y el HUD.
  - **Relativo a los transforms VIVOS** (condición de Drawing): captura el `GetRelativeTransform` de cada pieza al empezar y anima sobre eso.

## Contrato
| | |
|---|---|
| Llamadas | `Appear()` · `Vanish()` (eventos custom). |
| Reloj | `AppearT` (float público 0..1): parte en **1** (visible), sube con Appear y baja con Vanish. `Dir` ±1 · `Playing`. |
| Eventos | `OnAppeared` · `OnVanished` (dispatchers). |
| Sonido | `AppearSound` / `VanishSound` (SoundBase, instance-editable). IDs del prototipo: FX_BELLAPPEAR/VANISH, FX_PALETTEAPPEAR/VANISH, FX_SENSORAPPEAR/VANISH, FX_RINGAPPEAR, FX_HUDBIRTH/VANISH. Los pone Beltrán. |
| Qué toca | **Solo** los MeshComponent del dueño con tag (vía `GetComponentsByTag`). |

## Tags y qué les hace
- **`AppearBody`**, el cuerpo:
  - nace como **rendija** de canto a la vista, se abre como **párpado** y toma espesor;
  - escalares `Flash` (1 → 0, el enfriado) y `AppearGlow` (relevo de la ranura, con una exhalación al final).
- **`AppearMover`**, la pieza que asoma:
  - viaja de `MoverHide` a su lugar con `ease_out_back(1,2)` y el clac;
  - `Flash` (0,35 → 0) y `AppearGlow` (la punta del sensor: se enciende con un destello).
- **`AppearTrace`**: el trazo de luz (`M_AppearTrace_SC`), con `Sweep`, `Head` y `Glow`. Se oculta cuando está apagado o si `NoTrace`.
- **`AppearLate`**: `AppearGlow` de 0,80 a 1,00 (las ondas del sensor).

## Variables de configuración (instance-editable; TODAS en la categoría *Default*, ver trampas)
- `Duration` 1,5.
- `NoTrace`: sin trazo, como en el anillo. El cuerpo usa τ = 0,24 + 0,76·t: la rendija arranca en t = 0 y todo termina exacto en 1.
- `FaceAxis` (0,0,1): la normal de la cara, en el marco del dueño. El sensor usa (0,0,−1).
- `PivotDepth` (cm sobre FaceAxis): el plano de la ranura.
- `MoverHide` (cm, marco del padre): desde dónde asoma la pieza móvil.
- `AppearOnBegin`: nace al empezar.
- `Demo`: entra y sale en bucle (1,2 s de reposo), para el nivel de prueba.

## Grafos
- **`Capture`**: vacía los arreglos, junta por tag (cast a MeshComponent) y guarda los `GetRelativeTransform`. Después llama a `CaptureEye`.
- **`CaptureEye`**: el párpado, calculado **en el marco del dueño**.
  - Toma la cámara de `GetPlayerCameraManager(0)` y su vector derecha, y los pasa al marco con `InverseTransformLocation/Direction` del `GetActorTransform` del owner.
  - `Ax` = derecha proyectada en el plano de la cara.
  - `n'` = Ax × (ojo − pivote), del lado de n.
  - `Th` = atan2((n × n')·Ax, n·n'), en grados.
  - `Pv` = FaceAxis · PivotDepth.
- **`ApplyT(Tin)`**: toda la coreografía, con los **mismos números** que `blender-3d/scripts/anim_luz_objects.py`.
  - Se genera con `scripts/appear_luz_applyt_dsl.py`; si cambian los tiempos, se regenera y se escribe en un grafo **vacío**.
  - Cuerpo: `SetRelativeTransform(Compose(Rest, T(−Pv)·[Rot(Ax, Th·(1−o)) · Scale(sx en el plano, sz en la normal)]·T(Pv)))`.
  - La escala en el plano es pareja, así que el giro de las piezas alrededor de la normal no produce cizalla.
- **EventGraph**:
  - `BeginPlay`: si `AppearOnBegin`, captura y arranca desde 0.
  - `Appear`: si nunca capturó, captura; si está oculto, recalcula solo la cámara.
  - `Vanish`: si está en reposo, recaptura.
  - `Tick`: avanza `AppearT`, aplica y al llegar dispara el dispatcher. En reposo, con `Demo`, alterna.

## Trampas de esta construcción
- `SetScalarParameterValueOnMaterials` es de **MeshComponent**: los arreglos de `PrimitiveComponent` no conectan ("Could not connect pin Array Element to self").
- En el DSL, `Find` es `Utilities|Array|FindItem`. Un `get_node_type_pins` **crea nodos** en el grafo que se le pasa: después hay que borrarlos.
- El `write_graph_dsl` que falla no deja nodos (medido 2 veces), pero conviene contar con `find_nodes` antes de reescribir.
- 🔴 **Ponerle CATEGORÍA a una variable cambia el `type_id` de sus Get/Set en el DSL.** `find_node_types` los sigue listando como `Variables|Default|SetDir`, pero `write` falla con *"does not exist"*. Todas volvieron a *Default* y ahí el `write` anduvo. Los grafos ya escritos siguen funcionando: el nodo apunta a la variable por nombre.
- 🔴 **El `bind` no es una asignación** ([[bind-del-dsl-no-es-asignacion]]). El primer Tick calculaba `nt` con nodos puros, hacía `SetAppearT(nt)` y después `ApplyT(nt)`: `nt` se reevaluaba con el `AppearT` ya actualizado y avanzaba **dos pasos por cuadro**. Arreglo: `SetAppearT(...)` y después `ApplyT(GetAppearT)`, y los finales comparan con `GetAppearT`.
- `AppearOnBegin` es `Variables|Default|GetAppearonBegin`: la `O` se escribe minúscula.

## Dónde se usa
- `BP_ResultsArt_SC` (el cuadro de resultados): `FaceAxis` (1,0,0), `PivotDepth` 0, **`Duration` 2,0**, sonidos `SBubbleHoverOn/Out` SOLO en ese componente (la clase sigue sin sonido por defecto).
- `BP_BellArt_SC`: `PivotDepth` 4,41, `MoverHide` (0,0,−1,9); el bolsillo destella en Blender, acá todavía no.
- `BP_SaveMelodyArt_SC`: 1,5 y (0,0,−1,2).
- `BP_BioSensorArt_SC`: `FaceAxis` (0,0,−1), 0,608 y (0,0,1,7); las ondas llevan tag `AppearLate`.
- **Paleta (Drawing)**: tag `AppearBody` en la base y `AppearTrace` en `SM_DrawPalette_Trace_SC`; `FaceAxis` (0,0,1), `PivotDepth` −1,64. Cuñas, casquete, undo/redo, slider y disco los posa Drawing leyendo `AppearT`.

## Nivel de prueba `Mechanics/Appear/Test_Appear`
- Es una copia de `Test_QuestCtrl`: sin luces, con `BP_XRGameMode`, los 4 mandos y la paleta.
- Timbre en (90, −42, 160) con pitch 90; SAVE en (70, 2, 160) con yaw 90 y roll 90 (el texto se lee derecho); sensor en (70, 32, 160) con pitch −90. Los tres miran al PlayerStart.
- `Appear.Demo` = true en las tres instancias.
- Para verlo sin visor: `StartPIE {bSimulate: true, playMode: "PlayMode_Simulate"}` + `CaptureViewport` en ráfaga desde la cámara (−20, −3, 160).

## v2 (2026-09-30, turno de Mesh 3D; regla de carga de Narrativa)
- **Tick con `Dt = min(DeltaSeconds, 0,0333)`**: un nodo `Min(Float)` entre `DeltaSeconds` y sus dos consumidores (el avance de `AppearT` y la espera del `Demo`). Un cuadro trabado después de una carga frena la animación un instante en vez de comérsela entera.
- **`Prepare()` blindado**: solo recaptura el reposo si nunca capturó (`Bodies` vacío) o si está EN REPOSO (`AppearT` ≥ 0,999); si no, solo refresca la cámara (`CaptureEye`).
  - La v1 capturaba siempre. Un segundo `Prepare` con la pieza oculta tomaba la rendija como reposo y el marco no volvía a aparecer: el HUD con `AppearOnPlay` + `HUDHideNow`.
  - DSL en `scripts/results_entry_dsl.py` (`PREPARE_V2`), escrito sobre el grafo vaciado (se conserva el `FunctionEntry`).
- Compilado y guardado; `.uasset` escrito a las 06:35.

## `Prepare()` (2026-09-30, para el HUD)
- Captura el reposo, pone AppearT 0, Playing false y Dir 1, y hace `ApplyT(0)`: deja todo OCULTO y listo para `Appear()`.
- Llamarla con las piezas **en reposo** (típicamente en BeginPlay).
- ⚠ Desde otro BP, `Class|BPCAppearLuzSC|SetAppearT comp 0` **no conecta** en el DSL: el primer argumento posicional va al valor, no al target. Por eso existe `Prepare`.
