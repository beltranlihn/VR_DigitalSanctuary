# ic_space_dsl.py - BP_ICSpace_IC: el espacio de dibujo de 3 x 3 m (Inner Canvas). Piso (borde + centro) y 4 paredes (grilla tenue)
# con M_ICSpace_IC. Con la voz que lo presenta aparece el PISO (SpaceReveal: sube, se sostiene y queda en FloorAlpha); las paredes
# no se ven (BaseAlpha 0, Beltran 2026-11-12) salvo la que tiene cerca la cabeza o una mano (NearCm). El director lo reinicia con SpaceReset.
# Recorrido 2026-11-12 noche: el piso se marca desde el titulo (el director llama SpaceReveal y deja RevealT en 10: sin la subida);
# cuando la voz presenta el espacio, SpaceReveal otra vez: el piso sube y las 4 PAREDES se encienden con la misma curva (_intro x 0,55).
# Recorrido v2 (2026-11-12 noche): en el visor (AutoPlace) el piso se ve SIEMPRE con el circulo del centro y la muesca hacia el titulo
# (RingA, Front); el borde aparece con SpaceReveal (al elegir la mano); las paredes solo con la cercania (sin el destello). WarnOn = la
# cabeza a menos de WarnIn cm de un borde (o afuera); se apaga a mas de WarnOut (lo lee el director para el aviso).
# Componentes (los arma build_ic.py, centrados en el actor = el PlayerStart, en el piso): Floor, WallXp, WallXn, WallYp, WallYn.
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ic_common import *
SA = lambda c, x: '(Rendering|Material|SetScalarParameterValueonMaterials %s "Alpha" %s)' % (D(c), x)
CODES = {}

CODES['SpaceBoot'] = '''(fn SpaceBoot ()
  (if %(ap)s
    (Transformation|SetActorLocation self (Transformation|GetActorLocation (Actor|GetActorOfClass "/Script/Engine.PlayerStart")) false true))
  (for _c (Actor|GetComponentsByClass self "/Script/Engine.StaticMeshComponent")
    (Rendering|Material|SetVectorParameterValueonMaterials _c "Color" (Math|Conversions|ToVector(LinearColor) %(col)s))
    (Rendering|Material|SetScalarParameterValueonMaterials _c "Alpha" 0.0))
  (bind _tps (Actor|GetAllActorsWithTag "sc4_title"))
  (bind _dir (select (> (Utilities|Array|Length _tps) 0) (Math|Vector|Normalize (* (- (Transformation|GetActorLocation (Utilities|Array|Get(acopy) _tps 0)) (Transformation|GetActorLocation self)) (Math|Vector|MakeVector 1.0 1.0 0.0))) (Math|Vector|MakeVector 1.0 0.0 0.0)))
  (Rendering|Material|SetVectorParameterValueonMaterials %(floor)s "Front" (Math|Vector|MakeVector (* (.x _dir) %(fx)s) (* (.y _dir) %(fy)s) 0.0))
  (Rendering|Material|SetScalarParameterValueonMaterials %(floor)s "RingA" (select %(ap)s %(ra)s 0.0))
  %(rt)s
  %(sh)s
  %(w0)s
  (Rendering|SetActorHiddenInGame self (not %(ap)s)))
''' % dict(col=D('LineColor'), rt=DS('RevealT', '-1.0'), sh=DS('Shown', 'false'), ap=D('AutoPlace'), floor=D('Floor'), fx=D('FlipX'),
           fy=D('FlipY'), ra=D('RingA'), w0=DS('WarnOn', 'false'))

CODES['SpaceReveal'] = '''(fn SpaceReveal ()
  %s
  %s
  (Rendering|SetActorHiddenInGame self false)
  (Development|PrintString "SPACE: se marca el espacio de dibujo" :bPrintToScreen false))
''' % (DS('RevealT', '0.0'), DS('Shown', 'true'))

CODES['SpaceReset'] = '''(fn SpaceReset ()
  %s
  %s
  %s
  (for _c (Actor|GetComponentsByClass self "/Script/Engine.StaticMeshComponent")
    (Rendering|Material|SetScalarParameterValueonMaterials _c "Alpha" 0.0))
  (Rendering|SetActorHiddenInGame self (not %s)))
''' % (DS('RevealT', '-1.0'), DS('Shown', 'false'), DS('WarnOn', 'false'), D('AutoPlace'))

