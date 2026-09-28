// @uses SS,Hash,Shape,GroupScale,Calm,BallsLayout,SminS,Smin,Sph,BallsRay,HitBalls,Balls3
// @inputs LocalPos,GI,LV0,LV1,LV2,LV3,LV5
// @outputs return:Float3,Rel:Float3,Aoc:Float2
// RACIMO: cada vertice de la icoesfera marcha desde el centroide G (GI.xyz) en su direccion
// y biseca sobre el smin de las 2-3 bolas del grupo. Las bolas NO vienen del BP: salen de
// BallsLayout(indice del grupo, estado) — la misma cuenta que usa el brazo para la envoltura.
// Rel = punto relativo a G (normal POR PIXEL) · Aoc.x = oclusion hacia el nucleo.
LVLib L;
float T = ResolvedView.GameTime;
if (!(T > -1.0e9 && T < 1.0e9)) { T = 0.0; }
float Rc, rb, gap, Renv, rMid, rEnd, lam, kC, kN, kE, Ratt, MoundH, kBall, WobA;
float4 LV2g = float4(LV2.x * L.GroupScale(GI.w, LV5), LV2.yzw);   // tamano propio del grupo (SizeVariation)
L.Shape(LV0, LV1, LV2g, LV3, Rc, rb, gap, Renv, rMid, rEnd, lam, kC, kN, kE, Ratt, MoundH, kBall, WobA);
float3 toC = normalize(LV0.xyz - GI.xyz + float3(1.0e-4, 0.0, 0.0));
float4 B0, B1, B2;
L.BallsLayout(GI.w, rb, toC, L.SS(0.3, 0.6, saturate(LV1.x)), LV2.z, T, LV3.w, LV1, B0, B1, B2);
float3 u   = normalize(LocalPos + float3(1.0e-4, 0.0, 0.0));
float  r   = L.HitBalls(u, B0, B1, B2, kBall);
float3 rel = u * r;
float3 dst = GI.xyz + rel;
float3 g; float cr;
L.Balls3(rel, B0, B1, B2, kBall, g, cr);
float3 n   = normalize(g);
float3 D   = LV0.xyz - dst;
float  dl  = max(length(D), 1.0e-3);
float  occ = saturate(dot(n, D / dl)) * (Rc * Rc) / (dl * dl);
Rel = rel;
Aoc = float2(saturate(1.0 - 0.8 * occ), r);
float3 off = dst - LocalPos;
if (!(dot(off, off) < 1.0e12)) { off = float3(0.0, 0.0, 0.0); }
float ol = length(off);
return off * (min(ol, 400.0) / max(ol, 1.0e-4));
