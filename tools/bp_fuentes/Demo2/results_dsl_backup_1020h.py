# results_dsl.py - BP_DemoResults_SC: el cuadro de resultados de la demo (modelo curvo SM_DemoResults_*_SC, 2026-10-19)
# Contenido: dibujado con Canvas en 4 render targets (1 px = 1 mm) que se ven en el vidrio (slot Pane) de cada ventana.
# Rotulos y numero grande: TextRender (nitidos). Datos: BP_BioHub (casillas de 5 s del nivel), BP_BreathStage_SC.CycleScores,
# el historial de trazos y la tinta del dibujo.
D = lambda n: '(Variables|Default|Get%s)' % n
DS = lambda n, x: '(Variables|Default|Set%s %s)' % (n, x)
P = lambda s: '(Development|PrintString "%s" :bPrintToScreen false)' % s
CAM = '(Camera|GetCameraLocation (Game|GetPlayerCameraManager 0))'
CAMROT = '(Camera|GetCameraRotation (Game|GetPlayerCameraManager 0))'
PANE = '/Game/SoulCharger/Demo/Materials/M_DemoResPane_SC.M_DemoResPane_SC'
HUB = '/Game/SoulCharger/Core/Signals/BP_BioHub.BP_BioHub_C'
BST = '/Game/SoulCharger/Mechanics/Breath/Blueprints/BP_BreathStage_SC.BP_BreathStage_SC_C'
TBD = '/SC_Draw/Blueprints/BP_TBDirector_NC.BP_TBDirector_NC_C'
V2 = lambda x, y: '(Math|Vector2D|MakeVector2D %s %s)' % (x, y)
COL = lambda r, g, b: '(Utilities|Struct|MakeLinearColor %s %s %s 1.0)' % (r, g, b)
RT = lambda i: '(Utilities|Array|Get(acopy) %s %d)' % (D('RTs'), i)
LINE = lambda a, b, th, col: '(Canvas|DrawLine _cv :ScreenPositionA %s :ScreenPositionB %s :Thickness %s :RenderColor %s)' % (a, b, th, col)
BEGIN = lambda i: ('(Rendering|ClearRenderTarget2D :TextureRenderTarget %s :ClearColor (Utilities|Struct|MakeLinearColor 0.0 0.0 0.0 0.0))\n'
                   '  (bind (_cv _sz _ctx) (Rendering|BeginDrawCanvastoRenderTarget :TextureRenderTarget %s))') % (RT(i), RT(i))
END = '(Rendering|EndDrawCanvastoRenderTarget :Context _ctx)'
SETTEXT = lambda comp, txt: '(Rendering|Components|TextRender|SetText %s (Utilities|Text|ToText(String) %s))' % (comp, txt)
CODES = {}

def target(i, w, h, comp):
    return ('(bind _rt%d (Rendering|CreateRenderTarget2D :Width %d :Height %d :Format "RTF_RGBA8" :ClearColor (Utilities|Struct|MakeLinearColor 0.0 0.0 0.0 0.0) :bAutoGenerateMipMaps false))\n'
            '    (bind _mid%d (Rendering|Material|CreateDynamicMaterialInstance %s :ElementIndex 1 :SourceMaterial "%s"))\n'
            '    (Utilities|Array|Add %s _rt%d)\n'
            '    (Utilities|Array|Add %s _mid%d)\n'
            '    (Rendering|Material|SetTextureParameterValue _mid%d "Card" _rt%d)') % (i, w, h, i, comp, PANE, D('RTs'), i, D('MIDs'), i, i, i)

CODES['ResEnsure'] = '''(fn ResEnsure ()
  (if (< (Utilities|Array|Length %s) 4)
    (Utilities|Array|Clear %s)
    (Utilities|Array|Clear %s)
    %s
    %s
    %s
    %s))
''' % (D('RTs'), D('RTs'), D('MIDs'), target(0, 592, 142, D('WinEEG')), target(1, 592, 142, D('WinPulse')),
       target(2, 592, 142, D('WinBreath')), target(3, 272, 482, D('WinCalm')))

CODES['ResBoot'] = '''(fn ResBoot ()
  (Class|BPCAppearLuzSC|Prepare %s)
  (CallFunction|ResLabelsOn)
  (CallFunction|ResEnsure))
''' % D('AppearLuz')

