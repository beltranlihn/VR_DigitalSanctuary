# ic_kb_dsl.py - BP_ICKeyboard_IC: el teclado para escribir el nombre (Inner Canvas, 2026-11-11)
# Se apunta con los laseres de los dos BP_SeqRig_SC (modo resultados) y se aprieta el gatillo (ResPressN de cada rig).
# Un tablero invisible (Board, colision Destructible como el Hit de los botones) recibe el laser; la tecla apuntada sale de
# llevar el impacto al espacio del actor y compararlo con KeyY/KeyZ/KeyW/KeyH (ic_kb_layout.py). Las teclas son planos con
# M_ICKey_IC (placa + letra del atlas T_ICKeyAtlas). El nombre se dibuja en NameWork (1024 x 256, Quicksand) y se reduce 2:1 a
# NameRT (512 x 128): esa textura la usan el campo, el HUD (centro) y el cierre.
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ic_common import *
NK = 30
AGI = lambda arr, i: '(Utilities|Array|Get(acopy) %s %s)' % (D(arr), i)
CODES = {}

CODES['KbBoot'] = '''(fn KbBoot ()
  (Utilities|Array|Clear %(keys)s)
  (for _i (range %(nk)d)
    (Utilities|Array|Add %(keys)s %(field)s))
  (Utilities|Array|Clear %(hov)s)
  (for _i (range %(nk)d)
    (Utilities|Array|Add %(hov)s 0.0))
  (for _c (Actor|GetComponentsByClass self "/Script/Engine.StaticMeshComponent")
    (bind _n (Utilities|GetObjectName _c))
    (if (Utilities|String|StartsWith _n "K_")
      (Utilities|Array|SetArrayElem %(keys)s (Utilities|String|StringToInteger (Utilities|String|RightChop _n 2)) (Utilities|Casting|CastToStaticMeshComponent _c) true)))
  (bind _rigs (Actor|GetAllActorsOfClass "%(rigc)s"))
  %(rig)s
  %(rig2)s
  %(nw)s
  %(nrt)s
  %(fmid)s
  (Rendering|Material|SetTextureParameterValue %(gfm)s "Card" %(gnrt)s)
  (Rendering|Material|SetVectorParameterValueonMaterials %(fieldc)s "Color" (Math|Conversions|ToVector(LinearColor) %(fcol)s))
  (Rendering|Material|SetScalarParameterValueonMaterials %(fieldc)s "Base" 0.18)
  (Rendering|Material|SetScalarParameterValueonMaterials %(fieldc)s "Opacity" 0.3)
  (Rendering|Material|SetScalarParameterValueonMaterials %(fieldc)s "Gain" 1.2)
  (Rendering|Material|SetScalarParameterValueonMaterials %(fieldc)s "Boost" 1.4)
  (Rendering|SetActorHiddenInGame self true)
  (Development|PrintString "KB: teclado listo" :bPrintToScreen false))
''' % dict(keys=D('Keys'), hov=D('Hov'), nk=NK, field=D('Field'), fieldc=D('Field'), rigc=RIGC,
           rig=DS('Rig', '(Utilities|Array|Get(acopy) _rigs 0)'), rig2=DS('Rig2', '(Utilities|Array|Get(acopy) _rigs 1)'),
           nw=DS('NameWork', '(Rendering|CreateRenderTarget2D :Width 2048 :Height 512 :Format "RTF_RGBA8" :ClearColor %s :bAutoGenerateMipMaps false)' % LC(0.0, 0.0, 0.0, 0.0)),
           nrt=DS('NameRT', '(Rendering|CreateRenderTarget2D :Width 1024 :Height 256 :Format "RTF_RGBA8" :ClearColor %s :bAutoGenerateMipMaps false)' % LC(0.0, 0.0, 0.0, 0.0)),
           fmid=DS('FieldMID', '(Rendering|Material|CreateDynamicMaterialInstance %s :ElementIndex 0 :SourceMaterial "%s")' % (D('Field'), PANE)),
           gfm=D('FieldMID'), gnrt=D('NameRT'), fcol=D('FieldColor'))

