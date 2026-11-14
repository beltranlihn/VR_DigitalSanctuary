# edit_flow_1020b.py - cambios del 2026-10-20 (tarde) sobre flow_dsl.py, pedidos de Beltran tras probar Draw en Unreal
import shutil
p = 'flow_dsl.py'
shutil.copy(p, 'flow_dsl_backup_1020b.py')
s = open(p, encoding='utf-8').read()


def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (s.count(a), a[:90])
    s = s.replace(a, b)


# 1) Grab: el haptico es el de la Obra, BP_SeqRig_SC.Pulse (PlayHapticEffect + GrabHapticEffect al PlayerController)
rep('''  (if %(r)s
    (Game|Feedback|PlayHapticEffect (Game|GetPlayerController 0) "%(hap)s" "Right")
    (else
      (Game|Feedback|PlayHapticEffect (Game|GetPlayerController 0) "%(hap)s" "Left")))
''', '''  (Class|BPSeqRigSC|Pulse :self %(rig)s :bRight %(r)s)
''')
rep("go=GOPH(2), hap='/Game/XRFramework/Haptics/GrabHapticEffect.GrabHapticEffect')", "go=GOPH(2))")
rep("# Grab: haptico de la mano que toma (2026-10-20, pedido de Beltran; el GrabHapticEffect del framework, el mismo del SeqRig)",
    "# Grab: haptico de la mano que toma (2026-10-20, pedido de Beltran) = BP_SeqRig_SC.Pulse, el de la Obra")
# 2) PickGo (START de Breath): el mismo pulso en la mano dominante
rep('''    (if (or _auto _hov)
      (Class|BPShareButtonSC|Press _go)
      %(p)s''', '''    (if (or _auto _hov)
      (Class|BPShareButtonSC|Press _go)
      (Class|BPSeqRigSC|Pulse :self _rig :bRight %(right)s)
      %(p)s''')
rep("goph=GOPH(6), rp=D('RemotePhase'), gow=D('GoWait'))", "goph=GOPH(6), rp=D('RemotePhase'), gow=D('GoWait'), right=D('Right'))")
# 3) ShowPanel guarda la base del objeto que flota (para el vaiven)
rep('''  %(page0)s
  (CallFunction|FPanel)
  (Class|BPShareButtonSC|Appear %(card)s)''', '''  %(pbase)s
  %(page0)s
  (CallFunction|FPanel)
  (Class|BPShareButtonSC|Appear %(card)s)''')
rep("rf=D('ReachFwd'), rd=D('ReachDown'), page0=DS('Page', '0'),",
    "rf=D('ReachFwd'), rd=D('ReachDown'), page0=DS('Page', '0'), pbase=DS('PedBase', '(Transformation|GetActorLocation %s)' % D('Pedestal')),")
# 4) GrabStep: el objeto gira suave y sube y baja un poco mientras espera que lo tomen
rep('''CODES['GrabStep'] = \'\'\'(fn GrabStep ()
  (bind _pl''', '''CODES['GrabStep'] = \'\'\'(fn GrabStep ()
  (CallFunction|PedSpin)
  (bind _pl''')
# 5) FPanel: la voz de cada pagina
rep('''  (Rendering|Material|SetMaterial _plate 3 %(ring)s)
''', '''  (Rendering|Material|SetMaterial _plate 3 %(ring)s)
  (CallFunction|SayPage)
''')
# 6) Breath: las paginas que avanzan solas esperan a que termine su voz (los tiempos limite no esperan)
rep("(if (or (>= %(zt)s 1.5) (or", "(if (or (and (>= %(zt)s 1.5) (not %(spk)s)) (or")
rep("(if (or (>= %(bn)s %(breaths)s) (or", "(if (or (and (>= %(bn)s %(breaths)s) (not %(spk)s)) (or")
rep("pdone=P('DEMOFLOW: la etapa termino, StageOutro'))", "pdone=P('DEMOFLOW: la etapa termino, StageOutro'), spk=SPEAK)")
# 7) DrawTick :5 sin dibujo: el director cierra (se van los mandos) y vuelven las manos
rep('''        (elif (and %(req)s (or (Class|BPTBDirectorNC|GetStageDone %(tb)s) (>= %(tt)s (+ %(dt)s 30.0))))
          %(say3)s''', '''        (elif (and %(req)s (or (Class|BPTBDirectorNC|GetStageDone %(tb)s) (>= %(tt)s (+ %(dt)s 30.0))))
          (Class|BPTBDirectorNC|StageOutro %(tb)s)
          (CallFunction|HandsBack)
          %(say3)s''')
