# ic_spec.py - la estructura de los Blueprints de Inner Canvas (variables, funciones, componentes, valores del CDO).
# python ic_spec.py -> ic_spec.json, que lee build_ic.py (estructura) y cdo_ic.py (valores) dentro de Unreal.
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ic_kb_layout as KL

IC = '/Game/InnerCanvas/Blueprints/'
F, I, B, S, VEC, LCL = 'float', 'int', 'bool', 'string', 'Vector', 'LinearColor'
O = lambda c: 'obj:' + c
SND = O('/Script/Engine.SoundBase')
SMC = O('/Script/Engine.StaticMeshComponent')
RIG = O('/SC_Sequencer/Blueprints/BP_SeqRig_SC.BP_SeqRig_SC_C')
TB = O('/SC_Draw/Blueprints/BP_TBDirector_NC.BP_TBDirector_NC_C')
STROKE = O('/SC_Draw/Blueprints/BP_TBStroke.BP_TBStroke_C')
BTN = O('/Game/SoulCharger/Shared/Results/Blueprints/BP_ShareButton_SC.BP_ShareButton_SC_C')
MID = O('/Script/Engine.MaterialInstanceDynamic')
RT = O('/Script/Engine.TextureRenderTarget2D')
TEX = O('/Script/Engine.Texture')
PLANE = '/Engine/BasicShapes/Plane.Plane'
VO = lambda n: '/Game/InnerCanvas/Audio/VO/%s.%s' % (n, n)
ROTTXT = '(Pitch=0.000000,Yaw=90.000000,Roll=90.000000)'


def v(name, t, cat='Default', ed=False, arr=False):
    return [name, t, cat, ed, arr]


def comp(name, mesh=PLANE, mat=None, loc=(0, 0, 0), rot='(Pitch=0.000000,Yaw=0.000000,Roll=0.000000)', scale=(1, 1, 1), coll=False, hidden=False):
    return dict(name=name, mesh=mesh, mat=mat, loc=loc, rot=rot, scale=scale, coll=coll, hidden=hidden)


BPS = []

