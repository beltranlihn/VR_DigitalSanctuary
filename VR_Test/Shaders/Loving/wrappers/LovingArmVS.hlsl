// @uses SS,Hash,Shape,CoreWob,Calm,NeckBreath,BallsLayout,CentreGap,ArmSetup,BridgeSetup,SminS,SminH,Surr,StrandR,ArmRay,ArmField3,BridgeR,BridgeSDF,AmPod,AmBody,CentreR,Mound
// @inputs LocalPos,GI,GP,GN,BPr,LV0,LV1,LV2,LV3,LV4,LV5
// @outputs return:Float3,Nrm:Float3,Misc:Float3,Misc2:Float2
// BRAZO DE MEMBRANA: el tubo SM_LovingLimb_SC (eje Y local, -100..100) se proyecta sobre
// el campo del brazo. Zonas de anillos por t: [0,t1] hebra (espaciado coseno, denso en los
// ensanches) · [t1,t2] cuello + mitad cercana de la envoltura · [t2,1] tapa desde G, con el
// rayo girando de perpendicular a axial (como el gusano). 7 bisecciones + 1 secante.
// Salidas: Nrm = normal LOCAL (4 taps del campo 3D) · Misc = (J juntura, radio local,
// distancia al puente mas cercano) · Misc2 = (distancia con signo a la MEMBRANA del nucleo, t).
// GI = este grupo, GP/GN = vecinos (para los puentes), BPr = progreso de los puentes (prev, next).
// Todo el empaquetado (AP0..AP6, bolas, puentes) sale del estado por la libreria.
LVLib L;
float T = ResolvedView.GameTime;
if (!(T > -1.0e9 && T < 1.0e9)) { T = 0.0; }
float4 AP0, AP1, AP2, B0, B1, B2, AP3, AP4, AP5, AP6;
L.ArmSetup(GI, LV0, LV1, LV2, LV3, LV4, LV5, T, AP0, AP1, AP2, B0, B1, B2, AP3, AP4, AP5, AP6);
float3 lp = LocalPos;
float  t  = saturate((lp.y + 100.0) * 0.005);
float2 rc = normalize(lp.xz + float2(1.0e-4, 0.0));
float3 Pc = AP0.xyz; float Rcm = AP0.w;
float3 ax = AP1.xyz - Pc; float Lx = max(length(ax), 1.0); ax /= Lx;
float3 U  = normalize(LV4.xyz - ax * dot(LV4.xyz, ax) + float3(0.0, 0.0, 1.0e-5));   // plano de la figura (AP2.xyz es la inclinacion del ancla)
float3 Vb = cross(ax, U);
float3 n  = U * rc.x + Vb * rc.y;
float gap = AP1.w, hug = saturate(AP2.w);
float a0, e0, x0, A0, a1, e1, x1, A1, a2, e2, x2, A2;
L.Surr(B0, ax, n, gap, hug, a0, e0, x0, A0);
L.Surr(B1, ax, n, gap, hug, a1, e1, x1, A1);
L.Surr(B2, ax, n, gap, hug, a2, e2, x2, A2);
float Enear = max(max(A0 * (x0 - a0), A1 * (x1 - a1)), A2 * (x2 - a2));
float Emax  = max(max(A0 * (e0 + abs(a0)), A1 * (e1 + abs(a1))), A2 * (e2 + abs(a2)));
float zEs = Lx - Enear;
float t1 = AP5.z, t2 = AP5.w;
float zS = 0.8 * Rcm;
float zN = max(zEs - 2.0 * AP3.z, zS + 0.5);
float zA = lerp(zS, zN, 0.5 - 0.5 * cos(3.14159265 * saturate(t / max(t1, 1.0e-3))));
float zB = lerp(zN, Lx, saturate((t - t1) / max(t2 - t1, 1.0e-3)));
float z0 = lerp(lerp(zA, zB, step(t1, t)), Lx, step(t2, t));
float al = saturate((t - t2) / max(1.0 - t2, 1.0e-3)) * 1.5707963;
float sa = sin(al), ca = cos(al), s2 = sa * sa;
float pr = L.StrandR(z0, AP5.x + dot(AP2.xyz, n), zEs, AP3, AP5.y);   // ancla del ensanche inclinada con la membrana (ArmSetup)
float3 D  = float3(z0 - (Lx + a0), z0 - (Lx + a1), z0 - (Lx + a2));
float3 re = float3(lerp(e0, x0, s2), lerp(e1, x1, s2), lerp(e2, x2, s2));
float3 Aw = float3(A0, A1, A2);
float kC = AP4.x, kE = AP4.y, Ratt = AP4.z, kN = AP3.w;
float DA = z0 - (Lx - AP4.w);
float kAt = max(kE * saturate(Ratt / 2.0), 0.05), Aat = step(1.0e-3, Ratt);
float rmax = max(Rcm + kC, Emax + kE) + AP3.y + kN + 2.0;
float f0  = L.ArmRay(0.0,  z0, sa, Rcm, pr, kC, D, re, Aw, DA, Ratt, kAt, Aat, kE, kN);
float fhi = L.ArmRay(rmax, z0, sa, Rcm, pr, kC, D, re, Aw, DA, Ratt, kAt, Aat, kE, kN);
float lo = 0.0, hi = rmax, flo = f0;
[loop] for (int it = 0; it < 7; it++)
{
    float mr = 0.5 * (lo + hi);
    float fm = L.ArmRay(mr, z0, sa, Rcm, pr, kC, D, re, Aw, DA, Ratt, kAt, Aat, kE, kN);
    float in0 = step(fm, 0.0);
    lo = lerp(lo, mr, in0); flo = lerp(flo, fm, in0);
    hi = lerp(mr, hi, in0); fhi = lerp(fm, fhi, in0);
}
float rr = (lo + (hi - lo) * saturate(flo / min(flo - fhi, -1.0e-4))) * step(f0, 0.0);
float3 dst = Pc + ax * (z0 + rr * sa) + n * (rr * ca);
// normal: 4 taps del MISMO campo en 3D (sin arreglos: 4 variables con nombre)
float J, Jd;
float o  = 0.05;
float g0 = L.ArmField3(dst,                         AP0, AP1, AP2, B0, B1, B2, AP3, AP4, AP5, J);
float gx = L.ArmField3(dst + float3(o, 0.0, 0.0),   AP0, AP1, AP2, B0, B1, B2, AP3, AP4, AP5, Jd);
float gy = L.ArmField3(dst + float3(0.0, o, 0.0),   AP0, AP1, AP2, B0, B1, B2, AP3, AP4, AP5, Jd);
float gz = L.ArmField3(dst + float3(0.0, 0.0, o),   AP0, AP1, AP2, B0, B1, B2, AP3, AP4, AP5, Jd);
Nrm = normalize(float3(gx - g0, gy - g0, gz - g0) + float3(0.0, 0.0, 1.0e-6));
// recorte exacto contra los puentes vecinos (wB = 0 -> 1e4, sin recorte). Los puentes estan APAGADOS por
// defecto (bBridges false -> BPr = 0): [branch] uniforme por dibujo, sin BridgeSetup x2 ni BridgeSDF x2 por vertice.
// Mismo resultado: con BS.w = 0 BridgeSDF ya devolvia 1e4 + algo, y FilmPS solo mira si Misc.z pasa de 1e3.
float bp = 1.0e4, bn = 1.0e4;
[branch] if (BPr.x + BPr.y > 0.0)
{
    float4 BA0, BB0, BS0, BA1, BB1, BS1;
    L.BridgeSetup(GP, GI, BPr.x, LV0, LV1, LV2, LV3, BA0, BB0, BS0);
    L.BridgeSetup(GI, GN, BPr.y, LV0, LV1, LV2, LV3, BA1, BB1, BS1);
    bp = L.BridgeSDF(dst, BA0, BB0, BS0);
    bn = L.BridgeSDF(dst, BA1, BB1, BS1);
}
// contacto con la MEMBRANA del nucleo: la misma ameba (CentreR, con su ondulacion) + los
// abultamientos hacia este brazo Y hacia sus dos vecinos (con 6 grupos, o con una pareja que
// se acerca, el del vecino llega al anillo de la raiz: hasta 1,5 cm de error sin el) +
// CentreGap. Exacta, para que el corte del brazo caiga donde la membrana abre su hueco.
// wP/wN = 0/1: con N = 1 el vecino es el mismo brazo; con N = 2 GP == GN (se cuenta una vez).
float3 wc = dst - Pc; float lc = max(length(wc), 1.0e-3);
float3 uc = wc / lc;
float3 gTc, gmc = float3(0.0, 0.0, 0.0);
float  rC = L.CentreR(uc, AP6.w, LV1, LV3, T, gTc);
float  wP = step(0.5, abs(GP.w - GI.w));
float  wN = step(0.5, abs(GN.w - GI.w)) * step(0.5, abs(GN.w - GP.w));
rC += L.Mound(uc, float4(ax, AP6.y), AP6.z, gmc);
rC += L.Mound(uc, float4(normalize(GP.xyz - Pc + float3(1.0e-4, 0.0, 0.0)), AP6.y * wP), AP6.z, gmc);
rC += L.Mound(uc, float4(normalize(GN.xyz - Pc + float3(1.0e-4, 0.0, 0.0)), AP6.y * wN), AP6.z, gmc);
float dC = lc - (rC + (AP6.x - AP6.w));
Misc  = float3(J, rr, min(bp, bn));
Misc2 = float2(dC, t);
// CURL de la hebra (2026-09-28): funcion compartida con las particulas (ArmWindow + StrandCurl).
// Se aplica DESPUES de todos los recortes (dC, puentes), calculados sin deformar.
float zW0, zW1;
L.ArmWindow(AP1, AP2, AP3, AP4, AP5, B0, B1, B2, Lx, zW0, zW1);
float3 sdz;
dst += L.StrandCurl(dst, Pc, ax, U, Vb, zW0, zW1, saturate(LV1.x), saturate(LV1.z), LV5.y, GI.w, T, sdz);
Nrm = normalize(Nrm - ax * dot(sdz, Nrm));
float3 off = dst - lp;
if (!(dot(off, off) < 1.0e12)) { off = float3(0.0, 0.0, 0.0); }
float ol = length(off);
return off * (min(ol, 400.0) / max(ol, 1.0e-4));
