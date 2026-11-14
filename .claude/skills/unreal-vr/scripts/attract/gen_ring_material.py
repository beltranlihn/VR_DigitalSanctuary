# gen_ring_material.py (2026-11-04) - M_AttractRing_SC: la onda de cada nota sobre el espejo del salar (BP_AttractCall_SC).
# Escribe los Custom y el plan attract_ring_build.json; lo arma apply_attract_material.py (generico por plan).
# Custom Primitive Data: RA 0 = (Radio cm, Ancho cm, Alfa, Suavidad del borde) · RC 4 = (color RGB, brillo).
import json
OUT = 'C:/Users/beltr/Desktop/Alma Digital Studio/Projects/VR Unreal/VR_Test/Saved/ClaudeScripts/'
VS = r'''
float2 d = LP.xy / max(length(LP.xy), 0.0001);
float r = RA.x + (UV.y - 0.5) * RA.y;
float3 P = float3(d * r, LP.z);
return P - LP;
'''
PS = r'''
return RC.rgb * RC.a;
'''
OP = r'''
float e = 1.0 - abs(UV.y * 2.0 - 1.0);
return saturate(RA.z * pow(max(e, 0.0), max(RA.w, 0.01)));
'''
CPD = [('RA', 0, (100, 5, 0.8, 1.5)), ('RC', 4, (1.0, 0.8, 0.6, 1.4))]
params = [{'name': n, 'kind': 'vector', 'group': 'Ring', 'default': list(d), 'cpd': i} for n, i, d in CPD]
customs = [
    {'desc': 'RingVS', 'outputType': 'CMOT_Float3', 'code_file': 'attract_RingVS.txt',
     'inputs': [{'name': 'LP', 'src': {'kind': 'localpos'}}, {'name': 'UV', 'src': {'kind': 'uv'}}, {'name': 'RA', 'src': {'kind': 'param', 'param': 'RA'}}]},
    {'desc': 'RingPS', 'outputType': 'CMOT_Float3', 'code_file': 'attract_RingPS.txt',
     'inputs': [{'name': 'RC', 'src': {'kind': 'param', 'param': 'RC'}}]},
    {'desc': 'RingOpPS', 'outputType': 'CMOT_Float1', 'code_file': 'attract_RingOpPS.txt',
     'inputs': [{'name': 'UV', 'src': {'kind': 'uv'}}, {'name': 'RA', 'src': {'kind': 'param', 'param': 'RA'}}]},
]
outputs = [{'custom': 'RingVS', 'wpo': True}, {'custom': 'RingPS', 'prop': 'MP_EmissiveColor'}, {'custom': 'RingOpPS', 'prop': 'MP_Opacity'}]
open(OUT + 'attract_RingVS.txt', 'w').write(VS.strip() + '\n')
open(OUT + 'attract_RingPS.txt', 'w').write(PS.strip() + '\n')
open(OUT + 'attract_RingOpPS.txt', 'w').write(OP.strip() + '\n')
plan = {'material': '/Game/SoulCharger/Mechanics/Harp/Materials/M_AttractRing_SC', 'blend': 'BLEND_Translucent',
        'params': params, 'customs': customs, 'outputs': outputs}
json.dump(plan, open(OUT + 'attract_ring_build.json', 'w'), indent=1)
print('ok ring plan')