# ---------------- director ----------------
flow_vo = ['VoWelcome', 'VoSpace', 'VoInvite', 'VoGrab', 'VoPalette', 'VoGo', 'Vo30', 'VoInk', 'VoTime', 'VoNoInk', 'VoLook', 'VoThanks']
BPS.append(dict(
    name='BP_ICFlow_IC', path=IC + 'BP_ICFlow_IC', create=False,
    remove_funcs=['FinSpawn', 'FinShow', 'FinPick', 'SayPage', 'MoveTable', 'FPanel', 'GoAdjust', 'ShowPanel', 'SaveHands', 'RestoreHands',
                  'PickGo', 'BreathCount', 'BreathSay', 'BreathCue', 'BreathTick', 'HeartFig', 'HeartTick', 'LogPivot', 'ShiftStart',
                  'ShiftStep', 'FindLink', 'RemoteSync', 'RobotHold', 'RenderPctStep'],
    remove_vars=['Exp', 'MenuLevel', 'TopeS', 'ResultsHold', 'SensorColor', 'Breaths', 'BreathWait', 'SpinTurnsT', 'ShiftCm', 'Black', 'Page',
                 'bEnv', 'ZoneT', 'BreathN', 'bLow', 'StageT', 'bVo2Done', 'bShifted', 'ShiftT', 'ShiftK', 'ShiftVec', 'HandHidden',
                 'Vo1', 'Vo2', 'Vo3', 'Pages', 'Card', 'Go', 'Results', 'BStage', 'BRig', 'Tool', 'HandComps', 'Images', 'WinRingMat',
                 'RemotePhase', 'bRemoteRight', 'bRobotMode', 'ZoneWait', 'GoWait', 'MLink', 'bHold', 'HM', 'bSaidH1', 'bSaidH2',
                 'FigZ', 'HeartPulses', 'Fin', 'bFinDone', 'bSaidH3', 'bSaidH4', 'Poem1At', 'Poem2At', 'Pacer', 'LastPh', 'bSetF1',
                 'bSetF2', 'bSaidCount', 'bSaidNat', 'FinIn', 'FinHold', 'FinEx', 'FinEmpty', 'SighIn', 'SighEx', 'PanelAt', 'TitleO0',
                 'TitleO1', 'TitleHide', 'RenderPct', 'bPctDone', 'TraceColor', 'Voice', 'Kit', 'Amb'],
    vars=[v('Voice', O(IC + 'BP_ICVoice_IC.BP_ICVoice_IC_C')), v('Kit', O(IC + 'BP_ICHudKit_IC.BP_ICHudKit_IC_C')),
          v('Amb', O(IC + 'BP_ICAmb_IC.BP_ICAmb_IC_C')), v('Kb', O(IC + 'BP_ICKeyboard_IC.BP_ICKeyboard_IC_C')),
          v('Link', O(IC + 'BP_ICLink_IC.BP_ICLink_IC_C')), v('Space', O(IC + 'BP_ICSpace_IC.BP_ICSpace_IC_C')),
          v('Rig2', RIG), v('BtnEn', BTN), v('BtnEs', BTN), v('NameMID', MID),
          v('LangES', B), v('NameStr', S), v('EndInk', B), v('Said07', B), v('Said08', B), v('Said11', B), v('Center', VEC),
          v('QuietT', F), v('Session', I), v('LastPressN2', I), v('Clk1', B), v('Clk2', B), v('ClkES', B), v('Ink01', F),
          v('LogoR0', F, ed=True), v('LogoR1', F, ed=True), v('ButtonsAt', F, ed=True), v('VoGap', F, ed=True),
          v('SpinShow', F, ed=True), v('CloseHold', F, ed=True), v('InkM', F, ed=True), v('PresentK', F, ed=True),
          v('PresentZ', F, ed=True), v('SpaceSize', F, ed=True), v('SpaceH', F, ed=True), v('GuardM', F, ed=True),
          v('AutoLang', I, ed=True), v('AutoName', S, ed=True), v('ResetMode', I, ed=True), v('ICLevel', S, ed=True),
          v('HintLang', S, ed=True), v('HintName', S, ed=True)] + [v(n, SND, ed=True) for n in flow_vo],
    funcs=[('ResetVars', []), ('FPlaceClose', []), ('NameSetup', []), ('ChooseLang', [('ES', B, True)]), ('PickLang', []),
           ('KbWait', []), ('ShowPed', []), ('DrawGuard', []), ('LinkSync', []), ('IntroTick', [('Dt', F, True)]),
           ('GuideTick', [('Dt', F, True)]), ('ICReset', [])],
    comps=[comp('Logo', mat='/Game/SoulCharger/Obra/Titles/MI_Logo_ADS.MI_Logo_ADS'),
           comp('NameP', mat='/Game/SoulCharger/Demo/Materials/M_DemoResPane_SC.M_DemoResPane_SC')],
    cdo={'EyeRef': 165.0, 'VeilA0': 0.5, 'VeilA1': 3.0, 'TitleR0': 1.2, 'TitleR1': 2.6, 'LogoR0': 2.0, 'LogoR1': 3.4, 'ButtonsAt': 3.8,
         'DrawTime': 180.0, 'PracticeM': 1.0, 'PracticeWait': 45.0, 'GrabWait': 25.0, 'VoGap': 0.8, 'SpinShow': 20.0,
         'CloseHold': 7.0, 'InkM': 120.0, 'PresentK': 1.0, 'PresentZ': 130.0, 'SpaceSize': 300.0, 'SpaceH': 300.0, 'GuardM': 10.0,
         'AutoLang': -1, 'AutoName': '', 'ResetMode': 0, 'ICLevel': 'L_InnerCanvas', 'HintLang': 'HINT_LANG', 'HintName': 'HINT_NAME',
         'TagTitle': 'sc4_title', 'TitleMI': '/Game/InnerCanvas/Materials/MI_TourTitle_INNERCANVAS.MI_TourTitle_INNERCANVAS',
         'CTop': {'r': 0.80, 'g': 0.88, 'b': 0.84, 'a': 1.0}, 'CHor': {'r': 0.62, 'g': 0.72, 'b': 0.68, 'a': 1.0},
         'VoWelcome': VO('IC_01'), 'VoSpace': VO('IC_02'), 'VoInvite': VO('IC_03'), 'VoGrab': VO('IC_04'), 'VoPalette': VO('IC_05'),
         'VoGo': VO('IC_06'), 'Vo30': VO('IC_07'), 'VoInk': VO('IC_08'), 'VoTime': VO('IC_09'), 'VoNoInk': VO('IC_10'),
         'VoLook': VO('IC_11'), 'VoThanks': VO('IC_12')}))

# ---------------- HUD ----------------
BPS.append(dict(
    name='BP_ICHudKit_IC', path=IC + 'BP_ICHudKit_IC', create=False,
    remove_funcs=['KitFindRig', 'KitDisc', 'KitSister', 'HudShowNow'], remove_vars=[],
    vars=[v('InkK', F), v('InkShown', F), v('NameTex', TEX), v('NameMID', MID), v('InkColor', LCL, ed=True)],
    funcs=[('KitPaneLook', [('C', SMC, True)]), ('KitSetInk', [('K', F, True)]), ('KitSetName', [('Tex', TEX, True)]), ('KitReset', [])],
    comps=[comp('InkDisc', mat='/Game/SoulCharger/Shared/HUD/Materials/M_ChargeHalo_SC.M_ChargeHalo_SC'), comp('NameQuad')],
    cdo={'Mode': 4, 'AutoShow': -1.0, 'bShowNow': False, 'InkK': 1.0, 'InkShown': 1.0,
         'InkColor': {'r': 0.45, 'g': 1.0, 'b': 0.62, 'a': 1.0}}))

