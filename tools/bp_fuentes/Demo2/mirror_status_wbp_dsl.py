# mirror_status_wbp_dsl.py - WBP_MirrorStatus_SC (Demo/Blueprints): el estado de la conexion Quest <-> robot en la pantalla del robot
# (2026-10-20 noche, pedido de Beltran: "algun visor que nos diga que tanto la Quest como el proyecto del computador estan conectados").
# Arbol (armado con UMGToolSet): Root (CanvasPanel, HitTestInvisible)
#   BoxOk (arriba a la izquierda, negro 55 %) > TxtOk (verde, 15 negrita): "LINK OK ..."
#   BoxInfo (debajo, negro 60 %) > InfoV > TxtPC / TxtQuest / TxtState / TxtMuse (15)
#   BoxWarn (centro, rojo 92 %) > WarnV > TxtHead (40 negrita) / TxtBody1 (24) / TxtBody2 (20)
# Show la llama BP_MirrorLink_SC (DrawStatus) con todo armado: el enlace no ve las variables de los hijos (son de otra clase),
# pero si las funciones nuevas de otra clase (como ShowHint de la voz).
V = lambda n: '(Variables|WBP_MirrorStatus_SC|Get%s)' % n
TX = lambda w, s: '(Widget|SetText(Text) %s (Utilities|Text|ToText(String) %s))' % (V(w), s)
CODES = {}
CODES['Show'] = '''(fn Show (WarnA OkA InfoA Ok Head B1 B2 PC Quest State Muse)
  (Widget|SetRenderOpacity %s WarnA)
  (Widget|SetRenderOpacity %s OkA)
  (Widget|SetRenderOpacity %s InfoA)
  %s
  %s
  %s
  %s
  %s
  %s
  %s
  %s)
''' % (V('BoxWarn'), V('BoxOk'), V('BoxInfo'), TX('TxtOk', 'Ok'), TX('TxtHead', 'Head'), TX('TxtBody1', 'B1'), TX('TxtBody2', 'B2'),
       TX('TxtPC', 'PC'), TX('TxtQuest', 'Quest'), TX('TxtState', 'State'), TX('TxtMuse', 'Muse'))
ORDER = ['Show']
