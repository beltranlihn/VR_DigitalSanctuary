import json
CDO = '/Game/SoulCharger/Mechanics/Harp/Blueprints/BP_Harp_SC.Default__BP_Harp_SC_C'
INST = '/Game/SoulCharger/Mechanics/Harp/Maps/Test_Harp.Test_Harp:PersistentLevel.BP_Harp_SC_C_0'
K = ['VNS', 'VName', 'VVar', 'VSnd', 'LFrom', 'LOut', 'LTo', 'LIn', 'LSnd', 'DNode', 'DIn', 'DVal', 'DSnd']
SND = 3
OUT_GAIN = 0.025
NOISE_MIX = 0.12
TRIG_DELAY = 0.022
MAIN = 14
BRIGHT = 15
MODES = [
    (-11000.0, 3.2, 0.75, MAIN, 'P'),
    (-11004.5, 4.6, 0.20, BRIGHT, 'S'),
    (-11997.0, 2.7, 0.80, MAIN, 'P'),
    (-12016.0, 3.4, 0.28, MAIN, 'S'),
    (-12985.0, 1.9, 0.40, BRIGHT, 'P'),
    (-13008.0, 2.3, 0.16, BRIGHT, 'S'),
    (-17500.0, 0.7, 0.50, BRIGHT, 'M'),
    (-18160.0, 0.5, 0.40, BRIGHT, 'M'),
    (-307340.0, 0.6, 0.45, MAIN, 'P'),
    (-338000.0, 0.04, 0.30, BRIGHT, 'P'),
]
BODY = 8
GAIN_BASE = {'P': 400000.0, 'M': 500000.0, 'S': 600000.0}


def recipe():
    N = []
    L = []
    D = []
    N += [('UE', 'Trigger Delay', 'None'),
          ('UE', 'Trigger Counter', 'None'), ('UE', 'ConversionInt32ToTime', 'None'), ('UE', 'ConversionTimeToFloat', 'None'), ('UE', 'ConversionFloatToAudio', 'None'),
          ('UE', 'One-Pole High Pass Filter', 'Audio'),
          ('UE', 'Noise', 'Audio'), ('AD Envelope', 'AD Envelope', 'Audio'), ('UE', 'Multiply', 'Audio'), ('UE', 'Multiply', 'Audio by Float'),
          ('UE', 'Add', 'Audio'), ('UE', 'One-Pole Low Pass Filter', 'Audio'),
          ('UE', 'Multiply', 'Audio by Float'), ('UE', 'Multiply', 'Audio by Float'), ('UE', 'Multiply', 'Audio by Float'), ('UE', 'Multiply', 'Audio by Float')]
    L += [(-1, 'None', 0, 'In'), (0, 'Out', 1, 'In'), (1, 'Count', 2, 'In'), (2, 'Out', 3, 'In'), (3, 'Out', 4, 'In'), (4, 'Out', 5, 'In'),
          (0, 'Out', 7, 'Trigger'), (6, 'Audio', 8, 'PrimaryOperand'), (7, 'Out Envelope', 8, 'AdditionalOperands'),
          (8, 'Out', 9, 'PrimaryOperand'), (5, 'Out', 10, 'PrimaryOperand'), (9, 'Out', 10, 'AdditionalOperands'),
          (10, 'Out', 11, 'In'), (-3, 'None', 11, 'Cutoff Frequency'),
          (11, 'Out', 12, 'PrimaryOperand'), (-2, 'None', 12, 'AdditionalOperands'),
          (12, 'Out', 13, 'PrimaryOperand'), (-2, 'None', 13, 'AdditionalOperands'),
          (13, 'Out', 14, 'PrimaryOperand'), (-2, 'None', 14, 'AdditionalOperands'),
          (14, 'Out', 15, 'PrimaryOperand'), (-2, 'None', 15, 'AdditionalOperands')]
    D += [(0, 'Delay Time', TRIG_DELAY), (5, 'Cutoff Frequency', 4000.0), (7, 'Attack Time', 0.0003), (7, 'Decay Time', 0.005), (9, 'AdditionalOperands', NOISE_MIX)]
    outs = []
    for m, (fc, t60, a, bus, grp) in enumerate(MODES):
        b = len(N)
        N += [('UE', 'Biquad Filter', 'Audio'), ('UE', 'Multiply', 'Audio by Float')]
        L += [(bus, 'Out', b, 'In'), (b, 'Out', b + 1, 'PrimaryOperand')]
        D += [(b, 'Type', -1102.0), (b, 'Cutoff Frequency', fc), (b, 'Bandwidth', -(200000.0 + round(t60 * 1000.0))), (b + 1, 'AdditionalOperands', -(GAIN_BASE[grp] + round(a * t60 * 1818.0 * 10.0)))]
        outs.append(b + 1)
    w = len(N)
    N += [('UE', 'Multiply', 'Audio by Float')]
    L += [(outs[BODY], 'Out', w, 'PrimaryOperand')]
    D += [(w, 'AdditionalOperands', -1010.0)]
    outs[BODY] = w
    acc = outs[0]
    for o in outs[1:]:
        s = len(N)
        N += [('UE', 'Add', 'Audio')]
        L += [(acc, 'Out', s, 'PrimaryOperand'), (o, 'Out', s, 'AdditionalOperands')]
        acc = s
    g = len(N)
    N += [('UE', 'Multiply', 'Audio by Float'), ('UE', 'Stereo Panner', 'None')]
    L += [(acc, 'Out', g, 'PrimaryOperand'), (g, 'Out', g + 1, 'In'), (g + 1, 'Out Left', -10, 'None'), (g + 1, 'Out Right', -11, 'None')]
    D += [(g, 'AdditionalOperands', OUT_GAIN), (g + 1, 'Pan Amount', -1003.0)]
    return N, L, D, g


