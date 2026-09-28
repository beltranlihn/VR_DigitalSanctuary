// @uses SS,Shape,CoreWob,AmPod,AmBody,CentreR,Mound
// @inputs LocalPos,LV0,LV1,LV2,LV3,M0,M1,M2,M3,M4,M5,M6,M7,M8,M9
// @outputs return:Float3,Nrm:Float3
// NUCLEO: ameba r(u) (V4: 4 pseudopodos + 2 masas en pares, marco que gira) + un abultamiento hacia cada grupo.
// M_i = (centroide del grupo i, presencia 0-1). Altura del abultamiento desde el estado.
// Cero iteraciones; normal analitica POR VERTICE (icoesfera de 10k vertices).
LVLib L;
float T = ResolvedView.GameTime;
if (!(T > -1.0e9 && T < 1.0e9)) { T = 0.0; }
float Rc, rb, gap, Renv, rMid, rEnd, lam, kC, kN, kE, Ratt, MoundH, kBall, WobA;
L.Shape(LV0, LV1, LV2, LV3, Rc, rb, gap, Renv, rMid, rEnd, lam, kC, kN, kE, Ratt, MoundH, kBall, WobA);
float3 C = LV0.xyz;
float3 u = normalize(LocalPos + float3(1.0e-4, 0.0, 0.0));
float3 gT;
float  r  = L.CentreR(u, Rc, LV1, LV3, T, gT);
float3 gm = float3(0.0, 0.0, 0.0);
// Grupos ausentes (M.w = 0): abultamiento de altura 0 -> [branch] uniforme por dibujo, sin cambio en el resultado.
r += L.Mound(u, float4(normalize(M0.xyz - C + float3(1.0e-4, 0.0, 0.0)), MoundH * M0.w), 0.55, gm);
[branch] if (M1.w > 0.0) { r += L.Mound(u, float4(normalize(M1.xyz - C + float3(1.0e-4, 0.0, 0.0)), MoundH * M1.w), 0.55, gm); }
[branch] if (M2.w > 0.0) { r += L.Mound(u, float4(normalize(M2.xyz - C + float3(1.0e-4, 0.0, 0.0)), MoundH * M2.w), 0.55, gm); }
[branch] if (M3.w > 0.0) { r += L.Mound(u, float4(normalize(M3.xyz - C + float3(1.0e-4, 0.0, 0.0)), MoundH * M3.w), 0.55, gm); }
[branch] if (M4.w > 0.0) { r += L.Mound(u, float4(normalize(M4.xyz - C + float3(1.0e-4, 0.0, 0.0)), MoundH * M4.w), 0.55, gm); }
[branch] if (M5.w > 0.0) { r += L.Mound(u, float4(normalize(M5.xyz - C + float3(1.0e-4, 0.0, 0.0)), MoundH * M5.w), 0.55, gm); }
[branch] if (M6.w > 0.0) { r += L.Mound(u, float4(normalize(M6.xyz - C + float3(1.0e-4, 0.0, 0.0)), MoundH * M6.w), 0.55, gm); }
[branch] if (M7.w > 0.0) { r += L.Mound(u, float4(normalize(M7.xyz - C + float3(1.0e-4, 0.0, 0.0)), MoundH * M7.w), 0.55, gm); }
[branch] if (M8.w > 0.0) { r += L.Mound(u, float4(normalize(M8.xyz - C + float3(1.0e-4, 0.0, 0.0)), MoundH * M8.w), 0.55, gm); }
[branch] if (M9.w > 0.0) { r += L.Mound(u, float4(normalize(M9.xyz - C + float3(1.0e-4, 0.0, 0.0)), MoundH * M9.w), 0.55, gm); }
gT += gm - u * dot(u, gm);
Nrm = normalize(u - gT / max(r, 0.01));
float3 off = C + u * r - LocalPos;
if (!(dot(off, off) < 1.0e12)) { off = float3(0.0, 0.0, 0.0); }
float ol = length(off);
return off * (min(ol, 400.0) / max(ol, 1.0e-4));
