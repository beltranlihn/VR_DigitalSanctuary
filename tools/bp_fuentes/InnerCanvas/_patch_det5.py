# parche 2026-11-13 (Beltran): nombre que se achica si es largo (no se sale del marco del HUD), Dibujar a la profundidad de las otras
# etiquetas y mas a la izquierda (lo tapaba el mando), HUD: circulo de tinta pegado al vidrio y por delante, fondo del panel 15 % mas
# transparente.
import io


def sub(path, pairs):
    s = io.open(path, encoding='utf-8').read()
    for old, new in pairs:
        assert s.count(old) == 1, (path, old[:80])
        s = s.replace(old, new, 1)
    io.open(path, 'w', encoding='utf-8').write(s)


# teclado: el nombre (y la pregunta) se miden y se achican para no pasar de 1126 px de los 2048 (= el ancho de la caja del nombre en el
# HUD; en el campo del teclado sobra)
sub('ic_kb_dsl.py', [
    ("  (bind (_cv _sz _ctx) (Rendering|BeginDrawCanvastoRenderTarget :TextureRenderTarget %(nw)s))\n  (Canvas|DrawText _cv :RenderFont \"%(font)s\" :RenderText _txt :ScreenPosition %(mid)s :Scale (select _has %(sc)s %(sch)s)",
     "  (bind (_cv _sz _ctx) (Rendering|BeginDrawCanvastoRenderTarget :TextureRenderTarget %(nw)s))\n"
     "  (bind _tsz (Canvas|ClippedTextSize _cv :RenderFont \"%(font)s\" :RenderText _txt :Scale (Math|Vector2D|MakeVector2D 1.0 1.0)))\n"
     "  (bind (_tw _th) (Math|Vector2D|BreakVector2D _tsz))\n"
     "  (bind _fk (Math|Float|Min(Float) (select _has 2.5 1.85) (/ 1126.0 (Math|Float|Max(Float) _tw 1.0))))\n"
     "  (Canvas|DrawText _cv :RenderFont \"%(font)s\" :RenderText _txt :ScreenPosition %(mid)s :Scale (Math|Vector2D|MakeVector2D _fk _fk)"),
])

# tutor: Dibujar a la profundidad de las demas etiquetas; fondo del marco 15 % mas transparente (Rim.y 0,32 -> 0,272)
sub('ic_tutor2_dsl.py', [
    ("a5=SETA('Anch', '5', '(Math|Vector|MakeVector (- (.x _tl) 6.0) (.y _tl) (.z _tl))'),",
     "a5=SETA('Anch', '5', '(Math|Vector|MakeVector _ax (.y _tl) (.z _tl))'),"),
    ("  (Rendering|SetTranslucentSortPriority %(frame)s 1)\n",
     "  (Rendering|SetTranslucentSortPriority %(frame)s 1)\n  (Rendering|Material|SetVectorParameterValueonMaterials %(frame)s \"Rim\" (Math|Vector|MakeVector 0.45 0.272 0.85))\n"),
])
p = io.open('ic_spec_tutor.py', encoding='utf-8').read()
p = p.replace("{'x': 0.0, 'y': -8.0, 'z': 0.0}]})]", "{'x': 0.0, 'y': -14.0, 'z': 0.0}]})]", 1)
io.open('ic_spec_tutor.py', 'w', encoding='utf-8').write(p)

# HUD: el circulo de tinta pegado al vidrio, coplanar y por delante (con la curvatura los nidos se le ponian delante y titilaba)
sub('ic_kit_dsl.py', [
    ("    (Rendering|SetTranslucentSortPriority (Variables|Default|GetTimerQuad) 12)\n",
     "    (bind _ir (Class|SceneComponent|GetRelativeLocation (Variables|Default|GetInkDisc)))\n"
     "    (Transformation|SetRelativeLocationAndRotation (Variables|Default|GetInkDisc) (Math|Vector|MakeVector (.x _ir) (.y _ir) 0.3) (Math|Rotator|MakeRotator 0.0 0.0 0.0) false true)\n"
     "    (Rendering|SetTranslucentSortPriority (Variables|Default|GetInkDisc) 12)\n"
     "    (Rendering|SetTranslucentSortPriority (Variables|Default|GetTimerQuad) 12)\n"),
])
print('ok')
