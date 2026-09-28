// @uses SS,Hash,Shape,CentreGap,AmPod,AmBody,CentreR,Mound,ArmSetup,ArmWindow,StrandCurl,RayExit
// @inputs LocalPos,Crn,UVa,UVb,CamL,LV0,LV1,LV2,LV3,LV4,LV5,M0,M1,M2,M3,M4,M5,M6,M7,M8,M9,DustK
// @outputs return:Float3,DustUV:Float3
// SEGUNDA MEMBRANA DE PARTICULAS (2026-09-28, Beltran: "particulas muy pequenas que tomen la forma
// de todo este CELL, como una segunda membrana, con opacidad"). Cada quad de SM_LovingDust_SC es
// una particula: el VS calcula su CENTRO con la misma libreria que dibuja la celula (asi sigue la
// forma exacta: la ameba que ondula, las envolturas que respiran, las hebras con curl) y la gira
// hacia la camara. Nada en la CPU; una sola llamada de dibujo.
//   UVa = (a, b): direccion en la esfera · UVb = (sel, e): a que parte va + fase/tamano
//   ~34 % nucleo · del resto, 62 % envoltura del grupo y 38 % a lo largo de la hebra.
//   Los grupos ausentes no se sortean: el indice sale de la cantidad PRESENTE (N).
//   DustK = (tamano cm, opacidad, deriva cm, separacion de la superficie cm)
// Sin arreglos ni indices dinamicos (regla Adreno): cadenas de selects.
LVLib L;
float T = ResolvedView.GameTime;
if (!(T > -1.0e9 && T < 1.0e9)) { T = 0.0; }
float Rc, rb, gap, Renv, rMid, rEnd, lam, kC, kN, kE, Ratt, MoundH, kBall, WobA;
L.Shape(LV0, LV1, LV2, LV3, Rc, rb, gap, Renv, rMid, rEnd, lam, kC, kN, kE, Ratt, MoundH, kBall, WobA);
float gC = L.CentreGap(LV1, LV3, Rc);
float3 C = LV0.xyz;
float zd  = 2.0 * UVa.x - 1.0;
float phd = 6.2831853 * UVa.y;
float rsd = sqrt(saturate(1.0 - zd * zd));
float3 d  = float3(rsd * cos(phd), rsd * sin(phd), zd);
float sel = UVb.x, e = UVb.y;
float off = max(DustK.w, 0.0) * (0.35 + 0.65 * frac(e * 7.31));
// --- sobre la membrana del nucleo (misma ameba + abultamientos + hueco) ---
float3 gT, gm = float3(0.0, 0.0, 0.0);
float rC = L.CentreR(d, Rc, LV1, LV3, T, gT);
// grupos ausentes (M.w = 0): abultamiento de altura 0 -> [branch] uniforme por dibujo, mismo resultado
rC += L.Mound(d, float4(normalize(M0.xyz - C + float3(1.0e-4, 0.0, 0.0)), MoundH * M0.w), 0.55, gm);
[branch] if (M1.w > 0.0) { rC += L.Mound(d, float4(normalize(M1.xyz - C + float3(1.0e-4, 0.0, 0.0)), MoundH * M1.w), 0.55, gm); }
[branch] if (M2.w > 0.0) { rC += L.Mound(d, float4(normalize(M2.xyz - C + float3(1.0e-4, 0.0, 0.0)), MoundH * M2.w), 0.55, gm); }
[branch] if (M3.w > 0.0) { rC += L.Mound(d, float4(normalize(M3.xyz - C + float3(1.0e-4, 0.0, 0.0)), MoundH * M3.w), 0.55, gm); }
[branch] if (M4.w > 0.0) { rC += L.Mound(d, float4(normalize(M4.xyz - C + float3(1.0e-4, 0.0, 0.0)), MoundH * M4.w), 0.55, gm); }
[branch] if (M5.w > 0.0) { rC += L.Mound(d, float4(normalize(M5.xyz - C + float3(1.0e-4, 0.0, 0.0)), MoundH * M5.w), 0.55, gm); }
[branch] if (M6.w > 0.0) { rC += L.Mound(d, float4(normalize(M6.xyz - C + float3(1.0e-4, 0.0, 0.0)), MoundH * M6.w), 0.55, gm); }
[branch] if (M7.w > 0.0) { rC += L.Mound(d, float4(normalize(M7.xyz - C + float3(1.0e-4, 0.0, 0.0)), MoundH * M7.w), 0.55, gm); }
[branch] if (M8.w > 0.0) { rC += L.Mound(d, float4(normalize(M8.xyz - C + float3(1.0e-4, 0.0, 0.0)), MoundH * M8.w), 0.55, gm); }
[branch] if (M9.w > 0.0) { rC += L.Mound(d, float4(normalize(M9.xyz - C + float3(1.0e-4, 0.0, 0.0)), MoundH * M9.w), 0.55, gm); }
float3 Pcore = C + d * (rC + gC + off);
// --- grupo: indice entre los PRESENTES ---
float Np = step(0.5, M0.w) + step(0.5, M1.w) + step(0.5, M2.w) + step(0.5, M3.w) + step(0.5, M4.w)
         + step(0.5, M5.w) + step(0.5, M6.w) + step(0.5, M7.w) + step(0.5, M8.w) + step(0.5, M9.w);
