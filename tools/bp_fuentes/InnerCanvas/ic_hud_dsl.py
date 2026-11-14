# ic_hud_dsl.py - BP_ICWallHUD_IC: la pantalla del PC de Inner Canvas. Dibuja en 4 x 2 las 8 camaras (RTs de BP_ICWall_IC) y en cada
# cuadro el numero del visor, el nombre, el tiempo (m:ss, mientras dibuja) y una barra de tinta. Sin UMG: el HUD de Unreal (Canvas).
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ic_common import *
WALLC = IC + 'BP_ICWall_IC.BP_ICWall_IC_C'
# Fuente del PC: copia de Quicksand a tamano 64 (la original es 9: agrandada x3-x6 en 4K se pixelaba). _f = _u * 9/64 deja los
# textos del mismo tamano que antes, pero rasterizados grandes y reducidos (nitidos).
WFONT = '/Game/InnerCanvas/UI/F_ICWall_IC.F_ICWall_IC'
MFONT = '/Game/InnerCanvas/UI/F_ICWallM_IC.F_ICWallM_IC'   # 32 px
SFONT = '/Game/InnerCanvas/UI/F_ICWallS_IC.F_ICWallS_IC'   # 18 px
W2 = lambda var, i: '(Utilities|Array|Get(acopy) (Class|BPICWallIC|Get%s %s) %s)' % (var, D('Wall'), i)
CODES = {}

CODES['FindWall'] = '''(fn FindWall ()
  (Utilities|IsValid %s
    (:"Is Not Valid"
      %s)))
''' % (D('Wall'), DS('Wall', '(Actor|GetActorOfClass "%s")' % WALLC))