def sp(obj, vals):
    return execute_tool('editor_toolset.toolsets.object.ObjectTools.set_properties', json.dumps({'instance': {'refPath': obj}, 'values': json.dumps(vals)}))['returnValue']


def gp(obj, props):
    return json.loads(execute_tool('editor_toolset.toolsets.object.ObjectTools.get_properties', json.dumps({'instance': {'refPath': obj}, 'properties': props}))['returnValue'])


def run():
    out = {}
    try:
        c = gp(CDO, K + ['SndChorus'])
        keepV = [k for k in range(len(c['VSnd'])) if c['VSnd'][k] != SND]
        keepL = [k for k in range(len(c['LSnd'])) if c['LSnd'][k] != SND]
        keepD = [k for k in range(len(c['DSnd'])) if c['DSnd'][k] != SND]
        r = {}
        for k in ['VNS', 'VName', 'VVar', 'VSnd']:
            r[k] = [c[k][i] for i in keepV]
        for k in ['LFrom', 'LOut', 'LTo', 'LIn', 'LSnd']:
            r[k] = [c[k][i] for i in keepL]
        for k in ['DNode', 'DIn', 'DVal', 'DSnd']:
            r[k] = [c[k][i] for i in keepD]
        N, L, D, g = recipe()
        for ns, n, v in N:
            r['VNS'].append(ns); r['VName'].append(n); r['VVar'].append(v); r['VSnd'].append(SND)
        for fr, o, to, i in L:
            r['LFrom'].append(fr); r['LOut'].append(o); r['LTo'].append(to); r['LIn'].append(i); r['LSnd'].append(SND)
        for nd, i, v in D:
            r['DNode'].append(nd); r['DIn'].append(i); r['DVal'].append(v); r['DSnd'].append(SND)
        ch = list(c['SndChorus'])
        ch[SND] = 0.0
        extra = {'SndChorus': ch, 'HangT60Tilt': 0.25, 'HangBodyOther': 0.25}
        for who, obj in [('cdo', CDO), ('inst', INST)]:
            sp(obj, {k: [] for k in K})
            sp(obj, r)
            sp(obj, extra)
            back = gp(obj, K + ['SndChorus', 'HangT60Tilt', 'HangBodyOther'])
            out[who] = {'same': all(back[k] == r[k] for k in K), 'n3': [back['VSnd'].count(SND), back['LSnd'].count(SND), back['DSnd'].count(SND)],
                        'others': [len(keepV), len(keepL), len(keepD)], 'chorus': back['SndChorus'], 'tilt': back['HangT60Tilt'], 'body': back['HangBodyOther']}
        out['nodes'] = len(N)
        out['gain_row_node'] = g
    except BaseException as e:
        out['err'] = str(e)[:300]
    return out
