// HeartScapeVS - M_HeartScape_SC, VERTEX SHADER (fp32). Plan: docs/PLAN-MEMBRANA-DEL-LATIDO-2026-09-27.md
// Part 0 = membrana, 1 = esfera central, 2 = cielo. Todo en espacio LOCAL (centro = la esfera).
// return: membrana (dh/dx, dh/dy, h, cresta) | esfera (normal local xyz, 0).  WPO: desplazamiento local.  VI2: (x, y, pulso).
// Adreno: topes de bucle CONSTANTES y arreglos leidos solo en bucles desenrollados (gotcha 399).
float Tt = View.GameTime;
float live = step(0.5, Live);
float period = 60.0 / max(PreviewBPM, 1.0);
float ph = Tt / period;
float fph = frac(ph);
float bIdx = floor(ph);
// pulso lub-dub: vivo = ultimo latido que escribio el BP; preview = reloj propio (anima en el editor)
float pAge = lerp(fph * period, Beat.w - Beat.x, live);
float pI = lerp(PreviewIntensity, Beat.y, live);
float Att = max(Attack, 0.001);
float Dec = max(Decay, 0.001);
float e1 = (pAge < Att) ? smoothstep(0.0, Att, pAge) : exp(-(pAge - Att) / Dec);
float a2 = pAge - DubDelay;
float e2 = (a2 < 0.0) ? 0.0 : ((a2 < Att) ? smoothstep(0.0, Att, a2) : exp(-(a2 - Att) / Dec));
float Pulse = pI * (e1 + Dub * e2);
WPO = float3(0.0, 0.0, 0.0);
VI2 = float3(LP.x, LP.y, Pulse);
if (Part > 1.5) { return float4(0.0, 0.0, 0.0, 0.0); }
if (Part > 0.5)
{
  // esfera central: malla de radio 50 -> HeartRadius; late (lub-dub), se hunde y se deforma apenas
  float3 dir = normalize(LP + float3(0.0, 0.0, 1e-5));
  float amt = HeartMorph * (1.0 + 0.8 * Pulse);
  float3 up = (abs(dir.z) < 0.99) ? float3(0.0, 0.0, 1.0) : float3(1.0, 0.0, 0.0);
  float3 t1 = normalize(cross(dir, up));
  float3 t2 = cross(dir, t1);
  float3 P[3];
  [unroll] for (int s2 = 0; s2 < 3; s2++)
  {
    float3 dd = normalize(dir + ((s2 == 1) ? 0.02 * t1 : ((s2 == 2) ? 0.02 * t2 : float3(0.0, 0.0, 0.0))));
    float m = 0.5 * sin(3.0 * dd.x + 2.0 * dd.z + Tt * 0.9 + 1.3) + 0.3 * sin(4.0 * dd.y - 3.0 * dd.x - Tt * 1.3 + 2.6) + 0.2 * sin(5.0 * dd.z + 4.0 * dd.y + Tt * 1.7 + 5.2);
    P[s2] = dd * (1.0 + amt * m);
  }
  float3 n = normalize(cross(P[1] - P[0], P[2] - P[0]));
  n = (dot(n, dir) < 0.0) ? -n : n;
  float R = HeartRadius * (1.0 + PulseScale * Pulse);
  float3 target = P[0] * R + float3(0.0, 0.0, HeartZ - HeartSink * Pulse);
  WPO = target - LP;
  return float4(n, 0.0);
}
// ---- membrana ----
float Wd = max(Width, 1.0);
float Rch = max(Reach, 1.0);
float Bl = max(BirthDistance, 1.0);
float Lb = floor(Lobes + 0.5);
float WR = max(WellRadius, 1.0);
float4 WW[8] = { W0, W1, W2, W3, W4, W5, W6, W7 };
float3 wv[8];
[unroll] for (int kk = 0; kk < 8; kk++)
{
  // (distancia recorrida, intensidad, semilla) de cada onda: preview o la que escribio el BP
  float3 pv = float3((fph + kk) * period * Speed, PreviewIntensity, frac(sin((bIdx - kk) * 12.9898) * 43758.5453));
  float3 lv = float3(Beat.z - WW[kk].x, WW[kk].y, WW[kk].z);
  wv[kk] = lerp(pv, lv, live);
}
float4 BB[4] = { B0, B1, B2, B3 };
float E = 6.0;
float hs[3];
float crest = 0.0;
[unroll] for (int s = 0; s < 3; s++)
{
  float2 p = LP.xy + float2((s == 1) ? E : 0.0, (s == 2) ? E : 0.0);
  float r2 = dot(p, p);
  float r = sqrt(r2);
  float th = atan2(p.y, p.x + 1e-4);
  float h = 0.0;
  [unroll] for (int k = 0; k < 8; k++)
  {
    float d = wv[k].x;
    float sd = wv[k].z * 6.2831853;
    float u = saturate(d / Rch);
    float W = Wd * (1.0 + Spread * u);
    float warp = Warp * (0.65 * sin((Lb - 1.0) * th + 3.1 * sd) + 0.35 * sin((Lb + 1.0) * th - 0.7 * sd));
    float x = (r - (1.732 * WR + d) + warp * W) / W;
    float hills = 1.0 + Hills * (0.6 * sin(Lb * th + sd) + 0.3 * sin((Lb + 2.0) * th - 1.7 * sd) + 0.1 * sin((2.0 * Lb + 1.0) * th + 2.3 * sd));
    float life = wv[k].y * (1.0 - smoothstep(FadeStart, 1.0, u)) * smoothstep(0.0, Bl, d);
    float amp = life * lerp(HeightStart, HeightEnd, u) * max(hills, 0.0);
    float behind = step(x, 0.0);
    float a = 1.0 + Tail * behind;
    float g = exp(-(x * x) / (a * a));
    float mm = RingMix * behind;
    h += amp * g * (1.0 - mm + mm * cos(Ringing * x));
    if (s == 0) { crest += life * (1.0 - u) * (1.0 - u) * exp(-x * x); }
  }
  // pozo Ricker: hoyuelo + borde en r = 1.732 * WellRadius, de donde nace la onda
  float rho2 = r2 / (WR * WR);
  h -= (WellDepth + WellBeat * Pulse) * (1.0 - rho2) * exp(-0.5 * rho2);
  float rr = (r - WR * 1.732) / (WR * 0.6);
  h += RimExtra * (1.0 + 0.6 * Pulse) * exp(-rr * rr);
  // oleaje de fondo, apagado cerca del pozo
  float2 q = p / max(SwellScale, 1.0);
  float ts = Tt * SwellSpeed;
  float sw = 0.5 * sin(q.x + ts) * sin(0.8 * q.y - 0.7 * ts) + 0.3 * sin(1.7 * (q.x + q.y) + 1.3 * ts) + 0.2 * sin(2.3 * (q.x - 2.0 * q.y) - 0.9 * ts);
  h += Swell * sw * smoothstep(WR, WR * 4.0, r);
  // bultos por donde se sueltan las esferas (fase 4; con Bump.z = 0 no hacen nada)
  [unroll] for (int j = 0; j < 4; j++)
  {
    float ab = Beat.w - BB[j].w;
    float eb = smoothstep(-0.4, 0.3, ab) * (1.0 - smoothstep(0.3, 2.0, ab));
    float2 db = p - BB[j].xy;
    float Rb = max(BB[j].z, 1.0) * 1.8;
    h += step(0.5, BB[j].z) * live * BumpAmp * BB[j].z * eb * exp(-dot(db, db) / (Rb * Rb));
  }
  hs[s] = h;
}
WPO = float3(0.0, 0.0, hs[0]);
return float4((hs[1] - hs[0]) / E, (hs[2] - hs[0]) / E, hs[0], crest);
