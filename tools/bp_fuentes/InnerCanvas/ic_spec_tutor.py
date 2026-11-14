# ic_spec_tutor.py - estructura de BP_ICTutor_IC (el tutorial visual de Inner Canvas) -> ic_spec_tutor.json
# v1 (2026-11-12): 6 etiquetas L0..L5 y 6 lineas K0..K5 (planos con MI_ICLabel_IC). La paleta de muestra se crea en runtime.
# v2 (2026-11-12 noche, PDF de Beltran, memoria ic-recorrido-v2-marco): MARCO de instrucciones (Frame, M_ICPanel_IC) con el logo
# (Logo) y "Instructions" (Hdr); etiquetas de texto liso (M_ICText_IC + atlas T_ICTexts) con punto en el ancla (DA) y en la punta (DB);
# mantos blancos M0..M4 (M_ICMantle_IC) que en runtime se cuelgan de la Base de la paleta; cartas de la mano dominante (CardL, CardR +
# CardHit con colision para el laser, Sel, CapL, CapR); pistas bajo los botones / el teclado (H0, H1) y el aviso de borde pegado a la
# vista (Warn). Actor con +X lejos de la persona, +Y a su derecha, +Z arriba (como el teclado).
import json, os
IC = '/Game/InnerCanvas/Blueprints/'
F, I, B, S, VEC, LCL, ROT = 'float', 'int', 'bool', 'string', 'Vector', 'LinearColor', 'Rotator'
O = lambda c: 'obj:' + c
PLANE = '/Engine/BasicShapes/Plane.Plane'
LAB = '/Game/InnerCanvas/Materials/MI_ICLabel_IC.MI_ICLabel_IC'
TXT = '/Game/InnerCanvas/Materials/M_ICText_IC.M_ICText_IC'
PAN = '/Game/InnerCanvas/Materials/M_ICPanel_IC.M_ICPanel_IC'
MAN = '/Game/InnerCanvas/Materials/M_ICMantle_IC.M_ICMantle_IC'
TITLE = '/Game/InnerCanvas/Materials/MI_TourTitle_INNERCANVAS.MI_TourTitle_INNERCANVAS'
ROTTXT = '(Pitch=0.000000,Yaw=90.000000,Roll=90.000000)'
PAL = O('/SC_Draw/Blueprints/BP_DrawPalette_SC.BP_DrawPalette_SC_C')
PED = O('/SC_Base/Blueprints/BP_QuestCtrl_SC.BP_QuestCtrl_SC_C')
STROKE = O('/SC_Draw/Blueprints/BP_TBStroke.BP_TBStroke_C')
TB = O('/SC_Draw/Blueprints/BP_TBDirector_NC.BP_TBDirector_NC_C')
SMC = O('/Script/Engine.StaticMeshComponent')


def v(name, t, ed=False, arr=False):
    return [name, t, 'Default', ed, arr]


def comp(name, mat=LAB, rot=ROTTXT, coll=False, hidden=False, scale=(0.05, 0.03, 1)):
    return dict(name=name, mesh=PLANE, mat=mat, loc=(0, 0, 0), rot=rot, scale=scale, coll=coll, hidden=hidden)


R = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tutor_rects.json')))
ZERO = '(Pitch=0.000000,Yaw=0.000000,Roll=0.000000)'
COMPS = ([comp('L%d' % k) for k in range(6)] + [comp('K%d' % k) for k in range(6)] +
         [comp('Frame', mat=PAN), comp('Logo', mat=TITLE), comp('Hdr', mat=TXT)] +
         [comp('DA%d' % k, mat=TXT) for k in range(6)] + [comp('DB%d' % k, mat=TXT) for k in range(6)] +
         [comp('M%d' % k, mat=MAN, rot=ZERO) for k in range(5)] +
         [comp('CardL', mat=PAN), comp('CardR', mat=PAN), comp('CardHit', mat=PAN, coll=True, hidden=True),
          comp('Sel', mat=TXT), comp('CapL', mat=TXT), comp('CapR', mat=TXT),
          comp('H0', mat=TXT), comp('H1', mat=TXT), comp('Warn', mat=TXT)])
