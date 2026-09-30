# -*- coding: utf-8 -*-
"""make_spec.py - genera ghost_spec.json: variables (tipo, categoria, default, instance-editable) y parametros de
cada funcion de BP_GhostTake_SC, BP_GhostPlayer_SC y BP_GhostRecorder_SC, mas la lista de los 10 DA.
Lo leen lint_dsl.py (chequeo cruzado) y ghost_build.py (creacion en el turno)."""
import io
import json
import os

AQUI = os.path.dirname(os.path.abspath(__file__))
G = '/Game/SoulCharger/Mechanics/Ghost'
TAKE_C = G + '/BP_GhostTake_SC.BP_GhostTake_SC_C'
PLAYER_C = G + '/BP_GhostPlayer_SC.BP_GhostPlayer_SC_C'
IDS = ['GHOST_BELL', 'GHOST_TAKE', 'GHOST_PICK', 'GHOST_BREATH', 'GHOST_HEART', 'GHOST_LOVING', 'GHOST_ATTRACT',
       'GHOST_SAVE', 'GHOST_DRAW', 'GHOST_SHARE']


def da_name(i):
    return 'DA_Ghost_' + i.split('_', 1)[1].capitalize()


DAS = [G + '/Takes/' + da_name(i) + '.' + da_name(i) for i in IDS]
SMC = '/Script/Engine.StaticMeshComponent'
TRC = '/Script/Engine.TextRenderComponent'
SM = '/Script/Engine.StaticMesh'
MAT = '/Script/Engine.MaterialInterface'
SND = '/Script/Engine.SoundBase'
QC = '/Game/SoulCharger/Mechanics/QuestController/'


def v(name, cat, typ, default=None, edit=False, cls=None, cont=None):
    d = {'name': name, 'cat': cat, 'type': typ, 'edit': edit}
    if default is not None:
        d['default'] = default
    if cls:
        d['class'] = cls
    if cont:
        d['container'] = cont
    return d


def p(name, typ, cls=None, cont=None):
    d = {'name': name, 'type': typ}
    if cls:
        d['class'] = cls
    if cont:
        d['container'] = cont
    return d


spec = {}
spec['BP_GhostTake_SC'] = {
    'path': G + '/BP_GhostTake_SC', 'parent': '/Script/Engine.PrimaryDataAsset',
    'vars': [
        v('Id', 'Ghost', 'name', 'None', True), v('Text', 'Ghost', 'string', '', True),
        v('Hz', 'Ghost', 'float', 30.0, True), v('Frames', 'Ghost', 'int', 0, True),
        v('Stride', 'Ghost', 'int', 28, True), v('Data', 'Ghost', 'float', [], True, cont='array'),
        v('bUseRight', 'Ghost', 'bool', True, True), v('bUseLeft', 'Ghost', 'bool', False, True),
        v('bBeamRight', 'Ghost', 'bool', False, True), v('bBeamLeft', 'Ghost', 'bool', False, True),
        v('Note', 'Ghost', 'string', '', True)],
    'functions': {}}

TEXTS = {
    'GHOST_BELL': ('Rest your hand and hold', True, False, False, False),
    'GHOST_TAKE': ('Take it with your favorite hand', True, False, False, False),
    'GHOST_PICK': ('Point and pull the trigger', True, False, True, False),
    'GHOST_BREATH': ('Rest the sensor on your belly', True, False, False, False),
    'GHOST_HEART': ('Hold the sensor on your heart', True, False, False, False),
    'GHOST_LOVING': ('Move your hands slowly through the light', True, True, False, False),
    'GHOST_ATTRACT': ('Point · pull the trigger · place it', True, False, True, False),
    'GHOST_SAVE': ('Hold SAVE', True, True, False, False),
    'GHOST_DRAW': ('Pick a color · draw with the trigger', True, True, False, False),
    'GHOST_SHARE': ('Point at your choice and pull the trigger', True, False, True, False),
}
spec['DA'] = {'folder': G + '/Takes', 'items': [
    {'id': i, 'asset': da_name(i), 'text': TEXTS[i][0], 'R': TEXTS[i][1], 'L': TEXTS[i][2],
     'BR': TEXTS[i][3], 'BL': TEXTS[i][4]} for i in IDS]}