# NearOf: cercania 0..1 de un punto a cada pared (las paredes estan en +-Half del centro, alineadas con el mundo). d = distancia a la
# pared hacia adentro: 1 pegado a la pared, 0 a NearCm; afuera sigue en 1 hasta 3 m y se apaga a 5 m (en el PC las celdas estan a
# 1 km entre si: sin ese corte, todas las paredes de las otras celdas se encendian).
NEAR = lambda d: '(* (Math|Float|MapRangeClamped %s 0.0 _n 1.0 0.0) (Math|Float|MapRangeClamped %s -500.0 -300.0 0.0 1.0))' % (d, d)
CODES['NearOf'] = '''(fn NearOf (Pt)
  (bind _c (Transformation|GetActorLocation self))
  (bind _h (* 0.5 %(size)s))
  (bind _n %(near)s)
  %(xp)s
  %(xn)s
  %(yp)s
  %(yn)s)
''' % dict(size=D('Size'), near=D('NearCm'),
           xp=DS('NXp', '(Math|Float|Max(Float) %s %s)' % (D('NXp'), NEAR('(- (+ (.x _c) _h) (.x Pt))'))),
           xn=DS('NXn', '(Math|Float|Max(Float) %s %s)' % (D('NXn'), NEAR('(- (.x Pt) (- (.x _c) _h))'))),
           yp=DS('NYp', '(Math|Float|Max(Float) %s %s)' % (D('NYp'), NEAR('(- (+ (.y _c) _h) (.y Pt))'))),
           yn=DS('NYn', '(Math|Float|Max(Float) %s %s)' % (D('NYn'), NEAR('(- (.y Pt) (- (.y _c) _h))'))))

CODES['SpaceTick'] = '''(fn SpaceTick (Dt)
  %(rtp)s
  (bind _t %(rt)s)
  (bind _intro (* (Math|Float|MapRangeClamped _t 0.0 1.2 0.0 1.0) (Math|Float|MapRangeClamped _t (+ 1.2 %(hold)s) (+ 3.2 %(hold)s) 1.0 0.0)))
  %(n0)s
  %(n1)s
  %(n2)s
  %(n3)s
  (CallFunction|NearOf :Pt %(cam)s)
  (for _m (Actor|GetComponentsByClass (Game|GetPlayerPawn 0) "/Script/Engine.SkeletalMeshComponent")
    (CallFunction|NearOf :Pt (Transformation|GetWorldLocation _m)))
  (bind _b (* %(base)s (Math|Float|MapRangeClamped _t 0.0 1.2 0.0 1.0)))
  %(axp)s
  %(axn)s
  %(ayp)s
  %(ayn)s
  %(afl)s
  (bind _c (Transformation|GetActorLocation self))
  (bind _h (* 0.5 %(size)s))
  (bind _d (Math|Float|Min(Float) (- _h (Math|Float|Absolute(Float) (- (.x %(cam)s) (.x _c)))) (- _h (Math|Float|Absolute(Float) (- (.y %(cam)s) (.y _c))))))
  %(warn)s)
''' % dict(size=D('Size'), warn=DS('WarnOn', '(select %s (< _d %s) (< _d %s))' % (D('WarnOn'), D('WarnOut'), D('WarnIn'))), rtp=DS('RevealT', '(+ %s Dt)' % D('RevealT')), rt=D('RevealT'), hold=D('HoldT'), cam=CAM, base=D('BaseAlpha'),
           n0=DS('NXp', '0.0'), n1=DS('NXn', '0.0'), n2=DS('NYp', '0.0'), n3=DS('NYn', '0.0'),
           axp=SA('WallXp', '(Math|Float|Max(Float) _b (Math|Float|Clamp(Float) %s))' % D('NXp')),
           axn=SA('WallXn', '(Math|Float|Max(Float) _b (Math|Float|Clamp(Float) %s))' % D('NXn')),
           ayp=SA('WallYp', '(Math|Float|Max(Float) _b (Math|Float|Clamp(Float) %s))' % D('NYp')),
           ayn=SA('WallYn', '(Math|Float|Max(Float) _b (Math|Float|Clamp(Float) %s))' % D('NYn')),
           afl=SA('Floor', '(Math|Float|Max(Float) _intro %s)' % D('FloorAlpha')))

ORDER = ['SpaceBoot', 'SpaceReveal', 'SpaceReset', 'NearOf', 'SpaceTick']
EVG = '''(event EventBeginPlay
  (CallFunction|SpaceBoot))

(event EventTick (DeltaSeconds)
  (if %s
    (CallFunction|SpaceTick :Dt (Math|Float|Min(Float) DeltaSeconds 0.0333))))
''' % D('Shown')
