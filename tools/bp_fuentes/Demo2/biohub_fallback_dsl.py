# biohub_fallback_dsl.py - BP_BioHub (Core/Signals): la senal simulada pasa a ser RESPALDO (2026-10-20 noche, demo BDW).
# Beltran pidio senal simulada en el APK (sin sensor se veia todo plano), pero manana puede conectarse la app del sensor:
# con bFakeSignal true las dos entraban mezcladas por el mismo Ingest. Ahora:
# - HandleOsc (solo lo llama el servidor OSC = mensajes REALES): un /muse/calm, o un /muse/heart_rate > 20, pone RealAge en 0.
#   Mientras manda el simulado (bFakeSignal y RealAge >= FakeHold) los mensajes reales que no son calma/latido valido se descartan
#   (sensor_active 0 de una app con la vincha fuera no hace titilar bSensorOn).
# - MaybeFake: RealAge crece con el tiempo; FakeTick corre solo si bFakeSignal y RealAge >= FakeHold (2 s, < ConnTimeout 3 s:
#   bConnected no cae al pasar de real a simulado). Una linea de log en cada cambio ("BIO: Muse real" / "BIO: sin Muse").
# Con bFakeSignal false (la Obra) es identico a antes: HandleOsc deja pasar todo y MaybeFake nunca llama a FakeTick.
# Variables nuevas (categoria Default): RealAge float 1000 · FakeHold float 2.0 (editable).
CALM = '(Utilities|String|EqualExactly(String) _addr (Variables|Default|GetAddrCalm))'
HEART = '(Utilities|String|EqualExactly(String) _addr (Variables|Default|GetAddrHeart))'
REAL = '(or %s (and %s (> _value 20.0)))' % (CALM, HEART)
CODES = {}
CODES['HandleOsc'] = '''(fn HandleOsc (Message)
  (bind _addr (Audio|OSC|ConvertOSCAddressToString (Audio|OSC|GetOSCMessageAddress Message)))
  (bind (_value _ok) (Audio|OSC|GetOSCMessageFloatAtIndex Message))
  (if (and %(real)s (>= (Variables|Default|GetRealAge) (Variables|Default|GetFakeHold)))
    (Development|PrintString "BIO: Muse real (el simulado se apaga)" :bPrintToScreen false))
  (if %(real)s
    (Variables|Default|SetRealAge 0.0))
  (if (or (not (Variables|Default|GetFakeSignal)) (< (Variables|Default|GetRealAge) (Variables|Default|GetFakeHold)))
    (if _ok
      (CallFunction|IngestFloat :Addr _addr :Value _value)
      (else
        (CallFunction|HandleOscInt :Message Message :Addr _addr)))))
''' % dict(real=REAL)
CODES['MaybeFake'] = '''(fn MaybeFake (DeltaSeconds)
  (if (and (Variables|Default|GetFakeSignal) (and (< (Variables|Default|GetRealAge) (Variables|Default|GetFakeHold)) (>= (+ (Variables|Default|GetRealAge) DeltaSeconds) (Variables|Default|GetFakeHold))))
    (Development|PrintString "BIO: sin Muse, vuelve el simulado" :bPrintToScreen false))
  (Variables|Default|SetRealAge (Math|Float|Min(Float) (+ (Variables|Default|GetRealAge) DeltaSeconds) 1000.0))
  (if (and (Variables|Default|GetFakeSignal) (>= (Variables|Default|GetRealAge) (Variables|Default|GetFakeHold)))
    (CallFunction|FakeTick :DeltaSeconds DeltaSeconds)))
'''
ORDER = ['HandleOsc', 'MaybeFake']
