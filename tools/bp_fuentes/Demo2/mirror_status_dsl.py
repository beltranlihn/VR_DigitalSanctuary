# mirror_status_dsl.py - BP_MirrorLink_SC: estado de la conexion en la pantalla del robot + vigia de enlace (2026-10-20 noche)
# Pedido de Beltran: "la version de Windows deberia tener algun visor que nos diga que tanto la Quest como el proyecto del
# computador estan conectados". Disenado y verificado por el workflow robot-link-and-review (agentes de solo lectura).
# - Solo corre en el receptor (RxLog esta en la rama Mode 2 del Tick) y el cartel solo con MirrorRole 2 EXPLICITO (Robot.bat,
#   probar_robot.py): en PIE de escritorio / probar_nivel sin visor (Mode 2 automatico) no aparece nada en pantalla.
# - NoteRx (insertado por cirugia en OnOscMessageReceived_Event_0, antes de HandleOsc): IP del Quest + RxAge = 0.
# - LinkStep: mensajes/s, RxAge con el delta acotado a 0,1 s (un tiron del robot no dispara la vigia); sin mensajes por
#   LinkTimeout (3 s) -> bLinkLost + ZeroInput (gatillos y grips en 0: el robot deja de dibujar); vuelve sola con el proximo /sc/in.
# - Pantalla (WBP_MirrorStatus_SC.Show, cada 0,25 s): linea verde chica arriba a la izquierda ("LINK OK ... [Tab] details");
#   recuadro rojo al centro solo despues de WarnAfter (8 s) sin datos (una carga de nivel del Quest no lo enciende);
#   Tab: compacto -> detalle (PC / QUEST / STATE / BIO) -> oculto.
# - La IP del PC llega por Robot.bat (-MirrorMyIP=x.x.x.x).
WBP = '/Game/SoulCharger/Demo/Blueprints/WBP_MirrorStatus_SC.WBP_MirrorStatus_SC_C'
HUDC = '/Game/SoulCharger/Shared/HUD/Blueprints/BP_SoulHUD3D_SC.BP_SoulHUD3D_SC_C'
D = lambda n: '(Variables|Default|Get%s)' % n
DS = lambda n, x: '(Variables|Default|Set%s %s)' % (n, x)
Z = lambda n: '(Variables|Z-Estado|Get%s)' % n
L = lambda n: '(Variables|Link|Get%s)' % n
DT = '(Utilities|Time|GetWorldDeltaSeconds)'
I2S = lambda x: '(Utilities|String|ToString(Integer) %s)' % x
RND = lambda x: '(Math|Float|Round %s)' % x
RS = lambda i: '(Utilities|Array|Get(acopy) %s %d)' % (Z('RStF'), i)


def CAT(*parts):
    s = parts[0]
    for p in parts[1:]:
        s = '(Utilities|String|Append %s %s)' % (s, p)
    return s


WARN = '(> %s %s)' % (D('RxAge'), D('WarnAfter'))
CODES = {}
CODES['NoteRx'] = '''(fn NoteRx (Ip)
  %s
  %s)
''' % (DS('SenderIP', 'Ip'), DS('RxAge', '0.0'))
CODES['ZeroInput'] = '''(fn ZeroInput ()
  (Utilities|Array|Clear %s)
  (for _i (range (Utilities|Array|Length %s))
    (Utilities|Array|Add %s 0.0)))
''' % (Z('InF'), L('Keys'), Z('InF'))
CODES['LinkStep'] = '''(fn LinkStep ()
  %(age)s
  %(ratet)s
  (if (>= %(rt)s 1.0)
    %(rate)s
    %(prev)s
    %(rt0)s)
  (if (and (> %(ra)s %(to)s) (not %(lost)s))
    %(lost1)s
    (CallFunction|ZeroInput)
    (Development|PrintString %(plost)s :bPrintToScreen false))
  (if (and (<= %(ra)s %(to)s) (and %(lost)s (> %(rx)s 0)))
    %(lost0)s
    (Development|PrintString %(pback)s :bPrintToScreen false)))
''' % dict(age=DS('RxAge', '(+ %s (Math|Float|Min(Float) %s 0.1))' % (D('RxAge'), DT)), ratet=DS('RateT', '(+ %s %s)' % (D('RateT'), DT)),
           rt=D('RateT'), rate=DS('RxRate', RND('(/ (Math|Conversions|ToFloat(Integer) (- %s %s)) %s)' % (Z('RxCount'), D('RxPrev'), D('RateT')))),
           prev=DS('RxPrev', Z('RxCount')), rt0=DS('RateT', '0.0'), ra=D('RxAge'), to=D('LinkTimeout'), lost=D('LinkLost'), rx=Z('RxCount'),
           lost1=DS('LinkLost', 'true'), lost0=DS('LinkLost', 'false'),
           plost=CAT('"MIRROR: sin enlace con el Quest (gatillos y grips en 0), ultimo mensaje de "', D('SenderIP')),
           pback=CAT('"MIRROR: enlace con el Quest desde "', D('SenderIP')))
