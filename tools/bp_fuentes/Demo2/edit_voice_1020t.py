# edit_voice_1020t.py - 2026-10-20 (tarde): pistas sin audio como subtitulo (pedido de Beltran: las instrucciones de boton del menu
# tienen que salir como subtitulos, no como texto en medio de la nada). Sobre voice_dsl.py (respaldo voice_dsl_backup_1020t.py).
# ShowHint(Id): muestra la tarjeta de Id (una entrada sin audio en VoIds, CE 9999 = queda puesta) sin tocar Speaking, asi nadie espera
# a que "termine". HideHint(): la apaga con el mismo fundido. Say() apaga la pista.
import shutil
p = 'voice_dsl.py'
shutil.copy(p, 'voice_dsl_backup_1020t.py')
s = open(p, encoding='utf-8').read()


def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (s.count(a), a[:120])
    s = s.replace(a, b)


rep('''  (Variables|Default|SetSpeaking true)
  (Development|PrintString (Utilities|String|Append "VOZ: " (Utilities|GetObjectName Clip)) :bPrintToScreen false))
''', '''  (Variables|Default|SetSpeaking true)
  (Variables|Default|SetHint false)
  (Development|PrintString (Utilities|String|Append "VOZ: " (Utilities|GetObjectName Clip)) :bPrintToScreen false))
''')
rep('''(select (and (Variables|Default|GetSpeaking) (Variables|Default|GetSubs)) 5.0 -5.0)''',
    '''(select (and (or (Variables|Default|GetSpeaking) (Variables|Default|GetHint)) (Variables|Default|GetSubs)) 5.0 -5.0)''')
rep('''  (if (Variables|Default|GetSpeaking)
    (Variables|Default|SetT (+ (Variables|Default|GetT) Dt))
    (if (>= (Variables|Default|GetT) (+ (Variables|Default|GetDur) 0.2))
      (Variables|Default|SetSpeaking false)))
  (if (or (Variables|Default|GetSpeaking) (> (Variables|Default|GetAlpha) 0.0))''',
    '''  (if (Variables|Default|GetSpeaking)
    (Variables|Default|SetT (+ (Variables|Default|GetT) Dt))
    (if (>= (Variables|Default|GetT) (+ (Variables|Default|GetDur) 0.2))
      (Variables|Default|SetSpeaking false))
    (elif (Variables|Default|GetHint)
      (Variables|Default|SetT (+ (Variables|Default|GetT) Dt))))
  (if (or (or (Variables|Default|GetSpeaking) (Variables|Default|GetHint)) (> (Variables|Default|GetAlpha) 0.0))''')
s = s.replace("'VoiceTick': '''(fn VoiceTick (Dt)", """'ShowHint': '''(fn ShowHint (Id)
  (Variables|Default|SetCur (Utilities|Array|FindItem (Variables|Default|GetVoIds) Id))
  (Variables|Default|SetCard -1)
  (Variables|Default|SetT 0.0)
  (Variables|Default|SetHint true)
  (Development|PrintString (Utilities|String|Append "VOZ: pista " Id) :bPrintToScreen false))
''',
'HideHint': '''(fn HideHint ()
  (Variables|Default|SetHint false))
''',
'VoiceTick': '''(fn VoiceTick (Dt)""", 1)
rep("ORDER = ['Say', 'SubRef', 'SubAttach', 'SubCard', 'SubCards', 'SubDraw', 'VoiceTick']",
    "ORDER = ['Say', 'SubRef', 'SubAttach', 'SubCard', 'SubCards', 'SubDraw', 'ShowHint', 'HideHint', 'VoiceTick']")
open(p, 'w', encoding='utf-8').write(s)
print('voice ok')
