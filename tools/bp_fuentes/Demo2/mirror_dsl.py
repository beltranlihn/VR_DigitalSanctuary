# mirror_dsl.py - BP_MirrorLink_SC: el robot sigue al director de las experiencias (BP_DemoFlow_SC), 2026-10-19
# /sc/st slot 2 = fase del director, slot 3 = mano elegida (1 derecha, 0 izquierda). El robot NO escribe en el director
# (el catalogo no ve sus variables nuevas): el director lee RStF del enlace (BP_DemoFlow_SC.RemoteSync).
FLOW = '/Game/SoulCharger/Demo/Blueprints/BP_DemoFlow_SC.BP_DemoFlow_SC_C'
FR = '(Variables|Default|GetFlowRef)'
CODES = {}
CODES['FindFlow'] = '''(fn FindFlow ()
  (Utilities|IsValid %s
    (:"Is Not Valid"
      (Variables|Default|SetFlowRef (Actor|GetActorOfClass "%s")))))
''' % (FR, FLOW)
CODES['StFlow'] = '''(fn StFlow ()
  (CallFunction|FindFlow)
  (Utilities|IsValid %s
    (:"Is Valid"
      (Utilities|Array|SetArrayElem (Variables|Z-Estado|GetStF) 2 (Math|Conversions|ToFloat(Integer) (Class|BPDemoFlowSC|GetPhase %s)))
      (Utilities|Array|SetArrayElem (Variables|Z-Estado|GetStF) 3 (select (Class|BPDemoFlowSC|GetRight %s) 1.0 0.0)))))
''' % (FR, FR, FR)
CODES['UiFlow'] = '''(fn UiFlow ()
  (Utilities|IsValid %s
    (:"Is Valid"
      (Variables|Z-Estado|SetUiActive (and (== (Class|BPDemoFlowSC|GetExp %s) 0) (== (Class|BPDemoFlowSC|GetPhase %s) 5))))))
''' % (FR, FR, FR)
CODES['GatherState'] = '''(fn GatherState ()
  (CallFunction|ResetSt)
  (CallFunction|StMenu)
  (CallFunction|StInstr)
  (CallFunction|StRunner)
  (CallFunction|StFlow))
'''
CODES['UiGate'] = '''(fn UiGate ()
  (Variables|Z-Estado|SetUiActive false)
  (CallFunction|FindFlow)
  (CallFunction|UiFlow)
  (Utilities|IsValid (Variables|Z-Estado|GetMenuRef)
    (:"Is Valid"
      (Variables|Z-Estado|SetUiActive true))))
'''
# GatherState y UiGate quedan aca solo como historia: la version viva (con StBio/RelayBio) es la de mirror_bio_dsl.py.
# Orden para reconstruir el enlace: mirror_dsl.py -> mirror_bio_dsl.py -> mirror_input_dsl.py -> mirror_send_dsl.py
# (los eventos IA_Shoot_Left/Right se crean por cirugia, ver mirror_input_dsl.py y la ficha BP_MirrorLink_SC.md)
ORDER = ['FindFlow', 'StFlow', 'UiFlow']