CODES['AddStatus'] = '''(fn AddStatus ()
  (Utilities|IsValid %s
    (:"Is Valid"
      (UserInterface|Viewport|AddtoViewport %s)
      (Development|PrintString %s :bPrintToScreen false))))
''' % (D('StW'), D('StW'), CAT('"MIRROR: estado de conexion en pantalla, IP del PC "', D('MyIP')))
CODES['EnsureStatus'] = '''(fn EnsureStatus ()
  (Utilities|IsValid %s
    (:"Is Not Valid"
      (bind (_ip _found) (Utilities|ParseParamValue (Utilities|GetCommandLine) "MirrorMyIP="))
      %s
      %s
      (CallFunction|AddStatus))))
''' % (D('StW'), DS('MyIP', '(select _found _ip "?")'),
       DS('StW', '(UserInterface|CreateWidget :Class "%s" :OwningPlayer (Game|GetPlayerController 0))' % WBP))
HAND = '(select (> %s 0.5) "right" (select (>= %s 0.0) "left" "-"))' % (RS(3), RS(3))
CODES['DrawState'] = '''(fn DrawState ()
  (if (>= (Utilities|Array|Length %(rsf)s) 9)
    %(st)s
    %(mu)s
    (else
      %(st0)s
      %(mu0)s)))
''' % dict(rsf=Z('RStF'),
           st=DS('StStr', CAT('"STATE   level "', Z('RemoteLevel'), '"   menu phase "', I2S(RND(RS(0))), '"   flow phase "', I2S(RND(RS(2))), '"   hand "', HAND)),
           mu=DS('MuStr', '(select (or (or (>= %s 0.0) (> %s 0.0)) (and (>= %s 1.5) (> %s -500.0))) %s "BIO     no data from the Quest (-1)")' % (
               RS(7), RS(8), RS(5), RS(4), CAT('"BIO     from the Quest   neural "', I2S(RND('(* %s 100.0)' % RS(7))), '"   bpm "', I2S(RND(RS(8))),
                                 '"   calm index "', '(select (and (>= %s 1.5) (> %s -500.0)) %s "--")' % (RS(5), RS(4), CAT('(select (> %s 0.0) "+" "")' % RS(4), I2S(RND(RS(4))), '"%"'))))),
           st0=DS('StStr', '"STATE   no /sc/st yet"'), mu0=DS('MuStr', '"BIO     no /sc/st yet"'))
OKLINE = '(select %s %s %s)' % (D('LinkLost'), CAT('"QUEST: no data for "', I2S(RND(D('RxAge'))), '" s"'),
                                 CAT('"LINK OK   "', I2S(D('RxRate')), '" msg/s   Quest "', D('SenderIP'), '"   [Tab] details"'))
CODES['DrawStatus'] = '''(fn DrawStatus ()
  (Utilities|IsValid %(stw)s
    (:"Is Valid"
      (CallFunction|DrawState)
      (Class|WBPMirrorStatusSC|Show :self %(stw)s :WarnA (select %(warn)s 1.0 0.0) :OkA (select (or %(warn)s (== %(view)s 2)) 0.0 0.85) :InfoA (select (== %(view)s 1) 1.0 0.0) :Ok %(ok)s :Head (select (== %(rx)s 0) "WAITING FOR THE QUEST" "QUEST LINK LOST") :B1 %(b1)s :B2 %(b2)s :PC %(pc)s :Quest %(q)s :State %(sts)s :Muse %(mus)s))))
''' % dict(stw=D('StW'), warn=WARN, view=D('StatusView'), ok=OKLINE, rx=Z('RxCount'),
           b1=CAT('"Mirror IP to set on the Quest: "', D('MyIP'), '"   UDP "', I2S(L('Port'))),
           b2='(select (== %s 0) "No message received yet" %s)' % (Z('RxCount'), CAT('"Last message "', I2S(RND(D('RxAge'))), '" s ago from "', D('SenderIP'))),
           pc=CAT('"PC      robot listening on UDP "', I2S(L('Port')), '"   PC IP "', D('MyIP')),
           q='(select (== %s 0) "QUEST   no message yet" %s)' % (Z('RxCount'), CAT('"QUEST   "', D('SenderIP'), '"   "', I2S(D('RxRate')), '" msg/s   last "', I2S(RND('(* %s 1000.0)' % D('RxAge'))), '" ms ago   total "', I2S(Z('RxCount')))),
           sts=CAT(D('StStr'), '""'), mus=CAT(D('MuStr'), '""'))