float kf = floor(saturate((sel - 0.34) / 0.66) * max(Np, 1.0) * 0.9999);
float4 Gs = M0;
Gs = (kf > 0.5) ? M1 : Gs;
Gs = (kf > 1.5) ? M2 : Gs;
Gs = (kf > 2.5) ? M3 : Gs;
Gs = (kf > 3.5) ? M4 : Gs;
Gs = (kf > 4.5) ? M5 : Gs;
Gs = (kf > 5.5) ? M6 : Gs;
Gs = (kf > 6.5) ? M7 : Gs;
Gs = (kf > 7.5) ? M8 : Gs;
Gs = (kf > 8.5) ? M9 : Gs;
float4 a0, a1, a2, b0, b1, b2, a3, a4, a5, a6;
L.ArmSetup(float4(Gs.xyz, kf), LV0, LV1, LV2, LV3, LV4, LV5, T, a0, a1, a2, b0, b1, b2, a3, a4, a5, a6);
// sobre la envoltura del grupo (union de las bolas infladas, desde el centroide)
float envR = max(max(L.RayExit(d, b0, a1.w), L.RayExit(d, b1, a1.w)), L.RayExit(d, b2, a1.w));
float3 Penv = Gs.xyz + d * (envR + off);
// a lo largo de la hebra (tramo libre), con el MISMO curl que el brazo.
// v4 (2026-09-28, Beltran: "ondulaciones mas suaves"): la particula de la hebra se DESLIZA por el eje
// (+-1,5 DustDrift, fase propia, ANTES del curl -> queda siempre sobre la hebra curvada) en vez de
// derivar en 3D, y la manga se pega a la hebra (0,35 off; antes 0,6 -> hasta 1,5 cm de una hebra de 0,3).
float3 Pc = a0.xyz;
float3 ax = Gs.xyz - Pc; float Lx = max(length(ax), 1.0); ax /= Lx;
float3 U  = normalize(LV4.xyz - ax * dot(LV4.xyz, ax) + float3(0.0, 0.0, 1.0e-5));   // plano de la figura (a2.xyz es la inclinacion del ancla)
float3 Vb = cross(ax, U);
float zW0, zW1;
L.ArmWindow(a1, a2, a3, a4, a5, b0, b1, b2, Lx, zW0, zW1);
float zs = clamp(lerp(zW0, max(zW1, zW0), UVa.x) + 1.5 * DustK.z * sin(T * 0.29 + 6.2831853 * e), zW0, max(zW1, zW0));
float3 qd = normalize(d - ax * dot(d, ax) + float3(1.0e-4, 0.0, 0.0));
float3 Pstr = Pc + ax * zs + qd * (a3.x + 0.35 * off);
float3 sdz;
Pstr += L.StrandCurl(Pstr, Pc, ax, U, Vb, zW0, zW1, saturate(LV1.x), saturate(LV1.z), LV5.y, kf, T, sdz);
// eleccion (sin ramas)
float isCore = step(sel, 0.34);
// hebra corta (en calma el grupo se acerca): sus particulas se amontonarian en el cuello -> van a la envoltura
float isEnv  = max(step(e, 0.62), 1.0 - L.SS(4.0, 12.0, zW1 - zW0));
float3 P = lerp(lerp(Pstr, Penv, isEnv), Pcore, isCore);
float vis = lerp(step(0.5, Gs.w), 1.0, isCore);
float isStr = (1.0 - isCore) * (1.0 - isEnv);
// deriva propia, lenta. 🔴 En la hebra casi nada (x0,15): con fase 44,7*UVa.x (UVa.x es TAMBIEN la
// posicion a lo largo del tramo) la deriva de 0,6 cm por eje dibujaba siete ondas cortas + un serrucho
// de +-1 cm alrededor de la hebra: las "ondulaciones pequenas". Ahi el movimiento es el deslizamiento.
P += DustK.z * (1.0 - 0.85 * isStr) * float3(sin(T * 0.31 + 44.7 * UVa.x), sin(T * 0.27 + 31.3 * UVa.y), sin(T * 0.23 + 23.9 * e));
// sprite hacia la camara (CamL = camara en espacio LOCAL)
float3 f   = normalize(CamL.xyz - P + float3(1.0e-4, 0.0, 0.0));
float3 rgt = normalize(cross(float3(0.0, 0.0, 1.0), f) + float3(1.0e-4, 0.0, 0.0));
float3 upv = cross(f, rgt);
float2 c   = Crn.xy * 2.0 - 1.0;
float  sz  = max(DustK.x, 0.0) * (0.6 + 0.8 * frac(e * 3.7)) * vis;
float3 dst = P + (rgt * c.x + upv * c.y) * sz;
float  tw  = 0.55 + 0.45 * sin(T * (0.7 + 0.9 * UVa.y) + 6.2831853 * e);
DustUV = float3(c, max(DustK.y, 0.0) * tw * vis);
float3 offs = dst - LocalPos;
if (!(dot(offs, offs) < 1.0e12)) { offs = float3(0.0, 0.0, 0.0); }
float ol = length(offs);
return offs * (min(ol, 400.0) / max(ol, 1.0e-4));