spec['BP_GhostPlayer_SC'] = {
    'path': G + '/BP_GhostPlayer_SC', 'parent': '/Script/Engine.Actor',
    'vars': [
        v('Takes', 'Ghost', 'object', DAS, True, cls=TAKE_C, cont='array'),
        v('StepHz', 'Ghost', 'float', 11.0, True),
        v('EchoAlpha', 'Ghost', 'float', [1.0, 0.6, 0.35, 0.15, 0.05], True, cont='array'),
        v('GhostOpacity', 'Ghost', 'float', 0.8, True), v('FadeIn', 'Ghost', 'float', 0.4, True),
        v('FadeOut', 'Ghost', 'float', 0.6, True), v('LoopGap', 'Ghost', 'float', 1.0, True),
        v('LoopFade', 'Ghost', 'float', 0.3, True), v('bShowText', 'Ghost', 'bool', True, True),
        v('TextOffset', 'Ghost', 'vector', [60.0, 0.0, -40.0], True), v('TextSize', 'Ghost', 'float', 2.4, True),
        v('TextColor', 'Ghost', 'linearcolor', [0.9, 0.9, 0.88, 1.0], True),
        # provisorios de Narrativa (los importa en su turno; si no existen, el armado los lista en cdo_no_escritas)
        v('AppearSound', 'Ghost', 'object', None, True, cls=SND),   # Narrativa asigna FX_GHOSTAPPEAR (no importado aun)
        v('VanishSound', 'Ghost', 'object', None, True, cls=SND),   # Narrativa asigna FX_GHOSTOUT
        v('SfxVol', 'Ghost', 'float', 0.8, True), v('BeamLength', 'Ghost', 'float', 140.0, True),
        v('BeamRadius', 'Ghost', 'float', 0.22, True),
        v('AutoPlayId', 'Ghost', 'name', 'None', True), v('AutoPlayDelay', 'Ghost', 'float', 2.0, True),
        v('TestColor', 'Ghost', 'linearcolor', [0.75, 0.85, 1.0, 1.0], True),
        v('BodyMeshR', 'GhostMesh', 'object', QC + 'SM_QuestCtrl_Body_R_SC.SM_QuestCtrl_Body_R_SC', cls=SM),
        v('BodyMeshL', 'GhostMesh', 'object', QC + 'SM_QuestCtrl_Body_L_SC.SM_QuestCtrl_Body_L_SC', cls=SM),
        v('TrigMeshR', 'GhostMesh', 'object', QC + 'SM_QuestCtrl_Trigger_R_SC.SM_QuestCtrl_Trigger_R_SC', cls=SM),
        v('TrigMeshL', 'GhostMesh', 'object', QC + 'SM_QuestCtrl_Trigger_L_SC.SM_QuestCtrl_Trigger_L_SC', cls=SM),
        v('BeamMesh', 'GhostMesh', 'object', '/Engine/BasicShapes/Cylinder.Cylinder', cls=SM),
        v('GhostMat', 'GhostMesh', 'object', G + '/M_Ghost_SC.M_Ghost_SC', cls=MAT),
        v('TextMat', 'GhostMesh', 'object', '/Game/SoulCharger/Core/UI/Materials/M_TextUnlit.M_TextUnlit', cls=MAT),
        # grip -> malla del mando: las de SM_RHand/SM_LHand del dibujo (validadas en visor, BP_TBStroke.md 603-604)
        v('GripToMeshR', 'GhostMesh', 'transform', {'location': {'x': 5.685942, 'y': 0.540018, 'z': -1.677589},
                                                   'rotation': {'pitch': -13.566261, 'yaw': -83.539335, 'roll': 64.230738},
                                                   'scale': {'x': 1.0875, 'y': 1.0875, 'z': 1.0875}}),
        v('GripToMeshL', 'GhostMesh', 'transform', {'location': {'x': 5.876514, 'y': -1.566667, 'z': -2.049637},
                                                   'rotation': {'pitch': 0.0, 'yaw': -95.0, 'roll': 65.0},
                                                   'scale': {'x': 1.0875, 'y': 1.0875, 'z': 1.0875}}),
        v('HingePivotR', 'GhostMesh', 'vector', [1.565, 2.432, -0.145]),
        v('HingeAxisR', 'GhostMesh', 'vector', [0.976, -0.2177, -0.0083]),
        v('PressDegrees', 'GhostMesh', 'float', 14.0), v('PressSign', 'GhostMesh', 'float', -1.0),
        v('Found', 'Z-Ghost', 'bool'), v('WantCol', 'Z-Ghost', 'linearcolor'), v('MirrorOn', 'Z-Ghost', 'bool'),
        v('Data', 'Z-Ghost', 'float', cont='array'), v('Frames', 'Z-Ghost', 'int'), v('Hz', 'Z-Ghost', 'float'),
        v('Stride', 'Z-Ghost', 'int'), v('UseR', 'Z-Ghost', 'bool'), v('UseL', 'Z-Ghost', 'bool'),
        v('BeamR', 'Z-Ghost', 'bool'), v('BeamL', 'Z-Ghost', 'bool'), v('LineText', 'Z-Ghost', 'string'),
        v('ActR', 'Z-Ghost', 'bool'), v('ActL', 'Z-Ghost', 'bool'), v('BeamActR', 'Z-Ghost', 'bool'),
        v('BeamActL', 'Z-Ghost', 'bool'), v('Anchor', 'Z-Ghost', 'transform'), v('State', 'Z-Ghost', 'int'),
        v('T', 'Z-Ghost', 'float'), v('GapT', 'Z-Ghost', 'float'), v('Fade', 'Z-Ghost', 'float'),
        v('LoopK', 'Z-Ghost', 'float'), v('StepIdx', 'Z-Ghost', 'int'), v('LoopCount', 'Z-Ghost', 'int'),
        v('bPlaying', 'Z-Ghost', 'bool'), v('Ensured', 'Z-Ghost', 'bool'), v('NewComp', 'Z-Ghost', 'object', cls=SMC),
        v('Curs', 'Z-Ghost', 'object', cls=SMC, cont='array'), v('Trigs', 'Z-Ghost', 'object', cls=SMC, cont='array'),
        v('Beams', 'Z-Ghost', 'object', cls=SMC, cont='array'), v('Echoes', 'Z-Ghost', 'object', cls=SMC, cont='array'),
        v('Ages', 'Z-Ghost', 'int', cont='array'), v('CurXf', 'Z-Ghost', 'transform', cont='array'),
        v('HasPrev', 'Z-Ghost', 'bool', cont='array'), v('PoseXf', 'Z-Ghost', 'transform'),
        v('PoseAim', 'Z-Ghost', 'rotator'), v('PoseTrig', 'Z-Ghost', 'float'), v('OldI', 'Z-Ghost', 'int'),
        v('OldAge', 'Z-Ghost', 'int'), v('TextC', 'Z-Ghost', 'object', cls=TRC)],
    'functions': {
        'Play': [p('DemoId', 'name'), p('Col', 'linearcolor'), p('Mirror', 'bool')], 'Stop': [], 'Reanchor': [],
        'PreviewData': [p('D', 'float', cont='array'), p('N', 'int'), p('UR', 'bool'), p('UL', 'bool'),
                        p('BR', 'bool'), p('BL', 'bool'), p('Txt', 'string'), p('Col', 'linearcolor')],
        'GhFindLoop': [p('DemoId', 'name')], 'GhFindOne': [p('Tk', 'object', TAKE_C), p('DemoId', 'name')],
        'GhLoad': [p('Tk', 'object', TAKE_C)], 'GhStart': [], 'GhActive': [], 'GhSound': [p('Snd', 'object', SND)],
        'GhAnchor': [], 'GhEnsure': [], 'GhMakeHand': [p('H', 'int')], 'GhMakeMesh': [p('M', 'object', SM)],
        'GhMakeText': [], 'GhTick': [p('Dt', 'float')], 'GhFadeStep': [p('Dt', 'float')], 'GhRun': [p('Dt', 'float')],
        'GhAdvance': [p('Dt', 'float'), p('Dur', 'float')], 'GhStepCheck': [p('Dur', 'float')],
        'GhLoopCheck': [p('Dur', 'float')], 'GhGap': [p('Dt', 'float')], 'GhEnd': [], 'GhJump': [p('S', 'int')],
        'GhJumpHand': [p('H', 'int'), p('F', 'int')], 'GhPlace': [p('H', 'int')], 'GhPose': [p('F', 'int'), p('H', 'int')],
        'GhTrigSet': [p('H', 'int'), p('V', 'float'), p('Mx', 'transform')], 'GhBeamSet': [p('H', 'int')],
        'GhEchoAge': [], 'GhEchoReset': [], 'GhEchoPush': [p('H', 'int')], 'GhEchoFind': [p('H', 'int')],
        'GhEchoOld': [p('I', 'int')], 'GhAlpha': [], 'GhAlphaHand': [p('H', 'int'), p('K', 'float')],
        'GhEchoAlpha': [p('I', 'int'), p('K', 'float')], 'GhSetOp': [p('C', 'object', SMC), p('V', 'float')],
        'GhColor': [], 'GhColorArr': [p('A', 'object', SMC, 'array')], 'GhText': [], 'GhTextAlpha': [p('K', 'float')], 'GhAutoPlay': []}}

