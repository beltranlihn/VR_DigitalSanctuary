# Presupuestos de geometría para Quest 3 — cuánto y qué cuesta de verdad

Referencia para decidir densidad de malla ANTES de modelar. Complementa (no reemplaza) `unreal-vr/references/materials-vr.md` y `profiling-quest.md` — el veredicto final siempre es la medición en el APK.

## Los números (orientativos, de guías 2026 para XR2 Gen 2)

| Tipo de asset | Triángulos | Nota |
|---|---|---|
| **Escena total en pantalla** | 300k–500k por frame | Techo teórico del chip; la obra debería quedar MUY por debajo (estética Turrell = casi sin geometría) |
| **Sala/entorno completo** | 20k–80k | Con la carga por sublevels, solo cuenta lo cargado |
| **Prop interactivo en mano** | 500–2.000 | La mano lo acerca al ojo: la calidad percibida viene del material/silueta, no de la densidad |
| **Prop de escena (campana, panel, orbe)** | 1.000–5.000 | Suficiente para siluetas suaves a 1-3 m |
| **Personaje/figura hero** (Alma, ProtoSoul) | 15k–30k máx | Y solo si de verdad se mira de cerca |

Regla práctica: modelar la silueta que se ve a la distancia real de la obra (sentada, distancias fijas) y ni un loop más. Subdividir siempre se puede después; bajar polys destruye UVs y normales.

## 🔴 Lo que cuesta MÁS que los triángulos (Quest = fill-rate bound)

1. **Draw calls**: cada malla × cada slot de material = un draw. 10 props de 500 tris con 2 materiales cada uno cuestan más que 1 malla de 20k con 1 material. → **Un material por malla** como default; fusionar props decorativos que siempre van juntos; en Unreal, instancias del mismo Static Mesh son baratas.
2. **Transparencia / overdraw**: cada capa translúcida repinta píxeles ×2 ojos. La geometría que quede DETRÁS de un translúcido grande (los fades, la ameba) se paga dos veces → mallas translúcidas lo más ajustadas posible a su silueta (no quads gigantes).
3. **Vértices sobre triángulos**: en móvil el vertex stage pesa; hard edges y costuras de UV **duplican vértices** en GPU. Preferir smooth shading con pocos hard edges deliberados.
4. **Skinned meshes** cuestan ~2× que estáticas — para esta obra, casi todo puede ser estático + animación de material/transform (como ya hace Alma: la vida en el material, no en bones).

## Chequeo antes de exportar (por script, barato)

```python
import bpy
obj = bpy.data.objects["SM_MiAsset"]
deps = bpy.context.evaluated_depsgraph_get()
me = obj.evaluated_get(deps).to_mesh()   # CON modificadores
tris = sum(len(p.vertices) - 2 for p in me.polygons)
print({"tris": tris, "mat_slots": len(obj.material_slots),
       "uv_layers": [l.name for l in me.uv_layers]})
```

- `tris` contra la tabla de arriba.
- `mat_slots` ideal 1 (máximo 2).
- `uv_layers` debe listar los 2 canales si el asset recibe luz horneada.

## LODs

Con experiencia sentada y salas por sublevel, las distancias son fijas → **modelar directo al detalle de esa distancia** suele eliminar la necesidad de LODs. Si un asset se ve de cerca Y de lejos (el recorrido del elevador), generar LODs en Unreal al importar (reducción automática), no mantener variantes a mano en Blender.
