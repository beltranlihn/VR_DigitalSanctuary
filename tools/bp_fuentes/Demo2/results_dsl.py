# results_dsl.py - BP_DemoResults_SC: el cuadro de resultados de la demo (modelo curvo SM_DemoResults_*_SC, 2026-10-19)
# Contenido: dibujado con Canvas en 4 render targets (1 px = 1 mm) que se ven en el vidrio (slot Pane) de cada ventana.
# 21-10: TODO es textura, tambien los rotulos y el numero grande (Beltran: "en Soul Charger usamos texturas, no TextRender").
# Cada ventana se dibuja en un RT de trabajo a 2 px/mm (lineas + texto Quicksand) y se reduce 2:1 a su RT de 1 px/mm con
# DrawTexture (bilineal exacto a 2:1 = promedio de 2x2: un mip a mano). 1 px/mm es ~1,5x la densidad del visor a 1,6 m.
# Los TextRender quedan siempre ocultos. Datos: BP_BioHub (casillas de 5 s del nivel), BP_BreathStage_SC.CycleScores,
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
HMC = '/Game/SoulCharger/Mechanics/Heart/Blueprints/BP_HeartManager_SC.BP_HeartManager_SC_C'
V2 = lambda x, y: '(Math|Vector2D|MakeVector2D %s %s)' % (x, y)
COL = lambda r, g, b: '(Utilities|Struct|MakeLinearColor %s %s %s 1.0)' % (r, g, b)
RT = lambda i: '(Utilities|Array|Get(acopy) %s %d)' % (D('RTs'), i)
LINE = lambda a, b, th, col: '(Canvas|DrawLine _cv :ScreenPositionA %s :ScreenPositionB %s :Thickness %s :RenderColor %s)' % (a, b, th, col)
BEGIN = lambda i: ('(Rendering|ClearRenderTarget2D :TextureRenderTarget %s :ClearColor (Utilities|Struct|MakeLinearColor 0.0 0.0 0.0 0.0))\n'
                   '  (bind (_cv _sz _ctx) (Rendering|BeginDrawCanvastoRenderTarget :TextureRenderTarget %s))') % (RT(i), RT(i))
END = '(Rendering|EndDrawCanvastoRenderTarget :Context _ctx)'
SETTEXT = lambda comp, txt: '(Rendering|Components|TextRender|SetText %s (Utilities|Text|ToText(String) %s))' % (comp, txt)
CODES = {}

# S = escala del RT de TRABAJO (2 px/mm); el RT final de cada ventana es de 1 px/mm. SC() lleva mm a pixeles de trabajo.
S = 2
SC = lambda v: '%.1f' % (v * S)
FONT = '/Game/SoulCharger/Core/Font/Quicksand-SemiBold_Font.Quicksand-SemiBold_Font'
FONT_BASE = 9.0  # LegacyFontSize de la fuente: Scale = puntos / 9
PT = lambda em_mm: '%.3f' % (em_mm * S * 0.75 / FONT_BASE)  # em en mm -> pixeles de trabajo -> puntos (96 dpi) -> Scale
CLEAR0 = '(Utilities|Struct|MakeLinearColor 0.0 0.0 0.0 0.0)'
# 22-10 (feria): el numero grande se veia pixelado. Canvas rasteriza el glifo al LegacyFontSize de la fuente (DPIScale 1:
# CanvasItem.cpp, DrawStringInternal_RuntimeCache) y AGRANDA el bitmap por Scale: a 9 pt el numero iba x16,7. Con una copia
# de la fuente a 120 pt el glifo sale casi a su tamano final (x1,25 en el RT de trabajo, despues 2:1).
FONT_BIG = '/Game/SoulCharger/Demo/Fonts/Quicksand-SemiBold_Big_SC.Quicksand-SemiBold_Big_SC'
FONT_BIG_BASE = 120.0


