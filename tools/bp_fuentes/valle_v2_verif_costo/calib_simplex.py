# calib_simplex.py - calibracion del ALU de pixel de la Quest 3 con un dato MEDIDO del proyecto:
# saltear 3 simplex 4D por pixel a pantalla completa (dos ojos, 125 %) ahorro ~7,5-10 ms a 640 MHz
# (BP_Ganzfeld_SC.md, 2026-09-15/16: "saltearlo vale ~10 ms"; "el fondo liso vale ~7-8 ms frente al fluido sin relieve").
# Se cuenta un simplex 4D estandar (Gustavson/Ashima, 5 gradientes, 4 cadenas de permute) con la MISMA regla
# (dxc -O3, DXIL escalar) que los caminos del valle, y se despeja cuantas op-eq por reloj rinde el GPU.
import json
from pathlib import Path
import cost_ops as co

OUT = Path(__file__).resolve().parent
SRC = r"""
float4 mod289(float4 x) { return x - floor(x * (1.0 / 289.0)) * 289.0; }
float mod289s(float x) { return x - floor(x * (1.0 / 289.0)) * 289.0; }
float4 permute(float4 x) { return mod289(((x * 34.0) + 1.0) * x); }
float permutes(float x) { return mod289s(((x * 34.0) + 1.0) * x); }
float4 taylorInvSqrt(float4 r) { return 1.79284291400159 - 0.85373472095314 * r; }
float taylorInvSqrts(float r) { return 1.79284291400159 - 0.85373472095314 * r; }
float4 grad4(float j, float4 ip)
{
  float4 p, s;
  p.xyz = floor(frac(float3(j, j, j) * ip.xyz) * 7.0) * ip.z - 1.0;
  p.w = 1.5 - dot(abs(p.xyz), float3(1.0, 1.0, 1.0));
  s = float4(p < 0.0);
  p.xyz = p.xyz + (s.xyz * 2.0 - 1.0) * s.www;
  return p;
}
float snoise(float4 v)
{
  const float4 C = float4(0.138196601125011, 0.276393202250021, 0.414589803375032, -0.447213595499958);
  float4 i = floor(v + dot(v, 0.309016994374947451));
  float4 x0 = v - i + dot(i, C.xxxx);
  float4 i0;
  float3 isX = step(x0.yzw, x0.xxx);
  float3 isYZ = step(x0.zww, x0.yyz);
  i0.x = isX.x + isX.y + isX.z;
  i0.yzw = 1.0 - isX;
  i0.y += isYZ.x + isYZ.y;
  i0.zw += 1.0 - isYZ.xy;
  i0.z += isYZ.z;
  i0.w += 1.0 - isYZ.z;
  float4 i3 = saturate(i0);
  float4 i2 = saturate(i0 - 1.0);
  float4 i1 = saturate(i0 - 2.0);
  float4 x1 = x0 - i1 + C.xxxx;
  float4 x2 = x0 - i2 + C.yyyy;
  float4 x3 = x0 - i3 + C.zzzz;
  float4 x4 = x0 + C.wwww;
  i = mod289(i);
  float j0 = permutes(permutes(permutes(permutes(i.w) + i.z) + i.y) + i.x);
  float4 j1 = permute(permute(permute(permute(i.w + float4(i1.w, i2.w, i3.w, 1.0)) + i.z + float4(i1.z, i2.z, i3.z, 1.0))
                              + i.y + float4(i1.y, i2.y, i3.y, 1.0)) + i.x + float4(i1.x, i2.x, i3.x, 1.0));
  float4 ip = float4(1.0 / 294.0, 1.0 / 49.0, 1.0 / 7.0, 0.0);
  float4 p0 = grad4(j0, ip);
  float4 p1 = grad4(j1.x, ip);
  float4 p2 = grad4(j1.y, ip);
  float4 p3 = grad4(j1.z, ip);
  float4 p4 = grad4(j1.w, ip);
  float4 norm = taylorInvSqrt(float4(dot(p0, p0), dot(p1, p1), dot(p2, p2), dot(p3, p3)));
  p0 *= norm.x; p1 *= norm.y; p2 *= norm.z; p3 *= norm.w;
  p4 *= taylorInvSqrts(dot(p4, p4));
  float3 m0 = max(0.6 - float3(dot(x0, x0), dot(x1, x1), dot(x2, x2)), 0.0);
  float2 m1 = max(0.6 - float2(dot(x3, x3), dot(x4, x4)), 0.0);
  m0 = m0 * m0; m1 = m1 * m1;
  return 49.0 * (dot(m0 * m0, float3(dot(p0, x0), dot(p1, x1), dot(p2, x2))) + dot(m1 * m1, float2(dot(p3, x3), dot(p4, x4))));
}
cbuffer MatCB : register(b1) { float4 O1; float4 O2; float Tm; };
float4 main(float4 sv : SV_Position, float3 d : TEXCOORD0) : SV_Target
{
  float4 P = float4(d * 3.0, Tm);
  float r = snoise(P);
  %s
  return float4(r, g, b, 1.0);
}
"""
s1, a1, _ = co.compile_count(SRC % "float g = 0.0; float b = 0.0;", "ps", "simplex_x1")
s3, a3, _ = co.compile_count(SRC % "float g = snoise(P + O1); float b = snoise(P + O2);", "ps", "simplex_x3")
per = (a3 - a1) / 2.0, (sum(s3.values()) - sum(s1.values())) / 2.0
print("simplex 4D: ~%.0f ALU + %.0f SFU por evaluacion (x1: %d ALU %s; x3: %d ALU %s)" % (per[0], per[1], a1, s1, a3, s3))
PX = 2 * 2064 * 2208
res = {}
for ms in (7.5, 10.0):
    ops = 3 * (per[0] + 4 * per[1]) * PX
    theta = ops / (ms * 1e-3 * 640e6)
    res[str(ms)] = theta
    print("  si 3 simplex a pantalla completa = %.1f ms a 640 MHz -> rinde %.0f op-eq/reloj (%.2e op-eq/s a 456 MHz)"
          % (ms, theta, theta * 456e6))
(OUT / "calib_simplex.json").write_text(json.dumps({"simplex_alu": per[0], "simplex_sfu": per[1], "theta": res}, indent=1))
