# edit_flow_1020t.py - 2026-10-20 (tarde, Beltran probo Heart y Breath en Unreal). Sobre flow_dsl.py (respaldo flow_dsl_backup_1020t.py).
# 1) Haptico al tomar: el pulso (SeqRig.Pulse, el de la Obra) se dispara 0,12 s DESPUES del agarre. Antes iba en el mismo cuadro y lo
#    pisaba la propia etapa: HeartManager.TourSleep y BreathRig.SetHandedness ponen la haptica en 0 en las dos manos (SetHapticsByValue).
# 2) El sensor que flota desaparece en el MISMO cuadro en que aparece el de la mano (antes se iba con la animacion de AppearLuz).
# 3) Lo que flota gira y se inclina (TiltDeg) para verse por todos lados; en Draw el mando se inclina menos.
# 4) El nivel arranca en NEGRO (el velo con Black, como termino el menu) y se abre a la escena; el titulo dura lo que digan
#    TitleO0/O1/TitleHide del nivel (sin el salto de 3,5 s que lo cortaba a los 5,5 s).
# 5) Breath: sin START. La ultima pagina es solo instruccion + voz; al terminar la voz se va el panel y arranca la etapa.
# 6) Heart: dos paginas. 1 = toma el sensor; 2 = ponlo en el pecho, con una figura que late en vivo (BeatEnv y el umbral del
#    HeartManager -> parametros Pulse / Zone del material de la imagen). A los HeartPulses (3) pulsos se va el panel.
import shutil
p = 'flow_dsl.py'
shutil.copy(p, 'flow_dsl_backup_1020t.py')
s = open(p, encoding='utf-8').read()


def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (s.count(a), a[:120])
    s = s.replace(a, b)


# --- 4) arranque en negro + titulo sin salto
rep("veil=D('Veil'), title=D('Title'), ctop=D('CTop'), chor=D('CHor'), tmi=D('TitleMI'),",
    "veil=D('Veil'), title=D('Title'), ctop=D('Black'), chor=D('Black'), tmi=D('TitleMI'),")
rep("  (bind _lt (select (< _rt 5.5) _rt (+ _rt 3.5)))", "  (bind _lt %(rt)s)")

# --- 3) ShowPanel guarda el yaw de reposo del objeto que flota
rep('''  %(pbase)s
  %(page0)s''', '''  %(pbase)s
  %(pyaw)s
  %(page0)s''')
rep("page0=DS('Page', '0'), pbase=", "page0=DS('Page', '0'), pyaw=DS('PedYaw', '(+ _yaw 180.0)'), pbase=")

# --- 3) PedSpin: gira + se inclina en dos ejes (fases distintas) + sube y baja
rep('''CODES['PedSpin'] = """(fn PedSpin ()
  (Transformation|AddActorWorldRotation %(ped)s (Math|Rotator|MakeRotator 0.0 0.0 (* %(spin)s (Math|Float|Min(Float) (Utilities|Time|GetWorldDeltaSeconds) 0.0333))) false true)
  (Transformation|SetActorLocation %(ped)s (+ %(base)s (Math|Vector|MakeVector 0.0 0.0 (* %(bob)s (Math|Trig|Sin(Radians) (* %(pt)s 1.6))))) false true))
""" % dict(ped=D('Pedestal'), spin=D('SpinDeg'), base=D('PedBase'), bob=D('BobCm'), pt=D('PT'))''',
    '''CODES['PedSpin'] = """(fn PedSpin ()
  (bind _tl (select (== %(exp)s 1) (* 0.35 %(tilt)s) %(tilt)s))
  (Transformation|SetActorLocationAndRotation %(ped)s (+ %(base)s (Math|Vector|MakeVector 0.0 0.0 (* %(bob)s (Math|Trig|Sin(Radians) (* %(pt)s 1.6))))) (Math|Rotator|MakeRotator (* _tl (Math|Trig|Sin(Radians) (* %(pt)s 0.9))) (* _tl (Math|Trig|Sin(Radians) (* %(pt)s 0.65))) (+ %(pyaw)s (* %(spin)s %(pt)s))) false true))
""" % dict(ped=D('Pedestal'), spin=D('SpinDeg'), base=D('PedBase'), bob=D('BobCm'), pt=D('PT'), exp=D('Exp'), tilt=D('TiltDeg'), pyaw=D('PedYaw'))''')

# --- 1) y 2) Grab: sin pulso en el cuadro del agarre; el sensor que flota se esconde en el acto
rep('''  (Class|BPSeqRigSC|SetRightHanded :self %(rig)s :bRightHanded %(r)s)
  (Class|BPSeqRigSC|Pulse :self %(rig)s :bRight %(r)s)
  (if (== %(exp)s 0)
    (Class|BPCAppearLuzSC|Vanish (Class|BPBioSensorArtSC|GetAppear (Utilities|Casting|CastToBP_BioSensorArt_SC %(ped)s)))''',
    '''  (Class|BPSeqRigSC|SetRightHanded :self %(rig)s :bRightHanded %(r)s)
  (if (== %(exp)s 0)
    (Rendering|SetActorHiddenInGame %(ped)s true)''')