# DrawCells: todo en pixeles de 1080 escalados por _u = H / 1080 (en 4K el texto y las barras se ven igual que en 1080).
# Textos (11-13): :Scale 1.0 y fuente F_ICW<n>_IC al tamano justo (el Canvas no filtra las letras); _hi = H >= 1600 (juego 4K).
# (11-13: sin botones RESET/REINICIAR ni zonas de clic; franja de cada celda 40 px)
# Arriba un banner de 92 px: INNER CANVAS y la senal de cada visor (ultimo /ic/st hace < 3 s = OK, < 15 s = debil, si no sin senal).
# 11-13: 4 visores (1-4) en 2 x 2 de W/2 x (H - banner)/2 (en 4K 1920 x 988 = el RT de BP_ICWall_IC); la senal de los 4 arriba.
CODES['DrawCells'] = '''(fn DrawCells (W H)
  (bind _u (/ H 1080.0))
  (bind _hi (>= H 1600.0))
  (bind _f (* _u 0.140625))
  (bind _fm (* _u 0.28125))
  (bind _fs (* _u 0.5))
  (bind _bh (* 92.0 _u))
  (bind _cw (/ W 2.0))
  (bind _ch (/ (- H _bh) 2.0))
  (bind _now (Utilities|Time|GetGameTimeInSeconds))
  (HUD|DrawRect :RectColor %(bg)s :ScreenX 0.0 :ScreenY 0.0 :ScreenW W :ScreenH H)
  (if _hi
    (HUD|DrawText :Text "INNER CANVAS" :TextColor %(txt)s :ScreenX (Math|Conversions|ToFloat(Integer) (Math|Float|Truncate (+ (* 28.0 _u) 0.5))) :ScreenY (Math|Conversions|ToFloat(Integer) (Math|Float|Truncate (+ (* 20.0 _u) 0.5))) :Font "/Game/InnerCanvas/UI/F_ICW54_IC.F_ICW54_IC" :Scale 1.0 :bScalePosition false)
    (else
      (HUD|DrawText :Text "INNER CANVAS" :TextColor %(txt)s :ScreenX (Math|Conversions|ToFloat(Integer) (Math|Float|Truncate (+ (* 28.0 _u) 0.5))) :ScreenY (Math|Conversions|ToFloat(Integer) (Math|Float|Truncate (+ (* 20.0 _u) 0.5))) :Font "/Game/InnerCanvas/UI/F_ICW27_IC.F_ICW27_IC" :Scale 1.0 :bScalePosition false)))
  (if _hi
    (HUD|DrawText :Text "ALMA DIGITAL STUDIO" :TextColor %(num)s :ScreenX (Math|Conversions|ToFloat(Integer) (Math|Float|Truncate (+ (* 30.0 _u) 0.5))) :ScreenY (Math|Conversions|ToFloat(Integer) (Math|Float|Truncate (+ (* 66.0 _u) 0.5))) :Font "/Game/InnerCanvas/UI/F_ICW21_IC.F_ICW21_IC" :Scale 1.0 :bScalePosition false)
    (else
      (HUD|DrawText :Text "ALMA DIGITAL STUDIO" :TextColor %(num)s :ScreenX (Math|Conversions|ToFloat(Integer) (Math|Float|Truncate (+ (* 30.0 _u) 0.5))) :ScreenY (Math|Conversions|ToFloat(Integer) (Math|Float|Truncate (+ (* 66.0 _u) 0.5))) :Font "/Game/InnerCanvas/UI/F_ICW11_IC.F_ICW11_IC" :Scale 1.0 :bScalePosition false)))
  (for _i (range 4)
    (bind _x (* (Math|Conversions|ToFloat(Integer) (- _i (select (< _i 2) 0 2))) _cw))
    (bind _y (+ _bh (select (< _i 2) 0.0 _ch)))
    (bind _age (- _now %(lrx)s))
    (bind _ok (< _age 3.0))
    (bind _weak (< _age 15.0))
    (bind _sx (+ (* W 0.55) (* (Math|Conversions|ToFloat(Integer) _i) (* W 0.11))))
    (HUD|DrawRect :RectColor (select _ok %(cok)s (select _weak %(cweak)s %(coff)s)) :ScreenX _sx :ScreenY (* 30.0 _u) :ScreenW (* 16.0 _u) :ScreenH (* 16.0 _u))
    (if _hi
      (HUD|DrawText :Text (Utilities|String|Append "VISOR " (Utilities|String|ToString(Integer) (+ _i 1))) :TextColor %(txt)s :ScreenX (Math|Conversions|ToFloat(Integer) (Math|Float|Truncate (+ (+ _sx (* 24.0 _u)) 0.5))) :ScreenY (Math|Conversions|ToFloat(Integer) (Math|Float|Truncate (+ (* 22.0 _u) 0.5))) :Font "/Game/InnerCanvas/UI/F_ICW24_IC.F_ICW24_IC" :Scale 1.0 :bScalePosition false)
      (else
        (HUD|DrawText :Text (Utilities|String|Append "VISOR " (Utilities|String|ToString(Integer) (+ _i 1))) :TextColor %(txt)s :ScreenX (Math|Conversions|ToFloat(Integer) (Math|Float|Truncate (+ (+ _sx (* 24.0 _u)) 0.5))) :ScreenY (Math|Conversions|ToFloat(Integer) (Math|Float|Truncate (+ (* 22.0 _u) 0.5))) :Font "/Game/InnerCanvas/UI/F_ICW12_IC.F_ICW12_IC" :Scale 1.0 :bScalePosition false)))
    (if _hi
      (HUD|DrawText :Text (select _ok "OK" (select _weak "débil" "sin señal")) :TextColor (select _ok %(cok)s (select _weak %(cweak)s %(coff)s)) :ScreenX (Math|Conversions|ToFloat(Integer) (Math|Float|Truncate (+ (+ _sx (* 24.0 _u)) 0.5))) :ScreenY (Math|Conversions|ToFloat(Integer) (Math|Float|Truncate (+ (* 52.0 _u) 0.5))) :Font "/Game/InnerCanvas/UI/F_ICW21_IC.F_ICW21_IC" :Scale 1.0 :bScalePosition false)
      (else
        (HUD|DrawText :Text (select _ok "OK" (select _weak "débil" "sin señal")) :TextColor (select _ok %(cok)s (select _weak %(cweak)s %(coff)s)) :ScreenX (Math|Conversions|ToFloat(Integer) (Math|Float|Truncate (+ (+ _sx (* 24.0 _u)) 0.5))) :ScreenY (Math|Conversions|ToFloat(Integer) (Math|Float|Truncate (+ (* 52.0 _u) 0.5))) :Font "/Game/InnerCanvas/UI/F_ICW11_IC.F_ICW11_IC" :Scale 1.0 :bScalePosition false)))
    (bind _ph %(ph)s)
    (bind _tl (Math|Float|Max(Float) %(tl)s 0.0))
    (bind _m (Math|Float|Floor (/ _tl 60.0)))
    (bind _s (- (Math|Float|Floor _tl) (* _m 60.0)))
    (bind _show (and (>= _ph 8) (<= _ph 9)))
    (bind _ts (Utilities|String|Append (Utilities|String|ToString(Integer) (Math|Float|Truncate _m)) (Utilities|String|Append (select (< _s 10.0) ":0" ":") (Utilities|String|ToString(Integer) (Math|Float|Truncate _s)))))
    (HUD|DrawTexture :Texture %(rt)s :ScreenX (+ _x (* 3.0 _u)) :ScreenY (+ _y (* 3.0 _u)) :ScreenW (- _cw (* 6.0 _u)) :ScreenH (- _ch (* 6.0 _u)) :TextureU 0.0 :TextureV 0.0 :TextureUWidth 1.0 :TextureVHeight 1.0 :TintColor %(white)s :BlendMode "BLEND_Opaque" :Scale 1.0 :bScalePosition false :Rotation 0.0 :RotPivot %(z2)s)
    (HUD|DrawRect :RectColor %(band)s :ScreenX (+ _x (* 3.0 _u)) :ScreenY (+ _y (* 3.0 _u)) :ScreenW (- _cw (* 6.0 _u)) :ScreenH (* 40.0 _u))
    (HUD|DrawRect :RectColor %(band)s :ScreenX (+ _x (* 3.0 _u)) :ScreenY (- (+ _y _ch) (+ (* (* 34.0 %(fs2)s) _u) (* 12.0 _u))) :ScreenW (- _cw (* 6.0 _u)) :ScreenH (- (+ (* (* 34.0 %(fs2)s) _u) (* 12.0 _u)) (* 3.0 _u)))
    (if _hi
      (HUD|DrawText :Text (select (== _ph 11) "ESPERANDO RESET" "") :TextColor %(cweak)s :ScreenX (Math|Conversions|ToFloat(Integer) (Math|Float|Truncate (+ (- (+ _x _cw) (* 230.0 _u)) 0.5))) :ScreenY (Math|Conversions|ToFloat(Integer) (Math|Float|Truncate (+ (- (+ _y _ch) (* (* 34.0 %(fs2)s) _u)) 0.5))) :Font "/Game/InnerCanvas/UI/F_ICW24_IC.F_ICW24_IC" :Scale 1.0 :bScalePosition false)
      (else
        (HUD|DrawText :Text (select (== _ph 11) "ESPERANDO RESET" "") :TextColor %(cweak)s :ScreenX (Math|Conversions|ToFloat(Integer) (Math|Float|Truncate (+ (- (+ _x _cw) (* 230.0 _u)) 0.5))) :ScreenY (Math|Conversions|ToFloat(Integer) (Math|Float|Truncate (+ (- (+ _y _ch) (* (* 34.0 %(fs2)s) _u)) 0.5))) :Font "/Game/InnerCanvas/UI/F_ICW12_IC.F_ICW12_IC" :Scale 1.0 :bScalePosition false)))
    (if _hi
      (HUD|DrawText :Text (Utilities|String|ToString(Integer) (+ _i 1)) :TextColor %(num)s :ScreenX (Math|Conversions|ToFloat(Integer) (Math|Float|Truncate (+ (+ _x (* 16.0 _u)) 0.5))) :ScreenY (Math|Conversions|ToFloat(Integer) (Math|Float|Truncate (+ (+ _y (* 10.0 _u)) 0.5))) :Font "/Game/InnerCanvas/UI/F_ICW30_IC.F_ICW30_IC" :Scale 1.0 :bScalePosition false)
      (else
        (HUD|DrawText :Text (Utilities|String|ToString(Integer) (+ _i 1)) :TextColor %(num)s :ScreenX (Math|Conversions|ToFloat(Integer) (Math|Float|Truncate (+ (+ _x (* 16.0 _u)) 0.5))) :ScreenY (Math|Conversions|ToFloat(Integer) (Math|Float|Truncate (+ (+ _y (* 10.0 _u)) 0.5))) :Font "/Game/InnerCanvas/UI/F_ICW15_IC.F_ICW15_IC" :Scale 1.0 :bScalePosition false)))
    (if _hi
      (HUD|DrawText :Text %(nm)s :TextColor %(txt)s :ScreenX (Math|Conversions|ToFloat(Integer) (Math|Float|Truncate (+ (+ _x (* 16.0 _u)) 0.5))) :ScreenY (Math|Conversions|ToFloat(Integer) (Math|Float|Truncate (+ (- (+ _y _ch) (* (* 34.0 %(fs2)s) _u)) 0.5))) :Font "/Game/InnerCanvas/UI/F_ICW33_IC.F_ICW33_IC" :Scale 1.0 :bScalePosition false)
      (else
        (HUD|DrawText :Text %(nm)s :TextColor %(txt)s :ScreenX (Math|Conversions|ToFloat(Integer) (Math|Float|Truncate (+ (+ _x (* 16.0 _u)) 0.5))) :ScreenY (Math|Conversions|ToFloat(Integer) (Math|Float|Truncate (+ (- (+ _y _ch) (* (* 34.0 %(fs2)s) _u)) 0.5))) :Font "/Game/InnerCanvas/UI/F_ICW17_IC.F_ICW17_IC" :Scale 1.0 :bScalePosition false)))
    (if _hi
      (HUD|DrawText :Text (select _show _ts "") :TextColor %(txt)s :ScreenX (Math|Conversions|ToFloat(Integer) (Math|Float|Truncate (+ (- (+ _x _cw) (* (* 70.0 %(fs2)s) _u)) 0.5))) :ScreenY (Math|Conversions|ToFloat(Integer) (Math|Float|Truncate (+ (+ _y (* 10.0 _u)) 0.5))) :Font "/Game/InnerCanvas/UI/F_ICW33_IC.F_ICW33_IC" :Scale 1.0 :bScalePosition false)
      (else
        (HUD|DrawText :Text (select _show _ts "") :TextColor %(txt)s :ScreenX (Math|Conversions|ToFloat(Integer) (Math|Float|Truncate (+ (- (+ _x _cw) (* (* 70.0 %(fs2)s) _u)) 0.5))) :ScreenY (Math|Conversions|ToFloat(Integer) (Math|Float|Truncate (+ (+ _y (* 10.0 _u)) 0.5))) :Font "/Game/InnerCanvas/UI/F_ICW17_IC.F_ICW17_IC" :Scale 1.0 :bScalePosition false)))
    (HUD|DrawRect :RectColor %(inkbg)s :ScreenX (+ _x (* 16.0 _u)) :ScreenY (- (+ _y _ch) (* 14.0 _u)) :ScreenW (- _cw (* 32.0 _u)) :ScreenH (* 5.0 _u))
    (HUD|DrawRect :RectColor %(ink)s :ScreenX (+ _x (* 16.0 _u)) :ScreenY (- (+ _y _ch) (* 14.0 _u)) :ScreenW (* (- _cw (* 32.0 _u)) (select _show (Math|Float|Clamp(Float) %(inkv)s) 0.0)) :ScreenH (* 5.0 _u))))
''' % dict(bg=D('BgColor'), ph=W2('Phases', '_i'), tl=W2('TL', '_i'), rt=W2('RTs', '_i'), white=LC(1.0, 1.0, 1.0, 1.0), z2=V2('0.0', '0.0'),
           num=D('NumColor'), font=WFONT, mfont=MFONT, sfont=SFONT, fs=D('FS'), nm=W2('Names', '_i'), txt=D('TextColor'), fs2=D('FS2'), inkbg=D('InkBg'), ink=D('InkColor'),
           inkv=W2('Inks', '_i'), band=LC(0.0, 0.035, 0.03, 0.5), lrx=W2('LastRx', '_i'),
           cok=LC(0.3, 1.0, 0.45, 1.0), cweak=LC(1.0, 0.7, 0.15, 1.0), coff=LC(1.0, 0.3, 0.25, 1.0),
           ac=D('ArmCell'), am=D('ArmMode'), at=D('ArmT'), carm=LC(0.85, 0.5, 0.05, 0.95), cbtn=LC(0.05, 0.3, 0.2, 0.9),
           cbtn2=LC(0.12, 0.16, 0.15, 0.9))

