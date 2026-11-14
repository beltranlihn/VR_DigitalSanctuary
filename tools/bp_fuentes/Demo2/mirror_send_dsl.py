# mirror_send_dsl.py - BP_MirrorLink_SC.SendStep: el emisor manda a SendHz de verdad (2026-10-19)
# Antes ponia SendT en 0 al mandar: a 72 fps (13,9 ms) y 60 Hz (16,7 ms) mandaba cada 2 cuadros = 36 Hz.
# Ahora resta el periodo (con tope de un periodo para no acumular atraso si un cuadro se alarga).
CODES = {}
CODES['SendStep'] = '''(fn SendStep (Dt)
  (CallFunction|EnsureRig)
  (bind _per (/ 1.0 (Math|Float|Max(Float) (Variables|Link|GetSendHz) 1.0)))
  (Variables|Z-Estado|SetSendT (+ (Variables|Z-Estado|GetSendT) Dt))
  (Variables|Z-Estado|SetLvlT (+ (Variables|Z-Estado|GetLvlT) Dt))
  (if (and (Variables|Z-Estado|GetRigOk) (>= (Variables|Z-Estado|GetSendT) _per))
    (Variables|Z-Estado|SetSendT (Math|Float|Min(Float) (- (Variables|Z-Estado|GetSendT) _per) _per))
    (CallFunction|SendPose)
    (CallFunction|SendInput)
    (CallFunction|SendState)
    (if (>= (Variables|Z-Estado|GetLvlT) 0.25)
      (Variables|Z-Estado|SetLvlT 0.0)
      (CallFunction|SendLevel))))
'''
ORDER = ['SendStep']
EVG = ''
