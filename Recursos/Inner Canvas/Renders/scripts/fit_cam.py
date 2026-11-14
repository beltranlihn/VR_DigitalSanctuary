# fit_cam.py - encuadre automatico: pone la camara mirando a lo largo de -dir, centra el bbox proyectado y ajusta la
# distancia para que el objeto ocupe FILL del cuadro (cuadrado).
import bpy
from bpy_extras.object_utils import world_to_camera_view
import math
from mathutils import Quaternion, Vector


def world_points(objs):
    pts = []
    for ob in objs:
        mw = ob.matrix_world
        pts.extend(mw @ v.co for v in ob.data.vertices)
    return pts


def fit(cam, objs, direction, up=(0, 0, 1), lens=85.0, fill=0.86, roll=0.0):
    scn = bpy.context.scene
    pts = world_points(objs)
    c = sum(pts, Vector()) / len(pts)
    d = Vector(direction).normalized()
    cam.data.lens = lens
    cam.data.sensor_fit = 'AUTO'
    cam.data.clip_start = 0.002
    dist = 1.0
    for _ in range(8):
        cam.location = c + d * dist
        cam.rotation_euler = ((-d).to_track_quat('-Z', 'Y') @ Quaternion((0, 0, 1), math.radians(roll))).to_euler()
        bpy.context.view_layer.update()
        ndc = [world_to_camera_view(scn, cam, p) for p in pts]
        xs = [p.x for p in ndc]
        ys = [p.y for p in ndc]
        ex = max(max(xs) - min(xs), max(ys) - min(ys))
        # centrar: correr el punto mirado segun el desvio del centro del bbox (en coordenadas de camara)
        mx = (max(xs) + min(xs)) / 2 - 0.5
        my = (max(ys) + min(ys)) / 2 - 0.5
        R = cam.matrix_world.to_3x3()
        rx, ry = scn.render.resolution_x, scn.render.resolution_y
        span = dist * cam.data.sensor_width / lens          # sensor_fit AUTO: el sensor cubre el lado mas largo
        width, height = (span, span * ry / rx) if rx >= ry else (span * rx / ry, span)
        c = c + R @ Vector((mx * width, my * height, 0))
        dist *= ex / fill
    cam.location = c + d * dist
    bpy.context.view_layer.update()
    return dist
