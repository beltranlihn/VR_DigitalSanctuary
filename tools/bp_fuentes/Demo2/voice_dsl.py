# voice_dsl.py - el DSL de BP_DemoVoice_SC (la voz de la demo + subtitulos palabra por palabra bajo el HUD)
# 2026-10-24 (feria): idioma. LangES (lo pone el menu al elegir ENGLISH/ESPANOL; en los otros niveles sale de la opcion
# ?Lang=es de OpenLevel, leida en el primer VoiceTick). Say cambia el clip por su par de VoES (mismo indice que en VoEN) y
# el subtitulo se busca por el nombre del clip que suena (VO_X_ES). ShowHint busca <Id>_ES.
G = lambda arr, i: '(Utilities|Array|Get(acopy) (Variables|Default|Get%s) %s)' % (arr, i)
LW = '(Variables|Default|GetLineW)'
HUD = '/Game/SoulCharger/Shared/HUD/Blueprints/BP_SoulHUD3D_SC.BP_SoulHUD3D_SC_C'
CODES = {
'Say': '''(fn Say (Clip)
  (Variables|Default|SetClip2 Clip)
  (bind _i (Utilities|Array|FindItem (Variables|Default|GetVoEN) Clip))
  (if (and (Variables|Default|GetLangES) (>= _i 0))
    (Variables|Default|SetClip2 (Utilities|Array|Get(acopy) (Variables|Default|GetVoES) _i)))
  (Audio|Components|Audio|SetSound (Variables|Default|GetVoice) (Variables|Default|GetClip2))
  (Audio|Components|Audio|Play (Variables|Default|GetVoice) 0.0)
  (Variables|Default|SetCur (Utilities|Array|FindItem (Variables|Default|GetVoIds) (Utilities|GetObjectName (Variables|Default|GetClip2))))
  (Variables|Default|SetCard -1)
  (Variables|Default|SetT 0.0)
  (Variables|Default|SetDur (Class|SoundBase|GetDuration (Variables|Default|GetClip2)))
  (Variables|Default|SetSpeaking true)
  (Variables|Default|SetHint false)
  (Development|PrintString (Utilities|String|Append "VOZ: " (Utilities|GetObjectName (Variables|Default|GetClip2))) :bPrintToScreen false))
''',
'SubRef': '''(fn SubRef ()
  (Utilities|IsValid %s
    (:"Is Not Valid"
      (bind _lw (Utilities|Casting|CastToWBP_SubLine_SC :Object (UserInterface|GetUserWidgetObject (Variables|Default|GetSub)))
        (:then (Variables|Default|SetLineW _aswbp_sub_line_sc))
        (:CastFailed)))))
''' % LW,
'SubAttach': '''(fn SubAttach ()
  (bind _h (Actor|GetActorOfClass "%s"))
  (if (not (Variables|Default|GetAttached))
    (Utilities|IsValid _h
      (:"Is Valid"
        (Transformation|AttachActorToActor :ParentActor _h :LocationRule "SnapToTarget" :RotationRule "SnapToTarget" :ScaleRule "KeepWorld" :bWeldSimulatedBodies false)
        (Transformation|SetActorRelativeLocation :NewRelativeLocation (Variables|Default|GetOffset) :bSweep false :bTeleport false)
        (Variables|Default|SetAttached true)
        (UserInterface|SetManuallyRedraw (Variables|Default|GetSub) true)
        (Development|PrintString "VOZ: subtitulos colgados del HUD" :bPrintToScreen false)))))
''' % HUD,
'SubCard': '''(fn SubCard (C)
  (Variables|Default|SetCard C)
  (Class|WBPSubLineSC|Clear :self %s)
  (for _i (range %s)
    (Class|WBPSubLineSC|AddWord :self %s :Word %s)))
''' % (LW, G('CWN', 'C'), LW, G('Words', '(+ %s _i)' % G('CW0', 'C'))),
'SubCards': '''(fn SubCards ()
  (bind _c0 %s)
  (for _i (range %s)
    (if (and (>= (Variables|Default|GetT) %s) (and (< (Variables|Default|GetT) %s) (not (== (Variables|Default|GetCard) (+ _c0 _i)))))
      (CallFunction|SubCard :C (+ _c0 _i)))))
''' % (G('VoC0', '(Variables|Default|GetCur)'), G('VoCN', '(Variables|Default|GetCur)'), G('CS', '(+ _c0 _i)'), G('CE', '(+ _c0 _i)')),
'SubDraw': '''(fn SubDraw (Dt)
  (bind _cd (Variables|Default|GetCard))
  (bind _t (Variables|Default|GetT))
  (bind _lf (Math|Float|Max(Float) (Variables|Default|GetLineFade) 0.01))
  (Variables|Default|SetAlpha (Math|Float|Clamp(Float) (+ (Variables|Default|GetAlpha) (* Dt (select (and (or (Variables|Default|GetSpeaking) (Variables|Default|GetHint)) (Variables|Default|GetSubs)) 5.0 -5.0))) 0.0 1.0))
  (if (and (>= (Variables|Default|GetCur) 0) (>= _cd 0))
    (bind _a (* (Variables|Default|GetAlpha) (Math|Float|Min(Float) (Math|Float|Clamp(Float) (/ (- _t %s) _lf) 0.0 1.0) (Math|Float|Clamp(Float) (/ (- %s _t) _lf) 0.0 1.0))))
    (Class|WBPSubLineSC|LineAlpha :self %s :A _a)
    (for _i (range %s)
      (bind _k (Math|Float|Clamp(Float) (/ (- _t %s) (Math|Float|Max(Float) (Variables|Default|GetWordFade) 0.01)) 0.0 1.0))
      (Class|WBPSubLineSC|WordK :self %s :I _i :K (* _k (* _k (- 3.0 (* 2.0 _k)))) :Dim (Variables|Default|GetDim) :Rise (Variables|Default|GetRise)))
    (else
      (Class|WBPSubLineSC|LineAlpha :self %s :A 0.0))))
''' % (G('CS', '_cd'), G('CE', '_cd'), LW, G('CWN', '_cd'), G('WS', '(+ %s _i)' % G('CW0', '_cd')), LW, LW),
'ShowHint': '''(fn ShowHint (Id)
  (Variables|Default|SetCur (Utilities|Array|FindItem (Variables|Default|GetVoIds) (select (Variables|Default|GetLangES) (Utilities|String|Append Id "_ES") Id)))
  (Variables|Default|SetCard -1)
  (Variables|Default|SetT 0.0)
  (Variables|Default|SetHint true)
  (Development|PrintString (Utilities|String|Append "VOZ: pista " Id) :bPrintToScreen false))
''',
'HideHint': '''(fn HideHint ()
  (Variables|Default|SetHint false))
''',
'VoiceTick': '''(fn VoiceTick (Dt)
  (if (not (Variables|Default|GetLangInit))
    (Variables|Default|SetLangInit true)
    (Variables|Default|SetLangES (Utilities|String|Contains (GameOptions|ParseOption (Class|GameModeBase|GetOptionsString (Game|GetGameMode)) "Lang") "es"))
    (Development|PrintString (Utilities|String|Append "VOZ: idioma " (select (Variables|Default|GetLangES) "es" "en")) :bPrintToScreen false))
  (CallFunction|SubRef)
  (CallFunction|SubAttach)
  (if (Variables|Default|GetSpeaking)
    (Variables|Default|SetT (+ (Variables|Default|GetT) Dt))
    (if (>= (Variables|Default|GetT) (+ (Variables|Default|GetDur) 0.2))
      (Variables|Default|SetSpeaking false))
    (elif (Variables|Default|GetHint)
      (Variables|Default|SetT (+ (Variables|Default|GetT) Dt))))
  (if (or (or (Variables|Default|GetSpeaking) (Variables|Default|GetHint)) (> (Variables|Default|GetAlpha) 0.0))
    (Variables|Default|SetRedrawT 0.4)
    (else
      (Variables|Default|SetRedrawT (- (Variables|Default|GetRedrawT) Dt))))
  (if (> (Variables|Default|GetRedrawT) 0.0)
    (UserInterface|RequestRenderUpdate (Variables|Default|GetSub)))
  (Utilities|IsValid %s
    (:"Is Valid"
      (if (>= (Variables|Default|GetCur) 0)
        (CallFunction|SubCards))
      (CallFunction|SubDraw :Dt Dt))))
''' % LW,
}
ORDER = ['Say', 'SubRef', 'SubAttach', 'SubCard', 'SubCards', 'SubDraw', 'ShowHint', 'HideHint', 'VoiceTick']
EVG = '''(event EventTick (DeltaSeconds)
  (CallFunction|VoiceTick :Dt DeltaSeconds))
'''
