// @uses SS,Hash,Shape,CoreWob,Calm,NeckBreath,BallsLayout,CentreGap,ArmSetup,AmPod,AmBody,CentreR,Mound,SminS,SminH,Surr,StrandR,ArmField3
// @inputs LocalPos,LV0,LV1,LV2,LV3,LV4,LV5,M0,M1,M2,M3,M4,M5,M6,M7,M8,M9
// @outputs return:Float3,Nrm:Float3,Misc:Float3,Misc2:Float2
// MEMBRANA DEL NUCLEO: la misma ameba del nucleo opaco (lobulos + abultamientos hacia cada
// grupo) inflada CentreGap. Forma cerrada, cero iteraciones, normal analitica por vertice
// (el hueco es constante sobre la superficie, asi que la normal es la de la ameba).
// Recorte mutuo con los brazos: esta pelicula se apaga donde queda DENTRO del brazo real
// (ArmField3 del grupo mas cercano, la MISMA cuenta que dibuja el brazo) y la del brazo se
// apaga donde queda dentro de esta (dC). Una sola capa en la union + linea de Plateau.
// Por que el brazo MAS CERCANO alcanza: el anillo del hueco queda a <= ~18 grados de su eje y
// los grupos estan a >= 60 grados; el cambio de brazo cae en la bisectriz, donde los dos
// campos son grandes y positivos (sin hueco) y J ~ 0 en ambos. Una sola evaluacion del campo
// (revision 2026-09-27: la raiz simplificada dejaba el hueco hasta 2 cm chico para S >= 0,55).
// Sin arreglos ni indices dinamicos (regla Adreno): cadena de selects por slot.
// M_i = (centroide del grupo i, presencia 0-1); el indice del grupo es la posicion del slot.
LVLib L;
float T = ResolvedView.GameTime;
if (!(T > -1.0e9 && T < 1.0e9)) { T = 0.0; }
float Rc, rb, gap, Renv, rMid, rEnd, lam, kC, kN, kE, Ratt, MoundH, kBall, WobA;
L.Shape(LV0, LV1, LV2, LV3, Rc, rb, gap, Renv, rMid, rEnd, lam, kC, kN, kE, Ratt, MoundH, kBall, WobA);
float gC  = L.CentreGap(LV1, LV3, Rc);
float3 C  = LV0.xyz;
float3 u  = normalize(LocalPos + float3(1.0e-4, 0.0, 0.0));
float3 q0 = normalize(M0.xyz - C + float3(1.0e-4, 0.0, 0.0));
float3 gT;
float  r  = L.CentreR(u, Rc, LV1, LV3, T, gT);
float3 gm = float3(0.0, 0.0, 0.0);
// Por slot: el abultamiento hacia el grupo y, con la MISMA q, el candidato al grupo PRESENTE mas cercano en
// angulo (los ausentes restan 10 y nunca ganan). Grupos ausentes (M.w = 0): abultamiento de altura 0 y candidato
// perdedor -> [branch] uniforme por dibujo, mismo resultado; con 5 de 10 grupos no se pagan los otros 5.
// M0 siempre esta (GroupCount >= 1). 🔴 Sin arreglos: una rama con variables con nombre por slot (regla Adreno).
float  bd = -9.0;
float4 Gs = float4(M0.xyz, 0.0);
float  dk;
r += L.Mound(u, float4(q0, MoundH * M0.w), 0.55, gm);
dk = dot(u, q0) - 10.0 * (1.0 - step(0.5, M0.w)); Gs = (dk > bd) ? float4(M0.xyz, 0.0) : Gs; bd = max(bd, dk);
[branch] if (M1.w > 0.0)
{
    float3 q1 = normalize(M1.xyz - C + float3(1.0e-4, 0.0, 0.0));
    r += L.Mound(u, float4(q1, MoundH * M1.w), 0.55, gm);
    dk = dot(u, q1) - 10.0 * (1.0 - step(0.5, M1.w)); Gs = (dk > bd) ? float4(M1.xyz, 1.0) : Gs; bd = max(bd, dk);
}
[branch] if (M2.w > 0.0)
{
    float3 q2 = normalize(M2.xyz - C + float3(1.0e-4, 0.0, 0.0));
    r += L.Mound(u, float4(q2, MoundH * M2.w), 0.55, gm);
    dk = dot(u, q2) - 10.0 * (1.0 - step(0.5, M2.w)); Gs = (dk > bd) ? float4(M2.xyz, 2.0) : Gs; bd = max(bd, dk);
}
[branch] if (M3.w > 0.0)
{
    float3 q3 = normalize(M3.xyz - C + float3(1.0e-4, 0.0, 0.0));
    r += L.Mound(u, float4(q3, MoundH * M3.w), 0.55, gm);
    dk = dot(u, q3) - 10.0 * (1.0 - step(0.5, M3.w)); Gs = (dk > bd) ? float4(M3.xyz, 3.0) : Gs; bd = max(bd, dk);
}
[branch] if (M4.w > 0.0)
{
    float3 q4 = normalize(M4.xyz - C + float3(1.0e-4, 0.0, 0.0));
    r += L.Mound(u, float4(q4, MoundH * M4.w), 0.55, gm);
    dk = dot(u, q4) - 10.0 * (1.0 - step(0.5, M4.w)); Gs = (dk > bd) ? float4(M4.xyz, 4.0) : Gs; bd = max(bd, dk);
}
[branch] if (M5.w > 0.0)
{
    float3 q5 = normalize(M5.xyz - C + float3(1.0e-4, 0.0, 0.0));
    r += L.Mound(u, float4(q5, MoundH * M5.w), 0.55, gm);
    dk = dot(u, q5) - 10.0 * (1.0 - step(0.5, M5.w)); Gs = (dk > bd) ? float4(M5.xyz, 5.0) : Gs; bd = max(bd, dk);
}
[branch] if (M6.w > 0.0)
{
    float3 q6 = normalize(M6.xyz - C + float3(1.0e-4, 0.0, 0.0));
    r += L.Mound(u, float4(q6, MoundH * M6.w), 0.55, gm);
    dk = dot(u, q6) - 10.0 * (1.0 - step(0.5, M6.w)); Gs = (dk > bd) ? float4(M6.xyz, 6.0) : Gs; bd = max(bd, dk);
}
[branch] if (M7.w > 0.0)
{
    float3 q7 = normalize(M7.xyz - C + float3(1.0e-4, 0.0, 0.0));
    r += L.Mound(u, float4(q7, MoundH * M7.w), 0.55, gm);
    dk = dot(u, q7) - 10.0 * (1.0 - step(0.5, M7.w)); Gs = (dk > bd) ? float4(M7.xyz, 7.0) : Gs; bd = max(bd, dk);
}
[branch] if (M8.w > 0.0)
{
    float3 q8 = normalize(M8.xyz - C + float3(1.0e-4, 0.0, 0.0));
    r += L.Mound(u, float4(q8, MoundH * M8.w), 0.55, gm);
    dk = dot(u, q8) - 10.0 * (1.0 - step(0.5, M8.w)); Gs = (dk > bd) ? float4(M8.xyz, 8.0) : Gs; bd = max(bd, dk);
}
[branch] if (M9.w > 0.0)
{
    float3 q9 = normalize(M9.xyz - C + float3(1.0e-4, 0.0, 0.0));
    r += L.Mound(u, float4(q9, MoundH * M9.w), 0.55, gm);
    dk = dot(u, q9) - 10.0 * (1.0 - step(0.5, M9.w)); Gs = (dk > bd) ? float4(M9.xyz, 9.0) : Gs; bd = max(bd, dk);
}
gT += gm - u * dot(u, gm);
Nrm = normalize(u - gT / max(r + gC, 0.01));
float3 dst = C + u * (r + gC);
float none = step(bd, -5.0);
float4 a0, a1, a2, b0, b1, b2, a3, a4, a5, a6;
float  Jr;
L.ArmSetup(Gs, LV0, LV1, LV2, LV3, LV4, LV5, T, a0, a1, a2, b0, b1, b2, a3, a4, a5, a6);
float cl = L.ArmField3(dst, a0, a1, a2, b0, b1, b2, a3, a4, a5, Jr) + none * 1.0e4;
// densidad de juntura = la del brazo en el mismo punto (antes una constante 0,6: salto de
// densidad en la costura); radio de revelado alto (nunca colapsa); sin contacto propio
Misc  = float3(Jr * (1.0 - none), 10.0, cl);
Misc2 = float2(1.0e3, 0.0);
float3 off = dst - LocalPos;
if (!(dot(off, off) < 1.0e12)) { off = float3(0.0, 0.0, 0.0); }
float ol = length(off);
return off * (min(ol, 400.0) / max(ol, 1.0e-4));
