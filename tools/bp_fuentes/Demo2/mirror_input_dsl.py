# mirror_input_dsl.py - BP_MirrorLink_SC: el gatillo del Quest llega al robot por Enhanced Input (2026-10-19)
# En el visor las teclas XR NO llegan al buffer clasico (IsInputKeyDown / GetInputAnalogKeyState dan 0: assets-existentes.md),
# asi que /sc/in salia con los gatillos en 0 y el robot no dibujaba. Los eventos IA_Shoot_Left/Right SI llegan a un actor
# (AutoReceiveInput Player0): Triggered -> TrigX 1, Completed -> TrigX 0. BuildInput suma TrigL a los canales 0 y 13
# (gatillo izquierdo eje y click) y TrigR a 1 y 14. En el PC (teclado, Quest falso) el camino viejo sigue igual.
# OJO: los eventos IA_Shoot_Left/Right del EventGraph NO salen de este archivo: se crean por cirugia (create_node
# Input|EnhancedActionEvents|IA_Shoot_X, Triggered(0) -> ShootXOn, Completed(4) -> ShootXOff) y AutoReceiveInput Player0 en el CDO.
CODES = {}
for side in ('L', 'R'):
    CODES['Shoot%sOn' % side] = '(fn Shoot%sOn ()\n  (Variables|Default|SetTrig%s 1.0))\n' % (side, side)
    CODES['Shoot%sOff' % side] = '(fn Shoot%sOff ()\n  (Variables|Default|SetTrig%s 0.0))\n' % (side, side)
CODES['BuildInput'] = '''(fn BuildInput ()
  (Audio|OSC|ClearOSCMessage (Variables|Z-Estado|GetMsg))
  (bind _addr (Audio|OSC|ConvertStringToOSCAddress "/sc/in"))
  (Audio|OSC|SetOSCMessageAddress (Variables|Z-Estado|GetMsg) _addr)
  (for _i (range (Utilities|Array|Length (Variables|Link|GetKeys)))
    (bind _k (Utilities|Array|Get(acopy) (Variables|Link|GetKeys) _i))
    (bind _ev (select (or (== _i 0) (== _i 13)) (Variables|Default|GetTrigL) (select (or (== _i 1) (== _i 14)) (Variables|Default|GetTrigR) 0.0)))
    (Audio|OSC|AddFloattoOSCMessage (Variables|Z-Estado|GetMsg) (Math|Float|Max(Float) (Math|Float|Max(Float) (Game|Player|GetInputAnalogKeyState (Game|GetPlayerController 0) _k) (select (Game|Player|IsInputKeyDown (Game|GetPlayerController 0) _k) 1.0 0.0)) _ev))))
'''
ORDER = ['ShootLOn', 'ShootLOff', 'ShootROn', 'ShootROff', 'BuildInput']
EVG = ''
