// HeartGradVS v6 - M_HeartScape_SC, VERTEX SHADER -> VertexInterpolator_0 -> VI1 del PS.
// Membrana: (dh/dx, dh/dy, h, cresta) con GRADIENTE ANALITICO en UNA pasada. Esferas: normal local + pulso.
// El preludio (Pulse, Push, wd) es IDENTICO al de HeartHeightVS: si difieren, la normal no coincide con la forma.
float Tt = View.GameTime;
float live = step(0.5, Live);
float pm = floor(PerfMode + 0.5);
float period = 60.0 * max(floor(BeatDivider + 0.5), 1.0) / max(PreviewBPM, 1.0);
float ph = Tt / period;
float fph = frac(ph);
float bIdx = floor(ph);
float tP = max(PulseRise, 0.05);
float PushT = 0.5 / max(PushSpeed, 0.05);
float Pulse = 0.0;
float Push = 0.0;
[unroll] for (int bb = 0; bb < 3; bb++)
{
  float tB = (bb == 0) ? Beat.x : ((bb == 1) ? BeatP.x : BeatP.z);
  float iB = (bb == 0) ? Beat.y : ((bb == 1) ? BeatP.y : BeatP.w);
  float aB = lerp((fph + bb) * period, Beat.w - tB, live);
  float IB = lerp(PreviewIntensity, iB, live);
  float xP = max(aB / tP, 0.0);
  float xS = max(aB / PushT, 0.0);
  Pulse += IB * xP * xP * exp(2.0 - 2.0 * xP);
  Push += IB * xS * xS * exp(2.0 - 2.0 * xS);
}
float wd = PushT * max(Speed, 1.0);
float spc = lerp(period * Speed, Spacing, live);
float Rch = max(Reach, 1.0);
float Dmx = (spc > 1.0) ? 7.7 * spc : 1e9;
if (Part > 2.5)
{
  // ---- esferas que emergen: normal de la ameba (la escala uniforme no la cambia) + pulso suave para el brillo ----
  float WRo = max(WellRadius, 1.0);
  float dr = max(length(OA.xy) - 1.732 * WRo, 0.0);
  float so = OB.y * 6.2831853;
  float4 WO[8] = { W0, W1, W2, W3, W4, W5, W6, W7 };
  float pO = 0.0;
  [unroll] for (int ko = 0; ko < 8; ko++)
  {
    float d = lerp((fph + ko) * period * Speed, Beat.z - WO[ko].x, live) - wd;
    float I = lerp(PreviewIntensity, WO[ko].y, live);
    float u = saturate(d / Rch);
    float xk = max((d - dr) / (max(Speed, 1.0) * tP), 0.0);
    pO += I * (1.0 - smoothstep(FadeStart, 1.0, u)) * xk * xk * exp(2.0 - 2.0 * xk);
  }
  float3 dirO = normalize(LP + float3(0.0, 0.0, 1e-5));
  float h1 = frac(OB.y * 7.31 + 0.13);
  float h2 = frac(OB.y * 3.77 + 0.51);
  float h3 = frac(OB.y * 5.19 + 0.29);
  float psO = OB.y * 10.2 - 5.1;
  float WFo = 3.0 * (0.7 + 0.6 * h1);
  float WSo = 0.35 * (0.6 + 0.8 * h2);
  float3 axO = normalize(float3(h1, h2, h3) - 0.5 + float3(0.0, 0.0, 0.001));
  float saO, caO;
  sincos(so - 0.349 * Tt, saO, caO);
  float amtO = OrbMorph * OB.z;
  float3 axE = normalize(float3(h3, h1, h2) - 0.5 + float3(0.001, 0.0, 0.0));
  float3 nO = dirO;
  if (amtO > 0.0005)
  {
    float3 upO = (abs(dirO.z) < 0.99) ? float3(0.0, 0.0, 1.0) : float3(1.0, 0.0, 0.0);
    float3 tA = normalize(cross(dirO, upO));
    float3 tC = cross(dirO, tA);
    float3 PO[3];
    [unroll] for (int s3 = 0; s3 < 3; s3++)
    {
      float3 dd = normalize(dirO + ((s3 == 1) ? 0.02 * tA : ((s3 == 2) ? 0.02 * tC : float3(0.0, 0.0, 0.0))));
      float3 du = dd * caO + cross(axO, dd) * saO + axO * dot(axO, dd) * (1.0 - caO);
      float wsO = sin(du.x * WFo + psO * 1.7) + sin(du.y * WFo * 1.31 + psO * 3.1) + sin(du.z * WFo * 0.77 + psO * 5.3);
      float wmO = sin(du.x * WFo * 1.9 + Tt * WSo + psO * 2.3) * sin(du.y * WFo * 1.3 - Tt * WSo * 0.83 + psO * 1.9);
      PO[s3] = dd * (1.0 + amtO * (0.25 * wsO + 0.55 * wmO));
      PO[s3] += 0.3 * OB.z * dot(PO[s3], axE) * axE;
    }
    nO = normalize(cross(PO[1] - PO[0], PO[2] - PO[0]));
    nO = (dot(nO, dirO) < 0.0) ? -nO : nO;
  }
  return float4(nO, saturate(pO));
}
if (Part > 1.5) { return float4(0.0, 0.0, 0.0, 0.0); }
if (Part > 0.5)
{
  // esfera central: la misma forma que HeartHeightVS (giro + ameba lenta + achatado del empuje)
  float3 dir = normalize(LP + float3(0.0, 0.0, 1e-5));
  float3 ax = float3(0.3162, 0.5270, 0.7906);
  float sa, ca;
  sincos(-0.1396 * Tt, sa, ca);
  float WA = HeartMorph * (1.0 + 0.8 * Pulse);
  float sqz = HeartSquash * Push;
  float3 sq = float3(1.0 + 0.5 * sqz, 1.0 + 0.5 * sqz, 1.0 - sqz);
  float3 up = (abs(dir.z) < 0.99) ? float3(0.0, 0.0, 1.0) : float3(1.0, 0.0, 0.0);
  float3 t1 = normalize(cross(dir, up));
  float3 t2 = cross(dir, t1);
  float3 P[3];
  [unroll] for (int s2 = 0; s2 < 3; s2++)
  {
    float3 dd = normalize(dir + ((s2 == 1) ? 0.02 * t1 : ((s2 == 2) ? 0.02 * t2 : float3(0.0, 0.0, 0.0))));
    float3 du = dd * ca + cross(ax, dd) * sa + ax * dot(ax, dd) * (1.0 - ca);
    float ws = sin(du.x * 2.6 + 2.21) + sin(du.y * 3.4 + 4.03) + sin(du.z * 2.0 + 6.89);
    float wm = sin(du.x * 4.2 + Tt * 0.35 + 2.99) * sin(du.y * 3.4 - Tt * 0.29 + 2.47);
    P[s2] = dd * (1.0 + WA * (0.25 * ws + 0.55 * wm)) * sq;
  }
  float3 n = normalize(cross(P[1] - P[0], P[2] - P[0]));
  n = (dot(n, dir) < 0.0) ? -n : n;
  return float4(n, 0.0);
}
if (pm == 1.0 || pm == 3.0) { return float4(0.0, 0.0, 0.0, 0.0); }
float Wd = max(Width, 1.0);
float Bl = max(BirthDistance, 1.0);
float Lb = floor(Lobes + 0.5);
float WR = max(WellRadius, 1.0);
float2 p = LP.xy;
float r2 = dot(p, p);
float r = sqrt(r2);
float rs = max(r, 2.0);
float2 er = p / rs;                       // d r / d p
float2 et = float2(-er.y, er.x) / rs;     // d theta / d p
float th = atan2(p.y, p.x + 1e-4);
float4 WW[8] = { W0, W1, W2, W3, W4, W5, W6, W7 };
float h = 0.0;
float dhr = 0.0;
float dht = 0.0;
float crest = 0.0;
float2 gc = float2(0.0, 0.0);
[unroll] for (int k = 0; k < 8; k++)
{
  float d = lerp((fph + k) * period * Speed, Beat.z - WW[k].x, live) - wd;
  float I = lerp(PreviewIntensity, WW[k].y, live);
  float u = saturate(d / Rch);
  float W = Wd * (1.0 + Spread * u);
  float life = I * (1.0 - smoothstep(FadeStart, 1.0, u)) * smoothstep(0.0, Bl, d) * (1.0 - smoothstep(0.8 * Dmx, Dmx, d));
  float xa = (r - (1.732 * WR + d)) / W;
  if (life < 0.001 || xa > 2.5 + Warp || xa < -2.5 * (1.0 + Tail) - Warp) { continue; }
  float sd = lerp(frac(sin((bIdx - k) * 12.9898) * 43758.5453), WW[k].z, live) * 6.2831853;
  float s1, c1, s2w, c2w;
  sincos((Lb - 1.0) * th + 3.1 * sd, s1, c1);
  sincos((Lb + 1.0) * th - 0.7 * sd, s2w, c2w);
  float warp = Warp * (0.65 * s1 + 0.35 * s2w);
  float dwarp = Warp * (0.65 * (Lb - 1.0) * c1 + 0.35 * (Lb + 1.0) * c2w);
  float x = xa + warp;
  float sb1, cb1, sb2, cb2, sb3, cb3;
  sincos(Lb * th + sd, sb1, cb1);
  sincos((Lb + 2.0) * th - 1.7 * sd, sb2, cb2);
  sincos((2.0 * Lb + 1.0) * th + 2.3 * sd, sb3, cb3);
  float hills = 1.0 + Hills * (0.6 * sb1 + 0.3 * sb2 + 0.1 * sb3);
  float dhills = Hills * (0.6 * Lb * cb1 + 0.3 * (Lb + 2.0) * cb2 + 0.1 * (2.0 * Lb + 1.0) * cb3);
  float hc = max(hills, 0.0);
  float dhc = (hills > 0.0) ? dhills : 0.0;
  float A = life * lerp(HeightStart, HeightEnd, u);
  float behind = step(x, 0.0);
  float a = 1.0 + Tail * behind;
  float ia2 = 1.0 / (a * a);
  float g = exp(-x * x * ia2);
  float mm = RingMix * behind;
  float sR, cR;
  sincos(Ringing * x, sR, cR);
  float osc = 1.0 - mm + mm * cR;
  float Pv = g * osc;
  float dP = g * (-2.0 * x * ia2 * osc - mm * Ringing * sR);
  h += A * hc * Pv;
  dhr += A * hc * dP / W;
  dht += A * (dhc * Pv + hc * dP * dwarp);
  crest += life * (1.0 - u) * (1.0 - u) * exp(-x * x);
}
// pozo Ricker que hunde el EMPUJE: h = -D (1 - rho^2) e^(-rho^2/2) ; dh/dr = -D e^(-rho^2/2) (r / WR^2) (rho^2 - 3)
float rho2 = r2 / (WR * WR);
float ew = exp(-0.5 * rho2);
float D = WellDepth + WellBeat * Push;
h -= D * (1.0 - rho2) * ew;
dhr -= D * ew * (r / (WR * WR)) * (rho2 - 3.0);
float rr = (r - WR * 1.732) / (WR * 0.6);
float hrim = RimExtra * (1.0 + 0.6 * Push) * exp(-rr * rr);
h += hrim;
dhr += hrim * (-2.0 * rr) / (0.6 * WR);
// oleaje (cartesiano) por el fundido radial
float SS = max(SwellScale, 1.0);
float2 q = p / SS;
float ts = Tt * SwellSpeed;
float sA, cA, sB, cB, sC, cC, sD, cD;
sincos(q.x + ts, sA, cA);
sincos(0.8 * q.y - 0.7 * ts, sB, cB);
sincos(1.7 * (q.x + q.y) + 1.3 * ts, sC, cC);
sincos(2.3 * (q.x - 2.0 * q.y) - 0.9 * ts, sD, cD);
float sw = 0.5 * sA * sB + 0.3 * sC + 0.2 * sD;
float2 dsw = float2(0.5 * cA * sB + 0.51 * cC + 0.46 * cD, 0.4 * sA * cB + 0.51 * cC - 0.92 * cD) / SS;
float tf = saturate((r - WR) / (3.0 * WR));
float fade = tf * tf * (3.0 - 2.0 * tf);
float dfade = 6.0 * tf * (1.0 - tf) / (3.0 * WR);
h += Swell * sw * fade;
gc += Swell * dsw * fade;
dhr += Swell * sw * dfade;
float4 BB[4] = { B0, B1, B2, B3 };
[unroll] for (int j = 0; j < 4; j++)
{
  float ab = Beat.w - BB[j].w - PushT;
  float eb = smoothstep(-0.4, 0.3, ab) * (1.0 - smoothstep(0.3, 2.0, ab));
  float2 db = p - BB[j].xy;
  float Rb = max(BB[j].z, 1.0) * 1.8;
  float hb = step(0.5, BB[j].z) * live * BumpAmp * BB[j].z * eb * exp(-dot(db, db) / (Rb * Rb));
  h += hb;
  gc += hb * (-2.0 * db / (Rb * Rb));
}
float2 grad = dhr * er + dht * et + gc;
return float4(grad.x, grad.y, h, crest);
