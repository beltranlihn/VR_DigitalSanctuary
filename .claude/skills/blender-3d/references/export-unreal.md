# Export Blender → Unreal 5.8 — checklist completo (mallas estáticas)

Para los assets de Soul Charger: mallas **estáticas** (la obra no tiene skeletal meshes propios hoy; si aparece uno, ampliar esta guía — las reglas cambian). El destino es `VR_Test/Content/SoulCharger/` vía import FBX (Interchange).

## 0. Antes de exportar (en Blender)

| Paso | Detalle |
|---|---|
| **Unidades** | Scene Properties → Units: **métrico, Unit Scale 1.0** (metros). 1 m en Blender = 100 uu en Unreal; la conversión la hace el exporter con Apply Unit. |
| **Transforms aplicados** | `Ctrl+A → All Transforms` (o `transform_apply` por script). Escala ≠ 1 o rotación residual = el clásico asset 100× más chico/grande o acostado. |
| **Origen/pivote deliberado** | El origen del objeto ES el pivote en Unreal. Para props apoyados: en la **base** de la malla. Ponerlo antes de exportar. |
| **Normales afuera** | `Shift+N` (Recalculate Outside). Caras invertidas se ven negras/huecas en Unreal (backface culling). |
| **Sin n-gons problemáticos** | Quads/tris; el exporter triangula pero los n-gons cóncavos triangulan mal. Revisar zonas curvas. |
| **Naming** | Objeto = nombre final del asset: **`SM_<Nombre>`** (convención del proyecto Unreal). Sin espacios ni acentos. |

## 1. UVs — acá TODO es horneado (no hay Lumen)

🔴 A diferencia de lo que dice internet ("con UE5 no hace falta lightmap UV"), **este proyecto usa Lightmass horneado** (Quest, renderer móvil) → toda malla estática que reciba luz horneada necesita:

- **Canal UV 0**: texturas/material (puede solapar, puede espejar).
- **Canal UV 1**: **lightmap — SIN solapes, con padding** entre islas. Generarlo en Blender (nuevo UV map + Lightmap Pack o Smart UV Project con margen) **o** dejar que Unreal lo genere al importar (Generate Lightmap UVs) — para geometría simple, el de Unreal suele alcanzar; controlarlo tras el import.
- Assets **solo emisivos/unlit** (mucho del kit Turrell) no consumen lightmap, pero regalarles el canal 1 no cuesta y evita re-export si cambian de material.

## 2. Colisión custom en el mismo FBX (opcional pero barata)

Objetos extra en el mismo export, nombrados **exactamente** (case-sensitive, `<Nombre>` = nombre del objeto render):

| Prefijo | Forma |
|---|---|
| `UCX_<Nombre>` | Convex hull (lo usual). Varias piezas: `UCX_<Nombre>_00`, `_01`… |
| `UBX_<Nombre>` | Caja |
| `USP_<Nombre>` | Esfera |
| `UCP_<Nombre>` | Cápsula |

- Cada pieza UCX debe ser **convexa** y lo más simple posible (la física la paga el Quest).
- Al importar con UCX propios: **desactivar Auto Generate Collision** — si quedan los dos, Unreal apila su colisión encima de la custom.
- Para la mayoría de los props contemplativos de la obra (nada se choca), la colisión simple auto-generada o ninguna alcanza — no fabricar UCX por reflejo.

## 3. Settings del exporter FBX (File → Export → FBX)

- **Include**: Limit to **Selected Objects** ✓; Object Types: **Mesh** (+ los UCX/UBX seleccionados).
- **Transform**: Scale **1.0** · **Apply Unit ✓** · Apply Scalings: **FBX Units Scale** · Forward/Up: **dejar el default (-Z Forward, Y Up)** — el exporter ya convierte al sistema de Unreal.
- **Geometry**: Smoothing: **Face** (evita el warning "no smoothing group") · **Tangent Space ✓** · **Apply Modifiers ✓** · Triangulate: opcional (Unreal triangula igual; activarlo da control).
- Guardar como **preset del exporter** la primera vez para no re-decidir.

## 4. Materiales y texturas — la realidad del proyecto

- El FBX solo transporta lo básico del **Principled BSDF** (Base Color, Roughness, Metallic, Normal, Alpha). Nodos procedurales, math y Emission **NO viajan**.
- **En este proyecto los materiales se autoran en Unreal** (emisivos/unlit del kit Turrell, ver `unreal-vr/references/materials-vr.md`). Lo que importa del lado Blender:
  - **Slots de material con nombres claros** (`M_Bell_Body`, `M_Bell_Glow`): cada slot llega como material slot del Static Mesh y ahí se asigna el material real de Unreal.
  - **Cuantos MENOS slots, mejor**: cada slot = una sección de malla = un draw call ([quest-budgets.md](quest-budgets.md)). Ideal 1, máximo 2.
- Si algún asset sí lleva textura horneada desde Blender: bake a imagen (no procedural), Path Mode **Copy** + embed, o importar la textura aparte.

## 5. Import en Unreal (5.8 / Interchange)

- Uniform Scale **1.0** (si llega 100× mal, el bug está en el paso 0/3 — arreglar el export, no compensar acá).
- Import Collisions ✓ solo si el FBX trae UCX (y Auto Generate Collision OFF en ese caso).
- Tras importar, **verificar en el editor**: escala contra el pawn, pivote, lightmap UV channel asignado (Static Mesh Editor → UV Channel 1), y conteo de secciones de material.
- Import una vez a la carpeta limpia correcta; los retoques van por **Reimport** (mantiene referencias y material assignments).

## 6. Síntomas → causa

| Síntoma en Unreal | Causa |
|---|---|
| 100× más chico/grande | Apply Unit sin marcar, o Unit Scale ≠ 1.0, o escala sin aplicar |
| Acostado / rotado | Rotación sin aplicar en Blender |
| Caras negras o huecos | Normales invertidas → Recalculate Outside |
| "No smoothing group" warning | Smoothing no estaba en Face |
| Sombras horneadas manchadas | Lightmap UV con solapes o sin padding, o resolución de lightmap muy baja |
| Colisión rara / doble | UCX mal nombrado (case-sensitive) o Auto Generate encendido junto a UCX |
| Pivote en cualquier lado | Origen no seteado antes del export |