def TEXT(x, y, s, sc, cx='true'):
    return ('(Canvas|DrawText _cv :RenderFont "%s" :RenderText %s :ScreenPosition %s :Scale %s :RenderColor %s :Kerning 0.0 '
            ':ShadowColor %s :ShadowOffset %s :bCentreX %s :bCentreY true :bOutlined false :OutlineColor %s)') % (
        FONT, s, V2(x, y), V2(sc, sc), COL(1.0, 1.0, 1.0), CLEAR0, V2('0.0', '0.0'), cx, CLEAR0)

def TEXTF(font, x, y, s, sc, cx='true'):
    return ('(Canvas|DrawText _cv :RenderFont "%s" :RenderText %s :ScreenPosition %s :Scale %s :RenderColor %s :Kerning 0.0 '
            ':ShadowColor %s :ShadowOffset %s :bCentreX %s :bCentreY true :bOutlined false :OutlineColor %s)') % (
        font, s, V2(x, y), V2(sc, sc), COL(1.0, 1.0, 1.0), CLEAR0, V2('0.0', '0.0'), cx, CLEAR0)


def target(i, w, h, comp):
    return ('(bind _rt%d (Rendering|CreateRenderTarget2D :Width %d :Height %d :Format "RTF_RGBA8" :ClearColor (Utilities|Struct|MakeLinearColor 0.0 0.0 0.0 0.0) :bAutoGenerateMipMaps false))\n'
            '    (bind _mid%d (Rendering|Material|CreateDynamicMaterialInstance %s :ElementIndex 1 :SourceMaterial "%s"))\n'
            '    (Utilities|Array|Add %s _rt%d)\n'
            '    (Utilities|Array|Add %s _mid%d)\n'
            '    (Rendering|Material|SetTextureParameterValue _mid%d "Card" _rt%d)') % (i, w, h, i, comp, PANE, D('RTs'), i, D('MIDs'), i, i, i)


def work(i, w, h):
    return ('(bind _rt%d (Rendering|CreateRenderTarget2D :Width %d :Height %d :Format "RTF_RGBA8" :ClearColor (Utilities|Struct|MakeLinearColor 0.0 0.0 0.0 0.0) :bAutoGenerateMipMaps false))\n'
            '    (Utilities|Array|Add %s _rt%d)') % (i, w * S, h * S, D('RTs'), i)


# RTs 0-3: finales de cada ventana (1 px/mm); 4: trabajo de las ventanas anchas; 5: trabajo de la de calma
CODES['ResEnsure'] = '''(fn ResEnsure ()
  (if (< (Utilities|Array|Length %s) 6)
    (Utilities|Array|Clear %s)
    (Utilities|Array|Clear %s)
    %s
    %s
    %s
    %s
    %s
    %s))
''' % (D('RTs'), D('RTs'), D('MIDs'), target(0, 592, 142, D('WinEEG')), target(1, 592, 142, D('WinPulse')),
       target(2, 592, 142, D('WinBreath')), target(3, 272, 482, D('WinCalm')), work(4, 592, 142), work(5, 272, 482))


def DOWN(i, k, w, h):
    # reduce el RT de trabajo k al RT final i: opaco (copia rgba) y bilineal exacto a 2:1
    return ('(Rendering|ClearRenderTarget2D :TextureRenderTarget %s :ClearColor %s)\n'
            '  (bind (_cv2 _sz2 _ctx2) (Rendering|BeginDrawCanvastoRenderTarget :TextureRenderTarget %s))\n'
            '  (Canvas|DrawTexture _cv2 :RenderTexture %s :ScreenPosition %s :ScreenSize %s :CoordinatePosition %s :CoordinateSize %s '
            ':RenderColor %s :BlendMode "BLEND_Opaque" :Rotation 0.0 :PivotPoint %s)\n'
            '  (Rendering|EndDrawCanvastoRenderTarget :Context _ctx2)') % (
        RT(i), CLEAR0, RT(i), RT(k), V2('0.0', '0.0'), V2('%.1f' % w, '%.1f' % h), V2('0.0', '0.0'), V2('1.0', '1.0'),
        COL(1.0, 1.0, 1.0), V2('0.5', '0.5'))

