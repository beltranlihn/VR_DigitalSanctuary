# Receta del sonido 3 (hang por resonadores, 17a). La corre execute_tool_script: arma las filas del sonido 3 y las escribe en el CDO y en la instancia.
# Medido en .wav (17a): proporciones x1,997 / x2,985 / x7,50 / x8,16; T60 de la fundamental 3-4,5 s; batido de la octava 2,8 Hz (Re3) a 8,4 Hz (La4).
# Fuente de los numeros: docs/INVESTIGACION-SONIDO-HANG-2026-10-28.md. Indices de nodo = locales al sonido 3.
import json
CDO = '/Game/SoulCharger/Mechanics/Harp/Blueprints/BP_Harp_SC.Default__BP_Harp_SC_C'
INST = '/Game/SoulCharger/Mechanics/Harp/Maps/Test_Harp.Test_Harp:PersistentLevel.BP_Harp_SC_C_0'
K = ['VNS', 'VName', 'VVar', 'VSnd', 'LFrom', 'LOut', 'LTo', 'LIn', 'LSnd', 'DNode', 'DIn', 'DVal', 'DSnd']
SND = 3
OUT_GAIN = 0.025
NOISE_MIX = 0.12
TRIG_DELAY = 0.025  # s: cubre un bloque de audio de 1024 muestras a 44,1 kHz (23,2 ms, Android); en PC alcanzaria con ~11 ms
MAIN = 14    # nodo de la excitacion x Vel^3 (Pluck manda Vel = 0,2 + 0,8 v: Vel^3 = 32 dB de rango)
BRIGHT = 15  # x Vel^4 (42 dB): la quinta, las gemelas, los inarmonicos y el casco solo aparecen al golpear fuerte
# (frecuencia: -10000-1000*r = f*r | -300000-100*Hz = absoluta), (T60: -200000-1000*s), A (amplitud del modo), bus (MAIN = Vel^3, BRIGHT = Vel^4)
# ganancia del modo = A * T60 * 1818 (anillo del pasa-banda de 0 dB excitado por el clic del paso alto de 4 kHz: 2*pi*(2.2/T60)*(1/(2*pi*4000)))
MODES = [
    (-11000.0, 3.2, 0.75, MAIN, 'P'),    # fundamental
    (-11004.5, 4.6, 0.20, BRIGHT, 'S'),    # gemela lenta de la fundamental (el golpe fuerte suena mas largo)
    (-11997.0, 2.7, 0.80, MAIN, 'P'),    # octava (levemente baja, como las medidas)
    (-12016.0, 3.4, 0.28, MAIN, 'S'),    # gemela de la octava: batido 2,8 Hz (Re3) a 8,4 Hz (La4)
    (-12985.0, 1.9, 0.40, BRIGHT, 'P'),    # quinta de la octava
    (-13008.0, 2.3, 0.16, BRIGHT, 'S'),    # su gemela: batido 3,4 a 10 Hz
    (-17500.0, 0.7, 0.50, BRIGHT, 'M'),    # inarmonico x7,50 (Morrison y Rossing)
    (-18160.0, 0.5, 0.40, BRIGHT, 'M'),    # inarmonico x8,16
    (-307340.0, 0.6, 0.45, MAIN, 'P'),   # cuerpo (Helmholtz) 73,4 Hz, x peso del ding
    (-338000.0, 0.04, 0.30, BRIGHT, 'P'),  # golpe del casco 380 Hz
]
BODY = 8
# ganancia como ficha: P = x HangDecay, M = x HangDecay x HangMetal (inarmonicos), S = x HangDecay x HangShimmer (gemelas del batido)
GAIN_BASE = {'P': 400000.0, 'M': 500000.0, 'S': 600000.0}


def recipe():
    N = []
    L = []
    D = []
    # el golpe se demora TRIG_DELAY: Vel y Cut (parametros float) llegan a la grafica un bloque despues del disparo; sin la demora, cada golpe sonaba con la fuerza del anterior
    # el clic: Count del Trigger Counter (sube 1 en CADA golpe; Value no se mueve en el primero) -> Int32 a Time a Float -> audio -> paso alto 4 kHz
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