CODES['ResLabelsOn'] = '''(fn ResLabelsOn ()
  (bind _on (and %s (>= (Class|BPCAppearLuzSC|GetAppearT %s) 0.85)))
  (Rendering|SetVisibility %s _on)
  (Rendering|SetVisibility %s _on)
  (Rendering|SetVisibility %s _on)
  (Rendering|SetVisibility %s _on)
  (Rendering|SetVisibility %s _on)
  (Rendering|SetVisibility %s (and _on (== %s 1))))
''' % (D('Shown'), D('AppearLuz'), D('LblEEG'), D('LblPulse'), D('LblBreath'), D('LblCalm'), D('Big'), D('Note'), D('Exp'))

CODES['ResHubCalm'] = '''(fn ResHubCalm (Hub)
  (for _i (range (Math|Integer|Min(Integer) (+ (Class|BPBioHub|GetCurrentBin Hub) 1) 180))
    (if (Class|BPBioHub|BinHasCalm Hub _i)
      (Utilities|Array|Add %s (Class|BPBioHub|GetCalmBinAvg Hub _i)))
    (if (Class|BPBioHub|BinHasHeart Hub _i)
      (Utilities|Array|Add %s (Class|BPBioHub|GetHeartBinAvg Hub _i)))))
''' % (D('SerCalm'), D('SerHeart'))

CODES['ResHub'] = '''(fn ResHub ()
  (bind _hub (Actor|GetActorOfClass "%s"))
  (Utilities|IsValid _hub
    (:"Is Valid"
      (CallFunction|ResHubCalm :Hub _hub))))
''' % HUB

CODES['ResBreath'] = '''(fn ResBreath ()
  (bind _bs (Actor|GetActorOfClass "%s"))
  (Utilities|IsValid _bs
    (:"Is Valid"
      %s)))
''' % (BST, DS('Scores', '(Class|BPBreathStageSC|GetCycleScores _bs)'))

CODES['ResDraw'] = '''(fn ResDraw ()
  (bind _tb (Actor|GetActorOfClass "%s"))
  (Utilities|IsValid _tb
    (:"Is Valid"
      %s
      %s)))
''' % (TBD, DS('NStrokes', '(Utilities|Array|Length (Class|BPCTBToolNC|GetStrokeHistory (Class|BPTBDirectorNC|GetTBTool _tb)))'),
       DS('InkM', '(Class|BPTBDirectorNC|GetInkUsed _tb)'))

CODES['ResData'] = '''(fn ResData ()
  (Utilities|Array|Clear %(sc)s)
  (Utilities|Array|Clear %(sh)s)
  (Utilities|Array|Clear %(scores)s)
  (CallFunction|ResHub)
  (if (== %(exp)s 0)
    (CallFunction|ResBreath)
    (else
      (CallFunction|ResDraw)))
  %(c0)s
  %(h0)s
  (for _v %(sc)s
    %(cadd)s)
  (for _v %(sh)s
    %(hadd)s)
  %(cavg)s
  %(havg)s
  %(hlo)s
  %(hhi)s
  (for _v %(sh)s
    %(hlo2)s
    %(hhi2)s)
  (Development|PrintString (Utilities|String|Append "RESULTADOS: casillas de calma " (Utilities|String|ToString(Integer) (Utilities|Array|Length %(sc)s))) :bPrintToScreen false))
''' % dict(sc=D('SerCalm'), sh=D('SerHeart'), scores=D('Scores'), exp=D('Exp'),
           c0=DS('CalmAvg', '0.0'), h0=DS('HeartAvg', '0.0'),
           cadd=DS('CalmAvg', '(+ %s _v)' % D('CalmAvg')), hadd=DS('HeartAvg', '(+ %s _v)' % D('HeartAvg')),
           cavg=DS('CalmAvg', '(/ %s (Math|Float|Max(Float) (Math|Conversions|ToFloat(Integer) (Utilities|Array|Length %s)) 1.0))' % (D('CalmAvg'), D('SerCalm'))),
           havg=DS('HeartAvg', '(/ %s (Math|Float|Max(Float) (Math|Conversions|ToFloat(Integer) (Utilities|Array|Length %s)) 1.0))' % (D('HeartAvg'), D('SerHeart'))),
           hlo=DS('HLo', '1000.0'), hhi=DS('HHi', '0.0'),
           hlo2=DS('HLo', '(Math|Float|Min(Float) %s _v)' % D('HLo')), hhi2=DS('HHi', '(Math|Float|Max(Float) %s _v)' % D('HHi')))