CODES['ResBoot'] = '''(fn ResBoot ()
  (Class|BPCAppearLuzSC|Prepare %s)
  (CallFunction|ResLabelsOn)
  (CallFunction|ResEnsure))
''' % D('AppearLuz')

# 21-10: los rotulos van en la textura de cada ventana; los TextRender quedan siempre ocultos
CODES['ResLabelsOn'] = '''(fn ResLabelsOn ()
  (Rendering|SetVisibility %s false)
  (Rendering|SetVisibility %s false)
  (Rendering|SetVisibility %s false)
  (Rendering|SetVisibility %s false)
  (Rendering|SetVisibility %s false)
  (Rendering|SetVisibility %s false))
''' % (D('LblEEG'), D('LblPulse'), D('LblBreath'), D('LblCalm'), D('Big'), D('Note'))

CODES['ResHubCalm'] = '''(fn ResHubCalm (Hub)
  (for _i (range (Math|Integer|Min(Integer) (+ (Class|BPBioHub|GetCurrentBin Hub) 1) 180))
    (if (Class|BPBioHub|BinHasCalm Hub _i)
      (Utilities|Array|Add %s (Class|BPBioHub|GetCalmBinAvg Hub _i)))
    (if (Class|BPBioHub|BinHasHeart Hub _i)
      (Utilities|Array|Add %s (Class|BPBioHub|GetHeartBinAvg Hub _i)))))
''' % (D('SerCalm'), D('SerHeart'))

# 20-10 noche: CALM INDEX = el indice de calma de Muse Integration (% vs la calibracion, con signo), no el promedio de la calma.
# BioHub.CalmIndexOut da -999 si nunca llego (ni real ni simulado): el cuadro dice "--".
CODES['ResHub'] = '''(fn ResHub ()
  (bind _hub (Actor|GetActorOfClass "%s"))
  (Utilities|IsValid _hub
    (:"Is Valid"
      (CallFunction|ResHubCalm :Hub _hub)
      %s)))
''' % (HUB, DS('CalmIdx', '(select (Class|BPBioHub|GetCalmIdxSeen _hub) (Class|BPBioHub|GetCalmIdx _hub) -999.0)'))

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

# ResHeart (Exp 2): los latidos sentidos = pulsos x BeatDiv; un circulo por pulso (hasta 24) en la tercera ventana
CODES['ResHeart'] = '''(fn ResHeart ()
  (bind _hm (Actor|GetActorOfClass "%s"))
  (Utilities|IsValid _hm
    (:"Is Valid"
      %s
      (for _i (range (Math|Integer|Min(Integer) (Class|BPHeartManagerSC|GetBeatCount _hm) 24))
        (Utilities|Array|Add %s 0.12)))))
''' % (HMC, DS('NBeats', '(* (Class|BPHeartManagerSC|GetBeatCount _hm) (Class|BPHeartManagerSC|GetBeatDiv _hm))'), D('Scores'))

CODES['ResData'] = '''(fn ResData ()
  (Utilities|Array|Clear %(sc)s)
  (Utilities|Array|Clear %(sh)s)
  (Utilities|Array|Clear %(scores)s)
  %(ci0)s
  (CallFunction|ResHub)
  (if (== %(exp)s 0)
    (CallFunction|ResBreath)
    (elif (== %(exp)s 2)
      (CallFunction|ResHeart)
      (else
        (CallFunction|ResDraw))))
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
''' % dict(sc=D('SerCalm'), sh=D('SerHeart'), scores=D('Scores'), exp=D('Exp'), ci0=DS('CalmIdx', '-999.0'),
           c0=DS('CalmAvg', '0.0'), h0=DS('HeartAvg', '0.0'),
           cadd=DS('CalmAvg', '(+ %s _v)' % D('CalmAvg')), hadd=DS('HeartAvg', '(+ %s _v)' % D('HeartAvg')),
           cavg=DS('CalmAvg', '(/ %s (Math|Float|Max(Float) (Math|Conversions|ToFloat(Integer) (Utilities|Array|Length %s)) 1.0))' % (D('CalmAvg'), D('SerCalm'))),
           havg=DS('HeartAvg', '(/ %s (Math|Float|Max(Float) (Math|Conversions|ToFloat(Integer) (Utilities|Array|Length %s)) 1.0))' % (D('HeartAvg'), D('SerHeart'))),
           hlo=DS('HLo', '1000.0'), hhi=DS('HHi', '0.0'),
           hlo2=DS('HLo', '(Math|Float|Min(Float) %s _v)' % D('HLo')), hhi2=DS('HHi', '(Math|Float|Max(Float) %s _v)' % D('HHi')))