spec['BP_GhostRecorder_SC'] = {
    'path': G + '/BP_GhostRecorder_SC', 'parent': '/Script/Engine.Actor',
    'vars': [
        v('Takes', 'Rec', 'object', DAS, True, cls=TAKE_C, cont='array'),
        v('DemoTimes', 'Rec', 'float', [6.0, 5.0, 6.0, 8.0, 6.0, 8.0, 8.0, 5.0, 10.0, 6.0], True, cont='array'),
        v('MarkerPos', 'Rec', 'vector', [[48, 0, -28], [40, 12, -30], [160, 0, -15], [18, 0, -58], [14, -8, -32],
                                         [200, 0, 0], [130, 35, 5], [0, 0, 0], [50, 0, -48], [190, 0, -8]], True, cont='array'),
        v('MarkerSize', 'Rec', 'float', [10.0, 6.0, 18.0, 8.0, 7.0, 35.0, 10.0, 0.0, 20.0, 30.0], True, cont='array'),
        v('bShowMarkers', 'Rec', 'bool', True, True), v('Player', 'Rec', 'object', None, True, cls=PLAYER_C),
        v('RecHz', 'Rec', 'float', 30.0, True), v('DwellTime', 'Rec', 'float', 1.2, True),
        v('GazeDeg', 'Rec', 'float', 4.5, True), v('UiDist', 'Rec', 'float', 110.0, True),
        v('UiUp', 'Rec', 'float', 22.0, True), v('UiColor', 'Rec', 'linearcolor', [0.7, 0.85, 1.0, 1.0], True),
        v('PreviewColor', 'Rec', 'linearcolor', [0.75, 0.85, 1.0, 1.0], True),
        v('TickSound', 'Rec', 'object', '/Game/NeuralCanvas/Sound/VR_click1.VR_click1', True, cls=SND),
        v('GoSound', 'Rec', 'object', '/Game/NeuralCanvas/Sound/VR_shep_scale_up_02.VR_shep_scale_up_02', True, cls=SND),
        v('EndSound', 'Rec', 'object', '/Game/NeuralCanvas/Sound/VR_shep_scale_down_02.VR_shep_scale_down_02', True, cls=SND),
        v('OkSound', 'Rec', 'object', '/Game/NeuralCanvas/Sound/VR_click2.VR_click2', True, cls=SND),
        v('SfxVol', 'Rec', 'float', 0.8, True), v('DebugPress', 'Rec', 'int', -1, True),
        v('ButtonMesh', 'Rec', 'object', '/Engine/BasicShapes/Sphere.Sphere', cls=SM),
        v('MarkerMesh', 'Rec', 'object', '/Engine/BasicShapes/Sphere.Sphere', cls=SM),
        v('UiMat', 'Rec', 'object', G + '/M_Ghost_SC.M_Ghost_SC', cls=MAT),
        v('TextMat', 'Rec', 'object', '/Game/SoulCharger/Core/UI/Materials/M_TextUnlit.M_TextUnlit', cls=MAT),
        v('Idx', 'Z-Rec', 'int'), v('State', 'Z-Rec', 'int'), v('T', 'Z-Rec', 'float'), v('NextS', 'Z-Rec', 'float'),
        v('Take', 'Z-Rec', 'float', cont='array'), v('N', 'Z-Rec', 'int'), v('Anchor', 'Z-Rec', 'transform'),
        v('Dwell', 'Z-Rec', 'float', cont='array'), v('Btns', 'Z-Rec', 'object', cls=SMC, cont='array'),
        v('BtnTxt', 'Z-Rec', 'object', cls=TRC, cont='array'), v('BtnOn', 'Z-Rec', 'bool', cont='array'),
        v('TitleC', 'Z-Rec', 'object', cls=TRC), v('InfoC', 'Z-Rec', 'object', cls=TRC),
        v('BigC', 'Z-Rec', 'object', cls=TRC), v('Marker', 'Z-Rec', 'object', cls=SMC),
        v('Accepted', 'Z-Rec', 'bool', [False] * 10, cont='array'), v('LastCount', 'Z-Rec', 'int'),
        v('NewComp', 'Z-Rec', 'object', cls=SMC), v('NewText', 'Z-Rec', 'object', cls=TRC), v('Booted', 'Z-Rec', 'bool')],
    'functions': {
        'RcBoot': [], 'RcEnsure': [], 'RcMakeButton': [], 'RcMakeMesh': [p('M', 'object', SM)],
        'RcMakeText': [p('Size', 'float')], 'RcFrame': [], 'RcLayout': [],
        'RcPlaceText': [p('Tc', 'object', TRC), p('P', 'vector')], 'RcPlaceBtn': [p('I', 'int'), p('P', 'vector')],
        'RcTick': [p('Dt', 'float')], 'RcGaze': [p('Dt', 'float')], 'RcGazeOne': [p('I', 'int'), p('Dt', 'float')],
        'RcDwellReset': [], 'RcPress': [p('I', 'int')], 'RcCountStart': [], 'RcCountdown': [p('Dt', 'float')],
        'RcRecStart': [], 'RcRecording': [p('Dt', 'float')], 'RcSampleLoop': [], 'RcRecEndCheck': [], 'RcRecEnd': [],
        'RcCapture': [], 'RcPushPose': [p('P', 'vector'), p('R', 'rotator')], 'RcPushRot': [p('R', 'rotator')],
        'RcPushF': [p('V', 'float')], 'RcPreview': [], 'RcPlayerStop': [], 'RcAccept': [], 'RcShow': [],
        'RcBtn': [p('I', 'int'), p('On', 'bool'), p('Label', 'string')], 'RcMarker': [],
        'RcSound': [p('Snd', 'object', SND)], 'RcDebug': []}}

io.open(os.path.join(AQUI, 'ghost_spec.json'), 'w', encoding='utf-8').write(json.dumps(spec, indent=1, ensure_ascii=False))
print('ghost_spec.json:', {k: (len(v['vars']), len(v['functions'])) for k, v in spec.items() if k != 'DA'}, '+', len(IDS), 'DA')