def graph(i, ser, ynorm, col, name):
    n = '(Utilities|Array|Length %s)' % ser
    x = lambda k: '(+ 20.0 (/ (* 552.0 (Math|Conversions|ToFloat(Integer) %s)) (Math|Float|Max(Float) (Math|Conversions|ToFloat(Integer) (- %s 1)) 1.0)))' % (k, n)
    y = lambda k: '(- 132.0 (* 94.0 %s))' % ynorm('(Utilities|Array|Get(acopy) %s %s)' % (ser, k))
    return '''(fn %s ()
  %s
  %s
  (if (>= %s 2)
    (for _i (range (- %s 1))
      %s))
  %s)
''' % (name, BEGIN(i), LINE(V2('20.0', '132.0'), V2('572.0', '132.0'), '1.0', COL(0.12, 0.12, 0.14)), n, n,
       LINE(V2(x('_i'), y('_i')), V2(x('(+ _i 1)'), y('(+ _i 1)')), '3.0', col), END)

CODES['DrawEEG'] = graph(0, D('SerCalm'), lambda v: '(Math|Float|Clamp(Float) %s 0.0 1.0)' % v, COL(0.55, 0.45, 1.0), 'DrawEEG')
CODES['DrawPulse'] = graph(1, D('SerHeart'),
                           lambda v: '(/ (- %s (- %s 3.0)) (Math|Float|Max(Float) (- (+ %s 3.0) (- %s 3.0)) 1.0))' % (v, D('HLo'), D('HHi'), D('HLo')),
                           COL(1.0, 0.4, 0.35), 'DrawPulse')

RING = lambda: '''(for _k (range 40)
        (bind _a0 (* 9.0 (Math|Conversions|ToFloat(Integer) _k)))
        (bind _a1 (* 9.0 (Math|Conversions|ToFloat(Integer) (+ _k 1))))
        %s)''' % LINE(V2('(+ _cx (* _r (Math|Trig|Cos(Degrees) _a0)))', '(+ 76.0 (* _r (Math|Trig|Sin(Degrees) _a0)))'),
                      V2('(+ _cx (* _r (Math|Trig|Cos(Degrees) _a1)))', '(+ 76.0 (* _r (Math|Trig|Sin(Degrees) _a1)))'), '2.5', COL(0.4, 1.0, 0.85))
CODES['DrawBreath'] = '''(fn DrawBreath ()
  %s
  (bind _n (Utilities|Array|Length %s))
  (bind _sp (/ 552.0 (Math|Float|Max(Float) (Math|Conversions|ToFloat(Integer) _n) 1.0)))
  (if (== %s 0)
    (for _i (range _n)
      (bind _cx (+ 20.0 (* _sp (+ (Math|Conversions|ToFloat(Integer) _i) 0.5))))
      (bind _r (Math|Float|Min(Float) (+ 10.0 (* 44.0 (Math|Float|Clamp(Float) (Utilities|Array|Get(acopy) %s _i) 0.0 1.0))) (* 0.45 _sp)))
      %s))
  %s)
''' % (BEGIN(2), D('Scores'), D('Exp'), D('Scores'), RING(), END)

CODES['DrawCalm'] = '''(fn DrawCalm ()
  %s
  %s
  (if (> (Utilities|Array|Length %s) 0)
    %s)
  %s)
''' % (BEGIN(3), LINE(V2('36.0', '420.0'), V2('236.0', '420.0'), '8.0', COL(0.18, 0.18, 0.2)), D('SerCalm'),
       LINE(V2('36.0', '420.0'), V2('(+ 36.0 (* 200.0 (Math|Float|Clamp(Float) %s 0.0 1.0)))' % D('CalmAvg'), '420.0'), '8.0', COL(1.0, 0.7, 0.35)), END)

