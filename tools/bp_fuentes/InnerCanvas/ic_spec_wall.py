# ic_spec_wall.py - estructura de los Blueprints de la pantalla del PC de Inner Canvas -> ic_spec_wall.json (lo lee build_ic)
import json, os
IC = '/Game/InnerCanvas/Blueprints/'
F, I, B, S, VEC, LCL = 'float', 'int', 'bool', 'string', 'Vector', 'LinearColor'
O = lambda c: 'obj:' + c
STROKE = O('/SC_Draw/Blueprints/BP_TBStroke.BP_TBStroke_C')
MSG = 'struct:/Script/OSC.OSCMessage'


def v(name, t, ed=False, arr=False):
    return [name, t, 'Default', ed, arr]


BPS = [
    dict(name='BP_ICWall_IC', path=IC + 'BP_ICWall_IC', create=True, remove_funcs=[], remove_vars=[], comps=[],
         vars=[v('Ses', I, arr=True), v('Names', S, arr=True), v('Phases', I, arr=True), v('TL', F, arr=True), v('Inks', F, arr=True),
               v('Spin', B, arr=True), v('Cur', STROKE, arr=True), v('NoStroke', STROKE), v('CurIdx', I, arr=True), v('Knots', I, arr=True),
               v('LastRx', F, arr=True), v('Origins', VEC, arr=True), v('Pivots', O('/Script/Engine.Actor'), arr=True),
               v('RTs', O('/Script/Engine.TextureRenderTarget2D'), arr=True), v('Fl', F, arr=True), v('Addr', S), v('C', I), v('S', I),
               v('RxCount', I), v('Server', O('/Script/OSC.OSCServer')), v('PresK', F, arr=True), v('GrowSpeed', F, ed=True),
               v('ListenPort', I, ed=True), v('CellGap', F, ed=True), v('SpinDeg', F, ed=True), v('SwOn', B, ed=True), v('SwStr', F, ed=True),
               v('SwWave', F, ed=True), v('SwSpeed', F, ed=True), v('SwSpan', F, ed=True), v('SwSpeedVar', F, ed=True), v('SwScale', F, ed=True),
               v('SwDir', VEC, ed=True), v('SwFade', F, ed=True), v('PresFit', F, ed=True), v('PresHideT', F, ed=True),
               v('PresShowT', F, ed=True), v('PresPh', I, arr=True), v('PresT', F, arr=True),
               v('Tmp', O('/Script/Engine.Actor'), arr=True)],
         funcs=[('WallBoot', []), ('ClearCell', [('Cell', I, True)]), ('NewSes', []), ('OnState', []), ('OnName', [('Message', MSG, True)]),
                ('EndCur', [('Cell', I, True)]), ('StrokeHead', []), ('StrokeKnot', []), ('OnClear', []), ('RevealCell', [('Cell', I, True), ('R', F, True)]), ('Relocate', [('Cell', I, True)]),
                ('PresStep', [('Cell', I, True), ('Dt', F, True)]), ('OnPresent', []),
                ('Route', [('Message', MSG, True)]), ('OnMsg', [('Message', MSG, True)]), ('WallTick', [('Dt', F, True)])],
         cdo={'ListenPort': 9300, 'CellGap': 100000.0, 'GrowSpeed': 1.2, 'SpinDeg': 20.0, 'SwOn': True, 'SwStr': 2.739429, 'SwWave': 0.18, 'SwSpeed': 0.5,
              'SwSpan': 40.0, 'SwSpeedVar': 0.6, 'SwScale': 0.03, 'SwDir': {'x': 1.0, 'y': 0.6, 'z': 0.15}, 'SwFade': 1.2, 'PresFit': 290.0, 'PresHideT': 2.0, 'PresShowT': 2.5}),
    dict(name='BP_ICWallHUD_IC', path=IC + 'BP_ICWallHUD_IC', create=True, remove_funcs=[], remove_vars=[], comps=[],
         vars=[v('Wall', O(IC + 'BP_ICWall_IC.BP_ICWall_IC_C')), v('BgColor', LCL, ed=True), v('NumColor', LCL, ed=True),
               v('TextColor', LCL, ed=True), v('InkColor', LCL, ed=True), v('InkBg', LCL, ed=True), v('FS', F, ed=True), v('FS2', F, ed=True)],
         funcs=[('FindWall', []), ('DrawCells', [('W', F, True), ('H', F, True)]), ('DrawWall', [('W', F, True), ('H', F, True)])],
         cdo={'BgColor': {'r': 0.01, 'g': 0.03, 'b': 0.025, 'a': 1.0}, 'NumColor': {'r': 0.55, 'g': 1.0, 'b': 0.75, 'a': 0.9},
              'TextColor': {'r': 1.0, 'g': 1.0, 'b': 1.0, 'a': 1.0}, 'InkColor': {'r': 0.45, 'g': 1.0, 'b': 0.62, 'a': 1.0},
              'InkBg': {'r': 1.0, 'g': 1.0, 'b': 1.0, 'a': 0.15}, 'FS': 1.6, 'FS2': 1.8}),
    dict(name='BP_ICSpace_IC', path=IC + 'BP_ICSpace_IC', create=False, remove_funcs=[], remove_vars=[], comps=[],
         vars=[v('AutoPlace', B, ed=True)], funcs=[], cdo={'AutoPlace': True}),
]

if __name__ == '__main__':
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ic_spec_wall.json')
    json.dump({'bps': BPS}, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('ok', out)
