# mirror_bio_dsl.py - BP_MirrorLink_SC: el robot recibe el Muse a traves del visor (2026-10-19)
# /sc/st crece a 9 floats: slot 7 = calma cruda del BioHub del Quest, slot 8 = BPM (-1 = sin Muse conectado).
# El receptor se los pasa a SU BioHub con Ingest (el mismo camino que el OSC del Muse): HUD y resultados del robot con datos.
HUB = '/Game/SoulCharger/Core/Signals/BP_BioHub.BP_BioHub_C'
H = '(Variables|Default|GetHubRef)'
ST = '(Variables|Z-Estado|GetStF)'
RS = '(Variables|Z-Estado|GetRStF)'
CODES = {}
CODES['FindHub'] = '''(fn FindHub ()
  (Utilities|IsValid %s
    (:"Is Not Valid"
      (Variables|Default|SetHubRef (Actor|GetActorOfClass "%s")))))
''' % (H, HUB)
CODES['ResetSt'] = '''(fn ResetSt ()
  (Utilities|Array|Clear %s)
  (for _i (range 9)
    (Utilities|Array|Add %s -1.0)))
''' % (ST, ST)
CODES['StBio'] = '''(fn StBio ()
  (CallFunction|FindHub)
  (Utilities|IsValid %s
    (:"Is Valid"
      (if (Class|BPBioHub|GetConnected %s)
        (Utilities|Array|SetArrayElem %s 7 (Class|BPBioHub|GetCalm %s))
        (Utilities|Array|SetArrayElem %s 8 (Class|BPBioHub|GetHeart %s))))))
''' % (H, H, ST, H, ST, H)
# 20-10 noche: el robot muestra SOLO lo que manda el visor (real o simulado alla): su propio simulado se apaga en cuanto llega
# /sc/st (este camino solo corre con Mode 2 y 9 floats, o sea con el Quest emitiendo; en PIE de escritorio sin Quest no corre).
CODES['RelayBioOne'] = '''(fn RelayBioOne ()
  (Utilities|IsValid %s
    (:"Is Valid"
      (Class|BPBioHub|SetFakeSignal :self %s :bFakeSignal false)
      (if (>= (Utilities|Array|Get(acopy) %s 7) 0.0)
        (Class|BPBioHub|Ingest :self %s :Addr (Class|BPBioHub|GetAddrCalm %s) :Value (Utilities|Array|Get(acopy) %s 7)))
      (if (> (Utilities|Array|Get(acopy) %s 8) 0.0)
        (Class|BPBioHub|Ingest :self %s :Addr (Class|BPBioHub|GetAddrHeart %s) :Value (Utilities|Array|Get(acopy) %s 8))))))
''' % (H, H, RS, H, H, RS, RS, H, H, RS)
CODES['RelayBio'] = '''(fn RelayBio ()
  (if (and (== (Variables|Z-Estado|GetMode) 2) (>= (Utilities|Array|Length %s) 9))
    (CallFunction|FindHub)
    (CallFunction|RelayBioOne)))
''' % RS
CODES['GatherState'] = '''(fn GatherState ()
  (CallFunction|ResetSt)
  (CallFunction|StMenu)
  (CallFunction|StInstr)
  (CallFunction|StRunner)
  (CallFunction|StFlow)
  (CallFunction|StBio))
'''
CODES['UiGate'] = '''(fn UiGate ()
  (CallFunction|RelayBio)
  (Variables|Z-Estado|SetUiActive false)
  (CallFunction|FindFlow)
  (CallFunction|UiFlow)
  (Utilities|IsValid (Variables|Z-Estado|GetMenuRef)
    (:"Is Valid"
      (Variables|Z-Estado|SetUiActive true))))
'''
ORDER = ['FindHub', 'ResetSt', 'StBio', 'RelayBioOne', 'RelayBio', 'GatherState', 'UiGate']
