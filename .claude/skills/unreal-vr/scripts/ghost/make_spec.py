# -*- coding: utf-8 -*-
"""make_spec.py (v2, 2026-10-01) - genera ghost_spec.json: variables (tipo, categoria, default, instance-editable),
componentes del reproductor, parametros de cada funcion de BP_GhostTake_SC, BP_GhostPlayer_SC y BP_GhostRecorder_SC,
y los valores de los 10 DA. Lo leen lint_dsl.py (chequeo cruzado) y ghost_build.py (armado en el turno).
Plan: docs/PLAN-FANTASMAS-V2-2026-10-01.md. Datos de referencia (posiciones, mallas, montajes): scripts/ghost/v2_datos.md."""
import io
import json
import os

AQUI = os.path.dirname(os.path.abspath(__file__))
G = '/Game/SoulCharger/Mechanics/Ghost'
TAKE_C = G + '/BP_GhostTake_SC.BP_GhostTake_SC_C'
PLAYER_C = G + '/BP_GhostPlayer_SC.BP_GhostPlayer_SC_C'
IDS = ['GHOST_BELL', 'GHOST_TAKE', 'GHOST_PICK', 'GHOST_BREATH', 'GHOST_HEART', 'GHOST_LOVING', 'GHOST_ATTRACT',
       'GHOST_SAVE', 'GHOST_DRAW', 'GHOST_SHARE']
# las 7 que se graban (orden del estudio); Loving, Save y Share quedan sin uso (no se borran sin pedido de Beltran)
USADAS = ['GHOST_BELL', 'GHOST_TAKE', 'GHOST_PICK', 'GHOST_BREATH', 'GHOST_HEART', 'GHOST_ATTRACT', 'GHOST_DRAW']


def da_name(i):
    return 'DA_Ghost_' + i.split('_', 1)[1].capitalize()


SMC = '/Script/Engine.StaticMeshComponent'
ISM = '/Script/Engine.InstancedStaticMeshComponent'
SKC = '/Script/Engine.SkeletalMeshComponent'
TRC = '/Script/Engine.TextRenderComponent'
MC = '/Script/Engine.MeshComponent'
SC = '/Script/Engine.SceneComponent'
SM = '/Script/Engine.StaticMesh'
MAT = '/Script/Engine.MaterialInterface'
SND = '/Script/Engine.SoundBase'
ACT = '/Script/Engine.Actor'
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


def xf(loc, rot=(0.0, 0.0, 0.0), sc=(1.0, 1.0, 1.0)):
    """rot = (pitch, yaw, roll)."""
    return {'location': {'x': loc[0], 'y': loc[1], 'z': loc[2]},
            'rotation': {'pitch': rot[0], 'yaw': rot[1], 'roll': rot[2]},
            'scale': {'x': sc[0], 'y': sc[1], 'z': sc[2]}}


spec = {'version': 2}

# ---------------------------------------------------------------- la toma (Data Asset)
spec['BP_GhostTake_SC'] = {
    'path': G + '/BP_GhostTake_SC', 'parent': '/Script/Engine.PrimaryDataAsset',
    'remove': ['bUseRight', 'bUseLeft'],
    'vars': [
        v('Id', 'Ghost', 'name', 'None', True), v('Text', 'Ghost', 'string', '', True),
        v('Hz', 'Ghost', 'float', 30.0, True), v('Frames', 'Ghost', 'int', 0, True),
        v('Stride', 'Ghost', 'int', 34, True), v('Data', 'Ghost', 'float', [], True, cont='array'),
        v('HoldR', 'Ghost', 'int', 2, True), v('HoldL', 'Ghost', 'int', 0, True),
        v('bBeamRight', 'Ghost', 'bool', False, True), v('bBeamLeft', 'Ghost', 'bool', False, True),
        v('bHeadAnchor', 'Ghost', 'bool', False, True), v('Extra', 'Ghost', 'int', 0, True),
        v('DemoTime', 'Ghost', 'float', 6.0, True), v('Note', 'Ghost', 'string', '', True)],
    'functions': {}}