# rotulo de las ventanas anchas: arriba a la izquierda (x 20 mm, centro en y 26 mm), em 24 mm (el WorldSize 2,4 del TextRender).
# El grafico va de y 132 (0) a 48 (1) y los circulos se centran en y 84 con radio <= 46: nada toca el rotulo.
LABEL = lambda s: TEXT(SC(20), SC(26), s, PT(24), 'false')
TXT_EEG = '(select (>= (Utilities|Array|Length %s) 2) "NEURAL ACTIVITY" "NEURAL ACTIVITY  -  no signal")' % D('SerCalm')
TXT_PULSE = ('(select (>= (Utilities|Array|Length %s) 2) (Utilities|String|Append "PULSE  -  " (Utilities|String|Append '
             '(Utilities|String|ToString(Integer) (Math|Float|Round %s)) " bpm")) "PULSE  -  no signal")') % (D('SerHeart'), D('HeartAvg'))
TXT_BREATH = ('(select (== %s 0) "BREATH CYCLES" (select (== %s 2) (Utilities|String|Append "HEARTBEATS FELT  -  " '
              '(Utilities|String|ToString(Integer) %s)) "YOUR DRAWING"))') % (D('Exp'), D('Exp'), D('NBeats'))
TXT_NOTE = ('(Utilities|String|Append (Utilities|String|ToString(Integer) %s) (select (== %s 1) " stroke of light" " strokes of light"))'
            % (D('NStrokes'), D('NStrokes')))
TXT_BIG = ('(select (> %s -500.0) (Utilities|String|Append (Utilities|String|Append (select (> (Math|Float|Round %s) 0) "+" "") '
           '(Utilities|String|ToString(Integer) (Math|Float|Round %s))) "%%") "--")') % (D('CalmIdx'), D('CalmIdx'), D('CalmIdx'))


# 22-10 (feria): la curva se veia poligonal (rectas entre las casillas de 5 s del BioHub). Ahora es Catmull-Rom: pasa por
# cada casilla real (no inventa picos) con GK tramos rectos entre punto y punto, y se recorta a la ventana.
GK = 6
CR = lambda a, b, c, d, t: ('(* 0.5 (+ (* 2.0 %(b)s) (+ (* (- %(c)s %(a)s) %(t)s) (+ (* (+ (- (* 2.0 %(a)s) (* 5.0 %(b)s)) (- (* 4.0 %(c)s) %(d)s)) (* %(t)s %(t)s)) '
                            '(* (+ (- (* 3.0 %(b)s) %(a)s) (- %(d)s (* 3.0 %(c)s))) (* %(t)s (* %(t)s %(t)s)))))))') % dict(a=a, b=b, c=c, d=d, t=t)


