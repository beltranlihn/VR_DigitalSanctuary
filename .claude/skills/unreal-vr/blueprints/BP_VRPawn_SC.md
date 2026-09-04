# BP_VRPawn_SC — el pawn VR de la obra

`/Game/SoulCharger/Core/Pawn/BP_VRPawn_SC` · 🔴 **Asset COMPARTIDO** (`Core/`): coordinar antes de tocarlo.
Anatomía general y recetas VR: [`references/vr-pawn.md`](../references/vr-pawn.md).

## Lo que hace su `Event BeginPlay` (cadena verificada, 2026-08-28)
```
BeginPlay -> Branch -> Sequence -> SetTrackingOrigin(Stage) -> ExecuteConsoleCommand
          -> AddMappingContext -> AddMappingContext -> ArmRecenter   (nuevo)
```
⚠ **No hay `Event Possessed`** — el input se arma en BeginPlay, contra la recomendación de `vr-pawn.md`.
Funciona hoy; anotado por si aparece un bug de input que no se explique.

---

## 2026-08-28 — recentrado automático al arrancar

**Reporte de Beltrán:** *"cuando se reseteó la experiencia, aparecí en cualquier lugar. Debe caer
exactamente en el player start. Quizás fue percepción mía, pero recíbelo."*

**No era percepción.** El pawn hace `SetTrackingOrigin(**Stage**)` — el origen es el centro del Guardian —
y **nunca llamaba a `ResetOrientationAndPosition`**. El nodo existía en el proyecto, pero **colgado de un
botón del menú** (`WBP_Menu.ResetOrientationButton`): o sea que Beltrán ya había necesitado recentrar a
mano alguna vez. Con origen Stage, la cámara queda donde esté el cuerpo del usuario dentro de su espacio
de juego; al recargar el nivel el pawn vuelve al PlayerStart pero **el usuario sigue físicamente donde
estaba**, y después de 15 minutos sentado eso puede ser medio metro.

### El arreglo
| Función | Qué hace |
|---|---|
| **`ArmRecenter()`** | Enganchada al final del `BeginPlay`. Arma un timer de `RecenterDelay`. |
| **`RecenterSeated()`** | `ResetOrientationAndPosition(Yaw 0, OrientationAndPosition)` si `RecenterOnStart`. |

**El retardo no es un lujo**: en el frame del `BeginPlay` la pose del HMD todavía puede no ser válida —
es la receta "Stage + Recenter con Delay" de `vr-pawn.md`.

| Perilla | Valor | Nota |
|---|---|---|
| `RecenterOnStart` | `true` | Sin prefijo `b` **a propósito**: los bools con `b` no se pueden escribir por DSL (§62). |
| `RecenterDelay` | 0,5 s | |

💡 El pawn **se spawnea** (0 colocados en el nivel), así que los valores del CDO mandan — por una vez no
hubo que escribir nada en la instancia.

⬜ **Sin verificar**: esto sólo se juzga con las gafas puestas. Si al recentrar la obra queda girada
respecto de la sala, la perilla a mirar es el `Yaw` del nodo (hoy 0) o pasar el `Options` a sólo `Position`.

---

## 2026-09-02/03 — manos: se probó una malla nueva, se volvió a Manny con material translúcido

### Estado final (lo que corre hoy)
`HandLeft` / `HandRight` usan otra vez **`SKM_MannyXR_left` / `_right`** con
**`ABP_MannequinsXR`**, transforms de fábrica, y **una sola cosa cambiada: el material**.

| | `HandLeft` | `HandRight` |
|---|---|---|
| `SkeletalMeshAsset` | `/Game/XRMannequins/Meshes/SKM_MannyXR_left` | `…/SKM_MannyXR_right` |
| `AnimationMode` / `AnimClass` | `AnimationBlueprint` / `ABP_MannequinsXR_C` | ídem |
| `RelativeLocation` | (−2,98126 · −3,5 · 4,561753) | (−2,98126 · 3,5 · 4,561753) |
| `RelativeRotation` | (−25 · −180 · 90) | (25 · 0 · 90) |
| `RelativeScale3D` | (1 · 1 · 1) | (1 · 1 · 1) |
| `OverrideMaterials` | **`[MI_Hand_SC]`** (antes `MI_Manny_02`) | **`[MI_Hand_SC]`** |

Las animaciones de dedos funcionan porque nunca se tocaron: el graph sigue haciendo
`Get Anim Instance` → `Cast To ABP_MannequinsXR` → `Set` en sus 8 eventos.

