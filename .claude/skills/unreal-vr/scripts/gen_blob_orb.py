# -*- coding: utf-8 -*-
"""gen_blob_orb.py - genera SM_BlobOrb_SC: el lienzo de las esferas de sonido.

QUE ES. Una icoesfera de radio 50, bien teselada, con normales suaves. Es el equivalente
de SM_BlobTube_SC pero para una gota SUELTA: el vertex shader de M_BlobOrb_SC empuja cada
vertice a la superficie del mismo smin (bola principal + lobulo + wobble) que hoy resuelve
el raymarch de MI_OrbBlob_SC.

POR QUE RADIO 50. Es la convencion que ya usa SM_AlmaSphere: el material corre en espacio
LOCAL, donde la malla mide 50 sin importar la escala del actor, y por eso Rad0 = 42 y
ROrb = 38 funcionan en todos los tamanos sin empujar nada por instancia. Cambiar el radio
del lienzo obligaria a recalcular esos numeros: no se cambia.

POR QUE ICOESFERA Y NO UV-SPHERE. La UV-sphere amontona vertices en los polos y los estira
en el ecuador: el wobble se resolveria con detalle distinto segun la latitud, y los polos
se verian como dos puntos de artefacto. La icoesfera reparte parejo.

LA DENSIDAD. El wobble tiene frecuencia WobbleAFS.y (hoy 4) sobre la esfera entera, o sea
unas 4 ondas por vuelta. Subdivision 3 = 642 verts / 1.280 tris da ~20 vertices por onda,
de sobra. Con 20 esferas son 25k tris, que en este proyecto es ruido: somos fill-rate
bound, no geometry bound. Si la silueta se ve facetada de cerca, subir a 4 (2.562 verts)
antes de tocar cualquier otra cosa.

LAS NORMALES DE LA MALLA NO SE USAN para sombrear: la normal sale analitica del gradiente
del mismo campo, igual que en el gusano. Se dejan suaves igual para que la direccion
radial (que SI se usa, como direccion de marcha) quede continua.

Uso (headless, no necesita la sesion de Blender del usuario):
  "C:\\Program Files\\Blender Foundation\\Blender 5.2\\blender.exe" --background --python gen_blob_orb.py
Salida: <carpeta del script>/../../../../VR_Test/Saved/ClaudeScripts/SM_BlobOrb_SC.fbx
"""
import os

import bpy

SUBDIV = 3      # 3 = 642 verts / 1.280 tris. Subir a 4 solo si la silueta se ve facetada.
RADIO = 50.0    # 🔴 la convencion de SM_AlmaSphere. No cambiar sin recalcular Rad0/ROrb.
NOMBRE = "SM_BlobOrb_SC"


def limpiar_escena():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def construir():
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=SUBDIV, radius=RADIO,
                                          location=(0.0, 0.0, 0.0))
    ob = bpy.context.active_object
    ob.name = NOMBRE
    ob.data.name = NOMBRE
    for poly in ob.data.polygons:
        poly.use_smooth = True
    # UV simple por proyeccion esferica: el material no la usa (trabaja con LocalPos),
    # pero Unreal se queja al importar una malla sin UVs.
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.sphere_project()
    bpy.ops.object.mode_set(mode='OBJECT')
    return ob


def exportar(ob):
    aqui = os.path.dirname(os.path.abspath(__file__))
    destino_dir = os.path.abspath(os.path.join(
        aqui, "..", "..", "..", "..", "VR_Test", "Saved", "ClaudeScripts"))
    os.makedirs(destino_dir, exist_ok=True)
    ruta = os.path.join(destino_dir, NOMBRE + ".fbx")
    bpy.ops.object.select_all(action='DESELECT')
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.export_scene.fbx(
        filepath=ruta,
        use_selection=True,
        apply_unit_scale=True,
        global_scale=1.0,
        apply_scale_options='FBX_SCALE_NONE',
        object_types={'MESH'},
        mesh_smooth_type='FACE',
        use_mesh_modifiers=True,
        add_leaf_bones=False,
        bake_anim=False,
        path_mode='STRIP',
    )
    return ruta


def main():
    limpiar_escena()
    ob = construir()
    ruta = exportar(ob)
    me = ob.data
    print("LISTO %s  verts=%d  polys=%d  ->  %s"
          % (NOMBRE, len(me.vertices), len(me.polygons), ruta))


if __name__ == "__main__":
    main()
