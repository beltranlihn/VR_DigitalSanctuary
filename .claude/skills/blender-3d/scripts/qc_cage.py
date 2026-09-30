# qc_cage.py - mando de la obra (4a version, 2026-09-29): jaula de control INICIAL para la superficie de subdivision.
# Toma una superficie cerrada aproximada del mando (la fusion por Poisson, tp_body_R.obj / tp_trigger_R.obj) y la
# remalla en quads con QuadriFlow (flujo limpio, tamano parejo). Esa jaula es solo el punto de partida: qc_fit.py
# calcula despues donde va cada punto de control para que la superficie Catmull-Clark pase por el mando oficial.
# Uso: blender --background --python qc_cage.py -- <dir> <caras_cuerpo> <caras_gatillo>
import os
import sys
import traceback

import bmesh
import bpy
from mathutils import Matrix

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
D = argv[0] if argv else "."
TARGETS = {"tp_body_R": int(argv[1]) if len(argv) > 1 else 2000, "tp_trigger_R": int(argv[2]) if len(argv) > 2 else 300}


def cage(name, target):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.wm.obj_import(filepath=os.path.join(D, name + ".obj"), forward_axis='Y', up_axis='Z')
    ob = bpy.context.selected_objects[0]
    # QuadriFlow toma como "arista de largo cero" toda arista < 1e-4 unidades (0,1 mm en metros) y cancela:
    # se trabaja en MILIMETROS y se vuelve a metros al final
    ob.data.transform(Matrix.Scale(1000.0, 4))
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
    bmesh.ops.dissolve_degenerate(bm, dist=1e-4, edges=bm.edges[:])
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    bm.to_mesh(ob.data)
    bm.free()
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    dec = ob.modifiers.new("Dec", 'DECIMATE')
    dec.ratio = min(1.0, 60000 / len(ob.data.polygons))
    bpy.ops.object.modifier_apply(modifier="Dec")
    r = bpy.ops.object.quadriflow_remesh(target_faces=target, use_mesh_symmetry=False, use_preserve_sharp=False,
                                         use_preserve_boundary=False, preserve_attributes=False, smooth_normals=False,
                                         mode='FACES', seed=0)
    me = ob.data
    me.transform(Matrix.Scale(0.001, 4))
    nq = sum(1 for p in me.polygons if len(p.vertices) == 4)
    bm = bmesh.new()
    bm.from_mesh(me)
    nm = sum(1 for e in bm.edges if not e.is_manifold)
    bm.free()
    out = os.path.join(D, name.replace("tp_", "qc_cage_") + ".obj")
    with open(out, "w") as fh:
        for v in me.vertices:
            fh.write("v %.6f %.6f %.6f\n" % tuple(v.co))
        for p in me.polygons:
            fh.write("f " + " ".join(str(i + 1) for i in p.vertices) + "\n")
    print("JAULA", name, r, "verts", len(me.vertices), "caras", len(me.polygons), "quads", nq, "no_manifold", nm, "->", out)


for nm_, t in TARGETS.items():
    try:
        cage(nm_, t)
    except BaseException as e:
        print("JAULA_FALLO", nm_, type(e).__name__, e)
        traceback.print_exc()