CODES['StatusStep'] = '''(fn StatusStep ()
  (if (Game|Player|WasInputKeyJustPressed (Game|GetPlayerController 0) "Tab")
    %(view)s
    (Development|PrintString (Utilities|String|Append "MIRROR: vista del estado " %(vs)s) :bPrintToScreen false))
  %(stt)s
  (if (>= %(st)s 0.25)
    %(st0)s
    (CallFunction|EnsureStatus)
    (CallFunction|DrawStatus)))
''' % dict(view=DS('StatusView', '(select (>= %s 2) 0 (+ %s 1))' % (D('StatusView'), D('StatusView'))), vs=I2S(D('StatusView')),
           stt=DS('StT', '(+ %s %s)' % (D('StT'), DT)), st=D('StT'), st0=DS('StT', '0.0'))
CODES['RxLog'] = '''(fn RxLog ()
  (CallFunction|LinkStep)
  (if (== %(role)s 2)
    (CallFunction|StatusStep)
    (CallFunction|RobotHud))
  (Variables|Z-Estado|SetDbgT (+ (Variables|Z-Estado|GetDbgT) %(dt)s))
  (if (>= (Variables|Z-Estado|GetDbgT) 2.0)
    (Variables|Z-Estado|SetDbgT 0.0)
    (Development|PrintString %(p)s :bPrintToScreen false)))
''' % dict(role=L('MirrorRole'), dt=DT, p=CAT('"MIRROR: mensajes recibidos "', I2S(Z('RxCount')), '" ("', I2S(D('RxRate')), '"/s)"'))

# 20-10 noche (Beltran probo el robot con el Quest real): "si muevo el casco el HUD a veces se ve y a veces no" (el HUD cuelga de la
# camara del pawn, pose exacta, y la pantalla del robot es la camara de espectador suavizada, que se atrasa al girar) y "se ven
# pedazos del visor del pawn" (HeadMountedDisplayMesh tiene OwnerNoSee: el robot no mira desde el pawn, asi que se ve).
# RobotHud: una vez por nivel, cuando la camara de espectador ya esta y el HUD ya se colgo de la cabeza, el HUD pasa a colgar de
# SpecCam con el mismo offset relativo a la camara, girado HudUp grados hacia arriba (con FOV 90 la pildora quedaba cortada abajo),
# y se esconde el visor del pawn.
CODES['HideHmd'] = '''(fn HideHmd ()
  (for _c (Actor|GetComponentsByClass (Game|GetPlayerPawn 0) "/Script/Engine.StaticMeshComponent")
    (if (Utilities|String|Contains (Utilities|GetObjectName _c) "HeadMountedDisplay")
      (Development|SetHiddeninGame _c true))))
'''
CODES['RobotHudGo'] = '''(fn RobotHudGo ()
  (Utilities|IsValid %(hud)s
    (:"Is Valid"
      (if (Class|BPSoulHUDSC|GetAttached %(hud)s)
        (bind _rel (Math|Transform|MakeRelativeTransform (Transformation|GetActorTransform %(hud)s) (Transformation|GetWorldTransform %(cam)s)))
        (Transformation|AttachActorToComponent :self %(hud)s :Parent %(spec)s :LocationRule "KeepWorld" :RotationRule "KeepWorld" :ScaleRule "KeepWorld" :bWeldSimulatedBodies false)
        (Transformation|SetActorRelativeTransform :self %(hud)s :NewRelativeTransform (Math|Transform|ComposeTransforms _rel (Math|Transform|MakeTransform (Math|Vector|MakeVector 0.0 0.0 0.0) (Math|Rotator|MakeRotator 0.0 %(up)s 0.0) (Math|Vector|MakeVector 1.0 1.0 1.0))) :bSweep false :bTeleport true)
        %(done)s
        (CallFunction|HideHmd)
        (Development|PrintString "MIRROR: HUD en la camara de espectador y visor del pawn oculto" :bPrintToScreen false)))))
''' % dict(hud=D('HudRef'), cam=Z('Cam'), spec=D('SpecCam'), up=D('HudUp'), done=DS('HudSpec', 'true'))
CODES['RobotHud'] = '''(fn RobotHud ()
  (if (and (Variables|Z-Estado|GetSpecOn) (not %(done)s))
    %(find)s
    (CallFunction|RobotHudGo)))
''' % dict(done=D('HudSpec'), find=DS('HudRef', '(Utilities|Casting|CastToBP_SoulHUD3D_SC (Actor|GetActorOfClass "%s"))' % HUDC))
ORDER = ['HideHmd', 'RobotHudGo', 'RobotHud', 'NoteRx', 'ZeroInput', 'LinkStep', 'AddStatus', 'EnsureStatus', 'DrawState', 'DrawStatus', 'StatusStep', 'RxLog']
