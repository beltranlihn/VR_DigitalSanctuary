# mirror_smooth_dsl.py - BP_MirrorLink_SC.ApplyStep con las manos suavizadas (2026-10-21, pedido de Beltran en el router "Alma Digital":
# "la data del head funciona super bien ... las manos van super laggeadas, entrecortadas, se nota mucho en el dibujo").
# La camara del robot que se ve es SpecCam (SpecStep: VInterpTo/RInterpTo) y por eso la cabeza se ve fluida; los mandos se ponian
# en la pose del ULTIMO paquete cada cuadro, y por wifi los paquetes llegan a rafagas: escalones. Ahora cada mando sigue a la pose
# recibida con VInterpTo/RInterpTo a HandLag (14/s, ~70 ms, editable en Spectator) y salta directo si la diferencia pasa de 60 cm
# (primer paquete, cambio de nivel). La camara del pawn sigue exacta (la usan las mecanicas). El dibujo del robot sale de esos mandos.
# Lectura previa (respaldo): Demo2/readback_mirror_apply.txt.
G = lambda n: '(Variables|Z-Estado|Get%s)' % n
A = lambda i: '(Utilities|Array|Get(acopy) _posef %d)' % i
LOC = lambda i: '(Math|Vector|MakeVector %s %s %s)' % (A(i), A(i + 1), A(i + 2))
ROT = lambda i: '(Math|Rotator|MakeRotator %s %s %s)' % (A(i + 5), A(i + 3), A(i + 4))
DT = '(Utilities|Time|GetWorldDeltaSeconds)'
LAG = '(Variables|Spectator|GetHandLag)'


def smooth(comp, i):
    c = G(comp)
    return '''(if (> (Math|Vector|Distance(Vector) (Transformation|GetWorldLocation %(c)s) %(loc)s) 60.0)
      (Transformation|SetWorldLocationAndRotation %(c)s %(loc)s %(rot)s false true)
      (else
        (Transformation|SetWorldLocationAndRotation %(c)s (Math|Interpolation|VInterpTo (Transformation|GetWorldLocation %(c)s) %(loc)s %(dt)s %(lag)s) (Math|Interpolation|RInterpTo (Transformation|GetWorldRotation %(c)s) %(rot)s %(dt)s %(lag)s) false true)))''' % dict(
        c=c, loc=LOC(i), rot=ROT(i), dt=DT, lag=LAG)


CODES = {}
CODES['ApplyStep'] = '''(fn ApplyStep ()
  (bind _posef %(pf)s)
  (CallFunction|EnsureRig)
  (if (and %(rig)s (>= (Utilities|Array|Length _posef) 30))
    (Transformation|SetWorldLocationAndRotation %(cam)s %(cloc)s %(crot)s false true)
    %(lg)s
    %(rg)s
    %(la)s
    %(ra)s
    (Variables|Z-Estado|SetPoseReady (> %(rx)s 30))
    (CallFunction|Inject)))
''' % dict(pf=G('PoseF'), rig=G('RigOk'), cam=G('Cam'), cloc=LOC(0), crot=ROT(0),
           lg=smooth('MCLG', 6), rg=smooth('MCRG', 12), la=smooth('MCLA', 18), ra=smooth('MCRA', 24), rx=G('RxCount'))
ORDER = ['ApplyStep']
