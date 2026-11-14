# gen_mote_material.py (2026-11-04) - M_AttractMote_SC: las particulas de un chorro de Attracting (BP_AttractStreams_SC).
# Escribe los 3 Custom (HLSL) y el plan attract_mote_build.json en VR_Test/Saved/ClaudeScripts/; los arma en Unreal
# apply_attract_material.py (copia del pipeline de apply_chladni_material.py).
#
# Cada componente = un chorro. Todo lo del chorro llega por Custom Primitive Data (8 vectores RGBA, indices 0..31):
#   SA  0: T0 (GameTime en que arranco), Seed, -, -
#   SC  4: color RGB de la nota, ColorPow
#   CE  8: ojo del usuario (local del actor), Radius de la burbuja
#   EM 12: punto de emision en la ameba (local), Squash vertical de la burbuja
#   K1 16: Life, Count, Travel, Bend
#   K2 20: Spread, Swirl, Wobble, WobbleHz
#   K3 24: Jitter, ShellNoise, CenterDrop, FadeIn
#   K4 28: Size, MinAngle, FadeOut, Brightness
# Particula k (LocalPosition.x de SM_AttractMotes_SC) nace en T0 + k/rate y renace cada Life (rate = Count/Life): un chorro
# constante. Camino en polares alrededor del centro C de la burbuja: el radio baja de |E-C| a R (smoothstep en Travel), la
# direccion gira Bend alrededor del eje del chorro (cada chorro se curva en su plano) y, al llegar, sigue girando sobre la
# burbuja (Swirl, eje propio por particula = abanico). Ondulacion coherente por tiempo de emision (manguera viva).
import json, os
OUT = 'C:/Users/beltr/Desktop/Alma Digital Studio/Projects/VR Unreal/VR_Test/Saved/ClaudeScripts/'

CORE = r'''
float t = View.GameTime;
float k = floor(LP.x + 0.5);
float life = max(K1.x, 0.5);
float cnt = clamp(K1.y, 1.0, 256.0);
float trav = clamp(K1.z, 0.2, life);
float rate = cnt / life;
float since = t - SA.x - k / rate;
float alive = step(0.0, since) * step(k + 0.5, cnt);
float sn = max(since, 0.0);
float gen = floor(sn / life);
float a = sn - gen * life;
float3 p3 = frac(float3(k * 0.7123 + 0.31, gen * 1.371 + 0.17, SA.y * 0.0137 + 0.53) * float3(0.1031, 0.1030, 0.0973));
p3 += dot(p3, p3.yxz + 33.33);
float3 h = frac((p3.xxy + p3.yxx) * p3.zyx);
float3 q3 = frac(h * float3(0.1031, 0.1030, 0.0973) + float3(0.71, 0.13, 0.37));
q3 += dot(q3, q3.yxz + 33.33);
float3 g = frac((q3.xxy + q3.yxx) * q3.zyx);
float3 s3 = frac(float3(SA.y * 0.1031 + 0.11, SA.y * 0.1030 + 0.47, SA.y * 0.0973 + 0.83));
s3 += dot(s3, s3.yxz + 33.33);
s3 = frac((s3.xxy + s3.yxx) * s3.zyx);
float3 eye = CE.xyz;
float R = max(CE.w, 10.0);
float3 C = eye - float3(0.0, 0.0, K3.z);
float3 E = EM.xyz;
float3 dv = E - C;
float D = max(length(dv), R + 1.0);
float3 u0 = dv / D;
float3 upv = abs(u0.z) < 0.95 ? float3(0.0, 0.0, 1.0) : float3(1.0, 0.0, 0.0);
float3 e1 = normalize(cross(upv, u0));
float3 e2 = cross(u0, e1);
float psi = 6.2831853 * s3.x;
float3 axS = cos(psi) * e1 + sin(psi) * e2;
float pr = saturate(a / trav);
float sp = pr * pr * (3.0 - 2.0 * pr);
float Rk = R + K3.y * (h.y * 2.0 - 1.0);
float rho = Rk + (D - Rk) * (1.0 - sp);
float beta = K1.w * (0.6 + 0.4 * s3.y) * sp;
float3 d1 = u0 * cos(beta) + cross(axS, u0) * sin(beta);
float3 axK = normalize(axS + K2.x * (h * 2.0 - 1.0) + float3(0.0, 0.0, 0.0001));
float xs = (a - 0.7 * trav) / 0.8;
float soft = 0.8 * (xs > 8.0 ? xs : log(1.0 + exp(xs)));
float om = (K2.y / R) * (0.6 + 0.8 * g.x) * (s3.z < 0.5 ? -1.0 : 1.0);
float th = om * soft;
float ct = cos(th);
float st = sin(th);
float3 d2 = d1 * ct + cross(axK, d1) * st + axK * dot(axK, d1) * (1.0 - ct);
float3 rel = d2 * rho;
rel.z *= lerp(1.0, EM.w, sp);
float te = t - a;
float w1 = 6.2831853 * K2.w;
float n1 = 0.6 * sin(w1 * te + 6.2831853 * s3.y) + 0.4 * sin(1.73 * w1 * te + 6.2831853 * s3.z);
float n2 = 0.6 * sin(1.31 * w1 * te + 6.2831853 * s3.x) + 0.4 * sin(2.11 * w1 * te + 1.7);
float env = sin(3.14159265 * pr);
float3 P = C + rel + (e1 * n1 + e2 * n2) * (K2.z * env) + (g * 2.0 - 1.0) * (K3.x * pr);
float dist = length(P - eye);
float sz = max(K4.x, dist * K4.y);
'''