# KbShow: frente a la persona (Dist cm, Below cm bajo los ojos), mirandola; etiquetas del idioma; la N con tilde solo en espanol
CODES['KbShow'] = '''(fn KbShow (Spanish)
  %(es)s
  %(nm)s
  %(done)s
  %(typ)s
  %(ak)s
  %(van)s
  (bind _yaw (.yaw %(camrot)s))
  (bind _fwd (Math|Vector|MakeVector (Math|Trig|Cos(Degrees) _yaw) (Math|Trig|Sin(Degrees) _yaw) 0.0))
  (bind _pos (+ %(cam)s (+ (* _fwd %(dist)s) (Math|Vector|MakeVector 0.0 0.0 (* -1.0 %(below)s)))))
  (Transformation|SetActorLocationAndRotation self _pos (Math|Rotator|MakeRotfromX (- _pos %(cam)s)) false true)
  (for _i (range %(nk)d)
    (bind _k %(keyi)s)
    (Rendering|Material|SetVectorParameterValueonMaterials _k "Rect" (select Spanish %(res)s %(ren)s))
    (Rendering|Material|SetScalarParameterValueonMaterials _k "Asp" (/ %(kw)s %(kh)s))
    (Rendering|Material|SetScalarParameterValueonMaterials _k "Hover" 0.0)
    (Rendering|SetVisibility _k (or Spanish (!= _i 26))))
  (for _i (range %(nk)d)
    (Utilities|Array|SetArrayElem %(hov)s _i 0.0))
  %(lp1)s
  %(lp2)s
  (CallFunction|KbFade)
  (CallFunction|KbDraw)
  (Rendering|SetActorHiddenInGame self false)
  %(shown)s
  (Development|PrintString (Utilities|String|Append "KB: teclado a la vista, espanol = " (Utilities|String|ToString(Boolean) Spanish)) :bPrintToScreen false))
''' % dict(es=DS('ES', 'Spanish'), nm=DS('NameStr', '""'), done=DS('Done', 'false'), typ=DS('Typing', 'true'), ak=DS('AppearK', '0.0'),
           van=DS('Vanish', 'false'), camrot=CAMROT, cam=CAM, dist=D('Dist'), below=D('Below'), nk=NK, keyi=AGI('Keys', '_i'),
           res=AGI('RectES', '_i'), ren=AGI('RectEN', '_i'), hov=D('Hov'), kw=AGI('KeyW', '_i'), kh=AGI('KeyH', '_i'),
           lp1=DS('LastP1', '(Class|BPSeqRigSC|GetResPressN %s)' % D('Rig')), lp2=DS('LastP2', '(Class|BPSeqRigSC|GetResPressN %s)' % D('Rig2')),
           shown=DS('Shown', 'true'))

CODES['KbHide'] = '''(fn KbHide ()
  %s
  %s)
''' % (DS('Vanish', 'true'), DS('Typing', 'false'))

CODES['KbReset'] = '''(fn KbReset ()
  %s
  %s
  %s
  %s
  %s
  (Rendering|SetActorHiddenInGame self true))
''' % (DS('Done', 'false'), DS('NameStr', '""'), DS('Typing', 'false'), DS('Shown', 'false'), DS('Vanish', 'false'))

CODES['KbSetName'] = '''(fn KbSetName (Name)
  %s
  %s
  (CallFunction|KbDraw))
''' % (DS('NameStr', 'Name'), DS('Typing', 'false'))

# KbFade: aparicion/desaparicion (Fade del material de teclas y campo)
CODES['KbFade'] = '''(fn KbFade ()
  (bind _f (Math|Float|FInterpEaseInOut 0.0 1.0 %(ak)s 2.0))
  (for _k %(keys)s
    (Rendering|Material|SetScalarParameterValueonMaterials _k "Fade" _f))
  (Rendering|Material|SetScalarParameterValueonMaterials %(field)s "Fade" _f))
''' % dict(ak=D('AppearK'), keys=D('Keys'), field=D('Field'))

# KbHit: la tecla que apunta el laser del rig R (o -1) -> HitIdx
CODES['KbHit'] = '''(fn KbHit (R)
  %(h0)s
  (if (== (Class|BPSeqRigSC|GetBeamHitActor R) self)
    (bind _loc (Math|Transform|InverseTransformLocation (Transformation|GetActorTransform self) (Class|BPSeqRigSC|GetBeamHitLoc R)))
    (for _i (range %(nk)d)
      (if (and (or %(es)s (!= _i 26)) (and (<= (Math|Float|Absolute(Float) (- (.y _loc) %(ky)s)) (* 0.5 %(kw)s)) (<= (Math|Float|Absolute(Float) (- (.z _loc) %(kz)s)) (* 0.5 %(kh)s))))
        %(hi)s))))
''' % dict(h0=DS('HitIdx', '-1'), nk=NK, es=D('ES'), ky=AGI('KeyY', '_i'), kw=AGI('KeyW', '_i'), kz=AGI('KeyZ', '_i'), kh=AGI('KeyH', '_i'),
           hi=DS('HitIdx', '_i'))