# ---------------- teclado ----------------
pos = KL.layout()
ren, res = KL.rects()
kcomps = [comp('Board', loc=(0.6, KL.BOARD[0], KL.BOARD[1]), rot=ROTTXT, scale=(KL.BOARD[2] / 100.0, KL.BOARD[3] / 100.0, 1), coll=True, hidden=True),
          comp('Field', mat='/Game/SoulCharger/Demo/Materials/M_DemoResPane_SC.M_DemoResPane_SC', loc=(0, KL.FIELD[0], KL.FIELD[1]), rot=ROTTXT,
               scale=(KL.FIELD[2] / 100.0, KL.FIELD[3] / 100.0, 1))]
for i, (y, z, w, h) in enumerate(pos):
    kcomps.append(comp('K_%02d' % i, mat='/Game/InnerCanvas/Materials/M_ICKey_IC.M_ICKey_IC', loc=(0, y, z), rot=ROTTXT, scale=(w / 100.0, h / 100.0, 1)))
BPS.append(dict(
    name='BP_ICKeyboard_IC', path=IC + 'BP_ICKeyboard_IC', create=True, remove_funcs=[], remove_vars=[],
    vars=[v('Keys', SMC, arr=True), v('Hov', F, arr=True), v('KeyY', F, arr=True), v('KeyZ', F, arr=True), v('KeyW', F, arr=True),
          v('KeyH', F, arr=True), v('RectEN', VEC, arr=True), v('RectES', VEC, arr=True), v('CharsUp', S, arr=True), v('CharsLo', S, arr=True),
          v('NameStr', S), v('Done', B), v('Shown', B), v('Vanish', B), v('Typing', B), v('Caret', B), v('ES', B), v('Rig', RIG), v('Rig2', RIG),
          v('LastP1', I), v('LastP2', I), v('HitIdx', I), v('H1', I), v('H2', I), v('Clk1', B), v('Clk2', B), v('AppearK', F), v('BlinkT', F),
          v('NameWork', RT), v('NameRT', RT), v('FieldMID', MID),
          v('MaxLen', I, ed=True), v('Dist', F, ed=True), v('Below', F, ed=True), v('FieldColor', LCL, ed=True), v('TextColor', LCL, ed=True),
          v('PromptColor', LCL, ed=True), v('PromptEN', S, ed=True), v('PromptES', S, ed=True), v('ClickSound', SND, ed=True),
          v('PH1', I), v('PH2', I), v('HoverSound', SND, ed=True), v('HoverVol', F, ed=True), v('ClickVol', F, ed=True)],
    funcs=[('KbBoot', []), ('KbFade', []), ('KbDraw', []), ('KbShow', [('Spanish', B, True)]), ('KbHide', []), ('KbReset', []),
           ('KbSetName', [('Name', S, True)]), ('KbHit', [('R', RIG, True)]), ('KbPress', [('I', I, True)]), ('KbTick', [('Dt', F, True)])],
    comps=kcomps, tags=['Aimable'],
    cdo={'KeyY': [p[0] for p in pos], 'KeyZ': [p[1] for p in pos], 'KeyW': [p[2] for p in pos], 'KeyH': [p[3] for p in pos],
         'RectEN': [{'x': r[0], 'y': r[1], 'z': r[2]} for r in ren], 'RectES': [{'x': r[0], 'y': r[1], 'z': r[2]} for r in res],
         'CharsUp': KL.CHARS_UP, 'CharsLo': KL.CHARS_LO, 'HitIdx': -1, 'H1': -1, 'H2': -1,
         'MaxLen': 14, 'Dist': 70.0, 'Below': 28.0, 'FieldColor': {'r': 0.10, 'g': 0.22, 'b': 0.16, 'a': 1.0},
         'TextColor': {'r': 1.0, 'g': 1.0, 'b': 1.0, 'a': 1.0}, 'PromptColor': {'r': 0.62, 'g': 0.85, 'b': 0.74, 'a': 0.85},
         'PromptEN': "WHAT'S YOUR NAME?", 'PromptES': '¿CÓMO TE LLAMAS?',
         'ClickSound': '/Game/InnerCanvas/Audio/SFX/SND_IC_SelectTecla.SND_IC_SelectTecla', 'HoverSound': '/Game/InnerCanvas/Audio/SFX/SND_IC_HoverTecla.SND_IC_HoverTecla', 'PH1': -1, 'PH2': -1, 'HoverVol': 0.2, 'ClickVol': 0.5}))