# 8) DrawTick :6: vuelven las manos cuando los mandos terminan de irse (OutroTime del director);
#    al correrse el dibujo: se va el HUD y aparecen los resultados A LA VEZ -> fase 17 (resultados)
rep('''    (:6
      (if (>= %(skp)s 3)
        %(skt)s)
      (if (or (>= %(skt0)s %(turns)s) (>= _pt (* 2.0 %(turns)s)))
        (CallFunction|ShiftStart)
        %(say3)s
        %(pshift)s
        %(g15)s))))''', '''    (:6
      (if (and (not %(hon)s) (>= _pt (Class|BPTBDirectorNC|GetOutroTime %(tb)s)))
        (CallFunction|HandsBack))
      (if (>= %(skp)s 3)
        %(skt)s)
      (if (or (>= %(skt0)s %(turns)s) (>= _pt (* 2.0 %(turns)s)))
        (CallFunction|ShiftStart)
        %(say3)s
        (Class|BPDemoHudKitSC|HudPlop %(kit)s)
        (Class|BPDemoResultsSC|ResShow %(res)s)
        %(pshift)s
        %(g17)s))))''')
rep("pnone=P('DEMOFLOW: sin dibujo, sin presentacion: al cierre'), rp=D('RemotePhase'), pw=D('PracticeWait'))",
    "pnone=P('DEMOFLOW: sin dibujo, sin presentacion: al cierre'), rp=D('RemotePhase'), pw=D('PracticeWait'), hon=D('HandsOn'), res=D('Results'), g17=GOPH(17))")
rep("pshift=P('DEMOFLOW: el dibujo se corre a la derecha')",
    "pshift=P('DEMOFLOW: el dibujo se corre a la derecha, a la vez se va el HUD y aparecen los resultados')")
# 9) ShiftStep: la mesa se corre con el dibujo (antes de SetShiftK: _d es un bind puro, gotcha 409)
rep('''    (Class|BPCTBToolNC|SetSketchPivot :self _tool :SketchPivot (+ (Class|BPCTBToolNC|GetSketchPivot _tool) _d))
    %(sks)s))''', '''    (Class|BPCTBToolNC|SetSketchPivot :self _tool :SketchPivot (+ (Class|BPCTBToolNC|GetSketchPivot _tool) _d))
    (CallFunction|MoveTable :D _d)
    %(sks)s))''')

NEW = '''
# --- 2026-10-20 (tarde), pedidos de Beltran tras probar Draw en Unreal ---
# PedSpin: el sensor / el mando que flota gira suave (SpinDeg grados/s) y sube y baja BobCm, invitando a tomarlo
CODES['PedSpin'] = """(fn PedSpin ()
  (Transformation|AddActorWorldRotation %(ped)s (Math|Rotator|MakeRotator 0.0 0.0 (* %(spin)s (Math|Float|Min(Float) (Utilities|Time|GetWorldDeltaSeconds) 0.0333))) false true)
  (Transformation|SetActorLocation %(ped)s (+ %(base)s (Math|Vector|MakeVector 0.0 0.0 (* %(bob)s (Math|Trig|Sin(Radians) (* %(pt)s 1.6))))) false true))
""" % dict(ped=D('Pedestal'), spin=D('SpinDeg'), base=D('PedBase'), bob=D('BobCm'), pt=D('PT'))
# SayPage: la voz de la pagina del panel (PageVo por instancia: Breath VO_IB1-4, Draw VO_ID1-2)
CODES['SayPage'] = """(fn SayPage ()
  (if (> (Utilities|Array|Length %(pv)s) %(page)s)
    (Class|BPDemoVoiceSC|Say :self %(voice)s :Clip (Utilities|Array|Get(acopy) %(pv)s %(page)s))))
""" % dict(pv=D('PageVo'), page=D('Page'), voice=D('Voice'))
# HandsBack: al irse los mandos del dibujo vuelven las manos (el director las escondia con bHidePawnHands)
CODES['HandsBack'] = """(fn HandsBack ()
  (if (not %(hon)s)
    %(hon1)s
    (Class|BPTBDirectorNC|SetHidePawnHands :self %(tb)s :bHidePawnHands false)
    (for _c (Actor|GetComponentsByClass (Game|GetPlayerPawn 0) "/Script/Engine.SkeletalMeshComponent")
      (Rendering|SetVisibility _c true true)
      (Development|SetHiddeninGame _c false true))
    (Development|PrintString "DEMOFLOW: se fueron los mandos, vuelven las manos" :bPrintToScreen false)))
""" % dict(hon=D('HandsOn'), hon1=DS('HandsOn', 'true'), tb=D('TB'))
# MoveTable: la mesa del dibujo se corre con el dibujo
CODES['MoveTable'] = """(fn MoveTable (D)
  (bind _tbl (Class|BPCTBToolNC|GetDrawTable (Class|BPTBDirectorNC|GetTBTool %(tb)s)))
  (Utilities|IsValid _tbl
    (:"Is Valid"
      (Transformation|SetActorLocation _tbl (+ (Transformation|GetActorLocation _tbl) D) false true))))
""" % dict(tb=D('TB'))
'''
i = s.index("CODES['FlowTick']")
s = s[:i] + NEW + '\n' + s[i:]
rep("ORDER = ['FBoot', 'FHands',", "ORDER = ['PedSpin', 'SayPage', 'HandsBack', 'MoveTable', 'FBoot', 'FHands',")
open(p, 'w', encoding='utf-8').write(s)
print('ok')