# id: (texto en ingles, HoldR, HoldL, haz der, cabeza, extra, segundos)
TAKES = {
    'GHOST_BELL': ('Rest your hand and hold', 1, 0, False, False, 0, 5.0),
    'GHOST_TAKE': ('Take it with your favorite hand', 1, 0, False, False, 0, 5.0),
    'GHOST_PICK': ('Reach a soul and pull the trigger', 2, 0, False, False, 0, 6.0),
    'GHOST_BREATH': ('Rest the sensor on your belly and breathe', 3, 0, False, True, 0, 16.0),
    'GHOST_HEART': ('Hold the sensor on your heart', 3, 0, False, True, 0, 12.0),
    'GHOST_LOVING': ('Move your hands slowly through the light', 0, 0, False, True, 0, 8.0),
    'GHOST_ATTRACT': ('Point · pull the trigger · place it', 2, 4, True, False, 1, 12.0),
    'GHOST_SAVE': ('Hold SAVE', 0, 0, False, False, 0, 5.0),
    'GHOST_DRAW': ('Pick a color · draw with the trigger', 2, 5, False, False, 2, 10.0),
    'GHOST_SHARE': ('Point at your choice and pull the trigger', 0, 0, False, False, 0, 6.0),
}
spec['DA'] = {'folder': G + '/Takes', 'items': [
    {'id': i, 'asset': da_name(i), 'text': TAKES[i][0], 'HoldR': TAKES[i][1], 'HoldL': TAKES[i][2],
     'BR': TAKES[i][3], 'BL': False, 'Head': TAKES[i][4], 'Extra': TAKES[i][5], 'DemoTime': TAKES[i][6],
     'used': i in USADAS} for i in IDS]}