BPS = [dict(
    name='BP_ICTutor_IC', path=IC + 'BP_ICTutor_IC', create=True, remove_funcs=[], remove_vars=[],
    vars=[v('Pal', PAL), v('Ped', PED), v('Stroke', STROKE), v('TB', TB), v('Sd', F), v('ES', B), v('Run', B), v('T', F), v('DemoT', F),
          v('DemoPrev', F), v('OutT', F), v('On', B, arr=True), v('LabK', F, arr=True), v('Anch', VEC, arr=True), v('Labs', SMC, arr=True),
          v('Lines', SMC, arr=True), v('KeyC', SMC, arr=True), v('KeyW', VEC, arr=True), v('KeyD', VEC, arr=True), v('Pc', VEC),
          v('RestRot', ROT), v('DrawRot', ROT),
          v('RectEN', VEC, ed=True, arr=True), v('RectES', VEC, ed=True, arr=True), v('LabOff', VEC, ed=True, arr=True),
          v('Dist', F, ed=True), v('Below', F, ed=True), v('PalScale', F, ed=True), v('PalY', F, ed=True), v('PedY', F, ed=True),
          v('LabH', F, ed=True), v('TipL', F, ed=True), v('LineW', F, ed=True),
          # v2
          v('PalL', PAL), v('PalR', PAL), v('CtlL', PED), v('CtlR', PED), v('DotsA', SMC, arr=True), v('DotsB', SMC, arr=True),
          v('Mants', SMC, arr=True), v('TouchC', VEC), v('TouchB', VEC), v('PedP', VEC), v('CardsT', F), v('CardsOn', B), v('PickT', F),
          v('PickR', B), v('Hov', I), v('HitK', I), v('HintOn', B), v('HintK', F), v('WarnOn', B), v('WarnK', F), v('WarnAtt', B),
          v('FrameK', F), v('FrameOn', B), v('FrameT', F), v('HintM', I), v('MSign', F, ed=True),
          v('FrameW', F, ed=True), v('FrameH', F, ed=True), v('FrameX', F, ed=True), v('FrameZ', F, ed=True), v('LogoW', F, ed=True),
          v('HdrH', F, ed=True), v('DotD', F, ed=True), v('PedScale', F, ed=True), v('PalZ', F, ed=True), v('PedZ', F, ed=True),
          v('CardW', F, ed=True), v('CardH', F, ed=True), v('CardY', F, ed=True), v('MiniPal', F, ed=True), v('MiniCtl', F, ed=True),
          v('HintH', F, ed=True), v('WarnH', F, ed=True), v('WarnD', F, ed=True), v('LabB', VEC, ed=True, arr=True),
          v('PalInSound', O('/Script/Engine.SoundBase'), ed=True), v('PrevHov', I),
          v('CardHovSound', O('/Script/Engine.SoundBase'), ed=True), v('CardOutSound', O('/Script/Engine.SoundBase'), ed=True)],
    funcs=[('TutBoot', []), ('TutBegin', [('Spanish', B, True), ('Right', B, True), ('PedA', PED, True), ('TBA', TB, True)]),
           ('PlaceLabels', []), ('TutShow', [('K', I, True)]), ('TutDemo', []), ('TutOut', []), ('TutHide', []), ('LabTick', [('Dt', F, True)]),
           ('DemoStep', []), ('OutStep', []), ('TutTick', [('Dt', F, True)]),
           ('TutCards', []), ('CardsSpawn', []), ('CardHov', [('R', O('/SC_Sequencer/Blueprints/BP_SeqRig_SC.BP_SeqRig_SC_C'), True)]),
           ('TutPick', [('Right', B, True)]), ('HintShow', [('Mode', I, True), ('Spanish', B, True), ('Pos', VEC, True)]), ('HintOff', []),
           ('WarnSet', [('On', B, True)]), ('MantleSet', []), ('StrokeOut', [('R', F, True)]), ('Kill', [('A', O('/Script/Engine.Actor'), True)]), ('FrameShow', []), ('PalSndAll', [('Mute', B, True)])],
    comps=COMPS,
    cdo={'RectEN': [{'x': r[0], 'y': r[1], 'z': r[2]} for r in R['en']], 'RectES': [{'x': r[0], 'y': r[1], 'z': r[2]} for r in R['es']],
         'LabOff': [{'x': -0.6, 'y': 9.0, 'z': 8.0}, {'x': -0.6, 'y': -9.0, 'z': 9.0}, {'x': -0.6, 'y': 0.0, 'z': -9.0},
                    {'x': -0.6, 'y': -10.0, 'z': -6.0}, {'x': -0.6, 'y': -10.0, 'z': 4.0}, {'x': -0.6, 'y': 7.0, 'z': -8.0}],
         'Dist': 150.0, 'Below': 2.0, 'PalScale': 0.91, 'PalY': 15.0, 'PedY': 43.0, 'LabH': 4.0, 'TipL': 6.0, 'LineW': 0.22,
         'DemoT': -1.0, 'OutT': -1.0, 'CardsT': -1.0, 'PickT': -1.0,
         'FrameW': 137.0, 'FrameH': 75.0, 'FrameX': 7.0, 'FrameZ': 0.0, 'LogoW': 64.0, 'HdrH': 6.0, 'DotD': 1.1, 'PedScale': 1.8,
         'PalZ': -2.5, 'PedZ': -9.0, 'CardW': 52.0, 'CardH': 30.0, 'CardY': 33.0, 'MiniPal': 0.5, 'MiniCtl': 1.25,
         'HintH': 3.6, 'WarnH': 3.0, 'WarnD': 55.0, 'MSign': 1.0, 'PrevHov': -1, 'CardHovSound': '/Game/SoulCharger/Demo/Audio/Mix/SND_Demo_HoverOn.SND_Demo_HoverOn', 'CardOutSound': '/Game/SoulCharger/Demo/Audio/Mix/SND_Demo_HoverOut.SND_Demo_HoverOut', 'PalInSound': '/Game/InnerCanvas/Audio/SFX/SND_IC_PaletteIn.SND_IC_PaletteIn',
         'LabB': [{'x': 0.0, 'y': 8.7, 'z': 0.0}, {'x': 0.0, 'y': -11.5, 'z': 7.0}, {'x': 0.0, 'y': 6.6, 'z': -7.5},
                  {'x': 0.0, 'y': -8.9, 'z': 0.0}, {'x': 0.0, 'y': -8.9, 'z': 0.0}, {'x': 0.0, 'y': -14.0, 'z': 0.0}]})]

if __name__ == '__main__':
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ic_spec_tutor.json')
    json.dump({'bps': BPS}, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('ok', out)