### El material: `MI_Hand_SC` (blanco emisivo translúcido) — 🟢 lo que sí quedó
`Core/Pawn/Materials/M_Hand_SC` + su instancia **`MI_Hand_SC`**.
```
shadingModel  MSM_Unlit          Emissive <- HandColor * Brightness
blendMode     BLEND_Translucent  Opacity  <- saturate( Opacity + Fresnel(EdgePower) * EdgeBoost )
twoSided      false
```
El Fresnel va en la **opacidad**, no en el emisivo: por eso el borde se densifica, el centro
queda lechoso y lee como luz en el aire en vez de niebla plana. Parámetros de instancia (se
mueven sin recompilar shaders): `HandColor` (blanco) · `Brightness` (1) · `Opacity` (0,35) ·
`EdgeBoost` (0,65) · `EdgePower` (3).

🔴 **El costo está en el fill rate**: Meta mide ~80% más de GPU por frame que masked, y las manos
delante de la cara llenan mucha pantalla. `twoSided = false` a propósito (activarlo duplica el
overdraw y genera permutación de shader nueva). Plan B si el frame no cierra en el APK:
`BLEND_Masked` con el Fresnel en la máscara, u opaco unlit con Fresnel en el emisivo.
⚠ Al ser translúcidas, las manos **no escriben profundidad**. La ameba en modo HUD sigue por
encima igual (usa Disable Depth Test).

---

## 🔴 El re-skin de la mano nueva: intento FALLIDO, y por qué (para no repetirlo)

Beltrán trajo una mano propia (`hand_final.fbx`, rig de Maya, esqueleto `Hand_Low_Skeleton`).
Como el graph castea a `ABP_MannequinsXR`, la **única** vía sin rehacer nodos era meter esa malla
en `SK_MannequinsXR`. Se intentó por re-skin en Blender headless y **no se logró**: la malla se
deformaba mal en visor ("los dedos se doblan hacia atrás"). Se revirtió.

**Lo que quedó en disco, por si se retoma** (nada de esto está en uso):
- `/Game/SoulCharger/Core/Pawn/Hands/SKM_Hand_L` y `SKM_Hand_R` — el último intento importado.
- `C:\Users\beltr\Desktop\vr-hand\source\` — `hand_final.fbx`, los dos `SKM_MannyXR_*.FBX`
  exportados de Unreal, y los `SKM_Hand_*.fbx` generados.
- `C:\Users\beltr\Desktop\vr-hand\ajuste_manos.blend` — la mano encajada globalmente contra la
  de Manny en alambre, **lista para posar a mano** (Pose Mode, sólo rotar).
- [`scripts/reskin_to_skeleton.py`](../scripts/reskin_to_skeleton.py) — el pipeline completo.
- Basura del import en la raíz de `/Game`: `Hand_Low`, `Hand_Low1`, sus dos esqueletos, dos
  physics assets, `hand_finalTake_001/0011`, `aiStandardSurface1`, `blinn1`, `lambert1_*`.

### Las cuatro lecciones, que son de método y valen más que el intento
1. **La geometría se puede encajar con precisión numérica y aun así deformar mal.** Los 20 puntos
   quedaron a **0,0 mm** de las articulaciones de Manny y la pose de reposo se superponía casi
   exacta — y las animaciones igual salían quebradas. **Que los números cierren no prueba que
   deforme bien.** Lo único que lo prueba es flexionar los dedos y mirar.
2. **La causa de fondo, encontrada tarde: el GIRO sobre el eje del hueso.** `rotation_difference`
   da la rotación mínima entre dos direcciones y **no controla la torsión**. Con la carne del dedo
   torcida, los pliegues del nudillo quedan del lado del dorso: se ve exactamente como
   "se dobla hacia atrás". El arreglo es construir un **marco ortonormal completo** por hueso
   (X = eje del hueso, Y = normal de la palma proyectada) y mapear marco a marco. Quedó
   implementado en el script pero **sin verificar**.
3. **Trasladar huesos desgarra la malla; estirarlos no.** Forzar cada articulación con una
   traslación deja un quiebre visible en cada nudillo. Y ojo: **`pose_bone.matrix` ignora la
   escala al asignarse**, y `pb.scale.y` tampoco propaga en este rig — la salida fue hacer el
   skinning a mano (mezclar las transformaciones por peso), que además sale continuo.
4. 🔴 **En Unreal NO se puede editar la pose de reposo de un skeletal mesh.** No existe el panel.
   Lo más cercano es *Edit Retarget Pose* del IK Retargeter, que corrige **animaciones**, no la
   malla. Esa pose se edita en el DCC. Vale saberlo antes de prometer un camino que no existe.

### ⬜ Si se retoma
El camino sigue siendo el re-skin (es el único que deja el graph intacto), pero **con la torsión
resuelta y verificado con una prueba de flexión** —los dedos doblados, la malla nueva al lado de
la de Manny, mirando— **antes** de importar nada a Unreal.