# ---------------------------------------------------------------- el reproductor
# Montajes medidos (v2_datos.md): mando = SM_RHand/SM_LHand de BP_TBDirector_NC (validados en visor); sensor =
# SensorXfR de BP_UserTool_SC (Roll +90); SAVE = BtnOffset de BP_SeqRig_SC (mano IZQUIERDA); paleta = ArtAnchor por
# defecto de BP_TBPalette con la escala viva 0,464 (APROXIMADO: la pose viva sale de perillas del director que no estan
# escritas; el turno intenta leerla). Mano = HandRight/HandLeft del pawn (el turno la COPIA del CDO del pawn).
spec['BP_GhostPlayer_SC'] = {
    'path': G + '/BP_GhostPlayer_SC', 'parent': ACT,
    # variables de v1 que v2 no usa. OJO: BeamR/BeamL eran bool en v1 y en v2 son COMPONENTES: se quitan ANTES de
    # crear los componentes (si no, choca el nombre).
    'remove': ['ActL', 'ActR', 'Ages', 'AutoPlayId', 'BeamActL', 'BeamActR', 'BeamL', 'BeamR', 'Beams', 'Curs',
               'Echoes', 'Ensured', 'HasPrev', 'NewComp', 'OldAge', 'OldI', 'Takes', 'TestColor', 'TextC', 'Trigs',
               'UseL', 'UseR', 'WantCol'],
    'components': [
        {'name': 'BodyR', 'class': ISM, 'props': {'NumCustomDataFloats': 1}},
        {'name': 'BodyL', 'class': ISM, 'props': {'NumCustomDataFloats': 1}},
        {'name': 'TrigR', 'class': SMC}, {'name': 'TrigL', 'class': SMC},
        {'name': 'HandR', 'class': SKC, 'copy_from_pawn': 'HandRight'},
        {'name': 'HandL', 'class': SKC, 'copy_from_pawn': 'HandLeft'},
        {'name': 'PropR', 'class': SMC}, {'name': 'PropL', 'class': SMC},
        {'name': 'BeamR', 'class': SMC}, {'name': 'BeamL', 'class': SMC},
        {'name': 'Orb', 'class': SMC},
        {'name': 'Stroke', 'class': ISM}, {'name': 'Path', 'class': ISM},
        {'name': 'Label', 'class': TRC}],
    'vars': [
        # --- perillas de la instancia (cada fantasma colocado es una instruccion)
        v('Take', 'Ghost', 'object', None, True, cls=TAKE_C),
        v('FollowTag', 'Ghost', 'name', 'None', True),
        v('bPreview', 'Ghost', 'bool', True, True), v('PreviewTime', 'Ghost', 'float', 0.5, True),
        v('PreviewPoses', 'Ghost', 'int', 10, True), v('PreviewOnion', 'Ghost', 'float', 0.2, True),
        v('PathDot', 'Ghost', 'float', 0.012, True),
        v('bShowText', 'Ghost', 'bool', True, True),
        v('TextOffset', 'Ghost', 'vector', [60.0, 0.0, -40.0], True), v('TextSize', 'Ghost', 'float', 2.4, True),
        v('TextColor', 'Ghost', 'linearcolor', [0.9, 0.9, 0.88, 1.0], True),
        v('GhostColor', 'Ghost', 'linearcolor', [0.78, 0.88, 1.0, 1.0], True),
        v('GhostOpacity', 'Ghost', 'float', 0.85, True),
        v('TriggerColor', 'Ghost', 'linearcolor', [1.0, 0.62, 0.25, 1.0], True),
        v('TriggerGlow', 'Ghost', 'float', 3.0, True),
        v('StepHz', 'Ghost', 'float', 11.0, True),
        v('EchoAlpha', 'Ghost', 'float', [1.0, 0.55, 0.3, 0.15, 0.06], True, cont='array'),
        v('FadeIn', 'Ghost', 'float', 0.4, True), v('FadeOut', 'Ghost', 'float', 0.6, True),
        v('LoopGap', 'Ghost', 'float', 1.0, True), v('LoopFade', 'Ghost', 'float', 0.3, True),
        v('AppearSound', 'Ghost', 'object', None, True, cls=SND),   # Narrativa asigna FX_GHOSTAPPEAR (gotcha 563)
        v('VanishSound', 'Ghost', 'object', None, True, cls=SND),   # Narrativa asigna FX_GHOSTOUT
        v('SfxVol', 'Ghost', 'float', 0.8, True),
        v('BeamLength', 'Ghost', 'float', 140.0, True), v('BeamRadius', 'Ghost', 'float', 0.22, True),
        v('OrbRest', 'Ghost', 'vector', [600.0, 150.0, 120.0], True), v('OrbSize', 'Ghost', 'float', 18.0, True),
        v('OrbHoldDist', 'Ghost', 'float', 80.0, True), v('OrbSpeed', 'Ghost', 'float', 1.5, True),
        v('OrbGrab', 'Ghost', 'float', 30.0, True),
        v('StrokeWidth', 'Ghost', 'float', 0.8, True),
        v('bAutoPlay', 'Ghost', 'bool', False, True), v('AutoPlayDelay', 'Ghost', 'float', 2.0, True),
        v('LiveOpacity', 'Ghost', 'float', 0.45, True),
        # --- mallas y montajes (en el Blueprint)
        v('BodyMeshR', 'GhostMesh', 'object', QC + 'SM_QuestCtrl_Body_R_SC.SM_QuestCtrl_Body_R_SC', cls=SM),
        v('BodyMeshL', 'GhostMesh', 'object', QC + 'SM_QuestCtrl_Body_L_SC.SM_QuestCtrl_Body_L_SC', cls=SM),
        v('TrigMeshR', 'GhostMesh', 'object', QC + 'SM_QuestCtrl_Trigger_R_SC.SM_QuestCtrl_Trigger_R_SC', cls=SM),
        v('TrigMeshL', 'GhostMesh', 'object', QC + 'SM_QuestCtrl_Trigger_L_SC.SM_QuestCtrl_Trigger_L_SC', cls=SM),
        # sensor / SAVE / paleta: el turno las reemplaza por las fundidas (ghost_merge.py) si el fundido sale bien
        v('SensorMesh', 'GhostMesh', 'object', '/Game/SoulCharger/Mechanics/BioSensor/SM_BioSensor_SC.SM_BioSensor_SC', cls=SM),
        v('SaveMesh', 'GhostMesh', 'object', '/Game/SoulCharger/Mechanics/SaveMelody/SM_SaveMelody_Plate_SC.SM_SaveMelody_Plate_SC', cls=SM),
        v('PaletteMesh', 'GhostMesh', 'object', '/Game/SoulCharger/Mechanics/DrawPalette/SM_DrawPalette_Base_SC.SM_DrawPalette_Base_SC', cls=SM),
        v('BeamMesh', 'GhostMesh', 'object', '/Engine/BasicShapes/Cylinder.Cylinder', cls=SM),
        v('OrbMesh', 'GhostMesh', 'object', '/Engine/BasicShapes/Sphere.Sphere', cls=SM),
        v('StrokeMesh', 'GhostMesh', 'object', '/Engine/BasicShapes/Cylinder.Cylinder', cls=SM),
        v('PathMesh', 'GhostMesh', 'object', '/Engine/BasicShapes/Sphere.Sphere', cls=SM),
        v('GhostMat', 'GhostMesh', 'object', G + '/M_Ghost_SC.M_Ghost_SC', cls=MAT),
        v('TextMat', 'GhostMesh', 'object', '/Game/SoulCharger/Core/UI/Materials/M_TextUnlit.M_TextUnlit', cls=MAT),
        v('GripToMeshR', 'GhostMesh', 'transform', xf((5.685942, 0.540018, -1.677589), (-13.566261, -83.539335, 64.230738), (1.0875,) * 3)),
        v('GripToMeshL', 'GhostMesh', 'transform', xf((5.876514, -1.566667, -2.049637), (0.0, -95.0, 65.0), (1.0875,) * 3)),
        v('HandXfR', 'GhostMesh', 'transform', xf((-2.98126, 3.5, 4.561753))),    # el turno copia la rotacion real del pawn
        v('HandXfL', 'GhostMesh', 'transform', xf((-2.98126, -3.5, 4.561753))),
        v('SensorXf', 'GhostMesh', 'transform', xf((4.325, -1.685, -2.335), (0.0, 0.0, 90.0))),
        v('SaveXf', 'GhostMesh', 'transform', xf((5.57, 0.8, -2.08), (0.0, -90.0, 55.0), (0.4,) * 3)),
        v('PaletteXf', 'GhostMesh', 'transform', xf((2.19, 2.76, 7.51), (0.0, 146.12, -37.31), (0.464,) * 3)),
        v('TipOffset', 'GhostMesh', 'vector', [2.5, 0.0, 0.0]),
        v('HingePivotR', 'GhostMesh', 'vector', [1.565, 2.432, -0.145]),
        v('HingeAxisR', 'GhostMesh', 'vector', [0.976, -0.2177, -0.0083]),
        v('PressDegrees', 'GhostMesh', 'float', 14.0), v('PressSign', 'GhostMesh', 'float', -1.0),
        # --- estado interno
        v('Found', 'Z-Ghost', 'bool'), v('Baked', 'Z-Ghost', 'bool'), v('MirrorOn', 'Z-Ghost', 'bool'),
        v('Data', 'Z-Ghost', 'float', cont='array'), v('Frames', 'Z-Ghost', 'int'), v('Hz', 'Z-Ghost', 'float'),
        v('Stride', 'Z-Ghost', 'int'), v('LineText', 'Z-Ghost', 'string'), v('Extra', 'Z-Ghost', 'int'),
        v('HeadAnchor', 'Z-Ghost', 'bool'),
        v('Kind', 'Z-Ghost', 'int', cont='array'), v('BeamOn', 'Z-Ghost', 'bool', cont='array'),
        v('BodyRel', 'Z-Ghost', 'transform', cont='array'), v('PropRel', 'Z-Ghost', 'transform', cont='array'),
        v('CurXf', 'Z-Ghost', 'transform', cont='array'), v('Placed', 'Z-Ghost', 'bool', cont='array'),
        v('HistN', 'Z-Ghost', 'int', cont='array'), v('Hist', 'Z-Ghost', 'transform', cont='array'),
        v('Singles', 'Z-Ghost', 'object', cls=SC, cont='array'), v('TmpXf', 'Z-Ghost', 'transform', cont='array'),
        v('InstN', 'Z-Ghost', 'int'), v('InstPreview', 'Z-Ghost', 'bool'),
        v('SensorRel', 'Z-Ghost', 'transform'), v('MirXf', 'Z-Ghost', 'transform'),
        v('Anchor', 'Z-Ghost', 'transform'), v('State', 'Z-Ghost', 'int'), v('T', 'Z-Ghost', 'float'),
        v('GapT', 'Z-Ghost', 'float'), v('Fade', 'Z-Ghost', 'float'), v('LoopK', 'Z-Ghost', 'float'),
        v('AlphaK', 'Z-Ghost', 'float'), v('StepIdx', 'Z-Ghost', 'int'), v('LoopCount', 'Z-Ghost', 'int'),
        v('CurF', 'Z-Ghost', 'int'), v('bPlaying', 'Z-Ghost', 'bool'), v('bLive', 'Z-Ghost', 'bool'),
        v('PoseXf', 'Z-Ghost', 'transform'), v('PoseAim', 'Z-Ghost', 'rotator'), v('PoseAimLoc', 'Z-Ghost', 'vector'),
        v('PoseTrig', 'Z-Ghost', 'float'),
        v('OrbPath', 'Z-Ghost', 'vector', cont='array'), v('StrokeXf', 'Z-Ghost', 'transform', cont='array'),
        v('StrokeF', 'Z-Ghost', 'int', cont='array'), v('StrokeShown', 'Z-Ghost', 'int'),
        v('PathXf', 'Z-Ghost', 'transform', cont='array'),
        v('BkGrip', 'Z-Ghost', 'transform'), v('BkAim', 'Z-Ghost', 'rotator'), v('BkAimLoc', 'Z-Ghost', 'vector'),
        v('BkTrig', 'Z-Ghost', 'float'), v('BkHeld', 'Z-Ghost', 'bool'), v('BkPrevT', 'Z-Ghost', 'float'),
        v('BkPos', 'Z-Ghost', 'vector'), v('BkTip', 'Z-Ghost', 'vector'), v('BkPrevTip', 'Z-Ghost', 'vector'),
        v('BkHasPrev', 'Z-Ghost', 'bool'),
        v('FollowActor', 'Z-Ghost', 'object', cls=ACT), v('FollowOff', 'Z-Ghost', 'vector'),
        v('LiveGR', 'Z-Ghost', 'transform'), v('LiveGL', 'Z-Ghost', 'transform'),
        v('LiveAR', 'Z-Ghost', 'transform'), v('LiveAL', 'Z-Ghost', 'transform'),
        v('LiveTR', 'Z-Ghost', 'float'), v('LiveTL', 'Z-Ghost', 'float')],
    'functions': {
        'Play': [p('Mirror', 'bool')], 'Stop': [], 'Reanchor': [],
        'PreviewData': [p('D', 'float', cont='array'), p('N', 'int')],
        'GhPreviewGo': [p('D', 'float', cont='array'), p('N', 'int')],
        'LiveStart': [], 'GhLiveGo': [],
        'LiveSet': [p('Gr', 'transform'), p('Gl', 'transform'), p('Ar', 'transform'), p('Al', 'transform'),
                    p('Tr', 'float'), p('Tl', 'float')],
        'GhLiveHands': [], 'GhLivePlace': [p('H', 'int')], 'LiveStop': [], 'GhLiveAlpha': [],
        'GhLiveHandAlpha': [p('H', 'int')],
        'GhLoad': [], 'GhLoadTk': [], 'GhLoadMeta': [], 'GhLoadIfNeeded': [], 'GhBakeIf': [], 'GhPlayNow': [],
        'GhReset': [], 'GhCollect': [], 'GhSetup': [], 'GhArrInit': [], 'GhArrAdd': [p('I', 'int')], 'GhFixed': [],
        'GhSetupHand': [p('H', 'int')], 'GhRels': [p('H', 'int')], 'GhMirXf': [p('Xf', 'transform')],
        'GhPrep': [p('C', 'object', MC), p('Col', 'linearcolor')], 'GhMats': [p('C', 'object', MC)],
        'GhInstInit': [p('Ism', 'object', ISM), p('N', 'int')], 'GhInstFill': [p('N', 'int')],
        'GhInstData': [p('Ism', 'object', ISM), p('N', 'int')],
        'GhAnchor': [p('Game', 'bool')], 'GhAnchorHead': [], 'GhLayer': [],
        'GhFollowInit': [], 'GhFollowFind': [], 'GhFollowApply': [],
        'GhBake': [], 'GhBakeOne': [p('F', 'int')], 'GhBakePath': [p('F', 'int')], 'GhBakeOrb': [],
        'GhBakeStroke': [p('F', 'int')], 'GhSegMaybe': [p('F', 'int')], 'GhSeg': [p('F', 'int')],
        'GhStart': [], 'GhRestart': [], 'GhSound': [p('Snd', 'object', SND)],
        'GhTick': [p('Dt', 'float')], 'GhFadeStep': [p('Dt', 'float')], 'GhRun': [p('Dt', 'float')],
        'GhAdvance': [p('Dt', 'float'), p('Dur', 'float')], 'GhStepCheck': [p('Dur', 'float')],
        'GhLoopCheck': [p('Dur', 'float')], 'GhGap': [p('Dt', 'float')], 'GhEnd': [],
        'GhJump': [p('S', 'int')], 'GhJumpHand': [p('H', 'int')], 'GhPush': [p('H', 'int')],
        'GhPose': [p('F', 'int'), p('H', 'int')], 'GhPlace': [p('H', 'int')],
        'GhPlaceBody': [p('H', 'int'), p('Mx', 'transform')], 'GhPlaceIsm': [p('H', 'int'), p('Mx', 'transform')],
        'GhEchoes': [p('H', 'int')], 'GhEchoInst': [p('H', 'int'), p('K', 'int')],
        'GhPlaceTrig': [p('H', 'int'), p('Mx', 'transform')],
        'GhTrigSet': [p('H', 'int'), p('V', 'float'), p('Mx', 'transform')],
        'GhPlaceProp': [p('H', 'int')], 'GhPlaceBeam': [p('H', 'int')], 'GhBeamSet': [p('H', 'int')],
        'GhOrbAt': [], 'GhOrbPut': [], 'GhStrokeTo': [], 'GhStrokeGrow': [],
        'GhAlpha': [], 'GhAlphaHand': [p('H', 'int')], 'GhOp': [p('C', 'object', MC), p('V', 'float')],
        'GhText': [], 'GhTextAlpha': [p('K', 'float')], 'GhAutoPlay': [],
        'GhPreview': [], 'GhPvHands': [], 'GhPvHand': [p('H', 'int')], 'GhOnion': [p('H', 'int')],
        'GhOnionAll': [p('H', 'int')], 'GhOnionOne': [p('H', 'int'), p('K', 'int')], 'GhNoTake': []}}