VS = CORE + r'''
float3 vd = (P - eye) / max(dist, 0.01);
float3 rt = normalize(cross(float3(0.0, 0.0, 1.0), vd) + float3(0.0001, 0.0, 0.0));
float3 up = cross(vd, rt);
float2 c = UV * 2.0 - 1.0;
P += (rt * c.x + up * c.y) * (0.5 * sz * alive);
return P - LP;
'''

AL = CORE + r'''
float fin = smoothstep(0.0, max(K3.w, 0.01), a);
float fout = smoothstep(0.0, max(K4.z, 0.01), life - a);
return alive * fin * fout;
'''

# 2026-11-04 (2.a): translucido (alpha), no aditivo. El salar es claro: lo aditivo se lavaba a blanco y casi no se leia.
PS = r'''
float3 col = pow(max(SC.rgb, 0.0001), max(SC.a, 0.01));
return col * K4.w;
'''

OP = r'''
float2 c = UV * 2.0 - 1.0;
float d = saturate(1.0 - dot(c, c));
return saturate(Al * d * d);
'''

CPD = [('SA', 0, (0, 1, 0, 0)), ('SC', 4, (0.9, 0.7, 0.8, 2.0)), ('CE', 8, (0, 0, 115, 115)), ('EM', 12, (650, 0, 150, 0.75)),
       ('K1', 16, (16, 160, 7, 0.5)), ('K2', 20, (0.6, 20, 8, 0.12)), ('K3', 24, (2, 8, 20, 0.6)), ('K4', 28, (0.45, 0.0015, 3, 2))]

params = [{'name': n, 'kind': 'vector', 'group': 'Mote', 'default': list(d), 'cpd': i} for n, i, d in CPD]
vin = [{'name': 'LP', 'src': {'kind': 'localpos'}}, {'name': 'UV', 'src': {'kind': 'uv'}}] + \
      [{'name': n, 'src': {'kind': 'param', 'param': n}} for n, i, d in CPD if n != 'SC']
customs = [
    {'desc': 'MoteVS', 'outputType': 'CMOT_Float3', 'code_file': 'attract_MoteVS.txt', 'inputs': vin},
    {'desc': 'MoteAlphaVS', 'outputType': 'CMOT_Float1', 'code_file': 'attract_MoteAlphaVS.txt', 'inputs': vin},
    {'desc': 'MotePS', 'outputType': 'CMOT_Float3', 'code_file': 'attract_MotePS.txt',
     'inputs': [{'name': 'SC', 'src': {'kind': 'param', 'param': 'SC'}}, {'name': 'K4', 'src': {'kind': 'param', 'param': 'K4'}}]},
    {'desc': 'MoteOpPS', 'outputType': 'CMOT_Float1', 'code_file': 'attract_MoteOpPS.txt',
     'inputs': [{'name': 'UV', 'src': {'kind': 'uv'}}, {'name': 'Al', 'src': {'kind': 'vi'}}]},
]
open(OUT + 'attract_MoteVS.txt', 'w').write(VS.strip() + '\n')
open(OUT + 'attract_MoteAlphaVS.txt', 'w').write(AL.strip() + '\n')
open(OUT + 'attract_MotePS.txt', 'w').write(PS.strip() + '\n')
open(OUT + 'attract_MoteOpPS.txt', 'w').write(OP.strip() + '\n')
plan = {'material': '/Game/SoulCharger/Mechanics/Harp/Materials/M_AttractMote_SC', 'blend': 'BLEND_Translucent', 'params': params, 'customs': customs}
json.dump(plan, open(OUT + 'attract_mote_build.json', 'w'), indent=1)
print('ok', len(params), 'params', len(customs), 'customs')
