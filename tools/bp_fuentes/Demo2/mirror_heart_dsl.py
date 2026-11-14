# mirror_heart_dsl.py - BP_MirrorLink_SC (2026-10-20): en el robot el umbral del pecho de Heart usa la pose recibida.
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