# ---------------- enlace al PC ----------------
BPS.append(dict(
    name='BP_ICLink_IC', path=IC + 'BP_ICLink_IC', create=True, remove_funcs=[], remove_vars=[],
    vars=[v('Slot', I, ed=True), v('WallIP', S, ed=True), v('Port', I, ed=True), v('StateHz', F, ed=True),
          v('Client', O('/Script/OSC.OSCClient')), v('Msg', 'struct:/Script/OSC.OSCMessage'), v('Session', I), v('NameStr', S), v('Phase', I),
          v('TimeLeft', F), v('Ink', F), v('LangES', B), v('StT', F), v('NmT', F), v('TB', TB), v('Center', VEC), v('SentStrokes', I),
          v('SentKnots', I), v('KBase', I), v('KTo', I), v('Ready', B), v('Hist', STROKE, arr=True)],
    funcs=[('LinkBoot', []), ('LinkState', [('P', I, True), ('TL', F, True), ('InkK', F, True), ('ES', B, True)]), ('SendState', []),
           ('SendName', []), ('LinkNew', [('Name', S, True), ('Ses', I, True)]), ('LinkClear', []),
           ('LinkPresent', [('Pivot', VEC, True), ('K', F, True)]), ('SendHead', [('S', STROKE, True), ('I', I, True)]),
           ('SendKnot', [('S', STROKE, True), ('I', I, True), ('K', I, True)]), ('SendEnd', [('I', I, True), ('N', I, True)]),
           ('FlushKnots', [('S', STROKE, True), ('I', I, True)]), ('StreamStrokes', []), ('LinkTick', [('Dt', F, True)])],
    comps=[], cdo={'Slot': 1, 'WallIP': '192.168.1.10', 'Port': 9300, 'StateHz': 5.0}))

# ---------------- espacio 3 x 3 ----------------
MW = '/Game/InnerCanvas/Materials/MI_ICSpaceWall_IC.MI_ICSpaceWall_IC'
MF = '/Game/InnerCanvas/Materials/MI_ICSpaceFloor_IC.MI_ICSpaceFloor_IC'
WALLX = '(Pitch=90.000000,Yaw=0.000000,Roll=0.000000)'
WALLY = '(Pitch=90.000000,Yaw=90.000000,Roll=0.000000)'
BPS.append(dict(
    name='BP_ICSpace_IC', path=IC + 'BP_ICSpace_IC', create=True, remove_funcs=[], remove_vars=[],
    vars=[v('Shown', B), v('RevealT', F), v('NXp', F), v('NXn', F), v('NYp', F), v('NYn', F),
          v('Size', F, ed=True), v('NearCm', F, ed=True), v('HoldT', F, ed=True), v('BaseAlpha', F, ed=True), v('FloorAlpha', F, ed=True),
          v('LineColor', LCL, ed=True), v('WarnOn', B), v('WarnIn', F, ed=True), v('WarnOut', F, ed=True), v('RingA', F, ed=True),
          v('FlipX', F, ed=True), v('FlipY', F, ed=True)],
    funcs=[('SpaceBoot', []), ('SpaceReveal', []), ('SpaceReset', []), ('NearOf', [('Pt', VEC, True)]), ('SpaceTick', [('Dt', F, True)])],
    comps=[comp('Floor', mat=MF, loc=(0, 0, 0.5), scale=(3, 3, 1)),
           comp('WallXp', mat=MW, loc=(150, 0, 150), rot=WALLX, scale=(3, 3, 1)),
           comp('WallXn', mat=MW, loc=(-150, 0, 150), rot=WALLX, scale=(3, 3, 1)),
           comp('WallYp', mat=MW, loc=(0, 150, 150), rot=WALLY, scale=(3, 3, 1)),
           comp('WallYn', mat=MW, loc=(0, -150, 150), rot=WALLY, scale=(3, 3, 1))],
    cdo={'Size': 300.0, 'NearCm': 70.0, 'HoldT': 3.0, 'BaseAlpha': 0.08, 'FloorAlpha': 0.45, 'RevealT': -1.0,
         'LineColor': {'r': 0.55, 'g': 1.0, 'b': 0.75, 'a': 1.0}, 'WarnIn': 30.0, 'WarnOut': 45.0, 'RingA': 0.6, 'FlipX': 1.0, 'FlipY': 1.0}))

if __name__ == '__main__':
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ic_spec.json')
    json.dump({'bps': BPS}, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('ok', out, [b['name'] for b in BPS])
