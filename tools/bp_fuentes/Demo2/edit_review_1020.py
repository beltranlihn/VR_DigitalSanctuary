# edit_review_1020.py - 2026-10-20 (revision de toda la demo, pedido de Beltran). Sobre flow_dsl.py (respaldo flow_dsl_backup_1020r.py).
# 1) Breath y Heart terminan con las manos: el sensor se va (UserTool.Release; en Heart lo hace el manager) y HandsBack las muestra
#    (Release solo esconde el sensor: la mano queda oculta). HandsBack ahora no exige el director del dibujo (IsValid al final).
# 2) Breath, pagina 4: el laser del START sale de la mano LIBRE (la otra sostiene el sensor en la panza) y vibra esa mano.
import shutil
p = 'flow_dsl.py'
shutil.copy(p, 'flow_dsl_backup_1020r.py')
s = open(p, encoding='utf-8').read()


def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (s.count(a), a[:100])
    s = s.replace(a, b)


# HandsBack: el director del dibujo solo si existe (Breath/Heart no lo tienen)
rep('''CODES['HandsBack'] = """(fn HandsBack ()
  (if (not %(hon)s)
    %(hon1)s
    (Class|BPTBDirectorNC|SetHidePawnHands :self %(tb)s :bHidePawnHands false)
    (for _c (Actor|GetComponentsByClass (Game|GetPlayerPawn 0) "/Script/Engine.SkeletalMeshComponent")
      (Rendering|SetVisibility _c true true)
      (Development|SetHiddeninGame _c false true))
    (Development|PrintString "DEMOFLOW: se fueron los mandos, vuelven las manos" :bPrintToScreen false)))''',
    '''CODES['HandsBack'] = """(fn HandsBack ()
  (if (not %(hon)s)
    %(hon1)s
    (for _c (Actor|GetComponentsByClass (Game|GetPlayerPawn 0) "/Script/Engine.SkeletalMeshComponent")
      (Rendering|SetVisibility _c true true)
      (Development|SetHiddeninGame _c false true))
    (Development|PrintString "DEMOFLOW: se fueron los mandos / el sensor, vuelven las manos" :bPrintToScreen false)
    (Utilities|IsValid %(tb)s
      (:"Is Valid"
        (Class|BPTBDirectorNC|SetHidePawnHands :self %(tb)s :bHidePawnHands false)))))''')
# Breath :4 -> el laser del START en la mano libre
rep('''        (CallFunction|SaveHands)
        (Class|BPSeqRigSC|ResultsBeam %(rig)s true)''', '''        (CallFunction|SaveHands)
        (Class|BPSeqRigSC|SetRightHanded :self %(rig)s :bRightHanded (not %(right)s))
        (Class|BPSeqRigSC|ResultsBeam %(rig)s true)''')
# Breath :9 -> al cerrar la etapa el sensor se va
rep('''      (if (or (Class|BPBreathStageSC|GetStageDone %(bstage)s) (and %(req)s (>= %(st)s (+ %(tope)s 30.0))))
        (Class|BPBreathStageSC|StageOutro %(bstage)s)''', '''      (if (or (Class|BPBreathStageSC|GetStageDone %(bstage)s) (and %(req)s (>= %(st)s (+ %(tope)s 30.0))))
        (Class|BPBreathStageSC|StageOutro %(bstage)s)
        (Class|BPUserToolSC|Release %(tool)s)''')
# Breath :10 -> vuelven las manos
rep('''    (:10
      (if (>= _pt 2.8)
        %(say3)s
        %(g15)s))))''', '''    (:10
      (if (and (not %(hon)s) (>= _pt 1.2))
        (CallFunction|HandsBack))
      (if (>= _pt 2.8)
        %(say3)s
        %(g15)s))))''')
rep("pdone=P('DEMOFLOW: la etapa termino, StageOutro'), spk=SPEAK)",
    "pdone=P('DEMOFLOW: la etapa termino, StageOutro'), spk=SPEAK, right=D('Right'), tool=D('Tool'), hon=D('HandsOn'))")
# Heart :6 -> vuelven las manos (el manager ya solto el sensor en StageOutro)
rep('''    (:6
      (if (>= _pt 2.8)
        %(say3)s
        %(g15)s))))
""" % dict(pt=D('PT'), ph=D('Phase'), rt=D('RT'), env=D('Env'), env1=DS('Env', 'true'), hm=D('HM'),''', '''    (:6
      (if (and (not %(hon)s) (>= _pt 1.2))
        (CallFunction|HandsBack))
      (if (>= _pt 2.8)
        %(say3)s
        %(g15)s))))
""" % dict(hon=D('HandsOn'), pt=D('PT'), ph=D('Phase'), rt=D('RT'), env=D('Env'), env1=DS('Env', 'true'), hm=D('HM'),''')
# PickGo: vibra la mano del laser (la libre)
rep('''      (Class|BPSeqRigSC|Pulse :self _rig :bRight %(right)s)''', '''      (Class|BPSeqRigSC|Pulse :self _rig :bRight (Class|BPSeqRigSC|GetRightHanded _rig))''')
open(p, 'w', encoding='utf-8').write(s)

# ======================================================================================= BP_MirrorLink_SC: el latido del robot
open('mirror_heart_dsl.py', 'w', encoding='utf-8').write('''# mirror_heart_dsl.py - BP_MirrorLink_SC (2026-10-20): en el robot el umbral del pecho de Heart usa la pose recibida.
# Sin esto el BP_HeartManager_SC del robot exige tracking valido (en Windows no hay) y el latido solo arranca con el respaldo (30 s).
# Igual que RobotBreath con el BreathRig. Variable HMRef (BP_HeartManager_SC) para que el catalogo vea la clase.
HMC = '/Game/SoulCharger/Mechanics/Heart/Blueprints/BP_HeartManager_SC.BP_HeartManager_SC_C'
CODES = {}
CODES['RobotHeart'] = """(fn RobotHeart ()
  (Variables|Default|SetHMRef (Actor|GetActorOfClass "%s"))
  (Utilities|IsValid (Variables|Default|GetHMRef)
    (:"Is Valid"
      (Class|BPHeartManagerSC|SetIgnoreTracking :self (Variables|Default|GetHMRef) :bIgnoreTracking true)
      (Development|PrintString "MIRROR: el latido del robot usa la pose recibida (sin tracking)" :bPrintToScreen false))))
""" % HMC
CODES['RobotSetup'] = """(fn RobotSetup ()
  (if (== (Variables|Z-Estado|GetMode) 2)
    (CallFunction|RobotBreath)
    (CallFunction|RobotHeart)
    (CallFunction|RobotRunner)))
"""
ORDER = ['RobotHeart', 'RobotSetup']
EVG = ''
''')
print('ok')