def graph(i, ser, ynorm, col, name, label):
    n = '(Utilities|Array|Length %s)' % ser
    xs = lambda k: '(+ %s (/ (* %s %s) (Math|Float|Max(Float) (Math|Conversions|ToFloat(Integer) (- %s 1)) 1.0)))' % (SC(20), SC(552), k, n)
    yv = lambda k: ynorm('(Utilities|Array|Get(acopy) %s %s)' % (ser, k))
    yp = lambda v: '(- %s (* %s (Math|Float|Clamp(Float) %s 0.0 1.0)))' % (SC(132), SC(84), v)
    t0 = '(/ (Math|Conversions|ToFloat(Integer) _j) %d.0)' % GK
    t1 = '(/ (Math|Conversions|ToFloat(Integer) (+ _j 1)) %d.0)' % GK
    fi = '(Math|Conversions|ToFloat(Integer) _i)'
    return '''(fn %s ()
  %s
  %s
  (if (>= %s 2)
    (for _i (range (- %s 1))
      (bind _ya %s)
      (bind _yb %s)
      (bind _yc %s)
      (bind _yd %s)
      (for _j (range %d)
        %s)))
  %s
  %s
  %s)
''' % (name, BEGIN(4), LINE(V2(SC(20), SC(132)), V2(SC(572), SC(132)), SC(1), COL(0.12, 0.12, 0.14)), n, n,
       yv('(Math|Integer|Max(Integer) (- _i 1) 0)'), yv('_i'), yv('(+ _i 1)'), yv('(Math|Integer|Min(Integer) (+ _i 2) (- %s 1))' % n), GK,
       LINE(V2(xs('(+ %s %s)' % (fi, t0)), yp(CR('_ya', '_yb', '_yc', '_yd', t0))),
            V2(xs('(+ %s %s)' % (fi, t1)), yp(CR('_ya', '_yb', '_yc', '_yd', t1))), SC(3), col),
       LABEL(label), END, DOWN(i, 4, 592, 142))

CODES['DrawEEG'] = graph(0, D('SerCalm'), lambda v: '(Math|Float|Clamp(Float) %s 0.0 1.0)' % v, COL(0.55, 0.45, 1.0), 'DrawEEG', TXT_EEG)
CODES['DrawPulse'] = graph(1, D('SerHeart'),
                           lambda v: '(/ (- %s (- %s 3.0)) (Math|Float|Max(Float) (- (+ %s 3.0) (- %s 3.0)) 1.0))' % (v, D('HLo'), D('HHi'), D('HLo')),
                           COL(1.0, 0.4, 0.35), 'DrawPulse', TXT_PULSE)

RING = lambda: '''(for _k (range 40)
        (bind _a0 (* 9.0 (Math|Conversions|ToFloat(Integer) _k)))
        (bind _a1 (* 9.0 (Math|Conversions|ToFloat(Integer) (+ _k 1))))
        %s)''' % LINE(V2('(+ _cx (* _r (Math|Trig|Cos(Degrees) _a0)))', '(+ %s (* _r (Math|Trig|Sin(Degrees) _a0)))' % SC(84)),
                      V2('(+ _cx (* _r (Math|Trig|Cos(Degrees) _a1)))', '(+ %s (* _r (Math|Trig|Sin(Degrees) _a1)))' % SC(84)), SC(2.5), COL(0.4, 1.0, 0.85))
RINGH = lambda: '''(for _k (range 40)
        (bind _a0 (* 9.0 (Math|Conversions|ToFloat(Integer) _k)))
        (bind _a1 (* 9.0 (Math|Conversions|ToFloat(Integer) (+ _k 1))))
        %s)''' % LINE(V2('(+ _cx (* _r (Math|Trig|Cos(Degrees) _a0)))', '(+ %s (* _r (Math|Trig|Sin(Degrees) _a0)))' % SC(84)),
                      V2('(+ _cx (* _r (Math|Trig|Cos(Degrees) _a1)))', '(+ %s (* _r (Math|Trig|Sin(Degrees) _a1)))' % SC(84)), SC(2.5), COL(1.0, 0.45, 0.4))