CODES['ResLabels'] = '''(fn ResLabels ()
  (bind _nc (Utilities|Array|Length %(sc)s))
  (bind _nh (Utilities|Array|Length %(sh)s))
  %(eeg)s
  %(pulse)s
  %(breath)s
  %(calm)s
  %(big)s
  %(note)s)
''' % dict(sc=D('SerCalm'), sh=D('SerHeart'),
           eeg=SETTEXT(D('LblEEG'), '(select (>= _nc 2) "NEURAL ACTIVITY" "NEURAL ACTIVITY  -  no signal")'),
           pulse=SETTEXT(D('LblPulse'), '(select (>= _nh 2) (Utilities|String|Append "PULSE  -  " (Utilities|String|Append (Utilities|String|ToString(Integer) (Math|Float|Round %s)) " bpm")) "PULSE  -  no signal")' % D('HeartAvg')),
           breath=SETTEXT(D('LblBreath'), '(select (== %s 0) "BREATH CYCLES" "YOUR DRAWING")' % D('Exp')),
           calm=SETTEXT(D('LblCalm'), '"CALM INDEX"'),
           big=SETTEXT(D('Big'), '(select (> _nc 0) (Utilities|String|ToString(Integer) (Math|Float|Round (* 100.0 %s))) "--")' % D('CalmAvg')),
           note=SETTEXT(D('Note'), '(Utilities|String|Append (Utilities|String|ToString(Integer) %s) (select (== %s 1) " stroke of light" " strokes of light"))' % (D('NStrokes'), D('NStrokes'))))

CODES['ResPlace'] = '''(fn ResPlace ()
  (bind _yaw (.yaw (Transformation|GetActorRotation (Actor|GetActorOfClass "/Script/Engine.PlayerStart"))))
  (bind _fwd (Math|Vector|MakeVector (Math|Trig|Cos(Degrees) _yaw) (Math|Trig|Sin(Degrees) _yaw) 0.0))
  (Transformation|SetActorLocationAndRotation :NewLocation (+ %s (+ (* _fwd %s) (Math|Vector|MakeVector 0.0 0.0 (* -1.0 %s)))) :NewRotation (Math|Rotator|MakeRotator 0.0 0.0 (+ _yaw 180.0)) :bSweep false :bTeleport true))
''' % (CAM, D('Dist'), D('Drop'))

CODES['ResShow'] = '''(fn ResShow ()
  (CallFunction|ResEnsure)
  (CallFunction|ResPlace)
  (CallFunction|ResData)
  (CallFunction|DrawEEG)
  (CallFunction|DrawPulse)
  (CallFunction|DrawBreath)
  (CallFunction|DrawCalm)
  (CallFunction|ResLabels)
  (Rendering|Material|SetMaterial %s 0 %s)
  (Rendering|Material|SetMaterial %s 1 %s)
  (Class|BPCAppearLuzSC|Appear %s)
  %s
  %s)
''' % (D('Base'), D('BodyMat'), D('Base'), D('RingMat'), D('AppearLuz'), DS('Shown', 'true'), P('RESULTADOS: aparece el cuadro'))

CODES['ResHide'] = '''(fn ResHide ()
  (Class|BPCAppearLuzSC|Vanish %s)
  %s
  %s)
''' % (D('AppearLuz'), DS('Shown', 'false'), P('RESULTADOS: se va el cuadro'))

FADE = lambda c: '(Rendering|Material|SetScalarParameterValueonMaterials %s "Fade" _k)' % c
CODES['ResTick'] = '''(fn ResTick ()
  (bind _at (Class|BPCAppearLuzSC|GetAppearT %s))
  (bind _m (Math|Float|MapRangeClamped _at 0.6 1.0 0.0 1.0))
  (bind _k (* _m (* _m (- 3.0 (* 2.0 _m)))))
  %s
  %s
  %s
  %s
  (CallFunction|ResLabelsOn))
''' % (D('AppearLuz'), FADE(D('WinEEG')), FADE(D('WinPulse')), FADE(D('WinBreath')), FADE(D('WinCalm')))

ORDER = ['ResEnsure', 'ResLabelsOn', 'ResBoot', 'ResHubCalm', 'ResHub', 'ResBreath', 'ResDraw', 'ResData', 'DrawEEG', 'DrawPulse',
         'DrawBreath', 'DrawCalm', 'ResLabels', 'ResPlace', 'ResShow', 'ResHide', 'ResTick']
EVG = '''(event EventBeginPlay
  (CallFunction|ResBoot))

(event EventTick (DeltaSeconds)
  (CallFunction|ResTick))
'''
