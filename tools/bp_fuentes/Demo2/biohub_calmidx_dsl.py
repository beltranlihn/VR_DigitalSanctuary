# biohub_calmidx_dsl.py - BP_BioHub (Core/Signals): INDICE DE CALMA de Muse Integration (2026-10-20 noche, pedido de Beltran).
# La app del sensor (Code/MuseIntegration, contrato acordado con su sesion) manda:
#   /muse/calm_index  f  % de -100 a +100 respecto de la calibracion de la persona (+ = mas calma)
#   /muse/calm_quality f 0-1 (fraccion del peso de componentes validos)
# y sigue mandando /muse/alpha (actividad neuronal: en los niveles demo AddrCalm = "/muse/alpha"), /muse/heart_rate, /muse/sensor_active.
# - CalmIdx / CalmIdxQ / bCalmIdxSeen guardan el ultimo indice. CalmIndexOut() lo entrega (-999 si nunca llego): lo leen el cuadro
#   de resultados y el enlace (slot 4 de /sc/st para el robot). SetCalmIndex(V) lo usan el OSC, el simulado y el robot.
# - Simulado (respaldo, misma regla que la calma: solo sin senal real por FakeHold): FakeCalmIdx sube de 0 a ~+22 % en 150 s con un
#   vaiven chico, para que el cuadro de resultados muestre un numero creible sin sensor.
# - HandleOsc: igual que biohub_fallback_dsl.py + las dos direcciones nuevas (fuera de Ingest: no van a las casillas). Con calidad 0
#   (la app antes de terminar la calibracion) el indice se ignora; al pasar de simulado a real se borra el indice simulado.
# Con la Obra (sus BioHub no reciben estas direcciones y bFakeSignal false) nada cambia: CalmIndexOut da -999 y nadie lo lee.
CALM = '(Utilities|String|EqualExactly(String) _addr (Variables|Default|GetAddrCalm))'
HEART = '(Utilities|String|EqualExactly(String) _addr (Variables|Default|GetAddrHeart))'
REAL = '(or %s (and %s (> _value 20.0)))' % (CALM, HEART)
CODES = {}
CODES['SetCalmIndex'] = '''(fn SetCalmIndex (V)
  (Variables|Default|SetCalmIdx (Math|Float|Clamp(Float) V -100.0 100.0))
  (Variables|Default|SetCalmIdxSeen true))
'''
# CalmIndexOut quedo como funcion vacia (el MCP no creo su salida): los demas leen GetCalmIdx/GetCalmIdxSeen directo.
# revision 20-10 noche: el simulado nunca pisa un indice REAL ya recibido (bCalmIdxReal)
CODES['FakeCalmIdx'] = '''(fn FakeCalmIdx ()
  (if (not (Variables|Default|GetCalmIdxReal))
    (CallFunction|SetCalmIndex :V (+ (Math|Float|MapRangeClamped (Utilities|Time|GetGameTimeInSeconds) 0.0 150.0 0.0 22.0) (* 3.0 (Math|Trig|Sin(Degrees) (* (Utilities|Time|GetGameTimeInSeconds) 9.0)))))
    (Variables|Default|SetCalmIdxQ 0.9)))
'''
CODES['HandleOsc'] = '''(fn HandleOsc (Message)
  (bind _addr (Audio|OSC|ConvertOSCAddressToString (Audio|OSC|GetOSCMessageAddress Message)))
  (bind (_value _ok) (Audio|OSC|GetOSCMessageFloatAtIndex Message))
  (if (and %(real)s (>= (Variables|Default|GetRealAge) (Variables|Default|GetFakeHold)))
    (Development|PrintString "BIO: Muse real (el simulado se apaga)" :bPrintToScreen false)
    (if (not (Variables|Default|GetCalmIdxReal))
      (Variables|Default|SetCalmIdxSeen false)))
  (if %(real)s
    (Variables|Default|SetRealAge 0.0))
  (if (or (not (Variables|Default|GetFakeSignal)) (< (Variables|Default|GetRealAge) (Variables|Default|GetFakeHold)))
    (if (and _ok (Utilities|String|EqualExactly(String) _addr (Variables|Default|GetAddrCalmIdx)))
      (if (> (Variables|Default|GetCalmIdxQ) 0.0)
        (CallFunction|SetCalmIndex :V _value)
        (Variables|Default|SetCalmIdxReal true))
      (elif (and _ok (Utilities|String|EqualExactly(String) _addr (Variables|Default|GetAddrCalmQ)))
        (Variables|Default|SetCalmIdxQ _value)
        (elif _ok
          (CallFunction|IngestFloat :Addr _addr :Value _value)
          (else
            (CallFunction|HandleOscInt :Message Message :Addr _addr)))))))
''' % dict(real=REAL)
CODES['MaybeFake'] = '''(fn MaybeFake (DeltaSeconds)
  (if (and (Variables|Default|GetFakeSignal) (and (< (Variables|Default|GetRealAge) (Variables|Default|GetFakeHold)) (>= (+ (Variables|Default|GetRealAge) DeltaSeconds) (Variables|Default|GetFakeHold))))
    (Development|PrintString "BIO: sin Muse, vuelve el simulado" :bPrintToScreen false))
  (Variables|Default|SetRealAge (Math|Float|Min(Float) (+ (Variables|Default|GetRealAge) DeltaSeconds) 1000.0))
  (if (and (Variables|Default|GetFakeSignal) (>= (Variables|Default|GetRealAge) (Variables|Default|GetFakeHold)))
    (CallFunction|FakeTick :DeltaSeconds DeltaSeconds)
    (CallFunction|FakeCalmIdx)))
'''

# robot: el Quest no tiene indice de calma (-999 en el slot 4): se borra el que hubiera dejado el simulado del robot
CODES['ClearCalmIndex'] = '''(fn ClearCalmIndex ()
  (Variables|Default|SetCalmIdxSeen false)
  (Variables|Default|SetCalmIdx 0.0))
'''
ORDER = ['SetCalmIndex', 'ClearCalmIndex', 'FakeCalmIdx', 'HandleOsc', 'MaybeFake']
# Estructura (con herramientas, nivel neutro): variables Default CalmIdx float 0 · CalmIdxQ float 0 · bCalmIdxSeen bool false · bCalmIdxReal bool false ·
# AddrCalmIdx string "/muse/calm_index" · AddrCalmQ string "/muse/calm_quality"; funciones SetCalmIndex (entrada V float),
# CalmIndexOut (salida Out float), FakeCalmIdx.