CODES['DrawBreath'] = '''(fn DrawBreath ()
  %s
  (bind _n (Utilities|Array|Length %s))
  (bind _sp (/ %s (Math|Float|Max(Float) (Math|Conversions|ToFloat(Integer) _n) 1.0)))
  (if (== %s 0)
    (for _i (range _n)
      (bind _cx (+ %s (* _sp (+ (Math|Conversions|ToFloat(Integer) _i) 0.5))))
      (bind _r (Math|Float|Min(Float) (Math|Float|Min(Float) (+ %s (* %s (Math|Float|Clamp(Float) (Utilities|Array|Get(acopy) %s _i) 0.0 1.0))) (* 0.45 _sp)) %s))
      %s)
    (elif (== %s 2)
      (for _i (range _n)
        (bind _cx (+ %s (* _sp (+ (Math|Conversions|ToFloat(Integer) _i) 0.5))))
        (bind _r (Math|Float|Min(Float) (Math|Float|Min(Float) (+ %s (* %s (Math|Float|Clamp(Float) (Utilities|Array|Get(acopy) %s _i) 0.0 1.0))) (* 0.45 _sp)) %s))
        %s)))
  %s
  (if (== %s 1)
    %s)
  %s
  %s)
''' % (BEGIN(4), D('Scores'), SC(552), D('Exp'), SC(20), SC(10), SC(44), D('Scores'), SC(46), RING(), D('Exp'), SC(20), SC(10), SC(44), D('Scores'), SC(46), RINGH(),
       LABEL(TXT_BREATH), D('Exp'), TEXT(SC(296), SC(91), TXT_NOTE, PT(26)), END, DOWN(2, 4, 592, 142))

# 20-10 noche: barra divergente desde el centro (x 136): +100 % llega a 236 (calido), -100 % a 36 (frio). Dos if sin else para
# que EndDrawCanvas corra siempre.
CI = '(Math|Float|Clamp(Float) %s -100.0 100.0)' % D('CalmIdx')
# numero grande: em 100 mm, achicado si no entra en el 80 % del ancho de la ventana (ClippedTextSize; con 0 queda el de base)
BIG_SC = 100 * S * 0.75 / FONT_BIG_BASE
CODES['DrawCalm'] = '''(fn DrawCalm ()
  %s
  %s
  %s
  (if (and (> %s -500.0) (>= %s 0.0))
    %s)
  (if (and (> %s -500.0) (< %s 0.0))
    %s)
  %s
  (bind _big %s)
  (bind (_tw _th) (Math|Vector2D|BreakVector2D (Canvas|ClippedTextSize _cv :RenderFont "%s" :RenderText _big :Scale %s)))
  (bind _bs (* %s (Math|Float|Min(Float) 1.0 (/ %s (Math|Float|Max(Float) _tw 1.0)))))
  %s
  %s
  %s)
''' % (BEGIN(5), LINE(V2(SC(36), SC(420)), V2(SC(236), SC(420)), SC(8), COL(0.18, 0.18, 0.2)),
       LINE(V2(SC(136), SC(402)), V2(SC(136), SC(438)), SC(3), COL(0.55, 0.55, 0.6)),
       D('CalmIdx'), D('CalmIdx'), LINE(V2(SC(136), SC(420)), V2('(+ %s (* %s %s))' % (SC(136), '%.1f' % S, CI), SC(420)), SC(8), COL(1.0, 0.7, 0.35)),
       D('CalmIdx'), D('CalmIdx'), LINE(V2(SC(136), SC(420)), V2('(+ %s (* %s %s))' % (SC(136), '%.1f' % S, CI), SC(420)), SC(8), COL(0.45, 0.62, 1.0)),
       TEXT(SC(136), SC(46), '"CALM INDEX"', PT(26)),
       TXT_BIG, FONT_BIG, V2('%.3f' % BIG_SC, '%.3f' % BIG_SC), '%.3f' % BIG_SC, SC(272 * 0.8),
       TEXTF(FONT_BIG, SC(136), SC(241), '_big', '_bs'), END, DOWN(3, 5, 272, 482))

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
           # 21-10: en Heart el conteo va en el titulo (la nota tapaba la fila de circulos)
           breath=SETTEXT(D('LblBreath'), '(select (== %s 0) "BREATH CYCLES" (select (== %s 2) (Utilities|String|Append "HEARTBEATS FELT  -  " (Utilities|String|ToString(Integer) %s)) "YOUR DRAWING"))' % (D('Exp'), D('Exp'), D('NBeats'))),
           calm=SETTEXT(D('LblCalm'), '"CALM INDEX"'),
           big=SETTEXT(D('Big'), '(select (> %s -500.0) (Utilities|String|Append (Utilities|String|Append (select (> (Math|Float|Round %s) 0) "+" "") (Utilities|String|ToString(Integer) (Math|Float|Round %s))) "%%") "--")' % (D('CalmIdx'), D('CalmIdx'), D('CalmIdx'))),
           note=SETTEXT(D('Note'), '(select (== %s 2) (Utilities|String|Append (Utilities|String|ToString(Integer) %s) " heartbeats felt") (Utilities|String|Append (Utilities|String|ToString(Integer) %s) (select (== %s 1) " stroke of light" " strokes of light")))' % (D('Exp'), D('NBeats'), D('NStrokes'), D('NStrokes'))))

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
  %s
  (Class|BPCAppearLuzSC|Appear %s)
  %s
  %s)