# KbPress: OK (29) cierra si hay nombre; BORRAR (27) saca la ultima letra; ESPACIO (28) sin espacios dobles ni al principio;
# letras con mayuscula al principio de cada palabra. Sonido y destello de la tecla.
CODES['KbPress'] = '''(fn KbPress (I)
  (bind _len (Utilities|String|Len %(nm)s))
  (bind _cap (or (== _len 0) (Utilities|String|EndsWith %(nm)s " ")))
  (Utilities|Array|SetArrayElem %(hov)s I 2.0)
  (Audio|PlaySound2D %(snd)s :VolumeMultiplier %(cvol)s)
  (if (== I 29)
    (if (> (Utilities|String|Len (Utilities|String|TrimTrailing %(nm)s)) 0)
      %(nmt)s
      %(done)s
      %(typ0)s
      (CallFunction|KbDraw)
      (Development|PrintString (Utilities|String|Append "KB: OK, nombre = " %(nm)s) :bPrintToScreen false))
    (elif (== I 27)
      (if (> _len 0)
        %(del)s
        (CallFunction|KbDraw))
      (elif (== I 28)
        (if (and (> _len 0) (and (not (Utilities|String|EndsWith %(nm)s " ")) (< _len %(max)s)))
          %(spc)s
          (CallFunction|KbDraw))
        (else
          (if (< _len %(max)s)
            %(add)s
            (CallFunction|KbDraw)))))))
''' % dict(nm=D('NameStr'), hov=D('Hov'), snd=D('ClickSound'), cvol=D('ClickVol'), max=D('MaxLen'),
           nmt=DS('NameStr', '(Utilities|String|TrimTrailing %s)' % D('NameStr')), done=DS('Done', 'true'), typ0=DS('Typing', 'false'),
           dele='', **{'del': DS('NameStr', '(Utilities|String|LeftChop %s 1)' % D('NameStr'))},
           spc=DS('NameStr', '(Utilities|String|Append %s " ")' % D('NameStr')),
           add=DS('NameStr', '(Utilities|String|Append %s (select _cap %s %s))' % (D('NameStr'), AGI('CharsUp', 'I'), AGI('CharsLo', 'I'))))

# KbDraw: el nombre (o la pregunta, mas tenue) en NameWork a 2x y reducido a NameRT; con cursor mientras se escribe
CODES['KbDraw'] = '''(fn KbDraw ()
  (bind _has (> (Utilities|String|Len %(nm)s) 0))
  (bind _txt (select _has (Utilities|String|Append %(nm)s (select (and %(typ)s %(car)s) "|" " ")) (select %(es)s %(phes)s %(phen)s)))
  (Rendering|ClearRenderTarget2D :TextureRenderTarget %(nw)s :ClearColor %(c0)s)
  (bind (_cv _sz _ctx) (Rendering|BeginDrawCanvastoRenderTarget :TextureRenderTarget %(nw)s))
  (bind _tsz (Canvas|ClippedTextSize _cv :RenderFont "%(font)s" :RenderText _txt :Scale (Math|Vector2D|MakeVector2D 1.0 1.0)))
  (bind (_tw _th) (Math|Vector2D|BreakVector2D _tsz))
  (bind _fk (Math|Float|Min(Float) (select _has 2.5 1.85) (/ 1126.0 (Math|Float|Max(Float) _tw 1.0))))
  (Canvas|DrawText _cv :RenderFont "%(font)s" :RenderText _txt :ScreenPosition %(mid)s :Scale (Math|Vector2D|MakeVector2D _fk _fk) :RenderColor (select _has %(tcol)s %(hcol)s) :Kerning 0.0 :ShadowColor %(c0)s :ShadowOffset %(z2)s :bCentreX true :bCentreY true :bOutlined false :OutlineColor %(c0)s)
  (Rendering|EndDrawCanvastoRenderTarget :Context _ctx)
  (Rendering|ClearRenderTarget2D :TextureRenderTarget %(nrt)s :ClearColor %(c0)s)
  (bind (_cv2 _sz2 _ctx2) (Rendering|BeginDrawCanvastoRenderTarget :TextureRenderTarget %(nrt)s))
  (Canvas|DrawTexture _cv2 :RenderTexture %(nw)s :ScreenPosition %(z2)s :ScreenSize %(half)s :CoordinatePosition %(z2)s :CoordinateSize %(one2)s :RenderColor %(white)s :BlendMode "BLEND_Opaque" :Rotation 0.0 :PivotPoint %(piv)s)
  (Rendering|EndDrawCanvastoRenderTarget :Context _ctx2))
''' % dict(nm=D('NameStr'), typ=D('Typing'), car=D('Caret'), es=D('ES'), phes=D('PromptES'), phen=D('PromptEN'),
           nw=D('NameWork'), nrt=D('NameRT'), c0=LC(0.0, 0.0, 0.0, 0.0), font='/Game/InnerCanvas/UI/F_ICWall_IC.F_ICWall_IC', mid=V2('1024.0', '256.0'),
           sc=V2('2.5', '2.5'), sch=V2('1.85', '1.85'), tcol=D('TextColor'), hcol=D('PromptColor'), z2=V2('0.0', '0.0'),
           half=V2('1024.0', '256.0'), one2=V2('1.0', '1.0'), white=LC(1.0, 1.0, 1.0, 1.0), piv=V2('0.5', '0.5'))