rep('''    (elif (== %(exp)s 2)
      (Class|BPCAppearLuzSC|Vanish (Class|BPBioSensorArtSC|GetAppear (Utilities|Casting|CastToBP_BioSensorArt_SC %(ped)s)))''',
    '''    (elif (== %(exp)s 2)
      (Rendering|SetActorHiddenInGame %(ped)s true)''')
rep('''      (Class|BPTBDirectorNC|StageIntro %(tb)s))))
  %(go)s)''', '''      (Class|BPTBDirectorNC|StageIntro %(tb)s))))
  %(pp1)s
  %(go)s)''')
rep("           go=GOPH(2), hm=D('HM'))", "           go=GOPH(2), hm=D('HM'), pp1=DS('PulsePend', 'true'))")
rep("# Grab: haptico de la mano que toma (2026-10-20, pedido de Beltran) = BP_SeqRig_SC.Pulse, el de la Obra",
    "# Grab: haptico de la mano que toma (2026-10-20, pedido de Beltran) = BP_SeqRig_SC.Pulse, el de la Obra. Lo dispara FlowTick 0,12 s\n"
    "# despues (PulsePend): en el cuadro del agarre la etapa corta la haptica de las dos manos y se comia el pulso.")

# --- 1) FlowTick: el pulso pendiente
rep('''  (CallFunction|EnsureHands)
  (if %(shifted)s''', '''  (CallFunction|EnsureHands)
  (if (and %(pp)s (>= %(pt)s 0.12))
    %(pp0)s
    (Class|BPSeqRigSC|Pulse :self %(rig)s :bRight %(right)s))
  (if %(shifted)s''')
rep("rt=D('RT'), hold=D('Hold'), shifted=D('Shifted'), ph=D('Phase'), exp=D('Exp'))",
    "rt=D('RT'), hold=D('Hold'), shifted=D('Shifted'), ph=D('Phase'), exp=D('Exp'),\n"
    "           pp=D('PulsePend'), pp0=DS('PulsePend', 'false'), pt=D('PT'), rig=D('Rig'), right=D('Right'))")

# --- 5) Breath sin START
rep('''        %(page3)s
        (CallFunction|FPanel)
        (CallFunction|SaveHands)
        (Class|BPSeqRigSC|SetRightHanded :self %(rig)s :bRightHanded (not %(right)s))
        (Class|BPSeqRigSC|ResultsBeam %(rig)s true)
        %(lp)s
        (Class|BPShareButtonSC|Appear %(go)s)
        %(g5)s))
    (:5
      (CallFunction|PickGo))
    (:6
      (if (>= _pt 0.6)
        (Class|BPShareButtonSC|Vanish %(go)s)
        (Class|BPShareButtonSC|Vanish %(card)s)
        (Class|BPSeqRigSC|ResultsBeam %(rig)s false)
        (CallFunction|RestoreHands)
        %(g7)s))''', '''        %(page3)s
        (CallFunction|FPanel)
        %(g5)s))
    (:5
      (if (or (and (>= _pt 2.5) (not %(spk)s)) (or (>= _pt 25.0) (or (>= %(rp)s 6) (and (> %(ag)s 0.0) (>= _pt %(ag)s)))))
        %(p5)s
        %(g6)s))
    (:6
      (if (>= _pt 1.0)
        (Class|BPShareButtonSC|Vanish %(card)s)
        %(g7)s))''')
rep("           g1=GOPH(1), g3=GOPH(3), g4=GOPH(4), g5=GOPH(5), g7=GOPH(7), g8=GOPH(8), g9=GOPH(9), g10=GOPH(10), g15=GOPH(15),\n           page1=DS('Page', '1'), page2=DS('Page', '2'), page3=DS('Page', '3'), brig=D('BRig'), zone0=DS('ZoneT', '0.0'),",
    "           g1=GOPH(1), g3=GOPH(3), g4=GOPH(4), g5=GOPH(5), g6=GOPH(6), g7=GOPH(7), g8=GOPH(8), g9=GOPH(9), g10=GOPH(10), g15=GOPH(15),\n"
    "           p5=P('DEMOFLOW: Breath, termino la ultima instruccion: se va el panel'),\n"
    "           page1=DS('Page', '1'), page2=DS('Page', '2'), page3=DS('Page', '3'), brig=D('BRig'), zone0=DS('ZoneT', '0.0'),")