''' % (D('Base'), D('BodyMat'), D('Base'), D('RingMat'), '%(tint)s', D('AppearLuz'), DS('Shown', 'true'), P('RESULTADOS: aparece el cuadro'))

# 21-10 noche (Beltran, arreglo 7): el fondo del cuadro (Sheet, MI_Results_Glass_SC) y el vidrio de las 4 ventanas toman el color
# de la experiencia (azul Breath, verde Draw, rojo Heart: el de su carta del menu) y el fondo es un poco mas transparente.
GCOL = lambda: ('(select (== %s 1) (Math|Vector|MakeVector 0.5 0.92 0.68) (select (== %s 2) (Math|Vector|MakeVector 0.98 0.55 0.52) '
                '(Math|Vector|MakeVector 0.55 0.64 0.98)))') % (D('Exp'), D('Exp'))
GLCOL = lambda: ('(select (== %s 1) (Utilities|Struct|MakeLinearColor 0.5 0.92 0.68 1.0) (select (== %s 2) (Utilities|Struct|MakeLinearColor 0.98 0.55 0.52 1.0) '
                 '(Utilities|Struct|MakeLinearColor 0.55 0.64 0.98 1.0)))') % (D('Exp'), D('Exp'))
# las ventanas: por componente (...onMaterials): el marco (MI_Results_Frame_SC) no tiene "Color" y su "Base" es vector, asi que solo
# cambia el vidrio. (Rendering|Material|SetVectorParameterValue sobre el MID lo resuelve el DSL como el de Material Parameter Collection.)
WINS = ['WinEEG', 'WinPulse', 'WinBreath', 'WinCalm']
TINT = '''(Rendering|Material|SetVectorParameterValueonMaterials %(sheet)s "Color" %(gc)s)
  (Rendering|Material|SetScalarParameterValueonMaterials %(sheet)s "Base" 0.16)
  (Rendering|Material|SetScalarParameterValueonMaterials %(sheet)s "Opacity" 0.45)
  %(wins)s''' % dict(sheet=D('Sheet'), gc=GCOL(),
                     wins='\n  '.join('(Rendering|Material|SetVectorParameterValueonMaterials %s "Color" %s)\n  (Rendering|Material|SetScalarParameterValueonMaterials %s "Base" 0.08)'
                                       % (D(w), GCOL(), D(w)) for w in WINS))
CODES['ResShow'] = CODES['ResShow'] % dict(tint=TINT)

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

ORDER = ['ResEnsure', 'ResLabelsOn', 'ResBoot', 'ResHubCalm', 'ResHub', 'ResBreath', 'ResDraw', 'ResHeart', 'ResData', 'DrawEEG', 'DrawPulse',
         'DrawBreath', 'DrawCalm', 'ResLabels', 'ResPlace', 'ResShow', 'ResHide', 'ResTick']
EVG = '''(event EventBeginPlay
  (CallFunction|ResBoot))

(event EventTick (DeltaSeconds)
  (CallFunction|ResTick))
'''