# ---------------------------------------------------------------- el grabador
spec['BP_GhostRecorder_SC'] = {
    'path': G + '/BP_GhostRecorder_SC', 'parent': ACT,
    'remove': ['Takes', 'DemoTimes', 'MarkerPos', 'MarkerSize', 'bShowMarkers', 'Player', 'PreviewColor', 'MarkerMesh',
               'Marker'],
    'vars': [
        v('Ghosts', 'Rec', 'object', None, True, cls=PLAYER_C, cont='array'),
        v('CountTime', 'Rec', 'float', 3.0, True), v('RecHz', 'Rec', 'float', 30.0, True),
        v('DwellTime', 'Rec', 'float', 1.2, True), v('GazeDeg', 'Rec', 'float', 4.5, True),
        v('UiDist', 'Rec', 'float', 110.0, True), v('UiUp', 'Rec', 'float', 22.0, True),
        v('UiColor', 'Rec', 'linearcolor', [0.7, 0.85, 1.0, 1.0], True),
        v('BigSize', 'Rec', 'float', 9.0, True),
        v('CountOffHead', 'Rec', 'vector', [50.0, 0.0, -12.0], True),
        v('CountOffLevel', 'Rec', 'vector', [0.0, 0.0, 22.0], True),
        v('TickSound', 'Rec', 'object', '/Game/NeuralCanvas/Sound/VR_click1.VR_click1', True, cls=SND),
        v('GoSound', 'Rec', 'object', '/Game/NeuralCanvas/Sound/VR_shep_scale_up_02.VR_shep_scale_up_02', True, cls=SND),
        v('EndSound', 'Rec', 'object', '/Game/NeuralCanvas/Sound/VR_shep_scale_down_02.VR_shep_scale_down_02', True, cls=SND),
        v('OkSound', 'Rec', 'object', '/Game/NeuralCanvas/Sound/VR_click2.VR_click2', True, cls=SND),
        v('SfxVol', 'Rec', 'float', 0.8, True), v('DebugPress', 'Rec', 'int', -1, True),
        v('ButtonMesh', 'Rec', 'object', '/Engine/BasicShapes/Sphere.Sphere', cls=SM),
        v('UiMat', 'Rec', 'object', G + '/M_Ghost_SC.M_Ghost_SC', cls=MAT),
        v('TextMat', 'Rec', 'object', '/Game/SoulCharger/Core/UI/Materials/M_TextUnlit.M_TextUnlit', cls=MAT),
        v('Idx', 'Z-Rec', 'int'), v('State', 'Z-Rec', 'int'), v('T', 'Z-Rec', 'float'), v('NextS', 'Z-Rec', 'float'),
        v('Take', 'Z-Rec', 'float', cont='array'), v('N', 'Z-Rec', 'int'), v('Anchor', 'Z-Rec', 'transform'),
        v('HeadXf', 'Z-Rec', 'transform'), v('UiFrame', 'Z-Rec', 'transform'), v('HeadTake', 'Z-Rec', 'bool'),
        v('DemoTime', 'Z-Rec', 'float'),
        v('Dwell', 'Z-Rec', 'float', cont='array'), v('Btns', 'Z-Rec', 'object', cls=SMC, cont='array'),
        v('BtnTxt', 'Z-Rec', 'object', cls=TRC, cont='array'), v('BtnOn', 'Z-Rec', 'bool', cont='array'),
        v('TitleC', 'Z-Rec', 'object', cls=TRC), v('InfoC', 'Z-Rec', 'object', cls=TRC),
        v('BigC', 'Z-Rec', 'object', cls=TRC), v('Accepted', 'Z-Rec', 'bool', cont='array'),
        v('LastCount', 'Z-Rec', 'int'), v('NewComp', 'Z-Rec', 'object', cls=SMC),
        v('NewText', 'Z-Rec', 'object', cls=TRC), v('Booted', 'Z-Rec', 'bool'),
        v('GR', 'Z-Rec', 'transform'), v('GL', 'Z-Rec', 'transform'), v('AR', 'Z-Rec', 'transform'),
        v('AL', 'Z-Rec', 'transform'), v('TR', 'Z-Rec', 'float'), v('TL', 'Z-Rec', 'float'),
        v('PR', 'Z-Rec', 'float'), v('PL', 'Z-Rec', 'float')],
    'functions': {
        'RcBoot': [], 'RcEnsure': [], 'RcMakeButtons': [], 'RcMakeButton': [], 'RcLabels': [], 'RcAcceptInit': [],
        'RcMakeMesh': [p('M', 'object', SM)], 'RcMakeText': [], 'RcFrame': [], 'RcLayout': [], 'RcPlaceBtns': [],
        'RcPlaceBtn': [p('I', 'int')], 'RcPlaceText': [p('Tc', 'object', TRC), p('P', 'vector')],
        'RcPlaceBig': [], 'RcBigAtStation': [], 'RcTick': [p('Dt', 'float')], 'RcRead': [], 'RcLive': [],
        'RcGaze': [p('Dt', 'float')], 'RcGazeOne': [p('I', 'int'), p('Dt', 'float')], 'RcDwellReset': [],
        'RcPress': [p('I', 'int')], 'RcCountStart': [], 'RcAnchor': [], 'RcCountdown': [p('Dt', 'float')],
        'RcRecStart': [], 'RcRecording': [p('Dt', 'float')], 'RcRecLeft': [], 'RcSampleLoop': [],
        'RcRecEndCheck': [], 'RcRecEnd': [], 'RcCapture': [],
        'RcPushPose': [p('P', 'vector'), p('R', 'rotator')], 'RcPushLoc': [p('P', 'vector')],
        'RcPushRot': [p('R', 'rotator')], 'RcPushF': [p('V', 'float')], 'RcAccept': [], 'RcShow': [],
        'RcBtns': [], 'RcBtn': [p('I', 'int'), p('On', 'bool')], 'RcStations': [], 'RcStationOne': [p('I', 'int')],
        'RcSound': [p('Snd', 'object', SND)], 'RcDebug': []}}

io.open(os.path.join(AQUI, 'ghost_spec.json'), 'w', encoding='utf-8').write(json.dumps(spec, indent=1, ensure_ascii=False))
print('ghost_spec.json v2:', {k: (len(v['vars']), len(v['functions'])) for k, v in spec.items() if isinstance(v, dict) and 'vars' in v},
      '+', len(IDS), 'DA (', len(USADAS), 'en uso )')
