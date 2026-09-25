// BACKUP del code de MaterialExpressionCustom_0 de /Game/SoulCharger/Core/Attracting/M_SlotChain_SC
// Leido por MCP el 2026-09-24, ANTES de la cirugia de performance (plan: docs/PLAN-PERF-ATTRACTING.md).
// Para restaurar: ObjectTools.set_properties sobre el nodo con este string en "code" + recompile.

float3 ro = RayOrigin;
float3 rd = normalize(RayDir);
float Rad  = max(ParA.x, 0.5);
float Smth = max(ParA.y, 0.01);
int NSteps = (int)clamp(ParA.z, 4.0, 48.0);
int N      = (int)clamp(ParA.w + 0.5, 1.0, 8.0);
float WobA = WobAFS.x;
float WobF = WobAFS.y;
float WobS = WobAFS.z;
float solo = (WobA > 0.001) ? 1.0 : 0.0;
float ps = solo * (COrb.x*0.11 + COrb.y*0.17 + COrb.z*0.23);
float sJit = 1.0 + solo * (frac(ps*0.137 + 0.31) - 0.5) * 0.5;
float stepK = (WobA > 0.001) ? 0.7 : 1.0;
float3 P[9];
P[0]=C0; P[1]=C1; P[2]=C2; P[3]=C3; P[4]=C4; P[5]=C5; P[6]=C6; P[7]=C7;
float R[9];
R[0]=Rad0.x; R[1]=Rad0.y; R[2]=Rad0.z;
R[3]=Rad1.x; R[4]=Rad1.y; R[5]=Rad1.z;
R[6]=Rad2.x; R[7]=Rad2.y;
float PU[9];
PU[0]=Pul0.x; PU[1]=Pul0.y; PU[2]=Pul0.z;
PU[3]=Pul1.x; PU[4]=Pul1.y; PU[5]=Pul1.z;
PU[6]=Pul2.x; PU[7]=Pul2.y;
float lastF = max((float)(N-1), 1.0);
float3 chainDir = normalize(P[max(N-1,0)] - P[0] + float3(0.0, 0.00001, 0.0));
float ga = 2.39996323;
int j = 0;
for (j = 0; j < 8; j++)
{
  float fj = (float)j;
  float pn = fj / lastF;
  float gj = frac(fj * 0.6180339887 + ps * 0.618);
  float sv = sin(fj * ga);
  float u  = abs(2.0*pn - 1.0);
  float sw1 = sin(6.2831853 * (pn*SwellWv - T*SwellSpd*sJit) + ps*2.7);
  float sw2 = sin(6.2831853 * (pn*SwellWv*1.63 + T*SwellSpd*sJit*0.77 + 0.37) + ps*4.1);
  float swell = 0.55*sw1 + 0.45*sw2;
  float fac = 1.0 + SizeVar*sv + EndB*u*u + SwellAmt*swell;
  fac = max(fac, saturate(MinScl));
  R[j] = max(R[j] * fac, 0.01);
  float wj = max(FloatSpd, 0.0) * (0.85 + 0.30*gj);
  float3 off = FloatAmp * float3(sin(T*wj + fj*ga + ps*1.3), sin(T*wj*1.13 + fj*ga*2.0 + 1.0 + ps*2.1), sin(T*wj*0.87 + fj*ga*3.0 + 2.0 + ps*3.7));
  off -= chainDir * dot(off, chainDir) * (1.0 - saturate(FloatAlng));
  P[j] += off;
}
P[8]  = COrb;
R[8]  = max(ROrb, 0.001);
PU[8] = 0.0;
int NA = (ROrb > 0.001) ? (N + 1) : N;
float eps = max(Rad * 0.02, 0.05);
float t = 0.0;
float hit = 0.0;
float3 pos = ro;
int i = 0;
for (i = 0; i < NSteps; i++)
{
  pos = ro + rd * t;
  float res = 100000.0;
  for (j = 0; j < NA; j++)
  {
    float3 dv = pos - P[j];
    float dl = length(dv);
    float rr = R[j];
    if (WobA > 0.001)
    {
      float3 dn = dv / max(dl, 0.0001);
      float ws = sin(dn.x*WobF + ps*1.7) + sin(dn.y*WobF*1.31 + ps*3.1) + sin(dn.z*WobF*0.77 + ps*5.3);
      float wm = sin(dn.x*WobF*1.9 + T*WobS + ps*2.3) * sin(dn.y*WobF*1.3 - T*WobS*0.83 + ps*1.9);
      rr = rr * (1.0 + WobA * (ws*0.25 + wm*0.55));
    }
    float ds = dl - rr;
    float h = saturate(0.5 + 0.5*(res - ds)/Smth);
    res = lerp(res, ds, h) - Smth*h*(1.0-h);
  }
  if (res < eps) { hit = 1.0; break; }
  t += max(res * stepK, eps);
  if (t > MaxT) break;
}
float3 nrm = float3(0.0, 0.0, 1.0);
PulseW = 0.0;
if (hit > 0.5)
{
  float o = max(Rad * 0.06, 0.05);
  float kk = max(Smth * max(TintSp, 0.01), 0.01);
  float pw = 0.0;
  float3 offs[4];
  offs[0] = float3(0.0, 0.0, 0.0);
  offs[1] = float3(o, 0.0, 0.0);
  offs[2] = float3(0.0, o, 0.0);
  offs[3] = float3(0.0, 0.0, o);
  float dd[4];
  dd[0]=100000.0; dd[1]=100000.0; dd[2]=100000.0; dd[3]=100000.0;
  for (j = 0; j < NA; j++)
  {
    int k = 0;
    for (k = 0; k < 4; k++)
    {
      float3 dv = pos + offs[k] - P[j];
      float dl = length(dv);
      float rr = R[j];
      if (WobA > 0.001)
      {
        float3 dn = dv / max(dl, 0.0001);
        float ws = sin(dn.x*WobF + ps*1.7) + sin(dn.y*WobF*1.31 + ps*3.1) + sin(dn.z*WobF*0.77 + ps*5.3);
        float wm = sin(dn.x*WobF*1.9 + T*WobS + ps*2.3) * sin(dn.y*WobF*1.3 - T*WobS*0.83 + ps*1.9);
        rr = rr * (1.0 + WobA * (ws*0.25 + wm*0.55));
      }
      float a = dl - rr;
      float hh = saturate(0.5 + 0.5*(dd[k] - a)/Smth);
      dd[k] = lerp(dd[k], a, hh) - Smth*hh*(1.0-hh);
      if (k == 0)
      {
        float wj2 = exp(-max(a, 0.0) / kk);
        pw = max(pw, wj2 * PU[j]);
      }
    }
  }
  nrm = normalize(float3(dd[1] - dd[0], dd[2] - dd[0], dd[3] - dd[0]) + 0.00001);
  PulseW = saturate(pw * max(TintG, 0.0));
}
return float4(nrm, hit);