# OnBtn: clic en RESET (R) o REINICIAR (S) de un cuadro. El primer clic arma el boton (dice "¿SEGURO?" 3 s), el segundo manda la orden.
CODES['OnBtn'] = '''(fn OnBtn (Box)
  (bind _m (select (Utilities|String|EqualExactly(String) (Utilities|String|Left Box 1) "R") 1 2))
  (bind _i (Utilities|String|StringToInteger (Utilities|String|GetSubstring Box 1 2)))
  (bind _now (Utilities|Time|GetGameTimeInSeconds))
  (if (and (== %(ac)s _i) (and (== %(am)s _m) (< (- _now %(at)s) 3.0)))
    (Class|BPICWallIC|SendCmd :self %(w)s :Cell _i :Mode _m)
    %(ac0)s
    (else
      %(acs)s
      %(ams)s
      %(ats)s)))
''' % dict(ac=D('ArmCell'), am=D('ArmMode'), at=D('ArmT'), w=D('Wall'), ac0=DS('ArmCell', '-1'), acs=DS('ArmCell', '_i'),
           ams=DS('ArmMode', '_m'), ats=DS('ArmT', '_now'))

CODES['DrawWall'] = '''(fn DrawWall (W H)
  (CallFunction|FindWall)
  (Utilities|IsValid %s
    (:"Is Valid"
      (CallFunction|DrawCells :W W :H H))))
''' % D('Wall')

ORDER = ['FindWall', 'DrawCells', 'OnBtn', 'DrawWall']
EVG = '''(event EventBeginPlay
  (Class|PlayerController|SetShowMouseCursor :self (HUD|GetOwningPlayerController) :bShowMouseCursor false)
  (Class|PlayerController|SetEnableClickEvents :self (HUD|GetOwningPlayerController) :bEnableClickEvents false)
  (Variables|Default|SetArmCell -1))

(event EventHitBoxClicked (BoxName)
  (CallFunction|OnBtn :Box (Utilities|String|ToString(Name) BoxName)))

(event EventReceiveDrawHUD (SizeX SizeY)
  (CallFunction|DrawWall :W (Math|Conversions|ToFloat(Integer) SizeX) :H (Math|Conversions|ToFloat(Integer) SizeY)))
'''