# --- 6) Heart: dos paginas y la figura que late; fases contiguas 0-5
rep('''    (:2
      (if (>= _pt 1.8)
        %(page1)s
        (CallFunction|FPanel)
        (Class|BPHeartManagerSC|StageBegin %(hm)s)
        %(zone0)s
        %(g3)s))
    (:3
      %(zone)s
      (if (or (and (>= %(zt)s 1.5) (not %(spk)s)) (or (>= %(rp)s 4) (or (and (> %(zw)s 0.0) (>= _pt %(zw)s)) (and (> %(ag)s 0.0) (>= _pt %(ag)s)))))
        %(page2)s
        (CallFunction|FPanel)
        %(g4)s))
    (:4
      (if (or (and (>= _pt 2.0) (not %(spk)s)) (or (>= %(rp)s 5) (and (> %(ag)s 0.0) (>= _pt %(ag)s))))
        (Class|BPShareButtonSC|Vanish %(card)s)
        %(st0)s
        %(req0)s
        %(h10)s
        %(h20)s
        %(p7)s
        %(g5)s))
    (:5
      %(stp)s''', '''    (:2
      (if (>= _pt 1.8)
        %(page1)s
        (CallFunction|FPanel)
        (Class|BPHeartManagerSC|StageBegin %(hm)s)
        %(fz0)s
        %(g3)s))
    (:3
      (CallFunction|HeartFig)
      (if (or (and (>= (Class|BPHeartManagerSC|GetBeatCount %(hm)s) %(hp)s) (>= _pt 1.0)) (or (>= %(rp)s 4) (or (and (> %(zw)s 0.0) (>= _pt %(zw)s)) (and (> %(ag)s 0.0) (>= _pt %(ag)s)))))
        (Class|BPShareButtonSC|Vanish %(card)s)
        %(st0)s
        %(req0)s
        %(h10)s
        %(h20)s
        %(p7)s
        %(g4)s))
    (:4
      %(stp)s''')
rep('''      (if (and (not %(req)s) (or (>= %(st)s %(tope)s) (>= %(rp)s 6)))
        %(req1)s
        (Class|BPHeartManagerSC|StageRequestEnd %(hm)s)
        %(ptope)s)
      (if (or (Class|BPHeartManagerSC|GetStageDone %(hm)s) (and %(req)s (>= %(st)s (+ %(tope)s 30.0))))
        (Class|BPHeartManagerSC|StageOutro %(hm)s)
        %(pdone)s
        %(g6)s))
    (:6
      (if (and (not %(hon)s) (>= _pt 1.2))''', '''      (if (and (not %(req)s) (or (>= %(st)s %(tope)s) (>= %(rp)s 5)))
        %(req1)s
        (Class|BPHeartManagerSC|StageRequestEnd %(hm)s)
        %(ptope)s)
      (if (or (Class|BPHeartManagerSC|GetStageDone %(hm)s) (and %(req)s (>= %(st)s (+ %(tope)s 30.0))))
        (Class|BPHeartManagerSC|StageOutro %(hm)s)
        %(pdone)s
        %(g5)s))
    (:5
      (if (and (not %(hon)s) (>= _pt 1.2))''')
rep("           g1=GOPH(1), g3=GOPH(3), g4=GOPH(4), g5=GOPH(5), g6=GOPH(6), g15=GOPH(15),\n           page1=DS('Page', '1'), page2=DS('Page', '2'), zone0=DS('ZoneT', '0.0'),",
    "           g1=GOPH(1), g3=GOPH(3), g4=GOPH(4), g5=GOPH(5), g15=GOPH(15), hp=D('HeartPulses'), fz0=DS('FigZ', '0.0'),\n"
    "           page1=DS('Page', '1'), page2=DS('Page', '2'), zone0=DS('ZoneT', '0.0'),")
rep("           p7=P('DEMOFLOW: Heart, se va el panel: el latido'),", "           p7=P('DEMOFLOW: Heart, tres pulsos: se va el panel, el latido sigue'),")
rep("# un pulso cada BeatDiv latidos; cierra solo (StageBeats + la vuelta del mar) o al tope (StageRequestEnd). Sin Alma en el nivel su",
    "# un pulso cada BeatDiv latidos; cierra solo (StageBeats + la vuelta del mar) o al tope (StageRequestEnd). Fases 0-5 (2026-10-20 tarde:\n"
    "# dos paginas; la 2 tiene la figura que late, HeartFig, y se va a los HeartPulses pulsos). Sin Alma en el nivel su")

# HeartFig: la figura de la pagina 2 (M_DemoInstrHeart_SC en el slot de la imagen): Pulse = BeatEnv, Zone = umbral suavizado
s = s.replace("CODES['PracticeCut'] = ", '''CODES['HeartFig'] = """(fn HeartFig ()
  %(fz)s
  (bind _plate (Class|BPShareButtonSC|GetPlate %(card)s))
  (Rendering|Material|SetScalarParameterValueOnMaterials _plate "Pulse" (Class|BPHeartManagerSC|GetBeatEnv %(hm)s))
  (Rendering|Material|SetScalarParameterValueOnMaterials _plate "Zone" %(fzg)s))
""" % dict(fz=DS('FigZ', '(Math|Interpolation|FInterpTo %s (select (Class|BPHeartManagerSC|GetHeartZone %s) 1.0 0.0) (Utilities|Time|GetWorldDeltaSeconds) 5.0)' % (D('FigZ'), D('HM'))),
           card=D('Card'), hm=D('HM'), fzg=D('FigZ'))

CODES['PracticeCut'] = ''', 1)
rep("'PickGo', 'BreathCount', 'BreathTick', 'HeartTick',", "'PickGo', 'BreathCount', 'BreathTick', 'HeartFig', 'HeartTick',")
open(p, 'w', encoding='utf-8').write(s)
print('flow ok')
