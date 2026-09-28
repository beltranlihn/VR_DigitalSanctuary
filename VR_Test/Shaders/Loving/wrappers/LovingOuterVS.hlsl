// @uses SS,Hash,Shape,GroupScale,Calm,CoreWob,CentreGap,AmPod,AmBody,CentreR,Mound,CurlEnv,OuterEnv,OuterLobe,OuterWob
// @inputs LocalPos,LV0,LV1,LV2,LV3,LV4,LV5,M0,M1,M2,M3,M4,M5,M6,M7,M8,M9,OuterK
// @outputs return:Float3,Nrm:Float3
// ENVOLTURA EXTERIOR (2026-09-28): una ameba translucida que encierra TODA la celula. La icoesfera
// (SM_LovingIco_SC, radio 50) solo aporta direcciones: cada vertice va a C + u r(u), con r la union
// suave (norma p) del CUERPO (membrana del nucleo exacta + margen + OuterBody) y un PSEUDOPODO
// gaussiano por grupo presente, por la ondulacion positiva. Forma cerrada: cero iteraciones, sin
// BallsLayout por grupo, normal analitica POR VERTICE: n = normalize(u - tangencial(grad ln r)).
// OuterK = (margen efectivo cm [OuterMargin + holgura del polvo, lo suma el BP], OuterBody cm,
//           OuterSoftness 0-1 -> p de 8 a 3, OuterWobble). M_i = (centroide, presencia 0 o 1).
// Suavidad (revision 2026-09-28): con p 16 -> 4 y el default 0,65 (p 8,2) la union era casi un maximo: una estrella
// de 5 brazos con muescas en V (radio de curvatura 1,4 cm entre pseudopodos, 1,1 a S = 0) y lineas de costura; la
// icoesfera de 2562 no las resuelve (hasta 7-9 px de error de silueta, triangulos volteados). p 4 (default 0,8):
// muesca 5,3 cm (4,1 a S = 0), base del pseudopodo 15,5 cm; p 3 (1,0): 8,8 / 24,8 cm. Bajar p solo AGREGA material
// ((sum a^p)^(1/p) >= max a): el encierro no cambia; cuesta algo de relleno (+~4 % de cobertura de p 8,2 a p 4).
// 🔴 Sin arreglos ni indices dinamicos (regla Adreno): 10 llamadas con variables con nombre.
// 🔴 El cuerpo repite la cuenta de LovingCentreFilmVS (CentreR + Mound c0 0,55 + CentreGap): si esa
//    membrana cambia de formula, esta tambien (si no, el margen alrededor del nucleo deja de valer).
//    Como llama a la MISMA CentreR, sigue sola a la ameba V4 (pseudopodos que derivan): la envoltura
//    repite su forma, inflada m + OuterBody.
LVLib L;
float T = ResolvedView.GameTime;
if (!(T > -1.0e9 && T < 1.0e9)) { T = 0.0; }
float Rc, rb, gap, Renv, rMid, rEnd, lam, kC, kN, kE, Ratt, MoundH, kBall, WobA;
L.Shape(LV0, LV1, LV2, LV3, Rc, rb, gap, Renv, rMid, rEnd, lam, kC, kN, kE, Ratt, MoundH, kBall, WobA);
float  gC  = L.CentreGap(LV1, LV3, Rc);
float3 C   = LV0.xyz;
float3 u   = normalize(LocalPos + float3(1.0e-4, 0.0, 0.0));
float  m   = max(OuterK.x, 0.0);
float  p   = lerp(8.0, 3.0, saturate(OuterK.z));   // OuterSoftness 0 -> p 8 (pliegues marcados), 1 -> p 3 (default 0,8 -> p 4)
float  Coh = L.Calm(LV1);
float4 Env, Win;
L.OuterEnv(Rc, rb, gap, gC, rMid, rEnd, lam, kC, kN, MoundH, LV1, LV3, LV4, LV5, OuterK, Env, Win);
float3 gT;
float  rm = L.CentreR(u, Rc, LV1, LV3, T, gT);
float3 gm = float3(0.0, 0.0, 0.0);
float3 gE = float3(0.0, 0.0, 0.0);
float  sE = 0.0;
// Grupos AUSENTES (M.w = 0): [branch] uniforme por dibujo -> no se paga su lobulo (con 5 de 10 grupos, la mitad
// del trabajo). El resultado no cambia: un ausente aporta ~1e-16 contra ~8e-3 y un abultamiento de altura 0.
// M0 siempre esta (GroupCount >= 1). 🔴 La condicion es un uniform: sin indices dinamicos (regla Adreno).
L.OuterLobe(u, C, M0, 0.0, Env, Win, LV1, LV5, MoundH, m, p, Coh, T, sE, gE, rm, gm);
[branch] if (M1.w > 0.0) { L.OuterLobe(u, C, M1, 1.0, Env, Win, LV1, LV5, MoundH, m, p, Coh, T, sE, gE, rm, gm); }
[branch] if (M2.w > 0.0) { L.OuterLobe(u, C, M2, 2.0, Env, Win, LV1, LV5, MoundH, m, p, Coh, T, sE, gE, rm, gm); }
[branch] if (M3.w > 0.0) { L.OuterLobe(u, C, M3, 3.0, Env, Win, LV1, LV5, MoundH, m, p, Coh, T, sE, gE, rm, gm); }
[branch] if (M4.w > 0.0) { L.OuterLobe(u, C, M4, 4.0, Env, Win, LV1, LV5, MoundH, m, p, Coh, T, sE, gE, rm, gm); }
[branch] if (M5.w > 0.0) { L.OuterLobe(u, C, M5, 5.0, Env, Win, LV1, LV5, MoundH, m, p, Coh, T, sE, gE, rm, gm); }
[branch] if (M6.w > 0.0) { L.OuterLobe(u, C, M6, 6.0, Env, Win, LV1, LV5, MoundH, m, p, Coh, T, sE, gE, rm, gm); }
[branch] if (M7.w > 0.0) { L.OuterLobe(u, C, M7, 7.0, Env, Win, LV1, LV5, MoundH, m, p, Coh, T, sE, gE, rm, gm); }
[branch] if (M8.w > 0.0) { L.OuterLobe(u, C, M8, 8.0, Env, Win, LV1, LV5, MoundH, m, p, Coh, T, sE, gE, rm, gm); }
[branch] if (M9.w > 0.0) { L.OuterLobe(u, C, M9, 9.0, Env, Win, LV1, LV5, MoundH, m, p, Coh, T, sE, gE, rm, gm); }
// cuerpo = membrana del nucleo (ameba + abultamientos + hueco) + margen + OuterBody
gT += gm - u * dot(u, gm);
float  rB = max(rm + gC + m + max(OuterK.y, 0.0), 1.0);
float  E0 = exp2(p * log2(rB * 0.01));
sE += E0;
gE += (E0 / rB) * gT;
float  r  = 100.0 * exp2(log2(sE) / p);
float3 G  = gE / sE;                         // = grad ln r (con la componente radial de los lobulos)
float3 gW;
float  W   = L.OuterWob(u, T, gW);
float  fac = 1.0 + Env.w * W;
r *= fac;
G += (Env.w / fac) * gW;
Nrm = normalize(u - (G - u * dot(u, G)));
float3 dst = C + u * r;
float3 off = dst - LocalPos;
if (!(dot(off, off) < 1.0e12)) { off = float3(0.0, 0.0, 0.0); }
float ol = length(off);
return off * (min(ol, 400.0) / max(ol, 1.0e-4));
