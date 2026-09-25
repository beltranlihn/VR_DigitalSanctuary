// ---- BANCO DE MEDICION: PerfMode viene del MPC_Perf_SC (default 0 = la obra) ----
// 0 = actual   1 = Steps a la mitad   2 = SDF lisa (sin wobble ni decoracion)   3 = material gratis   4 = solo cadena (esferas apagadas)   5 = solo esferas (cadena apagada)
int PM = (int)(PerfMode + 0.5);
PulseW = 0.0;
if (PM == 3) { return float4(0.0, 0.0, 1.0, 0.0); }
// Modos 4 y 5: apagan UNA de las dos superficies, para partir el costo medido.
// Discriminante: solo las esferas traen WobbleAFS.x > 0 (la cadena usa el default 0 del master).
float isOrb = (WobAFS.x > 0.001) ? 1.0 : 0.0;
if (PM == 4 && isOrb > 0.5) { return float4(0.0, 0.0, 1.0, 0.0); }
if (PM == 5 && isOrb < 0.5) { return float4(0.0, 0.0, 1.0, 0.0); }
// Tiempo en fp32: el input T llega en HALF en el APK y a los ~15 min la animacion se
// cuantiza (trabado progresivo, fp16). View.GameTime es el MISMO reloj como uniform fp32.
float Tt = View.GameTime;
// Modos 6/7 del banco: simulan una sesion larga sumando 1024 s al reloj desde el boot.
// 6 = reloj inflado por el camino HALF (el trabado aparece al instante: el diagnostico).
// 7 = reloj inflado por el camino fp32 (fluido: el fix probado).
if (PM == 6) { half hT = half(Tt + 1024.0); Tt = hT; }
if (PM == 7) { Tt = Tt + 1024.0; }
float3 ro = RayOrigin;
float3 rd = normalize(RayDir);
float Rad  = max(ParA.x, 0.5);
float Smth = max(ParA.y, 0.01);
int NSteps = (int)clamp(ParA.z, 4.0, 48.0);
if (PM == 1) { NSteps = max(NSteps / 2, 4); }
int N      = (int)clamp(ParA.w + 0.5, 1.0, 8.0);
float WobA = WobAFS.x;
if (PM == 2) { WobA = 0.0; }
float WobF = WobAFS.y;
float WobS = WobAFS.z;
float solo = (WobA > 0.001) ? 1.0 : 0.0;
float ps = solo * (COrb.x*0.11 + COrb.y*0.17 + COrb.z*0.23);
float sJit = 1.0 + solo * (frac(ps*0.137 + 0.31) - 0.5) * 0.5;
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
P[8]  = COrb;
R[8]  = max(ROrb, 0.001);
PU[8] = 0.0;
int NA = (ROrb > 0.001) ? (N + 1) : N;
int ND = (NA < 8) ? NA : 8;
if (PM == 2) { ND = 0; }
float lastF = max((float)(N-1), 1.0);
float3 chainDir = normalize(P[max(N-1,0)] - P[0] + float3(0.0, 0.00001, 0.0));
float ga = 2.39996323;
int j = 0;
for (j = 0; j < ND; j++)
{
  float fj = (float)j;
  float pn = fj / lastF;
  float gj = frac(fj * 0.6180339887 + ps * 0.618);
  float sv = sin(fj * ga);
  float u  = abs(2.0*pn - 1.0);
  float sw1 = sin(6.2831853 * (pn*SwellWv - Tt*SwellSpd*sJit) + ps*2.7);
  float sw2 = sin(6.2831853 * (pn*SwellWv*1.63 + Tt*SwellSpd*sJit*0.77 + 0.37) + ps*4.1);
  float swell = 0.55*sw1 + 0.45*sw2;
  float fac = 1.0 + SizeVar*sv + EndB*u*u + SwellAmt*swell;
  fac = max(fac, saturate(MinScl));
  R[j] = max(R[j] * fac, 0.01);
  float wj = max(FloatSpd, 0.0) * (0.85 + 0.30*gj);
  float3 off = FloatAmp * float3(sin(Tt*wj + fj*ga + ps*1.3), sin(Tt*wj*1.13 + fj*ga*2.0 + 1.0 + ps*2.1), sin(Tt*wj*0.87 + fj*ga*3.0 + 2.0 + ps*3.7));
  off -= chainDir * dot(off, chainDir) * (1.0 - saturate(FloatAlng));
  P[j] += off;
}
float eps = max(Rad * 0.02, 0.05);
float mW = 0.0;
if (WobA > 0.001)
{
  float rmax = 0.0;
  for (j = 0; j < NA; j++) { rmax = max(rmax, R[j]); }
  mW = rmax * WobA * 1.31;
}
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
    float ds = length(dv) - R[j];
    float h = saturate(0.5 + 0.5*(res - ds)/Smth);
    res = lerp(res, ds, h) - Smth*h*(1.0-h);
  }
  if (mW > 0.0)
  {
    if (res < mW + eps*2.0)
    {
      float resF = 100000.0;
      for (j = 0; j < NA; j++)
      {
        float3 dv = pos - P[j];
        float dl = length(dv);
        float3 dn = dv / max(dl, 0.0001);
        float ws = sin(dn.x*WobF + ps*1.7) + sin(dn.y*WobF*1.31 + ps*3.1) + sin(dn.z*WobF*0.77 + ps*5.3);
        float wm = sin(dn.x*WobF*1.9 + Tt*WobS + ps*2.3) * sin(dn.y*WobF*1.3 - Tt*WobS*0.83 + ps*1.9);
        float rr = R[j] * (1.0 + WobA * (ws*0.25 + wm*0.55));
        float ds = dl - rr;
        float h = saturate(0.5 + 0.5*(resF - ds)/Smth);
        resF = lerp(resF, ds, h) - Smth*h*(1.0-h);
      }
      if (resF < eps) { hit = 1.0; break; }
      t += max(resF * 0.7, eps);
    }
    else
    {
      t += max(res - mW, eps);
    }
  }
  else
  {
    if (res < eps) { hit = 1.0; break; }
    t += max(res, eps);
  }
  if (t > MaxT) break;
}
float3 nrm = float3(0.0, 0.0, 1.0);
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
        float wm = sin(dn.x*WobF*1.9 + Tt*WobS + ps*2.3) * sin(dn.y*WobF*1.3 - Tt*WobS*0.83 + ps*1.9);
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