# KbTick: aparicion, cursor que titila, tecla apuntada por cada laser, clic (el que cambio su ResPressN) y brillo de las teclas
CODES['KbTick'] = '''(fn KbTick (Dt)
  %(akp)s
  (CallFunction|KbFade)
  %(blt)s
  (if (and %(typ)s (>= %(bl)s 0.5))
    %(bl0)s
    %(car)s
    (CallFunction|KbDraw))
  (CallFunction|KbHit :R %(rig)s)
  %(h1)s
  (CallFunction|KbHit :R %(rig2)s)
  %(h2)s
  (if (and (>= %(gh1)s 0) (and (!= %(gh1)s %(ph1)s) (not %(done)s)))
    (Audio|PlaySound2D %(hsnd)s :VolumeMultiplier %(hvol)s))
  (if (and (>= %(gh2)s 0) (and (!= %(gh2)s %(ph2)s) (and (!= %(gh2)s %(gh1)s) (not %(done)s))))
    (Audio|PlaySound2D %(hsnd)s :VolumeMultiplier %(hvol)s))
  %(sph1)s
  %(sph2)s
  (bind _rp (Class|BPSeqRigSC|GetResPressN %(rig)s))
  (bind _rp2 (Class|BPSeqRigSC|GetResPressN %(rig2)s))
  %(c1)s
  %(c2)s
  %(lp1)s
  %(lp2)s
  (for _i (range %(nk)d)
    (bind _t (select (or (== _i %(gh1)s) (== _i %(gh2)s)) 1.0 0.0))
    (bind _v (Math|Interpolation|FInterpTo (Utilities|Array|Get(acopy) %(hov)s _i) _t Dt 10.0))
    (Utilities|Array|SetArrayElem %(hov)s _i _v)
    (Rendering|Material|SetScalarParameterValueonMaterials (Utilities|Array|Get(acopy) %(keys)s _i) "Hover" _v))
  (if (and %(van)s (<= %(ak)s 0.01))
    %(sh0)s
    (Rendering|SetActorHiddenInGame self true)
    (elif (and %(gc1)s (not %(done)s))
      (CallFunction|KbPress :I %(gh1)s)
      (Class|BPSeqRigSC|Pulse :self %(rig)s :bRight (Class|BPSeqRigSC|GetRightHanded %(rig)s))
      (elif (and %(gc2)s (not %(done)s))
        (CallFunction|KbPress :I %(gh2)s)
        (Class|BPSeqRigSC|Pulse :self %(rig2)s :bRight (Class|BPSeqRigSC|GetRightHanded %(rig2)s))))))
''' % dict(akp=DS('AppearK', '(Math|Interpolation|FInterptoConstant %s (select %s 0.0 1.0) Dt 2.5)' % (D('AppearK'), D('Vanish'))),
           blt=DS('BlinkT', '(+ %s Dt)' % D('BlinkT')), typ=D('Typing'), bl=D('BlinkT'), bl0=DS('BlinkT', '0.0'),
           car=DS('Caret', '(not %s)' % D('Caret')), rig=D('Rig'), rig2=D('Rig2'), h1=DS('H1', D('HitIdx')), h2=DS('H2', D('HitIdx')),
           c1=DS('Clk1', '(and (!= _rp %s) (>= %s 0))' % (D('LastP1'), D('H1'))),
           c2=DS('Clk2', '(and (!= _rp2 %s) (>= %s 0))' % (D('LastP2'), D('H2'))),
           lp1=DS('LastP1', '_rp'), lp2=DS('LastP2', '_rp2'), nk=NK, gh1=D('H1'), gh2=D('H2'), hov=D('Hov'), keys=D('Keys'),
           van=D('Vanish'), ak=D('AppearK'), sh0=DS('Shown', 'false'), gc1=D('Clk1'), gc2=D('Clk2'), done=D('Done'),
           ph1=D('PH1'), ph2=D('PH2'), hsnd=D('HoverSound'), hvol=D('HoverVol'), sph1=DS('PH1', D('H1')), sph2=DS('PH2', D('H2')))

ORDER = ['KbBoot', 'KbFade', 'KbDraw', 'KbShow', 'KbHide', 'KbReset', 'KbSetName', 'KbHit', 'KbPress', 'KbTick']
EVG = '''(event EventBeginPlay
  (CallFunction|KbBoot))

(event EventTick (DeltaSeconds)
  (if %s
    (CallFunction|KbTick :Dt (Math|Float|Min(Float) DeltaSeconds 0.0333))))
''' % D('Shown')
